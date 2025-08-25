#!/usr/bin/env python
"""
Test simple des notifications
"""

import os
import sys
import django
import re

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

# Test de la regex
regex = re.compile(r'^\+\d{9,15}$')

print("=== TEST SIMPLE DE LA REGEX ===")

# Test 1: Numéro valide
phone1 = "+22990123456"
match1 = regex.match(phone1)
print(f"Test 1: {phone1} -> {'✅ Valide' if match1 else '❌ Invalide'}")

# Test 2: Numéro trop court
phone2 = "+12345678"
match2 = regex.match(phone2)
print(f"Test 2: {phone2} -> {'✅ Valide' if match2 else '❌ Invalide'}")

# Test 3: Numéro avec espaces
phone3 = "+123 456 789"
match3 = regex.match(phone3)
print(f"Test 3: {phone3} -> {'✅ Valide' if match3 else '❌ Invalide'}")

# Test 4: Numéro trop long
phone4 = "+1234567890123456"
match4 = regex.match(phone4)
print(f"Test 4: {phone4} -> {'✅ Valide' if match4 else '❌ Invalide'}")

print("\nRegex utilisée:", regex.pattern)

if __name__ == '__main__':
    test_notifications() 