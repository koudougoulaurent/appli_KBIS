#!/usr/bin/env python
import os
import sys
import django
from django.test import Client
from django.contrib.auth import get_user_model

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings_minimal')
django.setup()

# Test avec un client authentifié
print("=== TEST RÉCÉPISSÉ 450K AVEC AUTHENTIFICATION ===")
User = get_user_model()
client = Client()

# Créer un utilisateur de test
try:
    user = User.objects.get(username='test_user')
except User.DoesNotExist:
    user = User.objects.create_user(
        username='test_user',
        email='test@example.com',
        password='testpass123'
    )

# Se connecter
client.force_login(user)

# Tester l'URL
response = client.get('/paiements/avance-unifie-a5/23/')
print("Status code:", response.status_code)
print("Content-Type:", response.get('Content-Type', 'Unknown'))

if response.status_code == 200:
    content = response.content.decode('utf-8')
    print("Longueur du contenu:", len(content))
    print("Contient '450000':", '450000' in content)
    print("Contient 'Novembre 2025':", 'Novembre 2025' in content)
    print("Contient 'mois couverts':", 'mois couverts' in content.lower())
    
    # Sauvegarder le contenu pour inspection
    with open('recu_450k_authentifie.html', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Contenu HTML sauvegardé dans recu_450k_authentifie.html")
    
    # Chercher les montants dans le contenu
    import re
    montants = re.findall(r'(\d{1,3}(?:,\d{3})*)\s*F\s*CFA', content)
    print("Montants trouvés:", montants)
    
else:
    print("Erreur:", response.content.decode('utf-8')[:500])
