from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Document, Propriete, Locataire


class DiagnosticForm(forms.Form):
    """Formulaire pour la gestion des diagnostics immobiliers."""
    
    # Champs pour les diagnostics
    diagnostic_energetique = forms.FileField(
        label=_('Diagnostic de Performance Énergétique (DPE)'),
        help_text=_('Rapport DPE obligatoire (PDF, JPG, PNG)'),
        required=True
    )
    
    diagnostic_plomb = forms.FileField(
        label=_('Diagnostic Plomb (CREP)'),
        help_text=_('Rapport plomb si construction avant 1949'),
        required=False
    )
    
    diagnostic_amiante = forms.FileField(
        label=_('Diagnostic Amiante (DTA)'),
        help_text=_('Rapport amiante si construction avant 1997'),
        required=False
    )
    
    diagnostic_electrique = forms.FileField(
        label=_('Diagnostic Électrique'),
        help_text=_('Rapport électrique si installation > 15 ans'),
        required=False
    )
    
    diagnostic_gaz = forms.FileField(
        label=_('Diagnostic Gaz'),
        help_text=_('Rapport gaz si installation > 15 ans'),
        required=False
    )
    
    # Champs de liaison
    propriete = forms.ModelChoiceField(
        queryset=Propriete.objects.filter(disponible=True),
        label=_('Propriété concernée'),
        help_text=_('Sélectionnez la propriété pour laquelle ces diagnostics s\'appliquent'),
        required=True
    )
    
    notes = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4}),
        label=_('Notes et observations'),
        help_text=_('Observations particulières, dates de validité, recommandations'),
        required=False
    )
    
    def save_diagnostics(self, user):
        """Sauvegarde les diagnostics et crée les documents associés."""
        propriete = self.cleaned_data['propriete']
        notes = self.cleaned_data.get('notes', '')
        
        # Créer les documents pour chaque diagnostic fourni
        diagnostics_crees = []
        
        # DPE (obligatoire)
        if self.cleaned_data['diagnostic_energetique']:
            doc_dpe = Document.objects.create(
                nom=f"DPE - {propriete.titre}",
                type_document='diagnostic_energetique',
                description=f"Diagnostic de Performance Énergétique pour {propriete.titre}. {notes}",
                fichier=self.cleaned_data['diagnostic_energetique'],
                propriete=propriete,
                statut='valide',
                cree_par=user,
                tags='DPE,diagnostic,energie,obligatoire'
            )
            diagnostics_crees.append(doc_dpe)
        
        # Diagnostic Plomb
        if self.cleaned_data['diagnostic_plomb']:
            doc_plomb = Document.objects.create(
                nom=f"Diagnostic Plomb - {propriete.titre}",
                type_document='diagnostic_plomb',
                description=f"Diagnostic plomb (CREP) pour {propriete.titre}. {notes}",
                fichier=self.cleaned_data['diagnostic_plomb'],
                propriete=propriete,
                statut='valide',
                cree_par=user,
                tags='plomb,CREP,diagnostic,sante'
            )
            diagnostics_crees.append(doc_plomb)
        
        # Diagnostic Amiante
        if self.cleaned_data['diagnostic_amiante']:
            doc_amiante = Document.objects.create(
                nom=f"Diagnostic Amiante - {propriete.titre}",
                type_document='diagnostic_amiante',
                description=f"Diagnostic amiante (DTA) pour {propriete.titre}. {notes}",
                fichier=self.cleaned_data['diagnostic_amiante'],
                propriete=propriete,
                statut='valide',
                cree_par=user,
                tags='amiante,DTA,diagnostic,sante'
            )
            diagnostics_crees.append(doc_amiante)
        
        # Diagnostic Électrique
        if self.cleaned_data['diagnostic_electrique']:
            doc_electrique = Document.objects.create(
                nom=f"Diagnostic Électrique - {propriete.titre}",
                type_document='diagnostic_electrique',
                description=f"Diagnostic électrique pour {propriete.titre}. {notes}",
                fichier=self.cleaned_data['diagnostic_electrique'],
                propriete=propriete,
                statut='valide',
                cree_par=user,
                tags='electrique,diagnostic,securite'
            )
            diagnostics_crees.append(doc_electrique)
        
        # Diagnostic Gaz
        if self.cleaned_data['diagnostic_gaz']:
            doc_gaz = Document.objects.create(
                nom=f"Diagnostic Gaz - {propriete.titre}",
                type_document='diagnostic_gaz',
                description=f"Diagnostic gaz pour {propriete.titre}. {notes}",
                fichier=self.cleaned_data['diagnostic_gaz'],
                propriete=propriete,
                statut='valide',
                cree_par=user,
                tags='gaz,diagnostic,securite'
            )
            diagnostics_crees.append(doc_gaz)
        
        return diagnostics_crees


