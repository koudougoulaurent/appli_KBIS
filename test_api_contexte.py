#!/usr/bin/env python3
"""
Script de test pour vérifier le bon fonctionnement de l'API de contexte intelligent.
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from paiements.services_intelligents_retraits import ServiceContexteIntelligentRetraits
from proprietes.models import Bailleur

def test_api_contexte():
    """Test de l'API de contexte intelligent."""
    print("🧪 Test de l'API de contexte intelligent")
    print("=" * 50)
    
    # Récupérer le premier bailleur disponible
    try:
        bailleur = Bailleur.objects.filter(actif=True).first()
        if not bailleur:
            print("❌ Aucun bailleur actif trouvé dans la base de données")
            return False, None
        
        print(f"✅ Bailleur trouvé : {bailleur.get_nom_complet()} (ID: {bailleur.id})")
        
        # Tester le service de contexte
        print("\n🔍 Test du service de contexte...")
        contexte = ServiceContexteIntelligentRetraits.get_contexte_complet_bailleur(bailleur.id)
        
        if contexte['success']:
            print("✅ Service de contexte fonctionne correctement")
            data = contexte['data']
            
            print(f"📊 Données récupérées :")
            print(f"   - Bailleur : {data['bailleur']['nom']} {data['bailleur']['prenom']}")
            print(f"   - Propriétés : {len(data['proprietes']['proprietes'])}")
            print(f"   - Contrats actifs : {len(data['contrats_actifs'])}")
            print(f"   - Paiements récents : {len(data['paiements_recents'])}")
            print(f"   - Charges déductibles : {len(data['charges_deductibles'])}")
            print(f"   - Retraits récents : {len(data['retraits_recents'])}")
            print(f"   - Alertes : {len(data['alertes'])}")
            print(f"   - Suggestions : {len(data['suggestions'])}")
            
            return True, bailleur.id
        else:
            print(f"❌ Erreur dans le service : {contexte['error']}")
            return False, None
            
    except Exception as e:
        print(f"❌ Erreur lors du test : {str(e)}")
        import traceback
        traceback.print_exc()
        return False, None

def test_urls(bailleur_id):
    """Test des URLs de l'API."""
    print("\n🌐 Test des URLs de l'API")
    print("=" * 30)
    
    try:
        from django.urls import reverse
        from django.test import Client
        
        client = Client()
        
        # Test de l'URL de contexte
        url = f'/paiements/api/contexte-bailleur/{bailleur_id}/'
        print(f"🔗 Test de l'URL : {url}")
        
        response = client.get(url)
        print(f"📡 Statut de la réponse : {response.status_code}")
        
        if response.status_code == 200:
            print("✅ API accessible et fonctionnelle")
            return True
        else:
            print(f"❌ Erreur HTTP : {response.status_code}")
            print(f"📄 Contenu de la réponse : {response.content[:200]}...")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors du test des URLs : {str(e)}")
        return False

if __name__ == '__main__':
    print("🚀 Démarrage des tests de l'API de contexte intelligent")
    
    # Test du service
    service_ok, bailleur_id = test_api_contexte()
    
    if service_ok and bailleur_id:
        # Test des URLs
        urls_ok = test_urls(bailleur_id)
        
        if urls_ok:
            print("\n🎉 Tous les tests sont passés avec succès !")
            print("✅ L'API de contexte intelligent fonctionne correctement")
        else:
            print("\n⚠️  Le service fonctionne mais il y a un problème avec les URLs")
    else:
        print("\n❌ Le service de contexte ne fonctionne pas correctement")
    
    print("\n📋 Résumé des tests terminé")
