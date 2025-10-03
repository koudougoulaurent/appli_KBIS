"""
Context processors pour la navigation dynamique et la configuration entreprise
"""

from django.urls import reverse
from .dynamic_navigation import DynamicNavigationSystem

def dynamic_navigation(request):
    """
    Context processor pour ajouter la navigation dynamique à tous les templates
    """
    # Déterminer le module actuel basé sur l'URL
    current_module = None
    object_id = None
    
    path = request.path
    
    if '/proprietes/' in path:
        current_module = 'proprietes'
        # Extraire l'ID de l'objet si présent
        if '/detail/' in path or '/modifier/' in path:
            try:
                object_id = path.split('/')[-2]
                if object_id.isdigit():
                    object_id = int(object_id)
                else:
                    object_id = None
            except (ValueError, IndexError):
                object_id = None
    elif '/paiements/' in path:
        current_module = 'paiements'
        if '/detail/' in path or '/modifier/' in path:
            try:
                object_id = path.split('/')[-2]
                if object_id.isdigit():
                    object_id = int(object_id)
                else:
                    object_id = None
            except (ValueError, IndexError):
                object_id = None
    elif '/contrats/' in path:
        current_module = 'contrats'
        if '/detail/' in path or '/modifier/' in path:
            try:
                object_id = path.split('/')[-2]
                if object_id.isdigit():
                    object_id = int(object_id)
                else:
                    object_id = None
            except (ValueError, IndexError):
                object_id = None
    elif '/utilisateurs/' in path:
        current_module = 'utilisateurs'
        if '/detail/' in path or '/modifier/' in path:
            try:
                object_id = path.split('/')[-2]
                if object_id.isdigit():
                    object_id = int(object_id)
                else:
                    object_id = None
            except (ValueError, IndexError):
                object_id = None
    
    # Récupérer la navigation contextuelle
    try:
        navigation = DynamicNavigationSystem.get_contextual_links(
            request, current_module, object_id
        )
    except Exception:
        # Navigation par défaut en cas d'erreur
        navigation = {
            'primary': [
                {
                    'url': reverse('core:dashboard'),
                    'label': 'Dashboard',
                    'icon': 'speedometer2',
                    'active': True
                }
            ],
            'secondary': [],
            'quick_actions': [],
            'breadcrumbs': [
                {
                    'url': reverse('core:dashboard'),
                    'label': 'Dashboard',
                    'icon': 'house'
                }
            ]
        }
    
    return {
        'navigation': navigation,
        'current_module': current_module,
        'object_id': object_id
    }

def entreprise_config(request):  # pylint: disable=unused-argument
    """
    Context processor pour ajouter la configuration de l'entreprise à tous les templates
    """
    # Configuration par défaut de l'entreprise
    config = {
        'nom_entreprise': 'GESTIMMOB',
        'devise': 'F CFA',
        'logo_url': '/static/images/logo.png',
        'couleur_principale': '#6366f1',
        'version': '1.0.0',
        'support_email': 'support@gestimmob.com',
        'telephone_support': '+225 XX XX XX XX',
        'adresse': 'Abidjan, Côte d\'Ivoire',
        'site_web': 'https://gestimmob.com'
    }
    
    # Essayer de récupérer la configuration depuis la base de données
    try:
        from .models import ConfigurationEntreprise
        config_db = ConfigurationEntreprise.objects.first()  # type: ignore
        if config_db:
            config.update({
                'nom_entreprise': config_db.nom_entreprise or config['nom_entreprise'],
                'devise': config_db.devise or config['devise'],
                'logo_url': config_db.logo.url if config_db.logo else config['logo_url'],
                'couleur_principale': config_db.couleur_principale or config['couleur_principale'],
                'support_email': config_db.email_support or config['support_email'],
                'telephone_support': config_db.telephone_support or config['telephone_support'],
                'adresse': config_db.adresse or config['adresse'],
                'site_web': config_db.site_web or config['site_web']
            })
    except Exception:
        # En cas d'erreur, utiliser la configuration par défaut
        pass
    
    return {
        'entreprise': config
    }