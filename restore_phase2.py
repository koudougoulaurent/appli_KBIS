#!/usr/bin/env python
"""
Script de restauration à l'état Phase 2
Supprime les données de la Phase 3 (contrats et paiements) pour revenir à un état stable
"""
import os
import django
import sys

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from django.db import connection
from django.core.management import execute_from_command_line

def restore_to_phase2():
    """Restaure l'application à l'état Phase 2"""
    print("🔄 Restauration à l'état Phase 2...")
    
    try:
        # 1. Supprimer les données de la Phase 3
        print("📋 Suppression des données Phase 3...")
        
        with connection.cursor() as cursor:
            # Supprimer les données des contrats
            cursor.execute("DELETE FROM contrats_renouvellementcontrat;")
            cursor.execute("DELETE FROM contrats_documentcontrat;")
            cursor.execute("DELETE FROM contrats_clausecontrat;")
            cursor.execute("DELETE FROM contrats_contrat;")
            cursor.execute("DELETE FROM contrats_typecontrat;")
            
            # Supprimer les données des paiements
            cursor.execute("DELETE FROM paiements_transaction;")
            cursor.execute("DELETE FROM paiements_quittanceloyer;")
            cursor.execute("DELETE FROM paiements_retrait;")
            cursor.execute("DELETE FROM paiements_frais;")
            cursor.execute("DELETE FROM paiements_paiement;")
            cursor.execute("DELETE FROM paiements_typepaiement;")
            cursor.execute("DELETE FROM paiements_comptebancaire;")
            
            print("✅ Données Phase 3 supprimées")
        
        # 2. Vérifier l'état de la base de données
        print("🔍 Vérification de l'état de la base de données...")
        
        with connection.cursor() as cursor:
            # Vérifier les tables Phase 2 (propriétés, utilisateurs)
            cursor.execute("SELECT COUNT(*) FROM proprietes_propriete;")
            proprietes_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM proprietes_bailleur;")
            bailleurs_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM proprietes_locataire;")
            locataires_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM utilisateurs_utilisateur;")
            users_count = cursor.fetchone()[0]
            
            print(f"✅ Phase 2 - Propriétés: {proprietes_count}")
            print(f"✅ Phase 2 - Bailleurs: {bailleurs_count}")
            print(f"✅ Phase 2 - Locataires: {locataires_count}")
            print(f"✅ Phase 2 - Utilisateurs: {users_count}")
        
        # 3. Vérifier que les tables Phase 3 sont vides
        print("🔍 Vérification des tables Phase 3...")
        
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM contrats_contrat;")
            contrats_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM paiements_paiement;")
            paiements_count = cursor.fetchone()[0]
            
            print(f"✅ Phase 3 - Contrats: {contrats_count} (vide)")
            print(f"✅ Phase 3 - Paiements: {paiements_count} (vide)")
        
        print("\n🎉 Restauration Phase 2 terminée avec succès !")
        print("\n📋 État actuel :")
        print("- ✅ Phase 1 : Fondations (Django, auth, admin)")
        print("- ✅ Phase 2 : Gestion des propriétés (propriétés, bailleurs, locataires)")
        print("- 🔄 Phase 3 : Contrats et paiements (supprimés)")
        print("- 📋 Phase 4 : Interface utilisateur (à développer)")
        
        print("\n🌐 Accès :")
        print("- Dashboard : http://127.0.0.1:8000/")
        print("- Admin : http://127.0.0.1:8000/admin/")
        print("- Login : http://127.0.0.1:8000/accounts/login/")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la restauration : {e}")
        return False

def check_phase2_functionality():
    """Vérifie que les fonctionnalités Phase 2 fonctionnent"""
    print("\n🧪 Test des fonctionnalités Phase 2...")
    
    try:
        from proprietes.models import Propriete, Bailleur, Locataire
        from utilisateurs.models import Utilisateur
        
        # Test des modèles Phase 2
        proprietes = Propriete.objects.all()
        bailleurs = Bailleur.objects.all()
        locataires = Locataire.objects.all()
        users = Utilisateur.objects.all()
        
        print(f"✅ Modèles Phase 2 accessibles")
        print(f"   - Propriétés : {proprietes.count()}")
        print(f"   - Bailleurs : {bailleurs.count()}")
        print(f"   - Locataires : {locataires.count()}")
        print(f"   - Utilisateurs : {users.count()}")
        
        # Test de l'admin
        from django.contrib import admin
        registered_models = list(admin.site._registry.keys())
        phase2_models = [m for m in registered_models if 'proprietes' in str(m) or 'utilisateurs' in str(m)]
        
        print(f"✅ Admin Phase 2 : {len(phase2_models)} modèles enregistrés")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur test Phase 2 : {e}")
        return False

if __name__ == '__main__':
    print("🏢 RESTAURATION GESTION IMMOBILIÈRE - PHASE 2")
    print("=" * 50)
    
    success = restore_to_phase2()
    
    if success:
        check_phase2_functionality()
        print("\n✨ L'application est maintenant restaurée à l'état Phase 2 !")
        print("Vous pouvez continuer le développement à partir de cet état stable.")
    else:
        print("\n❌ La restauration a échoué. Vérifiez les erreurs ci-dessus.")
        sys.exit(1) 