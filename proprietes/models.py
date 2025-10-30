from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError

from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from .managers import NonDeletedManager
from core.duplicate_prevention import DuplicatePreventionMixin, validate_unique_contact_info
from django.db import transaction
from core.models import AutoNumberSequence
from django.utils import timezone


class TypeBien(models.Model):
    """Modèle pour les types de biens immobiliers."""
    nom = models.CharField(max_length=100, verbose_name=_("Nom"))
    description = models.TextField(blank=True, verbose_name=_("Description"))
    
    class Meta:
        app_label = 'proprietes'
        verbose_name = _("Type de bien")
        verbose_name_plural = _("Types de biens")
        ordering = ['nom']
    
    def __str__(self):
        return self.nom
    
    def necessite_unites_locatives(self):
        """
        Détermine si ce type de bien nécessite généralement des unités locatives.
        Basé sur des mots-clés dans le nom du type de bien.
        """
        nom_lower = self.nom.lower()
        
        # Types de biens qui nécessitent généralement des unités locatives
        mots_cles_unites = [
            'immeuble', 'building', 'résidence', 'complexe', 'centre commercial',
            'centre d\'affaires', 'tour', 'ensemble immobilier', 'copropriété',
            'parc d\'activités', 'zone industrielle', 'campus', 'cité', 'village',
            'lotissement', 'ensemble', 'bloc', 'bâtiment', 'structure'
        ]
        
        return any(mot_cle in nom_lower for mot_cle in mots_cles_unites)
    
    def get_suggestion_unites(self):
        """Retourne un message de suggestion pour la création d'unités."""
        if self.necessite_unites_locatives():
            return f"Ce type de bien ({self.nom}) contient généralement plusieurs unités locatives. " \
                   f"Souhaitez-vous créer des unités locatives pour cette propriété ?"
        return None


class Bailleur(DuplicatePreventionMixin, models.Model):
    """Modèle pour les bailleurs."""
    
    # Champs à vérifier pour les doublons
    duplicate_check_fields = ['email', 'telephone']
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
    telephone = models.CharField(max_length=30, verbose_name=_("Téléphone"))
    telephone_mobile = models.CharField(max_length=30, blank=True, verbose_name=_("Mobile"))
    
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
        app_label = 'proprietes'
        verbose_name = _("Bailleur")
        verbose_name_plural = _("Bailleurs")
        ordering = ['nom', 'prenom']
    
    objects = NonDeletedManager()
    
    def __str__(self):
        return f"{self.get_nom_complet()} ({self.numero_bailleur})"

    def save(self, *args, **kwargs):
        # Numéro séquentiel: BAI-YYYY-0001
        if not self.numero_bailleur or self.numero_bailleur in ("", "BL0001"):
            annee = timezone.now().year
            next_num = AutoNumberSequence.next_number(scope='BAILLEUR', year=annee)
            self.numero_bailleur = f"BAI-{annee}-{next_num:04d}"
        super().save(*args, **kwargs)
    
    def get_nom_complet(self):
        return f"{self.civilite} {self.prenom} {self.nom}"
    
    def get_absolute_url(self):
        return reverse('proprietes:detail_bailleur', kwargs={'pk': self.pk})
    
    def a_des_proprietes_louees(self):
        """
        Vérifie si le bailleur a des propriétés louées (avec contrats actifs).
        Retourne True si le bailleur a au moins une propriété louée, False sinon.
        """
        from contrats.models import Contrat
        
        # Vérifier les propriétés avec contrats actifs
        proprietes_louees = self.proprietes.filter(
            contrats__est_actif=True,
            contrats__est_resilie=False,
            contrats__is_deleted=False
        ).distinct()
        
        return proprietes_louees.exists()
    
    def get_proprietes_louees(self):
        """
        Retourne toutes les propriétés louées du bailleur (avec contrats actifs).
        """
        from contrats.models import Contrat
        
        return self.proprietes.filter(
            contrats__est_actif=True,
            contrats__est_resilie=False,
            contrats__is_deleted=False
        ).distinct().order_by('adresse')
    
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


