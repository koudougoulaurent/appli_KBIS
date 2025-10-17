"""
Point d'entrée pour Render - Redirige vers l'application Django
"""
import os
import sys
import django
from django.core.wsgi import get_wsgi_application

# Configuration de l'environnement Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings_postgresql')

# Configuration Django
django.setup()

# EXÉCUTION DU SCRIPT DE MIGRATION INTELLIGENTE
print("🚀 EXÉCUTION DU SCRIPT DE MIGRATION INTELLIGENTE")
print("=" * 60)

try:
    # Importer et exécuter le script de migration
    import migrate_smart
    migrate_smart.create_initial_data()
    print("✅ Données initiales créées avec succès!")
except Exception as e:
    print(f"❌ Erreur lors de la création des données initiales: {e}")
    # Ne pas faire échouer l'application si la création des données échoue
    pass

# Application WSGI
app = get_wsgi_application()
