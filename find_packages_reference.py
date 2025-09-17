#!/usr/bin/env python
"""
Script pour trouver la référence cachée à 'packages'
"""

import os
import sys
import ast
import re

def find_packages_in_file(file_path):
    """Cherche les références à 'packages' dans un fichier Python"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Chercher les imports
        if 'packages' in content:
            lines = content.split('\n')
            for i, line in enumerate(lines, 1):
                if 'packages' in line:
                    print(f"   Ligne {i}: {line.strip()}")
                    
    except Exception as e:
        print(f"❌ Erreur lecture {file_path}: {e}")

def find_packages_in_directory(directory):
    """Cherche les références à 'packages' dans tous les fichiers Python d'un répertoire"""
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                print(f"\n🔍 Fichier: {file_path}")
                find_packages_in_file(file_path)

# Chercher dans tous les répertoires
directories = ['core', 'utilisateurs', 'proprietes', 'contrats', 'paiements', 'notifications', 'gestion_immobiliere']

for directory in directories:
    if os.path.exists(directory):
        print(f"\n📁 Répertoire: {directory}")
        find_packages_in_directory(directory)
