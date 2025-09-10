from django.db import models
from django.contrib.auth.models import Group
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.utils import timezone


class NiveauAcces(models.Model):
    """Modèle pour définir les niveaux d'accès aux données."""
    
    NIVEAUX_CHOICES = [
        ('public', 'Public - Données générales'),
        ('interne', 'Interne - Données de l\'équipe'),
        ('confidentiel', 'Confidentiel - Données sensibles'),
        ('secret', 'Secret - Données critiques direction'),
        ('top_secret', 'Top Secret - Données stratégiques'),
    ]
    
    nom = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_("Nom du niveau")
    )
    niveau = models.CharField(
        max_length=20,
        choices=NIVEAUX_CHOICES,
        unique=True,
        verbose_name=_("Niveau d'accès")
    )
    description = models.TextField(
        verbose_name=_("Description"),
        help_text=_("Description détaillée du niveau d'accès")
    )
    priorite = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        verbose_name=_("Priorité"),
        help_text=_("1 = niveau le plus bas, 10 = niveau le plus élevé")
    )
    
    # Groupes autorisés
    groupes_autorises = models.ManyToManyField(
        Group,
        related_name='niveaux_acces',
        verbose_name=_("Groupes autorisés"),
        help_text=_("Groupes d'utilisateurs autorisés à ce niveau")
    )
    
    # Métadonnées
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    actif = models.BooleanField(default=True, verbose_name=_("Actif"))
    
    class Meta:
        verbose_name = _("Niveau d'accès")
        verbose_name_plural = _("Niveaux d'accès")
        ordering = ['-priorite', 'nom']
    
    def __str__(self):
        return f"{self.nom} ({self.get_niveau_display()})"


class PermissionTableauBord(models.Model):
    """Modèle pour gérer les permissions spécifiques aux tableaux de bord."""
    
    TYPE_DONNEES_CHOICES = [
        ('financier', 'Données financières'),
        ('locataire', 'Données locataires'),
        ('bailleur', 'Données bailleurs'),
        ('propriete', 'Données propriétés'),
        ('contrat', 'Données contrats'),
        ('paiement', 'Données paiements'),
        ('charge', 'Données charges'),
        ('statistique', 'Statistiques globales'),
        ('rapport', 'Rapports détaillés'),
    ]
    
    nom = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_("Nom de la permission")
    )
    type_donnees = models.CharField(
        max_length=20,
        choices=TYPE_DONNEES_CHOICES,
        verbose_name=_("Type de données")
    )
    niveau_acces_requis = models.ForeignKey(
        NiveauAcces,
        on_delete=models.PROTECT,
        verbose_name=_("Niveau d'accès requis")
    )
    
    # Permissions spécifiques
    peut_voir_montants = models.BooleanField(
        default=False,
        verbose_name=_("Peut voir les montants exacts")
    )
    peut_voir_details_personnels = models.BooleanField(
        default=False,
        verbose_name=_("Peut voir les détails personnels")
    )
    peut_voir_historique = models.BooleanField(
        default=False,
        verbose_name=_("Peut voir l'historique complet")
    )
    peut_exporter = models.BooleanField(
        default=False,
        verbose_name=_("Peut exporter les données")
    )
    peut_imprimer = models.BooleanField(
        default=False,
        verbose_name=_("Peut imprimer les rapports")
    )
    
    # Limitations
    limite_periode_jours = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_("Limitation période (jours)"),
        help_text=_("Nombre de jours maximum dans le passé (null = illimité)")
    )
    limite_nombre_resultats = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_("Limite nombre de résultats"),
        help_text=_("Nombre maximum de résultats affichés (null = illimité)")
    )
    
    # Métadonnées
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    actif = models.BooleanField(default=True, verbose_name=_("Actif"))
    
    class Meta:
        verbose_name = _("Permission tableau de bord")
        verbose_name_plural = _("Permissions tableaux de bord")
        ordering = ['type_donnees', 'nom']
    
    def __str__(self):
        return f"{self.nom} - {self.get_type_donnees_display()}"


