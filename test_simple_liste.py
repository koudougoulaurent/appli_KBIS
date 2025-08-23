#!/usr/bin/env python
"""
Test simple de la liste d'utilisateurs
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from django.test import Client
from utilisateurs.models import Utilisateur, GroupeTravail

def test_simple_liste():
    """Test simple de la liste d'utilisateurs"""
    
    print("🔍 TEST SIMPLE LISTE D'UTILISATEURS")
    print("=" * 50)
    
    # Test 1: Vérifier les données en base
    print("\n📊 Test 1: Données en base")
    print("-" * 30)
    
    utilisateurs = Utilisateur.objects.all()
    print(f"✅ {utilisateurs.count()} utilisateurs en base")
    
    for user in utilisateurs[:5]:  # Afficher les 5 premiers
        print(f"   - {user.username} ({user.get_full_name()}) - Groupe: {user.get_groupe_display()}")
    
    # Test 2: Vérifier les groupes
    print("\n🏢 Test 2: Groupes de travail")
    print("-" * 30)
    
    groupes = GroupeTravail.objects.all()
    print(f"✅ {groupes.count()} groupes en base")
    
    for groupe in groupes:
        print(f"   - {groupe.nom}: {groupe.utilisateurs.count()} utilisateurs")
    
    # Test 3: Test avec client Django
    print("\n🌐 Test 3: Test avec client Django")
    print("-" * 30)
    
    client = Client()
    
    # Connexion avec un utilisateur privilégié
    user = Utilisateur.objects.get(username='privilege1')
    user.set_password('test123')
    user.save()
    
    login_success = client.login(username='privilege1', password='test123')
    if login_success:
        print("✅ Connexion réussie")
        
        # Test accès à la liste
        try:
            response = client.get('/utilisateurs/utilisateurs/')
            print(f"✅ Réponse liste utilisateurs: {response.status_code}")
            
            if response.status_code == 200:
                content = response.content.decode()
                if 'utilisateurs' in content.lower():
                    print("✅ Contenu de la liste présent")
                else:
                    print("⚠️ Contenu de la liste manquant")
            else:
                print(f"❌ Erreur HTTP: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Erreur accès liste: {e}")
    else:
        print("❌ Échec de la connexion")
    
    print("\n✅ Test terminé !")

if __name__ == "__main__":
    test_simple_liste() 