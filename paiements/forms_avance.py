from django import forms
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import date
from .models_avance import AvanceLoyer
from .models import Paiement
from contrats.models import Contrat


class AvanceLoyerForm(forms.ModelForm):
    """
    Formulaire pour créer une avance de loyer
    """
    
    class Meta:
        model = AvanceLoyer
        fields = ['contrat', 'montant_avance', 'date_avance', 'notes']
        widgets = {
            'contrat': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_contrat_avance'
            }),
            'montant_avance': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01',
                'id': 'id_montant_avance'
            }),
            'date_avance': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'id': 'id_date_avance'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'id': 'id_notes_avance'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filtrer les contrats actifs
        self.fields['contrat'].queryset = Contrat.objects.filter(
            est_actif=True,
            est_resilie=False
        ).select_related('locataire', 'propriete')
        
        # Valeur par défaut pour la date
        if not self.instance.pk:
            self.fields['date_avance'].initial = date.today()
    
    def clean_montant_avance(self):
        montant = self.cleaned_data.get('montant_avance')
        if montant and montant <= 0:
            raise ValidationError("Le montant de l'avance doit être positif.")
        return montant
    
    def clean(self):
        cleaned_data = super().clean()
        contrat = cleaned_data.get('contrat')
        montant_avance = cleaned_data.get('montant_avance')
        
        if contrat and montant_avance:
            # Convertir le loyer mensuel en Decimal pour la comparaison
            try:
                if contrat.loyer_mensuel is None or contrat.loyer_mensuel == '':
                    loyer_mensuel = Decimal('0')
                else:
                    loyer_mensuel = Decimal(str(contrat.loyer_mensuel))
            except (ValueError, TypeError, AttributeError):
                loyer_mensuel = Decimal('0')
            
            # Vérifier que le contrat a un loyer mensuel défini
            if not contrat.loyer_mensuel or loyer_mensuel <= 0:
                raise ValidationError("Le contrat sélectionné n'a pas de loyer mensuel défini.")
            
            # Vérifier que l'avance est suffisante pour au moins un mois
            if montant_avance < loyer_mensuel:
                raise ValidationError(
                    f"L'avance doit être au moins égale au loyer mensuel ({loyer_mensuel} F CFA)."
                )
        
        return cleaned_data


class PaiementAvanceForm(forms.ModelForm):
    """
    Formulaire pour enregistrer un paiement d'avance
    """
    
    class Meta:
        model = Paiement
        fields = ['contrat', 'montant', 'mode_paiement', 'date_paiement', 'notes']
        widgets = {
            'contrat': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_contrat_paiement'
            }),
            'montant': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01',
                'id': 'id_montant_paiement'
            }),
            'mode_paiement': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_mode_paiement'
            }),
            'date_paiement': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'id': 'id_date_paiement'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'id': 'id_notes_paiement'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filtrer les contrats actifs
        self.fields['contrat'].queryset = Contrat.objects.filter(
            est_actif=True,
            est_resilie=False
        ).select_related('locataire', 'propriete')
        
        # Valeur par défaut pour la date
        if not self.instance.pk:
            self.fields['date_paiement'].initial = date.today()
    
    def clean_montant(self):
        montant = self.cleaned_data.get('montant')
        if montant and montant <= 0:
            raise ValidationError("Le montant du paiement doit être positif.")
        return montant
    
    def clean(self):
        cleaned_data = super().clean()
        contrat = cleaned_data.get('contrat')
        montant = cleaned_data.get('montant')
        
        if contrat and montant:
            # Convertir le loyer mensuel en Decimal pour la comparaison
            try:
                if contrat.loyer_mensuel is None or contrat.loyer_mensuel == '':
                    loyer_mensuel = Decimal('0')
                else:
                    loyer_mensuel = Decimal(str(contrat.loyer_mensuel))
            except (ValueError, TypeError, AttributeError):
                loyer_mensuel = Decimal('0')
            
            # Vérifier que le contrat a un loyer mensuel défini
            if not contrat.loyer_mensuel or loyer_mensuel <= 0:
                raise ValidationError("Le contrat sélectionné n'a pas de loyer mensuel défini.")
            
            # Vérifier que le paiement est suffisant pour au moins un mois
            if montant < loyer_mensuel:
                raise ValidationError(
                    f"Le paiement doit être au moins égal au loyer mensuel ({loyer_mensuel} F CFA)."
                )
        
        return cleaned_data


class FiltreAvanceForm(forms.Form):
    """
    Formulaire de filtrage des avances
    """
    contrat = forms.ModelChoiceField(
        queryset=Contrat.objects.filter(est_actif=True).select_related('locataire', 'propriete'),
        required=False,
        empty_label="Tous les contrats",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    statut = forms.ChoiceField(
        choices=[
            ('', 'Tous les statuts'),
            ('active', 'Active'),
            ('epuisee', 'Épuisée'),
            ('annulee', 'Annulée'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    mois_debut = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'month'
        })
    )
    
    mois_fin = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'month'
        })
    )


class FiltreHistoriqueForm(forms.Form):
    """
    Formulaire de filtrage de l'historique des paiements
    """
    mois_debut = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'month'
        })
    )
    
    mois_fin = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'month'
        })
    )
