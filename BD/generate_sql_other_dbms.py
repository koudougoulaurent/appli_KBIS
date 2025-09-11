#!/usr/bin/env python
"""
Script pour générer le code SQL pour différents SGBD
Usage: python generate_sql_other_dbms.py
"""

def generate_postgresql():
    """Génère le code SQL pour PostgreSQL"""
    
    sql_content = """-- =====================================================
-- SCHÉMA SQL COMPLET - GESTIMMOB (PostgreSQL)
-- Application de Gestion Immobilière
-- =====================================================

-- =====================================================
-- 1. MODULE CORE (Configuration & Sécurité)
-- =====================================================

-- Table: ConfigurationEntreprise
CREATE TABLE core_configurationentreprise (
    id SERIAL PRIMARY KEY,
    nom_entreprise VARCHAR(200) NOT NULL DEFAULT 'GESTIMMOB',
    slogan VARCHAR(200) DEFAULT '',
    adresse VARCHAR(200) NOT NULL DEFAULT '123 Rue de la Paix',
    code_postal VARCHAR(10) NOT NULL DEFAULT '75001',
    ville VARCHAR(100) NOT NULL DEFAULT 'Paris',
    pays VARCHAR(100) NOT NULL DEFAULT 'France',
    telephone VARCHAR(20) NOT NULL DEFAULT '01 23 45 67 89',
    email VARCHAR(254) NOT NULL DEFAULT 'contact@gestimmob.fr',
    site_web VARCHAR(200) DEFAULT '',
    siret VARCHAR(20) NOT NULL DEFAULT '123 456 789 00012',
    numero_licence VARCHAR(50) NOT NULL DEFAULT '123456789',
    capital_social VARCHAR(100) DEFAULT '',
    forme_juridique VARCHAR(100) NOT NULL DEFAULT 'SARL',
    logo_url VARCHAR(200) DEFAULT '',
    logo_upload VARCHAR(100) DEFAULT '',
    entete_upload VARCHAR(100) DEFAULT '',
    couleur_principale VARCHAR(7) NOT NULL DEFAULT '#2c3e50',
    couleur_secondaire VARCHAR(7) NOT NULL DEFAULT '#3498db',
    iban VARCHAR(34) DEFAULT '',
    bic VARCHAR(11) DEFAULT '',
    banque VARCHAR(100) DEFAULT '',
    texte_contrat TEXT DEFAULT '',
    texte_resiliation TEXT DEFAULT '',
    actif BOOLEAN NOT NULL DEFAULT TRUE,
    date_creation TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    date_modification TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Table: NiveauAcces
CREATE TABLE core_niveauacces (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(50) UNIQUE NOT NULL,
    niveau VARCHAR(20) UNIQUE NOT NULL CHECK (niveau IN ('public', 'interne', 'confidentiel', 'secret', 'top_secret')),
    description TEXT DEFAULT '',
    priorite INTEGER NOT NULL DEFAULT 5 CHECK (priorite >= 1 AND priorite <= 10),
    date_creation TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    date_modification TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    actif BOOLEAN NOT NULL DEFAULT TRUE
);

-- Table: PermissionTableauBord
CREATE TABLE core_permissiontableaubord (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(100) UNIQUE NOT NULL,
    type_donnees VARCHAR(20) NOT NULL CHECK (type_donnees IN ('financier', 'locataire', 'bailleur', 'propriete', 'contrat', 'paiement', 'charge', 'statistique', 'rapport')),
    niveau_acces_requis_id INTEGER NOT NULL,
    peut_voir_montants BOOLEAN NOT NULL DEFAULT FALSE,
    peut_voir_details_personnels BOOLEAN NOT NULL DEFAULT FALSE,
    peut_voir_historique BOOLEAN NOT NULL DEFAULT FALSE,
    peut_exporter BOOLEAN NOT NULL DEFAULT FALSE,
    peut_imprimer BOOLEAN NOT NULL DEFAULT FALSE,
    limite_periode_jours INTEGER DEFAULT NULL,
    limite_nombre_resultats INTEGER DEFAULT NULL,
    date_creation TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    date_modification TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    actif BOOLEAN NOT NULL DEFAULT TRUE,
    FOREIGN KEY (niveau_acces_requis_id) REFERENCES core_niveauacces(id)
);

-- Table: AuditLog
CREATE TABLE core_auditlog (
    id SERIAL PRIMARY KEY,
    content_type_id INTEGER NOT NULL,
    object_id INTEGER NOT NULL,
    action VARCHAR(20) NOT NULL CHECK (action IN ('create', 'update', 'delete', 'view', 'export', 'import', 'login', 'logout', 'validation', 'rejection')),
    user_id INTEGER NOT NULL,
    details JSONB DEFAULT '{}',
    object_repr VARCHAR(200) NOT NULL,
    ip_address INET DEFAULT NULL,
    user_agent TEXT DEFAULT '',
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    description TEXT DEFAULT '',
    FOREIGN KEY (content_type_id) REFERENCES django_content_type(id),
    FOREIGN KEY (user_id) REFERENCES utilisateurs_utilisateur(id)
);

-- Table: Devise
CREATE TABLE core_devise (
    id SERIAL PRIMARY KEY,
    code VARCHAR(3) UNIQUE NOT NULL,
    nom VARCHAR(100) NOT NULL,
    symbole VARCHAR(10) NOT NULL,
    taux_change DECIMAL(10,4) NOT NULL DEFAULT 1.0000,
    date_creation TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    date_modification TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    actif BOOLEAN NOT NULL DEFAULT TRUE,
    par_defaut BOOLEAN NOT NULL DEFAULT FALSE
);

-- =====================================================
-- 2. MODULE UTILISATEURS
-- =====================================================

-- Table: GroupeTravail
CREATE TABLE utilisateurs_groupetravail (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(100) UNIQUE NOT NULL,
    description TEXT DEFAULT '',
    actif BOOLEAN NOT NULL DEFAULT TRUE,
    date_creation TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    date_modification TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Table: Utilisateur (étend AbstractUser)
CREATE TABLE utilisateurs_utilisateur (
    id SERIAL PRIMARY KEY,
    password VARCHAR(128) NOT NULL,
    last_login TIMESTAMP DEFAULT NULL,
    is_superuser BOOLEAN NOT NULL DEFAULT FALSE,
    username VARCHAR(150) UNIQUE NOT NULL,
    first_name VARCHAR(150) DEFAULT '',
    last_name VARCHAR(150) DEFAULT '',
    email VARCHAR(254) DEFAULT '',
    is_staff BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    date_joined TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    telephone VARCHAR(100) DEFAULT '',
    adresse TEXT DEFAULT '',
    date_naissance DATE DEFAULT NULL,
    photo VARCHAR(100) DEFAULT NULL,
    groupe_travail_id INTEGER DEFAULT NULL,
    poste VARCHAR(100) DEFAULT '',
    departement VARCHAR(100) DEFAULT '',
    date_embauche DATE DEFAULT NULL,
    derniere_connexion TIMESTAMP DEFAULT NULL,
    date_creation TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    date_modification TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    deleted_at TIMESTAMP DEFAULT NULL,
    deleted_by_id INTEGER DEFAULT NULL,
    FOREIGN KEY (groupe_travail_id) REFERENCES utilisateurs_groupetravail(id),
    FOREIGN KEY (deleted_by_id) REFERENCES utilisateurs_utilisateur(id)
);

-- =====================================================
-- 3. MODULE PROPRIETES
-- =====================================================

-- Table: TypeBien
CREATE TABLE proprietes_typebien (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(100) UNIQUE NOT NULL,
    description TEXT DEFAULT '',
    actif BOOLEAN NOT NULL DEFAULT TRUE,
    date_creation TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    date_modification TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Table: Bailleur
CREATE TABLE proprietes_bailleur (
    id SERIAL PRIMARY KEY,
    numero_bailleur VARCHAR(20) UNIQUE NOT NULL DEFAULT 'BL0001',
    civilite VARCHAR(5) NOT NULL DEFAULT 'M' CHECK (civilite IN ('M', 'Mme', 'Mlle')),
    nom VARCHAR(100) NOT NULL,
    prenom VARCHAR(100) NOT NULL,
    date_naissance DATE DEFAULT NULL,
    email VARCHAR(254) DEFAULT NULL,
    telephone VARCHAR(20) NOT NULL,
    telephone_mobile VARCHAR(20) DEFAULT '',
    adresse TEXT DEFAULT NULL,
    code_postal VARCHAR(10) DEFAULT NULL,
    ville VARCHAR(100) DEFAULT NULL,
    pays VARCHAR(100) DEFAULT NULL,
    profession VARCHAR(100) DEFAULT '',
    employeur VARCHAR(100) DEFAULT '',
    revenus_mensuels DECIMAL(12,2) DEFAULT NULL,
    statut VARCHAR(20) NOT NULL DEFAULT 'actif' CHECK (statut IN ('actif', 'inactif', 'suspendu')),
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    date_creation TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    date_modification TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Table: Locataire
CREATE TABLE proprietes_locataire (
    id SERIAL PRIMARY KEY,
    numero_locataire VARCHAR(20) UNIQUE NOT NULL DEFAULT 'LT0001',
    civilite VARCHAR(5) NOT NULL DEFAULT 'M' CHECK (civilite IN ('M', 'Mme', 'Mlle')),
    nom VARCHAR(100) NOT NULL,
    prenom VARCHAR(100) NOT NULL,
    date_naissance DATE DEFAULT NULL,
    email VARCHAR(254) DEFAULT NULL,
    telephone VARCHAR(20) NOT NULL,
    telephone_mobile VARCHAR(20) DEFAULT '',
    adresse TEXT DEFAULT NULL,
    code_postal VARCHAR(10) DEFAULT NULL,
    ville VARCHAR(100) DEFAULT NULL,
    pays VARCHAR(100) DEFAULT NULL,
    profession VARCHAR(100) DEFAULT '',
    employeur VARCHAR(100) DEFAULT '',
    revenus_mensuels DECIMAL(12,2) DEFAULT NULL,
    statut VARCHAR(20) NOT NULL DEFAULT 'actif' CHECK (statut IN ('actif', 'inactif', 'suspendu')),
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    date_creation TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    date_modification TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Table: Propriete
CREATE TABLE proprietes_propriete (
    id SERIAL PRIMARY KEY,
    numero_propriete VARCHAR(20) UNIQUE NOT NULL DEFAULT 'PR0001',
    titre VARCHAR(200) NOT NULL,
    description TEXT DEFAULT '',
    adresse TEXT DEFAULT NULL,
    code_postal VARCHAR(10) DEFAULT NULL,
    ville VARCHAR(100) DEFAULT NULL,
    pays VARCHAR(100) DEFAULT NULL,
    type_bien_id INTEGER NOT NULL,
    surface DECIMAL(8,2) DEFAULT NULL,
    nombre_pieces INTEGER NOT NULL,
    nombre_chambres INTEGER NOT NULL,
    nombre_salles_bain INTEGER NOT NULL,
    ascenseur BOOLEAN NOT NULL DEFAULT FALSE,
    parking BOOLEAN NOT NULL DEFAULT FALSE,
    balcon BOOLEAN NOT NULL DEFAULT FALSE,
    jardin BOOLEAN NOT NULL DEFAULT FALSE,
    prix_achat DECIMAL(12,2) DEFAULT NULL,
    loyer_actuel DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    charges_locataire DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    etat VARCHAR(20) NOT NULL DEFAULT 'bon' CHECK (etat IN ('excellent', 'tres_bon', 'bon', 'moyen', 'a_renover')),
    disponible BOOLEAN NOT NULL DEFAULT TRUE,
    bailleur_id INTEGER NOT NULL,
    notes TEXT DEFAULT '',
    date_creation TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    date_modification TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    cree_par_id INTEGER NOT NULL,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    FOREIGN KEY (type_bien_id) REFERENCES proprietes_typebien(id),
    FOREIGN KEY (bailleur_id) REFERENCES proprietes_bailleur(id),
    FOREIGN KEY (cree_par_id) REFERENCES utilisateurs_utilisateur(id)
);

-- =====================================================
-- INDEXES POUR OPTIMISATION
-- =====================================================

-- Indexes sur les champs fréquemment utilisés
CREATE INDEX idx_contrat_propriete ON contrats_contrat(propriete_id);
CREATE INDEX idx_contrat_locataire ON contrats_contrat(locataire_id);
CREATE INDEX idx_contrat_actif ON contrats_contrat(est_actif);
CREATE INDEX idx_paiement_contrat ON paiements_paiement(contrat_id);
CREATE INDEX idx_paiement_date ON paiements_paiement(date_paiement);
CREATE INDEX idx_paiement_statut ON paiements_paiement(statut);
CREATE INDEX idx_propriete_bailleur ON proprietes_propriete(bailleur_id);
CREATE INDEX idx_propriete_disponible ON proprietes_propriete(disponible);
CREATE INDEX idx_notification_recipient ON notifications_notification(recipient_id);
CREATE INDEX idx_notification_read ON notifications_notification(is_read);
CREATE INDEX idx_auditlog_user ON core_auditlog(user_id);
CREATE INDEX idx_auditlog_timestamp ON core_auditlog(timestamp);

-- =====================================================
-- DONNÉES INITIALES
-- =====================================================

-- Insérer les niveaux d'accès par défaut
INSERT INTO core_niveauacces (nom, niveau, description, priorite) VALUES
('Public', 'public', 'Données accessibles à tous', 1),
('Interne', 'interne', 'Données de l''équipe', 3),
('Confidentiel', 'confidentiel', 'Données sensibles', 5),
('Secret', 'secret', 'Données critiques direction', 8),
('Top Secret', 'top_secret', 'Données stratégiques', 10);

-- Insérer les types de biens par défaut
INSERT INTO proprietes_typebien (nom, description) VALUES
('Appartement', 'Appartement résidentiel'),
('Studio', 'Studio meublé'),
('Maison', 'Maison individuelle'),
('Bureau', 'Espace de bureau'),
('Commerce', 'Local commercial'),
('Parking', 'Place de parking');

-- Insérer les devises par défaut
INSERT INTO core_devise (code, nom, symbole, taux_change, par_defaut) VALUES
('EUR', 'Euro', '€', 1.0000, TRUE),
('USD', 'Dollar américain', '$', 0.8500, FALSE),
('XOF', 'Franc CFA', 'F', 0.0015, FALSE);

-- Insérer un utilisateur administrateur par défaut
INSERT INTO utilisateurs_utilisateur (username, password, first_name, last_name, email, is_staff, is_superuser, is_active) VALUES
('admin', 'pbkdf2_sha256$600000$dummy$dummy', 'Administrateur', 'Système', 'admin@gestimmob.fr', TRUE, TRUE, TRUE);

-- Insérer une configuration d'entreprise par défaut
INSERT INTO core_configurationentreprise (nom_entreprise, actif) VALUES
('GESTIMMOB', TRUE);

-- =====================================================
-- TRIGGERS POUR AUDIT
-- =====================================================

-- Fonction pour mettre à jour date_modification
CREATE OR REPLACE FUNCTION update_modified_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.date_modification = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers pour les tables principales
CREATE TRIGGER update_core_configurationentreprise_modification 
    BEFORE UPDATE ON core_configurationentreprise
    FOR EACH ROW EXECUTE FUNCTION update_modified_column();

CREATE TRIGGER update_utilisateurs_utilisateur_modification 
    BEFORE UPDATE ON utilisateurs_utilisateur
    FOR EACH ROW EXECUTE FUNCTION update_modified_column();

CREATE TRIGGER update_proprietes_propriete_modification 
    BEFORE UPDATE ON proprietes_propriete
    FOR EACH ROW EXECUTE FUNCTION update_modified_column();

CREATE TRIGGER update_contrats_contrat_modification 
    BEFORE UPDATE ON contrats_contrat
    FOR EACH ROW EXECUTE FUNCTION update_modified_column();

-- =====================================================
-- FIN DU SCHÉMA SQL POSTGRESQL
-- ====================================================="""
    
    return sql_content

