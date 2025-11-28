# Fichier settings_dev pour développement local
# Utilise SQLite en local pour de meilleures performances
import os
from pathlib import Path

# Si on est vraiment en local (pas de RENDER), utiliser settings.py normal
if not os.environ.get('RENDER'):
    from gestion_immobiliere.settings import *
else:
    # Sinon, utiliser PostgreSQL pour les tests distants
    from gestion_immobiliere.settings_postgresql import *

