from django.shortcuts import render
from django import forms

class TestPhoneForm(forms.Form):
    telephone = forms.CharField(
        label="Téléphone",
        max_length=15,
        required=False,
        help_text="Sélectionnez d'abord un pays"
    )
    
    telephone_required = forms.CharField(
        label="Téléphone (Requis)",
        max_length=15,
        required=True,
        help_text="Ce champ est obligatoire"
    )

def test_mobile_phone(request):
    """Vue pour tester le widget téléphone sur mobile"""
    if request.method == 'POST':
        form = TestPhoneForm(request.POST)
        if form.is_valid():
            # Traitement du formulaire
            pass
    else:
        form = TestPhoneForm()
    
    # Créer des champs pour le template
    phone_field = form['telephone']
    phone_required_field = form['telephone_required']
    
    context = {
        'phone_field': phone_field,
        'phone_required_field': phone_required_field,
    }
    
    return render(request, 'test_mobile_phone.html', context)

