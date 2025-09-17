from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
import json

from .models import PlanPaiementPartiel, EchelonPaiement, PaiementPartiel
from .forms import PlanPaiementPartielForm, PaiementForm


@login_required
@require_http_methods(["GET"])
def get_plan_details(request, plan_id):
    """Récupérer les détails d'un plan pour AJAX"""
    try:
        plan = get_object_or_404(PlanPaiementPartiel, id=plan_id, is_deleted=False)
        
        data = {
            'id': str(plan.id),
            'nom_plan': plan.nom_plan,
            'montant_total': float(plan.montant_total),
            'montant_deja_paye': float(plan.montant_deja_paye),
            'montant_restant': float(plan.montant_restant),
            'statut': plan.statut,
            'progression': plan.calculer_progression(),
            'date_debut': plan.date_debut.isoformat() if plan.date_debut else None,
            'date_fin_prevue': plan.date_fin_prevue.isoformat() if plan.date_fin_prevue else None,
            'contrat': {
                'id': plan.contrat.id,
                'locataire': f"{plan.contrat.locataire.nom} {plan.contrat.locataire.prenom}",
                'propriete': plan.contrat.propriete.adresse
            }
        }
        
        return JsonResponse({'success': True, 'data': data})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_http_methods(["POST"])
def create_quick_payment(request):
    """Créer un paiement rapide via AJAX"""
    try:
        data = json.loads(request.body)
        
        plan_id = data.get('plan_id')
        montant = Decimal(str(data.get('montant', 0)))
        date_paiement = data.get('date_paiement')
        mode_paiement = data.get('mode_paiement', 'virement')
        
        if not plan_id or not montant or not date_paiement:
            return JsonResponse({'success': False, 'error': 'Données manquantes'})
        
        plan = get_object_or_404(PlanPaiementPartiel, id=plan_id, is_deleted=False)
        
        with transaction.atomic():
            # Créer le paiement partiel
            paiement = PaiementPartiel.objects.create(
                plan=plan,
                montant=montant,
                date_paiement=date_paiement,
                mode_paiement=mode_paiement,
                motif=f"Paiement rapide - {plan.nom_plan}",
                cree_par=request.user
            )
            
            # Mettre à jour le plan
            plan.montant_deja_paye += montant
            plan.save()
            
            # Vérifier si le plan est terminé
            if plan.montant_deja_paye >= plan.montant_total:
                plan.statut = 'termine'
                plan.date_fin_reelle = timezone.now().date()
                plan.save()
        
        return JsonResponse({
            'success': True, 
            'message': 'Paiement enregistré avec succès',
            'paiement_id': str(paiement.id)
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_http_methods(["POST"])
def bulk_update_plans(request):
    """Mise à jour en lot des plans"""
    try:
        data = json.loads(request.body)
        plan_ids = data.get('plan_ids', [])
        action = data.get('action')
        
        if not plan_ids or not action:
            return JsonResponse({'success': False, 'error': 'Données manquantes'})
        
        plans = PlanPaiementPartiel.objects.filter(
            id__in=plan_ids, 
            is_deleted=False
        )
        
        with transaction.atomic():
            if action == 'activate':
                plans.update(statut='actif')
            elif action == 'suspend':
                plans.update(statut='suspendu')
            elif action == 'delete':
                plans.update(is_deleted=True, supprime_par=request.user)
            else:
                return JsonResponse({'success': False, 'error': 'Action invalide'})
        
        return JsonResponse({
            'success': True, 
            'message': f'{plans.count()} plan(s) mis à jour avec succès'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_http_methods(["GET"])
def get_plans_data(request):
    """Récupérer les données des plans pour les graphiques"""
    try:
        # Statistiques générales
        stats = {
            'total_plans': PlanPaiementPartiel.objects.filter(is_deleted=False).count(),
            'plans_actifs': PlanPaiementPartiel.objects.filter(
                is_deleted=False, statut='actif'
            ).count(),
            'plans_termines': PlanPaiementPartiel.objects.filter(
                is_deleted=False, statut='termine'
            ).count(),
            'montant_total': float(PlanPaiementPartiel.objects.filter(
                is_deleted=False
            ).aggregate(total=Sum('montant_total'))['total'] or 0),
            'montant_paye': float(PlanPaiementPartiel.objects.filter(
                is_deleted=False
            ).aggregate(total=Sum('montant_deja_paye'))['total'] or 0),
        }
        
        # Données pour les graphiques
        chart_data = {
            'monthly_payments': [],  # Paiements par mois
            'status_distribution': [],  # Répartition par statut
            'recent_plans': []  # Plans récents
        }
        
        return JsonResponse({
            'success': True, 
            'stats': stats,
            'chart_data': chart_data
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_http_methods(["POST"])
def calculate_plan_schedule(request):
    """Calculer automatiquement le planning des échéances"""
    try:
        data = json.loads(request.body)
        
        montant_total = Decimal(str(data.get('montant_total', 0)))
        date_debut = data.get('date_debut')
        date_fin = data.get('date_fin')
        type_plan = data.get('type_plan', 'mensuel')  # mensuel, trimestriel, personnalisé
        
        if not montant_total or not date_debut or not date_fin:
            return JsonResponse({'success': False, 'error': 'Données manquantes'})
        
        from datetime import datetime, timedelta
        from dateutil.relativedelta import relativedelta
        
        debut = datetime.strptime(date_debut, '%Y-%m-%d').date()
        fin = datetime.strptime(date_fin, '%Y-%m-%d').date()
        
        # Calculer le nombre d'échéances selon le type
        if type_plan == 'mensuel':
            delta = relativedelta(months=1)
        elif type_plan == 'trimestriel':
            delta = relativedelta(months=3)
        else:
            # Calculer automatiquement
            diff_months = (fin.year - debut.year) * 12 + (fin.month - debut.month)
            if diff_months <= 3:
                delta = relativedelta(months=1)
            elif diff_months <= 6:
                delta = relativedelta(months=2)
            else:
                delta = relativedelta(months=3)
        
        # Générer les échéances
        echeances = []
        current_date = debut
        echeance_num = 1
        montant_restant = montant_total
        
        while current_date <= fin and montant_restant > 0:
            # Calculer le montant de cette échéance
            if echeance_num == 1 or current_date + delta > fin:
                montant_echeance = montant_restant
            else:
                montant_echeance = montant_total / ((fin - debut).days / 30)  # Approximation
            
            echeances.append({
                'numero': echeance_num,
                'date': current_date.isoformat(),
                'montant': float(montant_echeance),
                'statut': 'en_attente'
            })
            
            montant_restant -= montant_echeance
            current_date += delta
            echeance_num += 1
        
        return JsonResponse({
            'success': True,
            'echeances': echeances,
            'total_echeances': len(echeances),
            'montant_par_echeance': float(montant_total / len(echeances)) if echeances else 0
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_http_methods(["GET"])
def search_plans(request):
    """Recherche avancée des plans"""
    try:
        query = request.GET.get('q', '')
        status = request.GET.get('status', '')
        date_filter = request.GET.get('date', '')
        amount_min = request.GET.get('amount_min', '')
        amount_max = request.GET.get('amount_max', '')
        
        queryset = PlanPaiementPartiel.objects.filter(is_deleted=False)
        
        # Filtre par recherche textuelle
        if query:
            queryset = queryset.filter(
                Q(nom_plan__icontains=query) |
                Q(contrat__locataire__nom__icontains=query) |
                Q(contrat__locataire__prenom__icontains=query) |
                Q(numero_plan__icontains=query)
            )
        
        # Filtre par statut
        if status:
            queryset = queryset.filter(statut=status)
        
        # Filtre par montant
        if amount_min:
            queryset = queryset.filter(montant_total__gte=Decimal(amount_min))
        if amount_max:
            queryset = queryset.filter(montant_total__lte=Decimal(amount_max))
        
        # Filtre par date
        if date_filter:
            from datetime import datetime, timedelta
            today = timezone.now().date()
            
            if date_filter == 'today':
                queryset = queryset.filter(date_creation=today)
            elif date_filter == 'week':
                week_ago = today - timedelta(days=7)
                queryset = queryset.filter(date_creation__gte=week_ago)
            elif date_filter == 'month':
                month_ago = today - timedelta(days=30)
                queryset = queryset.filter(date_creation__gte=month_ago)
            elif date_filter == 'year':
                year_ago = today - timedelta(days=365)
                queryset = queryset.filter(date_creation__gte=year_ago)
        
        # Limiter les résultats
        plans = queryset[:50]
        
        results = []
        for plan in plans:
            results.append({
                'id': str(plan.id),
                'nom_plan': plan.nom_plan,
                'numero_plan': plan.numero_plan,
                'montant_total': float(plan.montant_total),
                'montant_deja_paye': float(plan.montant_deja_paye),
                'progression': plan.calculer_progression(),
                'statut': plan.statut,
                'statut_display': plan.get_statut_display(),
                'locataire': f"{plan.contrat.locataire.nom} {plan.contrat.locataire.prenom}",
                'date_creation': plan.date_creation.isoformat()
            })
        
        return JsonResponse({
            'success': True,
            'results': results,
            'total': len(results)
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
