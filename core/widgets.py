"""
Widgets personnalisés pour les identifiants uniques
"""

from django import forms
from django.forms.widgets import TextInput
from django.utils.safestring import mark_safe
from django.urls import reverse
import json


class UniqueIdWidget(TextInput):
    """Widget personnalisé pour les identifiants uniques avec bouton de génération."""
    
    def __init__(self, entity_type, attrs=None, generate_on_load=True):
        """
        Initialise le widget.
        
        Args:
            entity_type: Type d'entité pour la génération d'ID
            attrs: Attributs HTML additionnels
            generate_on_load: Générer automatiquement un ID au chargement
        """
        self.entity_type = entity_type
        self.generate_on_load = generate_on_load
        
        default_attrs = {
            'class': 'form-control unique-id-input',
            'readonly': True,
            'data-entity-type': entity_type,
        }
        
        if attrs:
            default_attrs.update(attrs)
        
        super().__init__(attrs=default_attrs)
    
    def format_value(self, value):
        """Formate la valeur pour l'affichage."""
        if value is None:
            return ''
        return str(value)
    
    def render(self, name, value, attrs=None, renderer=None):
        """Rend le widget avec le bouton de génération."""
        # Rendu du champ de base
        input_html = super().render(name, value, attrs, renderer)
        
        # Bouton de génération
        button_html = f'''
        <button type="button" class="btn btn-outline-primary btn-generate-id" 
                data-target="{attrs.get('id', name) if attrs else name}"
                data-entity-type="{self.entity_type}"
                title="Générer un nouvel identifiant">
            <i class="bi bi-arrow-clockwise"></i>
        </button>
        '''
        
        # Conteneur avec input group
        widget_html = f'''
        <div class="input-group">
            {input_html}
            <div class="input-group-append">
                {button_html}
            </div>
        </div>
        <small class="form-text text-muted">
            Format: {self._get_format_preview()}
        </small>
        '''
        
        return mark_safe(widget_html)
    
    def _get_format_preview(self):
        """Retourne un aperçu du format d'ID."""
        try:
            from core.services.unique_id_service import UniqueIdService
            return UniqueIdService.preview_code_format(self.entity_type)
        except Exception as e:
            # Log l'erreur et retourne un message par défaut
            print(f"Erreur lors de la récupération du format: {e}")
            return "Format non disponible"
    
    class Media:
        css = {
            'all': ('css/unique_id_widget.css',)
        }
        js = ('js/unique_id_widget.js',)


class ReadOnlyUniqueIdWidget(TextInput):
    """Widget en lecture seule pour afficher les identifiants existants."""
    
    def __init__(self, entity_type, attrs=None):
        self.entity_type = entity_type
        
        default_attrs = {
            'class': 'form-control',
            'readonly': True,
            'style': 'background-color: #f8f9fa;'
        }
        
        if attrs:
            default_attrs.update(attrs)
        
        super().__init__(attrs=default_attrs)
    
    def render(self, name, value, attrs=None, renderer=None):
        """Rend le widget en lecture seule avec style."""
        input_html = super().render(name, value, attrs, renderer)
        
        widget_html = f'''
        <div class="unique-id-readonly">
            {input_html}
            <small class="form-text text-muted">
                <i class="bi bi-lock"></i> Identifiant généré automatiquement
            </small>
        </div>
        '''
        
        return mark_safe(widget_html)


class UniqueIdField(forms.CharField):
    """Champ personnalisé pour les identifiants uniques."""
    
    def __init__(self, entity_type, generate_on_load=True, *args, **kwargs):
        """
        Initialise le champ.
        
        Args:
            entity_type: Type d'entité pour la génération d'ID
            generate_on_load: Générer automatiquement un ID au chargement
        """
        self.entity_type = entity_type
        self.generate_on_load = generate_on_load
        
        # Configuration par défaut
        kwargs.setdefault('required', True)
        kwargs.setdefault('max_length', 30)
        kwargs.setdefault('help_text', f'Identifiant unique généré automatiquement')
        
        # Widget standard avec attributs personnalisés
        widget_attrs = {
            'class': 'form-control unique-id-input',
            'readonly': True,
            'data-entity-type': entity_type,
        }
        
        if 'widget' not in kwargs:
            kwargs['widget'] = forms.TextInput(attrs=widget_attrs)
        
        super().__init__(*args, **kwargs)
    
    def clean(self, value):
        """Valide l'identifiant unique."""
        value = super().clean(value)
        
        if value:
            try:
                from core.services.unique_id_service import validate_unique_id
                validation = validate_unique_id(value, self.entity_type)
                
                if not validation['valid']:
                    raise forms.ValidationError(validation['message'])
            except Exception as e:
                # Log l'erreur et on accepte la valeur
                print(f"Erreur lors de la validation d'ID: {e}")
                pass
        
        return value
    
    def prepare_value(self, value):
        """Prépare la valeur pour l'affichage."""
        if value is None and self.generate_on_load:
            # Générer une valeur par défaut
            try:
                from core.services.unique_id_service import UniqueIdService
                return UniqueIdService.generate_code(self.entity_type)
            except Exception as e:
                # Log l'erreur et retourne None
                print(f"Erreur lors de la génération d'ID: {e}")
                return None
        return value
