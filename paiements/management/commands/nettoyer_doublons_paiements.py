"""
Commande pour nettoyer les doublons de paiements non professionnels
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from contrats.models import Contrat
from paiements.validators import ValidateurPaiementUnique
from collections import defaultdict


class Command(BaseCommand):
    help = "Nettoie les doublons de paiements (même mois/contrat)"

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Affiche les doublons sans les supprimer',
        )
        parser.add_argument(
            '--contrat-id',
            type=int,
            help='Nettoyer un contrat spécifique uniquement',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        contrat_id = options.get('contrat_id')
        
        if dry_run:
            self.stdout.write(self.style.WARNING("\n" + "="*80))
            self.stdout.write(self.style.WARNING("MODE DRY-RUN - Aucune suppression"))
            self.stdout.write(self.style.WARNING("="*80 + "\n"))
        
        self.stdout.write("\n" + "="*80)
        self.stdout.write("NETTOYAGE DES DOUBLONS DE PAIEMENTS")
        self.stdout.write("="*80 + "\n")
        
        # Récupérer les contrats à traiter
        if contrat_id:
            contrats = Contrat.objects.filter(id=contrat_id)
            if not contrats.exists():
                self.stdout.write(self.style.ERROR(f"Contrat #{contrat_id} non trouvé"))
                return
        else:
            contrats = Contrat.objects.all()
        
        total_contrats = contrats.count()
        self.stdout.write(f"Traitement de {total_contrats} contrat(s)...\n")
        
        # Statistiques globales
        stats = {
            'contrats_avec_doublons': 0,
            'total_doublons_loyer': 0,
            'total_doublons_avance': 0,
            'total_doublons_caution': 0,
            'total_supprimes': 0
        }
        
        types_a_verifier = ['loyer', 'avance', 'caution']
        
        for contrat in contrats:
            contrat_a_doublons = False
            
            for type_paiement in types_a_verifier:
                resultat = ValidateurPaiementUnique.nettoyer_doublons_existants(
                    contrat, type_paiement, dry_run=dry_run
                )
                
                if resultat['doublons_trouves'] > 0:
                    contrat_a_doublons = True
                    
                    # Afficher les détails
                    self.stdout.write(f"\n{'='*80}")
                    self.stdout.write(f"Contrat: {contrat.locataire.get_nom_complet()} (#{contrat.id})")
                    self.stdout.write(f"Type: {type_paiement.upper()}")
                    self.stdout.write(f"{'='*80}")
                    
                    for doublon in resultat['details']:
                        self.stdout.write(f"\n  Mois: {doublon['mois']}")
                        self.stdout.write(f"  Nombre de paiements: {doublon['nombre']}")
                        
                        # Paiement à garder
                        garde = doublon['garde']
                        self.stdout.write(self.style.SUCCESS(
                            f"  ✓ À GARDER: #{garde.id} - {garde.montant} F CFA - "
                            f"{garde.date_paiement} - {garde.get_statut_display()}"
                        ))
                        
                        # Paiements à supprimer
                        for paiement in doublon['a_supprimer']:
                            if dry_run:
                                self.stdout.write(self.style.WARNING(
                                    f"  ✗ À SUPPRIMER (dry-run): #{paiement.id} - {paiement.montant} F CFA - "
                                    f"{paiement.date_paiement} - {paiement.get_statut_display()}"
                                ))
                            else:
                                self.stdout.write(self.style.ERROR(
                                    f"  ✗ SUPPRIMÉ: #{paiement.id} - {paiement.montant} F CFA - "
                                    f"{paiement.date_paiement} - {paiement.get_statut_display()}"
                                ))
                    
                    # Mettre à jour les statistiques
                    if type_paiement == 'loyer':
                        stats['total_doublons_loyer'] += resultat['doublons_trouves']
                    elif type_paiement == 'avance':
                        stats['total_doublons_avance'] += resultat['doublons_trouves']
                    elif type_paiement == 'caution':
                        stats['total_doublons_caution'] += resultat['doublons_trouves']
                    
                    stats['total_supprimes'] += resultat['doublons_supprimes']
            
            if contrat_a_doublons:
                stats['contrats_avec_doublons'] += 1
        
        # Résumé final
        self.stdout.write("\n" + "="*80)
        self.stdout.write("RÉSUMÉ DU NETTOYAGE")
        self.stdout.write("="*80)
        self.stdout.write(f"\nContrats traités: {total_contrats}")
        self.stdout.write(f"Contrats avec doublons: {stats['contrats_avec_doublons']}")
        self.stdout.write(f"\nDoublons par type:")
        self.stdout.write(f"  - Loyer: {stats['total_doublons_loyer']}")
        self.stdout.write(f"  - Avance: {stats['total_doublons_avance']}")
        self.stdout.write(f"  - Caution: {stats['total_doublons_caution']}")
        
        total_doublons = (stats['total_doublons_loyer'] + 
                         stats['total_doublons_avance'] + 
                         stats['total_doublons_caution'])
        
        self.stdout.write(f"\nTotal doublons détectés: {total_doublons}")
        
        if dry_run:
            self.stdout.write(self.style.WARNING(
                f"\nDRY-RUN : Aucune suppression effectuée"
            ))
            self.stdout.write("Relancez sans --dry-run pour supprimer réellement")
        else:
            self.stdout.write(self.style.SUCCESS(
                f"\n✓ {stats['total_supprimes']} doublon(s) supprimé(s)"
            ))
        
        self.stdout.write("\n" + "="*80 + "\n")
