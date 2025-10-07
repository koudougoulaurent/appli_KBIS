from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.views.generic import CreateView, UpdateView, DetailView, ListView
from django.urls import reverse_lazy
from django.utils import timezone
from django.db.models import Q
from datetime import datetime, date

from .forms_intelligents import PaiementFormIntelligent, ChargeDeductibleFormIntelligent, RechercheContratForm
from .models import Paiement, ChargeDeductible
from .services_intelligents import ServiceContexteIntelligent
from contrats.models import Contrat
from proprietes.models import Propriete, Locataire
from core.utils import check_group_permissions, get_context_with_entreprise_config


@login_required
def paiement_intelligent_create(request):
    """
    Vue intelligente pour créer un paiement avec contexte automatique.
    """
    if request.method == 'POST':
        form = PaiementFormIntelligent(request.POST)
        if form.is_valid():
            paiement = form.save(commit=False)
            paiement.utilisateur = request.user
            paiement.date_creation = timezone.now()
            paiement.save()
            
            messages.success(request, f'Paiement créé avec succès pour le contrat {paiement.contrat.numero_contrat}')
            return redirect('paiements:detail', pk=paiement.pk)
    else:
        form = PaiementFormIntelligent()
    
    context = {
        'form': form,
        'title': 'Créer un paiement intelligent',
        'subtitle': 'Sélectionnez un contrat pour voir automatiquement toutes les informations'
    }
    
    context.update(get_context_with_entreprise_config(request))
    return render(request, 'paiements/paiement_intelligent_create.html', context)


@login_required
def paiement_intelligent_update(request, pk):
    """
    Vue intelligente pour modifier un paiement avec contexte automatique.
    """
    paiement = get_object_or_404(Paiement, pk=pk, is_deleted=False)
    
    if request.method == 'POST':
        form = PaiementFormIntelligent(request.POST, instance=paiement)
        if form.is_valid():
            paiement = form.save(commit=False)
            paiement.date_modification = timezone.now()
            paiement.save()
            
            messages.success(request, f'Paiement modifié avec succès')
            return redirect('paiements:detail', pk=paiement.pk)
    else:
        form = PaiementFormIntelligent(instance=paiement)
    
    context = {
        'form': form,
        'paiement': paiement,
        'title': 'Modifier le paiement',
        'subtitle': 'Modifiez les informations du paiement'
    }
    
    context.update(get_context_with_entreprise_config(request))
    return render(request, 'paiements/paiement_intelligent_update.html', context)


@login_required
def charge_intelligente_create(request):
    """
    Vue intelligente pour créer une charge déductible avec contexte automatique.
    """
    if request.method == 'POST':
        form = ChargeDeductibleFormIntelligent(request.POST)
        if form.is_valid():
            charge = form.save(commit=False)
            charge.utilisateur = request.user
            charge.date_creation = timezone.now()
            charge.save()
            
            messages.success(request, f'Charge déductible créée avec succès pour le contrat {charge.contrat.numero_contrat}')
            return redirect('paiements:charge_deductible_list')
    else:
        form = ChargeDeductibleFormIntelligent()
    
    context = {
        'form': form,
        'title': 'Créer une charge déductible intelligente',
        'subtitle': 'Sélectionnez un contrat pour voir automatiquement les informations'
    }
    
    context.update(get_context_with_entreprise_config(request))
    return render(request, 'paiements/charge_intelligente_create.html', context)


@login_required
def charge_intelligente_update(request, pk):
    """
    Vue intelligente pour modifier une charge déductible avec contexte automatique.
    """
    charge = get_object_or_404(ChargeDeductible, pk=pk, is_deleted=False)
    
    if request.method == 'POST':
        form = ChargeDeductibleFormIntelligent(request.POST, instance=charge)
        if form.is_valid():
            charge = form.save(commit=False)
            charge.date_modification = timezone.now()
            charge.save()
            
            messages.success(request, f'Charge déductible modifiée avec succès')
            return redirect('paiements:charge_deductible_list')
    else:
        form = ChargeDeductibleFormIntelligent(instance=charge)
    
    context = {
        'form': form,
        'charge': charge,
        'title': 'Modifier la charge déductible',
        'subtitle': 'Modifiez les informations de la charge'
    }
    
    context.update(get_context_with_entreprise_config(request))
    return render(request, 'paiements/charge_intelligente_update.html', context)


@login_required
def recherche_contrats_intelligente(request):
    """
    Vue de recherche intelligente de contrats.
    """
    if request.method == 'POST':
        form = RechercheContratForm(request.POST)
        if form.is_valid():
            contrats = form.rechercher_contrats()
            messages.success(request, f'{contrats.count()} contrat(s) trouvé(s)')
        else:
            contrats = Contrat.objects.none()
    else:
        form = RechercheContratForm()
        contrats = Contrat.objects.none()
    
    context = {
        'form': form,
        'contrats': contrats,
        'title': 'Recherche intelligente de contrats',
        'subtitle': 'Trouvez rapidement les contrats par différents critères'
    }
    
    context.update(get_context_with_entreprise_config(request))
    return render(request, 'paiements/recherche_contrats_intelligente.html', context)


