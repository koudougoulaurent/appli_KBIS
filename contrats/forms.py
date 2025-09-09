from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.db import models
from .models import Contrat, DocumentContrat, ResiliationContrat
from proprietes.models import Propriete, Bailleur, Locataire, UniteLocative, Piece
from datetime import date
from django_select2.forms import ModelSelect2Widget

class ContratForm(forms.ModelForm):
    """Formulaire pour créer/modifier un contrat de bail"""
    
    # Champ pour télécharger le PDF généré (optionnel)
    telecharger_pdf = forms.BooleanField(
        required=False,
        initial=True,
        label=_('Générer le contrat en PDF'),
        help_text=_('Cochez cette case pour générer automatiquement le contrat en PDF après sauvegarde'),
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    # Champs pour la création directe de paiement de caution/avance
    creer_paiement_caution = forms.BooleanField(
        required=False,
        initial=False,
        label=_('Créer un paiement de caution'),
        help_text=_('Cochez cette case pour créer automatiquement un paiement de caution lors de la création du contrat'),
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    creer_paiement_avance = forms.BooleanField(
        required=False,
        initial=False,
        label=_('Créer un paiement d\'avance de loyer'),
        help_text=_('Cochez cette case pour créer automatiquement un paiement d\'avance de loyer lors de la création du contrat'),
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    # Champs pour les informations de paiement
    mode_paiement_caution = forms.ChoiceField(
        required=False,
        choices=[
            ('', '---------'),
            ('virement', 'Virement bancaire'),
            ('cheque', 'Chèque'),
            ('especes', 'Espèces'),
            ('prelevement', 'Prélèvement automatique'),
            ('carte', 'Carte bancaire'),
        ],
        label=_('Mode de paiement de la caution'),
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    mode_paiement_avance = forms.ChoiceField(
        required=False,
        choices=[
            ('', '---------'),
            ('virement', 'Virement bancaire'),
            ('cheque', 'Chèque'),
            ('especes', 'Espèces'),
            ('prelevement', 'Prélèvement automatique'),
            ('carte', 'Carte bancaire'),
        ],
        label=_('Mode de paiement de l\'avance'),
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    # Champ pour sélectionner une unité locative spécifique
    unite_locative = forms.ModelChoiceField(
        queryset=UniteLocative.objects.all(),
        required=False,
        label=_("Unité locative"),
        help_text=_("Sélectionnez une unité locative spécifique si vous louez une partie de la propriété"),
        widget=ModelSelect2Widget(
            model=UniteLocative,
            search_fields=['numero__icontains', 'nom__icontains'],
            attrs={'data-placeholder': 'Rechercher une unité locative', 'class': 'form-select'},
            dependent_fields={}
        )
    )
    
    # Champ pour sélectionner une pièce spécifique
    piece = forms.ModelChoiceField(
        queryset=Piece.objects.all(),
        required=False,
        label=_("Pièce"),
        help_text=_("Sélectionnez une pièce spécifique si vous louez une pièce individuelle"),
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    class Meta:
        model = Contrat
        fields = [
            'numero_contrat', 'propriete', 'locataire', 'unite_locative',
            'date_debut', 'date_fin', 'date_signature', 'loyer_mensuel',
            'charges_mensuelles', 'depot_garantie', 'avance_loyer',
            'jour_paiement', 'mode_paiement', 'notes',
            'creer_paiement_caution', 'creer_paiement_avance',
            'date_paiement_caution', 'date_paiement_avance'
        ]
        widgets = {
            'numero_contrat': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Numéro du contrat'
            }),
            'propriete': forms.Select(attrs={
                'class': 'form-select'
            }),
            'locataire': forms.Select(attrs={
                'class': 'form-select'
            }),
            'date_debut': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'date_fin': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'date_signature': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'loyer_mensuel': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Loyer mensuel'
            }),
            'charges_mensuelles': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Charges mensuelles'
            }),
            'depot_garantie': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Dépôt de garantie'
            }),
            'avance_loyer': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Avance de loyer'
            }),
            'jour_paiement': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '31'
            }),
            'mode_paiement': forms.Select(attrs={
                'class': 'form-select'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Notes additionnelles...'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filtrer les propriétés disponibles
        # Une propriété est disponible si :
        # 1. Elle-même est marquée comme disponible, OU
        # 2. Elle a au moins une unité locative disponible
        
        # Filtrer les locataires actifs
        # Afficher toutes les propriétés et tous les locataires sans filtrage
        self.fields['propriete'].queryset = Propriete.objects.all()
        self.fields['locataire'].queryset = Locataire.objects.all()
        
        # Filtrer les unités locatives disponibles ou non réservées
        if self.instance.pk and self.instance.propriete:
            # Pour un contrat existant, filtrer par la propriété du contrat
            self.fields['unite_locative'].queryset = UniteLocative.objects.filter(
                propriete=self.instance.propriete,
                statut__in=['disponible', 'reservee']
            )
        elif 'propriete' in self.data:
            # Pour un nouveau contrat, filtrer par la propriété sélectionnée dans les données POST
            try:
                propriete_id = int(self.data.get('propriete'))
                self.fields['unite_locative'].queryset = UniteLocative.objects.filter(
                    propriete_id=propriete_id,
                    statut__in=['disponible', 'reservee']
                )
            except (ValueError, TypeError):
                self.fields['unite_locative'].queryset = UniteLocative.objects.none()
        elif self.initial.get('propriete'):
            # Pour un nouveau contrat, filtrer par la propriété initiale si elle est définie
            try:
                propriete_id = self.initial['propriete'].id if hasattr(self.initial['propriete'], 'id') else int(self.initial['propriete'])
                self.fields['unite_locative'].queryset = UniteLocative.objects.filter(
                    propriete_id=propriete_id,
                    statut__in=['disponible', 'reservee']
                )
            except (ValueError, TypeError):
                self.fields['unite_locative'].queryset = UniteLocative.objects.none()
        else:
            self.fields['unite_locative'].queryset = UniteLocative.objects.none()
            
        # Filtrer les pièces disponibles ou non réservées
        if self.instance.pk and self.instance.propriete:
            # Pour un contrat existant, filtrer par la propriété du contrat
            self.fields['piece'].queryset = Piece.objects.filter(
                propriete=self.instance.propriete,
                statut__in=['disponible', 'reservee']
            )
        elif 'propriete' in self.data:
            # Pour un nouveau contrat, filtrer par la propriété sélectionnée dans les données POST
            try:
                propriete_id = int(self.data.get('propriete'))
                self.fields['piece'].queryset = Piece.objects.filter(
                    propriete_id=propriete_id,
                    statut__in=['disponible', 'reservee']
                )
            except (ValueError, TypeError):
                self.fields['piece'].queryset = Piece.objects.none()
        elif self.initial.get('propriete'):
            # Pour un nouveau contrat, filtrer par la propriété initiale si elle est définie
            try:
                propriete_id = self.initial['propriete'].id if hasattr(self.initial['propriete'], 'id') else int(self.initial['propriete'])
                self.fields['piece'].queryset = Piece.objects.filter(
                    propriete_id=propriete_id,
                    statut__in=['disponible', 'reservee']
                )
            except (ValueError, TypeError):
                self.fields['piece'].queryset = Piece.objects.none()
        else:
            self.fields['piece'].queryset = Piece.objects.none()
        
        # Rendre les champs optionnels
        self.fields['charges_mensuelles'].required = False
        self.fields['depot_garantie'].required = False
        self.fields['jour_paiement'].required = False
        
        # Ajouter des classes CSS pour le style
        self.fields['loyer_mensuel'].widget.attrs.update({
            'class': 'form-control bg-light',
            'title': 'Ce champ sera automatiquement rempli à partir de la propriété sélectionnée',
            'placeholder': 'Sélectionnez une propriété pour remplir automatiquement'
        })
        
        # Ajouter les données des propriétés pour le JavaScript
        self.proprietes_data = {}
        proprietes_queryset = Propriete.objects.filter(
            models.Q(disponible=True) |
            models.Q(unites_locatives__statut='disponible', unites_locatives__is_deleted=False)
        ).distinct()
        
        print(f"DEBUG: {proprietes_queryset.count()} propriétés trouvées pour le formulaire")
        
        for propriete in proprietes_queryset:
            print(f"DEBUG: Traitement de la propriété {propriete.id} - {propriete.titre} (loyer: {propriete.loyer_actuel})")
            
            # Récupérer toutes les unités locatives pour cette propriété
            unites = UniteLocative.objects.filter(
                propriete=propriete
            )
            unites_data = [
                {
                    'id': unite.id,
                    'nom': unite.nom,
                    'loyer_mensuel': str(unite.loyer_mensuel) if unite.loyer_mensuel else "0.00",
                    'statut': unite.statut
                }
                for unite in unites
            ]
            
            # Récupérer toutes les pièces pour cette propriété
            pieces = Piece.objects.filter(
                propriete=propriete
            )
            pieces_data = [
                {
                    'id': piece.id,
                    'nom': piece.nom,
                    'loyer_mensuel': "0.00",  # Les pièces n'ont pas de loyer mensuel direct, cela dépend des contrats
                    'statut': piece.statut
                }
                for piece in pieces
            ]
            
            self.proprietes_data[propriete.id] = {
                'loyer': str(propriete.loyer_actuel) if propriete.loyer_actuel else "0.00",
                'titre': propriete.titre,
                'unites': unites_data,
                'pieces': pieces_data
            }
            
            print(f"DEBUG: Données ajoutées pour propriété {propriete.id}: loyer={self.proprietes_data[propriete.id]['loyer']}, unites={len(unites_data)}")
        
        print(f"DEBUG: Données finales des propriétés: {self.proprietes_data}")
        
        # Suppression de la personnalisation des anciens champs de caution/avance
    
    def clean(self):
        cleaned_data = super().clean()
        date_debut = cleaned_data.get('date_debut')
        date_fin = cleaned_data.get('date_fin')
        propriete = cleaned_data.get('propriete')
        locataire = cleaned_data.get('locataire')
        
        # Vérifier que la date de fin est après la date de début
        if date_debut and date_fin and date_fin <= date_debut:
            raise ValidationError("La date de fin doit être postérieure à la date de début.")
        
        # Vérifier que la date de début n'est pas dans le passé
        if date_debut and date_debut < timezone.now().date():
            raise ValidationError("La date de début ne peut pas être dans le passé.")
        
        # Vérifier que la propriété n'a pas déjà un contrat actif avec ce locataire
        if propriete and locataire:
            contrats_existants = Contrat.objects.filter(
                propriete=propriete,
                locataire=locataire,
                est_actif=True
            )
            if self.instance.pk:
                contrats_existants = contrats_existants.exclude(pk=self.instance.pk)
            
            if contrats_existants.exists():
                raise ValidationError(
                    f"Un contrat actif existe déjà entre {propriete.titre} et {locataire.nom}."
                )
        
        # Vérifier que la propriété est disponible (pour les nouveaux contrats)
        if propriete and not self.instance.pk:
            if not propriete.disponible:
                raise ValidationError(
                    f"La propriété {propriete.titre} n'est pas disponible pour la location. "
                    f"Elle a déjà un contrat actif."
                )
            
            # Vérification supplémentaire : s'assurer qu'il n'y a pas de contrats actifs
            contrats_actifs_propriete = Contrat.objects.filter(
                propriete=propriete,
                est_actif=True,
                est_resilie=False
            )
            
            if contrats_actifs_propriete.exists():
                raise ValidationError(
                    f"La propriété {propriete.titre} a déjà un contrat actif. "
                    f"Impossible de créer un nouveau contrat."
                )
        
        # Vérifier les chevauchements de dates pour la même propriété
        if propriete and date_debut and date_fin:
            contrats_chevauchants = Contrat.objects.filter(
                propriete=propriete,
                est_actif=True,
                est_resilie=False
            )
            
            if self.instance.pk:
                contrats_chevauchants = contrats_chevauchants.exclude(pk=self.instance.pk)
            
            for contrat_existant in contrats_chevauchants:
                # Vérifier s'il y a un chevauchement de dates
                if (date_debut < contrat_existant.date_fin and 
                    date_fin > contrat_existant.date_debut):
                    raise ValidationError(
                        f"Les dates du contrat chevauchent celles du contrat existant "
                        f"{contrat_existant.numero_contrat} "
                        f"({contrat_existant.date_debut} - {contrat_existant.date_fin})."
                    )
        
        # Remplir automatiquement le loyer à partir de la propriété sélectionnée
        if propriete and not cleaned_data.get('loyer_mensuel'):
            try:
                cleaned_data['loyer_mensuel'] = str(propriete.loyer_actuel)
            except AttributeError:
                pass
        
        # Validation de cohérence entre unité locative et pièces
        unite_locative = cleaned_data.get('unite_locative')
        if unite_locative:
            # Si une unité locative est sélectionnée, vérifier qu'aucune pièce n'est assignée
            if self.instance.pk:
                pieces_assignees = self.instance.pieces_contrat.filter(actif=True).exists()
                if pieces_assignees:
                    raise ValidationError(
                        "Ce contrat a déjà des pièces spécifiques assignées. "
                        "Impossible d'assigner une unité locative complète. "
                        "Veuillez d'abord supprimer les pièces assignées."
                    )
            
            # Vérifier que l'unité locative appartient à la propriété sélectionnée
            propriete = cleaned_data.get('propriete')
            if propriete and unite_locative.propriete != propriete:
                raise ValidationError(
                    "L'unité locative sélectionnée n'appartient pas à la propriété choisie."
                )
        
        return cleaned_data
    
    def save(self, commit=True, user=None):
        """Sauvegarde le contrat et crée automatiquement les documents associés."""
        contrat = super().save(commit=False)
        
        if commit:
            contrat.save()
            
            # Créer automatiquement les documents dans le système documentaire
            if user:
                self._create_documents_for_contrat(contrat, user)
        
        return contrat
    
    def get_errors_summary(self):
        """Retourne un résumé des erreurs de validation avec les noms des champs"""
        if not self.errors:
            return ""
        
        error_messages = []
        field_names = {
            'numero_contrat': 'Numéro de contrat',
            'propriete': 'Propriété',
            'locataire': 'Locataire',
            'date_debut': 'Date de début',
            'date_fin': 'Date de fin',
            'date_signature': 'Date de signature',
            'loyer_mensuel': 'Loyer mensuel',
            'charges_mensuelles': 'Charges mensuelles',
            'depot_garantie': 'Dépôt de garantie ou Caution',
            'avance_loyer': 'Avance de loyer',
            'jour_paiement': 'Jour de paiement',
            'mode_paiement': 'Mode de paiement',
            'notes': 'Notes'
        }
        
        for field, errors in self.errors.items():
            field_display_name = field_names.get(field, field)
            for error in errors:
                error_messages.append(f"• {field_display_name}: {error}")
        
        return "\n".join(error_messages)
    
    def _create_documents_for_contrat(self, contrat, user):
        """Crée automatiquement les documents pour un contrat."""
        from proprietes.models import Document
        
        # Mapping des champs de fichiers vers les types de documents
        document_mapping = {
            'contrat_bail_signe': ('contrat', 'Contrat de bail signé'),
            'etat_lieux_entree': ('etat_lieux', 'État des lieux d\'entrée'),
            'quittance_loyer': ('quittance', 'Quittance de loyer'),
            'attestation_assurance': ('assurance', 'Attestation d\'assurance habitation'),
            'reglement_interieur': ('courrier', 'Règlement intérieur'),
        }
        
        for field_name, (doc_type, description) in document_mapping.items():
            file_field = self.cleaned_data.get(field_name)
            if file_field:
                Document.objects.create(
                    nom=f"{description} - {contrat.propriete.titre} - {contrat.locataire.nom}",
                    type_document=doc_type,
                    description=f"{description} pour le contrat {contrat.numero_contrat}",
                    fichier=file_field,
                    propriete=contrat.propriete,
                    locataire=contrat.locataire,
                    statut='valide',
                    cree_par=user,
                    confidentiel=False  # Les documents de contrat ne sont pas confidentiels
                )



class DocumentContratForm(forms.ModelForm):
    """Formulaire pour ajouter un document au contrat"""
    
    class Meta:
        model = DocumentContrat
        fields = ['type_document', 'format_impression', 'version_template', 'notes_internes']
        widgets = {
            'type_document': forms.Select(attrs={
                'class': 'form-select'
            }),
            'format_impression': forms.Select(attrs={
                'class': 'form-select'
            }),
            'version_template': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Version du template'
            }),
            'notes_internes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Notes internes...'
            }),
        }

