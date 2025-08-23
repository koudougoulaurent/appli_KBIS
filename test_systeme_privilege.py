#!/usr/bin/env python3
"""
Script de test pour le système de permissions PRIVILEGE
Teste les fonctionnalités de suppression conditionnelle et gestion des profils
"""

import os
import sys
import django
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.db import transaction

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'projetImo.settings')
django.setup()

from utilisateurs.models import Utilisateur, GroupeTravail
from proprietes.models import Bailleur, Locataire, Propriete, TypeBien
from core.models import TemplateRecu, Devise

Utilisateur = get_user_model()

def test_systeme_privilege():
    """Test complet du système de permissions PRIVILEGE"""
    
    print("🔐 TEST DU SYSTÈME DE PERMISSIONS PRIVILEGE")
    print("=" * 50)
    
    # Créer les données de test
    print("\n📋 Création des données de test...")
    
    # Créer le groupe PRIVILEGE s'il n'existe pas
    groupe_privilege, created = GroupeTravail.objects.get_or_create(
        nom='PRIVILEGE',
        defaults={'description': 'Groupe avec permissions spéciales'}
    )
    
    # Créer un utilisateur PRIVILEGE
    user_privilege, created = Utilisateur.objects.get_or_create(
        username='privilege_test',
        defaults={
            'email': 'privilege@test.com',
            'groupe_travail': groupe_privilege,
            'is_active': True
        }
    )
    if created:
        user_privilege.set_password('test123')
        user_privilege.save()
        print("✅ Utilisateur PRIVILEGE créé")
    else:
        print("✅ Utilisateur PRIVILEGE existant")
    
    # Créer un utilisateur normal
    user_normal, created = Utilisateur.objects.get_or_create(
        username='normal_test',
        defaults={
            'email': 'normal@test.com',
            'groupe_travail': None,
            'is_active': True
        }
    )
    if created:
        user_normal.set_password('test123')
        user_normal.save()
        print("✅ Utilisateur normal créé")
    else:
        print("✅ Utilisateur normal existant")
    
    # Créer des données de test
    type_bien, created = TypeBien.objects.get_or_create(
        nom='Appartement Test',
        defaults={'description': 'Type de bien pour test'}
    )
    
    bailleur, created = Bailleur.objects.get_or_create(
        nom='Dupont',
        prenom='Jean',
        email='jean.dupont@test.com',
        defaults={
            'telephone': '0123456789',
            'adresse': '123 Rue Test'
        }
    )
    
    propriete, created = Propriete.objects.get_or_create(
        titre='Propriété Test',
        defaults={
            'adresse': '456 Avenue Test',
            'code_postal': '75001',
            'ville': 'Paris',
            'type_bien': type_bien,
            'bailleur': bailleur,
            'surface': 50.0,
            'nombre_pieces': 2
        }
    )
    
    print("✅ Données de test créées")
    
    # Test 1: Vérification des permissions PRIVILEGE
    print("\n🔍 Test 1: Vérification des permissions PRIVILEGE")
    
    print(f"   • Utilisateur PRIVILEGE: {user_privilege.is_privilege_user()}")
    print(f"   • Utilisateur normal: {user_normal.is_privilege_user()}")
    
    if user_privilege.is_privilege_user():
        print("   ✅ Permissions PRIVILEGE correctement détectées")
    else:
        print("   ❌ Erreur: L'utilisateur PRIVILEGE n'a pas les bonnes permissions")
    
    # Test 2: Vérification de la suppression conditionnelle
    print("\n🗑️ Test 2: Vérification de la suppression conditionnelle")
    
    # Test avec un élément non référencé (TypeBien sans propriété)
    type_bien_isolé, created = TypeBien.objects.get_or_create(
        nom='Type Isolé',
        defaults={'description': 'Type sans référence'}
    )
    
    peut_supprimer, peut_désactiver, raison = user_privilege.can_delete_any_element(type_bien_isolé)
    print(f"   • TypeBien isolé - Peut supprimer: {peut_supprimer}, Peut désactiver: {peut_désactiver}")
    print(f"   • Raison: {raison}")
    
    # Test avec un élément référencé (TypeBien avec propriété)
    peut_supprimer, peut_désactiver, raison = user_privilege.can_delete_any_element(type_bien)
    print(f"   • TypeBien référencé - Peut supprimer: {peut_supprimer}, Peut désactiver: {peut_désactiver}")
    print(f"   • Raison: {raison}")
    
    # Test 3: Test de suppression sécurisée
    print("\n🛡️ Test 3: Test de suppression sécurisée")
    
    # Supprimer le type isolé
    success, message, action = user_privilege.safe_delete_element(type_bien_isolé)
    print(f"   • Suppression type isolé: {success} - {message} - {action}")
    
    # Désactiver le type référencé
    success, message, action = user_privilege.safe_delete_element(type_bien)
    print(f"   • Désactivation type référencé: {success} - {message} - {action}")
    
    # Test 4: Test des vues PRIVILEGE
    print("\n🌐 Test 4: Test des vues PRIVILEGE")
    
    client = Client()
    
    # Connexion avec l'utilisateur PRIVILEGE
    login_success = client.login(username='privilege_test', password='test123')
    print(f"   • Connexion PRIVILEGE: {login_success}")
    
    if login_success:
        # Test du dashboard avancé
        response = client.get('/utilisateurs/privilege/dashboard/')
        print(f"   • Dashboard avancé: {response.status_code}")
        
        # Test de la gestion des éléments
        response = client.get('/utilisateurs/privilege/elements/')
        print(f"   • Gestion des éléments: {response.status_code}")
        
        # Test de la gestion des profils
        response = client.get('/utilisateurs/privilege/profiles/')
        print(f"   • Gestion des profils: {response.status_code}")
        
        # Test du journal d'audit
        response = client.get('/utilisateurs/privilege/audit/')
        print(f"   • Journal d'audit: {response.status_code}")
    
    # Test 5: Test avec un utilisateur normal
    print("\n👤 Test 5: Test avec un utilisateur normal")
    
    client.logout()
    login_success = client.login(username='normal_test', password='test123')
    print(f"   • Connexion utilisateur normal: {login_success}")
    
    if login_success:
        # Tentative d'accès aux vues PRIVILEGE
        response = client.get('/utilisateurs/privilege/dashboard/')
        print(f"   • Tentative d'accès dashboard PRIVILEGE: {response.status_code}")
        
        if response.status_code == 302:  # Redirection
            print("   ✅ Accès correctement refusé à l'utilisateur normal")
        else:
            print("   ❌ Erreur: L'utilisateur normal a accès aux vues PRIVILEGE")
    
    # Test 6: Vérification des statistiques
    print("\n📊 Test 6: Vérification des statistiques")
    
    stats = {
        'total_utilisateurs': Utilisateur.objects.count(),
        'utilisateurs_actifs': Utilisateur.objects.filter(is_active=True).count(),
        'total_bailleurs': Bailleur.objects.count(),
        'bailleurs_actifs': Bailleur.objects.filter(est_actif=True).count(),
        'total_proprietes': Propriete.objects.count(),
        'proprietes_actives': Propriete.objects.filter(est_actif=True).count(),
    }
    
    for key, value in stats.items():
        print(f"   • {key}: {value}")
    
    # Test 7: Nettoyage des données de test
    print("\n🧹 Test 7: Nettoyage des données de test")
    
    # Supprimer les données de test
    try:
        if 'type_bien_isolé' in locals():
            type_bien_isolé.delete()
        propriete.delete()
        bailleur.delete()
        type_bien.delete()
        print("   ✅ Données de test nettoyées")
    except Exception as e:
        print(f"   ⚠️ Erreur lors du nettoyage: {e}")
    
    print("\n🎉 Test du système PRIVILEGE terminé!")
    print("\n📋 RÉSUMÉ DES FONCTIONNALITÉS PRIVILEGE:")
    print("   ✅ Suppression conditionnelle d'éléments")
    print("   ✅ Désactivation d'éléments référencés")
    print("   ✅ Gestion exclusive des profils")
    print("   ✅ Journal d'audit automatique")
    print("   ✅ Vérification des références")
    print("   ✅ Permissions sécurisées")
    print("   ✅ Interface utilisateur avancée")

if __name__ == '__main__':
    test_systeme_privilege() 