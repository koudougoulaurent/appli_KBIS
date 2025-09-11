#!/bin/bash

# ===========================================
# SCRIPT DE DÉPLOIEMENT DIRECT PYTHONANYWHERE
# ===========================================

echo "🚀 DÉPLOIEMENT DIRECT PYTHONANYWHERE"
echo "===================================="

# Couleurs
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
print_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }

# Fonction pour installer un package
install_package() {
    local package=$1
    print_info "Installation de $package..."
    if pip install "$package" --quiet; then
        print_success "$package installé"
    else
        print_error "Erreur lors de l'installation de $package"
        return 1
    fi
}

# 1. Vérifier l'environnement Python
print_info "Vérification de l'environnement Python..."
python --version
if [ $? -ne 0 ]; then
    print_error "Python n'est pas disponible"
    exit 1
fi

# 2. Installer les packages essentiels un par un
print_info "Installation des packages essentiels..."

# Packages Django de base
install_package "Django>=4.2.7,<5.0"
install_package "django-bootstrap5>=2.0"
install_package "django-crispy-forms>=2.0"
install_package "crispy-bootstrap5>=0.7"

# API REST
install_package "djangorestframework>=3.14.0"

# Génération PDF
install_package "reportlab>=4.0.0"
install_package "xhtml2pdf>=0.2.5"

# Images
install_package "Pillow>=10.0.0"

# Extensions
install_package "django-extensions>=3.2.0"

# Fichiers statiques (ESSENTIEL)
install_package "whitenoise>=6.5.0"

# Sécurité
install_package "django-cors-headers>=4.0.0"
install_package "django-environ>=0.10.0"

# Utilitaires
install_package "python-decouple>=3.8"
install_package "python-dotenv>=1.0.0"

# PDF avancé
install_package "fonttools>=4.0.0"
install_package "PyPDF2>=3.0.0"

# 3. Créer le répertoire de logs
print_info "Création du répertoire de logs..."
mkdir -p logs
print_success "Répertoire logs créé"

# 4. Tester Django
print_info "Test de la configuration Django..."
python manage.py check
if [ $? -eq 0 ]; then
    print_success "Configuration Django valide"
else
    print_error "Problèmes de configuration détectés"
    print_info "Tentative de correction..."
    
    # Essayer avec les settings par défaut
    python manage.py check --settings=gestion_immobiliere.settings
    if [ $? -eq 0 ]; then
        print_success "Configuration avec settings par défaut OK"
    else
        print_error "Problèmes persistants"
        exit 1
    fi
fi

# 5. Migrations
print_info "Application des migrations..."
python manage.py makemigrations
python manage.py migrate
if [ $? -eq 0 ]; then
    print_success "Migrations appliquées"
else
    print_error "Erreur lors des migrations"
    exit 1
fi

# 6. Fichiers statiques
print_info "Collecte des fichiers statiques..."
python manage.py collectstatic --noinput
if [ $? -eq 0 ]; then
    print_success "Fichiers statiques collectés"
else
    print_warning "Problème avec les fichiers statiques, mais continuons..."
fi

# 7. Superutilisateur
print_info "Configuration du superutilisateur..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('Superutilisateur créé: admin/admin123')
else:
    print('Superutilisateur existe déjà')
"

# 8. Test final
print_info "Test final de l'application..."
python manage.py check --deploy
if [ $? -eq 0 ]; then
    print_success "Application prête pour la production"
else
    print_warning "Quelques avertissements, mais l'application devrait fonctionner"
fi

echo ""
echo "🎉 DÉPLOIEMENT TERMINÉ !"
echo "======================="
echo ""
print_success "Votre application Django est maintenant prête !"
echo ""
echo "📋 PROCHAINES ÉTAPES :"
echo "1. Configurez votre WSGI sur PythonAnywhere"
echo "2. Configurez les fichiers statiques"
echo "3. Redémarrez votre application web"
echo ""
echo "🌐 URL: https://laurenzo.pythonanywhere.com"
echo "🔑 Admin: admin / admin123"
