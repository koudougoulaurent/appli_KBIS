"""
Commande de management pour vérifier et compléter automatiquement 
tous les paiements partiels qui ont été complétés.
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from paiements.models import Paiement
from paiements.services_paiement_partiel import ServicePaiementPartiel
from decimal import Decimal
from collections import defaultdict


class Command(BaseCommand):
    help = 'Vérifie et complète automatiquement les paiements partiels dont le reliquat est soldé'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Affiche les modifications sans les appliquer',
        )
        parser.add_argument(
            '--contrat-id',
            type=int,
            help='Vérifier uniquement pour un contrat spécifique',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        contrat_id = options.get('contrat_id')
        
        self.stdout.write(self.style.WARNING('=' * 80))
        self.stdout.write(self.style.WARNING('VÉRIFICATION ET COMPLÉTION DES PAIEMENTS PARTIELS'))
        self.stdout.write(self.style.WARNING('=' * 80))
        
        if dry_run:
            self.stdout.write(self.style.NOTICE('MODE DRY-RUN : Aucune modification ne sera effectuée'))
        
        # Récupérer tous les paiements partiels actifs
        paiements_partiels = Paiement.objects.filter(
            est_paiement_partiel=True,
            statut='valide',
            is_deleted=False
        ).select_related('contrat', 'contrat__locataire', 'contrat__propriete')
        
        if contrat_id:
            paiements_partiels = paiements_partiels.filter(contrat_id=contrat_id)
            self.stdout.write(f'\nVérification pour le contrat ID {contrat_id}')
        
        # Grouper par contrat et mois
        paiements_par_mois = defaultdict(list)
        for paiement in paiements_partiels:
            if paiement.mois_paye:
                cle = (paiement.contrat.id, paiement.mois_paye)
                paiements_par_mois[cle].append(paiement)
        
        total_mois = len(paiements_par_mois)
        self.stdout.write(f'\n{total_mois} mois avec paiements partiels à vérifier\n')
        
        if total_mois == 0:
            self.stdout.write(self.style.WARNING('Aucun paiement partiel à vérifier'))
            return
        
        mois_completes = 0
        mois_incomplets = 0
        total_paiements_completes = 0
        erreurs = 0
        
        for (contrat_id, mois_paye), paiements in paiements_par_mois.items():
            try:
                contrat = paiements[0].contrat
                
                # Calculer le montant restant pour ce mois
                calcul = ServicePaiementPartiel.calculer_montant_restant(contrat, mois_paye)
                
                montant_du_mois = calcul['montant_du_mois']
                montant_paye = calcul['montant_paye']
                montant_restant = calcul['montant_restant']
                est_complet = calcul['est_complet']
                
                self.stdout.write(
                    f'\n📋 {contrat.numero_contrat} - {mois_paye}'
                )
                self.stdout.write(
                    f'   Locataire: {contrat.locataire.get_nom_complet() if contrat.locataire else "N/A"}'
                )
                self.stdout.write(
                    f'   Montant dû     : {montant_du_mois:>12} F CFA'
                )
                self.stdout.write(
                    f'   Montant payé   : {montant_paye:>12} F CFA'
                )
                self.stdout.write(
                    f'   Montant restant: {montant_restant:>12} F CFA'
                )
                self.stdout.write(
                    f'   Nb paiements   : {len(paiements)}'
                )
                
                if est_complet:
                    # Le mois est complété
                    self.stdout.write(
                        self.style.SUCCESS(f'   ✅ COMPLET - Marquage de {len(paiements)} paiement(s) comme complété(s)')
                    )
                    
                    if not dry_run:
                        # Utiliser la méthode verifier_et_completer_reliquat pour garantir la cohérence
                        with transaction.atomic():
                            # Prendre le premier paiement comme référence pour déclencher la vérification
                            premier_paiement = paiements[0]
                            completion_effectuee = ServicePaiementPartiel.verifier_et_completer_reliquat(
                                paiement=premier_paiement,
                                skip_save=True
                            )
                            if completion_effectuee:
                                total_paiements_completes += len(paiements)
                    else:
                        total_paiements_completes += len(paiements)
                    
                    mois_completes += 1
                else:
                    # Le mois n'est pas encore complété
                    self.stdout.write(
                        self.style.WARNING(f'   ⏳ INCOMPLET - Reste {montant_restant} F CFA à payer')
                    )
                    
                    # Mettre à jour les montants restants en utilisant verifier_et_completer_reliquat
                    # pour garantir la cohérence
                    if not dry_run:
                        with transaction.atomic():
                            # Prendre le premier paiement comme référence pour déclencher la mise à jour
                            premier_paiement = paiements[0]
                            ServicePaiementPartiel.verifier_et_completer_reliquat(
                                paiement=premier_paiement,
                                skip_save=True
                            )
                    
                    mois_incomplets += 1
                    
            except Exception as e:
                erreurs += 1
                self.stdout.write(
                    self.style.ERROR(f'\n✗ ERREUR pour {contrat.numero_contrat} - {mois_paye}')
                )
                self.stdout.write(self.style.ERROR(f'  {str(e)}'))
        
        # Résumé final
        self.stdout.write('\n')
        self.stdout.write(self.style.WARNING('=' * 80))
        self.stdout.write(self.style.WARNING('RÉSUMÉ DE LA VÉRIFICATION'))
        self.stdout.write(self.style.WARNING('=' * 80))
        self.stdout.write(f'\nTotal mois vérifiés : {total_mois}')
        self.stdout.write(self.style.SUCCESS(f'Mois complétés      : {mois_completes}'))
        self.stdout.write(f'Mois incomplets     : {mois_incomplets}')
        self.stdout.write(self.style.SUCCESS(f'Paiements complétés : {total_paiements_completes}'))
        
        if erreurs > 0:
            self.stdout.write(self.style.ERROR(f'Erreurs             : {erreurs}'))
        
        if dry_run:
            self.stdout.write(self.style.NOTICE('\nMODE DRY-RUN : Aucune modification n\'a été enregistrée'))
            self.stdout.write(self.style.NOTICE('Exécutez sans --dry-run pour appliquer les modifications'))
        else:
            self.stdout.write(self.style.SUCCESS('\n✓ Vérification et complétion terminées avec succès !'))
        
        self.stdout.write('')
