"""
Commande Django pour recalculer la commission agence et le montant réellement payé
pour tous les récapitulatifs mensuels existants.
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from paiements.models import RecapMensuel
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Recalcule la commission agence (10%) et le montant réellement payé pour tous les récapitulatifs mensuels'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force le recalcul même si les valeurs existent déjà',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Affiche ce qui serait fait sans faire de modifications',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        force = options['force']
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('Mode DRY-RUN : aucune modification ne sera effectuée'))
        
        # Récupérer tous les récapitulatifs (même supprimés logiquement pour les recalculer)
        recaps = RecapMensuel.objects.all().select_related('bailleur')
        total = recaps.count()
        
        self.stdout.write(f'\n📊 {total} récapitulatif(s) mensuel(s) trouvé(s)')
        
        updated_count = 0
        skipped_count = 0
        error_count = 0
        
        for recap in recaps:
            try:
                # Vérifier si on doit recalculer
                if not force and recap.commission_agence and recap.commission_agence > 0:
                    # Déjà calculé, vérifier si c'est correct
                    expected_commission = recap.total_net_a_payer * Decimal('0.10')
                    if abs(recap.commission_agence - expected_commission) < Decimal('0.01'):
                        skipped_count += 1
                        continue
                
                # Recalculer tous les totaux avec la nouvelle logique
                if not dry_run:
                    totaux = recap.calculer_totaux_bailleur()
                    
                    # Vérifier que la commission a été calculée
                    if 'commission_agence' in totaux:
                        recap.commission_agence = totaux['commission_agence']
                        recap.montant_reellement_paye = totaux['montant_reellement_paye']
                        recap.save(update_fields=['commission_agence', 'montant_reellement_paye', 
                                                  'total_loyers_bruts', 'total_charges_deductibles',
                                                  'total_charges_bailleur', 'total_net_a_payer'])
                    else:
                        # Fallback : calculer manuellement
                        commission_agence = recap.total_net_a_payer * Decimal('0.10')
                        montant_reellement_paye = max(recap.total_net_a_payer - commission_agence, Decimal('0'))
                        recap.commission_agence = commission_agence
                        recap.montant_reellement_paye = montant_reellement_paye
                        recap.save(update_fields=['commission_agence', 'montant_reellement_paye'])
                
                updated_count += 1
                
                if updated_count % 10 == 0:
                    self.stdout.write(f'  ✓ {updated_count}/{total} récapitulatifs traités...')
                
            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(
                        f'  ✗ Erreur pour le récapitulatif {recap.id}: {str(e)}'
                    )
                )
                logger.error(f"Erreur lors du recalcul du récapitulatif {recap.id}: {str(e)}", exc_info=True)
        
        # Résumé
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS(f'✅ {updated_count} récapitulatif(s) mis à jour'))
        if skipped_count > 0:
            self.stdout.write(self.style.WARNING(f'⏭️  {skipped_count} récapitulatif(s) ignoré(s) (déjà à jour)'))
        if error_count > 0:
            self.stdout.write(self.style.ERROR(f'❌ {error_count} erreur(s)'))
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\n⚠️  Mode DRY-RUN : aucune modification n\'a été effectuée'))
            self.stdout.write('   Relancez la commande sans --dry-run pour appliquer les modifications')
        else:
            self.stdout.write(self.style.SUCCESS('\n✅ Mise à jour terminée !'))

