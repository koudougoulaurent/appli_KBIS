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

from .forms_intelligents_retraits import RetraitBailleurFormIntelligent, RechercheBailleurForm
from .models import RetraitBailleur
from .services_intelligents_retraits import ServiceContexteIntelligentRetraits
from proprietes.models import Bailleur
from core.utils import check_group_permissions, get_context_with_entreprise_config


@login_required
def accueil_systeme_intelligent(request):
    """
    Page d'accueil du système intelligent des retraits.
    """
    # Récupérer quelques statistiques de base
    stats = {
        'total_bailleurs': Bailleur.objects.filter(actif=True).count(),
        'total_retraits': RetraitBailleur.objects.count(),
    }
    
    context = {
        'stats': stats,
        'title': 'Système Intelligent des Retraits',
        'subtitle': 'Gestion intelligente et automatisée des retraits aux bailleurs'
    }
    
    context.update(get_context_with_entreprise_config(context))
    return render(request, 'paiements/retraits/accueil_systeme_intelligent.html', context)


@login_required
def retrait_intelligent_create(request):
    """
    Vue intelligente pour créer un retrait avec contexte automatique.
    """
    if request.method == 'POST':
        form = RetraitBailleurFormIntelligent(request.POST)
        if form.is_valid():
            retrait = form.save(commit=False)
            retrait.cree_par = request.user
            retrait.date_creation = timezone.now()
            
            # Traitement spécial pour le champ mois_retrait
            mois_retrait = form.cleaned_data.get('mois_retrait')
            if mois_retrait:
                # S'assurer que c'est le premier jour du mois
                if mois_retrait.day != 1:
                    mois_retrait = mois_retrait.replace(day=1)
                retrait.mois_retrait = mois_retrait
            
            retrait.save()
            
            messages.success(request, f'Retrait créé avec succès pour le bailleur {retrait.bailleur.get_nom_complet()}')
            return redirect('paiements:retrait_detail', pk=retrait.pk)
    else:
        form = RetraitBailleurFormIntelligent()
    
    context = {
        'form': form,
        'title': 'Créer un retrait intelligent',
        'subtitle': 'Sélectionnez un bailleur pour voir automatiquement toutes les informations'
    }
    
    context.update(get_context_with_entreprise_config(context))
    return render(request, 'paiements/retraits/retrait_intelligent_create.html', context)


@login_required
def retrait_intelligent_update(request, pk):
    """
    Vue intelligente pour modifier un retrait avec contexte automatique.
    """
    retrait = get_object_or_404(RetraitBailleur, id=pk)
    
    if request.method == 'POST':
        form = RetraitBailleurFormIntelligent(request.POST, instance=retrait)
        if form.is_valid():
            retrait_modifie = form.save(commit=False)
            retrait_modifie.save()
            
            messages.success(request, 'Retrait modifié avec succès')
            return redirect('paiements:retrait_detail', pk=retrait.pk)
    else:
        form = RetraitBailleurFormIntelligent(instance=retrait)
    
    context = {
        'form': form,
        'retrait': retrait,
        'title': f'Modifier le retrait #{retrait.id}',
        'subtitle': 'Modifiez les informations du retrait'
    }
    
    context.update(get_context_with_entreprise_config(context))
    return render(request, 'paiements/retraits/retrait_intelligent_update.html', context)


