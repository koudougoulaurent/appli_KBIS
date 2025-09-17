"""
Modèles spécialisés pour le système de paiement partiel professionnel
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
from contrats.models import Contrat
from proprietes.models import Bailleur, Propriete
from paiements.models import Paiement
import uuid

Utilisateur = get_user_model()


class PlanPaiementPartiel(models.Model):
    """Plan de paiement partiel pour un contrat"""
    
    # Identifiants
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    numero_plan = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_("Numéro du plan")
    )
    
    # Contrat associé
    contrat = models.ForeignKey(
        Contrat,
        on_delete=models.CASCADE,
        related_name='plans_paiement_partiel',
        verbose_name=_("Contrat")
    )
    
    # Informations du plan
    nom_plan = models.CharField(
        max_length=100,
        verbose_name=_("Nom du plan"),
        help_text=_("Ex: Plan de paiement échelonné - Janvier 2025")
    )
    description = models.TextField(
        blank=True,
        verbose_name=_("Description du plan")
    )
    
    # Montants
    montant_total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        verbose_name=_("Montant total à payer")
    )
    montant_deja_paye = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_("Montant déjà payé")
    )
    montant_restant = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_("Montant restant")
    )
    
    # Dates
    date_debut = models.DateField(
        verbose_name=_("Date de début du plan")
    )
    date_fin_prevue = models.DateField(
        verbose_name=_("Date de fin prévue")
    )
    date_fin_reelle = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Date de fin réelle")
    )
    
    # Statut
    statut = models.CharField(
        max_length=20,
        choices=[
            ('actif', 'Actif'),
            ('suspendu', 'Suspendu'),
            ('termine', 'Terminé'),
            ('annule', 'Annulé'),
        ],
        default='actif',
        verbose_name=_("Statut du plan")
    )
    
    # Métadonnées
    cree_par = models.ForeignKey(
        Utilisateur,
        on_delete=models.PROTECT,
        related_name='plans_paiement_crees',
        verbose_name=_("Créé par")
    )
    date_creation = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Date de création")
    )
    modifie_par = models.ForeignKey(
        Utilisateur,
        on_delete=models.PROTECT,
        related_name='plans_paiement_modifies',
        null=True,
        blank=True,
        verbose_name=_("Modifié par")
    )
    date_modification = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Date de modification")
    )
    
    # Soft delete
    is_deleted = models.BooleanField(
        default=False,
        verbose_name=_("Supprimé")
    )
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Date de suppression")
    )
    deleted_by = models.ForeignKey(
        Utilisateur,
        on_delete=models.PROTECT,
        related_name='plans_paiement_supprimes',
        null=True,
        blank=True,
        verbose_name=_("Supprimé par")
    )
    
    class Meta:
        verbose_name = _("Plan de paiement partiel")
        verbose_name_plural = _("Plans de paiement partiel")
        ordering = ['-date_creation']
    
    def __str__(self):
        return f"Plan {self.numero_plan} - {self.contrat}"
    
    def save(self, *args, **kwargs):
        if not self.numero_plan:
            self.numero_plan = self.generate_numero_plan()
        
        # Calculer le montant restant
        self.montant_restant = self.montant_total - self.montant_deja_paye
        
        super().save(*args, **kwargs)
    
    def generate_numero_plan(self):
        """Générer un numéro de plan unique"""
        import datetime
        date_str = timezone.now().strftime('%Y%m%d')
        count = PlanPaiementPartiel.objects.filter(
            numero_plan__startswith=f"PPP{date_str}"
        ).count() + 1
        return f"PPP{date_str}{count:03d}"
    
    def calculer_progression(self):
        """Calculer le pourcentage de progression"""
        if self.montant_total > 0:
            return (self.montant_deja_paye / self.montant_total) * 100
        return 0
    
    def est_termine(self):
        """Vérifier si le plan est terminé"""
        return self.montant_restant <= 0 or self.statut == 'termine'
    
    def peut_etre_modifie(self):
        """Vérifier si le plan peut être modifié"""
        return self.statut in ['actif', 'suspendu'] and not self.is_deleted


class EchelonPaiement(models.Model):
    """Échelon de paiement dans un plan"""
    
    # Identifiants
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Plan associé
    plan = models.ForeignKey(
        PlanPaiementPartiel,
        on_delete=models.CASCADE,
        related_name='echelons',
        verbose_name=_("Plan de paiement")
    )
    
    # Informations de l'échelon
    numero_echelon = models.PositiveIntegerField(
        verbose_name=_("Numéro d'échelon")
    )
    montant = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        verbose_name=_("Montant de l'échelon")
    )
    date_echeance = models.DateField(
        verbose_name=_("Date d'échéance")
    )
    
    # Statut
    statut = models.CharField(
        max_length=20,
        choices=[
            ('en_attente', 'En attente'),
            ('paye', 'Payé'),
            ('en_retard', 'En retard'),
            ('annule', 'Annulé'),
        ],
        default='en_attente',
        verbose_name=_("Statut de l'échelon")
    )
    
    # Paiement associé
    paiement = models.ForeignKey(
        Paiement,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='echelon_paiement',
        verbose_name=_("Paiement associé")
    )
    
    # Dates
    date_paiement = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Date de paiement")
    )
    
    # Métadonnées
    cree_par = models.ForeignKey(
        Utilisateur,
        on_delete=models.PROTECT,
        related_name='echelons_crees',
        verbose_name=_("Créé par")
    )
    date_creation = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Date de création")
    )
    
    class Meta:
        verbose_name = _("Échelon de paiement")
        verbose_name_plural = _("Échelons de paiement")
        ordering = ['plan', 'numero_echelon']
        unique_together = ['plan', 'numero_echelon']
    
    def __str__(self):
        return f"Échelon {self.numero_echelon} - {self.plan.numero_plan} - {self.montant} FCFA"
    
    def est_en_retard(self):
        """Vérifier si l'échelon est en retard"""
        return self.statut == 'en_retard' or (
            self.statut == 'en_attente' and 
            timezone.now().date() > self.date_echeance
        )
    
    def marquer_comme_paye(self, paiement, utilisateur):
        """Marquer l'échelon comme payé"""
        self.statut = 'paye'
        self.paiement = paiement
        self.date_paiement = timezone.now()
        self.save()
        
        # Mettre à jour le plan
        self.plan.montant_deja_paye += self.montant
        self.plan.save()