class Locataire(DuplicatePreventionMixin, models.Model):
    """Modèle pour les locataires."""
    
    # Champs à vérifier pour les doublons
    duplicate_check_fields = ['email', 'telephone', 'telephone_mobile']
    CIVILITE_CHOICES = [
        ('M', 'Monsieur'),
        ('Mme', 'Madame'),
        ('Mlle', 'Mademoiselle'),
        ('Mademoiselle', 'Mademoiselle'),
        ('Societe', 'Société'),
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
    type_personne = models.CharField(
        max_length=20,
        choices=[
            ('physique', 'Personne physique'),
            ('societe', 'Société/Personne morale'),
        ],
        default='physique',
        verbose_name=_("Type de personne")
    )
    civilite = models.CharField(
        max_length=50,
        choices=CIVILITE_CHOICES,
        blank=True,
        null=True,
        verbose_name=_("Civilité")
    )
    nom = models.CharField(max_length=100, verbose_name=_("Nom"))
    prenom = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Prénom"))
    date_naissance = models.DateField(blank=True, null=True, verbose_name=_("Date de naissance"))
    
    # Contact
    email = models.EmailField(blank=True, null=True, verbose_name=_("Email"))
    telephone = models.CharField(max_length=30, verbose_name=_("Téléphone"))
    telephone_mobile = models.CharField(max_length=30, blank=True, verbose_name=_("Mobile"))
    
    # Adresse
    adresse = models.TextField(blank=True, null=True, verbose_name=_("Adresse"))
    code_postal = models.CharField(max_length=10, blank=True, null=True, verbose_name=_("Code postal"))
    ville = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Ville"))
    pays = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Pays"))
    
    # Informations professionnelles
    numero_cnib = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Numéro CNIB/CNI"))
    profession = models.CharField(max_length=100, blank=True, verbose_name=_("Profession"))
    employeur = models.CharField(max_length=100, blank=True, verbose_name=_("Employeur"))
    revenus_mensuels = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name=_("Revenus mensuels")
    )
    
    # Informations du garant
    garant_civilite = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name=_("Civilité du garant")
    )
    garant_nom = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Nom du garant"))
    garant_prenom = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Prénom du garant"))
    garant_telephone = models.CharField(max_length=30, blank=True, null=True, verbose_name=_("Téléphone du garant"))
    garant_email = models.EmailField(blank=True, null=True, verbose_name=_("Email du garant"))
    garant_profession = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Profession du garant"))
    garant_employeur = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Employeur du garant"))
    garant_revenus_mensuels = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name=_("Revenus mensuels du garant")
    )
    garant_adresse = models.TextField(blank=True, null=True, verbose_name=_("Adresse du garant"))
    garant_code_postal = models.CharField(max_length=10, blank=True, null=True, verbose_name=_("Code postal du garant"))
    garant_ville = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Ville du garant"))
    garant_pays = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Pays du garant"))
    
    # Pièce d'identité du garant
    garant_piece_identite = models.FileField(
        upload_to='garants/pieces_identite/',
        blank=True,
        null=True,
        verbose_name=_("Pièce d'identité du garant")
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
        app_label = 'proprietes'
        verbose_name = _("Locataire")
        verbose_name_plural = _("Locataires")
        ordering = ['nom', 'prenom']
    
    objects = NonDeletedManager()
    
    def __str__(self):
        return f"{self.get_nom_complet()} ({self.numero_locataire})"

    def save(self, *args, **kwargs):
        # Numéro séquentiel: LOC-YYYY-0001
        if not self.numero_locataire or self.numero_locataire in ("", "LT0001"):
            annee = timezone.now().year
            next_num = AutoNumberSequence.next_number(scope='LOCATAIRE', year=annee)
            self.numero_locataire = f"LOC-{annee}-{next_num:04d}"
        super().save(*args, **kwargs)
    
    def get_nom_complet(self):
        """Retourne le nom complet en gérant les cas où le prénom est vide (personnes morales)"""
        if self.prenom:
            return f"{self.civilite} {self.prenom} {self.nom}"
        else:
            # Pour les personnes morales ou sans prénom
            return f"{self.civilite} {self.nom}"
    
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

    def a_des_contrats_actifs(self):
        """
        Vérifie si le locataire a des contrats actifs.
        Retourne True si le locataire a des contrats actifs, False sinon.
        """
        from contrats.models import Contrat
        from django.utils import timezone
        
        # Vérifier les contrats actifs (non résiliés et non supprimés)
        contrats_actifs = self.contrats.filter(
            est_actif=True,
            est_resilie=False,
            is_deleted=False
        )
        
        return contrats_actifs.exists()
    
    def get_contrats_actifs(self):
        """
        Retourne tous les contrats actifs du locataire.
        """
        from contrats.models import Contrat
        from django.utils import timezone
        
        return self.contrats.filter(
            est_actif=True,
            est_resilie=False,
            is_deleted=False
        ).order_by('-date_debut')
    
    def peut_etre_supprime_definitivement(self):
        """
        Vérifie si le locataire peut être supprimé définitivement.
        Un locataire peut être supprimé définitivement seulement s'il n'a aucun contrat actif.
        """
        return not self.a_des_contrats_actifs()


class Propriete(models.Model):
    """Modèle pour les propriétés immobilières."""
    ETAT_CHOICES = [
        ('excellent', 'Excellent'),
        ('tres_bon', 'Très bon'),
        ('bon', 'Bon'),
        ('moyen', 'Moyen'),
        ('a_renover', 'À rénover'),
    ]
    
    TYPE_GESTION_CHOICES = [
        ('propriete_entiere', 'Propriété entière (louable en une seule fois)'),
        ('unites_multiples', 'Propriété avec unités locatives multiples'),
    ]
    
    # Informations de base
    numero_propriete = models.CharField(
        max_length=50,  # Augmenté pour supporter les IDs avec timestamp/UUID
        unique=True,
        default='PR0001',
        verbose_name=_("Numéro propriété"),
        help_text=_("Identifiant unique de la propriété"),
        db_index=True  # Index pour les performances
    )
    titre = models.CharField(max_length=200, verbose_name=_("Titre"))
    description = models.TextField(blank=True, verbose_name=_("Description"))
    
    # Localisation
    adresse = models.TextField(blank=True, null=True, verbose_name=_("Adresse"))
    code_postal = models.CharField(max_length=10, blank=True, null=True, verbose_name=_("Code postal"))
    ville = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Ville"))
    quartier = models.CharField(
        max_length=100, 
        blank=True, 
        null=True, 
        verbose_name=_("Quartier"),
        help_text=_("Quartier ou secteur où se trouve la propriété (très important pour la localisation)"),
        default=""  # Valeur par défaut pour éviter les erreurs
    )
    pays = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Pays"))
    
    # Caractéristiques
    type_bien = models.ForeignKey(
        TypeBien,
        on_delete=models.PROTECT,
        verbose_name=_("Type de bien")
    )
    type_gestion = models.CharField(
        max_length=20,
        choices=TYPE_GESTION_CHOICES,
        default='propriete_entiere',
        verbose_name=_("Type de gestion"),
        help_text=_("Définit si la propriété est louable entièrement ou par unités multiples")
    )
    surface = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name=_("Surface (m²)"),
        help_text=_("Surface en mètres carrés (optionnel)")
    )
    nombre_pieces = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name=_("Nombre de pièces")
    )
    nombre_chambres = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name=_("Nombre de chambres")
    )
    nombre_salles_bain = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name=_("Nombre de salles de bain")
    )
    
    # Équipements
    ascenseur = models.BooleanField(default=False, verbose_name=_("Ascenseur"))
    parking = models.BooleanField(default=False, verbose_name=_("Parking"))
    balcon = models.BooleanField(default=False, verbose_name=_("Balcon"))
    jardin = models.BooleanField(default=False, verbose_name=_("Jardin"))
    cuisine = models.BooleanField(default=False, verbose_name=_("Cuisine"))
    
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
        blank=True,
        null=True,
        verbose_name=_("Loyer mensuel")
    )
    charges_locataire = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        null=True,
        blank=True,
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
        app_label = 'proprietes'
        verbose_name = _("Propriété")
        verbose_name_plural = _("Propriétés")
        ordering = ['-date_creation']
    
    objects = NonDeletedManager()
    
    def __str__(self):
        return f"{self.titre} - {self.numero_propriete}"
    
    def get_absolute_url(self):
        return reverse('proprietes:detail', kwargs={'pk': self.pk})
    
    def est_propriete_entiere(self):
        """Vérifie si c'est une propriété louable entièrement."""
        return self.type_gestion == 'propriete_entiere'
    
    def est_avec_unites_multiples(self):
        """Vérifie si c'est une propriété avec unités locatives multiples."""
        return self.type_gestion == 'unites_multiples'
    
    def get_pieces_louables_individuellement(self):
        """
        Retourne les pièces qui peuvent être louées individuellement.
        Seulement pour les propriétés avec unités multiples.
        """
        if not self.est_avec_unites_multiples():
            return self.pieces.none()
        return self.pieces.filter(
            unite_locative__isnull=True,
            is_deleted=False
        )
    
    def get_unites_locatives(self):
        """
        Retourne les unités locatives de cette propriété.
        Seulement pour les propriétés avec unités multiples.
        """
        if not self.est_avec_unites_multiples():
            return self.unites_locatives.none()
        return self.unites_locatives.filter(is_deleted=False)
    
    def est_disponible_pour_location(self):
        """
        Vérifie si la propriété est disponible pour une nouvelle location.
        La logique diffère selon le type de gestion :
        - Propriété entière : vérifie s'il n'y a pas de contrat actif sur la propriété complète
        - Unités multiples : vérifie s'il y a des unités locatives ou pièces disponibles
        """
        from django.utils import timezone
        from contrats.models import Contrat
        
        if self.est_propriete_entiere():
            # Pour une propriété entière, vérifier s'il n'y a pas de contrat actif
            contrats_actifs = Contrat.objects.filter(
                propriete=self,
                est_actif=True,
                est_resilie=False,
                date_debut__lte=timezone.now().date(),
                date_fin__gte=timezone.now().date(),
                is_deleted=False,
                unite_locative__isnull=True  # Pas d'unité locative = propriété complète
            ).exists()
            
            return self.disponible and not contrats_actifs
            
        elif self.est_avec_unites_multiples():
            # Pour les propriétés avec unités multiples, vérifier les unités et pièces disponibles
            unites_disponibles = self.get_unites_locatives().filter(
                statut='disponible'
            ).exclude(
                contrats__est_actif=True,
                contrats__est_resilie=False,
                contrats__date_debut__lte=timezone.now().date(),
                contrats__date_fin__gte=timezone.now().date(),
                contrats__is_deleted=False
            ).exists()
            
            pieces_disponibles = self.get_pieces_louables_individuellement().filter(
                statut='disponible'
            ).exclude(
                contrats__est_actif=True,
                contrats__est_resilie=False,
                contrats__date_debut__lte=timezone.now().date(),
                contrats__date_fin__gte=timezone.now().date(),
                contrats__is_deleted=False
            ).exists()
            
            return unites_disponibles or pieces_disponibles
        
        return False
    
    def get_unites_locatives_disponibles(self):
        """
        Retourne les unités locatives vraiment disponibles pour cette propriété.
        Exclut celles qui sont déjà louées par des contrats actifs.
        """
        from django.utils import timezone
        from contrats.models import Contrat
        
        return self.unites_locatives.filter(
            statut='disponible',
            is_deleted=False
        ).exclude(
            contrats__est_actif=True,
            contrats__est_resilie=False,
            contrats__date_debut__lte=timezone.now().date(),
            contrats__date_fin__gte=timezone.now().date(),
            contrats__is_deleted=False
        )
    
    def get_pieces_disponibles(self):
        """
        Retourne les pièces vraiment disponibles pour cette propriété.
        Exclut celles qui sont déjà louées par des contrats actifs.
        """
        from django.utils import timezone
        from contrats.models import Contrat
        
        return self.pieces.filter(
            statut='disponible',
            is_deleted=False
        ).exclude(
            contrats__est_actif=True,
            contrats__est_resilie=False,
            contrats__date_debut__lte=timezone.now().date(),
            contrats__date_fin__gte=timezone.now().date(),
            contrats__is_deleted=False
        )
    
    def get_contrats_actifs(self):
        """
        Retourne les contrats actifs pour cette propriété.
        """
        from django.utils import timezone
        from contrats.models import Contrat
        
        return Contrat.objects.filter(
            propriete=self,
            est_actif=True,
            est_resilie=False,
            date_debut__lte=timezone.now().date(),
            date_fin__gte=timezone.now().date(),
            is_deleted=False
        )
    
    def get_contrats_propriete_complete(self):
        """
        Retourne les contrats actifs qui couvrent la propriété entière.
        """
        return self.get_contrats_actifs().filter(unite_locative__isnull=True)
    
    def get_contrats_unites_locatives(self):
        """
        Retourne les contrats actifs sur les unités locatives de cette propriété.
        """
        return self.get_contrats_actifs().filter(unite_locative__isnull=False)
    
    def get_statut_disponibilite(self):
        """
        Retourne le statut de disponibilité de la propriété.
        """
        if not self.est_disponible_pour_location():
            contrats_propriete_complete = self.get_contrats_propriete_complete()
            if contrats_propriete_complete.exists():
                return "Entièrement occupée"
            
            # Vérifier si toutes les unités sont louées individuellement
            unites_disponibles = self.get_unites_locatives_disponibles()
            pieces_disponibles = self.get_pieces_disponibles()
            
            if not unites_disponibles.exists() and not pieces_disponibles.exists():
                return "Toutes les unités/pièces sont louées"
            else:
                return "Partiellement disponible"
        return "Disponible"
    
    def necessite_unites_locatives(self):
        """
        Détermine si cette propriété nécessite des unités locatives.
        Basé sur le type de bien et les caractéristiques de la propriété.
        """
        try:
            # Vérifier d'abord le type de bien
            if self.type_bien and self.type_bien.necessite_unites_locatives():
                return True
            
            # Vérifier les caractéristiques de la propriété
            # Grande surface ou nombreuses pièces peuvent indiquer plusieurs unités
            if self.surface and self.surface > 200:  # Plus de 200m²
                return True
            
            if self.nombre_pieces and self.nombre_pieces > 8:  # Plus de 8 pièces
                return True
        except Exception as e:
            # En cas d'erreur, retourner False par défaut
            return False
        
        return False
    
    def get_suggestion_creation_unites(self):
        """Retourne un message de suggestion personnalisé pour cette propriété."""
        try:
            if self.necessite_unites_locatives():
                suggestions = []
                
                # Suggestion basée sur le type
                if self.type_bien:
                    type_suggestion = self.type_bien.get_suggestion_unites()
                    if type_suggestion:
                        suggestions.append(type_suggestion)
                
                # Suggestions basées sur les caractéristiques
                if self.surface and self.surface > 200:
                    suggestions.append(f"Avec {self.surface}m², cette propriété pourrait être divisée en plusieurs unités.")
                
                if self.nombre_pieces and self.nombre_pieces > 8:
                    suggestions.append(f"Avec {self.nombre_pieces} pièces, vous pourriez créer plusieurs unités locatives.")
                
                return " ".join(suggestions)
        except Exception as e:
            # En cas d'erreur, retourner None pour éviter de casser la page
            return None
        
        return None
    
    def get_loyer_total(self):
        """Retourne le loyer total (loyer + charges)."""
        loyer = self.loyer_actuel or 0
        charges = self.charges_locataire or 0
        return loyer + charges
    
    def get_loyer_actuel_calcule(self):
        """Calcule le loyer actuel basé sur les unités locatives ou le loyer direct."""
        from decimal import Decimal
        
        # Si la propriété a des unités locatives, calculer à partir des contrats des unités
        unites_locatives = self.unites_locatives.filter(is_deleted=False)
        
        if unites_locatives.exists():
            loyer_total = Decimal('0')
            
            for unite in unites_locatives:
                # Récupérer les contrats actifs de cette unité
                contrats_unite = unite.contrats.filter(
                    est_actif=True,
                    est_resilie=False
                )
                
                if contrats_unite.exists():
                    for contrat in contrats_unite:
                        contrat_loyer = Decimal(str(contrat.loyer_mensuel or '0'))
                        contrat_charges = Decimal(str(contrat.charges_mensuelles or '0'))
                        loyer_total += contrat_loyer + contrat_charges
                else:
                    # Si pas de contrat, utiliser les montants de l'unité
                    unite_loyer = Decimal(str(unite.loyer_mensuel or '0'))
                    unite_charges = Decimal(str(unite.charges_mensuelles or '0'))
                    loyer_total += unite_loyer + unite_charges
            
            return loyer_total
        else:
            # Si pas d'unités, chercher un contrat direct sur la propriété
            contrat_actif = self.contrats.filter(
                est_actif=True,
                est_resilie=False
            ).first()
            
            if contrat_actif:
                contrat_loyer = Decimal(str(contrat_actif.loyer_mensuel or '0'))
                contrat_charges = Decimal(str(contrat_actif.charges_mensuelles or '0'))
                return contrat_loyer + contrat_charges
            else:
                # Retourner le loyer_actuel de la propriété
                return Decimal(str(self.loyer_actuel or '0'))
    
    def get_charges_bailleur_en_cours(self):
        """Retourne le montant total des charges bailleur en cours pour cette propriété."""
        from django.db.models import Sum
        
        total = ChargesBailleur.objects.filter(
            propriete=self,
            statut__in=['en_attente', 'deduite_retrait']
        ).aggregate(
            total=Sum('montant_restant')
        )['total']
        
        return total or 0
    
    def get_total_mensuel_bailleur(self):
        """
        Retourne le montant total mensuel que le bailleur doit recevoir
        pour toutes ses propriétés louées (loyers - charges déductibles).
        """
        from django.db.models import Sum
        from contrats.models import Contrat
        
        # Calculer le total des loyers de toutes les propriétés du bailleur
        total_loyers = Propriete.objects.filter(
            bailleur=self.bailleur,
            is_deleted=False
        ).aggregate(
            total=Sum('loyer_actuel')
        )['total'] or 0
        
        # Calculer le total des charges déductibles de toutes les propriétés du bailleur
        total_charges_deductibles = Contrat.objects.filter(
            propriete__bailleur=self.bailleur,
            est_actif=True
        ).aggregate(
            total=Sum('charges_deductibles')
        )['total'] or 0
        
        # Calculer le total des charges bailleur de toutes les propriétés du bailleur
        total_charges_bailleur = ChargesBailleur.objects.filter(
            propriete__bailleur=self.bailleur,
            statut__in=['en_attente', 'deduite_retrait']
        ).aggregate(
            total=Sum('montant_restant')
        )['total'] or 0
        
        # Montant net = loyers - charges déductibles - charges bailleur
        montant_net = total_loyers - total_charges_deductibles - total_charges_bailleur
        
        return max(0, montant_net)  # Ne pas retourner de montant négatif
    
    def get_nombre_unites_locatives(self):
        """Retourne le nombre d'unités locatives dans cette propriété."""
        return self.unites_locatives.filter(is_deleted=False).count()
    
    def get_unites_disponibles(self):
        """Retourne les unités locatives disponibles."""
        return self.unites_locatives.filter(
            statut='disponible',
            is_deleted=False
        )
    
    def get_unites_occupees(self):
        """Retourne les unités locatives occupées."""
        return self.unites_locatives.filter(
            statut='occupee',
            is_deleted=False
        )
    
    def get_taux_occupation_global(self):
        """Calcule le taux d'occupation global de la propriété."""
        total_unites = self.get_nombre_unites_locatives()
        if total_unites == 0:
            return 0
        unites_occupees = self.get_unites_occupees().count()
        return round((unites_occupees / total_unites) * 100, 2)
    
    def get_revenus_mensuels_potentiels(self):
        """Calcule les revenus mensuels potentiels de toutes les unités."""
        from django.db.models import Sum
        revenus = self.unites_locatives.filter(
            is_deleted=False
        ).aggregate(
            total_loyers=Sum('loyer_mensuel'),
            total_charges=Sum('charges_mensuelles')
        )
        
        loyers_total = revenus['total_loyers'] or 0
        charges_total = revenus['total_charges'] or 0
        return loyers_total + charges_total
    
    def get_revenus_mensuels_actuels(self):
        """Calcule les revenus mensuels actuels (unités occupées seulement)."""
        from django.db.models import Sum
        revenus = self.unites_locatives.filter(
            statut='occupee',
            is_deleted=False
        ).aggregate(
            total_loyers=Sum('loyer_mensuel'),
            total_charges=Sum('charges_mensuelles')
        )
        
        loyers_total = revenus['total_loyers'] or 0
        charges_total = revenus['total_charges'] or 0
        return loyers_total + charges_total
    
    def est_grande_propriete(self):
        """Détermine si c'est une grande propriété (plus de 5 unités)."""
        return self.get_nombre_unites_locatives() > 5
    
    def get_statistiques_unites(self):
        """Retourne des statistiques détaillées sur les unités."""
        from django.db.models import Count, Sum, Avg
        
        stats = self.unites_locatives.filter(is_deleted=False).aggregate(
            total_unites=Count('id'),
            unites_disponibles=Count('id', filter=models.Q(statut='disponible')),
            unites_occupees=Count('id', filter=models.Q(statut='occupee')),
            unites_reservees=Count('id', filter=models.Q(statut='reservee')),
            unites_renovation=Count('id', filter=models.Q(statut='en_renovation')),
            surface_totale=Sum('surface'),
            loyer_moyen=Avg('loyer_mensuel'),
            revenus_potentiels=Sum('loyer_mensuel') + Sum('charges_mensuelles')
        )
        
        if stats['total_unites'] > 0:
            stats['taux_occupation'] = round(
                (stats['unites_occupees'] / stats['total_unites']) * 100, 2
            )
        else:
            stats['taux_occupation'] = 0
            
        return stats
    
    def get_taux_occupation_global(self):
        """Calcule le taux d'occupation global de la propriété."""
        stats = self.get_statistiques_unites()
        return stats.get('taux_occupation', 0)


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
        app_label = 'proprietes'
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
        max_length=50,
        unique=True,
        blank=True,
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
    
    # Informations de déduction
    motif_deduction = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name=_("Motif de la déduction"),
        help_text=_("Raison de la déduction du retrait mensuel")
    )
    notes_deduction = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Notes de déduction"),
        help_text=_("Commentaires sur la déduction")
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
        app_label = 'proprietes'
        verbose_name = _("Charge bailleur")
        verbose_name_plural = _("Charges bailleur")
        ordering = ['-date_charge']
    
    def __str__(self):
        return f"{self.titre} - {self.montant} F CFA"
    
    def get_absolute_url(self):
        return reverse('proprietes:detail_charge_bailleur', kwargs={'pk': self.pk})
    
    def is_en_retard(self):
        """Vérifie si la charge est en retard."""
        if self.date_echeance and self.statut == 'en_attente':
            from django.utils import timezone
            return timezone.now().date() > self.date_echeance
        return False
    
    def generer_numero_charge_unique(self):
        """
        Génère un numéro de charge unique de manière thread-safe
        """
        from django.db import transaction
        from datetime import datetime
        import uuid
        import time
        
        # Utiliser un UUID complet pour garantir l'unicité absolue
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        microseconds = int(time.time() * 1000000) % 1000000  # Microsecondes pour plus de précision
        unique_id = str(uuid.uuid4()).replace('-', '')[:8]  # UUID court pour le format
        numero = f"CHG-{timestamp}-{microseconds:06d}-{unique_id}"
        
        # Vérifier l'unicité avec retry automatique
        max_retries = 5
        retry_count = 0
        
        with transaction.atomic():
            while ChargesBailleur.objects.filter(numero_charge=numero).exists() and retry_count < max_retries:
                retry_count += 1
                # Générer un nouveau numéro avec plus de randomisation
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                microseconds = int(time.time() * 1000000) % 1000000
                unique_id = str(uuid.uuid4()).replace('-', '')[:8]
                numero = f"CHG-{timestamp}-{microseconds:06d}-{unique_id}"
        
        # Si on arrive ici et que le numéro existe encore, utiliser un UUID pur
        if ChargesBailleur.objects.filter(numero_charge=numero).exists():
            numero = f"CHG-{str(uuid.uuid4()).replace('-', '')}"
        
        return numero

    def save(self, *args, **kwargs):
        """Override save pour calculer automatiquement le montant restant et générer un numéro unique."""
        from django.db import IntegrityError
        import uuid
        
        # Générer le numéro de charge si nécessaire
        if not self.numero_charge or self.numero_charge == 'CH0001':
            self.numero_charge = self.generer_numero_charge_unique()
        
        # Calculer le montant restant
        if self.montant and self.montant_deja_deduit is not None:
            self.montant_restant = self.montant - self.montant_deja_deduit
            
            # Mettre à jour le statut automatiquement
            if self.montant_restant <= 0:
                self.statut = 'remboursee'
            elif self.montant_deja_deduit > 0:
                self.statut = 'deduite_retrait'
        
        # Tentative de sauvegarde avec gestion des conflits
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                super().save(*args, **kwargs)
                break  # Succès, sortir de la boucle
            except IntegrityError as e:
                if 'numero_charge' in str(e) and retry_count < max_retries - 1:
                    # Conflit sur numero_charge, générer un nouveau numéro
                    retry_count += 1
                    self.numero_charge = f"CHG-{str(uuid.uuid4()).replace('-', '')}"
                else:
                    # Autre erreur ou max retries atteint
                    raise e
    
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
            from core.models import AuditLog
            from django.contrib.contenttypes.models import ContentType
            content_type = ContentType.objects.get_for_model(ChargesBailleur)
            AuditLog.objects.create(
                content_type=content_type,
                object_id=self.id,
                action='update',
                user=self.cree_par,
                details={
                    'description': f'Déduction de {montant_deduit} F CFA du retrait mensuel',
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
    
    def get_statut_color(self):
        """Retourne la couleur CSS selon le statut."""
        colors = {
            'en_attente': 'warning',
            'payee': 'success',
            'remboursee': 'info',
            'deduite_retrait': 'primary',
            'annulee': 'danger'
        }
        return colors.get(self.statut, 'secondary')
    
    def get_priorite_color(self):
        """Retourne la couleur CSS selon la priorité."""
        colors = {
            'basse': 'success',
            'normale': 'info',
            'haute': 'warning',
            'urgente': 'danger'
        }
        return colors.get(self.priorite, 'secondary')
    
    def est_en_retard(self):
        """Vérifie si la charge est en retard de paiement."""
        if self.date_echeance and self.statut == 'en_attente':
            from django.utils import timezone
            return timezone.now().date() > self.date_echeance
        return False
    
    def get_jours_retard(self):
        """Retourne le nombre de jours de retard."""
        if self.est_en_retard():
            from django.utils import timezone
            return (timezone.now().date() - self.date_echeance).days
        return 0
    
    def peut_etre_annulee(self):
        """Vérifie si la charge peut être annulée."""
        return self.statut in ['en_attente']
    
    def peut_etre_modifiee(self):
        """Vérifie si la charge peut être modifiée."""
        return self.statut in ['en_attente']
    
    def get_montant_restant_pourcentage(self):
        """Retourne le pourcentage du montant restant par rapport au montant total."""
        if self.montant <= 0:
            return 0
        return (self.montant_restant / self.montant) * 100
    
    def get_historique_deductions(self):
        """Retourne l'historique des déductions pour cette charge."""
        try:
            from core.models import AuditLog
            from django.contrib.contenttypes.models import ContentType
            content_type = ContentType.objects.get_for_model(ChargesBailleur)
            return AuditLog.objects.filter(
                content_type=content_type,
                object_id=self.id,
                action='update'
            ).order_by('-timestamp')
        except Exception:
            return []
    
    def get_impact_sur_retrait(self, mois_retrait=None):
        """
        Calcule l'impact de cette charge sur un retrait mensuel.
        
        Args:
            mois_retrait: Mois du retrait (par défaut: mois de la charge)
            
        Returns:
            Dict contenant l'impact calculé
        """
        from decimal import Decimal
        from django.utils import timezone
        
        if mois_retrait is None:
            mois_retrait = self.date_charge.replace(day=1)
        
        # Vérifier si la charge est dans le bon mois
        if (self.date_charge.year != mois_retrait.year or 
            self.date_charge.month != mois_retrait.month):
            return {
                'impact': Decimal('0'),
                'raison': 'Charge hors période'
            }
        
        # Vérifier si la charge peut être déduite
        if not self.peut_etre_deduit():
            return {
                'impact': Decimal('0'),
                'raison': 'Charge non déductible'
            }
        
        return {
            'impact': self.get_montant_deductible(),
            'raison': 'Charge déductible',
            'montant_total': self.montant,
            'montant_deja_deduit': self.montant_deja_deduit,
            'montant_restant': self.montant_restant,
            'progression': self.get_progression_deduction()
        }
    
    def get_resume_financier(self):
        """Retourne un résumé financier de la charge."""
        return {
            'montant_total': self.montant,
            'montant_deja_deduit': self.montant_deja_deduit,
            'montant_restant': self.montant_restant,
            'progression_deduction': self.get_progression_deduction(),
            'statut': self.get_statut_display(),
            'priorite': self.get_priorite_display(),
            'peut_etre_deduit': self.peut_etre_deduit(),
            'est_en_retard': self.est_en_retard(),
            'jours_retard': self.get_jours_retard()
        }


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
        app_label = 'proprietes'
        verbose_name = _("Liaison charge bailleur - retrait")
        verbose_name_plural = _("Liaisons charges bailleur - retraits")
        unique_together = ['charge_bailleur', 'retrait_bailleur']
        ordering = ['-date_deduction']
    
    def __str__(self):
        return f"{self.charge_bailleur.titre} - {self.retrait_bailleur} - {self.montant_deduit} F CFA"
    
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
        app_label = 'proprietes'
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


class UniteLocative(models.Model):
    """Modèle pour gérer les unités locatives (appartements, bureaux, etc.) dans les grandes propriétés."""
    
    TYPE_UNITE_CHOICES = [
        ('appartement', 'Appartement'),
        ('studio', 'Studio'),
        ('bureau', 'Bureau'),
        ('local_commercial', 'Local commercial'),
        ('chambre', 'Chambre meublée'),
        ('parking', 'Place de parking'),
        ('cave', 'Cave/Débarras'),
        ('autre', 'Autre'),
    ]
    
    STATUT_CHOICES = [
        ('disponible', 'Disponible'),
        ('occupee', 'Occupée'),
        ('reservee', 'Réservée'),
        ('en_renovation', 'En rénovation'),
        ('hors_service', 'Hors service'),
    ]
    
    # Informations de base
    propriete = models.ForeignKey(
        Propriete,
        on_delete=models.CASCADE,
        related_name='unites_locatives',
        verbose_name=_("Propriété")
    )
    bailleur = models.ForeignKey(
        Bailleur,
        on_delete=models.PROTECT,
        related_name='unites_locatives',
        blank=True,
        null=True,
        verbose_name=_("Bailleur"),
        help_text=_("Bailleur spécifique pour cette unité (optionnel, par défaut celui de la propriété)")
    )
    numero_unite = models.CharField(
        max_length=20,
        verbose_name=_("Numéro d'unité"),
        help_text=_("Ex: Apt 101, Bureau 205, Chambre A12")
    )
    nom = models.CharField(
        max_length=100, 
        verbose_name=_("Nom de l'unité"),
        help_text=_("Nom descriptif de l'unité")
    )
    type_unite = models.CharField(
        max_length=20,
        choices=TYPE_UNITE_CHOICES,
        verbose_name=_("Type d'unité")
    )
    
    # Caractéristiques physiques
    etage = models.IntegerField(
        blank=True, 
        null=True, 
        verbose_name=_("Étage"),
        help_text=_("Numéro d'étage (0 pour RDC, -1 pour sous-sol)")
    )
    surface = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name=_("Surface (m²)")
    )
    nombre_pieces = models.PositiveIntegerField(
        default=1,
        verbose_name=_("Nombre de pièces")
    )
    nombre_chambres = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Nombre de chambres")
    )
    nombre_salles_bain = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Nombre de salles de bain")
    )
    
    # Équipements et caractéristiques
    meuble = models.BooleanField(default=False, verbose_name=_("Meublé"))
    balcon = models.BooleanField(default=False, verbose_name=_("Balcon/Terrasse"))
    parking_inclus = models.BooleanField(default=False, verbose_name=_("Parking inclus"))
    climatisation = models.BooleanField(default=False, verbose_name=_("Climatisation"))
    internet_inclus = models.BooleanField(default=False, verbose_name=_("Internet inclus"))
    
    # Informations financières
    loyer_mensuel = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00,
        verbose_name=_("Loyer mensuel")
    )
    charges_mensuelles = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name=_("Charges mensuelles")
    )
    caution_demandee = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00,
        verbose_name=_("Caution demandée")
    )
    
    # État et disponibilité
    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='disponible',
        verbose_name=_("Statut")
    )
    date_disponibilite = models.DateField(
        blank=True,
        null=True,
        verbose_name=_("Date de disponibilité")
    )
    
    # Informations complémentaires
    description = models.TextField(
        blank=True, 
        verbose_name=_("Description"),
        help_text=_("Description détaillée de l'unité")
    )
    notes_privees = models.TextField(
        blank=True, 
        verbose_name=_("Notes privées"),
        help_text=_("Notes internes non visibles par les locataires")
    )
    
    # Métadonnées
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name=_("Date de création"))
    date_modification = models.DateTimeField(auto_now=True, verbose_name=_("Date de modification"))
    is_deleted = models.BooleanField(default=False, verbose_name=_("Supprimé logiquement"))
    
    class Meta:
        app_label = 'proprietes'
        verbose_name = _("Unité locative")
        verbose_name_plural = _("Unités locatives")
        ordering = ['propriete', 'etage', 'numero_unite']
        unique_together = ['propriete', 'numero_unite']
    
    objects = NonDeletedManager()
    
    def __str__(self):
        return f"{self.numero_unite} - {self.propriete.titre}"
    
    def get_absolute_url(self):
        return reverse('proprietes:unite_detail', kwargs={'pk': self.pk})
    
    def get_loyer_total(self):
        """Retourne le loyer total (loyer + charges)."""
        loyer = self.loyer_mensuel or 0
        charges = self.charges_mensuelles or 0
        return loyer + charges
    
    def get_loyer_total_formatted(self):
        """Retourne le loyer total formaté."""
        from core.utils import format_currency_fcfa
        return format_currency_fcfa(self.get_loyer_total())
    
    def est_disponible(self, date_debut=None, date_fin=None):
        """Vérifie si l'unité est disponible pour une période donnée."""
        if self.statut not in ['disponible', 'reservee']:
            return False
        
        from django.utils import timezone
        from contrats.models import Contrat
        
        if not date_debut:
            date_debut = timezone.now().date()
        if not date_fin:
            date_fin = date_debut + timezone.timedelta(days=365)
        
        # Vérifier les contrats actifs qui se chevauchent
        contrats_conflictuels = Contrat.objects.filter(
            unite_locative=self,
            est_actif=True,
            est_resilie=False,
            date_debut__lt=date_fin,
            date_fin__gt=date_debut
        ).exists()
        
        return not contrats_conflictuels
    
    def get_contrat_actuel(self):
        """Retourne le contrat actuel de cette unité."""
        from contrats.models import Contrat
        from django.utils import timezone
        
        return Contrat.objects.filter(
            unite_locative=self,
            est_actif=True,
            est_resilie=False,
            date_debut__lte=timezone.now().date(),
            date_fin__gte=timezone.now().date()
        ).first()
    
    def get_locataire_actuel(self):
        """Retourne le locataire actuel de cette unité."""
        contrat = self.get_contrat_actuel()
        return contrat.locataire if contrat else None
    
    @property
    def contrats_actifs(self):
        """Retourne tous les contrats actifs de cette unité."""
        from contrats.models import Contrat
        from django.utils import timezone
        
        return Contrat.objects.filter(
            unite_locative=self,
            est_actif=True,
            est_resilie=False,
            date_debut__lte=timezone.now().date(),
            date_fin__gte=timezone.now().date()
        )
    
    def get_bailleur_effectif(self):
        """Retourne le bailleur effectif (celui de l'unité ou celui de la propriété)."""
        return self.bailleur if self.bailleur else self.propriete.bailleur
    
    def get_revenus_potentiels_annuels(self):
        """Calcule les revenus potentiels annuels."""
        return self.get_loyer_total() * 12
    
    def get_taux_occupation(self):
        """Calcule le taux d'occupation de l'unité sur les 12 derniers mois."""
        from contrats.models import Contrat
        from django.utils import timezone
        from datetime import timedelta
        
        # Période d'analyse : 12 derniers mois
        fin_periode = timezone.now().date()
        debut_periode = fin_periode - timedelta(days=365)
        
        # Récupérer tous les contrats qui se chevauchent avec cette période
        contrats = Contrat.objects.filter(
            unite_locative=self,
            date_debut__lt=fin_periode,
            date_fin__gt=debut_periode
        )
        
        if not contrats.exists():
            return 0.0
        
        # Calculer les jours d'occupation
        jours_occupes = 0
        for contrat in contrats:
            # Calculer l'intersection entre le contrat et la période d'analyse
            debut_effectif = max(contrat.date_debut, debut_periode)
            fin_effective = min(contrat.date_fin, fin_periode)
            
            if debut_effectif < fin_effective:
                jours_occupes += (fin_effective - debut_effectif).days
        
        # Éviter le double comptage en cas de contrats qui se chevauchent
        jours_occupes = min(jours_occupes, 365)
        
        return round((jours_occupes / 365) * 100, 1)
    
    def get_duree_moyenne_occupation(self):
        """Calcule la durée moyenne d'occupation en mois."""
        from contrats.models import Contrat
        from django.db.models import Avg
        from django.utils import timezone
        
        # Récupérer les contrats terminés pour calculer la durée moyenne
        contrats_termines = Contrat.objects.filter(
            unite_locative=self,
            est_resilie=True
        ).exclude(date_fin__isnull=True)
        
        if not contrats_termines.exists():
            # Si pas de contrats terminés, calculer avec le contrat actuel
            contrat_actuel = self.get_contrat_actuel()
            if contrat_actuel:
                duree_actuelle = (timezone.now().date() - contrat_actuel.date_debut).days
                return round(duree_actuelle / 30.44, 1)  # Conversion en mois
            return 0.0
        
        # Calculer la durée moyenne des contrats terminés
        durees = []
        for contrat in contrats_termines:
            duree_jours = (contrat.date_fin - contrat.date_debut).days
            durees.append(duree_jours / 30.44)  # Conversion en mois
        
        if durees:
            return round(sum(durees) / len(durees), 1)
        
        return 0.0


