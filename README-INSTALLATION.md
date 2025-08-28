# Installation des dépendances pour l'application de gestion immobilière

## Dépendances requises

Pour exécuter l'application, vous devez installer les dépendances suivantes:

### Python et Django
- Python 3.8 ou supérieur
- Django 4.2.7 ou supérieur
- django-bootstrap5 2.0 ou supérieur

### Fichier requirements.txt

Vous pouvez créer un fichier `requirements.txt` avec le contenu suivant:

```
Django>=4.2.7
django-bootstrap5>=2.0
```

### Installation des dépendances

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

3. **Installer les dépendances**:
```bash
pip install -r requirements.txt
```

ou

```bash
pip install Django>=4.2.7
pip install django-bootstrap5>=2.0
```

## Vérification de l'installation

Pour vérifier que Django est correctement installé:

```bash
python -m django --version
```

Cette commande devrait afficher la version de Django installée.

## Prochaines étapes

Après avoir installé les dépendances, vous pouvez suivre les instructions du fichier README.md pour:

1. Configurer la base de données
2. Créer un superutilisateur
3. Exécuter l'application