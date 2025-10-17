# CORRECTION MANUELLE URGENTE - CHAMPS TÉLÉPHONE

## 🚨 PROBLÈME CRITIQUE
L'erreur `value too long for type character varying(20)` persiste car les colonnes de la base de données PostgreSQL n'ont pas été modifiées.

## 🔧 SOLUTION MANUELLE IMMÉDIATE

### Option 1: Via l'interface Render
1. Aller sur le dashboard Render
2. Sélectionner votre service `appli-kbis-postgresql`
3. Aller dans l'onglet "Shell"
4. Exécuter les commandes suivantes :

```bash
python emergency_fix.py
```

### Option 2: Via psql (si accès direct)
Se connecter à la base de données PostgreSQL et exécuter :

```sql
-- Corriger les colonnes de la table locataire
ALTER TABLE proprietes_locataire ALTER COLUMN telephone TYPE VARCHAR(30);
ALTER TABLE proprietes_locataire ALTER COLUMN telephone_mobile TYPE VARCHAR(30);
ALTER TABLE proprietes_locataire ALTER COLUMN garant_telephone TYPE VARCHAR(30);

-- Corriger les colonnes de la table bailleur
ALTER TABLE proprietes_bailleur ALTER COLUMN telephone TYPE VARCHAR(30);
ALTER TABLE proprietes_bailleur ALTER COLUMN telephone_mobile TYPE VARCHAR(30);
```

### Option 3: Redéploiement forcé
Le script `emergency_fix.py` sera exécuté automatiquement au prochain redéploiement.

## ✅ VÉRIFICATION
Après correction, vérifier que les colonnes sont bien à 30 caractères :

```sql
SELECT table_name, column_name, character_maximum_length 
FROM information_schema.columns 
WHERE table_name IN ('proprietes_locataire', 'proprietes_bailleur')
AND column_name IN ('telephone', 'telephone_mobile', 'garant_telephone')
ORDER BY table_name, column_name;
```

## 🎯 RÉSULTAT ATTENDU
Toutes les colonnes doivent afficher `character_maximum_length = 30`

