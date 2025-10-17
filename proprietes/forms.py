from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from decimal import Decimal
from .models import Propriete, Bailleur, Locataire, TypeBien, ChargesBailleur, Photo, Document, Piece, PieceContrat, UniteLocative, ReservationUnite
from django.core.validators import RegexValidator
# Imports supprimés - utilisation du système simple comme BailleurForm
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
        required=False,
        label=_('Acte de propriété'),
        help_text=_('Acte de propriété ou titre de propriété (PDF, JPG, PNG)'),
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,.jpg,.jpeg,.png'
        })
    )
    
    diagnostic_energetique = forms.FileField(
        required=False,
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
            'type_bien', 'type_gestion', 'bailleur', 'surface', 'nombre_pieces', 'nombre_chambres', 'nombre_salles_bain',
            'ascenseur', 'parking', 'balcon', 'jardin', 'cuisine',
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
            'type_gestion': forms.Select(attrs={
                'class': 'form-select'
            }),
            'surface': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '75.5 (optionnel)',
                'step': '0.01',
                'min': '0'
            }),
            'nombre_pieces': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '3 (optionnel)',
                'min': '1'
            }),
            'nombre_chambres': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '2 (optionnel)',
                'min': '0'
            }),
            'nombre_salles_bain': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '1 (optionnel)',
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
            'ascenseur': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'parking': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'balcon': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'jardin': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'cuisine': forms.CheckboxInput(attrs={
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
            'type_gestion': _('Type de gestion'),
            'bailleur': _('Bailleur'),
            'surface': _('Surface (m²)'),
            'nombre_pieces': _('Nombre de pièces'),
            'nombre_chambres': _('Nombre de chambres'),
            'nombre_salles_bain': _('Nombre de salles de bain'),
            'ascenseur': _('Ascenseur'),
            'parking': _('Parking'),
            'balcon': _('Balcon'),
            'jardin': _('Jardin'),
            'cuisine': _('Cuisine'),
            'prix_achat': _('Prix d\'achat (F CFA)'),
            'loyer_actuel': _('Loyer actuel (F CFA)'),
            'charges_locataire': _('Charges locataire (F CFA)'),
            'etat': _('État du bien'),
            'disponible': _('Disponible à la location'),
            'notes': _('Notes'),
        }
        help_texts = {
            'titre': _('Donnez un titre descriptif à la propriété'),
            'type_gestion': _('Définit si la propriété est louable entièrement ou par unités multiples'),
            'bailleur': _('Sélectionnez le bailleur propriétaire de cette propriété'),
            'surface': _('Surface en mètres carrés (optionnel)'),
            'nombre_pieces': _('Nombre total de pièces de la propriété (optionnel)'),
            'nombre_chambres': _('Nombre de chambres à coucher (optionnel)'),
            'nombre_salles_bain': _('Nombre de salles de bain (optionnel)'),
            'prix_achat': _('Prix d\'achat de la propriété (optionnel)'),
            'loyer_actuel': _('Loyer mensuel actuel (optionnel)'),
            'charges_locataire': _('Charges mensuelles à la charge du locataire (eau, électricité, etc.) - Optionnel'),
            'notes': _('Informations supplémentaires sur la propriété'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Personnalisation des champs
        self.fields['type_bien'].empty_label = "Sélectionnez un type de bien"
        self.fields['type_gestion'].empty_label = "Sélectionnez le type de gestion"
        self.fields['bailleur'].empty_label = "Sélectionnez un bailleur"
        self.fields['etat'].empty_label = "Sélectionnez l'état"
        
        # S'assurer que le queryset des types de biens est correct
        from .models import TypeBien
        self.fields['type_bien'].queryset = TypeBien.objects.all()
        
        # Rendre le champ charges_locataire optionnel
        self.fields['charges_locataire'].required = False
        
        # Rendre le champ numero_propriete optionnel (généré automatiquement)
        self.fields['numero_propriete'].required = False
        
        # Rendre les champs de caractéristiques optionnels
        self.fields['surface'].required = False
        self.fields['nombre_pieces'].required = False
        self.fields['nombre_chambres'].required = False
        self.fields['nombre_salles_bain'].required = False
        
        # Rendre les champs financiers optionnels
        self.fields['prix_achat'].required = False
        # Le loyer_actuel sera rendu conditionnel selon le type de gestion
        self.fields['loyer_actuel'].required = False
        
        # Ajout de classes CSS pour les champs requis
        for field_name, field in self.fields.items():
            if field.required:
                field.widget.attrs['class'] = field.widget.attrs.get('class', '') + ' required'

    def clean_surface(self):
        """Validation de la surface."""
        surface = self.cleaned_data.get('surface')
        if surface is not None and surface <= 0:
            raise ValidationError(_('La surface doit être supérieure à 0.'))
        return surface

    def clean_nombre_pieces(self):
        """Validation du nombre de pièces."""
        pieces = self.cleaned_data.get('nombre_pieces')
        if pieces is not None and pieces <= 0:
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

    def clean_numero_propriete(self):
        """Validation intelligente du numéro de propriété - Plus jamais de doublons."""
        from core.robust_id_generator import RobustIDGenerator
        
        numero_propriete = self.cleaned_data.get('numero_propriete')
        
        if numero_propriete:
            # Vérifier si le numéro existe déjà
            from proprietes.models import Propriete
            queryset = Propriete.objects.filter(
                numero_propriete=numero_propriete,
                is_deleted=False
            )
            
            if self.instance and self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            
            if queryset.exists():
                # Le numéro existe, générer un nouveau numéro vraiment unique
                try:
                    numero_propriete = RobustIDGenerator.generate_property_id()
                    self._auto_generated = True
                    self._original_number = self.cleaned_data.get('numero_propriete')
                except Exception as e:
                    # En cas d'erreur, utiliser un timestamp unique
                    from datetime import datetime
                    import uuid
                    timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')[:-3]
                    unique_id = str(uuid.uuid4())[:8]
                    numero_propriete = f"PRO-{timestamp}-{unique_id}"
                    self._auto_generated = True
                    self._original_number = self.cleaned_data.get('numero_propriete')
        else:
            # Aucun numéro fourni, générer automatiquement
            try:
                numero_propriete = RobustIDGenerator.generate_property_id()
                self._auto_generated = True
                self._original_number = None
            except Exception as e:
                # En cas d'erreur, utiliser un timestamp unique
                from datetime import datetime
                import uuid
                timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')[:-3]
                unique_id = str(uuid.uuid4())[:8]
                numero_propriete = f"PRO-{timestamp}-{unique_id}"
                self._auto_generated = True
                self._original_number = None
        
        return numero_propriete
    
    def clean(self):
        """Validation globale du formulaire."""
        cleaned_data = super().clean()
        
        # Vérification de la cohérence entre chambres et pièces (seulement si les deux sont renseignés)
        nombre_pieces = cleaned_data.get('nombre_pieces')
        nombre_chambres = cleaned_data.get('nombre_chambres')
        
        if nombre_pieces is not None and nombre_chambres is not None and nombre_chambres > nombre_pieces:
            raise ValidationError(_('Le nombre de chambres ne peut pas être supérieur au nombre de pièces.'))
        
        # Validation conditionnelle du loyer selon le type de gestion
        type_gestion = cleaned_data.get('type_gestion')
        loyer_actuel = cleaned_data.get('loyer_actuel')
        
        if type_gestion == 'propriete_entiere':
            # Pour une propriété entière, le loyer actuel est obligatoire
            if not loyer_actuel or loyer_actuel <= 0:
                raise ValidationError(_('Le loyer actuel est obligatoire pour une propriété entière.'))
        elif type_gestion == 'unites_multiples':
            # Pour des unités multiples, le loyer actuel n'est pas utilisé (chaque pièce a son propre loyer)
            # On peut le mettre à 0 ou le laisser vide
            if loyer_actuel and loyer_actuel > 0:
                # Avertir l'utilisateur que ce loyer ne sera pas utilisé
                self.add_error('loyer_actuel', _('Pour des unités multiples, le loyer global n\'est pas utilisé. Chaque pièce aura son propre loyer.'))
        
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
        from django.core.files.base import ContentFile
        import os
        
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
                try:
                    # Vérifier que c'est un objet File valide
                    if hasattr(file_field, 'read') and hasattr(file_field, 'name'):
                        # C'est déjà un objet File valide
                        fichier = file_field
                    else:
                        # C'est probablement des bytes, créer un ContentFile
                        if isinstance(file_field, bytes):
                            fichier = ContentFile(file_field, name=f"{field_name}_{propriete.numero_propriete}.pdf")
                        else:
                            # Essayer de convertir en ContentFile
                            fichier = ContentFile(file_field, name=f"{field_name}_{propriete.numero_propriete}.pdf")
                    
                    Document.objects.create(
                        nom=f"{description} - {propriete.titre}",
                        type_document=doc_type,
                        description=f"{description} pour la propriété {propriete.numero_propriete}",
                        fichier=fichier,
                        propriete=propriete,
                        statut='valide',
                        cree_par=user,
                        confidentiel=False  # Les documents de propriété ne sont pas confidentiels
                    )
                except Exception as e:
                    print(f"Erreur lors de la création du document {field_name}: {e}")
                    # Créer un document sans fichier pour éviter de bloquer la création
                    Document.objects.create(
                        nom=f"{description} - {propriete.titre} (Erreur fichier)",
                        type_document=doc_type,
                        description=f"{description} pour la propriété {propriete.numero_propriete} - Erreur: {str(e)}",
                        propriete=propriete,
                        statut='brouillon',
                        cree_par=user,
                        confidentiel=False
                    )
        
        # Gestion spéciale pour les photos multiples
        photos_field = self.cleaned_data.get('photos_propriete')
        if photos_field:
            try:
                # Si c'est un fichier multiple, créer un document pour chaque photo
                if hasattr(photos_field, '__iter__') and not hasattr(photos_field, 'read'):
                    for i, photo in enumerate(photos_field):
                        if hasattr(photo, 'read') and hasattr(photo, 'name'):
                            fichier = photo
                        else:
                            # Créer un ContentFile pour les bytes
                            if isinstance(photo, bytes):
                                fichier = ContentFile(photo, name=f"photo_{i+1}_{propriete.numero_propriete}.jpg")
                            else:
                                fichier = ContentFile(photo, name=f"photo_{i+1}_{propriete.numero_propriete}.jpg")
                        
                        Document.objects.create(
                            nom=f"Photo {i+1} - {propriete.titre}",
                            type_document='autre',
                            description=f"Photo de la propriété {propriete.numero_propriete}",
                            fichier=fichier,
                            propriete=propriete,
                            statut='valide',
                            cree_par=user,
                            confidentiel=False
                        )
                else:
                    # Si c'est un seul fichier
                    if hasattr(photos_field, 'read') and hasattr(photos_field, 'name'):
                        fichier = photos_field
                    else:
                        if isinstance(photos_field, bytes):
                            fichier = ContentFile(photos_field, name=f"photo_{propriete.numero_propriete}.jpg")
                        else:
                            fichier = ContentFile(photos_field, name=f"photo_{propriete.numero_propriete}.jpg")
                    
                    Document.objects.create(
                        nom=f"Photo - {propriete.titre}",
                        type_document='autre',
                        description=f"Photo de la propriété {propriete.numero_propriete}",
                        fichier=fichier,
                        propriete=propriete,
                        statut='valide',
                        cree_par=user,
                        confidentiel=False
                    )
            except Exception as e:
                print(f"Erreur lors de la création des photos: {e}")
                # Créer un document d'erreur
                Document.objects.create(
                    nom=f"Photos - {propriete.titre} (Erreur)",
                    type_document='autre',
                    description=f"Photos de la propriété {propriete.numero_propriete} - Erreur: {str(e)}",
                    propriete=propriete,
                    statut='brouillon',
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
            'montant': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '150.00',
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
            'montant': _('Montant (F CFA)'),
            'date_charge': _('Date de la charge'),
            'date_echeance': _('Date d\'échéance'),
            'priorite': _('Priorité'),
        }
        help_texts = {
            'propriete': _('Sélectionnez la propriété concernée par cette charge'),
            'titre': _('Donnez un titre clair à cette charge'),
            'description': _('Décrivez en détail la nature de cette charge'),
            'montant': _('Montant de la charge en F CFA'),
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
        if montant:
            # Remplacer les virgules par des points pour la validation
            if isinstance(montant, str):
                montant_clean = montant.replace(',', '.')
                try:
                    montant_decimal = Decimal(montant_clean)
                    if montant_decimal <= 0:
                        raise ValidationError(_('Le montant doit être supérieur à 0.'))
                    if montant_decimal > Decimal('999999999.99'):
                        raise ValidationError(_('Le montant est trop élevé (maximum 999,999,999.99 F CFA).'))
                    return montant_decimal
                except (ValueError, TypeError):
                    raise ValidationError(_('Le montant doit être un nombre valide.'))
            elif montant <= 0:
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
        from django.core.files.base import ContentFile
        
        # Mapping des champs de fichiers vers les types de documents
        document_mapping = {
            'facture_charge': ('facture', 'Facture de la charge bailleur'),
            'devis_charge': ('devis', 'Devis de la charge bailleur'),
            'justificatif_travaux': ('justificatif', 'Justificatif des travaux bailleur'),
        }
        
        for field_name, (doc_type, description) in document_mapping.items():
            file_field = self.cleaned_data.get(field_name)
            if file_field:
                try:
                    # Vérifier que c'est un objet File valide
                    if hasattr(file_field, 'read') and hasattr(file_field, 'name'):
                        fichier = file_field
                    else:
                        # Créer un ContentFile pour les bytes
                        if isinstance(file_field, bytes):
                            fichier = ContentFile(file_field, name=f"{field_name}_{charge.id}.pdf")
                        else:
                            fichier = ContentFile(file_field, name=f"{field_name}_{charge.id}.pdf")
                    
                    Document.objects.create(
                        nom=f"{description} - {charge.propriete.titre}",
                        type_document=doc_type,
                        description=f"{description} pour la charge {charge.titre}",
                        fichier=fichier,
                        propriete=charge.propriete,
                        statut='valide',
                        cree_par=user,
                        confidentiel=False  # Les documents de charge ne sont pas confidentiels
                    )
                except Exception as e:
                    print(f"Erreur lors de la création du document {field_name}: {e}")
                    # Créer un document d'erreur
                    Document.objects.create(
                        nom=f"{description} - {charge.propriete.titre} (Erreur)",
                        type_document=doc_type,
                        description=f"{description} pour la charge {charge.titre} - Erreur: {str(e)}",
                        propriete=charge.propriete,
                        statut='brouillon',
                        cree_par=user,
                        confidentiel=False
                    )


class ChargesBailleurDeductionForm(forms.Form):
    """Formulaire pour la déduction des charges bailleur du loyer."""
    
    montant_deduction = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=0.01,
        label=_('Montant à déduire (F CFA)'),
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
    
    motif = forms.CharField(
        max_length=200,
        required=True,
        label=_('Motif de la déduction'),
        help_text=_('Raison de cette déduction'),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ex: Réparation plomberie, travaux urgents...'
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
            # Calculer le montant maximum déductible basé sur le retrait mensuel du bailleur
            from paiements.models import RetraitBailleur
            from django.db.models import Sum
            from datetime import date
            
            # Récupérer le retrait mensuel du bailleur pour le mois en cours
            mois_actuel = date.today().replace(day=1)
            retrait_mensuel = RetraitBailleur.objects.filter(
                bailleur=propriete.bailleur,
                mois_retrait__year=mois_actuel.year,
                mois_retrait__month=mois_actuel.month,
                statut__in=['en_attente', 'valide', 'paye']
            ).aggregate(
                total=Sum('montant_net_a_payer')
            )['total'] or 0
            
            # Si pas de retrait mensuel, utiliser le total mensuel calculé
            if retrait_mensuel == 0:
                retrait_mensuel = propriete.get_total_mensuel_bailleur()
            
            charges_en_cours = propriete.get_charges_bailleur_en_cours()
            montant_max = min(retrait_mensuel, charges_en_cours)
            
            self.fields['montant_deduction'].widget.attrs['max'] = str(montant_max)
            self.fields['montant_deduction'].help_text = f'Montant maximum déductible : {montant_max} F CFA (basé sur le retrait mensuel du bailleur)'

    def clean_montant_deduction(self):
        """Validation du montant de déduction basée sur le retrait mensuel du bailleur."""
        montant = self.cleaned_data.get('montant_deduction')
        
        if self.propriete and montant:
            # Calculer le retrait mensuel du bailleur
            from paiements.models import RetraitBailleur
            from django.db.models import Sum
            from datetime import date
            
            # Récupérer le retrait mensuel du bailleur pour le mois en cours
            mois_actuel = date.today().replace(day=1)
            retrait_mensuel = RetraitBailleur.objects.filter(
                bailleur=self.propriete.bailleur,
                mois_retrait__year=mois_actuel.year,
                mois_retrait__month=mois_actuel.month,
                statut__in=['en_attente', 'valide', 'paye']
            ).aggregate(
                total=Sum('montant_net_a_payer')
            )['total'] or 0
            
            # Si pas de retrait mensuel, utiliser le total mensuel calculé
            if retrait_mensuel == 0:
                retrait_mensuel = self.propriete.get_total_mensuel_bailleur()
            
            # Récupérer les charges en cours
            charges_en_cours = self.propriete.get_charges_bailleur_en_cours()
            
            # Validation basée sur le retrait mensuel du bailleur
            if montant > retrait_mensuel:
                raise ValidationError(
                    _('Le montant de déduction ne peut pas dépasser le retrait mensuel du bailleur '
                      f'({retrait_mensuel} F CFA).')
                )
            
            if montant > charges_en_cours:
                raise ValidationError(
                    _('Le montant de déduction ne peut pas dépasser les charges en cours '
                      f'({charges_en_cours} F CFA).')
                )
        
        return montant


class BailleurForm(forms.ModelForm):
    """Formulaire pour l'ajout et la modification de bailleurs avec gestion documentaire intégrée."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Utiliser des champs select classiques qui fonctionnent
        self.fields['civilite'].widget = forms.Select(attrs={
            'class': 'form-select'
        })
        self.fields['civilite'].choices = [
            ('', '---------'),
            ('M', 'Monsieur'),
            ('Mme', 'Madame'),
            ('Mlle', 'Mademoiselle'),
        ]
        # Rendre le champ optionnel avec valeur par défaut
        self.fields['civilite'].required = False
        if not self.instance.pk:  # Nouveau bailleur
            self.fields['civilite'].initial = 'M'
        
        # Rendre le champ numero_bailleur en lecture seule
        self.fields['numero_bailleur'].widget.attrs['readonly'] = True
    
    
    # Validation personnalisée pour le téléphone
    telephone = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '01 23 45 67 89'
        })
    )
    
    # Champs pour les documents optionnels
    piece_identite = forms.FileField(
        required=False,
        label=_('Pièce d\'identité'),
        help_text=_('CNI, passeport ou titre de séjour (PDF, JPG, PNG)'),
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,.jpg,.jpeg,.png'
        })
    )
    
    justificatif_domicile = forms.FileField(
        required=False,
        label=_('Justificatif de domicile'),
        help_text=_('Facture EDF, téléphone, quittance de loyer (PDF, JPG, PNG)'),
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,.jpg,.jpeg,.png'
        })
    )
    
    attestation_bancaire = forms.FileField(
        required=False,
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
    
    def clean(self):
        """Validation globale du formulaire avec prévention des doublons."""
        cleaned_data = super().clean()
        
        # Vérifier les doublons d'informations de contact
        from core.duplicate_prevention import validate_unique_contact_info
        try:
            validate_unique_contact_info(
                self._meta.model, 
                self.instance, 
                ['email', 'telephone']
            )
        except ValidationError as e:
            # Ajouter l'erreur aux champs concernés
            if 'email' in str(e):
                self.add_error('email', e)
            if 'telephone' in str(e):
                self.add_error('telephone', e)
        
        return cleaned_data
    
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
        from django.core.files.base import ContentFile
        
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
                try:
                    # Vérifier que c'est un objet File valide
                    if hasattr(file_field, 'read') and hasattr(file_field, 'name'):
                        fichier = file_field
                    else:
                        # Créer un ContentFile pour les bytes
                        if isinstance(file_field, bytes):
                            fichier = ContentFile(file_field, name=f"{field_name}_{bailleur.id}.pdf")
                        else:
                            fichier = ContentFile(file_field, name=f"{field_name}_{bailleur.id}.pdf")
                    
                    Document.objects.create(
                        nom=f"{description} - {bailleur.nom} {bailleur.prenom}",
                        type_document=doc_type,
                        description=description,
                        fichier=fichier,
                        bailleur=bailleur,
                        statut='valide',
                        cree_par=user,
                        confidentiel=True  # Les documents personnels sont confidentiels
                    )
                except Exception as e:
                    print(f"Erreur lors de la création du document {field_name}: {e}")
                    # Créer un document d'erreur
                    Document.objects.create(
                        nom=f"{description} - {bailleur.nom} {bailleur.prenom} (Erreur)",
                        type_document=doc_type,
                        description=f"{description} - Erreur: {str(e)}",
                        bailleur=bailleur,
                        statut='brouillon',
                        cree_par=user,
                        confidentiel=True
                    )

    def clean_telephone(self):
        """Validation du téléphone."""
        telephone = self.cleaned_data.get('telephone')
        if telephone:
            # Nettoyer le numéro (supprimer espaces, tirets, points)
            clean_number = re.sub(r'[\s\-\.]', '', telephone)
            
            # Vérifier que c'est bien des chiffres (avec éventuellement + au début)
            if not re.match(r'^\+?[0-9]+$', clean_number):
                raise ValidationError(_('Le numéro de téléphone ne peut contenir que des chiffres et éventuellement un + au début.'))
            
            # Vérifier la longueur minimale (8 chiffres)
            digits_only = re.sub(r'^\+', '', clean_number)
            if len(digits_only) < 8:
                raise ValidationError(_('Le numéro de téléphone doit contenir au moins 8 chiffres.'))
            
            # Vérifier la longueur maximale (15 chiffres selon les standards internationaux)
            if len(digits_only) > 15:
                raise ValidationError(_('Le numéro de téléphone ne peut pas dépasser 15 chiffres.'))
            
            # Formater le numéro pour un affichage cohérent
            if clean_number.startswith('0') and len(digits_only) == 10:
                # Format français : 01 23 45 67 89
                formatted = f"{clean_number[:2]} {clean_number[2:4]} {clean_number[4:6]} {clean_number[6:8]} {clean_number[8:10]}"
                return formatted
            elif clean_number.startswith('33') and len(digits_only) == 11:
                # Format international français : +33 1 23 45 67 89
                formatted = f"+{clean_number[:2]} {clean_number[2:3]} {clean_number[3:5]} {clean_number[5:7]} {clean_number[7:9]} {clean_number[9:11]}"
                return formatted
            elif clean_number.startswith('+'):
                # Déjà en format international, garder tel quel
                return clean_number
            else:
                # Format local, garder tel quel
                return telephone
                
        return telephone

    def clean_telephone_mobile(self):
        """Validation du téléphone mobile."""
        telephone_mobile = self.cleaned_data.get('telephone_mobile')
        if telephone_mobile:
            # Nettoyer le numéro (supprimer espaces, tirets, points)
            clean_number = re.sub(r'[\s\-\.]', '', telephone_mobile)
            
            # Vérifier que c'est bien des chiffres (avec éventuellement + au début)
            if not re.match(r'^\+?[0-9]+$', clean_number):
                raise ValidationError(_('Le numéro de téléphone mobile ne peut contenir que des chiffres et éventuellement un + au début.'))
            
            # Vérifier la longueur minimale (8 chiffres)
            digits_only = re.sub(r'^\+', '', clean_number)
            if len(digits_only) < 8:
                raise ValidationError(_('Le numéro de téléphone mobile doit contenir au moins 8 chiffres.'))
            
            # Vérifier la longueur maximale (15 chiffres selon les standards internationaux)
            if len(digits_only) > 15:
                raise ValidationError(_('Le numéro de téléphone mobile ne peut pas dépasser 15 chiffres.'))
            
            # Formater le numéro pour un affichage cohérent
            if clean_number.startswith('0') and len(digits_only) == 10:
                # Format français : 06 12 34 56 78
                formatted = f"{clean_number[:2]} {clean_number[2:4]} {clean_number[4:6]} {clean_number[6:8]} {clean_number[8:10]}"
                return formatted
            elif clean_number.startswith('33') and len(digits_only) == 11:
                # Format international français : +33 6 12 34 56 78
                formatted = f"+{clean_number[:2]} {clean_number[2:3]} {clean_number[3:5]} {clean_number[5:7]} {clean_number[7:9]} {clean_number[9:11]}"
                return formatted
            elif clean_number.startswith('+'):
                # Déjà en format international, garder tel quel
                return clean_number
            else:
                # Format local, garder tel quel
                return telephone_mobile
                
        return telephone_mobile


class LocataireForm(forms.ModelForm):
    """Formulaire pour l'ajout et la modification de locataires - Parfaitement lié au modèle."""
    
    # Champs de téléphone simples comme dans BailleurForm
    telephone = forms.CharField(
        max_length=20,
        required=True,
        label=_('Téléphone principal'),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '01 23 45 67 89'
        })
    )
    
    telephone_mobile = forms.CharField(
        max_length=20,
        required=False,
        label=_('Téléphone mobile'),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '06 12 34 56 78'
        })
    )
    
    garant_telephone = forms.CharField(
        max_length=20,
        required=False,
        label=_('Téléphone du garant'),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '01 23 45 67 89'
        })
    )
    
    # Champs civilité en saisie libre
    civilite = forms.CharField(
        max_length=50,
        required=False,
        label=_('Civilité'),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Monsieur, Madame, Mademoiselle, Docteur, etc.'
        })
    )
    
    garant_civilite = forms.CharField(
        max_length=50,
        required=False,
        label=_('Civilité du garant'),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Monsieur, Madame, Mademoiselle, Docteur, etc.'
        })
    )
    
    class Meta:
        model = Locataire
        fields = [
            'civilite', 'nom', 'prenom', 'date_naissance',
            'email', 'adresse', 'code_postal', 'ville', 'pays', 'profession', 
            'employeur', 'revenus_mensuels', 'garant_civilite', 'garant_nom', 
            'garant_prenom', 'garant_email', 'garant_profession', 'garant_employeur', 
            'garant_revenus_mensuels', 'garant_adresse', 'garant_code_postal',
            'garant_ville', 'garant_pays', 'garant_piece_identite', 'statut'
        ]
        widgets = {
            'civilite': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Monsieur, Madame, Mademoiselle, Docteur, etc.'
            }),
            'nom': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom de famille'
            }),
            'prenom': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Prénom'
            }),
            'date_naissance': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'email@exemple.com'
            }),
            'telephone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Téléphone principal'
            }),
            'telephone_mobile': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Téléphone mobile (optionnel)'
            }),
            'adresse': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Adresse complète'
            }),
            'code_postal': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Code postal'
            }),
            'ville': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ville'
            }),
            'pays': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Pays',
                'value': 'France'
            }),
            'profession': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Profession (optionnel)'
            }),
            'employeur': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Employeur (optionnel)'
            }),
            'revenus_mensuels': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Revenus mensuels en F CFA (optionnel)',
                'step': '0.01',
                'min': '0'
            }),
            'garant_civilite': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Monsieur, Madame, Mademoiselle, Docteur, etc.'
            }),
            'garant_nom': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom du garant (optionnel)'
            }),
            'garant_prenom': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Prénom du garant (optionnel)'
            }),
            'garant_telephone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Téléphone du garant (optionnel)'
            }),
            'garant_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Email du garant (optionnel)'
            }),
            'garant_profession': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Profession du garant (optionnel)'
            }),
            'garant_employeur': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Employeur du garant (optionnel)'
            }),
            'garant_revenus_mensuels': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Revenus mensuels du garant en F CFA (optionnel)',
                'step': '0.01',
                'min': '0'
            }),
            'garant_adresse': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Adresse du garant (optionnel)'
            }),
            'garant_code_postal': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Code postal du garant (optionnel)'
            }),
            'garant_ville': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ville du garant (optionnel)'
            }),
            'garant_pays': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Pays du garant (optionnel)',
                'value': 'France'
            }),
            'garant_piece_identite': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.jpg,.jpeg,.png'
            }),
            'statut': forms.Select(attrs={
                'class': 'form-select'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Configurer le champ statut avec un select classique
        self.fields['statut'].widget = forms.Select(attrs={
            'class': 'form-select'
        })
        self.fields['statut'].choices = [
            ('actif', 'Actif'),
            ('inactif', 'Inactif'),
            ('suspendu', 'Suspendu'),
        ]
        
        # Valeurs par défaut pour les nouveaux locataires
        if not self.instance.pk:
            self.fields['civilite'].initial = 'M'
            self.fields['statut'].initial = 'actif'
            self.fields['pays'].initial = 'France'
            self.fields['garant_pays'].initial = 'France'
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Validation des revenus du garant
        revenus_locataire = cleaned_data.get('revenus_mensuels')
        revenus_garant = cleaned_data.get('garant_revenus_mensuels')
        
        if revenus_locataire and revenus_garant:
            if revenus_garant < revenus_locataire * 3:
                raise ValidationError(
                    "Les revenus du garant doivent être d'au moins 3 fois ceux du locataire pour une garantie solide."
                )
        
        # Vérifier les doublons d'informations de contact
        from core.duplicate_prevention import validate_unique_contact_info
        try:
            validate_unique_contact_info(
                self._meta.model, 
                self.instance, 
                ['email', 'telephone', 'telephone_mobile']
            )
        except ValidationError as e:
            # Ajouter l'erreur aux champs concernés
            if 'email' in str(e):
                self.add_error('email', e)
            if 'telephone' in str(e):
                self.add_error('telephone', e)
            if 'telephone_mobile' in str(e):
                self.add_error('telephone_mobile', e)
        
        return cleaned_data


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
    """Formulaire de recherche avancée pour les documents."""
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Rechercher un document...',
            'autocomplete': 'off'
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
        queryset=Propriete.objects.none(),  # Sera rempli dans __init__
        required=False,
        empty_label="Toutes les propriétés",
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    bailleur = forms.ModelChoiceField(
        queryset=Bailleur.objects.none(),  # Sera rempli dans __init__
        required=False,
        empty_label="Tous les bailleurs",
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    locataire = forms.ModelChoiceField(
        queryset=Locataire.objects.none(),  # Sera rempli dans __init__
        required=False,
        empty_label="Tous les locataires",
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    confidentiel = forms.ChoiceField(
        choices=[
            ('', 'Tous les documents'),
            ('true', 'Documents confidentiels seulement'),
            ('false', 'Documents publics seulement')
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    taille_min = forms.IntegerField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Taille min (KB)',
            'min': '0'
        })
    )
    
    taille_max = forms.IntegerField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Taille max (KB)',
            'min': '0'
        })
    )
    
    tags = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Tags séparés par des virgules...'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Utiliser la logique de filtrage des propriétés disponibles
        from core.property_utils import get_proprietes_disponibles_global
        self.fields['propriete'].queryset = get_proprietes_disponibles_global()
        self.fields['bailleur'].queryset = Bailleur.objects.filter(is_deleted=False).order_by('nom', 'prenom')
        self.fields['locataire'].queryset = Locataire.objects.filter(is_deleted=False).order_by('nom', 'prenom')
    
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
    
    date_expiration_debut = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    date_expiration_fin = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    def clean(self):
        cleaned_data = super().clean()
        taille_min = cleaned_data.get('taille_min')
        taille_max = cleaned_data.get('taille_max')
        date_debut = cleaned_data.get('date_debut')
        date_fin = cleaned_data.get('date_fin')
        date_expiration_debut = cleaned_data.get('date_expiration_debut')
        date_expiration_fin = cleaned_data.get('date_expiration_fin')
        
        # Validation de la taille
        if taille_min and taille_max and taille_min > taille_max:
            raise forms.ValidationError("La taille minimale ne peut pas être supérieure à la taille maximale.")
        
        # Validation des dates
        if date_debut and date_fin and date_debut > date_fin:
            raise forms.ValidationError("La date de début ne peut pas être postérieure à la date de fin.")
        
        if date_expiration_debut and date_expiration_fin and date_expiration_debut > date_expiration_fin:
            raise forms.ValidationError("La date d'expiration de début ne peut pas être postérieure à la date d'expiration de fin.")
        
        return cleaned_data


