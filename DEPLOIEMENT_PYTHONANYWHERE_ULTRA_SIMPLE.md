# 🚀 Déploiement Ultra-Simple sur PythonAnywhere

## ⚡ Commandes à Exécuter (Copier-Coller)

### 1. **Sur PythonAnywhere, dans le Bash Console :**

```bash
# Aller dans votre projet
cd /home/laurenzo/appli_KBIS

# Rendre le script exécutable
chmod +x fix_pythonanywhere.sh

# Exécuter le script de correction
./fix_pythonanywhere.sh
```

### 2. **Si le script ne fonctionne pas, exécutez ces commandes une par une :**

```bash
# Installer les packages essentiels
pip install Django>=4.2.7,<5.0
pip install django-bootstrap5>=2.0
pip install django-crispy-forms>=2.0
pip install crispy-bootstrap5>=0.7
pip install djangorestframework>=3.14.0
pip install reportlab>=4.0.0
pip install xhtml2pdf>=0.2.5
pip install Pillow>=10.0.0
pip install whitenoise>=6.5.0
pip install django-extensions>=3.2.0
pip install django-cors-headers>=4.0.0
pip install django-environ>=0.10.0
pip install python-decouple>=3.8
pip install python-dotenv>=1.0.0
pip install fonttools>=4.0.0
pip install PyPDF2>=3.0.0

# Migrations
python manage.py makemigrations
python manage.py migrate

# Fichiers statiques
python manage.py collectstatic --noinput

# Superutilisateur
python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('admin', 'admin@example.com', 'admin123') if not User.objects.filter(username='admin').exists() else None"
```

### 3. **Configuration WSGI sur PythonAnywhere :**

1. Allez dans l'onglet **Web** de PythonAnywhere
2. Cliquez sur **WSGI configuration file**
3. Remplacez tout le contenu par :

```python
import os
import sys

path = '/home/laurenzo/appli_KBIS'
if path not in sys.path:
    sys.path.append(path)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

### 4. **Configuration des fichiers statiques :**

Dans l'onglet **Web** de PythonAnywhere :

- **Static files**: `/static/` → `/home/laurenzo/appli_KBIS/staticfiles/`
- **Media files**: `/media/` → `/home/laurenzo/appli_KBIS/media/`

### 5. **Redémarrer l'application :**

Cliquez sur le bouton **Reload** dans l'onglet Web.

## 🎉 C'est Tout !

Votre application sera accessible sur : `https://laurenzo.pythonanywhere.com`

- **Interface admin** : `https://laurenzo.pythonanywhere.com/admin/`
- **Connexion** : `admin` / `admin123`

## 🔧 En Cas de Problème

Si vous avez encore des erreurs, exécutez :

```bash
# Vérifier la configuration
python manage.py check

# Vérifier les packages installés
pip list | grep -i django

# Tester l'application
python manage.py runserver 0.0.0.0:8000
```

## 📞 Support

Si ça ne marche toujours pas, vérifiez :
1. Que vous êtes dans le bon répertoire (`/home/laurenzo/appli_KBIS`)
2. Que tous les packages sont installés (`pip list`)
3. Que les migrations sont appliquées (`python manage.py showmigrations`)
4. Que les fichiers statiques sont collectés (`ls staticfiles/`)

---

**Note** : Ce guide est optimisé pour votre configuration spécifique sur PythonAnywhere.
