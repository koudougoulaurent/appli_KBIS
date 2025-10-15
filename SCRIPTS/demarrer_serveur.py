#!/usr/bin/env python
"""
Script pour démarrer le serveur Django
"""
import os
import sys
import django
from django.core.management import execute_from_command_line

if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
    django.setup()
    
    print("🚀 Démarrage du serveur Django...")
    print("📱 Accédez à l'application sur : http://127.0.0.1:8000/")
    print("🔐 Connectez-vous avec vos identifiants")
    print("📋 Nouvelles fonctionnalités disponibles :")
    print("   - Menu 'Charges' : Gestion des charges déductibles")
    print("   - Menu 'Récapitulatifs' : Génération de PDF avec charges intégrées")
    print("   - Menu 'Paiements' : Toutes les fonctionnalités existantes")
    print("\n" + "="*60)
    
    execute_from_command_line(['manage.py', 'runserver'])