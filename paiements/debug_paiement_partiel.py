"""
Module de debugging pour paiements partiels
"""

def log_paiement_partiel_post(request, form):
    """Affiche les données POST et erreurs formulaire"""
    print("="*80)
    print("🔍 DEBUG PAIEMENT PARTIEL")
    print(f"  POST mois_paye: {request.POST.get('mois_paye')}")
    print(f"  POST annee_paiement: {request.POST.get('annee_paiement')}")
    print(f"  Form valid: {form.is_valid()}")
    if not form.is_valid():
        print(f"  Form errors: {form.errors}")
    if form.is_valid():
        print(f"  CLEANED mois_paye: {form.cleaned_data.get('mois_paye')}")
    print("="*80)
