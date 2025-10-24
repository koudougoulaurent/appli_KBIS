"""
Commande Django pour corriger les mois payés manquants
Remplit automatiquement le champ mois_paye pour les paiements existants
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from paiements.models import Paiement
import locale
from datetime import datetime


class Command(BaseCommand):
    help = 'Corrige les mois payés manquants pour les paiements existants'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Affiche les changements sans les appliquer',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        self.stdout.write(
            self.style.SUCCESS('Correction des mois payés manquants...')
        )
        
        # Trouver tous les paiements sans mois_paye
        paiements_sans_mois = Paiement.objects.filter(
            mois_paye__isnull=True
        ) | Paiement.objects.filter(
            mois_paye=''
        )
        
        total_a_corriger = paiements_sans_mois.count()
        
        if total_a_corriger == 0:
            self.stdout.write(
                self.style.SUCCESS('Aucun paiement à corriger trouvé.')
            )
            return
        
        self.stdout.write(f'Paiements à corriger : {total_a_corriger}')
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('Mode dry-run - Aucun changement ne sera appliqué')
            )
        
        # Configurer la locale française
        try:
            locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')
        except:
            try:
                locale.setlocale(locale.LC_TIME, 'French_France.1252')
            except:
                self.stdout.write(
                    self.style.WARNING('Impossible de définir la locale française, utilisation de la locale par défaut')
                )
        
        corrections_appliquees = 0
        
        for paiement in paiements_sans_mois:
            # Générer le mois payé basé sur la date de paiement
            try:
                mois_nom = paiement.date_paiement.strftime('%B').capitalize()
                annee = paiement.date_paiement.year
                mois_paye = f"{mois_nom} {annee}"
                
                if dry_run:
                    self.stdout.write(
                        f'  - PAI-{paiement.id}: {paiement.date_paiement.strftime("%d/%m/%Y")} -> {mois_paye}'
                    )
                else:
                    with transaction.atomic():
                        paiement.mois_paye = mois_paye
                        paiement.save()
                        corrections_appliquees += 1
                        
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Erreur pour PAI-{paiement.id}: {str(e)}')
                )
        
        if not dry_run:
            self.stdout.write(
                self.style.SUCCESS(f'{corrections_appliquees} paiements corrigés')
            )
        
        # Vérifier les statistiques
        self.stdout.write('\nStatistiques des mois payés :')
        paiements_avec_mois = Paiement.objects.exclude(
            mois_paye__isnull=True
        ).exclude(
            mois_paye=''
        ).count()
        
        paiements_sans_mois_restants = Paiement.objects.filter(
            mois_paye__isnull=True
        ) | Paiement.objects.filter(
            mois_paye=''
        )
        
        self.stdout.write(f'  - Paiements avec mois payé : {paiements_avec_mois}')
        self.stdout.write(f'  - Paiements sans mois payé : {paiements_sans_mois_restants.count()}')
        
        self.stdout.write(
            self.style.SUCCESS('\nCorrection terminée !')
        )
