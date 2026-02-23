#!/usr/bin/env python3
"""
Service pour générer le récapitulatif mensuel d'état de paiement des loyers
pour chaque bailleur
"""

import logging
import datetime
from dateutil.relativedelta import relativedelta
from decimal import Decimal
from django.utils import timezone
from django.db.models import Q, Sum
from paiements.models import Paiement
from proprietes.models import Propriete
from contrats.models import Contrat

logger = logging.getLogger(__name__)

# Dictionnaire des mois en français
MOIS_FRANCAIS = {
    1: 'Janvier', 2: 'Février', 3: 'Mars', 4: 'Avril',
    5: 'Mai', 6: 'Juin', 7: 'Juillet', 8: 'Août',
    9: 'Septembre', 10: 'Octobre', 11: 'Novembre', 12: 'Décembre'
}


def formater_mois_francais(date_obj):
    """
    Formate une date pour afficher le mois en français (ex: "Avril 2025")
    """
    if not date_obj:
        return ""
    return f"{MOIS_FRANCAIS[date_obj.month]} {date_obj.year}"


class ServiceRecapPaiementMensuel:
    """Service pour générer le récapitulatif d'état de paiement mensuel par bailleur."""
    
    @staticmethod
    def preparer_donnees_recap_paiement(bailleur, mois_recap):
        """
        Prépare les données pour le récapitulatif de paiement mensuel.
        
        Args:
            bailleur: Instance de Bailleur
            mois_recap: Date du mois à récapituler (premier jour du mois)
        
        Returns:
            dict: Dictionnaire contenant toutes les données pour le récapitulatif
        """
        # Calculer les dates de début et fin du mois
        mois_debut = mois_recap.replace(day=1)
        if mois_recap.month == 12:
            mois_fin = mois_recap.replace(year=mois_recap.year + 1, month=1, day=1) - relativedelta(days=1)
        else:
            mois_fin = mois_recap.replace(month=mois_recap.month + 1, day=1) - relativedelta(days=1)
        
        # Récupérer les propriétés du bailleur avec contrats actifs (même logique que RecapMensuel)
        # Pour garantir la cohérence entre les deux documents
        proprietes_louees = bailleur.proprietes.filter(
            is_deleted=False,
            contrats__est_actif=True,
            contrats__est_resilie=False,
            contrats__date_debut__lte=mois_fin
        ).filter(
            Q(contrats__date_fin__gte=mois_debut) | Q(contrats__date_fin__isnull=True)
        ).distinct().select_related('type_bien', 'bailleur').prefetch_related(
            'contrats__locataire'
        )
        
        # Log pour déboguer
        logger.debug("Bailleur %s: %d propriétés trouvées avec contrats pour le mois %s",
                    bailleur.get_nom_complet(),
                    proprietes_louees.count(),
                    formater_mois_francais(mois_recap))
        
        proprietes_avec_statut = []
        total_proprietes = 0
        total_reglees = 0
        total_en_retard = 0
        
        for propriete in proprietes_louees:
            # Récupérer TOUS les contrats actifs et non résiliés qui couvrent ce mois
            # (même logique que RecapMensuel.get_proprietes_details pour la cohérence)
            contrats_actifs = propriete.contrats.filter(
                est_actif=True,
                est_resilie=False,
                date_debut__lte=mois_fin
            ).filter(
                Q(date_fin__gte=mois_debut) | Q(date_fin__isnull=True)
            ).select_related('locataire').order_by('-date_debut')
            
            # Si aucun contrat ne couvre exactement ce mois, récupérer les contrats récents
            if not contrats_actifs.exists():
                contrats_actifs = propriete.contrats.filter(
                    est_resilie=False,
                    date_debut__lte=mois_fin
                ).select_related('locataire').order_by('-date_debut')
            
            # Si toujours rien, passer à la propriété suivante
            if not contrats_actifs.exists():
                logger.debug("Propriété %s: aucun contrat trouvé", propriete.titre or propriete.adresse)
                continue
            
            # Traiter TOUS les contrats (pour cohérence avec RecapMensuel)
            for contrat_actif in contrats_actifs:
                # Vérifier si le contrat couvre vraiment ce mois spécifique
                contrat_couvre_mois = (
                    contrat_actif.date_debut <= mois_fin and
                    (contrat_actif.date_fin is None or contrat_actif.date_fin >= mois_debut)
                )
                
                # Log pour déboguer
                logger.debug("Propriété %s: contrat %s - début: %s, fin: %s, couvre mois: %s, actif: %s",
                            propriete.titre or propriete.adresse,
                            contrat_actif.numero_contrat,
                            contrat_actif.date_debut,
                            contrat_actif.date_fin,
                            contrat_couvre_mois,
                            contrat_actif.est_actif)
                
                # Vérifier si le loyer du mois est payé (seulement si le contrat couvre le mois)
                if contrat_couvre_mois:
                    statut_paiement = ServiceRecapPaiementMensuel._verifier_statut_paiement(
                        contrat_actif, mois_debut, mois_fin
                    )
                else:
                    # Si le contrat ne couvre pas le mois, marquer comme non applicable
                    date_debut_str = contrat_actif.date_debut.strftime("%d/%m/%Y") if contrat_actif.date_debut else "N/A"
                    if contrat_actif.date_fin:
                        date_fin_str = contrat_actif.date_fin.strftime("%d/%m/%Y")
                    else:
                        date_fin_str = "Indéfini"
                    
                    statut_paiement = {
                        'statut': 'non_applicable',
                        'statut_display': 'NON APPLICABLE',
                        'montant_paye': Decimal('0'),
                        'montant_attendu': Decimal('0'),
                        'details': f'Contrat du {date_debut_str} au {date_fin_str}'
                    }
                
                # Trouver le dernier mois réellement réglé en base pour ce contrat
                try:
                    dernier_mois_regle = ServiceRecapPaiementMensuel._get_dernier_mois_regle(contrat_actif)
                    dernier_mois_regle_display = formater_mois_francais(dernier_mois_regle) if dernier_mois_regle else "Aucun"
                except Exception as e:
                    logger.warning(f"Erreur _get_dernier_mois_regle contrat {contrat_actif.id}: {e}")
                    dernier_mois_regle = None
                    dernier_mois_regle_display = "Aucun"

                # Préparer les données de la propriété avec tous les détails du contrat
                donnees_propriete = {
                    'propriete': propriete,
                    'contrat': contrat_actif,
                    'locataire': contrat_actif.locataire,
                    'numero_contrat': contrat_actif.numero_contrat,
                    'date_debut_contrat': contrat_actif.date_debut,
                    'date_fin_contrat': contrat_actif.date_fin,
                    'loyer_mensuel': contrat_actif.loyer_mensuel or Decimal('0'),
                    'charges_mensuelles': contrat_actif.charges_mensuelles or Decimal('0'),
                    'contrat_est_actif': contrat_actif.est_actif,
                    'contrat_couvre_mois': contrat_couvre_mois,
                    'statut': statut_paiement['statut'],
                    'statut_display': statut_paiement['statut_display'],
                    'montant_paye': statut_paiement['montant_paye'],
                    'montant_attendu': statut_paiement['montant_attendu'],
                    'date_paiement': statut_paiement.get('date_paiement'),
                    'details_paiement': statut_paiement.get('details', ''),
                    'dernier_mois_regle': dernier_mois_regle,
                    'dernier_mois_regle_display': dernier_mois_regle_display,
                }
                
                proprietes_avec_statut.append(donnees_propriete)
                
                # Compter seulement si le contrat couvre vraiment le mois
                if contrat_couvre_mois:
                    total_proprietes += 1
                    if statut_paiement['statut'] == 'regle':
                        total_reglees += 1
                    elif statut_paiement['statut'] == 'en_retard':
                        total_en_retard += 1
        
        # Trier par statut (en retard en premier, puis réglées)
        proprietes_avec_statut.sort(key=lambda x: (x['statut'] == 'regle', x['propriete'].titre or ''))
        
        # Préparer le récapitulatif global
        recap_data = {
            'bailleur': bailleur,
            'mois_recap': mois_recap,
            'mois_debut': mois_debut,
            'mois_fin': mois_fin,
            'mois_display': formater_mois_francais(mois_recap),  # Format français garanti
            'proprietes': proprietes_avec_statut,
            'total_proprietes': total_proprietes,
            'total_reglees': total_reglees,
            'total_en_retard': total_en_retard,
            'date_generation': timezone.now(),
        }
        
        return recap_data
    
    @staticmethod
    def _verifier_statut_paiement(contrat, mois_debut, mois_fin):
        """
        Vérifie le statut de paiement du loyer pour un contrat donné.

        Logique simplifiée ancrée sur le DERNIER MOIS RÉGLÉ en base :
        - RÉGLÉ   : le mois de référence est couvert dans mois_payes
        - EN RETARD : retard = (dernier_mois_réglé + 1) → mois_debut (aujourd'hui)
                      Pas de recherche de trous dans l'historique ; on part du dernier
                      mois effectivement payé pour calculer les mois en souffrance.
        """
        loyer_mensuel = contrat.loyer_mensuel or Decimal('0')
        if loyer_mensuel <= 0:
            return {
                'statut': 'non_applicable',
                'statut_display': 'NON APPLICABLE',
                'montant_paye': Decimal('0'),
                'montant_attendu': Decimal('0'),
                'details': 'Loyer mensuel non défini',
                'nombre_mois_retard': 0,
                'mois_en_retard': [],
            }

        # 1. Récupérer tous les paiements validés
        tous_paiements = list(Paiement.objects.filter(
            contrat=contrat,
            statut='valide'
        ).filter(
            Q(type_paiement='loyer') |
            Q(type_paiement='paiement_partiel') |
            Q(type_paiement='avance')
        ).order_by('date_paiement'))

        # 2. Construire l'ensemble des mois couverts par les paiements
        mois_payes, montant_restant_seq = ServiceRecapPaiementMensuel._construire_mois_payes(
            contrat, tous_paiements, mois_fin, loyer_mensuel, retourner_montant_restant=True
        )

        # L'ancre est le DERNIER MOIS PAYÉ en base, sans restriction de date de début
        # de contrat. La date_debut sert uniquement de repli lorsqu'aucun paiement n'existe.
        mois_debut_contrat = contrat.date_debut.replace(day=1)
        mois_payes_valides = mois_payes  # tous les mois couverts, peu importe l'année

        mois_ref_key = (mois_debut.year, mois_debut.month)
        dernier_paiement_utilise = tous_paiements[-1] if tous_paiements else None

        # ── RÉGLÉ : le mois de référence est couvert ──────────────────────────
        if mois_ref_key in mois_payes_valides:
            montant_total_paye = loyer_mensuel
            details_parts = []
            if dernier_paiement_utilise:
                montant_ref = (
                    dernier_paiement_utilise.montant_net_paye or
                    dernier_paiement_utilise.montant or Decimal('0')
                )
                if montant_ref >= loyer_mensuel:
                    nb_mois = int(montant_ref // loyer_mensuel)
                    if nb_mois > 1:
                        details_parts.append(f'Avance de {nb_mois} mois ({montant_ref:.0f} F CFA)')
            details = f'Loyer payé ({montant_total_paye:.0f} F CFA)'
            if details_parts:
                details += ' - ' + ' '.join(details_parts)
            return {
                'statut': 'regle',
                'statut_display': 'RÉGLÉ',
                'montant_paye': montant_total_paye,
                'montant_attendu': loyer_mensuel,
                'date_paiement': dernier_paiement_utilise.date_paiement if dernier_paiement_utilise else None,
                'details': details,
                'nombre_mois_retard': 0,
                'mois_en_retard': [],
            }

        # ── EN RETARD ──────────────────────────────────────────────────────────
        # Ancre = dernier mois réglé en base. Le retard commence au mois suivant.
        # Pas de recherche de trous ; les mois entre l'ancre et aujourd'hui sont tous en retard.
        total_paye_global = sum(
            p.montant_net_paye or p.montant or Decimal('0')
            for p in tous_paiements
        )

        if mois_payes_valides:
            dernier_key = max(mois_payes_valides)
            mois_depuis = datetime.date(dernier_key[0], dernier_key[1], 1) + relativedelta(months=1)
        else:
            # Aucun paiement valide : retard depuis le début du contrat
            mois_depuis = mois_debut_contrat

        mois_en_retard = []
        mois_iter = mois_depuis
        while mois_iter <= mois_debut:
            mois_en_retard.append(mois_iter)
            mois_iter = mois_iter + relativedelta(months=1)

        # Détecter les paiements partiels sur les mois en retard
        from .services_paiement_partiel import ServicePaiementPartiel
        montant_partiel_par_mois = {}
        for p in tous_paiements:
            if p.mois_paye:
                d = ServicePaiementPartiel.convertir_mois_paye_en_date(p.mois_paye)
                if d:
                    key = (d.year, d.month)
                    montant_partiel_par_mois[key] = montant_partiel_par_mois.get(key, Decimal('0')) + (p.montant_net_paye or p.montant or Decimal('0'))

        mois_liste_str = []
        for m in mois_en_retard:
            key = (m.year, m.month)
            label = formater_mois_francais(m)
            partiel = montant_partiel_par_mois.get(key, Decimal('0'))
            if Decimal('0') < partiel < loyer_mensuel:
                label += f" (partiel: {partiel:.0f} F)"
            mois_liste_str.append(label)
        nombre_mois_retard = len(mois_en_retard)
        montant_total_du_retard = nombre_mois_retard * loyer_mensuel
        montant_manquant = max(Decimal('0'), montant_total_du_retard - montant_restant_seq)

        if nombre_mois_retard > 0:
            details_retard = f'Retard de {nombre_mois_retard} mois'
            if mois_liste_str:
                details_retard += f' : {", ".join(mois_liste_str)}'
            details_retard += f' - Manque {montant_manquant:.0f} F CFA sur {montant_total_du_retard:.0f} F CFA'
        else:
            details_retard = f'Manque {montant_manquant:.0f} F CFA sur {loyer_mensuel:.0f} F CFA'

        return {
            'statut': 'en_retard',
            'statut_display': 'EN RETARD',
            'montant_paye': total_paye_global,
            'montant_attendu': loyer_mensuel,
            'montant_manquant': montant_manquant,
            'nombre_mois_retard': nombre_mois_retard,
            'mois_en_retard': mois_liste_str,
            'details': details_retard,
        }
    
    @staticmethod
    def _avance_couvre_mois(avance_paiement, mois_debut):
        """
        Vérifie si une avance de loyer couvre le mois donné.
        CORRIGÉ : Utilise le système centralisé AvanceLoyer au lieu de recalculer.
        
        Args:
            avance_paiement: Instance de Paiement de type 'avance' (LEGACY - non utilisé maintenant)
            mois_debut: Date de début du mois à vérifier
        
        Returns:
            bool: True si l'avance couvre le mois
        """
        # CORRECTION MAJEURE : Utiliser le système d'avances centralisé (AvanceLoyer)
        # au lieu de recalculer manuellement les mois couverts
        from .services_avance import ServiceGestionAvance
        
        try:
            # Vérifier si le mois est couvert par une avance active dans le système AvanceLoyer
            contrat = avance_paiement.contrat
            return ServiceGestionAvance.verifier_mois_couvert_par_avance(contrat, mois_debut)
        except Exception as e:
            # En cas d'erreur, fallback sur l'ancienne logique (pour compatibilité)
            # Calculer le dernier mois payé avec les paiements précédents
            dernier_mois_paiement = ServiceRecapPaiementMensuel._get_dernier_mois_paiement_avance(
                avance_paiement.contrat, avance_paiement.date_paiement
            )
            
            if not dernier_mois_paiement:
                # Si pas de paiement précédent, l'avance commence au mois suivant la date de paiement
                mois_couvert_debut = avance_paiement.date_paiement.replace(day=1) + relativedelta(months=1)
            else:
                # L'avance commence au mois suivant le dernier paiement
                mois_couvert_debut = dernier_mois_paiement + relativedelta(months=1)
            
            # Calculer le nombre de mois couverts par l'avance
            loyer_mensuel = avance_paiement.contrat.loyer_mensuel or Decimal('0')
            if loyer_mensuel <= 0:
                return False
            
            # Utiliser montant_net_paye ou montant
            montant_avance = avance_paiement.montant_net_paye or avance_paiement.montant or Decimal('0')
            nombre_mois = int(montant_avance // loyer_mensuel)
            
            if nombre_mois <= 0:
                return False
            
            mois_couvert_fin = mois_couvert_debut + relativedelta(months=nombre_mois - 1)
            
            # Vérifier si le mois donné est dans la plage couverte
            return mois_debut >= mois_couvert_debut and mois_debut <= mois_couvert_fin
    
    @staticmethod
    def _get_dernier_mois_paiement_avance(contrat, date_reference):
        """
        Récupère le dernier mois de paiement (dernière quittance de loyer)
        avant une date de référence.
        
        Args:
            contrat: Instance de Contrat
            date_reference: Date de référence
        
        Returns:
            date: Date du dernier mois payé (premier jour du mois) ou None
        """
        dernier_paiement_loyer = Paiement.objects.filter(
            contrat=contrat,
            statut='valide',
            type_paiement='loyer',
            date_paiement__lt=date_reference
        ).order_by('-date_paiement').first()
        
        if dernier_paiement_loyer:
            return dernier_paiement_loyer.date_paiement.replace(day=1)
        
        return None
    
    @staticmethod
    def _construire_mois_payes(contrat, tous_paiements, mois_fin_ref, loyer_mensuel, retourner_montant_restant=False):
        """
        Construit l'ensemble des mois payés pour un contrat.
        - mois_paye (champ) = mois de loyer couvert par le paiement
        - date_paiement = date d'encaissement (ordre chronologique uniquement, pas d'attribution)
        Utilise mois_paye quand disponible pour l'attribution, sinon application séquentielle.
        
        Args:
            retourner_montant_restant: Si True, retourne (mois_payes, montant_restant)
        
        Returns:
            set ou tuple: Ensemble des mois payés, ou (mois_payes, montant_restant) si retourner_montant_restant
        """
        from .services_paiement_partiel import ServicePaiementPartiel
        
        mois_debut_contrat = contrat.date_debut.replace(day=1)
        mois_payes = set()
        montant_par_mois = {}  # (year, month) -> Decimal
        
        # 1. Paiements avec mois_paye explicite : attribuer au mois indiqué
        # Utilise loyer_mensuel directement comme montant dû (pas de calculer_montant_du_mois
        # qui déclenche des écritures DB via consommer_avance_pour_mois — opération READ-ONLY ici).
        for paiement in tous_paiements:
            if not paiement.mois_paye:
                continue
            date_mois = ServicePaiementPartiel.convertir_mois_paye_en_date(paiement.mois_paye)
            if not date_mois or date_mois > mois_fin_ref:
                continue
            montant_paye = paiement.montant_net_paye or paiement.montant or Decimal('0')
            key = (date_mois.year, date_mois.month)
            montant_par_mois[key] = montant_par_mois.get(key, Decimal('0')) + montant_paye
            if montant_par_mois[key] >= loyer_mensuel:
                mois_payes.add(key)
        
        # 2. Paiements sans mois_paye : application séquentielle
        mois_courant = mois_debut_contrat
        montant_restant = Decimal('0')
        for paiement in tous_paiements:
            if paiement.mois_paye:
                continue
            montant_paiement = paiement.montant_net_paye or paiement.montant or Decimal('0')
            montant_total = montant_restant + montant_paiement
            while montant_total >= loyer_mensuel and mois_courant <= mois_fin_ref:
                key = (mois_courant.year, mois_courant.month)
                if key not in mois_payes:
                    mois_payes.add(key)
                montant_total -= loyer_mensuel
                mois_courant = mois_courant + relativedelta(months=1)
            montant_restant = montant_total
        
        if retourner_montant_restant:
            return mois_payes, montant_restant
        return mois_payes
    
    @staticmethod
    def _calculer_mois_retard(contrat, mois_reference):
        """
        Calcule le nombre de mois de retard pour un contrat donné.
        Remonte depuis le mois de référence pour compter les mois consécutifs non payés.
        
        Args:
            contrat: Instance de Contrat
            mois_reference: Date du mois de référence (premier jour du mois)
        
        Returns:
            int: Nombre de mois de retard (0 si à jour)
        """
        loyer_mensuel = contrat.loyer_mensuel or Decimal('0')
        if loyer_mensuel <= 0:
            return 0
        
        # Calculer les dates du mois de référence
        if mois_reference.month == 12:
            mois_fin_ref = mois_reference.replace(year=mois_reference.year + 1, month=1, day=1) - relativedelta(days=1)
        else:
            mois_fin_ref = mois_reference.replace(month=mois_reference.month + 1, day=1) - relativedelta(days=1)
        
        # Récupérer tous les paiements validés
        tous_paiements = Paiement.objects.filter(
            contrat=contrat,
            statut='valide'
        ).filter(
            Q(type_paiement='loyer') | 
            Q(type_paiement='paiement_partiel') |
            Q(type_paiement='avance')
        ).order_by('date_paiement')
        
        # Construire mois_payes en tenant compte de mois_paye quand disponible
        mois_payes = ServiceRecapPaiementMensuel._construire_mois_payes(
            contrat, tous_paiements, mois_fin_ref, loyer_mensuel
        )
        
        # Borne inférieure : ne pas remonter avant le début du contrat
        mois_debut_contrat = contrat.date_debut.replace(day=1)

        # Compter les mois de retard consécutifs en remontant depuis le mois de référence
        mois_retard = 0
        mois_verifie = mois_reference

        while mois_verifie >= mois_debut_contrat:
            # Vérifier si ce mois est payé
            mois_key = (mois_verifie.year, mois_verifie.month)
            
            # Vérifier si le contrat couvre ce mois
            if mois_verifie < mois_debut_contrat:
                break
            
            if contrat.date_fin:
                mois_fin_contrat = contrat.date_fin.replace(day=1)
                if mois_verifie > mois_fin_contrat:
                    break
            
            # Si le mois n'est pas payé, c'est un mois de retard
            if mois_key not in mois_payes:
                mois_retard += 1
            else:
                # Si on trouve un mois payé, on arrête (les mois précédents sont réglés)
                break
            
            # Remonter au mois précédent
            if mois_verifie.month == 1:
                mois_verifie = mois_verifie.replace(year=mois_verifie.year - 1, month=12, day=1)
            else:
                mois_verifie = mois_verifie.replace(month=mois_verifie.month - 1, day=1)
        
        return mois_retard
    
    @staticmethod
    def _get_dernier_mois_regle(contrat):
        """
        Trouve le dernier mois effectivement réglé en base pour un contrat donné.
        Opération READ-ONLY : aucune écriture DB (pas de consommer_avance_pour_mois).

        Logique :
        - Paiements avec mois_paye explicite → max(dates converties)
        - Paiements sans mois_paye → affectation séquentielle simple (loyer_mensuel)
        Le dernier mois réglé est le max des deux résultats.

        Returns:
            date | None: Premier jour du dernier mois réglé, ou None si aucun paiement.
        """
        from .services_paiement_partiel import ServicePaiementPartiel

        loyer_mensuel = contrat.loyer_mensuel or Decimal('0')
        if loyer_mensuel <= 0:
            return None

        filtre_type = Q(type_paiement='loyer') | Q(type_paiement='paiement_partiel') | Q(type_paiement='avance')

        # ── 1. Paiements avec mois_paye explicite ────────────────────────────
        # On vérifie que le total cumulé pour ce mois >= loyer_mensuel,
        # exactement comme _construire_mois_payes, pour garantir la cohérence.
        montant_par_mois_explicite = {}
        paiements_avec = Paiement.objects.filter(
            contrat=contrat, statut='valide'
        ).filter(filtre_type).exclude(
            Q(mois_paye='') | Q(mois_paye__isnull=True)
        ).values_list('mois_paye', 'montant_net_paye', 'montant')

        for mois_paye_str, montant_net, montant_brut in paiements_avec:
            d = ServicePaiementPartiel.convertir_mois_paye_en_date(mois_paye_str)
            if d:
                m = montant_net or montant_brut or Decimal('0')
                key = (d.year, d.month)
                montant_par_mois_explicite[key] = montant_par_mois_explicite.get(key, Decimal('0')) + m

        dernier_avec_mois = None
        for (y, mo), total in montant_par_mois_explicite.items():
            if total >= loyer_mensuel:
                d = datetime.date(y, mo, 1)
                if dernier_avec_mois is None or d > dernier_avec_mois:
                    dernier_avec_mois = d

        # ── 2. Paiements sans mois_paye : séquentiel READ-ONLY ───────────────
        paiements_sans = list(Paiement.objects.filter(
            contrat=contrat, statut='valide'
        ).filter(filtre_type).filter(
            Q(mois_paye='') | Q(mois_paye__isnull=True)
        ).order_by('date_paiement'))

        dernier_sequentiel = None
        if paiements_sans:
            mois_courant = contrat.date_debut.replace(day=1)
            montant_cumule = Decimal('0')
            for paiement in paiements_sans:
                montant = paiement.montant_net_paye or paiement.montant or Decimal('0')
                montant_cumule += montant
                while montant_cumule >= loyer_mensuel:
                    dernier_sequentiel = mois_courant
                    montant_cumule -= loyer_mensuel
                    mois_courant = mois_courant + relativedelta(months=1)

        candidats = [d for d in [dernier_avec_mois, dernier_sequentiel] if d is not None]
        return max(candidats) if candidats else None

    @staticmethod
    def preparer_donnees_recap_locataires(bailleur, mois_recap):
        """
        Prépare les données pour le récapitulatif de paiement mensuel par locataire.
        Pour un bailleur donné, liste tous ses locataires avec leur statut de paiement.
        
        Args:
            bailleur: Instance de Bailleur
            mois_recap: Date du mois à récapituler (premier jour du mois)
        
        Returns:
            dict: Dictionnaire contenant toutes les données pour le récapitulatif par locataire
        """
        # Calculer les dates de début et fin du mois
        mois_debut = mois_recap.replace(day=1)
        if mois_recap.month == 12:
            mois_fin = mois_recap.replace(year=mois_recap.year + 1, month=1, day=1) - relativedelta(days=1)
        else:
            mois_fin = mois_recap.replace(month=mois_recap.month + 1, day=1) - relativedelta(days=1)
        
        # Récupérer tous les contrats actifs du bailleur pour ce mois
        contrats_actifs_qs = Contrat.objects.filter(
            propriete__bailleur=bailleur,
            propriete__is_deleted=False,
            est_actif=True,
            est_resilie=False,
            date_debut__lte=mois_fin
        ).filter(
            Q(date_fin__gte=mois_debut) | Q(date_fin__isnull=True)
        ).select_related('locataire', 'propriete').order_by('locataire__nom', 'locataire__prenom')
        
        # FORCER la conversion en liste Python standard pour éviter NotImplementedType
        # Évaluer le QuerySet immédiatement
        contrats_actifs = []
        try:
            # Forcer l'évaluation du QuerySet en itérant explicitement
            for contrat in contrats_actifs_qs:
                # S'assurer que tous les attributs sont accessibles
                try:
                    _ = contrat.id
                    _ = contrat.locataire
                    _ = contrat.propriete
                    contrats_actifs.append(contrat)
                except Exception as e:
                    logger.warning(f"Erreur lors de l'accès aux attributs du contrat {contrat.pk}: {e}")
                    continue
        except Exception as e:
            logger.error(f"Erreur lors de la conversion des contrats en liste: {e}", exc_info=True)
            contrats_actifs = []
        
        # Grouper par locataire
        locataires_dict = {}
        total_locataires = 0
        total_reglees = 0
        total_en_retard = 0
        
        for contrat in contrats_actifs:
            locataire = contrat.locataire
            if not locataire:
                continue
            
            # Vérifier si le contrat couvre ce mois
            contrat_couvre_mois = (
                contrat.date_debut <= mois_fin and
                (contrat.date_fin is None or contrat.date_fin >= mois_debut)
            )
            
            # Obtenir le statut de paiement
            if contrat_couvre_mois:
                statut_paiement = ServiceRecapPaiementMensuel._verifier_statut_paiement(
                    contrat, mois_debut, mois_fin
                )
            else:
                date_debut_str = contrat.date_debut.strftime("%d/%m/%Y") if contrat.date_debut else "N/A"
                date_fin_str = contrat.date_fin.strftime("%d/%m/%Y") if contrat.date_fin else "Indéfini"
                statut_paiement = {
                    'statut': 'non_applicable',
                    'statut_display': 'NON APPLICABLE',
                    'montant_paye': Decimal('0'),
                    'montant_attendu': Decimal('0'),
                    'details': f'Contrat du {date_debut_str} au {date_fin_str}'
                }
            
            # Créer ou mettre à jour l'entrée du locataire
            # Utiliser nombre_mois_retard de statut_paiement (même source que les détails)
            # pour garantir la cohérence entre badge et texte.
            mois_retard_statut = statut_paiement.get('nombre_mois_retard', 0) if contrat_couvre_mois else 0

            if locataire.id not in locataires_dict:
                locataires_dict[locataire.id] = {
                    'locataire_id': locataire.id,
                    'locataire_nom': locataire.get_nom_complet() if hasattr(locataire, 'get_nom_complet') else f"{locataire.nom or ''} {locataire.prenom or ''}".strip(),
                    'locataire_numero': (locataire.numero_locataire or str(locataire.id).zfill(4))[:30],
                    'locataire_telephone': (locataire.telephone or '')[:20],
                    'contrats': [],
                    'statut_global': statut_paiement['statut'],
                    'statut_global_display': statut_paiement['statut_display'],
                    'total_montant_paye': Decimal('0'),
                    'total_montant_attendu': Decimal('0'),
                    'mois_retard_global': mois_retard_statut,
                }
            else:
                # Garder le pire retard (le plus grand nombre de mois)
                if mois_retard_statut > locataires_dict[locataire.id].get('mois_retard_global', 0):
                    locataires_dict[locataire.id]['mois_retard_global'] = mois_retard_statut
            
            # Ajouter le contrat - S'assurer que tous les attributs sont des valeurs Python simples
            # Tronquer les chaînes longues pour éviter les problèmes de mémoire lors de la génération PDF
            try:
                numero_contrat = str(contrat.numero_contrat) if contrat.numero_contrat else "N/A"
                if len(numero_contrat) > 20:
                    numero_contrat = numero_contrat[:20] + "..."
                
                date_debut_contrat = contrat.date_debut if contrat.date_debut else None
                date_fin_contrat = contrat.date_fin if contrat.date_fin else None
                loyer_mensuel = Decimal(str(contrat.loyer_mensuel)) if contrat.loyer_mensuel else Decimal('0')
                charges_mensuelles = Decimal(str(contrat.charges_mensuelles)) if contrat.charges_mensuelles else Decimal('0')
                
                # Tronquer les détails de paiement (PDF Render: limite mémoire)
                details_paiement = str(statut_paiement.get('details', ''))
                if len(details_paiement) > 80:
                    details_paiement = details_paiement[:80] + "..."
                
                # Tronquer les adresses et titres de propriété
                propriete_titre = contrat.propriete.titre if contrat.propriete and contrat.propriete.titre else "Sans titre"
                if len(propriete_titre) > 50:
                    propriete_titre = propriete_titre[:50] + "..."
                
                propriete_adresse = contrat.propriete.adresse if contrat.propriete and contrat.propriete.adresse else "Non renseignée"
                if len(propriete_adresse) > 60:
                    propriete_adresse = propriete_adresse[:60] + "..."
                propriete_ville = (contrat.propriete.ville or "")[:20] if contrat.propriete else ""
                
                # Utiliser nombre_mois_retard de statut_paiement (cohérent avec les détails)
                mois_retard = statut_paiement.get('nombre_mois_retard', 0) if contrat_couvre_mois else 0

                # Trouver le dernier mois réellement réglé en base pour ce contrat
                try:
                    dernier_mois_regle = ServiceRecapPaiementMensuel._get_dernier_mois_regle(contrat)
                    dernier_mois_regle_display = formater_mois_francais(dernier_mois_regle) if dernier_mois_regle else "Aucun"
                except Exception as e:
                    logger.warning(f"Erreur _get_dernier_mois_regle contrat {contrat.id}: {e}")
                    dernier_mois_regle = None
                    dernier_mois_regle_display = "Aucun"

                # Créer un dictionnaire avec valeurs primitives uniquement (évite OOM PDF sur Render)
                contrat_dict = {
                    'contrat_id': contrat.id,
                    'propriete_id': contrat.propriete.id if contrat.propriete else None,
                    'numero_contrat': numero_contrat,
                    'date_debut_contrat': date_debut_contrat,
                    'date_fin_contrat': date_fin_contrat,
                    'statut': str(statut_paiement['statut']),
                    'statut_display': str(statut_paiement['statut_display']),
                    'montant_paye': Decimal(str(statut_paiement['montant_paye'])),
                    'montant_attendu': Decimal(str(statut_paiement['montant_attendu'])),
                    'date_paiement': statut_paiement.get('date_paiement'),
                    'details_paiement': details_paiement,
                    'loyer_mensuel': loyer_mensuel,
                    'charges_mensuelles': charges_mensuelles,
                    'propriete_titre_truncated': propriete_titre,
                    'propriete_adresse_truncated': propriete_adresse,
                    'propriete_ville': propriete_ville,
                    'mois_retard': mois_retard,
                    'dernier_mois_regle': dernier_mois_regle,
                    'dernier_mois_regle_display': dernier_mois_regle_display,
                }
                locataires_dict[locataire.id]['contrats'].append(contrat_dict)
            except Exception as e:
                logger.error(f"Erreur lors de la création du dictionnaire de contrat: {e}", exc_info=True)
                continue
            
            # Mettre à jour les totaux du locataire
            locataires_dict[locataire.id]['total_montant_paye'] += statut_paiement['montant_paye']
            locataires_dict[locataire.id]['total_montant_attendu'] += statut_paiement['montant_attendu']
            
            # Mettre à jour le statut global (le pire statut)
            if statut_paiement['statut'] == 'en_retard':
                locataires_dict[locataire.id]['statut_global'] = 'en_retard'
                locataires_dict[locataire.id]['statut_global_display'] = 'EN RETARD'
            elif statut_paiement['statut'] == 'regle' and locataires_dict[locataire.id]['statut_global'] != 'en_retard':
                locataires_dict[locataire.id]['statut_global'] = 'regle'
                locataires_dict[locataire.id]['statut_global_display'] = 'RÉGLÉ'
        
        # Convertir en liste et compter - FORCER en liste Python standard
        try:
            locataires_avec_statut = list(locataires_dict.values())
        except (TypeError, AttributeError) as e:
            logger.error(f"Erreur lors de la conversion des locataires en liste: {e}")
            locataires_avec_statut = []
        
        # S'assurer que chaque locataire a une liste de contrats
        for locataire_data in locataires_avec_statut:
            if 'contrats' not in locataire_data:
                locataire_data['contrats'] = []
            elif not isinstance(locataire_data['contrats'], list):
                try:
                    locataire_data['contrats'] = list(locataire_data['contrats'])
                except (TypeError, AttributeError):
                    locataire_data['contrats'] = []
        
        for locataire_data in locataires_avec_statut:
            # Compter seulement si au moins un contrat couvre le mois
            a_contrat_couvrant_mois = any(
                c.get('statut') != 'non_applicable' for c in locataire_data.get('contrats', [])
            )
            
            if a_contrat_couvrant_mois:
                total_locataires += 1
                if locataire_data['statut_global'] == 'regle':
                    total_reglees += 1
                elif locataire_data['statut_global'] == 'en_retard':
                    total_en_retard += 1
        
        # Tronquer les codes locataires pour éviter les problèmes de mémoire
        for locataire_data in locataires_avec_statut:
            locataire = locataire_data.get('locataire')
            if locataire:
                # Tronquer le numéro locataire si trop long
                if hasattr(locataire, 'numero_locataire') and locataire.numero_locataire:
                    numero_loc = str(locataire.numero_locataire)
                    if len(numero_loc) > 30:
                        # Garder les 15 premiers et 15 derniers caractères
                        locataire.numero_locataire = numero_loc[:15] + "..." + numero_loc[-12:]
        
        # Trier par statut (en retard en premier, puis réglés), puis par nom
        # S'assurer que tous les champs existent avant de trier
        try:
            locataires_avec_statut.sort(key=lambda x: (
                x.get('statut_global', '') != 'en_retard',  # En retard en premier
                x.get('statut_global', '') == 'regle',  # Puis réglés
                getattr(x.get('locataire'), 'nom', '') or '',
                getattr(x.get('locataire'), 'prenom', '') or ''
            ))
        except Exception as e:
            logger.error(f"Erreur lors du tri des locataires: {e}")
            # Si le tri échoue, on garde l'ordre original
        
        # Préparer le récapitulatif global
        recap_data = {
            'bailleur': bailleur,
            'mois_recap': mois_recap,
            'mois_debut': mois_debut,
            'mois_fin': mois_fin,
            'mois_display': formater_mois_francais(mois_recap),
            'locataires': locataires_avec_statut,
            'total_locataires': total_locataires,
            'total_reglees': total_reglees,
            'total_en_retard': total_en_retard,
            'date_generation': timezone.now(),
        }
        
        return recap_data

