#!/usr/bin/env python
"""
Test simple pour isoler le problème de validation
"""

import os
import sys
import django
from django.test import TestCase
from django.contrib.auth import get_user_model

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from proprietes.forms import BailleurForm

Utilisateur = get_user_model()


def test_bailleur_form():
    """Test simple du formulaire bailleur"""
    print("🔍 Test simple du formulaire bailleur...")
    
    # Données de test valides
    form_data = {
        'nom': 'Doe',
        'prenom': 'John',
        'email': 'john.doe@example.com',
        'telephone': '01 23 45 67 89',
        'adresse': '123 Rue de la Paix, 75001 Paris',
        'profession': 'Ingénieur',
        'entreprise': 'Tech Corp',
        'iban': 'FR7630006000011234567890189',
        'bic': 'BNPAFRPPXXX',
        'notes': 'Notes importantes'
    }
    
    try:
        form = BailleurForm(data=form_data)
        if form.is_valid():
            print("✅ Formulaire valide")
            print(f"Données nettoyées: {form.cleaned_data}")
        else:
            print("❌ Formulaire invalide")
            print(f"Erreurs: {form.errors}")
    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    test_bailleur_form() 