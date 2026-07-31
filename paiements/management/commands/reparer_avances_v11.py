"""
Réparation des avances de loyer — V11
=====================================

Corrige les avances déjà enregistrées en base qui ont été altérées par les
anciennes logiques :

  1. `statut` mis à 'epuisee' sur un simple critère de DATE (couverture échue)
     alors que l'avance n'était pas consommée → le statut est recalculé à partir
     de la consommation réelle (ConsommationAvance).
  2. `montant_restant` réinitialisé au montant total à chaque synchronisation
     → recalculé à partir des consommations réellement enregistrées.
  3. `nombre_mois_couverts` / `mois_fin_couverture` incohérents avec le montant
     et le loyer (auto-correction destructive qui ramenait des avances de
     plusieurs mois à 1 mois) → recalculés via ServiceLogiqueAvanceUnique.
  4. Avances orphelines : paiement de type 'avance' sans AvanceLoyer associée.

Par défaut la commande tourne en simulation (dry-run) et n'écrit RIEN.

Utilisation :
    python manage.py reparer_avances_v11                    # simulation, tous les contrats
    python manage.py reparer_avances_v11 --contrat 42       # simulation, un contrat
    python manage.py reparer_avances_v11 --appliquer        # écriture réelle
    python manage.py reparer_avances_v11 --appliquer --recalculer-debut
    python manage.py reparer_avances_v11 --creer-manquantes --appliquer
"""
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Sum
from dateutil.relativedelta import relativedelta

from contrats.models import Contrat
from paiements.models import Paiement
from paiements.models_avance import AvanceLoyer, ConsommationAvance
from paiements.services_logique_avance_unique import ServiceLogiqueAvanceUnique


MOIS_FR = {
    1: 'janvier', 2: 'février', 3: 'mars', 4: 'avril', 5: 'mai', 6: 'juin',
    7: 'juillet', 8: 'août', 9: 'septembre', 10: 'octobre', 11: 'novembre',
    12: 'décembre',
}


def fmt_mois(d):
    if not d:
        return '—'
    return f"{MOIS_FR.get(d.month, d.month)} {d.year}"


