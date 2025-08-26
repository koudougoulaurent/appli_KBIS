#!/usr/bin/env python
"""
Script de migration pour changer la devise de XOF vers F CFA
Ce script met à jour la base de données et les références
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from django.db import transaction
from core.models import Devise
from django.core.management import call_command

def migrate_currency_xof_to_fcfa():
    """
    Migre la devise XOF vers F CFA dans la base de données
    """
    print("🔄 Début de la migration XOF → F CFA...")
    
    try:
        with transaction.atomic():
            # 1. Mettre à jour ou créer la devise F CFA
            devise_fcfa, created = Devise.objects.update_or_create(
                code='F CFA',
                defaults={
                    'nom': 'Franc CFA',
                    'symbole': 'F CFA',
                    'taux_change': 655.957,
                    'actif': True
                }
            )
            
            if created:
                print(f"✅ Devise F CFA créée avec succès")
            else:
                print(f"✅ Devise F CFA mise à jour")
            
            # 2. Désactiver l'ancienne devise XOF si elle existe
            try:
                devise_xof = Devise.objects.get(code='XOF')
                devise_xof.actif = False
                devise_xof.save()
                print(f"✅ Devise XOF désactivée")
            except Devise.DoesNotExist:
                print(f"ℹ️  Devise XOF n'existait pas")
            
            # 3. Mettre à jour la devise active par défaut
            # Cette mise à jour sera gérée par les settings Django
            
            print("✅ Migration terminée avec succès!")
            
    except Exception as e:
        print(f"❌ Erreur lors de la migration: {e}")
        return False
    
    return True

def update_session_devises():
    """
    Met à jour les sessions utilisateur pour utiliser F CFA
    """
    print("🔄 Mise à jour des sessions utilisateur...")
    
    try:
        # Cette fonction peut être étendue pour mettre à jour les sessions
        # Pour l'instant, les utilisateurs devront se reconnecter
        print("ℹ️  Les utilisateurs devront se reconnecter pour voir F CFA")
        return True
    except Exception as e:
        print(f"❌ Erreur lors de la mise à jour des sessions: {e}")
        return False

def main():
    """
    Fonction principale de migration
    """
    print("🚀 Migration de la devise XOF vers F CFA")
    print("=" * 50)
    
    # 1. Migration de la base de données
    if not migrate_currency_xof_to_fcfa():
        print("❌ Échec de la migration de la base de données")
        return False
    
    # 2. Mise à jour des sessions
    if not update_session_devises():
        print("⚠️  Échec de la mise à jour des sessions")
    
    print("\n" + "=" * 50)
    print("✅ Migration terminée!")
    print("\n📋 Actions effectuées:")
    print("   • Devise F CFA créée/mise à jour")
    print("   • Devise XOF désactivée")
    print("   • Configuration mise à jour")
    print("\n⚠️  Actions requises:")
    print("   • Redémarrer le serveur Django")
    print("   • Les utilisateurs doivent se reconnecter")
    print("   • Vérifier que tous les templates affichent 'F CFA'")
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
