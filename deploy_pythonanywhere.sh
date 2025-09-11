#!/bin/bash

# ===========================================
# SCRIPT DE DÉPLOIEMENT AUTOMATIQUE PYTHONANYWHERE
# ===========================================

echo "🚀 DÉPLOIEMENT SUR PYTHONANYWHERE - APPLICATION IMMOBILIÈRE"
echo "=========================================================="

# Variables de configuration
PROJECT_NAME="gestion_immobiliere"
PYTHON_VERSION="3.10"
REQUIREMENTS_FILE="requirements_pythonanywhere.txt"
SETTINGS_FILE="settings_pythonanywhere"

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fonction pour afficher les messages colorés
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Vérification des prérequis
print_status "Vérification des prérequis..."

# Vérifier si Python 3.10 est disponible
if ! command -v python3.10 &> /dev/null; then
    print_error "Python 3.10 n'est pas installé ou n'est pas dans le PATH"
    exit 1
fi

# Vérifier si le fichier requirements existe
if [ ! -f "$REQUIREMENTS_FILE" ]; then
    print_error "Le fichier $REQUIREMENTS_FILE n'existe pas"
    exit 1
fi

# Vérifier si manage.py existe
if [ ! -f "manage.py" ]; then
    print_error "Le fichier manage.py n'existe pas. Êtes-vous dans le bon répertoire ?"
    exit 1
fi

print_success "Prérequis vérifiés ✓"

# ===========================================
# INSTALLATION DES PACKAGES
# ===========================================

print_status "Installation des packages Python..."

# Mise à jour de pip
python3.10 -m pip install --user --upgrade pip

# Installation des packages
if python3.10 -m pip install --user -r "$REQUIREMENTS_FILE"; then
    print_success "Packages installés avec succès ✓"
else
    print_error "Erreur lors de l'installation des packages"
    exit 1
fi

# ===========================================
# CONFIGURATION DE LA BASE DE DONNÉES
# ===========================================

print_status "Configuration de la base de données..."

# Créer le répertoire de logs s'il n'existe pas
mkdir -p logs

# Appliquer les migrations
print_status "Application des migrations..."
if python3.10 manage.py makemigrations; then
    print_success "Migrations créées ✓"
else
    print_warning "Aucune nouvelle migration nécessaire"
fi

if python3.10 manage.py migrate --settings=$PROJECT_NAME.$SETTINGS_FILE; then
    print_success "Migrations appliquées ✓"
else
    print_error "Erreur lors de l'application des migrations"
    exit 1
fi

# ===========================================
# COLLECTE DES FICHIERS STATIQUES
# ===========================================

print_status "Collecte des fichiers statiques..."

if python3.10 manage.py collectstatic --noinput --settings=$PROJECT_NAME.$SETTINGS_FILE; then
    print_success "Fichiers statiques collectés ✓"
else
    print_error "Erreur lors de la collecte des fichiers statiques"
    exit 1
fi

# ===========================================
# CRÉATION DU SUPERUTILISATEUR
# ===========================================

print_status "Configuration du superutilisateur..."

# Vérifier si un superutilisateur existe déjà
if python3.10 manage.py shell --settings=$PROJECT_NAME.$SETTINGS_FILE -c "from django.contrib.auth import get_user_model; User = get_user_model(); print('Superuser exists:', User.objects.filter(is_superuser=True).exists())" | grep -q "True"; then
    print_warning "Un superutilisateur existe déjà"
else
    print_status "Création d'un superutilisateur par défaut..."
    echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('admin', 'admin@example.com', 'admin123') if not User.objects.filter(username='admin').exists() else None" | python3.10 manage.py shell --settings=$PROJECT_NAME.$SETTINGS_FILE
    print_success "Superutilisateur créé (admin/admin123) ✓"
fi

# ===========================================
# VÉRIFICATIONS FINALES
# ===========================================

print_status "Vérifications finales..."

# Vérifier la configuration Django
if python3.10 manage.py check --settings=$PROJECT_NAME.$SETTINGS_FILE; then
    print_success "Configuration Django valide ✓"
else
    print_error "Problèmes de configuration détectés"
    exit 1
fi

# Vérifier les fichiers statiques
if [ -d "staticfiles" ] && [ "$(ls -A staticfiles)" ]; then
    print_success "Fichiers statiques présents ✓"
else
    print_warning "Aucun fichier statique trouvé"
fi

# ===========================================
# INSTRUCTIONS DE CONFIGURATION PYTHONANYWHERE
# ===========================================

echo ""
echo "🎉 DÉPLOIEMENT TERMINÉ AVEC SUCCÈS !"
echo "=================================="
echo ""
echo "📋 PROCHAINES ÉTAPES SUR PYTHONANYWHERE :"
echo ""
echo "1. 🌐 Configuration Web App :"
echo "   - Allez dans l'onglet 'Web' de PythonAnywhere"
echo "   - Modifiez le fichier WSGI : /var/www/votre-nom_pythonanywhere_com_wsgi.py"
echo "   - Remplacez le contenu par :"
echo ""
echo "   import os"
echo "   import sys"
echo "   path = '/home/votre-nom/votre-projet'"
echo "   if path not in sys.path:"
echo "       sys.path.append(path)"
echo "   os.environ['DJANGO_SETTINGS_MODULE'] = 'gestion_immobiliere.settings_pythonanywhere'"
echo "   from django.core.wsgi import get_wsgi_application"
echo "   application = get_wsgi_application()"
echo ""
echo "2. 📁 Configuration des fichiers statiques :"
echo "   - Static files: /static/ → /home/votre-nom/votre-projet/staticfiles/"
echo "   - Media files: /media/ → /home/votre-nom/votre-projet/media/"
echo ""
echo "3. 🔧 Configuration des variables d'environnement :"
echo "   - Créez un fichier .env dans votre projet :"
echo "   - SECRET_KEY=votre-secret-key-securise"
echo "   - DEBUG=False"
echo "   - ALLOWED_HOSTS=votre-nom.pythonanywhere.com"
echo ""
echo "4. 🚀 Redémarrez votre application web"
echo ""
echo "5. 🌐 Accédez à votre application :"
echo "   - URL principale : https://votre-nom.pythonanywhere.com"
echo "   - Interface admin : https://votre-nom.pythonanywhere.com/admin/"
echo "   - Connexion : admin / admin123"
echo ""
echo "📚 Documentation complète : GUIDE_DEPLOIEMENT_PYTHONANYWHERE_COMPLET.md"
echo ""

# ===========================================
# RÉSUMÉ DES PACKAGES INSTALLÉS
# ===========================================

echo "📦 PACKAGES INSTALLÉS :"
echo "======================="
python3.10 -m pip list --user | grep -E "(Django|django-|reportlab|Pillow|whitenoise|crispy|rest_framework)"

echo ""
print_success "Script de déploiement terminé ! 🎉"
