# Guide de Déploiement - ProjetImo

Ce guide explique comment déployer l'application ProjetImo sur une nouvelle machine ou en production.

## Prérequis

### Système
- **OS** : Windows 10+, macOS 10.15+, Ubuntu 18.04+, CentOS 7+
- **Python** : 3.8 ou supérieur
- **RAM** : Minimum 2GB, recommandé 4GB+
- **Espace disque** : Minimum 1GB

### Logiciels
- Python 3.8+
- pip (gestionnaire de paquets Python)
- Git
- Un éditeur de code (VS Code, PyCharm, etc.)

## Installation sur une nouvelle machine

### 1. Cloner le projet
```bash
# Cloner depuis GitHub
git clone https://github.com/yourusername/projetimo.git
cd projetimo

# Ou depuis un autre repository Git
git clone <url-du-repo>
cd projetimo
```

### 2. Créer l'environnement virtuel
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. Installer les dépendances
```bash
# Installation complète
pip install -r requirements.txt

# Ou installation avec Makefile
make install

# Installation en mode développement
make install-dev

# Installation en mode production
make install-prod
```

### 4. Configuration de l'environnement
```bash
# Copier le fichier d'exemple
cp env.example .env

# Éditer le fichier .env avec vos paramètres
# SECRET_KEY=votre-clé-secrète-unique
# DEBUG=False pour la production
# DATABASE_URL=votre-url-de-base-de-données
```

### 5. Configuration de la base de données
```bash
# Créer les tables
python manage.py migrate

# Créer un superutilisateur
python manage.py createsuperuser

# Ou utiliser le Makefile
make migrate
make superuser
```

### 6. Collecter les fichiers statiques
```bash
python manage.py collectstatic
# Ou
make collectstatic
```

### 7. Lancer l'application
```bash
# Mode développement
python manage.py runserver

# Ou avec Makefile
make run
```

## Configuration de la production

### Variables d'environnement critiques
```env
DEBUG=False
SECRET_KEY=votre-clé-secrète-très-longue-et-complexe
ALLOWED_HOSTS=votre-domaine.com,www.votre-domaine.com
DATABASE_URL=postgresql://user:password@localhost:5432/projetimo
```

### Base de données de production
```bash
# PostgreSQL (recommandé)
sudo apt-get install postgresql postgresql-contrib
sudo -u postgres createdb projetimo
sudo -u postgres createuser projetimo_user

# MySQL
sudo apt-get install mysql-server
mysql -u root -p
CREATE DATABASE projetimo;
CREATE USER 'projetimo_user'@'localhost' IDENTIFIED BY 'password';
GRANT ALL PRIVILEGES ON projetimo.* TO 'projetimo_user'@'localhost';
```

### Serveur web
```bash
# Nginx
sudo apt-get install nginx
sudo systemctl enable nginx
sudo systemctl start nginx

# Gunicorn
pip install gunicorn
gunicorn --bind 0.0.0.0:8000 gestion_immobiliere.wsgi:application
```

## Déploiement avec Docker (optionnel)

### 1. Construire l'image
```bash
docker build -t projetimo .
```

### 2. Lancer le conteneur
```bash
docker run -d -p 8000:8000 --name projetimo-app projetimo
```

### 3. Avec docker-compose
```bash
docker-compose up -d
```

## Commandes utiles

### Makefile
```bash
make help          # Afficher l'aide
make install       # Installation complète
make run           # Lancer le serveur
make test          # Lancer les tests
make clean         # Nettoyer les fichiers temporaires
make backup        # Sauvegarder la base de données
make restore       # Restaurer la base de données
make deploy        # Déploiement complet
```

### Django
```bash
python manage.py runserver          # Serveur de développement
python manage.py migrate            # Appliquer les migrations
python manage.py makemigrations    # Créer de nouvelles migrations
python manage.py collectstatic     # Collecter les fichiers statiques
python manage.py createsuperuser   # Créer un superutilisateur
python manage.py shell             # Shell Django
python manage.py test              # Lancer les tests
```

## Migration des données

### Sauvegarde
```bash
# Sauvegarde de la base de données
python manage.py dumpdata > backup.json

# Ou avec le Makefile
make backup
```

### Restauration
```bash
# Restauration des données
python manage.py loaddata backup.json

# Ou avec le Makefile
make restore
```

## Sécurité

### Checklist de sécurité
- [ ] `DEBUG=False` en production
- [ ] `SECRET_KEY` unique et complexe
- [ ] `ALLOWED_HOSTS` configuré correctement
- [ ] Base de données sécurisée
- [ ] HTTPS activé
- [ ] Mots de passe forts
- [ ] Permissions de fichiers correctes

### Permissions des fichiers
```bash
# Linux/Mac
chmod 755 /path/to/projetimo
chmod 644 /path/to/projetimo/.env
chmod 755 /path/to/projetimo/media
chmod 755 /path/to/projetimo/staticfiles
```

## Monitoring et maintenance

### Logs
```bash
# Vérifier les logs Django
tail -f logs/django.log

# Vérifier les logs système
sudo journalctl -u projetimo
```

### Sauvegardes automatiques
```bash
# Ajouter au crontab
0 2 * * * cd /path/to/projetimo && make backup
```

### Mises à jour
```bash
# Mettre à jour le code
git pull origin master

# Appliquer les migrations
python manage.py migrate

# Redémarrer l'application
sudo systemctl restart projetimo
```

## Dépannage

### Problèmes courants
1. **Erreur de migration** : Vérifier la version de Django et Python
2. **Erreur de permissions** : Vérifier les droits d'accès aux dossiers
3. **Erreur de base de données** : Vérifier la connexion et les migrations
4. **Erreur de fichiers statiques** : Exécuter `collectstatic`

### Support
- Vérifier les logs Django et système
- Consulter la documentation Django
- Ouvrir une issue sur GitHub
- Contacter l'équipe de développement

## Conclusion

Ce guide couvre les étapes essentielles pour déployer ProjetImo sur une nouvelle machine. Pour toute question ou problème, n'hésitez pas à consulter la documentation Django ou à contacter l'équipe de développement.
