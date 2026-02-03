"""
Commande pour corriger les mois_debut_couverture incorrects dans les avances existantes
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from datetime import date
from dateutil.relativedelta import relativedelta

from paiements.models_avance import AvanceLoyer, ConsommationAvance
from paiements.services_logique_avance_unique import ServiceLogiqueAvanceUnique
from contrats.models import Contrat


class Command(BaseCommand):
    help = 'Corrige les mois_debut_couverture incorrects dans les avances existantes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--contrat-id',
            type=int,
            help='ID du contrat spécifique à corriger',
        )
        parser.add_argument(
            '--avance-id',
            type=int,
            help='ID de l\'avance spécifique à corriger',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simuler sans sauvegarder',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forcer la correction même si mois_debut semble correct',
        )

    def handle(self, *args, **options):
        contrat_id = options.get('contrat_id')
        avance_id = options.get('avance_id')
        dry_run = options.get('dry_run', False)
        force = options.get('force', False)
        
        mois_actuel = date.today().replace(day=1)
        
        # Récupérer les avances à corriger
        if avance_id:
            avances = AvanceLoyer.objects.filter(id=avance_id)
        elif contrat_id:
            avances = AvanceLoyer.objects.filter(contrat_id=contrat_id)
        else:
            avances = AvanceLoyer.objects.all()
        
        avances = avances.order_by('contrat', 'date_avance')
        
        self.stdout.write(f"\n{'='*80}")
        self.stdout.write(f"Correction des mois_debut_couverture")
        self.stdout.write(f"{'='*80}\n")
        
        if dry_run:
            self.stdout.write(self.style.WARNING("⚠️ MODE DRY-RUN - Aucune modification ne sera sauvegardée\n"))
        
        corrigees = 0
        ignorees = 0
        erreurs = 0
        
        for avance in avances:
            try:
                # Vérifier si la correction est nécessaire
                mois_debut_actuel = avance.mois_debut_couverture
                date_avance = avance.date_avance
                
                if not mois_debut_actuel:
                    self.stdout.write(f"❌ Avance #{avance.id}: mois_debut_couverture est NULL")
                    if not dry_run:
                        # Calculer le mois début correct
                        nouveau_mois_debut = ServiceLogiqueAvanceUnique.determiner_mois_debut_couverture_nouvelle_avance(
                            avance.contrat, date_avance
                        )
                        avance.mois_debut_couverture = nouveau_mois_debut
                        avance.save()
                        self.stdout.write(f"   ✓ Corrigé: {nouveau_mois_debut.strftime('%d/%m/%Y')}")
                    corrigees += 1
                    continue
                
                # Vérifier si mois_debut est dans le futur par rapport à date_avance
                mois_avance = date_avance.replace(day=1)
                mois_debut_norm = mois_debut_actuel.replace(day=1)
                
                # Calculer le mois début correct selon la logique actuelle
                mois_debut_correct = ServiceLogiqueAvanceUnique.determiner_mois_debut_couverture_nouvelle_avance(
                    avance.contrat, date_avance
                )
                
                # Vérifier si correction nécessaire
                correction_necessaire = False
                raison = ""
                
                # Cas 1: mois_debut est dans le futur par rapport à date_avance (sauf si c'est normal)
                if mois_debut_norm > mois_avance + relativedelta(months=1):
                    # Vérifier s'il y a une raison valable (avances précédentes, etc.)
                    # Si le mois correct calculé est différent, c'est une erreur
                    if mois_debut_correct != mois_debut_norm:
                        correction_necessaire = True
                        raison = f"Mois début ({mois_debut_norm.strftime('%B %Y')}) est trop dans le futur par rapport à date avance ({mois_avance.strftime('%B %Y')})"
                
                # Cas 2: mois_debut est dans le futur par rapport au mois actuel ET l'avance devrait être consommée
                if not correction_necessaire and mois_debut_norm >= mois_actuel:
                    # Vérifier si l'avance devrait avoir été consommée
                    # Si date_avance est dans le passé et mois_debut est dans le futur, c'est suspect
                    if date_avance < date.today() - relativedelta(months=1):
                        # L'avance a été créée il y a plus d'un mois mais commence dans le futur
                        # Vérifier s'il y a des consommations
                        consommations = ConsommationAvance.objects.filter(avance=avance).count()
                        if consommations == 0:
                            # Pas de consommation alors que l'avance devrait avoir commencé
                            if mois_debut_correct < mois_debut_norm:
                                correction_necessaire = True
                                raison = f"Mois début ({mois_debut_norm.strftime('%B %Y')}) est dans le futur alors que l'avance devrait avoir commencé ({mois_debut_correct.strftime('%B %Y')})"
                
                # Cas 3: Force mode - toujours recalculer
                if force and mois_debut_correct != mois_debut_norm:
                    correction_necessaire = True
                    raison = "Mode force activé - recalcul du mois début"
                
                if correction_necessaire:
                    self.stdout.write(f"\n🔧 Avance #{avance.id} (Contrat #{avance.contrat_id}):")
                    self.stdout.write(f"   Date avance: {date_avance.strftime('%d/%m/%Y')}")
                    self.stdout.write(f"   Mois début actuel: {mois_debut_actuel.strftime('%d/%m/%Y')}")
                    self.stdout.write(f"   Mois début correct: {mois_debut_correct.strftime('%d/%m/%Y')}")
                    self.stdout.write(f"   Raison: {raison}")
                    
                    if not dry_run:
                        with transaction.atomic():
                            # Sauvegarder l'ancien mois début pour référence
                            ancien_mois_debut = avance.mois_debut_couverture
                            
                            # Corriger le mois début
                            avance.mois_debut_couverture = mois_debut_correct
                            
                            # Recalculer le mois fin
                            if avance.nombre_mois_couverts > 0:
                                avance.mois_fin_couverture = mois_debut_correct + relativedelta(months=avance.nombre_mois_couverts - 1)
                            
                            avance.save()
                            
                            self.stdout.write(f"   ✓ Corrigé: {mois_debut_correct.strftime('%d/%m/%Y')}")
                            
                            # Si l'ancien mois début était dans le passé et le nouveau aussi, vérifier consommation
                            if ancien_mois_debut < mois_actuel and mois_debut_correct < mois_actuel:
                                # Forcer la consommation automatique
                                from paiements.services_consommation_dynamique import ServiceConsommationDynamique
                                resultat = ServiceConsommationDynamique.consommer_avances_automatiquement(avance.contrat)
                                if resultat['consommees'] > 0:
                                    self.stdout.write(f"   ✓ Consommation automatique déclenchée: {resultat['consommees']} avance(s)")
                    else:
                        self.stdout.write(f"   [DRY-RUN] Serait corrigé vers: {mois_debut_correct.strftime('%d/%m/%Y')}")
                    
                    corrigees += 1
                else:
                    ignorees += 1
                    
            except Exception as e:
                erreurs += 1
                self.stdout.write(self.style.ERROR(f"\n❌ Erreur sur avance #{avance.id}: {str(e)}"))
                import traceback
                if self.verbosity >= 2:
                    self.stdout.write(traceback.format_exc())
        
        self.stdout.write(f"\n{'='*80}")
        self.stdout.write(f"Résumé:")
        self.stdout.write(f"  ✓ Corrigées: {corrigees}")
        self.stdout.write(f"  ⊘ Ignorées: {ignorees}")
        self.stdout.write(f"  ❌ Erreurs: {erreurs}")
        self.stdout.write(f"{'='*80}\n")
        
        if dry_run:
            self.stdout.write(self.style.WARNING("\n⚠️ Mode DRY-RUN - Aucune modification n'a été sauvegardée"))
            self.stdout.write(self.style.WARNING("   Relancez sans --dry-run pour appliquer les corrections\n"))
