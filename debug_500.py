#!/usr/bin/env python
"""
Script de diagnostic pour identifier la cause de l'erreur 500
"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

def debug_500():
    print("🔍 DIAGNOSTIC DE L'ERREUR 500...")
    
    try:
        # 1. Test des imports de base
        print("1. Test des imports de base...")
        from django.shortcuts import render, redirect
        from django.contrib.auth import login, authenticate
        print("✅ Imports Django OK")
        
        # 2. Test des modèles utilisateurs
        print("2. Test des modèles utilisateurs...")
        from utilisateurs.models import Utilisateur, GroupeTravail
        print("✅ Modèles utilisateurs OK")
        
        # 3. Test des vues
        print("3. Test des vues...")
        from utilisateurs.views import connexion_groupes, login_groupe
        print("✅ Vues utilisateurs OK")
        
        # 4. Test des templates
        print("4. Test des templates...")
        from django.template.loader import get_template
        template = get_template('utilisateurs/login_groupe.html')
        print("✅ Template login_groupe OK")
        
        # 5. Test de la vue login_groupe avec des données simulées
        print("5. Test de la vue login_groupe...")
        from django.test import RequestFactory
        from django.contrib.auth.models import AnonymousUser
        
        factory = RequestFactory()
        request = factory.get('/utilisateurs/login/ADMINISTRATION/')
        request.user = AnonymousUser()
        
        # Simuler un groupe ADMINISTRATION
        try:
            groupe = GroupeTravail.objects.get(nom='ADMINISTRATION')
            print(f"✅ Groupe ADMINISTRATION trouvé: {groupe}")
        except GroupeTravail.DoesNotExist:
            print("❌ Groupe ADMINISTRATION non trouvé")
            return
        
        # Test de la vue
        try:
            response = login_groupe(request, 'ADMINISTRATION')
            print(f"✅ Vue login_groupe OK - Status: {response.status_code}")
        except Exception as e:
            print(f"❌ Erreur dans login_groupe: {e}")
            import traceback
            traceback.print_exc()
        
        # 6. Test des imports problématiques
        print("6. Test des imports problématiques...")
        try:
            from core.intelligent_views import IntelligentListView
            print("✅ IntelligentListView OK")
        except Exception as e:
            print(f"❌ Erreur IntelligentListView: {e}")
        
        try:
            from proprietes.models import Bailleur, Locataire, Propriete
            print("✅ Modèles propriétés OK")
        except Exception as e:
            print(f"❌ Erreur modèles propriétés: {e}")
        
        try:
            from core.models import AuditLog, TemplateRecu, Devise
            print("✅ Modèles core OK")
        except Exception as e:
            print(f"❌ Erreur modèles core: {e}")
        
        print("🎉 DIAGNOSTIC TERMINÉ")
        
    except Exception as e:
        print(f"❌ ERREUR CRITIQUE: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_500()
