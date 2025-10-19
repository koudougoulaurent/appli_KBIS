"""
Commande Django pour corriger le système des avances
Résout tous les problèmes identifiés :
1. Date de début basée sur le contrat, pas le paiement
2. Concordance parfaite entre montant avance et récépissé
3. Calcul correct des mois couverts basé sur le dernier mois de loyer payé
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from paiements.models import Paiement
from paiements.models_avance import AvanceLoyer
from paiements.services_avance_corrige import ServiceAvanceCorrige


class Command(BaseCommand):
    help = 'Corrige le système des avances avec la logique corrigée'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Affiche ce qui serait fait sans effectuer les modifications',
        )
        parser.add_argument(
            '--avance-id',
            type=int,
            help='Corriger une avance spécifique par son ID',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        avance_id = options.get('avance_id')
        
        self.stdout.write("=== CORRECTION DU SYSTÈME DES AVANCES ===")
        self.stdout.write(f"Début: {self.get_current_time()}")
        
        if dry_run:
            self.stdout.write(self.style.WARNING('MODE DRY-RUN - Aucune modification ne sera effectuée'))
        
        if avance_id:
            self.corriger_avance_specifique(avance_id, dry_run)
        else:
            self.corriger_toutes_avances(dry_run)
    
    def get_current_time(self):
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def corriger_avance_specifique(self, avance_id, dry_run):
        """Corrige une avance spécifique."""
        try:
            avance = AvanceLoyer.objects.select_related('contrat').get(id=avance_id)
            self.stdout.write(f"\n=== CORRECTION DE L'AVANCE {avance_id} ===")
            
            # Calculer avec la logique corrigée
            mois_couverts_data = ServiceAvanceCorrige.calculer_mois_couverts_correct(
                avance.contrat, avance.montant_avance, avance.date_avance
            )
            
            if not mois_couverts_data:
                self.stdout.write(self.style.ERROR(f"Impossible de calculer les mois couverts pour l'avance {avance_id}"))
                return
            
            # Afficher les informations
            self.stdout.write(f"Contrat: {avance.contrat}")
            self.stdout.write(f"Montant avance: {avance.montant_avance} F CFA")
            self.stdout.write(f"Loyer mensuel: {avance.contrat.loyer_mensuel} F CFA")
            self.stdout.write(f"Date avance: {avance.date_avance}")
            self.stdout.write(f"")
            self.stdout.write(f"ANCIENNES VALEURS:")
            self.stdout.write(f"  - Mois couverts: {avance.nombre_mois_couverts}")
            self.stdout.write(f"  - Début couverture: {avance.mois_debut_couverture}")
            self.stdout.write(f"  - Fin couverture: {avance.mois_fin_couverture}")
            self.stdout.write(f"")
            self.stdout.write(f"NOUVELLES VALEURS:")
            self.stdout.write(f"  - Mois couverts: {mois_couverts_data['nombre']}")
            self.stdout.write(f"  - Début couverture: {mois_couverts_data['date_debut']}")
            self.stdout.write(f"  - Fin couverture: {mois_couverts_data['date_fin']}")
            self.stdout.write(f"  - Mois: {mois_couverts_data['mois_texte']}")
            self.stdout.write(f"  - Reste: {mois_couverts_data['reste']} F CFA")
            
            if not dry_run:
                with transaction.atomic():
                    avance.nombre_mois_couverts = mois_couverts_data['nombre']
                    avance.montant_reste = mois_couverts_data['reste']
                    avance.mois_debut_couverture = mois_couverts_data['date_debut']
                    avance.mois_fin_couverture = mois_couverts_data['date_fin']
                    avance.save()
                    
                self.stdout.write(self.style.SUCCESS(f"✓ Avance {avance_id} corrigée avec succès"))
            else:
                self.stdout.write(self.style.WARNING(f"[DRY-RUN] Avance {avance_id} serait corrigée"))
                
        except AvanceLoyer.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"Avance {avance_id} non trouvée"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Erreur lors de la correction de l'avance {avance_id}: {e}"))
    
    def corriger_toutes_avances(self, dry_run):
        """Corrige toutes les avances."""
        # Afficher les statistiques avant correction
        self.afficher_statistiques_avances()
        
        # Récupérer toutes les avances actives
        avances = AvanceLoyer.objects.filter(statut='active').select_related('contrat')
        
        self.stdout.write(f"\nNombre d'avances à corriger: {avances.count()}")
        
        corrections_effectuees = 0
        erreurs = 0
        
        for avance in avances:
            try:
                # Calculer avec la logique corrigée
                mois_couverts_data = ServiceAvanceCorrige.calculer_mois_couverts_correct(
                    avance.contrat, avance.montant_avance, avance.date_avance
                )
                
                if not mois_couverts_data:
                    self.stdout.write(self.style.ERROR(f"✗ Avance {avance.id}: Impossible de calculer les mois couverts"))
                    erreurs += 1
                    continue
                
                # Vérifier si des changements sont nécessaires
                changements = (
                    avance.nombre_mois_couverts != mois_couverts_data['nombre'] or
                    avance.mois_debut_couverture != mois_couverts_data['date_debut'] or
                    avance.mois_fin_couverture != mois_couverts_data['date_fin']
                )
                
                if changements:
                    if dry_run:
                        self.stdout.write(f"[DRY-RUN] ✓ Avance {avance.id}: {mois_couverts_data['mois_texte']}")
                    else:
                        with transaction.atomic():
                            avance.nombre_mois_couverts = mois_couverts_data['nombre']
                            avance.montant_reste = mois_couverts_data['reste']
                            avance.mois_debut_couverture = mois_couverts_data['date_debut']
                            avance.mois_fin_couverture = mois_couverts_data['date_fin']
                            avance.save()
                        
                        self.stdout.write(f"✓ Avance {avance.id}: {mois_couverts_data['mois_texte']}")
                    
                    corrections_effectuees += 1
                else:
                    self.stdout.write(f"- Avance {avance.id}: Aucun changement nécessaire")
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"✗ Erreur pour l'avance {avance.id}: {e}"))
                erreurs += 1
        
        self.stdout.write(f"\n=== RÉSULTATS ===")
        self.stdout.write(f"Corrections effectuées: {corrections_effectuees}")
        self.stdout.write(f"Erreurs: {erreurs}")
        self.stdout.write(f"Fin: {self.get_current_time()}")
        
        if not dry_run and corrections_effectuees > 0:
            self.stdout.write("\n=== STATISTIQUES APRÈS CORRECTION ===")
            self.afficher_statistiques_avances()
    
    def afficher_statistiques_avances(self):
        """Affiche les statistiques des avances."""
        from django.db import models
        
        self.stdout.write("\n=== STATISTIQUES DES AVANCES ===")
        
        # Statistiques générales
        total_avances = AvanceLoyer.objects.count()
        avances_actives = AvanceLoyer.objects.filter(statut='active').count()
        total_montant = AvanceLoyer.objects.aggregate(
            total=models.Sum('montant_avance')
        )['total'] or 0
        
        self.stdout.write(f"Total avances: {total_avances}")
        self.stdout.write(f"Avances actives: {avances_actives}")
        self.stdout.write(f"Montant total: {total_montant:,.0f} F CFA")
        
        # Statistiques par contrat
        stats_contrats = AvanceLoyer.objects.filter(statut='active').values(
            'contrat__numero_contrat', 'contrat__locataire__nom', 'contrat__locataire__prenom'
        ).annotate(
            count=models.Count('id'),
            total_montant=models.Sum('montant_avance'),
            total_mois=models.Sum('nombre_mois_couverts')
        ).order_by('-total_montant')[:10]
        
        self.stdout.write(f"\nTop 10 des contrats par montant d'avance:")
        for stat in stats_contrats:
            nom_complet = f"{stat['contrat__locataire__prenom']} {stat['contrat__locataire__nom']}"
            self.stdout.write(f"  {stat['contrat__numero_contrat']} ({nom_complet}): {stat['count']} avances, {stat['total_montant']:,.0f} F CFA, {stat['total_mois']} mois")
