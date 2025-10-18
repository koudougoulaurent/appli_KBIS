#!/usr/bin/env python3
"""
Formulaires avancés pour la gestion des charges déductibles
===========================================================

Ce module contient des formulaires spécialisés pour la gestion complète
des charges déductibles avec validation et intégration aux récapitulatifs.
"""

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.db.models import Q

from .models import ChargeDeductible
from contrats.models import Contrat
from proprietes.models import Bailleur, Propriete


class ChargeDeductibleForm(forms.ModelForm):
    """Formulaire pour créer/modifier une charge déductible."""
    
    class Meta:
        model = ChargeDeductible
        fields = [
            'contrat', 'montant', 'description',
            'date_charge'
        ]
        widgets = {
            'contrat': forms.Select(attrs={
                'class': 'form-control',
                'id': 'id_contrat'
            }),
            'montant': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01',
                'id': 'id_montant'
            }),
            'libelle': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Réparation chauffe-eau',
                'id': 'id_libelle'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Description détaillée de la charge...',
                'id': 'id_description'
            }),
            'type_charge': forms.Select(attrs={
                'class': 'form-control',
                'id': 'id_type_charge'
            }),
            'date_charge': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'id': 'id_date_charge'
            }),
            'facture_numero': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Numéro de facture',
                'id': 'id_facture_numero'
            }),
            'fournisseur': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom du fournisseur',
                'id': 'id_fournisseur'
            }),
            'justificatif_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'URL du justificatif (optionnel)',
                'id': 'id_justificatif_url'
            }),
        }
        labels = {
            'contrat': _('Contrat concerné'),
            'montant': _('Montant de la charge'),
            'libelle': _('Libellé de la charge'),
            'description': _('Description détaillée'),
            'type_charge': _('Type de charge'),
            'date_charge': _('Date de la charge'),
            'facture_numero': _('Numéro de facture'),
            'fournisseur': _('Fournisseur'),
            'justificatif_url': _('URL du justificatif'),
        }
    
    def __init__(self, *args, **kwargs):
        self.bailleur = kwargs.pop('bailleur', None)
        super().__init__(*args, **kwargs)
        
        # Filtrer les contrats par bailleur si spécifié
        if self.bailleur:
            self.fields['contrat'].queryset = Contrat.objects.filter(
                propriete__bailleur=self.bailleur,
                est_actif=True
            ).select_related('propriete', 'locataire')
        else:
            self.fields['contrat'].queryset = Contrat.objects.filter(
                est_actif=True
            ).select_related('propriete', 'locataire')
    
    def clean_montant(self):
        montant = self.cleaned_data.get('montant')
        if montant is not None and montant <= 0:
            raise ValidationError(_('Le montant doit être positif.'))
        return montant
    
    def clean_contrat(self):
        contrat = self.cleaned_data.get('contrat')
        if contrat and not contrat.est_actif:
            raise ValidationError(_('Le contrat sélectionné n\'est pas actif.'))
        return contrat


class RechercheChargesForm(forms.Form):
    """Formulaire de recherche pour les charges déductibles."""
    
    # Critères de recherche
    bailleur = forms.ModelChoiceField(
        queryset=Bailleur.objects.filter(actif=True),
        required=False,
        empty_label="Tous les bailleurs",
        widget=forms.Select(attrs={'class': 'form-control'}),
        label=_('Bailleur')
    )
    
    type_charge = forms.ChoiceField(
        choices=[('', 'Tous les types')],  # type_charge supprimé
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label=_('Type de charge')
    )
    
    statut = forms.ChoiceField(
        choices=[('', 'Tous les statuts')],  # statut supprimé
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label=_('Statut')
    )
    
    date_debut = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label=_('Date de début')
    )
    
    date_fin = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label=_('Date de fin')
    )
    
    montant_min = forms.DecimalField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'placeholder': 'Montant minimum'
        }),
        label=_('Montant minimum')
    )
    
    montant_max = forms.DecimalField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'placeholder': 'Montant maximum'
        }),
        label=_('Montant maximum')
    )
    
    libelle = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Rechercher dans le libellé...'
        }),
        label=_('Libellé')
    )


class ValidationChargesForm(forms.Form):
    """Formulaire pour valider ou refuser des charges."""
    
    charges = forms.ModelMultipleChoiceField(
        queryset=ChargeDeductible.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        label=_('Charges à traiter')
    )
    
    action = forms.ChoiceField(
        choices=[
            ('valider', 'Valider les charges sélectionnées'),
            ('refuser', 'Refuser les charges sélectionnées'),
            ('deduire', 'Marquer comme déduites'),
        ],
        widget=forms.RadioSelect,
        label=_('Action à effectuer')
    )
    
    motif_refus = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Motif du refus (si applicable)...'
        }),
        label=_('Motif du refus')
    )
    
    def __init__(self, *args, **kwargs):
        queryset = kwargs.pop('queryset', ChargeDeductible.objects.none())
        super().__init__(*args, **kwargs)
        self.fields['charges'].queryset = queryset


class ImportChargesForm(forms.Form):
    """Formulaire pour importer des charges depuis un fichier."""
    
    fichier = forms.FileField(
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.csv,.xlsx,.xls'
        }),
        label=_('Fichier à importer'),
        help_text=_('Formats supportés: CSV, Excel (.xlsx, .xls)')
    )
    
    bailleur = forms.ModelChoiceField(
        queryset=Bailleur.objects.filter(actif=True),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label=_('Bailleur concerné'),
        help_text=_('Toutes les charges seront associées à ce bailleur')
    )
    
    type_charge_defaut = forms.ChoiceField(
        choices=[('', 'Sélectionner un type')],  # type_charge supprimé
        widget=forms.Select(attrs={'class': 'form-control'}),
        label=_('Type de charge par défaut'),
        help_text=_('Type appliqué si non spécifié dans le fichier')
    )
    
    ignorer_premiere_ligne = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label=_('Ignorer la première ligne'),
        help_text=_('Cochez si la première ligne contient les en-têtes')
    )


class RapportChargesForm(forms.Form):
    """Formulaire pour générer des rapports sur les charges."""
    
    TYPE_RAPPORT_CHOICES = [
        ('par_bailleur', 'Par bailleur'),
        ('par_type', 'Par type de charge'),
        ('par_periode', 'Par période'),
        ('synthese', 'Synthèse générale'),
    ]
    
    type_rapport = forms.ChoiceField(
        choices=TYPE_RAPPORT_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label=_('Type de rapport')
    )
    
    periode_debut = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label=_('Période de début')
    )
    
    periode_fin = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label=_('Période de fin')
    )
    
    format_sortie = forms.ChoiceField(
        choices=[
            ('pdf', 'PDF'),
            ('excel', 'Excel'),
            ('csv', 'CSV'),
        ],
        initial='pdf',
        widget=forms.Select(attrs={'class': 'form-control'}),
        label=_('Format de sortie')
    )
    
    inclure_details = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label=_('Inclure les détails'),
        help_text=_('Inclure le détail de chaque charge dans le rapport')
    )
