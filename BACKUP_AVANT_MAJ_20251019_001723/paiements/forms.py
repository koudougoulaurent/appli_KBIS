from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from .models import Paiement, ChargeDeductible, RetraitBailleur, RecapMensuel
from contrats.models import Contrat
from proprietes.models import Bailleur
from datetime import date


class PaiementForm(forms.ModelForm):
    """Formulaire pour créer/modifier un paiement."""
    
    # Champ mois_paye SUPPRIMÉ du formulaire - géré uniquement côté template
    
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
            'date_paiement', 'mois_paye', 'numero_cheque', 'reference_virement', 'notes'
        ]
        widgets = {
            'date_paiement': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'mois_paye': forms.Select(attrs={'class': 'form-select'}, choices=[
                ('', '-- Sélectionner un mois --'),
                ('janvier', 'Janvier'),
                ('février', 'Février'),
                ('mars', 'Mars'),
                ('avril', 'Avril'),
                ('mai', 'Mai'),
                ('juin', 'Juin'),
                ('juillet', 'Juillet'),
                ('août', 'Août'),
                ('septembre', 'Septembre'),
                ('octobre', 'Octobre'),
                ('novembre', 'Novembre'),
                ('décembre', 'Décembre'),
            ]),
            'montant': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'type_paiement': forms.Select(attrs={'class': 'form-select'}),
            'mode_paiement': forms.Select(attrs={'class': 'form-select'}),
            # 'reference_paiement': forms.TextInput(attrs={'class': 'form-control'}),  # Champ supprimé
            'numero_cheque': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Numéro de chèque (si applicable)')
            }),
            'reference_virement': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Référence virement (si applicable)')
            }),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'statut': forms.Select(attrs={'class': 'form-select'}),
            'contrat': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'contrat': _('Contrat'),
            'montant': _('Montant'),
            'type_paiement': _('Type de paiement'),
            'mode_paiement': _('Mode de paiement'),
            'date_paiement': _('Date de paiement'),
            'mois_paye': _('Mois payé'),
            # 'reference_paiement': _('Référence de paiement'),  # Champ supprimé
            'numero_cheque': _('Numéro de chèque'),
            'reference_virement': _('Référence virement'),
            'notes': _('Notes'),
            'statut': _('Statut'),
        }
    
    def __init__(self, *args, **kwargs):
        contrat_id = kwargs.pop('contrat_id', None)
        mois_suggere = kwargs.pop('mois_suggere', None)
        super().__init__(*args, **kwargs)
        
        # Filtrer les contrats actifs seulement
        self.fields['contrat'].queryset = Contrat.objects.filter(
            est_actif=True,
            est_resilie=False,
            is_deleted=False
        ).select_related('locataire', 'propriete')
        
        # Personnaliser l'affichage des contrats
        self.fields['contrat'].label_from_instance = lambda obj: (
            f"{obj.numero_contrat} - {obj.locataire.nom} {obj.locataire.prenom} "
            f"({obj.propriete.titre})"
        )
        
        # Améliorer le widget de sélection de contrat
        self.fields['contrat'].widget.attrs.update({
            'class': 'form-select form-select-lg',
            'data-toggle': 'select2',
            'data-placeholder': 'Recherchez un contrat...',
            'id': 'id_contrat'
        })
        
        # Valeur par défaut pour la date
        if not self.instance.pk:
            self.fields['date_paiement'].initial = timezone.now().date()
            # Pré-remplir le mois suggéré si fourni
            if mois_suggere:
                self.fields['mois_paye'].initial = mois_suggere
        
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
        mode_paiement = cleaned_data.get('mode_paiement')
        numero_cheque = cleaned_data.get('numero_cheque')
        reference_virement = cleaned_data.get('reference_virement')
        mois_paye = cleaned_data.get('mois_paye')
        
        # Validation des montants - DÉSACTIVÉE pour permettre tous les paiements
        # Les montants sont validés côté base de données et dans les vues
        # Cette validation était trop restrictive et bloquait les paiements valides
        
        # Validation des informations de paiement selon le mode
        if mode_paiement == 'cheque' and not numero_cheque:
            raise ValidationError(_('Le numéro de chèque est requis pour un paiement par chèque.'))
        
        if mode_paiement == 'virement' and not reference_virement:
            raise ValidationError(_('La référence virement est requise pour un paiement par virement.'))
        
        # Validation des doublons de paiement pour le même contrat dans le même mois
        if contrat and mois_paye:
            existing_payment = Paiement.objects.filter(
                contrat_id=contrat.id,
                mois_paye=mois_paye,
                is_deleted=False
            ).exclude(pk=self.instance.pk if self.instance.pk else None)
            
            if existing_payment.exists():
                existing = existing_payment.first()
                self.add_error('mois_paye', 
                    f"Un paiement existe déjà pour ce contrat au mois de {mois_paye}. "
                    f"Paiement existant du {existing.date_paiement.strftime('%d/%m/%Y')} "
                    f"pour un montant de {existing.montant} F CFA."
                )
        
        return cleaned_data
    


