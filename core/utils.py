from core.models import Devise, ConfigurationEntreprise
from django.conf import settings

def convertir_montant(montant, devise_source, devise_cible):
    if not devise_source or not devise_cible:
        return montant
    if devise_source.code == devise_cible.code:
        return montant
    # Conversion via EUR comme pivot
    montant_eur = montant / devise_source.taux_par_rapport_a_eur
    montant_cible = montant_eur * devise_cible.taux_par_rapport_a_eur
    return round(montant_cible, 2)

def format_currency_xof(value, show_decimals=True, short_format=False):
    """
    Formate un montant en XOF selon les standards du Franc CFA
    
    Args:
        value: Le montant à formater
        show_decimals: Afficher les décimales (défaut: True)
        short_format: Utiliser les abréviations K/M (défaut: False)
    
    Returns:
        str: Le montant formaté avec XOF
    """
    try:
        if value is None or value == '':
            return "0 XOF"
        
        amount = float(value)
        
        # Format court avec abréviations
        if short_format:
            if amount >= 1000000:
                return f"{amount/1000000:,.1f}M XOF".replace(',', ' ').replace('.', ',')
            elif amount >= 1000:
                return f"{amount/1000:,.0f}K XOF".replace(',', ' ')
        
        # Format standard
        if show_decimals and amount != int(amount):
            # Afficher avec 2 décimales si nécessaire
            formatted = f"{amount:,.2f}".replace(',', ' ').replace('.', ',')
        else:
            # Format entier
            formatted = f"{int(amount):,}".replace(',', ' ')
        
        return f"{formatted} XOF"
        
    except (ValueError, TypeError):
        return f"{value} XOF"

def get_currency_settings():
    """Récupère les paramètres de devise depuis les settings"""
    return getattr(settings, 'CURRENCY_SETTINGS', {
        'DEFAULT_CURRENCY': 'XOF',
        'CURRENCY_SYMBOL': 'XOF',
        'CURRENCY_NAME': 'Franc CFA',
        'CURRENCY_CODE': 'XOF',
        'DECIMAL_PLACES': 2,
        'USE_THOUSAND_SEPARATOR': True,
        'THOUSAND_SEPARATOR': ' ',
        'DECIMAL_SEPARATOR': ',',
    })

def inserer_devises_principales():
    from core.models import Devise
    devises = [
        {'code': 'XOF', 'nom': 'Franc CFA', 'symbole': 'XOF', 'taux_par_rapport_a_eur': 655.957},
        {'code': 'USD', 'nom': 'Dollar US', 'symbole': '$', 'taux_par_rapport_a_eur': 1.08},
        {'code': 'XOF', 'nom': 'Franc CFA BCEAO', 'symbole': 'XOF', 'taux_par_rapport_a_eur': 655.957},
    ]
    for d in devises:
        Devise.objects.update_or_create(
            code=d['code'],
            defaults={
                'nom': d['nom'],
                'symbole': d['symbole'],
                'taux_par_rapport_a_eur': d['taux_par_rapport_a_eur'],
                'actif': True
            }
        ) 

