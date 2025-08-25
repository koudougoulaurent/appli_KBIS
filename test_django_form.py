#!/usr/bin/env python3
"""
Test Django du formulaire complet
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')

try:
    django.setup()
    print("✅ Django configuré avec succès")
except Exception as e:
    print(f"❌ Erreur Django: {e}")
    sys.exit(1)

try:
    from utilisateurs.forms import UtilisateurForm
    from utilisateurs.models import GroupeTravail
    print("✅ Imports réussis")
except Exception as e:
    print(f"❌ Erreur d'import: {e}")
    sys.exit(1)

def test_django_form():
    """Test du formulaire Django complet"""
    
    print("\n=== TEST DU FORMULAIRE DJANGO ===\n")
    
    # Créer un groupe de travail pour les tests
    try:
        groupe, created = GroupeTravail.objects.get_or_create(
            nom='ADMINISTRATION',
            defaults={'description': 'Groupe pour les tests'}
        )
        print(f"✅ Groupe de travail: {groupe.nom}")
    except Exception as e:
        print(f"❌ Erreur création groupe: {e}")
        return
    
    # Test 1: Numéro valide avec code pays automatique
    print("\n--- Test 1: Numéro local seulement ---")
    form_data1 = {
        'username': 'test_user1',
        'email': 'test1@example.com',
        'telephone': '90123456',  # Seulement le numéro local
        'country_code': '229',    # Bénin
        'groupe_travail': groupe.id,
        'password': 'testpass123',
        'password_confirm': 'testpass123'
    }
    
    form1 = UtilisateurForm(data=form_data1)
    is_valid1 = form1.is_valid()
    print(f"Formulaire valide: {'✅ OUI' if is_valid1 else '❌ NON'}")
    
    if is_valid1:
        print(f"Téléphone nettoyé: {form1.cleaned_data.get('telephone')}")
    else:
        print(f"Erreurs: {form1.errors}")
    
    # Test 2: Numéro avec espaces
    print("\n--- Test 2: Numéro avec espaces ---")
    form_data2 = {
        'username': 'test_user2',
        'email': 'test2@example.com',
        'telephone': '+229 90 12 34 56',  # Avec espaces
        'country_code': '229',
        'groupe_travail': groupe.id,
        'password': 'testpass123',
        'password_confirm': 'testpass123'
    }
    
    form2 = UtilisateurForm(data=form_data2)
    is_valid2 = form2.is_valid()
    print(f"Formulaire valide: {'✅ OUI' if is_valid2 else '❌ NON'}")
    
    if is_valid2:
        print(f"Téléphone nettoyé: {form2.cleaned_data.get('telephone')}")
    else:
        print(f"Erreurs: {form2.errors}")
    
    # Test 3: Numéro complet déjà saisi
    print("\n--- Test 3: Numéro complet déjà saisi ---")
    form_data3 = {
        'username': 'test_user3',
        'email': 'test3@example.com',
        'telephone': '+22990123456',  # Code pays déjà inclus
        'country_code': '229',
        'groupe_travail': groupe.id,
        'password': 'testpass123',
        'password_confirm': 'testpass123'
    }
    
    form3 = UtilisateurForm(data=form_data3)
    is_valid3 = form3.is_valid()
    print(f"Formulaire valide: {'✅ OUI' if is_valid3 else '❌ NON'}")
    
    if is_valid3:
        print(f"Téléphone nettoyé: {form3.cleaned_data.get('telephone')}")
    else:
        print(f"Erreurs: {form3.errors}")
    
    print("\n=== RÉSULTATS ===")
    if is_valid1 and is_valid2 and is_valid3:
        print("🎉 TOUS LES TESTS PASSENT ! Le formulaire fonctionne parfaitement.")
    else:
        print("❌ Certains tests ont échoué. Vérifiez les erreurs ci-dessus.")

if __name__ == '__main__':
    test_django_form()
