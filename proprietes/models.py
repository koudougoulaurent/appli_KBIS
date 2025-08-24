from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from .managers import NonDeletedManager
import uuid

class TypeBien(models.Model):
    """Modèle pour les types de biens immobiliers."""
    nom = models.CharField(max_length=100, verbose_name=_("Nom"))
    description = models.TextField(blank=True, verbose_name=_("Description"))
    
    class Meta:
        verbose_name = _("Type de bien")
        verbose_name_plural = _("Types de biens")
        ordering = ['nom']
    
    def __str__(self):
        return self.nom


class Bailleur(models.Model):
    """Modèle pour les bailleurs."""
    CIVILITE_CHOICES = [
        ('M', 'Monsieur'),
        ('Mme', 'Madame'),
        ('Mlle', 'Mademoiselle'),
    ]
    
    # Informations personnelles
    numero_bailleur = models.CharField(
        max_length=20,
        unique=True,
        default='BL0001',
        verbose_name=_("Numéro bailleur"),
        help_text=_("Identifiant unique du bailleur")
    )
    code_bailleur = models.CharField(
        max_length=50,
        blank=True,
        default='',
        verbose_name=_("Code bailleur"),
        help_text=_("Code personnalisé du bailleur")
    )
    civilite = models.CharField(
        max_length=5,
        choices=CIVILITE_CHOICES,
        default='M',
        verbose_name=_("Civilité")
    )
    nom = models.CharField(max_length=100, verbose_name=_("Nom"))
    prenom = models.CharField(max_length=100, verbose_name=_("Prénom"))
    date_naissance = models.DateField(blank=True, null=True, verbose_name=_("Date de naissance"))
    
    # Contact
    email = models.EmailField(blank=True, null=True, verbose_name=_("Email"))
    telephone = models.CharField(max_length=20, verbose_name=_("Téléphone"))
    telephone_mobile = models.CharField(max_length=20, blank=True, verbose_name=_("Mobile"))
    
    # Adresse
    adresse = models.TextField(blank=True, null=True, verbose_name=_("Adresse"))
    code_postal = models.CharField(max_length=10, blank=True, null=True, verbose_name=_("Code postal"))
    ville = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Ville"))
    pays = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Pays"))
    
    # Informations bancaires
    iban = models.CharField(max_length=34, blank=True, verbose_name=_("IBAN"))
    bic = models.CharField(max_length=11, blank=True, verbose_name=_("BIC"))
    banque = models.CharField(max_length=100, blank=True, verbose_name=_("Banque"))
    
    # Métadonnées
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name=_("Date de création"))
    date_modification = models.DateTimeField(auto_now=True, verbose_name=_("Date de modification"))
    actif = models.BooleanField(default=True, verbose_name=_("Actif"))
    is_deleted = models.BooleanField(default=False, verbose_name=_("Supprimé logiquement"))
    
    class Meta:
        verbose_name = _("Bailleur")
        verbose_name_plural = _("Bailleurs")
        ordering = ['nom', 'prenom']
    
    objects = NonDeletedManager()
    
    def __str__(self):
        return f"{self.get_nom_complet()} ({self.numero_bailleur})"
    
    def get_nom_complet(self):
        return f"{self.civilite} {self.prenom} {self.nom}"
    
    def get_absolute_url(self):
        return reverse('proprietes:detail_bailleur', kwargs={'pk': self.pk})
    
    def get_statistiques_paiements(self):
        """Récupère les statistiques des paiements pour ce bailleur."""
        from paiements.models import Paiement
        from django.db.models import Sum, Count
        from django.utils import timezone
        from datetime import timedelta
        
        # Période de référence (12 derniers mois)
        date_debut = timezone.now() - timedelta(days=365)
        
        # Paiements du bailleur
        paiements = Paiement.objects.filter(
            contrat__propriete__bailleur=self,
            statut='valide',
            date_paiement__gte=date_debut
        )
        
        # Statistiques
        stats = {
            'total_paiements': paiements.count(),
            'montant_total': paiements.aggregate(total=Sum('montant'))['total'] or 0,
            'moyenne_mensuelle': 0,
            'derniers_mois': [],
            'proprietes_avec_paiements': paiements.values('contrat__propriete').distinct().count(),
        }
        
        # Calcul de la moyenne mensuelle
        if stats['total_paiements'] > 0:
            stats['moyenne_mensuelle'] = stats['montant_total'] / 12
        
        # Paiements par mois (6 derniers mois)
        for i in range(6):
            mois = timezone.now() - timedelta(days=30*i)
            debut_mois = mois.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            fin_mois = (debut_mois + timedelta(days=32)).replace(day=1) - timedelta(seconds=1)
            
            paiements_mois = paiements.filter(
                date_paiement__gte=debut_mois,
                date_paiement__lte=fin_mois
            )
            
            stats['derniers_mois'].append({
                'mois': debut_mois.strftime('%B %Y'),
                'montant': paiements_mois.aggregate(total=Sum('montant'))['total'] or 0,
                'nombre': paiements_mois.count()
            })
        
        return stats


