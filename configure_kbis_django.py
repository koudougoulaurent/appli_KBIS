
# Script de configuration KBIS pour Django
import os
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from core.models import ConfigurationEntreprise
from django.core.files import File

def configure_kbis():
    # Obtenir ou créer la configuration
    config, created = ConfigurationEntreprise.objects.get_or_create(
        defaults={
            'nom_entreprise': 'KBIS',
            'adresse': 'BP 440 Ouaga pissy 10050',
            'ville': 'Ouagadougou',
            'pays': 'Burkina Faso',
            'telephone_principal': '+226 79 18 32 32',
            'telephone_secondaire': '+226 66 66 45 60',
            'email': 'kbissarl2022@gmail.com',
            'forme_juridique': 'SARL',
            'couleur_principale': '#1e3a8a',
            'couleur_secondaire': '#fbbf24',
        }
    )
    
    # Mettre à jour les informations
    config.nom_entreprise = 'KBIS'
    config.adresse = 'BP 440 Ouaga pissy 10050'
    config.ville = 'Ouagadougou'
    config.pays = 'Burkina Faso'
    config.telephone_principal = '+226 79 18 32 32'
    config.telephone_secondaire = '+226 66 66 45 60'
    config.email = 'kbissarl2022@gmail.com'
    config.forme_juridique = 'SARL'
    config.couleur_principale = '#1e3a8a'
    config.couleur_secondaire = '#fbbf24'
    
    # Assigner l'en-tête
    header_path = 'media/entetes_entreprise/kbis_header.png'
    if os.path.exists(header_path):
        with open(header_path, 'rb') as f:
            config.entete_upload.save('kbis_header.png', File(f), save=True)
        print('✅ En-tête KBIS configuré')
    else:
        print('❌ Fichier d\'en-tête non trouvé')
    
    config.save()
    print(f'✅ Configuration KBIS mise à jour : {config.nom_entreprise}')

if __name__ == '__main__':
    configure_kbis()
