#!/usr/bin/env python
"""
Rapport de sécurité pour KBIS IMMOBILIER
Analyse de la configuration de sécurité
"""
import os
import sys
import django
from django.conf import settings

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings_minimal')
django.setup()

def generate_security_report():
    """Générer un rapport de sécurité"""
    print("🔒 RAPPORT DE SÉCURITÉ KBIS IMMOBILIER")
    print("=" * 60)
    
    # Vérifications de base
    checks = []
    
    # 1. Configuration HTTPS
    if hasattr(settings, 'SECURE_SSL_REDIRECT') and settings.SECURE_SSL_REDIRECT:
        checks.append(("HTTPS Redirection", "✅", "Activée"))
    else:
        checks.append(("HTTPS Redirection", "❌", "Désactivée - CRITIQUE"))
    
    # 2. Headers de sécurité
    if hasattr(settings, 'SECURE_BROWSER_XSS_FILTER') and settings.SECURE_BROWSER_XSS_FILTER:
        checks.append(("XSS Protection", "✅", "Activée"))
    else:
        checks.append(("XSS Protection", "⚠️", "Désactivée"))
    
    # 3. Cookies sécurisés
    if hasattr(settings, 'SESSION_COOKIE_SECURE') and settings.SESSION_COOKIE_SECURE:
        checks.append(("Cookies Sécurisés", "✅", "Activés"))
    else:
        checks.append(("Cookies Sécurisés", "❌", "Désactivés - CRITIQUE"))
    
    # 4. CSRF Protection
    if 'django.middleware.csrf.CsrfViewMiddleware' in settings.MIDDLEWARE:
        checks.append(("CSRF Protection", "✅", "Activée"))
    else:
        checks.append(("CSRF Protection", "❌", "Désactivée - CRITIQUE"))
    
    # 5. Debug mode
    if settings.DEBUG:
        checks.append(("Debug Mode", "❌", "Activé - DANGEREUX en production"))
    else:
        checks.append(("Debug Mode", "✅", "Désactivé"))
    
    # 6. Clé secrète
    if len(settings.SECRET_KEY) >= 50 and not settings.SECRET_KEY.startswith('django-insecure-'):
        checks.append(("Clé Secrète", "✅", "Sécurisée"))
    else:
        checks.append(("Clé Secrète", "❌", "Faible - CRITIQUE"))
    
    # 7. Hosts autorisés
    if settings.ALLOWED_HOSTS and '*' not in settings.ALLOWED_HOSTS:
        checks.append(("Hosts Autorisés", "✅", "Restrictifs"))
    else:
        checks.append(("Hosts Autorisés", "❌", "Trop permissifs - CRITIQUE"))
    
    # 8. Validation des mots de passe
    if hasattr(settings, 'AUTH_PASSWORD_VALIDATORS') and len(settings.AUTH_PASSWORD_VALIDATORS) >= 4:
        checks.append(("Validation Mots de Passe", "✅", "Renforcée"))
    else:
        checks.append(("Validation Mots de Passe", "⚠️", "Basique"))
    
    # 9. Logging
    if hasattr(settings, 'LOGGING') and settings.LOGGING:
        checks.append(("Logging", "✅", "Configuré"))
    else:
        checks.append(("Logging", "⚠️", "Non configuré"))
    
    # 10. Fichiers statiques
    if hasattr(settings, 'STATICFILES_DIRS') and settings.STATICFILES_DIRS:
        checks.append(("Fichiers Statiques", "✅", "Configurés"))
    else:
        checks.append(("Fichiers Statiques", "⚠️", "Non configurés"))
    
    # Afficher les résultats
    print("\n📊 RÉSULTATS DES VÉRIFICATIONS:")
    print("-" * 60)
    
    passed = 0
    failed = 0
    warned = 0
    
    for check_name, status, message in checks:
        print(f"{status} {check_name}: {message}")
        if status == "✅":
            passed += 1
        elif status == "❌":
            failed += 1
        else:
            warned += 1
    
    total = len(checks)
    security_score = (passed / total) * 100
    
    print("\n" + "=" * 60)
    print(f"📈 SCORE DE SÉCURITÉ: {security_score:.1f}%")
    print(f"✅ Vérifications réussies: {passed}")
    print(f"❌ Échecs critiques: {failed}")
    print(f"⚠️  Avertissements: {warned}")
    
    # Recommandations
    print("\n🎯 RECOMMANDATIONS PRIORITAIRES:")
    print("-" * 60)
    
    if failed > 0:
        print("🚨 ACTIONS CRITIQUES REQUISES:")
        for check_name, status, message in checks:
            if status == "❌":
                print(f"   • {check_name}: {message}")
    
    if warned > 0:
        print("\n⚠️  AMÉLIORATIONS RECOMMANDÉES:")
        for check_name, status, message in checks:
            if status == "⚠️":
                print(f"   • {check_name}: {message}")
    
    # Configuration de sécurité recommandée
    print("\n🔧 CONFIGURATION DE SÉCURITÉ RECOMMANDÉE:")
    print("-" * 60)
    print("""
# Configuration de sécurité pour production
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Strict'
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Strict'

SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

DEBUG = False
SECRET_KEY = 'votre-cle-secrete-ultra-longue-et-complexe'
ALLOWED_HOSTS = ['votre-domaine.com', 'localhost']
""")
    
    # Conclusion
    print("\n" + "=" * 60)
    if security_score >= 80:
        print("🎉 SYSTÈME DE SÉCURITÉ ROBUSTE!")
        print("   Votre application est bien protégée.")
    elif security_score >= 60:
        print("⚠️  SYSTÈME DE SÉCURITÉ MOYEN")
        print("   Des améliorations sont recommandées.")
    else:
        print("🚨 SYSTÈME DE SÉCURITÉ CRITIQUE!")
        print("   Des actions immédiates sont requises.")
    
    print("\n💡 Pour l'immobilier, la sécurité est CRITIQUE!")
    print("   • Données financières sensibles")
    print("   • Informations clients confidentielles")
    print("   • Conformité réglementaire requise")
    print("   • Réputation de l'entreprise en jeu")

if __name__ == "__main__":
    generate_security_report()
