#!/bin/bash 
echo Deploiement sur LWS... 
pip install -r requirements_production.txt --user 
python manage.py makemigrations 
python manage.py migrate 
python manage.py collectstatic --noinput 
python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('admin', 'admin@example.com', 'admin123') if not User.objects.filter(username='admin').exists() else None" 
echo Deploiement termine! 
