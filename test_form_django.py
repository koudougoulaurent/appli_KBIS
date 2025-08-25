#!/usr/bin/env python3
"""
Test du formulaire Django pour la validation du téléphone
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from utilisateurs.forms import UtilisateurForm
from utilisateurs.models import GroupeTravail

def test_form_validation():
    """Test de la validation du formulaire"""
    
    # Créer un groupe de travail pour les tests
    groupe, created = GroupeTravail.objects.get_or_create(
        nom='ADMINISTRATION',
        defaults={'description': 'Groupe pour les tests'}
    )
    
    print("=== TEST DE VALIDATION DU FORMULAIRE ===")
    
    # Test 1: Numéro valide
    form_data1 = {
        'username': 'test_user1',
        'email': 'test1@example.com',
        'telephone': '+22990123456',
        'groupe_travail': groupe.id,
        'password': 'testpass123',
        'password_confirm': 'testpass123'
    }
    
    form1 = UtilisateurForm(data=form_data1)
    is_valid1 = form1.is_valid()
    print(f"Test 1: +22990123456 -> {'✅ Valide' if is_valid1 else '❌ Invalide'}")
    
    if not is_valid1:
        print(f"    Erreurs: {form1.errors}")
    
    # Test 2: Numéro invalide (pas de +)
    form_data2 = {
        'username': 'test_user2',
        'email': 'test2@example.com',
        'telephone': '22990123456',
        'groupe_travail': groupe.id,
        'password': 'testpass123',
        'password_confirm': 'testpass123'
    }
    
    form2 = UtilisateurForm(data=form_data2)
    is_valid2 = form2.is_valid()
    print(f"Test 2: 22990123456 -> {'✅ Valide' if is_valid2 else '❌ Invalide'}")
    
    if not is_valid2:
        print(f"    Erreurs: {form2.errors}")
    
    # Test 3: Numéro avec espaces
    form_data3 = {
        'username': 'test_user3',
        'email': 'test3@example.com',
        'telephone': '+229 90 12 34 56',
        'groupe_travail': groupe.id,
        'password': 'testpass123',
        'password_confirm': 'testpass123'
    }
    
    form3 = UtilisateurForm(data=form_data3)
    is_valid3 = form3.is_valid()
    print(f"Test 3: +229 90 12 34 56 -> {'✅ Valide' if is_valid3 else '❌ Invalide'}")
    
    if not is_valid3:
        print(f"    Erreurs: {form3.errors}")
    
    # Test 4: Numéro trop court
    form_data4 = {
        'username': 'test_user4',
        'email': 'test4@example.com',
        'telephone': '+12345678',
        'groupe_travail': groupe.id,
        'password': 'testpass123',
        'password_confirm': 'testpass123'
    }
    
    form4 = UtilisateurForm(data=form_data4)
    is_valid4 = form4.is_valid()
    print(f"Test 4: +12345678 -> {'✅ Valide' if is_valid4 else '❌ Invalide'}")
    
    if not is_valid4:
        print(f"    Erreurs: {form4.errors}")
    
    print("\n=== RÉSULTATS ===")
    print("Le formulaire fonctionne correctement si:")
    print("- Test 1: ✅ (numéro valide)")
    print("- Test 2: ❌ (pas de +)")
    print("- Test 3: ❌ (avec espaces)")
    print("- Test 4: ❌ (trop court)")

if __name__ == '__main__':
    test_form_validation()
