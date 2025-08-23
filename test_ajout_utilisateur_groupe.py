#!/usr/bin/env python
"""
Test d'ajout d'utilisateur avec sélection de groupe de travail
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from django.test import Client
from django.contrib.auth import authenticate
from utilisateurs.models import Utilisateur, GroupeTravail
from utilisateurs.forms import UtilisateurForm

def test_ajout_utilisateur_groupe():
    """Test de l'ajout d'utilisateur avec sélection de groupe"""
    
    print("🔧 TEST AJOUT UTILISATEUR AVEC GROUPE DE TRAVAIL")
    print("=" * 60)
    
    # Test 1: Vérifier les groupes disponibles
    print("\n📋 Test 1: Groupes de travail disponibles")
    print("-" * 40)
    
    groupes = GroupeTravail.objects.all()
    if groupes.exists():
        print("✅ Groupes trouvés :")
        for groupe in groupes:
            print(f"   - {groupe.nom}: {groupe.description}")
    else:
        print("❌ Aucun groupe trouvé")
        return False
    
    # Test 2: Vérifier le formulaire
    print("\n📝 Test 2: Formulaire UtilisateurForm")
    print("-" * 40)
    
    form = UtilisateurForm()
    
    # Vérifier que le champ groupe_travail existe
    if 'groupe_travail' in form.fields:
        print("✅ Champ groupe_travail présent dans le formulaire")
        
        # Vérifier les choix disponibles
        choices = form.fields['groupe_travail'].choices
        print(f"✅ {len(choices)} choix disponibles dans le champ groupe_travail")
        
        for choice in choices:
            if choice[0]:  # Ignorer le choix vide
                print(f"   - {choice[0]}: {choice[1]}")
    else:
        print("❌ Champ groupe_travail manquant dans le formulaire")
        return False
    
    # Test 3: Test de création d'utilisateur
    print("\n👤 Test 3: Création d'utilisateur test")
    print("-" * 40)
    
    # Données de test
    test_data = {
        'username': 'test_groupe',
        'first_name': 'Test',
        'last_name': 'Groupe',
        'email': 'test.groupe@example.com',
        'telephone': '+33123456789',
        'groupe_travail': groupes.first().id,  # Premier groupe disponible
        'poste': 'Testeur',
        'departement': 'Tests',
        'actif': True,
        'password': 'test123',
        'password_confirm': 'test123'
    }
    
    form = UtilisateurForm(data=test_data)
    if form.is_valid():
        print("✅ Formulaire valide")
        
        # Sauvegarder l'utilisateur
        utilisateur = form.save()
        print(f"✅ Utilisateur créé: {utilisateur.username}")
        print(f"   Groupe: {utilisateur.groupe_travail.nom}")
        print(f"   Email: {utilisateur.email}")
        
        # Vérifier que l'utilisateur peut se connecter
        user = authenticate(username='test_groupe', password='test123')
        if user:
            print("✅ Authentification réussie")
        else:
            print("❌ Échec de l'authentification")
        
        # Nettoyer - supprimer l'utilisateur de test
        utilisateur.delete()
        print("✅ Utilisateur de test supprimé")
        
    else:
        print("❌ Formulaire invalide:")
        print(form.errors)
        return False
    
    # Test 4: Test d'accès à la page d'ajout
    print("\n🌐 Test 4: Accès à la page d'ajout d'utilisateur")
    print("-" * 40)
    
    client = Client()
    
    # Connexion avec un utilisateur de test
    user = authenticate(username='privilege1', password='test123')
    if user:
        client.force_login(user)
        print("✅ Connexion réussie avec privilege1")
        
        # Test page ajouter utilisateur
        try:
            response = client.get('/utilisateurs/utilisateurs/ajouter/')
            if response.status_code == 200:
                print("✅ Page ajouter utilisateur accessible")
                
                # Vérifier que le formulaire contient le champ groupe_travail
                if 'groupe_travail' in response.content.decode():
                    print("✅ Champ groupe_travail présent dans la page")
                else:
                    print("❌ Champ groupe_travail manquant dans la page")
                    return False
                    
            else:
                print(f"❌ Erreur page ajouter utilisateur: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Erreur accès ajouter utilisateur: {e}")
            return False
        
    else:
        print("❌ Impossible de se connecter avec privilege1")
        return False
    
    print("\n✅ TOUS LES TESTS PASSÉS !")
    print("🎉 L'ajout d'utilisateur avec sélection de groupe fonctionne !")
    
    return True

if __name__ == "__main__":
    test_ajout_utilisateur_groupe() 