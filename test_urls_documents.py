#!/usr/bin/env python
"""
Script pour tester les URLs de génération de documents
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

User = get_user_model()


def test_document_urls():
    """Test les URLs de génération de documents"""
    print("=== TEST DES URLs DE GENERATION DE DOCUMENTS ===\n")
    
    base_url = "http://localhost:8000"
    
    # Récupérer un paiement existant
    paiement = Paiement.objects.filter(statut='valide').first()
    if not paiement:
        print("[ERREUR] Aucun paiement valide trouve dans la base de donnees")
        return
    
    print(f"Paiement de test: ID {paiement.id} - {paiement.montant} F CFA")
    print()
    
    # Test 1: URL de génération de quittance manuelle
    print("1. Test generation quittance manuelle...")
    try:
        url = f"{base_url}/paiements/paiement/{paiement.id}/generer-quittance/"
        print(f"   URL: {url}")
        
        # Simuler une requête POST
        response = requests.post(url, timeout=10)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            print("[OK] Generation quittance manuelle fonctionne")
        elif response.status_code == 302:
            print("[OK] Redirection (normal pour POST)")
        else:
            print(f"[ATTENTION] Status inattendu: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("[ERREUR] Impossible de se connecter au serveur. Assurez-vous que le serveur Django est demarre.")
    except Exception as e:
        print(f"[ERREUR] {e}")
    
    print()
    
    # Test 2: URL de génération de récépissé KBIS
    print("2. Test generation recepisse KBIS...")
    try:
        url = f"{base_url}/paiements/paiement/{paiement.id}/recu-kbis/"
        print(f"   URL: {url}")
        
        response = requests.get(url, timeout=10)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            print("[OK] Generation recepisse KBIS fonctionne")
            # Vérifier que c'est du HTML
            if 'text/html' in response.headers.get('content-type', ''):
                print("   Contenu HTML detecte")
            else:
                print(f"   Type de contenu: {response.headers.get('content-type', 'Inconnu')}")
        else:
            print(f"[ATTENTION] Status inattendu: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("[ERREUR] Impossible de se connecter au serveur. Assurez-vous que le serveur Django est demarre.")
    except Exception as e:
        print(f"[ERREUR] {e}")
    
    print()
    
    # Test 3: Vérifier les quittances existantes
    print("3. Test liste des quittances...")
    try:
        url = f"{base_url}/paiements/quittances/"
        print(f"   URL: {url}")
        
        response = requests.get(url, timeout=10)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            print("[OK] Liste des quittances accessible")
        else:
            print(f"[ATTENTION] Status inattendu: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("[ERREUR] Impossible de se connecter au serveur.")
    except Exception as e:
        print(f"[ERREUR] {e}")
    
    print()
    
    # Test 4: Créer une quittance et tester son affichage
    print("4. Test creation et affichage quittance...")
    try:
        # Créer une quittance si elle n'existe pas
        quittance, created = QuittancePaiement.objects.get_or_create(
            paiement=paiement,
            defaults={'cree_par': User.objects.first()}
        )
        
        if created:
            print(f"   Quittance creee: {quittance.numero_quittance}")
        else:
            print(f"   Quittance existante: {quittance.numero_quittance}")
        
        # Tester l'affichage de la quittance
        url = f"{base_url}/paiements/quittance/{quittance.id}/"
        print(f"   URL: {url}")
        
        response = requests.get(url, timeout=10)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            print("[OK] Affichage quittance fonctionne")
            # Vérifier que c'est du HTML
            if 'text/html' in response.headers.get('content-type', ''):
                print("   Contenu HTML detecte")
            else:
                print(f"   Type de contenu: {response.headers.get('content-type', 'Inconnu')}")
        else:
            print(f"[ATTENTION] Status inattendu: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("[ERREUR] Impossible de se connecter au serveur.")
    except Exception as e:
        print(f"[ERREUR] {e}")
    
    print("\n=== FIN DES TESTS ===")


if __name__ == "__main__":
    test_document_urls()

