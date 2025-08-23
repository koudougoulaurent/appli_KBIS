from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.validators import FileExtensionValidator
from django.core.exceptions import ValidationError
import os
from django.conf import settings

class ConfigurationEntreprise(models.Model):
    """
    Configuration des informations de l'entreprise pour les reçus et documents
    """
    # Informations de base
    nom_entreprise = models.CharField(max_length=200, default="GESTIMMOB")
    slogan = models.CharField(max_length=200, blank=True, null=True)
    
    # Adresse
    adresse = models.CharField(max_length=200, default="123 Rue de la Paix")
    code_postal = models.CharField(max_length=10, default="75001")
    ville = models.CharField(max_length=100, default="Paris")
    pays = models.CharField(max_length=100, default="France")
    
    # Contact
    telephone = models.CharField(max_length=20, default="01 23 45 67 89")
    email = models.EmailField(default="contact@gestimmob.fr")
    site_web = models.URLField(blank=True, null=True)
    
    # Informations légales
    siret = models.CharField(max_length=20, default="123 456 789 00012")
    numero_licence = models.CharField(max_length=50, default="123456789")
    capital_social = models.CharField(max_length=100, blank=True, null=True)
    forme_juridique = models.CharField(max_length=100, default="SARL")
    
    # Logo et branding
    logo_url = models.URLField(blank=True, null=True, help_text="URL du logo de l'entreprise")
    couleur_principale = models.CharField(max_length=7, default="#2c3e50", help_text="Couleur principale (format hex)")
    couleur_secondaire = models.CharField(max_length=7, default="#3498db", help_text="Couleur secondaire (format hex)")
    
    # Informations bancaires (optionnel)
    iban = models.CharField(max_length=34, blank=True, null=True)
    bic = models.CharField(max_length=11, blank=True, null=True)
    banque = models.CharField(max_length=100, blank=True, null=True)
    
    # Textes personnalisables pour les documents
    texte_contrat = models.TextField(
        blank=True, 
        null=True,
        verbose_name=_("Texte personnalisé pour les contrats"),
        help_text=_("Texte personnalisé pour les obligations et conditions des contrats de bail")
    )
    texte_resiliation = models.TextField(
        blank=True, 
        null=True,
        verbose_name=_("Texte personnalisé pour les résiliations"),
        help_text=_("Texte personnalisé pour les conditions de sortie des résiliations")
    )
    
    # Métadonnées
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    actif = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'Configuration Entreprise'
        verbose_name_plural = 'Configurations Entreprise'
    
    def __str__(self):
        return f"Configuration {self.nom_entreprise}"
    
    def get_adresse_complete(self):
        """Retourne l'adresse complète formatée"""
        return f"{self.adresse}, {self.code_postal} {self.ville}, {self.pays}"
    
    def get_contact_complet(self):
        """Retourne les informations de contact formatées"""
        contact = f"Tél: {self.telephone}"
        if self.email:
            contact += f" | Email: {self.email}"
        if self.site_web:
            contact += f" | Web: {self.site_web}"
        return contact
    
    def get_informations_legales(self):
        """Retourne les informations légales formatées"""
        legal = f"SIRET: {self.siret}"
        if self.numero_licence:
            legal += f" | N° Licence: {self.numero_licence}"
        if self.capital_social:
            legal += f" | Capital: {self.capital_social}"
        if self.forme_juridique:
            legal += f" | {self.forme_juridique}"
        return legal
    
    @classmethod
    def get_configuration_active(cls):
        """Retourne la configuration active de l'entreprise"""
        return cls.objects.filter(actif=True).first()


