# Application de Gestion Immobilière

## Description
Cette application de gestion immobilière permet de gérer les propriétés, les bailleurs, les locataires, les contrats, les paiements et les rapports financiers.

## Configuration de l'environnement

### Méthode 1: Installation automatique (recommandée)

#### Pour Windows
1. Double-cliquez sur le fichier `install.bat` ou exécutez-le depuis l'invite de commandes
2. Suivez les instructions à l'écran

#### Pour macOS/Linux
1. Rendez le script exécutable : `chmod +x install.sh`
2. Exécutez le script : `./install.sh`

### Méthode 2: Installation manuelle

#### Prérequis
- Python 3.8 ou supérieur
- pip (gestionnaire de paquets Python)

#### Installation des dépendances
Pour plus de détails sur l'installation des dépendances, consultez le fichier [README-INSTALLATION.md](README-INSTALLATION.md).

### Installation de Django

1. **Créer un environnement virtuel** (recommandé):
```bash
python -m venv venv
```

2. **Activer l'environnement virtuel**:
- Sur Windows:
```bash
venv\Scripts\activate
```
- Sur macOS/Linux:
```bash
source venv/bin/activate
```

3. **Installer Django et les dépendances**:
```bash
pip install -r requirements.txt
```

### Configuration de l'application

1. **Configurer la base de données**:
```bash
python manage.py migrate
```

2. **Créer un superutilisateur** (optionnel mais recommandé):
```bash
python manage.py createsuperuser
```

3. **Collecter les fichiers statiques**:
```bash
python manage.py collectstatic
```

## Exécution de l'application

### Méthode 1: Démarrage automatique (recommandée)

#### Pour Windows
1. Double-cliquez sur le fichier `start.bat` ou exécutez-le depuis l'invite de commandes
2. L'application sera accessible à l'adresse http://127.0.0.1:8000/

#### Pour macOS/Linux
1. Rendez le script exécutable : `chmod +x start.sh`
2. Exécutez le script : `./start.sh`
3. L'application sera accessible à l'adresse http://127.0.0.1:8000/

### Méthode 2: Démarrage manuel

#### Démarrer le serveur de développement
```bash
python manage.py runserver
```

L'application sera accessible à l'adresse http://127.0.0.1:8000/

### Accès à l'interface d'administration
L'interface d'administration est accessible à l'adresse http://127.0.0.1:8000/admin/

## Structure du projet

- `bailleurs/` - Gestion des bailleurs
- `contrats/` - Gestion des contrats de location
- `core/` - Fonctionnalités centrales de l'application
- `gestion_immobiliere/` - Configuration principale du projet
- `notifications/` - Gestion des notifications
- `paiements/` - Gestion des paiements et rapports financiers
- `proprietes/` - Gestion des propriétés immobilières
- `static/` - Fichiers statiques (CSS, JavaScript, images)
- `templates/` - Templates HTML
- `utilisateurs/` - Gestion des utilisateurs et des groupes

## 🚀 Fonctionnalités principales

### 📊 Système de récapitulatifs mensuels (NOUVEAU)
- **Génération automatique** de rapports financiers mensuels
- **PDF professionnels** avec en-tête personnalisé et pied de page dynamique
- **Calculs précis** des loyers, charges et paiements
- **Gestion des permissions** (superusers et groupe PRIVILEGE)
- **Suppression logique** des récapitulatifs
- **Interface intuitive** pour la création et consultation

### 🏠 Gestion immobilière complète
- Gestion des propriétés, bailleurs et locataires
- Contrats de location avec suivi des paiements
- Système de notifications intégré
- Rapports financiers détaillés

### 🎨 Design et présentation
- Interface moderne et responsive
- Palette de couleurs unifiée avec de meilleurs contrastes
- Système de design complet avec variables CSS
- En-têtes et pieds de page personnalisables

### 🔒 Sécurité et permissions
- Système de groupes d'utilisateurs (PRIVILEGE, CAISSE, ADMINISTRATION)
- Contrôle d'accès granulaire
- Suppression logique des données sensibles
- Validation robuste des données

## 📚 Documentation

- **[Documentation des récapitulatifs](DOCUMENTATION_RECAPITULATIFS.md)** - Guide complet du système de récapitulatifs
- **[Guide d'installation](README-INSTALLATION.md)** - Instructions détaillées d'installation

## Dépannage

### Erreur "ModuleNotFoundError: No module named 'django'"
Cette erreur signifie que Django n'est pas installé ou que l'environnement virtuel n'est pas activé.

Solution:
1. Vérifier que l'environnement virtuel est activé
2. Installer Django avec `pip install django`

### Problèmes de base de données
Si vous rencontrez des problèmes avec la base de données:
```bash
python manage.py migrate
```

### Problèmes de fichiers statiques
Si les styles CSS ne s'affichent pas correctement:
```bash
python manage.py collectstatic