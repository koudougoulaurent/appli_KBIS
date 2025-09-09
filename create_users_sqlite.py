#!/usr/bin/env python
"""
Script pour créer des utilisateurs de test directement via SQLite
"""

import sqlite3
import hashlib
import os
from datetime import datetime

def create_users():
    """Créer des utilisateurs de test directement dans la base SQLite"""
    
    # Chemin vers la base de données
    db_path = 'db.sqlite3'
    
    if not os.path.exists(db_path):
        print("❌ Base de données non trouvée. Veuillez d'abord exécuter les migrations Django.")
        return False
    
    print("🚀 Création des utilisateurs de test pour GESTIMMOB")
    print("=" * 60)
    
    # Connexion à la base de données
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Vérifier si la table utilisateurs existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='utilisateurs_utilisateur'")
        if not cursor.fetchone():
            print("❌ Table utilisateurs non trouvée. Veuillez d'abord exécuter les migrations Django.")
            return False
        
        # Créer les groupes de travail
        print("🔧 Création des groupes de travail...")
        
        groups_data = [
            ('CAISSE', 'Groupe pour la gestion de la caisse et des paiements', '{"modules": ["paiements", "retraits", "recapitulatifs"], "actions": ["view", "add", "change", "delete"]}'),
            ('CONTROLES', 'Groupe pour les contrôles et validations', '{"modules": ["paiements", "contrats", "proprietes"], "actions": ["view", "change"]}'),
            ('ADMINISTRATION', 'Groupe pour l\'administration générale', '{"modules": ["utilisateurs", "proprietes", "contrats", "paiements"], "actions": ["view", "add", "change"]}'),
            ('PRIVILEGE', 'Groupe avec tous les privilèges', '{"modules": ["utilisateurs", "proprietes", "contrats", "paiements", "retraits", "recapitulatifs"], "actions": ["view", "add", "change", "delete"]}')
        ]
        
        for nom, description, permissions in groups_data:
            cursor.execute("""
                INSERT OR IGNORE INTO utilisateurs_groupetravail 
                (nom, description, permissions, actif, date_creation, date_modification)
                VALUES (?, ?, ?, 1, ?, ?)
            """, (nom, description, permissions, datetime.now(), datetime.now()))
            print(f"   ✅ Groupe {nom} créé")
        
        # Récupérer les IDs des groupes
        cursor.execute("SELECT id, nom FROM utilisateurs_groupetravail")
        groups = {nom: id for id, nom in cursor.fetchall()}
        
        # Créer les utilisateurs de test
        print("\n👥 Création des utilisateurs de test...")
        
        users_data = [
            # Superutilisateur
            ('admin', 'admin@gestimmob.com', 'admin123', 'Administrateur', 'Système', 1, 1, groups['PRIVILEGE'], 'Administrateur Système', 'IT', '+225 07 12 34 56 78', 'Abidjan, Côte d\'Ivoire'),
            # Groupe CAISSE
            ('caisse1', 'caisse1@gestimmob.com', 'caisse123', 'Marie', 'Kouassi', 0, 0, groups['CAISSE'], 'Agent de Caisse', 'Finance', '+225 07 23 45 67 89', 'Cocody, Abidjan'),
            ('caisse2', 'caisse2@gestimmob.com', 'caisse123', 'Jean', 'Traoré', 0, 0, groups['CAISSE'], 'Responsable Caisse', 'Finance', '+225 07 34 56 78 90', 'Plateau, Abidjan'),
            # Groupe CONTROLES
            ('controle1', 'controle1@gestimmob.com', 'controle123', 'Fatou', 'Diabaté', 0, 0, groups['CONTROLES'], 'Contrôleur', 'Contrôle', '+225 07 45 67 89 01', 'Yopougon, Abidjan'),
            ('controle2', 'controle2@gestimmob.com', 'controle123', 'Kouassi', 'Koné', 0, 0, groups['CONTROLES'], 'Superviseur Contrôle', 'Contrôle', '+225 07 56 78 90 12', 'Marcory, Abidjan'),
            # Groupe ADMINISTRATION
            ('admin1', 'admin1@gestimmob.com', 'admin123', 'Aminata', 'Sangaré', 0, 0, groups['ADMINISTRATION'], 'Gestionnaire', 'Administration', '+225 07 67 89 01 23', 'Riviera, Abidjan'),
            ('admin2', 'admin2@gestimmob.com', 'admin123', 'Moussa', 'Ouattara', 0, 0, groups['ADMINISTRATION'], 'Chef Administration', 'Administration', '+225 07 78 90 12 34', 'Angré, Abidjan'),
            # Groupe PRIVILEGE
            ('privilege1', 'privilege1@gestimmob.com', 'privilege123', 'Kadiatou', 'Coulibaly', 0, 0, groups['PRIVILEGE'], 'Directeur', 'Direction', '+225 07 89 01 23 45', 'Zone 4, Abidjan'),
            ('privilege2', 'privilege2@gestimmob.com', 'privilege123', 'Ibrahim', 'Bamba', 0, 0, groups['PRIVILEGE'], 'Directeur Adjoint', 'Direction', '+225 07 90 12 34 56', 'Bingerville, Abidjan')
        ]
        
        for username, email, password, first_name, last_name, is_staff, is_superuser, groupe_id, poste, departement, telephone, adresse in users_data:
            # Vérifier si l'utilisateur existe déjà
            cursor.execute("SELECT id FROM utilisateurs_utilisateur WHERE username = ?", (username,))
            if cursor.fetchone():
                print(f"   ℹ️  Utilisateur {username} existe déjà")
                continue
            
            # Hasher le mot de passe (simplifié pour SQLite)
            password_hash = f"pbkdf2_sha256$600000${hashlib.sha256(password.encode()).hexdigest()[:12]}${hashlib.sha256(password.encode()).hexdigest()}"
            
            # Insérer l'utilisateur
            cursor.execute("""
                INSERT INTO utilisateurs_utilisateur 
                (username, email, password, first_name, last_name, is_staff, is_superuser, 
                 groupe_travail_id, poste, departement, telephone, adresse, actif, 
                 date_creation, date_modification, is_deleted, is_active, date_joined)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?, 0, 1, ?)
            """, (username, email, password_hash, first_name, last_name, is_staff, is_superuser,
                  groupe_id, poste, departement, telephone, adresse, datetime.now(), datetime.now(), datetime.now()))
            
            print(f"   ✅ Utilisateur {username} créé ({first_name} {last_name})")
        
        # Valider les changements
        conn.commit()
        
        # Afficher la liste des utilisateurs créés
        print("\n📋 Liste des utilisateurs de test :")
        print("=" * 80)
        
        cursor.execute("""
            SELECT u.username, u.first_name, u.last_name, u.email, u.poste, u.telephone, g.nom
            FROM utilisateurs_utilisateur u
            LEFT JOIN utilisateurs_groupetravail g ON u.groupe_travail_id = g.id
            ORDER BY g.nom, u.username
        """)
        
        current_group = None
        for username, first_name, last_name, email, poste, telephone, group_name in cursor.fetchall():
            if group_name != current_group:
                current_group = group_name
                print(f"\n🔹 Groupe {group_name}:")
            
            print(f"   • {username} - {first_name} {last_name}")
            print(f"     Email: {email}")
            print(f"     Poste: {poste}")
            print(f"     Téléphone: {telephone}")
            print()
        
        print("\n✅ Création terminée avec succès !")
        print("\n🔑 Informations de connexion :")
        print("   • Superutilisateur: admin / admin123")
        print("   • Caisse: caisse1 / caisse123")
        print("   • Contrôle: controle1 / controle123")
        print("   • Administration: admin1 / admin123")
        print("   • Privilège: privilege1 / privilege123")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la création : {e}")
        conn.rollback()
        return False
    
    finally:
        conn.close()

if __name__ == '__main__':
    create_users()
