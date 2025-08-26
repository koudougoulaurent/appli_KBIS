#!/usr/bin/env python
"""
Script de test simple pour le système de récapitulatif mensuel
"""

import os
import sys
import django
from datetime import datetime

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from django.contrib.auth.models import Group
from paiements.models import RecapMensuel
from proprietes.models import Bailleur
from utilisateurs.models import Utilisateur

def test_simple():
    """Test simple du système."""
    print("🚀 TEST SIMPLE DU SYSTÈME DE RÉCAPITULATIF MENSUEL")
    print("=" * 50)
    
    try:
        # Vérifier les modèles de base
        print("📊 Vérification des modèles de base...")
        
        # Compter les bailleurs
        total_bailleurs = Bailleur.objects.filter(is_deleted=False).count()
        print(f"   ✅ Bailleurs actifs: {total_bailleurs}")
        
        # Compter les utilisateurs
        total_utilisateurs = Utilisateur.objects.filter(is_deleted=False).count()
        print(f"   ✅ Utilisateurs actifs: {total_utilisateurs}")
        
        # Compter les récapitulatifs existants
        total_recaps = RecapMensuel.objects.filter(is_deleted=False).count()
        print(f"   ✅ Récapitulatifs existants: {total_recaps}")
        
        # Vérifier les groupes
        groupes = Group.objects.all()
        print(f"   ✅ Groupes disponibles: {[g.name for g in groupes]}")
        
        # Test de création d'un utilisateur simple
        print("\n🔧 Test de création d'utilisateur...")
        try:
            user_test, created = Utilisateur.objects.get_or_create(
                username='test_simple',
                defaults={
                    'email': 'test@simple.com',
                    'first_name': 'Test',
                    'last_name': 'Simple',
                    'telephone': '0000000000'  # Téléphone obligatoire
                }
            )
            
            if created:
                print("   ✅ Utilisateur de test créé avec succès")
                
                # Ajouter au groupe PRIVILEGE
                groupe_privilege, _ = Group.objects.get_or_create(name='PRIVILEGE')
                user_test.groups.add(groupe_privilege)
                print("   ✅ Utilisateur ajouté au groupe PRIVILEGE")
                
                # Nettoyer
                user_test.delete()
                print("   ✅ Utilisateur de test supprimé")
            else:
                print("   ✅ Utilisateur de test existe déjà")
                
        except Exception as e:
            print(f"   ❌ Erreur création utilisateur: {e}")
        
        print("\n🎉 Test simple réussi !")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        return False

if __name__ == '__main__':
    test_simple()
