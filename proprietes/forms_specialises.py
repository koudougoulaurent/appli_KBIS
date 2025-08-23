from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .models import Propriete, Bailleur, Locataire, Document


class DiagnosticForm(forms.Form):
    """Formulaire spécialisé pour la gestion des diagnostics immobiliers avec gestion documentaire intégrée."""
    
    # Champs pour les diagnostics obligatoires
    diagnostic_energetique = forms.FileField(
        required=True,
        label=_('Diagnostic de Performance Énergétique (DPE)'),
        help_text=_('DPE obligatoire pour toute location (PDF, JPG, PNG)'),
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,.jpg,.jpeg,.png'
        })
    )
    
    diagnostic_plomb = forms.FileField(
        required=False,
        label=_('Diagnostic plomb'),
        help_text=_('Diagnostic plomb si construit avant 1949 (PDF, JPG, PNG)'),
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,.jpg,.jpeg,.png'
        })
    )
    
    diagnostic_amiante = forms.FileField(
        required=False,
        label=_('Diagnostic amiante'),
        help_text=_('Diagnostic amiante si construit avant 1997 (PDF, JPG, PNG)'),
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,.jpg,.jpeg,.png'
        })
    )
    
    diagnostic_electrique = forms.FileField(
        required=False,
        label=_('Diagnostic électrique'),
        help_text=_('Diagnostic électrique si installation > 15 ans (PDF, JPG, PNG)'),
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,.jpg,.jpeg,.png'
        })
    )
    
    diagnostic_gaz = forms.FileField(
        required=False,
        label=_('Diagnostic gaz'),
        help_text=_('Diagnostic gaz si installation > 15 ans (PDF, JPG, PNG)'),
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,.jpg,.jpeg,.png'
        })
    )
    
    # Champ pour la propriété concernée
    propriete = forms.ModelChoiceField(
        queryset=Propriete.objects.all(),
        required=True,
        label=_('Propriété concernée'),
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    # Champ pour les notes
    notes = forms.CharField(
        required=False,
        label=_('Notes sur les diagnostics'),
        help_text=_('Commentaires sur l\'état des diagnostics'),
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Notes sur les diagnostics...'
        })
    )
    
    def save_diagnostics(self, user):
        """Sauvegarde les diagnostics et crée automatiquement les documents associés."""
        propriete = self.cleaned_data.get('propriete')
        
        if propriete and user:
            self._create_documents_for_diagnostics(propriete, user)
        
        return propriete
    
    def _create_documents_for_diagnostics(self, propriete, user):
        """Crée automatiquement les documents pour les diagnostics."""
        # Mapping des champs de fichiers vers les types de documents
        document_mapping = {
            'diagnostic_energetique': ('diagnostic', 'Diagnostic de Performance Énergétique (DPE)'),
            'diagnostic_plomb': ('diagnostic', 'Diagnostic plomb'),
            'diagnostic_amiante': ('diagnostic', 'Diagnostic amiante'),
            'diagnostic_electrique': ('diagnostic', 'Diagnostic électrique'),
            'diagnostic_gaz': ('diagnostic', 'Diagnostic gaz'),
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
                    confidentiel=False  # Les diagnostics ne sont pas confidentiels
                )


class AssuranceForm(forms.Form):
    """Formulaire spécialisé pour la gestion des assurances avec gestion documentaire intégrée."""
    
    # Champs pour les documents d'assurance
    attestation_assurance_habitation = forms.FileField(
        required=True,
        label=_('Attestation d\'assurance habitation'),
        help_text=_('Attestation d\'assurance habitation du locataire (PDF, JPG, PNG)'),
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,.jpg,.jpeg,.png'
        })
    )
    
    attestation_assurance_proprietaire = forms.FileField(
        required=False,
        label=_('Attestation d\'assurance propriétaire'),
        help_text=_('Attestation d\'assurance propriétaire (PDF, JPG, PNG)'),
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,.jpg,.jpeg,.png'
        })
    )
    
    attestation_assurance_loyer_impayes = forms.FileField(
        required=False,
        label=_('Assurance loyer impayés'),
        help_text=_('Attestation d\'assurance loyer impayés (PDF, JPG, PNG)'),
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,.jpg,.jpeg,.png'
        })
    )
    
    # Champ pour la propriété concernée
    propriete = forms.ModelChoiceField(
        queryset=Propriete.objects.all(),
        required=True,
        label=_('Propriété concernée'),
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    # Champ pour le locataire concerné
    locataire = forms.ModelChoiceField(
        queryset=Locataire.objects.all(),
        required=False,
        label=_('Locataire concerné'),
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    # Champ pour les notes
    notes = forms.CharField(
        required=False,
        label=_('Notes sur les assurances'),
        help_text=_('Commentaires sur les assurances'),
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Notes sur les assurances...'
        })
    )
    
    def save_assurances(self, user):
        """Sauvegarde les assurances et crée automatiquement les documents associés."""
        propriete = self.cleaned_data.get('propriete')
        locataire = self.cleaned_data.get('locataire')
        
        if propriete and user:
            self._create_documents_for_assurances(propriete, locataire, user)
        
        return propriete
    
    def _create_documents_for_assurances(self, propriete, locataire, user):
        """Crée automatiquement les documents pour les assurances."""
        # Mapping des champs de fichiers vers les types de documents
        document_mapping = {
            'attestation_assurance_habitation': ('assurance', 'Attestation d\'assurance habitation'),
            'attestation_assurance_proprietaire': ('assurance', 'Attestation d\'assurance propriétaire'),
            'attestation_assurance_loyer_impayes': ('assurance', 'Assurance loyer impayés'),
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
                    locataire=locataire,
                    statut='valide',
                    cree_par=user,
                    confidentiel=False  # Les assurances ne sont pas confidentielles
                )


