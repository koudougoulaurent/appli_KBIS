web: python manage.py migrate && python manage.py mettre_a_jour_statuts_actifs && python manage.py corriger_statuts_disponibilite && gunicorn --bind 0.0.0.0:$PORT app:app
