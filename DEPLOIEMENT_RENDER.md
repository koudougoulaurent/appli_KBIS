# 🚀 Guide de Déploiement Automatique sur Render

## 📋 Vue d'ensemble

Ce projet utilise un **script de déploiement automatique** qui s'exécute à chaque push sur la branche de production sur Render.

## 🔧 Configuration

### Fichiers de déploiement

1. **`build.sh`** : Script de build automatique
   - Installation des dépendances Python
   - Collecte des fichiers statiques
   - Exécution des migrations
   - **Régénération automatique des PDFs des contrats**
   - **Régénération automatique des récapitulatifs mensuels**

2. **`start.sh`** : Script de démarrage du serveur
   - Exécution finale des migrations
   - Mise à jour des statuts
   - Démarrage de Gunicorn

3. **`render.yaml`** : Configuration Render
   - Définit l'environnement Python
   - Configure les commandes de build et start
   - Gère les variables d'environnement

## 🎯 Processus de Déploiement Automatique

### Étape 1 : Push vers GitHub
```bash
git add .
git commit -m "Vos modifications"
git push origin migration-postgresql-propre
```

### Étape 2 : Render détecte le push et lance automatiquement :

```
🚀 DÉBUT DU DÉPLOIEMENT
├── 📦 Installation des dépendances Python
├── 📂 Collecte des fichiers statiques
├── 🗄️  Exécution des migrations
├── 📄 Régénération des PDFs des contrats existants
├── 📊 Régénération des récapitulatifs mensuels existants
└── ✅ DÉPLOIEMENT TERMINÉ
```

### Étape 3 : Démarrage du serveur
```
├── 🗄️  Migrations finales
├── 🔄 Mise à jour des statuts
└── 🌐 Serveur en ligne
```

## ⚙️ Commandes Manuelles (si nécessaire)

### Accès au Shell Render

1. Aller sur **Render Dashboard**
2. Sélectionner votre service **appli-kbis-postgresql**
3. Cliquer sur **"Shell"** dans le menu de gauche
4. Exécuter les commandes :

```bash
# Régénérer tous les contrats
python manage.py regenerer_contrats_pdf

# Régénérer tous les récapitulatifs
python manage.py regenerer_recapitulatifs_pdf

# Régénérer un contrat spécifique
python manage.py regenerer_contrats_pdf --contrat-id 123

# Régénérer les récaps d'un bailleur
python manage.py regenerer_recapitulatifs_pdf --bailleur-id 5

# Régénérer les récaps d'un mois
python manage.py regenerer_recapitulatifs_pdf --mois 2025-11
```

## 🔒 Sécurité

- Les commandes de régénération utilisent des **erreurs non bloquantes** (`|| echo`)
- Si aucun document n'existe, le déploiement continue normalement
- Les erreurs sont loguées mais ne bloquent pas le déploiement

## 📊 Monitoring

### Logs de déploiement sur Render

Vous pouvez voir l'exécution de chaque étape dans les logs Render :
1. Dashboard Render → Votre service
2. Onglet **"Logs"**
3. Filtrer par **"Deploy"**

### Vérification post-déploiement

```bash
# Vérifier les migrations
python manage.py showmigrations

# Vérifier les fichiers statiques
python manage.py collectstatic --dry-run

# Tester la génération de PDF
python manage.py regenerer_contrats_pdf --contrat-id 1
```

## 🆘 Dépannage

### Le déploiement échoue ?

1. **Vérifier les logs Render** pour identifier l'étape en échec
2. **Tester localement** :
   ```bash
   chmod +x build.sh
   ./build.sh
   ```
3. **Vérifier les dépendances** dans `requirements.txt`

### Les PDFs ne se régénèrent pas ?

- Vérifier que les commandes `regenerer_contrats_pdf` et `regenerer_recapitulatifs_pdf` existent
- Vérifier les permissions sur la base de données
- Exécuter manuellement via le Shell Render

## 🎉 Avantages de ce système

✅ **Automatique** : Aucune intervention manuelle nécessaire  
✅ **Fiable** : Toujours les mêmes étapes à chaque déploiement  
✅ **Traçable** : Logs détaillés de chaque étape  
✅ **Réversible** : En cas d'erreur, Render garde les versions précédentes  
✅ **PDFs à jour** : Tous les documents sont automatiquement mis à jour avec la dernière version  

## 📝 Notes importantes

- Le script `build.sh` doit être **exécutable** (`chmod +x build.sh`)
- Les erreurs de régénération de PDFs sont **non bloquantes** pour permettre le déploiement même sans documents existants
- Les variables d'environnement sont configurées dans `render.yaml`
- Le processus complet prend environ **2-5 minutes** selon le nombre de documents

---

**Dernière mise à jour :** Décembre 2025  
**Version :** 1.0

