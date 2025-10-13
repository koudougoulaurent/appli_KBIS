#!/bin/bash

# =============================================================================
# SCRIPT COMPLET DE CORRECTION DE BASE DE DONNÉES - KBIS IMMOBILIER
# =============================================================================
# Ce script corrige TOUS les problèmes de base de données :
# - Force l'utilisation de PostgreSQL
# - Corrige le fichier settings.py
# - Applique les migrations
# - Redémarre l'application
# =============================================================================

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Variables
APP_DIR="/var/www/kbis_immobilier"
SERVICE_NAME="kbis_immobilier"

echo -e "${BLUE}=============================================================================${NC}"
echo -e "${BLUE}🔧 SCRIPT COMPLET DE CORRECTION DE BASE DE DONNÉES${NC}"
echo -e "${BLUE}=============================================================================${NC}"

# =============================================================================
# PHASE 1: ARRÊT DE L'APPLICATION
# =============================================================================
echo -e "\n${YELLOW}🛑 PHASE 1: ARRÊT DE L'APPLICATION${NC}"
echo "=========================================="

echo -e "${YELLOW}Arrêt de l'application...${NC}"
sudo systemctl stop $SERVICE_NAME

# =============================================================================
# PHASE 2: CORRECTION DU FICHIER SETTINGS.PY
# =============================================================================
echo -e "\n${YELLOW}🔧 PHASE 2: CORRECTION DU FICHIER SETTINGS.PY${NC}"
echo "=================================================="

cd $APP_DIR || { echo -e "${RED}❌ Impossible d'accéder au répertoire $APP_DIR${NC}"; exit 1; }

echo -e "${YELLOW}Sauvegarde du fichier settings.py...${NC}"
cp gestion_immobiliere/settings.py gestion_immobiliere/settings.py.backup

echo -e "${YELLOW}Correction du fichier settings.py pour forcer PostgreSQL...${NC}"

# Remplacer SQLite par PostgreSQL
sed -i 's/django.db.backends.sqlite3/django.db.backends.postgresql/g' gestion_immobiliere/settings.py

# Vérifier que la correction est appliquée
if grep -q "django.db.backends.postgresql" gestion_immobiliere/settings.py; then
    echo -e "${GREEN}✅ Correction appliquée avec succès${NC}"
else
    echo -e "${RED}❌ Erreur lors de la correction${NC}"
    exit 1
fi

# =============================================================================
# PHASE 3: VÉRIFICATION DE LA CONFIGURATION .ENV
# =============================================================================
echo -e "\n${YELLOW}🔧 PHASE 3: VÉRIFICATION DE LA CONFIGURATION .ENV${NC}"
echo "======================================================"

echo -e "${YELLOW}Vérification du fichier .env...${NC}"
if [ -f ".env" ]; then
    echo -e "${GREEN}✅ Fichier .env existe${NC}"
    cat .env
else
    echo -e "${YELLOW}Création du fichier .env...${NC}"
    cat > .env << 'EOF'
DJANGO_SETTINGS_MODULE=gestion_immobiliere.settings
DEBUG=False
SECRET_KEY=django-insecure-production-key-change-me
DB_NAME=kbis_productiondb
DB_USER=kbis_prod_user
DB_PASSWORD=kbis_prod_password
DB_HOST=localhost
DB_PORT=5432
ALLOWED_HOSTS=localhost,78.138.58.185,127.0.0.1
EOF
fi

# =============================================================================
# PHASE 4: VÉRIFICATION DE POSTGRESQL
# =============================================================================
echo -e "\n${YELLOW}🔧 PHASE 4: VÉRIFICATION DE POSTGRESQL${NC}"
echo "============================================="

echo -e "${YELLOW}Vérification de PostgreSQL...${NC}"
if sudo -u postgres psql -c "SELECT version();" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ PostgreSQL fonctionne${NC}"
else
    echo -e "${RED}❌ PostgreSQL ne fonctionne pas${NC}"
    exit 1
fi

echo -e "${YELLOW}Vérification de la base de données...${NC}"
if sudo -u postgres psql -c "\l" | grep -q "kbis_productiondb"; then
    echo -e "${GREEN}✅ Base de données kbis_productiondb existe${NC}"
else
    echo -e "${YELLOW}Création de la base de données...${NC}"
    sudo -u postgres psql -c "CREATE DATABASE kbis_productiondb;"
    sudo -u postgres psql -c "CREATE USER kbis_prod_user WITH PASSWORD 'kbis_prod_password';"
    sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE kbis_productiondb TO kbis_prod_user;"
fi

# =============================================================================
# PHASE 5: ACTIVATION DE L'ENVIRONNEMENT VIRTUEL
# =============================================================================
echo -e "\n${YELLOW}🔧 PHASE 5: ACTIVATION DE L'ENVIRONNEMENT VIRTUEL${NC}"
echo "======================================================"

