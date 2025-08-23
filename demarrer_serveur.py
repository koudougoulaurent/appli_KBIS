#!/usr/bin/env python
"""
Script pour démarrer le serveur Django et tester l'interface
"""

import os
import sys
import django
import subprocess
import time
import webbrowser
from pathlib import Path

def demarrer_serveur():
    """Démarrer le serveur Django et ouvrir le navigateur"""
    
    print("🚀 DÉMARRAGE DU SERVEUR DJANGO")
    print("=" * 60)
    
    # Vérifier que nous sommes dans le bon répertoire
    current_dir = Path.cwd()
    print(f"📁 Répertoire actuel: {current_dir}")
    
    # Vérifier la présence des fichiers Django
    manage_py = current_dir / "manage.py"
    if not manage_py.exists():
        print("❌ manage.py non trouvé. Assurez-vous d'être dans le répertoire du projet.")
        return False
    
    print("✅ manage.py trouvé")
    
    # Vérifier la base de données
    db_file = current_dir / "db.sqlite3"
    if db_file.exists():
        print(f"✅ Base de données trouvée: {db_file}")
        # Vérifier la taille
        size_mb = db_file.stat().st_size / (1024 * 1024)
        print(f"   Taille: {size_mb:.2f} MB")
    else:
        print("❌ Base de données non trouvée")
        return False
    
    # Vérifier les migrations
    print("\n📊 Vérification des migrations:")
    print("-" * 40)
    
    try:
        # Vérifier les migrations en attente
        result = subprocess.run([
            sys.executable, "manage.py", "showmigrations"
        ], capture_output=True, text=True, cwd=current_dir)
        
        if result.returncode == 0:
            print("✅ Migrations vérifiées")
            # Afficher les migrations des contrats
            if "contrats" in result.stdout:
                print("   - App contrats: migrations présentes")
            if "paiements" in result.stdout:
                print("   - App paiements: migrations présentes")
        else:
            print("⚠️ Erreur lors de la vérification des migrations")
            print(result.stderr)
    except Exception as e:
        print(f"⚠️ Erreur lors de la vérification des migrations: {e}")
    
    # Démarrer le serveur
    print("\n🌐 Démarrage du serveur Django:")
    print("-" * 40)
    
    try:
        # Démarrer le serveur en arrière-plan
        print("   Démarrage du serveur sur http://127.0.0.1:8000/")
        
        # Créer le processus du serveur
        server_process = subprocess.Popen([
            sys.executable, "manage.py", "runserver", "127.0.0.1:8000"
        ], cwd=current_dir)
        
        print("   ✅ Serveur démarré avec succès!")
        print("   ⏳ Attente de 3 secondes pour le démarrage...")
        
        # Attendre que le serveur démarre
        time.sleep(3)
        
        # Ouvrir le navigateur
        print("   🌐 Ouverture du navigateur...")
        try:
            webbrowser.open("http://127.0.0.1:8000/")
            print("   ✅ Navigateur ouvert")
        except Exception as e:
            print(f"   ⚠️ Erreur lors de l'ouverture du navigateur: {e}")
        
        print("\n" + "=" * 60)
        print("🎯 INSTRUCTIONS POUR TESTER LES IDS UNIQUES")
        print("=" * 60)
        print("1. Le serveur Django est maintenant démarré sur http://127.0.0.1:8000/")
        print("2. Connectez-vous avec vos identifiants")
        print("3. Allez dans le menu 'Contrats' pour voir la liste")
        print("4. Vous devriez voir les numéros uniques comme:")
        print("   - CTR-F3BD6CB7")
        print("   - CTR-474E0FD7")
        print("   - CTR-670463B8")
        print("   - etc.")
        print("5. Allez dans le menu 'Paiements' pour voir les reçus")
        print("6. Vous devriez voir les numéros de reçus comme:")
        print("   - REC-20250819-76901")
        print("   - REC-20250806-76576")
        print("   - etc.")
        print("\n⚠️  Pour arrêter le serveur, appuyez sur Ctrl+C dans ce terminal")
        print("=" * 60)
        
        # Attendre que l'utilisateur arrête le serveur
        try:
            server_process.wait()
        except KeyboardInterrupt:
            print("\n🛑 Arrêt du serveur...")
            server_process.terminate()
            server_process.wait()
            print("✅ Serveur arrêté")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du démarrage du serveur: {e}")
        return False

if __name__ == "__main__":
    demarrer_serveur()