class ReservationUnite(models.Model):
    """Modèle pour gérer les réservations d'unités locatives."""
    
    STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('confirmee', 'Confirmée'),
        ('annulee', 'Annulée'),
        ('expiree', 'Expirée'),
        ('convertie_contrat', 'Convertie en contrat'),
    ]
    
    # Informations de base
    unite_locative = models.ForeignKey(
        UniteLocative,
        on_delete=models.CASCADE,
        related_name='reservations',
        verbose_name=_("Unité locative")
    )
    locataire_potentiel = models.ForeignKey(
        Locataire,
        on_delete=models.CASCADE,
        related_name='reservations',
        verbose_name=_("Locataire potentiel")
    )
    
    # Dates
    date_reservation = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Date de réservation")
    )
    date_debut_souhaitee = models.DateField(
        verbose_name=_("Date de début souhaitée")
    )
    date_fin_prevue = models.DateField(
        blank=True,
        null=True,
        verbose_name=_("Date de fin prévue")
    )
    date_expiration = models.DateTimeField(
        verbose_name=_("Date d'expiration de la réservation"),
        help_text=_("Date limite pour confirmer la réservation")
    )
    
    # Informations financières
    montant_reservation = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name=_("Montant de réservation"),
        help_text=_("Montant versé pour réserver l'unité")
    )
    
    # Statut et notes
    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='en_attente',
        verbose_name=_("Statut")
    )
    notes = models.TextField(
        blank=True,
        verbose_name=_("Notes"),
        help_text=_("Notes sur la réservation")
    )
    convertir_en_contrat = models.BooleanField(
        default=False,
        verbose_name=_("Convertir en contrat"),
        help_text=_("Cocher pour convertir immédiatement cette réservation en contrat de bail")
    )
    
    # Métadonnées
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
        app_label = 'proprietes'
        verbose_name = _("Réservation d'unité")
        verbose_name_plural = _("Réservations d'unités")
        ordering = ['-date_reservation']
    
    objects = NonDeletedManager()
    
    def __str__(self):
        return f"Réservation {self.unite_locative.numero_unite} - {self.locataire_potentiel.nom}"
    
    def est_active(self):
        """Vérifie si la réservation est encore active."""
        from django.utils import timezone
        return (
            self.statut in ['en_attente', 'confirmee'] and
            self.date_expiration > timezone.now()
        )
    
    def est_expiree(self):
        """Vérifie si la réservation a expiré."""
        from django.utils import timezone
        return self.date_expiration <= timezone.now()
    
    def peut_etre_convertie_en_contrat(self):
        """Vérifie si la réservation peut être convertie en contrat."""
        return self.statut == 'confirmee' and self.est_active()
    
    def save(self, *args, **kwargs):
        # Mettre à jour le statut si expiré
        if self.est_expiree() and self.statut in ['en_attente', 'confirmee']:
            self.statut = 'expiree'
        
        # Mettre à jour le statut de l'unité si nécessaire
        if self.statut == 'confirmee' and self.unite_locative.statut == 'disponible':
            self.unite_locative.statut = 'reservee'
            self.unite_locative.save()
        elif self.statut in ['annulee', 'expiree'] and self.unite_locative.statut == 'reservee':
            # Vérifier s'il n'y a pas d'autres réservations actives
            autres_reservations = ReservationUnite.objects.filter(
                unite_locative=self.unite_locative,
                statut__in=['en_attente', 'confirmee']
            ).exclude(pk=self.pk).exists()
            
            if not autres_reservations:
                self.unite_locative.statut = 'disponible'
                self.unite_locative.save()
        
        super().save(*args, **kwargs)


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
    unite_locative = models.ForeignKey(
        UniteLocative,
        on_delete=models.CASCADE,
        related_name='pieces',
        blank=True,
        null=True,
        verbose_name=_("Unité locative"),
        help_text=_("Unité locative à laquelle appartient cette pièce (optionnel)")
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
    
    # Gestion des espaces partagés
    est_espace_partage = models.BooleanField(
        default=False,
        verbose_name=_("Espace partagé"),
        help_text=_("Cochez si cette pièce est un espace partagé (cuisine, salon commun, etc.)")
    )
    acces_inclus_dans_pieces = models.ManyToManyField(
        'self',
        through='AccesEspacePartage',
        symmetrical=False,
        related_name='espaces_partages_accessibles',
        blank=True,
        verbose_name=_("Accès depuis les pièces"),
        help_text=_("Pièces qui ont accès à cet espace partagé")
    )
    cout_acces_mensuel = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0,
        verbose_name=_("Coût d'accès mensuel"),
        help_text=_("Coût mensuel pour l'accès à cet espace partagé (si applicable)")
    )
    
    # Métadonnées
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name=_("Date de création"))
    date_modification = models.DateTimeField(auto_now=True, verbose_name=_("Date de modification"))
    is_deleted = models.BooleanField(default=False, verbose_name=_("Supprimé logiquement"))
    
    class Meta:
        app_label = 'proprietes'
        verbose_name = _("Pièce")
        verbose_name_plural = _("Pièces")
        ordering = ['propriete', 'type_piece', 'numero_piece']
        unique_together = ['propriete', 'numero_piece']
    
    objects = NonDeletedManager()
    
    def __str__(self):
        return f"{self.nom} - {self.propriete.titre}"
    
    def get_absolute_url(self):
        return reverse('proprietes:piece_detail', kwargs={'pk': self.pk})
    
    def peut_etre_louee_individuellement(self):
        """
        Détermine si cette pièce peut être louée individuellement.
        Une pièce peut être louée individuellement si :
        1. La propriété est de type 'unites_multiples'
        2. La pièce n'est pas liée à une unité locative spécifique
        3. La pièce n'est pas un espace partagé
        """
        return (
            self.propriete.est_avec_unites_multiples() and
            self.unite_locative is None and
            not self.est_espace_partage
        )
    
    def est_dans_propriete_entiere(self):
        """
        Détermine si cette pièce fait partie d'une propriété louable entièrement.
        Dans ce cas, la pièce ne peut pas être louée individuellement.
        """
        return self.propriete.est_propriete_entiere()
    
    def get_statut_affichage(self):
        """
        Retourne le statut d'affichage de la pièce selon le type de propriété.
        Pour les propriétés entières, les pièces ne sont pas "disponibles" individuellement.
        """
        if self.est_dans_propriete_entiere():
            # Pour les propriétés entières, les pièces ne sont pas louables individuellement
            return "incluse dans la propriété"
        else:
            # Pour les propriétés avec unités multiples, afficher le statut normal
            return self.get_statut_display()
    
    def est_vraiment_disponible(self):
        """
        Vérifie si la pièce est vraiment disponible pour location.
        Pour les propriétés entières, retourne False car les pièces ne se louent pas individuellement.
        """
        if self.est_dans_propriete_entiere():
            return False
        
        if not self.peut_etre_louee_individuellement():
            return False
            
        # Vérifier s'il n'y a pas de contrat actif sur cette pièce
        from django.utils import timezone
        from contrats.models import Contrat
        
        contrats_actifs = Contrat.objects.filter(
            pieces=self,
            est_actif=True,
            est_resilie=False,
            date_debut__lte=timezone.now().date(),
            date_fin__gte=timezone.now().date(),
            is_deleted=False
        ).exists()
        
        return self.statut == 'disponible' and not contrats_actifs
    
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
    
    def get_espaces_partages_accessibles(self):
        """Retourne les espaces partagés accessibles depuis cette pièce."""
        if self.est_espace_partage:
            return Piece.objects.none()  # Un espace partagé n'a pas accès à d'autres espaces
        
        return Piece.objects.filter(
            acces_depuis_pieces__piece_privee=self,
            acces_depuis_pieces__actif=True,
            est_espace_partage=True
        ).distinct()
    
    def get_pieces_avec_acces(self):
        """Retourne les pièces qui ont accès à cet espace partagé."""
        if not self.est_espace_partage:
            return Piece.objects.none()  # Seuls les espaces partagés peuvent avoir des accès
        
        return Piece.objects.filter(
            acces_espaces_partages__espace_partage=self,
            acces_espaces_partages__actif=True
        ).distinct()
    
    def calculer_cout_acces_espaces_partages(self, date_reference=None):
        """Calcule le coût total des accès aux espaces partagés pour cette pièce."""
        from django.utils import timezone
        
        if not date_reference:
            date_reference = timezone.now().date()
        
        acces = AccesEspacePartage.objects.filter(
            piece_privee=self,
            actif=True,
            date_debut_acces__lte=date_reference
        ).filter(
            models.Q(date_fin_acces__isnull=True) |
            models.Q(date_fin_acces__gte=date_reference)
        )
        
        cout_total = 0
        details_couts = []
        
        for acces_obj in acces:
            cout_acces = acces_obj.get_cout_total_mensuel()
            cout_total += cout_acces
            
            if cout_acces > 0:
                details_couts.append({
                    'espace': acces_obj.espace_partage.nom,
                    'cout': cout_acces,
                    'inclus': acces_obj.acces_inclus
                })
        
        return {
            'cout_total': cout_total,
            'details': details_couts
        }
    
    def peut_etre_louee_individuellement(self):
        """Vérifie si cette pièce peut être louée individuellement."""
        if self.est_espace_partage:
            return False  # Les espaces partagés ne peuvent pas être loués individuellement
        
        # Vérifier si la pièce a accès aux espaces essentiels (cuisine, salle de bain)
        espaces_accessibles = self.get_espaces_partages_accessibles()
        types_espaces_accessibles = set(espaces_accessibles.values_list('type_piece', flat=True))
        
        # Au minimum, accès à une cuisine et une salle de bain
        espaces_essentiels = {'cuisine', 'salle_bain'}
        
        return espaces_essentiels.issubset(types_espaces_accessibles)


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
        app_label = 'proprietes'
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