class LogAccesDonnees(models.Model):
    """Modèle pour journaliser les accès aux données sensibles."""
    
    TYPE_ACTION_CHOICES = [
        ('consultation', 'Consultation'),
        ('export', 'Export'),
        ('impression', 'Impression'),
        ('modification', 'Modification'),
        ('suppression', 'Suppression'),
    ]
    
    utilisateur = models.ForeignKey(
        'utilisateurs.Utilisateur',
        on_delete=models.PROTECT,
        verbose_name=_("Utilisateur")
    )
    type_action = models.CharField(
        max_length=20,
        choices=TYPE_ACTION_CHOICES,
        verbose_name=_("Type d'action")
    )
    type_donnees = models.CharField(
        max_length=50,
        verbose_name=_("Type de données accédées")
    )
    identifiant_objet = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name=_("Identifiant de l'objet")
    )
    niveau_acces_utilise = models.ForeignKey(
        NiveauAcces,
        on_delete=models.PROTECT,
        verbose_name=_("Niveau d'accès utilisé")
    )
    
    # Informations techniques
    adresse_ip = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name=_("Adresse IP")
    )
    user_agent = models.TextField(
        null=True,
        blank=True,
        verbose_name=_("User Agent")
    )
    
    # Horodatage
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name=_("Horodatage"))
    
    # Résultat de l'action
    succes = models.BooleanField(default=True, verbose_name=_("Succès"))
    message_erreur = models.TextField(
        null=True,
        blank=True,
        verbose_name=_("Message d'erreur")
    )
    
    class Meta:
        verbose_name = _("Log d'accès aux données")
        verbose_name_plural = _("Logs d'accès aux données")
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['utilisateur', '-timestamp']),
            models.Index(fields=['type_donnees', '-timestamp']),
            models.Index(fields=['niveau_acces_utilise', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.utilisateur} - {self.get_type_action_display()} - {self.timestamp}"


class ConfigurationTableauBord(models.Model):
    """Configuration personnalisée des tableaux de bord par utilisateur."""
    
    utilisateur = models.ForeignKey(
        'utilisateurs.Utilisateur',
        on_delete=models.CASCADE,
        verbose_name=_("Utilisateur")
    )
    nom_tableau = models.CharField(
        max_length=100,
        verbose_name=_("Nom du tableau de bord")
    )
    
    # Configuration d'affichage
    widgets_actifs = models.JSONField(
        default=list,
        verbose_name=_("Widgets actifs"),
        help_text=_("Liste des widgets activés pour ce tableau")
    )
    ordre_widgets = models.JSONField(
        default=list,
        verbose_name=_("Ordre des widgets"),
        help_text=_("Ordre d'affichage des widgets")
    )
    configuration_widgets = models.JSONField(
        default=dict,
        verbose_name=_("Configuration des widgets"),
        help_text=_("Configuration spécifique de chaque widget")
    )
    
    # Paramètres de sécurité
    masquer_montants_sensibles = models.BooleanField(
        default=True,
        verbose_name=_("Masquer les montants sensibles")
    )
    affichage_anonymise = models.BooleanField(
        default=False,
        verbose_name=_("Affichage anonymisé"),
        help_text=_("Remplacer les noms par des codes")
    )
    limite_donnees_recentes = models.PositiveIntegerField(
        default=30,
        verbose_name=_("Limiter aux données récentes (jours)")
    )
    
    # Métadonnées
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    par_defaut = models.BooleanField(
        default=False,
        verbose_name=_("Tableau par défaut")
    )
    
    class Meta:
        verbose_name = _("Configuration tableau de bord")
        verbose_name_plural = _("Configurations tableaux de bord")
        unique_together = [['utilisateur', 'nom_tableau']]
        ordering = ['utilisateur', '-par_defaut', 'nom_tableau']
    
    def __str__(self):
        return f"{self.utilisateur} - {self.nom_tableau}"


class AuditLog(models.Model):
    """Modèle pour l'audit des actions utilisateur (compatibilité avec l'ancien système)."""
    
    ACTION_CHOICES = [
        ('create', 'Création'),
        ('update', 'Modification'),
        ('delete', 'Suppression'),
        ('view', 'Consultation'),
        ('export', 'Export'),
        ('import', 'Import'),
        ('login', 'Connexion'),
        ('logout', 'Déconnexion'),
        ('validation', 'Validation'),
        ('rejection', 'Rejet'),
    ]
    
    # Référence générique vers n'importe quel modèle
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_("Type de contenu")
    )
    object_id = models.PositiveIntegerField(
        null=True, 
        blank=True,
        verbose_name=_("ID de l'objet")
    )
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Action effectuée
    action = models.CharField(
        max_length=20,
        choices=ACTION_CHOICES,
        verbose_name=_("Action")
    )
    
    # Utilisateur qui a effectué l'action
    user = models.ForeignKey(
        'utilisateurs.Utilisateur',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='audit_logs',
        verbose_name=_("Utilisateur")
    )
    
    # Données et représentation de l'objet
    details = models.JSONField(
        null=True,
        blank=True,
        verbose_name=_("Détails")
    )
    object_repr = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        verbose_name=_("Représentation de l'objet")
    )
    
    # Informations techniques
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name=_("Adresse IP")
    )
    user_agent = models.TextField(
        null=True,
        blank=True,
        verbose_name=_("User Agent")
    )
    
    # Horodatage
    timestamp = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Horodatage")
    )
    
    # Informations supplémentaires
    description = models.TextField(
        null=True,
        blank=True,
        verbose_name=_("Description")
    )
    
    class Meta:
        verbose_name = _("Log d'audit")
        verbose_name_plural = _("Logs d'audit")
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'action', 'timestamp'], name='core_auditl_user_id_0dff28_idx'),
            models.Index(fields=['content_type', 'object_id'], name='core_auditl_content_fec0c4_idx'),
            models.Index(fields=['timestamp'], name='core_auditl_timesta_80074f_idx'),
        ]
    
    def __str__(self):
        if self.content_object:
            return f"{self.user} - {self.get_action_display()} - {self.content_object} - {self.timestamp}"
        return f"{self.user} - {self.get_action_display()} - {self.timestamp}"


