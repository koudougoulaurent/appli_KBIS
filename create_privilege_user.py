#!/usr/bin/env python
"""
Script pour créer l'utilisateur privilege1 avec le mot de passe test123
"""

import sqlite3
import hashlib
import os
from datetime import datetime

def create_privilege_user():
    """Créer l'utilisateur privilege1 avec le mot de passe test123"""
    
    # Chemin vers la base de données
    db_path = 'db.sqlite3'
    
    if not os.path.exists(db_path):
        print("❌ Base de données non trouvée. Veuillez d'abord exécuter les migrations Django.")
        return False
    
    print("🚀 Création de l'utilisateur privilege1")
    print("=" * 50)
    
    # Connexion à la base de données
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Vérifier si la table utilisateurs existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='utilisateurs_utilisateur'")
        if not cursor.fetchone():
            print("❌ Table utilisateurs non trouvée. Veuillez d'abord exécuter les migrations Django.")
            return False
        
        # Récupérer l'ID du groupe PRIVILEGE
        cursor.execute("SELECT id FROM utilisateurs_groupetravail WHERE nom = 'PRIVILEGE'")
        groupe_result = cursor.fetchone()
        
        if not groupe_result:
            print("❌ Groupe PRIVILEGE non trouvé. Création du groupe...")
            cursor.execute("""
                INSERT INTO utilisateurs_groupetravail 
                (nom, description, permissions, actif, date_creation, date_modification)
                VALUES (?, ?, ?, 1, ?, ?)
            """, ('PRIVILEGE', 'Groupe avec tous les privilèges', 
                  '{"modules": ["utilisateurs", "proprietes", "contrats", "paiements", "retraits", "recapitulatifs"], "actions": ["view", "add", "change", "delete"]}',
                  datetime.now(), datetime.now()))
            groupe_id = cursor.lastrowid
            print("   ✅ Groupe PRIVILEGE créé")
        else:
            groupe_id = groupe_result[0]
            print("   ✅ Groupe PRIVILEGE trouvé")
        
        # Vérifier si l'utilisateur privilege1 existe déjà
        cursor.execute("SELECT id FROM utilisateurs_utilisateur WHERE username = 'privilege1'")
        if cursor.fetchone():
            print("   ℹ️  Utilisateur privilege1 existe déjà. Mise à jour du mot de passe...")
            
            # Mettre à jour le mot de passe
            password_hash = f"pbkdf2_sha256$600000${hashlib.sha256('test123'.encode()).hexdigest()[:12]}${hashlib.sha256('test123'.encode()).hexdigest()}"
            
            cursor.execute("""
                UPDATE utilisateurs_utilisateur 
                SET password = ?, groupe_travail_id = ?, date_modification = ?
                WHERE username = 'privilege1'
            """, (password_hash, groupe_id, datetime.now()))
            
            print("   ✅ Mot de passe de privilege1 mis à jour")
        else:
            print("   🔧 Création de l'utilisateur privilege1...")
            
            # Hasher le mot de passe
            password_hash = f"pbkdf2_sha256$600000${hashlib.sha256('test123'.encode()).hexdigest()[:12]}${hashlib.sha256('test123'.encode()).hexdigest()}"
            
            # Insérer l'utilisateur
            cursor.execute("""
                INSERT INTO utilisateurs_utilisateur 
                (username, email, password, first_name, last_name, is_staff, is_superuser, 
                 groupe_travail_id, poste, departement, telephone, adresse, actif, 
                 date_creation, date_modification, is_deleted, is_active, date_joined)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?, 0, 1, ?)
            """, ('privilege1', 'privilege1@gestimmob.com', password_hash, 'Kadiatou', 'Coulibaly', 
                  0, 0, groupe_id, 'Directeur', 'Direction', '+225 07 89 01 23 45', 
                  'Zone 4, Abidjan', datetime.now(), datetime.now(), datetime.now()))
            
            print("   ✅ Utilisateur privilege1 créé")
        
        # Valider les changements
        conn.commit()
        
        # Vérifier la création
        cursor.execute("""
            SELECT u.username, u.first_name, u.last_name, u.email, g.nom
            FROM utilisateurs_utilisateur u
            LEFT JOIN utilisateurs_groupetravail g ON u.groupe_travail_id = g.id
            WHERE u.username = 'privilege1'
        """)
        
        result = cursor.fetchone()
        if result:
            username, first_name, last_name, email, group_name = result
            print(f"\n✅ Utilisateur créé avec succès !")
            print(f"   • Nom d'utilisateur: {username}")
            print(f"   • Nom complet: {first_name} {last_name}")
            print(f"   • Email: {email}")
            print(f"   • Groupe: {group_name}")
            print(f"   • Mot de passe: test123")
            
            print(f"\n🔑 Informations de connexion :")
            print(f"   • Utilisateur: privilege1")
            print(f"   • Mot de passe: test123")
            print(f"   • Groupe: PRIVILEGE (tous les privilèges)")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la création : {e}")
        conn.rollback()
        return False
    
    finally:
        conn.close()

if __name__ == '__main__':
    create_privilege_user()
