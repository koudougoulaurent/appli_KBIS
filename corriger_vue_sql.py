#!/usr/bin/env python
"""
Script pour corriger la vue SQL problématique v_stats_proprietes
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from django.db import connection

def corriger_vue_sql():
    """Corrige la vue SQL problématique."""
    try:
        with connection.cursor() as cursor:
            # Supprimer la vue problématique si elle existe
            cursor.execute("DROP VIEW IF EXISTS v_stats_proprietes")
            print("✅ Vue v_stats_proprietes supprimée avec succès")
            
            # Vérifier s'il y a d'autres vues problématiques
            cursor.execute("SELECT name FROM sqlite_master WHERE type='view'")
            vues = cursor.fetchall()
            print(f"📋 Vues restantes dans la base : {[vue[0] for vue in vues]}")
            
            # Vérifier la structure de la table proprietes
            cursor.execute("PRAGMA table_info(proprietes_propriete)")
            colonnes = cursor.fetchall()
            print(f"🏠 Colonnes de la table proprietes : {[col[1] for col in colonnes]}")
            
    except Exception as e:
        print(f"❌ Erreur lors de la correction : {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🔧 Correction de la vue SQL problématique...")
    if corriger_vue_sql():
        print("✅ Correction terminée avec succès")
    else:
        print("❌ Échec de la correction")
        sys.exit(1)