class ConfigurationEntreprise(models.Model):
    """Modèle pour la configuration de l'entreprise."""
    
    nom_entreprise = models.CharField(
        max_length=200,
        default='GESTIMMOB',
        verbose_name=_("Nom de l'entreprise")
    )
    slogan = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name=_("Slogan")
    )
    adresse = models.CharField(
        max_length=200,
        default='123 Rue de la Paix',
        verbose_name=_("Adresse")
    )
    code_postal = models.CharField(
        max_length=10,
        default='75001',
        verbose_name=_("Code postal")
    )
    ville = models.CharField(
        max_length=100,
        default='Paris',
        verbose_name=_("Ville")
    )
    pays = models.CharField(
        max_length=100,
        default='France',
        verbose_name=_("Pays")
    )
    telephone = models.CharField(
        max_length=20,
        default='01 23 45 67 89',
        verbose_name=_("Téléphone")
    )
    email = models.EmailField(
        default='contact@gestimmob.fr',
        verbose_name=_("Email")
    )
    site_web = models.URLField(
        blank=True,
        null=True,
        verbose_name=_("Site web")
    )
    siret = models.CharField(
        max_length=20,
        default='123 456 789 00012',
        verbose_name=_("Numéro SIRET")
    )
    numero_licence = models.CharField(
        max_length=50,
        default='123456789',
        verbose_name=_("Numéro de licence")
    )
    capital_social = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=_("Capital social")
    )
    forme_juridique = models.CharField(
        max_length=100,
        default='SARL',
        verbose_name=_("Forme juridique")
    )
    logo_url = models.URLField(
        blank=True,
        null=True,
        help_text=_("URL externe du logo de l'entreprise (optionnel)"),
        verbose_name=_("URL externe du logo")
    )
    logo_upload = models.ImageField(
        upload_to='logos_entreprise/',
        blank=True,
        null=True,
        help_text=_("Logo uploadé directement (PNG, JPG, GIF - max 5MB)"),
        verbose_name=_("Logo uploadé")
    )
    entete_upload = models.ImageField(
        upload_to='entetes_entreprise/',
        blank=True,
        null=True,
        help_text=_("En-tête complet uploadé (PNG, JPG - max 10MB, dimensions recommandées: 800x200 pixels)"),
        verbose_name=_("En-tête complet uploadé")
    )
    couleur_principale = models.CharField(
        max_length=7,
        default='#2c3e50',
        help_text=_("Couleur principale (format hex)"),
        verbose_name=_("Couleur principale")
    )
    couleur_secondaire = models.CharField(
        max_length=7,
        default='#3498db',
        help_text=_("Couleur secondaire (format hex)"),
        verbose_name=_("Couleur secondaire")
    )
    iban = models.CharField(
        max_length=34,
        blank=True,
        null=True,
        verbose_name=_("IBAN")
    )
    bic = models.CharField(
        max_length=11,
        blank=True,
        null=True,
        verbose_name=_("BIC")
    )
    banque = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=_("Banque")
    )
    texte_contrat = models.TextField(
        blank=True,
        null=True,
        help_text=_("Texte personnalisé pour les obligations et conditions des contrats de bail"),
        verbose_name=_("Texte personnalisé pour les contrats")
    )
    texte_resiliation = models.TextField(
        blank=True,
        null=True,
        help_text=_("Texte personnalisé pour les conditions de sortie des résiliations"),
        verbose_name=_("Texte personnalisé pour les résiliations")
    )
    
    # Métadonnées
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    actif = models.BooleanField(default=True, verbose_name=_("Actif"))
    
    class Meta:
        verbose_name = _("Configuration Entreprise")
        verbose_name_plural = _("Configurations Entreprise")
        ordering = ['-date_modification']
    
    def __str__(self):
        return f"Configuration {self.nom_entreprise}"
    
    @classmethod
    def get_configuration_active(cls):
        """Retourne la configuration active de l'entreprise."""
        # Récupérer la configuration active
        config = cls.objects.filter(actif=True).first()
        
        if not config:
            # Créer une configuration par défaut si aucune n'existe
            config = cls.objects.create(
                nom_entreprise="GESTIMMOB",
                adresse="123 Rue de la Paix",
                code_postal="75001",
                ville="Paris",
                pays="France",
                telephone="01 23 45 67 89",
                email="contact@gestimmob.fr",
                siret="123 456 789 00012",
                numero_licence="123456789",
                forme_juridique="SARL",
                couleur_principale="#2c3e50",
                couleur_secondaire="#3498db",
                actif=True
            )
        else:
            # S'assurer que la configuration est bien active
            if not config.actif:
                config.actif = True
                config.save()
        
        return config
    
    def get_adresse_complete(self):
        """Retourne l'adresse complète formatée."""
        adresse_parts = []
        if self.adresse:
            adresse_parts.append(self.adresse)
        if self.code_postal and self.ville:
            adresse_parts.append(f"{self.code_postal} {self.ville}")
        elif self.code_postal:
            adresse_parts.append(self.code_postal)
        elif self.ville:
            adresse_parts.append(self.ville)
        if self.pays:
            adresse_parts.append(self.pays)
        
        return ", ".join(adresse_parts) if adresse_parts else "Adresse non définie"
    
    def get_contact_complet(self):
        """Retourne les informations de contact formatées."""
        contact_parts = []
        if self.telephone:
            contact_parts.append(f"Tél: {self.telephone}")
        if self.email:
            contact_parts.append(f"Email: {self.email}")
        if self.site_web:
            contact_parts.append(f"Web: {self.site_web}")
        
        return " | ".join(contact_parts) if contact_parts else "Contact non défini"
    
    def get_informations_legales(self):
        """Retourne les informations légales formatées."""
        legal_parts = []
        if self.siret:
            legal_parts.append(f"SIRET: {self.siret}")
        if self.numero_licence:
            legal_parts.append(f"N° Licence: {self.numero_licence}")
        if self.capital_social:
            legal_parts.append(f"Capital: {self.capital_social}")
        if self.forme_juridique:
            legal_parts.append(self.forme_juridique)
        
        return " | ".join(legal_parts) if legal_parts else "Informations légales non définies"
    
    def get_informations_bancaires(self):
        """Retourne les informations bancaires formatées."""
        bank_parts = []
        if self.banque:
            bank_parts.append(f"Banque: {self.banque}")
        if self.iban:
            bank_parts.append(f"IBAN: {self.iban}")
        if self.bic:
            bank_parts.append(f"BIC: {self.bic}")
        
        return " | ".join(bank_parts) if bank_parts else "Informations bancaires non définies"
    
    def get_logo_prioritaire(self):
        """
        Retourne le logo prioritaire : d'abord l'upload, puis l'URL externe.
        
        Returns:
            str: Chemin du logo ou URL, None si aucun logo
        """
        if self.logo_upload:
            return self.logo_upload.path
        elif self.logo_url:
            return self.logo_url
        return None
    
    def get_logo_url_prioritaire(self):
        """
        Retourne l'URL du logo prioritaire pour l'affichage.
        
        Returns:
            str: URL du logo ou chemin media, None si aucun logo
        """
        if self.logo_upload:
            return self.logo_upload.url
        elif self.logo_url:
            return self.logo_url
        return None
    
    def get_entete_prioritaire(self):
        """
        Retourne l'en-tête prioritaire : d'abord l'upload, puis le logo + texte.
        
        Returns:
            str: Chemin de l'en-tête ou None si aucun en-tête
        """
        if self.entete_upload:
            return self.entete_upload.path
        return None
    
    def get_entete_url_prioritaire(self):
        """
        Retourne l'URL de l'en-tête prioritaire pour l'affichage.
        
        Returns:
            str: URL de l'en-tête ou None si aucun en-tête
        """
        if self.entete_upload:
            return self.entete_upload.url
        return None
    
    def a_un_entete_personnalise(self):
        """
        Vérifie si l'entreprise a un en-tête personnalisé.
        
        Returns:
            bool: True si un en-tête personnalisé existe
        """
        return bool(self.entete_upload)


