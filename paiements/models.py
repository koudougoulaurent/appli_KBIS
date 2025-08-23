from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from django.contrib.auth import get_user_model
from django.utils import timezone
from contrats.models import Contrat
from proprietes.managers import NonDeletedManager

Utilisateur = get_user_model()


class ChargeDeductible(models.Model):
    """Modèle pour les charges avancées par le locataire et déductibles du loyer."""
    
    # Informations de base
    contrat = models.ForeignKey(
        Contrat,
        on_delete=models.PROTECT,
        related_name='charges_deductibles',
        verbose_name=_("Contrat")
    )
    montant = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        verbose_name=_("Montant de la charge")
    )
    
    # Description de la charge
    libelle = models.CharField(
        max_length=200,
        verbose_name=_("Libellé de la charge")
    )
    description = models.TextField(
        blank=True,
        verbose_name=_("Description détaillée")
    )
    
    # Type de charge
    type_charge = models.CharField(
        max_length=30,
        choices=[
            ('reparation', 'Réparation'),
            ('travaux', 'Travaux'),
            ('entretien', 'Entretien'),
            ('urgence', 'Urgence'),
            ('fourniture', 'Fourniture'),
            ('service', 'Service'),
            ('autre', 'Autre'),
        ],
        default='reparation',
        verbose_name=_("Type de charge")
    )
    
    # Statut de la charge
    statut = models.CharField(
        max_length=20,
        choices=[
            ('en_attente', 'En attente de validation'),
            ('validee', 'Validée'),
            ('deduite', 'Déduite du loyer'),
            ('refusee', 'Refusée'),
            ('annulee', 'Annulée'),
        ],
        default='en_attente',
        verbose_name=_("Statut")
    )
    
    # Dates importantes
    date_charge = models.DateField(
        verbose_name=_("Date de la charge")
    )
    date_creation = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Date de création")
    )
    date_validation = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Date de validation")
    )
    date_deduction = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Date de déduction")
    )
    
    # Justificatifs
    justificatif_url = models.URLField(
        blank=True,
        verbose_name=_("URL du justificatif")
    )
    facture_numero = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Numéro de facture")
    )
    fournisseur = models.CharField(
        max_length=150,
        blank=True,
        verbose_name=_("Fournisseur")
    )
    
    # Métadonnées
    date_modification = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Date de modification")
    )
    cree_par = models.ForeignKey(
        Utilisateur,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='charges_crees',
        verbose_name=_("Créé par")
    )
    valide_par = models.ForeignKey(
        Utilisateur,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='charges_validees',
        verbose_name=_("Validée par")
    )
    
    # Gestion de la suppression logique
    is_deleted = models.BooleanField(
        default=False,
        verbose_name='Supprimé logiquement'
    )
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Date de suppression'
    )
    deleted_by = models.ForeignKey(
        Utilisateur,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='charges_deleted',
        verbose_name='Supprimé par'
    )
    
    objects = NonDeletedManager()
    all_objects = models.Manager()
    
    class Meta:
        verbose_name = _("Charge déductible")
        verbose_name_plural = _("Charges déductibles")
        ordering = ['-date_charge']
    
    def __str__(self):
        return f"{self.libelle} - {self.contrat.numero_contrat} - {self.montant} XOF"
    
    def get_montant_formatted(self):
        """Retourne le montant formaté avec la devise."""
        return f"{self.montant} XOF"
    
    def get_statut_display_color(self):
        """Retourne la couleur CSS pour le statut."""
        colors = {
            'en_attente': 'warning',
            'validee': 'success',
            'deduite': 'info',
            'refusee': 'danger',
            'annulee': 'secondary',
        }
        return colors.get(self.statut, 'secondary')
    
    def peut_etre_validee(self):
        """Vérifie si la charge peut être validée."""
        return self.statut == 'en_attente'
    
    def peut_etre_deduite(self):
        """Vérifie si la charge peut être déduite du loyer."""
        return self.statut == 'validee'
    
    def valider_charge(self, utilisateur):
        """Valide la charge."""
        if self.peut_etre_validee():
            self.statut = 'validee'
            self.date_validation = timezone.now()
            self.valide_par = utilisateur
            self.save()
            return True
        return False
    
    def deduire_du_loyer(self, utilisateur):
        """Marque la charge comme déduite du loyer."""
        if self.peut_etre_deduite():
            self.statut = 'deduite'
            self.date_deduction = timezone.now()
            self.save()
            return True
        return False


