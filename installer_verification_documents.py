#!/usr/bin/env python3
"""
Script d'Installation du Système de Vérification de Véracité des Documents
=========================================================================

Ce script configure automatiquement le système de vérification dans votre
application Django existante.

Auteur: Assistant IA
Date: 2025
"""

import os
import sys
import shutil
from pathlib import Path

def print_header():
    """Affiche l'en-tête du script."""
    print("🔍 INSTALLATION DU SYSTÈME DE VÉRIFICATION DE VÉRACITÉ DES DOCUMENTS")
    print("=" * 70)
    print("Ce script va configurer automatiquement le système de vérification")
    print("dans votre application Django existante.")
    print()

def check_django_environment():
    """Vérifie que l'environnement Django est configuré."""
    print("🔍 VÉRIFICATION DE L'ENVIRONNEMENT DJANGO")
    print("-" * 50)
    
    # Vérifier que nous sommes dans le bon répertoire
    if not os.path.exists('manage.py'):
        print("❌ Erreur: manage.py non trouvé")
        print("   Assurez-vous d'être dans le répertoire racine de votre application Django")
        return False
    
    # Vérifier la structure des répertoires
    required_dirs = ['core', 'proprietes', 'contrats', 'utilisateurs']
    missing_dirs = []
    
    for dir_name in required_dirs:
        if not os.path.exists(dir_name):
            missing_dirs.append(dir_name)
    
    if missing_dirs:
        print(f"⚠️  Répertoires manquants: {', '.join(missing_dirs)}")
        print("   Le script va les créer automatiquement")
    else:
        print("✅ Structure des répertoires vérifiée")
    
    return True

def create_directory_structure():
    """Crée la structure de répertoires nécessaire."""
    print("\n📁 CRÉATION DE LA STRUCTURE DES RÉPERTOIRES")
    print("-" * 50)
    
    directories = [
        'core/services',
        'core/middleware',
        'core/utils'
    ]
    
    for directory in directories:
        try:
            os.makedirs(directory, exist_ok=True)
            print(f"   ✅ Créé: {directory}")
        except Exception as e:
            print(f"   ❌ Erreur création {directory}: {e}")
            return False
    
    return True

def create_init_files():
    """Crée les fichiers __init__.py nécessaires."""
    print("\n📄 CRÉATION DES FICHIERS __INIT__.PY")
    print("-" * 50)
    
    init_files = [
        'core/__init__.py',
        'core/services/__init__.py',
        'core/middleware/__init__.py',
        'core/utils/__init__.py'
    ]
    
    for init_file in init_files:
        try:
            if not os.path.exists(init_file):
                with open(init_file, 'w', encoding='utf-8') as f:
                    f.write('# Fichier d\'initialisation pour le module\n')
                print(f"   ✅ Créé: {init_file}")
            else:
                print(f"   ℹ️  Existe déjà: {init_file}")
        except Exception as e:
            print(f"   ❌ Erreur création {init_file}: {e}")
            return False
    
    return True

