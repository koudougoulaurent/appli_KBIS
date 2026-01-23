"""
Commande pour corriger les avances avec mois de début incorrect
CORRECTION V10.1: Les avances créées avant V8 ont souvent un mois de début incorrect
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from paiements.models_avance import AvanceLoyer
from paiements.models import Paiement
from dateutil.relativedelta import relativedelta
from decimal import Decimal


class Command(BaseCommand):
    help = 'Corrige les avances avec mois de début incorrect (saute janvier)'

    def add_arguments(self, parser):
        parser.add_argument('--corriger', action='store_true', help='Corriger automatiquement les incohérences')
        parser.add_argument('--avance-id', type=int, help='ID d\'une avance spécifique à corriger')

    def handle(self, *args, **options):
        corriger = options.get('corriger', False)
        avance_id = options.get('avance_id')
        
        self.stdout.write(self.style.SUCCESS(f'\n{"="*80}'))
        self.stdout.write(self.style.SUCCESS('CORRECTION AVANCES - MOIS DE DÉBUT INCORRECT'))
        self.stdout.write(self.style.SUCCESS(f'{"="*80}\n'))
        
        # Filtrer les avances
        if avance_id:
            avances = AvanceLoyer.objects.filter(pk=avance_id)
        else:
            avances = AvanceLoyer.objects.filter(statut='active')
        
        avances_problematiques = []
        avances_correctes = 0
        
        for avance in avances:
            # Calculer le mois de début théorique avec la logique V10
            mois_debut_theorique = self._calculer_mois_debut_theorique(avance.contrat)
            
            # Calculer le mois de fin théorique
            mois_fin_theorique = mois_debut_theorique + relativedelta(months=avance.nombre_mois_couverts - 1)
            
            # Vérifier si les mois sont différents
            if avance.mois_debut_couverture != mois_debut_theorique or avance.mois_fin_couverture != mois_fin_theorique:
                avances_problematiques.append({
                    'avance': avance,
                    'mois_debut_actuel': avance.mois_debut_couverture,
                    'mois_fin_actuel': avance.mois_fin_couverture,
                    'mois_debut_theorique': mois_debut_theorique,
                    'mois_fin_theorique': mois_fin_theorique
                })
            else:
                avances_correctes += 1
        
        self.stdout.write(f'\nAvances analysées: {avances.count()}')
        self.stdout.write(self.style.SUCCESS(f'Avances correctes: {avances_correctes}'))
        self.stdout.write(self.style.ERROR(f'Avances problématiques: {len(avances_problematiques)}\n'))
        
        if avances_problematiques:
            self.stdout.write(self.style.WARNING(f'\n{"="*80}'))
            self.stdout.write(self.style.WARNING('AVANCES AVEC MOIS DE DÉBUT INCORRECT'))
            self.stdout.write(self.style.WARNING(f'{"="*80}\n'))
            
            for item in avances_problematiques:
                avance = item['avance']
                self.stdout.write(f'\nAvance #{avance.id}:')
                self.stdout.write(f'  Contrat: #{avance.contrat.id} - {avance.contrat.locataire.get_nom_complet() if avance.contrat.locataire else "N/A"}')
                self.stdout.write(f'  Montant: {avance.montant_avance} F CFA')
                self.stdout.write(f'  Loyer mensuel: {avance.loyer_mensuel} F CFA')
                self.stdout.write(f'  Nombre mois: {avance.nombre_mois_couverts}')
                self.stdout.write(self.style.ERROR(f'  Mois début ACTUEL: {item["mois_debut_actuel"]}'))
                self.stdout.write(self.style.ERROR(f'  Mois fin ACTUEL: {item["mois_fin_actuel"]}'))
                self.stdout.write(self.style.SUCCESS(f'  Mois début CORRECT: {item["mois_debut_theorique"]}'))
                self.stdout.write(self.style.SUCCESS(f'  Mois fin CORRECT: {item["mois_fin_theorique"]}'))
                
                # Afficher les mois couverts actuels
                mois_couverts_actuels = self._generer_liste_mois(item["mois_debut_actuel"], avance.nombre_mois_couverts)
                mois_couverts_corrects = self._generer_liste_mois(item["mois_debut_theorique"], avance.nombre_mois_couverts)
                
                self.stdout.write(self.style.ERROR(f'  Mois couverts ACTUELS: {", ".join(mois_couverts_actuels)}'))
                self.stdout.write(self.style.SUCCESS(f'  Mois couverts CORRECTS: {", ".join(mois_couverts_corrects)}'))
                
                if corriger:
                    self.stdout.write(self.style.WARNING('\n  CORRECTION EN COURS...'))
                    try:
                        with transaction.atomic():
                            avance.mois_debut_couverture = item["mois_debut_theorique"]
                            avance.mois_fin_couverture = item["mois_fin_theorique"]
                            avance.save(update_fields=['mois_debut_couverture', 'mois_fin_couverture'])
                            self.stdout.write(self.style.SUCCESS(f'  ✓ Avance #{avance.id} corrigée'))
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'  ✗ Erreur correction avance #{avance.id}: {e}'))
        
        self.stdout.write(self.style.SUCCESS(f'\n{"="*80}'))
        if corriger:
            self.stdout.write(self.style.SUCCESS(f'✓ CORRECTION TERMINÉE'))
            self.stdout.write(self.style.SUCCESS(f'  {len(avances_problematiques)} avance(s) corrigée(s)'))
        else:
            self.stdout.write(self.style.WARNING('MODE DIAGNOSTIC SEULEMENT'))
            self.stdout.write(self.style.WARNING('Utilisez --corriger pour appliquer les corrections'))
        self.stdout.write(self.style.SUCCESS(f'{"="*80}\n'))
    
    def _calculer_mois_debut_theorique(self, contrat):
        """Calcule le mois de début théorique avec la logique V10"""
        # 1. Chercher le dernier paiement de loyer validé
        dernier_paiement_loyer = Paiement.objects.filter(
            contrat=contrat,
            type_paiement='loyer',
            statut='valide',
            is_deleted=False
        ).order_by('-date_paiement').first()
        
        dernier_mois_paiement = None
        if dernier_paiement_loyer:
            if dernier_paiement_loyer.mois_paye:
                from paiements.services_paiement_partiel import ServicePaiementPartiel
                dernier_mois_paiement = ServicePaiementPartiel.convertir_mois_paye_en_date(dernier_paiement_loyer.mois_paye)
            else:
                dernier_mois_paiement = dernier_paiement_loyer.date_paiement.replace(day=1)
        
        # 2. Chercher la dernière avance active (en excluant l'avance actuelle)
        derniere_avance = AvanceLoyer.objects.filter(
            contrat=contrat,
            statut='active',
            mois_fin_couverture__isnull=False
        ).order_by('-mois_fin_couverture').first()
        
        dernier_mois_avance = None
        if derniere_avance:
            dernier_mois_avance = derniere_avance.mois_fin_couverture
        
        # 3. Prendre le plus récent
        dernier_mois_couvert = None
        
        if dernier_mois_paiement and dernier_mois_avance:
            dernier_mois_couvert = max(dernier_mois_paiement, dernier_mois_avance)
        elif dernier_mois_paiement:
            dernier_mois_couvert = dernier_mois_paiement
        elif dernier_mois_avance:
            dernier_mois_couvert = dernier_mois_avance
        
        # 4. Calculer le mois de début
        if dernier_mois_couvert:
            mois_debut = dernier_mois_couvert + relativedelta(months=1)
        else:
            # Aucun paiement ni avance : utiliser date de début du contrat
            if hasattr(contrat, 'date_debut') and contrat.date_debut:
                mois_debut = contrat.date_debut.replace(day=1)
            elif hasattr(contrat, 'date_entree') and contrat.date_entree:
                mois_debut = contrat.date_entree.replace(day=1)
            else:
                from django.utils import timezone
                mois_debut = timezone.now().date().replace(day=1)
        
        return mois_debut
    
    def _generer_liste_mois(self, mois_debut, nombre_mois):
        """Génère la liste des mois couverts"""
        mois_liste = []
        mois_courant = mois_debut
        
        for i in range(nombre_mois):
            mois_liste.append(mois_courant.strftime('%B %Y'))
            mois_courant = mois_courant + relativedelta(months=1)
        
        return mois_liste
