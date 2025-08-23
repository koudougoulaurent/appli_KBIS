#!/usr/bin/env python3
"""
Script simple pour tester l'interface des contrats
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

User = get_user_model()

def test_acces_formulaire():
    """Test simple d'accès au formulaire"""
    print("🔍 Test d'accès au formulaire de contrat...")
    
    try:
        # Utiliser un utilisateur existant
        user = User.objects.filter(is_staff=True).first()
        
        if not user:
            print("⚠️  Aucun utilisateur admin trouvé")
            return False
        
        print(f"✅ Utilisateur trouvé : {user.username}")
        
        # Créer un client et se connecter
        client = Client()
        client.force_login(user)  # Connexion forcée pour les tests
        
        # Tester l'accès au formulaire
        url = reverse('contrats:ajouter')
        response = client.get(url)
        
        print(f"📋 URL testée : {url}")
        print(f"📊 Code de statut : {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Formulaire accessible")
            
            # Vérifier le contenu
            content = response.content.decode('utf-8')
            
            checks = [
                ('telecharger_pdf', 'Champ telecharger_pdf'),
                ('Générer le contrat en PDF', 'Label PDF'),
                ('pdf-section', 'Section PDF'),
                ('form-check-input', 'Input checkbox'),
            ]
            
            for search_text, description in checks:
                if search_text in content:
                    print(f"✅ {description} trouvé")
                else:
                    print(f"❌ {description} NOT trouvé")
            
            return True
        else:
            print(f"❌ Erreur d'accès : {response.status_code}")
            if hasattr(response, 'content'):
                print(f"Contenu : {response.content.decode('utf-8')[:500]}...")
            return False
            
    except Exception as e:
        print(f"❌ Erreur : {e}")
        import traceback
        traceback.print_exc()
        return False

def test_urls_disponibles():
    """Teste les URLs disponibles"""
    print("\n🔍 Test des URLs...")
    
    try:
        urls_contrats = [
            'contrats:liste',
            'contrats:ajouter',
        ]
        
        for url_name in urls_contrats:
            try:
                url = reverse(url_name)
                print(f"✅ {url_name} : {url}")
            except Exception as e:
                print(f"❌ {url_name} : {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur URLs : {e}")
        return False

def main():
    print("🚀 Test simple de l'interface des contrats")
    print("=" * 50)
    
    # Tests
    urls_ok = test_urls_disponibles()
    form_ok = test_acces_formulaire()
    
    print("\n" + "=" * 50)
    print("📊 RÉSUMÉ")
    print("=" * 50)
    
    if urls_ok and form_ok:
        print("🎉 Interface accessible - Les changements PDF devraient être visibles")
        print("\n💡 Actions à faire :")
        print("1. Ouvrir http://localhost:8000/contrats/ajouter/")
        print("2. Vérifier la section 'Génération automatique de contrat PDF'")
        print("3. Tester la création d'un contrat avec PDF")
    else:
        print("⚠️  Problèmes détectés - Vérifier les erreurs ci-dessus")

if __name__ == "__main__":
    main()
