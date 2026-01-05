"""
Commande pour diagnostiquer les avances d'un contrat spécifique
"""
from django.core.management.base import BaseCommand
from contrats.models import Contrat
from paiements.models_avance import AvanceLoyer
from decimal import Decimal

class Command(BaseCommand):
    help = 'Diagnostic des avances pour un contrat'

    def add_arguments(self, parser):
        parser.add_argument('contrat_id', type=int, help='ID du contrat')

    def handle(self, *args, **options):
        contrat_id = options['contrat_id']
        
        try:
            contrat = Contrat.objects.get(pk=contrat_id, is_deleted=False)
        except Contrat.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'❌ Contrat {contrat_id} introuvable'))
            return
        
        self.stdout.write(self.style.SUCCESS(f'\n📋 DIAGNOSTIC CONTRAT {contrat.numero_contrat}'))
        self.stdout.write(f'Locataire: {contrat.locataire}')
        self.stdout.write(f'Propriété: {contrat.propriete}')
        self.stdout.write(f'Loyer mensuel: {contrat.get_loyer_total()} F CFA')
        
        # Récupérer toutes les avances (actives et anciennes)
        avances = AvanceLoyer.objects.filter(
            contrat=contrat
        ).order_by('-date_avance')
        
        self.stdout.write(f'\n🔍 AVANCES TROUVÉES: {avances.count()}')
        
        for i, avance in enumerate(avances, 1):
            self.stdout.write(f'\n--- Avance #{i} (ID: {avance.id}) ---')
            self.stdout.write(f'Date avance: {avance.date_avance}')
            self.stdout.write(f'Montant: {avance.montant_avance} F CFA')
            self.stdout.write(f'Loyer mensuel configuré: {avance.loyer_mensuel} F CFA')
            self.stdout.write(f'Mois couverts: {avance.nombre_mois_couverts}')
            self.stdout.write(f'Début couverture: {avance.mois_debut_couverture}')
            self.stdout.write(f'Fin couverture: {avance.mois_fin_couverture}')
            self.stdout.write(f'Montant restant: {avance.montant_restant} F CFA')
            self.stdout.write(f'Statut: {avance.statut}')
            
            # Vérifier si les calculs sont corrects
            loyer_contrat = Decimal(str(contrat.get_loyer_total()))
            mois_calcules = int(avance.montant_avance // loyer_contrat) if loyer_contrat > 0 else 0
            
            if abs(avance.loyer_mensuel - loyer_contrat) > 100:
                self.stdout.write(self.style.ERROR(
                    f'⚠️  INCOHÉRENCE: Loyer configuré ({avance.loyer_mensuel}) ≠ Loyer contrat ({loyer_contrat})'
                ))
            
            if mois_calcules != avance.nombre_mois_couverts:
                self.stdout.write(self.style.ERROR(
                    f'⚠️  INCOHÉRENCE: Devrait couvrir {mois_calcules} mois au lieu de {avance.nombre_mois_couverts}'
                ))
        
        # Vérifier les doublons
        from django.db.models import Count
        doublons = AvanceLoyer.objects.filter(
            contrat=contrat
        ).values('date_avance', 'montant_avance').annotate(
            count=Count('id')
        ).filter(count__gt=1)
        
        if doublons:
            self.stdout.write(self.style.ERROR(f'\n⚠️  DOUBLONS DÉTECTÉS: {doublons.count()}'))
            for doublon in doublons:
                self.stdout.write(f'   - {doublon["date_avance"]}: {doublon["montant_avance"]} F CFA (x{doublon["count"]})')
        
        self.stdout.write(self.style.SUCCESS('\n✅ Diagnostic terminé'))