class Paiement(models.Model):
    """Modèle pour les paiements de loyer avec support des paiements partiels."""
    
    # Numéro unique professionnel
    numero_paiement = models.CharField(
        max_length=50,
        unique=True,
        null=True,
        blank=True,
        verbose_name=_("Numéro Paiement"),
        help_text=_("Numéro unique professionnel du paiement")
    )
    
    # Identifiant unique
    reference_paiement = models.CharField(
        max_length=30,
        unique=True,
        null=True,
        blank=True,
        verbose_name=_("Référence Paiement"),
        help_text=_("Référence unique pour identifier le paiement")
    )
    
    # Informations de base
    contrat = models.ForeignKey(
        Contrat,
        on_delete=models.PROTECT,
        related_name='paiements',
        verbose_name=_("Contrat")
    )
    montant = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        verbose_name=_("Montant")
    )
    
    # Informations sur les charges déductibles
    montant_charges_deduites = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_("Montant des charges déduites")
    )
    montant_net_paye = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Montant net payé (après déductions)")
    )
    
    # Gestion des paiements partiels
    est_paiement_partiel = models.BooleanField(
        default=False,
        verbose_name=_("Paiement partiel")
    )
    mois_paye = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Mois payé"),
        help_text=_("Mois pour lequel ce paiement est effectué")
    )
    montant_du_mois = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Montant dû pour le mois"),
        help_text=_("Montant total dû pour le mois (loyer + charges)")
    )
    montant_restant_du = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_("Montant restant dû"),
        help_text=_("Montant restant à payer pour ce mois")
    )
    
    # Type et statut
    type_paiement = models.CharField(
        max_length=20,
        choices=[
            ('loyer', 'Loyer'),
            ('charges', 'Charges'),
            ('caution', 'Caution'),
            ('avance_loyer', 'Avance de loyer'),
            ('depot_garantie', 'Dépôt de garantie'),
            ('regularisation', 'Régularisation'),
            ('paiement_partiel', 'Paiement partiel'),
            ('autre', 'Autre'),
        ],
        default='loyer',
        verbose_name=_("Type de paiement")
    )
    statut = models.CharField(
        max_length=20,
        choices=[
            ('en_attente', 'En attente'),
            ('valide', 'Validé'),
            ('refuse', 'Refusé'),
            ('annule', 'Annulé'),
        ],
        default='en_attente',
        verbose_name=_("Statut")
    )
    
    # Mode de paiement
    mode_paiement = models.CharField(
        max_length=20,
        choices=[
            ('virement', 'Virement bancaire'),
            ('cheque', 'Chèque'),
            ('especes', 'Espèces'),
            ('prelevement', 'Prélèvement automatique'),
            ('carte', 'Carte bancaire'),
        ],
        verbose_name=_("Mode de paiement")
    )
    
    # Dates
    date_paiement = models.DateField(verbose_name=_("Date de paiement"))
    date_encaissement = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Date d'encaissement")
    )
    
    # Informations bancaires
    numero_cheque = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_("Numéro de chèque")
    )
    reference_virement = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Référence virement")
    )
    
    # Métadonnées
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name=_("Date de création"))
    date_modification = models.DateTimeField(auto_now=True, verbose_name=_("Date de modification"))
    notes = models.TextField(blank=True, verbose_name=_("Notes"))
    
    # Relations
    cree_par = models.ForeignKey(
        Utilisateur,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='paiements_crees',
        verbose_name=_("Créé par")
    )
    valide_par = models.ForeignKey(
        Utilisateur,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='paiements_valides',
        verbose_name=_("Validé par")
    )
    
    is_deleted = models.BooleanField(default=False, verbose_name='Supprimé logiquement')
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name='Date de suppression')
    deleted_by = models.ForeignKey(Utilisateur, null=True, blank=True, on_delete=models.SET_NULL, related_name='paiement_deleted', verbose_name='Supprimé par')
    
    objects = NonDeletedManager()
    all_objects = models.Manager()
    
    class Meta:
        verbose_name = _("Paiement")
        verbose_name_plural = _("Paiements")
        ordering = ['-date_paiement', '-date_creation']
    
    def __str__(self):
        return f"Paiement {self.reference_paiement} - {self.contrat.numero_contrat} - {self.montant} XOF"
    
    def save(self, *args, **kwargs):
        if not self.reference_paiement:
            self.reference_paiement = self.generate_reference_paiement()
        
        # Calculer automatiquement le montant net payé
        if self.montant_net_paye is None:
            self.montant_net_paye = self.montant - self.montant_charges_deduites
        
        super().save(*args, **kwargs)
    
    def generate_reference_paiement(self):
        """Génère une référence unique pour le paiement."""
        from django.utils.crypto import get_random_string
        prefix = "PAY"
        while True:
            code = f"{prefix}-{get_random_string(8, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')}"
            if not Paiement.objects.filter(reference_paiement=code).exists():
                return code
    
    def get_locataire(self):
        """Retourne le locataire associé à ce paiement."""
        return self.contrat.locataire
    
    def get_bailleur(self):
        """Retourne le bailleur associé à ce paiement."""
        return self.contrat.propriete.bailleur
    
    def get_propriete(self):
        """Retourne la propriété associée à ce paiement."""
        return self.contrat.propriete
    
    def get_code_locataire(self):
        """Retourne le code unique du locataire."""
        return self.get_locataire().code_locataire
    
    def get_code_bailleur(self):
        """Retourne le code unique du bailleur."""
        return self.get_bailleur().code_bailleur
    
    def get_nom_complet_locataire(self):
        """Retourne le nom complet du locataire."""
        return self.get_locataire().get_nom_complet()
    
    def get_nom_complet_bailleur(self):
        """Retourne le nom complet du bailleur."""
        return self.get_bailleur().get_nom_complet()
    
    def get_adresse_propriete(self):
        """Retourne l'adresse de la propriété."""
        return self.get_propriete().adresse
    
    def get_ville_propriete(self):
        """Retourne la ville de la propriété."""
        return self.get_propriete().ville
    
    def get_montant_formatted(self):
        """Retourne le montant formaté avec la devise."""
        return f"{self.montant} XOF"
    
    def get_montant_net_formatted(self):
        """Retourne le montant net formaté avec la devise."""
        return f"{self.montant_net_paye} XOF"
    
    def get_montant_charges_formatted(self):
        """Retourne le montant des charges formaté avec la devise."""
        return f"{self.montant_charges_deduites} XOF"
    
    def get_statut_display_color(self):
        """Retourne la couleur CSS pour le statut."""
        colors = {
            'en_attente': 'warning',
            'valide': 'success',
            'refuse': 'danger',
            'annule': 'secondary',
        }
        return colors.get(self.statut, 'secondary')
    
    def get_type_display_icon(self):
        """Retourne l'icône Bootstrap pour le type de paiement."""
        icons = {
            'loyer': 'bi-house',
            'charges': 'bi-lightning',
            'caution': 'bi-shield',
            'avance_loyer': 'bi-piggy-bank',
            'depot_garantie': 'bi-shield-check',
            'regularisation': 'bi-arrow-repeat',
            'paiement_partiel': 'bi-currency-exchange',
            'autre': 'bi-coin',
        }
        return icons.get(self.type_paiement, 'bi-coin')
    
    def get_mode_display_icon(self):
        """Retourne l'icône Bootstrap pour le mode de paiement."""
        icons = {
            'virement': 'bi-bank',
            'cheque': 'bi-receipt',
            'especes': 'bi-cash',
            'prelevement': 'bi-arrow-repeat',
            'carte': 'bi-credit-card',
        }
        return icons.get(self.mode_paiement, 'bi-coin')
    
    def peut_etre_valide(self):
        """Vérifie si le paiement peut être validé."""
        return self.statut == 'en_attente'
    
    def valider_paiement(self, utilisateur):
        """Valide le paiement et génère automatiquement une quittance."""
        if self.peut_etre_valide():
            self.statut = 'valide'
            self.date_encaissement = timezone.now().date()
            self.valide_par = utilisateur
            self.save()
            
            # Générer automatiquement une quittance de paiement
            self.generer_quittance(utilisateur)
            
            return True
        return False
    
    def generer_quittance(self, utilisateur):
        """Génère automatiquement une quittance de paiement."""
        from .models import QuittancePaiement
        
        # Vérifier si une quittance existe déjà
        if not hasattr(self, 'quittance'):
            QuittancePaiement.objects.create(
                paiement=self,
                cree_par=utilisateur
            )
    
    def peut_etre_annule(self):
        """Vérifie si le paiement peut être annulé."""
        return self.statut in ['en_attente', 'valide']
    
    def annuler_paiement(self, utilisateur, raison=""):
        """Annule le paiement."""
        if self.peut_etre_annule():
            self.statut = 'annule'
            self.notes = f"Annulé par {utilisateur.get_full_name()}. Raison: {raison}"
            self.save()
            return True
        return False
    
    def get_type_paiement_display(self):
        """Retourne le type de paiement avec une description complète."""
        if self.type_paiement == 'caution':
            return f"Caution - {self.get_montant_formatted()}"
        elif self.type_paiement == 'avance_loyer':
            return f"Avance de loyer - {self.get_montant_formatted()}"
        elif self.type_paiement == 'depot_garantie':
            return f"Dépôt de garantie - {self.get_montant_formatted()}"
        else:
            # Pour les autres types, utiliser le nom du type directement
            # ou retourner une description par défaut
            type_names = {
                'loyer': 'Loyer',
                'charges': 'Charges',
                'autres': 'Autres',
            }
            return type_names.get(self.type_paiement, self.type_paiement)