class Locataire(models.Model):
    """Modèle pour les locataires."""
    CIVILITE_CHOICES = [
        ('M', 'Monsieur'),
        ('Mme', 'Madame'),
        ('Mlle', 'Mademoiselle'),
    ]
    
    STATUT_CHOICES = [
        ('actif', 'Actif'),
        ('inactif', 'Inactif'),
        ('suspendu', 'Suspendu'),
    ]
    
    # Informations personnelles
    numero_locataire = models.CharField(
        max_length=20,
        unique=True,
        default='LT0001',
        verbose_name=_("Numéro locataire"),
        help_text=_("Identifiant unique du locataire")
    )
    civilite = models.CharField(
        max_length=5,
        choices=CIVILITE_CHOICES,
        default='M',
        verbose_name=_("Civilité")
    )
    nom = models.CharField(max_length=100, verbose_name=_("Nom"))
    prenom = models.CharField(max_length=100, verbose_name=_("Prénom"))
    date_naissance = models.DateField(blank=True, null=True, verbose_name=_("Date de naissance"))
    
    # Contact
    email = models.EmailField(blank=True, null=True, verbose_name=_("Email"))
    telephone = models.CharField(max_length=20, verbose_name=_("Téléphone"))
    telephone_mobile = models.CharField(max_length=20, blank=True, verbose_name=_("Mobile"))
    
    # Adresse
    adresse = models.TextField(blank=True, null=True, verbose_name=_("Adresse"))
    code_postal = models.CharField(max_length=10, blank=True, null=True, verbose_name=_("Code postal"))
    ville = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Ville"))
    pays = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Pays"))
    
    # Informations professionnelles
    profession = models.CharField(max_length=100, blank=True, verbose_name=_("Profession"))
    employeur = models.CharField(max_length=100, blank=True, verbose_name=_("Employeur"))
    revenus_mensuels = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name=_("Revenus mensuels")
    )
    
    # Statut
    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='actif',
        verbose_name=_("Statut")
    )
    
    # Métadonnées
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name=_("Date de création"))
    date_modification = models.DateTimeField(auto_now=True, verbose_name=_("Date de modification"))
    is_deleted = models.BooleanField(default=False, verbose_name=_("Supprimé logiquement"))
    
    class Meta:
        verbose_name = _("Locataire")
        verbose_name_plural = _("Locataires")
        ordering = ['nom', 'prenom']
    
    objects = NonDeletedManager()
    
    def __str__(self):
        return f"{self.get_nom_complet()} ({self.numero_locataire})"
    
    def get_nom_complet(self):
        return f"{self.civilite} {self.prenom} {self.nom}"
    
    def get_absolute_url(self):
        return reverse('proprietes:detail_locataire', kwargs={'pk': self.pk})
    
    def get_statistiques_paiements(self):
        """Récupère les statistiques des paiements pour ce locataire."""
        from paiements.models import Paiement
        from django.db.models import Sum, Count
        from django.utils import timezone
        from datetime import timedelta
        
        # Période de référence (12 derniers mois)
        date_debut = timezone.now() - timedelta(days=365)
        
        # Paiements du locataire
        paiements = Paiement.objects.filter(
            contrat__locataire=self,
            statut='valide',
            date_paiement__gte=date_debut
        )
        
        # Statistiques
        stats = {
            'total_paiements': paiements.count(),
            'montant_total': paiements.aggregate(total=Sum('montant'))['total'] or 0,
            'moyenne_mensuelle': 0,
            'derniers_mois': [],
            'proprietes_louees': paiements.values('contrat__propriete').distinct().count(),
        }
        
        # Calcul de la moyenne mensuelle
        if stats['total_paiements'] > 0:
            stats['moyenne_mensuelle'] = stats['montant_total'] / 12
        
        # Paiements par mois (6 derniers mois)
        for i in range(6):
            mois = timezone.now() - timedelta(days=30*i)
            debut_mois = mois.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            fin_mois = (debut_mois + timedelta(days=32)).replace(day=1) - timedelta(seconds=1)
            
            paiements_mois = paiements.filter(
                date_paiement__gte=debut_mois,
                date_paiement__lte=fin_mois
            )
            
            stats['derniers_mois'].append({
                'mois': debut_mois.strftime('%B %Y'),
                'montant': paiements_mois.aggregate(total=Sum('montant'))['total'] or 0,
                'nombre': paiements_mois.count()
            })
        
        return stats


