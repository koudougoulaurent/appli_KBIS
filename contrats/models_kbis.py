from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from .models import Contrat


class ContratKbis(models.Model):
    """Modèle pour les contrats KBIS avec toutes les informations spécifiques."""
    
    contrat = models.OneToOneField(
        Contrat,
        on_delete=models.CASCADE,
        related_name='contrat_kbis',
        verbose_name=_("Contrat de base")
    )
    
    # === INFORMATIONS DE L'AGENCE KBIS ===
    agence_nom = models.CharField(
        max_length=200,
        default="KBIS IMMOBILIER",
        verbose_name=_("Nom de l'agence")
    )
    agence_adresse = models.CharField(
        max_length=300,
        default="secteur 26 Pissy",
        verbose_name=_("Adresse de l'agence")
    )
    agence_representant = models.CharField(
        max_length=200,
        default="M. NIKIEMA PA MAMDOU",
        verbose_name=_("Représentant de l'agence")
    )
    agence_telephone = models.CharField(
        max_length=20,
        default="70-20-64-91",
        verbose_name=_("Téléphone de l'agence")
    )
    
    # === INFORMATIONS DU LOCATAIRE ===
    locataire_cnib = models.CharField(
        max_length=50,
        verbose_name=_("N° CNIB du locataire")
    )
    locataire_profession = models.CharField(
        max_length=200,
        verbose_name=_("Profession du locataire")
    )
    locataire_adresse = models.TextField(
        verbose_name=_("Adresse du locataire")
    )
    locataire_telephone = models.CharField(
        max_length=20,
        verbose_name=_("Téléphone du locataire")
    )
    
    # === INFORMATIONS DU GARANT ===
    garant_nom = models.CharField(
        max_length=200,
        verbose_name=_("Nom du garant")
    )
    garant_profession = models.CharField(
        max_length=200,
        verbose_name=_("Profession du garant")
    )
    garant_adresse = models.TextField(
        verbose_name=_("Adresse du garant")
    )
    garant_telephone = models.CharField(
        max_length=20,
        verbose_name=_("Téléphone du garant")
    )
    garant_cnib = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name=_("N° CNIB du garant")
    )
    
    # === INFORMATIONS DE LA PROPRIÉTÉ ===
    propriete_numero = models.CharField(
        max_length=50,
        verbose_name=_("Numéro de la maison")
    )
    propriete_adresse = models.CharField(
        max_length=300,
        verbose_name=_("Adresse de la propriété")
    )
    
    # === INFORMATIONS FINANCIÈRES ===
    caution_montant = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name=_("Montant de la caution"),
        help_text=_("Montant total de la caution (généralement 3 mois de loyer)")
    )
    caution_nombre_mois = models.IntegerField(
        default=3,
        validators=[MinValueValidator(1), MaxValueValidator(12)],
        verbose_name=_("Nombre de mois de caution")
    )
    paiement_debut_mois = models.CharField(
        max_length=50,
        default="fin du mois de SEPTEMBRE 2025",
        verbose_name=_("Début du paiement")
    )
    paiement_echeance = models.CharField(
        max_length=50,
        default="03 du mois suivant",
        verbose_name=_("Échéance de paiement")
    )
    
    # === CONDITIONS SPÉCIALES ===
    delai_annulation = models.IntegerField(
        default=48,
        verbose_name=_("Délai d'annulation (heures)")
    )
    preavis_resiliation_locataire = models.CharField(
        max_length=50,
        default="un mois",
        verbose_name=_("Préavis de résiliation (locataire)")
    )
    preavis_resiliation_agence = models.CharField(
        max_length=50,
        default="trois mois",
        verbose_name=_("Préavis de résiliation (agence)")
    )
    date_remise_cles = models.CharField(
        max_length=50,
        default="01er du mois suivant",
        verbose_name=_("Date de remise des clés")
    )
    
    # === INFORMATIONS DE GÉNÉRATION ===
    date_generation = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Date de génération")
    )
    version_template = models.CharField(
        max_length=20,
        default="1.0",
        verbose_name=_("Version du template")
    )
    
    class Meta:
        verbose_name = _("Contrat KBIS")
        verbose_name_plural = _("Contrats KBIS")
        ordering = ['-date_generation']
    
    def __str__(self):
        return f"Contrat KBIS - {self.contrat.numero_contrat} - {self.contrat.locataire.nom}"
    
    def get_caution_montant_lettres(self):
        """Convertit le montant de la caution en lettres."""
        from .utils import nombre_en_lettres
        return nombre_en_lettres(int(self.caution_montant))
    
    def get_loyer_mensuel_lettres(self):
        """Convertit le loyer mensuel en lettres."""
        from .utils import nombre_en_lettres
        return nombre_en_lettres(int(self.contrat.loyer_mensuel))