class QuittancePaiement(models.Model):
    """Modèle pour les quittances de paiement générées automatiquement."""
    
    # Numéro unique de la quittance
    numero_quittance = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_("Numéro de quittance"),
        help_text=_("Numéro unique de la quittance")
    )
    
    # Paiement associé
    paiement = models.OneToOneField(
        Paiement,
        on_delete=models.CASCADE,
        related_name='quittance',
        verbose_name=_("Paiement")
    )
    
    # Informations de la quittance
    date_emission = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Date d'émission")
    )
    date_impression = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Date d'impression")
    )
    
    # Statut de la quittance
    statut = models.CharField(
        max_length=20,
        choices=[
            ('generee', 'Générée'),
            ('imprimee', 'Imprimée'),
            ('envoyee', 'Envoyée'),
            ('archivée', 'Archivée'),
        ],
        default='generee',
        verbose_name=_("Statut")
    )
    
    # Métadonnées
    cree_par = models.ForeignKey(
        Utilisateur,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='quittances_crees',
        verbose_name=_("Créé par")
    )
    
    # Gestion de la suppression logique
    is_deleted = models.BooleanField(
        default=False,
        verbose_name='Supprimé logiquement'
    )
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Date de suppression'
    )
    deleted_by = models.ForeignKey(
        Utilisateur,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='quittances_deleted',
        verbose_name='Supprimé par'
    )
    
    objects = NonDeletedManager()
    all_objects = models.Manager()
    
    class Meta:
        verbose_name = _("Quittance de paiement")
        verbose_name_plural = _("Quittances de paiement")
        ordering = ['-date_emission']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.numero_quittance:
            self.numero_quittance = self.generate_numero_quittance()
    
    def __str__(self):
        return f"Quittance {self.numero_quittance} - {self.paiement.reference_paiement}"
    
    def generate_numero_quittance(self):
        """Génère un numéro unique pour la quittance."""
        from django.utils.crypto import get_random_string
        prefix = "QUIT"
        while True:
            code = f"{prefix}-{get_random_string(8, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')}"
            if not QuittancePaiement.objects.filter(numero_quittance=code).exists():
                return code
    
    def get_locataire(self):
        """Retourne le locataire associé à cette quittance."""
        return self.paiement.get_locataire()
    
    def get_bailleur(self):
        """Retourne le bailleur associé à cette quittance."""
        return self.paiement.get_bailleur()
    
    def get_propriete(self):
        """Retourne la propriété associée à cette quittance."""
        return self.paiement.get_propriete()
    
    def get_contrat(self):
        """Retourne le contrat associé à cette quittance."""
        return self.paiement.contrat
    
    def marquer_imprimee(self):
        """Marque la quittance comme imprimée."""
        self.statut = 'imprimee'
        self.date_impression = timezone.now()
        self.save()
    
    def marquer_envoyee(self):
        """Marque la quittance comme envoyée."""
        self.statut = 'envoyee'
        self.save()
    
    def marquer_archivee(self):
        """Marque la quittance comme archivée."""
        self.statut = 'archivée'
        self.save()
    
    def get_statut_display_color(self):
        """Retourne la couleur CSS pour le statut."""
        colors = {
            'generee': 'info',
            'imprimee': 'success',
            'envoyee': 'primary',
            'archivée': 'secondary',
        }
        return colors.get(self.statut, 'secondary')


