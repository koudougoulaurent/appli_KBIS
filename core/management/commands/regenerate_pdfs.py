"""
Commande Django pour régénérer tous les PDF
"""

from django.core.management.base import BaseCommand
from core.pdf_cache import PDFRegenerationService, PDFCacheManager
from core.signals import force_regenerate_all_documents

class Command(BaseCommand):
    help = 'Régénère tous les documents PDF avec la configuration actuelle'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force la régénération même si le cache est valide',
        )
        parser.add_argument(
            '--type',
            type=str,
            choices=['contrat', 'resiliation', 'all'],
            default='all',
            help='Type de document à régénérer',
        )
        parser.add_argument(
            '--clear-cache',
            action='store_true',
            help='Vide le cache avant la régénération',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🚀 Démarrage de la régénération des PDF...')
        )
        
        # Vider le cache si demandé
        if options['clear_cache']:
            self.stdout.write('🗑️ Vidage du cache...')
            PDFCacheManager.invalidate_all_pdf_cache()
        
        # Régénérer selon le type demandé
        if options['type'] == 'all':
            result = PDFRegenerationService.regenerate_all_documents()
        elif options['type'] == 'contrat':
            result = PDFRegenerationService.regenerate_all_contracts()
        elif options['type'] == 'resiliation':
            result = PDFRegenerationService.regenerate_all_resiliations()
        
        # Afficher les résultats
        if result['success']:
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Régénération terminée: {result.get("total_regenerated", 0)} documents mis à jour'
                )
            )
            
            # Afficher les détails par type
            if 'contracts' in result:
                contracts = result['contracts']
                self.stdout.write(
                    f'📄 Contrats: {contracts["regenerated_count"]}/{contracts["total_count"]} régénérés'
                )
                if contracts.get('errors'):
                    for error in contracts['errors']:
                        self.stdout.write(
                            self.style.WARNING(f'⚠️ {error}')
                        )
            
            if 'resiliations' in result:
                resiliations = result['resiliations']
                self.stdout.write(
                    f'📄 Résiliations: {resiliations["regenerated_count"]}/{resiliations["total_count"]} régénérés'
                )
                if resiliations.get('errors'):
                    for error in resiliations['errors']:
                        self.stdout.write(
                            self.style.WARNING(f'⚠️ {error}')
                        )
        else:
            self.stdout.write(
                self.style.ERROR(f'❌ Erreur lors de la régénération: {result.get("error", "Erreur inconnue")}')
            )
        
        # Afficher les statistiques du cache
        cache_stats = PDFCacheManager.get_cache_stats()
        self.stdout.write(f'📊 Hash de configuration actuel: {cache_stats["current_config_hash"]}')
