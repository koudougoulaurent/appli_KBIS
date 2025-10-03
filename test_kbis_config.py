
# Script de test pour vérifier l'en-tête KBIS
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from core.models import ConfigurationEntreprise

def test_kbis_config():
    config = ConfigurationEntreprise.objects.first()
    if config:
        print(f'✅ Configuration trouvée : {config.nom_entreprise}')
        if config.entete_upload:
            print(f'✅ En-tête personnalisé : {config.entete_upload.name}')
            if os.path.exists(config.entete_upload.path):
                print(f'✅ Fichier d\'en-tête existe : {config.entete_upload.path}')
            else:
                print(f'❌ Fichier d\'en-tête manquant : {config.entete_upload.path}')
        else:
            print('❌ Aucun en-tête personnalisé configuré')
    else:
        print('❌ Aucune configuration d\'entreprise trouvée')

if __name__ == '__main__':
    test_kbis_config()
