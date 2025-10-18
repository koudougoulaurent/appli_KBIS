from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.urls import reverse
from decimal import Decimal
from datetime import date
from contrats.models import Contrat
from proprietes.managers import NonDeletedManager
from django.conf import settings
from proprietes.models import Bailleur, Propriete


class ChargeDeductible(models.Model):
    """Modèle pour les charges avancées par le locataire et déductibles du loyer."""
    
    # Informations de base
    contrat = models.ForeignKey(
        Contrat,
        on_delete=models.CASCADE,
        related_name='charges_deductibles',
        verbose_name=_("Contrat")
    )
    
    # Détails de la charge
    description = models.CharField(
        max_length=200,
        verbose_name=_("Description de la charge")
    )
    montant = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        verbose_name=_("Montant de la charge")
    )
    date_charge = models.DateField(
        verbose_name=_("Date de la charge")
    )
    
    # Statut
    est_deductible_loyer = models.BooleanField(
        default=True,
        verbose_name=_("Déductible du loyer")
    )
    est_valide = models.BooleanField(
        default=False,
        verbose_name=_("Validé")
    )
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)
    
    objects = NonDeletedManager()
    all_objects = models.Manager()
    
    class Meta:
        verbose_name = _("Charge déductible")
        verbose_name_plural = _("Charges déductibles")
        ordering = ['-date_charge']
    
    def __str__(self):
        return f"{self.description} - {self.montant} F CFA"


class Paiement(models.Model):
    """Modèle pour les paiements de loyer avec support des paiements partiels."""
    
    # Relations
    contrat = models.ForeignKey(
        Contrat,
        on_delete=models.CASCADE,
        related_name='paiements',
        verbose_name=_("Contrat")
    )
    
    # Montants
    montant = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        verbose_name=_("Montant payé")
    )
    montant_charges_deduites = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_("Montant des charges déduites")
    )
    montant_net_paye = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Montant net payé")
    )
    
    # Type et mode de paiement
    type_paiement = models.CharField(
        max_length=20,
        choices=[
            ('loyer', 'Loyer'),
            ('caution', 'Caution'),
            ('avance', 'Avance'),
            ('charges', 'Charges'),
        ],
        default='loyer',
        verbose_name=_("Type de paiement")
    )
    mode_paiement = models.CharField(
        max_length=20,
        choices=[
            ('especes', 'Espèces'),
            ('cheque', 'Chèque'),
            ('virement', 'Virement'),
            ('mobile_money', 'Mobile Money'),
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
    
    # Statut
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
    
    # Informations bancaires
    numero_cheque = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_("Numéro de chèque")
    )
    reference_virement = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Référence du virement")
    )
    
    # Validation
    valide_par = models.ForeignKey(
        'utilisateurs.Utilisateur',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='paiements_valides',
        verbose_name=_("Validé par")
    )
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(
        'utilisateurs.Utilisateur',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='paiement_deleted',
        verbose_name=_("Supprimé par")
    )
    
    objects = NonDeletedManager()
    all_objects = models.Manager()
    
    class Meta:
        verbose_name = _("Paiement")
        verbose_name_plural = _("Paiements")
        ordering = ['-date_paiement']
    
    def __str__(self):
        return f"Paiement {self.montant} F CFA - {self.contrat.locataire.get_nom_complet()}"
    
    def get_statut_color(self):
        """Retourne la couleur Bootstrap pour le statut"""
        colors = {
            'en_attente': 'warning',
            'valide': 'success',
            'refuse': 'danger',
            'annule': 'secondary',
        }
        return colors.get(self.statut, 'secondary')


# =============================================================================
# MODÈLES POUR LES RETRAITS AUX BAILLEURS
# =============================================================================

