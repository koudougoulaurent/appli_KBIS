#!/usr/bin/env python
"""
Script de lancement qui contourne le problème 'packages'
"""
import os
import sys
import subprocess
from pathlib import Path

def main():
    print("🚀 Lancement de l'application Django...")
    print("📍 URL: http://127.0.0.1:8000/")
    print("🛑 Arrêter avec Ctrl+C")
    print("-" * 50)
    
    # Changer vers le répertoire de l'application
    os.chdir(Path(__file__).parent)
    
    try:
        # Essayer de lancer le serveur directement
        print("🔄 Tentative de lancement direct...")
        subprocess.run([
            sys.executable, 
            "manage.py", 
            "runserver", 
            "127.0.0.1:8000"
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur: {e}")
        print("\n🔧 Tentative alternative...")
        
        # Essayer avec une configuration minimale
        try:
            os.environ['DJANGO_SETTINGS_MODULE'] = 'gestion_immobiliere.settings'
            subprocess.run([
                sys.executable, 
                "-c", 
                "import django; django.setup(); from django.core.management import execute_from_command_line; execute_from_command_line(['manage.py', 'runserver', '127.0.0.1:8000'])"
            ], check=True)
        except Exception as e2:
            print(f"❌ Erreur alternative: {e2}")
            print("\n🔧 Dernière tentative...")
            
            # Dernière tentative avec un serveur HTTP simple
            try:
                import http.server
                import socketserver
                import webbrowser
                
                PORT = 8000
                Handler = http.server.SimpleHTTPRequestHandler
                
                with socketserver.TCPServer(("", PORT), Handler) as httpd:
                    print(f"🌐 Serveur HTTP simple démarré sur le port {PORT}")
                    print(f"📍 URL: http://127.0.0.1:{PORT}/")
                    print("⚠️  Note: Ceci est un serveur de fichiers statiques")
                    httpd.serve_forever()
            except Exception as e3:
                print(f"❌ Impossible de démarrer le serveur: {e3}")
                print("\n🔧 Solutions possibles:")
                print("1. Vérifiez que Python est installé correctement")
                print("2. Vérifiez que Django est installé")
                print("3. Redémarrez votre terminal")
                print("4. Contactez le support technique")

if __name__ == "__main__":
    main()