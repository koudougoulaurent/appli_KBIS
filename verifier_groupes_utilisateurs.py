#!/usr/bin/env python
"""
Script pour vérifier les groupes et utilisateurs
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from utilisateurs.models import Utilisateur, GroupeTravail
from django.contrib.auth import authenticate

def verifier_groupes():
    """Vérifier les groupes existants"""
    print("👥 Groupes existants:")
    print("-" * 40)
    
    groupes = GroupeTravail.objects.all()
    for groupe in groupes:
        print(f"✅ {groupe.nom} - Actif: {groupe.actif}")
        utilisateurs = groupe.utilisateurs.all()
        print(f"   Utilisateurs ({utilisateurs.count()}):")
        for user in utilisateurs:
            print(f"     - {user.username} (actif: {user.actif})")
        print()

def verifier_utilisateur_admin1():
    """Vérifier l'utilisateur admin1"""
    print("🔍 Vérification de l'utilisateur admin1:")
    print("-" * 40)
    
    try:
        user = Utilisateur.objects.get(username='admin1')
        print(f"✅ Utilisateur trouvé: {user.username}")
        print(f"   - Actif: {user.actif}")
        print(f"   - Groupe: {user.groupe_travail}")
        print(f"   - Staff: {user.is_staff}")
        print(f"   - Superuser: {user.is_superuser}")
        
        # Test d'authentification
        auth_user = authenticate(username='admin1', password='test123')
        if auth_user:
            print("✅ Authentification réussie")
        else:
            print("❌ Échec de l'authentification")
            
    except Utilisateur.DoesNotExist:
        print("❌ Utilisateur admin1 non trouvé")

def creer_utilisateur_test():
    """Créer un utilisateur de test pour chaque groupe"""
    print("\n🔧 Création d'utilisateurs de test:")
    print("-" * 40)
    
    groupes = GroupeTravail.objects.filter(actif=True)
    
    for groupe in groupes:
        username = f"test_{groupe.nom.lower()}"
        
        # Vérifier si l'utilisateur existe déjà
        if not Utilisateur.objects.filter(username=username).exists():
            user = Utilisateur.objects.create_user(
                username=username,
                password='test123',
                email=f'{username}@test.com',
                groupe_travail=groupe,
                actif=True
            )
            print(f"✅ Créé: {username} dans le groupe {groupe.nom}")
        else:
            print(f"⚠️  Existe déjà: {username} dans le groupe {groupe.nom}")

def main():
    """Fonction principale"""
    print("🔍 VÉRIFICATION DES GROUPES ET UTILISATEURS")
    print("=" * 60)
    
    verifier_groupes()
    verifier_utilisateur_admin1()
    creer_utilisateur_test()
    
    print("\n" + "=" * 60)
    print("📋 RÉSUMÉ")
    print("=" * 60)
    print("Les utilisateurs de test sont maintenant disponibles pour tester les dashboards.")

if __name__ == '__main__':
    main() 