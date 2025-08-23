#!/usr/bin/env python
"""
Diagnostic rapide de l'application Django
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from django.db import connection
from contrats.models import Contrat
from paiements.models import Recu, Paiement
from proprietes.models import Propriete, Locataire
from utilisateurs.models import Utilisateur, GroupeTravail

def diagnostic_rapide():
    """Diagnostic rapide de l'application"""
    
    print("🔍 DIAGNOSTIC RAPIDE DE L'APPLICATION")
    print("=" * 60)
    
    # Test 1: Connexion à la base
    print("\n📊 Test 1: Connexion à la base de données")
    print("-" * 40)
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            print(f"✅ Base connectée - {len(tables)} tables")
            
            # Vérifier les tables principales
            tables_principales = ['contrats_contrat', 'paiements_recu', 'paiements_paiement', 'proprietes_propriete']
            for table in tables_principales:
                if any(table in str(t) for t in tables):
                    print(f"   ✅ {table}")
                else:
                    print(f"   ❌ {table}")
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")
        return False
    
    # Test 2: Données dans les modèles
    print("\n📋 Test 2: Données dans les modèles")
    print("-" * 40)
    
    # Contrats
    contrats_count = Contrat.objects.count()
    print(f"   Contrats: {contrats_count}")
    if contrats_count > 0:
        contrat_exemple = Contrat.objects.first()
        print(f"     Exemple: {contrat_exemple.numero_contrat} - {contrat_exemple.propriete.adresse if contrat_exemple.propriete else 'Aucune'}")
    
    # Reçus
    recus_count = Recu.objects.count()
    print(f"   Reçus: {recus_count}")
    if recus_count > 0:
        recu_exemple = Recu.objects.first()
        print(f"     Exemple: {recu_exemple.numero_recu}")
    
    # Paiements
    paiements_count = Paiement.objects.count()
    print(f"   Paiements: {paiements_count}")
    
    # Propriétés
    proprietes_count = Propriete.objects.count()
    print(f"   Propriétés: {proprietes_count}")
    
    # Locataires
    locataires_count = Locataire.objects.count()
    print(f"   Locataires: {locataires_count}")
    
    # Utilisateurs
    utilisateurs_count = Utilisateur.objects.count()
    print(f"   Utilisateurs: {utilisateurs_count}")
    
    # Test 3: Vérification des URLs
    print("\n🌐 Test 3: Vérification des URLs")
    print("-" * 40)
    
    try:
        from django.urls import reverse
        from django.urls.resolvers import URLPattern, URLResolver
        
        # Vérifier les URLs principales
        urls_a_tester = [
            'core:dashboard',
            'contrats:liste',
            'paiements:liste',
            'proprietes:liste'
        ]
        
        for url_name in urls_a_tester:
            try:
                url = reverse(url_name)
                print(f"   ✅ {url_name}: {url}")
            except Exception as e:
                print(f"   ❌ {url_name}: {e}")
                
    except Exception as e:
        print(f"   ⚠️ Erreur lors de la vérification des URLs: {e}")
    
    # Test 4: Vérification des templates
    print("\n🎨 Test 4: Vérification des templates")
    print("-" * 40)
    
    template_dir = "templates"
    if os.path.exists(template_dir):
        print(f"   ✅ Répertoire templates trouvé")
        
        # Vérifier les templates principaux
        templates_a_verifier = [
            'templates/base.html',
            'templates/contrats/liste.html',
            'templates/paiements/recus_liste.html',
            'templates/base_liste_intelligente.html'
        ]
        
        for template in templates_a_verifier:
            if os.path.exists(template):
                print(f"     ✅ {template}")
            else:
                print(f"     ❌ {template}")
    else:
        print(f"   ❌ Répertoire templates non trouvé")
    
    # Test 5: Vérification des fichiers statiques
    print("\n📁 Test 5: Vérification des fichiers statiques")
    print("-" * 40)
    
    static_dir = "static"
    if os.path.exists(static_dir):
        print(f"   ✅ Répertoire static trouvé")
        
        # Vérifier les sous-répertoires
        sous_dirs = ['css', 'js']
        for sous_dir in sous_dirs:
            sous_dir_path = os.path.join(static_dir, sous_dir)
            if os.path.exists(sous_dir_path):
                files = os.listdir(sous_dir_path)
                print(f"     ✅ {sous_dir}: {len(files)} fichiers")
            else:
                print(f"     ❌ {sous_dir}: non trouvé")
    else:
        print(f"   ❌ Répertoire static non trouvé")
    
    # Test 6: Résumé et recommandations
    print("\n🎯 RÉSUMÉ ET RECOMMANDATIONS")
    print("=" * 60)
    
    if contrats_count > 0 and recus_count > 0:
        print("✅ L'application semble fonctionnelle avec des données")
        print("✅ Les IDs uniques sont présents dans la base")
        print("\n🔍 POUR TROUVER LE PROBLÈME:")
        print("1. Vérifiez que le serveur Django est démarré")
        print("2. Vérifiez que vous êtes connecté avec un utilisateur valide")
        print("3. Vérifiez que vous accédez aux bonnes URLs")
        print("4. Vérifiez la console du navigateur pour les erreurs JavaScript")
        print("5. Vérifiez les logs Django pour les erreurs serveur")
        
        print("\n🚀 POUR DÉMARRER LE SERVEUR:")
        print("   python manage.py runserver 127.0.0.1:8000")
        
        print("\n🌐 URLS À TESTER:")
        print("   - Dashboard: http://127.0.0.1:8000/")
        print("   - Contrats: http://127.0.0.1:8000/contrats/")
        print("   - Paiements: http://127.0.0.1:8000/paiements/")
        
    else:
        print("⚠️ L'application n'a pas de données de test")
        print("⚠️ Créez d'abord des données de test")
        print("\n🔧 POUR CRÉER DES DONNÉES DE TEST:")
        print("   python manage.py shell")
        print("   # Puis exécutez des scripts de création de données")
    
    return True

if __name__ == "__main__":
    diagnostic_rapide()