class ChargeCommune(models.Model):
    """Modèle pour gérer les charges communes d'une propriété."""
    
    TYPE_REPARTITION_CHOICES = [
        ('surface', 'Répartition par surface'),
        ('nb_occupants', 'Répartition par nombre d\'occupants'),
        ('equipartition', 'Répartition équitable'),
        ('personnalisee', 'Répartition personnalisée'),
    ]
    
    TYPE_CHARGE_CHOICES = [
        ('electricite', 'Électricité'),
        ('eau', 'Eau'),
        ('gaz', 'Gaz'),
        ('internet', 'Internet'),
        ('entretien', 'Entretien'),
        ('assurance', 'Assurance'),
        ('taxes', 'Taxes'),
        ('gardiennage', 'Gardiennage'),
        ('nettoyage', 'Nettoyage'),
        ('autre', 'Autre'),
    ]
    
    # Informations de base
    propriete = models.ForeignKey(
        Propriete,
        on_delete=models.CASCADE,
        related_name='charges_communes',
        verbose_name=_("Propriété")
    )
    nom = models.CharField(max_length=100, verbose_name=_("Nom de la charge"))
    type_charge = models.CharField(
        max_length=20,
        choices=TYPE_CHARGE_CHOICES,
        verbose_name=_("Type de charge")
    )
    description = models.TextField(blank=True, verbose_name=_("Description"))
    
    # Montant et répartition
    montant_mensuel = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Montant mensuel total")
    )
    type_repartition = models.CharField(
        max_length=20,
        choices=TYPE_REPARTITION_CHOICES,
        default='equipartition',
        verbose_name=_("Type de répartition")
    )
    
    # Périodes d'application
    date_debut = models.DateField(verbose_name=_("Date de début"))
    date_fin = models.DateField(
        blank=True,
        null=True,
        verbose_name=_("Date de fin")
    )
    
    # Statut
    active = models.BooleanField(default=True, verbose_name=_("Active"))
    
    # Métadonnées
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name=_("Date de création"))
    date_modification = models.DateTimeField(auto_now=True, verbose_name=_("Date de modification"))
    is_deleted = models.BooleanField(default=False, verbose_name=_("Supprimé logiquement"))
    
    objects = NonDeletedManager()
    
    class Meta:
        app_label = 'proprietes'
        verbose_name = _("Charge commune")
        verbose_name_plural = _("Charges communes")
        ordering = ['-date_creation']
    
    def __str__(self):
        return f"{self.nom} - {self.propriete.titre}"
    
    def est_active(self, date_reference=None):
        """Vérifie si la charge est active à une date donnée."""
        from django.utils import timezone
        
        if not self.active:
            return False
        
        if not date_reference:
            date_reference = timezone.now().date()
        
        if self.date_debut > date_reference:
            return False
        
        if self.date_fin and self.date_fin < date_reference:
            return False
        
        return True
    
    def calculer_repartition(self, date_reference=None):
        """
        Calcule la répartition de cette charge entre les locataires de pièces.
        Retourne un dictionnaire avec les montants par contrat/pièce.
        """
        from django.utils import timezone
        
        if not date_reference:
            date_reference = timezone.now().date()
        
        if not self.est_active(date_reference):
            return {}
        
        # Récupérer les pièces occupées à cette date
        pieces_occupees = PieceContrat.objects.filter(
            piece__propriete=self.propriete,
            actif=True,
            date_debut_occupation__lte=date_reference,
            contrat__est_actif=True,
            contrat__est_resilie=False
        ).filter(
            models.Q(date_fin_occupation__isnull=True) |
            models.Q(date_fin_occupation__gte=date_reference)
        ).select_related('piece', 'contrat', 'contrat__locataire')
        
        if not pieces_occupees.exists():
            return {}
        
        repartition = {}
        
        if self.type_repartition == 'equipartition':
            # Répartition équitable
            montant_par_piece = float(self.montant_mensuel) / pieces_occupees.count()
            for piece_contrat in pieces_occupees:
                repartition[piece_contrat.id] = {
                    'piece_contrat': piece_contrat,
                    'montant': montant_par_piece,
                    'base_calcul': 'équipartition'
                }
        
        elif self.type_repartition == 'surface':
            # Répartition par surface
            surface_totale = sum(
                float(pc.piece.surface) if pc.piece.surface else 0 
                for pc in pieces_occupees
            )
            
            if surface_totale > 0:
                for piece_contrat in pieces_occupees:
                    surface_piece = float(piece_contrat.piece.surface) if piece_contrat.piece.surface else 0
                    proportion = surface_piece / surface_totale
                    montant = float(self.montant_mensuel) * proportion
                    repartition[piece_contrat.id] = {
                        'piece_contrat': piece_contrat,
                        'montant': montant,
                        'base_calcul': f'surface ({surface_piece} m²)'
                    }
        
        elif self.type_repartition == 'nb_occupants':
            # Répartition par nombre d'occupants (1 par contrat pour simplifier)
            nb_occupants = pieces_occupees.count()
            montant_par_occupant = float(self.montant_mensuel) / nb_occupants
            for piece_contrat in pieces_occupees:
                repartition[piece_contrat.id] = {
                    'piece_contrat': piece_contrat,
                    'montant': montant_par_occupant,
                    'base_calcul': '1 occupant'
                }
        
        return repartition
    
    def get_montant_pour_piece_contrat(self, piece_contrat, date_reference=None):
        """Retourne le montant de cette charge pour une pièce-contrat spécifique."""
        repartition = self.calculer_repartition(date_reference)
        return repartition.get(piece_contrat.id, {}).get('montant', 0)