class AssuranceForm(forms.Form):
    """Formulaire pour la gestion des assurances immobilières."""
    
    # Champs pour les attestations d'assurance
    attestation_assurance_habitation = forms.FileField(
        label=_('Attestation d\'Assurance Habitation Locataire'),
        help_text=_('Attestation d\'assurance habitation du locataire (obligatoire)'),
        required=False
    )
    
    attestation_assurance_proprietaire = forms.FileField(
        label=_('Attestation d\'Assurance Propriétaire Non Occupant (PNO)'),
        help_text=_('Attestation d\'assurance PNO pour le bailleur'),
        required=False
    )
    
    attestation_assurance_loyer_impayes = forms.FileField(
        label=_('Attestation d\'Assurance Loyers Impayés (GLI)'),
        help_text=_('Attestation d\'assurance GLI pour protection contre impayés'),
        required=False
    )
    
    # Champs de liaison
    propriete = forms.ModelChoiceField(
        queryset=Propriete.objects.filter(disponible=True),
        label=_('Propriété concernée'),
        help_text=_('Sélectionnez la propriété concernée par ces assurances'),
        required=True
    )
    
    locataire = forms.ModelChoiceField(
        queryset=Locataire.objects.filter(statut='actif'),
        label=_('Locataire'),
        help_text=_('Optionnel - pour l\'assurance habitation du locataire'),
        required=False
    )
    
    notes = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4}),
        label=_('Notes et observations'),
        help_text=_('Numéros de police, dates d\'échéance, montants de franchise, etc.'),
        required=False
    )
    
    def save_assurances(self, user):
        """Sauvegarde les assurances et crée les documents associés."""
        propriete = self.cleaned_data['propriete']
        locataire = self.cleaned_data.get('locataire')
        notes = self.cleaned_data.get('notes', '')
        
        # Créer les documents pour chaque assurance fournie
        assurances_crees = []
        
        # Assurance Habitation Locataire
        if self.cleaned_data['attestation_assurance_habitation']:
            doc_habitation = Document.objects.create(
                nom=f"Assurance Habitation - {propriete.titre}",
                type_document='assurance_habitation',
                description=f"Attestation d'assurance habitation pour {propriete.titre}. Locataire: {locataire.get_nom_complet() if locataire else 'Non spécifié'}. {notes}",
                fichier=self.cleaned_data['attestation_assurance_habitation'],
                propriete=propriete,
                locataire=locataire,
                statut='valide',
                cree_par=user,
                confidentiel=True,
                tags='assurance,habitation,locataire,obligatoire'
            )
            assurances_crees.append(doc_habitation)
        
        # Assurance Propriétaire Non Occupant
        if self.cleaned_data['attestation_assurance_proprietaire']:
            doc_pno = Document.objects.create(
                nom=f"Assurance PNO - {propriete.titre}",
                type_document='assurance_pno',
                description=f"Attestation d'assurance PNO pour {propriete.titre}. {notes}",
                fichier=self.cleaned_data['attestation_assurance_proprietaire'],
                propriete=propriete,
                statut='valide',
                cree_par=user,
                confidentiel=True,
                tags='assurance,PNO,proprietaire,bailleur'
            )
            assurances_crees.append(doc_pno)
        
        # Assurance Loyers Impayés
        if self.cleaned_data['attestation_assurance_loyer_impayes']:
            doc_gli = Document.objects.create(
                nom=f"Assurance GLI - {propriete.titre}",
                type_document='assurance_gli',
                description=f"Attestation d'assurance GLI pour {propriete.titre}. {notes}",
                fichier=self.cleaned_data['attestation_assurance_loyer_impayes'],
                propriete=propriete,
                statut='valide',
                cree_par=user,
                confidentiel=True,
                tags='assurance,GLI,loyers,impayes'
            )
            assurances_crees.append(doc_gli)
        
        return assurances_crees


