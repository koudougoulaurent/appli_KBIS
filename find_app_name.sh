#!/bin/bash
# Script pour retrouver le nom de l'application sur le VPS
# Usage: ./find_app_name.sh

echo "🔍 Recherche du nom de l'application sur le VPS"
echo "=============================================="

# Vérifier que nous sommes root ou sudo
if [ "$EUID" -ne 0 ]; then
    echo "❌ Ce script doit être exécuté en tant que root ou avec sudo"
    echo "   Utilisez: sudo ./find_app_name.sh"
    exit 1
fi

echo "✅ Privilèges administrateur confirmés"

# 1. Chercher dans /opt/
echo "📁 Recherche dans /opt/..."
if [ -d "/opt" ]; then
    echo "Contenu de /opt/:"
    ls -la /opt/ | grep -E "(app|gest|immob|kbis|django)" || echo "Aucun dossier d'application trouvé dans /opt/"
fi

# 2. Chercher dans /home/
echo ""
echo "📁 Recherche dans /home/..."
if [ -d "/home" ]; then
    for user in /home/*; do
        if [ -d "$user" ]; then
            username=$(basename "$user")
            echo "Utilisateur: $username"
            if [ -d "$user" ]; then
                find "$user" -maxdepth 2 -type d -name "*app*" -o -name "*gest*" -o -name "*immob*" -o -name "*kbis*" -o -name "*django*" 2>/dev/null | head -10
            fi
        fi
    done
fi

# 3. Chercher dans /var/www/
echo ""
echo "📁 Recherche dans /var/www/..."
if [ -d "/var/www" ]; then
    echo "Contenu de /var/www/:"
    ls -la /var/www/ | grep -E "(app|gest|immob|kbis|django)" || echo "Aucun dossier d'application trouvé dans /var/www/"
fi

# 4. Chercher les processus Django/Gunicorn
echo ""
echo "🔍 Recherche des processus Django/Gunicorn..."
ps aux | grep -E "(django|gunicorn|python.*manage)" | grep -v grep || echo "Aucun processus Django trouvé"

# 5. Chercher les services systemd
echo ""
echo "🔍 Recherche des services systemd..."
systemctl list-units --type=service | grep -E "(app|gest|immob|kbis|django|gunicorn)" || echo "Aucun service d'application trouvé"

# 6. Chercher les fichiers manage.py
echo ""
echo "🔍 Recherche des fichiers manage.py..."
find / -name "manage.py" 2>/dev/null | head -10 || echo "Aucun fichier manage.py trouvé"

# 7. Chercher les configurations Nginx
echo ""
echo "🔍 Recherche des configurations Nginx..."
if [ -d "/etc/nginx/sites-available" ]; then
    echo "Sites disponibles:"
    ls -la /etc/nginx/sites-available/ | grep -v default
fi

if [ -d "/etc/nginx/sites-enabled" ]; then
    echo "Sites activés:"
    ls -la /etc/nginx/sites-enabled/ | grep -v default
fi

# 8. Chercher les fichiers de configuration Gunicorn
echo ""
echo "🔍 Recherche des fichiers de configuration Gunicorn..."
find /etc/systemd/system/ -name "*.service" -exec grep -l "gunicorn\|django" {} \; 2>/dev/null || echo "Aucun service Gunicorn trouvé"

# 9. Chercher les répertoires avec des fichiers requirements.txt
echo ""
echo "🔍 Recherche des répertoires avec requirements.txt..."
find / -name "requirements.txt" 2>/dev/null | head -10 | while read file; do
    echo "Requirements trouvé: $file"
    dir=$(dirname "$file")
    echo "  Répertoire: $dir"
    if [ -f "$dir/manage.py" ]; then
        echo "  ✅ Contient manage.py - Application Django trouvée!"
    fi
done

# 10. Chercher les répertoires avec des migrations Django
echo ""
echo "🔍 Recherche des répertoires avec migrations Django..."
find / -name "migrations" -type d 2>/dev/null | head -10 | while read dir; do
    if [ -f "$dir/../manage.py" ]; then
        app_dir=$(dirname "$dir")
        echo "Application Django trouvée: $app_dir"
        if [ -f "$app_dir/requirements.txt" ]; then
            echo "  ✅ Contient requirements.txt"
        fi
    fi
done

echo ""
echo "🎯 RÉSUMÉ DE LA RECHERCHE"
echo "========================"
echo ""
echo "Pour identifier votre application, regardez :"
echo "1. Les répertoires contenant manage.py"
echo "2. Les services systemd actifs"
echo "3. Les configurations Nginx"
echo "4. Les processus Django/Gunicorn en cours"
echo ""
echo "Une fois identifié, notez :"
echo "- Le chemin complet de l'application"
echo "- Le nom du service systemd"
echo "- L'utilisateur qui possède l'application"
echo ""
echo "✅ Recherche terminée !"
