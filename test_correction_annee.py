"""
Script de test pour vérifier la correction de la gestion de l'année
dans les paiements partiels
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from paiements.services_paiement_partiel import ServicePaiementPartiel
from datetime import date

# Test 1: Convertir "novembre" sans année
print("=" * 80)
print("TEST 1: Convertir 'novembre' (sans année)")
print("=" * 80)
result1 = ServicePaiementPartiel.convertir_mois_paye_en_date("novembre")
print(f"Résultat: {result1}")
print(f"Devrait être: novembre 2026 (année courante)")
print()

# Test 2: Convertir "novembre 2025" avec année
print("=" * 80)
print("TEST 2: Convertir 'novembre 2025' (avec année)")
print("=" * 80)
result2 = ServicePaiementPartiel.convertir_mois_paye_en_date("novembre 2025")
print(f"Résultat: {result2}")
print(f"Devrait être: 2025-11-01")
print()

# Test 3: Simulation de ce qui se passe dans views.py
print("=" * 80)
print("TEST 3: Simulation views.py - avec année sélectionnée")
print("=" * 80)
mois_paye_nom = "novembre"
annee_selectionnee = "2025"

import re
if not re.search(r'\d{4}', mois_paye_nom):
    if annee_selectionnee:
        mois_paye_nom = f"{mois_paye_nom} {annee_selectionnee}"
        print(f"Année ajoutée: {mois_paye_nom}")
    else:
        from datetime import datetime
        annee_actuelle = datetime.now().year
        mois_paye_nom = f"{mois_paye_nom} {annee_actuelle}"
        print(f"Année courante utilisée: {mois_paye_nom}")

result3 = ServicePaiementPartiel.convertir_mois_paye_en_date(mois_paye_nom)
print(f"Résultat final: {result3}")
print(f"Devrait être: 2025-11-01")
print()

# Test 4: Validation avec WARMA MARIAM (contrat 129)
print("=" * 80)
print("TEST 4: Validation pour WARMA MARIAM (contrat 129)")
print("=" * 80)
try:
    from contrats.models import Contrat
    contrat = Contrat.objects.get(id=129)
    
    # Déterminer le mois attendu
    mois_attendu = ServicePaiementPartiel.determiner_mois_a_regler(contrat)
    print(f"Mois attendu: {mois_attendu['mois_paye']}")
    
    # Tester avec novembre 2025
    validation = ServicePaiementPartiel.valider_mois_a_regler(
        contrat, "novembre 2025", "loyer"
    )
    print(f"Validation pour 'novembre 2025': {validation['valide']}")
    if not validation['valide']:
        print(f"Message: {validation['message']}")
    
    # Tester avec novembre 2026
    validation2 = ServicePaiementPartiel.valider_mois_a_regler(
        contrat, "novembre 2026", "loyer"
    )
    print(f"Validation pour 'novembre 2026': {validation2['valide']}")
    if not validation2['valide']:
        print(f"Message: {validation2['message']}")
    
except Exception as e:
    print(f"Erreur lors du test: {str(e)}")

print("\n" + "=" * 80)
print("TESTS TERMINÉS")
print("=" * 80)
