from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.db.models import Q
from decimal import Decimal

from .models import RetraitBailleur
from proprietes.models import Bailleur


class RetraitBailleurFormIntelligent(forms.ModelForm):
    """
    Formulaire intelligent pour les retraits avec contexte automatique.
    """
    
    # Champs de sélection intelligents
    bailleur = forms.ModelChoiceField(
        queryset=Bailleur.objects.filter(actif=True).select_related(),
        empty_label="Sélectionnez un bailleur...",
        widget=forms.Select(attrs={
            'class': 'form-select form-select-lg',
            'data-toggle': 'select2',
            'data-placeholder': 'Tapez pour rechercher un bailleur...',
            'id': 'bailleur-select'
        }),
        help_text=_("Tapez directement au clavier pour rechercher un bailleur")
    )
    
    # Champs automatiquement remplis
    montant_loyers_suggere = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control form-control-lg',
            'readonly': 'readonly',
            'id': 'montant-loyers-suggere'
        }),
        help_text=_("Montant des loyers suggéré basé sur le contexte")
    )
    
    montant_charges_suggere = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control form-control-lg',
            'readonly': 'readonly',
            'id': 'montant-charges-suggere'
        }),
        help_text=_("Montant des charges suggéré basé sur le contexte")
    )
    
    montant_net_suggere = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control form-control-lg',
            'readonly': 'readonly',
            'id': 'montant-net-suggere'
        }),
        help_text=_("Montant net suggéré basé sur le contexte")
    )
    
    # Champs cachés pour le contexte
    contexte_bailleur = forms.CharField(
        widget=forms.HiddenInput(attrs={'id': 'contexte-bailleur'}),
        required=False
    )
    
    class Meta:
        model = RetraitBailleur
        fields = [
            'bailleur', 'mois_retrait', 'montant_loyers_bruts',
            'montant_charges_deductibles', 'montant_net_a_payer', 'type_retrait', 
            'statut', 'mode_retrait', 'date_demande', 'date_versement',
            'numero_cheque', 'reference_virement', 'notes',
            'montant_loyers_suggere', 'montant_charges_suggere', 'montant_net_suggere',
            'contexte_bailleur'
        ]
        widgets = {
            'mois_retrait': forms.DateInput(attrs={
                'class': 'form-control form-control-lg',
                'type': 'date',
                'id': 'mois-retrait'
            }),
            'montant_loyers_bruts': forms.NumberInput(attrs={
                'class': 'form-control form-control-lg',
                'step': '0.01',
                'min': '0.01',
                'id': 'montant-loyers-bruts'
            }),
            'montant_charges_deductibles': forms.NumberInput(attrs={
                'class': 'form-control form-control-lg',
                'step': '0.01',
                'min': '0',
                'id': 'montant-charges-deductibles'
            }),
            'montant_net_a_payer': forms.NumberInput(attrs={
                'class': 'form-control form-control-lg',
                'step': '0.01',
                'min': '0.01',
                'readonly': 'readonly',
                'id': 'montant-net-a-payer'
            }),
            'type_retrait': forms.Select(attrs={
                'class': 'form-select form-select-lg',
                'id': 'type-retrait'
            }),
            'statut': forms.Select(attrs={
                'class': 'form-select form-select-lg',
                'id': 'statut-retrait'
            }),
            'mode_retrait': forms.Select(attrs={
                'class': 'form-select form-select-lg',
                'id': 'mode-retrait'
            }),
            'date_demande': forms.DateInput(attrs={
                'class': 'form-control form-control-lg',
                'type': 'date',
                'id': 'date-demande'
            }),
            'date_versement': forms.DateInput(attrs={
                'class': 'form-control form-control-lg',
                'type': 'date',
                'id': 'date-versement'
            }),
            'numero_cheque': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Numéro de chèque',
                'id': 'numero-cheque'
            }),
            'reference_virement': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Référence du virement',
                'id': 'reference-virement'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control form-control-lg',
                'rows': 3,
                'placeholder': 'Notes sur le retrait',
                'id': 'notes-retrait'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filtrer les bailleurs actifs seulement
        self.fields['bailleur'].queryset = Bailleur.objects.filter(
            actif=True
        ).order_by('nom', 'prenom')
        
        # Personnaliser l'affichage des bailleurs
        self.fields['bailleur'].label_from_instance = lambda obj: (
            f"{obj.nom} {obj.prenom} - {obj.code_bailleur}"
        )
        
        # Valeurs par défaut
        if not self.instance.pk:
            from django.utils import timezone
            self.fields['date_demande'].initial = timezone.now().date()
            self.fields['mois_retrait'].initial = timezone.now().date().replace(day=1)
            self.fields['statut'].initial = 'en_attente'
            self.fields['type_retrait'].initial = 'mensuel'
            self.fields['montant_charges_deductibles'].initial = 0
            self.fields['montant_net_a_payer'].initial = 0
    
    def clean_mois_retrait(self):
        """Valider le format du mois de retrait."""
        mois_retrait = self.cleaned_data.get('mois_retrait')
        if mois_retrait:
            # S'assurer que c'est le premier jour du mois
            if mois_retrait.day != 1:
                mois_retrait = mois_retrait.replace(day=1)
        return mois_retrait
    
    def clean(self):
        """Validation globale du formulaire."""
        cleaned_data = super().clean()
        montant_loyers_bruts = cleaned_data.get('montant_loyers_bruts')
        montant_charges_deductibles = cleaned_data.get('montant_charges_deductibles')
        
        # Validation des montants
        if montant_loyers_bruts is not None and montant_loyers_bruts <= 0:
            raise ValidationError(_('Le montant des loyers bruts doit être positif.'))
        
        if montant_charges_deductibles is not None and montant_charges_deductibles < 0:
            raise ValidationError(_('Le montant des charges déductibles ne peut pas être négatif.'))
        
        # Calculer automatiquement le montant net
        if montant_loyers_bruts is not None and montant_charges_deductibles is not None:
            montant_net_calcule = montant_loyers_bruts - montant_charges_deductibles
            
            # Vérifier que le montant net est positif
            if montant_net_calcule <= 0:
                raise ValidationError(_('Le montant net à payer doit être positif. Les charges déductibles ne peuvent pas dépasser les loyers bruts.'))
            
            # Mettre à jour le champ montant net
            cleaned_data['montant_net_a_payer'] = montant_net_calcule
        
        return cleaned_data


class RechercheBailleurForm(forms.Form):
    """
    Formulaire de recherche intelligente de bailleurs.
    """
    
    recherche = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Rechercher par nom, prénom, code ou email...',
            'id': 'recherche-bailleur'
        }),
        help_text=_("Tapez pour rechercher un bailleur")
    )
    
    statut = forms.ChoiceField(
        choices=[
            ('', 'Tous les statuts'),
            ('actif', 'Actif'),
            ('inactif', 'Inactif')
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select form-select-lg',
            'id': 'statut-bailleur'
        })
    )
    
    type_retrait = forms.ChoiceField(
        choices=[
            ('', 'Tous les types'),
            ('mensuel', 'Mensuel'),
            ('trimestriel', 'Trimestriel'),
            ('annuel', 'Annuel'),
            ('exceptionnel', 'Exceptionnel')
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select form-select-lg',
            'id': 'type-retrait-filtre'
        })
    )
    
    def clean_recherche(self):
        """Nettoyer et valider la recherche."""
        recherche = self.cleaned_data.get('recherche', '').strip()
        if len(recherche) < 2 and recherche:
            raise ValidationError(_('La recherche doit contenir au moins 2 caractères.'))
        return recherche
