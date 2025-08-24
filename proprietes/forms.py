from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .models import Propriete, Bailleur, Locataire, TypeBien, ChargesBailleur, Photo, Document, Piece, PieceContrat
from core.widgets import UniqueIdField, ReadOnlyUniqueIdWidget
from django.core.validators import RegexValidator
import re

# Validation personnalisée pour les numéros de téléphone français
phone_regex_fr = RegexValidator(
    regex=r'^(\+33|0)?[1-9](\d{1,2}\s?){3,4}\d{1,2}$',
    message="Le numéro de téléphone doit être au format français valide (ex: 01 23 45 67 89 ou 06 12 34 56 78)"
)

def validate_phone_french(value):
    """Validation personnalisée pour les numéros de téléphone français"""
    if not value:
        return
    
    # Nettoyer le numéro (supprimer espaces, tirets, points)
    clean_number = re.sub(r'[\s\-\.]', '', value)
    
    # Vérifier la longueur minimale (8 chiffres pour les numéros français)
    if len(clean_number) < 8:
        raise ValidationError("Le numéro de téléphone doit contenir au moins 8 chiffres.")
    
    # Vérifier le format français
    if not re.match(r'^(\+33|0)?[1-9](\d{1,2}){3,4}$', clean_number):
        raise ValidationError("Format de numéro de téléphone invalide pour la France.")


