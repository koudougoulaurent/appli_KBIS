#!/usr/bin/env python3
"""
Script de débogage pour identifier l'erreur de type dans le service.
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from paiements.services_intelligents_retraits import ServiceContexteIntelligentRetraits
from proprietes.models import Bailleur

def debug_service():
    """Débogage étape par étape du service."""
    print("🔍 Débogage du service de contexte intelligent")
    print("=" * 50)
    
    try:
        # Récupérer le premier bailleur disponible
        bailleur = Bailleur.objects.filter(actif=True).first()
        if not bailleur:
            print("❌ Aucun bailleur actif trouvé")
            return
        
        print(f"✅ Bailleur trouvé : {bailleur.get_nom_complet()} (ID: {bailleur.id})")
        
        # Test étape par étape
        print("\n1️⃣ Test des informations du bailleur...")
        try:
            infos = ServiceContexteIntelligentRetraits._get_infos_bailleur(bailleur)
            print("✅ Informations du bailleur OK")
        except Exception as e:
            print(f"❌ Erreur infos bailleur : {e}")
            return
        
        print("\n2️⃣ Test des propriétés...")
        try:
            proprietes = ServiceContexteIntelligentRetraits._get_proprietes_bailleur(bailleur)
            print("✅ Propriétés OK")
        except Exception as e:
            print(f"❌ Erreur propriétés : {e}")
            import traceback
            traceback.print_exc()
            return
        
        print("\n3️⃣ Test des contrats...")
        try:
            contrats = ServiceContexteIntelligentRetraits._get_contrats_actifs(bailleur)
            print("✅ Contrats OK")
        except Exception as e:
            print(f"❌ Erreur contrats : {e}")
            import traceback
            traceback.print_exc()
            return
        
        print("\n4️⃣ Test des paiements...")
        try:
            paiements = ServiceContexteIntelligentRetraits._get_paiements_recents(bailleur)
            print("✅ Paiements OK")
        except Exception as e:
            print(f"❌ Erreur paiements : {e}")
            import traceback
            traceback.print_exc()
            return
        
        print("\n🎉 Tous les tests sont passés !")
        
    except Exception as e:
        print(f"❌ Erreur générale : {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    debug_service()