class Propriete(models.Model):
    """Modèle pour les propriétés immobilières."""
    ETAT_CHOICES = [
        ('excellent', 'Excellent'),
        ('tres_bon', 'Très bon'),
        ('bon', 'Bon'),
        ('moyen', 'Moyen'),
        ('a_renover', 'À rénover'),
    ]
    
    # Informations de base
    numero_propriete = models.CharField(
        max_length=20,
        unique=True,
        default='PR0001',
        verbose_name=_("Numéro propriété"),
        help_text=_("Identifiant unique de la propriété")
    )
    titre = models.CharField(max_length=200, verbose_name=_("Titre"))
    description = models.TextField(blank=True, verbose_name=_("Description"))
    
    # Localisation
    adresse = models.TextField(blank=True, null=True, verbose_name=_("Adresse"))
    code_postal = models.CharField(max_length=10, blank=True, null=True, verbose_name=_("Code postal"))
    ville = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Ville"))
    pays = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Pays"))
    
    # Caractéristiques
    type_bien = models.ForeignKey(
        TypeBien,
        on_delete=models.PROTECT,
        verbose_name=_("Type de bien")
    )
    surface = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        verbose_name=_("Surface (m²)")
    )
    nombre_pieces = models.PositiveIntegerField(verbose_name=_("Nombre de pièces"))
    nombre_chambres = models.PositiveIntegerField(verbose_name=_("Nombre de chambres"))
    nombre_salles_bain = models.PositiveIntegerField(verbose_name=_("Nombre de salles de bain"))
    
    # Équipements
    ascenseur = models.BooleanField(default=False, verbose_name=_("Ascenseur"))
    parking = models.BooleanField(default=False, verbose_name=_("Parking"))
    balcon = models.BooleanField(default=False, verbose_name=_("Balcon"))
    jardin = models.BooleanField(default=False, verbose_name=_("Jardin"))
    
    # Informations financières
    prix_achat = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name=_("Prix d'achat")
    )
    loyer_actuel = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name=_("Loyer mensuel")
    )
    charges_locataire = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_("Charges locataire")
    )
    
    # État et disponibilité
    etat = models.CharField(
        max_length=20,
        choices=ETAT_CHOICES,
        default='bon',
        verbose_name=_("État")
    )
    disponible = models.BooleanField(default=True, verbose_name=_("Disponible"))
    
    # Relations
    bailleur = models.ForeignKey(
        Bailleur,
        on_delete=models.PROTECT,
        related_name='proprietes',
        verbose_name=_("Bailleur")
    )
    
    # Métadonnées
    notes = models.TextField(blank=True, verbose_name=_("Notes"))
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name=_("Date de création"))
    date_modification = models.DateTimeField(auto_now=True, verbose_name=_("Date de modification"))
    cree_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Créé par")
    )
    is_deleted = models.BooleanField(default=False, verbose_name=_("Supprimé logiquement"))
    
    class Meta:
        verbose_name = _("Propriété")
        verbose_name_plural = _("Propriétés")
        ordering = ['-date_creation']
    
    objects = NonDeletedManager()
    
    def __str__(self):
        return f"{self.titre} - {self.numero_propriete}"
    
    def get_absolute_url(self):
        return reverse('proprietes:detail', kwargs={'pk': self.pk})
    
    def get_loyer_total(self):
        """Retourne le loyer total (loyer + charges)."""
        return self.loyer_actuel + self.charges_locataire