class ProprieteForm(forms.ModelForm):
    """Formulaire pour l'ajout et la modification de propriétés avec gestion documentaire intégrée."""
    
    # Champs pour les documents requis de la propriété
    acte_propriete = forms.FileField(
        required=True,
        label=_('Acte de propriété'),
        help_text=_('Acte de propriété ou titre de propriété (PDF, JPG, PNG)'),
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,.jpg,.jpeg,.png'
        })
    )
    
    diagnostic_energetique = forms.FileField(
        required=True,
        label=_('Diagnostic énergétique'),
        help_text=_('Diagnostic de performance énergétique (DPE) (PDF, JPG, PNG)'),
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,.jpg,.jpeg,.png'
        })
    )
    
    diagnostic_plomb = forms.FileField(
        required=False,
        label=_('Diagnostic plomb'),
        help_text=_('Diagnostic plomb si applicable (PDF, JPG, PNG)'),
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,.jpg,.jpeg,.png'
        })
    )
    
    diagnostic_amiante = forms.FileField(
        required=False,
        label=_('Diagnostic amiante'),
        help_text=_('Diagnostic amiante si applicable (PDF, JPG, PNG)'),
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,.jpg,.jpeg,.png'
        })
    )
    
    photos_propriete = forms.FileField(
        required=False,
        label=_('Photos de la propriété'),
        help_text=_('Photos de la propriété (JPG, PNG)'),
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.jpg,.jpeg,.png'
        })
    )
    
    class Meta:
        model = Propriete
        fields = [
            'numero_propriete', 'titre', 'adresse', 'code_postal', 'ville', 'pays',
            'type_bien', 'bailleur', 'surface', 'nombre_pieces', 'nombre_chambres', 'nombre_salles_bain',
            'ascenseur', 'parking', 'balcon', 'jardin',
            'prix_achat', 'loyer_actuel', 'charges_locataire',
            'etat', 'disponible', 'notes'
        ]
        widgets = {
            'numero_propriete': forms.TextInput(attrs={
                'class': 'form-control',
                'readonly': 'readonly',
                'placeholder': 'Généré automatiquement'
            }),
            'titre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Appartement T3 avec balcon'
            }),
            'bailleur': forms.Select(attrs={
                'class': 'form-select',
                'placeholder': 'Sélectionnez un bailleur'
            }),
            'adresse': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Adresse complète de la propriété'
            }),
            'code_postal': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '75001'
            }),
            'ville': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Paris'
            }),
            'pays': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'France'
            }),
            'type_bien': forms.Select(attrs={
                'class': 'form-select'
            }),
            'surface': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '75.5',
                'step': '0.01',
                'min': '0'
            }),
            'nombre_pieces': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '3',
                'min': '1'
            }),
            'nombre_chambres': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '2',
                'min': '0'
            }),
            'nombre_salles_bain': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '1',
                'min': '0'
            }),
            'prix_achat': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '250000',
                'step': '0.01',
                'min': '0'
            }),
            'loyer_actuel': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '1200',
                'step': '0.01',
                'min': '0'
            }),
            'charges_locataire': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '150',
                'step': '0.01',
                'min': '0'
            }),
            'etat': forms.Select(attrs={
                'class': 'form-select'
            }),
            'disponible': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Notes supplémentaires sur la propriété...'
            }),
        }
        labels = {
            'numero_propriete': _('N° Propriété'),
            'titre': _('Titre de la propriété'),
            'adresse': _('Adresse'),
            'code_postal': _('Code postal'),
            'ville': _('Ville'),
            'pays': _('Pays'),
            'type_bien': _('Type de bien'),
            'bailleur': _('Bailleur'),
            'surface': _('Surface (m²)'),
            'nombre_pieces': _('Nombre de pièces'),
            'nombre_chambres': _('Nombre de chambres'),
            'nombre_salles_bain': _('Nombre de salles de bain'),
            'ascenseur': _('Ascenseur'),
            'parking': _('Parking'),
            'balcon': _('Balcon'),
            'jardin': _('Jardin'),
            'prix_achat': _('Prix d\'achat (XOF)'),
            'loyer_actuel': _('Loyer actuel (XOF)'),
            'charges_locataire': _('Charges locataire (XOF)'),
            'etat': _('État du bien'),
            'disponible': _('Disponible à la location'),
            'notes': _('Notes'),
        }
        help_texts = {
            'titre': _('Donnez un titre descriptif à la propriété'),
            'bailleur': _('Sélectionnez le bailleur propriétaire de cette propriété'),
            'surface': _('Surface en mètres carrés'),
            'prix_achat': _('Prix d\'achat de la propriété (optionnel)'),
            'loyer_actuel': _('Loyer mensuel actuel (optionnel)'),
            'charges_locataire': _('Charges mensuelles à la charge du locataire (eau, électricité, etc.)'),
            'notes': _('Informations supplémentaires sur la propriété'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Personnalisation des champs
        self.fields['type_bien'].empty_label = "Sélectionnez un type de bien"
        self.fields['bailleur'].empty_label = "Sélectionnez un bailleur"
        self.fields['etat'].empty_label = "Sélectionnez l'état"
        
        # Ajout de classes CSS pour les champs requis
        for field_name, field in self.fields.items():
            if field.required:
                field.widget.attrs['class'] = field.widget.attrs.get('class', '') + ' required'

    def clean_surface(self):
        """Validation de la surface."""
        surface = self.cleaned_data.get('surface')
        if surface and surface <= 0:
            raise ValidationError(_('La surface doit être supérieure à 0.'))
        return surface

    def clean_nombre_pieces(self):
        """Validation du nombre de pièces."""
        pieces = self.cleaned_data.get('nombre_pieces')
        if pieces and pieces <= 0:
            raise ValidationError(_('Le nombre de pièces doit être supérieur à 0.'))
        return pieces

    def clean_prix_achat(self):
        """Validation du prix d'achat."""
        prix = self.cleaned_data.get('prix_achat')
        if prix and prix <= 0:
            raise ValidationError(_('Le prix d\'achat doit être supérieur à 0.'))
        return prix

    def clean_loyer_actuel(self):
        """Validation du loyer actuel."""
        loyer = self.cleaned_data.get('loyer_actuel')
        if loyer and loyer <= 0:
            raise ValidationError(_('Le loyer doit être supérieur à 0.'))
        return loyer

    def clean_charges_locataire(self):
        """Validation des charges locataire."""
        charges = self.cleaned_data.get('charges_locataire')
        if charges and charges < 0:
            raise ValidationError(_('Les charges ne peuvent pas être négatives.'))
        return charges

    def clean(self):
        """Validation globale du formulaire."""
        cleaned_data = super().clean()
        
        # Vérification de la cohérence entre chambres et pièces
        nombre_pieces = cleaned_data.get('nombre_pieces')
        nombre_chambres = cleaned_data.get('nombre_chambres')
        
        if nombre_pieces and nombre_chambres and nombre_chambres > nombre_pieces:
            raise ValidationError(_('Le nombre de chambres ne peut pas être supérieur au nombre de pièces.'))
        
        return cleaned_data
    
    def save(self, commit=True, user=None):
        """Sauvegarde la propriété et crée automatiquement les documents associés."""
        propriete = super().save(commit=False)
        
        if commit:
            propriete.save()
            
            # Créer automatiquement les documents dans le système documentaire
            if user:
                self._create_documents_for_propriete(propriete, user)
        
        return propriete
    
    def _create_documents_for_propriete(self, propriete, user):
        """Crée automatiquement les documents pour une propriété."""
        from .models import Document
        
        # Mapping des champs de fichiers vers les types de documents
        document_mapping = {
            'acte_propriete': ('justificatif', 'Acte de propriété'),
            'diagnostic_energetique': ('diagnostic', 'Diagnostic énergétique (DPE)'),
            'diagnostic_plomb': ('diagnostic', 'Diagnostic plomb'),
            'diagnostic_amiante': ('diagnostic', 'Diagnostic amiante'),
        }
        
        for field_name, (doc_type, description) in document_mapping.items():
            file_field = self.cleaned_data.get(field_name)
            if file_field:
                Document.objects.create(
                    nom=f"{description} - {propriete.titre}",
                    type_document=doc_type,
                    description=f"{description} pour la propriété {propriete.numero_propriete}",
                    fichier=file_field,
                    propriete=propriete,
                    statut='valide',
                    cree_par=user,
                    confidentiel=False  # Les documents de propriété ne sont pas confidentiels
                )
        
        # Gestion spéciale pour les photos multiples
        photos_field = self.cleaned_data.get('photos_propriete')
        if photos_field:
            # Si c'est un fichier multiple, créer un document pour chaque photo
            if hasattr(photos_field, '__iter__'):
                for i, photo in enumerate(photos_field):
                    Document.objects.create(
                        nom=f"Photo {i+1} - {propriete.titre}",
                        type_document='autre',
                        description=f"Photo de la propriété {propriete.numero_propriete}",
                        fichier=photo,
                        propriete=propriete,
                        statut='valide',
                        cree_par=user,
                        confidentiel=False
                    )
            else:
                # Si c'est un seul fichier
                Document.objects.create(
                    nom=f"Photo - {propriete.titre}",
                    type_document='autre',
                    description=f"Photo de la propriété {propriete.numero_propriete}",
                    fichier=photos_field,
                    propriete=propriete,
                    statut='valide',
                    cree_par=user,
                    confidentiel=False
                )


class ChargesBailleurForm(forms.ModelForm):
    """Formulaire pour l'ajout et la modification de charges bailleur avec gestion documentaire intégrée."""
    
    # Champs pour les documents requis de la charge
    facture_charge = forms.FileField(
        required=True,
        label=_('Facture de la charge'),
        help_text=_('Facture du fournisseur/prestataire (PDF, JPG, PNG)'),
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,.jpg,.jpeg,.png'
        })
    )
    
    devis_charge = forms.FileField(
        required=False,
        label=_('Devis de la charge'),
        help_text=_('Devis préalable à la facture (PDF, JPG, PNG)'),
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,.jpg,.jpeg,.png'
        })
    )
    
    justificatif_travaux = forms.FileField(
        required=False,
        label=_('Justificatif des travaux'),
        help_text=_('Photos avant/après, rapport d\'intervention (PDF, JPG, PNG)'),
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,.jpg,.jpeg,.png'
        })
    )
    
    class Meta:
        model = ChargesBailleur
        fields = [
            'propriete', 'titre', 'description', 'type_charge',
            'montant', 'date_charge', 'date_echeance', 'priorite'
        ]
        widgets = {
            'propriete': forms.Select(attrs={
                'class': 'form-select'
            }),
            'titre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Réparation chaudière'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Description détaillée de la charge...'
            }),
            'type_charge': forms.Select(attrs={
                'class': 'form-select'
            }),
            'montant': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '150.00',
                'step': '0.01',
                'min': '0'
            }),
            'date_charge': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'priorite': forms.Select(attrs={
                'class': 'form-select'
            }),
            'date_echeance': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
        }
        labels = {
            'propriete': _('Propriété concernée'),
            'titre': _('Titre de la charge'),
            'description': _('Description détaillée'),
            'type_charge': _('Type de charge'),
            'montant': _('Montant (XOF)'),
            'date_charge': _('Date de la charge'),
            'date_echeance': _('Date d\'échéance'),
            'priorite': _('Priorité'),
        }
        help_texts = {
            'propriete': _('Sélectionnez la propriété concernée par cette charge'),
            'titre': _('Donnez un titre clair à cette charge'),
            'description': _('Décrivez en détail la nature de cette charge'),
            'montant': _('Montant de la charge en XOF'),
            'date_charge': _('Date à laquelle cette charge a été effectuée'),
            'date_echeance': _('Date limite pour le paiement de cette charge'),
            'priorite': _('Niveau de priorité pour le remboursement'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Personnalisation des champs
        self.fields['propriete'].empty_label = "Sélectionnez une propriété"
        self.fields['type_charge'].empty_label = "Sélectionnez le type"
        self.fields['priorite'].empty_label = "Sélectionnez la priorité"
        
        # Filtrage des propriétés louées
        self.fields['propriete'].queryset = Propriete.objects.filter(disponible=False)

    def clean_montant(self):
        """Validation du montant."""
        montant = self.cleaned_data.get('montant')
        if montant and montant <= 0:
            raise ValidationError(_('Le montant doit être supérieur à 0.'))
        return montant

    def clean_date_charge(self):
        """Validation de la date de charge."""
        date_charge = self.cleaned_data.get('date_charge')
        if date_charge:
            from django.utils import timezone
            if date_charge > timezone.now().date():
                raise ValidationError(_('La date de charge ne peut pas être dans le futur.'))
        return date_charge
    
    def save(self, commit=True, user=None):
        """Sauvegarde la charge bailleur et crée automatiquement les documents associés."""
        charge = super().save(commit=False)
        
        if commit:
            charge.save()
            
            # Créer automatiquement les documents dans le système documentaire
            if user:
                self._create_documents_for_charge_bailleur(charge, user)
        
        return charge
    
    def _create_documents_for_charge_bailleur(self, charge, user):
        """Crée automatiquement les documents pour une charge bailleur."""
        from .models import Document
        
        # Mapping des champs de fichiers vers les types de documents
        document_mapping = {
            'facture_charge': ('facture', 'Facture de la charge bailleur'),
            'devis_charge': ('devis', 'Devis de la charge bailleur'),
            'justificatif_travaux': ('justificatif', 'Justificatif des travaux bailleur'),
        }
        
        for field_name, (doc_type, description) in document_mapping.items():
            file_field = self.cleaned_data.get(field_name)
            if file_field:
                Document.objects.create(
                    nom=f"{description} - {charge.propriete.titre}",
                    type_document=doc_type,
                    description=f"{description} pour la charge {charge.titre}",
                    fichier=file_field,
                    propriete=charge.propriete,
                    statut='valide',
                    cree_par=user,
                    confidentiel=False  # Les documents de charge ne sont pas confidentiels
                )


class ChargesBailleurDeductionForm(forms.Form):
    """Formulaire pour la déduction des charges bailleur du loyer."""
    
    montant_deduction = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=0.01,
        label=_('Montant à déduire (XOF)'),
        help_text=_('Montant à déduire du loyer pour rembourser les charges bailleur'),
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0.01'
        })
    )
    
    date_deduction = forms.DateField(
        label=_('Date de déduction'),
        help_text=_('Date à laquelle la déduction sera appliquée'),
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    notes = forms.CharField(
        max_length=500,
        required=False,
        label=_('Notes'),
        help_text=_('Commentaires sur cette déduction'),
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Notes sur la déduction...'
        })
    )

    def __init__(self, propriete=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.propriete = propriete
        
        if propriete:
            # Calculer le montant maximum déductible
            loyer_total = propriete.get_loyer_total()
            charges_en_cours = propriete.get_charges_bailleur_en_cours()
            montant_max = min(loyer_total, charges_en_cours)
            
            self.fields['montant_deduction'].widget.attrs['max'] = str(montant_max)
            self.fields['montant_deduction'].help_text = f'Montant maximum déductible : {montant_max} XOF'

    def clean_montant_deduction(self):
        """Validation du montant de déduction."""
        montant = self.cleaned_data.get('montant_deduction')
        
        if self.propriete:
            loyer_total = self.propriete.get_loyer_total()
            charges_en_cours = self.propriete.get_charges_bailleur_en_cours()
            
            if montant > loyer_total:
                raise ValidationError(_('Le montant de déduction ne peut pas dépasser le loyer total.'))
            
            if montant > charges_en_cours:
                raise ValidationError(_('Le montant de déduction ne peut pas dépasser les charges en cours.'))
        
        return montant


class BailleurForm(forms.ModelForm):
    """Formulaire pour l'ajout et la modification de bailleurs avec gestion documentaire intégrée."""
    
    # Validation personnalisée pour le téléphone
    telephone = forms.CharField(
        max_length=20,
        validators=[validate_phone_french],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '01 23 45 67 89'
        })
    )
    
    # Champs pour les documents requis
    piece_identite = forms.FileField(
        required=True,
        label=_('Pièce d\'identité'),
        help_text=_('CNI, passeport ou titre de séjour (PDF, JPG, PNG)'),
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,.jpg,.jpeg,.png'
        })
    )
    
    justificatif_domicile = forms.FileField(
        required=True,
        label=_('Justificatif de domicile'),
        help_text=_('Facture EDF, téléphone, quittance de loyer (PDF, JPG, PNG)'),
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,.jpg,.jpeg,.png'
        })
    )
    
    attestation_bancaire = forms.FileField(
        required=True,
        label=_('Attestation bancaire'),
        help_text=_('RIB ou attestation de compte bancaire (PDF, JPG, PNG)'),
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,.jpg,.jpeg,.png'
        })
    )
    
    declaration_revenus = forms.FileField(
        required=False,
        label=_('Déclaration de revenus'),
        help_text=_('Dernier avis d\'imposition (PDF, JPG, PNG)'),
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,.jpg,.jpeg,.png'
        })
    )
    
    documents_propriete = forms.FileField(
        required=False,
        label=_('Documents de propriété'),
        help_text=_('Acte de propriété, titre de propriété (PDF, JPG, PNG)'),
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,.jpg,.jpeg,.png'
        })
    )
    
    class Meta:
        model = Bailleur
        fields = [
            'numero_bailleur', 'civilite', 'nom', 'prenom', 'date_naissance',
            'email', 'telephone', 'telephone_mobile', 'adresse', 'code_postal',
            'ville', 'pays', 'iban', 'bic', 'banque'
        ]
        widgets = {
            'numero_bailleur': forms.TextInput(attrs={
                'class': 'form-control',
                'readonly': 'readonly',
                'placeholder': 'Généré automatiquement'
            }),
            'civilite': forms.Select(attrs={
                'class': 'form-select'
            }),
            'nom': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Dupont'
            }),
            'prenom': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Jean'
            }),
            'date_naissance': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'jean.dupont@email.com'
            }),
            'telephone_mobile': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '06 12 34 56 78'
            }),
            'adresse': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Adresse du bailleur'
            }),
            'code_postal': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '75001'
            }),
            'ville': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Paris'
            }),
            'pays': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'France'
            }),
            'iban': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'FR76 1234 5678 9012 3456 7890 123'
            }),
            'bic': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'BNPAFRPP123'
            }),
            'banque': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom de la banque'
            }),
        }
        labels = {
            'numero_bailleur': _('N° Bailleur'),
            'civilite': _('Civilité'),
            'nom': _('Nom'),
            'prenom': _('Prénom'),
            'date_naissance': _('Date de naissance'),
            'email': _('Email'),
            'telephone': _('Téléphone'),
            'telephone_mobile': _('Mobile'),
            'adresse': _('Adresse'),
            'code_postal': _('Code postal'),
            'ville': _('Ville'),
            'pays': _('Pays'),
            'iban': _('IBAN'),
            'bic': _('BIC'),
            'banque': _('Banque'),
        }

    def clean_iban(self):
        """Validation de l'IBAN."""
        iban = self.cleaned_data.get('iban')
        if iban:
            # Suppression des espaces pour la validation
            iban_clean = iban.replace(' ', '').upper()
            if not iban_clean.startswith('FR') or len(iban_clean) != 27:
                raise ValidationError(_('L\'IBAN doit être un IBAN français valide (27 caractères).'))
        return iban
    
    def save(self, commit=True, user=None):
        """Sauvegarde le bailleur et crée automatiquement les documents associés."""
        bailleur = super().save(commit=False)
        
        if commit:
            bailleur.save()
            
            # Créer automatiquement les documents dans le système documentaire
            if user:
                self._create_documents_for_bailleur(bailleur, user)
        
        return bailleur
    
    def _create_documents_for_bailleur(self, bailleur, user):
        """Crée automatiquement les documents pour un bailleur."""
        from .models import Document
        
        # Mapping des champs de fichiers vers les types de documents
        document_mapping = {
            'piece_identite': ('justificatif', 'Pièce d\'identité du bailleur'),
            'justificatif_domicile': ('justificatif', 'Justificatif de domicile du bailleur'),
            'attestation_bancaire': ('justificatif', 'Attestation bancaire du bailleur'),
            'declaration_revenus': ('justificatif', 'Déclaration de revenus du bailleur'),
            'documents_propriete': ('justificatif', 'Documents de propriété du bailleur'),
        }
        
        for field_name, (doc_type, description) in document_mapping.items():
            file_field = self.cleaned_data.get(field_name)
            if file_field:
                Document.objects.create(
                    nom=f"{description} - {bailleur.nom} {bailleur.prenom}",
                    type_document=doc_type,
                    description=description,
                    fichier=file_field,
                    bailleur=bailleur,
                    statut='valide',
                    cree_par=user,
                    confidentiel=True  # Les documents personnels sont confidentiels
                )

    def clean_telephone(self):
        """Validation du téléphone."""
        telephone = self.cleaned_data.get('telephone')
        if telephone:
            # Suppression des espaces et caractères spéciaux
            tel_clean = ''.join(filter(str.isdigit, telephone))
            if len(tel_clean) < 8:
                raise ValidationError(_('Le numéro de téléphone doit contenir au moins 8 chiffres.'))
        return telephone


