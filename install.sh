#!/bin/bash

echo "Installation des dependances pour l'application de gestion immobiliere"
echo

# Verifier si Python est installe
if ! command -v python3 &> /dev/null
then
    echo "Python n'est pas installe. Veuillez installer Python 3.8 ou superieur."
    exit 1
fi

# Creer un environnement virtuel
echo "Creation de l'environnement virtuel..."
python3 -m venv venv
if [ $? -ne 0 ]; then
    echo "Erreur lors de la creation de l'environnement virtuel."
    exit 1
fi

# Activer l'environnement virtuel
echo "Activation de l'environnement virtuel..."
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo "Erreur lors de l'activation de l'environnement virtuel."
    exit 1
fi

# Installer les dependances
echo "Installation des dependances..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "Erreur lors de l'installation des dependances."
    exit 1
fi

echo
echo "Installation terminee avec succes !"
echo "Pour activer l'environnement virtuel, executez : source venv/bin/activate"
echo "Pour demarrer l'application, executez : python manage.py runserver"