class RetraitBailleur(models.Model):
    """Modèle pour les retraits des bailleurs avec gestion des charges déductibles."""
    
    # Informations de base
    bailleur = models.ForeignKey(
        'proprietes.Bailleur',
        on_delete=models.PROTECT,
        related_name='retraits_bailleur',
        verbose_name=_("Bailleur")
    )
    
    # Période concernée
    mois_retrait = models.DateField(
        verbose_name=_("Mois de retrait"),
        help_text=_("Mois pour lequel le retrait est effectué")
    )
    
    # Montants
    montant_loyers_bruts = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        verbose_name=_("Montant total des loyers bruts")
    )
    montant_charges_deductibles = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name=_("Montant total des charges déductibles")
    )
    montant_net_a_payer = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name=_("Montant net à payer (après déduction des charges)")
    )
    
    # Type et statut
    type_retrait = models.CharField(
        max_length=20,
        choices=[
            ('mensuel', 'Retrait mensuel'),
            ('trimestriel', 'Retrait trimestriel'),
            ('annuel', 'Retrait annuel'),
            ('exceptionnel', 'Retrait exceptionnel'),
        ],
        default='mensuel',
        verbose_name=_("Type de retrait")
    )
    statut = models.CharField(
        max_length=20,
        choices=[
            ('en_attente', 'En attente'),
            ('valide', 'Validé'),
            ('paye', 'Payé'),
            ('annule', 'Annulé'),
        ],
        default='en_attente',
        verbose_name=_("Statut")
    )
    
    # Mode de retrait
    mode_retrait = models.CharField(
        max_length=20,
        choices=[
            ('virement', 'Virement bancaire'),
            ('cheque', 'Chèque'),
            ('especes', 'Espèces'),
        ],
        verbose_name=_("Mode de retrait")
    )
    
    # Dates
    date_demande = models.DateField(verbose_name=_("Date de demande"))
    date_versement = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Date de versement")
    )
    
    # Informations bancaires
    numero_cheque = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_("Numéro de chèque")
    )
    reference_virement = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Référence virement")
    )
    
    # Métadonnées
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name=_("Date de création"))
    date_modification = models.DateTimeField(auto_now=True, verbose_name=_("Date de modification"))
    notes = models.TextField(blank=True, verbose_name=_("Notes"))
    
    # Relations
    cree_par = models.ForeignKey(
        Utilisateur,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='retraits_crees',
        verbose_name=_("Créé par")
    )
    valide_par = models.ForeignKey(
        Utilisateur,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='retraits_valides',
        verbose_name=_("Validé par")
    )
    paye_par = models.ForeignKey(
        Utilisateur,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='retraits_payes',
        verbose_name=_("Payé par")
    )
    
    # SÉCURITÉ ET AUDIT - NOUVEAU
    # Horodatage des actions critiques
    date_validation = models.DateTimeField(
        null=True, 
        blank=True, 
        verbose_name=_("Date de validation")
    )
    date_paiement = models.DateTimeField(
        null=True, 
        blank=True, 
        verbose_name=_("Date de paiement")
    )
    date_annulation = models.DateTimeField(
        null=True, 
        blank=True, 
        verbose_name=_("Date d'annulation")
    )
    
    # Motif des actions critiques
    motif_annulation = models.TextField(
        blank=True, 
        null=True, 
        verbose_name=_("Motif de l'annulation")
    )
    motif_modification = models.TextField(
        blank=True, 
        null=True, 
        verbose_name=_("Motif de la modification")
    )
    
    # Contrôles de sécurité
    peut_etre_modifie = models.BooleanField(
        default=True, 
        verbose_name=_("Peut être modifié"),
        help_text=_("Désactivé une fois validé")
    )
    peut_etre_annule = models.BooleanField(
        default=True, 
        verbose_name=_("Peut être annulé"),
        help_text=_("Désactivé une fois payé")
    )
    
    # Hash de sécurité pour vérifier l'intégrité
    hash_securite = models.CharField(
        max_length=64, 
        blank=True, 
        null=True, 
        verbose_name=_("Hash de sécurité")
    )
    
    # Niveau d'autorisation requis pour les modifications
    NIVEAU_AUTORISATION_CHOICES = [
        ('standard', 'Standard'),
        ('superviseur', 'Superviseur'),
        ('manager', 'Manager'),
        ('admin', 'Administrateur'),
        ('system', 'Système uniquement'),
    ]
    niveau_autorisation_modification = models.CharField(
        max_length=20,
        choices=NIVEAU_AUTORISATION_CHOICES,
        default='standard',
        verbose_name=_("Niveau d'autorisation requis pour modification")
    )
    
    # Lien avec les charges déductibles
    charges_deductibles = models.ManyToManyField(
        'ChargeDeductible',
        through='RetraitChargeDeductible',
        related_name='retraits_bailleur',
        verbose_name=_("Charges déductibles")
    )
    
    # Lien avec les paiements concernés
    paiements_concernes = models.ManyToManyField(
        'Paiement',
        related_name='retraits_bailleur',
        verbose_name=_("Paiements concernés")
    )
    
    is_deleted = models.BooleanField(default=False, verbose_name='Supprimé logiquement')
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name='Date de suppression')
    deleted_by = models.ForeignKey(
        Utilisateur,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='retraits_bailleur_supprimes',
        verbose_name='Supprimé par'
    )
    
    objects = NonDeletedManager()
    all_objects = models.Manager()
    
    class Meta:
        verbose_name = _("Retrait bailleur")
        verbose_name_plural = _("Retraits bailleur")
        ordering = ['-mois_retrait']
        unique_together = ['bailleur', 'mois_retrait']
        indexes = [
            models.Index(fields=['bailleur', 'mois_retrait']),
            models.Index(fields=['statut']),
            models.Index(fields=['date_demande']),
        ]
    
    def __str__(self):
        return f"Retrait {self.bailleur} - {self.mois_retrait.strftime('%B %Y')} - {self.montant_net_a_payer} XOF"
    
    def save(self, *args, **kwargs):
        """Override save pour calculer automatiquement le montant net et générer le hash de sécurité."""
        # S'assurer que les montants sont des Decimal
        from decimal import Decimal
        if isinstance(self.montant_loyers_bruts, str):
            self.montant_loyers_bruts = Decimal(self.montant_loyers_bruts)
        if isinstance(self.montant_charges_deductibles, str):
            self.montant_charges_deductibles = Decimal(self.montant_charges_deductibles)
        
        # Calculer le montant net
        if self.montant_loyers_bruts > 0:
            self.montant_net_a_payer = self.montant_loyers_bruts - self.montant_charges_deductibles
        
        # Générer le hash de sécurité
        self.generer_hash_securite()
        
        super().save(*args, **kwargs)
    
    def generer_hash_securite(self):
        """Génère un hash de sécurité pour vérifier l'intégrité des données."""
        import hashlib
        data_string = f"{self.id}{self.montant_loyers_bruts}{self.montant_charges_deductibles}{self.statut}{self.date_creation}"
        self.hash_securite = hashlib.sha256(data_string.encode()).hexdigest()
    
    def verifier_integrite(self):
        """Vérifie l'intégrité des données en comparant avec le hash de sécurité."""
        if not self.hash_securite:
            return False
        import hashlib
        data_string = f"{self.id}{self.montant_loyers_bruts}{self.montant_charges_deductibles}{self.statut}{self.date_creation}"
        current_hash = hashlib.sha256(data_string.encode()).hexdigest()
        return current_hash == self.hash_securite
    
    def valider_retrait(self, utilisateur, force=False):
        """
        Valide un retrait avec contrôles de sécurité.
        Une fois validé, le retrait ne peut plus être modifié sauf par un administrateur.
        """
        from django.utils import timezone
        
        # Vérifier que l'utilisateur a les droits
        if not force and not self.peut_etre_valide(utilisateur):
            raise PermissionError("Vous n'avez pas les droits pour valider ce retrait")
        
        # Vérifier l'intégrité des données
        if not self.verifier_integrite():
            raise ValueError("L'intégrité des données du retrait est compromise")
        
        # Mettre à jour le statut
        self.statut = 'valide'
        self.valide_par = utilisateur
        self.date_validation = timezone.now()
        
        # Désactiver la modification (sauf pour les administrateurs)
        self.peut_etre_modifie = False
        self.niveau_autorisation_modification = 'admin'
        
        # Sauvegarder
        self.save()
    
        # Créer un log d'audit
        self.creer_log_audit('validation', utilisateur, f"Retrait validé par {utilisateur.get_nom_complet()}")
    
    def marquer_paye(self, utilisateur, force=False):
        """
        Marque un retrait comme payé avec contrôles de sécurité.
        Une fois payé, le retrait ne peut plus être annulé sauf par le système.
        """
        from django.utils import timezone
        
        # Vérifier que l'utilisateur a les droits
        if not force and not self.peut_etre_paye(utilisateur):
            raise PermissionError("Vous n'avez pas les droits pour marquer ce retrait comme payé")
        
        # Vérifier que le retrait est validé
        if self.statut != 'valide':
            raise ValueError("Seuls les retraits validés peuvent être marqués comme payés")
        
        # Mettre à jour le statut
        self.statut = 'paye'
        self.paye_par = utilisateur
        self.date_paiement = timezone.now()
        self.date_versement = timezone.now().date()
        
        # Désactiver l'annulation (sauf pour le système)
        self.peut_etre_annule = False
        self.niveau_autorisation_modification = 'system'
        
        # Sauvegarder
        self.save()
    
        # Créer un log d'audit
        self.creer_log_audit('paiement', utilisateur, f"Retrait marqué comme payé par {utilisateur.get_nom_complet()}")
    
    def annuler_retrait(self, utilisateur, motif, force=False):
        """
        Annule un retrait avec contrôles de sécurité stricts.
        Seuls les administrateurs peuvent annuler un retrait validé.
        """
        from django.utils import timezone
        
        # Vérifier que l'utilisateur a les droits
        if not force and not self.peut_etre_annule(utilisateur):
            raise PermissionError("Vous n'avez pas les droits pour annuler ce retrait")
        
        # Vérifier que le retrait peut être annulé
        if not self.peut_etre_annule:
            raise ValueError("Ce retrait ne peut plus être annulé")
        
        # Si le retrait est validé, seuls les administrateurs peuvent l'annuler
        if self.statut == 'valide' and not self.utilisateur_est_admin(utilisateur):
            raise PermissionError("Seuls les administrateurs peuvent annuler un retrait validé")
        
        # Mettre à jour le statut
        self.statut = 'annule'
        self.date_annulation = timezone.now()
        self.motif_annulation = motif
        
        # Désactiver toutes les modifications
        self.peut_etre_modifie = False
        self.peut_etre_annule = False
        self.niveau_autorisation_modification = 'system'
        
        # Sauvegarder
        self.save()
        
        # Créer un log d'audit
        self.creer_log_audit('annulation', utilisateur, f"Retrait annulé par {utilisateur.get_nom_complet()}. Motif: {motif}")
    
    def peut_etre_valide(self, utilisateur):
        """Vérifie si l'utilisateur peut valider ce retrait."""
        if self.statut != 'en_attente':
            return False
        return self.utilisateur_est_autorise(utilisateur, 'standard')
    
    def peut_etre_paye(self, utilisateur):
        """Vérifie si l'utilisateur peut marquer ce retrait comme payé."""
        if self.statut != 'valide':
            return False
        return self.utilisateur_est_autorise(utilisateur, 'superviseur')
    
    def peut_etre_annule(self, utilisateur):
        """Vérifie si l'utilisateur peut annuler ce retrait."""
        if not self.peut_etre_annule:
            return False
        if self.statut == 'paye':
            return False
        return self.utilisateur_est_autorise(utilisateur, 'standard')
    
    def get_mode_display_icon(self):
        """Retourne l'icône Bootstrap pour le mode de retrait."""
        icons = {
            'virement': 'bi-bank',
            'cheque': 'bi-receipt',
            'especes': 'bi-cash-coin',
        }
        return icons.get(self.mode_retrait, 'bi-currency-exchange')
    
    def get_mode_retrait_display(self):
        """Retourne le nom d'affichage du mode de retrait."""
        modes = {
            'virement': 'Virement bancaire',
            'cheque': 'Chèque',
            'especes': 'Espèces',
        }
        return modes.get(self.mode_retrait, self.mode_retrait)
    
    def get_type_retrait_display(self):
        """Retourne le nom d'affichage du type de retrait."""
        types = {
            'mensuel': 'Retrait mensuel',
            'trimestriel': 'Retrait trimestriel',
            'annuel': 'Retrait annuel',
            'exceptionnel': 'Retrait exceptionnel',
        }
        return types.get(self.type_retrait, self.type_retrait)
    
    def get_statut_display(self):
        """Retourne le nom d'affichage du statut."""
        statuts = {
            'en_attente': 'En attente',
            'valide': 'Validé',
            'paye': 'Payé',
            'annule': 'Annulé',
        }
        return statuts.get(self.statut, self.statut)
    
    def get_statut_display_color(self):
        """Retourne la couleur CSS pour le statut."""
        colors = {
            'en_attente': 'warning',
            'valide': 'success',
            'paye': 'info',
            'annule': 'danger',
        }
        return colors.get(self.statut, 'secondary')
    
    def peut_etre_edite(self):
        """Vérifie si le retrait peut être édité."""
        return self.peut_etre_modifie and self.statut == 'en_attente'
    
    def utilisateur_est_autorise(self, utilisateur, niveau_requis):
        """Vérifie si l'utilisateur a le niveau d'autorisation requis."""
        niveaux = {
            'standard': 1,
            'superviseur': 2,
            'manager': 3,
            'admin': 4,
            'system': 5
        }
        
        # Vérifier le niveau de l'utilisateur
        niveau_utilisateur = self.get_niveau_utilisateur(utilisateur)
        return niveaux.get(niveau_utilisateur, 0) >= niveaux.get(niveau_requis, 0)
    
    def utilisateur_est_admin(self, utilisateur):
        """Vérifie si l'utilisateur est un administrateur."""
        return self.utilisateur_est_autorise(utilisateur, 'admin')
    
    def get_niveau_utilisateur(self, utilisateur):
        """Détermine le niveau d'autorisation de l'utilisateur."""
        # Logique pour déterminer le niveau de l'utilisateur
        # À adapter selon votre système de permissions
        if utilisateur.is_superuser:
            return 'admin'
        elif hasattr(utilisateur, 'groupe') and utilisateur.groupe:
            if 'admin' in utilisateur.groupe.nom.lower():
                return 'admin'
            elif 'manager' in utilisateur.groupe.nom.lower():
                return 'manager'
            elif 'superviseur' in utilisateur.groupe.nom.lower():
                return 'superviseur'
        return 'standard'
    
    def creer_log_audit(self, action, utilisateur, description):
        """Crée un log d'audit pour tracer toutes les actions critiques."""
        try:
            from core.models import LogAudit
            LogAudit.objects.create(
                modele='RetraitBailleur',
                instance_id=self.id,
                action=action,
                utilisateur=utilisateur,
                description=description,
                donnees_avant={},
                donnees_apres=self.to_dict()
            )
        except Exception as e:
            # En cas d'erreur, on log mais on ne bloque pas l'opération
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Erreur lors de la création du log d'audit: {e}")
    
    def to_dict(self):
        """Convertit le retrait en dictionnaire pour l'audit."""
        return {
            'id': self.id,
            'statut': self.statut,
            'montant_loyers_bruts': str(self.montant_loyers_bruts),
            'montant_charges_deductibles': str(self.montant_charges_deductibles),
            'montant_net_a_payer': str(self.montant_net_a_payer),
            'date_validation': self.date_validation.isoformat() if self.date_validation else None,
            'date_paiement': self.date_paiement.isoformat() if self.date_paiement else None,
            'hash_securite': self.hash_securite
        }