class LocataireForm(forms.ModelForm):
    """Formulaire pour l'ajout et la modification de locataires avec gestion documentaire intégrée."""
    
    # Champs pour les documents requis
    piece_identite = forms.FileField(
        required=True,
        label=_('Pièce d\'identité'),
        help_text=_('CNI, passeport ou titre de séjour (PDF, JPG, PNG)'),
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,.jpg,.jpeg,.png'
        })
    )
    
    justificatif_domicile = forms.FileField(
        required=True,
        label=_('Justificatif de domicile'),
        help_text=_('Facture EDF, téléphone, quittance de loyer (PDF, JPG, PNG)'),
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,.jpg,.jpeg,.png'
        })
    )
    
    justificatifs_revenus = forms.FileField(
        required=True,
        label=_('Justificatifs de revenus'),
        help_text=_('3 derniers bulletins de salaire (PDF, JPG, PNG)'),
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,.jpg,.jpeg,.png'
        })
    )
    
    avis_imposition = forms.FileField(
        required=True,
        label=_('Avis d\'imposition'),
        help_text=_('Dernier avis d\'imposition (PDF, JPG, PNG)'),
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,.jpg,.jpeg,.png'
        })
    )
    
    garant_caution = forms.FileField(
        required=False,
        label=_('Garant/Caution'),
        help_text=_('Attestation de caution ou assurance loyer impayés (PDF, JPG, PNG)'),
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,.jpg,.jpeg,.png'
        })
    )
    
    class Meta:
        model = Locataire
        fields = [
            'numero_locataire', 'civilite', 'nom', 'prenom', 'date_naissance',
            'email', 'telephone', 'telephone_mobile', 'adresse', 'code_postal',
            'ville', 'pays', 'profession', 'employeur', 'revenus_mensuels', 'statut'
        ]
        widgets = {
            'numero_locataire': forms.TextInput(attrs={
                'class': 'form-control',
                'readonly': 'readonly',
                'placeholder': 'Généré automatiquement'
            }),
            'civilite': forms.Select(attrs={
                'class': 'form-control'
            }),
            'nom': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Martin'
            }),
            'prenom': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Sophie'
            }),
            'date_naissance': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'sophie.martin@email.com'
            }),
            'telephone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '01 23 45 67 89'
            }),
            'telephone_mobile': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '06 12 34 56 78'
            }),
            'adresse': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Adresse du locataire'
            }),
            'code_postal': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '75001'
            }),
            'ville': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Paris'
            }),
            'pays': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'France'
            }),
            'profession': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ingénieur'
            }),
            'employeur': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom de l\'employeur'
            }),
            'revenus_mensuels': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '3500',
                'step': '0.01',
                'min': '0'
            }),
            'statut': forms.Select(attrs={
                'class': 'form-control'
            }),
        }
        labels = {
            'numero_locataire': _('N° Locataire'),
            'civilite': _('Civilité'),
            'nom': _('Nom'),
            'prenom': _('Prénom'),
            'date_naissance': _('Date de naissance'),
            'email': _('Email'),
            'telephone': _('Téléphone'),
            'telephone_mobile': _('Mobile'),
            'adresse': _('Adresse'),
            'code_postal': _('Code postal'),
            'ville': _('Ville'),
            'pays': _('Pays'),
            'profession': _('Profession'),
            'employeur': _('Employeur'),
            'revenus_mensuels': _('Revenus mensuels (XOF)'),
            'statut': _('Statut'),
        }
        help_texts = {
            'revenus_mensuels': _('Revenus mensuels nets pour évaluer la capacité de paiement'),
            'statut': _('Statut actuel du locataire'),
        }

    def clean_telephone(self):
        """Validation du téléphone."""
        telephone = self.cleaned_data.get('telephone')
        if telephone:
            # Suppression des espaces et caractères spéciaux
            tel_clean = ''.join(filter(str.isdigit, telephone))
            if len(tel_clean) < 8:
                raise ValidationError(_('Le numéro de téléphone doit contenir au moins 8 chiffres.'))
        return telephone

    def clean_revenus_mensuels(self):
        """Validation des revenus mensuels."""
        revenus = self.cleaned_data.get('revenus_mensuels')
        if revenus and revenus <= 0:
            raise ValidationError(_('Les revenus mensuels doivent être supérieurs à 0.'))
        return revenus
    
    def save(self, commit=True, user=None):
        """Sauvegarde le locataire et crée automatiquement les documents associés."""
        locataire = super().save(commit=False)
        
        if commit:
            locataire.save()
            
            # Créer automatiquement les documents dans le système documentaire
            if user:
                self._create_documents_for_locataire(locataire, user)
        
        return locataire
    
    def _create_documents_for_locataire(self, locataire, user):
        """Crée automatiquement les documents pour un locataire."""
        from .models import Document
        
        # Mapping des champs de fichiers vers les types de documents
        document_mapping = {
            'piece_identite': ('justificatif', 'Pièce d\'identité du locataire'),
            'justificatif_domicile': ('justificatif', 'Justificatif de domicile du locataire'),
            'justificatifs_revenus': ('justificatif', 'Justificatifs de revenus du locataire'),
            'avis_imposition': ('justificatif', 'Avis d\'imposition du locataire'),
            'garant_caution': ('justificatif', 'Garant/Caution du locataire'),
        }
        
        for field_name, (doc_type, description) in document_mapping.items():
            file_field = self.cleaned_data.get(field_name)
            if file_field:
                Document.objects.create(
                    nom=f"{description} - {locataire.nom} {locataire.prenom}",
                    type_document=doc_type,
                    description=description,
                    fichier=file_field,
                    locataire=locataire,
                    statut='valide',
                    cree_par=user,
                    confidentiel=True  # Les documents personnels sont confidentiels
                )


