"""
Vues API pour les services de base
"""

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View
from django.db.models import Q, Count, Sum
import json
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Devise
from core.utils import convertir_montant
from paiements.models import Paiement
from proprietes.models import Propriete, Bailleur, Locataire
from contrats.models import Contrat
from utilisateurs.models import Utilisateur, GroupeTravail
from notifications.models import Notification
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.db.models.functions import ExtractHour, ExtractWeekDay
from django.utils import timezone
from datetime import datetime, timedelta
from core.models import AuditLog


@login_required
@require_http_methods(["GET"])
def api_dashboard_data(request):
    """API pour récupérer les données du tableau de bord principal."""
    # Statistiques détaillées
    stats = {
        'utilisateurs': {
            'total': Utilisateur.objects.count(),
            'actifs': Utilisateur.objects.filter(actif=True).count(),
        },
        'paiements': {
            'total': Paiement.objects.count(),
            'valides': Paiement.objects.filter(statut='valide').count(),
            'en_attente': Paiement.objects.filter(statut='en_attente').count(),
            'refuses': Paiement.objects.filter(statut='refuse').count(),
        },

        'proprietes': {
            'total': Propriete.objects.count(),
            'louees': Propriete.objects.filter(disponible=False).count(),
            'disponibles': Propriete.objects.filter(disponible=True).count(),
        },
        'contrats': {
            'total': Contrat.objects.count(),
            'actifs': Contrat.objects.filter(est_actif=True, est_resilie=False).count(),
            'expires': Contrat.objects.filter(est_resilie=True).count(),
        }
    }
    
    # Graphiques et tendances
    tendances = {
        'paiements_mois': Paiement.objects.filter(
            date_creation__month=timezone.now().month
        ).count(),
    }
    
    devise_active = getattr(request, 'devise_active', None)
            devise_base = Devise.objects.get(code='F CFA')
    
    data = {
        'stats': stats,
        'tendances': tendances,
    }
    
    return JsonResponse(data)


