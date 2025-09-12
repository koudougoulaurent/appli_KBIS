#!/bin/bash
# Script de déploiement automatique pour LWS Hosting
# Usage: ./deploy_lws.sh

echo "🚀 Déploiement de l'application Django sur LWS Hosting..."
echo "=================================================="

# Vérifier que nous sommes dans le bon répertoire
if [ ! -f "manage.py" ]; then
    echo "❌ Erreur: manage.py non trouvé. Êtes-vous dans le bon répertoire ?"
    echo "   Assurez-vous d'être dans le dossier racine de votre projet Django."
    exit 1
fi

echo "✅ Répertoire de projet détecté"

# Vérifier la présence du fichier requirements
if [ ! -f "requirements_production.txt" ]; then
    echo "⚠️  Avertissement: requirements_production.txt non trouvé"
    echo "   Utilisation de requirements.txt par défaut"
    REQUIREMENTS_FILE="requirements.txt"
else
    REQUIREMENTS_FILE="requirements_production.txt"
fi

echo "📦 Installation des dépendances Python..."
echo "   Fichier utilisé: $REQUIREMENTS_FILE"

# Installation des dépendances
if pip install -r "$REQUIREMENTS_FILE" --user; then
    echo "✅ Dépendances installées avec succès"
else
    echo "❌ Erreur lors de l'installation des dépendances"
    echo "   Vérifiez que pip est installé et accessible"
    exit 1
fi

echo "🗄️ Exécution des migrations de base de données..."

# Créer les migrations si nécessaire
if python manage.py makemigrations; then
    echo "✅ Migrations créées"
else
    echo "⚠️  Avertissement: Erreur lors de la création des migrations"
fi

# Appliquer les migrations
if python manage.py migrate; then
    echo "✅ Migrations appliquées avec succès"
else
    echo "❌ Erreur lors de l'application des migrations"
    echo "   Vérifiez la configuration de la base de données"
    exit 1
fi

echo "📁 Collecte des fichiers statiques..."

# Collecter les fichiers statiques
if python manage.py collectstatic --noinput; then
    echo "✅ Fichiers statiques collectés avec succès"
else
    echo "❌ Erreur lors de la collecte des fichiers statiques"
    echo "   Vérifiez la configuration STATIC_ROOT"
    exit 1
fi

echo "👤 Configuration du superutilisateur..."

# Vérifier si un superutilisateur existe déjà
if python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); print('Superutilisateur existe:', User.objects.filter(is_superuser=True).exists())" | grep -q "True"; then
    echo "✅ Superutilisateur déjà existant"
else
    echo "   Création d'un superutilisateur par défaut..."
    echo "   Nom d'utilisateur: admin"
    echo "   Email: admin@example.com"
    echo "   Mot de passe: admin123"
    
    # Créer le superutilisateur
    python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('Superutilisateur créé')
else:
    print('Superutilisateur admin existe déjà')
"
fi

echo "🔧 Configuration des permissions..."

# Vérifier et corriger les permissions
echo "   Vérification des permissions des fichiers..."

# Permissions pour les dossiers (755)
find . -type d -exec chmod 755 {} \; 2>/dev/null || true

# Permissions pour les fichiers Python (644)
find . -name "*.py" -exec chmod 644 {} \; 2>/dev/null || true

# Permissions spéciales pour manage.py et wsgi.py
chmod 755 manage.py 2>/dev/null || true
chmod 755 wsgi.py 2>/dev/null || true

echo "✅ Permissions configurées"

echo "📋 Vérification de la configuration..."

# Vérifier la configuration Django
if python manage.py check --deploy; then
    echo "✅ Configuration Django validée"
else
    echo "⚠️  Avertissement: Problèmes détectés dans la configuration"
    echo "   Vérifiez les logs pour plus de détails"
fi

echo "🌐 Test de démarrage du serveur..."

# Test rapide du serveur (en arrière-plan)
echo "   Démarrage du serveur de test..."
timeout 10s python manage.py runserver 0.0.0.0:8000 > /dev/null 2>&1 &
SERVER_PID=$!

# Attendre un peu
sleep 3

# Vérifier si le serveur fonctionne
if kill -0 $SERVER_PID 2>/dev/null; then
    echo "✅ Serveur de test démarré avec succès"
    kill $SERVER_PID 2>/dev/null || true
else
    echo "❌ Erreur lors du démarrage du serveur de test"
fi

echo ""
echo "🎉 Déploiement terminé avec succès !"
echo "=================================================="
echo ""
echo "📝 Prochaines étapes :"
echo "1. Vérifiez que le fichier .htaccess est à la racine de votre site"
echo "2. Vérifiez que wsgi.py pointe vers 'gestion_immobiliere.settings_lws'"
echo "3. Testez votre site sur votre domaine LWS"
echo "4. Connectez-vous avec admin/admin123 et changez le mot de passe"
echo ""
echo "🔗 URLs importantes :"
echo "   - Administration: https://votre-domaine.com/admin/"
echo "   - Application: https://votre-domaine.com/"
echo ""
echo "📊 Informations de connexion :"
echo "   - Nom d'utilisateur: admin"
echo "   - Mot de passe: admin123"
echo "   - ⚠️  CHANGEZ CE MOT DE PASSE IMMÉDIATEMENT !"
echo ""
echo "🆘 En cas de problème :"
echo "   - Consultez les logs dans /logs/django_lws.log"
echo "   - Vérifiez la configuration dans settings_lws.py"
echo "   - Contactez le support LWS si nécessaire"
echo ""
echo "✅ Votre application Django est maintenant déployée sur LWS !"