class PaiementPartiel(models.Model):
    """Paiement partiel spécialisé"""
    
    # Identifiants
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    numero_paiement_partiel = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_("Numéro de paiement partiel")
    )
    
    # Relations
    plan = models.ForeignKey(
        PlanPaiementPartiel,
        on_delete=models.CASCADE,
        related_name='paiements_partiels',
        verbose_name=_("Plan de paiement")
    )
    echelon = models.ForeignKey(
        EchelonPaiement,
        on_delete=models.CASCADE,
        related_name='paiements',
        null=True,
        blank=True,
        verbose_name=_("Échelon associé")
    )
    paiement_principal = models.ForeignKey(
        Paiement,
        on_delete=models.CASCADE,
        related_name='paiements_partiels',
        verbose_name=_("Paiement principal")
    )
    
    # Montants
    montant = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        verbose_name=_("Montant du paiement partiel")
    )
    montant_restant_apres = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_("Montant restant après ce paiement")
    )
    
    # Informations
    motif = models.CharField(
        max_length=200,
        verbose_name=_("Motif du paiement partiel")
    )
    description = models.TextField(
        blank=True,
        verbose_name=_("Description détaillée")
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
    
    # Dates
    date_paiement = models.DateTimeField(
        default=timezone.now,
        verbose_name=_("Date de paiement")
    )
    date_validation = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Date de validation")
    )
    
    # Métadonnées
    cree_par = models.ForeignKey(
        Utilisateur,
        on_delete=models.PROTECT,
        related_name='paiements_partiels_crees',
        verbose_name=_("Créé par")
    )
    valide_par = models.ForeignKey(
        Utilisateur,
        on_delete=models.PROTECT,
        related_name='paiements_partiels_valides',
        null=True,
        blank=True,
        verbose_name=_("Validé par")
    )
    
    # Soft delete
    is_deleted = models.BooleanField(
        default=False,
        verbose_name=_("Supprimé")
    )
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Date de suppression")
    )
    deleted_by = models.ForeignKey(
        Utilisateur,
        on_delete=models.PROTECT,
        related_name='paiements_partiels_supprimes',
        null=True,
        blank=True,
        verbose_name=_("Supprimé par")
    )
    
    class Meta:
        verbose_name = _("Paiement partiel")
        verbose_name_plural = _("Paiements partiels")
        ordering = ['-date_paiement']
    
    def __str__(self):
        return f"Paiement partiel {self.numero_paiement_partiel} - {self.montant} FCFA"
    
    def save(self, *args, **kwargs):
        if not self.numero_paiement_partiel:
            self.numero_paiement_partiel = self.generate_numero()
        
        # Calculer le montant restant après ce paiement
        if self.plan:
            self.montant_restant_apres = self.plan.montant_restant - self.montant
        
        super().save(*args, **kwargs)
    
    def generate_numero(self):
        """Générer un numéro de paiement partiel unique"""
        import datetime
        date_str = timezone.now().strftime('%Y%m%d')
        count = PaiementPartiel.objects.filter(
            numero_paiement_partiel__startswith=f"PP{date_str}"
        ).count() + 1
        return f"PP{date_str}{count:04d}"
    
    def valider(self, utilisateur):
        """Valider le paiement partiel"""
        self.statut = 'valide'
        self.valide_par = utilisateur
        self.date_validation = timezone.now()
        self.save()
        
        # Mettre à jour le plan
        self.plan.montant_deja_paye += self.montant
        self.plan.save()
        
        # Marquer l'échelon comme payé si applicable
        if self.echelon:
            self.echelon.marquer_comme_paye(self.paiement_principal, utilisateur)


