"""
Formulaires spécialisés pour le système de paiement partiel
"""

from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
from .models_partial_payment import PlanPaiementPartiel, EchelonPaiement, PaiementPartiel
from contrats.models import Contrat
from paiements.models import Paiement
import datetime


class PlanPaiementPartielForm(forms.ModelForm):
    """Formulaire pour créer/modifier un plan de paiement partiel"""
    
    class Meta:
        model = PlanPaiementPartiel
        fields = [
            'contrat', 'nom_plan', 'description', 'montant_total',
            'date_debut', 'date_fin_prevue', 'statut'
        ]
        widgets = {
            'contrat': forms.Select(attrs={
                'class': 'form-control select2',
                'data-placeholder': 'Sélectionner un contrat'
            }),
            'nom_plan': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Plan de paiement échelonné - Janvier 2025'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Description détaillée du plan de paiement'
            }),
            'montant_total': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01'
            }),
            'date_debut': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'date_fin_prevue': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'statut': forms.Select(attrs={
                'class': 'form-control'
            })
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filtrer les contrats actifs
        if user:
            self.fields['contrat'].queryset = Contrat.objects.filter(
                is_deleted=False
            ).select_related('locataire', 'propriete')
        
        # Ajouter des classes CSS
        for field_name, field in self.fields.items():
            if field_name not in self.Meta.widgets:
                field.widget.attrs.update({'class': 'form-control'})
    
    def clean(self):
        cleaned_data = super().clean()
        date_debut = cleaned_data.get('date_debut')
        date_fin_prevue = cleaned_data.get('date_fin_prevue')
        montant_total = cleaned_data.get('montant_total')
        
        # Vérifier que la date de fin est après la date de début
        if date_debut and date_fin_prevue:
            if date_fin_prevue <= date_debut:
                raise ValidationError(
                    "La date de fin prévue doit être postérieure à la date de début."
                )
        
        # Vérifier que le montant total est positif
        if montant_total and montant_total <= 0:
            raise ValidationError(
                "Le montant total doit être supérieur à zéro."
            )
        
        return cleaned_data


class EchelonPaiementForm(forms.ModelForm):
    """Formulaire pour créer/modifier un échelon de paiement"""
    
    class Meta:
        model = EchelonPaiement
        fields = ['numero_echelon', 'montant', 'date_echeance', 'statut']
        widgets = {
            'numero_echelon': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1'
            }),
            'montant': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01'
            }),
            'date_echeance': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'statut': forms.Select(attrs={
                'class': 'form-control'
            })
        }
    
    def __init__(self, *args, **kwargs):
        plan = kwargs.pop('plan', None)
        super().__init__(*args, **kwargs)
        
        if plan:
            self.fields['numero_echelon'].initial = plan.echelons.count() + 1
        
        # Ajouter des classes CSS
        for field_name, field in self.fields.items():
            if field_name not in self.Meta.widgets:
                field.widget.attrs.update({'class': 'form-control'})
    
    def clean(self):
        cleaned_data = super().clean()
        numero_echelon = cleaned_data.get('numero_echelon')
        montant = cleaned_data.get('montant')
        date_echeance = cleaned_data.get('date_echeance')
        
        # Vérifier que le montant est positif
        if montant and montant <= 0:
            raise ValidationError(
                "Le montant de l'échelon doit être supérieur à zéro."
            )
        
        # Vérifier que la date d'échéance est dans le futur
        if date_echeance and date_echeance < timezone.now().date():
            raise ValidationError(
                "La date d'échéance ne peut pas être dans le passé."
            )
        
        return cleaned_data


class PaiementPartielForm(forms.ModelForm):
    """Formulaire pour créer un paiement partiel"""
    
    class Meta:
        model = PaiementPartiel
        fields = ['plan', 'echelon', 'montant', 'motif', 'description']
        widgets = {
            'plan': forms.Select(attrs={
                'class': 'form-control select2',
                'data-placeholder': 'Sélectionner un plan'
            }),
            'echelon': forms.Select(attrs={
                'class': 'form-control select2',
                'data-placeholder': 'Sélectionner un échelon (optionnel)'
            }),
            'montant': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01'
            }),
            'motif': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Paiement partiel du loyer de janvier'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Description détaillée du paiement partiel'
            })
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filtrer les plans actifs
        if user:
            self.fields['plan'].queryset = PlanPaiementPartiel.objects.filter(
                is_deleted=False,
                statut__in=['actif', 'suspendu']
            ).select_related('contrat')
        
        # Ajouter des classes CSS
        for field_name, field in self.fields.items():
            if field_name not in self.Meta.widgets:
                field.widget.attrs.update({'class': 'form-control'})
    
    def clean(self):
        cleaned_data = super().clean()
        plan = cleaned_data.get('plan')
        echelon = cleaned_data.get('echelon')
        montant = cleaned_data.get('montant')
        
        # Vérifier que le montant est positif
        if montant and montant <= 0:
            raise ValidationError(
                "Le montant du paiement partiel doit être supérieur à zéro."
            )
        
        # Vérifier que le montant ne dépasse pas le montant restant du plan
        if plan and montant:
            if montant > plan.montant_restant:
                raise ValidationError(
                    f"Le montant du paiement partiel ({montant} FCFA) ne peut pas "
                    f"dépasser le montant restant du plan ({plan.montant_restant} FCFA)."
                )
        
        # Vérifier que l'échelon appartient au plan
        if plan and echelon:
            if echelon.plan != plan:
                raise ValidationError(
                    "L'échelon sélectionné n'appartient pas au plan sélectionné."
                )
        
        return cleaned_data


