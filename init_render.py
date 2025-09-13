#!/usr/bin/env python
"""
Script d'initialisation pour Render
Crée les groupes de travail et un superutilisateur par défaut
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from django.contrib.auth import get_user_model
from utilisateurs.models import GroupeTravail

def init_groups():
    """Créer les groupes de travail"""
    print("🔧 Création des groupes de travail...")
    
    groupes = [
        {'nom': 'ADMINISTRATION', 'description': 'GESTION ADMINISTRATIVE'},
        {'nom': 'CAISSE', 'description': 'GESTION DES PAIEMENTS ET RETRAITS'},
        {'nom': 'CONTROLE', 'description': 'GESTION DU CONTRÔLE'},
        {'nom': 'PRIVILEGE', 'description': 'ACCÈS COMPLET'}
    ]
    
    for groupe_data in groupes:
        groupe, created = GroupeTravail.objects.get_or_create(
            nom=groupe_data['nom'],
            defaults={'description': groupe_data['description']}
        )
        if created:
            print(f"✅ Groupe créé : {groupe.nom}")
        else:
            print(f"ℹ️  Groupe existant : {groupe.nom}")

def init_superuser():
    """Créer un superutilisateur par défaut"""
    print("\n🔧 Création du superutilisateur...")
    
    User = get_user_model()
    
    # Vérifier si un superutilisateur existe déjà
    if User.objects.filter(is_superuser=True).exists():
        print("ℹ️  Un superutilisateur existe déjà")
        return
    
    # Créer le superutilisateur
    try:
        user = User.objects.create_superuser(
            username='admin',
            email='admin@gestimmob.com',
            password='admin123',
            prenom='Administrateur',
            nom='Système'
        )
        print("✅ Superutilisateur créé :")
        print(f"   - Username: admin")
        print(f"   - Password: admin123")
        print(f"   - Email: admin@gestimmob.com")
    except Exception as e:
        print(f"❌ Erreur lors de la création du superutilisateur : {e}")

def main():
    """Fonction principale"""
    print("🚀 Initialisation de l'application pour Render...")
    print("=" * 50)
    
    try:
        init_groups()
        init_superuser()
        
        print("\n" + "=" * 50)
        print("✅ Initialisation terminée avec succès !")
        print("\n📋 Informations de connexion :")
        print("   - URL: https://appli-kbis.onrender.com")
        print("   - Username: admin")
        print("   - Password: admin123")
        print("\n🎉 Votre application est prête à être utilisée !")
        
    except Exception as e:
        print(f"\n❌ Erreur lors de l'initialisation : {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
