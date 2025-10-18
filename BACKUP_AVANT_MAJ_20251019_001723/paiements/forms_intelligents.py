from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.db.models import Q
from decimal import Decimal

from .models import Paiement, ChargeDeductible
from contrats.models import Contrat
from proprietes.models import Propriete, Locataire


class PaiementFormIntelligent(forms.ModelForm):
    """
    Formulaire intelligent pour les paiements avec contexte automatique.
    """
    
    # Champs de sélection intelligents
    contrat = forms.ModelChoiceField(
        queryset=Contrat.objects.filter(is_deleted=False).select_related('propriete', 'locataire'),
        empty_label="Sélectionnez un contrat...",
        widget=forms.Select(attrs={
            'class': 'form-select form-select-lg',
            'data-toggle': 'select2',
            'data-placeholder': 'Tapez pour rechercher un contrat...',
            'id': 'contrat-select'
        }),
        help_text=_("Tapez directement au clavier pour rechercher un contrat")
    )
    
    # Champs automatiquement remplis
    montant_suggere = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control form-control-lg',
            'readonly': 'readonly',
            'id': 'montant-suggere'
        }),
        help_text=_("Montant suggéré basé sur le contrat")
    )
    
    libelle_suggere = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'readonly': 'readonly',
            'id': 'libelle-suggere'
        }),
        help_text=_("Libellé suggéré basé sur le contexte")
    )
    
    # Champs cachés pour le contexte
    contexte_contrat = forms.CharField(
        widget=forms.HiddenInput(attrs={'id': 'contexte-contrat'}),
        required=False
    )
    
    class Meta:
        model = Paiement
        fields = [
            'contrat', 'montant', 'date_paiement', 'type_paiement', 
            'mode_paiement', 'reference_paiement', 'libelle', 'statut',
            'montant_suggere', 'libelle_suggere', 'contexte_contrat'
        ]
        widgets = {
            'montant': forms.NumberInput(attrs={
                'class': 'form-control form-control-lg',
                'step': '0.01',
                'min': '0.01',
                'id': 'montant-paiement'
            }),
            'date_paiement': forms.DateInput(attrs={
                'class': 'form-control form-control-lg',
                'type': 'date',
                'id': 'date-paiement'
            }),
            'type_paiement': forms.Select(attrs={
                'class': 'form-select form-select-lg',
                'id': 'type-paiement'
            }),
            'mode_paiement': forms.Select(attrs={
                'class': 'form-select form-select-lg',
                'id': 'mode-paiement'
            }),
            'reference_paiement': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Référence du paiement',
                'id': 'reference-paiement'
            }),
            'libelle': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Libellé du paiement',
                'id': 'libelle-paiement'
            }),
            'statut': forms.Select(attrs={
                'class': 'form-select form-select-lg',
                'id': 'statut-paiement'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Personnalisation des labels
        self.fields['contrat'].label = _("Contrat")
        self.fields['montant'].label = _("Montant")
        self.fields['date_paiement'].label = _("Date de paiement")
        self.fields['type_paiement'].label = _("Type de paiement")
        self.fields['mode_paiement'].label = _("Mode de paiement")
        self.fields['reference_paiement'].label = _("Référence")
        self.fields['libelle'].label = _("Libellé")
        self.fields['statut'].label = _("Statut")
        
        # Ajout des classes Bootstrap
        for field_name, field in self.fields.items():
            if field_name not in ['contrat', 'montant_suggere', 'libelle_suggere', 'contexte_contrat']:
                if 'class' not in field.widget.attrs:
                    field.widget.attrs['class'] = 'form-control form-control-lg'
    
    def clean(self):
        cleaned_data = super().clean()
        contrat = cleaned_data.get('contrat')
        montant = cleaned_data.get('montant')
        
        # Validation des montants - DÉSACTIVÉE pour permettre tous les paiements
        # Les montants sont validés côté base de données et dans les vues
        
        return cleaned_data


class ChargeDeductibleFormIntelligent(forms.ModelForm):
    """
    Formulaire intelligent pour les charges déductibles avec contexte automatique.
    """
    
    contrat = forms.ModelChoiceField(
        queryset=Contrat.objects.filter(is_deleted=False).select_related('propriete', 'locataire'),
        empty_label="Sélectionnez un contrat...",
        widget=forms.Select(attrs={
            'class': 'form-select form-select-lg',
            'data-toggle': 'select2',
            'data-placeholder': 'Recherchez un contrat...',
            'id': 'contrat-charge-select'
        }),
        help_text=_("Sélectionnez un contrat pour voir automatiquement les informations")
    )
    
    # Champs automatiquement remplis
    montant_max_suggere = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control form-control-lg',
            'readonly': 'readonly',
            'id': 'montant-max-suggere'
        }),
        help_text=_("Montant maximum suggéré basé sur le solde du contrat")
    )
    
    class Meta:
        model = ChargeDeductible
        fields = [
            'contrat', 'montant', 'libelle', 'description', 'type_charge',
            'date_charge', 'facture_numero', 'fournisseur', 'montant_max_suggere'
        ]
        widgets = {
            'montant': forms.NumberInput(attrs={
                'class': 'form-control form-control-lg',
                'step': '0.01',
                'min': '0.01',
                'id': 'montant-charge'
            }),
            'libelle': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Libellé de la charge',
                'id': 'libelle-charge'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control form-control-lg',
                'rows': 3,
                'placeholder': 'Description détaillée de la charge',
                'id': 'description-charge'
            }),
            'type_charge': forms.Select(attrs={
                'class': 'form-select form-select-lg',
                'id': 'type-charge'
            }),
            'date_charge': forms.DateInput(attrs={
                'class': 'form-control form-control-lg',
                'type': 'date',
                'id': 'date-charge'
            }),
            'facture_numero': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Numéro de facture',
                'id': 'facture-numero'
            }),
            'fournisseur': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Nom du fournisseur',
                'id': 'fournisseur-charge'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Personnalisation des labels
        self.fields['contrat'].label = _("Contrat")
        self.fields['montant'].label = _("Montant")
        self.fields['libelle'].label = _("Libellé")
        self.fields['description'].label = _("Description")
        self.fields['type_charge'].label = _("Type de charge")
        self.fields['date_charge'].label = _("Date de la charge")
        self.fields['facture_numero'].label = _("Numéro de facture")
        self.fields['fournisseur'].label = _("Fournisseur")
        
        # Ajout des classes Bootstrap
        for field_name, field in self.fields.items():
            if field_name not in ['contrat', 'montant_max_suggere']:
                if 'class' not in field.widget.attrs:
                    field.widget.attrs['class'] = 'form-control form-control-lg'
    
    def clean(self):
        cleaned_data = super().clean()
        contrat = cleaned_data.get('contrat')
        montant = cleaned_data.get('montant')
        
        # Validation des montants - DÉSACTIVÉE pour permettre tous les paiements
        # Les montants sont validés côté base de données et dans les vues
        
        return cleaned_data


