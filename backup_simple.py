#!/usr/bin/env python
"""
Script de sauvegarde simple des données
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
    print("SAUVEGARDE AUTOMATIQUE DES DONNEES")
    print("=" * 50)
    
    try:
        from django.core.management import execute_from_command_line
        
        # Créer un nom de fichier avec timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"backup_automatique_{timestamp}.json"
        
        print(f"Creation de la sauvegarde: {backup_file}")
        
        # Exporter toutes les données importantes
        execute_from_command_line([
            'manage.py', 'dumpdata', 
            '--indent', '2',
            '--output', backup_file
        ])
        
        # Vérifier que la sauvegarde a été créée
        if os.path.exists(backup_file):
            size = os.path.getsize(backup_file)
            print(f"OK Sauvegarde creee: {backup_file}")
            print(f"Taille: {size / 1024 / 1024:.2f} MB")
            return True
        else:
            print("ERREUR: Fichier de sauvegarde non cree")
            return False
            
    except Exception as e:
        print(f"ERREUR lors de la sauvegarde: {e}")
        return False

if __name__ == '__main__':
    print("SYSTEME DE SECURITE DES DONNEES")
    print("=" * 50)
    
    if sauvegarder_donnees():
        print("\nSauvegarde terminee avec succes!")
        print("Vos donnees sont protegees!")
    else:
        print("\nEchec de la sauvegarde!")
        sys.exit(1)