class RetraitChargeDeductible(models.Model):
    """Modèle de liaison entre RetraitBailleur et ChargeDeductible."""
    
    retrait_bailleur = models.ForeignKey(
        RetraitBailleur,
        on_delete=models.CASCADE,
        verbose_name=_("Retrait bailleur")
    )
    charge_deductible = models.ForeignKey(
        ChargeDeductible,
        on_delete=models.CASCADE,
        verbose_name=_("Charge déductible")
    )
    date_ajout = models.DateTimeField(auto_now_add=True, verbose_name=_("Date d'ajout"))
    
    class Meta:
        verbose_name = _("Charge déductible du retrait")
        verbose_name_plural = _("Charges déductibles du retrait")
        unique_together = ['retrait_bailleur', 'charge_deductible']
    
    def __str__(self):
        return f"{self.retrait_bailleur} - {self.charge_deductible}"


class RecuRetrait(models.Model):
    """Modèle pour les reçus de retrait des bailleurs."""
    
    retrait_bailleur = models.OneToOneField(
        RetraitBailleur,
        on_delete=models.CASCADE,
        related_name='recu_retrait',
        verbose_name=_("Retrait bailleur")
    )
    numero_recu = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_("Numéro de reçu")
    )
    date_emission = models.DateTimeField(auto_now_add=True, verbose_name=_("Date d'émission"))
    
    # Informations d'impression
    imprime = models.BooleanField(default=False, verbose_name=_("Imprimé"))
    date_impression = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Date d'impression")
    )
    imprime_par = models.ForeignKey(
        Utilisateur,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recus_retrait_imprimes',
        verbose_name=_("Imprimé par")
    )
    
    # Informations de génération
    genere_automatiquement = models.BooleanField(
        default=True,
        verbose_name=_("Généré automatiquement")
    )
    
    # Options d'impression
    format_impression = models.CharField(
        max_length=20,
        choices=[
            ('a5', 'A5'),
            ('a4', 'A4'),
        ],
        default='a5',
        verbose_name=_("Format d'impression")
    )
    
    # Métadonnées
    notes_internes = models.TextField(blank=True, verbose_name=_("Notes internes"))
    
    class Meta:
        verbose_name = _("Reçu de retrait")
        verbose_name_plural = _("Reçus de retrait")
        ordering = ['-date_emission']
    
    def __str__(self):
        return f"Reçu retrait {self.numero_recu} - {self.retrait_bailleur.bailleur}"
    
    def save(self, *args, **kwargs):
        if not self.numero_recu:
            self.numero_recu = self._generer_numero_recu()
        super().save(*args, **kwargs)
    
    def _generer_numero_recu(self):
        """Génère un numéro de reçu unique."""
        from datetime import datetime
        from django.utils.crypto import get_random_string
        
        prefix = "RET"
        date_str = datetime.now().strftime("%Y%m")
        random_str = get_random_string(6, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
        
        numero = f"{prefix}-{date_str}-{random_str}"
        
        # Vérifier l'unicité
        while RecuRetrait.objects.filter(numero_recu=numero).exists():
            random_str = get_random_string(6, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
            numero = f"{prefix}-{date_str}-{random_str}"
        
        return numero
    
    def marquer_imprime(self, utilisateur):
        """Marque le reçu comme imprimé."""
        self.imprime = True
        self.date_impression = timezone.now()
        self.imprime_par = utilisateur
        self.save()
    
    def get_bailleur(self):
        """Retourne le bailleur associé à ce reçu."""
        return self.retrait_bailleur.bailleur
    
    def get_montant_total(self):
        """Retourne le montant total du retrait."""
        return self.retrait_bailleur.montant_net_a_payer
    
    def get_montant_formatted(self):
        """Retourne le montant formaté."""
        return f"{self.get_montant_total()} XOF"
    
    def get_date_retrait(self):
        """Retourne la date du retrait."""
        return self.retrait_bailleur.mois_retrait
    
    def get_statut_retrait(self):
        """Retourne le statut du retrait."""
        return self.retrait_bailleur.get_statut_display()


class TableauBordFinancier(models.Model):
    """Modèle pour le tableau de bord financier professionnel - Intégré dans le module paiements."""
    
    # Informations de base
    nom = models.CharField(
        max_length=100, 
        verbose_name=_("Nom du tableau de bord"),
        help_text=_("Nom descriptif du tableau de bord")
    )
    description = models.TextField(
        blank=True, 
        verbose_name=_("Description"),
        help_text=_("Description détaillée du tableau de bord")
    )
    
    # Relations
    proprietes = models.ManyToManyField(
        'proprietes.Propriete',
        verbose_name=_("Propriétés incluses"),
        help_text=_("Propriétés à inclure dans ce tableau de bord"),
        blank=True
    )
    bailleurs = models.ManyToManyField(
        'proprietes.Bailleur',
        blank=True,
        verbose_name=_("Bailleurs inclus"),
        help_text=_("Bailleurs à inclure dans ce tableau de bord")
    )
    
    # Paramètres d'affichage
    afficher_revenus = models.BooleanField(
        default=True,
        verbose_name=_("Afficher les revenus"),
        help_text=_("Inclure les revenus dans le tableau de bord")
    )
    afficher_charges = models.BooleanField(
        default=True,
        verbose_name=_("Afficher les charges"),
        help_text=_("Inclure les charges dans le tableau de bord")
    )
    afficher_benefices = models.BooleanField(
        default=True,
        verbose_name=_("Afficher les bénéfices"),
        help_text=_("Inclure les bénéfices dans le tableau de bord")
    )
    afficher_taux_occupation = models.BooleanField(
        default=True,
        verbose_name=_("Afficher le taux d'occupation"),
        help_text=_("Inclure le taux d'occupation dans le tableau de bord")
    )
    
    # Période d'analyse
    PERIODE_CHOICES = [
        ('mensuel', 'Mensuel'),
        ('trimestriel', 'Trimestriel'),
        ('annuel', 'Annuel'),
        ('personnalise', 'Personnalisé'),
    ]
    periode = models.CharField(
        max_length=20,
        choices=PERIODE_CHOICES,
        default='mensuel',
        verbose_name=_("Période d'analyse")
    )
    date_debut_personnalisee = models.DateField(
        blank=True,
        null=True,
        verbose_name=_("Date de début (période personnalisée)")
    )
    date_fin_personnalisee = models.DateField(
        blank=True,
        null=True,
        verbose_name=_("Date de fin (période personnalisée)")
    )
    
    # Configuration avancée
    seuil_alerte = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name=_("Seuil d'alerte"),
        help_text=_("Montant seuil pour déclencher des alertes")
    )
    devise = models.CharField(
        max_length=10,
        default='XOF',
        verbose_name=_("Devise"),
        help_text=_("Devise utilisée pour les montants")
    )
    couleur_theme = models.CharField(
        max_length=7,
        default='#007bff',
        verbose_name=_("Couleur du thème"),
        help_text=_("Couleur principale du tableau de bord (format hexadécimal)")
    )
    
    # Métadonnées
    date_creation = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Date de création")
    )
    date_modification = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Date de modification")
    )
    cree_par = models.ForeignKey(
        Utilisateur,
        on_delete=models.CASCADE,
        verbose_name=_("Créé par"),
        related_name='tableaux_bord_crees'
    )
    actif = models.BooleanField(
        default=True,
        verbose_name=_("Tableau actif"),
        help_text=_("Désactiver pour masquer ce tableau de bord")
    )
    
    class Meta:
        verbose_name = _("Tableau de bord financier")
        verbose_name_plural = _("Tableaux de bord financiers")
        ordering = ['-date_creation']
        permissions = [
            ("view_tableau_bord_financier", "Peut voir les tableaux de bord financiers"),
            ("add_tableau_bord_financier", "Peut créer des tableaux de bord financiers"),
            ("change_tableau_bord_financier", "Peut modifier les tableaux de bord financiers"),
            ("delete_tableau_bord_financier", "Peut supprimer les tableaux de bord financiers"),
        ]
    
    def __str__(self):
        return f"{self.nom} ({self.get_periode_display()})"
    
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('paiements:tableau_bord_detail', kwargs={'pk': self.pk})
    
    def get_periode_analyse(self):
        """Retourne la période d'analyse pour le calcul."""
        from django.utils import timezone
        now = timezone.now()
        
        if self.periode == 'mensuel':
            return {
                'debut': now.replace(day=1),
                'fin': now
            }
        elif self.periode == 'trimestriel':
            # Calculer le trimestre actuel
            quarter = (now.month - 1) // 3
            start_month = quarter * 3 + 1
            return {
                'debut': now.replace(month=start_month, day=1),
                'fin': now
            }
        elif self.periode == 'annuel':
            return {
                'debut': now.replace(month=1, day=1),
                'fin': now
            }
        elif self.periode == 'personnalise' and self.date_debut_personnalisee and self.date_fin_personnalisee:
            return {
                'debut': self.date_debut_personnalisee,
                'fin': self.date_fin_personnalisee
            }
        
        # Par défaut, mois en cours
        return {
            'debut': now.replace(day=1),
            'fin': now
        }
    
    def get_statistiques_financieres(self):
        """Retourne les statistiques financières pour la période."""
        periode = self.get_periode_analyse()
        
        # Calculer les revenus (loyers reçus)
        revenus = self._calculer_revenus(periode)
        
        # Calculer les charges
        charges = self._calculer_charges(periode)
        
        # Calculer le taux d'occupation
        taux_occupation = self._calculer_taux_occupation(periode)
        
        return {
            'revenus': revenus,
            'charges': charges,
            'benefices': revenus - charges,
            'taux_occupation': taux_occupation,
            'periode': periode
        }
    
    def _calculer_revenus(self, periode):
        """Calcule les revenus pour la période donnée."""
        from .models import Paiement
        
        paiements = Paiement.objects.filter(
            contrat__propriete__in=self.proprietes.all(),
            date_paiement__gte=periode['debut'],
            date_paiement__lte=periode['fin'],
            statut='valide'
        )
        
        return paiements.aggregate(
            total=models.Sum('montant')
        )['total'] or 0
    
    def _calculer_charges(self, periode):
        """Calcule les charges pour la période donnée."""
        from proprietes.models import ChargeBailleur
        
        charges = ChargeBailleur.objects.filter(
            propriete__in=self.proprietes.all(),
            date_charge__gte=periode['debut'],
            date_charge__lte=periode['fin']
        )
        
        return charges.aggregate(
            total=models.Sum('montant')
        )['total'] or 0
    
    def _calculer_taux_occupation(self, periode):
        """Calcule le taux d'occupation pour la période donnée."""
        from contrats.models import Contrat
        
        contrats_actifs = Contrat.objects.filter(
            propriete__in=self.proprietes.all(),
            est_actif=True,
            est_resilie=False
        )
        
        total_proprietes = self.proprietes.count()
        if total_proprietes == 0:
            return 0
        
        return (contrats_actifs.count() / total_proprietes) * 100
    
    def get_nombre_proprietes(self):
        """Retourne le nombre de propriétés incluses."""
        return self.proprietes.count()
    
    def get_nombre_bailleurs(self):
        """Retourne le nombre de bailleurs inclus."""
        return self.bailleurs.count()
    
    def is_alerte_active(self):
        """Vérifie si le seuil d'alerte est dépassé."""
        if not self.seuil_alerte:
            return False
        
        stats = self.get_statistiques_financieres()
        return stats['benefices'] < self.seuil_alerte
    
    def get_statut_display(self):
        """Retourne le statut d'affichage du tableau de bord."""
        if not self.actif:
            return "Inactif"
        elif self.is_alerte_active():
            return "Alerte"
        else:
            return "Actif"
    
    @property
    def montant(self):
        """Propriété pour maintenir la compatibilité avec l'ancien modèle Retrait."""
        return self.montant_net_a_payer

