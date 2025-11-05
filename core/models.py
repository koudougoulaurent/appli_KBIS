from django.db import models
from django.contrib.auth.models import Group
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()


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
    active = models.BooleanField(default=True, verbose_name=_("Actif"))
    
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
    active = models.BooleanField(default=True, verbose_name=_("Actif"))
    
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
    active = models.BooleanField(default=True, verbose_name=_("Actif"))
    
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
        help_text=_("Code ISO 4217 (ex: XOF, USD, F CFA)")
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
    active = models.BooleanField(default=True, verbose_name=_("Actif"))
    
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


class ConfigurationEntreprise(models.Model):
    """Configuration de l'entreprise KBIS pour les documents."""
    
    nom_entreprise = models.CharField(max_length=200, default="KBIS IMMOBILIER")
    slogan = models.CharField(max_length=300, default="Votre Partenaire Immobilier de Confiance")
    
    # Adresse
    adresse_ligne1 = models.CharField(max_length=200, default="Avenue de la République")
    adresse_ligne2 = models.CharField(max_length=200, default="Quartier Centre-Ville", blank=True)
    ville = models.CharField(max_length=100, default="Abidjan")
    pays = models.CharField(max_length=100, default="Côte d'Ivoire")
    code_postal = models.CharField(max_length=20, blank=True)
    
    # Contact
    telephone = models.CharField(max_length=20, default="+225 XX XX XX XX XX")
    telephone_2 = models.CharField(max_length=20, blank=True)
    telephone_3 = models.CharField(max_length=20, blank=True, verbose_name="Téléphone 3")
    telephone_4 = models.CharField(max_length=20, blank=True, verbose_name="Téléphone 4")
    email = models.EmailField(default="contact@kbis-immobilier.ci")
    site_web = models.URLField(default="www.kbis-immobilier.ci", blank=True)
    
    # Informations légales
    rccm = models.CharField(max_length=50, default="CI-ABJ-XXXX-X-XXXXX", blank=True)
    ifu = models.CharField(max_length=20, default="XXXXXXXXXX", blank=True)
    numero_compte_contribuable = models.CharField(max_length=30, blank=True)
    
    # Logo et branding
    logo = models.ImageField(upload_to='logos/', blank=True, null=True)
    couleur_principale = models.CharField(max_length=7, default="#2c5aa0", help_text="Couleur hexadécimale")
    couleur_secondaire = models.CharField(max_length=7, default="#f8f9fa", help_text="Couleur hexadécimale")
    
    # Métadonnées
    active = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Configuration d'Entreprise"
        verbose_name_plural = "Configurations d'Entreprise"
    
    def __str__(self):
        return f"{self.nom_entreprise} ({self.ville})"
    
    @classmethod
    def get_configuration_active(cls):
        """Retourne la configuration active de l'entreprise."""
        config = cls.objects.filter(active=True).first()
        if not config:
            # Créer une configuration par défaut si aucune n'existe
            config = cls.objects.create()
        return config
    
    def get_adresse_complete(self):
        """Retourne l'adresse complète formatée."""
        adresse_parts = []
        if self.adresse_ligne1:
            adresse_parts.append(self.adresse_ligne1)
        if self.adresse_ligne2:
            adresse_parts.append(self.adresse_ligne2)
        if self.code_postal and self.ville:
            adresse_parts.append(f"{self.code_postal} {self.ville}")
        elif self.code_postal:
            adresse_parts.append(self.code_postal)
        elif self.ville:
            adresse_parts.append(self.ville)
        if self.pays:
            adresse_parts.append(self.pays)
        
        return ", ".join(adresse_parts) if adresse_parts else "Adresse non configurée"
    
    def get_telephones_formates(self):
        """Retourne tous les téléphones formatés séparés par ' / '."""
        telephones = []
        if self.telephone:
            telephones.append(self.telephone)
        if self.telephone_2:
            telephones.append(self.telephone_2)
        if self.telephone_3:
            telephones.append(self.telephone_3)
        if self.telephone_4:
            telephones.append(self.telephone_4)
        
        return " / ".join(telephones) if telephones else ""
    
    def get_contact_complet(self):
        """Retourne les informations de contact formatées."""
        contact_parts = []
        telephones = self.get_telephones_formates()
        if telephones:
            contact_parts.append(f"Tél: {telephones}")
        if self.email:
            contact_parts.append(f"Email: {self.email}")
        if self.site_web:
            contact_parts.append(f"Web: {self.site_web}")
        
        return " | ".join(contact_parts) if contact_parts else "Contact non configuré"
    
    def get_informations_legales(self):
        """Retourne les informations légales formatées."""
        legal_parts = []
        if self.rccm:
            legal_parts.append(f"RCCM: {self.rccm}")
        if self.ifu:
            legal_parts.append(f"IFU: {self.ifu}")
        if self.numero_compte_contribuable:
            legal_parts.append(f"N° Compte Contribuable: {self.numero_compte_contribuable}")
        
        return " | ".join(legal_parts) if legal_parts else "Informations légales non définies"
    
    def a_un_entete_personnalise(self):
        """Vérifie si l'entreprise a un en-tête personnalisé."""
        # Toujours retourner True car on a toujours un logo ou une image
        return True
    
    def get_entete_prioritaire(self):
        """Retourne le chemin de l'en-tête prioritaire."""
        import os
        from django.conf import settings
        
        # Priorité 1: Image d'en-tête personnalisée enteteEnImage.png
        entete_image_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'enteteEnImage.png')
        if os.path.exists(entete_image_path):
            return entete_image_path
            
        # Priorité 2: Logo de l'entreprise uploadé
        if self.logo:
            return self.logo.path
            
        # Priorité 3: Image par défaut
        static_image_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'header_footer', 'entetepieddepage.png')
        if os.path.exists(static_image_path):
            return static_image_path
            
        return None
    
    def get_logo_prioritaire(self):
        """Retourne le logo prioritaire (upload ou logo par défaut)."""
        if self.logo:
            return self.logo.path
        else:
            # Fallback vers le logo KBIS par défaut
            import os
            from django.conf import settings
            logo_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'logo_kbis.jpg')
            if os.path.exists(logo_path):
                return logo_path
        return None


