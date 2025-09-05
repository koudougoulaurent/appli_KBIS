from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .models import Paiement, ChargeDeductible, Contrat
from proprietes.models import Document


class QuittanceLoyerForm(forms.Form):
    """Formulaire spécialisé pour la génération et gestion des quittances de loyer avec gestion documentaire intégrée."""
    
    # Champs pour la quittance
    contrat = forms.ModelChoiceField(
        queryset=Contrat.objects.filter(est_actif=True),
        required=True,
        label=_('Contrat concerné'),
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    periode_quittance = forms.ChoiceField(
        choices=[
            ('mensuel', 'Mensuel'),
            ('trimestriel', 'Trimestriel'),
            ('semestriel', 'Semestriel'),
            ('annuel', 'Annuel'),
        ],
        required=True,
        initial='mensuel',
        label=_('Période de la quittance'),
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    mois_quittance = forms.ChoiceField(
        choices=[
            ('01', 'Janvier'), ('02', 'Février'), ('03', 'Mars'),
            ('04', 'Avril'), ('05', 'Mai'), ('06', 'Juin'),
            ('07', 'Juillet'), ('08', 'Août'), ('09', 'Septembre'),
            ('10', 'Octobre'), ('11', 'Novembre'), ('12', 'Décembre')
        ],
        required=True,
        label=_('Mois de la quittance'),
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    annee_quittance = forms.IntegerField(
        required=True,
        label=_('Année de la quittance'),
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '2020',
            'max': '2030'
        })
    )
    
    montant_loyer = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=True,
        label=_('Montant du loyer (F CFA)'),
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0'
        })
    )
    
    montant_charges = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        initial=0,
        label=_('Montant des charges (F CFA)'),
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0'
        })
    )
    
    montant_total = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=True,
        label=_('Montant total (F CFA)'),
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0',
            'readonly': 'readonly'
        })
    )
    
    # Champs pour les documents
    quittance_generee = forms.FileField(
        required=False,
        label=_('Quittance générée'),
        help_text=_('Quittance de loyer générée (PDF)'),
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf'
        })
    )
    
    justificatif_paiement = forms.FileField(
        required=False,
        label=_('Justificatif de paiement'),
        help_text=_('Justificatif du paiement (PDF, JPG, PNG)'),
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,.jpg,.jpeg,.png'
        })
    )
    
    # Champ pour les notes
    notes = forms.CharField(
        required=False,
        label=_('Notes sur la quittance'),
        help_text=_('Commentaires sur la quittance'),
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Notes sur la quittance...'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Définir l'année par défaut
        from django.utils import timezone
        current_year = timezone.now().year
        self.fields['annee_quittance'].initial = current_year
        
        # Définir le mois par défaut
        current_month = timezone.now().month
        self.fields['mois_quittance'].initial = f"{current_month:02d}"
    
    def clean(self):
        cleaned_data = super().clean()
        montant_loyer = cleaned_data.get('montant_loyer', 0)
        montant_charges = cleaned_data.get('montant_charges', 0)
        
        # Calculer le montant total
        montant_total = montant_loyer + montant_charges
        cleaned_data['montant_total'] = montant_total
        
        return cleaned_data
    
    def save_quittance(self, user):
        """Sauvegarde la quittance et crée automatiquement les documents associés."""
        contrat = self.cleaned_data.get('contrat')
        
        if contrat and user:
            self._create_documents_for_quittance(contrat, user)
        
        return contrat
    
    def _create_documents_for_quittance(self, contrat, user):
        """Crée automatiquement les documents pour la quittance."""
        # Mapping des champs de fichiers vers les types de documents
        document_mapping = {
            'quittance_generee': ('quittance', 'Quittance de loyer'),
            'justificatif_paiement': ('justificatif', 'Justificatif de paiement'),
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
                    confidentiel=False  # Les quittances ne sont pas confidentielles
                )


class FactureForm(forms.Form):
    """Formulaire spécialisé pour la gestion des factures avec gestion documentaire intégrée."""
    
    # Champs pour la facture
    contrat = forms.ModelChoiceField(
        queryset=Contrat.objects.filter(est_actif=True),
        required=True,
        label=_('Contrat concerné'),
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    type_facture = forms.ChoiceField(
        choices=[
            ('loyer', 'Loyer'),
            ('charges', 'Charges'),
            ('travaux', 'Travaux'),
            ('entretien', 'Entretien'),
            ('autre', 'Autre'),
        ],
        required=True,
        label=_('Type de facture'),
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    montant_facture = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=True,
        label=_('Montant de la facture (F CFA)'),
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0'
        })
    )
    
    date_facture = forms.DateField(
        required=True,
        label=_('Date de la facture'),
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    date_echeance = forms.DateField(
        required=True,
        label=_('Date d\'échéance'),
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    # Champs pour les documents
    facture_generee = forms.FileField(
        required=True,
        label=_('Facture générée'),
        help_text=_('Facture générée (PDF)'),
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf'
        })
    )
    
    justificatif_facture = forms.FileField(
        required=False,
        label=_('Justificatif de la facture'),
        help_text=_('Justificatif de la facture (PDF, JPG, PNG)'),
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,.jpg,.jpeg,.png'
        })
    )
    
    # Champ pour les notes
    notes = forms.CharField(
        required=False,
        label=_('Notes sur la facture'),
        help_text=_('Commentaires sur la facture'),
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Notes sur la facture...'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Définir la date par défaut
        from django.utils import timezone
        current_date = timezone.now().date()
        self.fields['date_facture'].initial = current_date
        
        # Définir l'échéance par défaut (fin du mois)
        from datetime import date
        if current_date.month == 12:
            next_month = date(current_date.year + 1, 1, 1)
        else:
            next_month = date(current_date.year, current_date.month + 1, 1)
        
        # Dernier jour du mois
        from calendar import monthrange
        last_day = monthrange(next_month.year, next_month.month)[1]
        echeance = date(next_month.year, next_month.month, last_day)
        self.fields['date_echeance'].initial = echeance
    
    def clean(self):
        cleaned_data = super().clean()
        date_facture = cleaned_data.get('date_facture')
        date_echeance = cleaned_data.get('date_echeance')
        
        # Vérifier que l'échéance est après la date de facture
        if date_facture and date_echeance and date_echeance <= date_facture:
            raise ValidationError(_('La date d\'échéance doit être postérieure à la date de facture.'))
        
        return cleaned_data
    
    def save_facture(self, user):
        """Sauvegarde la facture et crée automatiquement les documents associés."""
        contrat = self.cleaned_data.get('contrat')
        
        if contrat and user:
            self._create_documents_for_facture(contrat, user)
        
        return contrat
    
    def _create_documents_for_facture(self, contrat, user):
        """Crée automatiquement les documents pour la facture."""
        # Mapping des champs de fichiers vers les types de documents
        document_mapping = {
            'facture_generee': ('facture', 'Facture générée'),
            'justificatif_facture': ('justificatif', 'Justificatif de la facture'),
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
                    confidentiel=False  # Les factures ne sont pas confidentielles
                )


class RecuForm(forms.Form):
    """Formulaire spécialisé pour la gestion des reçus avec gestion documentaire intégrée."""
    
    # Champs pour le reçu
    contrat = forms.ModelChoiceField(
        queryset=Contrat.objects.filter(est_actif=True),
        required=True,
        label=_('Contrat concerné'),
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    type_recu = forms.ChoiceField(
        choices=[
            ('loyer', 'Loyer'),
            ('charges', 'Charges'),
            ('caution', 'Caution'),
            ('travaux', 'Travaux'),
            ('autre', 'Autre'),
        ],
        required=True,
        label=_('Type de reçu'),
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    montant_recu = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=True,
        label=_('Montant reçu (F CFA)'),
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0'
        })
    )
    
    mode_paiement = forms.ChoiceField(
        choices=[
            ('virement', 'Virement bancaire'),
            ('cheque', 'Chèque'),
            ('especes', 'Espèces'),
            ('prelevement', 'Prélèvement automatique'),
            ('carte', 'Carte bancaire'),
        ],
        required=True,
        label=_('Mode de paiement'),
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    date_paiement = forms.DateField(
        required=True,
        label=_('Date de paiement'),
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    # Champs pour les documents
    recu_genere = forms.FileField(
        required=True,
        label=_('Reçu généré'),
        help_text=_('Reçu généré (PDF)'),
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf'
        })
    )
    
    justificatif_paiement = forms.FileField(
        required=False,
        label=_('Justificatif de paiement'),
        help_text=_('Justificatif du paiement (PDF, JPG, PNG)'),
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,.jpg,.jpeg,.png'
        })
    )
    
    # Champ pour les notes
    notes = forms.CharField(
        required=False,
        label=_('Notes sur le reçu'),
        help_text=_('Commentaires sur le reçu'),
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Notes sur le reçu...'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Définir la date par défaut
        from django.utils import timezone
        current_date = timezone.now().date()
        self.fields['date_paiement'].initial = current_date
    
    def save_recu(self, user):
        """Sauvegarde le reçu et crée automatiquement les documents associés."""
        contrat = self.cleaned_data.get('contrat')
        
        if contrat and user:
            self._create_documents_for_recu(contrat, user)
        
        return contrat
    
    def _create_documents_for_recu(self, contrat, user):
        """Crée automatiquement les documents pour le reçu."""
        # Mapping des champs de fichiers vers les types de documents
        document_mapping = {
            'recu_genere': ('justificatif', 'Reçu généré'),
            'justificatif_paiement': ('justificatif', 'Justificatif de paiement'),
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
                    confidentiel=False  # Les reçus ne sont pas confidentiels
                )