class TypeBienForm(forms.ModelForm):
    """Formulaire pour l'ajout et la modification de types de biens."""
    
    class Meta:
        model = TypeBien
        fields = ['nom', 'description']
        widgets = {
            'nom': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Appartement, Maison, Studio...'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Description du type de bien...'
            }),
        }
        labels = {
            'nom': _('Nom du type'),
            'description': _('Description'),
        } 

class PhotoForm(forms.ModelForm):
    """Formulaire pour la gestion des photos de propriétés avec gestion documentaire intégrée"""
    
    # Champs pour les photos multiples
    photos_multiples = forms.FileField(
        required=False,
        label=_('Photos de la propriété'),
        help_text=_('Sélectionnez une photo (JPG, PNG) - Max 5MB'),
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.jpg,.jpeg,.png'
        })
    )
    
    class Meta:
        model = Photo
        fields = ['image', 'titre', 'description', 'ordre', 'est_principale']
        widgets = {
            'titre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Titre de la photo'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Description de la photo'
            }),
            'ordre': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0
            }),
            'est_principale': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Personnaliser les labels
        self.fields['image'].label = "Sélectionner une image"
        self.fields['image'].help_text = "Formats acceptés: JPG, PNG. Taille max: 5MB"
        self.fields['est_principale'].label = "Définir comme photo principale"

    def clean_image(self):
        image = self.cleaned_data.get('image')
        if image:
            # Vérifier la taille (5MB max)
            if image.size > 5 * 1024 * 1024:
                raise forms.ValidationError(
                    "L'image ne doit pas dépasser 5MB"
                )
            
            # Vérifier le format
            allowed_formats = ['image/jpeg', 'image/png', 'image/jpg']
            if image.content_type not in allowed_formats:
                raise forms.ValidationError(
                    "Format d'image non supporté. Utilisez JPG ou PNG."
                )
        
        return image