@login_required
def recherche_bailleurs_intelligente(request):
    """
    Vue de recherche intelligente de bailleurs.
    """
    if request.method == 'POST':
        form = RechercheBailleurForm(request.POST)
        if form.is_valid():
            recherche = form.cleaned_data.get('recherche', '')
            statut = form.cleaned_data.get('statut', '')
            type_retrait = form.cleaned_data.get('type_retrait', '')
            
            # Construire la requête de base
            bailleurs = Bailleur.objects.all()
            
            # Appliquer les filtres
            if recherche:
                bailleurs = bailleurs.filter(
                    Q(nom__icontains=recherche) |
                    Q(prenom__icontains=recherche) |
                    Q(code_bailleur__icontains=recherche) |
                    Q(email__icontains=recherche)
                )
            
            if statut:
                if statut == 'actif':
                    bailleurs = bailleurs.filter(actif=True)
                elif statut == 'inactif':
                    bailleurs = bailleurs.filter(actif=False)
            
            # Filtrer par type de retrait si spécifié
            if type_retrait:
                bailleurs = bailleurs.filter(
                    retraits_bailleur__type_retrait=type_retrait
                ).distinct()
            
            # Limiter les résultats
            bailleurs = bailleurs[:20]
            
            context = {
                'form': form,
                'bailleurs': bailleurs,
                'recherche_effectuee': True,
                'title': 'Recherche intelligente de bailleurs',
                'subtitle': 'Trouvez rapidement les bailleurs pour créer des retraits'
            }
        else:
            context = {
                'form': form,
                'title': 'Recherche intelligente de bailleurs',
                'subtitle': 'Trouvez rapidement les bailleurs pour créer des retraits'
            }
    else:
        form = RechercheBailleurForm()
        context = {
            'form': form,
            'title': 'Recherche intelligente de bailleurs',
            'subtitle': 'Trouvez rapidement les bailleurs pour créer des retraits'
        }
    
    context.update(get_context_with_entreprise_config(context))
    return render(request, 'paiements/retraits/recherche_bailleurs_intelligente.html', context)


@login_required
def dashboard_intelligent_retraits(request):
    """
    Dashboard intelligent pour les retraits avec suggestions automatiques.
    """
    # Récupération des bailleurs nécessitant attention
    bailleurs_attention = []
    
    # Bailleurs avec contrats actifs
    bailleurs_actifs = Bailleur.objects.filter(
        actif=True
    ).filter(
        proprietes__is_deleted=False
    ).filter(
        proprietes__contrats__is_deleted=False
    ).distinct()[:10]
    
    for bailleur in bailleurs_actifs:
        contexte = ServiceContexteIntelligentRetraits.get_contexte_complet_bailleur(bailleur.id)
        if contexte['success']:
            bailleurs_attention.append({
                'bailleur': bailleur,
                'contexte': contexte['data'],
                'priorite': 'haute' if contexte['data']['alertes'] else 'normale'
            })
    
    # Bailleurs avec retraits en attente
    bailleurs_retraits_attente = []
    for bailleur in Bailleur.objects.filter(
        actif=True,
        retraits_bailleur__statut='en_attente'
    ).distinct()[:5]:
        calculs = ServiceContexteIntelligentRetraits._get_calculs_automatiques(bailleur)
        if calculs['peut_creer_retrait']:
            bailleurs_retraits_attente.append({
                'bailleur': bailleur,
                'calculs': calculs
            })
    
    # Statistiques globales
    total_bailleurs = Bailleur.objects.filter(actif=True).count()
    total_retraits = RetraitBailleur.objects.filter(is_deleted=False).count()
    total_retraits_en_attente = RetraitBailleur.objects.filter(
        is_deleted=False, 
        statut='en_attente'
    ).count()
    
    context = {
        'bailleurs_attention': bailleurs_attention,
        'bailleurs_retraits_attente': bailleurs_retraits_attente,
        'stats': {
            'total_bailleurs': total_bailleurs,
            'total_retraits': total_retraits,
            'total_retraits_en_attente': total_retraits_en_attente,
        },
        'title': 'Dashboard intelligent des retraits',
        'subtitle': 'Vue d\'ensemble et suggestions automatiques'
    }
    
    context.update(get_context_with_entreprise_config(context))
    return render(request, 'paiements/retraits/dashboard_intelligent_retraits.html', context)


