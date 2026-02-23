#!/bin/bash
set -e

# Exécuter les migrations
python manage.py migrate --noinput

# Exécuter les commandes de maintenance en arrière-plan pour ne pas bloquer le démarrage
python manage.py mettre_a_jour_statuts_actifs &
python manage.py corriger_statuts_disponibilite &

# Démarrer Gunicorn immédiatement
exec gunicorn gestion_immobiliere.wsgi:application \
    --bind 0.0.0.0:$PORT \
    --timeout 300 \
    --workers 1 \
    --worker-class sync \
    --access-logfile - \
    --error-logfile -

