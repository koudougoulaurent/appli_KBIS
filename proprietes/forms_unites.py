"""
Formulaires pour la gestion des unités locatives
"""
from django import forms
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from datetime import timedelta

from .models import UniteLocative, ReservationUnite, Propriete, Locataire, Bailleur


class UniteLocativeForm(forms.ModelForm):
    """Formulaire pour créer/modifier une unité locative."""
    
    class Meta:
        model = UniteLocative
        fields = [
            'propriete', 'bailleur', 'numero_unite', 'nom', 'type_unite',
            'etage', 'surface', 'nombre_pieces', 'nombre_chambres', 'nombre_salles_bain',
            'meuble', 'balcon', 'parking_inclus', 'climatisation', 'internet_inclus',
            'loyer_mensuel', 'charges_mensuelles', 'caution_demandee',
            'statut', 'date_disponibilite', 'description', 'notes_privees'
        ]
        widgets = {
            'propriete': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'bailleur': forms.Select(attrs={
                'class': 'form-select',
                'placeholder': 'Sélectionnez un bailleur (optionnel)'
            }),
            'numero_unite': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Apt 101, Bureau 205, Chambre A12',
                'required': True
            }),
            'nom': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom descriptif de l\'unité',
                'required': True
            }),
            'type_unite': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'etage': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0 pour RDC, -1 pour sous-sol'
            }),
            'surface': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': 'Surface en m²'
            }),
            'nombre_pieces': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'value': '1'
            }),
            'nombre_chambres': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'value': '0'
            }),
            'nombre_salles_bain': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'value': '0'
            }),
            'meuble': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'balcon': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'parking_inclus': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'climatisation': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'internet_inclus': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'loyer_mensuel': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Montant en F CFA'
            }),
            'charges_mensuelles': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Montant en F CFA'
            }),
            'caution_demandee': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Montant en F CFA'
            }),
            'statut': forms.Select(attrs={
                'class': 'form-select'
            }),
            'date_disponibilite': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': '4',
                'placeholder': 'Description détaillée de l\'unité'
            }),
            'notes_privees': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': '3',
                'placeholder': 'Notes internes (non visibles par les locataires)'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Limiter les propriétés aux propriétés actives
        self.fields['propriete'].queryset = Propriete.objects.filter(is_deleted=False)
        
        # Limiter les bailleurs aux bailleurs actifs
        self.fields['bailleur'].queryset = Bailleur.objects.filter(is_deleted=False, actif=True)
        self.fields['bailleur'].empty_label = "Utiliser le bailleur de la propriété"
        
        # Si une propriété est pré-sélectionnée, définir le bailleur par défaut
        if self.initial.get('propriete'):
            propriete = self.initial['propriete']
            if hasattr(propriete, 'bailleur'):
                self.fields['bailleur'].initial = propriete.bailleur
        
        # Rendre certains champs requis
        self.fields['numero_unite'].required = True
        self.fields['nom'].required = True
        self.fields['type_unite'].required = True
        self.fields['loyer_mensuel'].required = True
    
    def clean_numero_unite(self):
        """Valider l'unicité du numéro d'unité dans la propriété."""
        numero_unite = self.cleaned_data['numero_unite']
        propriete = self.cleaned_data.get('propriete')
        
        if propriete:
            # Exclure l'instance actuelle si on modifie
            queryset = UniteLocative.objects.filter(
                propriete=propriete,
                numero_unite=numero_unite,
                is_deleted=False
            )
            
            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            
            if queryset.exists():
                raise forms.ValidationError(
                    f"Une unité avec le numéro '{numero_unite}' existe déjà dans cette propriété."
                )
        
        return numero_unite
    
    def clean_surface(self):
        """Valider la surface."""
        surface = self.cleaned_data.get('surface')
        if surface is not None and surface <= 0:
            raise forms.ValidationError("La surface doit être supérieure à 0.")
        return surface
    
    def clean_loyer_mensuel(self):
        """Valider le loyer mensuel."""
        loyer = self.cleaned_data.get('loyer_mensuel')
        if loyer is not None and loyer < 0:
            raise forms.ValidationError("Le loyer ne peut pas être négatif.")
        return loyer
    
    def clean(self):
        """Validation globale du formulaire."""
        cleaned_data = super().clean()
        
        nombre_chambres = cleaned_data.get('nombre_chambres', 0)
        nombre_salles_bain = cleaned_data.get('nombre_salles_bain', 0)
        nombre_pieces = cleaned_data.get('nombre_pieces', 1)
        
        # Vérifier que le nombre de chambres et salles de bain ne dépasse pas le nombre de pièces
        if nombre_chambres + nombre_salles_bain > nombre_pieces:
            raise forms.ValidationError(
                "Le nombre total de chambres et salles de bain ne peut pas dépasser le nombre de pièces."
            )
        
        return cleaned_data


