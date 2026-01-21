"""
Commande pour corriger les champs mois_paye manquants dans les paiements
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from paiements.models import Paiement
from datetime import datetime
import re


class Command(BaseCommand):
    help = "Corrige les champs mois_paye manquants dans les paiements"

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Affiche les modifications sans les appliquer',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING("MODE DRY-RUN - Aucune modification ne sera appliquée"))
        
        # Dictionnaire pour convertir les mois
        mois_francais = {
            1: 'janvier', 2: 'février', 3: 'mars', 4: 'avril',
            5: 'mai', 6: 'juin', 7: 'juillet', 8: 'août',
            9: 'septembre', 10: 'octobre', 11: 'novembre', 12: 'décembre'
        }
        
        # Fonction pour extraire le mois du libellé
        def extraire_mois_du_libelle(libelle):
            """Extrait le mois du libellé si possible"""
            if not libelle:
                return None
            
            libelle_lower = libelle.lower()
            
            # Chercher un pattern "loyer XXX YYYY" ou "XXX YYYY"
            for mois_num, mois_nom in mois_francais.items():
                if mois_nom in libelle_lower:
                    # Chercher l'année
                    annee_match = re.search(r'(\d{4})', libelle)
                    if annee_match:
                        annee = annee_match.group(1)
                        return f"{mois_nom} {annee}"
            
            return None
        
        # Récupérer tous les paiements sans mois_paye renseigné
        paiements_sans_mois = Paiement.objects.filter(
            type_paiement__in=['loyer', 'paiement_partiel']
        ).filter(
            mois_paye__isnull=True
        ) | Paiement.objects.filter(
            type_paiement__in=['loyer', 'paiement_partiel'],
            mois_paye=''
        )
        
        total = paiements_sans_mois.count()
        self.stdout.write(f"\nTrouvé {total} paiements sans mois_paye renseigné")
        
        if total == 0:
            self.stdout.write(self.style.SUCCESS("\nAucun paiement à corriger"))
            return
        
        corrigés = 0
        non_corrigés = 0
        
        with transaction.atomic():
            for paiement in paiements_sans_mois:
                mois_paye_calcule = None
                
                # 1. Essayer d'extraire du libellé
                if paiement.libelle:
                    mois_paye_calcule = extraire_mois_du_libelle(paiement.libelle)
                
                # 2. Si pas trouvé, utiliser la date de paiement
                if not mois_paye_calcule:
                    mois_num = paiement.date_paiement.month
                    annee = paiement.date_paiement.year
                    mois_nom = mois_francais[mois_num]
                    mois_paye_calcule = f"{mois_nom} {annee}"
                
                if mois_paye_calcule:
                    self.stdout.write(
                        f"  Paiement {paiement.id} (date: {paiement.date_paiement}) "
                        f"→ mois_paye: {mois_paye_calcule}"
                    )
                    
                    if not dry_run:
                        paiement.mois_paye = mois_paye_calcule
                        paiement.save(update_fields=['mois_paye'])
                    
                    corrigés += 1
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f"  Paiement {paiement.id} : Impossible de déterminer le mois"
                        )
                    )
                    non_corrigés += 1
        
        self.stdout.write("\n" + "-" * 60)
        self.stdout.write(f"Paiements corrigés : {corrigés}")
        self.stdout.write(f"Paiements non corrigés : {non_corrigés}")
        
        if dry_run:
            self.stdout.write(self.style.WARNING("\nDRY-RUN : Aucune modification appliquée"))
            self.stdout.write("Exécutez sans --dry-run pour appliquer les modifications")
        else:
            self.stdout.write(self.style.SUCCESS("\nCorrection terminée avec succès !"))
