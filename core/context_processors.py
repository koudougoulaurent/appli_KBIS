from core.models import Devise, ConfigurationEntreprise

def devise_active(request):
    return {'devise_active': getattr(request, 'devise_active', None)}

def devises_actives(request):
    return {'devises_actives': Devise.objects.filter(actif=True)}

def entreprise_config(request):
    """Processeur de contexte pour la configuration de l'entreprise"""
    try:
        config = ConfigurationEntreprise.get_configuration_active()
        return {
            'config_entreprise': config,
            'nom_entreprise': config.nom_entreprise,
            'slogan_entreprise': config.slogan,
        }
    except Exception:
        return {
            'config_entreprise': None,
            'nom_entreprise': 'KBIS IMMOBILIER',
            'slogan_entreprise': 'Système de Gestion Immobilière',
        } 