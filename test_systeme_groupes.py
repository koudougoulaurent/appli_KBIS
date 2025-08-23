#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de test pour le système de groupes de travail GESTIMMOB
"""

import os
import sys
import django
from datetime import date

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from django.test import Client
from django.urls import reverse
from utilisateurs.models import GroupeTravail, Utilisateur

def test_groupes_existants():
    """Teste que tous les groupes existent"""
    print("🔍 Test des groupes existants...")
    
    groupes_attendus = ['CAISSE', 'CONTROLES', 'ADMINISTRATION', 'PRIVILEGE']
    groupes_trouves = []
    
    for nom in groupes_attendus:
        try:
            groupe = GroupeTravail.objects.get(nom=nom)
            groupes_trouves.append(nom)
            print(f"✅ Groupe {nom} trouvé")
        except GroupeTravail.DoesNotExist:
            print(f"❌ Groupe {nom} manquant")
    
    if len(groupes_trouves) == len(groupes_attendus):
        print("✅ Tous les groupes sont présents")
        return True
    else:
        print("❌ Certains groupes sont manquants")
        return False

def test_comptes_utilisateurs():
    """Teste que les comptes de test existent"""
    print("\n👥 Test des comptes utilisateurs...")
    
    comptes_attendus = {
        'CAISSE': ['caisse1', 'caisse2'],
        'CONTROLES': ['controle1', 'controle2'],
        'ADMINISTRATION': ['admin1', 'admin2'],
        'PRIVILEGE': ['privilege1', 'privilege2']
    }
    
    comptes_trouves = 0
    total_attendus = sum(len(comptes) for comptes in comptes_attendus.values())
    
    for groupe_nom, usernames in comptes_attendus.items():
        try:
            groupe = GroupeTravail.objects.get(nom=groupe_nom)
            for username in usernames:
                try:
                    user = Utilisateur.objects.get(username=username, groupe_travail=groupe)
                    comptes_trouves += 1
                    print(f"✅ Compte {username} ({groupe_nom}) trouvé")
                except Utilisateur.DoesNotExist:
                    print(f"❌ Compte {username} ({groupe_nom}) manquant")
        except GroupeTravail.DoesNotExist:
            print(f"❌ Groupe {groupe_nom} manquant")
    
    if comptes_trouves == total_attendus:
        print(f"✅ Tous les {total_attendus} comptes sont présents")
        return True
    else:
        print(f"❌ {comptes_trouves}/{total_attendus} comptes trouvés")
        return False

def test_urls_accessibles():
    """Teste que les URLs principales sont accessibles"""
    print("\n🌐 Test des URLs accessibles...")
    
    client = Client()
    
    # Test de la page de connexion des groupes
    try:
        response = client.get('/')
        if response.status_code == 302:  # Redirection vers /utilisateurs/
            response = client.get('/utilisateurs/')
        
        if response.status_code == 200:
            print("✅ Page de connexion des groupes accessible")
        else:
            print(f"❌ Page de connexion des groupes - Status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erreur page de connexion des groupes: {e}")
        return False
    
    # Test des pages de connexion par groupe
    groupes = GroupeTravail.objects.filter(actif=True)
    for groupe in groupes:
        try:
            url = f'/utilisateurs/login/{groupe.nom}/'
            response = client.get(url)
            if response.status_code == 200:
                print(f"✅ Page de connexion {groupe.nom} accessible")
            else:
                print(f"❌ Page de connexion {groupe.nom} - Status: {response.status_code}")
        except Exception as e:
            print(f"❌ Erreur page de connexion {groupe.nom}: {e}")
    
    return True

def test_connexion_utilisateur():
    """Teste la connexion d'un utilisateur"""
    print("\n🔐 Test de connexion utilisateur...")
    
    client = Client()
    
    # Test avec un utilisateur CAISSE
    try:
        user = Utilisateur.objects.get(username='caisse1', groupe_travail__nom='CAISSE')
        
        # Test de connexion
        login_success = client.login(username='caisse1', password='caisse123')
        if login_success:
            print("✅ Connexion utilisateur caisse1 réussie")
            
            # Test d'accès au dashboard
            response = client.get(f'/utilisateurs/dashboard/{user.groupe_travail.nom}/')
            if response.status_code == 200:
                print("✅ Accès au dashboard CAISSE réussi")
            else:
                print(f"❌ Accès au dashboard CAISSE - Status: {response.status_code}")
        else:
            print("❌ Échec de connexion utilisateur caisse1")
            return False
            
    except Utilisateur.DoesNotExist:
        print("❌ Utilisateur caisse1 non trouvé")
        return False
    except Exception as e:
        print(f"❌ Erreur test connexion: {e}")
        return False
    
    return True