def generate_mysql():
    """Génère le code SQL pour MySQL"""
    
    sql_content = """-- =====================================================
-- SCHÉMA SQL COMPLET - GESTIMMOB (MySQL)
-- Application de Gestion Immobilière
-- =====================================================

-- =====================================================
-- 1. MODULE CORE (Configuration & Sécurité)
-- =====================================================

-- Table: ConfigurationEntreprise
CREATE TABLE core_configurationentreprise (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nom_entreprise VARCHAR(200) NOT NULL DEFAULT 'GESTIMMOB',
    slogan VARCHAR(200) DEFAULT '',
    adresse VARCHAR(200) NOT NULL DEFAULT '123 Rue de la Paix',
    code_postal VARCHAR(10) NOT NULL DEFAULT '75001',
    ville VARCHAR(100) NOT NULL DEFAULT 'Paris',
    pays VARCHAR(100) NOT NULL DEFAULT 'France',
    telephone VARCHAR(20) NOT NULL DEFAULT '01 23 45 67 89',
    email VARCHAR(254) NOT NULL DEFAULT 'contact@gestimmob.fr',
    site_web VARCHAR(200) DEFAULT '',
    siret VARCHAR(20) NOT NULL DEFAULT '123 456 789 00012',
    numero_licence VARCHAR(50) NOT NULL DEFAULT '123456789',
    capital_social VARCHAR(100) DEFAULT '',
    forme_juridique VARCHAR(100) NOT NULL DEFAULT 'SARL',
    logo_url VARCHAR(200) DEFAULT '',
    logo_upload VARCHAR(100) DEFAULT '',
    entete_upload VARCHAR(100) DEFAULT '',
    couleur_principale VARCHAR(7) NOT NULL DEFAULT '#2c3e50',
    couleur_secondaire VARCHAR(7) NOT NULL DEFAULT '#3498db',
    iban VARCHAR(34) DEFAULT '',
    bic VARCHAR(11) DEFAULT '',
    banque VARCHAR(100) DEFAULT '',
    texte_contrat TEXT DEFAULT '',
    texte_resiliation TEXT DEFAULT '',
    actif BOOLEAN NOT NULL DEFAULT TRUE,
    date_creation TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    date_modification TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table: NiveauAcces
CREATE TABLE core_niveauacces (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nom VARCHAR(50) UNIQUE NOT NULL,
    niveau VARCHAR(20) UNIQUE NOT NULL CHECK (niveau IN ('public', 'interne', 'confidentiel', 'secret', 'top_secret')),
    description TEXT DEFAULT '',
    priorite INT NOT NULL DEFAULT 5 CHECK (priorite >= 1 AND priorite <= 10),
    date_creation TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    date_modification TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    actif BOOLEAN NOT NULL DEFAULT TRUE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table: PermissionTableauBord
CREATE TABLE core_permissiontableaubord (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nom VARCHAR(100) UNIQUE NOT NULL,
    type_donnees VARCHAR(20) NOT NULL CHECK (type_donnees IN ('financier', 'locataire', 'bailleur', 'propriete', 'contrat', 'paiement', 'charge', 'statistique', 'rapport')),
    niveau_acces_requis_id INT NOT NULL,
    peut_voir_montants BOOLEAN NOT NULL DEFAULT FALSE,
    peut_voir_details_personnels BOOLEAN NOT NULL DEFAULT FALSE,
    peut_voir_historique BOOLEAN NOT NULL DEFAULT FALSE,
    peut_exporter BOOLEAN NOT NULL DEFAULT FALSE,
    peut_imprimer BOOLEAN NOT NULL DEFAULT FALSE,
    limite_periode_jours INT DEFAULT NULL,
    limite_nombre_resultats INT DEFAULT NULL,
    date_creation TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    date_modification TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    actif BOOLEAN NOT NULL DEFAULT TRUE,
    FOREIGN KEY (niveau_acces_requis_id) REFERENCES core_niveauacces(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table: AuditLog
CREATE TABLE core_auditlog (
    id INT AUTO_INCREMENT PRIMARY KEY,
    content_type_id INT NOT NULL,
    object_id INT NOT NULL,
    action VARCHAR(20) NOT NULL CHECK (action IN ('create', 'update', 'delete', 'view', 'export', 'import', 'login', 'logout', 'validation', 'rejection')),
    user_id INT NOT NULL,
    details JSON DEFAULT NULL,
    object_repr VARCHAR(200) NOT NULL,
    ip_address VARCHAR(45) DEFAULT NULL,
    user_agent TEXT DEFAULT '',
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    description TEXT DEFAULT '',
    FOREIGN KEY (content_type_id) REFERENCES django_content_type(id),
    FOREIGN KEY (user_id) REFERENCES utilisateurs_utilisateur(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table: Devise
CREATE TABLE core_devise (
    id INT AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(3) UNIQUE NOT NULL,
    nom VARCHAR(100) NOT NULL,
    symbole VARCHAR(10) NOT NULL,
    taux_change DECIMAL(10,4) NOT NULL DEFAULT 1.0000,
    date_creation TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    date_modification TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    actif BOOLEAN NOT NULL DEFAULT TRUE,
    par_defaut BOOLEAN NOT NULL DEFAULT FALSE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- 2. MODULE UTILISATEURS
-- =====================================================

-- Table: GroupeTravail
CREATE TABLE utilisateurs_groupetravail (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nom VARCHAR(100) UNIQUE NOT NULL,
    description TEXT DEFAULT '',
    actif BOOLEAN NOT NULL DEFAULT TRUE,
    date_creation TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    date_modification TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table: Utilisateur (étend AbstractUser)
CREATE TABLE utilisateurs_utilisateur (
    id INT AUTO_INCREMENT PRIMARY KEY,
    password VARCHAR(128) NOT NULL,
    last_login TIMESTAMP DEFAULT NULL,
    is_superuser BOOLEAN NOT NULL DEFAULT FALSE,
    username VARCHAR(150) UNIQUE NOT NULL,
    first_name VARCHAR(150) DEFAULT '',
    last_name VARCHAR(150) DEFAULT '',
    email VARCHAR(254) DEFAULT '',
    is_staff BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    date_joined TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    telephone VARCHAR(100) DEFAULT '',
    adresse TEXT DEFAULT '',
    date_naissance DATE DEFAULT NULL,
    photo VARCHAR(100) DEFAULT NULL,
    groupe_travail_id INT DEFAULT NULL,
    poste VARCHAR(100) DEFAULT '',
    departement VARCHAR(100) DEFAULT '',
    date_embauche DATE DEFAULT NULL,
    derniere_connexion TIMESTAMP DEFAULT NULL,
    date_creation TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    date_modification TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    deleted_at TIMESTAMP DEFAULT NULL,
    deleted_by_id INT DEFAULT NULL,
    FOREIGN KEY (groupe_travail_id) REFERENCES utilisateurs_groupetravail(id),
    FOREIGN KEY (deleted_by_id) REFERENCES utilisateurs_utilisateur(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- INDEXES POUR OPTIMISATION
-- =====================================================

-- Indexes sur les champs fréquemment utilisés
CREATE INDEX idx_contrat_propriete ON contrats_contrat(propriete_id);
CREATE INDEX idx_contrat_locataire ON contrats_contrat(locataire_id);
CREATE INDEX idx_contrat_actif ON contrats_contrat(est_actif);
CREATE INDEX idx_paiement_contrat ON paiements_paiement(contrat_id);
CREATE INDEX idx_paiement_date ON paiements_paiement(date_paiement);
CREATE INDEX idx_paiement_statut ON paiements_paiement(statut);
CREATE INDEX idx_propriete_bailleur ON proprietes_propriete(bailleur_id);
CREATE INDEX idx_propriete_disponible ON proprietes_propriete(disponible);
CREATE INDEX idx_notification_recipient ON notifications_notification(recipient_id);
CREATE INDEX idx_notification_read ON notifications_notification(is_read);
CREATE INDEX idx_auditlog_user ON core_auditlog(user_id);
CREATE INDEX idx_auditlog_timestamp ON core_auditlog(timestamp);

-- =====================================================
-- DONNÉES INITIALES
-- =====================================================

-- Insérer les niveaux d'accès par défaut
INSERT INTO core_niveauacces (nom, niveau, description, priorite) VALUES
('Public', 'public', 'Données accessibles à tous', 1),
('Interne', 'interne', 'Données de l''équipe', 3),
('Confidentiel', 'confidentiel', 'Données sensibles', 5),
('Secret', 'secret', 'Données critiques direction', 8),
('Top Secret', 'top_secret', 'Données stratégiques', 10);

-- Insérer les types de biens par défaut
INSERT INTO proprietes_typebien (nom, description) VALUES
('Appartement', 'Appartement résidentiel'),
('Studio', 'Studio meublé'),
('Maison', 'Maison individuelle'),
('Bureau', 'Espace de bureau'),
('Commerce', 'Local commercial'),
('Parking', 'Place de parking');

-- Insérer les devises par défaut
INSERT INTO core_devise (code, nom, symbole, taux_change, par_defaut) VALUES
('EUR', 'Euro', '€', 1.0000, TRUE),
('USD', 'Dollar américain', '$', 0.8500, FALSE),
('XOF', 'Franc CFA', 'F', 0.0015, FALSE);

-- Insérer un utilisateur administrateur par défaut
INSERT INTO utilisateurs_utilisateur (username, password, first_name, last_name, email, is_staff, is_superuser, is_active) VALUES
('admin', 'pbkdf2_sha256$600000$dummy$dummy', 'Administrateur', 'Système', 'admin@gestimmob.fr', TRUE, TRUE, TRUE);

-- Insérer une configuration d'entreprise par défaut
INSERT INTO core_configurationentreprise (nom_entreprise, actif) VALUES
('GESTIMMOB', TRUE);

-- =====================================================
-- FIN DU SCHÉMA SQL MYSQL
-- ====================================================="""
    
    return sql_content