def check_group_permissions(user, allowed_groups, operation_type='modify'):
    """
    Vérifie les permissions d'un utilisateur selon son groupe et le type d'opération
    
    Args:
        user: L'utilisateur connecté
        allowed_groups: Liste des groupes autorisés (ex: ['PRIVILEGE', 'ADMINISTRATION'])
        operation_type: Type d'opération ('add', 'modify', 'delete', 'view', 'validate', 'resilier')
    
    Returns:
        dict: Dictionnaire avec 'allowed' (bool) et 'message' (str)
    """
    if not user.is_authenticated:
        return {'allowed': False, 'message': 'Utilisateur non authentifié.'}
    
    groupe = getattr(user, 'groupe_travail', None)
    if not groupe:
        return {'allowed': False, 'message': 'Aucun groupe de travail assigné.'}
    
    groupe_nom = groupe.nom.upper()
    
    # PRIVILEGE a TOUS les droits sur TOUTES les fonctionnalités sensibles
    if groupe_nom == 'PRIVILEGE':
        return {'allowed': True, 'message': 'Accès autorisé (groupe PRIVILEGE).'}
    
    # SÉCURITÉ STRICTE : Seul PRIVILEGE a accès aux fonctionnalités sensibles
    operations_sensibles = ['modify', 'delete', 'validate', 'resilier']
    if operation_type in operations_sensibles:
        return {'allowed': False, 'message': f'Accès refusé. Seul le groupe PRIVILEGE peut effectuer des {operation_type}.'}
    
    # CAISSE : Lecture uniquement, pas de modification/suppression
    if groupe_nom == 'CAISSE':
        if operation_type == 'view':
            return {'allowed': True, 'message': 'Accès autorisé (groupe CAISSE - consultation uniquement).'}
        elif operation_type == 'add':
            # CAISSE peut ajouter des paiements mais pas d'autres éléments sensibles
            return {'allowed': True, 'message': 'Accès autorisé (groupe CAISSE - ajout de paiements).'}
        else:
            return {'allowed': False, 'message': 'Le groupe CAISSE ne peut que consulter et ajouter des paiements.'}
    
    # CONTROLES : Lecture et audit uniquement
    if groupe_nom == 'CONTROLES':
        if operation_type == 'view':
            return {'allowed': True, 'message': 'Accès autorisé (groupe CONTROLES - audit et vérification).'}
        else:
            return {'allowed': False, 'message': 'Le groupe CONTROLES peut consulter et vérifier mais pas modifier, supprimer ou valider.'}
    
    # ADMINISTRATION : Lecture et ajout limité uniquement
    if groupe_nom == 'ADMINISTRATION':
        if operation_type == 'view':
            return {'allowed': True, 'message': 'Accès autorisé (groupe ADMINISTRATION - consultation).'}
        elif operation_type == 'add':
            # ADMINISTRATION peut ajouter des éléments de base mais pas de fonctionnalités sensibles
            return {'allowed': True, 'message': 'Accès autorisé (groupe ADMINISTRATION - ajout d\'éléments de base).'}
        else:
            return {'allowed': False, 'message': 'Le groupe ADMINISTRATION peut consulter et ajouter des éléments de base mais pas modifier, supprimer ou valider.'}
    
    # Autres groupes : Vérifier la liste allowed_groups pour les opérations non sensibles
    if groupe_nom in allowed_groups and operation_type not in operations_sensibles:
        return {'allowed': True, 'message': f'Accès autorisé (groupe {groupe_nom}).'}
    
    return {'allowed': False, 'message': f'Accès refusé. Groupe requis: {", ".join(allowed_groups)}.'} 

def log_audit_action(request, action, content_type=None, object_id=None, object_repr=None, details=None):
    """
    Enregistre une action dans les logs d'audit
    
    Args:
        request: La requête HTTP
        action: L'action effectuée (create, update, delete, view, etc.)
        content_type: Le type de contenu (optionnel)
        object_id: L'ID de l'objet (optionnel)
        object_repr: La représentation textuelle de l'objet (optionnel)
        details: Détails supplémentaires en JSON (optionnel)
    """
    try:
        from .models import AuditLog
        from django.contrib.contenttypes.models import ContentType
        
        # Récupérer l'adresse IP et le user agent
        ip_address = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Créer le log d'audit
        AuditLog.objects.create(
            user=request.user,
            action=action,
            content_type=content_type,
            object_id=object_id,
            object_repr=object_repr,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent
        )
    except Exception as e:
        # En cas d'erreur, on log mais on ne fait pas échouer l'opération principale
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Erreur lors de l'enregistrement du log d'audit: {e}")