class Photo(models.Model):
    """Modèle pour les photos des propriétés."""
    propriete = models.ForeignKey(
        Propriete, 
        on_delete=models.CASCADE,
        related_name='photos',
        verbose_name=_("Propriété")
    )
    image = models.ImageField(
        upload_to='proprietes/photos/',
        verbose_name=_("Image"),
        help_text=_("Format recommandé: JPG, PNG. Taille max: 5MB")
    )
    titre = models.CharField(
        max_length=100,
        verbose_name=_("Titre"),
        help_text=_("Titre descriptif de la photo")
    )
    description = models.TextField(
        blank=True,
        verbose_name=_("Description"),
        help_text=_("Description détaillée de la photo")
    )
    ordre = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Ordre d'affichage"),
        help_text=_("Ordre d'affichage dans la galerie (0 = premier)")
    )
    est_principale = models.BooleanField(
        default=False,
        verbose_name=_("Photo principale"),
        help_text=_("Cochez si c'est la photo principale de la propriété")
    )
    date_creation = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Date de création")
    )
    date_modification = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Date de modification")
    )
    
    class Meta:
        verbose_name = _("Photo")
        verbose_name_plural = _("Photos")
        ordering = ['ordre', 'date_creation']
        unique_together = ['propriete', 'ordre']
    
    def __str__(self):
        return f"{self.titre} - {self.propriete.adresse}"
    
    def save(self, *args, **kwargs):
        # Si c'est marqué comme photo principale, retirer le statut des autres
        if self.est_principale:
            Photo.objects.filter(
                propriete=self.propriete,
                est_principale=True
            ).exclude(pk=self.pk).update(est_principale=False)
        
        # Définir l'ordre automatiquement si non spécifié
        if not self.ordre:
            max_ordre = Photo.objects.filter(
                propriete=self.propriete
            ).aggregate(
                max_ordre=models.Max('ordre')
            )['max_ordre'] or 0
            self.ordre = max_ordre + 1
        
        super().save(*args, **kwargs)
    
    def get_image_url(self):
        """Retourne l'URL de l'image."""
        if self.image:
            return self.image.url
        return None
    
    def get_thumbnail_url(self):
        """Retourne l'URL de la miniature (pour l'instant identique à l'image)."""
        if self.image:
            return self.image.url
        return None





