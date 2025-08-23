#!/usr/bin/env python
"""
Vérification du mot de passe de l'utilisateur de test
- Test de l'authentification avec différents mots de passe
- Vérification de la configuration d'authentification
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from django.contrib.auth import authenticate
from utilisateurs.models import Utilisateur

def verifier_mot_de_passe():
    """Vérifie le mot de passe de l'utilisateur de test"""
    
    print("🔐 VÉRIFICATION DU MOT DE PASSE")
    print("=" * 40)
    
    # Étape 1: Trouver l'utilisateur de test
    print("\n🔍 Étape 1: Recherche de l'utilisateur de test")
    print("-" * 40)
    
    utilisateur_test = None
    for user in Utilisateur.objects.all():
        if user.groupe_travail and user.actif:
            utilisateur_test = user
            break
    
    if not utilisateur_test:
        print("❌ Aucun utilisateur valide trouvé")
        return False
    
    print(f"✅ Utilisateur de test: {utilisateur_test.username}")
    print(f"   Groupe: {utilisateur_test.groupe_travail.nom}")
    print(f"   Actif: {utilisateur_test.actif}")
    print(f"   Date de création: {utilisateur_test.date_joined}")
    print(f"   Dernière connexion: {utilisateur_test.derniere_connexion}")
    
    # Étape 2: Tester différents mots de passe
    print("\n🔑 Étape 2: Test de différents mots de passe")
    print("-" * 40)
    
    mots_de_passe_tests = [
        'test123',
        'password',
        'admin',
        '123456',
        'admin123',
        'password123',
        'test',
        '123',
        '',
        utilisateur_test.username,  # Utiliser le nom d'utilisateur comme mot de passe
    ]
    
    for mot_de_passe in mots_de_passe_tests:
        try:
            # Tester l'authentification
            user = authenticate(username=utilisateur_test.username, password=mot_de_passe)
            
            if user is not None:
                print(f"✅ Mot de passe valide trouvé: '{mot_de_passe}'")
                print(f"   Utilisateur authentifié: {user.username}")
                print(f"   Actif: {user.actif}")
                print(f"   Groupe: {user.groupe_travail.nom if user.groupe_travail else 'Aucun'}")
                return True
            else:
                print(f"❌ Mot de passe invalide: '{mot_de_passe}'")
                
        except Exception as e:
            print(f"❌ Erreur avec le mot de passe '{mot_de_passe}': {e}")
    
    # Étape 3: Vérifier si l'utilisateur a un mot de passe défini
    print("\n🔍 Étape 3: Vérification du mot de passe de l'utilisateur")
    print("-" * 40)
    
    try:
        # Vérifier si l'utilisateur a un mot de passe défini
        if utilisateur_test.has_usable_password():
            print("✅ L'utilisateur a un mot de passe utilisable")
        else:
            print("❌ L'utilisateur n'a pas de mot de passe utilisable")
            
        # Vérifier la méthode de hachage
        print(f"✅ Méthode de hachage: {utilisateur_test.password[:20]}...")
        
    except Exception as e:
        print(f"❌ Erreur lors de la vérification: {e}")
    
    # Étape 4: Créer un nouveau mot de passe si nécessaire
    print("\n🔧 Étape 4: Création d'un nouveau mot de passe si nécessaire")
    print("-" * 40)
    
    try:
        # Vérifier si l'utilisateur peut être authentifié avec un mot de passe simple
        if not utilisateur_test.has_usable_password():
            print("⚠️ L'utilisateur n'a pas de mot de passe utilisable")
            print("   Création d'un nouveau mot de passe...")
            
            # Créer un nouveau mot de passe
            nouveau_mot_de_passe = 'admin123'
            utilisateur_test.set_password(nouveau_mot_de_passe)
            utilisateur_test.save()
            
            print(f"✅ Nouveau mot de passe créé: '{nouveau_mot_de_passe}'")
            
            # Tester l'authentification avec le nouveau mot de passe
            user = authenticate(username=utilisateur_test.username, password=nouveau_mot_de_passe)
            
            if user is not None:
                print("✅ Authentification réussie avec le nouveau mot de passe")
                return True
            else:
                print("❌ Échec de l'authentification avec le nouveau mot de passe")
        else:
            print("✅ L'utilisateur a déjà un mot de passe utilisable")
            
    except Exception as e:
        print(f"❌ Erreur lors de la création du mot de passe: {e}")
    
    print("\n✅ VÉRIFICATION TERMINÉE !")
    print("🎯 Vérifiez les résultats ci-dessus")
    
    return False

if __name__ == "__main__":
    verifier_mot_de_passe()