class RetraitBailleur(models.Model):
    """
    Modèle pour les retraits aux bailleurs
    """
    STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('valide', 'Validé'),
        ('paye', 'Payé'),
        ('annule', 'Annulé'),
    ]
    
    TYPE_RETRAIT_CHOICES = [
        ('mensuel', 'Retrait mensuel'),
        ('trimestriel', 'Retrait trimestriel'),
        ('annuel', 'Retrait annuel'),
        ('exceptionnel', 'Retrait exceptionnel'),
    ]
    
    MODE_RETRAIT_CHOICES = [
        ('virement', 'Virement bancaire'),
        ('cheque', 'Chèque'),
        ('especes', 'Espèces'),
    ]
    
    # Relations
    bailleur = models.ForeignKey(
        'proprietes.Bailleur',
        on_delete=models.CASCADE,
        verbose_name=_("Bailleur"),
        related_name='retraits'
    )
    
    # Informations de base
    mois_retrait = models.DateField(
        verbose_name=_("Mois de retrait"),
        help_text=_("Mois pour lequel le retrait est effectué")
    )
    
    # Montants
    montant_loyers_bruts = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name=_("Montant des loyers bruts")
    )
    
    montant_charges_deductibles = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name=_("Montant des charges déductibles")
    )
    
    montant_charges_bailleur = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name=_("Montant des charges bailleur")
    )
    
    montant_net_a_payer = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name=_("Montant net à payer")
    )
    
    # Configuration
    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='en_attente',
        verbose_name=_("Statut")
    )
    
    type_retrait = models.CharField(
        max_length=20,
        choices=TYPE_RETRAIT_CHOICES,
        default='mensuel',
        verbose_name=_("Type de retrait")
    )
    
    mode_retrait = models.CharField(
        max_length=20,
        choices=MODE_RETRAIT_CHOICES,
        default='virement',
        verbose_name=_("Mode de retrait")
    )
    
    # Dates
    date_demande = models.DateField(
        auto_now_add=True,
        verbose_name=_("Date de demande")
    )
    
    date_validation = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Date de validation")
    )
    
    date_paiement = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Date de paiement")
    )
    
    # Utilisateurs
    cree_par = models.ForeignKey(
        'utilisateurs.Utilisateur',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='retraits_crees',
        verbose_name=_("Créé par")
    )
    
    valide_par = models.ForeignKey(
        'utilisateurs.Utilisateur',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='retraits_valides',
        verbose_name=_("Validé par")
    )
    
    # Métadonnées
    notes = models.TextField(
        blank=True,
        verbose_name=_("Notes")
    )
    
    is_deleted = models.BooleanField(
        default=False,
        verbose_name=_("Supprimé")
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Date de création")
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Date de modification")
    )
    
    class Meta:
        verbose_name = _("Retrait bailleur")
        verbose_name_plural = _("Retraits bailleur")
        ordering = ['-mois_retrait', '-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['bailleur', 'mois_retrait'],
                condition=models.Q(is_deleted=False),
                name='unique_retrait_actif_per_bailleur_month'
            )
        ]
        indexes = [
            models.Index(fields=['bailleur', 'mois_retrait']),
            models.Index(fields=['statut']),
            models.Index(fields=['date_demande']),
        ]
    
    def __str__(self):
        return f"Retrait {self.mois_retrait.strftime('%B %Y')} - {self.bailleur.get_nom_complet()}"
    
    def get_nom_complet(self):
        """Retourne le nom complet du bailleur"""
        return self.bailleur.get_nom_complet()
    
    def calculer_montant_net(self):
        """Calcule le montant net à payer"""
        net = self.montant_loyers_bruts - self.montant_charges_deductibles - self.montant_charges_bailleur
        self.montant_net_a_payer = max(net, Decimal('0'))
        return self.montant_net_a_payer
    
    def valider(self, user):
        """Valide le retrait"""
        self.statut = 'valide'
        self.date_validation = date.today()
        self.valide_par = user
        self.save()
    
    def marquer_paye(self, user):
        """Marque le retrait comme payé"""
        self.statut = 'paye'
        self.date_paiement = date.today()
        self.save()
    
    def annuler(self, user):
        """Annule le retrait"""
        self.statut = 'annule'
        self.save()


class RetraitQuittance(models.Model):
    """
    Modèle pour les quittances de retrait
    """
    retrait = models.OneToOneField(
        RetraitBailleur,
        on_delete=models.CASCADE,
        related_name='quittance',
        verbose_name=_("Retrait")
    )
    
    numero_quittance = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_("Numéro de quittance")
    )
    
    date_emission = models.DateField(
        auto_now_add=True,
        verbose_name=_("Date d'émission")
    )
    
    cree_par = models.ForeignKey(
        'utilisateurs.Utilisateur',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Créé par")
    )
    
    # Métadonnées
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Date de création")
    )
    
    class Meta:
        verbose_name = _("Quittance de retrait")
        verbose_name_plural = _("Quittances de retrait")
        ordering = ['-date_emission']
    
    def __str__(self):
        return f"Quittance {self.numero_quittance} - {self.retrait.get_nom_complet()}"
    
    def generer_numero(self):
        """Génère un numéro de quittance unique"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"QUI-{timestamp}-{self.retrait.id}"
    
    def save(self, *args, **kwargs):
        if not self.numero_quittance:
            self.numero_quittance = self.generer_numero()
        super().save(*args, **kwargs)
