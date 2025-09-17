"""
Vues spécialisées pour le système de paiement partiel
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.conf import settings
from decimal import Decimal
import json
import datetime

from .models_partial_payment import (
    PlanPaiementPartiel, EchelonPaiement, PaiementPartiel, AlertePaiementPartiel
)
from .forms_partial_payment import (
    PlanPaiementPartielForm, EchelonPaiementForm, PaiementPartielForm,
    RecherchePaiementPartielForm, GenerationEchelonsForm
)
from contrats.models import Contrat
from paiements.models import Paiement


@login_required
def dashboard_paiements_partiels(request):
    """Dashboard principal des paiements partiels"""
    
    # Statistiques générales
    stats = {
        'total_plans': PlanPaiementPartiel.objects.filter(is_deleted=False).count(),
        'plans_actifs': PlanPaiementPartiel.objects.filter(
            is_deleted=False, statut='actif'
        ).count(),
        'plans_termines': PlanPaiementPartiel.objects.filter(
            is_deleted=False, statut='termine'
        ).count(),
        'montant_total_plans': PlanPaiementPartiel.objects.filter(
            is_deleted=False
        ).aggregate(total=Sum('montant_total'))['total'] or 0,
        'montant_paye_total': PlanPaiementPartiel.objects.filter(
            is_deleted=False
        ).aggregate(total=Sum('montant_deja_paye'))['total'] or 0,
        'echelons_en_retard': EchelonPaiement.objects.filter(
            statut='en_retard'
        ).count(),
        'alertes_actives': AlertePaiementPartiel.objects.filter(
            statut='active'
        ).count(),
    }
    
    # Plans récents
    plans_recents = PlanPaiementPartiel.objects.filter(
        is_deleted=False
    ).select_related('contrat', 'contrat__locataire', 'contrat__propriete').order_by('-date_creation')[:5]
    
    # Échelons en retard
    echelons_retard = EchelonPaiement.objects.filter(
        statut='en_retard'
    ).select_related('plan', 'plan__contrat').order_by('date_echeance')[:10]
    
    # Alertes actives
    alertes_actives = AlertePaiementPartiel.objects.filter(
        statut='active'
    ).select_related('plan', 'plan__contrat').order_by('-date_creation')[:10]
    
    context = {
        'stats': stats,
        'plans_recents': plans_recents,
        'echelons_retard': echelons_retard,
        'alertes_actives': alertes_actives,
    }
    
    return render(request, 'paiements/partial_payment/dashboard.html', context)


@login_required
def liste_plans_paiement(request):
    """Liste des plans de paiement partiel avec filtres"""
    
    # Formulaire de recherche
    form = RecherchePaiementPartielForm(request.GET)
    
    # Base queryset
    queryset = PlanPaiementPartiel.objects.filter(is_deleted=False).select_related(
        'contrat', 'contrat__locataire', 'contrat__propriete', 'cree_par'
    )
    
    # Appliquer les filtres
    if form.is_valid():
        if form.cleaned_data.get('contrat'):
            queryset = queryset.filter(contrat=form.cleaned_data['contrat'])
        
        if form.cleaned_data.get('statut'):
            queryset = queryset.filter(statut=form.cleaned_data['statut'])
        
        if form.cleaned_data.get('date_debut'):
            queryset = queryset.filter(date_creation__date__gte=form.cleaned_data['date_debut'])
        
        if form.cleaned_data.get('date_fin'):
            queryset = queryset.filter(date_creation__date__lte=form.cleaned_data['date_fin'])
        
        if form.cleaned_data.get('montant_min'):
            queryset = queryset.filter(montant_total__gte=form.cleaned_data['montant_min'])
        
        if form.cleaned_data.get('montant_max'):
            queryset = queryset.filter(montant_total__lte=form.cleaned_data['montant_max'])
        
        if form.cleaned_data.get('recherche'):
            search_term = form.cleaned_data['recherche']
            queryset = queryset.filter(
                Q(nom_plan__icontains=search_term) |
                Q(description__icontains=search_term) |
                Q(numero_plan__icontains=search_term) |
                Q(contrat__locataire__nom__icontains=search_term) |
                Q(contrat__locataire__prenom__icontains=search_term)
            )
    
    # Pagination
    paginator = Paginator(queryset, 20)
    page_number = request.GET.get('page')
    plans = paginator.get_page(page_number)
    
    context = {
        'plans': plans,
        'form': form,
    }
    
    return render(request, 'paiements/partial_payment/liste_plans.html', context)


@login_required
def detail_plan_paiement(request, plan_id):
    """Détail d'un plan de paiement partiel"""
    
    plan = get_object_or_404(PlanPaiementPartiel, id=plan_id, is_deleted=False)
    
    # Échelons du plan
    echelons = plan.echelons.all().order_by('numero_echelon')
    
    # Paiements partiels du plan
    paiements = plan.paiements_partiels.filter(is_deleted=False).order_by('-date_paiement')
    
    # Statistiques du plan
    stats = {
        'total_echelons': echelons.count(),
        'echelons_payes': echelons.filter(statut='paye').count(),
        'echelons_en_attente': echelons.filter(statut='en_attente').count(),
        'echelons_en_retard': echelons.filter(statut='en_retard').count(),
        'progression_pourcentage': plan.calculer_progression(),
        'montant_restant': plan.montant_restant,
    }
    
    # Alertes du plan
    alertes = plan.alertes.filter(statut='active').order_by('-date_creation')
    
    context = {
        'plan': plan,
        'echelons': echelons,
        'paiements': paiements,
        'stats': stats,
        'alertes': alertes,
    }
    
    return render(request, 'paiements/partial_payment/detail_plan.html', context)


