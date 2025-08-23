#!/usr/bin/env python
"""
Correction des utilisateurs sans groupe de travail
- Attribution d'un groupe par défaut aux utilisateurs orphelins
- Résolution du problème de redirection vers la page de connexion
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from utilisateurs.models import Utilisateur, GroupeTravail
from django.contrib.auth.models import User

def corriger_utilisateurs_sans_groupe():
    """Corrige les utilisateurs sans groupe de travail"""
    
    print("🔧 CORRECTION DES UTILISATEURS SANS GROUPE DE TRAVAIL")
    print("=" * 60)
    
    # Étape 1: Identifier les utilisateurs sans groupe
    print("\n📋 Étape 1: Identification des utilisateurs sans groupe")
    print("-" * 50)
    
    utilisateurs_sans_groupe = Utilisateur.objects.filter(groupe_travail__isnull=True)
    print(f"⚠️ {utilisateurs_sans_groupe.count()} utilisateurs sans groupe de travail")
    
    if utilisateurs_sans_groupe.count() == 0:
        print("✅ Tous les utilisateurs ont un groupe de travail")
        return True
    
    # Afficher les utilisateurs sans groupe
    for user in utilisateurs_sans_groupe:
        print(f"   - {user.username} ({user.get_full_name()}) - Actif: {user.actif}")
    
    # Étape 2: Identifier les groupes disponibles
    print("\n🏢 Étape 2: Groupes de travail disponibles")
    print("-" * 50)
    
    groupes = GroupeTravail.objects.filter(actif=True)
    print(f"✅ {groupes.count()} groupes de travail actifs")
    
    for groupe in groupes:
        print(f"   - {groupe.nom} (Actif: {groupe.actif})")
    
    if groupes.count() == 0:
        print("❌ Aucun groupe de travail actif trouvé")
        return False
    
    # Étape 3: Déterminer le groupe par défaut
    print("\n🎯 Étape 3: Détermination du groupe par défaut")
    print("-" * 50)
    
    # Priorité: ADMINISTRATION > CAISSE > GESTION > LOCATION
    groupes_priorite = ['ADMINISTRATION', 'CAISSE', 'GESTION', 'LOCATION']
    groupe_defaut = None
    
    for nom_groupe in groupes_priorite:
        try:
            groupe = GroupeTravail.objects.get(nom=nom_groupe, actif=True)
            groupe_defaut = groupe
            print(f"✅ Groupe par défaut sélectionné: {groupe.nom}")
            break
        except GroupeTravail.DoesNotExist:
            continue
    
    if not groupe_defaut:
        # Prendre le premier groupe actif disponible
        groupe_defaut = groupes.first()
        print(f"✅ Groupe par défaut sélectionné (fallback): {groupe_defaut.nom}")
    
    # Étape 4: Corriger les utilisateurs sans groupe
    print("\n🔧 Étape 4: Correction des utilisateurs sans groupe")
    print("-" * 50)
    
    utilisateurs_corriges = 0
    utilisateurs_erreur = 0
    
    for user in utilisateurs_sans_groupe:
        try:
            # Règles de correction basées sur le nom d'utilisateur
            if user.username.lower() in ['admin', 'admin_demo', 'admin_test']:
                # Utilisateurs admin -> groupe ADMINISTRATION
                try:
                    groupe_admin = GroupeTravail.objects.get(nom='ADMINISTRATION', actif=True)
                    user.groupe_travail = groupe_admin
                    print(f"   ✅ {user.username} -> ADMINISTRATION (admin)")
                except GroupeTravail.DoesNotExist:
                    user.groupe_travail = groupe_defaut
                    print(f"   ✅ {user.username} -> {groupe_defaut.nom} (fallback)")
            
            elif user.username.lower() in ['agent', 'assistant']:
                # Utilisateurs agent/assistant -> groupe GESTION
                try:
                    groupe_gestion = GroupeTravail.objects.get(nom='GESTION', actif=True)
                    user.groupe_travail = groupe_gestion
                    print(f"   ✅ {user.username} -> GESTION (agent/assistant)")
                except GroupeTravail.DoesNotExist:
                    user.groupe_travail = groupe_defaut
                    print(f"   ✅ {user.username} -> {groupe_defaut.nom} (fallback)")
            
            else:
                # Autres utilisateurs -> groupe par défaut
                user.groupe_travail = groupe_defaut
                print(f"   ✅ {user.username} -> {groupe_defaut.nom} (défaut)")
            
            user.save()
            utilisateurs_corriges += 1
            
        except Exception as e:
            print(f"   ❌ Erreur pour {user.username}: {e}")
            utilisateurs_erreur += 1
    
    # Étape 5: Vérification finale
    print("\n✅ Étape 5: Vérification finale")
    print("-" * 50)
    
    utilisateurs_sans_groupe_apres = Utilisateur.objects.filter(groupe_travail__isnull=True)
    print(f"✅ {utilisateurs_corriges} utilisateurs corrigés")
    
    if utilisateurs_erreur > 0:
        print(f"⚠️ {utilisateurs_erreur} erreurs lors de la correction")
    
    if utilisateurs_sans_groupe_apres.count() == 0:
        print("🎉 Tous les utilisateurs ont maintenant un groupe de travail !")
    else:
        print(f"⚠️ {utilisateurs_sans_groupe_apres.count()} utilisateurs restent sans groupe")
        for user in utilisateurs_sans_groupe_apres:
            print(f"   - {user.username} ({user.get_full_name()})")
    
    # Étape 6: Test de la correction
    print("\n🧪 Étape 6: Test de la correction")
    print("-" * 50)
    
    try:
        from django.test import Client
        from django.urls import reverse
        
        client = Client()
        
        # Tester l'accès à une page protégée (doit rediriger vers la connexion)
        response = client.get('/paiements/retraits/')
        
        if response.status_code == 302:  # Redirection
            print(f"✅ Redirection fonctionnelle: {response.status_code}")
            print(f"   Vers: {response.url}")
            
            if 'utilisateurs' in response.url:
                print("✅ Redirection vers la page de connexion des groupes")
            else:
                print(f"⚠️ Redirection vers: {response.url}")
        else:
            print(f"⚠️ Pas de redirection: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
    
    print("\n✅ CORRECTION TERMINÉE !")
    print("🎯 Les utilisateurs ont maintenant des groupes de travail")
    print("🔒 Les redirections devraient fonctionner correctement")
    
    return True

if __name__ == "__main__":
    corriger_utilisateurs_sans_groupe()
