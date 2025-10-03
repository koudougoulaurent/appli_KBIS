# Test de réservation - à exécuter dans le shell Django
from proprietes.models import UniteLocative, Locataire, ReservationUnite
from proprietes.forms_unites import ReservationUniteForm
from datetime import datetime, timedelta

print("=== TEST DE RÉSERVATION ===")

# Vérifier les données
unites = UniteLocative.objects.filter(is_deleted=False, statut='disponible')
locataires = Locataire.objects.filter(is_deleted=False, statut='actif')

print(f"Unités disponibles: {unites.count()}")
print(f"Locataires actifs: {locataires.count()}")

if unites.exists() and locataires.exists():
    unite = unites.first()
    locataire = locataires.first()
    
    print(f"Unité test: {unite.numero_unite}")
    print(f"Locataire test: {locataire.nom} {locataire.prenom}")
    
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
    print(f"Formulaire valide: {form.is_valid()}")
    
    if not form.is_valid():
        print("Erreurs du formulaire:")
        for field, errors in form.errors.items():
            print(f"  {field}: {errors}")
    else:
        print("Formulaire valide!")
else:
    print("Données insuffisantes pour le test")