class TemplateRecu(models.Model):
    """Modèles de templates pour les reçus."""
    
    nom = models.CharField(
        max_length=100,
        verbose_name=_("Nom du template")
    )
    description = models.TextField(
        blank=True,
        verbose_name=_("Description")
    )
    
    # Fichier template
    fichier_template = models.FileField(
        upload_to='templates_recus/',
        verbose_name=_("Fichier template"),
        help_text=_("Fichier HTML du template"),
        validators=[FileExtensionValidator(allowed_extensions=['html', 'htm'])]
    )
    
    # Options de personnalisation
    couleur_principale = models.CharField(
        max_length=7,
        default='#2c3e50',
        verbose_name=_("Couleur principale")
    )
    couleur_secondaire = models.CharField(
        max_length=7,
        default='#3498db',
        verbose_name=_("Couleur secondaire")
    )
    police_principale = models.CharField(
        max_length=50,
        default='Arial',
        verbose_name=_("Police principale")
    )
    
    # Options d'affichage
    afficher_logo = models.BooleanField(default=True, verbose_name=_("Afficher le logo"))
    afficher_siret = models.BooleanField(default=True, verbose_name=_("Afficher le SIRET"))
    afficher_tva = models.BooleanField(default=True, verbose_name=_("Afficher la TVA"))
    afficher_iban = models.BooleanField(default=False, verbose_name=_("Afficher l'IBAN"))
    
    # Métadonnées
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name=_("Date de création"))
    date_modification = models.DateTimeField(auto_now=True, verbose_name=_("Date de modification"))
    actif = models.BooleanField(default=True, verbose_name=_("Template actif"))
    par_defaut = models.BooleanField(default=False, verbose_name=_("Template par défaut"))
    is_deleted = models.BooleanField(default=False, verbose_name='Supprimé logiquement')
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name='Date de suppression')
    deleted_by = models.ForeignKey('utilisateurs.Utilisateur', null=True, blank=True, on_delete=models.SET_NULL, related_name='templaterecu_deleted', verbose_name='Supprimé par')
    
    class Meta:
        verbose_name = _("Template de reçu")
        verbose_name_plural = _("Templates de reçus")
        ordering = ['nom']
    
    def __str__(self):
        return self.nom
    
    def save(self, *args, **kwargs):
        """S'assurer qu'il n'y a qu'un seul template par défaut."""
        if self.par_defaut:
            TemplateRecu.objects.exclude(pk=self.pk).update(par_defaut=False)
        super().save(*args, **kwargs)
    
    @classmethod
    def get_template_par_defaut(cls):
        """Retourne le template par défaut."""
        return cls.objects.filter(par_defaut=True, actif=True).first()
    
    @classmethod
    def get_templates_actifs(cls):
        """Retourne tous les templates actifs."""
        return cls.objects.filter(actif=True).order_by('-par_defaut', 'nom')


class Devise(models.Model):
    code = models.CharField(max_length=3, unique=True)
    nom = models.CharField(max_length=32)
    symbole = models.CharField(max_length=8)
    taux_par_rapport_a_eur = models.DecimalField(max_digits=12, decimal_places=6, default=1)
    actif = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nom} ({self.code})"





