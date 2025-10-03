#!/usr/bin/env python
"""
Test simple de la réservation via le shell Django
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'appli_KBIS.settings')
django.setup()

def test_reservation_simple():
    """Test simple de la réservation"""
    print("🚀 TEST SIMPLE DE RÉSERVATION")
    print("=" * 40)
    
    try:
        from proprietes.models import UniteLocative, Locataire, ReservationUnite
        from proprietes.forms_unites import ReservationUniteForm
        from datetime import datetime, timedelta
        
        # Vérifier les données
        unites = UniteLocative.objects.filter(is_deleted=False, statut='disponible')
        locataires = Locataire.objects.filter(is_deleted=False, statut='actif')
        
        print(f"✅ Unités disponibles: {unites.count()}")
        print(f"✅ Locataires actifs: {locataires.count()}")
        
        if unites.exists() and locataires.exists():
            unite = unites.first()
            locataire = locataires.first()
            
            print(f"   - Unité: {unite.numero_unite}")
            print(f"   - Locataire: {locataire.nom} {locataire.prenom}")
            
            # Test du formulaire
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
            print(f"✅ Formulaire valide: {form.is_valid()}")
            
            if not form.is_valid():
                print("❌ Erreurs:")
                for field, errors in form.errors.items():
                    print(f"   - {field}: {errors}")
            else:
                print("🎉 Le formulaire fonctionne correctement!")
                
        else:
            print("❌ Données insuffisantes pour le test")
            
    except Exception as e:
        print(f"❌ Erreur: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_reservation_simple()
