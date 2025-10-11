#!/bin/bash

# Script de correction des redirections HTTPS forcées et erreurs 502 sur formulaires
# Désactive les paramètres de sécurité HTTPS non configurés

set -e

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🔧 CORRECTION DES REDIRECTIONS HTTPS ET ERREURS 502${NC}"
echo "====================================================="

# Variables
APP_DIR="/var/www/kbis_immobilier"

echo -e "\n${YELLOW}1. SAUVEGARDE DE LA CONFIGURATION ACTUELLE${NC}"

cd $APP_DIR
source venv/bin/activate

# Sauvegarder settings.py
cp gestion_immobiliere/settings.py gestion_immobiliere/settings.py.backup

echo -e "\n${YELLOW}2. DIAGNOSTIC DE LA CONFIGURATION HTTPS${NC}"

# Vérifier les paramètres HTTPS dans settings.py
echo "Paramètres HTTPS actuels:"
grep -n "SECURE\|HTTPS\|SSL" gestion_immobiliere/settings.py || echo "Aucun paramètre HTTPS trouvé"

echo -e "\n${YELLOW}3. CORRECTION DES PARAMÈTRES DE SÉCURITÉ${NC}"

# Créer un script Python pour corriger les paramètres
cat > /tmp/fix_https_settings.py << 'EOF'
import re

# Lire le fichier settings.py
with open('gestion_immobiliere/settings.py', 'r') as f:
    content = f.read()

# Paramètres à désactiver pour HTTP
https_settings = [
    'SECURE_SSL_REDIRECT',
    'SECURE_HSTS_SECONDS',
    'SECURE_HSTS_INCLUDE_SUBDOMAINS',
    'SECURE_HSTS_PRELOAD',
    'SECURE_PROXY_SSL_HEADER',
    'SECURE_BROWSER_XSS_FILTER',
    'SECURE_CONTENT_TYPE_NOSNIFF',
    'SECURE_REFERRER_POLICY',
    'SESSION_COOKIE_SECURE',
    'CSRF_COOKIE_SECURE',
    'SECURE_REDIRECT_EXEMPT',
]

# Désactiver tous les paramètres HTTPS
for setting in https_settings:
    # Remplacer par False
    content = re.sub(f'^{setting}\s*=\s*True', f'{setting} = False', content, flags=re.MULTILINE)
    # Commenter les lignes qui ne sont pas False
    content = re.sub(f'^{setting}\s*=\s*(?!False)', f'# {setting} = ', content, flags=re.MULTILINE)

# Ajouter les paramètres corrects pour HTTP
http_settings = '''
# Configuration pour HTTP (sans SSL)
SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False
SECURE_BROWSER_XSS_FILTER = False
SECURE_CONTENT_TYPE_NOSNIFF = False
SECURE_REFERRER_POLICY = None
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_REDIRECT_EXEMPT = []

# Configuration pour les formulaires
CSRF_TRUSTED_ORIGINS = ['http://78.138.58.185', 'http://localhost']
ALLOWED_HOSTS = ['78.138.58.185', 'localhost', '127.0.0.1']
'''

# Ajouter les paramètres à la fin du fichier
if 'SECURE_SSL_REDIRECT' not in content:
    content += http_settings

# Écrire le fichier modifié
with open('gestion_immobiliere/settings.py', 'w') as f:
    f.write(content)

print("Configuration HTTPS désactivée avec succès")
EOF

python3 /tmp/fix_https_settings.py

echo -e "\n${YELLOW}4. VÉRIFICATION DE LA SYNTAXE PYTHON${NC}"

# Vérifier la syntaxe
python3 -m py_compile gestion_immobiliere/settings.py

echo -e "\n${YELLOW}5. REDÉMARRAGE DE L'APPLICATION${NC}"

# Arrêter gunicorn
sudo pkill -f gunicorn || true
sleep 2

# Redémarrer gunicorn
nohup gunicorn --workers 3 --bind 127.0.0.1:8000 --daemon --pid /tmp/gunicorn.pid gestion_immobiliere.wsgi:application &

sleep 3

echo -e "\n${YELLOW}6. VÉRIFICATION${NC}"

# Vérifier que gunicorn fonctionne
if pgrep -f gunicorn > /dev/null; then
    echo -e "${GREEN}✅ Gunicorn redémarré${NC}"
else
    echo -e "${RED}❌ Gunicorn ne fonctionne pas${NC}"
    exit 1
fi

# Test de connectivité
echo "Test de l'application:"
if curl -s -I http://78.138.58.185 >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Application accessible${NC}"
else
    echo -e "${RED}❌ Application non accessible${NC}"
fi

# Test de l'admin
echo "Test de l'administration:"
if curl -s -I http://78.138.58.185/admin/ >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Interface d'administration accessible${NC}"
else
    echo -e "${RED}❌ Interface d'administration non accessible${NC}"
fi

echo -e "\n${YELLOW}7. TEST DES FORMULAIRES${NC}"

# Tester une page avec formulaire
echo "Test d'une page avec formulaire:"
curl -s -I http://78.138.58.185/admin/ | head -5

echo -e "\n${GREEN}🎉 CORRECTION TERMINÉE !${NC}"
echo "Les redirections HTTPS forcées ont été désactivées."
echo "Votre application devrait maintenant fonctionner correctement en HTTP."
echo ""
echo "URLs d'accès :"
echo "- Application : http://78.138.58.185"
echo "- Administration : http://78.138.58.185/admin/"
echo ""
echo "Si vous voulez configurer HTTPS plus tard, vous pourrez :"
echo "1. Obtenir un certificat SSL"
echo "2. Configurer nginx pour HTTPS"
echo "3. Réactiver les paramètres de sécurité dans settings.py"

