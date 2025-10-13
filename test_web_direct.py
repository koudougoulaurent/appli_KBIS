#!/usr/bin/env python
"""
Script pour tester directement la génération via l'interface web
"""

import os
import sys
import django
import requests
from datetime import datetime

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings_simple')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

django.setup()

from paiements.models import Paiement, QuittancePaiement
from django.contrib.auth import get_user_model
from django.test import Client

User = get_user_model()


def test_web_direct():
    """Test direct de la génération via l'interface web"""
    print("=== TEST GENERATION VIA INTERFACE WEB ===\n")
    
    # Test 1: Récupérer un paiement et créer une quittance
    print("1. Creation d'une quittance de test...")
    try:
        paiement = Paiement.objects.filter(statut='valide').first()
        if not paiement:
            print("   [ERREUR] Aucun paiement valide trouve")
            return
        
        print(f"   Paiement: ID {paiement.id} - {paiement.montant} F CFA")
        
        # Supprimer l'ancienne quittance si elle existe
        if hasattr(paiement, 'quittance'):
            print("   Suppression de l'ancienne quittance...")
            paiement.quittance.delete()
        
        # Créer une nouvelle quittance
        user = User.objects.first()
        quittance = QuittancePaiement.objects.create(
            paiement=paiement,
            cree_par=user
        )
        
        print(f"   [OK] Quittance creee: {quittance.numero_quittance}")
        
    except Exception as e:
        print(f"   [ERREUR] {e}")
        return
    
    print()
    
    # Test 2: Test direct de la méthode du modèle
    print("2. Test direct de la methode du modele...")
    try:
        html_direct = paiement.generer_quittance_kbis_dynamique()
        if html_direct:
            print("   [OK] Generation directe reussie")
            print(f"   Taille: {len(html_direct)} caracteres")
            
            if 'data:image/png;base64' in html_direct:
                print("   [OK] Image base64 presente")
            else:
                print("   [ATTENTION] Image base64 manquante")
            
            # Sauvegarder
            with open('test_direct_model.html', 'w', encoding='utf-8') as f:
                f.write(html_direct)
            print("   Fichier sauvegarde: test_direct_model.html")
        else:
            print("   [ERREUR] Generation directe echouee")
            
    except Exception as e:
        print(f"   [ERREUR] {e}")
        import traceback
        traceback.print_exc()
    
    print()
    
    # Test 3: Test via le client Django
    print("3. Test via le client Django...")
    try:
        client = Client()
        
        # Se connecter avec un utilisateur
        user = User.objects.first()
        if user:
            login_success = client.login(username=user.username, password='admin')  # Essayons avec le mot de passe par défaut
            if not login_success:
                # Essayer de créer un utilisateur de test
                test_user, created = User.objects.get_or_create(
                    username='test_debug',
                    defaults={
                        'email': 'test@debug.com',
                        'first_name': 'Test',
                        'last_name': 'Debug',
                        'is_active': True,
                        'is_staff': True,
                    }
                )
                if created:
                    test_user.set_password('testpass123')
                    test_user.save()
                    login_success = client.login(username='test_debug', password='testpass123')
                
            if login_success:
                print("   [OK] Connexion reussie")
                
                # Tester l'URL de la quittance
                url = f'/paiements/quittance/{quittance.id}/'
                print(f"   URL: {url}")
                
                response = client.get(url)
                print(f"   Status: {response.status_code}")
                
                if response.status_code == 200:
                    print("   [OK] Page accessible")
                    
                    content = response.content.decode('utf-8')
                    print(f"   Taille contenu: {len(content)} caracteres")
                    
                    if 'data:image/png;base64' in content:
                        print("   [OK] Image base64 presente dans la reponse web")
                    else:
                        print("   [ATTENTION] Image base64 manquante dans la reponse web")
                    
                    # Sauvegarder
                    with open('test_web_response.html', 'w', encoding='utf-8') as f:
                        f.write(content)
                    print("   Fichier sauvegarde: test_web_response.html")
                else:
                    print(f"   [ATTENTION] Status inattendu: {response.status_code}")
            else:
                print("   [ERREUR] Impossible de se connecter")
        else:
            print("   [ERREUR] Aucun utilisateur trouve")
            
    except Exception as e:
        print(f"   [ERREUR] {e}")
        import traceback
        traceback.print_exc()
    
    print()
    
    # Test 4: Comparaison des contenus
    print("4. Comparaison des contenus...")
    try:
        if os.path.exists('test_direct_model.html') and os.path.exists('test_web_response.html'):
            with open('test_direct_model.html', 'r', encoding='utf-8') as f:
                direct_content = f.read()
            
            with open('test_web_response.html', 'r', encoding='utf-8') as f:
                web_content = f.read()
            
            print(f"   Taille direct: {len(direct_content)} caracteres")
            print(f"   Taille web: {len(web_content)} caracteres")
            
            if direct_content == web_content:
                print("   [OK] Contenus identiques")
            else:
                print("   [ATTENTION] Contenus differents")
                
                # Vérifier les différences
                if 'data:image/png;base64' in direct_content and 'data:image/png;base64' not in web_content:
                    print("   [PROBLEME] Image presente en direct mais absente via web")
                elif 'data:image/png;base64' not in direct_content and 'data:image/png;base64' in web_content:
                    print("   [PROBLEME] Image presente via web mais absente en direct")
        else:
            print("   [ATTENTION] Fichiers de comparaison non trouves")
            
    except Exception as e:
        print(f"   [ERREUR] {e}")
    
    print("\n=== FIN TESTS ===")


if __name__ == "__main__":
    test_web_direct()