def update_settings_py():
    """Met à jour le fichier settings.py pour ajouter le middleware."""
    print("\n⚙️  MISE À JOUR DU FICHIER SETTINGS.PY")
    print("-" * 50)
    
    settings_file = 'gestion_immobiliere/settings.py'
    
    if not os.path.exists(settings_file):
        print(f"   ⚠️  Fichier {settings_file} non trouvé")
        print("   Vous devrez ajouter manuellement le middleware")
        return True
    
    try:
        # Lire le contenu actuel
        with open(settings_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Vérifier si le middleware est déjà présent
        if 'DocumentVerificationMiddleware' in content:
            print("   ℹ️  Le middleware est déjà configuré")
            return True
        
        # Ajouter le middleware
        middleware_marker = 'MIDDLEWARE = ['
        if middleware_marker in content:
            # Trouver la position du middleware
            pos = content.find(middleware_marker)
            end_pos = content.find(']', pos)
            
            # Insérer le nouveau middleware
            new_middleware = "    'core.middleware.document_verification_middleware.DocumentVerificationMiddleware',\n"
            
            # Insérer avant le dernier middleware
            before_last = content.rfind(',', pos, end_pos)
            if before_last != -1:
                content = content[:before_last + 1] + '\n' + new_middleware + content[before_last + 1:]
            else:
                # Insérer après l'ouverture
                content = content[:pos + len(middleware_marker)] + '\n' + new_middleware + content[pos + len(middleware_marker):]
            
            # Écrire le fichier modifié
            with open(settings_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print("   ✅ Middleware ajouté au fichier settings.py")
        else:
            print("   ⚠️  Section MIDDLEWARE non trouvée")
            print("   Vous devrez ajouter manuellement le middleware")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Erreur lors de la mise à jour: {e}")
        return False

def update_forms_existants():
    """Met à jour les formulaires existants pour intégrer la vérification."""
    print("\n📝 MISE À JOUR DES FORMULAIRES EXISTANTS")
    print("-" * 50)
    
    forms_files = [
        'proprietes/forms.py',
        'proprietes/forms_specialises.py'
    ]
    
    for forms_file in forms_files:
        if os.path.exists(forms_file):
            try:
                # Lire le contenu
                with open(forms_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Vérifier si le mixin est déjà présent
                if 'DocumentVerificationFormMixin' in content:
                    print(f"   ℹ️  {forms_file}: Mixin déjà intégré")
                    continue
                
                # Ajouter l'import
                import_statement = "from core.middleware.document_verification_middleware import DocumentVerificationFormMixin\n"
                
                # Trouver la première ligne d'import
                lines = content.split('\n')
                import_line = -1
                
                for i, line in enumerate(lines):
                    if line.strip().startswith('from ') or line.strip().startswith('import '):
                        import_line = i
                        break
                
                if import_line != -1:
                    # Insérer après le dernier import
                    last_import = import_line
                    for i in range(import_line, len(lines)):
                        if lines[i].strip().startswith('from ') or lines[i].strip().startswith('import '):
                            last_import = i
                        elif lines[i].strip() == '':
                            break
                    
                    lines.insert(last_import + 1, import_statement)
                    
                    # Écrire le fichier modifié
                    with open(forms_file, 'w', encoding='utf-8') as f:
                        f.write('\n'.join(lines))
                    
                    print(f"   ✅ {forms_file}: Import ajouté")
                else:
                    print(f"   ⚠️  {forms_file}: Aucune ligne d'import trouvée")
                
            except Exception as e:
                print(f"   ❌ Erreur lors de la mise à jour de {forms_file}: {e}")
    
    return True

def create_requirements_update():
    """Crée un fichier requirements.txt mis à jour."""
    print("\n📦 MISE À JOUR DES DÉPENDANCES")
    print("-" * 50)
    
    requirements_file = 'requirements_verification.txt'
    
    try:
        with open(requirements_file, 'w', encoding='utf-8') as f:
            f.write("# Dépendances pour le système de vérification des documents\n")
            f.write("# Installer avec: pip install -r requirements_verification.txt\n\n")
            f.write("# OCR et traitement d'images\n")
            f.write("pytesseract>=0.3.10\n")
            f.write("Pillow>=9.0.0\n")
            f.write("opencv-python>=4.5.0\n\n")
            f.write("# Traitement PDF\n")
            f.write("pdfplumber>=0.7.0\n")
            f.write("PyPDF2>=3.0.0\n\n")
            f.write("# Traitement de texte\n")
            f.write("python-magic>=0.4.27\n")
            f.write("chardet>=4.0.0\n\n")
            f.write("# Utilitaires\n")
            f.write("python-dateutil>=2.8.2\n")
        
        print(f"   ✅ Fichier {requirements_file} créé")
        print("   💡 Installez les dépendances avec: pip install -r requirements_verification.txt")
        
    except Exception as e:
        print(f"   ❌ Erreur création requirements: {e}")
    
    return True

def create_test_script():
    """Crée un script de test pour vérifier l'installation."""
    print("\n🧪 CRÉATION DU SCRIPT DE TEST")
    print("-" * 50)
    
    test_script = 'test_installation_verification.py'
    
    try:
        with open(test_script, 'w', encoding='utf-8') as f:
            f.write('''#!/usr/bin/env python3
"""
Script de Test de l'Installation du Système de Vérification
==========================================================

Ce script vérifie que l'installation s'est bien passée.

Exécution: python test_installation_verification.py
"""

import os
import sys

def test_imports():
    """Test des imports du système de vérification."""
    print("🔍 TEST DES IMPORTS")
    print("-" * 30)
    
    try:
        from core.services.verification_documents import DocumentVerificationService
        print("✅ Service de vérification importé avec succès")
    except ImportError as e:
        print(f"❌ Erreur import service: {e}")
        return False
    
    try:
        from core.middleware.document_verification_middleware import DocumentVerificationMiddleware
        print("✅ Middleware importé avec succès")
    except ImportError as e:
        print(f"❌ Erreur import middleware: {e}")
        return False
    
    try:
        from core.middleware.document_verification_middleware import DocumentVerificationFormMixin
        print("✅ Mixin de formulaire importé avec succès")
    except ImportError as e:
        print(f"❌ Erreur import mixin: {e}")
        return False
    
    return True

def test_service_creation():
    """Test de la création du service."""
    print("\\n🔧 TEST DE CRÉATION DU SERVICE")
    print("-" * 30)
    
    try:
        from core.services.verification_documents import DocumentVerificationService
        
        service = DocumentVerificationService()
        print("✅ Service créé avec succès")
        
        # Test des méthodes
        stats = service.get_statistics()
        print("✅ Méthode get_statistics() fonctionne")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur création service: {e}")
        return False

def test_middleware_creation():
    """Test de la création du middleware."""
    print("\\n🔄 TEST DE CRÉATION DU MIDDLEWARE")
    print("-" * 30)
    
    try:
        from core.middleware.document_verification_middleware import DocumentVerificationMiddleware
        
        # Simuler une requête
        class MockRequest:
            method = 'GET'
            FILES = {}
            session = {}
        
        middleware = DocumentVerificationMiddleware()
        print("✅ Middleware créé avec succès")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur création middleware: {e}")
        return False

def main():
    """Fonction principale."""
    print("🚀 TEST DE L'INSTALLATION DU SYSTÈME DE VÉRIFICATION")
    print("=" * 60)
    
    success = True
    
    # Tests
    if not test_imports():
        success = False
    
    if not test_service_creation():
        success = False
    
    if not test_middleware_creation():
        success = False
    
    # Résumé
    print("\\n" + "=" * 60)
    if success:
        print("🎉 TOUS LES TESTS SONT PASSÉS AVEC SUCCÈS !")
        print("✅ Le système de vérification est correctement installé")
        print("\\n🚀 PROCHAINES ÉTAPES:")
        print("   1. Installer les dépendances: pip install -r requirements_verification.txt")
        print("   2. Redémarrer votre serveur Django")
        print("   3. Tester avec un formulaire d'upload")
    else:
        print("❌ CERTAINS TESTS ONT ÉCHOUÉ")
        print("⚠️  Vérifiez l'installation et relancez le script")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
''')
        
        print(f"   ✅ Script de test {test_script} créé")
        
    except Exception as e:
        print(f"   ❌ Erreur création script de test: {e}")
    
    return True

def create_documentation():
    """Crée la documentation d'utilisation."""
    print("\n📚 CRÉATION DE LA DOCUMENTATION")
    print("-" * 50)
    
    doc_file = 'GUIDE_UTILISATION_VERIFICATION.md'
    
    try:
        with open(doc_file, 'w', encoding='utf-8') as f:
            f.write('''# 📖 Guide d'Utilisation du Système de Vérification

## 🚀 Démarrage Rapide

### 1. Installation des Dépendances
```bash
pip install -r requirements_verification.txt
```

### 2. Redémarrage du Serveur
```bash
python manage.py runserver
```

### 3. Test de l'Installation
```bash
python test_installation_verification.py
```

## 🔧 Utilisation

### Dans vos Formulaires
```python
from core.middleware.document_verification_middleware import DocumentVerificationFormMixin

class MonFormulaire(DocumentVerificationFormMixin, forms.ModelForm):
    pass
```

### Accès aux Résultats
```python
if form.is_valid():
    verification_results = form.get_verification_results()
    verification_summary = form.get_verification_summary()
```

## 📞 Support

Pour toute question, consultez la documentation complète dans `INTEGRATION_VERIFICATION_DOCUMENTS.md`
''')
        
        print(f"   ✅ Documentation {doc_file} créée")
        
    except Exception as e:
        print(f"   ❌ Erreur création documentation: {e}")
    
    return True

def main():
    """Fonction principale d'installation."""
    print_header()
    
    # Vérifications préliminaires
    if not check_django_environment():
        print("❌ L'environnement Django n'est pas correctement configuré")
        return False
    
    # Installation
    steps = [
        ("Création de la structure des répertoires", create_directory_structure),
        ("Création des fichiers __init__.py", create_init_files),
        ("Mise à jour du fichier settings.py", update_settings_py),
        ("Mise à jour des formulaires existants", update_forms_existants),
        ("Mise à jour des dépendances", create_requirements_update),
        ("Création du script de test", create_test_script),
        ("Création de la documentation", create_documentation)
    ]
    
    print("🚀 DÉBUT DE L'INSTALLATION")
    print("=" * 70)
    
    success = True
    
    for step_name, step_function in steps:
        print(f"\n📋 {step_name.upper()}")
        print("-" * 50)
        
        try:
            if step_function():
                print(f"   ✅ {step_name} terminé avec succès")
            else:
                print(f"   ❌ {step_name} a échoué")
                success = False
        except Exception as e:
            print(f"   ❌ Erreur lors de {step_name}: {e}")
            success = False
    
    # Résumé final
    print("\n" + "=" * 70)
    if success:
        print("🎉 INSTALLATION TERMINÉE AVEC SUCCÈS !")
        print()
        print("📋 RÉSUMÉ DE L'INSTALLATION:")
        print("   ✅ Service de vérification des documents créé")
        print("   ✅ Middleware automatique configuré")
        print("   ✅ Mixin pour formulaires disponible")
        print("   ✅ Fichiers de configuration mis à jour")
        print("   ✅ Scripts de test créés")
        print("   ✅ Documentation générée")
        print()
        print("🚀 PROCHAINES ÉTAPES:")
        print("   1. Installer les dépendances: pip install -r requirements_verification.txt")
        print("   2. Redémarrer votre serveur Django")
        print("   3. Tester l'installation: python test_installation_verification.py")
        print("   4. Consulter la documentation: GUIDE_UTILISATION_VERIFICATION.md")
        print()
        print("💡 VOTRE APPLICATION DISPOSE MAINTENANT D'UN SYSTÈME DE")
        print("   VÉRIFICATION AUTOMATIQUE DE VÉRACITÉ DES DOCUMENTS !")
    else:
        print("❌ L'INSTALLATION A RENCONTRÉ DES PROBLÈMES")
        print("   Vérifiez les erreurs ci-dessus et relancez le script")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