class ReservationUniteForm(forms.ModelForm):
    """Formulaire pour créer/modifier une réservation d'unité."""
    
    # Champ pour conversion immédiate en contrat
    convertir_en_contrat = forms.BooleanField(
        required=False,
        initial=False,
        label=_('Convertir immédiatement en contrat'),
        help_text=_('Cochez cette case pour créer automatiquement un contrat à partir de cette réservation'),
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    class Meta:
        model = ReservationUnite
        fields = [
            'locataire_potentiel', 'date_debut_souhaitee', 'date_fin_prevue',
            'date_expiration', 'montant_reservation', 'statut', 'notes'
        ]
        widgets = {
            'locataire_potentiel': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'date_debut_souhaitee': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': True
            }),
            'date_fin_prevue': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'date_expiration': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'montant_reservation': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Montant en F CFA'
            }),
            'statut': forms.Select(attrs={
                'class': 'form-select'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': '4',
                'placeholder': 'Notes sur la réservation'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Limiter aux locataires actifs
        self.fields['locataire_potentiel'].queryset = Locataire.objects.filter(is_deleted=False)
        
        # Définir une date d'expiration par défaut (7 jours)
        if not self.instance.pk:
            self.fields['date_expiration'].initial = timezone.now() + timedelta(days=7)
    
    def clean_date_debut_souhaitee(self):
        """Valider la date de début souhaitée."""
        date_debut = self.cleaned_data.get('date_debut_souhaitee')
        
        if date_debut and date_debut < timezone.now().date():
            raise forms.ValidationError(
                "La date de début souhaitée ne peut pas être dans le passé."
            )
        
        return date_debut
    
    def clean_date_expiration(self):
        """Valider la date d'expiration."""
        date_expiration = self.cleaned_data.get('date_expiration')
        
        if date_expiration and date_expiration <= timezone.now():
            raise forms.ValidationError(
                "La date d'expiration doit être dans le futur."
            )
        
        return date_expiration
    
    def clean(self):
        """Validation globale du formulaire."""
        cleaned_data = super().clean()
        
        date_debut = cleaned_data.get('date_debut_souhaitee')
        date_fin = cleaned_data.get('date_fin_prevue')
        
        if date_debut and date_fin and date_fin <= date_debut:
            raise forms.ValidationError(
                "La date de fin prévue doit être postérieure à la date de début."
            )
        
        return cleaned_data


class FiltreUniteForm(forms.Form):
    """Formulaire de filtrage pour la liste des unités."""
    
    propriete = forms.ModelChoiceField(
        queryset=Propriete.objects.none(),  # Sera rempli dans __init__
        required=False,
        empty_label="Toutes les propriétés",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Utiliser la logique de filtrage des propriétés disponibles
        from core.property_utils import get_proprietes_disponibles_global
        self.fields['propriete'].queryset = get_proprietes_disponibles_global()
    
    statut = forms.ChoiceField(
        choices=[('', 'Tous les statuts')] + list(UniteLocative.STATUT_CHOICES),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    type_unite = forms.ChoiceField(
        choices=[('', 'Tous les types')] + list(UniteLocative.TYPE_UNITE_CHOICES),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Rechercher par numéro, nom, propriété...'
        })
    )
    
    etage_min = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Étage min'
        })
    )
    
    etage_max = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Étage max'
        })
    )
    
    loyer_min = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Loyer min',
            'step': '0.01'
        })
    )
    
    loyer_max = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Loyer max',
            'step': '0.01'
        })
    )


class RapportOccupationForm(forms.Form):
    """Formulaire pour générer des rapports d'occupation."""
    
    propriete = forms.ModelChoiceField(
        queryset=Propriete.objects.filter(is_deleted=False),
        required=False,
        empty_label="Toutes les propriétés",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    date_debut = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    date_fin = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    type_rapport = forms.ChoiceField(
        choices=[
            ('occupation', 'Taux d\'occupation'),
            ('revenus', 'Revenus générés'),
            ('disponibilite', 'Disponibilité des unités'),
            ('complet', 'Rapport complet'),
        ],
        required=True,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    def clean(self):
        """Validation des dates."""
        cleaned_data = super().clean()
        date_debut = cleaned_data.get('date_debut')
        date_fin = cleaned_data.get('date_fin')
        
        if date_debut and date_fin:
            if date_fin <= date_debut:
                raise forms.ValidationError(
                    "La date de fin doit être postérieure à la date de début."
                )
            
            if (date_fin - date_debut).days > 365:
                raise forms.ValidationError(
                    "La période ne peut pas dépasser 365 jours."
                )
        
        return cleaned_data
