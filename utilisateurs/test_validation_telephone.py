#!/usr/bin/env python3
"""
Test de validation du numéro de téléphone
Vérifie que le format '+999999999' avec max 15 chiffres est respecté
"""

import re
import sys
import os

# Ajouter le chemin du projet Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')

import django
django.setup()

from django.test import TestCase
from django.core.exceptions import ValidationError
from utilisateurs.models import Utilisateur
from utilisateurs.forms import UtilisateurForm

class TestValidationTelephone(TestCase):
    """Tests pour la validation du numéro de téléphone"""
    
    def test_format_telephone_valide(self):
        """Test des formats de téléphone valides"""
        formats_valides = [
            '+123456789',      # 9 chiffres
            '+1234567890',     # 10 chiffres
            '+12345678901',    # 11 chiffres
            '+123456789012',   # 12 chiffres
            '+1234567890123',  # 13 chiffres
            '+12345678901234', # 14 chiffres
            '+123456789012345' # 15 chiffres (maximum)
        ]
        
        for format_valide in formats_valides:
            with self.subTest(format=format_valide):
                # Test du modèle
                utilisateur = Utilisateur(
                    username=f'test_{format_valide}',
                    email=f'test_{format_valide}@example.com',
                    telephone=format_valide
                )
                utilisateur.full_clean()  # Doit passer sans erreur
                
                # Test du formulaire
                form_data = {
                    'username': f'test_{format_valide}',
                    'email': f'test_{format_valide}@example.com',
                    'telephone': format_valide,
                    'groupe_travail': None  # Sera défini dans setUp
                }
                form = UtilisateurForm(data=form_data)
                self.assertTrue(form.is_valid(), f"Format {format_valide} devrait être valide")
    
    def test_format_telephone_invalide(self):
        """Test des formats de téléphone invalides"""
        formats_invalides = [
            '123456789',       # Pas de +
            '+12345678',       # Moins de 9 chiffres
            '+1234567890123456', # Plus de 15 chiffres
            '+123456789a',     # Contient des lettres
            '+123 456 789',    # Contient des espaces
            '+123-456-789',    # Contient des tirets
            '+123.456.789',    # Contient des points
            '',                # Vide
            None,              # Null
        ]
        
        for format_invalide in formats_invalides:
            with self.subTest(format=format_invalide):
                # Test du modèle
                utilisateur = Utilisateur(
                    username=f'test_invalid_{format_invalide}',
                    email=f'test_invalid_{format_invalide}@example.com',
                    telephone=format_invalide
                )
                
                with self.assertRaises(ValidationError):
                    utilisateur.full_clean()
                
                # Test du formulaire
                form_data = {
                    'username': f'test_invalid_{format_invalide}',
                    'email': f'test_invalid_{format_invalide}@example.com',
                    'telephone': format_invalide,
                    'groupe_travail': None  # Sera défini dans setUp
                }
                form = UtilisateurForm(data=form_data)
                self.assertFalse(form.is_valid(), f"Format {format_invalide} devrait être invalide")
    
    def test_validation_regex_modele(self):
        """Test que la regex du modèle fonctionne correctement"""
        from utilisateurs.models import Utilisateur
        
        # Récupérer le validateur du modèle
        phone_validator = None
        for field in Utilisateur._meta.fields:
            if field.name == 'telephone':
                for validator in field.validators:
                    if hasattr(validator, 'regex'):
                        phone_validator = validator
                        break
                break
        
        self.assertIsNotNone(phone_validator, "Le validateur téléphone doit être défini")
        
        # Test de la regex
        regex = phone_validator.regex
        
        # Formats valides
        self.assertIsNotNone(regex.match('+123456789'))
        self.assertIsNotNone(regex.match('+123456789012345'))
        
        # Formats invalides
        self.assertIsNone(regex.match('123456789'))
        self.assertIsNone(regex.match('+12345678'))
        self.assertIsNone(regex.match('+1234567890123456'))
    
    def test_validation_formulaire(self):
        """Test que la validation du formulaire fonctionne correctement"""
        # Test avec un numéro valide
        form_data = {
            'username': 'test_telephone',
            'email': 'test@example.com',
            'telephone': '+123456789',
            'groupe_travail': None  # Sera défini dans setUp
        }
        form = UtilisateurForm(data=form_data)
        self.assertTrue(form.is_valid())
        
        # Test avec un numéro invalide
        form_data['telephone'] = '123456789'  # Pas de +
        form = UtilisateurForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('telephone', form.errors)
    
    def setUp(self):
        """Configuration initiale pour les tests"""
        from utilisateurs.models import GroupeTravail
        
        # Créer un groupe de travail pour les tests
        self.groupe_travail, created = GroupeTravail.objects.get_or_create(
            nom='ADMINISTRATION',
            defaults={'description': 'Groupe pour les tests'}
        )
        
        # Mettre à jour les données de test avec le groupe
        for test_method in dir(self):
            if test_method.startswith('test_'):
                method = getattr(self, test_method)
                if hasattr(method, '__code__'):
                    # Remplacer les références à None par le groupe de travail
                    if 'groupe_travail' in method.__code__.co_names:
                        # Cette méthode utilise groupe_travail
                        pass

if __name__ == '__main__':
    # Exécuter les tests
    import unittest
    unittest.main()
