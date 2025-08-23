#!/usr/bin/env python
"""
Test simple des notifications
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from notifications.models import Notification
from utilisateurs.models import Utilisateur

def test_notifications():
    print("🧪 Test simple des notifications...")
    
    # Vérifier les utilisateurs
    users = Utilisateur.objects.all()
    print(f"✅ {users.count()} utilisateurs trouvés")
    
    # Vérifier les notifications
    notifications = Notification.objects.all()
    print(f"✅ {notifications.count()} notifications trouvées")
    
    # Vérifier les notifications non lues
    unread = Notification.objects.filter(is_read=False)
    print(f"✅ {unread.count()} notifications non lues")
    
    # Vérifier les types de notifications
    types = Notification.objects.values_list('type').distinct()
    print(f"✅ Types de notifications : {[t[0] for t in types]}")
    
    # Vérifier les priorités
    priorities = Notification.objects.values_list('priority').distinct()
    print(f"✅ Priorités : {[p[0] for p in priorities]}")
    
    print("\n🎉 Test terminé avec succès !")
    print("\n📝 URLs à tester :")
    print("   - http://127.0.0.1:8000/notifications/")
    print("   - http://127.0.0.1:8000/notifications/preferences/")
    print("   - http://127.0.0.1:8000/notifications/api/")

if __name__ == '__main__':
    test_notifications() 