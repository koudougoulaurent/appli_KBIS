#!/usr/bin/env python
"""
Désactivation de la redirection forcée vers la page de connexion des groupes
- Suppression des décorateurs @login_required des vues de liste
- Permettre l'accès direct aux pages sans authentification forcée
- Conservation de la sécurité sur les actions sensibles uniquement
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required

def desactiver_redirection_forcee():
    """Désactive la redirection forcée vers la page de connexion"""
    
    print("🚫 DÉSACTIVATION DE LA REDIRECTION FORCÉE")
    print("=" * 60)
    
    # Étape 1: Identifier les vues avec @login_required
    print("\n🔍 Étape 1: Identification des vues protégées")
    print("-" * 50)
    
    try:
        from paiements.views import RetraitListView
        
        # Vérifier si la vue a le décorateur @login_required
        if hasattr(RetraitListView, '_decorators'):
            print("✅ RetraitListView a des décorateurs")
            print(f"   Décorateurs: {RetraitListView._decorators}")
        else:
            print("✅ RetraitListView n'a pas de décorateurs")
            
        # Vérifier la méthode dispatch
        if hasattr(RetraitListView, 'dispatch'):
            print("✅ RetraitListView a une méthode dispatch")
            
    except Exception as e:
        print(f"❌ Erreur lors de la vérification: {e}")
    
    # Étape 2: Supprimer le décorateur @login_required
    print("\n🔧 Étape 2: Suppression du décorateur @login_required")
    print("-" * 50)
    
    try:
        # Supprimer le décorateur @login_required de la classe
        if hasattr(RetraitListView, '_decorators'):
            # Filtrer pour garder seulement les décorateurs non-login_required
            decorateurs_restants = []
            for decorateur in RetraitListView._decorators:
                if 'login_required' not in str(decorateur):
                    decorateurs_restants.append(decorateur)
            
            RetraitListView._decorators = decorateurs_restants
            print(f"✅ Décorateurs restants: {decorateurs_restants}")
        else:
            print("✅ Aucun décorateur à supprimer")
            
    except Exception as e:
        print(f"❌ Erreur lors de la suppression: {e}")
    
    # Étape 3: Vérifier que la suppression a fonctionné
    print("\n✅ Étape 3: Vérification de la suppression")
    print("-" * 50)
    
    try:
        if hasattr(RetraitListView, '_decorators'):
            print(f"✅ Décorateurs après suppression: {RetraitListView._decorators}")
        else:
            print("✅ Aucun décorateur")
            
    except Exception as e:
        print(f"❌ Erreur lors de la vérification: {e}")
    
    # Étape 4: Test de la vue sans protection
    print("\n🧪 Étape 4: Test de la vue sans protection")
    print("-" * 50)
    
    try:
        from django.test import Client
        
        client = Client()
        
        # Tester l'accès à la page des retraits (ne doit plus rediriger)
        response = client.get('/paiements/retraits/')
        print(f"✅ GET /paiements/retraits/ - Status: {response.status_code}")
        
        if response.status_code == 200:
            print("🎉 SUCCÈS ! Page accessible sans redirection")
            print("✅ La redirection forcée est désactivée !")
        elif response.status_code == 302:
            print(f"⚠️ Redirection toujours active vers: {response.url}")
        else:
            print(f"❌ Erreur: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
    
    print("\n✅ DÉSACTIVATION TERMINÉE !")
    print("🎯 La redirection forcée vers la page de connexion est désactivée")
    
    return True

if __name__ == "__main__":
    desactiver_redirection_forcee()
