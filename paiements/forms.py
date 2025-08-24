from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from .models import Paiement, ChargeDeductible, RetraitBailleur, TableauBordFinancier, RecapitulatifMensuelBailleur
from contrats.models import Contrat
from proprietes.models import Bailleur
from datetime import date, datetime
from decimal import Decimal
import json


class PaiementForm(forms.ModelForm):
    """Formulaire pour créer/modifier un paiement."""
    
    # Champs additionnels pour la gestion des charges déductibles
    appliquer_charges_deductibles = forms.BooleanField(
        required=False,
        initial=False,
        label=_('Appliquer les charges déductibles'),
        help_text=_('Cocher pour appliquer automatiquement les charges déductibles validées')
    )
    
    charges_deductibles = forms.ModelMultipleChoiceField(
        queryset=ChargeDeductible.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label=_('Charges déductibles à appliquer'),
        help_text=_('Sélectionner les charges déductibles à appliquer à ce paiement')
    )
    
    # Note: Les quittances sont générées automatiquement après validation du paiement
    # Aucun document n'est requis lors de la création du paiement
    
    class Meta:
        model = Paiement
        fields = [
            'contrat', 'montant', 'type_paiement', 'mode_paiement',
            'date_paiement', 'reference_paiement', 'numero_cheque', 'reference_virement', 'notes'
        ]
        widgets = {
            'date_paiement': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'montant': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'type_paiement': forms.Select(attrs={'class': 'form-control'}),
            'mode_paiement': forms.Select(attrs={'class': 'form-control'}),
            'reference_paiement': forms.TextInput(attrs={'class': 'form-control'}),
            'numero_cheque': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Numéro de chèque (si applicable)')
            }),
            'reference_virement': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Référence virement (si applicable)')
            }),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'statut': forms.Select(attrs={'class': 'form-control'}),
            'contrat': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'contrat': _('Contrat'),
            'montant': _('Montant'),
            'type_paiement': _('Type de paiement'),
            'mode_paiement': _('Mode de paiement'),
            'date_paiement': _('Date de paiement'),
            'reference_paiement': _('Référence de paiement'),
            'numero_cheque': _('Numéro de chèque'),
            'reference_virement': _('Référence virement'),
            'notes': _('Notes'),
            'statut': _('Statut'),
        }
    
    def __init__(self, *args, **kwargs):
        contrat_id = kwargs.pop('contrat_id', None)
        super().__init__(*args, **kwargs)
        
        # Filtrer les contrats actifs seulement
        self.fields['contrat'].queryset = Contrat.objects.filter(
            est_actif=True,
            est_resilie=False
        ).select_related('locataire', 'propriete')
        
        # Personnaliser l'affichage des contrats
        self.fields['contrat'].label_from_instance = lambda obj: (
            f"{obj.numero_contrat} - {obj.locataire.nom} {obj.locataire.prenom} "
            f"({obj.propriete.titre})"
        )
        
        # Valeur par défaut pour la date
        if not self.instance.pk:
            self.fields['date_paiement'].initial = timezone.now().date()
        
        # Si un contrat est spécifié, le pré-sélectionner et charger ses charges
        if contrat_id:
            try:
                contrat = Contrat.objects.get(id=contrat_id, est_actif=True)
                self.fields['contrat'].initial = contrat
                self.fields['montant'].initial = contrat.get_loyer_total()
                
                # Charger les charges déductibles validées pour ce contrat
                self.fields['charges_deductibles'].queryset = ChargeDeductible.objects.filter(
                    contrat=contrat, 
                    statut='validee'
                ).order_by('-date_charge')
                
                # Si il y a des charges validées, les pré-sélectionner
                if self.fields['charges_deductibles'].queryset.exists():
                    self.fields['charges_deductibles'].initial = self.fields['charges_deductibles'].queryset
                    
            except Contrat.DoesNotExist:
                pass
        
        # Si on modifie un paiement existant, charger ses charges
        elif self.instance.pk and self.instance.contrat:
            contrat = self.instance.contrat
            self.fields['charges_deductibles'].queryset = ChargeDeductible.objects.filter(
                contrat=contrat, 
                statut='validee'
            ).order_by('-date_charge')
    
    def clean_montant(self):
        montant = self.cleaned_data.get('montant')
        if montant is not None and montant <= 0:
            raise ValidationError(_('Le montant doit être positif.'))
        return montant
    
    def clean_date_paiement(self):
        date_paiement = self.cleaned_data.get('date_paiement')
        if date_paiement and date_paiement > timezone.now().date():
            raise ValidationError(_('La date de paiement ne peut pas être dans le futur.'))
        return date_paiement
    
    def clean(self):
        cleaned_data = super().clean()
        contrat = cleaned_data.get('contrat')
        type_paiement = cleaned_data.get('type_paiement')
        montant = cleaned_data.get('montant')
        mode_paiement = cleaned_data.get('mode_paiement')
        numero_cheque = cleaned_data.get('numero_cheque')
        reference_virement = cleaned_data.get('reference_virement')
        
        # Validation spécifique selon le type de paiement
        if contrat and type_paiement and montant:
            if type_paiement == 'loyer' and montant != contrat.loyer_mensuel:
                # Avertissement si le montant du loyer ne correspond pas
                pass  # On peut ajouter une validation plus stricte si nécessaire
            
            elif type_paiement == 'caution' and montant != contrat.caution:
                # Avertissement si le montant de la caution ne correspond pas
                pass  # On peut ajouter une validation plus stricte si nécessaire
        
        # Validation des informations de paiement selon le mode
        if mode_paiement == 'cheque' and not numero_cheque:
            raise ValidationError(_('Le numéro de chèque est requis pour un paiement par chèque.'))
        
        if mode_paiement == 'virement' and not reference_virement:
            raise ValidationError(_('La référence virement est requise pour un paiement par virement.'))
        
        return cleaned_data


