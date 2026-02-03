"""
Commande Django pour forcer la consommation de toutes les avances passées
Usage: python manage.py forcer_consommation_avances [--contrat-id ID]
"""
from django.core.management.base import BaseCommand
from django.conf import settings
from paiements.models_avance import AvanceLoyer, ConsommationAvance
from paiements.services_consommation_dynamique import ServiceConsommationDynamique
from datetime import date
from dateutil.relativedelta import relativedelta


class Command(BaseCommand):
    help = 'Force la consommation automatique de toutes les avances pour les mois écoulés'

    def add_arguments(self, parser):
        parser.add_argument(
            '--contrat-id',
            type=int,
            help='ID du contrat spécifique (optionnel)',
        )
        parser.add_argument(
            '--avance-id',
            type=int,
            help='ID de l\'avance spécifique (optionnel)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simule sans sauvegarder',
        )

    def handle(self, *args, **options):
        contrat_id = options.get('contrat_id')
        avance_id = options.get('avance_id')
        dry_run = options.get('dry_run', False)
        
        self.stdout.write(self.style.SUCCESS('🔄 FORÇAGE CONSOMMATION AUTOMATIQUE DES AVANCES'))
        self.stdout.write('=' * 80)
        
        if dry_run:
            self.stdout.write(self.style.WARNING('⚠️  MODE DRY-RUN : Aucune modification ne sera sauvegardée'))
        
        # Récupérer les avances
        if avance_id:
            avances = AvanceLoyer.objects.filter(id=avance_id, statut='active')
            self.stdout.write(f'📋 Traitement de l\'avance #{avance_id}')
        elif contrat_id:
            avances = AvanceLoyer.objects.filter(contrat_id=contrat_id, statut='active')
            self.stdout.write(f'📋 Traitement des avances du contrat #{contrat_id}')
        else:
            avances = AvanceLoyer.objects.filter(statut='active')
            self.stdout.write(f'📋 Traitement de TOUTES les avances actives ({avances.count()} avances)')
        
        if not avances.exists():
            self.stdout.write(self.style.WARNING('⚠️  Aucune avance active trouvée'))
            return
        
        mois_actuel = date.today().replace(day=1)
        self.stdout.write(f'📅 Mois actuel: {mois_actuel.strftime("%B %Y")}')
        self.stdout.write('')
        
        total_consommees = 0
        total_mois_ajoutes = 0
        
        for avance in avances:
            self.stdout.write(f'\n🔍 Avance #{avance.id} - Contrat #{avance.contrat.id}')
            self.stdout.write(f'   - Mois début: {avance.mois_debut_couverture}')
            self.stdout.write(f'   - Mois fin: {avance.mois_fin_couverture}')
            self.stdout.write(f'   - Nombre mois couverts: {avance.nombre_mois_couverts}')
            self.stdout.write(f'   - Montant restant: {avance.montant_restant} F CFA')
            
            # Compter les consommations existantes
            consommations_existantes = ConsommationAvance.objects.filter(avance=avance).count()
            self.stdout.write(f'   - Consommations existantes: {consommations_existantes}')
            
            # Calculer les mois à consommer
            mois_a_consommer = ServiceConsommationDynamique._calculer_mois_a_consommer(avance, mois_actuel)
            
            if not mois_a_consommer:
                self.stdout.write(self.style.WARNING('   ⚠️  Aucun mois à consommer'))
                continue
            
            self.stdout.write(self.style.SUCCESS(f'   ✅ {len(mois_a_consommer)} mois à consommer: {[m.strftime("%B %Y") for m in mois_a_consommer]}'))
            
            if not dry_run:
                # Forcer la consommation
                resultat = ServiceConsommationDynamique._consommer_avance_par_temps(avance)
                
                if resultat['consommee']:
                    total_consommees += 1
                    total_mois_ajoutes += resultat['mois_ajoutes']
                    self.stdout.write(self.style.SUCCESS(f'   ✅ {resultat["mois_ajoutes"]} mois consommés avec succès'))
                    
                    # Recharger pour voir le nouveau statut
                    avance.refresh_from_db()
                    self.stdout.write(f'   - Nouveau montant restant: {avance.montant_restant} F CFA')
                    self.stdout.write(f'   - Nouveau statut: {avance.statut}')
                else:
                    self.stdout.write(self.style.ERROR('   ❌ Erreur lors de la consommation'))
            else:
                self.stdout.write(self.style.WARNING('   🔄 [DRY-RUN] Ces mois seraient consommés'))
                total_mois_ajoutes += len(mois_a_consommer)
        
        self.stdout.write('')
        self.stdout.write('=' * 80)
        if dry_run:
            self.stdout.write(self.style.WARNING(f'🔍 [DRY-RUN] {total_mois_ajoutes} mois seraient consommés'))
        else:
            self.stdout.write(self.style.SUCCESS(f'✅ {total_consommees} avance(s) traitée(s), {total_mois_ajoutes} mois consommés'))
        
        self.stdout.write('=' * 80)
