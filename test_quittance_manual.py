#!/usr/bin/env python
"""
Script pour tester la génération manuelle de quittance
"""

import os
import sys
import django
from datetime import datetime

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings_simple')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

django.setup()

from paiements.models import Paiement, QuittancePaiement
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType

User = get_user_model()


def test_quittance_manual():
    """Test la génération manuelle de quittance"""
    print("=== TEST GENERATION MANUELLE DE QUITTANCE ===\n")
    
    # Récupérer un paiement existant
    paiement = Paiement.objects.filter(statut='valide').first()
    if not paiement:
        print("[ERREUR] Aucun paiement valide trouve dans la base de donnees")
        return
    
    print(f"Paiement de test: ID {paiement.id} - {paiement.montant} F CFA")
    print()
    
    # Test 1: Vérifier si une quittance existe déjà
    print("1. Verification quittance existante...")
    try:
        if hasattr(paiement, 'quittance'):
            print(f"   Quittance existante: {paiement.quittance.numero_quittance}")
            print("   Suppression de l'ancienne quittance...")
            paiement.quittance.delete()
        else:
            print("   Aucune quittance existante")
    except Exception as e:
        print(f"[ERREUR] {e}")
    
    print()
    
    # Test 2: Créer une quittance manuellement
    print("2. Creation quittance manuelle...")
    try:
        # Récupérer le premier utilisateur
        user = User.objects.first()
        if not user:
            print("[ERREUR] Aucun utilisateur trouve")
            return
        
        print(f"   Utilisateur: {user.username}")
        
        # Créer la quittance
        quittance = QuittancePaiement.objects.create(
            paiement=paiement,
            cree_par=user
        )
        
        print(f"[OK] Quittance creee: {quittance.numero_quittance}")
        
    except Exception as e:
        print(f"[ERREUR] Creation quittance: {e}")
        return
    
    print()
    
    # Test 3: Tester la génération du contenu HTML
    print("3. Test generation contenu HTML...")
    try:
        html_content = paiement.generer_quittance_kbis_dynamique()
        if html_content:
            print("[OK] Contenu HTML genere avec succes")
            print(f"   Taille: {len(html_content)} caracteres")
            
            # Sauvegarder pour vérification
            with open('test_quittance_manual.html', 'w', encoding='utf-8') as f:
                f.write(html_content)
            print("   Fichier sauvegarde: test_quittance_manual.html")
        else:
            print("[ERREUR] Aucun contenu HTML genere")
            
    except Exception as e:
        print(f"[ERREUR] Generation HTML: {e}")
    
    print()
    
    # Test 4: Tester l'affichage de la quittance
    print("4. Test affichage quittance...")
    try:
        # Simuler la vue quittance_detail
        from paiements.views import quittance_detail
        from django.test import RequestFactory
        from django.contrib.auth.models import AnonymousUser
        
        factory = RequestFactory()
        request = factory.get(f'/paiements/quittance/{quittance.id}/')
        request.user = user
        
        response = quittance_detail(request, quittance.id)
        
        print(f"   Status code: {response.status_code}")
        print(f"   Content type: {response.get('Content-Type', 'Non specifie')}")
        
        if response.status_code == 200:
            print("[OK] Affichage quittance fonctionne")
        else:
            print(f"[ATTENTION] Status inattendu: {response.status_code}")
            
    except Exception as e:
        print(f"[ERREUR] Affichage quittance: {e}")
    
    print()
    
    # Test 5: Vérifier les logs d'audit
    print("5. Verification logs d'audit...")
    try:
        from core.models import AuditLog
        
        logs = AuditLog.objects.filter(
            content_type=ContentType.objects.get_for_model(QuittancePaiement),
            object_id=quittance.id
        ).order_by('-timestamp')
        
        print(f"   Nombre de logs trouves: {logs.count()}")
        for log in logs[:3]:  # Afficher les 3 derniers
            print(f"   - {log.action} par {log.user} le {log.timestamp}")
            
    except Exception as e:
        print(f"[ERREUR] Verification logs: {e}")
    
    print("\n=== FIN DES TESTS ===")


if __name__ == "__main__":
    test_quittance_manual()