class ChargesBailleur(models.Model):
    """Modèle pour les charges du bailleur."""
    TYPE_CHARGE_CHOICES = [
        ('reparation', 'Réparation'),
        ('entretien', 'Entretien'),
        ('assurance', 'Assurance'),
        ('taxe', 'Taxe'),
        ('syndic', 'Syndic'),
        ('travaux', 'Travaux'),
        ('autre', 'Autre'),
    ]
    
    STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('payee', 'Payée'),
        ('remboursee', 'Remboursée'),
        ('deduite_retrait', 'Déduite du retrait mensuel'),  # NOUVEAU
        ('annulee', 'Annulée'),
    ]
    
    PRIORITE_CHOICES = [
        ('basse', 'Basse'),
        ('normale', 'Normale'),
        ('haute', 'Haute'),
        ('urgente', 'Urgente'),
    ]
    
    # Informations de base
    numero_charge = models.CharField(
        max_length=20,
        unique=True,
        default='CH0001',
        verbose_name=_("Numéro de charge"),
        help_text=_("Identifiant unique de la charge")
    )
    titre = models.CharField(max_length=200, verbose_name=_("Titre"))
    description = models.TextField(blank=True, verbose_name=_("Description"))
    
    # Classification
    type_charge = models.CharField(
        max_length=20,
        choices=TYPE_CHARGE_CHOICES,
        verbose_name=_("Type de charge")
    )
    priorite = models.CharField(
        max_length=20,
        choices=PRIORITE_CHOICES,
        default='normale',
        verbose_name=_("Priorité")
    )
    
    # Montant et dates
    montant = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Montant")
    )
    montant_deja_deduit = models.DecimalField(  # NOUVEAU
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_("Montant déjà déduit des retraits")
    )
    montant_restant = models.DecimalField(  # NOUVEAU
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_("Montant restant à déduire")
    )
    date_charge = models.DateField(verbose_name=_("Date de la charge"))
    date_echeance = models.DateField(
        blank=True,
        null=True,
        verbose_name=_("Date d'échéance")
    )
    
    # Relations
    propriete = models.ForeignKey(
        Propriete,
        on_delete=models.CASCADE,
        related_name='charges_bailleur',
        verbose_name=_("Propriété")
    )
    
    # Statut et suivi
    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='en_attente',
        verbose_name=_("Statut")
    )
    date_paiement = models.DateField(
        blank=True,
        null=True,
        verbose_name=_("Date de paiement")
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
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Créé par")
    )
    
    class Meta:
        verbose_name = _("Charge bailleur")
        verbose_name_plural = _("Charges bailleur")
        ordering = ['-date_charge']
    
    def __str__(self):
        return f"{self.titre} - {self.montant}€"
    
    def get_absolute_url(self):
        return reverse('proprietes:detail_charge_bailleur', kwargs={'pk': self.pk})
    
    def is_en_retard(self):
        """Vérifie si la charge est en retard."""
        if self.date_echeance and self.statut == 'en_attente':
            from django.utils import timezone
            return timezone.now().date() > self.date_echeance
        return False
    
    def save(self, *args, **kwargs):
        """Override save pour calculer automatiquement le montant restant."""
        if self.montant and self.montant_deja_deduit is not None:
            self.montant_restant = self.montant - self.montant_deja_deduit
            
            # Mettre à jour le statut automatiquement
            if self.montant_restant <= 0:
                self.statut = 'remboursee'
            elif self.montant_deja_deduit > 0:
                self.statut = 'deduite_retrait'
        
        super().save(*args, **kwargs)
    
    def marquer_comme_deduit(self, montant_deduction):
        """
        Marque une charge comme partiellement ou totalement déduite du retrait mensuel.
        
        Args:
            montant_deduction: Montant à déduire
            
        Returns:
            float: Montant effectivement déduit
        """
        from decimal import Decimal
        
        montant_deduction = Decimal(str(montant_deduction))
        montant_restant = Decimal(str(self.montant_restant))
        
        # Calculer le montant effectivement déductible
        montant_effectivement_deduit = min(montant_deduction, montant_restant)
        
        if montant_effectivement_deduit > 0:
            # Mettre à jour les montants
            self.montant_deja_deduit += montant_effectivement_deduit
            self.montant_restant = self.montant - self.montant_deja_deduit
            
            # Mettre à jour le statut
            if self.montant_restant <= 0:
                self.statut = 'remboursee'
            else:
                self.statut = 'deduite_retrait'
            
            # Sauvegarder
            self.save()
            
            # Créer un log de déduction
            self.creer_log_deduction(montant_effectivement_deduit)
        
        return float(montant_effectivement_deduit)
    
    def creer_log_deduction(self, montant_deduit):
        """Crée un log de déduction pour traçabilité."""
        try:
            from core.models import LogAudit
            LogAudit.objects.create(
                modele='ChargesBailleur',
                instance_id=self.id,
                action='deduction_retrait',
                utilisateur=self.cree_par,
                description=f'Déduction de {montant_deduit} XOF du retrait mensuel',
                donnees_avant={},
                donnees_apres={
                    'montant_deja_deduit': str(self.montant_deja_deduit),
                    'montant_restant': str(self.montant_restant),
                    'statut': self.statut
                }
            )
        except Exception as e:
            # En cas d'erreur, on log mais on ne bloque pas l'opération
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Erreur lors de la création du log de déduction: {e}")
    
    def peut_etre_deduit(self):
        """Vérifie si la charge peut être déduite du retrait mensuel."""
        return (
            self.statut in ['en_attente', 'deduite_retrait'] and 
            self.montant_restant > 0
        )
    
    def get_montant_deductible(self):
        """Retourne le montant déductible du retrait mensuel."""
        return self.montant_restant
    
    def get_progression_deduction(self):
        """Retourne le pourcentage de progression de la déduction."""
        if self.montant <= 0:
            return 0
        return (self.montant_deja_deduit / self.montant) * 100