class RepartitionChargeCommune(models.Model):
    """Modèle pour stocker les répartitions calculées des charges communes."""
    
    charge_commune = models.ForeignKey(
        ChargeCommune,
        on_delete=models.CASCADE,
        related_name='repartitions',
        verbose_name=_("Charge commune")
    )
    piece_contrat = models.ForeignKey(
        PieceContrat,
        on_delete=models.CASCADE,
        related_name='charges_communes_reparties',
        verbose_name=_("Pièce-Contrat")
    )
    
    # Montants
    montant_calcule = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Montant calculé")
    )
    montant_ajuste = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name=_("Montant ajusté manuellement")
    )
    
    # Période d'application
    mois = models.PositiveIntegerField(verbose_name=_("Mois"))
    annee = models.PositiveIntegerField(verbose_name=_("Année"))
    
    # Informations de calcul
    base_calcul = models.CharField(
        max_length=100,
        verbose_name=_("Base de calcul")
    )
    date_calcul = models.DateTimeField(auto_now_add=True, verbose_name=_("Date de calcul"))
    
    # Statut
    applique = models.BooleanField(default=False, verbose_name=_("Appliqué au contrat"))
    date_application = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_("Date d'application")
    )
    
    class Meta:
        app_label = 'proprietes'
        verbose_name = _("Répartition charge commune")
        verbose_name_plural = _("Répartitions charges communes")
        unique_together = ['charge_commune', 'piece_contrat', 'mois', 'annee']
        ordering = ['-annee', '-mois']
    
    def __str__(self):
        return f"{self.charge_commune.nom} - {self.piece_contrat} - {self.mois}/{self.annee}"
    
    def get_montant_final(self):
        """Retourne le montant final (ajusté si disponible, sinon calculé)."""
        return self.montant_ajuste if self.montant_ajuste is not None else self.montant_calcule


