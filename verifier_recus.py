#!/usr/bin/env python
"""
Script pour vérifier l'état des reçus dans la base de données
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from paiements.models import Paiement, Recu
from django.db import connection

def verifier_etat_recus():
    """Vérifier l'état des reçus dans la base de données"""
    
    print("🔍 VÉRIFICATION DE L'ÉTAT DES REÇUS")
    print("=" * 50)
    
    # Vérifier les tables
    with connection.cursor() as cursor:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%recu%'")
        tables_recus = cursor.fetchall()
        print(f"📋 Tables liées aux reçus: {[table[0] for table in tables_recus]}")
    
    # Compter les paiements et reçus
    nb_paiements = Paiement.objects.count()
    nb_recus = Recu.objects.count()
    
    print(f"\n📊 STATISTIQUES:")
    print(f"   • Paiements: {nb_paiements}")
    print(f"   • Reçus: {nb_recus}")
    print(f"   • Taux de génération: {(nb_recus/nb_paiements*100):.1f}%" if nb_paiements > 0 else "   • Taux de génération: N/A")
    
    # Vérifier les reçus existants
    if nb_recus > 0:
        print(f"\n📄 DERNIERS REÇUS:")
        for recu in Recu.objects.all()[:10]:
            print(f"   • {recu.numero_recu} - Paiement ID: {recu.paiement.id} - Statut: {recu.get_statut_display()}")
    else:
        print(f"\n❌ AUCUN REÇU TROUVÉ")
    
    # Vérifier les paiements sans reçus
    paiements_sans_recus = Paiement.objects.filter(recu__isnull=True).count()
    print(f"\n⚠️  PAIEMENTS SANS REÇUS: {paiements_sans_recus}")
    
    if paiements_sans_recus > 0:
        print(f"   Derniers paiements sans reçus:")
        for paiement in Paiement.objects.filter(recu__isnull=True)[:5]:
            print(f"   • ID: {paiement.id} - {paiement.montant} F CFA - {paiement.date_paiement} - Contrat: {paiement.contrat.numero_contrat}")
    
    return nb_paiements, nb_recus, paiements_sans_recus

def generer_recus_manquants():
    """Générer les reçus manquants pour les paiements existants"""
    
    print(f"\n🔄 GÉNÉRATION DES REÇUS MANQUANTS")
    print("=" * 50)
    
    paiements_sans_recus = Paiement.objects.filter(recu__isnull=True)
    nb_a_generer = paiements_sans_recus.count()
    
    if nb_a_generer == 0:
        print("✅ Tous les paiements ont déjà des reçus!")
        return 0
    
    print(f"📝 Génération de {nb_a_generer} reçus...")
    
    from datetime import datetime
    import random
    
    recus_crees = 0
    
    for paiement in paiements_sans_recus:
        try:
            # Créer le reçu en utilisant la méthode du modèle
            recu = Recu.objects.create(
                paiement=paiement,
                numero_recu=f"REC-{datetime.now().strftime('%Y%m%d')}-{random.randint(10000, 99999)}",
                template_utilise='standard',
                valide=True,
                nombre_impressions=0,
                nombre_emails=0,
                generation_automatique=True
            )
            
            print(f"   ✅ Reçu créé: {recu.numero_recu} pour Paiement ID: {paiement.id}")
            recus_crees += 1
            
        except Exception as e:
            print(f"   ❌ Erreur pour Paiement ID {paiement.id}: {e}")
    
    print(f"\n🎯 RÉSULTAT: {recus_crees} reçus générés sur {nb_a_generer}")
    return recus_crees

def generer_recus_automatiques():
    """Générer automatiquement tous les reçus manquants sans demander confirmation"""
    
    print(f"\n🚀 GÉNÉRATION AUTOMATIQUE DES REÇUS")
    print("=" * 50)
    
    paiements_sans_recus = Paiement.objects.filter(recu__isnull=True)
    nb_a_generer = paiements_sans_recus.count()
    
    if nb_a_generer == 0:
        print("✅ Tous les paiements ont déjà des reçus!")
        return 0
    
    print(f"📝 Génération automatique de {nb_a_generer} reçus...")
    
    from datetime import datetime
    import random
    
    recus_crees = 0
    
    for paiement in paiements_sans_recus:
        try:
            # Créer le reçu en utilisant la méthode du modèle
            recu = Recu.objects.create(
                paiement=paiement,
                numero_recu=f"REC-{datetime.now().strftime('%Y%m%d')}-{random.randint(10000, 99999)}",
                template_utilise='standard',
                valide=True,
                nombre_impressions=0,
                nombre_emails=0,
                generation_automatique=True
            )
            
            print(f"   ✅ Reçu créé: {recu.numero_recu} pour Paiement ID: {paiement.id}")
            recus_crees += 1
            
        except Exception as e:
            print(f"   ❌ Erreur pour Paiement ID {paiement.id}: {e}")
    
    print(f"\n🎯 RÉSULTAT: {recus_crees} reçus générés sur {nb_a_generer}")
    return recus_crees

if __name__ == "__main__":
    try:
        # Vérifier l'état actuel
        nb_paiements, nb_recus, paiements_sans_recus = verifier_etat_recus()
        
        # Générer automatiquement les reçus manquants
        if paiements_sans_recus > 0:
            print(f"\n🤔 Voulez-vous générer automatiquement les {paiements_sans_recus} reçus manquants? (o/n): ", end="")
            reponse = input().lower().strip()
            
            if reponse in ['o', 'oui', 'y', 'yes']:
                recus_crees = generer_recus_automatiques()
                
                if recus_crees > 0:
                    print(f"\n✅ GÉNÉRATION TERMINÉE!")
                    print(f"   • Reçus créés: {recus_crees}")
                    print(f"   • Total reçus: {Recu.objects.count()}")
                    
                    # Vérifier l'état final
                    print(f"\n🔍 VÉRIFICATION FINALE:")
                    verifier_etat_recus()
            else:
                print("❌ Génération annulée par l'utilisateur")
        else:
            print("\n✅ Tous les paiements ont des reçus!")
            
    except Exception as e:
        print(f"❌ ERREUR: {e}")
        import traceback
        traceback.print_exc() 