"""
Commande de management pour migrer tous les bailleurs existants vers le système de contrat de gestion.

Usage:
    python manage.py migrer_contrats_gestion
    
Cette commande:
- Crée un contrat de gestion pour tous les bailleurs qui ont des propriétés mais pas de contrat
- S'assure qu'un bailleur n'a qu'un seul contrat de gestion
- Inclut toutes les propriétés du bailleur dans son contrat unique
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from proprietes.models import Bailleur, Propriete, ContratGestion
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Migre tous les bailleurs existants vers le système de contrat de gestion unique'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Affiche ce qui sera fait sans effectuer les modifications',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force la migration même si des contrats existent déjà',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        force = options['force']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('Mode DRY-RUN: Aucune modification ne sera effectuée'))
        
        # Statistiques
        stats = {
            'bailleurs_traites': 0,
            'contrats_crees': 0,
            'contrats_fusionnes': 0,
            'proprietes_ajoutees': 0,
            'erreurs': 0
        }
        
        # Récupérer tous les bailleurs actifs
        bailleurs = Bailleur.objects.filter(is_deleted=False)
        total_bailleurs = bailleurs.count()
        
        self.stdout.write(f'\n{"="*60}')
        self.stdout.write(f'Migration des contrats de gestion')
        self.stdout.write(f'{"="*60}')
        self.stdout.write(f'Total bailleurs à traiter: {total_bailleurs}\n')
        
        for bailleur in bailleurs:
            try:
                # Récupérer toutes les propriétés du bailleur
                proprietes_bailleur = Propriete.objects.filter(
                    bailleur=bailleur,
                    is_deleted=False
                )
                
                # Si le bailleur n'a pas de propriétés, on passe
                if not proprietes_bailleur.exists():
                    continue
                
                stats['bailleurs_traites'] += 1
                
                # Récupérer tous les contrats de gestion du bailleur
                contrats_existants = ContratGestion.objects.filter(
                    bailleur=bailleur,
                    is_deleted=False
                )
                
                if contrats_existants.count() == 0:
                    # Pas de contrat, créer un nouveau contrat
                    if not dry_run:
                        with transaction.atomic():
                            contrat_gestion = ContratGestion.objects.create(
                                bailleur=bailleur,
                                date_signature=timezone.now().date(),
                                date_debut=timezone.now().date(),
                                commission_percentage=10.00,
                                est_actif=True,
                                est_resilie=False,
                            )
                            contrat_gestion.proprietes.set(proprietes_bailleur)
                            stats['contrats_crees'] += 1
                            stats['proprietes_ajoutees'] += proprietes_bailleur.count()
                    
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'[CREATION] {bailleur.get_nom_complet()}: '
                            f'Contrat créé avec {proprietes_bailleur.count()} propriété(s)'
                        )
                    )
                
                elif contrats_existants.count() == 1:
                    # Un seul contrat, s'assurer qu'il inclut toutes les propriétés
                    contrat = contrats_existants.first()
                    proprietes_actuelles = contrat.get_proprietes_list()
                    
                    # Vérifier si toutes les propriétés sont incluses
                    proprietes_manquantes = proprietes_bailleur.exclude(
                        id__in=proprietes_actuelles.values_list('id', flat=True)
                    )
                    
                    if proprietes_manquantes.exists() or force:
                        if not dry_run:
                            with transaction.atomic():
                                contrat.proprietes.set(proprietes_bailleur)
                                stats['proprietes_ajoutees'] += proprietes_manquantes.count()
                        
                        self.stdout.write(
                            self.style.WARNING(
                                f'[MISE A JOUR] {bailleur.get_nom_complet()}: '
                                f'Contrat {contrat.numero_contrat} mis à jour avec {proprietes_manquantes.count()} propriété(s) ajoutée(s)'
                            )
                        )
                    else:
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'[OK] {bailleur.get_nom_complet()}: '
                                f'Contrat {contrat.numero_contrat} déjà à jour'
                            )
                        )
                
                else:
                    # Plusieurs contrats, fusionner en un seul
                    if not dry_run:
                        with transaction.atomic():
                            # Garder le contrat le plus récent
                            contrat_principal = max(contrats_existants, key=lambda c: c.date_signature)
                            autres_contrats = [c for c in contrats_existants if c.id != contrat_principal.id]
                            
                            # Mettre à jour le contrat principal avec toutes les propriétés
                            contrat_principal.proprietes.set(proprietes_bailleur)
                            
                            # Supprimer logiquement les autres contrats
                            for contrat in autres_contrats:
                                contrat.is_deleted = True
                                contrat.save()
                            
                            stats['contrats_fusionnes'] += len(autres_contrats)
                            stats['proprietes_ajoutees'] += proprietes_bailleur.count()
                    
                    self.stdout.write(
                        self.style.WARNING(
                            f'[FUSION] {bailleur.get_nom_complet()}: '
                            f'{contrats_existants.count()} contrats fusionnés en un seul ({contrat_principal.numero_contrat})'
                        )
                    )
                
            except Exception as e:
                stats['erreurs'] += 1
                self.stdout.write(
                    self.style.ERROR(
                        f'[ERREUR] {bailleur.get_nom_complet()}: {str(e)}'
                    )
                )
                logger.error(f"Erreur lors de la migration du bailleur {bailleur.id}: {str(e)}")
        
        # Afficher les statistiques finales
        self.stdout.write(f'\n{"="*60}')
        self.stdout.write(f'Résumé de la migration')
        self.stdout.write(f'{"="*60}')
        self.stdout.write(f'Bailleurs traités: {stats["bailleurs_traites"]}')
        self.stdout.write(f'Contrats créés: {stats["contrats_crees"]}')
        self.stdout.write(f'Contrats fusionnés: {stats["contrats_fusionnes"]}')
        self.stdout.write(f'Propriétés ajoutées: {stats["proprietes_ajoutees"]}')
        self.stdout.write(f'Erreurs: {stats["erreurs"]}')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\nMode DRY-RUN: Aucune modification effectuée'))
        else:
            self.stdout.write(self.style.SUCCESS('\nMigration terminée avec succès!'))

