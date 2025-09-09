#!/usr/bin/env python
"""
Script de test pour les actions rapides des bailleurs
"""

import os
import sys
import django
from django.conf import settings

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from proprietes.models import Bailleur, Propriete
from django.test import Client
from django.contrib.auth import get_user_model

User = get_user_model()

def test_actions_rapides():
    """Test des actions rapides pour les bailleurs"""
    print("🧪 Test des Actions Rapides pour Bailleurs")
    print("=" * 50)
    
    # Créer un client de test
    client = Client()
    
    # Créer un utilisateur de test
    try:
        user = User.objects.get(username='privilege')
        print(f"✅ Utilisateur trouvé: {user.username}")
    except User.DoesNotExist:
        print("❌ Utilisateur 'privilege' non trouvé")
        return False
    
    # Se connecter
    client.force_login(user)
    print("✅ Connexion réussie")
    
    # Test 1: Page de détail du bailleur
    print("\n📄 Test 1: Page de détail du bailleur")
    try:
        response = client.get('/proprietes/bailleurs/1/')
        if response.status_code == 200:
            print("✅ Page de détail du bailleur accessible")
            
            # Vérifier la présence des actions rapides
            content = response.content.decode('utf-8')
            if 'Actions Rapides' in content:
                print("✅ Actions rapides présentes")
            else:
                print("❌ Actions rapides manquantes")
                
            if 'Modifier' in content:
                print("✅ Bouton Modifier présent")
            else:
                print("❌ Bouton Modifier manquant")
                
            if 'Ajouter Propriété' in content:
                print("✅ Bouton Ajouter Propriété présent")
            else:
                print("❌ Bouton Ajouter Propriété manquant")
                
        else:
            print(f"❌ Erreur page de détail: {response.status_code}")
    except Exception as e:
        print(f"❌ Erreur test page de détail: {e}")
    
    # Test 2: Page des propriétés du bailleur
    print("\n📄 Test 2: Page des propriétés du bailleur")
    try:
        response = client.get('/proprietes/bailleurs/1/proprietes/')
        if response.status_code == 200:
            print("✅ Page des propriétés accessible")
            
            # Vérifier les statistiques
            content = response.content.decode('utf-8')
            if 'Total Propriétés' in content:
                print("✅ Statistiques présentes")
            else:
                print("❌ Statistiques manquantes")
                
        else:
            print(f"❌ Erreur page propriétés: {response.status_code}")
    except Exception as e:
        print(f"❌ Erreur test page propriétés: {e}")
    
    # Test 3: Page de test des actions rapides
    print("\n📄 Test 3: Page de test des actions rapides")
    try:
        response = client.get('/proprietes/test-actions-rapides/')
        if response.status_code == 200:
            print("✅ Page de test accessible")
            
            content = response.content.decode('utf-8')
            if 'Test des Actions Rapides' in content:
                print("✅ Page de test complète")
            else:
                print("❌ Page de test incomplète")
                
        else:
            print(f"❌ Erreur page de test: {response.status_code}")
    except Exception as e:
        print(f"❌ Erreur test page de test: {e}")
    
    # Test 4: Vérification des modèles
    print("\n📊 Test 4: Vérification des modèles")
    try:
        bailleur = Bailleur.objects.first()
        if bailleur:
            print(f"✅ Bailleur trouvé: {bailleur.get_nom_complet()}")
            
            proprietes = bailleur.proprietes.all()
            print(f"✅ Propriétés trouvées: {proprietes.count()}")
            
            # Vérifier les champs disponibles
            if hasattr(proprietes.first(), 'disponible'):
                print("✅ Champ 'disponible' présent")
            else:
                print("❌ Champ 'disponible' manquant")
                
            if hasattr(proprietes.first(), 'loyer_actuel'):
                print("✅ Champ 'loyer_actuel' présent")
            else:
                print("❌ Champ 'loyer_actuel' manquant")
                
        else:
            print("❌ Aucun bailleur trouvé")
    except Exception as e:
        print(f"❌ Erreur vérification modèles: {e}")
    
    print("\n🎉 Tests terminés!")
    return True

if __name__ == '__main__':
    test_actions_rapides()
