from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator
from django.utils import timezone
from core.models import AuditLog
from proprietes.managers import NonDeletedManager
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q


class GroupeTravail(models.Model):
    """Modèle pour les groupes de travail de l'application GESTIMMOB"""
    
    CHOIX_GROUPES = [
        ('CAISSE', 'CAISSE'),
        ('CONTROLES', 'CONTROLES'),
        ('ADMINISTRATION', 'ADMINISTRATION'),
        ('PRIVILEGE', 'PRIVILEGE'),
    ]
    
    nom = models.CharField(max_length=20, choices=CHOIX_GROUPES, unique=True)
    description = models.TextField(blank=True)
    permissions = models.JSONField(default=dict, help_text="Permissions spécifiques au groupe")
    actif = models.BooleanField(default=True)
    date_creation = models.DateTimeField(default=timezone.now)
    date_modification = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Groupe de travail"
        verbose_name_plural = "Groupes de travail"
        ordering = ['nom']
    
    def __str__(self):
        return self.nom
    
    def get_permissions_list(self):
        """Retourne la liste des permissions du groupe"""
        return self.permissions.get('modules', [])


# Manager personnalisé pour les utilisateurs - Version corrigée
class UtilisateurManager(BaseUserManager):
    def get_queryset(self):
        # Utiliser le QuerySet par défaut et filtrer sur is_deleted
        return super().get_queryset().filter(is_deleted=False)
    
    def all_with_deleted(self):
        # Méthode pour accéder à tous les utilisateurs, même supprimés
        return super().get_queryset()
    
    def all_users(self):
        # Méthode pour accéder à tous les utilisateurs (actifs et inactifs)
        return super().get_queryset()
    
    def create_user(self, username, email=None, password=None, **extra_fields):
        """Créer un utilisateur normal"""
        if not username:
            raise ValueError('Le nom d\'utilisateur est obligatoire')
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        """Créer un superutilisateur"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Le superutilisateur doit avoir is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Le superutilisateur doit avoir is_superuser=True.')
        
        return self.create_user(username, email, password, **extra_fields)


class Utilisateur(AbstractUser):
    """Modèle utilisateur étendu avec groupe de travail"""
    
    # Champs supplémentaires
    telephone = models.CharField(max_length=100, blank=True, null=True)  # Aucune validation - temporaire
    adresse = models.TextField(blank=True)
    date_naissance = models.DateField(null=True, blank=True)
    photo = models.ImageField(upload_to='photos_utilisateurs/', null=True, blank=True)
    
    # Groupe de travail
    groupe_travail = models.ForeignKey(
        GroupeTravail, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='utilisateurs'
    )
    
    # Informations professionnelles
    poste = models.CharField(max_length=100, blank=True)
    departement = models.CharField(max_length=100, blank=True)
    date_embauche = models.DateField(null=True, blank=True)
    
    # Statut
    actif = models.BooleanField(default=True)
    derniere_connexion = models.DateTimeField(null=True, blank=True)
    
    # Métadonnées
    date_creation = models.DateTimeField(default=timezone.now)
    date_modification = models.DateTimeField(auto_now=True)
    
    # Suppression logique
    is_deleted = models.BooleanField(default=False, verbose_name='Supprimé logiquement')
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name='Date de suppression')
    deleted_by = models.ForeignKey(
        'self', 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL, 
        related_name='utilisateur_deleted', 
        verbose_name='Supprimé par'
    )
    
    # Managers
    objects = UtilisateurManager()
    all_objects = models.Manager()
    
    class Meta:
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"
        ordering = ['username']
    
    def __str__(self):
        return f"{self.username} ({self.get_full_name()})"
    
    def get_nom_complet(self):
        """Retourne le nom complet de l'utilisateur"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        else:
            return self.username
    
    def get_groupe_display(self):
        """Retourne le nom du groupe de travail"""
        return self.groupe_travail.nom if self.groupe_travail else "Aucun groupe"
    
    def has_module_permission(self, module):
        """Vérifie si l'utilisateur a accès à un module spécifique"""
        if not self.groupe_travail:
            return False
        return module in self.groupe_travail.get_permissions_list()
    
    def get_accessible_modules(self):
        """Retourne la liste des modules accessibles à l'utilisateur"""
        if not self.groupe_travail:
            return []
        return self.groupe_travail.get_permissions_list()
    
    # === PERMISSIONS SPÉCIALES POUR LE GROUPE PRIVILEGE ===
    
    def is_privilege_user(self):
        """Vérifie si l'utilisateur appartient au groupe PRIVILEGE"""
        return self.groupe_travail and self.groupe_travail.nom.upper() == 'PRIVILEGE'
    
    def can_delete_any_element(self, model_instance):
        """
        Vérifie si l'utilisateur PRIVILEGE peut supprimer un élément.
        Retourne (peut_supprimer, peut_désactiver, raison, détails_références)
        """
        if not self.is_privilege_user():
            return False, False, "Utilisateur non autorisé", None
        
        # Vérifier si l'élément est référencé ailleurs
        references = self._check_references(model_instance)
        
        if not references:
            # Aucune référence trouvée, peut supprimer
            return True, False, "Aucune référence trouvée", None
        else:
            # Références trouvées, peut seulement désactiver
            details = self.get_detailed_references_info(model_instance)
            return False, True, f"Élément référencé par d'autres éléments", details
    
    def can_manage_profiles(self):
        """Vérifie si l'utilisateur peut créer/modifier des profils"""
        return self.is_privilege_user()
    
    def _check_references(self, model_instance):
        """
        Vérifie si un élément est référencé par d'autres modèles.
        Retourne une liste des références trouvées avec plus de détails.
        """
        references = []
        model_class = model_instance.__class__
        model_name = model_class.__name__
        
        # Définir les relations à vérifier selon le type de modèle
        relations_to_check = self._get_relations_to_check(model_name)
        
        for relation_info in relations_to_check:
            try:
                related_model = relation_info['model']
                field_name = relation_info['field']
                
                # Vérifier les références directes
                filter_kwargs = {field_name: model_instance}
                related_objects = related_model.objects.filter(**filter_kwargs)
                count = related_objects.count()
                
                if count > 0:
                    # Ajouter des informations détaillées sur les références
                    reference_info = {
                        'model': related_model._meta.verbose_name_plural,
                        'count': count,
                        'field': field_name,
                        'sample_objects': list(related_objects[:3].values('id', 'pk')),  # Échantillon des objets
                        'model_name': related_model.__name__
                    }
                    references.append(reference_info)
                    
            except Exception as e:
                # Ignorer les erreurs de relation
                continue
        
        return references
    
    def get_detailed_references_info(self, model_instance):
        """
        Retourne des informations détaillées sur les références pour l'affichage.
        Utile pour l'interface utilisateur.
        """
        references = self._check_references(model_instance)
        
        if not references:
            return None
        
        detailed_info = {
            'has_references': True,
            'total_references': sum(ref['count'] for ref in references),
            'references_by_model': references,
            'summary': self._format_references_summary(references)
        }
        
        return detailed_info
    
    def _format_references_summary(self, references):
        """Formate un résumé lisible des références"""
        if not references:
            return "Aucune référence trouvée"
        
        summary_parts = []
        for ref in references:
            summary_parts.append(f"{ref['model']} ({ref['count']})")
        
        return f"Référencé par : {', '.join(summary_parts)}"
    
    def _get_relations_to_check(self, model_name):
        """
        Retourne la liste des relations à vérifier selon le type de modèle.
        """
        # Utiliser des imports dynamiques pour éviter les imports circulaires
        try:
            from proprietes.models import Bailleur, Locataire, Propriete, TypeBien, ChargesBailleur
            from core.models import TemplateRecu, Devise
            
            relations_map = {
                'Bailleur': [
                    {'model': Propriete, 'field': 'bailleur'},
                ],
                'Locataire': [
                    # Ajouter les relations quand les modèles de contrats seront créés
                ],
                'Propriete': [
                    # Ajouter les relations quand les modèles de contrats seront créés
                    {'model': ChargesBailleur, 'field': 'propriete'},
                ],
                'TypeBien': [
                    {'model': Propriete, 'field': 'type_bien'},
                ],
                'TemplateRecu': [
                    # Ajouter les relations si nécessaire
                ],
                'Devise': [
                    # Ajouter les relations si nécessaire
                ],
            }
            
            return relations_map.get(model_name, [])
        except ImportError:
            # Si les modèles ne sont pas encore disponibles, retourner une liste vide
            return []
    
    def safe_delete_element(self, model_instance, request=None):
        """
        Supprime ou désactive un élément selon les permissions PRIVILEGE.
        Retourne (succès, message, action_effectuée, détails_références)
        """
        if not self.is_privilege_user():
            return False, "Permissions insuffisantes", None, None
        
        peut_supprimer, peut_désactiver, raison, détails_références = self.can_delete_any_element(model_instance)
        
        if peut_supprimer:
            # Suppression logique
            model_instance.is_deleted = True
            model_instance.deleted_at = timezone.now()
            model_instance.deleted_by = self
            model_instance.save()
            
            # Log d'audit
            self._log_audit_action(model_instance, 'delete', request)
            
            return True, f"Élément supprimé avec succès", "suppression", None
            
        elif peut_désactiver:
            # Désactivation
            if hasattr(model_instance, 'est_actif'):
                model_instance.est_actif = False
                model_instance.save()
                action = "désactivation"
            elif hasattr(model_instance, 'actif'):
                model_instance.actif = False
                model_instance.save()
                action = "désactivation"
            else:
                return False, "Impossible de désactiver cet élément", None, détails_références
            
            # Log d'audit
            self._log_audit_action(model_instance, 'update', request, 
                                 old_data={'actif': True}, 
                                 new_data={'actif': False})
            
            return True, f"Élément désactivé car référencé: {raison}", action, détails_références
            
        else:
            return False, f"Impossible de supprimer ou désactiver: {raison}", None, détails_références
    
    def _log_audit_action(self, model_instance, action, request=None, old_data=None, new_data=None):
        """Enregistre l'action dans le journal d'audit"""
        try:
            # Convertir l'action en minuscules pour correspondre aux nouveaux choix
            action = action.lower()
            
            # Créer un dictionnaire de détails avec les anciennes et nouvelles données
            details = {}
            if old_data:
                details['old_data'] = old_data
            if new_data:
                details['new_data'] = new_data
            
            AuditLog.objects.create(
                content_type=ContentType.objects.get_for_model(model_instance),
                object_id=model_instance.pk,
                action=action,
                details=details if details else None,
                object_repr=str(model_instance),
                user=self,
                ip_address=request.META.get('REMOTE_ADDR') if request else None,
                user_agent=request.META.get('HTTP_USER_AGENT') if request else None,
            )
        except Exception as e:
            # Ignorer les erreurs de log
            pass

# Les managers sont maintenant définis directement dans la classe