class ChargeDeductibleForm(forms.ModelForm):
    """Formulaire pour créer/modifier une charge déductible."""
    
    class Meta:
        model = ChargeDeductible
        fields = [
            'contrat', 'montant', 'libelle', 'description', 'type_charge'
        ]
        widgets = {
            'contrat': forms.Select(attrs={'class': 'form-control'}),
            'montant': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'libelle': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'type_charge': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'contrat': _('Contrat'),
            'montant': _('Montant'),
            'libelle': _('Libellé de la charge'),
            'description': _('Description'),
            'type_charge': _('Type de charge'),
        }
    
    def clean_montant(self):
        montant = self.cleaned_data.get('montant')
        if montant is not None and montant <= 0:
            raise ValidationError(_('Le montant doit être positif.'))
        return montant


# PaiementAvecChargesForm temporairement supprimé - à réimplémenter après la migration


class RechercheAvanceePaiementsForm(forms.Form):
    """Formulaire de recherche avancée pour les paiements."""
    
    # Critères de recherche
    numero_contrat = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Numéro de contrat')}),
        label=_('Numéro de contrat')
    )
    
    nom_locataire = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Nom du locataire')}),
        label=_('Nom du locataire')
    )
    
    type_paiement = forms.ChoiceField(
        choices=[('', _('Tous les types'))] + [
            ('loyer', 'Loyer'),
            ('charges', 'Charges'),
            ('caution', 'Caution'),
            ('avance_loyer', 'Avance de loyer'),
            ('depot_garantie', 'Dépôt de garantie'),
            ('regularisation', 'Régularisation'),
            ('paiement_partiel', 'Paiement partiel'),
            ('autre', 'Autre'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label=_('Type de paiement')
    )
    
    mode_paiement = forms.ChoiceField(
        choices=[('', _('Tous les modes'))] + [
            ('virement', 'Virement bancaire'),
            ('cheque', 'Chèque'),
            ('especes', 'Espèces'),
            ('prelevement', 'Prélèvement automatique'),
            ('carte', 'Carte bancaire'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label=_('Mode de paiement')
    )
    
    statut = forms.ChoiceField(
        choices=[('', _('Tous les statuts'))] + [
            ('en_attente', 'En attente'),
            ('valide', 'Validé'),
            ('refuse', 'Refusé'),
            ('annule', 'Annulé'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label=_('Statut')
    )
    
    # Filtres par montant
    montant_min = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': _('Montant minimum')}),
        label=_('Montant minimum')
    )
    
    montant_max = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': _('Montant maximum')}),
        label=_('Montant maximum')
    )
    
    # Filtres par date
    date_debut = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label=_('Date de début')
    )
    
    date_fin = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label=_('Date de fin')
    )
    
    # Filtres par propriété
    propriete = forms.ModelChoiceField(
        queryset=None,  # Sera défini dans __init__
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label=_('Propriété'),
        empty_label=_('Toutes les propriétés')
    )
    
    # Filtres par bailleur
    bailleur = forms.ModelChoiceField(
        queryset=Bailleur.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label=_('Bailleur'),
        empty_label=_('Tous les bailleurs')
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Définir le queryset pour les propriétés
        from proprietes.models import Propriete
        self.fields['propriete'].queryset = Propriete.objects.all().select_related('bailleur')
        
        # Personnaliser l'affichage des propriétés
        self.fields['propriete'].label_from_instance = lambda obj: (
            f"{obj.titre} - {obj.adresse} ({obj.bailleur.nom})"
        )
        
        # Personnaliser l'affichage des bailleurs
        self.fields['bailleur'].label_from_instance = lambda obj: (
            f"{obj.nom} {obj.prenom}" if obj.prenom else obj.nom
        )
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Validation des montants
        montant_min = cleaned_data.get('montant_min')
        montant_max = cleaned_data.get('montant_max')
        
        if montant_min is not None and montant_max is not None:
            if montant_min > montant_max:
                raise ValidationError(_('Le montant minimum ne peut pas être supérieur au montant maximum.'))
        
        # Validation des dates
        date_debut = cleaned_data.get('date_debut')
        date_fin = cleaned_data.get('date_fin')
        
        if date_debut and date_fin:
            if date_debut > date_fin:
                raise ValidationError(_('La date de début ne peut pas être postérieure à la date de fin.'))
        
        return cleaned_data


class RetraitBailleurForm(forms.ModelForm):
    """Formulaire pour créer/modifier un retrait bailleur."""
    
    class Meta:
        model = RetraitBailleur
        fields = [
            'bailleur', 'mois_retrait', 'montant_loyers_bruts',
            'montant_charges_deductibles', 'montant_net_a_payer', 'type_retrait', 'statut', 'mode_retrait',
            'date_demande', 'date_versement', 'numero_cheque', 'reference_virement', 'notes'
        ]
        widgets = {
            'mois_retrait': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'montant_loyers_bruts': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01'
            }),
            'montant_charges_deductibles': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'type_retrait': forms.Select(attrs={
                'class': 'form-control'
            }),
            'statut': forms.Select(attrs={
                'class': 'form-control'
            }),
            'mode_retrait': forms.Select(attrs={
                'class': 'form-control'
            }),
            'date_demande': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'montant_net_a_payer': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01',
                'readonly': 'readonly'
            }),
            'date_versement': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'numero_cheque': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Numéro de chèque'
            }),
            'reference_virement': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Référence du virement'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filtrer les bailleurs actifs seulement
        self.fields['bailleur'].queryset = Bailleur.objects.filter(
            actif=True
        ).order_by('nom', 'prenom')
        
        # Personnaliser l'affichage des bailleurs
        self.fields['bailleur'].label_from_instance = lambda obj: (
            f"{obj.nom} {obj.prenom} - {obj.email}"
        )
        
        # Valeurs par défaut
        if not self.instance.pk:
            self.fields['date_demande'].initial = timezone.now().date()
            self.fields['mois_retrait'].initial = timezone.now().date().replace(day=1)
            self.fields['statut'].initial = 'en_attente'
            self.fields['type_retrait'].initial = 'mensuel'
            self.fields['montant_charges_deductibles'].initial = 0
            self.fields['montant_net_a_payer'].initial = 0
    
    def clean_mois_retrait(self):
        """Valider le format du mois de retrait."""
        mois_retrait = self.cleaned_data.get('mois_retrait')
        if mois_retrait:
            # S'assurer que c'est le premier jour du mois
            if mois_retrait.day != 1:
                mois_retrait = mois_retrait.replace(day=1)
        return mois_retrait
    
    def clean(self):
        """Validation globale du formulaire."""
        cleaned_data = super().clean()
        montant_loyers_bruts = cleaned_data.get('montant_loyers_bruts')
        montant_charges_deductibles = cleaned_data.get('montant_charges_deductibles')
        
        # Validation des montants
        if montant_loyers_bruts is not None and montant_loyers_bruts <= 0:
            raise ValidationError(_('Le montant des loyers bruts doit être positif.'))
        
        if montant_charges_deductibles is not None and montant_charges_deductibles < 0:
            raise ValidationError(_('Le montant des charges déductibles ne peut pas être négatif.'))
        
        # Calculer automatiquement le montant net
        if montant_loyers_bruts is not None and montant_charges_deductibles is not None:
            montant_net_calcule = montant_loyers_bruts - montant_charges_deductibles
            
            # Vérifier que le montant net est positif
            if montant_net_calcule <= 0:
                raise ValidationError(_('Le montant net à payer doit être positif. Les charges déductibles ne peuvent pas dépasser les loyers bruts.'))
            
            # Mettre à jour le champ montant net
            cleaned_data['montant_net_a_payer'] = montant_net_calcule
        
        return cleaned_data