class LogAudit(models.Model):
    """
    Modèle pour tracer toutes les actions critiques sur les entités importantes
    """
    # Informations de base
    modele = models.CharField(max_length=100, verbose_name=_("Modèle concerné"))
    instance_id = models.IntegerField(verbose_name=_("ID de l'instance"))
    
    # Action effectuée
    action = models.CharField(max_length=50, verbose_name=_("Action effectuée"))
    description = models.TextField(verbose_name=_("Description de l'action"))
    
    # Utilisateur et contexte
    utilisateur = models.ForeignKey(
        'utilisateurs.Utilisateur',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Utilisateur ayant effectué l'action")
    )
    ip_address = models.GenericIPAddressField(
        null=True, 
        blank=True, 
        verbose_name=_("Adresse IP")
    )
    user_agent = models.TextField(
        blank=True, 
        null=True, 
        verbose_name=_("User Agent")
    )
    
    # Données avant/après pour l'audit
    donnees_avant = models.JSONField(
        default=dict, 
        verbose_name=_("Données avant modification")
    )
    donnees_apres = models.JSONField(
        default=dict, 
        verbose_name=_("Données après modification")
    )
    
    # Horodatage
    date_action = models.DateTimeField(auto_now_add=True, verbose_name=_("Date de l'action"))
    
    # Champ pour la suppression logique
    deleted_by = models.ForeignKey(
        'utilisateurs.Utilisateur', 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL, 
        related_name='logaudit_deleted', 
        verbose_name='Supprimé par'
    )
    
    class Meta:
        verbose_name = 'Log d\'audit'
        verbose_name_plural = 'Logs d\'audit'
        ordering = ['-date_action']
        indexes = [
            models.Index(fields=['modele', 'instance_id']),
            models.Index(fields=['action']),
            models.Index(fields=['utilisateur']),
            models.Index(fields=['date_action']),
        ]
    
    def __str__(self):
        return f"{self.action} sur {self.modele} #{self.instance_id} par {self.utilisateur}"
    
    @classmethod
    def log_action(cls, modele, instance_id, action, utilisateur, description, 
                   donnees_avant=None, donnees_apres=None, request=None):
        """
        Méthode utilitaire pour créer un log d'audit
        """
        log = cls.objects.create(
            modele=modele,
            instance_id=instance_id,
            action=action,
            utilisateur=utilisateur,
            description=description,
            donnees_avant=donnees_avant or {},
            donnees_apres=donnees_apres or {}
        )
        
        # Ajouter les informations de contexte si disponible
        if request:
            log.ip_address = cls.get_client_ip(request)
            log.user_agent = request.META.get('HTTP_USER_AGENT', '')
            log.save()
        
        return log
    
    @staticmethod
    def get_client_ip(request):
        """Récupère l'adresse IP du client"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class AuditLog(models.Model):

    """

    Modèle pour enregistrer les actions des utilisateurs (audit trail)

    """

    ACTION_CHOICES = [

        ('create', 'Création'),

        ('update', 'Modification'),

        ('delete', 'Suppression'),

        ('view', 'Consultation'),

        ('login', 'Connexion'),

        ('logout', 'Déconnexion'),

        ('export', 'Export'),

        ('import', 'Import'),

        ('validation', 'Validation'),

        ('rejection', 'Rejet'),

    ]

    

    user = models.ForeignKey(

        settings.AUTH_USER_MODEL, 

        on_delete=models.CASCADE, 

        verbose_name="Utilisateur",

        related_name='audit_logs',

        null=True,

        blank=True

    )

    action = models.CharField(

        max_length=20, 

        choices=ACTION_CHOICES, 

        verbose_name="Action"

    )

    content_type = models.ForeignKey(

        ContentType, 

        on_delete=models.CASCADE, 

        verbose_name="Type de contenu",

        null=True, 

        blank=True

    )

    object_id = models.PositiveIntegerField(

        verbose_name="ID de l'objet",

        null=True, 

        blank=True

    )

    object_repr = models.CharField(

        max_length=200, 

        verbose_name="Représentation de l'objet",

        null=True, 

        blank=True

    )

    details = models.JSONField(

        verbose_name="Détails",

        null=True, 

        blank=True

    )

    ip_address = models.GenericIPAddressField(

        verbose_name="Adresse IP",

        null=True, 

        blank=True

    )

    user_agent = models.TextField(

        verbose_name="User Agent",

        null=True, 

        blank=True

    )

    timestamp = models.DateTimeField(

        auto_now_add=True, 

        verbose_name="Horodatage"

    )

    

    class Meta:

        verbose_name = "Log d'audit"

        verbose_name_plural = "Logs d'audit"

        ordering = ['-timestamp']

        indexes = [

            models.Index(fields=['user', 'action', 'timestamp']),

            models.Index(fields=['content_type', 'object_id']),

            models.Index(fields=['timestamp']),

        ]

    

    def __str__(self):

        return f"{self.user.username} - {self.get_action_display()} - {self.timestamp}"

    

    def get_absolute_url(self):

        return reverse('admin:core_auditlog_change', args=[self.id])


