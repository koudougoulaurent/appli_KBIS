#!/usr/bin/env python3
"""
Script pour corriger les colonnes manquantes dans core_configurationentreprise
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from django.db import connection

def fix_configuration_entreprise_columns():
    """Corriger les colonnes manquantes dans core_configurationentreprise"""
    
    cursor = connection.cursor()
    
    print("🔍 Vérification de la structure de la table core_configurationentreprise...")
    
    # Vérifier la structure actuelle
    cursor.execute('PRAGMA table_info(core_configurationentreprise)')
    columns = cursor.fetchall()
    print(f"Colonnes actuelles ({len(columns)}):")
    for col in columns:
        print(f"  - {col[1]} ({col[2]})")
    
    # Colonnes à ajouter
    columns_to_add = [
        ('adresse_ligne1', 'VARCHAR(255)'),
        ('adresse_ligne2', 'VARCHAR(255)'),
        ('ville', 'VARCHAR(100)'),
        ('code_postal', 'VARCHAR(20)'),
        ('pays', 'VARCHAR(100)'),
        ('telephone', 'VARCHAR(20)'),
        ('email', 'VARCHAR(255)'),
        ('site_web', 'VARCHAR(255)'),
        ('logo', 'VARCHAR(255)'),
        ('description', 'TEXT'),
        ('slogan', 'VARCHAR(255)'),
        ('capital_social', 'DECIMAL(15,2)'),
        ('numero_rc', 'VARCHAR(50)'),
        ('numero_cc', 'VARCHAR(50)'),
        ('numero_nif', 'VARCHAR(50)'),
        ('numero_cnss', 'VARCHAR(50)'),
        ('numero_impot', 'VARCHAR(50)'),
        ('banque_principale', 'VARCHAR(255)'),
        ('numero_compte', 'VARCHAR(50)'),
        ('cle_rib', 'VARCHAR(10)'),
        ('devise', 'VARCHAR(10)'),
        ('taux_tva', 'DECIMAL(5,2)'),
        ('actif', 'BOOLEAN'),
        ('created_at', 'DATETIME'),
        ('updated_at', 'DATETIME')
    ]
    
    print(f"\n🔧 Ajout de {len(columns_to_add)} colonnes...")
    
    added_count = 0
    for col_name, col_type in columns_to_add:
        try:
            cursor.execute(f'ALTER TABLE core_configurationentreprise ADD COLUMN {col_name} {col_type}')
            print(f"✅ Colonne {col_name} ajoutée")
            added_count += 1
        except Exception as e:
            if "duplicate column name" in str(e).lower():
                print(f"⚠️  Colonne {col_name} existe déjà")
            else:
                print(f"❌ Erreur pour {col_name}: {e}")
    
    print(f"\n📊 Résultat: {added_count} colonnes ajoutées")
    
    # Vérifier la nouvelle structure
    cursor.execute('PRAGMA table_info(core_configurationentreprise)')
    columns = cursor.fetchall()
    print(f"\nNouvelle structure ({len(columns)} colonnes):")
    for col in columns:
        print(f"  - {col[1]} ({col[2]})")
    
    # Créer un enregistrement de configuration par défaut
    print("\n🏢 Création d'un enregistrement de configuration par défaut...")
    
    try:
        cursor.execute("""
            INSERT OR IGNORE INTO core_configurationentreprise 
            (nom_entreprise, adresse_ligne1, ville, pays, telephone, email, devise, actif, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
        """, (
            'KBIS Immobilier',
            'Avenue de la Paix',
            'Ouagadougou',
            'Burkina Faso',
            '+226 25 30 60 70',
            'contact@kbis.bf',
            'F CFA',
            1
        ))
        print("✅ Configuration d'entreprise par défaut créée")
    except Exception as e:
        print(f"⚠️  Configuration d'entreprise: {e}")
    
    print("\n🎯 Correction terminée ! La génération PDF devrait maintenant fonctionner.")

if __name__ == "__main__":
    fix_configuration_entreprise_columns()