class RecherchePaiementPartielForm(forms.Form):
    """Formulaire de recherche pour les paiements partiels"""
    
    # Filtres de base
    contrat = forms.ModelChoiceField(
        queryset=Contrat.objects.filter(is_deleted=False),
        required=False,
        empty_label="Tous les contrats",
        widget=forms.Select(attrs={
            'class': 'form-control select2',
            'data-placeholder': 'Filtrer par contrat'
        })
    )
    
    plan = forms.ModelChoiceField(
        queryset=PlanPaiementPartiel.objects.filter(is_deleted=False),
        required=False,
        empty_label="Tous les plans",
        widget=forms.Select(attrs={
            'class': 'form-control select2',
            'data-placeholder': 'Filtrer par plan'
        })
    )
    
    statut = forms.ChoiceField(
        choices=[
            ('', 'Tous les statuts'),
            ('actif', 'Actif'),
            ('suspendu', 'Suspendu'),
            ('termine', 'Terminé'),
            ('annule', 'Annulé'),
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    # Filtres de date
    date_debut = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    date_fin = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    # Filtres de montant
    montant_min = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0',
            'placeholder': 'Montant minimum'
        })
    )
    
    montant_max = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0',
            'placeholder': 'Montant maximum'
        })
    )
    
    # Recherche textuelle
    recherche = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Rechercher par nom, numéro, description...'
        })
    )
    
    def clean(self):
        cleaned_data = super().clean()
        date_debut = cleaned_data.get('date_debut')
        date_fin = cleaned_data.get('date_fin')
        montant_min = cleaned_data.get('montant_min')
        montant_max = cleaned_data.get('montant_max')
        
        # Vérifier que la date de fin est après la date de début
        if date_debut and date_fin:
            if date_fin < date_debut:
                raise ValidationError(
                    "La date de fin doit être postérieure à la date de début."
                )
        
        # Vérifier que le montant maximum est supérieur au montant minimum
        if montant_min and montant_max:
            if montant_max < montant_min:
                raise ValidationError(
                    "Le montant maximum doit être supérieur au montant minimum."
                )
        
        return cleaned_data


class GenerationEchelonsForm(forms.Form):
    """Formulaire pour générer automatiquement des échelons"""
    
    plan = forms.ModelChoiceField(
        queryset=PlanPaiementPartiel.objects.filter(is_deleted=False),
        widget=forms.HiddenInput()
    )
    
    nombre_echelons = forms.IntegerField(
        min_value=2,
        max_value=12,
        initial=3,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '2',
            'max': '12'
        })
    )
    
    type_generation = forms.ChoiceField(
        choices=[
            ('egal', 'Montants égaux'),
            ('decroissant', 'Montants décroissants'),
            ('croissant', 'Montants croissants'),
            ('personnalise', 'Personnalisé'),
        ],
        initial='egal',
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input'
        })
    )
    
    date_premier_echelon = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    intervalle_jours = forms.IntegerField(
        min_value=1,
        max_value=365,
        initial=30,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '1',
            'max': '365'
        })
    )
    
    def clean(self):
        cleaned_data = super().clean()
        nombre_echelons = cleaned_data.get('nombre_echelons')
        plan = cleaned_data.get('plan')
        date_premier_echelon = cleaned_data.get('date_premier_echelon')
        
        # Vérifier que la date du premier échelon est dans le futur
        if date_premier_echelon and date_premier_echelon < timezone.now().date():
            raise ValidationError(
                "La date du premier échelon ne peut pas être dans le passé."
            )
        
        # Vérifier que le nombre d'échelons est cohérent avec le plan
        if plan and nombre_echelons:
            if plan.echelons.exists():
                raise ValidationError(
                    "Ce plan a déjà des échelons. Veuillez les supprimer avant de générer de nouveaux échelons."
                )
        
        return cleaned_data