class ChargeDeductibleForm(forms.ModelForm):
    """Formulaire pour créer/modifier une charge déductible."""
    
    class Meta:
        model = ChargeDeductible
        fields = [
            'contrat', 'montant', 'description'
        ]
        widgets = {
            'contrat': forms.Select(attrs={'class': 'form-select'}),
            'montant': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            # 'libelle': forms.TextInput(attrs={'class': 'form-control'}),  # Champ supprimé
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            # 'type_charge': forms.Select(attrs={'class': 'form-select'}),  # Champ supprimé
        }
        labels = {
            'contrat': _('Contrat'),
            'montant': _('Montant'),
            # 'libelle': _('Libellé de la charge'),  # Champ supprimé
            'description': _('Description'),
            # 'type_charge': _('Type de charge'),  # Champ supprimé
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
        widget=forms.Select(attrs={'class': 'form-select'}),
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
        widget=forms.Select(attrs={'class': 'form-select'}),
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
        widget=forms.Select(attrs={'class': 'form-select'}),
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
        widget=forms.Select(attrs={'class': 'form-select'}),
        label=_('Propriété'),
        empty_label=_('Toutes les propriétés')
    )
    
    # Filtres par bailleur
    bailleur = forms.ModelChoiceField(
        queryset=Bailleur.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
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
            'montant_charges_deductibles', 'montant_charges_bailleur', 'montant_net_a_payer', 
            'type_retrait', 'statut', 'mode_retrait', 'notes'
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
            'montant_charges_bailleur': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'montant_net_a_payer': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01',
                'readonly': 'readonly'
            }),
            'type_retrait': forms.Select(attrs={
                'class': 'form-select'
            }),
            'statut': forms.Select(attrs={
                'class': 'form-select'
            }),
            'mode_retrait': forms.Select(attrs={
                'class': 'form-select'
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
            self.fields['mois_retrait'].initial = timezone.now().date().replace(day=1)
            self.fields['statut'].initial = 'en_attente'
            self.fields['type_retrait'].initial = 'mensuel'
            self.fields['montant_charges_deductibles'].initial = 0
            self.fields['montant_charges_bailleur'].initial = 0
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
        montant_charges_bailleur = cleaned_data.get('montant_charges_bailleur', 0) or 0
        if montant_loyers_bruts is not None and montant_charges_deductibles is not None:
            montant_net_calcule = montant_loyers_bruts - montant_charges_deductibles - montant_charges_bailleur
            
            # Vérifier que le montant net est positif
            if montant_net_calcule <= 0:
                raise ValidationError(_('Le montant net à payer doit être positif. Les charges ne peuvent pas dépasser les loyers bruts.'))
            
            # Mettre à jour le champ montant net
            cleaned_data['montant_net_a_payer'] = max(montant_net_calcule, 0)
        
        return cleaned_data


class GestionChargesBailleurForm(forms.Form):
    """Formulaire pour gérer les charges de bailleur dans un retrait."""
    
    charge_bailleur = forms.ModelChoiceField(
        queryset=None,
        label=_('Charge bailleur à déduire'),
        help_text=_('Sélectionnez la charge à déduire du retrait mensuel'),
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'charge_bailleur_select'
        })
    )
    
    montant_deduction = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=0.01,
        label=_('Montant à déduire (F CFA)'),
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
    
    def __init__(self, *args, retrait_bailleur=None, **kwargs):
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
                f"{obj.titre} - {obj.propriete.adresse} - {obj.montant_restant} F CFA restant"
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


# class TableauBordFinancierForm(forms.ModelForm):  # Modèle supprimé
    # """Formulaire professionnel pour créer/modifier un tableau de bord financier."""
    # Classe commentée car le modèle n'existe plus
    # Contenu de la classe commenté car le modèle n'existe plus


