"""
Système de prévention des doublons pour les modèles
"""
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class DuplicatePreventionMixin:
    """
    Mixin pour prévenir les doublons basés sur des champs spécifiques
    """
    
    # Champs à vérifier pour les doublons (à redéfinir dans chaque modèle)
    duplicate_check_fields = []
    
    def clean(self):
        """
        Validation personnalisée pour prévenir les doublons
        """
        super().clean()
        self._check_duplicates()
    
    def _check_duplicates(self):
        """
        Vérifie s'il existe des doublons basés sur les champs spécifiés
        """
        if not self.duplicate_check_fields:
            return
        
        # Construire les filtres pour la recherche de doublons
        filters = {}
        for field in self.duplicate_check_fields:
            value = getattr(self, field, None)
            if value:  # Seulement si la valeur n'est pas vide
                filters[field] = value
        
        if not filters:
            return
        
        # Exclure l'instance actuelle si c'est une mise à jour
        queryset = self.__class__.objects.filter(**filters)
        if self.pk:
            queryset = queryset.exclude(pk=self.pk)
        
        # Exclure les enregistrements supprimés logiquement
        if hasattr(self, 'is_deleted'):
            queryset = queryset.filter(is_deleted=False)
        
        if queryset.exists():
            # Construire le message d'erreur
            field_names = [self._meta.get_field(field).verbose_name for field in self.duplicate_check_fields]
            field_values = [str(getattr(self, field, '')) for field in self.duplicate_check_fields]
            
            error_message = _(
                "Un enregistrement avec ces informations existe déjà : "
            )
            for name, value in zip(field_names, field_values):
                error_message += f"{name}: {value}, "
            error_message = error_message.rstrip(", ")
            
            raise ValidationError(error_message)


def validate_unique_contact_info(model_class, instance, fields_to_check):
    """
    Fonction utilitaire pour valider l'unicité des informations de contact
    
    Args:
        model_class: Classe du modèle à vérifier
        instance: Instance à valider
        fields_to_check: Liste des champs à vérifier
    """
    if not fields_to_check:
        return
    
    # Construire les filtres
    filters = {}
    for field in fields_to_check:
        value = getattr(instance, field, None)
        if value and value.strip():  # Seulement si la valeur n'est pas vide
            filters[field] = value
    
    if not filters:
        return
    
    # Exclure l'instance actuelle si c'est une mise à jour
    queryset = model_class.objects.filter(**filters)
    if instance.pk:
        queryset = queryset.exclude(pk=instance.pk)
    
    # Exclure les enregistrements supprimés logiquement
    if hasattr(instance, 'is_deleted'):
        queryset = queryset.filter(is_deleted=False)
    
    if queryset.exists():
        # Construire le message d'erreur
        field_names = [model_class._meta.get_field(field).verbose_name for field in fields_to_check]  # pylint: disable=protected-access
        field_values = [str(getattr(instance, field, '')) for field in fields_to_check]
        
        error_message = _(
            "Un enregistrement avec ces informations de contact existe déjà : "
        )
        for name, value in zip(field_names, field_values):
            error_message += f"{name}: {value}, "
        error_message = error_message.rstrip(", ")
        
        raise ValidationError(error_message)