class AccesEspacePartage(models.Model):
    """Modèle pour gérer les accès aux espaces partagés depuis les pièces privées."""
    
    piece_privee = models.ForeignKey(
        Piece,
        on_delete=models.CASCADE,
        related_name='acces_espaces_partages',
        verbose_name=_("Pièce privée")
    )
    espace_partage = models.ForeignKey(
        Piece,
        on_delete=models.CASCADE,
        related_name='acces_depuis_pieces',
        verbose_name=_("Espace partagé")
    )
    
    # Conditions d'accès
    acces_inclus = models.BooleanField(
        default=True,
        verbose_name=_("Accès inclus"),
        help_text=_("L'accès à cet espace est-il inclus dans le loyer de la pièce ?")
    )
    cout_supplementaire = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0,
        verbose_name=_("Coût supplémentaire mensuel"),
        help_text=_("Coût supplémentaire mensuel pour l'accès (si non inclus)")
    )
    
    # Restrictions d'usage
    heures_acces_debut = models.TimeField(
        blank=True,
        null=True,
        verbose_name=_("Heure de début d'accès"),
        help_text=_("Heure de début d'accès autorisé (optionnel)")
    )
    heures_acces_fin = models.TimeField(
        blank=True,
        null=True,
        verbose_name=_("Heure de fin d'accès"),
        help_text=_("Heure de fin d'accès autorisé (optionnel)")
    )
    jours_acces = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_("Jours d'accès"),
        help_text=_("Jours de la semaine autorisés (ex: Lun-Ven, Weekend, etc.)")
    )
    
    # Dates d'activation
    date_debut_acces = models.DateField(verbose_name=_("Date de début d'accès"))
    date_fin_acces = models.DateField(
        blank=True,
        null=True,
        verbose_name=_("Date de fin d'accès")
    )
    
    # Statut
    actif = models.BooleanField(default=True, verbose_name=_("Actif"))
    
    # Métadonnées
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name=_("Date de création"))
    date_modification = models.DateTimeField(auto_now=True, verbose_name=_("Date de modification"))
    
    class Meta:
        app_label = 'proprietes'
        verbose_name = _("Accès espace partagé")
        verbose_name_plural = _("Accès espaces partagés")
        unique_together = ['piece_privee', 'espace_partage']
        ordering = ['-date_creation']
    
    def __str__(self):
        return f"{self.piece_privee.nom} → {self.espace_partage.nom}"
    
    def est_actif(self, date_reference=None):
        """Vérifie si l'accès est actif à une date donnée."""
        from django.utils import timezone
        
        if not self.actif:
            return False
        
        if not date_reference:
            date_reference = timezone.now().date()
        
        if self.date_debut_acces > date_reference:
            return False
        
        if self.date_fin_acces and self.date_fin_acces < date_reference:
            return False
        
        return True
    
    def get_cout_total_mensuel(self):
        """Retourne le coût total mensuel pour cet accès."""
        cout_base = float(self.espace_partage.cout_acces_mensuel) if self.espace_partage.cout_acces_mensuel else 0
        cout_supplementaire = float(self.cout_supplementaire) if self.cout_supplementaire else 0
        
        if self.acces_inclus:
            return cout_supplementaire  # Seul le coût supplémentaire est facturé
        else:
            return cout_base + cout_supplementaire  # Coût total
    
    def clean(self):
        """Validation personnalisée."""
        from django.core.exceptions import ValidationError
        
        if self.piece_privee == self.espace_partage:
            raise ValidationError("Une pièce ne peut pas avoir accès à elle-même.")
        
        if not self.espace_partage.est_espace_partage:
            raise ValidationError("L'espace de destination doit être marqué comme espace partagé.")
        
        if self.piece_privee.est_espace_partage:
            raise ValidationError("Une pièce marquée comme espace partagé ne peut pas avoir d'accès à d'autres espaces.")
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)