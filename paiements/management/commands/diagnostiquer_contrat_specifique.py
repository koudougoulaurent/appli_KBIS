"""
Commande pour diagnostiquer un contrat spécifique avec incohérence d'avance
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from contrats.models import Contrat
from paiements.models import Paiement
from paiements.models_avance import AvanceLoyer
from datetime import datetime
from dateutil.relativedelta import relativedelta


class Command(BaseCommand):
    help = 'Diagnostique et corrige un contrat spécifique avec incohérence d\'avance'

    def add_arguments(self, parser):
        parser.add_argument('contrat_id', type=int, help='ID du contrat à diagnostiquer')
        parser.add_argument('--corriger', action='store_true', help='Corriger les incohérences détectées')

    def handle(self, *args, **options):
        contrat_id = options['contrat_id']
        corriger = options.get('corriger', False)
        
        try:
            contrat = Contrat.objects.get(pk=contrat_id, is_deleted=False)
        except Contrat.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Contrat #{contrat_id} introuvable'))
            return
        
        self.stdout.write(self.style.SUCCESS(f'\n{"="*80}'))
        self.stdout.write(self.style.SUCCESS(f'DIAGNOSTIC CONTRAT #{contrat.id}'))
        self.stdout.write(self.style.SUCCESS(f'{"="*80}'))
        
        # Informations du contrat
        self.stdout.write(f'\nLocataire: {contrat.locataire.get_nom_complet() if contrat.locataire else "N/A"}')
        self.stdout.write(f'Propriete: {contrat.propriete.titre if contrat.propriete else "N/A"}')
        self.stdout.write(f'Loyer mensuel: {contrat.loyer_mensuel} F CFA')
        
        # 1. PAIEMENTS DE LOYER
        self.stdout.write(self.style.SUCCESS(f'\n\n1. PAIEMENTS DE LOYER'))
        self.stdout.write(f'{"-"*80}')
        
        paiements_loyer = Paiement.objects.filter(
            contrat=contrat,
            type_paiement='loyer',
            statut='valide',
            is_deleted=False
        ).order_by('-date_paiement')[:10]
        
        if paiements_loyer:
            for p in paiements_loyer:
                self.stdout.write(f'  #{p.id} | {p.date_paiement} | Mois: {p.mois_paye or "NON DEFINI"} | {p.montant} F CFA')
                
            dernier_paiement = paiements_loyer.first()
            self.stdout.write(self.style.SUCCESS(f'\n  Dernier paiement loyer:'))
            self.stdout.write(f'    - Date: {dernier_paiement.date_paiement}')
            self.stdout.write(f'    - Mois paye: {dernier_paiement.mois_paye}')
        else:
            self.stdout.write(self.style.WARNING('  Aucun paiement de loyer trouve'))
        
        # 2. AVANCES DE LOYER
        self.stdout.write(self.style.SUCCESS(f'\n\n2. AVANCES DE LOYER'))
        self.stdout.write(f'{"-"*80}')
        
        avances = AvanceLoyer.objects.filter(
            contrat=contrat
        ).order_by('-date_avance')
        
        if avances:
            for avance in avances:
                self.stdout.write(f'\n  Avance #{avance.id}:')
                self.stdout.write(f'    - Date: {avance.date_avance}')
                self.stdout.write(f'    - Montant: {avance.montant_avance} F CFA')
                self.stdout.write(f'    - Loyer mensuel: {avance.loyer_mensuel} F CFA')
                self.stdout.write(f'    - Mois couverts: {avance.nombre_mois_couverts}')
                self.stdout.write(f'    - Periode: {avance.mois_debut_couverture} -> {avance.mois_fin_couverture}')
                self.stdout.write(f'    - Montant restant: {avance.montant_restant} F CFA')
                self.stdout.write(f'    - Statut: {avance.statut}')
                
                # Vérifier la cohérence
                mois_calcules = int(avance.montant_avance / avance.loyer_mensuel)
                mois_fin_theorique = avance.mois_debut_couverture + relativedelta(months=mois_calcules - 1)
                
                if mois_fin_theorique != avance.mois_fin_couverture:
                    self.stdout.write(self.style.ERROR(f'    INCOHERENCE DETECTEE!'))
                    self.stdout.write(self.style.ERROR(f'      Mois fin actuel: {avance.mois_fin_couverture}'))
                    self.stdout.write(self.style.ERROR(f'      Mois fin theorique: {mois_fin_theorique}'))
                    self.stdout.write(self.style.ERROR(f'      Difference: {(avance.mois_fin_couverture - mois_fin_theorique).days} jours'))
        else:
            self.stdout.write(self.style.WARNING('  Aucune avance trouvee'))
        
        # 3. CALCUL DU PROCHAIN MOIS A PAYER
        self.stdout.write(self.style.SUCCESS(f'\n\n3. CALCUL DU PROCHAIN MOIS A PAYER'))
        self.stdout.write(f'{"-"*80}')
        
        try:
            from paiements.services_logique_avance_unique import ServiceLogiqueAvanceUnique
            prochain_mois = ServiceLogiqueAvanceUnique.get_prochain_mois_a_payer(contrat)
            self.stdout.write(f'  Prochain mois a payer: {prochain_mois.strftime("%B %Y")}')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  Erreur calcul prochain mois: {e}'))
            import traceback
            traceback.print_exc()
        
        # 4. VERIFICATION DE LA COHERENCE
        self.stdout.write(self.style.SUCCESS(f'\n\n4. VERIFICATION DE LA COHERENCE'))
        self.stdout.write(f'{"-"*80}')
        
        avances_actives = AvanceLoyer.objects.filter(
            contrat=contrat,
            statut='active'
        )
        
        if avances_actives:
            for avance in avances_actives:
                # Vérifier si avance devrait être épuisée
                now = datetime.now().date().replace(day=1)
                if avance.mois_fin_couverture < now and avance.montant_restant == 0:
                    self.stdout.write(self.style.WARNING(f'  Avance #{avance.id} devrait etre epuisee (fin: {avance.mois_fin_couverture})'))
                    
                    if corriger:
                        avance.statut = 'epuisee'
                        avance.save(update_fields=['statut'])
                        self.stdout.write(self.style.SUCCESS(f'    CORRIGE: Statut mis a jour -> epuisee'))
        
        # 5. CORRECTION SI DEMANDEE
        if corriger:
            self.stdout.write(self.style.SUCCESS(f'\n\n5. CORRECTION'))
            self.stdout.write(f'{"-"*80}')
            
            with transaction.atomic():
                # Resynchroniser toutes les avances du contrat
                from paiements.services_logique_avance_unique import ServiceLogiqueAvanceUnique
                
                for avance in avances:
                    if avance.statut == 'active':
                        try:
                            ServiceLogiqueAvanceUnique.synchroniser_avance_existante(avance)
                            self.stdout.write(self.style.SUCCESS(f'  Avance #{avance.id} resynchronisee'))
                        except Exception as e:
                            self.stdout.write(self.style.ERROR(f'  Erreur avance #{avance.id}: {e}'))
                
                self.stdout.write(self.style.SUCCESS(f'\n  CORRECTION TERMINEE'))
        
        self.stdout.write(self.style.SUCCESS(f'\n{"="*80}'))
        self.stdout.write(self.style.SUCCESS('DIAGNOSTIC TERMINE'))
        self.stdout.write(self.style.SUCCESS(f'{"="*80}\n'))
