#!/usr/bin/env python
import os
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from proprietes.models import Locataire

def create_locataires():
    # Vérifier s'il y a déjà des locataires
    if Locataire.objects.filter(is_deleted=False).exists():
        print("Des locataires existent déjà.")
        print(f"Total locataires actifs: {Locataire.objects.filter(is_deleted=False, statut='actif').count()}")
        return
    
    # Créer des locataires de test
    locataires = [
        {
            'numero_locataire': 'LT0001',
            'civilite': 'M',
            'nom': 'Dupont',
            'prenom': 'Jean',
            'email': 'jean.dupont@email.com',
            'telephone': '01 23 45 67 89',
            'adresse': '123 Rue de la Paix',
            'ville': 'Paris',
            'code_postal': '75001',
            'pays': 'France',
            'profession': 'Ingénieur',
            'employeur': 'TechCorp',
            'revenus_mensuels': 3500.00,
            'statut': 'actif'
        },
        {
            'numero_locataire': 'LT0002',
            'civilite': 'Mme',
            'nom': 'Martin',
            'prenom': 'Marie',
            'email': 'marie.martin@email.com',
            'telephone': '01 98 76 54 32',
            'adresse': '456 Avenue des Champs',
            'ville': 'Paris',
            'code_postal': '75008',
            'pays': 'France',
            'profession': 'Avocate',
            'employeur': 'Cabinet Legal',
            'revenus_mensuels': 4200.00,
            'statut': 'actif'
        },
        {
            'numero_locataire': 'LT0003',
            'civilite': 'M',
            'nom': 'Bernard',
            'prenom': 'Pierre',
            'email': 'pierre.bernard@email.com',
            'telephone': '01 55 44 33 22',
            'adresse': '789 Boulevard Saint-Germain',
            'ville': 'Paris',
            'code_postal': '75006',
            'pays': 'France',
            'profession': 'Médecin',
            'employeur': 'Hôpital Public',
            'revenus_mensuels': 4500.00,
            'statut': 'actif'
        }
    ]
    
    for data in locataires:
        locataire = Locataire.objects.create(**data)
        print(f"Créé: {locataire.get_nom_complet()}")
    
    print(f"\n{len(locataires)} locataires créés avec succès!")
    print(f"Total locataires actifs: {Locataire.objects.filter(is_deleted=False, statut='actif').count()}")

if __name__ == '__main__':
    create_locataires()