@login_required
def contexte_bailleur_rapide(request, bailleur_id):
    """
    Vue rapide du contexte d'un bailleur.
    """
    try:
        bailleur = Bailleur.objects.get(id=bailleur_id)
        contexte = ServiceContexteIntelligentRetraits.get_contexte_complet_bailleur(bailleur_id)
        
        if not contexte['success']:
            messages.error(request, f'Erreur: {contexte["error"]}')
            return redirect('paiements:retraits_liste')
        
        context = {
            'bailleur': bailleur,
            'contexte': contexte['data'],
            'title': f'Contexte rapide - {bailleur.get_nom_complet()}',
            'subtitle': 'Informations essentielles pour la création de retrait'
        }
        
        context.update(get_context_with_entreprise_config(context))
        return render(request, 'paiements/retraits/contexte_bailleur_rapide.html', context)
        
    except Exception as e:
        messages.error(request, f'Bailleur non trouvé: {str(e)}')
        return redirect('paiements:retraits_liste')


@login_required
def suggestions_retrait_automatiques(request, bailleur_id):
    """
    Vue détaillée des suggestions de retrait pour un bailleur.
    """
    try:
        bailleur = Bailleur.objects.get(id=bailleur_id)
        suggestions = ServiceContexteIntelligentRetraits.get_suggestions_retrait(bailleur_id)
        
        if not suggestions['success']:
            messages.error(request, f'Erreur: {suggestions["error"]}')
            return redirect('paiements:retraits_liste')
        
        context = {
            'bailleur': bailleur,
            'suggestions': suggestions['suggestions'],
            'title': f'Suggestions de retrait - {bailleur.get_nom_complet()}',
            'subtitle': 'Suggestions intelligentes basées sur le contexte'
        }
        
        context.update(get_context_with_entreprise_config(context))
        return render(request, 'paiements/retraits/suggestions_retrait_automatiques.html', context)
        
    except Exception as e:
        messages.error(request, f'Bailleur non trouvé: {str(e)}')
        return redirect('paiements:retraits_liste')


class RetraitIntelligentCreateView(LoginRequiredMixin, CreateView):
    """
    Vue générique pour créer un retrait intelligent.
    """
    model = RetraitBailleur
    form_class = RetraitBailleurFormIntelligent
    template_name = 'paiements/retraits/retrait_intelligent_create.html'
    success_url = reverse_lazy('paiements:retraits_liste')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(get_context_with_entreprise_config(self.request))
        context['title'] = 'Créer un retrait intelligent'
        context['subtitle'] = 'Sélectionnez un bailleur pour voir automatiquement toutes les informations'
        return context
    
    def form_valid(self, form):
        form.instance.cree_par = self.request.user
        form.instance.date_creation = timezone.now()
        
        # Traitement spécial pour le champ mois_retrait
        mois_retrait = form.cleaned_data.get('mois_retrait')
        if mois_retrait:
            # S'assurer que c'est le premier jour du mois
            if mois_retrait.day != 1:
                mois_retrait = mois_retrait.replace(day=1)
            form.instance.mois_retrait = mois_retrait
        
        messages.success(self.request, 'Retrait créé avec succès')
        return super().form_valid(form)


class RetraitIntelligentUpdateView(LoginRequiredMixin, UpdateView):
    """
    Vue générique pour modifier un retrait intelligent.
    """
    model = RetraitBailleur
    form_class = RetraitBailleurFormIntelligent
    template_name = 'paiements/retraits/retrait_intelligent_update.html'
    
    def get_success_url(self):
        return reverse_lazy('paiements:retrait_detail', kwargs={'pk': self.object.pk})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(get_context_with_entreprise_config(self.request))
        context['title'] = f'Modifier le retrait #{self.object.id}'
        context['subtitle'] = 'Modifiez les informations du retrait'
        return context


@login_required
def api_contexte_bailleur(request, bailleur_id):
    """
    API pour récupérer le contexte d'un bailleur (utilisée par JavaScript).
    """
    try:
        contexte = ServiceContexteIntelligentRetraits.get_contexte_complet_bailleur(bailleur_id)
        return JsonResponse(contexte)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
def api_suggestions_retrait(request, bailleur_id):
    """
    API pour récupérer les suggestions de retrait d'un bailleur.
    """
    try:
        suggestions = ServiceContexteIntelligentRetraits.get_suggestions_retrait(bailleur_id)
        return JsonResponse(suggestions)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
