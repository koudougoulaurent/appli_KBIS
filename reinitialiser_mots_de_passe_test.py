#!/usr/bin/env python
"""
Script pour réinitialiser les mots de passe des utilisateurs de test
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from utilisateurs.models import Utilisateur

def reinitialiser_mots_de_passe_test():
    """Réinitialise les mots de passe des utilisateurs de test"""
    
    print("🔐 RÉINITIALISATION DES MOTS DE PASSE DE TEST")
    print("=" * 60)
    
    # Liste des utilisateurs de test par groupe
    utilisateurs_test = {
        'CAISSE': ['caisse1', 'caisse2'],
        'ADMINISTRATION': ['admin1', 'admin2'],
        'CONTROLES': ['controle1', 'controle2'],
        'PRIVILEGE': ['privilege1', 'privilege2'],
    }
    
    mot_de_passe_test = 'test123'
    
    for groupe_nom, usernames in utilisateurs_test.items():
        print(f"\n📋 Groupe: {groupe_nom}")
        print("-" * 30)
        
        for username in usernames:
            try:
                utilisateur = Utilisateur.objects.get(username=username)
                utilisateur.set_password(mot_de_passe_test)
                utilisateur.save()
                print(f"✅ {username}: Mot de passe réinitialisé")
            except Utilisateur.DoesNotExist:
                print(f"❌ {username}: Utilisateur non trouvé")
            except Exception as e:
                print(f"❌ {username}: Erreur - {e}")
    
    print(f"\n✅ Mots de passe réinitialisés à '{mot_de_passe_test}'")
    print("\n🔑 Informations de connexion:")
    print("• CAISSE: caisse1 / test123")
    print("• ADMINISTRATION: admin1 / test123")
    print("• CONTROLES: controle1 / test123")
    print("• PRIVILEGE: privilege1 / test123")

if __name__ == '__main__':
    reinitialiser_mots_de_passe_test() 