# class RecapMensuelForm(forms.ModelForm):  # Modèle supprimé
    # """Formulaire pour créer/modifier un récapitulatif mensuel par bailleur."""
    
    # class Meta:
        # model = RecapMensuel
        # fields = [
        #     'bailleur', 'mois_recapitulatif', 'type_recapitulatif', 'notes'
        # ]
        # widgets = {
            # 'bailleur': forms.Select(attrs={
            #     'class': 'form-select',
            #     'required': True
            # }),
            # 'mois_recapitulatif': forms.DateInput(attrs={
            #     'class': 'form-control',
            #     'type': 'date',
            #     'required': True
            # }),
            # 'type_recapitulatif': forms.Select(attrs={
            #     'class': 'form-select',
            #     'required': True,
            #     'onchange': 'updatePeriodLabel()'
            # }),
            # 'notes': forms.Textarea(attrs={
            #     'class': 'form-control',
            #     'rows': 3,
            #     'placeholder': 'Notes et observations sur ce récapitulatif...'
            # })
        # }
        # labels = {
        #     'bailleur': _('Bailleur'),
        #     'mois_recapitulatif': _('Mois de référence'),
        #     'type_recapitulatif': _('Type de récapitulatif'),
        #     'notes': _('Notes et observations')
        # }
        # help_texts = {
        #     'mois_recapitulatif': _('Mois de référence pour le calcul du récapitulatif'),
        #     'type_recapitulatif': _('Période couverte par le récapitulatif'),
        #     'notes': _('Informations complémentaires sur ce récapitulatif')
        # }
    
    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
        
        # # Filtrer les bailleurs actifs
        # self.fields['bailleur'].queryset = Bailleur.objects.filter(
        #     is_deleted=False
        # ).order_by('nom', 'prenom')
        
        # # Personnaliser les choix du type de récapitulatif
        # self.fields['type_recapitulatif'].choices = [
        #     ('mensuel', '📅 Mensuel - 1 mois'),
        #     ('trimestriel', '📊 Trimestriel - 3 mois'),
        #     ('annuel', '📈 Annuel - 12 mois'),
        #     ('exceptionnel', '⚡ Exceptionnel - Période personnalisée'),
        # ]
        
        # # Définir le mois actuel par défaut
        # if not self.instance.pk:
        #     from django.utils import timezone
        #     mois_actuel = timezone.now().replace(day=1)
        #     self.fields['mois_recapitulatif'].initial = mois_actuel
    
    # def clean(self):
    #     cleaned_data = super().clean()
    #     bailleur = cleaned_data.get('bailleur')
    #     mois_recapitulatif = cleaned_data.get('mois_recapitulatif')
        # type_recapitulatif = cleaned_data.get('type_recapitulatif')
        
        # if bailleur and mois_recapitulatif and type_recapitulatif:
        #     # Vérifier s'il existe déjà un récapitulatif pour cette combinaison
        #     existing_recap = RecapMensuel.objects.filter(
        #         bailleur=bailleur,
        #         mois_recapitulatif=mois_recapitulatif,
        #         type_recapitulatif=type_recapitulatif
        #     ).exclude(pk=self.instance.pk if self.instance else None)
            
        #     if existing_recap.exists():
        #         raise forms.ValidationError(
        #             f"Un récapitulatif {type_recapitulatif} existe déjà pour "
        #             f"{bailleur.get_nom_complet()} - {mois_recapitulatif.strftime('%B %Y')}"
        #         )
        
        # return cleaned_data


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
        widget=forms.Select(attrs={'class': 'form-select'})
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


