-- =====================================================
-- SCHEMA BASE DE DONNEES - SYSTEME AVANCES INTELLIGENTES
-- =====================================================
-- Date: 09/10/2025
-- Version: 2.0
-- Description: Schéma mis à jour avec le système d'avances intelligent
-- =====================================================

-- =====================================================
-- NOUVELLES TABLES ET CHAMPS AJOUTES
-- =====================================================

-- 1. NOUVEAU CHAMP DANS AVANCELOYER
-- =====================================================
-- Ajout du champ 'paiement' pour lier les avances aux paiements
ALTER TABLE paiements_avanceloyer ADD COLUMN paiement_id INTEGER NULL;
ALTER TABLE paiements_avanceloyer ADD CONSTRAINT fk_avanceloyer_paiement 
    FOREIGN KEY (paiement_id) REFERENCES paiements_paiement(id) 
    ON DELETE SET NULL;

-- 2. NOUVEAUX CHAMPS DE SELECTION MANUELLE
-- =====================================================
-- Champs pour la sélection manuelle des mois couverts
ALTER TABLE paiements_avanceloyer ADD COLUMN mode_selection_mois VARCHAR(20) DEFAULT 'automatique';
ALTER TABLE paiements_avanceloyer ADD COLUMN mois_couverts_manuels JSON DEFAULT '[]';

-- =====================================================
-- MIGRATIONS REQUISES
-- =====================================================

-- Migration 0011: Ajout des champs de sélection manuelle
-- Migration 0012: Ajout du champ paiement

-- =====================================================
-- INDEX POUR PERFORMANCES
-- =====================================================

-- Index pour les requêtes fréquentes
CREATE INDEX IF NOT EXISTS idx_avanceloyer_paiement ON paiements_avanceloyer(paiement_id);
CREATE INDEX IF NOT EXISTS idx_avanceloyer_mode_selection ON paiements_avanceloyer(mode_selection_mois);
CREATE INDEX IF NOT EXISTS idx_avanceloyer_statut ON paiements_avanceloyer(statut);
CREATE INDEX IF NOT EXISTS idx_avanceloyer_contrat ON paiements_avanceloyer(contrat_id);

-- =====================================================
-- VUES POUR RAPPORTS
-- =====================================================

-- Vue des avances actives avec paiements
CREATE VIEW IF NOT EXISTS vue_avances_actives AS
SELECT 
    a.id,
    a.contrat_id,
    c.numero_contrat,
    a.montant_avance,
    a.montant_restant,
    a.nombre_mois_couverts,
    a.mois_debut_couverture,
    a.mois_fin_couverture,
    a.statut,
    a.mode_selection_mois,
    a.paiement_id,
    p.numero_paiement,
    p.date_paiement
FROM paiements_avanceloyer a
LEFT JOIN contrats_contrat c ON a.contrat_id = c.id
LEFT JOIN paiements_paiement p ON a.paiement_id = p.id
WHERE a.statut = 'active';

-- Vue des consommations d'avances
CREATE VIEW IF NOT EXISTS vue_consommations_avances AS
SELECT 
    ca.id,
    ca.avance_id,
    a.contrat_id,
    c.numero_contrat,
    ca.mois_consomme,
    ca.montant_consomme,
    ca.date_consommation,
    ca.solde_restant
FROM paiements_consommationavance ca
JOIN paiements_avanceloyer a ON ca.avance_id = a.id
JOIN contrats_contrat c ON a.contrat_id = c.id;

-- =====================================================
-- TRIGGERS POUR COHERENCE DES DONNEES
-- =====================================================

-- Trigger pour mettre à jour le montant restant
CREATE TRIGGER IF NOT EXISTS trigger_update_montant_restant
AFTER INSERT ON paiements_consommationavance
BEGIN
    UPDATE paiements_avanceloyer 
    SET montant_restant = montant_avance - (
        SELECT COALESCE(SUM(montant_consomme), 0) 
        FROM paiements_consommationavance 
        WHERE avance_id = NEW.avance_id
    )
    WHERE id = NEW.avance_id;
END;

-- Trigger pour mettre à jour le statut
CREATE TRIGGER IF NOT EXISTS trigger_update_statut_avance
AFTER UPDATE OF montant_restant ON paiements_avanceloyer
BEGIN
    UPDATE paiements_avanceloyer 
    SET statut = CASE 
        WHEN montant_restant <= 0 THEN 'epuisee'
        ELSE 'active'
    END
    WHERE id = NEW.id;
END;

-- =====================================================
-- DONNEES DE TEST (OPTIONNEL)
-- =====================================================

-- Insertion d'une avance de test (à supprimer en production)
-- INSERT INTO paiements_avanceloyer (
--     contrat_id, montant_avance, loyer_mensuel, date_avance, 
--     nombre_mois_couverts, mois_debut_couverture, mois_fin_couverture,
--     statut, montant_restant, mode_selection_mois, created_at, updated_at
-- ) VALUES (
--     1, 200000.00, 50000.00, '2025-10-09', 
--     4, '2025-10-01', '2026-01-01',
--     'active', 200000.00, 'automatique', 
--     datetime('now'), datetime('now')
-- );

-- =====================================================
-- VERIFICATION DE L'INTEGRITE
-- =====================================================

-- Vérifier que toutes les avances ont des données cohérentes
SELECT 
    'Avances sans contrat' as probleme,
    COUNT(*) as nombre
FROM paiements_avanceloyer a
LEFT JOIN contrats_contrat c ON a.contrat_id = c.id
WHERE c.id IS NULL

UNION ALL

SELECT 
    'Avances avec montant restant négatif' as probleme,
    COUNT(*) as nombre
FROM paiements_avanceloyer
WHERE montant_restant < 0

UNION ALL

SELECT 
    'Avances avec dates incohérentes' as probleme,
    COUNT(*) as nombre
FROM paiements_avanceloyer
WHERE mois_debut_couverture > mois_fin_couverture;

-- =====================================================
-- NOTES POUR LE DEPLOIEMENT
-- =====================================================

-- 1. Exécuter les migrations dans l'ordre :
--    - python manage.py migrate paiements 0011
--    - python manage.py migrate paiements 0012

-- 2. Vérifier l'intégrité des données :
--    - python manage.py shell
--    - from paiements.models_avance import AvanceLoyer
--    - AvanceLoyer.objects.filter(statut='epuisee', montant_restant__gt=0).count()

-- 3. Corriger les données existantes si nécessaire :
--    - python manage.py shell
--    - from paiements.models_avance import AvanceLoyer
--    - for avance in AvanceLoyer.objects.all(): avance.save()

-- 4. Tester les nouvelles fonctionnalités :
--    - Création d'avance avec sélection manuelle
--    - Intégration automatique avec les paiements
--    - Calculs de progression corrects
