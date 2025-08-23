# ProjetImo - Application de Gestion Immobilière

## Description
Application Django complète pour la gestion immobilière, incluant la gestion des propriétés, contrats, paiements, utilisateurs et notifications.

## Fonctionnalités principales
- **Gestion des propriétés** : Ajout, modification, suppression de biens immobiliers
- **Gestion des contrats** : Création et suivi des contrats de location/vente
- **Gestion des paiements** : Suivi des loyers, charges et autres paiements
- **Gestion des utilisateurs** : Système d'authentification et de gestion des droits
- **Notifications** : Système de notifications automatiques
- **API REST** : Interface programmatique pour l'intégration
- **Interface web** : Dashboard moderne et responsive avec Bootstrap

## Technologies utilisées
- **Backend** : Django 4.2+, Python 3.8+
- **Frontend** : HTML5, CSS3, JavaScript, Bootstrap 5
- **Base de données** : SQLite (développement), PostgreSQL/MySQL (production)
- **API** : Django REST Framework
- **Authentification** : Système d'authentification Django personnalisé

## Installation

### Prérequis
- Python 3.8 ou supérieur
- pip (gestionnaire de paquets Python)
- Git

### Installation locale
```bash
# Cloner le repository
git clone <url-du-repo>
cd projetImo

# Créer un environnement virtuel
python -m venv venv

# Activer l'environnement virtuel
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt

# Effectuer les migrations
python manage.py makemigrations
python manage.py migrate

# Créer un superutilisateur
python manage.py createsuperuser

# Lancer le serveur de développement
python manage.py runserver
```

## Structure du projet
```
projetImo/
├── bailleurs/          # Gestion des bailleurs
├── contrats/           # Gestion des contrats
├── core/               # Fonctionnalités principales
├── gestion_immobiliere/ # Configuration Django
├── notifications/      # Système de notifications
├── paiements/          # Gestion des paiements
├── proprietes/         # Gestion des propriétés
├── utilisateurs/       # Gestion des utilisateurs
├── static/             # Fichiers statiques (CSS, JS, images)
├── templates/          # Templates HTML
├── media/              # Fichiers uploadés par les utilisateurs
└── manage.py           # Script de gestion Django
```

## Configuration

### Variables d'environnement
Créer un fichier `.env` à la racine du projet :
```env
DEBUG=True
SECRET_KEY=votre-clé-secrète
DATABASE_URL=sqlite:///db.sqlite3
ALLOWED_HOSTS=localhost,127.0.0.1
```

### Base de données
- **Développement** : SQLite (par défaut)
- **Production** : PostgreSQL ou MySQL recommandés

## Utilisation

### Accès à l'application
- **Interface web** : http://localhost:8000
- **Admin Django** : http://localhost:8000/admin
- **API REST** : http://localhost:8000/api/

### Création d'un utilisateur
1. Accéder à l'interface d'administration
2. Créer un nouvel utilisateur
3. Assigner les permissions appropriées

## Développement

### Ajout de nouvelles fonctionnalités
1. Créer les modèles dans l'app appropriée
2. Effectuer les migrations
3. Créer les vues et templates
4. Ajouter les URLs
5. Tester les fonctionnalités

### Tests
```bash
# Lancer tous les tests
python manage.py test

# Lancer les tests d'une app spécifique
python manage.py test utilisateurs
```

### Code style
- Suivre les conventions PEP 8
- Utiliser des noms de variables et fonctions descriptifs
- Ajouter des docstrings pour les classes et méthodes
- Commenter le code complexe

## Déploiement

### Production
1. Modifier `DEBUG=False` dans les paramètres
2. Configurer une base de données de production
3. Collecter les fichiers statiques : `python manage.py collectstatic`
4. Configurer un serveur web (Nginx, Apache)
5. Utiliser Gunicorn ou uWSGI comme serveur WSGI

### Docker (optionnel)
```bash
# Construire l'image
docker build -t projetimo .

# Lancer le conteneur
docker run -p 8000:8000 projetimo
```

## Contribution
1. Fork le projet
2. Créer une branche pour votre fonctionnalité
3. Commiter vos changements
4. Pousser vers la branche
5. Ouvrir une Pull Request

## Licence
Ce projet est sous licence MIT. Voir le fichier LICENSE pour plus de détails.

## Support
Pour toute question ou problème :
- Ouvrir une issue sur GitHub
- Contacter l'équipe de développement

## Changelog
Voir le fichier CHANGELOG.md pour l'historique des versions. 