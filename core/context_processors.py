from core.models import Devise

def devise_active(request):
    return {'devise_active': getattr(request, 'devise_active', None)}

def devises_actives(request):
    return {'devises_actives': Devise.objects.filter(actif=True)} 