class GestionChargesBailleurForm(forms.Form):
    """Formulaire pour gérer les charges de bailleur dans un retrait."""
    
    charge_bailleur = forms.ModelChoiceField(
        queryset=None,
        label=_('Charge bailleur à déduire'),
        help_text=_('Sélectionnez la charge à déduire du retrait mensuel'),
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'charge_bailleur_select'
        })
    )
    
    montant_deduction = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=0.01,
        label=_('Montant à déduire (XOF)'),
        help_text=_('Montant à déduire du retrait mensuel'),
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0.01',
            'id': 'montant_deduction'
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
    
    def __init__(self, retrait_bailleur=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.retrait_bailleur = retrait_bailleur
        
        if retrait_bailleur:
            # Filtrer les charges de bailleur éligibles
            from proprietes.models import ChargesBailleur
            
            charges_eligibles = ChargesBailleur.objects.filter(
                propriete__bailleur=retrait_bailleur.bailleur,
                statut__in=['en_attente', 'deduite_retrait']
            ).exclude(
                retraits_lies__retrait_bailleur=retrait_bailleur
            ).select_related('propriete')
            
            self.fields['charge_bailleur'].queryset = charges_eligibles
            
            # Personnaliser l'affichage des charges
            self.fields['charge_bailleur'].label_from_instance = lambda obj: (
                f"{obj.titre} - {obj.propriete.adresse} - {obj.montant_restant} XOF restant"
            )
    
    def clean(self):
        """Validation globale du formulaire."""
        cleaned_data = super().clean()
        charge_bailleur = cleaned_data.get('charge_bailleur')
        montant_deduction = cleaned_data.get('montant_deduction')
        
        if charge_bailleur and montant_deduction:
            # Vérifier que le montant ne dépasse pas le montant restant
            montant_restant = charge_bailleur.get_montant_deductible()
            if montant_deduction > montant_restant:
                raise ValidationError(
                    f'Le montant de déduction ({montant_deduction}) ne peut pas dépasser '
                    f'le montant restant ({montant_restant}) de la charge.'
                )
            
            # Vérifier que le montant ne dépasse pas le montant net du retrait
            if self.retrait_bailleur:
                montant_net_disponible = self.retrait_bailleur.montant_net_a_payer
                if montant_deduction > montant_net_disponible:
                    raise ValidationError(
                        f'Le montant de déduction ({montant_deduction}) ne peut pas dépasser '
                        f'le montant net disponible ({montant_net_disponible}) du retrait.'
                    )
        
        return cleaned_data


class TableauBordFinancierForm(forms.ModelForm):
    """Formulaire professionnel pour créer/modifier un tableau de bord financier."""
    
    class Meta:
        model = TableauBordFinancier
        fields = [
            'nom', 'description', 'proprietes', 'bailleurs',
            'afficher_revenus', 'afficher_charges', 'afficher_benefices', 'afficher_taux_occupation',
            'periode', 'date_debut_personnalisee', 'date_fin_personnalisee',
            'seuil_alerte', 'devise', 'couleur_theme', 'actif'
        ]
        widgets = {
            'nom': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Ex: Tableau de bord mensuel - Q1 2024')
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('Description détaillée du tableau de bord...')
            }),
            'proprietes': forms.SelectMultiple(attrs={
                'class': 'form-control select2',
                'data-placeholder': _('Sélectionner les propriétés...')
            }),
            'bailleurs': forms.SelectMultiple(attrs={
                'class': 'form-control select2',
                'data-placeholder': _('Sélectionner les bailleurs...')
            }),
            'periode': forms.Select(attrs={
                'class': 'form-control'
            }),
            'date_debut_personnalisee': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'date_fin_personnalisee': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'seuil_alerte': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': _('Montant seuil pour les alertes')
            }),
            'devise': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'XOF'
            }),
            'couleur_theme': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'color',
                'placeholder': '#007bff'
            }),
        }
        labels = {
            'nom': _('Nom du tableau de bord'),
            'description': _('Description'),
            'proprietes': _('Propriétés incluses'),
            'bailleurs': _('Bailleurs inclus'),
            'afficher_revenus': _('Afficher les revenus'),
            'afficher_charges': _('Afficher les charges'),
            'afficher_benefices': _('Afficher les bénéfices'),
            'afficher_taux_occupation': _('Afficher le taux d\'occupation'),
            'periode': _('Période d\'analyse'),
            'date_debut_personnalisee': _('Date de début (période personnalisée)'),
            'date_fin_personnalisee': _('Date de fin (période personnalisée)'),
            'seuil_alerte': _('Seuil d\'alerte'),
            'devise': _('Devise'),
            'couleur_theme': _('Couleur du thème'),
            'actif': _('Tableau actif'),
        }
        help_texts = {
            'nom': _('Nom descriptif et unique pour identifier ce tableau de bord'),
            'description': _('Description détaillée des objectifs et du contenu de ce tableau de bord'),
            'proprietes': _('Sélectionner les propriétés à inclure dans l\'analyse financière'),
            'bailleurs': _('Sélectionner les bailleurs à inclure dans l\'analyse (optionnel)'),
            'periode': _('Période d\'analyse pour les calculs financiers'),
            'seuil_alerte': _('Montant minimum des bénéfices avant déclenchement d\'une alerte'),
            'devise': _('Devise utilisée pour l\'affichage des montants'),
            'couleur_theme': _('Couleur principale pour la personnalisation visuelle'),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Importer les modèles nécessaires
        from proprietes.models import Propriete, Bailleur
        
        # Filtrer les propriétés et bailleurs actifs
        self.fields['proprietes'].queryset = Propriete.objects.filter(
            actif=True,
            is_deleted=False
        ).select_related('bailleur').order_by('titre')
        
        self.fields['bailleurs'].queryset = Bailleur.objects.filter(
            actif=True,
            is_deleted=False
        ).order_by('nom', 'prenom')
        
        # Personnaliser l'affichage des propriétés
        self.fields['proprietes'].label_from_instance = lambda obj: (
            f"{obj.titre} - {obj.adresse} ({obj.bailleur.nom if obj.bailleur else 'N/A'})"
        )
        
        # Personnaliser l'affichage des bailleurs
        self.fields['bailleurs'].label_from_instance = lambda obj: (
            f"{obj.nom} {obj.prenom} - {obj.email or obj.telephone}"
        )
        
        # Valeurs par défaut
        if not self.instance.pk:
            self.fields['actif'].initial = True
            self.fields['devise'].initial = 'XOF'
            self.fields['couleur_theme'].initial = '#007bff'
            self.fields['afficher_revenus'].initial = True
            self.fields['afficher_charges'].initial = True
            self.fields['afficher_benefices'].initial = True
            self.fields['afficher_taux_occupation'].initial = True
        
        # Définir l'utilisateur créateur
        if user and not self.instance.pk:
            self.instance.cree_par = user
    
    def clean(self):
        """Validation globale du formulaire."""
        cleaned_data = super().clean()
        periode = cleaned_data.get('periode')
        date_debut = cleaned_data.get('date_debut_personnalisee')
        date_fin = cleaned_data.get('date_fin_personnalisee')
        
        # Validation des dates personnalisées
        if periode == 'personnalise':
            if not date_debut:
                raise ValidationError(_('La date de début est requise pour une période personnalisée.'))
            if not date_fin:
                raise ValidationError(_('La date de fin est requise pour une période personnalisée.'))
            if date_debut and date_fin and date_debut >= date_fin:
                raise ValidationError(_('La date de début doit être antérieure à la date de fin.'))
        
        # Validation du seuil d'alerte
        seuil_alerte = cleaned_data.get('seuil_alerte')
        if seuil_alerte is not None and seuil_alerte < 0:
            raise ValidationError(_('Le seuil d\'alerte ne peut pas être négatif.'))
        
        # Validation des propriétés
        proprietes = cleaned_data.get('proprietes')
        if proprietes and proprietes.count() == 0:
            raise ValidationError(_('Au moins une propriété doit être sélectionnée.'))
        
        return cleaned_data
    
    def clean_nom(self):
        """Validation du nom du tableau de bord."""
        nom = self.cleaned_data.get('nom')
        if nom:
            # Vérifier l'unicité du nom
            from .models import TableauBordFinancier
            queryset = TableauBordFinancier.objects.filter(nom=nom)
            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            
            if queryset.exists():
                raise ValidationError(_('Un tableau de bord avec ce nom existe déjà.'))
        
        return nom


class RecapitulatifMensuelBailleurForm(forms.ModelForm):
    """Formulaire pour créer/modifier un récapitulatif mensuel par bailleur."""
    
    class Meta:
        model = RecapitulatifMensuelBailleur
        fields = [
            'bailleur', 'mois_recapitulatif', 'type_recapitulatif', 'notes'
        ]
        widgets = {
            'bailleur': forms.Select(attrs={
                'class': 'form-control',
                'placeholder': 'Sélectionnez le bailleur'
            }),
            'mois_recapitulatif': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'type_recapitulatif': forms.Select(attrs={
                'class': 'form-control'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Notes et observations sur ce récapitulatif...'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Définir le mois actuel par défaut
        if not self.instance.pk:
            from django.utils import timezone
            mois_actuel = timezone.now().replace(day=1)
            self.fields['mois_recapitulatif'].initial = mois_actuel
    
    def clean_mois_recapitulatif(self):
        """Validation du mois du récapitulatif."""
        mois = self.cleaned_data['mois_recapitulatif']
        
        # Vérifier qu'il n'y a pas déjà un récapitulatif pour ce mois
        if not self.instance.pk:
            type_recap = self.cleaned_data.get('type_recapitulatif', 'mensuel')
            if RecapitulatifMensuelBailleur.objects.filter(
                mois_recapitulatif=mois,
                type_recapitulatif=type_recap
            ).exists():
                raise forms.ValidationError(
                    f"Un récapitulatif {type_recap} existe déjà pour {mois.strftime('%B %Y')}"
                )
        
        return mois


class RecapitulatifMensuelValidationForm(forms.Form):
    """Formulaire pour valider un récapitulatif mensuel par bailleur."""
    
    confirmation = forms.BooleanField(
        required=True,
        label="Je confirme que ce récapitulatif est correct et peut être validé",
        help_text="Cette action ne peut pas être annulée"
    )
    
    notes_validation = forms.CharField(
        max_length=500,
        required=False,
        label="Notes de validation",
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Observations sur la validation...'
        })
    )


class RecapitulatifMensuelEnvoiForm(forms.Form):
    """Formulaire pour envoyer un récapitulatif mensuel par bailleur."""
    
    methode_envoi = forms.ChoiceField(
        choices=[
            ('email', 'Email'),
            ('courrier', 'Courrier postal'),
            ('main_propre', 'Remis en main propre'),
            ('autre', 'Autre méthode')
        ],
        label="Méthode d'envoi",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    destinataire = forms.CharField(
        max_length=200,
        label="Destinataire",
        help_text="Nom et coordonnées du destinataire"
    )
    
    notes_envoi = forms.CharField(
        max_length=500,
        required=False,
        label="Notes d'envoi",
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Détails sur l\'envoi...'
        })
    )
    
    date_envoi_prevue = forms.DateField(
        label="Date d'envoi prévue",
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
