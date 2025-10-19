from django import forms
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import date
from .models_avance import AvanceLoyer
from .models import Paiement
from contrats.models import Contrat


class AvanceLoyerForm(forms.ModelForm):
    """
    Formulaire pour créer une avance de loyer avec sélection manuelle des mois
    """
    
    # *** NOUVEAUX CHAMPS POUR LA SÉLECTION MANUELLE ***
    mode_selection_mois = forms.ChoiceField(
        choices=AvanceLoyer.MODE_SELECTION_CHOICES,
        initial='automatique',
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input',
            'id': 'id_mode_selection'
        }),
        label="Mode de sélection des mois",
        help_text="Choisissez comment déterminer les mois couverts par cette avance"
    )
    
    mois_couverts_manuels = forms.CharField(
        required=False,
        widget=forms.HiddenInput(attrs={
            'id': 'id_mois_couverts_manuels'
        }),
        label="Mois couverts sélectionnés"
    )
    
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
        mode_selection = cleaned_data.get('mode_selection_mois')
        mois_couverts_manuels = cleaned_data.get('mois_couverts_manuels')
        
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
            
            # *** NOUVELLE VALIDATION : Mode de sélection manuelle ***
            if mode_selection == 'manuel':
                if not mois_couverts_manuels:
                    raise ValidationError("Veuillez sélectionner au moins un mois en mode manuel.")
                
                # Parser les mois sélectionnés
                try:
                    import json
                    mois_liste = json.loads(mois_couverts_manuels) if mois_couverts_manuels else []
                    
                    if not mois_liste:
                        raise ValidationError("Aucun mois sélectionné.")
                    
                    # Vérifier que le montant est suffisant pour tous les mois sélectionnés
                    montant_requis = loyer_mensuel * len(mois_liste)
                    if montant_avance < montant_requis:
                        raise ValidationError(
                            f"Le montant de l'avance ({montant_avance:,.0f} F CFA) est insuffisant pour couvrir "
                            f"{len(mois_liste)} mois. Montant requis : {montant_requis:,.0f} F CFA."
                        )
                    
                    # Valider le format des dates
                    for mois_str in mois_liste:
                        try:
                            from datetime import datetime
                            datetime.strptime(mois_str, '%Y-%m-%d')
                        except ValueError:
                            raise ValidationError(f"Format de date invalide : {mois_str}")
                    
                except json.JSONDecodeError:
                    raise ValidationError("Format des mois sélectionnés invalide.")
        
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
    
    def calculer_mois_et_reste(self, contrat, montant_avance):
        """
        Calcule automatiquement le nombre de mois couverts et le reste
        """
        if not contrat or not montant_avance:
            return 0, Decimal('0')
        
        try:
            loyer_mensuel = Decimal(str(contrat.loyer_mensuel)) if contrat.loyer_mensuel else Decimal('0')
        except (ValueError, TypeError, AttributeError):
            loyer_mensuel = Decimal('0')
        
        if loyer_mensuel <= 0:
            return 0, montant_avance
        
        # Calculer le nombre de mois couverts (division entière)
        nombre_mois = int(montant_avance // loyer_mensuel)
        
        # Calculer le reste
        reste = montant_avance % loyer_mensuel
        
        return nombre_mois, reste


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
