#!/usr/bin/env python
import os
import sys
import django
from django.test import Client
from django.contrib.auth import get_user_model

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings_minimal')
django.setup()

from paiements.services_document_unifie_complet import DocumentUnifieA5ServiceComplet

# Test direct du service
print("=== TEST DIRECT DU SERVICE ===")
service = DocumentUnifieA5ServiceComplet()
html_content = service.generer_document_unifie('paiement_avance', paiement_id=2)

print("Longueur du contenu HTML:", len(html_content))
print("Contient '140000':", '140000' in html_content)
print("Contient 'Octobre 2025':", 'Octobre 2025' in html_content)
print("Contient 'mois couverts':", 'mois couverts' in html_content.lower())

# Sauvegarder le contenu pour inspection
with open('recu_direct.html', 'w', encoding='utf-8') as f:
    f.write(html_content)
print("Contenu HTML sauvegardé dans recu_direct.html")

# Test avec un client authentifié
print("\n=== TEST AVEC CLIENT AUTHENTIFIÉ ===")
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
response = client.get('/paiements/avance-unifie-a5/2/')
print("Status code:", response.status_code)
print("Content-Type:", response.get('Content-Type', 'Unknown'))

if response.status_code == 200:
    content = response.content.decode('utf-8')
    print("Longueur du contenu:", len(content))
    print("Contient '140000':", '140000' in content)
    print("Contient 'Octobre 2025':", 'Octobre 2025' in content)
    print("Contient 'mois couverts':", 'mois couverts' in content.lower())
    
    # Sauvegarder le contenu
    with open('recu_authentifie.html', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Contenu HTML authentifié sauvegardé dans recu_authentifie.html")
else:
    print("Erreur:", response.content.decode('utf-8')[:500])
