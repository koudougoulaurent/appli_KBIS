# Makefile pour ProjetImo
# Application de Gestion Immobilière Django

.PHONY: help install run test clean migrate makemigrations shell collectstatic backup restore

# Variables
PYTHON = python
MANAGE = $(PYTHON) manage.py
VENV = venv
PIP = $(VENV)/Scripts/pip  # Windows
# PIP = $(VENV)/bin/pip    # Linux/Mac

# Aide
help:
	@echo "Commandes disponibles:"
	@echo "  install        - Installer les dépendances"
	@echo "  run            - Lancer le serveur de développement"
	@echo "  test           - Lancer les tests"
	@echo "  clean          - Nettoyer les fichiers temporaires"
	@echo "  migrate        - Appliquer les migrations"
	@echo "  makemigrations - Créer de nouvelles migrations"
	@echo "  shell          - Ouvrir le shell Django"
	@echo "  collectstatic  - Collecter les fichiers statiques"
	@echo "  backup         - Sauvegarder la base de données"
	@echo "  restore        - Restaurer la base de données"
	@echo "  superuser      - Créer un superutilisateur"
	@echo "  reset          - Réinitialiser la base de données"

# Installation
install:
	@echo "Création de l'environnement virtuel..."
	$(PYTHON) -m venv $(VENV)
	@echo "Activation de l'environnement virtuel..."
	@echo "Installation des dépendances..."
	$(PIP) install -r requirements.txt
	@echo "Installation terminée!"

# Lancement du serveur
run:
	@echo "Lancement du serveur de développement..."
	$(MANAGE) runserver

# Tests
test:
	@echo "Lancement des tests..."
	$(MANAGE) test

# Nettoyage
clean:
	@echo "Nettoyage des fichiers temporaires..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type f -name "*.log" -delete
	@echo "Nettoyage terminé!"

# Migrations
migrate:
	@echo "Application des migrations..."
	$(MANAGE) migrate

makemigrations:
	@echo "Création de nouvelles migrations..."
	$(MANAGE) makemigrations

# Shell Django
shell:
	@echo "Ouverture du shell Django..."
	$(MANAGE) shell

# Collecte des fichiers statiques
collectstatic:
	@echo "Collecte des fichiers statiques..."
	$(MANAGE) collectstatic --noinput

# Sauvegarde
backup:
	@echo "Sauvegarde de la base de données..."
	@if [ -f db.sqlite3 ]; then \
		cp db.sqlite3 "backups/db_backup_$$(date +%Y%m%d_%H%M%S).sqlite3"; \
		echo "Sauvegarde créée dans backups/"; \
	else \
		echo "Aucune base de données trouvée"; \
	fi

# Restauration
restore:
	@echo "Restauration de la base de données..."
	@if [ -d backups ]; then \
		ls -la backups/*.sqlite3; \
		echo "Entrez le nom du fichier à restaurer:"; \
		read file; \
		cp "backups/$$file" db.sqlite3; \
		echo "Base de données restaurée"; \
	else \
		echo "Aucune sauvegarde trouvée"; \
	fi

# Création d'un superutilisateur
superuser:
	@echo "Création d'un superutilisateur..."
	$(MANAGE) createsuperuser

# Réinitialisation complète
reset:
	@echo "ATTENTION: Cette action va supprimer toutes les données!"
	@echo "Êtes-vous sûr? (y/N)"
	@read -r response; \
	if [ "$$response" = "y" ] || [ "$$response" = "Y" ]; then \
		rm -f db.sqlite3; \
		$(MANAGE) migrate; \
		$(MANAGE) createsuperuser; \
		echo "Base de données réinitialisée"; \
	else \
		echo "Opération annulée"; \
	fi

# Installation en mode développement
install-dev: install
	@echo "Installation des dépendances de développement..."
	$(PIP) install -r requirements.txt[dev]

# Installation en mode production
install-prod: install
	@echo "Installation des dépendances de production..."
	$(PIP) install -r requirements.txt[production]

# Vérification de la sécurité
security-check:
	@echo "Vérification de la sécurité..."
	$(MANAGE) check --deploy

# Validation des modèles
validate:
	@echo "Validation des modèles..."
	$(MANAGE) check

# Documentation
docs:
	@echo "Génération de la documentation..."
	@echo "Documentation disponible dans README.md et CHANGELOG.md"

# Déploiement
deploy: clean collectstatic migrate
	@echo "Déploiement terminé!"

# Sauvegarde complète du projet
backup-full:
	@echo "Sauvegarde complète du projet..."
	@timestamp=$$(date +%Y%m%d_%H%M%S); \
	tar -czf "backups/projetimo_full_$$timestamp.tar.gz" \
		--exclude=venv \
		--exclude=__pycache__ \
		--exclude=*.pyc \
		--exclude=*.log \
		--exclude=media \
		--exclude=staticfiles \
		--exclude=backups \
		--exclude=.git \
		.
	@echo "Sauvegarde complète créée: projetimo_full_$$timestamp.tar.gz"