class Command(BaseCommand):
    help = "Répare les avances de loyer incohérentes (statut, montant restant, mois couverts)."

    def add_arguments(self, parser):
        parser.add_argument(
            '--appliquer',
            action='store_true',
            help="Écrit réellement les corrections en base (sinon simulation seule).",
        )
        parser.add_argument(
            '--contrat',
            type=int,
            default=None,
            help="Limiter la réparation à un contrat (ID).",
        )
        parser.add_argument(
            '--recalculer-debut',
            action='store_true',
            help=(
                "Recalcule aussi mois_debut_couverture en rejouant les avances dans "
                "l'ordre chronologique. À n'utiliser que si les périodes de couverture "
                "sont visiblement décalées."
            ),
        )
        parser.add_argument(
            '--creer-manquantes',
            action='store_true',
            help="Crée les AvanceLoyer manquantes pour les paiements de type 'avance'.",
        )

    # ------------------------------------------------------------------ #

    def handle(self, *args, **options):
        self.appliquer = options['appliquer']
        self.recalculer_debut = options['recalculer_debut']
        self.creer_manquantes = options['creer_manquantes']

        contrats = Contrat.objects.all()
        if options['contrat']:
            contrats = contrats.filter(id=options['contrat'])
        contrats = contrats.filter(
            id__in=AvanceLoyer.objects.values_list('contrat_id', flat=True)
        ) | contrats.filter(
            id__in=Paiement.objects.filter(type_paiement='avance').values_list('contrat_id', flat=True)
        )
        contrats = contrats.distinct().select_related('locataire', 'propriete')

        self.stdout.write('=' * 78)
        self.stdout.write(
            self.style.WARNING('MODE SIMULATION (--appliquer absent) : aucune écriture en base')
            if not self.appliquer
            else self.style.ERROR('MODE ÉCRITURE : les corrections seront enregistrées')
        )
        self.stdout.write('=' * 78)

        self.total_corrections = 0
        self.total_creations = 0
        self.total_contrats = 0

        for contrat in contrats:
            self._traiter_contrat(contrat)

        self.stdout.write('')
        self.stdout.write('=' * 78)
        self.stdout.write(f"Contrats analysés    : {self.total_contrats}")
        self.stdout.write(f"Avances corrigées    : {self.total_corrections}")
        self.stdout.write(f"Avances créées       : {self.total_creations}")
        if not self.appliquer and (self.total_corrections or self.total_creations):
            self.stdout.write('')
            self.stdout.write(self.style.WARNING(
                "Relancez avec --appliquer pour enregistrer ces corrections."
            ))
        self.stdout.write('=' * 78)

    # ------------------------------------------------------------------ #

    def _traiter_contrat(self, contrat):
        avances = list(
            AvanceLoyer.objects
            .filter(contrat=contrat)
            .exclude(statut='annulee')
            .order_by('date_avance', 'id')
        )
        paiements_avance_orphelins = []
        if self.creer_manquantes:
            paiements_avance_orphelins = list(
                Paiement.objects
                .filter(contrat=contrat, type_paiement='avance', statut='valide', is_deleted=False)
                .exclude(id__in=[a.paiement_id for a in avances if a.paiement_id])
                .order_by('date_paiement', 'id')
            )

        if not avances and not paiements_avance_orphelins:
            return

        self.total_contrats += 1
        entete = f"Contrat #{contrat.id} — {contrat.numero_contrat or 'sans numéro'}"
        try:
            entete += f" — {contrat.locataire.get_nom_complet()}"
        except Exception:
            pass

        lignes = []
        loyer_contrat = self._loyer_contrat(contrat)

        # --- 1. Réparation des avances existantes ---------------------- #
        curseur_couverture = None  # fin de couverture de l'avance précédente
        for avance in avances:
            modifs = self._reparer_avance(avance, loyer_contrat, curseur_couverture)
            if modifs:
                self.total_corrections += 1
                lignes.append(f"  Avance #{avance.id} ({avance.montant_avance} F CFA, {avance.date_avance}) :")
                for m in modifs:
                    lignes.append(f"      • {m}")
            curseur_couverture = avance.mois_fin_couverture or curseur_couverture

        # --- 2. Création des avances manquantes ------------------------ #
        for paiement in paiements_avance_orphelins:
            libelle = (
                f"  Paiement #{paiement.id} ({paiement.montant} F CFA, {paiement.date_paiement}) "
                f"→ AvanceLoyer manquante"
            )
            if self.appliquer:
                try:
                    with transaction.atomic():
                        nouvelle = ServiceLogiqueAvanceUnique.creer_avance_avec_logique_unique(
                            contrat=contrat,
                            montant_avance=Decimal(str(paiement.montant)),
                            date_avance=paiement.date_paiement,
                            notes=f"Créée par reparer_avances_v11 depuis paiement {paiement.id}",
                            paiement=paiement,
                        )
                    libelle += f" → CRÉÉE (#{nouvelle.id}, {fmt_mois(nouvelle.mois_debut_couverture)} → {fmt_mois(nouvelle.mois_fin_couverture)})"
                    self.total_creations += 1
                except Exception as e:
                    libelle += f" → ÉCHEC : {e}"
            else:
                libelle += " → à créer"
                self.total_creations += 1
            lignes.append(libelle)

        if lignes:
            self.stdout.write('')
            self.stdout.write(self.style.MIGRATE_HEADING(entete))
            for ligne in lignes:
                self.stdout.write(ligne)

    # ------------------------------------------------------------------ #

    def _reparer_avance(self, avance, loyer_contrat, curseur_couverture):
        """Retourne la liste lisible des corrections appliquées (ou simulées)."""
        modifs = []
        champs = []

        loyer = Decimal(str(avance.loyer_mensuel or '0'))
        if loyer <= 0 and loyer_contrat > 0:
            modifs.append(f"loyer_mensuel : {avance.loyer_mensuel} → {loyer_contrat}")
            avance.loyer_mensuel = loyer_contrat
            loyer = loyer_contrat
            champs.append('loyer_mensuel')

        montant = Decimal(str(avance.montant_avance or '0'))

        # --- nombre de mois couverts ------------------------------------ #
        if loyer > 0 and avance.mode_selection_mois != 'manuel':
            nb_attendu, reste = ServiceLogiqueAvanceUnique.calculer_nombre_mois_couverts(montant, loyer)
            if nb_attendu != avance.nombre_mois_couverts:
                modifs.append(
                    f"nombre_mois_couverts : {avance.nombre_mois_couverts} → {nb_attendu} "
                    f"({montant} / {loyer})"
                )
                avance.nombre_mois_couverts = nb_attendu
                champs.append('nombre_mois_couverts')
            if reste != Decimal(str(avance.montant_reste or '0')):
                avance.montant_reste = reste
                champs.append('montant_reste')

        # --- mois de début (optionnel) ---------------------------------- #
        if self.recalculer_debut and curseur_couverture:
            debut_attendu = curseur_couverture + relativedelta(months=1)
            if avance.mois_debut_couverture != debut_attendu:
                modifs.append(
                    f"mois_debut_couverture : {fmt_mois(avance.mois_debut_couverture)} → {fmt_mois(debut_attendu)}"
                )
                avance.mois_debut_couverture = debut_attendu
                champs.append('mois_debut_couverture')

        # --- mois de fin ------------------------------------------------ #
        if avance.mois_debut_couverture and avance.nombre_mois_couverts > 0:
            fin_attendue = ServiceLogiqueAvanceUnique.calculer_mois_fin_couverture(
                avance.mois_debut_couverture, avance.nombre_mois_couverts
            )
            if avance.mois_fin_couverture != fin_attendue:
                modifs.append(
                    f"mois_fin_couverture : {fmt_mois(avance.mois_fin_couverture)} → {fmt_mois(fin_attendue)}"
                )
                avance.mois_fin_couverture = fin_attendue
                champs.append('mois_fin_couverture')

        # --- montant restant, à partir des consommations RÉELLES -------- #
        total_consomme = ConsommationAvance.objects.filter(avance=avance).aggregate(
            total=Sum('montant_consomme')
        )['total'] or Decimal('0')
        restant_attendu = max(Decimal('0'), montant - Decimal(str(total_consomme)))
        if Decimal(str(avance.montant_restant or '0')) != restant_attendu:
            modifs.append(
                f"montant_restant : {avance.montant_restant} → {restant_attendu} "
                f"(consommé réel : {total_consomme})"
            )
            avance.montant_restant = restant_attendu
            champs.append('montant_restant')

        # --- statut, basé sur la consommation et NON sur la date -------- #
        statut_attendu = 'epuisee' if restant_attendu <= 0 else 'active'
        if avance.statut != statut_attendu:
            modifs.append(
                f"statut : '{avance.statut}' → '{statut_attendu}' "
                f"(recalculé sur la consommation réelle, pas sur la date)"
            )
            avance.statut = statut_attendu
            champs.append('statut')

        if modifs and self.appliquer:
            # update_fields : on n'appelle pas calculer_mois_couverts() (réservé
            # à la création), on écrit exactement les champs recalculés ici.
            avance.save(update_fields=list(dict.fromkeys(champs)))

        return modifs

    # ------------------------------------------------------------------ #

    @staticmethod
    def _loyer_contrat(contrat):
        try:
            valeur = contrat.get_loyer_total() if hasattr(contrat, 'get_loyer_total') else contrat.loyer_mensuel
            if isinstance(valeur, str):
                valeur = valeur.replace(',', '').replace(' ', '')
            return Decimal(str(valeur or '0'))
        except Exception:
            return Decimal('0')