def get_client_ip(request):
    """
    Récupère l'adresse IP réelle du client
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def detecter_anomalies():
    """
    Détecte les anomalies dans le système
    
    Returns:
        dict: Dictionnaire contenant les anomalies détectées
    """
    from django.utils import timezone
    from datetime import timedelta
    from django.db.models import Q
    from django.contrib.auth import get_user_model
    
    User = get_user_model()
    anomalies = []
    stats = {'danger': 0, 'warning': 0, 'info': 0, 'total': 0}
    
    try:
        # 1. Paiements en retard (plus de 30 jours)
        from paiements.models import Paiement
        date_limite = timezone.now().date() - timedelta(days=30)
        paiements_retard = Paiement.objects.filter(
            date_echeance__lt=date_limite,
            statut='en_attente'
        ).select_related('contrat__locataire')
        
        if paiements_retard.exists():
            anomalies.append({
                'type': 'paiement_retard',
                'titre': f'{paiements_retard.count()} paiement(s) en retard',
                'description': f'Paiements en retard de plus de 30 jours',
                'severite': 'danger',
                'date': timezone.now(),
                'url': '/paiements/liste/'
            })
            stats['danger'] += 1
        
        # 2. Contrats expirant dans les 30 jours
        from contrats.models import Contrat
        date_expiration = timezone.now().date() + timedelta(days=30)
        contrats_expirant = Contrat.objects.filter(
            date_fin__lte=date_expiration,
            statut='actif'
        ).select_related('locataire')
        
        if contrats_expirant.exists():
            anomalies.append({
                'type': 'contrat_expirant',
                'titre': f'{contrats_expirant.count()} contrat(s) expirant bientôt',
                'description': f'Contrats expirant dans les 30 prochains jours',
                'severite': 'warning',
                'date': timezone.now(),
                'url': '/contrats/liste/'
            })
            stats['warning'] += 1
        
        # 3. Propriétés vides depuis plus de 6 mois
        from proprietes.models import Propriete
        date_limite_vide = timezone.now().date() - timedelta(days=180)
        proprietes_vides = Propriete.objects.filter(
            statut='disponible',
            date_disponibilite__lt=date_limite_vide
        )
        
        if proprietes_vides.exists():
            anomalies.append({
                'type': 'propriete_vide',
                'titre': f'{proprietes_vides.count()} propriété(s) vide(s) depuis longtemps',
                'description': f'Propriétés disponibles depuis plus de 6 mois',
                'severite': 'info',
                'date': timezone.now(),
                'url': '/proprietes/liste/'
            })
            stats['info'] += 1
        
        # 4. Utilisateurs inactifs depuis plus de 90 jours
        date_limite_inactif = timezone.now() - timedelta(days=90)
        utilisateurs_inactifs = User.objects.filter(
            last_login__lt=date_limite_inactif,
            is_active=True
        ).exclude(is_superuser=True)
        
        if utilisateurs_inactifs.exists():
            anomalies.append({
                'type': 'utilisateur_inactif',
                'titre': f'{utilisateurs_inactifs.count()} utilisateur(s) inactif(s)',
                'description': f'Utilisateurs qui ne se sont pas connectés depuis 90 jours',
                'severite': 'warning',
                'date': timezone.now(),
                'url': '/utilisateurs/liste/'
            })
            stats['warning'] += 1
        
        # Calculer le total
        stats['total'] = len(anomalies)
        
    except Exception as e:
        # En cas d'erreur, on retourne une anomalie système
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Erreur lors de la détection d'anomalies: {e}")
        
        anomalies.append({
            'type': 'erreur_systeme',
            'titre': 'Erreur de détection d\'anomalies',
            'description': f'Erreur technique: {str(e)}',
            'severite': 'danger',
            'date': timezone.now(),
            'url': None
        })
        stats['danger'] += 1
        stats['total'] = 1
    
    return {
        'anomalies': anomalies,
        'stats_anomalies': stats,
        'paiements_retard': paiements_retard if 'paiements_retard' in locals() else [],
        'contrats_expirant': contrats_expirant if 'contrats_expirant' in locals() else [],
        'proprietes_vides': proprietes_vides if 'proprietes_vides' in locals() else [],
        'utilisateurs_inactifs': utilisateurs_inactifs if 'utilisateurs_inactifs' in locals() else []
    }


def get_context_with_entreprise_config(base_context=None):
    """
    Fonction utilitaire pour ajouter la configuration d'entreprise au contexte des templates.
    Utilisée pour tous les documents générés (quittances, reçus, contrats, etc.)
    
    Args:
        base_context (dict): Contexte de base existant
        
    Returns:
        dict: Contexte enrichi avec la configuration d'entreprise
    """
    if base_context is None:
        base_context = {}
    
    # Récupérer la configuration active de l'entreprise
    config_entreprise = ConfigurationEntreprise.get_configuration_active()
    
    # Ajouter au contexte
    base_context['config_entreprise'] = config_entreprise
    
    return base_context 