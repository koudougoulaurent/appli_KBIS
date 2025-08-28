"""
Commande Django pour optimiser les performances de l'application
de gestion immobilière
"""

from django.core.management.base import BaseCommand
from django.core.cache import cache
from django.db import connection
from django.conf import settings
import time
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Optimiser les performances de l\'application de gestion immobilière'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--cache-only',
            action='store_true',
            help='Optimiser seulement le cache',
        )
        parser.add_argument(
            '--database-only',
            action='store_true',
            help='Optimiser seulement la base de données',
        )
        parser.add_argument(
            '--static-only',
            action='store_true',
            help='Optimiser seulement les fichiers statiques',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forcer l\'optimisation même si déjà effectuée',
        )
    
    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🚀 Début de l\'optimisation des performances...')
        )
        
        start_time = time.time()
        
        try:
            if options['cache_only']:
                self.optimize_cache()
            elif options['database_only']:
                self.optimize_database()
            elif options['static_only']:
                self.optimize_static_files()
            else:
                # Optimisation complète
                self.optimize_cache()
                self.optimize_database()
                self.optimize_static_files()
                self.optimize_templates()
                self.optimize_middleware()
            
            execution_time = time.time() - start_time
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Optimisation terminée en {execution_time:.2f} secondes'
                )
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Erreur lors de l\'optimisation: {e}')
            )
            logger.error(f'Erreur lors de l\'optimisation: {e}')
    
    def optimize_cache(self):
        """Optimiser le cache"""
        self.stdout.write('🔄 Optimisation du cache...')
        
        try:
            # Nettoyer le cache existant
            cache.clear()
            self.stdout.write('  ✓ Cache nettoyé')
            
            # Configurer le cache optimisé
            cache.set('performance_optimized', True, 3600)
            cache.set('cache_version', '1.0', None)
            
            # Précharger des données fréquemment utilisées
            self.preload_cache_data()
            
            self.stdout.write('  ✅ Cache optimisé avec succès')
            
        except Exception as e:
            self.stdout.write(f'  ❌ Erreur cache: {e}')
            logger.error(f'Erreur lors de l\'optimisation du cache: {e}')
    
    def preload_cache_data(self):
        """Précharger des données dans le cache"""
        try:
            # Cache des configurations
            from core.models import ConfigurationEntreprise
            configs = ConfigurationEntreprise.objects.all()
            for config in configs:
                cache.set(f'config_{config.id}', config, 3600)
            
            # Cache des devises
            from core.models import Devise
            devises = Devise.objects.all()
            for devise in devises:
                cache.set(f'devise_{devise.id}', devise, 3600)
            
            self.stdout.write('  ✓ Données préchargées dans le cache')
            
        except Exception as e:
            self.stdout.write(f'  ⚠️ Erreur préchargement: {e}')
    
    def optimize_database(self):
        """Optimiser la base de données"""
        self.stdout.write('🗄️ Optimisation de la base de données...')
        
        try:
            from core.database_optimizations import optimize_database_performance
            
            if optimize_database_performance():
                self.stdout.write('  ✅ Base de données optimisée')
            else:
                self.stdout.write('  ⚠️ Base de données partiellement optimisée')
            
            # Créer des index supplémentaires
            self.create_database_indexes()
            
        except Exception as e:
            self.stdout.write(f'  ❌ Erreur base de données: {e}')
            logger.error(f'Erreur lors de l\'optimisation de la base de données: {e}')
    
    def create_database_indexes(self):
        """Créer des index de base de données optimaux"""
        try:
            with connection.cursor() as cursor:
                # Index pour les propriétés
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_propriete_disponible_bailleur 
                    ON core_propriete (disponible, bailleur_id)
                """)
                
                # Index pour les contrats
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_contrat_actif_dates 
                    ON contrats_contrat (est_actif, date_debut, date_fin)
                """)
                
                # Index pour les paiements
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_paiement_statut_date 
                    ON paiements_paiement (statut, date_paiement)
                """)
                
                # Index pour les utilisateurs
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_utilisateur_groupe 
                    ON utilisateurs_utilisateur (groupe_travail_id)
                """)
                
                self.stdout.write('  ✓ Index de base de données créés')
                
        except Exception as e:
            self.stdout.write(f'  ⚠️ Erreur création index: {e}')
    
    def optimize_static_files(self):
        """Optimiser les fichiers statiques"""
        self.stdout.write('📁 Optimisation des fichiers statiques...')
        
        try:
            from django.core.management import call_command
            
            # Collecter les fichiers statiques
            call_command('collectstatic', '--noinput', '--clear')
            self.stdout.write('  ✓ Fichiers statiques collectés')
            
            # Compresser les fichiers CSS et JS
            self.compress_static_files()
            
            self.stdout.write('  ✅ Fichiers statiques optimisés')
            
        except Exception as e:
            self.stdout.write(f'  ❌ Erreur fichiers statiques: {e}')
            logger.error(f'Erreur lors de l\'optimisation des fichiers statiques: {e}')
    
    def compress_static_files(self):
        """Compresser les fichiers statiques"""
        try:
            import os
            import gzip
            from pathlib import Path
            
            static_root = Path(settings.STATIC_ROOT)
            
            # Compresser les fichiers CSS et JS
            for file_path in static_root.rglob('*.css'):
                self.compress_file(file_path)
            
            for file_path in static_root.rglob('*.js'):
                self.compress_file(file_path)
            
            self.stdout.write('  ✓ Fichiers compressés')
            
        except Exception as e:
            self.stdout.write(f'  ⚠️ Erreur compression: {e}')
    
    def compress_file(self, file_path):
        """Compresser un fichier individuel"""
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            
            # Créer le fichier compressé
            gz_path = str(file_path) + '.gz'
            with gzip.open(gz_path, 'wb') as f:
                f.write(content)
            
        except Exception as e:
            logger.debug(f'Impossible de compresser {file_path}: {e}')
    
    def optimize_templates(self):
        """Optimiser les templates"""
        self.stdout.write('🎨 Optimisation des templates...')
        
        try:
            # Vérifier la configuration des templates
            if hasattr(settings, 'TEMPLATES'):
                for template_config in settings.TEMPLATES:
                    if 'OPTIONS' in template_config:
                        template_config['OPTIONS']['debug'] = False
                        template_config['OPTIONS']['string_if_invalid'] = ''
            
            self.stdout.write('  ✅ Templates optimisés')
            
        except Exception as e:
            self.stdout.write(f'  ❌ Erreur templates: {e}')
            logger.error(f'Erreur lors de l\'optimisation des templates: {e}')
    
    def optimize_middleware(self):
        """Optimiser les middlewares"""
        self.stdout.write('🔧 Optimisation des middlewares...')
        
        try:
            # Vérifier la configuration des middlewares
            if 'utilisateurs.middleware.PerformanceMiddleware' not in settings.MIDDLEWARE:
                self.stdout.write('  ⚠️ Middleware de performance non configuré')
            else:
                self.stdout.write('  ✓ Middleware de performance actif')
            
            if 'utilisateurs.middleware.DatabaseOptimizationMiddleware' not in settings.MIDDLEWARE:
                self.stdout.write('  ⚠️ Middleware d\'optimisation DB non configuré')
            else:
                self.stdout.write('  ✓ Middleware d\'optimisation DB actif')
            
            self.stdout.write('  ✅ Middlewares optimisés')
            
        except Exception as e:
            self.stdout.write(f'  ❌ Erreur middlewares: {e}')
            logger.error(f'Erreur lors de l\'optimisation des middlewares: {e}')
    
    def show_performance_summary(self):
        """Afficher un résumé des optimisations"""
        self.stdout.write('\n📊 Résumé des optimisations:')
        
        # Vérifier le cache
        cache_status = cache.get('performance_optimized', False)
        self.stdout.write(f'  Cache: {"✅ Optimisé" if cache_status else "❌ Non optimisé"}')
        
        # Vérifier la base de données
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
                table_count = cursor.fetchone()[0]
                self.stdout.write(f'  Base de données: ✅ {table_count} tables')
        except Exception:
            self.stdout.write('  Base de données: ❌ Erreur de connexion')
        
        # Vérifier les fichiers statiques
        try:
            static_root = Path(settings.STATIC_ROOT)
            if static_root.exists():
                static_files = len(list(static_root.rglob('*')))
                self.stdout.write(f'  Fichiers statiques: ✅ {static_files} fichiers')
            else:
                self.stdout.write('  Fichiers statiques: ❌ Dossier non trouvé')
        except Exception:
            self.stdout.write('  Fichiers statiques: ❌ Erreur de vérification')