def main():
    """Fonction principale pour générer tous les fichiers SQL"""
    
    print("=" * 60)
    print("🗄️  GÉNÉRATION DES SCRIPTS SQL POUR DIFFÉRENTS SGBD")
    print("=" * 60)
    
    # Générer PostgreSQL
    print("📝 Génération du script PostgreSQL...")
    postgresql_sql = generate_postgresql()
    with open('SCHEMA_POSTGRESQL.sql', 'w', encoding='utf-8') as f:
        f.write(postgresql_sql)
    print("✅ Fichier PostgreSQL créé: SCHEMA_POSTGRESQL.sql")
    
    # Générer MySQL
    print("📝 Génération du script MySQL...")
    mysql_sql = generate_mysql()
    with open('SCHEMA_MYSQL.sql', 'w', encoding='utf-8') as f:
        f.write(mysql_sql)
    print("✅ Fichier MySQL créé: SCHEMA_MYSQL.sql")
    
    print("\n" + "=" * 60)
    print("🎉 GÉNÉRATION TERMINÉE !")
    print("=" * 60)
    print("\n📁 Fichiers créés:")
    print("  - SCHEMA_SQL_COMPLET.sql (SQLite)")
    print("  - SCHEMA_POSTGRESQL.sql (PostgreSQL)")
    print("  - SCHEMA_MYSQL.sql (MySQL)")
    print("\n📝 Scripts disponibles:")
    print("  - create_database.py (Création automatique SQLite)")
    print("  - generate_sql_other_dbms.py (Génération multi-SGBD)")
    
    print("\n🚀 Utilisation:")
    print("1. SQLite: python create_database.py")
    print("2. PostgreSQL: psql -d database_name -f SCHEMA_POSTGRESQL.sql")
    print("3. MySQL: mysql -u username -p database_name < SCHEMA_MYSQL.sql")

if __name__ == '__main__':
    main()
