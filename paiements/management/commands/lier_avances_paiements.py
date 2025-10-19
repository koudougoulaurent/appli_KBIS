"""
Commande pour lier les avances existantes aux paiements correspondants
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from paiements.models import Paiement
from paiements.models_avance import AvanceLoyer
from decimal import Decimal


class Command(BaseCommand):
    help = 'Lie les avances existantes aux paiements correspondants'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Affiche ce qui serait fait sans effectuer les modifications',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('MODE DRY-RUN - Aucune modification ne sera effectuée'))
        
        # Récupérer les avances sans paiement
        avances_sans_paiement = AvanceLoyer.objects.filter(paiement__isnull=True)
        
        # Récupérer les paiements d'avance sans avance liée
        paiements_avance = Paiement.objects.filter(type_paiement='avance')
        
        self.stdout.write(f'Avances sans paiement: {avances_sans_paiement.count()}')
        self.stdout.write(f'Paiements d\'avance: {paiements_avance.count()}')
        
        liaisons_effectuees = 0
        erreurs = 0
        
        # Essayer de lier les avances aux paiements par contrat et montant
        for avance in avances_sans_paiement:
            try:
                # Chercher un paiement d'avance pour le même contrat
                paiements_contrat = paiements_avance.filter(contrat=avance.contrat)
                
                if paiements_contrat.exists():
                    # Essayer de trouver un paiement avec le même montant
                    paiement_meme_montant = paiements_contrat.filter(
                        montant=avance.montant_avance
                    ).first()
                    
                    if paiement_meme_montant:
                        if not dry_run:
                            with transaction.atomic():
                                avance.paiement = paiement_meme_montant
                                avance.save()
                        
                        self.stdout.write(
                            f'[OK] Lié avance {avance.id} ({avance.montant_avance} F CFA) '
                            f'à paiement {paiement_meme_montant.id} pour contrat {avance.contrat.id}'
                        )
                        liaisons_effectuees += 1
                    else:
                        # Prendre le premier paiement du contrat
                        paiement_contrat = paiements_contrat.first()
                        if not dry_run:
                            with transaction.atomic():
                                avance.paiement = paiement_contrat
                                avance.save()
                        
                        self.stdout.write(
                            f'[WARN] Lié avance {avance.id} ({avance.montant_avance} F CFA) '
                            f'à paiement {paiement_contrat.id} ({paiement_contrat.montant} F CFA) '
                            f'pour contrat {avance.contrat.id} (montants différents)'
                        )
                        liaisons_effectuees += 1
                else:
                    self.stdout.write(
                        f'[ERROR] Aucun paiement d\'avance trouvé pour contrat {avance.contrat.id} '
                        f'(avance {avance.id}: {avance.montant_avance} F CFA)'
                    )
                    
            except Exception as e:
                erreurs += 1
                self.stdout.write(
                    self.style.ERROR(f'[ERROR] Erreur lors de la liaison de l\'avance {avance.id}: {str(e)}')
                )
        
        # Résumé
        self.stdout.write('\n' + '='*50)
        self.stdout.write(f'RÉSUMÉ:')
        self.stdout.write(f'Liaisons effectuées: {liaisons_effectuees}')
        self.stdout.write(f'Erreurs: {erreurs}')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('MODE DRY-RUN - Aucune modification n\'a été effectuée'))
        else:
            self.stdout.write(self.style.SUCCESS('Liaisons terminées avec succès!'))
