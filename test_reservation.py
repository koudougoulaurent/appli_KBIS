#!/usr/bin/env python
"""
Script de test pour vérifier le fonctionnement de la réservation d'unité
"""
import os
import sys
import django
from datetime import datetime, timedelta

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'appli_KBIS.settings')
django.setup()

from proprietes.models import UniteLocative, Locataire, ReservationUnite
from proprietes.forms_unites import ReservationUniteForm

def test_reservation_form():
    """Test du formulaire de réservation"""
    print("🚀 TEST DU FORMULAIRE DE RÉSERVATION")
    print("=" * 50)
    
    # Vérifier qu'il y a des unités disponibles
    unites_disponibles = UniteLocative.objects.filter(
        is_deleted=False, 
        statut='disponible'
    )
    print(f"✅ Unités disponibles: {unites_disponibles.count()}")
    
    if unites_disponibles.exists():
        unite = unites_disponibles.first()
        print(f"   - Unité test: {unite.numero_unite} ({unite.nom})")
    else:
        print("❌ Aucune unité disponible pour le test")
        return False
    
    # Vérifier qu'il y a des locataires actifs
    locataires_actifs = Locataire.objects.filter(
        is_deleted=False, 
        statut='actif'
    )
    print(f"✅ Locataires actifs: {locataires_actifs.count()}")
    
    if locataires_actifs.exists():
        locataire = locataires_actifs.first()
        print(f"   - Locataire test: {locataire.nom} {locataire.prenom}")
    else:
        print("❌ Aucun locataire actif pour le test")
        return False
    
    # Test du formulaire avec données valides
    print("\n📝 Test du formulaire avec données valides...")
    
    data = {
        'unite_locative': unite.pk,
        'locataire_potentiel': locataire.pk,
        'date_debut_souhaitee': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
        'date_fin_prevue': (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'),
        'statut': 'en_attente',
        'montant_reservation': '50000.00',
        'date_expiration': (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%dT%H:%M'),
        'notes': 'Test de réservation automatique',
        'convertir_en_contrat': False
    }
    
    form = ReservationUniteForm(data, unite_locative=unite)
    
    print(f"   - Formulaire valide: {form.is_valid()}")
    
    if not form.is_valid():
        print("❌ Erreurs du formulaire:")
        for field, errors in form.errors.items():
            print(f"   - {field}: {errors}")
        return False
    else:
        print("✅ Formulaire valide!")
        
        # Test de sauvegarde
        try:
            reservation = form.save(commit=False)
            reservation.unite_locative = unite
            reservation.save()
            print(f"✅ Réservation créée avec succès: ID {reservation.pk}")
            
            # Nettoyer le test
            reservation.delete()
            print("✅ Test nettoyé")
            return True
            
        except Exception as e:
            print(f"❌ Erreur lors de la sauvegarde: {str(e)}")
            return False

def test_reservation_errors():
    """Test des erreurs du formulaire"""
    print("\n🔍 TEST DES ERREURS DU FORMULAIRE")
    print("=" * 50)
    
    # Test avec données invalides
    data_invalide = {
        'unite_locative': '',
        'locataire_potentiel': '',
        'date_debut_souhaitee': '',
        'statut': '',
        'date_expiration': '',
    }
    
    form = ReservationUniteForm(data_invalide)
    print(f"   - Formulaire invalide (attendu): {not form.is_valid()}")
    
    if not form.is_valid():
        print("✅ Erreurs détectées correctement:")
        for field, errors in form.errors.items():
            print(f"   - {field}: {errors}")
        return True
    else:
        print("❌ Le formulaire devrait être invalide!")
        return False

if __name__ == "__main__":
    print("🎯 DÉMARRAGE DES TESTS DE RÉSERVATION")
    print("=" * 60)
    
    success = True
    
    # Test 1: Formulaire valide
    if not test_reservation_form():
        success = False
    
    # Test 2: Gestion des erreurs
    if not test_reservation_errors():
        success = False
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 TOUS LES TESTS SONT PASSÉS!")
        print("✅ Le système de réservation fonctionne correctement.")
    else:
        print("❌ CERTAINS TESTS ONT ÉCHOUÉ!")
        print("🔧 Vérifiez les erreurs ci-dessus.")
    
    print("=" * 60)
