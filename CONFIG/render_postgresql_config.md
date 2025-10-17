# Configuration PostgreSQL Progressive pour Render

## 🎯 Objectif
Configurer progressivement PostgreSQL sur Render tout en gardant SQLite comme fallback.

## 🔧 Configuration Actuelle

### 1. Settings Render (`gestion_immobiliere/settings_render.py`)
- **Détection automatique** de PostgreSQL via `DATABASE_URL`
- **Fallback vers SQLite** si PostgreSQL n'est pas disponible
- **Paramètres optimisés** pour Render

### 2. Script de Migration (`CONFIG/migrate_sqlite_to_postgresql_progressive.py`)
- **Sauvegarde automatique** des données SQLite
- **Migration progressive** vers PostgreSQL
- **Création des données initiales**

### 3. Script de Test (`CONFIG/test_postgresql_config.py`)
- **Test de connexion** PostgreSQL
- **Test des modèles** Django
- **Test des migrations**

## 🚀 Étapes de Configuration

### Étape 1: Configuration Render
1. Aller sur Render.com
2. Sélectionner votre service
3. Aller dans "Environment"
4. Ajouter la variable `DATABASE_URL` avec votre URL PostgreSQL

### Étape 2: Test Local
```bash
# Tester la configuration PostgreSQL
python CONFIG/test_postgresql_config.py

# Tester la migration
python CONFIG/migrate_sqlite_to_postgresql_progressive.py
```

### Étape 3: Déploiement
1. Pousser les modifications sur GitHub
2. Render détectera automatiquement PostgreSQL
3. L'application basculera automatiquement vers PostgreSQL

## 📊 Avantages de cette Configuration

### ✅ PostgreSQL (Production)
- **Persistance des données** sur Render
- **Performance optimisée** pour la production
- **Sauvegarde automatique** par Render
- **Scalabilité** améliorée

### ✅ SQLite (Fallback)
- **Compatibilité** avec l'existant
- **Simplicité** de configuration
- **Pas de dépendances** externes

## 🔍 Détection Automatique

Le système détecte automatiquement :
- **Environnement Render** : `RENDER=true`
- **URL PostgreSQL** : `DATABASE_URL` définie
- **Configuration** : Bascule automatique

## 🛠️ Commandes Utiles

### Test de Configuration
```bash
python CONFIG/test_postgresql_config.py
```

### Migration des Données
```bash
python CONFIG/migrate_sqlite_to_postgresql_progressive.py
```

### Setup de la Base
```bash
python setup_render.py
```

## 📝 Variables d'Environnement

### Obligatoires sur Render
- `DATABASE_URL` : URL de connexion PostgreSQL
- `RENDER` : `true` (défini automatiquement par Render)

### Optionnelles
- `DEBUG` : `false` (production)
- `SECRET_KEY` : Clé secrète Django

## 🎉 Résultat Attendu

Après configuration :
1. **Détection automatique** de PostgreSQL sur Render
2. **Migration transparente** des données SQLite
3. **Fonctionnement normal** avec PostgreSQL
4. **Fallback SQLite** si problème PostgreSQL

## 🔧 Dépannage

### Problème de Connexion PostgreSQL
- Vérifier `DATABASE_URL` sur Render
- Vérifier les paramètres de connexion
- Consulter les logs Render

### Problème de Migration
- Vérifier la sauvegarde SQLite
- Vérifier les permissions PostgreSQL
- Relancer la migration

### Fallback SQLite
- L'application basculera automatiquement
- Les données seront perdues (normal)
- Recréer les données initiales