class AlertePaiementPartiel(models.Model):
    """Alertes pour les paiements partiels"""
    
    # Identifiants
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Relations
    plan = models.ForeignKey(
        PlanPaiementPartiel,
        on_delete=models.CASCADE,
        related_name='alertes',
        verbose_name=_("Plan de paiement")
    )
    echelon = models.ForeignKey(
        EchelonPaiement,
        on_delete=models.CASCADE,
        related_name='alertes',
        null=True,
        blank=True,
        verbose_name=_("Échelon concerné")
    )
    
    # Informations de l'alerte
    type_alerte = models.CharField(
        max_length=30,
        choices=[
            ('echeance_proche', 'Échéance proche'),
            ('echeance_depassee', 'Échéance dépassée'),
            ('montant_insuffisant', 'Montant insuffisant'),
            ('plan_suspendu', 'Plan suspendu'),
            ('plan_termine', 'Plan terminé'),
        ],
        verbose_name=_("Type d'alerte")
    )
    message = models.TextField(
        verbose_name=_("Message d'alerte")
    )
    niveau_urgence = models.CharField(
        max_length=20,
        choices=[
            ('faible', 'Faible'),
            ('moyen', 'Moyen'),
            ('eleve', 'Élevé'),
            ('critique', 'Critique'),
        ],
        default='moyen',
        verbose_name=_("Niveau d'urgence")
    )
    
    # Statut
    statut = models.CharField(
        max_length=20,
        choices=[
            ('active', 'Active'),
            ('traitee', 'Traitée'),
            ('ignoree', 'Ignorée'),
        ],
        default='active',
        verbose_name=_("Statut de l'alerte")
    )
    
    # Dates
    date_creation = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Date de création")
    )
    date_traitement = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Date de traitement")
    )
    
    # Métadonnées
    cree_par = models.ForeignKey(
        Utilisateur,
        on_delete=models.PROTECT,
        related_name='alertes_paiement_crees',
        verbose_name=_("Créé par")
    )
    traite_par = models.ForeignKey(
        Utilisateur,
        on_delete=models.PROTECT,
        related_name='alertes_paiement_traitees',
        null=True,
        blank=True,
        verbose_name=_("Traité par")
    )
    
    class Meta:
        verbose_name = _("Alerte de paiement partiel")
        verbose_name_plural = _("Alertes de paiement partiel")
        ordering = ['-date_creation']
    
    def __str__(self):
        return f"Alerte {self.type_alerte} - {self.plan.numero_plan}"
    
    def traiter(self, utilisateur):
        """Traiter l'alerte"""
        self.statut = 'traitee'
        self.traite_par = utilisateur
        self.date_traitement = timezone.now()
        self.save()
