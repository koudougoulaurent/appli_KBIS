"""
Commande de gestion pour recalculer tous les récapitulatifs mensuels
en prenant en compte les charges bailleur
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal
from paiements.models import RecapMensuel
from proprietes.models import ChargesBailleur
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Recalcule tous les récapitulatifs mensuels pour intégrer les charges bailleur'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Affiche les modifications sans les sauvegarder',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force la mise à jour même si les charges sont déjà présentes',
        )
        parser.add_argument(
            '--annee',
            type=int,
            help='Ne recalculer que les récaps d\'une année spécifique',
        )
        parser.add_argument(
            '--mois',
            type=int,
            help='Ne recalculer que les récaps d\'un mois spécifique (1-12)',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        force = options.get('force', False)
        annee = options.get('annee')
        mois = options.get('mois')

        self.stdout.write(self.style.SUCCESS('\n' + '='*80))
        self.stdout.write(self.style.SUCCESS('RECALCUL DES RÉCAPITULATIFS MENSUELS AVEC CHARGES BAILLEUR'))
        self.stdout.write(self.style.SUCCESS('='*80 + '\n'))

        if dry_run:
            self.stdout.write(self.style.WARNING('MODE TEST (DRY-RUN) - Aucune modification ne sera sauvegardee\n'))

        # Récupérer tous les récapitulatifs
        recaps = RecapMensuel.objects.filter(is_deleted=False).order_by('mois_recap')
        
        # Filtrer par année si spécifié
        if annee:
            recaps = recaps.filter(mois_recap__year=annee)
            self.stdout.write(f"Filtrage sur l'annee {annee}")
        
        # Filtrer par mois si spécifié
        if mois:
            recaps = recaps.filter(mois_recap__month=mois)
            self.stdout.write(f"Filtrage sur le mois {mois}")

        total_recaps = recaps.count()
        self.stdout.write(f"\n{total_recaps} recapitulatif(s) trouve(s)\n")

        if total_recaps == 0:
            self.stdout.write(self.style.WARNING('Aucun récapitulatif à traiter.'))
            return

        # Statistiques
        stats = {
            'total': total_recaps,
            'avec_charges': 0,
            'sans_charges': 0,
            'deja_a_jour': 0,
            'mis_a_jour': 0,
            'erreurs': 0,
            'montant_total_charges': Decimal('0'),
        }

        # Traiter chaque récapitulatif
        for index, recap in enumerate(recaps, start=1):
            self.stdout.write(f"\n{'-'*80}")
            self.stdout.write(f"[{index}/{total_recaps}] Recapitulatif #{recap.id} - {recap.bailleur.nom} - {recap.mois_recap.strftime('%B %Y')}")
            self.stdout.write(f"{'-'*80}")

            try:
                # Récupérer les charges bailleur pour ce mois
                # Utiliser les mêmes statuts que get_proprietes_details() pour cohérence
                charges_bailleur_mois = ChargesBailleur.objects.filter(
                    propriete__bailleur=recap.bailleur,
                    date_charge__year=recap.mois_recap.year,
                    date_charge__month=recap.mois_recap.month,
                    statut__in=['en_attente', 'valide']
                )

                nombre_charges = charges_bailleur_mois.count()
                
                # Calculer le total des charges
                total_charges_bailleur = Decimal('0')
                for charge in charges_bailleur_mois:
                    montant_a_deduire = getattr(charge, 'montant_restant', None) or charge.montant
                    total_charges_bailleur += montant_a_deduire

                # Afficher les informations actuelles
                self.stdout.write(f"\nEtat actuel :")
                self.stdout.write(f"   Loyers bruts : {recap.total_loyers_bruts:,.0f} F CFA")
                self.stdout.write(f"   Charges bailleur (BDD) : {recap.total_charges_bailleur:,.0f} F CFA")
                self.stdout.write(f"   Charges bailleur (calculees) : {total_charges_bailleur:,.0f} F CFA")
                self.stdout.write(f"   Nombre de charges trouvees : {nombre_charges}")

                # Vérifier si une mise à jour est nécessaire
                if not force and recap.total_charges_bailleur == total_charges_bailleur:
                    stats['deja_a_jour'] += 1
                    self.stdout.write(self.style.SUCCESS(f"   Deja a jour (charges = {total_charges_bailleur:,.0f} F)"))
                    
                    if total_charges_bailleur == 0:
                        stats['sans_charges'] += 1
                    else:
                        stats['avec_charges'] += 1
                    
                    continue

                # Recalculer les montants
                ancien_total_charges = recap.total_charges_bailleur
                ancien_net = recap.total_net_a_payer
                ancienne_commission = getattr(recap, 'commission_agence', Decimal('0'))
                ancien_montant_paye = getattr(recap, 'montant_reellement_paye', Decimal('0'))

                # Nouveau calcul
                nouveau_net = recap.total_loyers_bruts - total_charges_bailleur
                nouveau_net = max(nouveau_net, Decimal('0'))
                
                nouvelle_commission = (nouveau_net * Decimal('0.10')).quantize(Decimal('0.01'))
                nouveau_montant_paye = max(nouveau_net - nouvelle_commission, Decimal('0'))

                self.stdout.write(f"\nNouveau calcul :")
                self.stdout.write(f"   Loyers bruts : {recap.total_loyers_bruts:,.0f} F CFA")
                self.stdout.write(f"   - Charges bailleur : {total_charges_bailleur:,.0f} F CFA")
                self.stdout.write(f"   = Montant net : {nouveau_net:,.0f} F CFA")
                self.stdout.write(f"   - Commission (10%) : {nouvelle_commission:,.0f} F CFA")
                self.stdout.write(f"   = A payer au bailleur : {nouveau_montant_paye:,.0f} F CFA")

                # Afficher les différences
                diff_charges = total_charges_bailleur - ancien_total_charges
                diff_net = nouveau_net - ancien_net
                diff_commission = nouvelle_commission - ancienne_commission
                diff_paye = nouveau_montant_paye - ancien_montant_paye

                self.stdout.write(f"\nDifferences :")
                self.stdout.write(f"   Charges bailleur : {self._format_diff(diff_charges)}")
                self.stdout.write(f"   Net à payer : {self._format_diff(diff_net)}")
                self.stdout.write(f"   Commission : {self._format_diff(diff_commission)}")
                self.stdout.write(f"   Montant réellement payé : {self._format_diff(diff_paye)}")

                # Sauvegarder si pas en dry-run
                if not dry_run:
                    with transaction.atomic():
                        recap.total_charges_bailleur = total_charges_bailleur
                        recap.total_net_a_payer = nouveau_net
                        
                        if hasattr(recap, 'commission_agence'):
                            recap.commission_agence = nouvelle_commission
                        if hasattr(recap, 'montant_reellement_paye'):
                            recap.montant_reellement_paye = nouveau_montant_paye
                        
                        recap.save()
                        
                        self.stdout.write(self.style.SUCCESS(f"\n   Recapitulatif mis a jour avec succes !"))
                        stats['mis_a_jour'] += 1
                else:
                    self.stdout.write(self.style.WARNING(f"\n   MODIFICATION NON SAUVEGARDEE (dry-run)"))
                    stats['mis_a_jour'] += 1

                # Statistiques
                if total_charges_bailleur > 0:
                    stats['avec_charges'] += 1
                    stats['montant_total_charges'] += total_charges_bailleur
                else:
                    stats['sans_charges'] += 1

            except Exception as e:
                stats['erreurs'] += 1
                self.stdout.write(self.style.ERROR(f"\n   ERREUR : {str(e)}"))
                logger.error(f"Erreur lors du recalcul du recap {recap.id}: {str(e)}")
                continue

        # Afficher le résumé final
        self.stdout.write(f"\n\n{'='*80}")
        self.stdout.write(self.style.SUCCESS('RESUME DU TRAITEMENT'))
        self.stdout.write(f"{'='*80}\n")
        
        self.stdout.write(f"Total recapitulatifs traites : {stats['total']}")
        self.stdout.write(f"   - Avec charges bailleur : {stats['avec_charges']}")
        self.stdout.write(f"   - Sans charges bailleur : {stats['sans_charges']}")
        self.stdout.write(f"   - Deja a jour : {stats['deja_a_jour']}")
        self.stdout.write(self.style.SUCCESS(f"   - Mis a jour : {stats['mis_a_jour']}"))
        
        if stats['erreurs'] > 0:
            self.stdout.write(self.style.ERROR(f"   - Erreurs : {stats['erreurs']}"))
        
        if stats['montant_total_charges'] > 0:
            self.stdout.write(f"\nMontant total des charges bailleur integrees : {stats['montant_total_charges']:,.0f} F CFA")

        if dry_run and stats['mis_a_jour'] > 0:
            self.stdout.write(self.style.WARNING(f"\nPour appliquer les modifications, relancez sans --dry-run"))
        
        self.stdout.write(f"\n{'='*80}\n")
        
        if not dry_run and stats['mis_a_jour'] > 0:
            self.stdout.write(self.style.SUCCESS(f"Traitement termine avec succes !"))
        else:
            self.stdout.write(self.style.WARNING(f"Mode test - Aucune modification enregistree"))

    def _format_diff(self, diff):
        """Formate une différence avec couleur"""
        if diff > 0:
            return self.style.SUCCESS(f"+{diff:,.0f} F CFA")
        elif diff < 0:
            return self.style.ERROR(f"{diff:,.0f} F CFA")
        else:
            return "0 F CFA (inchangé)"