echo -e "${YELLOW}Activation de l'environnement virtuel...${NC}"
source venv/bin/activate

# =============================================================================
# PHASE 6: VÉRIFICATION DE LA CONNEXION À LA BASE DE DONNÉES
# =============================================================================
echo -e "\n${YELLOW}🔧 PHASE 6: VÉRIFICATION DE LA CONNEXION${NC}"
echo "============================================="

echo -e "${YELLOW}Test de la connexion à PostgreSQL...${NC}"
python3 << 'EOF'
import os
import django
from django.conf import settings

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from django.db import connection

try:
    cursor = connection.cursor()
    cursor.execute("SELECT version();")
    version = cursor.fetchone()[0]
    print(f"✅ Connexion PostgreSQL réussie: {version}")
except Exception as e:
    print(f"❌ Erreur de connexion: {e}")
    exit(1)
EOF

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Connexion à PostgreSQL réussie${NC}"
else
    echo -e "${RED}❌ Erreur de connexion à PostgreSQL${NC}"
    exit 1
fi

# =============================================================================
# PHASE 7: APPLICATION DES MIGRATIONS
# =============================================================================
echo -e "\n${YELLOW}🔧 PHASE 7: APPLICATION DES MIGRATIONS${NC}"
echo "============================================="

echo -e "${YELLOW}Application des migrations sur PostgreSQL...${NC}"
python3 manage.py migrate

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Migrations appliquées avec succès${NC}"
else
    echo -e "${RED}❌ Erreur lors des migrations${NC}"
    exit 1
fi

# =============================================================================
# PHASE 8: COLLECTE DES FICHIERS STATIQUES
# =============================================================================
echo -e "\n${YELLOW}🔧 PHASE 8: COLLECTE DES FICHIERS STATIQUES${NC}"
echo "=================================================="

echo -e "${YELLOW}Collecte des fichiers statiques...${NC}"
python3 manage.py collectstatic --noinput

# =============================================================================
# PHASE 9: REDÉMARRAGE DE L'APPLICATION
# =============================================================================
echo -e "\n${YELLOW}🔧 PHASE 9: REDÉMARRAGE DE L'APPLICATION${NC}"
echo "============================================="

echo -e "${YELLOW}Redémarrage de l'application...${NC}"
sudo systemctl start $SERVICE_NAME
sudo systemctl status $SERVICE_NAME

# =============================================================================
# PHASE 10: VÉRIFICATIONS FINALES
# =============================================================================
echo -e "\n${YELLOW}🔧 PHASE 10: VÉRIFICATIONS FINALES${NC}"
echo "====================================="

echo -e "${YELLOW}Test de l'application...${NC}"
sleep 5

# Test de l'application
if curl -I http://127.0.0.1:8000 2>/dev/null | grep -q "HTTP"; then
    echo -e "${GREEN}✅ Application répond sur le port 8000${NC}"
else
    echo -e "${RED}❌ Application ne répond pas${NC}"
    echo -e "${YELLOW}Logs de l'application:${NC}"
    sudo journalctl -u $SERVICE_NAME -n 10 --no-pager
fi

# Test via Nginx
if curl -I http://78.138.58.185 2>/dev/null | grep -q "HTTP"; then
    echo -e "${GREEN}✅ Application accessible via Nginx${NC}"
else
    echo -e "${RED}❌ Application non accessible via Nginx${NC}"
fi

# =============================================================================
# RÉSUMÉ FINAL
# =============================================================================
echo -e "\n${BLUE}=============================================================================${NC}"
echo -e "${BLUE}🎉 CORRECTION DE BASE DE DONNÉES TERMINÉE${NC}"
echo -e "${BLUE}=============================================================================${NC}"

echo -e "\n${GREEN}✅ Corrections effectuées :${NC}"
echo "  - Fichier settings.py corrigé pour PostgreSQL"
echo "  - Configuration .env vérifiée"
echo "  - Base de données PostgreSQL vérifiée"
echo "  - Migrations appliquées"
echo "  - Fichiers statiques collectés"
echo "  - Application redémarrée"

echo -e "\n${YELLOW}🔗 URLs d'accès :${NC}"
echo "  - Application : http://78.138.58.185"
echo "  - Admin : http://78.138.58.185/admin/"

echo -e "\n${YELLOW}📋 Commandes utiles :${NC}"
echo "  - Logs application : sudo journalctl -u $SERVICE_NAME -f"
echo "  - Status application : sudo systemctl status $SERVICE_NAME"
echo "  - Test base de données : python3 manage.py dbshell"

echo -e "\n${BLUE}=============================================================================${NC}"