class EtatLieuxKbis(models.Model):
    """Modèle pour l'état des lieux du contrat KBIS."""
    
    contrat_kbis = models.OneToOneField(
        ContratKbis,
        on_delete=models.CASCADE,
        related_name='etat_lieux',
        verbose_name=_("Contrat KBIS")
    )
    
    # === INDEXES DES COMPTEURS ===
    indexe_sonabel = models.BooleanField(
        default=True,
        verbose_name=_("Indexé du compteur SONABEL")
    )
    indexe_onea = models.BooleanField(
        default=True,
        verbose_name=_("Indexé du compteur ONEA")
    )
    
    # === ÉTAT DE LA PEINTURE ===
    peinture_murs = models.CharField(
        max_length=20,
        choices=[
            ('OK', 'OK'),
            ('PASSABLE', 'PASSABLE'),
            ('MAUVAIS', 'MAUVAIS')
        ],
        default='OK',
        verbose_name=_("État de la peinture des murs")
    )
    peinture_couvertures = models.CharField(
        max_length=20,
        choices=[
            ('OK', 'OK'),
            ('PASSABLE', 'PASSABLE'),
            ('MAUVAIS', 'MAUVAIS')
        ],
        default='OK',
        verbose_name=_("État de la peinture des couvertures")
    )
    peinture_plafond = models.CharField(
        max_length=20,
        choices=[
            ('OK', 'OK'),
            ('PASSABLE', 'PASSABLE'),
            ('MAUVAIS', 'MAUVAIS')
        ],
        default='OK',
        verbose_name=_("État de la peinture du plafond")
    )
    
    # === ÉTAT DES ÉLÉMENTS ===
    cremone_vitre = models.CharField(
        max_length=20,
        choices=[
            ('OK', 'OK'),
            ('PASSABLE', 'PASSABLE'),
            ('MAUVAIS', 'MAUVAIS')
        ],
        default='OK',
        verbose_name=_("État de crémoné de vitre")
    )
    prise_electrique = models.CharField(
        max_length=20,
        choices=[
            ('OK', 'OK'),
            ('PASSABLE', 'PASSABLE'),
            ('MAUVAIS', 'MAUVAIS')
        ],
        default='OK',
        verbose_name=_("État des prises électriques")
    )
    
    # === CLÉS ===
    cles_grand_portail = models.BooleanField(
        default=True,
        verbose_name=_("Clés du grand portail")
    )
    cles_porte_salon = models.BooleanField(
        default=True,
        verbose_name=_("Clés de la porte du salon")
    )
    cles_iso_planes = models.BooleanField(
        default=True,
        verbose_name=_("Clés iso planes")
    )
    cles_placard = models.BooleanField(
        default=True,
        verbose_name=_("Clés du placard")
    )
    
    # === ÉLÉMENTS DÉCORATIFS ===
    porte_rideau = models.BooleanField(
        default=True,
        verbose_name=_("Porte rideau")
    )
    reglettes = models.CharField(
        max_length=20,
        choices=[
            ('OK', 'OK'),
            ('NON', 'NON')
        ],
        default='OK',
        verbose_name=_("Réglettes")
    )
    veilleuses = models.CharField(
        max_length=20,
        choices=[
            ('OK', 'OK'),
            ('NON', 'NON')
        ],
        default='OK',
        verbose_name=_("Veilleuses")
    )
    ventilateurs = models.CharField(
        max_length=20,
        choices=[
            ('OK', 'OK'),
            ('NON', 'NON')
        ],
        default='OK',
        verbose_name=_("Ventilateurs")
    )
    
    # === CUISINE ===
    robinets_cuisine = models.CharField(
        max_length=20,
        choices=[
            ('OK', 'OK'),
            ('NON', 'NON')
        ],
        default='OK',
        verbose_name=_("Robinet de la cuisine")
    )
    placards_cuisine = models.CharField(
        max_length=20,
        choices=[
            ('OK', 'OK'),
            ('NON', 'NON')
        ],
        default='OK',
        verbose_name=_("Placards de la cuisine")
    )
    
    # === ÉLÉMENTS TECHNIQUES ===
    sonnerie = models.CharField(
        max_length=20,
        choices=[
            ('OK', 'OK'),
            ('NON', 'NON')
        ],
        default='OK',
        verbose_name=_("État de la sonnerie")
    )
    
    # === SANITAIRES ===
    wc = models.CharField(
        max_length=20,
        choices=[
            ('OK', 'OK'),
            ('NON', 'NON')
        ],
        default='OK',
        verbose_name=_("WC")
    )
    lavabos = models.CharField(
        max_length=20,
        choices=[
            ('OK', 'OK'),
            ('NON', 'NON')
        ],
        default='OK',
        verbose_name=_("Lavabos")
    )
    miroir = models.CharField(
        max_length=20,
        choices=[
            ('OK', 'OK'),
            ('NON', 'NON')
        ],
        default='OK',
        verbose_name=_("Miroir")
    )
    flexible_douche = models.CharField(
        max_length=20,
        choices=[
            ('OK', 'OK'),
            ('NON', 'NON')
        ],
        default='OK',
        verbose_name=_("Flexible de douche (colonne)")
    )
    accessoires_sanitaires = models.CharField(
        max_length=20,
        choices=[
            ('OK', 'OK'),
            ('NON', 'NON')
        ],
        default='OK',
        verbose_name=_("Accessoires sanitaires")
    )
    lampes_sanitaire = models.CharField(
        max_length=20,
        choices=[
            ('OK', 'OK'),
            ('NON', 'NON')
        ],
        default='OK',
        verbose_name=_("Lampes sanitaires")
    )
    chauffe_eau = models.CharField(
        max_length=20,
        choices=[
            ('OK', 'OK'),
            ('NON', 'NON')
        ],
        default='OK',
        verbose_name=_("Chauffe-eau")
    )
    climatiseur = models.CharField(
        max_length=20,
        choices=[
            ('OK', 'OK'),
            ('NON', 'NON')
        ],
        default='OK',
        verbose_name=_("Climatiseur (entretien)")
    )
    
    # === OBSERVATIONS ===
    observations = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Observations")
    )
    
    # === INFORMATIONS DE GÉNÉRATION ===
    date_generation = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Date de génération")
    )
    
    class Meta:
        verbose_name = _("État des lieux KBIS")
        verbose_name_plural = _("États des lieux KBIS")
        ordering = ['-date_generation']
    
    def __str__(self):
        return f"État des lieux - {self.contrat_kbis.contrat.numero_contrat}"
