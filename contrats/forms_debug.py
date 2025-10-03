"""
Formulaire de débogage pour les contrats
"""

from django import forms
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from .models import Contrat
from proprietes.models import Propriete, Locataire


class ContratFormDebug(forms.ModelForm):
    """Formulaire de débogage pour créer/modifier un contrat de bail"""
    
    class Meta:
        model = Contrat
        fields = [
            'propriete',
            'locataire', 
            'date_debut',
            'date_fin',
            'date_signature',
            'loyer_mensuel',
            'charges_mensuelles',
            'depot_garantie',
            'avance_loyer',
            'notes'
        ]
        
        widgets = {
            'propriete': forms.Select(attrs={'class': 'form-select'}),
            'locataire': forms.Select(attrs={'class': 'form-select'}),
            'date_debut': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'date_fin': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'date_signature': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'loyer_mensuel': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'charges_mensuelles': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'depot_garantie': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'avance_loyer': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Remplir les choix pour propriété et locataire
        self.fields['propriete'].queryset = Propriete.objects.filter(is_deleted=False)
        self.fields['locataire'].queryset = Locataire.objects.filter(is_deleted=False)
        
        # Définir des valeurs par défaut
        if not self.instance.pk:
            self.fields['date_debut'].initial = timezone.now().date()
            self.fields['date_signature'].initial = timezone.now().date()
            self.fields['loyer_mensuel'].initial = 0
            self.fields['charges_mensuelles'].initial = 0
            self.fields['depot_garantie'].initial = 0
            self.fields['avance_loyer'].initial = 0
    
    def clean(self):
        cleaned_data = super().clean()
        date_debut = cleaned_data.get('date_debut')
        date_fin = cleaned_data.get('date_fin')
        
        if date_debut and date_fin and date_fin <= date_debut:
            raise forms.ValidationError("La date de fin doit être postérieure à la date de début.")
        
        if date_debut and date_debut < timezone.now().date():
            raise forms.ValidationError("La date de début ne peut pas être dans le passé.")
        
        return cleaned_data
