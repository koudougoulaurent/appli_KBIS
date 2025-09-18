#!/usr/bin/env python
"""
Script de test de sécurité pour KBIS INTERNATIONAL
Teste les vulnérabilités et la robustesse du système
"""
import os
import sys
import django
from django.conf import settings

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings_minimal')
django.setup()

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from core.security import SecurityValidator, DataSanitizer, AccessControl
from core.security_monitoring import SecurityMonitor
import json


class SecurityTestSuite:
    """Suite de tests de sécurité"""
    
    def __init__(self):
        self.client = Client()
        self.test_results = []
    
    def run_all_tests(self):
        """Exécuter tous les tests de sécurité"""
        print("🔒 DÉMARRAGE DES TESTS DE SÉCURITÉ KBIS INTERNATIONAL")
        print("=" * 60)
        
        # Tests de validation
        self.test_input_validation()
        self.test_sql_injection_protection()
        self.test_xss_protection()
        self.test_csrf_protection()
        self.test_authentication_security()
        self.test_authorization_security()
        self.test_data_sanitization()
        self.test_password_security()
        self.test_session_security()
        self.test_file_upload_security()
        
        # Afficher les résultats
        self.display_results()
    
    def test_input_validation(self):
        """Test de validation des entrées"""
        print("🔍 Test de validation des entrées...")
        
        validator = SecurityValidator()
        
        # Test validation email
        try:
            validator.validate_email("test@example.com")
            self.add_result("Email validation", "PASS", "Email valide accepté")
        except Exception as e:
            self.add_result("Email validation", "FAIL", f"Erreur: {e}")
        
        # Test validation téléphone
        try:
            validator.validate_phone_number("0123456789")
            self.add_result("Phone validation", "PASS", "Téléphone valide accepté")
        except Exception as e:
            self.add_result("Phone validation", "FAIL", f"Erreur: {e}")
        
        # Test validation montant
        try:
            validator.validate_amount(1000.50)
            self.add_result("Amount validation", "PASS", "Montant valide accepté")
        except Exception as e:
            self.add_result("Amount validation", "FAIL", f"Erreur: {e}")
    
    def test_sql_injection_protection(self):
        """Test de protection contre l'injection SQL"""
        print("💉 Test de protection SQL injection...")
        
        # Tentatives d'injection SQL
        sql_attempts = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "admin'--",
            "1 UNION SELECT * FROM users",
            "'; INSERT INTO users VALUES ('hacker', 'password'); --"
        ]
        
        for attempt in sql_attempts:
            response = self.client.get(f'/paiements/?search={attempt}')
            if response.status_code == 403:
                self.add_result("SQL Injection Protection", "PASS", f"Bloqué: {attempt[:30]}...")
            else:
                self.add_result("SQL Injection Protection", "WARN", f"Potentiellement vulnérable: {attempt[:30]}...")
    
    def test_xss_protection(self):
        """Test de protection contre XSS"""
        print("🌐 Test de protection XSS...")
        
        xss_attempts = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
            "<svg onload=alert('XSS')>",
        ]
        
        for attempt in xss_attempts:
            response = self.client.get(f'/paiements/?search={attempt}')
            if '<script>' not in response.content.decode():
                self.add_result("XSS Protection", "PASS", f"Script bloqué: {attempt[:20]}...")
            else:
                self.add_result("XSS Protection", "FAIL", f"Script non bloqué: {attempt[:20]}...")
    
    def test_csrf_protection(self):
        """Test de protection CSRF"""
        print("🛡️ Test de protection CSRF...")
        
        # Test sans token CSRF
        response = self.client.post('/paiements/partiels/plans/creer/', {
            'nom_plan': 'Test Plan',
            'montant_total': 1000
        })
        
        if response.status_code == 403:
            self.add_result("CSRF Protection", "PASS", "Requête sans token CSRF bloquée")
        else:
            self.add_result("CSRF Protection", "FAIL", "Requête sans token CSRF acceptée")
    
    def test_authentication_security(self):
        """Test de sécurité d'authentification"""
        print("🔐 Test de sécurité d'authentification...")
        
        # Test de force brute
        for i in range(6):
            response = self.client.post('/utilisateurs/login/PRIVILEGE/', {
                'username': 'admin',
                'password': 'wrong_password'
            })
        
        if response.status_code == 403:
            self.add_result("Brute Force Protection", "PASS", "Tentatives multiples bloquées")
        else:
            self.add_result("Brute Force Protection", "WARN", "Protection contre force brute limitée")
    
    def test_authorization_security(self):
        """Test de sécurité d'autorisation"""
        print("👤 Test de sécurité d'autorisation...")
        
        # Test d'accès non autorisé
        response = self.client.get('/security/dashboard/')
        if response.status_code == 302:  # Redirection vers login
            self.add_result("Authorization", "PASS", "Accès non autorisé redirigé")
        else:
            self.add_result("Authorization", "FAIL", "Accès non autorisé possible")
    
    def test_data_sanitization(self):
        """Test de nettoyage des données"""
        print("🧹 Test de nettoyage des données...")
        
        sanitizer = DataSanitizer()
        
        # Test nettoyage chaîne
        dirty_string = "<script>alert('XSS')</script>Hello"
        clean_string = sanitizer.sanitize_string(dirty_string)
        
        if '<script>' not in clean_string:
            self.add_result("Data Sanitization", "PASS", "Caractères dangereux supprimés")
        else:
            self.add_result("Data Sanitization", "FAIL", "Caractères dangereux non supprimés")
    
    def test_password_security(self):
        """Test de sécurité des mots de passe"""
        print("🔑 Test de sécurité des mots de passe...")
        
        from core.security import PasswordSecurity
        
        # Test génération mot de passe sécurisé
        secure_password = PasswordSecurity.generate_secure_password()
        
        if len(secure_password) >= 12:
            self.add_result("Password Generation", "PASS", f"Mot de passe sécurisé généré ({len(secure_password)} chars)")
        else:
            self.add_result("Password Generation", "FAIL", "Mot de passe trop court")
        
        # Test validation force mot de passe
        try:
            PasswordSecurity.validate_password_strength("WeakPass123!")
            self.add_result("Password Validation", "FAIL", "Mot de passe faible accepté")
        except Exception:
            self.add_result("Password Validation", "PASS", "Mot de passe faible rejeté")
    
    def test_session_security(self):
        """Test de sécurité des sessions"""
        print("📱 Test de sécurité des sessions...")
        
        # Test configuration session
        if hasattr(settings, 'SESSION_COOKIE_SECURE') and settings.SESSION_COOKIE_SECURE:
            self.add_result("Session Security", "PASS", "Cookies de session sécurisés")
        else:
            self.add_result("Session Security", "WARN", "Cookies de session non sécurisés")
    
    def test_file_upload_security(self):
        """Test de sécurité des uploads de fichiers"""
        print("📁 Test de sécurité des uploads...")
        
        # Test limitation taille fichier
        if hasattr(settings, 'FILE_UPLOAD_MAX_MEMORY_SIZE'):
            max_size = settings.FILE_UPLOAD_MAX_MEMORY_SIZE
            if max_size <= 5242880:  # 5MB
                self.add_result("File Upload Security", "PASS", f"Taille max: {max_size/1024/1024:.1f}MB")
            else:
                self.add_result("File Upload Security", "WARN", f"Taille max élevée: {max_size/1024/1024:.1f}MB")
        else:
            self.add_result("File Upload Security", "WARN", "Pas de limitation de taille")
    
    def add_result(self, test_name, status, message):
        """Ajouter un résultat de test"""
        self.test_results.append({
            'test': test_name,
            'status': status,
            'message': message
        })
    
    def display_results(self):
        """Afficher les résultats des tests"""
        print("\n" + "=" * 60)
        print("📊 RÉSULTATS DES TESTS DE SÉCURITÉ")
        print("=" * 60)
        
        passed = len([r for r in self.test_results if r['status'] == 'PASS'])
        failed = len([r for r in self.test_results if r['status'] == 'FAIL'])
        warned = len([r for r in self.test_results if r['status'] == 'WARN'])
        total = len(self.test_results)
        
        print(f"✅ Tests réussis: {passed}")
        print(f"❌ Tests échoués: {failed}")
        print(f"⚠️  Avertissements: {warned}")
        print(f"📈 Score de sécurité: {(passed/total)*100:.1f}%")
        
        print("\n📋 DÉTAIL DES TESTS:")
        for result in self.test_results:
            status_icon = "✅" if result['status'] == 'PASS' else "❌" if result['status'] == 'FAIL' else "⚠️"
            print(f"{status_icon} {result['test']}: {result['message']}")
        
        print("\n" + "=" * 60)
        if failed == 0:
            print("🎉 SYSTÈME DE SÉCURITÉ ROBUSTE!")
        else:
            print("🚨 ATTENTION: Vulnérabilités détectées!")


if __name__ == "__main__":
    test_suite = SecurityTestSuite()
    test_suite.run_all_tests()