def test_permissions_groupes():
    """Teste les permissions des groupes"""
    print("\n🔒 Test des permissions des groupes...")
    
    groupes = GroupeTravail.objects.all()
    
    for groupe in groupes:
        print(f"\n📋 Groupe: {groupe.nom}")
        permissions = groupe.permissions
        
        if 'modules' in permissions:
            modules = permissions['modules']
            print(f"   Modules accessibles: {', '.join(modules)}")
        else:
            print("   ⚠️ Aucun module défini")
        
        if 'actions' in permissions:
            actions = permissions['actions']
            print(f"   Actions autorisées: {', '.join(actions)}")
        else:
            print("   ⚠️ Aucune action définie")
        
        if 'restrictions' in permissions:
            restrictions = permissions['restrictions']
            if restrictions:
                print(f"   Restrictions: {', '.join(restrictions)}")
            else:
                print("   ✅ Aucune restriction")
        else:
            print("   ✅ Aucune restriction définie")
    
    return True

def afficher_resume_tests():
    """Affiche un résumé des tests"""
    print("\n" + "="*60)
    print("📊 RÉSUMÉ DES TESTS")
    print("="*60)
    
    # Statistiques
    total_groupes = GroupeTravail.objects.count()
    total_utilisateurs = Utilisateur.objects.count()
    utilisateurs_actifs = Utilisateur.objects.filter(actif=True).count()
    
    print(f"\n🏢 Groupes de travail: {total_groupes}")
    print(f"👥 Utilisateurs totaux: {total_utilisateurs}")
    print(f"✅ Utilisateurs actifs: {utilisateurs_actifs}")
    
    # Répartition par groupe
    print(f"\n📋 Répartition par groupe:")
    for groupe in GroupeTravail.objects.all():
        count = groupe.utilisateurs.count()
        print(f"   • {groupe.nom}: {count} utilisateur(s)")
    
    print(f"\n🎯 URLs de test:")
    print(f"   • Page principale: http://127.0.0.1:8000/")
    print(f"   • Connexion groupes: http://127.0.0.1:8000/utilisateurs/")
    print(f"   • Admin Django: http://127.0.0.1:8000/admin/")
    
    print(f"\n🔑 Comptes de test disponibles:")
    for groupe in GroupeTravail.objects.all():
        utilisateurs = groupe.utilisateurs.filter(actif=True)
        if utilisateurs.exists():
            print(f"\n   📋 {groupe.nom}:")
            for user in utilisateurs:
                print(f"      • {user.username} / {user.get_full_name()}")
                print(f"        Mot de passe: {groupe.nom.lower()}123")

def main():
    """Fonction principale de test"""
    print("🧪 TESTS DU SYSTÈME DE GROUPES GESTIMMOB")
    print("="*60)
    
    tests_reussis = 0
    total_tests = 5
    
    # Tests
    if test_groupes_existants():
        tests_reussis += 1
    
    if test_comptes_utilisateurs():
        tests_reussis += 1
    
    if test_urls_accessibles():
        tests_reussis += 1
    
    if test_connexion_utilisateur():
        tests_reussis += 1
    
    if test_permissions_groupes():
        tests_reussis += 1
    
    # Résumé
    print(f"\n" + "="*60)
    print(f"📊 RÉSULTATS DES TESTS: {tests_reussis}/{total_tests}")
    print("="*60)
    
    if tests_reussis == total_tests:
        print("🎉 TOUS LES TESTS SONT RÉUSSIS !")
        print("✅ Le système de groupes est opérationnel")
    else:
        print("⚠️ CERTAINS TESTS ONT ÉCHOUÉ")
        print("🔧 Veuillez vérifier la configuration")
    
    # Afficher le résumé détaillé
    afficher_resume_tests()
    
    return tests_reussis == total_tests

if __name__ == "__main__":
    success = main()
    
    if success:
        print("\n🎯 Le système est prêt pour la production !")
        print("🚀 Vous pouvez maintenant utiliser l'application.")
    else:
        print("\n🔧 Des corrections sont nécessaires avant utilisation.") 