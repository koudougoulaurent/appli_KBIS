"""
Configuration WSGI pour PythonAnywhere
À copier dans /var/www/votre-nom_pythonanywhere_com_wsgi.py
"""

import os
import sys

# ===========================================
# CONFIGURATION DU CHEMIN DU PROJET
# ===========================================

# Remplacez 'votre-nom' et 'votre-projet' par vos valeurs réelles
# Exemple: /home/laurenzo/appli_KBIS
path = '/home/laurenzo/appli_KBIS'
if path not in sys.path:
    sys.path.append(path)

# ===========================================
# CONFIGURATION DE L'ENVIRONNEMENT DJANGO
# ===========================================

# Définir le module de settings pour PythonAnywhere
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')

# ===========================================
# IMPORT ET CONFIGURATION DE L'APPLICATION
# ===========================================

try:
    from django.core.wsgi import get_wsgi_application
    application = get_wsgi_application()
    print("✅ Application Django chargée avec succès")
except Exception as e:
    print(f"❌ Erreur lors du chargement de l'application Django: {e}")
    # En cas d'erreur, essayer avec les settings par défaut
    try:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
        from django.core.wsgi import get_wsgi_application
        application = get_wsgi_application()
        print("✅ Application Django chargée avec settings par défaut")
    except Exception as e2:
        print(f"❌ Erreur critique: {e2}")
        # En cas d'erreur, retourner une application de base
        def application(environ, start_response):
            status = '500 Internal Server Error'
            response_headers = [('Content-type', 'text/plain')]
            start_response(status, response_headers)
            return [b'Erreur de configuration Django']

# ===========================================
# NOTES DE CONFIGURATION
# ===========================================

"""
INSTRUCTIONS D'UTILISATION :

1. Copiez ce fichier dans /var/www/votre-nom_pythonanywhere_com_wsgi.py
2. Remplacez 'votre-nom' et 'votre-projet' par vos valeurs réelles
3. Assurez-vous que le chemin pointe vers votre projet Django
4. Redémarrez votre application web dans PythonAnywhere

VÉRIFICATIONS :
- Le fichier doit être dans /var/www/
- Le nom doit correspondre à votre domaine PythonAnywhere
- Les permissions doivent être correctes (644)
- Le chemin du projet doit être absolu et correct

DÉPANNAGE :
- Vérifiez les logs d'erreur dans l'onglet Web de PythonAnywhere
- Testez la configuration avec : python3.10 manage.py check --settings=gestion_immobiliere.settings_pythonanywhere
- Vérifiez que tous les packages sont installés
"""