@login_required
@require_http_methods(["GET"])
def api_groupe_dashboard_data(request, groupe_nom):
    """API pour récupérer les données du tableau de bord d'un groupe."""
    utilisateur = request.user
    
    # Vérifier que l'utilisateur appartient au bon groupe
    if not utilisateur.groupe_travail or utilisateur.groupe_travail.nom != groupe_nom:
        return JsonResponse({'error': "Vous n'avez pas accès à ce dashboard."}, status=403)
    
    groupe = utilisateur.groupe_travail
    
    # Statistiques selon le groupe
    stats = {}
    
    if groupe_nom == 'CAISSE':
        # Optimisation : Une seule requête pour toutes les stats
        mois_courant = datetime.now().month
        annee_courante = datetime.now().year
        
        # Requête optimisée pour les statistiques
        stats_paiements = Paiement.objects.filter(
            date_paiement__month=mois_courant,
            date_paiement__year=annee_courante
        ).aggregate(
            total_paiements=Sum('montant'),
            count_paiements=Count('id')
        )
        
        # Stats des retraits supprimées après refactoring
        stats_retraits = {
            'total_retraits': 0
        }
        
        stats_cautions = Paiement.objects.filter(
            type_paiement='depot_garantie',
            statut='valide'
        ).aggregate(
            total_cautions=Sum('montant')
        )
        
        stats_attente = Paiement.objects.filter(statut='en_attente').count()
        
        stats = {
            'paiements_mois': stats_paiements['total_paiements'] or 0,
            'retraits_mois': stats_retraits['total_retraits'] or 0,
            'cautions_cours': stats_cautions['total_cautions'] or 0,
            'paiements_attente': stats_attente,
        }
        
    elif groupe_nom == 'ADMINISTRATION':
        # Optimisation : Requêtes groupées
        stats_proprietes = Propriete.objects.aggregate(
            total=Count('id')
        )
        
        stats_contrats = Contrat.objects.aggregate(
            actifs=Count('id', filter=Q(est_actif=True)),
            renouveler=Count('id', filter=Q(
                date_fin__lte=datetime.now() + timedelta(days=30),
                est_actif=True
            ))
        )
        
        stats_bailleurs = Bailleur.objects.aggregate(
            total=Count('id')
        )
        
        stats = {
            'total_proprietes': stats_proprietes['total'],
            'contrats_actifs': stats_contrats['actifs'],
            'total_bailleurs': stats_bailleurs['total'],
            'contrats_renouveler': stats_contrats['renouveler'],
        }
        
    elif groupe_nom == 'CONTROLES':
        # Optimisation : Requêtes groupées
        stats_controles = Paiement.objects.aggregate(
            a_valider=Count('id', filter=Q(statut='en_attente'))
        )
        
        stats_contrats = Contrat.objects.aggregate(
            a_verifier=Count('id', filter=Q(est_actif=True))
        )
        
        stats = {
            'paiements_a_valider': stats_controles['a_valider'],
            'contrats_a_verifier': stats_contrats['a_verifier'],
            'anomalies': 0,  # À implémenter selon vos besoins
            'rapports_generes': 0,  # À implémenter selon vos besoins
        }
        
    elif groupe_nom == 'PRIVILEGE':
        # Optimisation : Requêtes groupées
        stats_systeme = {
            'proprietes': Propriete.objects.count(),
            'utilisateurs': Utilisateur.objects.count(),
            'contrats': Contrat.objects.count(),
            'paiements': Paiement.objects.count(),
            'groupes': GroupeTravail.objects.count(),
            'notifications': Notification.objects.count(),
            'utilisateurs_actifs': Utilisateur.objects.filter(actif=True).count(),
            'bailleurs': Bailleur.objects.filter(actif=True).count(),
            'locataires': Locataire.objects.filter(statut='actif').count(),
            'contrats_actifs': Contrat.objects.filter(est_actif=True).count(),
        }
        
        stats = {
            'total_proprietes': stats_systeme['proprietes'],
            'total_utilisateurs': stats_systeme['utilisateurs'],
            'total_contrats': stats_systeme['contrats'],
            'total_paiements': stats_systeme['paiements'],
            'total_groupes': stats_systeme['groupes'],
            'total_notifications': stats_systeme['notifications'],
            'utilisateurs_actifs': stats_systeme['utilisateurs_actifs'],
            'total_bailleurs': stats_systeme['bailleurs'],
            'total_locataires': stats_systeme['locataires'],
            'contrats_actifs': stats_systeme['contrats_actifs'],
        }
    
    data = {
        'stats': stats,
    }
    
    return JsonResponse(data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_audit_data_realtime(request):
    """
    API pour récupérer les données d'audit en temps réel
    Permet l'actualisation dynamique des rapports d'audit
    """
    try:
        # Paramètres de filtrage
        search_query = request.GET.get('search', '')
        action_type = request.GET.get('action_type', '')
        user_filter = request.GET.get('user', '')
        date_from = request.GET.get('date_from', '')
        date_to = request.GET.get('date_to', '')
        page_size = int(request.GET.get('page_size', 25))
        page = int(request.GET.get('page', 1))
        
        # Construction de la requête de base
        queryset = AuditLog.objects.select_related('user', 'content_type').all()
        
        # Filtres
        if search_query:
            queryset = queryset.filter(
                Q(user__username__icontains=search_query) |
                Q(action__icontains=search_query) |
                Q(object_repr__icontains=search_query) |
                Q(details__icontains=search_query)
            )
        
        if action_type:
            queryset = queryset.filter(action=action_type)
            
        if user_filter:
            queryset = queryset.filter(user__username=user_filter)
            
        if date_from:
            try:
                date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
                queryset = queryset.filter(timestamp__date__gte=date_from_obj.date())
            except ValueError:
                pass
                
        if date_to:
            try:
                date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')
                queryset = queryset.filter(timestamp__date__lte=date_to_obj.date())
            except ValueError:
                pass
        
        # Pagination
        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)
        
        # Statistiques en temps réel
        total_actions = queryset.count()
        actions_par_type = queryset.values('action').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Calcul des pourcentages
        for action in actions_par_type:
            action['percentage'] = round((action['count'] / total_actions) * 100, 1) if total_actions > 0 else 0
        
        # Actions par utilisateur
        actions_par_utilisateur = queryset.values('user__username').annotate(
            count=Count('id')
        ).filter(user__username__isnull=False).order_by('-count')[:10]
        
        # Actions par heure de la journée
        actions_par_heure = queryset.annotate(
            heure=ExtractHour('timestamp')
        ).values('heure').annotate(
            count=Count('id')
        ).order_by('heure')
        
        # Actions par jour de la semaine
        actions_par_jour = queryset.annotate(
            jour=ExtractWeekDay('timestamp')
        ).values('jour').annotate(
            count=Count('id')
        ).order_by('jour')
        
        # Actions critiques récentes
        actions_critiques = queryset.filter(
            action__in=['delete', 'update']
        ).select_related('user', 'content_type').order_by('-timestamp')[:5]
        
        # Utilisateurs actifs aujourd'hui
        utilisateurs_actifs_aujourd_hui = queryset.filter(
            timestamp__date=timezone.now().date()
        ).values('user__username').annotate(
            count=Count('id')
        ).filter(user__username__isnull=False).order_by('-count')[:5]
        
        # Données des logs paginés
        logs_data = []
        for log in page_obj.object_list:
            logs_data.append({
                'id': log.id,
                'timestamp': log.timestamp.isoformat(),
                'user': log.user.username if log.user else 'Système',
                'action': log.get_action_display(),
                'action_code': log.action,
                'content_type': log.content_type.model if log.content_type else '-',
                'object_id': log.object_id,
                'object_repr': log.object_repr,
                'details': log.details,
                'ip_address': log.ip_address,
                'user_agent': log.user_agent,
                'get_absolute_url': log.get_absolute_url() if hasattr(log, 'get_absolute_url') else None,
            })
        
        # Statistiques globales
        stats_audit = {
            'total_actions': total_actions,
            'actions_aujourd_hui': queryset.filter(timestamp__date=timezone.now().date()).count(),
            'actions_cette_semaine': queryset.filter(
                timestamp__gte=timezone.now() - timedelta(days=7)
            ).count(),
            'actions_ce_mois': queryset.filter(
                timestamp__gte=timezone.now() - timedelta(days=30)
            ).count(),
            'utilisateurs_uniques': queryset.values('user').distinct().count(),
        }
        
        response_data = {
            'success': True,
            'data': {
                'logs': logs_data,
                'stats': stats_audit,
                'actions_par_type': list(actions_par_type),
                'actions_par_utilisateur': list(actions_par_utilisateur),
                'actions_par_heure': list(actions_par_heure),
                'actions_par_jour': list(actions_par_jour),
                'actions_critiques': [
                    {
                        'id': log.id,
                        'timestamp': log.timestamp.isoformat(),
                        'user': log.user.username if log.user else 'Système',
                        'action': log.get_action_display(),
                        'content_type': log.content_type.model if log.content_type else '-',
                        'object_repr': log.object_repr,
                    }
                    for log in actions_critiques
                ],
                'utilisateurs_actifs_aujourd_hui': list(utilisateurs_actifs_aujourd_hui),
            },
            'pagination': {
                'current_page': page_obj.number,
                'total_pages': page_obj.paginator.num_pages,
                'has_previous': page_obj.has_previous(),
                'has_next': page_obj.has_next(),
                'total_count': paginator.count,
            },
            'filters': {
                'search': search_query,
                'action_type': action_type,
                'user': user_filter,
                'date_from': date_from,
                'date_to': date_to,
                'page_size': page_size,
            },
            'timestamp': timezone.now().isoformat(),
        }
        
        return Response(response_data)
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e),
            'timestamp': timezone.now().isoformat(),
        }, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_audit_notifications(request):
    """
    API pour récupérer les notifications d'audit en temps réel
    Retourne les nouvelles actions depuis la dernière vérification
    """
    try:
        last_check = request.GET.get('last_check', '')
        
        if last_check:
            try:
                last_check_time = datetime.fromisoformat(last_check.replace('Z', '+00:00'))
                new_actions = AuditLog.objects.filter(
                    timestamp__gt=last_check_time
                ).select_related('user', 'content_type').order_by('-timestamp')[:10]
            except ValueError:
                new_actions = AuditLog.objects.none()
        else:
            # Si pas de timestamp, retourner les actions de la dernière heure
            new_actions = AuditLog.objects.filter(
                timestamp__gte=timezone.now() - timedelta(hours=1)
            ).select_related('user', 'content_type').order_by('-timestamp')[:10]
        
        notifications = []
        for action in new_actions:
            notifications.append({
                'id': action.id,
                'timestamp': action.timestamp.isoformat(),
                'user': action.user.username if action.user else 'Système',
                'action': action.get_action_display(),
                'action_code': action.action,
                'content_type': action.content_type.model if action.content_type else '-',
                'object_repr': action.object_repr,
                'severity': 'high' if action.action in ['delete', 'rejection'] else 'medium' if action.action in ['update', 'validation'] else 'low',
            })
        
        return Response({
            'success': True,
            'notifications': notifications,
            'count': len(notifications),
            'timestamp': timezone.now().isoformat(),
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e),
            'timestamp': timezone.now().isoformat(),
        }, status=500)


