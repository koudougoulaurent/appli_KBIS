#!/bin/bash

echo "Demarrage de l'application de gestion immobiliere"
echo

# Verifier si l'environnement virtuel existe
if [ ! -f "venv/bin/activate" ]; then
    echo "L'environnement virtuel n'existe pas. Veuillez d'abord executer install.sh"
    exit 1
fi

# Activer l'environnement virtuel
echo "Activation de l'environnement virtuel..."
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo "Erreur lors de l'activation de l'environnement virtuel."
    exit 1
fi

# Demarrer l'application
echo "Demarrage de l'application..."
python manage.py runserver
if [ $? -ne 0 ]; then
    echo "Erreur lors du demarrage de l'application."
    exit 1
fi

echo
echo "L'application est maintenant accessible a l'adresse http://127.0.0.1:8000/"