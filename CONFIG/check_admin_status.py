#!/usr/bin/env python
"""
Script de vérification du statut de l'admin Django
À exécuter sur Render pour diagnostiquer les problèmes
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

def check_admin_status():
    """Vérifie le statut de l'admin Django"""
    print("🔍 Vérification du statut de l'admin Django")
    print("=" * 50)
    
    # 1. Vérifier les settings
    print("\n1️⃣ Configuration Django:")
    from django.conf import settings
    print(f"   DEBUG: {settings.DEBUG}")
    print(f"   ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}")
    print(f"   ROOT_URLCONF: {settings.ROOT_URLCONF}")
    print(f"   STATIC_ROOT: {settings.STATIC_ROOT}")
    
    # 2. Vérifier les URLs
    print("\n2️⃣ Configuration des URLs:")
    try:
        from django.urls import reverse
        admin_url = reverse('admin:index')
        print(f"   ✅ URL Admin: {admin_url}")
    except Exception as e:
        print(f"   ❌ Erreur URL Admin: {e}")
    
    # 3. Vérifier les apps installées
    print("\n3️⃣ Applications installées:")
    for app in settings.INSTALLED_APPS:
        if 'admin' in app:
            print(f"   ✅ {app}")
    
    # 4. Vérifier la base de données
    print("\n4️⃣ Base de données:")
    try:
        from django.db import connection
        cursor = connection.cursor()
        cursor.execute("SELECT 1")
        print("   ✅ Connexion DB: OK")
    except Exception as e:
        print(f"   ❌ Connexion DB: {e}")
    
    # 5. Vérifier les migrations
    print("\n5️⃣ Migrations:")
    try:
        from django.core.management import call_command
        from io import StringIO
        out = StringIO()
        call_command('showmigrations', '--plan', stdout=out)
        migrations = out.getvalue()
        if '[X]' in migrations:
            print("   ✅ Migrations appliquées")
        else:
            print("   ⚠️ Migrations en attente")
    except Exception as e:
        print(f"   ❌ Erreur migrations: {e}")
    
    # 6. Vérifier les fichiers statiques
    print("\n6️⃣ Fichiers statiques:")
    import os
    static_root = settings.STATIC_ROOT
    if os.path.exists(static_root):
        print(f"   ✅ STATIC_ROOT existe: {static_root}")
        files_count = len([f for f in os.listdir(static_root) if os.path.isfile(os.path.join(static_root, f))])
        print(f"   📁 Nombre de fichiers: {files_count}")
    else:
        print(f"   ❌ STATIC_ROOT manquant: {static_root}")
    
    # 7. Test de l'admin
    print("\n7️⃣ Test de l'admin:")
    try:
        from django.contrib.admin.sites import site
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        users_count = User.objects.count()
        superusers_count = User.objects.filter(is_superuser=True).count()
        
        print(f"   👥 Utilisateurs: {users_count}")
        print(f"   👑 Superutilisateurs: {superusers_count}")
        
        if superusers_count == 0:
            print("   ⚠️ Aucun superutilisateur trouvé")
        else:
            print("   ✅ Superutilisateur(s) disponible(s)")
            
    except Exception as e:
        print(f"   ❌ Erreur admin: {e}")
    
    print("\n" + "=" * 50)
    print("✅ Vérification terminée")
    
    # Recommandations
    print("\n💡 Recommandations:")
    if not settings.DEBUG and 'appli-kbis-3.onrender.com' not in settings.ALLOWED_HOSTS:
        print("   - Ajouter 'appli-kbis-3.onrender.com' à ALLOWED_HOSTS")
    if not os.path.exists(static_root):
        print("   - Exécuter: python manage.py collectstatic --noinput")
    if superusers_count == 0:
        print("   - Créer un superutilisateur: python manage.py createsuperuser")

if __name__ == "__main__":
    check_admin_status()
