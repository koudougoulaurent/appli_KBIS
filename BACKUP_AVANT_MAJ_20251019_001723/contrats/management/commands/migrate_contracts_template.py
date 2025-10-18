#!/usr/bin/env python
"""
Commande de migration pour remplir automatiquement les nouveaux champs des contrats
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from contrats.models import Contrat
from contrats.services_contrat_pdf_updated import ContratPDFServiceUpdated
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Migre les contrats existants pour remplir les nouveaux champs de template'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Affiche ce qui sera fait sans effectuer les modifications',
        )
        parser.add_argument(
            '--contrat-id',
            type=int,
            help='Migre un contrat spécifique par son ID',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        contrat_id = options.get('contrat_id')
        
        self.stdout.write(
            self.style.SUCCESS('Debut de la migration des contrats...')
        )
        
        # Récupérer les contrats à migrer
        if contrat_id:
            contrats = Contrat.objects.filter(id=contrat_id)
            if not contrats.exists():
                self.stdout.write(
                    self.style.ERROR(f'❌ Aucun contrat trouvé avec l\'ID {contrat_id}')
                )
                return
        else:
            contrats = Contrat.objects.all()
        
        total_contrats = contrats.count()
        self.stdout.write(f'Nombre de contrats a migrer: {total_contrats}')
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('Mode DRY-RUN - Aucune modification ne sera effectuee')
            )
        
        # Statistiques
        stats = {
            'migres': 0,
            'erreurs': 0,
            'deja_complets': 0,
        }
        
        for contrat in contrats:
            try:
                # Vérifier si le contrat a déjà des champs remplis
                if (contrat.loyer_mensuel_texte and 
                    contrat.depot_garantie_texte and 
                    contrat.montant_garantie_max):
                    stats['deja_complets'] += 1
                    self.stdout.write(f'Contrat {contrat.id} deja complet')
                    continue
                
                if dry_run:
                    self.stdout.write(f'Contrat {contrat.id} sera migre')
                    stats['migres'] += 1
                    continue
                
                # Migrer le contrat
                with transaction.atomic():
                    service = ContratPDFServiceUpdated(contrat)
                    service.auto_remplir_champs_contrat()
                    
                    stats['migres'] += 1
                    self.stdout.write(f'Contrat {contrat.id} migre avec succes')
                    
            except Exception as e:
                stats['erreurs'] += 1
                self.stdout.write(
                    self.style.ERROR(f'Erreur lors de la migration du contrat {contrat.id}: {str(e)}')
                )
                logger.error(f'Erreur migration contrat {contrat.id}: {str(e)}')
        
        # Afficher les statistiques finales
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('RESULTATS DE LA MIGRATION'))
        self.stdout.write('='*50)
        self.stdout.write(f'Contrats migres: {stats["migres"]}')
        self.stdout.write(f'Contrats deja complets: {stats["deja_complets"]}')
        self.stdout.write(f'Erreurs: {stats["erreurs"]}')
        self.stdout.write(f'Total traite: {stats["migres"] + stats["deja_complets"] + stats["erreurs"]}')
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('\nMode DRY-RUN - Aucune modification n\'a ete effectuee')
            )
            self.stdout.write('Pour effectuer la migration, relancez sans --dry-run')
        else:
            self.stdout.write(
                self.style.SUCCESS('\nMigration terminee avec succes!')
            )