class TemplateDocument(models.Model):
    """Modèle pour gérer les templates de documents."""
    
    TYPE_DOCUMENT_CHOICES = [
        ('recu', 'Reçu de paiement'),
        ('facture', 'Facture'),
        ('contrat', 'Contrat de location'),
        ('quittance', 'Quittance de loyer'),
        ('courrier', 'Courrier officiel'),
        ('rapport', 'Rapport'),
        ('autre', 'Autre document'),
    ]
    
    FORMAT_CHOICES = [
        ('A4', 'Format A4'),
        ('A5', 'Format A5'),
        ('letter', 'Format Lettre US'),
    ]
    
    nom = models.CharField(max_length=100, unique=True)
    type_document = models.CharField(max_length=20, choices=TYPE_DOCUMENT_CHOICES)
    description = models.TextField(blank=True)
    
    # Configuration du template
    format_page = models.CharField(max_length=10, choices=FORMAT_CHOICES, default='A4')
    marge_haut = models.IntegerField(default=20, help_text="Marge en mm")
    marge_bas = models.IntegerField(default=20, help_text="Marge en mm")
    marge_gauche = models.IntegerField(default=20, help_text="Marge en mm")
    marge_droite = models.IntegerField(default=20, help_text="Marge en mm")
    
    # En-tête et pied de page
    inclure_entete = models.BooleanField(default=True)
    inclure_pied_page = models.BooleanField(default=True)
    hauteur_entete = models.IntegerField(default=80, help_text="Hauteur en mm")
    hauteur_pied_page = models.IntegerField(default=40, help_text="Hauteur en mm")
    
    # Template HTML
    template_html = models.TextField(blank=True, help_text="Template HTML personnalisé")
    css_personnalise = models.TextField(blank=True, help_text="CSS personnalisé")
    
    # Métadonnées
    par_defaut = models.BooleanField(default=False)
    actif = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Template de Document"
        verbose_name_plural = "Templates de Documents"
        ordering = ['type_document', 'nom']
    
    def __str__(self):
        return f"{self.nom} ({self.get_type_document_display()})"
    
    @classmethod
    def get_template_defaut(cls, type_document):
        """Retourne le template par défaut pour un type de document."""
        template = cls.objects.filter(
            type_document=type_document,
            par_defaut=True,
            actif=True
        ).first()
        
        if not template:
            # Créer un template par défaut si aucun n'existe
            template = cls.objects.create(
                nom=f"Template {type_document.title()} par défaut",
                type_document=type_document,
                par_defaut=True
            )
        
        return template