@login_required
def creer_plan_paiement(request):
    """Créer un nouveau plan de paiement partiel"""
    
    if request.method == 'POST':
        form = PlanPaiementPartielForm(request.POST, user=request.user)
        if form.is_valid():
            plan = form.save(commit=False)
            plan.cree_par = request.user
            plan.save()
            
            messages.success(request, f'Plan de paiement partiel "{plan.nom_plan}" créé avec succès!')
            return redirect('paiements:detail_plan', plan_id=plan.id)
    else:
        form = PlanPaiementPartielForm(user=request.user)
    
    context = {
        'form': form,
        'title': 'Créer un plan de paiement partiel',
    }
    
    return render(request, 'paiements/partial_payment/creer_plan.html', context)


@login_required
def modifier_plan_paiement(request, plan_id):
    """Modifier un plan de paiement partiel"""
    
    plan = get_object_or_404(PlanPaiementPartiel, id=plan_id, is_deleted=False)
    
    if not plan.peut_etre_modifie():
        messages.error(request, 'Ce plan ne peut pas être modifié.')
        return redirect('paiements:detail_plan', plan_id=plan.id)
    
    if request.method == 'POST':
        form = PlanPaiementPartielForm(request.POST, instance=plan, user=request.user)
        if form.is_valid():
            plan = form.save(commit=False)
            plan.modifie_par = request.user
            plan.save()
            
            messages.success(request, f'Plan de paiement partiel "{plan.nom_plan}" modifié avec succès!')
            return redirect('paiements:detail_plan', plan_id=plan.id)
    else:
        form = PlanPaiementPartielForm(instance=plan, user=request.user)
    
    context = {
        'form': form,
        'plan': plan,
        'title': f'Modifier le plan {plan.nom_plan}',
    }
    
    return render(request, 'paiements/partial_payment/modifier_plan.html', context)


@login_required
def generer_echelons(request, plan_id):
    """Générer automatiquement des échelons pour un plan"""
    
    plan = get_object_or_404(PlanPaiementPartiel, id=plan_id, is_deleted=False)
    
    if request.method == 'POST':
        form = GenerationEchelonsForm(request.POST)
        if form.is_valid():
            nombre_echelons = form.cleaned_data['nombre_echelons']
            type_generation = form.cleaned_data['type_generation']
            date_premier_echelon = form.cleaned_data['date_premier_echelon']
            intervalle_jours = form.cleaned_data['intervalle_jours']
            
            # Générer les échelons
            echelons_crees = plan.generer_echelons_automatiques(
                nombre_echelons=nombre_echelons,
                type_generation=type_generation,
                date_premier_echelon=date_premier_echelon,
                intervalle_jours=intervalle_jours,
                utilisateur=request.user
            )
            
            messages.success(request, f'{echelons_crees} échelon(s) généré(s) avec succès!')
            return redirect('paiements:detail_plan', plan_id=plan.id)
    else:
        form = GenerationEchelonsForm(initial={'plan': plan})
    
    context = {
        'form': form,
        'plan': plan,
        'title': f'Générer des échelons pour {plan.nom_plan}',
    }
    
    return render(request, 'paiements/partial_payment/generer_echelons.html', context)


