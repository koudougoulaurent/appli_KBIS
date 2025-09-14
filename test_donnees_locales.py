#!/usr/bin/env python3
"""
Script de test local pour vérifier la création des données
"""

import os
import sys
import django

# Configuration de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from utilisateurs.models import GroupeTravail, Utilisateur
from proprietes.models import TypeBien

def tester_donnees():
    """Teste la création des données localement"""
    print("🧪 TEST LOCAL DES DONNÉES")
    print("=" * 30)
    
    # Test des groupes
    print(f"📋 Groupes de travail: {GroupeTravail.objects.count()}")
    for groupe in GroupeTravail.objects.all():
        print(f"  • {groupe.nom}: {groupe.description}")
    
    # Test des types de biens
    print(f"\n🏠 Types de biens: {TypeBien.objects.count()}")
    for type_bien in TypeBien.objects.all()[:10]:  # Afficher les 10 premiers
        print(f"  • {type_bien.nom}")
    if TypeBien.objects.count() > 10:
        print(f"  ... et {TypeBien.objects.count() - 10} autres")
    
    # Test des utilisateurs
    print(f"\n👥 Utilisateurs: {Utilisateur.objects.count()}")
    for user in Utilisateur.objects.all():
        print(f"  • {user.username} ({user.first_name} {user.last_name}) - {user.poste}")
    
    print("\n✅ Test terminé avec succès !")

if __name__ == "__main__":
    tester_donnees()