# Formulaire TypeContratForm supprimé car le modèle TypeContrat n'existe pas

class RechercheContratForm(forms.Form):
    """Formulaire de recherche pour les contrats"""
    recherche = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Rechercher par numéro, titre, propriété...'
        })
    )
    
    statut = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'Tous les statuts'),
            ('actif', 'Actif'),
            ('inactif', 'Inactif'),
            ('resilie', 'Résilié'),
            ('expire', 'Expiré')
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    propriete = forms.ModelChoiceField(
        required=False,
        queryset=Propriete.objects.all(),
        empty_label="Toutes les propriétés",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    bailleur = forms.ModelChoiceField(
        required=False,
        queryset=Bailleur.objects.all(),
        empty_label="Tous les bailleurs",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    tri = forms.ChoiceField(
        required=False,
        choices=[
            ('-date_creation', 'Plus récents'),
            ('date_creation', 'Plus anciens'),
            ('date_debut', 'Date de début'),
            ('date_fin', 'Date de fin'),
            ('loyer_mensuel', 'Loyer croissant'),
            ('-loyer_mensuel', 'Loyer décroissant'),
        ],
        initial='-date_creation',
        widget=forms.Select(attrs={'class': 'form-select'})
    )

class RenouvellementContratForm(forms.Form):
    """Formulaire pour renouveler un contrat"""
    date_debut = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    date_fin = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    loyer_mensuel = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0'
        })
    )
    
    charges_mensuelles = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        initial=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0'
        })
    )
    
    motif = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Motif du renouvellement...'
        })
    )
    
    def __init__(self, contrat_original=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if contrat_original:
            # Pré-remplir avec les données du contrat original
            self.fields['loyer_mensuel'].initial = contrat_original.loyer_mensuel
            self.fields['charges_mensuelles'].initial = contrat_original.charges_mensuelles
    
    def clean(self):
        cleaned_data = super().clean()
        date_debut = cleaned_data.get('date_debut')
        date_fin = cleaned_data.get('date_fin')
        
        if date_debut and date_fin and date_fin <= date_debut:
            raise ValidationError("La date de fin doit être postérieure à la date de début.")
        
        if date_debut and date_debut < timezone.now().date():
            raise ValidationError("La date de début ne peut pas être dans le passé.")
        
        return cleaned_data 

class ResiliationContratForm(forms.ModelForm):
    """Formulaire pour créer/modifier une résiliation de contrat."""
    
    # Ajout du champ contrat pour l'affichage (lecture seule)
    contrat = forms.ModelChoiceField(
        queryset=Contrat.objects.filter(est_actif=True),
        empty_label=None,
        widget=forms.Select(attrs={'class': 'form-select', 'disabled': 'disabled'}),
        required=False
    )
    
    class Meta:
        model = ResiliationContrat
        fields = [
            'date_resiliation',
            'motif_resiliation',
            'type_resiliation',
            'etat_lieux_sortie',
            'caution_remboursee',
            'montant_remboursement',
            'date_remboursement',
            'notes'
        ]
        
        widgets = {
            'date_resiliation': forms.DateInput(attrs={'type': 'date'}),
            'date_remboursement': forms.DateInput(attrs={'type': 'date'}),
            'motif_resiliation': forms.Textarea(attrs={'rows': 4}),
            'etat_lieux_sortie': forms.Textarea(attrs={'rows': 4}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Définir la date d'aujourd'hui par défaut
        if not self.instance.pk:
            self.fields['date_resiliation'].initial = timezone.now().date()
        
        # Personnaliser les widgets
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
    
    def clean(self):
        cleaned_data = super().clean()
        caution_remboursee = cleaned_data.get('caution_remboursee')
        montant_remboursement = cleaned_data.get('montant_remboursement')
        date_remboursement = cleaned_data.get('date_remboursement')
        
        if caution_remboursee and not montant_remboursement:
            raise forms.ValidationError(
                "Le montant de remboursement est requis si la caution est remboursée."
            )
        
        if caution_remboursee and not date_remboursement:
            raise forms.ValidationError(
                "La date de remboursement est requise si la caution est remboursée."
            )
        
        return cleaned_data 
