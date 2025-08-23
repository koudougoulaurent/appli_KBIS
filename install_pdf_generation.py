#!/usr/bin/env python3
"""
Script d'installation pour la fonctionnalité de génération PDF
Ce script configure et teste la génération automatique de PDF
"""

import os
import sys
import subprocess
import importlib

def check_python_version():
    """Vérifie la version de Python"""
    print("🐍 Vérification de la version Python...")
    
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ est requis")
        return False
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} détecté")
    return True

def install_dependencies():
    """Installe les dépendances nécessaires"""
    print("\n📦 Installation des dépendances...")
    
    try:
        # Installation de reportlab (dépendance principale)
        print("   Installation de reportlab...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "reportlab>=4.0.0"])
        print("   ✅ reportlab installé avec succès")
        
        # Installation des dépendances optionnelles
        optional_deps = [
            "Pillow>=9.0.0",
            "fonttools>=4.0.0",
            "PyPDF2>=3.0.0"
        ]
        
        for dep in optional_deps:
            try:
                print(f"   Installation de {dep}...")
                subprocess.check_call([sys.executable, "-m", "pip", "install", dep])
                print(f"   ✅ {dep} installé avec succès")
            except subprocess.CalledProcessError:
                print(f"   ⚠️  {dep} n'a pas pu être installé (optionnel)")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur lors de l'installation : {e}")
        return False

def check_django_environment():
    """Vérifie l'environnement Django"""
    print("\n🔧 Vérification de l'environnement Django...")
    
    try:
        # Vérifier si Django est installé
        import django
        print(f"✅ Django {django.get_version()} détecté")
        
        # Vérifier si on est dans un projet Django
        if not os.path.exists('manage.py'):
            print("❌ manage.py non trouvé - assurez-vous d'être dans le répertoire du projet Django")
            return False
        
        print("✅ Projet Django détecté")
        return True
        
    except ImportError:
        print("❌ Django n'est pas installé")
        return False

def setup_django():
    """Configure Django pour les tests"""
    print("\n⚙️  Configuration de Django...")
    
    try:
        # Configuration Django
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
        
        # Initialisation Django
        django.setup()
        print("✅ Django configuré avec succès")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la configuration Django : {e}")
        return False

def test_imports():
    """Teste l'import des modules PDF"""
    print("\n🧪 Test des imports...")
    
    try:
        # Test des services PDF
        from contrats.services import ContratPDFService, ResiliationPDFService
        print("✅ Services PDF importés avec succès")
        
        # Test de la configuration
        from contrats.config import ENTREPRISE_CONFIG, PDF_CONFIG
        print("✅ Configuration importée avec succès")
        
        return True
        
    except ImportError as e:
        print(f"❌ Erreur d'import : {e}")
        return False

def run_tests():
    """Lance les tests de génération PDF"""
    print("\n🚀 Lancement des tests...")
    
    try:
        # Exécuter le script de test
        test_script = "contrats/test_pdf.py"
        if os.path.exists(test_script):
            print("   Exécution des tests de génération PDF...")
            subprocess.run([sys.executable, test_script])
        else:
            print("   ⚠️  Script de test non trouvé")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors des tests : {e}")
        return False

def create_sample_config():
    """Crée un exemple de configuration personnalisée"""
    print("\n📝 Création d'un exemple de configuration...")
    
    config_example = """# Exemple de configuration personnalisée pour votre entreprise
# Copiez ce fichier vers contrats/config_personnalise.py et modifiez-le

ENTREPRISE_CONFIG_PERSONNALISE = {
    'nom': 'VOTRE ENTREPRISE IMMOBILIERE',
    'adresse': 'Votre adresse complète',
    'ville': 'Votre ville',
    'code_postal': 'Votre code postal',
    'pays': 'Votre pays',
    'telephone': 'Votre téléphone',
    'email': 'votre@email.com',
    'site_web': 'www.votre-site.com',
    'siret': 'Votre SIRET',
    'numero_tva': 'Votre numéro TVA',
    'rcs': 'Votre RCS',
    'capital_social': 'Votre capital social',
    'gerant': 'Nom du gérant',
    
    # Informations bancaires
    'banque': 'Votre banque',
    'iban': 'Votre IBAN',
    'bic': 'Votre BIC',
    
    # Logo et branding
    'logo_path': 'static/images/votre_logo.png',
    'couleur_principale': '#Votre couleur principale',
    'couleur_secondaire': '#Votre couleur secondaire',
}

# Utilisez cette configuration en modifiant contrats/config.py
"""
    
    try:
        with open('exemple_config_entreprise.py', 'w', encoding='utf-8') as f:
            f.write(config_example)
        print("✅ Exemple de configuration créé : exemple_config_entreprise.py")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la création de l'exemple : {e}")
        return False

def main():
    """Fonction principale d'installation"""
    print("🚀 Installation de la fonctionnalité de génération PDF")
    print("=" * 60)
    
    # Vérifications préliminaires
    if not check_python_version():
        return False
    
    if not check_django_environment():
        return False
    
    # Installation des dépendances
    if not install_dependencies():
        return False
    
    # Configuration Django
    if not setup_django():
        return False
    
    # Test des imports
    if not test_imports():
        return False
    
    # Création de l'exemple de configuration
    create_sample_config()
    
    # Lancement des tests
    run_tests()
    
    # Résumé final
    print("\n" + "=" * 60)
    print("🎉 INSTALLATION TERMINÉE AVEC SUCCÈS !")
    print("=" * 60)
    
    print("\n📋 Prochaines étapes :")
    print("1. Personnalisez la configuration dans contrats/config.py")
    print("2. Testez la génération PDF via l'interface web")
    print("3. Consultez la documentation dans GENERATION_PDF_CONTRATS.md")
    
    print("\n🔧 En cas de problème :")
    print("- Vérifiez les logs Django")
    print("- Exécutez : python contrats/test_pdf.py")
    print("- Consultez la documentation")
    
    print("\n✅ La fonctionnalité de génération PDF est maintenant disponible !")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Installation interrompue par l'utilisateur")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Erreur inattendue : {e}")
        sys.exit(1)