class ChargesBailleurRetrait(models.Model):
    """Modèle de liaison entre ChargesBailleur et RetraitBailleur pour tracer les déductions."""
    
    charge_bailleur = models.ForeignKey(
        ChargesBailleur,
        on_delete=models.CASCADE,
        related_name='retraits_lies',
        verbose_name=_("Charge bailleur")
    )
    retrait_bailleur = models.ForeignKey(
        'paiements.RetraitBailleur',
        on_delete=models.CASCADE,
        related_name='charges_bailleur_liees',
        verbose_name=_("Retrait bailleur")
    )
    montant_deduit = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Montant déduit de ce retrait")
    )
    date_deduction = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Date de la déduction")
    )
    notes = models.TextField(
        blank=True,
        verbose_name=_("Notes sur la déduction")
    )
    
    class Meta:
        verbose_name = _("Liaison charge bailleur - retrait")
        verbose_name_plural = _("Liaisons charges bailleur - retraits")
        unique_together = ['charge_bailleur', 'retrait_bailleur']
        ordering = ['-date_deduction']
    
    def __str__(self):
        return f"{self.charge_bailleur.titre} - {self.retrait_bailleur} - {self.montant_deduit} XOF"
    
    def get_absolute_url(self):
        return reverse('proprietes:detail_charge_bailleur', kwargs={'pk': self.charge_bailleur.pk})


class Document(models.Model):
    """Modèle pour la gestion des documents - Intégré dans le module propriétés."""
    TYPE_DOCUMENT_CHOICES = [
        ('contrat', 'Contrat de bail'),
        ('etat_lieux', 'État des lieux'),
        ('quittance', 'Quittance de loyer'),
        ('facture', 'Facture'),
        ('devis', 'Devis'),
        ('assurance', 'Assurance'),
        ('diagnostic', 'Diagnostic'),
        ('justificatif', 'Justificatif'),
        ('courrier', 'Courrier'),
        ('autre', 'Autre'),
    ]
    
    STATUT_CHOICES = [
        ('brouillon', 'Brouillon'),
        ('en_attente', 'En attente'),
        ('valide', 'Validé'),
        ('archive', 'Archivé'),
        ('expire', 'Expiré'),
    ]
    
    # Informations de base
    nom = models.CharField(max_length=200, verbose_name=_("Nom du document"))
    type_document = models.CharField(
        max_length=20,
        choices=TYPE_DOCUMENT_CHOICES,
        verbose_name=_("Type de document")
    )
    description = models.TextField(blank=True, verbose_name=_("Description"))
    
    # Fichier
    fichier = models.FileField(
        upload_to='documents/',
        verbose_name=_("Fichier"),
        help_text=_("Formats acceptés: PDF, DOC, DOCX, JPG, PNG")
    )
    taille_fichier = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name=_("Taille du fichier (bytes)")
    )
    
    # Relations
    propriete = models.ForeignKey(
        Propriete,
        on_delete=models.CASCADE,
        related_name='documents',
        blank=True,
        null=True,
        verbose_name=_("Propriété")
    )
    bailleur = models.ForeignKey(
        Bailleur,
        on_delete=models.CASCADE,
        related_name='documents',
        blank=True,
        null=True,
        verbose_name=_("Bailleur")
    )
    locataire = models.ForeignKey(
        Locataire,
        on_delete=models.CASCADE,
        related_name='documents',
        blank=True,
        null=True,
        verbose_name=_("Locataire")
    )
    
    # Statut et dates
    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='brouillon',
        verbose_name=_("Statut")
    )
    date_creation = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Date de création")
    )
    date_modification = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Date de modification")
    )
    date_expiration = models.DateField(
        blank=True,
        null=True,
        verbose_name=_("Date d'expiration")
    )
    
    # Métadonnées
    cree_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Créé par"),
        related_name='documents_proprietes'
    )
    tags = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_("Tags"),
        help_text=_("Mots-clés séparés par des virgules")
    )
    confidentiel = models.BooleanField(
        default=False,
        verbose_name=_("Document confidentiel")
    )
    is_deleted = models.BooleanField(default=False, verbose_name=_("Supprimé logiquement"))
    
    class Meta:
        verbose_name = _("Document")
        verbose_name_plural = _("Documents")
        ordering = ['-date_creation']
    
    objects = NonDeletedManager()
    
    def __str__(self):
        return f"{self.nom} ({self.get_type_document_display()})"
    
    def save(self, *args, **kwargs):
        # Calculer la taille du fichier
        if self.fichier and hasattr(self.fichier, 'size'):
            self.taille_fichier = self.fichier.size
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('proprietes:document_detail', kwargs={'pk': self.pk})
    
    def get_taille_fichier_lisible(self):
        """Retourne la taille du fichier dans un format lisible."""
        if not self.taille_fichier:
            return "Inconnue"
        
        taille = self.taille_fichier
        for unit in ['B', 'KB', 'MB', 'GB']:
            if taille < 1024.0:
                return f"{taille:.1f} {unit}"
            taille /= 1024.0
        return f"{taille:.1f} TB"
    
    def is_expired(self):
        """Vérifie si le document est expiré."""
        if self.date_expiration:
            from django.utils import timezone
            return timezone.now().date() > self.date_expiration
        return False


