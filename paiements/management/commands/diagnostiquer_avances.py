"""
Commande pour diagnostiquer et corriger les avances incorrectement marquées comme épuisées
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from paiements.models_avance import AvanceLoyer
from paiements.models import Paiement
from datetime import datetime
from dateutil.relativedelta import relativedelta


class Command(BaseCommand):
    help = "Diagnostique et corrige les avances incorrectement marquées comme épuisées"

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Affiche les modifications sans les appliquer',
        )
        parser.add_argument(
            '--corriger',
            action='store_true',
            help='Corrige automatiquement les avances problématiques',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        corriger = options['corriger']
        
        if dry_run:
            self.stdout.write(self.style.WARNING("MODE DRY-RUN - Aucune modification"))
        
        self.stdout.write("\n" + "=" * 80)
        self.stdout.write("DIAGNOSTIC DES AVANCES")
        self.stdout.write("=" * 80 + "\n")
        
        # 1. Vérifier toutes les avances avec statut 'active'
        avances_actives = AvanceLoyer.objects.filter(statut='active')
        self.stdout.write(f"\n1. Avances ACTIVES : {avances_actives.count()}")
        
        problemes_detectes = 0
        
        for avance in avances_actives:
            self.stdout.write(f"\n  Avance ID {avance.id} (Contrat: {avance.contrat.locataire.get_nom_complet()}):")
            self.stdout.write(f"    - Date avance : {avance.date_avance}")
            self.stdout.write(f"    - Montant : {avance.montant_avance} F CFA")
            self.stdout.write(f"    - Loyer mensuel : {avance.loyer_mensuel} F CFA")
            self.stdout.write(f"    - Mois couverts : {avance.nombre_mois_couverts}")
            self.stdout.write(f"    - Montant restant : {avance.montant_restant} F CFA")
            self.stdout.write(f"    - Couverture : {avance.mois_debut_couverture} → {avance.mois_fin_couverture}")
            
            # Vérifier la cohérence
            today = datetime.now().date().replace(day=1)
            
            # Problème 1 : Montant restant = 0 mais statut = active
            if avance.montant_restant <= 0:
                self.stdout.write(self.style.WARNING(
                    f"    ⚠️  PROBLÈME : Montant restant = 0 mais statut = active"
                ))
                problemes_detectes += 1
                
                if corriger and not dry_run:
                    avance.statut = 'epuisee'
                    avance.save()
                    self.stdout.write(self.style.SUCCESS("    ✓ CORRIGÉ : Statut changé en 'epuisee'"))
            
            # Problème 2 : Date de fin dépassée
            if avance.mois_fin_couverture and avance.mois_fin_couverture < today:
                self.stdout.write(self.style.WARNING(
                    f"    ⚠️  ATTENTION : Date de fin ({avance.mois_fin_couverture}) < Aujourd'hui ({today})"
                ))
                self.stdout.write(f"    → Avance devrait être considérée comme expirée")
                # Ne pas corriger automatiquement car c'est peut-être normal
        
        # 2. Vérifier les avances marquées 'epuisee' qui devraient être actives
        avances_epuisees = AvanceLoyer.objects.filter(statut='epuisee')
        self.stdout.write(f"\n2. Avances ÉPUISÉES : {avances_epuisees.count()}")
        
        avances_incorrectement_epuisees = 0
        
        for avance in avances_epuisees:
            # Une avance est incorrectement épuisée si :
            # - Elle a encore du montant restant > 0
            # - ET sa date de fin n'est pas encore passée
            today = datetime.now().date().replace(day=1)
            
            if avance.montant_restant > 0 and avance.mois_fin_couverture >= today:
                self.stdout.write(f"\n  Avance ID {avance.id} (Contrat: {avance.contrat.locataire.get_nom_complet()}):")
                self.stdout.write(f"    - Montant restant : {avance.montant_restant} F CFA (> 0)")
                self.stdout.write(f"    - Couverture : {avance.mois_debut_couverture} → {avance.mois_fin_couverture}")
                self.stdout.write(self.style.ERROR(
                    f"    ❌ ERREUR : Avance marquée 'epuisee' mais devrait être 'active' !"
                ))
                avances_incorrectement_epuisees += 1
                problemes_detectes += 1
                
                if corriger and not dry_run:
                    avance.statut = 'active'
                    avance.save()
                    self.stdout.write(self.style.SUCCESS("    ✓ CORRIGÉ : Statut changé en 'active'"))
        
        # 3. Vérifier les paiements d'avance sans AvanceLoyer correspondante
        self.stdout.write(f"\n3. Paiements d'avance sans objet AvanceLoyer :")
        
        paiements_avance = Paiement.objects.filter(
            type_paiement='avance',
            statut='valide',
            is_deleted=False
        )
        
        paiements_sans_avance = 0
        
        for paiement in paiements_avance:
            # Vérifier si une AvanceLoyer existe
            avance_existe = AvanceLoyer.objects.filter(paiement=paiement).exists()
            
            if not avance_existe:
                self.stdout.write(f"\n  Paiement ID {paiement.id} :")
                self.stdout.write(f"    - Contrat : {paiement.contrat.locataire.get_nom_complet()}")
                self.stdout.write(f"    - Date : {paiement.date_paiement}")
                self.stdout.write(f"    - Montant : {paiement.montant} F CFA")
                self.stdout.write(self.style.ERROR(
                    f"    ❌ ERREUR : Aucun objet AvanceLoyer correspondant !"
                ))
                paiements_sans_avance += 1
                problemes_detectes += 1
                
                if corriger and not dry_run:
                    # Synchroniser ce paiement
                    from paiements.services_synchronisation_avances import ServiceSynchronisationAvances
                    try:
                        ServiceSynchronisationAvances.synchroniser_avance_avec_paiement(paiement)
                        self.stdout.write(self.style.SUCCESS("    ✓ CORRIGÉ : AvanceLoyer créée"))
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"    ✗ ERREUR : {str(e)}"))
        
        # Résumé
        self.stdout.write("\n" + "=" * 80)
        self.stdout.write("RÉSUMÉ")
        self.stdout.write("=" * 80)
        self.stdout.write(f"\nAvances actives : {avances_actives.count()}")
        self.stdout.write(f"Avances épuisées : {avances_epuisees.count()}")
        self.stdout.write(f"\nProblèmes détectés : {problemes_detectes}")
        self.stdout.write(f"  - Avances incorrectement épuisées : {avances_incorrectement_epuisees}")
        self.stdout.write(f"  - Paiements sans AvanceLoyer : {paiements_sans_avance}")
        
        if problemes_detectes > 0:
            if corriger and not dry_run:
                self.stdout.write(self.style.SUCCESS(f"\n✓ {problemes_detectes} problème(s) corrigé(s)"))
            else:
                self.stdout.write(self.style.WARNING(
                    f"\n⚠️  Pour corriger automatiquement, relancez avec --corriger"
                ))
                if not dry_run:
                    self.stdout.write("   (ou avec --dry-run --corriger pour simuler)")
        else:
            self.stdout.write(self.style.SUCCESS("\n✓ Aucun problème détecté"))
        
        self.stdout.write("\n" + "=" * 80 + "\n")
