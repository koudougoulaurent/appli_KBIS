# 🚀 GUIDE DE DÉPLOIEMENT RENDER - KBIS INTERNATIONAL

## 📋 Prérequis

- Compte Render.com
- Application Django prête
- Base de données PostgreSQL configurée

## 🗄️ Configuration de la base de données permanente

### 1. Créer une base de données PostgreSQL sur Render

1. **Connectez-vous à Render.com**
2. **Allez dans "Databases"**
3. **Cliquez sur "New +"**
4. **Sélectionnez "PostgreSQL"**
5. **Configurez :**
   - **Name:** `kbis-postgres`
   - **Database:** `kbis_production`
   - **User:** `kbis_user`
   - **Plan:** Choisissez selon vos besoins :
     - **Starter (Gratuit):** 1 GB, 512 MB RAM
     - **Standard ($7/mois):** 10 GB, 1 GB RAM
     - **Pro ($25/mois):** 100 GB, 2 GB RAM
     - **Pro Max ($85/mois):** 500 GB, 4 GB RAM

### 2. Configuration recommandée

Pour une application de gestion immobilière, nous recommandons :

- **Développement/Test:** Plan Starter (gratuit)
- **Production légère:** Plan Standard ($7/mois)
- **Production moyenne:** Plan Pro ($25/mois)
- **Production intensive:** Plan Pro Max ($85/mois)

## ⚙️ Configuration de l'application

### 1. Variables d'environnement

Dans Render, configurez ces variables :

```bash
# Base de données (automatique avec Render)
DATABASE_URL=postgresql://kbis_user:password@host:port/kbis_production

# Django
DEBUG=False
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=appli-kbis.onrender.com

# Email (optionnel)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Autres
STATIC_URL=/static/
MEDIA_URL=/media/
```

### 2. Fichiers de configuration

Utilisez les fichiers fournis :
- `render.yaml` - Configuration Render
- `gestion_immobiliere/settings_render.py` - Settings Django
- `requirements_render.txt` - Dépendances Python

## 🚀 Déploiement

### 1. Méthode 1 : Via l'interface Render

1. **Connectez votre repository GitHub**
2. **Sélectionnez le repository KBIS**
3. **Configurez :**
   - **Build Command:** `pip install -r requirements_render.txt && python manage.py collectstatic --noinput`
   - **Start Command:** `gunicorn gestion_immobiliere.wsgi:application`
   - **Environment:** `Python 3.11`
4. **Ajoutez les variables d'environnement**
5. **Déployez !**

### 2. Méthode 2 : Via le fichier render.yaml

1. **Poussez le fichier `render.yaml` dans votre repository**
2. **Render détectera automatiquement la configuration**
3. **Déployez !**

### 3. Méthode 3 : Via le script de déploiement

```bash
# Rendre le script exécutable
chmod +x deploy_render.sh

# Exécuter le déploiement
./deploy_render.sh
```

## 📊 Gestion des données

### 1. Sauvegarde automatique

Render effectue des sauvegardes automatiques :
- **Starter:** Sauvegardes quotidiennes (7 jours de rétention)
- **Standard+:** Sauvegardes quotidiennes (30 jours de rétention)

### 2. Sauvegarde manuelle

```bash
# Via l'interface Render
# Allez dans votre base de données > "Backups" > "Create Backup"

# Via ligne de commande (si accès SSH)
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d_%H%M%S).sql
```

### 3. Restauration

```bash
# Via l'interface Render
# Allez dans "Backups" > Sélectionnez une sauvegarde > "Restore"

# Via ligne de commande
psql $DATABASE_URL < backup_file.sql
```

## 🔧 Maintenance

### 1. Monitoring

- **Logs:** Disponibles dans l'interface Render
- **Métriques:** CPU, RAM, Stockage
- **Alertes:** Configurables pour les seuils

### 2. Mises à jour

```bash
# 1. Modifier le code localement
# 2. Pousser vers GitHub
# 3. Render déploie automatiquement
# 4. Vérifier les logs de déploiement
```

### 3. Migrations de base de données

```bash
# Les migrations s'appliquent automatiquement au déploiement
# Ou manuellement via l'interface Render > "Shell"
python manage.py migrate --settings=gestion_immobiliere.settings_render
```

## 💰 Coûts estimés

### Plan Starter (Gratuit)
- **Base de données:** 1 GB
- **Application:** 512 MB RAM
- **Limitations:** Pas de support 24/7

### Plan Standard ($7/mois)
- **Base de données:** 10 GB
- **Application:** 1 GB RAM
- **Support:** Email

### Plan Pro ($25/mois)
- **Base de données:** 100 GB
- **Application:** 2 GB RAM
- **Support:** Email + Chat

### Plan Pro Max ($85/mois)
- **Base de données:** 500 GB
- **Application:** 4 GB RAM
- **Support:** Prioritaire

## 🚨 Points d'attention

### 1. Sécurité
- ✅ HTTPS automatique
- ✅ Variables d'environnement sécurisées
- ✅ Base de données isolée
- ⚠️ Configurer les CORS si nécessaire

### 2. Performance
- ✅ CDN pour les fichiers statiques
- ✅ Compression automatique
- ⚠️ Optimiser les requêtes Django
- ⚠️ Utiliser le cache si nécessaire

### 3. Sauvegarde
- ✅ Sauvegardes automatiques
- ⚠️ Tester la restauration régulièrement
- ⚠️ Exporter les données critiques

## 🆘 Dépannage

### Problèmes courants

1. **Erreur de migration**
   ```bash
   # Vérifier les logs
   # Appliquer manuellement
   python manage.py migrate --settings=gestion_immobiliere.settings_render
   ```

2. **Erreur de fichiers statiques**
   ```bash
   # Vérifier la configuration
   python manage.py collectstatic --noinput --settings=gestion_immobiliere.settings_render
   ```

3. **Erreur de base de données**
   ```bash
   # Vérifier la connexion
   python manage.py dbshell --settings=gestion_immobiliere.settings_render
   ```

### Support

- **Documentation Render:** https://render.com/docs
- **Support technique:** Via l'interface Render
- **Communauté:** Stack Overflow, Reddit

## 📈 Évolutivité

### Montée en charge
- **Vertical:** Changer de plan (plus de RAM/CPU)
- **Horizontal:** Load balancer (plans Pro+)
- **Base de données:** Réplication (plans Pro+)

### Migration vers d'autres plateformes
- **Export des données:** Via pg_dump
- **Configuration:** Fichiers fournis
- **Code:** Repository GitHub

---

*Guide de déploiement pour KBIS INTERNATIONAL - Gestion Immobilière*
