from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone

from .models import Notification, NotificationPreference
from .serializers import NotificationSerializer
from core.intelligent_views import IntelligentListView
from utilisateurs.mixins import PrivilegeButtonsMixin


class NotificationListView(PrivilegeButtonsMixin, IntelligentListView):
    model = Notification
    template_name = 'base_liste_intelligente.html'
    paginate_by = 20
    page_title = 'Notifications'
    page_icon = 'bell'
    search_fields = ['title', 'message', 'type', 'priority']
    filter_fields = ['type', 'priority', 'is_read']
    default_sort = 'created_at'
    columns = [
        {'field': 'title', 'label': 'Titre', 'sortable': True},
        {'field': 'type', 'label': 'Type', 'sortable': True},
        {'field': 'priority', 'label': 'Priorité', 'sortable': True},
        {'field': 'is_read', 'label': 'Lue', 'sortable': True},
        {'field': 'created_at', 'label': 'Date', 'sortable': True},
    ]
    actions = [
        {'url_name': 'notifications:notification_detail', 'icon': 'eye', 'style': 'outline-primary', 'title': 'Voir'},
    ]
    sort_options = [
        {'value': 'created_at', 'label': 'Date'},
        {'value': 'priority', 'label': 'Priorité'},
    ]

notification_list = NotificationListView.as_view()


@login_required
def notification_detail(request, pk):
    """
    Vue pour afficher le détail d'une notification
    """
    # Vérification des permissions : PRIVILEGE, ADMINISTRATION, CONTROLES peuvent voir les détails
    from core.utils import check_group_permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'CONTROLES', 'CAISSE'], 'view')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('notifications:notification_list')
    
    notification = get_object_or_404(Notification, pk=pk, recipient=request.user)
    
    # Marquer comme lue si ce n'est pas déjà fait
    if not notification.is_read:
        notification.mark_as_read()
    
    context = {
        'notification': notification,
    }
    
    return render(request, 'notifications/notification_detail.html', context)


@login_required
def preferences(request):
    """
    Vue pour gérer les préférences de notification
    """
    try:
        preferences = NotificationPreference.objects.get(user=request.user)
    except NotificationPreference.DoesNotExist:
        preferences = NotificationPreference.objects.create(user=request.user)
    
    if request.method == 'POST':
        # Traitement du formulaire
        email_notifications = request.POST.get('email_notifications') == 'on'
        browser_notifications = request.POST.get('browser_notifications') == 'on'
        sms_notifications = request.POST.get('sms_notifications') == 'on'
        phone_number = request.POST.get('phone_number', '').strip()
        
        # Préférences par type
        payment_due_email = request.POST.get('payment_due_email') == 'on'
        payment_received_email = request.POST.get('payment_received_email') == 'on'
        contract_expiring_email = request.POST.get('contract_expiring_email') == 'on'
        maintenance_email = request.POST.get('maintenance_email') == 'on'
        system_alerts_email = request.POST.get('system_alerts_email') == 'on'
        
        # Digest
        daily_digest = request.POST.get('daily_digest') == 'on'
        weekly_digest = request.POST.get('weekly_digest') == 'on'
        
        # Validation du numéro de téléphone
        if sms_notifications and not phone_number:
            messages.error(request, 'Le numéro de téléphone est requis pour activer les notifications SMS.')
        else:
            # Mise à jour
            preferences.email_notifications = email_notifications
            preferences.browser_notifications = browser_notifications
            preferences.sms_notifications = sms_notifications
            preferences.phone_number = phone_number
            preferences.payment_due_email = payment_due_email
            preferences.payment_received_email = payment_received_email
            preferences.contract_expiring_email = contract_expiring_email
            preferences.maintenance_email = maintenance_email
            preferences.system_alerts_email = system_alerts_email
            preferences.daily_digest = daily_digest
            preferences.weekly_digest = weekly_digest
            preferences.save()
            
            messages.success(request, 'Préférences de notification mises à jour avec succès.')
            return redirect('notifications:preferences')
    
    context = {
        'preferences': preferences,
        'notification_types': Notification.TYPE_CHOICES,
    }
    
    return render(request, 'notifications/preferences.html', context)


@login_required
def mark_as_read(request, pk):
    """
    Vue AJAX pour marquer une notification comme lue
    """
    if request.method == 'POST':
        try:
            notification = Notification.objects.get(pk=pk, recipient=request.user)
            notification.mark_as_read()
            return JsonResponse({'status': 'success'})
        except Notification.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Notification non trouvée'}, status=404)
    
    return JsonResponse({'status': 'error', 'message': 'Méthode non autorisée'}, status=405)


@login_required
def mark_all_as_read(request):
    """
    Vue AJAX pour marquer toutes les notifications comme lues
    """
    if request.method == 'POST':
        count = Notification.objects.filter(
            recipient=request.user, 
            is_read=False
        ).update(is_read=True, read_at=timezone.now())
        
        return JsonResponse({
            'status': 'success', 
            'message': f'{count} notification(s) marquée(s) comme lue(s)'
        })
    
    return JsonResponse({'status': 'error', 'message': 'Méthode non autorisée'}, status=405)


@login_required
def notification_count(request):
    """
    Vue AJAX pour obtenir le nombre de notifications non lues
    """
    if request.method == 'GET':
        unread_count = Notification.get_unread_count(request.user)
        return JsonResponse({'unread_count': unread_count})
    
    return JsonResponse({'status': 'error', 'message': 'Méthode non autorisée'}, status=405)