class HistoriqueGeneration(models.Model):
    """Historique des documents générés."""
    
    template = models.ForeignKey(TemplateDocument, on_delete=models.CASCADE)
    type_document = models.CharField(max_length=20)
    nom_fichier = models.CharField(max_length=200)
    taille_fichier = models.IntegerField(null=True, blank=True, help_text="Taille en octets")
    
    # Référence vers l'objet source
    reference_objet = models.CharField(max_length=100, blank=True, help_text="ID de l'objet source")
    type_objet = models.CharField(max_length=50, blank=True, help_text="Type de l'objet source")
    
    # Métadonnées
    date_generation = models.DateTimeField(auto_now_add=True)
    succes = models.BooleanField(default=True)
    message_erreur = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "Historique de Génération"
        verbose_name_plural = "Historiques de Génération"
        ordering = ['-date_generation']
    
    def __str__(self):
        status = "✓" if self.succes else "✗"
        return f"{status} {self.nom_fichier} - {self.date_generation.strftime('%d/%m/%Y %H:%M')}"


class SecurityEvent(models.Model):
    """Modèle pour enregistrer les événements de sécurité"""
    
    EVENT_TYPES = [
        ('login_success', 'Connexion réussie'),
        ('login_failed', 'Échec de connexion'),
        ('logout', 'Déconnexion'),
        ('password_change', 'Changement de mot de passe'),
        ('permission_denied', 'Accès refusé'),
        ('suspicious_activity', 'Activité suspecte'),
        ('file_upload', 'Upload de fichier'),
        ('data_access', 'Accès aux données'),
        ('data_modification', 'Modification de données'),
        ('session_invalidated', 'Session invalidée'),
        ('rate_limit_exceeded', 'Limite de taux dépassée'),
        ('sql_injection_attempt', 'Tentative d\'injection SQL'),
        ('xss_attempt', 'Tentative XSS'),
        ('file_security_violation', 'Violation de sécurité fichier'),
    ]
    
    SEVERITY_LEVELS = [
        ('low', 'Faible'),
        ('medium', 'Moyen'),
        ('high', 'Élevé'),
        ('critical', 'Critique'),
    ]
    
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES)
    severity = models.CharField(max_length=20, choices=SEVERITY_LEVELS, default='medium')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    description = models.TextField()
    details = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    resolved = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['event_type', 'timestamp']),
            models.Index(fields=['severity', 'timestamp']),
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['ip_address', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.get_event_type_display()} - {self.user or 'Anonyme'} - {self.timestamp}"


class AutoNumberSequence(models.Model):
    """Séquences de numérotation atomiques par portée et année."""
    scope = models.CharField(max_length=50, verbose_name=_("Portée"))
    year = models.PositiveIntegerField(verbose_name=_("Année"))
    current = models.PositiveIntegerField(default=0, verbose_name=_("Compteur courant"))

    class Meta:
        app_label = 'core'
        verbose_name = _("Séquence de numérotation")
        verbose_name_plural = _("Séquences de numérotation")
        unique_together = [('scope', 'year')]
        indexes = [models.Index(fields=['scope', 'year'])]

    def __str__(self):
        return f"{self.scope}-{self.year}: {self.current}"

    @classmethod
    def next_number(cls, scope: str, year: int) -> int:
        """Retourne le prochain numéro en toute sécurité (verrouillage transactionnel)."""
        with transaction.atomic():
            seq = cls.objects.select_for_update().filter(scope=scope, year=year).first()
            if not seq:
                seq = cls.objects.create(scope=scope, year=year, current=0)
            seq.current += 1
            seq.save(update_fields=['current'])
            return seq.current

    @classmethod
    def preview_next_number(cls, scope: str, year: int) -> int:
        """Aperçu du prochain numéro sans consommer la séquence (pas de lock)."""
        seq = cls.objects.filter(scope=scope, year=year).only('current').first()
        if not seq:
            return 1
        return (seq.current or 0) + 1