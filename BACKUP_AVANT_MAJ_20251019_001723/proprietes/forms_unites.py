"""
Formulaires pour la gestion des unités locatives
"""
from django import forms
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from datetime import timedelta
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, Row, Column

from .models import UniteLocative, ReservationUnite, Propriete, Locataire, Bailleur


class UniteLocativeForm(forms.ModelForm):
    """Formulaire pour créer/modifier une unité locative."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_class = 'needs-validation'
        self.helper.form_show_labels = True
        self.helper.form_show_errors = True
    
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
                'placeholder': 'Loyer mensuel en F CFA'
            }),
            'charges_mensuelles': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Charges mensuelles en F CFA'
            }),
            'caution_demandee': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Caution demandée en F CFA'
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
                'rows': 3,
                'placeholder': 'Description de l\'unité locative'
            }),
            'notes_privees': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Notes privées (non visibles par les locataires)'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Définir les choix pour le champ type_unite
        self.fields['type_unite'].choices = UniteLocative.TYPE_UNITE_CHOICES
        self.fields['type_unite'].required = True
        
        # Définir les choix pour le champ propriete
        self.fields['propriete'].queryset = Propriete.objects.filter(is_deleted=False).order_by('titre')
        self.fields['propriete'].required = True
        
        # Définir les choix pour le champ bailleur
        self.fields['bailleur'].queryset = Bailleur.objects.filter(is_deleted=False, actif=True).order_by('nom', 'prenom')
        self.fields['bailleur'].required = False
        self.fields['bailleur'].empty_label = "Sélectionnez un bailleur (optionnel)"
        
        # Définir les choix pour le champ statut
        self.fields['statut'].choices = UniteLocative.STATUT_CHOICES
        self.fields['statut'].required = True
        
        # Valeurs par défaut
        if not self.instance.pk:  # Nouvelle unité
            self.fields['statut'].initial = 'disponible'
            self.fields['date_disponibilite'].initial = timezone.now().date()
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Validation des données
        surface = cleaned_data.get('surface')
        nombre_pieces = cleaned_data.get('nombre_pieces')
        nombre_chambres = cleaned_data.get('nombre_chambres')
        
        if surface and surface <= 0:
            raise forms.ValidationError("La surface doit être positive.")
        
        if nombre_pieces and nombre_pieces <= 0:
            raise forms.ValidationError("Le nombre de pièces doit être positif.")
        
        if nombre_chambres and nombre_chambres < 0:
            raise forms.ValidationError("Le nombre de chambres ne peut pas être négatif.")
        
        if nombre_chambres and nombre_pieces and nombre_chambres >= nombre_pieces:
            raise forms.ValidationError("Le nombre de chambres doit être inférieur au nombre total de pièces.")
        
        return cleaned_data


class ReservationUniteForm(forms.ModelForm):
    """Formulaire pour créer/modifier une réservation d'unité."""
    
    # Champ non-modèle pour la conversion en contrat
    convertir_en_contrat = forms.BooleanField(
        required=False,
        initial=False,
        label=_("Convertir immédiatement en contrat"),
        help_text=_("Si coché, la réservation sera immédiatement convertie en contrat de bail"),
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    class Meta:
        model = ReservationUnite
        fields = [
            'unite_locative', 'locataire_potentiel', 'date_debut_souhaitee', 'date_fin_prevue', 'statut',
            'montant_reservation', 'date_expiration', 'notes'
        ]
        widgets = {
            'unite_locative': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
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
            'statut': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'montant_reservation': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Montant de réservation en F CFA'
            }),
            'date_expiration': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local',
                'required': True
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Notes sur la réservation'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        unite_locative = kwargs.pop('unite_locative', None)
        super().__init__(*args, **kwargs)
        
        # Définir les choix pour le champ unite_locative
        if unite_locative:
            # Si une unité est spécifiée, la pré-sélectionner et la cacher
            self.fields['unite_locative'].initial = unite_locative
            self.fields['unite_locative'].queryset = UniteLocative.objects.filter(pk=unite_locative.pk)
            self.fields['unite_locative'].widget = forms.HiddenInput()
        else:
            # Sinon, afficher toutes les unités disponibles
            self.fields['unite_locative'].queryset = UniteLocative.objects.filter(
                is_deleted=False, 
                statut='disponible'
            ).order_by('propriete__titre', 'numero_unite')
        self.fields['unite_locative'].required = True
        
        # Définir les choix pour le champ locataire_potentiel
        try:
            locataires_actifs = Locataire.objects.filter(
                is_deleted=False, 
                statut='actif'
            ).order_by('nom', 'prenom')
            
            self.fields['locataire_potentiel'].queryset = locataires_actifs
            self.fields['locataire_potentiel'].required = True
            self.fields['locataire_potentiel'].empty_label = "Sélectionnez un locataire" if locataires_actifs.exists() else "Aucun locataire actif disponible"
            self.fields['locataire_potentiel'].label = "Locataire potentiel"
            
            # Si aucun locataire actif, rendre le champ optionnel temporairement
            if not locataires_actifs.exists():
                self.fields['locataire_potentiel'].required = False
                # Ajouter un message d'aide
                self.fields['locataire_potentiel'].help_text = "Aucun locataire actif trouvé. Veuillez d'abord créer des locataires dans la section 'Locataires'."
        except Exception:  # pylint: disable=broad-except
            # En cas d'erreur, utiliser un queryset vide
            self.fields['locataire_potentiel'].queryset = Locataire.objects.none()
            self.fields['locataire_potentiel'].empty_label = "Erreur de chargement des locataires"
            self.fields['locataire_potentiel'].help_text = "Impossible de charger les locataires. Vérifiez la configuration de la base de données."
        
        # Définir les choix pour le champ statut
        self.fields['statut'].choices = ReservationUnite.STATUT_CHOICES
        self.fields['statut'].required = True
        
        # Valeurs par défaut
        if not self.instance.pk:  # Nouvelle réservation
            self.fields['statut'].initial = 'en_attente'
            self.fields['date_debut_souhaitee'].initial = timezone.now().date()
            # Date d'expiration par défaut : 7 jours
            self.fields['date_expiration'].initial = timezone.now() + timedelta(days=7)
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Validation des dates
        date_debut = cleaned_data.get('date_debut_souhaitee')
        date_fin = cleaned_data.get('date_fin_prevue')
        date_expiration = cleaned_data.get('date_expiration')
        
        if date_debut and date_fin and date_debut >= date_fin:
            raise forms.ValidationError("La date de fin doit être postérieure à la date de début.")
        
        if date_debut and date_debut < timezone.now().date():
            raise forms.ValidationError("La date de début ne peut pas être dans le passé.")
        
        if date_expiration and date_expiration <= timezone.now():
            raise forms.ValidationError("La date d'expiration doit être dans le futur.")
        
        return cleaned_data