@login_required
def ajouter_echelon(request, plan_id):
    """Ajouter un échelon manuellement à un plan"""
    
    plan = get_object_or_404(PlanPaiementPartiel, id=plan_id, is_deleted=False)
    
    if request.method == 'POST':
        form = EchelonPaiementForm(request.POST, plan=plan)
        if form.is_valid():
            echelon = form.save(commit=False)
            echelon.plan = plan
            echelon.cree_par = request.user
            echelon.save()
            
            messages.success(request, f'Échelon {echelon.numero_echelon} ajouté avec succès!')
            return redirect('paiements:detail_plan', plan_id=plan.id)
    else:
        form = EchelonPaiementForm(plan=plan)
    
    context = {
        'form': form,
        'plan': plan,
        'title': f'Ajouter un échelon à {plan.nom_plan}',
    }
    
    return render(request, 'paiements/partial_payment/ajouter_echelon.html', context)


@login_required
def effectuer_paiement_partiel(request, plan_id):
    """Effectuer un paiement partiel"""
    
    plan = get_object_or_404(PlanPaiementPartiel, id=plan_id, is_deleted=False)
    
    if request.method == 'POST':
        form = PaiementPartielForm(request.POST, user=request.user)
        if form.is_valid():
            paiement_partiel = form.save(commit=False)
            paiement_partiel.plan = plan
            paiement_partiel.cree_par = request.user
            
            # Créer le paiement principal
            paiement_principal = Paiement.objects.create(
                contrat=plan.contrat,
                montant=paiement_partiel.montant,
                date_paiement=paiement_partiel.date_paiement,
                statut='valide',
                est_paiement_partiel=True,
                cree_par=request.user
            )
            
            paiement_partiel.paiement_principal = paiement_principal
            paiement_partiel.save()
            
            # Valider le paiement partiel
            paiement_partiel.valider(request.user)
            
            messages.success(request, f'Paiement partiel de {paiement_partiel.montant} FCFA effectué avec succès!')
            return redirect('paiements:detail_plan', plan_id=plan.id)
    else:
        form = PaiementPartielForm(user=request.user, initial={'plan': plan})
    
    context = {
        'form': form,
        'plan': plan,
        'title': f'Effectuer un paiement partiel - {plan.nom_plan}',
    }
    
    return render(request, 'paiements/partial_payment/effectuer_paiement.html', context)


@login_required
def liste_paiements_partiels(request):
    """Liste des paiements partiels"""
    
    # Formulaire de recherche
    form = RecherchePaiementPartielForm(request.GET)
    
    # Base queryset
    queryset = PaiementPartiel.objects.filter(is_deleted=False).select_related(
        'plan', 'plan__contrat', 'plan__contrat__locataire', 'paiement_principal', 'cree_par'
    )
    
    # Appliquer les filtres
    if form.is_valid():
        if form.cleaned_data.get('plan'):
            queryset = queryset.filter(plan=form.cleaned_data['plan'])
        
        if form.cleaned_data.get('date_debut'):
            queryset = queryset.filter(date_paiement__date__gte=form.cleaned_data['date_debut'])
        
        if form.cleaned_data.get('date_fin'):
            queryset = queryset.filter(date_paiement__date__lte=form.cleaned_data['date_fin'])
        
        if form.cleaned_data.get('montant_min'):
            queryset = queryset.filter(montant__gte=form.cleaned_data['montant_min'])
        
        if form.cleaned_data.get('montant_max'):
            queryset = queryset.filter(montant__lte=form.cleaned_data['montant_max'])
    
    # Pagination
    paginator = Paginator(queryset, 20)
    page_number = request.GET.get('page')
    paiements = paginator.get_page(page_number)
    
    context = {
        'paiements': paiements,
        'form': form,
    }
    
    return render(request, 'paiements/partial_payment/liste_paiements.html', context)


