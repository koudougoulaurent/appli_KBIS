#!/usr/bin/env python
"""
Script pour tester l'affichage des documents via le serveur web
"""

import os
import sys
import django
import requests
import webbrowser
from datetime import datetime

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings_simple')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

django.setup()

from paiements.models import Paiement, QuittancePaiement
from django.contrib.auth import get_user_model

User = get_user_model()


def test_web_documents():
    """Test l'affichage des documents via le serveur web"""
    print("=== TEST DOCUMENTS VIA SERVEUR WEB ===\n")
    
    base_url = "http://localhost:8000"
    
    # Test 1: Vérifier que le serveur est accessible
    print("1. Verification du serveur...")
    try:
        response = requests.get(base_url, timeout=5)
        print(f"   Serveur accessible: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("[ERREUR] Serveur non accessible. Demarrez le serveur avec: python manage.py runserver")
        return
    except Exception as e:
        print(f"[ERREUR] {e}")
        return
    
    print()
    
    # Test 2: Tester l'accès aux images statiques
    print("2. Test acces aux images statiques...")
    try:
        image_url = f"{base_url}/static/images/enteteEnImage.png"
        response = requests.get(image_url, timeout=5)
        print(f"   Image d'entete: {response.status_code}")
        
        if response.status_code == 200:
            print("   [OK] Image d'entete accessible via le serveur")
            print(f"   Taille: {len(response.content)} bytes")
        else:
            print("   [ATTENTION] Image d'entete non accessible")
            
    except Exception as e:
        print(f"[ERREUR] {e}")
    
    print()
    
    # Test 3: Tester la génération de récépissé via URL
    print("3. Test generation recepisse via URL...")
    try:
        paiement = Paiement.objects.filter(statut='valide').first()
        if paiement:
            url = f"{base_url}/paiements/paiement/{paiement.id}/recu-kbis/"
            print(f"   URL: {url}")
            
            response = requests.get(url, timeout=10)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                print("   [OK] Recepisse genere via URL")
                
                # Vérifier que l'image est dans le contenu
                if 'enteteEnImage.png' in response.text:
                    print("   [OK] Image d'entete presente dans le recepisse")
                else:
                    print("   [ATTENTION] Image d'entete manquante dans le recepisse")
                
                # Sauvegarder pour vérification
                with open('test_recepisse_web.html', 'w', encoding='utf-8') as f:
                    f.write(response.text)
                print("   Recepisse sauvegarde: test_recepisse_web.html")
            else:
                print(f"   [ATTENTION] Status inattendu: {response.status_code}")
        else:
            print("   [ATTENTION] Aucun paiement valide trouve")
            
    except Exception as e:
        print(f"[ERREUR] {e}")
    
    print()
    
    # Test 4: Tester l'affichage des quittances
    print("4. Test affichage des quittances...")
    try:
        # Créer une quittance si nécessaire
        paiement = Paiement.objects.filter(statut='valide').first()
        if paiement:
            quittance, created = QuittancePaiement.objects.get_or_create(
                paiement=paiement,
                defaults={'cree_par': User.objects.first()}
            )
            
            url = f"{base_url}/paiements/quittance/{quittance.id}/"
            print(f"   URL: {url}")
            
            response = requests.get(url, timeout=10)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                print("   [OK] Quittance accessible via URL")
                
                # Vérifier l'image
                if 'enteteEnImage.png' in response.text:
                    print("   [OK] Image d'entete presente dans la quittance")
                else:
                    print("   [ATTENTION] Image d'entete manquante dans la quittance")
                
                # Sauvegarder pour vérification
                with open('test_quittance_web.html', 'w', encoding='utf-8') as f:
                    f.write(response.text)
                print("   Quittance sauvegarde: test_quittance_web.html")
            else:
                print(f"   [ATTENTION] Status inattendu: {response.status_code}")
        else:
            print("   [ATTENTION] Aucun paiement valide trouve")
            
    except Exception as e:
        print(f"[ERREUR] {e}")
    
    print()
    
    # Test 5: Ouvrir les documents dans le navigateur
    print("5. Ouverture des documents dans le navigateur...")
    try:
        # Ouvrir le document de démonstration
        demo_file = os.path.abspath('demo_quittance_avec_image.html')
        if os.path.exists(demo_file):
            print(f"   Ouverture: {demo_file}")
            webbrowser.open(f'file://{demo_file}')
            print("   [OK] Document demo ouvert dans le navigateur")
        else:
            print("   [ATTENTION] Fichier demo non trouve")
            
    except Exception as e:
        print(f"[ERREUR] {e}")
    
    print("\n=== FIN DES TESTS ===")
    print("\nINSTRUCTIONS POUR TESTER MANUELLEMENT:")
    print("1. Ouvrez votre navigateur")
    print("2. Allez sur http://localhost:8000/paiements/")
    print("3. Cliquez sur un paiement")
    print("4. Cliquez sur 'Quittances' ou 'Recépissé'")
    print("5. Vérifiez que l'image d'entête s'affiche correctement")


if __name__ == "__main__":
    test_web_documents()