class EtatLieuxForm(forms.Form):
    """Formulaire spécialisé pour la gestion des états des lieux avec gestion documentaire intégrée."""
    
    # Champs pour les états des lieux
    etat_lieux_entree = forms.FileField(
        required=True,
        label=_('État des lieux d\'entrée'),
        help_text=_('État des lieux d\'entrée signé (PDF, JPG, PNG)'),
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,.jpg,.jpeg,.png'
        })
    )
    
    etat_lieux_sortie = forms.FileField(
        required=False,
        label=_('État des lieux de sortie'),
        help_text=_('État des lieux de sortie signé (PDF, JPG, PNG)'),
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,.jpg,.jpeg,.png'
        })
    )
    
    photos_etat_lieux = forms.FileField(
        required=False,
        label=_('Photos de l\'état des lieux'),
        help_text=_('Photos de l\'état des lieux (JPG, PNG)'),
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.jpg,.jpeg,.png'
        })
    )
    
    # Champ pour la propriété concernée
    propriete = forms.ModelChoiceField(
        queryset=Propriete.objects.all(),
        required=True,
        label=_('Propriété concernée'),
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    # Champ pour le locataire concerné
    locataire = forms.ModelChoiceField(
        queryset=Locataire.objects.all(),
        required=True,
        label=_('Locataire concerné'),
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    # Champ pour la date de l'état des lieux
    date_etat_lieux = forms.DateField(
        required=True,
        label=_('Date de l\'état des lieux'),
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    # Champ pour les notes
    notes = forms.CharField(
        required=False,
        label=_('Notes sur l\'état des lieux'),
        help_text=_('Commentaires sur l\'état des lieux'),
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Notes sur l\'état des lieux...'
        })
    )
    
    def save_etat_lieux(self, user):
        """Sauvegarde les états des lieux et crée automatiquement les documents associés."""
        propriete = self.cleaned_data.get('propriete')
        locataire = self.cleaned_data.get('locataire')
        
        if propriete and locataire and user:
            self._create_documents_for_etat_lieux(propriete, locataire, user)
        
        return propriete
    
    def _create_documents_for_etat_lieux(self, propriete, locataire, user):
        """Crée automatiquement les documents pour les états des lieux."""
        # Mapping des champs de fichiers vers les types de documents
        document_mapping = {
            'etat_lieux_entree': ('etat_lieux', 'État des lieux d\'entrée'),
            'etat_lieux_sortie': ('etat_lieux', 'État des lieux de sortie'),
        }
        
        for field_name, (doc_type, description) in document_mapping.items():
            file_field = self.cleaned_data.get(field_name)
            if file_field:
                Document.objects.create(
                    nom=f"{description} - {propriete.titre} - {locataire.nom}",
                    type_document=doc_type,
                    description=f"{description} pour {propriete.numero_propriete} - {locataire.nom}",
                    fichier=file_field,
                    propriete=propriete,
                    locataire=locataire,
                    statut='valide',
                    cree_par=user,
                    confidentiel=False  # Les états des lieux ne sont pas confidentiels
                )
        
        # Gestion spéciale pour les photos multiples
        photos_field = self.cleaned_data.get('photos_etat_lieux')
        if photos_field:
            # Si c'est un fichier multiple, créer un document pour chaque photo
            if hasattr(photos_field, '__iter__'):
                for i, photo in enumerate(photos_field):
                    Document.objects.create(
                        nom=f"Photo état des lieux {i+1} - {propriete.titre} - {locataire.nom}",
                        type_document='autre',
                        description=f"Photo de l'état des lieux pour {propriete.numero_propriete} - {locataire.nom}",
                        fichier=photo,
                        propriete=propriete,
                        locataire=locataire,
                        statut='valide',
                        cree_par=user,
                        confidentiel=False
                    )
            else:
                # Si c'est un seul fichier
                Document.objects.create(
                    nom=f"Photo état des lieux - {propriete.titre} - {locataire.nom}",
                    type_document='autre',
                    description=f"Photo de l'état des lieux pour {propriete.numero_propriete} - {locataire.nom}",
                    fichier=photos_field,
                    propriete=propriete,
                    locataire=locataire,
                    statut='valide',
                    cree_par=user,
                    confidentiel=False
                )
