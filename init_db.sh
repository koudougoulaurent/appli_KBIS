#!/bin/bash

echo "Initialisation de la base de donnees et creation du superutilisateur"
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

# Executer le script d'initialisation
echo "Execution du script d'initialisation..."
python init_db.py
if [ $? -ne 0 ]; then
    echo "Erreur lors de l'execution du script d'initialisation."
    exit 1
fi

echo
echo "Initialisation terminee avec succes !"