class PhotoMultipleForm(forms.Form):
    images = forms.FileField(
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        }),
        label="Sélectionner plusieurs images",
        help_text="Vous pouvez sélectionner plusieurs images à la fois (utilisez Ctrl+clic pour sélectionner plusieurs fichiers)"
    )
    
    def clean_images(self):
        images = self.files.getlist('images')
        if not images:
            return []
        
        cleaned_images = []
        for image in images:
            if image.size > 5 * 1024 * 1024:  # 5MB
                raise ValidationError(f"L'image {image.name} est trop volumineuse. Taille maximum: 5MB")
            
            # Vérifier le type de fichier
            if not image.content_type.startswith('image/'):
                raise ValidationError(f"Le fichier {image.name} n'est pas une image valide")
            
            cleaned_images.append(image)
        
        return cleaned_images


class ProprieteAvecPhotosForm(ProprieteForm):
    """
    Formulaire étendu pour l'ajout de propriétés avec photos
    """
    photos = forms.FileField(
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        }),
        required=False,
        label="Photos de la propriété",
        help_text="Sélectionnez une ou plusieurs photos (utilisez Ctrl+clic pour sélectionner plusieurs fichiers)"
    )
    
    def clean_photos(self):
        photos = self.files.getlist('photos')
        if not photos:
            return []
        
        cleaned_photos = []
        for photo in photos:
            if photo.size > 5 * 1024 * 1024:  # 5MB
                raise ValidationError(f"La photo {photo.name} est trop volumineuse. Taille maximum: 5MB")
            
            # Vérifier le type de fichier
            if not photo.content_type.startswith('image/'):
                raise ValidationError(f"Le fichier {photo.name} n'est pas une image valide")
            
            cleaned_photos.append(photo)
        
        return cleaned_photos


