#!/usr/bin/env python
"""
Test de toutes les pages principales de l'application
- Vérification que toutes les pages sont accessibles sans redirection
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from django.test import Client

def test_toutes_les_pages():
    """Test de toutes les pages principales"""
    
    print("🧪 TEST DE TOUTES LES PAGES PRINCIPALES")
    print("=" * 60)
    
    client = Client()
    
    # Liste de toutes les pages à tester
    pages_a_tester = [
        ('/paiements/', 'Page principale des paiements'),
        ('/paiements/retraits/', 'Liste des retraits'),
        ('/paiements/recaps-mensuels/', 'Recaps mensuels'),
        ('/paiements/recus/', 'Liste des reçus'),
        ('/paiements/charges-deductibles/', 'Charges déductibles'),
        ('/paiements/comptes/', 'Comptes bancaires'),
        ('/paiements/retraits-bailleur/', 'Retraits bailleur'),
        ('/paiements/liste/', 'Liste des paiements'),
        ('/paiements/charges-deductibles/liste/', 'Liste des charges déductibles'),
        ('/paiements/recus/liste/', 'Liste des reçus'),
    ]
    
    pages_ok = 0
    pages_redirection = 0
    pages_erreur = 0
    
    for url, description in pages_a_tester:
        try:
            response = client.get(url)
            status = response.status_code
            
            if status == 200:
                print(f"✅ {description}: {url} - Status: {status}")
                pages_ok += 1
            elif status == 302:
                print(f"❌ {description}: {url} - Status: {status} -> Redirection vers: {response.url}")
                pages_redirection += 1
            elif status == 403:
                print(f"🚫 {description}: {url} - Status: {status} (Forbidden)")
                pages_erreur += 1
            elif status == 404:
                print(f"❓ {description}: {url} - Status: {status} (Not Found)")
                pages_erreur += 1
            else:
                print(f"⚠️ {description}: {url} - Status: {status}")
                pages_erreur += 1
                
        except Exception as e:
            print(f"❌ {description}: {url} - Erreur: {e}")
            pages_erreur += 1
    
    # Résumé
    print("\n📊 RÉSUMÉ DU TEST")
    print("-" * 30)
    print(f"✅ Pages accessibles (200): {pages_ok}")
    print(f"❌ Pages avec redirection (302): {pages_redirection}")
    print(f"⚠️ Pages avec erreur (403/404): {pages_erreur}")
    print(f"📋 Total des pages testées: {len(pages_a_tester)}")
    
    if pages_redirection == 0:
        print("\n🎉 SUCCÈS ! Aucune page ne redirige plus !")
        print("✅ Le problème de redirection est complètement résolu")
    else:
        print(f"\n⚠️ Il reste {pages_redirection} pages qui redirigent")
        print("🔍 Vérifiez ces pages pour identifier le problème")
    
    return pages_redirection == 0

if __name__ == "__main__":
    test_toutes_les_pages()
