#!/usr/bin/env python
"""
Script de test pour vérifier l'accessibilité de toutes les pages web
"""

import os
import sys
import django
from django.test import Client
from django.contrib.auth import get_user_model

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

def test_pages_accessibility():
    """Teste l'accessibilité de toutes les pages web"""
    
    print("🧪 Test d'accessibilité des pages web")
    print("=" * 50)
    
    # Créer un client de test
    client = Client()
    
    # Créer un utilisateur de test
    User = get_user_model()
    user, created = User.objects.get_or_create(
        username='testuser',
        defaults={
            'email': 'test@example.com',
            'is_staff': True,
            'is_superuser': True
        }
    )
    
    if created:
        user.set_password('testpass123')
        user.save()
        print(f"✅ Utilisateur de test créé: {user.username}")
    
    # Se connecter
    login_success = client.login(username='testuser', password='testpass123')
    if not login_success:
        print("❌ Échec de la connexion")
        return False
    
    print("✅ Connexion réussie")
    
    # Liste des URLs à tester
    urls_to_test = [
        # Pages principales
        ('/', 'Dashboard'),
        ('/utilisateurs/liste/', 'Liste des Utilisateurs'),
        ('/proprietes/liste/', 'Liste des Propriétés'),
        ('/proprietes/bailleurs/', 'Liste des Bailleurs'),
        ('/proprietes/locataires/', 'Liste des Locataires'),
        ('/contrats/liste/', 'Liste des Contrats'),
        ('/paiements/liste/', 'Liste des Paiements'),
        ('/paiements/retraits/', 'Liste des Retraits'),
        ('/notifications/', 'Liste des Notifications'),
        
        # Pages d'ajout
        ('/utilisateurs/ajouter/', 'Ajouter Utilisateur'),
        ('/proprietes/ajouter/', 'Ajouter Propriété'),
        ('/proprietes/bailleurs/ajouter/', 'Ajouter Bailleur'),
        ('/proprietes/locataires/ajouter/', 'Ajouter Locataire'),
        ('/contrats/ajouter/', 'Ajouter Contrat'),
        ('/paiements/ajouter/', 'Ajouter Paiement'),
        ('/paiements/retraits/ajouter/', 'Ajouter Retrait'),
        
        # API Interface
        ('/api-interface/', 'Interface API'),
    ]
    
    success_count = 0
    total_count = len(urls_to_test)
    
    print(f"\n📋 Test de {total_count} pages web :")
    print("-" * 50)
    
    for url, description in urls_to_test:
        try:
            response = client.get(url)
            if response.status_code == 200:
                print(f"✅ {description:<25} - {url}")
                success_count += 1
            else:
                print(f"❌ {description:<25} - {url} (Status: {response.status_code})")
        except Exception as e:
            print(f"❌ {description:<25} - {url} (Erreur: {str(e)})")
    
    print("-" * 50)
    print(f"📊 Résultats : {success_count}/{total_count} pages accessibles")
    
    if success_count == total_count:
        print("🎉 Toutes les pages sont accessibles !")
        return True
    else:
        print("⚠️ Certaines pages ne sont pas accessibles")
        return False

def test_admin_access():
    """Teste l'accessibilité de l'admin Django"""
    
    print("\n🔧 Test d'accessibilité de l'admin Django")
    print("=" * 50)
    
    client = Client()
    
    # Se connecter
    User = get_user_model()
    user = User.objects.get(username='testuser')
    client.login(username='testuser', password='testpass123')
    
    # URLs admin à tester
    admin_urls = [
        ('/admin/', 'Admin Principal'),
        ('/admin/proprietes/propriete/', 'Admin Propriétés'),
        ('/admin/proprietes/bailleur/', 'Admin Bailleurs'),
        ('/admin/proprietes/locataire/', 'Admin Locataires'),
        ('/admin/contrats/contrat/', 'Admin Contrats'),
        ('/admin/paiements/paiement/', 'Admin Paiements'),
        ('/admin/paiements/retrait/', 'Admin Retraits'),
        ('/admin/notifications/notification/', 'Admin Notifications'),
        ('/admin/utilisateurs/utilisateur/', 'Admin Utilisateurs'),
    ]
    
    success_count = 0
    total_count = len(admin_urls)
    
    for url, description in admin_urls:
        try:
            response = client.get(url)
            if response.status_code == 200:
                print(f"✅ {description:<20} - {url}")
                success_count += 1
            else:
                print(f"❌ {description:<20} - {url} (Status: {response.status_code})")
        except Exception as e:
            print(f"❌ {description:<20} - {url} (Erreur: {str(e)})")
    
    print("-" * 50)
    print(f"📊 Résultats Admin : {success_count}/{total_count} pages accessibles")
    
    return success_count == total_count

def main():
    """Fonction principale"""
    
    print("🚀 Test complet de l'accessibilité des pages")
    print("=" * 60)
    
    # Test des pages web
    web_success = test_pages_accessibility()
    
    # Test de l'admin
    admin_success = test_admin_access()
    
    print("\n" + "=" * 60)
    print("📋 RÉSUMÉ FINAL")
    print("=" * 60)
    
    if web_success and admin_success:
        print("🎉 SUCCÈS : Toutes les pages sont accessibles !")
        print("✅ Pages web : Fonctionnelles")
        print("✅ Admin Django : Fonctionnel")
        print("\n🚀 Le projet est prêt pour la Phase 5 !")
        return True
    else:
        print("⚠️ ATTENTION : Certaines pages ne sont pas accessibles")
        if not web_success:
            print("❌ Pages web : Problèmes détectés")
        if not admin_success:
            print("❌ Admin Django : Problèmes détectés")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1) 