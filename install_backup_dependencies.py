#!/usr/bin/env python3
"""
Installation automatique des dépendances pour le système de sauvegarde avancé
"""

import sys
import subprocess
import importlib

def install_package(package_name):
    """Installe un package Python via pip"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        print(f"✅ {package_name} installé avec succès")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur installation {package_name}: {e}")
        return False

def check_and_install_dependencies():
    """Vérifie et installe les dépendances manquantes"""
    print("🔍 VÉRIFICATION DES DÉPENDANCES DU SYSTÈME DE SAUVEGARDE")
    print("=" * 60)
    
    dependencies = {
        'psutil': 'psutil>=5.8.0',
        'hashlib': None,  # Module standard Python
        'platform': None,  # Module standard Python
        'pathlib': None,   # Module standard Python
    }
    
    missing_packages = []
    
    for package, pip_name in dependencies.items():
        try:
            importlib.import_module(package)
            print(f"✅ {package} - OK")
        except ImportError:
            if pip_name:
                print(f"❌ {package} - MANQUANT")
                missing_packages.append(pip_name)
            else:
                print(f"⚠️  {package} - Module standard manquant (problème Python)")
    
    if missing_packages:
        print(f"\n📦 Installation de {len(missing_packages)} package(s) manquant(s)...")
        for package in missing_packages:
            install_package(package)
    else:
        print("\n✅ Toutes les dépendances sont satisfaites!")
    
    print("\n🎉 Installation terminée - Le système de sauvegarde est prêt!")

if __name__ == "__main__":
    check_and_install_dependencies()