class DocumentForm(forms.ModelForm):
    """Formulaire pour la création et modification de documents."""
    
    class Meta:
        model = Document
        fields = [
            'nom', 'type_document', 'description', 'fichier',
            'propriete', 'bailleur', 'locataire', 'statut',
            'date_expiration', 'tags', 'confidentiel'
        ]
        widgets = {
            'nom': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom du document'
            }),
            'type_document': forms.Select(attrs={
                'class': 'form-select'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Description du document'
            }),
            'fichier': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.jpg,.jpeg,.png'
            }),
            'propriete': forms.Select(attrs={
                'class': 'form-select'
            }),
            'bailleur': forms.Select(attrs={
                'class': 'form-select'
            }),
            'locataire': forms.Select(attrs={
                'class': 'form-select'
            }),
            'statut': forms.Select(attrs={
                'class': 'form-select'
            }),
            'date_expiration': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'tags': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Tags séparés par des virgules'
            }),
            'confidentiel': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Rendre les champs de relation optionnels
        self.fields['propriete'].required = False
        self.fields['bailleur'].required = False
        self.fields['locataire'].required = False
        self.fields['date_expiration'].required = False


class DocumentSearchForm(forms.Form):
    """Formulaire de recherche pour les documents."""
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Rechercher un document...'
        })
    )
    
    type_document = forms.ChoiceField(
        choices=[('', 'Tous les types')] + Document.TYPE_DOCUMENT_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    statut = forms.ChoiceField(
        choices=[('', 'Tous les statuts')] + Document.STATUT_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    propriete = forms.ModelChoiceField(
        queryset=Propriete.objects.filter(disponible=True),
        required=False,
        empty_label="Toutes les propriétés",
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
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


class PieceSelectionForm(forms.Form):
    """Formulaire pour la sélection des pièces dans un contrat."""
    
    pieces = forms.ModelMultipleChoiceField(
        queryset=Piece.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        label=_("Pièces à louer"),
        help_text=_("Sélectionnez les pièces que vous souhaitez louer")
    )
    
    def __init__(self, propriete_id=None, date_debut=None, date_fin=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        if propriete_id:
            # Filtrer les pièces disponibles pour cette propriété
            from .services import GestionPiecesService
            
            if date_debut and date_fin:
                pieces_disponibles = GestionPiecesService.get_pieces_disponibles(
                    propriete_id, date_debut, date_fin
                )
            else:
                pieces_disponibles = GestionPiecesService.get_pieces_disponibles(propriete_id)
            
            self.fields['pieces'].queryset = pieces_disponibles
            self.fields['pieces'].label = f"Pièces disponibles ({pieces_disponibles.count()})"
    
    def clean_pieces(self):
        """Validation personnalisée pour les pièces sélectionnées."""
        pieces = self.cleaned_data.get('pieces')
        
        if not pieces:
            raise forms.ValidationError(_("Vous devez sélectionner au moins une pièce."))
        
        return pieces


class PieceContratForm(forms.ModelForm):
    """Formulaire pour la gestion des pièces dans un contrat."""
    
    class Meta:
        model = PieceContrat
        fields = ['piece', 'loyer_piece', 'charges_piece', 'date_debut_occupation', 'date_fin_occupation']
        widgets = {
            'piece': forms.Select(attrs={'class': 'form-select'}),
            'loyer_piece': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'charges_piece': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'date_debut_occupation': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'date_fin_occupation': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }
    
    def __init__(self, contrat=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        if contrat:
            # Filtrer les pièces disponibles pour ce contrat
            from .services import GestionPiecesService
            
            pieces_disponibles = GestionPiecesService.get_pieces_disponibles(
                contrat.propriete.id,
                contrat.date_debut,
                contrat.date_fin
            )
            
            # Ajouter les pièces déjà assignées à ce contrat
            pieces_assignees = contrat.pieces.all()
            pieces_disponibles = pieces_disponibles | pieces_assignees
            
            self.fields['piece'].queryset = pieces_disponibles
            self.fields['piece'].label = f"Pièce ({pieces_disponibles.count()} disponibles)"
    
    def clean(self):
        """Validation personnalisée pour éviter les conflits."""
        cleaned_data = super().clean()
        
        piece = cleaned_data.get('piece')
        date_debut = cleaned_data.get('date_debut_occupation')
        date_fin = cleaned_data.get('date_fin_occupation')
        
        if piece and date_debut and date_fin:
            # Vérifier que la pièce est disponible pour cette période
            if not piece.est_disponible(date_debut, date_fin):
                raise forms.ValidationError(
                    _("La pièce '{piece}' n'est pas disponible pour la période du {debut} au {fin}.").format(
                        piece=piece.nom,
                        debut=date_debut,
                        fin=date_fin
                    )
                )
        
        return cleaned_data


class ContratPiecesForm(forms.Form):
    """Formulaire principal pour la création/modification d'un contrat avec pièces."""
    
    # Informations du contrat
    numero_contrat = forms.CharField(
        max_length=50,
        label=_("Numéro de contrat"),
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    propriete = forms.ModelChoiceField(
        queryset=Propriete.objects.filter(is_deleted=False),
        label=_("Propriété"),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    locataire = forms.ModelChoiceField(
        queryset=Locataire.objects.filter(is_deleted=False),
        label=_("Locataire"),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    # Dates
    date_debut = forms.DateField(
        label=_("Date de début"),
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    
    date_fin = forms.DateField(
        label=_("Date de fin"),
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    
    date_signature = forms.DateField(
        label=_("Date de signature"),
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    
    # Informations financières
    loyer_mensuel = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        label=_("Loyer mensuel"),
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )
    
    charges_mensuelles = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        label=_("Charges mensuelles"),
        required=False,
        initial=0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )
    
    # Sélection des pièces
    pieces = forms.ModelMultipleChoiceField(
        queryset=Piece.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        label=_("Pièces à louer"),
        help_text=_("Sélectionnez les pièces que vous souhaitez louer")
    )
    
    # Informations supplémentaires
    depot_garantie = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        label=_("Dépôt de garantie"),
        required=False,
        initial=0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )
    
    avance_loyer = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        label=_("Avance de loyer"),
        required=False,
        initial=0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )
    
    jour_paiement = forms.IntegerField(
        min_value=1,
        max_value=31,
        label=_("Jour de paiement"),
        initial=1,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    
    mode_paiement = forms.ChoiceField(
        choices=[
            ('virement', 'Virement bancaire'),
            ('cheque', 'Chèque'),
            ('especes', 'Espèces'),
            ('prelevement', 'Prélèvement automatique'),
        ],
        label=_("Mode de paiement"),
        initial='virement',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    def __init__(self, contrat=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        if contrat:
            # Pré-remplir les champs avec les données du contrat existant
            self.fields['numero_contrat'].initial = contrat.numero_contrat
            self.fields['propriete'].initial = contrat.propriete
            self.fields['locataire'].initial = contrat.locataire
            self.fields['date_debut'].initial = contrat.date_debut
            self.fields['date_fin'].initial = contrat.date_fin
            self.fields['date_signature'].initial = contrat.date_signature
            self.fields['loyer_mensuel'].initial = contrat.loyer_mensuel
            self.fields['charges_mensuelles'].initial = contrat.charges_mensuelles
            self.fields['depot_garantie'].initial = contrat.depot_garantie
            self.fields['avance_loyer'].initial = contrat.avance_loyer
            self.fields['jour_paiement'].initial = contrat.jour_paiement
            self.fields['mode_paiement'].initial = contrat.mode_paiement
            
            # Pré-sélectionner les pièces déjà assignées
            self.fields['pieces'].initial = contrat.pieces.all()
        
        # Mettre à jour le queryset des pièces si une propriété est sélectionnée
        if 'propriete' in self.data:
            try:
                propriete_id = int(self.data.get('propriete'))
                self.fields['pieces'].queryset = Piece.objects.filter(
                    propriete_id=propriete_id,
                    is_deleted=False
                )
            except (ValueError, TypeError):
                pass
        elif self.initial.get('propriete'):
            propriete_id = self.initial['propriete'].id
            self.fields['pieces'].queryset = Piece.objects.filter(
                propriete_id=propriete_id,
                is_deleted=False
            )
    
    def clean(self):
        """Validation personnalisée pour éviter les conflits de pièces."""
        cleaned_data = super().clean()
        
        propriete = cleaned_data.get('propriete')
        pieces = cleaned_data.get('pieces')
        date_debut = cleaned_data.get('date_debut')
        date_fin = cleaned_data.get('date_fin')
        
        if propriete and pieces and date_debut and date_fin:
            # Vérifier la disponibilité des pièces
            from .services import ValidationContratService
            
            disponible, conflits = ValidationContratService.verifier_disponibilite_pieces(
                propriete_id=propriete.id,
                pieces_ids=[p.id for p in pieces],
                date_debut=date_debut,
                date_fin=date_fin,
                contrat_existant=getattr(self, 'contrat', None)
            )
            
            if not disponible:
                erreurs = []
                for conflit in conflits:
                    if conflit['type'] == 'conflit_dates':
                        erreurs.append(
                            _("Conflit pour la pièce '{piece}': {raison} "
                              "(Contrat {contrat} - {locataire} du {periode})").format(
                                piece=conflit['piece'],
                                raison=conflit['raison'],
                                contrat=conflit['contrat_existant'],
                                locataire=conflit['locataire_existant'],
                                periode=conflit['periode']
                            )
                        )
                    else:
                        erreurs.append(
                            _("Conflit pour la pièce '{piece}': {raison}").format(
                                piece=conflit['piece'],
                                raison=conflit['raison']
                            )
                        )
                
                if erreurs:
                    raise forms.ValidationError(erreurs)
        
        return cleaned_data 


 