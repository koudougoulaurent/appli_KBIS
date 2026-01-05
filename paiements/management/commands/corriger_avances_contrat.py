"""
Commande pour supprimer les avances en double et corriger les avances mal configurées
"""
from django.core.management.base import BaseCommand
from contrats.models import Contrat
from paiements.models_avance import AvanceLoyer
from decimal import Decimal
from dateutil.relativedelta import relativedelta
from django.db.models import Count

class Command(BaseCommand):
    help = 'Nettoyer et corriger les avances d\'un contrat'

    def add_arguments(self, parser):
        parser.add_argument('contrat_id', type=int, help='ID du contrat')
        parser.add_argument('--auto', action='store_true', help='Correction automatique sans confirmation')

    def handle(self, *args, **options):
        contrat_id = options['contrat_id']
        auto = options.get('auto', False)
        
        try:
            contrat = Contrat.objects.get(pk=contrat_id, is_deleted=False)
        except Contrat.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'❌ Contrat {contrat_id} introuvable'))
            return
        
        self.stdout.write(self.style.SUCCESS(f'\n🔧 CORRECTION AVANCES - Contrat {contrat.numero_contrat}'))
        
        loyer_contrat = Decimal(str(contrat.get_loyer_total()))
        self.stdout.write(f'Loyer mensuel contrat: {loyer_contrat} F CFA')
        
        # 1. Détecter et supprimer les doublons
        self.stdout.write('\n📊 Étape 1: Détection des doublons...')
        
        avances_groupees = AvanceLoyer.objects.filter(
            contrat=contrat
        ).values('date_avance', 'montant_avance').annotate(
            count=Count('id'),
            ids=Count('id')
        ).filter(count__gt=1)
        
        doublons_supprimes = 0
        for groupe in avances_groupees:
            avances_identiques = AvanceLoyer.objects.filter(
                contrat=contrat,
                date_avance=groupe['date_avance'],
                montant_avance=groupe['montant_avance']
            ).order_by('id')
            
            # Garder la première, supprimer les autres
            premiere = avances_identiques.first()
            doublons = avances_identiques.exclude(id=premiere.id)
            
            self.stdout.write(f'   Doublon trouvé: {groupe["date_avance"]} - {groupe["montant_avance"]} F CFA (x{groupe["count"]})')
            
            if auto or input(f'   Supprimer {doublons.count()} doublon(s)? (o/n): ').lower() == 'o':
                count = doublons.count()
                doublons.delete()
                doublons_supprimes += count
                self.stdout.write(self.style.SUCCESS(f'   ✅ {count} doublon(s) supprimé(s)'))
        
        if doublons_supprimes == 0:
            self.stdout.write('   ✅ Aucun doublon trouvé')
        
        # 2. Corriger les avances mal configurées
        self.stdout.write('\n🔧 Étape 2: Correction des avances mal configurées...')
        
        avances = AvanceLoyer.objects.filter(
            contrat=contrat
        ).order_by('date_avance')
        
        avances_corrigees = 0
        for avance in avances:
            # Calculer le nombre de mois correct
            mois_calcules = int(avance.montant_avance // loyer_contrat) if loyer_contrat > 0 else 0
            
            # Vérifier les incohérences
            loyer_incorrect = abs(avance.loyer_mensuel - loyer_contrat) > 100
            mois_incorrects = mois_calcules != avance.nombre_mois_couverts
            
            if loyer_incorrect or mois_incorrects:
                self.stdout.write(f'\n   ⚠️  Avance {avance.id} - {avance.date_avance}:')
                self.stdout.write(f'      Montant: {avance.montant_avance} F CFA')
                
                if loyer_incorrect:
                    self.stdout.write(f'      Loyer actuel: {avance.loyer_mensuel} F CFA → Correction: {loyer_contrat} F CFA')
                
                if mois_incorrects:
                    self.stdout.write(f'      Mois actuels: {avance.nombre_mois_couverts} → Correction: {mois_calcules}')
                
                if auto or input('      Corriger cette avance? (o/n): ').lower() == 'o':
                    avance.loyer_mensuel = loyer_contrat
                    avance.nombre_mois_couverts = mois_calcules
                    
                    if mois_calcules > 0:
                        avance.mois_fin_couverture = avance.mois_debut_couverture + relativedelta(months=mois_calcules - 1)
                    else:
                        avance.mois_fin_couverture = avance.mois_debut_couverture
                    
                    avance.save()
                    avances_corrigees += 1
                    self.stdout.write(self.style.SUCCESS('      ✅ Avance corrigée'))
        
        if avances_corrigees == 0:
            self.stdout.write('   ✅ Toutes les avances sont correctes')
        
        # 3. Résumé
        self.stdout.write(self.style.SUCCESS(f'\n✅ CORRECTION TERMINÉE'))
        self.stdout.write(f'   - Doublons supprimés: {doublons_supprimes}')
        self.stdout.write(f'   - Avances corrigées: {avances_corrigees}')
        
        # Afficher l'état final
        self.stdout.write('\n📋 ÉTAT FINAL:')
        avances_finales = AvanceLoyer.objects.filter(contrat=contrat).order_by('date_avance')
        for avance in avances_finales:
            self.stdout.write(f'   • {avance.date_avance}: {avance.montant_avance} F CFA → {avance.nombre_mois_couverts} mois ({avance.mois_debut_couverture} à {avance.mois_fin_couverture})')