class UniteLocativeSearchForm(forms.Form):
    """Formulaire de recherche pour les unités locatives."""
    
    TYPE_UNITE_CHOICES = [('', 'Tous les types')] + list(UniteLocative.TYPE_UNITE_CHOICES)
    STATUT_CHOICES = [('', 'Tous les statuts')] + list(UniteLocative.STATUT_CHOICES)
    
    propriete = forms.ModelChoiceField(
        queryset=Propriete.objects.filter(is_deleted=False).order_by('titre'),
        required=False,
        empty_label="Toutes les propriétés",
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    type_unite = forms.ChoiceField(
        choices=TYPE_UNITE_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    statut = forms.ChoiceField(
        choices=STATUT_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    etage_min = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Étage minimum'
        })
    )
    
    etage_max = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Étage maximum'
        })
    )
    
    surface_min = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'placeholder': 'Surface minimum (m²)'
        })
    )
    
    surface_max = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'placeholder': 'Surface maximum (m²)'
        })
    )
    
    loyer_min = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'placeholder': 'Loyer minimum (F CFA)'
        })
    )
    
    loyer_max = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'placeholder': 'Loyer maximum (F CFA)'
        })
    )
    
    meuble = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    balcon = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    parking_inclus = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    climatisation = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    internet_inclus = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Validation des plages
        etage_min = cleaned_data.get('etage_min')
        etage_max = cleaned_data.get('etage_max')
        
        if etage_min is not None and etage_max is not None and etage_min > etage_max:
            raise forms.ValidationError("L'étage minimum ne peut pas être supérieur à l'étage maximum.")
        
        surface_min = cleaned_data.get('surface_min')
        surface_max = cleaned_data.get('surface_max')
        
        if surface_min is not None and surface_max is not None and surface_min > surface_max:
            raise forms.ValidationError("La surface minimum ne peut pas être supérieure à la surface maximum.")
        
        loyer_min = cleaned_data.get('loyer_min')
        loyer_max = cleaned_data.get('loyer_max')
        
        if loyer_min is not None and loyer_max is not None and loyer_min > loyer_max:
            raise forms.ValidationError("Le loyer minimum ne peut pas être supérieur au loyer maximum.")
        
        return cleaned_data