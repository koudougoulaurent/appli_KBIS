#!/usr/bin/env python
"""
Test simple pour vérifier que les reçus sont bien générés
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from paiements.models import Paiement, Recu

def test_recus_simple():
    """Test simple de vérification des reçus"""
    
    print("🧪 TEST SIMPLE DES REÇUS")
    print("=" * 40)
    
    # Vérifier l'état des données
    nb_paiements = Paiement.objects.count()
    nb_recus = Recu.objects.count()
    
    print(f"📊 ÉTAT DES DONNÉES:")
    print(f"   • Paiements: {nb_paiements}")
    print(f"   • Reçus: {nb_recus}")
    print(f"   • Taux de couverture: {(nb_recus/nb_paiements*100):.1f}%")
    
    if nb_recus == 0:
        print("❌ AUCUN REÇU TROUVÉ")
        return False
    
    # Vérifier quelques reçus
    print(f"\n📄 EXEMPLES DE REÇUS:")
    for i, recu in enumerate(Recu.objects.all()[:5], 1):
        print(f"   {i}. {recu.numero_recu} - Paiement ID: {recu.paiement.id} - {recu.paiement.montant} XOF")
    
    # Vérifier qu'il n'y a plus de paiements sans reçus
    paiements_sans_recus = Paiement.objects.filter(recu__isnull=True).count()
    print(f"\n⚠️  PAIEMENTS SANS REÇUS: {paiements_sans_recus}")
    
    if paiements_sans_recus == 0:
        print("✅ TOUS LES PAIEMENTS ONT DES REÇUS!")
        return True
    else:
        print("❌ IL RESTE DES PAIEMENTS SANS REÇUS")
        return False

def afficher_statistiques_recus():
    """Afficher des statistiques sur les reçus"""
    
    print(f"\n📈 STATISTIQUES DES REÇUS")
    print("=" * 40)
    
    # Statistiques par template
    templates = Recu.objects.values_list('template_utilise', flat=True).distinct()
    print(f"📋 Templates utilisés:")
    for template in templates:
        count = Recu.objects.filter(template_utilise=template).count()
        print(f"   • {template}: {count} reçus")
    
    # Statistiques par statut
    valides = Recu.objects.filter(valide=True).count()
    non_valides = Recu.objects.filter(valide=False).count()
    print(f"\n✅ Reçus validés: {valides}")
    print(f"❌ Reçus non validés: {non_valides}")
    
    # Statistiques d'impression
    imprimes = Recu.objects.filter(imprime=True).count()
    non_imprimes = Recu.objects.filter(imprime=False).count()
    print(f"\n🖨️  Reçus imprimés: {imprimes}")
    print(f"📄 Reçus non imprimés: {non_imprimes}")
    
    # Statistiques d'envoi email
    envoyes_email = Recu.objects.filter(envoye_email=True).count()
    non_envoyes_email = Recu.objects.filter(envoye_email=False).count()
    print(f"\n📧 Reçus envoyés par email: {envoyes_email}")
    print(f"📮 Reçus non envoyés par email: {non_envoyes_email}")

if __name__ == "__main__":
    try:
        success = test_recus_simple()
        
        if success:
            afficher_statistiques_recus()
            print(f"\n🎉 SUCCÈS: Tous les reçus sont générés et opérationnels!")
        else:
            print(f"\n❌ ÉCHEC: Des problèmes ont été détectés")
            
    except Exception as e:
        print(f"❌ ERREUR: {e}")
        import traceback
        traceback.print_exc() 