@login_required
def alertes_paiements_partiels(request):
    """Gestion des alertes de paiements partiels"""
    
    # Filtrer les alertes
    statut = request.GET.get('statut', 'active')
    niveau_urgence = request.GET.get('niveau_urgence', '')
    
    queryset = AlertePaiementPartiel.objects.select_related(
        'plan', 'plan__contrat', 'plan__contrat__locataire', 'cree_par'
    )
    
    if statut:
        queryset = queryset.filter(statut=statut)
    
    if niveau_urgence:
        queryset = queryset.filter(niveau_urgence=niveau_urgence)
    
    # Pagination
    paginator = Paginator(queryset, 20)
    page_number = request.GET.get('page')
    alertes = paginator.get_page(page_number)
    
    context = {
        'alertes': alertes,
        'statut': statut,
        'niveau_urgence': niveau_urgence,
    }
    
    return render(request, 'paiements/partial_payment/alertes.html', context)


@login_required
@require_http_methods(["POST"])
def traiter_alerte(request, alerte_id):
    """Traiter une alerte"""
    
    alerte = get_object_or_404(AlertePaiementPartiel, id=alerte_id)
    alerte.traiter(request.user)
    
    messages.success(request, 'Alerte traitée avec succès!')
    return redirect('paiements:alertes_partiels')


@login_required
def rapport_paiements_partiels(request):
    """Rapport des paiements partiels"""
    
    # Période par défaut (derniers 30 jours)
    date_fin = timezone.now().date()
    date_debut = date_fin - datetime.timedelta(days=30)
    
    # Filtres
    if request.GET.get('date_debut'):
        date_debut = datetime.datetime.strptime(request.GET['date_debut'], '%Y-%m-%d').date()
    
    if request.GET.get('date_fin'):
        date_fin = datetime.datetime.strptime(request.GET['date_fin'], '%Y-%m-%d').date()
    
    # Données du rapport
    plans = PlanPaiementPartiel.objects.filter(
        is_deleted=False,
        date_creation__date__range=[date_debut, date_fin]
    ).select_related('contrat', 'contrat__locataire')
    
    paiements = PaiementPartiel.objects.filter(
        is_deleted=False,
        date_paiement__date__range=[date_debut, date_fin]
    ).select_related('plan', 'plan__contrat')
    
    # Statistiques
    stats = {
        'total_plans': plans.count(),
        'total_paiements': paiements.count(),
        'montant_total_paye': paiements.aggregate(total=Sum('montant'))['total'] or 0,
        'plans_termines': plans.filter(statut='termine').count(),
        'taux_reussite': 0,
    }
    
    if stats['total_plans'] > 0:
        stats['taux_reussite'] = (stats['plans_termines'] / stats['total_plans']) * 100
    
    context = {
        'plans': plans,
        'paiements': paiements,
        'stats': stats,
        'date_debut': date_debut,
        'date_fin': date_fin,
    }
    
    return render(request, 'paiements/partial_payment/rapport.html', context)


# API Views pour AJAX
@login_required
def api_echelons_plan(request, plan_id):
    """API pour récupérer les échelons d'un plan"""
    
    plan = get_object_or_404(PlanPaiementPartiel, id=plan_id, is_deleted=False)
    echelons = plan.echelons.all().order_by('numero_echelon')
    
    data = []
    for echelon in echelons:
        data.append({
            'id': str(echelon.id),
            'numero': echelon.numero_echelon,
            'montant': float(echelon.montant),
            'date_echeance': echelon.date_echeance.isoformat(),
            'statut': echelon.statut,
            'est_en_retard': echelon.est_en_retard(),
        })
    
    return JsonResponse({'echelons': data})


@login_required
def api_statistiques_plan(request, plan_id):
    """API pour récupérer les statistiques d'un plan"""
    
    plan = get_object_or_404(PlanPaiementPartiel, id=plan_id, is_deleted=False)
    
    stats = {
        'montant_total': float(plan.montant_total),
        'montant_paye': float(plan.montant_deja_paye),
        'montant_restant': float(plan.montant_restant),
        'progression_pourcentage': plan.calculer_progression(),
        'statut': plan.statut,
        'est_termine': plan.est_termine(),
    }
    
    return JsonResponse(stats)