@login_required
def sms_configuration(request):
    """
    Vue pour configurer les paramètres SMS
    """
    try:
        preferences = NotificationPreference.objects.get(user=request.user)
    except NotificationPreference.DoesNotExist:
        preferences = NotificationPreference.objects.create(user=request.user)
    
    if request.method == 'POST':
        # Traitement du formulaire SMS
        sms_notifications = request.POST.get('sms_notifications') == 'on'
        phone_number = request.POST.get('phone_number', '').strip()
        
        # Préférences SMS par type
        payment_overdue_sms = request.POST.get('payment_overdue_sms') == 'on'
        payment_due_sms = request.POST.get('payment_due_sms') == 'on'
        contract_expiring_sms = request.POST.get('contract_expiring_sms') == 'on'
        maintenance_sms = request.POST.get('maintenance_sms') == 'on'
        system_alerts_sms = request.POST.get('system_alerts_sms') == 'on'
        
        # Validation du numéro de téléphone
        if sms_notifications and not phone_number:
            messages.error(request, 'Le numéro de téléphone est requis pour activer les notifications SMS.')
        else:
            # Mise à jour des préférences
            preferences.sms_notifications = sms_notifications
            preferences.phone_number = phone_number
            preferences.payment_overdue_sms = payment_overdue_sms
            preferences.payment_due_sms = payment_due_sms
            preferences.contract_expiring_sms = contract_expiring_sms
            preferences.maintenance_sms = maintenance_sms
            preferences.system_alerts_sms = system_alerts_sms
            preferences.save()
            
            messages.success(request, 'Configuration SMS mise à jour avec succès.')
            return redirect('notifications:sms_configuration')
    
    # Statistiques SMS
    from .models import SMSNotification
    sms_stats = {
        'total_sent': SMSNotification.objects.filter(user=request.user).count(),
        'successful': SMSNotification.objects.filter(user=request.user, status='sent').count(),
        'failed': SMSNotification.objects.filter(user=request.user, status='failed').count(),
        'pending': SMSNotification.objects.filter(user=request.user, status='pending').count(),
    }
    
    context = {
        'preferences': preferences,
        'sms_stats': sms_stats,
    }
    
    return render(request, 'notifications/sms_configuration.html', context)


@login_required
def sms_history(request):
    """
    Vue pour afficher l'historique des SMS
    """
    from .models import SMSNotification
    from django.core.paginator import Paginator
    
    # Récupérer les SMS de l'utilisateur
    sms_list = SMSNotification.objects.filter(user=request.user).order_by('-created_at')
    
    # Filtres
    status = request.GET.get('status')
    notification_type = request.GET.get('type')
    
    if status:
        sms_list = sms_list.filter(status=status)
    if notification_type:
        sms_list = sms_list.filter(notification_type=notification_type)
    
    # Pagination
    paginator = Paginator(sms_list, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistiques
    total_sms = SMSNotification.objects.filter(user=request.user).count()
    successful_sms = SMSNotification.objects.filter(user=request.user, status='sent').count()
    failed_sms = SMSNotification.objects.filter(user=request.user, status='failed').count()
    
    context = {
        'page_obj': page_obj,
        'total_sms': total_sms,
        'successful_sms': successful_sms,
        'failed_sms': failed_sms,
        'status_choices': SMSNotification.STATUS_CHOICES,
        'notification_types': Notification.TYPE_CHOICES,
    }
    
    return render(request, 'notifications/sms_history.html', context)


@login_required
def send_test_sms(request):
    """
    Vue AJAX pour envoyer un SMS de test
    """
    if request.method == 'POST':
        try:
            preferences = NotificationPreference.objects.get(user=request.user)
            
            if not preferences.sms_notifications or not preferences.phone_number:
                return JsonResponse({
                    'status': 'error', 
                    'message': 'Les notifications SMS ne sont pas activées ou le numéro de téléphone n\'est pas configuré.'
                }, status=400)
            
            from .sms_service import SMSService
            sms_service = SMSService()
            
            # Envoyer un SMS de test
            success, message = sms_service.send_sms(
                phone_number=preferences.phone_number,
                message="Test SMS - GESTIMMOB - Ceci est un message de test pour vérifier la configuration SMS.",
                user=request.user,
                notification_type='test'
            )
            
            if success:
                return JsonResponse({
                    'status': 'success',
                    'message': 'SMS de test envoyé avec succès !'
                })
            else:
                return JsonResponse({
                    'status': 'error',
                    'message': f'Erreur lors de l\'envoi du SMS de test : {message}'
                }, status=400)
                
        except NotificationPreference.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'Préférences SMS non trouvées.'
            }, status=404)
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Erreur inattendue : {str(e)}'
            }, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Méthode non autorisée'}, status=405)


@login_required
def send_overdue_notifications(request):
    """
    Vue pour déclencher manuellement l'envoi des notifications de retard de paiement
    """
    if request.method == 'POST':
        try:
            from .sms_service import send_monthly_overdue_notifications
            
            # Envoyer les notifications
            result = send_monthly_overdue_notifications()
            
            if result['success']:
                messages.success(request, f"Notifications envoyées avec succès ! {result['count']} SMS envoyé(s).")
            else:
                messages.error(request, f"Erreur lors de l'envoi des notifications : {result['message']}")
                
        except Exception as e:
            messages.error(request, f"Erreur inattendue : {str(e)}")
    
    return redirect('notifications:sms_configuration') 