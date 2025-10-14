#!/usr/bin/env python
"""
Commande ultra-rapide pour initialiser les données sur Render
"""

import os
import django

# Configuration Django pour Render
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from utilisateurs.models import GroupeTravail, Utilisateur
from proprietes.models import TypeBien
from django.contrib.auth.hashers import make_password

print("🚀 INITIALISATION RAPIDE RENDER")
print("=" * 40)

try:
    # 1. Groupes
    print("🏢 Création des groupes...")
    groupes_data = [('CAISSE', 'Gestion des paiements'), ('CONTROLES', 'Contrôle et audit'), ('ADMINISTRATION', 'Gestion administrative'), ('PRIVILEGE', 'Accès complet')]
    for nom, desc in groupes_data:
        groupe, created = GroupeTravail.objects.update_or_create(nom=nom, defaults={'description': desc, 'actif': True, 'permissions': {}})
        print(f"✅ {nom}")

# 2. Types de biens
print("🏠 Création des types de biens...")
types_data = [('Appartement', 'Appartement en immeuble'), ('Maison', 'Maison individuelle'), ('Studio', 'Studio meublé'), ('Loft', 'Loft industriel'), ('Villa', 'Villa avec jardin')]
for nom, desc in types_data:
    type_bien, created = TypeBien.objects.update_or_create(nom=nom, defaults={'description': desc})
    print(f"✅ {nom}")

# 3. Utilisateurs
print("👥 Création des utilisateurs...")
users_data = [
    ('admin', 'admin@gestimmob.com', 'Super', 'Administrateur', 'PRIVILEGE', True, True),
    ('caisse1', 'caisse1@gestimmob.com', 'Marie', 'Caissière', 'CAISSE', False, False),
    ('controle1', 'controle1@gestimmob.com', 'Sophie', 'Contrôleuse', 'CONTROLES', False, False),
    ('admin1', 'admin1@gestimmob.com', 'Claire', 'Administratrice', 'ADMINISTRATION', True, False),
    ('privilege1', 'privilege1@gestimmob.com', 'Alice', 'Manager', 'PRIVILEGE', True, False)
]

for username, email, first, last, groupe_nom, staff, superuser in users_data:
    groupe = GroupeTravail.objects.get(nom=groupe_nom)
    user, created = Utilisateur.objects.update_or_create(
        username=username,
        defaults={
            'email': email,
            'first_name': first,
            'last_name': last,
            'groupe_travail': groupe,
            'is_staff': staff,
            'is_superuser': superuser,
            'actif': True,
            'password': make_password('password123')
        }
    )
    print(f"✅ {username}")

    print("=" * 40)
    print("🎉 INITIALISATION TERMINÉE !")
    print(f"📊 Groupes: {GroupeTravail.objects.count()}")
    print(f"📊 Types: {TypeBien.objects.count()}")
    print(f"📊 Utilisateurs: {Utilisateur.objects.count()}")
    print("🔑 Mot de passe: password123")
    print("🌐 Rechargez votre page maintenant !")

except Exception as e:
    print(f"❌ Erreur lors de l'initialisation: {e}")
    print("⚠️ L'application peut fonctionner sans les données de test")