class UniteRechercheForm(forms.Form):
    """Formulaire de recherche avancée pour les unités locatives."""
    
    search = forms.CharField(
        required=False,
        label="Recherche générale",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Numéro d\'unité, nom, propriété...',
            'id': 'search-input'
        }),
        help_text="Recherchez par numéro d'unité, nom, propriété ou description"
    )
    
    propriete = forms.ModelChoiceField(
        queryset=Propriete.objects.none(),  # Sera rempli dans __init__
        required=False,
        empty_label="Toutes les propriétés",
        label="Propriété",
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'propriete-select'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Utiliser la logique de filtrage des propriétés disponibles
        from core.property_utils import get_proprietes_disponibles_global
        self.fields['propriete'].queryset = get_proprietes_disponibles_global()
    
    bailleur = forms.ModelChoiceField(
        queryset=Bailleur.objects.filter(is_deleted=False),
        required=False,
        empty_label="Tous les bailleurs",
        label="Bailleur",
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'bailleur-select'
        })
    )
    
    statut = forms.ChoiceField(
        choices=[('', 'Tous les statuts')] + UniteLocative.STATUT_CHOICES,
        required=False,
        label="Statut",
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'statut-select'
        })
    )
    
    type_unite = forms.ChoiceField(
        choices=[('', 'Tous les types')] + UniteLocative.TYPE_UNITE_CHOICES,
        required=False,
        label="Type d'unité",
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'type-unite-select'
        })
    )
    
    etage_min = forms.IntegerField(
        required=False,
        label="Étage minimum",
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ex: 0'
        })
    )
    
    etage_max = forms.IntegerField(
        required=False,
        label="Étage maximum",
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ex: 5'
        })
    )
    
    loyer_min = forms.DecimalField(
        required=False,
        label="Loyer minimum (€)",
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0',
            'step': '0.01'
        })
    )
    
    loyer_max = forms.DecimalField(
        required=False,
        label="Loyer maximum (€)",
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '5000',
            'step': '0.01'
        })
    )
    
    surface_min = forms.DecimalField(
        required=False,
        label="Surface minimum (m²)",
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0',
            'step': '0.01'
        })
    )
    
    surface_max = forms.DecimalField(
        required=False,
        label="Surface maximum (m²)",
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '200',
            'step': '0.01'
        })
    )
    
    nombre_pieces_min = forms.IntegerField(
        required=False,
        label="Nombre de pièces min",
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '1'
        })
    )
    
    nombre_pieces_max = forms.IntegerField(
        required=False,
        label="Nombre de pièces max",
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '10'
        })
    )
    
    # Équipements
    meuble = forms.ChoiceField(
        choices=[('', 'Peu importe'), ('true', 'Meublé'), ('false', 'Non meublé')],
        required=False,
        label="Meublé",
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    balcon = forms.ChoiceField(
        choices=[('', 'Peu importe'), ('true', 'Avec balcon'), ('false', 'Sans balcon')],
        required=False,
        label="Balcon/Terrasse",
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    parking_inclus = forms.ChoiceField(
        choices=[('', 'Peu importe'), ('true', 'Parking inclus'), ('false', 'Sans parking')],
        required=False,
        label="Parking",
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    climatisation = forms.ChoiceField(
        choices=[('', 'Peu importe'), ('true', 'Climatisé'), ('false', 'Non climatisé')],
        required=False,
        label="Climatisation",
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    date_disponibilite_debut = forms.DateField(
        required=False,
        label="Disponible à partir du",
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    date_disponibilite_fin = forms.DateField(
        required=False,
        label="Disponible jusqu'au",
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    # Options d'affichage
    tri = forms.ChoiceField(
        choices=[
            ('numero_unite', 'Numéro d\'unité'),
            ('loyer_mensuel', 'Loyer croissant'),
            ('-loyer_mensuel', 'Loyer décroissant'),
            ('surface', 'Surface croissante'),
            ('-surface', 'Surface décroissante'),
            ('propriete__titre', 'Propriété'),
            ('etage', 'Étage'),
            ('date_creation', 'Date de création'),
        ],
        initial='numero_unite',
        label="Trier par",
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Optimisation des requêtes
        self.fields['propriete'].queryset = Propriete.objects.filter(
            is_deleted=False
        ).select_related('bailleur').order_by('titre')
        
        self.fields['bailleur'].queryset = Bailleur.objects.filter(
            is_deleted=False
        ).order_by('nom', 'prenom')


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


class PieceForm(forms.ModelForm):
    """Formulaire pour la création et modification de pièces."""
    
    class Meta:
        model = Piece
        fields = ['nom', 'type_piece', 'numero_piece', 'surface', 'description', 'statut', 'est_espace_partage']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'type_piece': forms.Select(attrs={'class': 'form-select'}),
            'numero_piece': forms.TextInput(attrs={'class': 'form-control'}),
            'surface': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'statut': forms.Select(attrs={'class': 'form-select'}),
            'est_espace_partage': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, propriete=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.propriete = propriete
        
        # Rendre le champ surface optionnel
        self.fields['surface'].required = False
        self.fields['numero_piece'].required = False
        self.fields['description'].required = False
        
        # Ajouter des labels personnalisés
        self.fields['nom'].label = _('Nom de la pièce')
        self.fields['type_piece'].label = _('Type de pièce')
        self.fields['numero_piece'].label = _('Numéro de pièce')
        self.fields['surface'].label = _('Surface (m²)')
        self.fields['description'].label = _('Description')
        self.fields['statut'].label = _('Statut')
        self.fields['est_espace_partage'].label = _('Espace partagé')
    
    def clean(self):
        cleaned_data = super().clean()
        nom = cleaned_data.get('nom')
        numero_piece = cleaned_data.get('numero_piece')
        
        if self.propriete and nom:
            # Vérifier l'unicité du nom dans la propriété
            queryset = Piece.objects.filter(propriete=self.propriete, nom=nom, is_deleted=False)
            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            
            if queryset.exists():
                raise ValidationError(_('Une pièce avec ce nom existe déjà dans cette propriété.'))
        
        if self.propriete and numero_piece:
            # Vérifier l'unicité du numéro de pièce dans la propriété
            queryset = Piece.objects.filter(propriete=self.propriete, numero_piece=numero_piece, is_deleted=False)
            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            
            if queryset.exists():
                raise ValidationError(_('Une pièce avec ce numéro existe déjà dans cette propriété.'))
        
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


# Import des formulaires pour les unités locatives
# from .forms_unites import UniteLocativeForm, ReservationUniteForm, UniteLocativeSearchForm

# Formulaires simples pour les unités locatives
class UniteLocativeForm(forms.ModelForm):
    class Meta:
        model = UniteLocative
        fields = [
            'propriete', 'bailleur', 'numero_unite', 'nom', 'type_unite',
            'etage', 'surface', 'nombre_pieces', 'nombre_chambres', 'nombre_salles_bain',
            'meuble', 'balcon', 'parking_inclus', 'climatisation', 'internet_inclus',
            'loyer_mensuel', 'charges_mensuelles', 'caution_demandee', 'date_disponibilite',
            'description', 'notes_privees'
        ]
        widgets = {
            'propriete': forms.Select(attrs={'class': 'form-control'}),
            'bailleur': forms.Select(attrs={'class': 'form-control'}),
            'numero_unite': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: A1, T2-1, Studio-3'}),
            'nom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom descriptif de l\'unité'}),
            'type_unite': forms.Select(attrs={'class': 'form-control'}),
            'etage': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 2'}),
            'surface': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 45.5', 'step': '0.01'}),
            'nombre_pieces': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 3', 'min': '0'}),
            'nombre_chambres': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 2', 'min': '0'}),
            'nombre_salles_bain': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 1', 'min': '0'}),
            'meuble': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'balcon': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'parking_inclus': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'climatisation': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'internet_inclus': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'loyer_mensuel': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 150000', 'min': '0', 'step': '1000'}),
            'charges_mensuelles': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 15000 (optionnel)', 'min': '0', 'step': '1000'}),
            'caution_demandee': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 300000', 'min': '0', 'step': '1000'}),
            'date_disponibilite': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Décrivez l\'unité, ses caractéristiques particulières...'}),
            'notes_privees': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Notes internes, observations, remarques...'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Rendre les champs optionnels
        self.fields['charges_mensuelles'].required = False
        self.fields['caution_demandee'].required = False
        self.fields['date_disponibilite'].required = False
        self.fields['description'].required = False
        self.fields['notes_privees'].required = False
        self.fields['surface'].required = False
        self.fields['etage'].required = False
        self.fields['nombre_pieces'].required = False
        self.fields['nombre_chambres'].required = False
        self.fields['nombre_salles_bain'].required = False
        self.fields['bailleur'].required = False
        
        # Ajouter les choix manquants pour type_unite
        self.fields['type_unite'].choices = [
            ('', 'Sélectionnez un type'),
            ('appartement', 'Appartement'),
            ('studio', 'Studio'),
            ('bureau', 'Bureau'),
            ('local_commercial', 'Local commercial'),
            ('chambre', 'Chambre meublée'),
            ('parking', 'Place de parking'),
            ('cave', 'Cave/Débarras'),
            ('autre', 'Autre'),
        ]
    
    def clean(self):
        cleaned_data = super().clean()
        
        # S'assurer que les champs numériques ont des valeurs par défaut
        if not cleaned_data.get('nombre_pieces'):
            cleaned_data['nombre_pieces'] = 1
        if not cleaned_data.get('nombre_chambres'):
            cleaned_data['nombre_chambres'] = 0
        if not cleaned_data.get('nombre_salles_bain'):
            cleaned_data['nombre_salles_bain'] = 0
        if not cleaned_data.get('charges_mensuelles'):
            cleaned_data['charges_mensuelles'] = 0
        if not cleaned_data.get('caution_demandee'):
            cleaned_data['caution_demandee'] = 0
            
        return cleaned_data

class ReservationUniteForm(forms.ModelForm):
    class Meta:
        model = ReservationUnite
        fields = ['unite_locative', 'locataire_potentiel', 'date_debut_souhaitee', 'date_fin_prevue', 'date_expiration', 'montant_reservation', 'statut', 'notes']
        widgets = {
            'date_debut_souhaitee': forms.DateInput(attrs={'type': 'date'}),
            'date_fin_prevue': forms.DateInput(attrs={'type': 'date'}),
            'date_expiration': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

class UniteRechercheForm(forms.Form):
    nom = forms.CharField(max_length=100, required=False)
    type_unite = forms.ChoiceField(choices=[('', 'Tous')] + UniteLocative.TYPE_UNITE_CHOICES, required=False)
    loyer_mensuel_min = forms.DecimalField(max_digits=10, decimal_places=2, required=False)
    loyer_mensuel_max = forms.DecimalField(max_digits=10, decimal_places=2, required=False)