class RecapMensuelForm(forms.ModelForm):
    """Formulaire pour créer/modifier un récapitulatif mensuel."""
    
    class Meta:
        model = RecapMensuel
        fields = ['bailleur', 'mois_recap']
        widgets = {
            'bailleur': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'mois_recap': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': True
            })
        }
        labels = {
            'bailleur': _('Bailleur'),
            'mois_recap': _('Mois de référence')
        }
        help_texts = {
            'mois_recap': _('Mois de référence pour le calcul du récapitulatif')
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filtrer les bailleurs actifs
        self.fields['bailleur'].queryset = Bailleur.objects.filter(
            actif=True
        ).order_by('nom', 'prenom')
        
        # Personnaliser l'affichage des bailleurs
        self.fields['bailleur'].label_from_instance = lambda obj: (
            f"{obj.nom} {obj.prenom}" if obj.prenom else obj.nom
        )
        
        # Définir le mois actuel par défaut
        if not self.instance.pk:
            mois_actuel = timezone.now().replace(day=1)
            self.fields['mois_recap'].initial = mois_actuel
    
    def clean(self):
        cleaned_data = super().clean()
        bailleur = cleaned_data.get('bailleur')
        mois_recap = cleaned_data.get('mois_recap')
        
        if bailleur and mois_recap:
            # Vérifier s'il existe déjà un récapitulatif pour cette combinaison
            existing_recap = RecapMensuel.objects.filter(
                bailleur=bailleur,
                mois_recap=mois_recap
            ).exclude(pk=self.instance.pk if self.instance else None)
            
            if existing_recap.exists():
                raise forms.ValidationError(
                    f"Un récapitulatif existe déjà pour "
                    f"{bailleur.get_nom_complet()} - {mois_recap.strftime('%B %Y')}"
                )
        
        return cleaned_data


class GenererPDFLotForm(forms.Form):
    """Formulaire pour la génération de PDF en lot."""
    
    mois_recap = forms.DateField(
        label="Mois à traiter",
        widget=forms.DateInput(
            attrs={
                'type': 'month',
                'class': 'form-control',
                'required': True
            }
        ),
        help_text="Sélectionnez le mois pour lequel générer les PDFs"
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Définir la valeur par défaut au mois actuel
        if not self.initial:
            self.initial['mois_recap'] = date.today().replace(day=1)


# ===== FORMULAIRES POUR LES PAIEMENTS PARTIELS =====

# class PlanPaiementPartielForm(forms.ModelForm):
#     """Formulaire pour créer/modifier un plan de paiement partiel - DÉSACTIVÉ"""
#     
#     class Meta:
#         model = PlanPaiementPartiel
#         fields = [
#             'contrat', 'nom_plan', 'description', 'montant_total',
#             'date_debut', 'date_fin_prevue', 'statut'
#         ]
#         widgets = {
#             'contrat': forms.Select(attrs={
#                 'class': 'form-select select2',
#                 'data-placeholder': 'Sélectionner un contrat'
#             }),
#             'nom_plan': forms.TextInput(attrs={
#                 'class': 'form-control',
#                 'placeholder': 'Ex: Plan de paiement partiel - Janvier 2025'
#             }),
#             'description': forms.Textarea(attrs={
#                 'class': 'form-control',
#                 'rows': 3,
#                 'placeholder': 'Description du plan de paiement partiel'
#             }),
#             'montant_total': forms.NumberInput(attrs={
#                 'class': 'form-control',
#                 'step': '0.01',
#                 'min': '0.01'
#             }),
#             'date_debut': forms.DateInput(attrs={
#                 'class': 'form-control',
#                 'type': 'date'
#             }),
#             'date_fin_prevue': forms.DateInput(attrs={
#                 'class': 'form-control',
#                 'type': 'date'
#             }),
#             'statut': forms.Select(attrs={
#                 'class': 'form-select'
#             })
#         }
#     
#     def __init__(self, *args, **kwargs):
#         user = kwargs.pop('user', None)
#         super().__init__(*args, **kwargs)
#         
#         # Filtrer les contrats actifs
#         if user:
#             self.fields['contrat'].queryset = Contrat.objects.filter(
#                 is_deleted=False
#             ).select_related('locataire', 'propriete')
#         
#         # Ajouter des classes CSS
#         for field_name, field in self.fields.items():
#             if field_name not in self.Meta.widgets:
#                 field.widget.attrs.update({'class': 'form-control'})
#         
#         # Personnaliser les labels pour un vocabulaire plus simple
#         self.fields['nom_plan'].label = "Nom du Plan"
#         self.fields['montant_total'].label = "Montant à Payer"
#         self.fields['date_fin_prevue'].label = "Date Limite"
#         self.fields['statut'].label = "Statut"
#     
#     def clean(self):
#         cleaned_data = super().clean()
#         date_debut = cleaned_data.get('date_debut')
#         date_fin_prevue = cleaned_data.get('date_fin_prevue')
#         montant_total = cleaned_data.get('montant_total')
#         
#         # Vérifier que la date limite est après la date de début
#         if date_debut and date_fin_prevue:
#             if date_fin_prevue <= date_debut:
#                 raise ValidationError(
#                     "La date limite doit être après la date de début."
#                 )
#         
#         # Vérifier que le montant à payer est positif
#         if montant_total and montant_total <= 0:
#             raise ValidationError(
#                 "Le montant à payer doit être supérieur à zéro."
#             )
#         
#         return cleaned_data


# class EchelonPaiementForm(forms.ModelForm):
#     """Formulaire pour créer/modifier un échelon de paiement - DÉSACTIVÉ"""
#     
#     class Meta:
#         model = EchelonPaiement
#         fields = ['numero_echelon', 'montant', 'date_echeance', 'statut']
#         widgets = {
#             'numero_echelon': forms.NumberInput(attrs={
#                 'class': 'form-control',
#                 'min': '1'
#             }),
#             'montant': forms.NumberInput(attrs={
#                 'class': 'form-control',
#                 'step': '0.01',
#                 'min': '0.01'
#             }),
#             'date_echeance': forms.DateInput(attrs={
#                 'class': 'form-control',
#                 'type': 'date'
#             }),
#             'statut': forms.Select(attrs={
#                 'class': 'form-select'
#             })
#         }
#     
#     def __init__(self, *args, **kwargs):
#         plan = kwargs.pop('plan', None)
#         super().__init__(*args, **kwargs)
#         
#         if plan:
#             self.fields['numero_echelon'].initial = plan.echelons.count() + 1
#         
#         # Ajouter des classes CSS
#         for field_name, field in self.fields.items():
#             if field_name not in self.Meta.widgets:
#                 field.widget.attrs.update({'class': 'form-control'})
#     
#     def clean(self):
#         cleaned_data = super().clean()
#         numero_echelon = cleaned_data.get('numero_echelon')
#         montant = cleaned_data.get('montant')
#         date_echeance = cleaned_data.get('date_echeance')
#         
#         # Vérifier que le montant est positif
#         if montant and montant <= 0:
#             raise ValidationError(
#                 "Le montant de l'échelon doit être supérieur à zéro."
#             )
#         
#         # Vérifier que la date d'échéance est dans le futur
#         if date_echeance and date_echeance < timezone.now().date():
#             raise ValidationError(
#                 "La date d'échéance ne peut pas être dans le passé."
#             )
#         
#         return cleaned_data


# class PaiementPartielForm(forms.ModelForm):
#     """Formulaire pour créer un paiement partiel - DÉSACTIVÉ"""
#     
#     class Meta:
#         model = PaiementPartiel
#         fields = ['plan', 'echelon', 'montant', 'motif', 'description']
#         widgets = {
#             'plan': forms.Select(attrs={
#                 'class': 'form-select select2',
#                 'data-placeholder': 'Sélectionner un plan'
#             }),
#             'echelon': forms.Select(attrs={
#                 'class': 'form-select select2',
#                 'data-placeholder': 'Sélectionner un échelon (optionnel)'
#             }),
#             'montant': forms.NumberInput(attrs={
#                 'class': 'form-control',
#                 'step': '0.01',
#                 'min': '0.01'
#             }),
#             'motif': forms.TextInput(attrs={
#                 'class': 'form-control',
#                 'placeholder': 'Ex: Paiement partiel du loyer de janvier'
#             }),
#             'description': forms.Textarea(attrs={
#                 'class': 'form-control',
#                 'rows': 3,
#                 'placeholder': 'Description détaillée du paiement partiel'
#             })
#         }
#     
#     def __init__(self, *args, **kwargs):
#         user = kwargs.pop('user', None)
#         super().__init__(*args, **kwargs)
#         
#         # Filtrer les plans actifs - DÉSACTIVÉ
#         # if user:
#         #     self.fields['plan'].queryset = PlanPaiementPartiel.objects.filter(
#         #         is_deleted=False,
#         #         statut__in=['actif', 'suspendu']
#         #     ).select_related('contrat')
#         
#         # Ajouter des classes CSS
#         for field_name, field in self.fields.items():
#             if field_name not in self.Meta.widgets:
#                 field.widget.attrs.update({'class': 'form-control'})
#     
#     def clean(self):
#         cleaned_data = super().clean()
#         plan = cleaned_data.get('plan')
#         echelon = cleaned_data.get('echelon')
#         montant = cleaned_data.get('montant')
#         
#         # Vérifier que le montant est positif
#         if montant and montant <= 0:
#             raise ValidationError(
#                 "Le montant du paiement partiel doit être supérieur à zéro."
#             )
#         
#         # Vérifier que le montant ne dépasse pas le montant restant du plan
#         if plan and montant:
#             if montant > plan.montant_restant:
#                 raise ValidationError(
#                     f"Le montant du paiement partiel ({montant} FCFA) ne peut pas "
#                     f"dépasser le montant restant du plan ({plan.montant_restant} FCFA)."
#                 )
#         
#         # Vérifier que l'échelon appartient au plan
#         if plan and echelon:
#             if echelon.plan != plan:
#                 raise ValidationError(
#                     "L'échelon sélectionné n'appartient pas au plan sélectionné."
#                 )
#         
#         return cleaned_data