@method_decorator(login_required, name='dispatch')
class GenerateUniqueIdView(View):
    """Vue API pour générer des identifiants uniques."""
    
    def post(self, request):
        """Génère un identifiant unique pour un type d'entité."""
        try:
            data = json.loads(request.body)
            entity_type = data.get('entity_type')
            
            if not entity_type:
                return JsonResponse({'error': 'Type d\'entité requis'}, status=400)
            
            if entity_type not in UniqueIdService.get_all_entity_types():
                return JsonResponse({'error': f'Type non supporté: {entity_type}'}, status=400)
            
            # Générer le code
            code = UniqueIdService.generate_code(entity_type)
            
            return JsonResponse({
                'code': code,
                'entity_type': entity_type,
                'description': UniqueIdService.get_entity_description(entity_type)
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_gestion_cautions(request):
    """
    Endpoint API unifié pour la gestion des cautions et avances.
    """
    from contrats.models import Contrat
    from paiements.models import Paiement
    
    # Paramètres de filtrage
    statut_caution = request.GET.get('statut_caution')
    statut_avance = request.GET.get('statut_avance')
    proprietaire = request.GET.get('proprietaire')
    ville = request.GET.get('ville')
    
    # Base queryset pour les contrats
    contrats = Contrat.objects.filter(
        est_actif=True, 
        est_resilie=False
    ).select_related(
        'locataire', 
        'propriete', 
        'propriete__bailleur'
    )
    
    # Filtres
    if statut_caution == 'payee':
        contrats = contrats.filter(caution_payee=True)
    elif statut_caution == 'non_payee':
        contrats = contrats.filter(caution_payee=False, caution_requise=True)
        
    if statut_avance == 'payee':
        contrats = contrats.filter(avance_payee=True)
    elif statut_avance == 'non_payee':
        contrats = contrats.filter(avance_payee=False, avance_requise=True)
    
    if proprietaire:
        contrats = contrats.filter(propriete__bailleur__nom__icontains=proprietaire)
    
    if ville:
        contrats = contrats.filter(propriete__ville__icontains=ville)
    
    # Données des contrats avec cautions et avances
    contrats_data = []
    total_cautions_en_attente = 0
    total_avances_en_attente = 0
    total_cautions_payees = 0
    total_avances_payees = 0
    
    for contrat in contrats:
        # Paiements de caution et avance pour ce contrat
        paiements_caution = Paiement.objects.filter(
            contrat=contrat,
            type_paiement__in=['caution', 'depot_garantie'],
            statut='valide'
        ).aggregate(total=Sum('montant'))['total'] or 0
        
        paiements_avance = Paiement.objects.filter(
            contrat=contrat,
            type_paiement='avance_loyer',
            statut='valide'
        ).aggregate(total=Sum('montant'))['total'] or 0
        
        contrat_data = {
            'id': contrat.id,
            'numero_contrat': contrat.numero_contrat,
            'locataire': {
                'id': contrat.locataire.id,
                'nom': contrat.locataire.nom,
                'prenom': contrat.locataire.prenom,
                'telephone': contrat.locataire.telephone,
                'email': contrat.locataire.email,
            },
            'propriete': {
                'id': contrat.propriete.id,
                'titre': contrat.propriete.titre,
                'adresse': contrat.propriete.adresse,
                'ville': contrat.propriete.ville,
                'code_postal': contrat.propriete.code_postal,
            },
            'bailleur': {
                'id': contrat.propriete.bailleur.id,
                'nom': contrat.propriete.bailleur.nom,
                'prenom': contrat.propriete.bailleur.prenom,
                'telephone': contrat.propriete.bailleur.telephone,
                'email': contrat.propriete.bailleur.email,
            },
            'caution': {
                'requise': contrat.caution_requise,
                'payee': contrat.caution_payee,
                'montant': float(contrat.caution_montant),
                'date_paiement': contrat.date_paiement_caution,
                'paiements_effectues': float(paiements_caution),
            },
            'avance': {
                'requise': contrat.avance_requise,
                'payee': contrat.avance_payee,
                'montant': float(contrat.avance_montant),
                'date_paiement': contrat.date_paiement_avance,
                'paiements_effectues': float(paiements_avance),
            },
            'loyer_mensuel': float(contrat.loyer_mensuel),
            'date_debut': contrat.date_debut,
            'date_fin': contrat.date_fin,
            'statut_contrat': 'actif' if contrat.est_actif else 'inactif',
        }
        
        contrats_data.append(contrat_data)
        
        # Calculer les totaux
        if contrat.caution_requise and not contrat.caution_payee:
            total_cautions_en_attente += contrat.caution_montant
        elif contrat.caution_payee:
            total_cautions_payees += contrat.caution_montant
            
        if contrat.avance_requise and not contrat.avance_payee:
            total_avances_en_attente += contrat.avance_montant
        elif contrat.avance_payee:
            total_avances_payees += contrat.avance_montant
    
    # Statistiques globales
    stats = {
        'total_contrats': len(contrats_data),
        'cautions': {
            'total_requises': contrats.filter(caution_requise=True).count(),
            'total_payees': contrats.filter(caution_payee=True).count(),
            'total_en_attente': contrats.filter(caution_requise=True, caution_payee=False).count(),
            'montant_total_requis': float(contrats.filter(caution_requise=True).aggregate(Sum('caution_montant'))['caution_montant__sum'] or 0),
            'montant_total_paye': float(total_cautions_payees),
            'montant_total_en_attente': float(total_cautions_en_attente),
        },
        'avances': {
            'total_requises': contrats.filter(avance_requise=True).count(),
            'total_payees': contrats.filter(avance_payee=True).count(),
            'total_en_attente': contrats.filter(avance_requise=True, avance_payee=False).count(),
            'montant_total_requis': float(contrats.filter(avance_requise=True).aggregate(Sum('avance_montant'))['avance_montant__sum'] or 0),
            'montant_total_paye': float(total_avances_payees),
            'montant_total_en_attente': float(total_avances_en_attente),
        },
    }
    
    return Response({
        'statistiques': stats,
        'contrats': contrats_data,
        'filtres_appliques': {
            'statut_caution': statut_caution,
            'statut_avance': statut_avance,
            'proprietaire': proprietaire,
            'ville': ville,
        }
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_marquer_caution_payee(request, contrat_id):
    """
    Marquer la caution d'un contrat comme payée.
    """
    try:
        contrat = Contrat.objects.get(id=contrat_id, est_actif=True, est_resilie=False)
    except Contrat.DoesNotExist:
        return Response(
            {'error': 'Contrat non trouvé ou inactif.'},
            status=404
        )
    
    if contrat.caution_payee:
        return Response(
            {'error': 'La caution est déjà marquée comme payée.'},
            status=400
        )
    
    # Marquer la caution comme payée
    contrat.caution_payee = True
    contrat.date_paiement_caution = timezone.now().date()
    contrat.save()
    
    return Response({
        'message': 'Caution marquée comme payée avec succès.',
        'contrat': {
            'id': contrat.id,
            'numero_contrat': contrat.numero_contrat,
            'caution_payee': contrat.caution_payee,
            'date_paiement_caution': contrat.date_paiement_caution,
        }
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_marquer_avance_payee(request, contrat_id):
    """
    Marquer l'avance de loyer d'un contrat comme payée.
    """
    try:
        contrat = Contrat.objects.get(id=contrat_id, est_actif=True, est_resilie=False)
    except Contrat.DoesNotExist:
        return Response(
            {'error': 'Contrat non trouvé ou inactif.'},
            status=404
        )
    
    if contrat.avance_payee:
        return Response(
            {'error': 'L\'avance est déjà marquée comme payée.'},
            status=400
        )
    
    # Marquer l'avance comme payée
    contrat.avance_payee = True
    contrat.date_paiement_avance = timezone.now().date()
    contrat.save()
    
    return Response({
        'message': 'Avance marquée comme payée avec succès.',
        'contrat': {
            'id': contrat.id,
            'numero_contrat': contrat.numero_contrat,
            'avance_payee': contrat.avance_payee,
            'date_paiement_avance': contrat.date_paiement_avance,
        }
    })