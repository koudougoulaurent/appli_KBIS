from django.core.management.base import BaseCommand
from django.db import transaction
from contrats.models import Contrat
from paiements.models import Paiement
from decimal import Decimal

class Command(BaseCommand):
    help = 'Corrige les statuts de paiement pour tous les contrats'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Affiche les corrections sans les appliquer',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('Mode DRY-RUN activé - Aucune modification ne sera appliquée'))
        
        self.stdout.write('=== CORRECTION DES STATUTS DE PAIEMENT ===')
        
        # Récupérer tous les contrats actifs
        contrats = Contrat.objects.filter(
            est_actif=True,
            est_resilie=False
        ).select_related('propriete', 'locataire')
        
        self.stdout.write(f'Nombre de contrats à traiter: {contrats.count()}')
        
        contrats_corriges = 0
        contrats_avec_problemes = 0
        
        with transaction.atomic():
            for contrat in contrats:
                # Montants requis
                caution_requise = Decimal(str(contrat.depot_garantie)) if contrat.depot_garantie else Decimal('0')
                avance_requise = Decimal(str(contrat.avance_loyer)) if contrat.avance_loyer else Decimal('0')
                
                # Calculer les montants payés avec tous les types possibles
                paiements_caution = Paiement.objects.filter(
                    contrat=contrat,
                    type_paiement__in=['caution', 'depot_garantie'],
                    statut='valide'
                )
                
                montant_caution_paye = sum(p.montant for p in paiements_caution)
                
                paiements_avance = Paiement.objects.filter(
                    contrat=contrat,
                    type_paiement__in=['avance_loyer', 'avance'],
                    statut='valide'
                )
                
                montant_avance_paye = sum(p.montant for p in paiements_avance)
                
                # Vérifier les statuts
                caution_payee = montant_caution_paye >= caution_requise if caution_requise > 0 else True
                avance_payee = montant_avance_paye >= avance_requise if avance_requise > 0 else True
                
                # Vérifier si des corrections sont nécessaires
                contrat_modified = False
                
                if contrat.caution_payee != caution_payee:
                    self.stdout.write(
                        f'  Contrat {contrat.numero_contrat}: Correction caution {contrat.caution_payee} -> {caution_payee}'
                    )
                    if not dry_run:
                        contrat.caution_payee = caution_payee
                    contrat_modified = True
                
                if contrat.avance_loyer_payee != avance_payee:
                    self.stdout.write(
                        f'  Contrat {contrat.numero_contrat}: Correction avance {contrat.avance_loyer_payee} -> {avance_payee}'
                    )
                    if not dry_run:
                        contrat.avance_loyer_payee = avance_payee
                    contrat_modified = True
                
                if contrat_modified:
                    if not dry_run:
                        contrat.save()
                    contrats_corriges += 1
                
                # Vérifier les problèmes
                if caution_requise > 0 and not caution_payee:
                    self.stdout.write(
                        self.style.WARNING(
                            f'  ! ATTENTION: Contrat {contrat.numero_contrat} - Caution non payée '
                            f'(requis: {caution_requise}, payé: {montant_caution_paye})'
                        )
                    )
                    contrats_avec_problemes += 1
                
                if avance_requise > 0 and not avance_payee:
                    self.stdout.write(
                        self.style.WARNING(
                            f'  ! ATTENTION: Contrat {contrat.numero_contrat} - Avance non payée '
                            f'(requis: {avance_requise}, payé: {montant_avance_paye})'
                        )
                    )
                    contrats_avec_problemes += 1
        
        self.stdout.write('\n=== RÉSUMÉ ===')
        self.stdout.write(f'Contrats traités: {contrats.count()}')
        self.stdout.write(f'Contrats corrigés: {contrats_corriges}')
        self.stdout.write(f'Contrats avec problèmes: {contrats_avec_problemes}')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('Mode DRY-RUN - Aucune modification appliquée'))
        else:
            self.stdout.write(self.style.SUCCESS('Correction terminée avec succès!'))
