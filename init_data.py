#!/usr/bin/env python
"""
Script d'initialisation des données de base
"""
import os
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from contrats.models import TypeContrat
from paiements.models import TypePaiement

def init_types_contrats():
    """Initialise les types de contrats de base"""
    types = [
        {
            'nom': 'Bail résidentiel',
            'description': 'Contrat de location pour résidence principale',
            'duree_min_mois': 12,
            'duree_max_mois': 36,
            'caution_requise': True,
            'charges_comprises': False,
        },
        {
            'nom': 'Bail meublé',
            'description': 'Contrat de location avec meubles',
            'duree_min_mois': 12,
            'duree_max_mois': 36,
            'caution_requise': True,
            'charges_comprises': True,
        },
        {
            'nom': 'Location saisonnière',
            'description': 'Location courte durée (vacances)',
            'duree_min_mois': 1,
            'duree_max_mois': 6,
            'caution_requise': True,
            'charges_comprises': True,
        },
        {
            'nom': 'Bail commercial',
            'description': 'Contrat de location pour activité commerciale',
            'duree_min_mois': 24,
            'duree_max_mois': 60,
            'caution_requise': True,
            'charges_comprises': False,
        },
    ]
    
    for type_data in types:
        TypeContrat.objects.get_or_create(
            nom=type_data['nom'],
            defaults=type_data
        )
        print(f"Type de contrat créé : {type_data['nom']}")

def init_types_paiements():
    """Initialise les types de paiements de base"""
    types = [
        {
            'nom': 'Loyer',
            'description': 'Paiement du loyer mensuel',
            'est_recurrent': True,
            'est_remboursable': False,
            'couleur': '#007bff',
        },
        {
            'nom': 'Charges',
            'description': 'Paiement des charges locatives',
            'est_recurrent': True,
            'est_remboursable': False,
            'couleur': '#28a745',
        },
        {
            'nom': 'Caution',
            'description': 'Dépôt de garantie',
            'est_recurrent': False,
            'est_remboursable': True,
            'couleur': '#ffc107',
        },
        {
            'nom': 'Frais d\'agence',
            'description': 'Frais de gestion et d\'agence',
            'est_recurrent': False,
            'est_remboursable': False,
            'couleur': '#dc3545',
        },
        {
            'nom': 'Régularisation',
            'description': 'Régularisation de charges',
            'est_recurrent': False,
            'est_remboursable': True,
            'couleur': '#6c757d',
        },
    ]
    
    for type_data in types:
        TypePaiement.objects.get_or_create(
            nom=type_data['nom'],
            defaults=type_data
        )
        print(f"Type de paiement créé : {type_data['nom']}")

if __name__ == '__main__':
    print("Initialisation des données de base...")
    
    print("\n1. Création des types de contrats...")
    init_types_contrats()
    
    print("\n2. Création des types de paiements...")
    init_types_paiements()
    
    print("\nInitialisation terminée avec succès !") 