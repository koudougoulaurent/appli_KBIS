"""
Script pour vérifier toutes les avances du contrat 6
"""

import os
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from paiements.models import Paiement
from paiements.models_avance import AvanceLoyer
from contrats.models import Contrat

# Contrat 6
contrat = Contrat.objects.get(id=6)

print("=" * 80)
print(f"📋 ANALYSE DES AVANCES POUR LE CONTRAT {contrat}")
print("=" * 80)

# Toutes les avances (actives et inactives)
toutes_avances = AvanceLoyer.objects.filter(contrat=contrat).order_by('-date_avance')

print(f"\n🏦 TOUTES LES AVANCES (actives et inactives): {toutes_avances.count()}")
for avance in toutes_avances:
    print(f"\n   Avance ID {avance.id}:")
    print(f"   - Date: {avance.date_avance}")
    print(f"   - Montant: {avance.montant_avance:,.0f} F CFA")
    print(f"   - Loyer mensuel: {avance.loyer_mensuel:,.0f} F CFA")
    print(f"   - Nombre de mois couverts: {avance.nombre_mois_couverts}")
    print(f"   - Montant restant: {avance.montant_restant:,.0f} F CFA")
    print(f"   - Statut: {avance.statut}")
    print(f"   - Début couverture: {avance.mois_debut_couverture}")
    print(f"   - Fin couverture: {avance.mois_fin_couverture}")

# Tous les paiements pour ce contrat
print(f"\n\n💰 TOUS LES PAIEMENTS POUR CE CONTRAT:")
paiements = Paiement.objects.filter(contrat=contrat, is_deleted=False).order_by('-date_paiement')[:15]

for p in paiements:
    print(f"   {p.date_paiement} - {p.montant:,.0f} F - {p.type_paiement} - {p.mois_paye or 'N/A'} - {p.statut}")