# Alias pour maintenir la compatibilité avec le code existant
Retrait = RetraitBailleur


class RecapMensuel(models.Model):
    """Modèle pour les récapitulatifs mensuels des bailleurs."""
    
    # Informations de base
    bailleur = models.ForeignKey(
        'proprietes.Bailleur',
        on_delete=models.PROTECT,
        related_name='recaps_mensuels',
        verbose_name=_("Bailleur")
    )
    mois_recap = models.DateField(
        verbose_name=_("Mois du récapitulatif"),
        help_text=_("Mois pour lequel le récapitulatif est établi")
    )
    
    # Montants des loyers
    total_loyers_bruts = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name=_("Total des loyers bruts")
    )
    total_charges_deductibles = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name=_("Total des charges déductibles")
    )
    total_net_a_payer = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name=_("Total net à payer")
    )
    
    # Informations sur les propriétés
    nombre_proprietes = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Nombre de propriétés")
    )
    nombre_contrats_actifs = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Nombre de contrats actifs")
    )
    nombre_paiements_recus = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Nombre de paiements reçus")
    )
    
    # Statut du récapitulatif
    statut = models.CharField(
        max_length=20,
        choices=[
            ('brouillon', 'Brouillon'),
            ('valide', 'Validé'),
            ('envoye', 'Envoyé au bailleur'),
            ('paye', 'Payé au bailleur'),
        ],
        default='brouillon',
        verbose_name=_("Statut")
    )
    
    # Métadonnées
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name=_("Date de création"))
    date_validation = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Date de validation")
    )
    date_envoi = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Date d'envoi")
    )
    date_paiement = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Date de paiement")
    )
    
    # Relations
    cree_par = models.ForeignKey(
        Utilisateur,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recaps_mensuels_crees',
        verbose_name=_("Créé par")
    )
    valide_par = models.ForeignKey(
        Utilisateur,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recaps_mensuels_valides',
        verbose_name=_("Validé par")
    )
    
    # Lien avec les retraits
    retraits_associes = models.ManyToManyField(
        'RetraitBailleur',
        related_name='recaps_mensuels',
        verbose_name=_("Retraits associés")
    )
    
    # Lien avec les paiements
    paiements_concernes = models.ManyToManyField(
        'Paiement',
        related_name='recaps_mensuels',
        verbose_name=_("Paiements concernés")
    )
    
    # Lien avec les charges déductibles
    charges_deductibles = models.ManyToManyField(
        'ChargeDeductible',
        related_name='recaps_mensuels',
        verbose_name=_("Charges déductibles")
    )
    
    is_deleted = models.BooleanField(default=False, verbose_name='Supprimé logiquement')
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name='Date de suppression')
    deleted_by = models.ForeignKey(
        Utilisateur,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='recaps_mensuels_supprimes',
        verbose_name='Supprimé par'
    )
    
    objects = NonDeletedManager()
    all_objects = models.Manager()
    
    class Meta:
        verbose_name = _("Récapitulatif mensuel")
        verbose_name_plural = _("Récapitulatifs mensuels")
        ordering = ['-mois_recap']
        unique_together = ['bailleur', 'mois_recap']
        indexes = [
            models.Index(fields=['bailleur', 'mois_recap']),
            models.Index(fields=['statut']),
            models.Index(fields=['date_creation']),
        ]
    
    def __str__(self):
        return f"Récap {self.bailleur} - {self.mois_recap.strftime('%B %Y')} - {self.total_net_a_payer} XOF"
    
    def save(self, *args, **kwargs):
        """Override save pour calculer automatiquement les totaux."""
        if self.total_loyers_bruts > 0:
            self.total_net_a_payer = self.total_loyers_bruts - self.total_charges_deductibles
        super().save(*args, **kwargs)
    
    def calculer_totaux(self):
        """Calcule les totaux du récapitulatif."""
        from django.db.models import Sum, Count
        
        # Calculer le total des loyers bruts
        loyers_bruts = self.paiements_concernes.filter(
            type_paiement='loyer',
            statut='valide'
        ).aggregate(total=Sum('montant'))['total'] or 0
        
        # Calculer le total des charges déductibles
        charges_deductibles = self.charges_deductibles.filter(
            statut='validee'
        ).aggregate(total=Sum('montant'))['total'] or 0
        
        # Mettre à jour les totaux
        self.total_loyers_bruts = loyers_bruts
        self.total_charges_deductibles = charges_deductibles
        self.total_net_a_payer = loyers_bruts - charges_deductibles
        
        # Mettre à jour les compteurs
        self.nombre_proprietes = self.bailleur.propriete_set.count()
        self.nombre_contrats_actifs = self.bailleur.propriete_set.filter(
            contrats__est_actif=True,
            contrats__est_resilie=False
        ).distinct().count()
        self.nombre_paiements_recus = self.paiements_concernes.filter(
            statut='valide'
        ).count()
        
        self.save()
    
    def valider_recap(self, utilisateur):
        """Valide le récapitulatif."""
        self.statut = 'valide'
        self.valide_par = utilisateur
        self.date_validation = timezone.now()
        self.save()
    
    def marquer_envoye(self, utilisateur):
        """Marque le récapitulatif comme envoyé."""
        self.statut = 'envoye'
        self.date_envoi = timezone.now()
        self.save()
    
    def marquer_paye(self, utilisateur):
        """Marque le récapitulatif comme payé."""
        self.statut = 'paye'
        self.date_paiement = timezone.now()
        self.save()
    
    def generer_document_pdf(self):
        """Génère le document PDF du récapitulatif."""
        # Cette méthode sera implémentée dans les vues
        pass
    
    def get_detail_proprietes(self):
        """Retourne le détail des propriétés et contrats."""
        proprietes = self.bailleur.propriete_set.all()
        detail = []
        
        for propriete in proprietes:
            contrats_actifs = propriete.contrats.filter(
                est_actif=True,
                est_resilie=False
            )
            
            if contrats_actifs.exists():
                for contrat in contrats_actifs:
                    # Calculer le loyer du mois
                    loyer_mois = contrat.loyer_mensuel + contrat.charges_mensuelles
                    
                    # Vérifier si un paiement a été reçu
                    paiement_mois = self.paiements_concernes.filter(
                        contrat=contrat,
                        mois_paye__month=self.mois_recap.month,
                        mois_paye__year=self.mois_recap.year,
                        statut='valide'
                    ).first()
                    
                    detail.append({
                        'propriete': propriete,
                        'contrat': contrat,
                        'locataire': contrat.locataire,
                        'loyer_mensuel': contrat.loyer_mensuel,
                        'charges_mensuelles': contrat.charges_mensuelles,
                        'loyer_total': loyer_mois,
                        'paiement_recu': paiement_mois.montant if paiement_mois else 0,
                        'statut_paiement': 'Payé' if paiement_mois else 'En attente',
                    })
        
        return detail
    
    def get_detail_charges(self):
        """Retourne le détail des charges déductibles."""
        return self.charges_deductibles.filter(statut='validee')
    
    # Méthodes de formatage XOF
    def get_total_loyers_bruts_formatted(self):
        """Retourne le total des loyers bruts formaté en XOF"""
        from core.utils import format_currency_xof
        return format_currency_xof(self.total_loyers_bruts)
    
    def get_total_charges_deductibles_formatted(self):
        """Retourne le total des charges déductibles formaté en XOF"""
        from core.utils import format_currency_xof
        return format_currency_xof(self.total_charges_deductibles)
    
    def get_total_net_formatted(self):
        """Retourne le total net formaté en XOF"""
        from core.utils import format_currency_xof
        return format_currency_xof(self.total_net_a_payer)
