"""
Commande Django pour corriger les années incorrectes dans mois_paye
Corrige les paiements où l'année ne correspond pas (ex: janvier 2025 après décembre 2025)
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q
from paiements.models import Paiement
from datetime import datetime
from dateutil.relativedelta import relativedelta
import re


class Command(BaseCommand):
    help = 'Corrige les années incorrectes dans mois_paye pour les paiements existants'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Affiche les changements sans les appliquer',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        self.stdout.write(
            self.style.SUCCESS('Correction des années incorrectes dans mois_paye...')
        )
        
        # Mapping des mois français
        mois_francais = {
            'janvier': 1, 'février': 2, 'mars': 3, 'avril': 4,
            'mai': 5, 'juin': 6, 'juillet': 7, 'août': 8,
            'septembre': 9, 'octobre': 10, 'novembre': 11, 'décembre': 12
        }
        
        # Récupérer tous les paiements avec mois_paye
        paiements = Paiement.objects.filter(
            Q(mois_paye__isnull=False) & ~Q(mois_paye='')
        ).select_related('contrat').order_by('date_paiement')
        
        mois_actuel = datetime.now().month
        annee_actuelle = datetime.now().year
        
        corrections = []
        
        for paiement in paiements:
            if not paiement.mois_paye:
                continue
                
            # Extraire le mois et l'année de mois_paye
            mois_paye_str = paiement.mois_paye.strip()
            
            # Trouver le mois dans la chaîne
            mois_num = None
            mois_nom = None
            for nom_mois, num in mois_francais.items():
                if nom_mois.lower() in mois_paye_str.lower():
                    mois_num = num
                    mois_nom = nom_mois
                    break
            
            if not mois_num:
                continue
            
            # Extraire l'année
            annee_match = re.search(r'(\d{4})', mois_paye_str)
            if not annee_match:
                continue
            
            annee_actuelle_paye = int(annee_match.group(1))
            
            # Vérifier si l'année est incorrecte
            # Si on est en novembre/décembre 2025 et que le mois payé est janvier 2025,
            # ça devrait être janvier 2026
            correction_necessaire = False
            nouvelle_annee = annee_actuelle_paye
            
            # Cas 1: On est en décembre et le mois payé est janvier de la même année
            # (devrait être l'année suivante)
            if mois_actuel == 12 and mois_num == 1 and annee_actuelle_paye == annee_actuelle:
                nouvelle_annee = annee_actuelle + 1
                correction_necessaire = True
            
            # Cas 2: On est en novembre/décembre 2025 et le mois payé est janvier 2025
            # mais la date de paiement est en 2025 (devrait être janvier 2026)
            elif mois_actuel >= 11 and mois_num == 1:
                # Vérifier si c'est un paiement récent (créé en novembre/décembre 2025)
                if paiement.date_paiement.year == annee_actuelle and paiement.date_paiement.month >= 11:
                    if annee_actuelle_paye == annee_actuelle:
                        nouvelle_annee = annee_actuelle + 1
                        correction_necessaire = True
            
            # Cas 3: Le mois payé est avant le mois actuel de la même année
            # et on est en fin d'année (novembre/décembre), c'est probablement l'année suivante
            elif mois_actuel >= 11 and mois_num < mois_actuel and annee_actuelle_paye == annee_actuelle:
                # Vérifier si le paiement a été fait récemment
                if paiement.date_paiement.year == annee_actuelle:
                    nouvelle_annee = annee_actuelle + 1
                    correction_necessaire = True
            
            if correction_necessaire:
                nouveau_mois_paye = f"{mois_nom} {nouvelle_annee}"
                corrections.append({
                    'paiement': paiement,
                    'ancien': paiement.mois_paye,
                    'nouveau': nouveau_mois_paye,
                })
        
        if not corrections:
            self.stdout.write(
                self.style.SUCCESS('Aucune correction nécessaire.')
            )
            return
        
        self.stdout.write(f'\n{len(corrections)} paiement(s) à corriger:')
        for corr in corrections:
            self.stdout.write(
                f"  - PAI-{corr['paiement'].id}: {corr['ancien']} -> {corr['nouveau']}"
            )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('\nMode dry-run - Aucun changement ne sera appliqué')
            )
            return
        
        # Appliquer les corrections
        with transaction.atomic():
            for corr in corrections:
                corr['paiement'].mois_paye = corr['nouveau']
                corr['paiement'].save(update_fields=['mois_paye'])
        
        self.stdout.write(
            self.style.SUCCESS(f'\n{len(corrections)} paiement(s) corrigé(s) avec succès!')
        )

