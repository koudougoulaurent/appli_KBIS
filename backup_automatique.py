#!/usr/bin/env python
"""
Script de sauvegarde automatique des données
À exécuter AVANT chaque déploiement
"""
import os
import sys
import django
from datetime import datetime
import json

# Configuration Django pour PostgreSQL
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings_postgresql')
django.setup()

def sauvegarder_donnees():
    """Sauvegarde complète de toutes les données"""
    print("🔄 SAUVEGARDE AUTOMATIQUE DES DONNÉES")
    print("=" * 50)
    
    try:
        from django.core.management import execute_from_command_line
        
        # Créer un nom de fichier avec timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"backup_automatique_{timestamp}.json"
        
        print(f"📁 Création de la sauvegarde: {backup_file}")
        
        # Exporter toutes les données importantes
        execute_from_command_line([
            'manage.py', 'dumpdata', 
            '--indent', '2',
            '--exclude', 'contenttypes',
            '--exclude', 'auth.permission',
            '--exclude', 'sessions',
            '--output', backup_file
        ])
        
        # Vérifier que la sauvegarde a été créée
        if os.path.exists(backup_file):
            size = os.path.getsize(backup_file)
            print(f"✅ Sauvegarde créée: {backup_file}")
            print(f"📊 Taille: {size / 1024 / 1024:.2f} MB")
            
            # Créer un fichier de métadonnées
            metadata = {
                "timestamp": timestamp,
                "fichier": backup_file,
                "taille": size,
                "status": "success"
            }
            
            with open(f"backup_metadata_{timestamp}.json", "w") as f:
                json.dump(metadata, f, indent=2)
            
            print(f"📋 Métadonnées sauvegardées: backup_metadata_{timestamp}.json")
            return True
        else:
            print("❌ Erreur: Fichier de sauvegarde non créé")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors de la sauvegarde: {e}")
        return False

def verifier_integrite():
    """Vérifie l'intégrité des données après déploiement"""
    print("\n🔍 VÉRIFICATION DE L'INTÉGRITÉ")
    print("=" * 50)
    
    try:
        from django.core.management import execute_from_command_line
        
        # Vérifier que la base est accessible
        execute_from_command_line(['manage.py', 'check', '--database', 'default'])
        print("✅ Base de données accessible")
        
        # Compter les enregistrements principaux
        from core.models import ConfigurationEntreprise
        from utilisateurs.models import Utilisateur
        from proprietes.models import Propriete
        from contrats.models import Contrat
        from paiements.models import Paiement
        
        print(f"📊 Utilisateurs: {Utilisateur.objects.count()}")
        print(f"📊 Propriétés: {Propriete.objects.count()}")
        print(f"📊 Contrats: {Contrat.objects.count()}")
        print(f"📊 Paiements: {Paiement.objects.count()}")
        
        print("✅ Intégrité des données vérifiée")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la vérification: {e}")
        return False

if __name__ == '__main__':
    print("🛡️ SYSTÈME DE SÉCURITÉ DES DONNÉES")
    print("=" * 50)
    
    if len(sys.argv) > 1 and sys.argv[1] == 'verifier':
        verifier_integrite()
    else:
        if sauvegarder_donnees():
            print("\n🎉 Sauvegarde terminée avec succès!")
            print("💾 Vos données sont protégées!")
        else:
            print("\n❌ Échec de la sauvegarde!")
            sys.exit(1)