class TemplateRecu(models.Model):
    """Modèle pour les templates de reçus (compatibilité avec l'ancien système)."""
    
    nom = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_("Nom du template")
    )
    description = models.TextField(
        blank=True,
        verbose_name=_("Description")
    )
    contenu_html = models.TextField(
        verbose_name=_("Contenu HTML"),
        help_text=_("Template HTML avec variables Django"),
        default="<p>Template vide</p>"
    )
    
    # Métadonnées
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    actif = models.BooleanField(default=True, verbose_name=_("Actif"))
    
    # Variables disponibles
    variables_disponibles = models.JSONField(
        default=list,
        verbose_name=_("Variables disponibles"),
        help_text=_("Liste des variables utilisables dans le template")
    )
    
    class Meta:
        verbose_name = _("Template de reçu")
        verbose_name_plural = _("Templates de reçus")
        ordering = ['nom']
    
    def __str__(self):
        return self.nom


class Devise(models.Model):
    """Modèle pour les devises (compatibilité avec l'ancien système)."""
    
    code = models.CharField(
        max_length=3,
        unique=True,
        verbose_name=_("Code devise"),
        help_text=_("Code ISO 4217 (ex: EUR, USD, F CFA)")
    )
    nom = models.CharField(
        max_length=100,
        verbose_name=_("Nom de la devise")
    )
    symbole = models.CharField(
        max_length=10,
        verbose_name=_("Symbole")
    )
    
    # Taux de change par rapport à la devise de base
    taux_change = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        default=1.0,
        verbose_name=_("Taux de change")
    )
    
    # Métadonnées
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    actif = models.BooleanField(default=True, verbose_name=_("Actif"))
    
    # Devise par défaut
    par_defaut = models.BooleanField(
        default=False,
        verbose_name=_("Devise par défaut")
    )
    
    class Meta:
        verbose_name = _("Devise")
        verbose_name_plural = _("Devises")
        ordering = ['nom']
    
    def __str__(self):
        return f"{self.nom} ({self.code})"
    
    def save(self, *args, **kwargs):
        # S'assurer qu'une seule devise est par défaut
        if self.par_defaut:
            Devise.objects.filter(par_defaut=True).update(par_defaut=False)
        super().save(*args, **kwargs)