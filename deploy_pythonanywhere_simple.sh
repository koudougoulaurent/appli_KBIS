#!/bin/bash

# ===========================================
# SCRIPT DE DÉPLOIEMENT ULTRA-SIMPLE PYTHONANYWHERE
# ===========================================

echo "🚀 DÉPLOIEMENT AUTOMATIQUE PYTHONANYWHERE"
echo "========================================="

# Couleurs
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }

# 1. Installation des packages
echo "📦 Installation des packages..."
pip install Django>=4.2.7,<5.0
pip install django-bootstrap5>=2.0
pip install django-crispy-forms>=2.0
pip install crispy-bootstrap5>=0.7
pip install djangorestframework>=3.14.0
pip install reportlab>=4.0.0
pip install xhtml2pdf>=0.2.5
pip install Pillow>=10.0.0
pip install whitenoise>=6.5.0
pip install django-extensions>=3.2.0
pip install django-cors-headers>=4.0.0
pip install django-environ>=0.10.0
pip install python-decouple>=3.8
pip install python-dotenv>=1.0.0
pip install fonttools>=4.0.0
pip install PyPDF2>=3.0.0

if [ $? -eq 0 ]; then
    print_success "Packages installés avec succès"
else
    print_error "Erreur lors de l'installation des packages"
    exit 1
fi

# 2. Créer le répertoire de logs
mkdir -p logs
print_success "Répertoire logs créé"

# 3. Migrations
echo "🗄️ Application des migrations..."
python manage.py makemigrations
python manage.py migrate

if [ $? -eq 0 ]; then
    print_success "Migrations appliquées"
else
    print_error "Erreur lors des migrations"
    exit 1
fi

# 4. Collecte des fichiers statiques
echo "📁 Collecte des fichiers statiques..."
python manage.py collectstatic --noinput

if [ $? -eq 0 ]; then
    print_success "Fichiers statiques collectés"
else
    print_error "Erreur lors de la collecte des fichiers statiques"
    exit 1
fi

# 5. Créer un superutilisateur si nécessaire
echo "👤 Configuration du superutilisateur..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('Superutilisateur créé: admin/admin123')
else:
    print('Superutilisateur existe déjà')
"

# 6. Vérification finale
echo "🔍 Vérification finale..."
python manage.py check

if [ $? -eq 0 ]; then
    print_success "Configuration Django valide"
else
    print_error "Problèmes de configuration détectés"
    exit 1
fi

echo ""
echo "🎉 DÉPLOIEMENT TERMINÉ AVEC SUCCÈS !"
echo "===================================="
echo ""
echo "🌐 Votre application est prête !"
echo "📱 URL: https://votre-nom.pythonanywhere.com"
echo "🔑 Admin: admin / admin123"
echo ""
print_success "Tout est configuré et fonctionnel ! 🚀"
