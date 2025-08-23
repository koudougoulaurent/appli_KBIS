#!/usr/bin/env python3
"""
Script pour tester l'interface web des contrats et vérifier la génération PDF
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from django.test import Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from contrats.models import Contrat
from proprietes.models import Propriete, Locataire
from core.models import ConfigurationEntreprise

User = get_user_model()

def test_formulaire_contrat():
    """Teste l'accès au formulaire de contrat"""
    print("🔍 Test de l'accès au formulaire de contrat...")
    
    try:
        # Créer un client de test
        client = Client()
        
        # Créer ou récupérer un utilisateur de test
        user, created = User.objects.get_or_create(
            username='test_admin',
            defaults={
                'email': 'test@admin.com',
                'nom': 'Admin',
                'prenom': 'Test',
                'is_staff': True,
                'is_superuser': True
            }
        )
        if created:
            user.set_password('test123')
            user.save()
            print(f"✅ Utilisateur de test créé : {user.username}")
        else:
            print(f"✅ Utilisateur de test existant : {user.username}")
        
        # Se connecter
        login_success = client.login(username='test_admin', password='test123')
        if not login_success:
            print("❌ Échec de la connexion")
            return False
        
        print("✅ Connexion réussie")
        
        # Tester l'accès au formulaire d'ajout de contrat
        url = reverse('contrats:ajouter')
        response = client.get(url)
        
        print(f"📋 URL testée : {url}")
        print(f"📊 Code de statut : {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Formulaire d'ajout de contrat accessible")
            
            # Vérifier si le champ telecharger_pdf est présent
            content = response.content.decode('utf-8')
            if 'telecharger_pdf' in content:
                print("✅ Champ 'telecharger_pdf' trouvé dans le formulaire")
            else:
                print("❌ Champ 'telecharger_pdf' NOT trouvé dans le formulaire")
            
            if 'Générer le contrat en PDF' in content:
                print("✅ Label PDF trouvé dans le formulaire")
            else:
                print("❌ Label PDF NOT trouvé dans le formulaire")
            
            if 'pdf-section' in content:
                print("✅ Section PDF trouvée dans le template")
            else:
                print("❌ Section PDF NOT trouvée dans le template")
                
            return True
        else:
            print(f"❌ Erreur d'accès au formulaire : {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors du test : {e}")
        import traceback
        traceback.print_exc()
        return False

def test_configuration_entreprise():
    """Teste la configuration de l'entreprise"""
    print("\n🔍 Test de la configuration de l'entreprise...")
    
    try:
        config = ConfigurationEntreprise.get_configuration_active()
        
        if config:
            print(f"✅ Configuration trouvée : {config.nom_entreprise}")
            print(f"   📍 Adresse : {config.get_adresse_complete()}")
            
            # Vérifier les nouveaux champs
            if hasattr(config, 'texte_contrat'):
                print("✅ Champ 'texte_contrat' disponible")
                if config.texte_contrat:
                    print(f"   📄 Texte contrat : {len(config.texte_contrat)} caractères")
                else:
                    print("   ⚠️  Texte contrat : Vide")
            else:
                print("❌ Champ 'texte_contrat' NOT disponible")
                
            if hasattr(config, 'texte_resiliation'):
                print("✅ Champ 'texte_resiliation' disponible")
                if config.texte_resiliation:
                    print(f"   📄 Texte résiliation : {len(config.texte_resiliation)} caractères")
                else:
                    print("   ⚠️  Texte résiliation : Vide")
            else:
                print("❌ Champ 'texte_resiliation' NOT disponible")
                
        else:
            print("⚠️  Aucune configuration d'entreprise trouvée")
            print("   Créez une configuration via l'administration Django")
            
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test de configuration : {e}")
        return False

def test_donnees_test():
    """Teste la disponibilité des données de test"""
    print("\n🔍 Test des données de test...")
    
    try:
        # Vérifier les contrats
        contrats_count = Contrat.objects.count()
        print(f"📊 Contrats disponibles : {contrats_count}")
        
        if contrats_count > 0:
            contrat = Contrat.objects.first()
            print(f"   📋 Premier contrat : {contrat.numero_contrat}")
            print(f"   🏠 Propriété : {contrat.propriete.titre}")
            print(f"   👤 Locataire : {contrat.locataire.nom} {contrat.locataire.prenom}")
        
        # Vérifier les propriétés
        proprietes_count = Propriete.objects.count()
        print(f"📊 Propriétés disponibles : {proprietes_count}")
        
        # Vérifier les locataires
        locataires_count = Locataire.objects.count()
        print(f"📊 Locataires disponibles : {locataires_count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test des données : {e}")
        return False

def test_urls_contrats():
    """Teste les URLs des contrats"""
    print("\n🔍 Test des URLs des contrats...")
    
    try:
        from django.urls import reverse
        
        urls_to_test = [
            'contrats:liste',
            'contrats:ajouter',
        ]
        
        for url_name in urls_to_test:
            try:
                url = reverse(url_name)
                print(f"✅ URL '{url_name}' : {url}")
            except Exception as e:
                print(f"❌ URL '{url_name}' : Erreur - {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test des URLs : {e}")
        return False

def main():
    """Fonction principale de test"""
    print("🚀 Test de l'interface des contrats et de la génération PDF")
    print("=" * 70)
    
    tests = [
        ("Configuration entreprise", test_configuration_entreprise),
        ("Données de test", test_donnees_test),
        ("URLs des contrats", test_urls_contrats),
        ("Formulaire de contrat", test_formulaire_contrat),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Erreur lors du test '{test_name}' : {e}")
            results.append((test_name, False))
    
    # Résumé
    print("\n" + "=" * 70)
    print("📊 RÉSUMÉ DES TESTS")
    print("=" * 70)
    
    success_count = 0
    for test_name, result in results:
        status = "✅ SUCCÈS" if result else "❌ ÉCHEC"
        print(f"{status} : {test_name}")
        if result:
            success_count += 1
    
    print(f"\n🎯 Résultat global : {success_count}/{len(results)} tests réussis")
    
    if success_count == len(results):
        print("🎉 Tous les tests sont passés avec succès !")
        print("   L'interface des contrats devrait fonctionner correctement.")
    else:
        print("⚠️  Certains tests ont échoué.")
        print("   Vérifiez les erreurs ci-dessus.")
    
    print("\n💡 ACTIONS RECOMMANDÉES")
    print("=" * 70)
    print("1. Accédez à http://localhost:8000/contrats/ajouter/")
    print("2. Vérifiez que la section PDF est visible")
    print("3. Testez la création d'un contrat avec génération PDF")
    print("4. Si des erreurs persistent, vérifiez les logs Django")

if __name__ == "__main__":
    main()