class EtatLieuxForm(forms.Form):
    """Formulaire pour la gestion des états des lieux."""
    
    # Champs pour les états des lieux
    etat_lieux_entree = forms.FileField(
        label=_('État des Lieux d\'Entrée'),
        help_text=_('Document signé de l\'état des lieux d\'entrée (obligatoire)'),
        required=False
    )
    
    etat_lieux_sortie = forms.FileField(
        label=_('État des Lieux de Sortie'),
        help_text=_('Document signé de l\'état des lieux de sortie'),
        required=False
    )
    
    photos_etat_lieux = forms.FileField(
        label=_('Photos de l\'État des Lieux'),
        help_text=_('Photos des pièces et éléments importants (JPG, PNG)'),
        required=False
    )
    
    # Champs de liaison
    propriete = forms.ModelChoiceField(
        queryset=Propriete.objects.filter(disponible=True),
        label=_('Propriété concernée'),
        help_text=_('Sélectionnez la propriété concernée'),
        required=True
    )
    
    locataire = forms.ModelChoiceField(
        queryset=Locataire.objects.filter(statut='actif'),
        label=_('Locataire'),
        help_text=_('Locataire concerné par cet état des lieux'),
        required=True
    )
    
    date_etat_lieux = forms.DateField(
        label=_('Date de l\'état des lieux'),
        help_text=_('Date de réalisation de l\'état des lieux'),
        required=True,
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    
    notes = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4}),
        label=_('Notes et observations'),
        help_text=_('Observations particulières, anomalies constatées, accords, etc.'),
        required=False
    )
    
    def save_etat_lieux(self, user):
        """Sauvegarde l'état des lieux et crée les documents associés."""
        propriete = self.cleaned_data['propriete']
        locataire = self.cleaned_data['locataire']
        date_etat_lieux = self.cleaned_data['date_etat_lieux']
        notes = self.cleaned_data.get('notes', '')
        
        # Créer les documents pour chaque élément fourni
        documents_crees = []
        
        # État des lieux d'entrée
        if self.cleaned_data['etat_lieux_entree']:
            doc_entree = Document.objects.create(
                nom=f"État des Lieux d'Entrée - {propriete.titre} - {locataire.get_nom_complet()}",
                type_document='etat_lieux_entree',
                description=f"État des lieux d'entrée pour {propriete.titre} - Locataire: {locataire.get_nom_complet()} - Date: {date_etat_lieux}. {notes}",
                fichier=self.cleaned_data['etat_lieux_entree'],
                propriete=propriete,
                locataire=locataire,
                statut='valide',
                cree_par=user,
                confidentiel=True,
                tags='etat_lieux,entree,contrat,obligatoire'
            )
            documents_crees.append(doc_entree)
        
        # État des lieux de sortie
        if self.cleaned_data['etat_lieux_sortie']:
            doc_sortie = Document.objects.create(
                nom=f"État des Lieux de Sortie - {propriete.titre} - {locataire.get_nom_complet()}",
                type_document='etat_lieux_sortie',
                description=f"État des lieux de sortie pour {propriete.titre} - Locataire: {locataire.get_nom_complet()} - Date: {date_etat_lieux}. {notes}",
                fichier=self.cleaned_data['etat_lieux_sortie'],
                propriete=propriete,
                locataire=locataire,
                statut='valide',
                cree_par=user,
                confidentiel=True,
                tags='etat_lieux,sortie,contrat,obligatoire'
            )
            documents_crees.append(doc_sortie)
        
        # Photos de l'état des lieux
        if self.cleaned_data['photos_etat_lieux']:
            doc_photos = Document.objects.create(
                nom=f"Photos État des Lieux - {propriete.titre} - {locataire.get_nom_complet()}",
                type_document='photos_etat_lieux',
                description=f"Photos de l'état des lieux pour {propriete.titre} - Locataire: {locataire.get_nom_complet()} - Date: {date_etat_lieux}. {notes}",
                fichier=self.cleaned_data['photos_etat_lieux'],
                propriete=propriete,
                locataire=locataire,
                statut='valide',
                cree_par=user,
                confidentiel=True,
                tags='etat_lieux,photos,contrat,visualisation'
            )
            documents_crees.append(doc_photos)
        
        return documents_crees