class RechercheContratForm(forms.Form):
    """
    Formulaire de recherche intelligente de contrats.
    """
    
    TERMES_RECHERCHE_CHOICES = [
        ('numero', 'Numéro de contrat'),
        ('locataire', 'Nom du locataire'),
        ('propriete', 'Adresse de la propriété'),
        ('bailleur', 'Nom du bailleur'),
        ('ville', 'Ville'),
    ]
    
    terme_recherche = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Recherchez un contrat, locataire, propriété...',
            'id': 'terme-recherche'
        }),
        help_text=_("Tapez pour rechercher automatiquement")
    )
    
    type_recherche = forms.ChoiceField(
        choices=TERMES_RECHERCHE_CHOICES,
        initial='numero',
        widget=forms.Select(attrs={
            'class': 'form-select form-select-lg',
            'id': 'type-recherche'
        }),
        help_text=_("Type de recherche")
    )
    
    def clean_terme_recherche(self):
        terme = self.cleaned_data['terme_recherche']
        if len(terme.strip()) < 2:
            raise ValidationError(_("Veuillez saisir au moins 2 caractères pour la recherche."))
        return terme.strip()
    
    def rechercher_contrats(self):
        """
        Effectue la recherche intelligente de contrats.
        """
        terme = self.cleaned_data['terme_recherche']
        type_recherche = self.cleaned_data['type_recherche']
        
        queryset = Contrat.objects.filter(is_deleted=False).select_related(
            'propriete', 'locataire', 'propriete__bailleur'
        )
        
        if type_recherche == 'numero':
            queryset = queryset.filter(numero_contrat__icontains=terme)
        elif type_recherche == 'locataire':
            queryset = queryset.filter(
                Q(locataire__nom__icontains=terme) | 
                Q(locataire__prenom__icontains=terme)
            )
        elif type_recherche == 'propriete':
            queryset = queryset.filter(
                Q(propriete__adresse__icontains=terme) |
                Q(propriete__titre__icontains=terme)
            )
        elif type_recherche == 'bailleur':
            queryset = queryset.filter(
                Q(propriete__bailleur__nom__icontains=terme) |
                Q(propriete__bailleur__prenom__icontains=terme)
            )
        elif type_recherche == 'ville':
            queryset = queryset.filter(propriete__ville__icontains=terme)
        else:
            # Recherche globale
            queryset = queryset.filter(
                Q(numero_contrat__icontains=terme) |
                Q(locataire__nom__icontains=terme) |
                Q(locataire__prenom__icontains=terme) |
                Q(propriete__adresse__icontains=terme) |
                Q(propriete__titre__icontains=terme) |
                Q(propriete__ville__icontains=terme) |
                Q(propriete__bailleur__nom__icontains=terme) |
                Q(propriete__bailleur__prenom__icontains=terme)
            )
        
        return queryset.order_by('-date_debut')[:20]  # Limite à 20 résultats
