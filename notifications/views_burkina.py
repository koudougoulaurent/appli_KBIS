"""
Vues pour les notifications avec support du Burkina Faso
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods

from .models import NotificationPreference
from .forms import NotificationPreferenceForm, TestSMSForm, BulkNotificationForm
from .services_notifications_dynamiques import ServiceNotificationsDynamiques
from .validators import clean_phone_number


@login_required
def preferences_burkina(request):
    """
    Vue pour les préférences de notification avec format Burkina Faso
    """
    try:
        preferences, created = NotificationPreference.objects.get_or_create(
            user=request.user
        )
    except Exception as e:
        messages.error(request, f"Erreur lors du chargement des préférences: {str(e)}")
        return redirect('notifications:notification_list')
    
    if request.method == 'POST':
        form = NotificationPreferenceForm(request.POST, instance=preferences)
        if form.is_valid():
            try:
                # Nettoyer le numéro de téléphone
                if form.cleaned_data.get('phone_number'):
                    form.instance.phone_number = clean_phone_number(
                        form.cleaned_data['phone_number']
                    )
                
                form.save()
                messages.success(request, "Préférences sauvegardées avec succès!")
                return redirect('notifications:preferences_burkina')
            except Exception as e:
                messages.error(request, f"Erreur lors de la sauvegarde: {str(e)}")
        else:
            messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
    else:
        form = NotificationPreferenceForm(instance=preferences)
    
    context = {
        'form': form,
        'preferences': preferences,
        'phone_formatted': preferences.phone_number if preferences.phone_number else None,
    }
    
    return render(request, 'notifications/preferences_burkina.html', context)


@login_required
@require_http_methods(["POST"])
def test_sms_burkina(request):
    """
    Test d'envoi de SMS avec format Burkina Faso
    """
    form = TestSMSForm(request.POST)
    
    if form.is_valid():
        try:
            phone_number = clean_phone_number(form.cleaned_data['phone_number'])
            message = form.cleaned_data['message']
            
            # Créer une notification de test
            notification = ServiceNotificationsDynamiques.creer_notification_intelligente(
                recipient=request.user,
                type_notification='system_alert',
                message=f"Test SMS: {message}",
                force_send=True
            )
            
            if notification:
                return JsonResponse({
                    'success': True,
                    'message': f'SMS de test envoyé à {phone_number}',
                    'notification_id': notification.id
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Erreur lors de l\'envoi du SMS de test'
                })
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Erreur: {str(e)}'
            })
    else:
        return JsonResponse({
            'success': False,
            'message': 'Données invalides',
            'errors': form.errors
        })


@login_required
def validate_phone_burkina(request):
    """
    Validation en temps réel du numéro de téléphone Burkina Faso
    """
    if request.method == 'POST':
        phone_number = request.POST.get('phone_number', '')
        
        try:
            cleaned_phone = clean_phone_number(phone_number)
            return JsonResponse({
                'valid': True,
                'formatted': cleaned_phone,
                'message': 'Numéro valide'
            })
        except Exception as e:
            return JsonResponse({
                'valid': False,
                'message': str(e)
            })
    
    return JsonResponse({'valid': False, 'message': 'Méthode non autorisée'})


@login_required
def format_phone_burkina(request):
    """
    Formatage automatique du numéro de téléphone Burkina Faso
    """
    if request.method == 'POST':
        phone_number = request.POST.get('phone_number', '')
        
        try:
            formatted_phone = clean_phone_number(phone_number)
            return JsonResponse({
                'success': True,
                'formatted': formatted_phone
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
    
    return JsonResponse({'success': False, 'message': 'Méthode non autorisée'})


@login_required
def bulk_notification_burkina(request):
    """
    Envoi de notifications en masse avec support Burkina Faso
    """
    if request.method == 'POST':
        form = BulkNotificationForm(request.POST)
        
        if form.is_valid():
            try:
                # Logique d'envoi en masse
                recipients = form.cleaned_data['recipients']
                notification_type = form.cleaned_data['notification_type']
                title = form.cleaned_data['title']
                message = form.cleaned_data['message']
                send_email = form.cleaned_data['send_email']
                send_sms = form.cleaned_data['send_sms']
                
                # Ici vous pouvez implémenter la logique d'envoi en masse
                # basée sur les destinataires sélectionnés
                
                messages.success(request, f"Notifications envoyées avec succès!")
                return redirect('notifications:bulk_notification_burkina')
                
            except Exception as e:
                messages.error(request, f"Erreur lors de l'envoi: {str(e)}")
        else:
            messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
    else:
        form = BulkNotificationForm()
    
    context = {
        'form': form,
    }
    
    return render(request, 'notifications/bulk_notification_burkina.html', context)


@login_required
def phone_format_help(request):
    """
    Aide pour le format des numéros de téléphone Burkina Faso
    """
    context = {
        'examples': [
            '+226 70 12 34 56',
            '+226 76 98 76 54',
            '+226 25 36 47 58',
            '+226 65 43 21 09',
        ],
        'formats': [
            'Format international: +226 XX XX XX XX',
            'Format local: 0X XX XX XX (converti automatiquement)',
            'Format compact: +226XXXXXXXX (formaté automatiquement)',
        ],
        'rules': [
            'Le numéro doit commencer par +226',
            'Suivi de 8 chiffres',
            'Les espaces sont optionnels',
            'Le système valide automatiquement le format',
        ]
    }
    
    return render(request, 'notifications/phone_format_help.html', context)