class Piece(models.Model):
    """Modèle pour gérer les pièces individuelles d'une propriété."""
    TYPE_PIECE_CHOICES = [
        ('chambre', 'Chambre'),
        ('salon', 'Salon'),
        ('cuisine', 'Cuisine'),
        ('salle_bain', 'Salle de bain'),
        ('toilettes', 'Toilettes'),
        ('couloir', 'Couloir'),
        ('balcon', 'Balcon'),
        ('terrasse', 'Terrasse'),
        ('jardin', 'Jardin'),
        ('parking', 'Parking'),
        ('cave', 'Cave'),
        ('grenier', 'Grenier'),
        ('autre', 'Autre'),
    ]
    
    STATUT_CHOICES = [
        ('disponible', 'Disponible'),
        ('occupee', 'Occupée'),
        ('en_renovation', 'En rénovation'),
        ('hors_service', 'Hors service'),
    ]
    
    # Informations de base
    propriete = models.ForeignKey(
        Propriete,
        on_delete=models.CASCADE,
        related_name='pieces',
        verbose_name=_("Propriété")
    )
    nom = models.CharField(max_length=100, verbose_name=_("Nom de la pièce"))
    type_piece = models.CharField(
        max_length=20,
        choices=TYPE_PIECE_CHOICES,
        verbose_name=_("Type de pièce")
    )
    surface = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name=_("Surface (m²)")
    )
    numero_piece = models.CharField(
        max_length=10,
        blank=True,
        verbose_name=_("Numéro de pièce")
    )
    
    # État et disponibilité
    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='disponible',
        verbose_name=_("Statut")
    )
    description = models.TextField(blank=True, verbose_name=_("Description"))
    
    # Métadonnées
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name=_("Date de création"))
    date_modification = models.DateTimeField(auto_now=True, verbose_name=_("Date de modification"))
    is_deleted = models.BooleanField(default=False, verbose_name=_("Supprimé logiquement"))
    
    class Meta:
        verbose_name = _("Pièce")
        verbose_name_plural = _("Pièces")
        ordering = ['propriete', 'type_piece', 'numero_piece']
        unique_together = ['propriete', 'numero_piece']
    
    objects = NonDeletedManager()
    
    def __str__(self):
        return f"{self.nom} - {self.propriete.titre}"
    
    def get_absolute_url(self):
        return reverse('proprietes:piece_detail', kwargs={'pk': self.pk})
    
    def est_disponible(self, date_debut=None, date_fin=None):
        """Vérifie si la pièce est disponible pour une période donnée."""
        if self.statut != 'disponible':
            return False
        
        # Vérifier s'il y a des contrats actifs pour cette pièce
        from contrats.models import Contrat
        from django.utils import timezone
        
        if not date_debut:
            date_debut = timezone.now().date()
        if not date_fin:
            date_fin = date_debut + timezone.timedelta(days=365)  # Par défaut 1 an
        
        # Vérifier les contrats actifs qui se chevauchent
        contrats_conflictuels = Contrat.objects.filter(
            pieces=self,
            est_actif=True,
            est_resilie=False,
            date_debut__lt=date_fin,
            date_fin__gt=date_debut
        ).exists()
        
        return not contrats_conflictuels
    
    def get_contrat_actuel(self):
        """Retourne le contrat actuel de cette pièce."""
        from contrats.models import Contrat
        from django.utils import timezone
        
        return Contrat.objects.filter(
            pieces=self,
            est_actif=True,
            est_resilie=False,
            date_debut__lte=timezone.now().date(),
            date_fin__gte=timezone.now().date()
        ).first()
    
    def get_locataire_actuel(self):
        """Retourne le locataire actuel de cette pièce."""
        contrat = self.get_contrat_actuel()
        return contrat.locataire if contrat else None
    
    def marquer_occupee(self):
        """Marque la pièce comme occupée."""
        self.statut = 'occupee'
        self.save()
    
    def marquer_disponible(self):
        """Marque la pièce comme disponible."""
        self.statut = 'disponible'
        self.save()
    
    def marquer_en_renovation(self):
        """Marque la pièce comme en rénovation."""
        self.statut = 'en_renovation'
        self.save()
    
    def get_historique_contrats(self):
        """Retourne l'historique des contrats pour cette pièce."""
        from contrats.models import Contrat
        
        return Contrat.objects.filter(
            pieces=self,
            is_deleted=False
        ).order_by('-date_debut')
    
    def get_statistiques_occupation(self):
        """Retourne les statistiques d'occupation de la pièce."""
        from contrats.models import Contrat
        from django.utils import timezone
        from datetime import timedelta
        
        # Période de référence (12 derniers mois)
        date_debut = timezone.now().date() - timedelta(days=365)
        
        contrats = Contrat.objects.filter(
            pieces=self,
            date_debut__gte=date_debut,
            is_deleted=False
        )
        
        total_contrats = contrats.count()
        jours_occupes = 0
        
        for contrat in contrats:
            if contrat.date_fin:
                duree = (contrat.date_fin - contrat.date_debut).days
                jours_occupes += duree
            else:
                # Contrat en cours
                jours_occupes += (timezone.now().date() - contrat.date_debut).days
        
        taux_occupation = (jours_occupes / 365) * 100 if total_contrats > 0 else 0
        
        return {
            'total_contrats': total_contrats,
            'jours_occupes': jours_occupes,
            'taux_occupation': round(taux_occupation, 2),
            'contrats_actifs': contrats.filter(est_actif=True, est_resilie=False).count()
        }


