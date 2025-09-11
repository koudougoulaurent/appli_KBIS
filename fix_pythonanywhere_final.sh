#!/bin/bash

echo "=== CORRECTION FINALE POUR PYTHONANYWHERE ==="
echo "Installation de tous les packages manquants..."

# Activer l'environnement virtuel
source ~/.virtualenvs/mv/bin/activate

# Installer tous les packages manquants
echo "Installation des packages manquants..."
pip install django-filter
pip install django-select2
pip install django-bootstrap5
pip install django-crispy-forms
pip install crispy-bootstrap5
pip install djangorestframework
pip install reportlab
pip install xhtml2pdf
pip install Pillow
pip install django-extensions
pip install whitenoise
pip install django-cors-headers
pip install django-environ
pip install python-decouple
pip install python-dotenv
pip install fonttools
pip install PyPDF2

echo "Vérification de l'installation..."
pip list | grep -E "(django-filter|django-select2|django-bootstrap5|django-crispy-forms|crispy-bootstrap5|djangorestframework|reportlab|xhtml2pdf|Pillow|django-extensions|whitenoise|django-cors-headers|django-environ|python-decouple|python-dotenv|fonttools|PyPDF2)"

echo "Création du répertoire de logs..."
mkdir -p logs

echo "Vérification de la configuration Django..."
python manage.py check

echo "Application des migrations..."
python manage.py makemigrations
python manage.py migrate

echo "Collecte des fichiers statiques..."
python manage.py collectstatic --noinput

echo "Création du superutilisateur..."
echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('admin', 'admin@example.com', 'admin123') if not User.objects.filter(username='admin').exists() else print('Superutilisateur existe déjà')" | python manage.py shell

echo "Test final..."
python manage.py check --deploy

echo "=== CORRECTION TERMINÉE ==="
echo "Votre application devrait maintenant fonctionner sur PythonAnywhere !"