#!/usr/bin/env python
"""
Script pour générer automatiquement tous les reçus manquants
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from paiements.models import Paiement, Recu
from datetime import datetime
import random

def generer_tous_recus():
    """Générer automatiquement tous les reçus manquants"""
    
    print("🚀 GÉNÉRATION AUTOMATIQUE DE TOUS LES REÇUS")
    print("=" * 60)
    
    # Vérifier l'état initial
    nb_paiements = Paiement.objects.count()
    nb_recus_initiaux = Recu.objects.count()
    paiements_sans_recus = Paiement.objects.filter(recu__isnull=True)
    nb_a_generer = paiements_sans_recus.count()
    
    print(f"📊 ÉTAT INITIAL:")
    print(f"   • Paiements totaux: {nb_paiements}")
    print(f"   • Reçus existants: {nb_recus_initiaux}")
    print(f"   • Reçus à générer: {nb_a_generer}")
    
    if nb_a_generer == 0:
        print("\n✅ Tous les paiements ont déjà des reçus!")
        return 0
    
    print(f"\n🔄 DÉBUT DE LA GÉNÉRATION...")
    print("=" * 60)
    
    recus_crees = 0
    erreurs = 0
    
    for i, paiement in enumerate(paiements_sans_recus, 1):
        try:
            # Générer un numéro de reçu unique
            numero_recu = f"REC-{datetime.now().strftime('%Y%m%d')}-{random.randint(10000, 99999)}"
            
            # Créer le reçu avec les bons attributs
            recu = Recu.objects.create(
                paiement=paiement,
                numero_recu=numero_recu,
                template_utilise='standard',
                valide=True,
                nombre_impressions=0,
                nombre_emails=0,
                genere_automatiquement=True
            )
            
            print(f"   ✅ [{i:3d}/{nb_a_generer}] Reçu créé: {numero_recu} pour Paiement ID: {paiement.id}")
            recus_crees += 1
            
        except Exception as e:
            print(f"   ❌ [{i:3d}/{nb_a_generer}] Erreur pour Paiement ID {paiement.id}: {e}")
            erreurs += 1
    
    # Résultats finaux
    print("\n" + "=" * 60)
    print("🎯 RÉSULTATS FINAUX")
    print("=" * 60)
    print(f"   • Reçus créés avec succès: {recus_crees}")
    print(f"   • Erreurs rencontrées: {erreurs}")
    print(f"   • Total reçus après génération: {Recu.objects.count()}")
    print(f"   • Taux de réussite: {(recus_crees/nb_a_generer*100):.1f}%")
    
    # Vérifier s'il reste des paiements sans reçus
    paiements_sans_recus_final = Paiement.objects.filter(recu__isnull=True).count()
    if paiements_sans_recus_final == 0:
        print(f"\n✅ SUCCÈS: Tous les paiements ont maintenant des reçus!")
    else:
        print(f"\n⚠️  ATTENTION: {paiements_sans_recus_final} paiements n'ont toujours pas de reçus")
    
    return recus_crees

if __name__ == "__main__":
    try:
        recus_crees = generer_tous_recus()
        print(f"\n🎉 GÉNÉRATION TERMINÉE! {recus_crees} reçus ont été créés.")
        
    except Exception as e:
        print(f"❌ ERREUR CRITIQUE: {e}")
        import traceback
        traceback.print_exc() 