class PieceContrat(models.Model):
    """Modèle de liaison entre pièces et contrats pour gérer les locations par pièce."""
    
    piece = models.ForeignKey(
        Piece,
        on_delete=models.CASCADE,
        related_name='contrats_pieces',
        verbose_name=_("Pièce")
    )
    contrat = models.ForeignKey(
        'contrats.Contrat',
        on_delete=models.CASCADE,
        related_name='pieces_contrat',
        verbose_name=_("Contrat")
    )
    
    # Informations spécifiques à la pièce dans ce contrat
    loyer_piece = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name=_("Loyer spécifique à la pièce")
    )
    charges_piece = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_("Charges spécifiques à la pièce")
    )
    
    # Dates d'occupation spécifiques à la pièce
    date_debut_occupation = models.DateField(verbose_name=_("Date de début d'occupation"))
    date_fin_occupation = models.DateField(
        blank=True,
        null=True,
        verbose_name=_("Date de fin d'occupation")
    )
    
    # Statut
    actif = models.BooleanField(default=True, verbose_name=_("Actif"))
    
    # Métadonnées
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name=_("Date de création"))
    date_modification = models.DateTimeField(auto_now=True, verbose_name=_("Date de modification"))
    
    class Meta:
        verbose_name = _("Pièce-Contrat")
        verbose_name_plural = _("Pièces-Contrats")
        unique_together = ['piece', 'contrat']
        ordering = ['-date_creation']
    
    def __str__(self):
        return f"{self.piece.nom} - Contrat {self.contrat.numero_contrat}"
    
    def est_actif(self):
        """Vérifie si la liaison pièce-contrat est active."""
        from django.utils import timezone
        
        if not self.actif:
            return False
        
        aujourd_hui = timezone.now().date()
        
        if self.date_debut_occupation > aujourd_hui:
            return False
        
        if self.date_fin_occupation and self.date_fin_occupation < aujourd_hui:
            return False
        
        return True
    
    def get_duree_occupation(self):
        """Retourne la durée d'occupation en jours."""
        if not self.date_fin_occupation:
            from django.utils import timezone
            return (timezone.now().date() - self.date_debut_occupation).days
        
        return (self.date_fin_occupation - self.date_debut_occupation).days
    
    def get_loyer_total(self):
        """Retourne le loyer total de la pièce (loyer + charges)."""
        loyer = self.loyer_piece or 0
        charges = self.charges_piece or 0
        return loyer + charges