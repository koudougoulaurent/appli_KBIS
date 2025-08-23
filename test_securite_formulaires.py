#!/usr/bin/env python
"""
Script de test pour vérifier la sécurité des formulaires et la sauvegarde des données
"""

import os
import sys
import django
from datetime import datetime, timedelta

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import transaction
from proprietes.models import Bailleur, Locataire, Propriete, TypeBien
from proprietes.forms import BailleurForm, LocataireForm, ProprieteForm
from core.save_handlers import DataSaveHandler
from core.validators import SecurityValidator, DataSanitizer, SecurityChecks

Utilisateur = get_user_model()


class SecurityTestSuite:
    """Suite de tests de sécurité pour les formulaires"""
    
    def __init__(self):
        self.client = Client()
        self.test_user = None
        self.results = {
            'passed': 0,
            'failed': 0,
            'errors': []
        }
    
    def run_all_tests(self):
        """Exécuter tous les tests de sécurité"""
        
        print("🔒 TESTS DE SÉCURITÉ DES FORMULAIRES")
        print("=" * 60)
        
        # Créer un utilisateur de test
        self._create_test_user()
        
        # Tests de validation des données
        self._test_data_validation()
        
        # Tests de sécurité des formulaires
        self._test_form_security()
        
        # Tests de sauvegarde des données
        self._test_data_save()
        
        # Tests de nettoyage des données
        self._test_data_sanitization()
        
        # Tests de protection contre les attaques
        self._test_attack_protection()
        
        # Afficher les résultats
        self._print_results()
    
    def _create_test_user(self):
        """Créer un utilisateur de test"""
        try:
            self.test_user, created = Utilisateur.objects.get_or_create(
                username='test_security',
                defaults={
                    'email': 'test@security.com',
                    'first_name': 'Test',
                    'last_name': 'Security',
                    'is_staff': True,
                    'is_superuser': True
                }
            )
            if created:
                self.test_user.set_password('testpass123')
                self.test_user.save()
                print("✅ Utilisateur de test créé")
            else:
                print("✅ Utilisateur de test existant")
        except Exception as e:
            print(f"❌ Erreur création utilisateur: {e}")
    
    def _test_data_validation(self):
        """Tester la validation des données"""
        
        print("\n📋 Tests de validation des données")
        print("-" * 40)
        
        # Test validation téléphone
        self._test_phone_validation()
        
        # Test validation email
        self._test_email_validation()
        
        # Test validation code postal
        self._test_postal_code_validation()
        
        # Test validation IBAN
        self._test_iban_validation()
        
        # Test validation montants
        self._test_amount_validation()
    
    def _test_phone_validation(self):
        """Tester la validation des téléphones"""
        
        test_cases = [
            ("01 23 45 67 89", True, "Téléphone français valide"),
            ("+33 1 23 45 67 89", True, "Téléphone français avec indicatif"),
            ("0123456789", True, "Téléphone sans espaces"),
            ("123", False, "Téléphone trop court"),
            ("abc", False, "Téléphone avec lettres"),
            ("01 23 45 67 89 00 00", False, "Téléphone trop long"),
        ]
        
        for phone, expected, description in test_cases:
            try:
                result = SecurityValidator.validate_phone_number(phone)
                if expected:
                    print(f"✅ {description}")
                    self.results['passed'] += 1
                else:
                    print(f"❌ {description} - Devrait échouer")
                    self.results['failed'] += 1
            except ValidationError:
                if not expected:
                    print(f"✅ {description} - Échec attendu")
                    self.results['passed'] += 1
                else:
                    print(f"❌ {description} - Échec inattendu")
                    self.results['failed'] += 1
    
    def _test_email_validation(self):
        """Tester la validation des emails"""
        
        test_cases = [
            ("test@example.com", True, "Email valide"),
            ("test.email@domain.co.uk", True, "Email avec sous-domaine"),
            ("test+tag@example.com", True, "Email avec tag"),
            ("invalid-email", False, "Email invalide"),
            ("test@", False, "Email incomplet"),
            ("@example.com", False, "Email sans nom"),
        ]
        
        for email, expected, description in test_cases:
            try:
                result = DataSanitizer.sanitize_email(email)
                if expected:
                    print(f"✅ {description}")
                    self.results['passed'] += 1
                else:
                    print(f"❌ {description} - Devrait échouer")
                    self.results['failed'] += 1
            except Exception:
                if not expected:
                    print(f"✅ {description} - Échec attendu")
                    self.results['passed'] += 1
                else:
                    print(f"❌ {description} - Échec inattendu")
                    self.results['failed'] += 1
    
    def _test_postal_code_validation(self):
        """Tester la validation des codes postaux"""
        
        test_cases = [
            ("75001", True, "Code postal valide"),
            ("12345", True, "Code postal valide"),
            ("1234", False, "Code postal trop court"),
            ("123456", False, "Code postal trop long"),
            ("abc12", False, "Code postal avec lettres"),
            ("12 345", True, "Code postal avec espace"),
        ]
        
        for postal, expected, description in test_cases:
            try:
                result = SecurityValidator.validate_postal_code(postal)
                if expected:
                    print(f"✅ {description}")
                    self.results['passed'] += 1
                else:
                    print(f"❌ {description} - Devrait échouer")
                    self.results['failed'] += 1
            except ValidationError:
                if not expected:
                    print(f"✅ {description} - Échec attendu")
                    self.results['passed'] += 1
                else:
                    print(f"❌ {description} - Échec inattendu")
                    self.results['failed'] += 1
    
    def _test_iban_validation(self):
        """Tester la validation des IBAN"""
        
        test_cases = [
            ("FR7630006000011234567890189", True, "IBAN français valide"),
            ("DE89370400440532013000", True, "IBAN allemand valide"),
            ("123", False, "IBAN trop court"),
            ("FR7630006000011234567890189XX", False, "IBAN français invalide"),
        ]
        
        for iban, expected, description in test_cases:
            try:
                result = SecurityValidator.validate_iban(iban)
                if expected:
                    print(f"✅ {description}")
                    self.results['passed'] += 1
                else:
                    print(f"❌ {description} - Devrait échouer")
                    self.results['failed'] += 1
            except ValidationError:
                if not expected:
                    print(f"✅ {description} - Échec attendu")
                    self.results['passed'] += 1
                else:
                    print(f"❌ {description} - Échec inattendu")
                    self.results['failed'] += 1
    
    def _test_amount_validation(self):
        """Tester la validation des montants"""
        
        test_cases = [
            (100.50, True, "Montant positif"),
            (0, True, "Montant nul"),
            (-10, False, "Montant négatif"),
            (999999999.99, True, "Montant maximum"),
            (1000000000, False, "Montant trop élevé"),
        ]
        
        for amount, expected, description in test_cases:
            try:
                result = SecurityValidator.validate_amount(amount)
                if expected:
                    print(f"✅ {description}")
                    self.results['passed'] += 1
                else:
                    print(f"❌ {description} - Devrait échouer")
                    self.results['failed'] += 1
            except ValidationError:
                if not expected:
                    print(f"✅ {description} - Échec attendu")
                    self.results['passed'] += 1
                else:
                    print(f"❌ {description} - Échec inattendu")
                    self.results['failed'] += 1
    
    def _test_form_security(self):
        """Tester la sécurité des formulaires"""
        
        print("\n🛡️ Tests de sécurité des formulaires")
        print("-" * 40)
        
        # Test formulaire bailleur
        self._test_bailleur_form_security()
        
        # Test formulaire locataire
        self._test_locataire_form_security()
        
        # Test formulaire propriété
        self._test_propriete_form_security()
    
    def _test_bailleur_form_security(self):
        """Tester la sécurité du formulaire bailleur"""
        
        # Données valides
        valid_data = {
            'nom': 'Dupont',
            'prenom': 'Jean',
            'email': 'jean.dupont@example.com',
            'telephone': '01 23 45 67 89',
            'adresse': '123 Rue de la Paix, 75001 Paris',
        }
        
        form = BailleurForm(data=valid_data)
        if form.is_valid():
            print("✅ Formulaire bailleur - données valides")
            self.results['passed'] += 1
        else:
            print(f"❌ Formulaire bailleur - données valides: {form.errors}")
            self.results['failed'] += 1
        
        # Données invalides (injection SQL)
        invalid_data = valid_data.copy()
        invalid_data['nom'] = "'; DROP TABLE proprietes_bailleur; --"
        
        form = BailleurForm(data=invalid_data)
        if not form.is_valid():
            print("✅ Formulaire bailleur - injection SQL détectée")
            self.results['passed'] += 1
        else:
            print("❌ Formulaire bailleur - injection SQL non détectée")
            self.results['failed'] += 1
    
    def _test_locataire_form_security(self):
        """Tester la sécurité du formulaire locataire"""
        
        # Données valides
        valid_data = {
            'nom': 'Martin',
            'prenom': 'Marie',
            'email': 'marie.martin@example.com',
            'telephone': '01 98 76 54 32',
            'adresse_actuelle': '456 Avenue des Champs, 75008 Paris',
        }
        
        form = LocataireForm(data=valid_data)
        if form.is_valid():
            print("✅ Formulaire locataire - données valides")
            self.results['passed'] += 1
        else:
            print(f"❌ Formulaire locataire - données valides: {form.errors}")
            self.results['failed'] += 1
    
    def _test_propriete_form_security(self):
        """Tester la sécurité du formulaire propriété"""
        
        # Créer un type de bien pour le test
        type_bien, created = TypeBien.objects.get_or_create(
            nom='Appartement',
            defaults={'description': 'Appartement standard'}
        )
        
        # Créer un bailleur pour le test
        bailleur, created = Bailleur.objects.get_or_create(
            nom='Test',
            prenom='Bailleur',
            email='test.bailleur@example.com',
            defaults={
                'telephone': '01 11 11 11 11',
                'adresse': 'Test',
            }
        )
        
        # Données valides
        valid_data = {
            'titre': 'Appartement Test',
            'adresse': '789 Boulevard Test',
            'ville': 'Paris',
            'code_postal': '75016',
            'pays': 'France',
            'surface': 75.5,
            'nombre_pieces': 4,
            'nombre_chambres': 2,
            'nombre_salles_bain': 1,
            'loyer_actuel': 1200.00,
            'charges': 150.00,
            'etat': 'bon',
            'bailleur': bailleur.id,
            'type_bien': type_bien.id,
        }
        
        form = ProprieteForm(data=valid_data)
        if form.is_valid():
            print("✅ Formulaire propriété - données valides")
            self.results['passed'] += 1
        else:
            print(f"❌ Formulaire propriété - données valides: {form.errors}")
            self.results['failed'] += 1
    
    def _test_data_save(self):
        """Tester la sauvegarde des données"""
        
        print("\n💾 Tests de sauvegarde des données")
        print("-" * 40)
        
        # Test sauvegarde bailleur
        self._test_bailleur_save()
        
        # Test sauvegarde locataire
        self._test_locataire_save()
        
        # Test sauvegarde propriété
        self._test_propriete_save()
    
    def _test_bailleur_save(self):
        """Tester la sauvegarde d'un bailleur"""
        
        bailleur_data = {
            'nom': 'Test',
            'prenom': 'Sauvegarde',
            'email': 'test.sauvegarde@example.com',
            'telephone': '01 22 33 44 55',
            'adresse': 'Test Adresse',
        }
        
        try:
            bailleur, success, message = DataSaveHandler.save_bailleur(bailleur_data, self.test_user)
            if success and bailleur:
                print("✅ Sauvegarde bailleur réussie")
                self.results['passed'] += 1
                
                # Vérifier que les données sont bien sauvegardées
                saved_bailleur = Bailleur.objects.get(pk=bailleur.pk)
                if (saved_bailleur.nom == bailleur_data['nom'] and 
                    saved_bailleur.prenom == bailleur_data['prenom']):
                    print("✅ Données bailleur correctement sauvegardées")
                    self.results['passed'] += 1
                else:
                    print("❌ Données bailleur mal sauvegardées")
                    self.results['failed'] += 1
            else:
                print(f"❌ Sauvegarde bailleur échouée: {message}")
                self.results['failed'] += 1
        except Exception as e:
            print(f"❌ Erreur sauvegarde bailleur: {e}")
            self.results['failed'] += 1
    
    def _test_locataire_save(self):
        """Tester la sauvegarde d'un locataire"""
        
        locataire_data = {
            'nom': 'Test',
            'prenom': 'Locataire',
            'email': 'test.locataire@example.com',
            'telephone': '01 33 44 55 66',
            'adresse_actuelle': 'Test Adresse Locataire',
        }
        
        try:
            locataire, success, message = DataSaveHandler.save_locataire(locataire_data, self.test_user)
            if success and locataire:
                print("✅ Sauvegarde locataire réussie")
                self.results['passed'] += 1
            else:
                print(f"❌ Sauvegarde locataire échouée: {message}")
                self.results['failed'] += 1
        except Exception as e:
            print(f"❌ Erreur sauvegarde locataire: {e}")
            self.results['failed'] += 1
    
    def _test_propriete_save(self):
        """Tester la sauvegarde d'une propriété"""
        
        # Créer un type de bien et un bailleur pour le test
        type_bien, created = TypeBien.objects.get_or_create(
            nom='Test Bien',
            defaults={'description': 'Bien de test'}
        )
        
        bailleur, created = Bailleur.objects.get_or_create(
            nom='Test',
            prenom='Propriétaire',
            email='test.proprietaire@example.com',
            defaults={
                'telephone': '01 44 55 66 77',
                'adresse': 'Test',
            }
        )
        
        propriete_data = {
            'titre': 'Propriété Test',
            'adresse': 'Test Adresse Propriété',
            'ville': 'Paris',
            'code_postal': '75003',
            'pays': 'France',
            'surface': 80.0,
            'nombre_pieces': 3,
            'nombre_chambres': 2,
            'nombre_salles_bain': 1,
            'loyer_actuel': 1500.00,
            'charges': 200.00,
            'etat': 'bon',
            'bailleur': bailleur,
            'type_bien': type_bien,
        }
        
        try:
            propriete, success, message = DataSaveHandler.save_propriete(propriete_data, self.test_user)
            if success and propriete:
                print("✅ Sauvegarde propriété réussie")
                self.results['passed'] += 1
            else:
                print(f"❌ Sauvegarde propriété échouée: {message}")
                self.results['failed'] += 1
        except Exception as e:
            print(f"❌ Erreur sauvegarde propriété: {e}")
            self.results['failed'] += 1
    
    def _test_data_sanitization(self):
        """Tester le nettoyage des données"""
        
        print("\n🧹 Tests de nettoyage des données")
        print("-" * 40)
        
        # Test nettoyage texte
        dirty_text = "  Test   avec   espaces   multiples  "
        clean_text = DataSanitizer.sanitize_text(dirty_text)
        if clean_text == "Test avec espaces multiples":
            print("✅ Nettoyage texte réussi")
            self.results['passed'] += 1
        else:
            print("❌ Nettoyage texte échoué")
            self.results['failed'] += 1
        
        # Test nettoyage email
        dirty_email = "  TEST@EXAMPLE.COM  "
        clean_email = DataSanitizer.sanitize_email(dirty_email)
        if clean_email == "test@example.com":
            print("✅ Nettoyage email réussi")
            self.results['passed'] += 1
        else:
            print("❌ Nettoyage email échoué")
            self.results['failed'] += 1
        
        # Test nettoyage téléphone
        dirty_phone = "  01  23  45  67  89  "
        clean_phone = DataSanitizer.sanitize_phone(dirty_phone)
        if clean_phone == "01 23 45 67 89":
            print("✅ Nettoyage téléphone réussi")
            self.results['passed'] += 1
        else:
            print("❌ Nettoyage téléphone échoué")
            self.results['failed'] += 1
    
    def _test_attack_protection(self):
        """Tester la protection contre les attaques"""
        
        print("\n🛡️ Tests de protection contre les attaques")
        print("-" * 40)
        
        # Test protection injection SQL
        sql_attack = "'; DROP TABLE proprietes_bailleur; --"
        if not SecurityChecks.check_sql_injection(sql_attack):
            print("✅ Protection injection SQL active")
            self.results['passed'] += 1
        else:
            print("❌ Protection injection SQL inactive")
            self.results['failed'] += 1
        
        # Test protection XSS
        xss_attack = "<script>alert('XSS')</script>"
        if not SecurityChecks.check_xss_attack(xss_attack):
            print("✅ Protection XSS active")
            self.results['passed'] += 1
        else:
            print("❌ Protection XSS inactive")
            self.results['failed'] += 1
        
        # Test protection injection commande
        cmd_attack = "ls; rm -rf /"
        if not SecurityChecks.check_command_injection(cmd_attack):
            print("✅ Protection injection commande active")
            self.results['passed'] += 1
        else:
            print("❌ Protection injection commande inactive")
            self.results['failed'] += 1
    
    def _print_results(self):
        """Afficher les résultats des tests"""
        
        print("\n" + "=" * 60)
        print("📊 RÉSULTATS DES TESTS DE SÉCURITÉ")
        print("=" * 60)
        print(f"✅ Tests réussis: {self.results['passed']}")
        print(f"❌ Tests échoués: {self.results['failed']}")
        
        total = self.results['passed'] + self.results['failed']
        if total > 0:
            success_rate = (self.results['passed'] / total) * 100
            print(f"📈 Taux de réussite: {success_rate:.1f}%")
        
        if self.results['failed'] == 0:
            print("\n🎉 Tous les tests de sécurité sont passés !")
        else:
            print(f"\n⚠️ {self.results['failed']} test(s) ont échoué.")
        
        print("\n" + "=" * 60)


def main():
    """Fonction principale"""
    
    print("🚀 Démarrage des tests de sécurité des formulaires")
    print("=" * 60)
    
    # Créer et exécuter la suite de tests
    test_suite = SecurityTestSuite()
    test_suite.run_all_tests()


if __name__ == '__main__':
    main() 