@login_required
def dashboard_intelligent(request):
    """
    Dashboard intelligent avec suggestions automatiques.
    """
    # Récupération des contrats nécessitant attention
    contrats_attention = []
    
    # Contrats avec échéances proches
    aujourd_hui = timezone.now().date()
    contrats_echeance = Contrat.objects.filter(
        is_deleted=False,
        jour_paiement__gte=aujourd_hui.day - 7,
        jour_paiement__lte=aujourd_hui.day + 7
    ).select_related('propriete', 'locataire')[:10]
    
    for contrat in contrats_echeance:
        contexte = ServiceContexteIntelligent.get_contexte_complet_contrat(contrat.id)
        if contexte['success']:
            contrats_attention.append({
                'contrat': contrat,
                'contexte': contexte['data'],
                'priorite': 'haute' if contexte['data']['alertes'] else 'normale'
            })
    
    # Contrats avec solde négatif
    contrats_solde_negatif = []
    for contrat in Contrat.objects.filter(is_deleted=False).select_related('propriete', 'locataire')[:5]:
        calculs = ServiceContexteIntelligent._get_calculs_automatiques(contrat)
        if calculs['solde_actuel'] < 0:
            contrats_solde_negatif.append({
                'contrat': contrat,
                'calculs': calculs
            })
    
    # Statistiques globales
    total_contrats = Contrat.objects.filter(is_deleted=False).count()
    total_paiements = Paiement.objects.filter(is_deleted=False, statut='valide').count()
    total_charges = ChargeDeductible.objects.filter(is_deleted=False, est_valide=False).count()
    
    context = {
        'contrats_attention': contrats_attention,
        'contrats_solde_negatif': contrats_solde_negatif,
        'statistiques': {
            'total_contrats': total_contrats,
            'total_paiements': total_paiements,
            'total_charges': total_charges,
        },
        'title': 'Dashboard intelligent',
        'subtitle': 'Vue d\'ensemble intelligente de votre portefeuille'
    }
    
    context.update(get_context_with_entreprise_config(request))
    return render(request, 'paiements/dashboard_intelligent.html', context)


@login_required
def contexte_contrat_rapide(request, contrat_id):
    """
    Vue rapide du contexte d'un contrat.
    """
    try:
        contrat = Contrat.objects.select_related(
            'propriete', 'locataire', 'propriete__bailleur'
        ).get(id=contrat_id, is_deleted=False)
        
        # Récupération du contexte complet
        contexte = ServiceContexteIntelligent.get_contexte_complet_contrat(contrat_id)
        
        if not contexte['success']:
            messages.error(request, contexte['error'])
            return redirect('paiements:dashboard')
        
        context = {
            'contrat': contrat,
            'contexte': contexte['data'],
            'title': f'Contexte du contrat {contrat.numero_contrat}',
            'subtitle': 'Toutes les informations contextuelles du contrat'
        }
        
        context.update(get_context_with_entreprise_config(request))
        return render(request, 'paiements/contexte_contrat_rapide.html', context)
        
    except Contrat.DoesNotExist:
        messages.error(request, 'Contrat non trouvé')
        return redirect('paiements:dashboard')


@login_required
def suggestions_paiement_automatiques(request, contrat_id):
    """
    Vue des suggestions automatiques de paiement pour un contrat.
    """
    try:
        contrat = Contrat.objects.get(id=contrat_id, is_deleted=False)
        
        # Récupération des suggestions
        suggestions = ServiceContexteIntelligent.get_suggestions_paiement(contrat_id)
        
        if not suggestions['success']:
            messages.error(request, suggestions['error'])
            return redirect('paiements:dashboard')
        
        # Récupération du contexte pour affichage
        contexte = ServiceContexteIntelligent.get_contexte_complet_contrat(contrat_id)
        
        context = {
            'contrat': contrat,
            'suggestions': suggestions['suggestions'],
            'contexte': contexte['data'] if contexte['success'] else None,
            'title': f'Suggestions de paiement - {contrat.numero_contrat}',
            'subtitle': 'Suggestions intelligentes basées sur le contexte du contrat'
        }
        
        context.update(get_context_with_entreprise_config(request))
        return render(request, 'paiements/suggestions_paiement_automatiques.html', context)
        
    except Contrat.DoesNotExist:
        messages.error(request, 'Contrat non trouvé')
        return redirect('paiements:dashboard')


class PaiementIntelligentCreateView(LoginRequiredMixin, CreateView):
    """
    Vue générique pour créer un paiement intelligent.
    """
    model = Paiement
    form_class = PaiementFormIntelligent
    template_name = 'paiements/paiement_intelligent_create.html'
    success_url = reverse_lazy('paiements:liste')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(get_context_with_entreprise_config(self.request))
        context['title'] = 'Créer un paiement intelligent'
        context['subtitle'] = 'Sélectionnez un contrat pour voir automatiquement toutes les informations'
        return context
    
    def form_valid(self, form):
        form.instance.utilisateur = self.request.user
        form.instance.date_creation = timezone.now()
        messages.success(self.request, 'Paiement créé avec succès')
        return super().form_valid(form)


class ChargeIntelligenteCreateView(LoginRequiredMixin, CreateView):
    """
    Vue générique pour créer une charge déductible intelligente.
    """
    model = ChargeDeductible
    form_class = ChargeDeductibleFormIntelligent
    template_name = 'paiements/charge_intelligente_create.html'
    success_url = reverse_lazy('paiements:charge_deductible_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(get_context_with_entreprise_config(self.request))
        context['title'] = 'Créer une charge déductible intelligente'
        context['subtitle'] = 'Sélectionnez un contrat pour voir automatiquement les informations'
        return context
    
    def form_valid(self, form):
        form.instance.utilisateur = self.request.user
        form.instance.date_creation = timezone.now()
        messages.success(self.request, 'Charge déductible créée avec succès')
        return super().form_valid(form)
