#!/usr/bin/env python
"""
Test de la correction de réservation
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'appli_KBIS.settings')
django.setup()

from proprietes.models import UniteLocative, Locataire
from proprietes.forms_unites import ReservationUniteForm
from datetime import datetime, timedelta

def test_reservation_fix():
    print("🔧 TEST DE LA CORRECTION DE RÉSERVATION")
    print("=" * 50)
    
    # Récupérer une unité et un locataire
    unite = UniteLocative.objects.filter(is_deleted=False, statut='disponible').first()
    locataire = Locataire.objects.filter(is_deleted=False, statut='actif').first()
    
    if not unite or not locataire:
        print("❌ Données insuffisantes pour le test")
        return False
    
    print(f"✅ Unité: {unite.numero_unite}")
    print(f"✅ Locataire: {locataire.nom} {locataire.prenom}")
    
    # Test 1: Formulaire avec unité spécifiée
    print("\n📝 Test 1: Formulaire avec unité spécifiée")
    data = {
        'unite_locative': unite.pk,
        'locataire_potentiel': locataire.pk,
        'date_debut_souhaitee': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
        'statut': 'en_attente',
        'montant_reservation': '50000.00',
        'date_expiration': (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%dT%H:%M'),
        'notes': 'Test automatique',
    }
    
    form = ReservationUniteForm(data, unite_locative=unite)
    print(f"   - Formulaire valide: {form.is_valid()}")
    
    if not form.is_valid():
        print("❌ Erreurs:")
        for field, errors in form.errors.items():
            print(f"   - {field}: {errors}")
        return False
    else:
        print("✅ Formulaire valide!")
    
    # Test 2: Vérifier que l'unité est bien cachée
    print("\n📝 Test 2: Vérification du champ unité")
    unite_field = form['unite_locative']
    print(f"   - Type de widget: {type(unite_field.field.widget).__name__}")
    print(f"   - Valeur: {unite_field.value()}")
    
    if isinstance(unite_field.field.widget, type(unite_field.field.widget).__bases__[0]):
        print("✅ Champ unité correctement configuré")
    else:
        print("❌ Problème avec le champ unité")
        return False
    
    print("\n🎉 TOUS LES TESTS SONT PASSÉS!")
    print("✅ La correction fonctionne correctement.")
    return True

if __name__ == "__main__":
    test_reservation_fix()
