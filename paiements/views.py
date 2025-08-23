from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods, require_POST
from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView
from django.urls import reverse_lazy
from django.db.models import Q, Sum, Count, F, Case, When, DecimalField
from django.db.models.functions import Coalesce
from django.utils import timezone
from datetime import datetime, timedelta
from django.core.paginator import Paginator
from django.contrib.contenttypes.models import ContentType
from django.template.loader import render_to_string
from django.conf import settings
from decimal import Decimal
import json
import os

from .models import Paiement, ChargeDeductible, QuittancePaiement
from .forms import PaiementForm, ChargeDeductibleForm, RetraitBailleurForm
from contrats.models import Contrat
from proprietes.models import Propriete, Locataire, Bailleur
from core.models import AuditLog, ConfigurationEntreprise
from core.utils import check_group_permissions, get_context_with_entreprise_config
from django.views.generic import ListView
from .models import TableauBordFinancier
from .forms import TableauBordFinancierForm
from .models import RetraitBailleur
from .models import RecapMensuel


@login_required
def paiements_dashboard(request):
    """
    Dashboard principal des paiements avec vue d'ensemble et accès contextuel aux listes
    """
    # Statistiques générales
    total_paiements = Paiement.objects.filter(is_deleted=False).count()
    paiements_valides = Paiement.objects.filter(is_deleted=False, statut='valide').count()
    paiements_en_attente = Paiement.objects.filter(is_deleted=False, statut='en_attente').count()
    paiements_refuses = Paiement.objects.filter(is_deleted=False, statut='refuse').count()
    
    # Montants
    montant_total = Paiement.objects.filter(
        is_deleted=False, 
        statut='valide'
    ).aggregate(total=Sum('montant'))['total'] or 0
    
    montant_mois_courant = Paiement.objects.filter(
        is_deleted=False,
        statut='valide',
        date_paiement__month=timezone.now().month,
        date_paiement__year=timezone.now().year
    ).aggregate(total=Sum('montant'))['total'] or 0
    
    # Top propriétés par revenus
    top_proprietes_revenus = Paiement.objects.filter(
        is_deleted=False,
        statut='valide'
    ).values(
        'contrat__propriete__titre', 
        'contrat__propriete__ville'
    ).annotate(
        total=Sum('montant')
    ).order_by('-total')[:5]
    
    # Paiements récents
    paiements_recents = Paiement.objects.filter(
        is_deleted=False
    ).select_related('contrat__propriete', 'contrat__locataire').order_by('-date_paiement')[:5]
    
    # Paiements nécessitant attention
    paiements_attention = Paiement.objects.filter(
        is_deleted=False
    ).filter(
        Q(statut='en_attente') | 
        Q(statut='refuse') |
        Q(date_paiement__lt=timezone.now().date() - timedelta(days=30))
    ).select_related('contrat__propriete', 'contrat__locataire')[:5]
    
    # Statistiques par mois (6 derniers mois)
    mois_stats = []
    for i in range(6):
        date = timezone.now() - timedelta(days=30*i)
        mois = date.month
        annee = date.year
        
        total_mois = Paiement.objects.filter(
            is_deleted=False,
            statut='valide',
            date_paiement__month=mois,
            date_paiement__year=annee
        ).aggregate(total=Sum('montant'))['total'] or 0
        
        mois_stats.append({
            'mois': date.strftime('%B %Y'),
            'total': total_mois
        })
    
    mois_stats.reverse()
    
    context = {
        'total_paiements': total_paiements,
        'paiements_valides': paiements_valides,
        'paiements_en_attente': paiements_en_attente,
        'paiements_refuses': paiements_refuses,
        'montant_total': montant_total,
        'montant_mois_courant': montant_mois_courant,
        'top_proprietes_revenus': top_proprietes_revenus,
        'paiements_recents': paiements_recents,
        'paiements_attention': paiements_attention,
        'mois_stats': mois_stats,
    }
    
    return render(request, 'paiements/dashboard.html', context)


class PaiementListView(LoginRequiredMixin, ListView):
    model = Paiement
    template_name = 'paiements/paiement_list.html'
    context_object_name = 'paiements'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.select_related(
            'contrat__locataire',
            'contrat__propriete',
            'contrat__propriete__bailleur'
        ).order_by('-date_creation')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Statistiques pour le contexte
        context['total_paiements'] = Paiement.objects.count()
        context['paiements_valides'] = Paiement.objects.filter(statut='valide').count()
        context['paiements_en_attente'] = Paiement.objects.filter(statut='en_attente').count()
        context['paiements_refuses'] = Paiement.objects.filter(statut='refuse').count()
        
        # Montant total
        context['montant_total'] = Paiement.objects.aggregate(
            total=Sum('montant')
        )['total'] or 0
        
        # Statistiques par type
        context['stats_types'] = Paiement.objects.values('type_paiement').annotate(
            count=Count('id'),
            total=Sum('montant')
        ).order_by('-count')
        
        return context


paiement_list = PaiementListView.as_view()


class PaiementDetailView(LoginRequiredMixin, DetailView):
    model = Paiement
    template_name = 'paiements/paiement_detail.html'
    context_object_name = 'paiement'
    
    def get_object(self):
        return get_object_or_404(
            Paiement.objects.select_related(
                'contrat__locataire',
                'contrat__propriete',
                'contrat__propriete__bailleur'
            ),
            pk=self.kwargs['pk']
        )


paiement_detail = PaiementDetailView.as_view()


@login_required
def ajouter_paiement(request):
    """Ajouter un nouveau paiement."""
    # Vérification des permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE'], 'add')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:paiement_list')
    
    if request.method == 'POST':
        form = PaiementForm(request.POST)
        if form.is_valid():
            paiement = form.save(commit=False)
            paiement.save()
            
            # Log d'audit
            AuditLog.objects.create(
                content_type=ContentType.objects.get_for_model(Paiement),
                object_id=paiement.pk,
                action='CREATE',
                old_data=None,
                new_data={f.name: getattr(paiement, f.name) for f in paiement._meta.fields},
                user=request.user,
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            messages.success(request, 'Paiement ajouté avec succès!')
            return redirect('paiements:paiement_detail', pk=paiement.pk)
    else:
        form = PaiementForm()
    
    context = {
        'form': form,
        'title': 'Ajouter un paiement',
    }
    
    return render(request, 'paiements/paiement_form.html', context)


@login_required
def modifier_paiement(request, pk):
    """Modifier un paiement existant."""
    paiement = get_object_or_404(Paiement, pk=pk)
    
    # Vérification des permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE'], 'modify')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:paiement_detail', pk=pk)
    
    old_data = {f.name: getattr(paiement, f.name) for f in paiement._meta.fields}
    
    if request.method == 'POST':
        form = PaiementForm(request.POST, instance=paiement)
        if form.is_valid():
            form.save()
            
            # Log d'audit
            new_data = {f.name: getattr(paiement, f.name) for f in paiement._meta.fields}
            AuditLog.objects.create(
                content_type=ContentType.objects.get_for_model(Paiement),
                object_id=paiement.pk,
                action='UPDATE',
                old_data=old_data,
                new_data=new_data,
                user=request.user,
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            messages.success(request, 'Paiement modifié avec succès!')
            return redirect('paiements:paiement_detail', pk=pk)
    else:
        form = PaiementForm(instance=paiement)
    
    context = {
        'form': form,
        'paiement': paiement,
        'title': 'Modifier le paiement',
    }
    
    return render(request, 'paiements/paiement_form.html', context)


@login_required
@require_POST
def supprimer_paiement(request, pk):
    """Supprimer un paiement (suppression logique)."""
    paiement = get_object_or_404(Paiement, pk=pk)
    
    # Vérification des permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE'], 'delete')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:paiement_detail', pk=pk)
    
    # Suppression logique
    old_data = {f.name: getattr(paiement, f.name) for f in paiement._meta.fields}
    paiement.is_deleted = True
    paiement.deleted_at = timezone.now()
    paiement.deleted_by = request.user
    paiement.save()
    
    # Log d'audit
    AuditLog.objects.create(
        content_type=ContentType.objects.get_for_model(Paiement),
        object_id=paiement.pk,
        action='DELETE',
        old_data=old_data,
        new_data=None,
        user=request.user,
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )
    
    messages.success(request, 'Paiement supprimé avec succès (suppression logique).')
    return redirect('paiements:paiement_list')


@login_required
@require_POST
def valider_paiement(request, pk):
    """Valider un paiement."""
    paiement = get_object_or_404(Paiement, pk=pk)
    
    # Vérification des permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE'], 'modify')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:paiement_detail', pk=pk)
    
    old_data = {f.name: getattr(paiement, f.name) for f in paiement._meta.fields}
    paiement.statut = 'valide'
    paiement.date_validation = timezone.now()
    paiement.validé_par = request.user
    paiement.save()
    
    # Log d'audit
    new_data = {f.name: getattr(paiement, f.name) for f in paiement._meta.fields}
    AuditLog.objects.create(
        content_type=ContentType.objects.get_for_model(Paiement),
        object_id=paiement.pk,
        action='UPDATE',
        old_data=old_data,
        new_data=new_data,
        user=request.user,
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )
    
    messages.success(request, 'Paiement validé avec succès.')
    return redirect('paiements:paiement_detail', pk=pk)


# Vues pour les charges déductibles
class ChargeDeductibleListView(LoginRequiredMixin, ListView):
    model = ChargeDeductible
    template_name = 'paiements/charge_deductible_list.html'
    context_object_name = 'charges'
    paginate_by = 20


charge_deductible_list = ChargeDeductibleListView.as_view()


@login_required
def ajouter_charge_deductible(request):
    """Ajouter une nouvelle charge déductible."""
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION'], 'add')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:charge_deductible_list')
    
    if request.method == 'POST':
        form = ChargeDeductibleForm(request.POST)
        if form.is_valid():
            charge = form.save()
            messages.success(request, 'Charge déductible ajoutée avec succès!')
            return redirect('paiements:charge_deductible_list')
    else:
        form = ChargeDeductibleForm()
    
    context = {
        'form': form,
        'title': 'Ajouter une charge déductible',
    }
    
    return render(request, 'paiements/charge_deductible_form.html', context)


@login_required
def modifier_charge_deductible(request, pk):
    """Modifier une charge déductible."""
    charge = get_object_or_404(ChargeDeductible, pk=pk)
    
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION'], 'modify')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:charge_deductible_list')
    
    if request.method == 'POST':
        form = ChargeDeductibleForm(request.POST, instance=charge)
        if form.is_valid():
            form.save()
            messages.success(request, 'Charge déductible modifiée avec succès!')
            return redirect('paiements:charge_deductible_list')
    else:
        form = ChargeDeductibleForm(instance=charge)
    
    context = {
        'form': form,
        'charge': charge,
        'title': 'Modifier la charge déductible',
    }
    
    return render(request, 'paiements/charge_deductible_form.html', context)


# API Views
@login_required
@require_http_methods(["GET"])
def api_paiements_data(request):
    """API pour récupérer les données des paiements."""
    # Statistiques de base
    stats = {
        'total': Paiement.objects.count(),
        'valides': Paiement.objects.filter(statut='valide').count(),
        'en_attente': Paiement.objects.filter(statut='en_attente').count(),
        'refuses': Paiement.objects.filter(statut='refuse').count(),
        'montant_total': Paiement.objects.aggregate(total=Sum('montant'))['total'] or 0,
    }
    
    # Données par type de paiement
    types_data = list(Paiement.objects.values('type_paiement').annotate(
        count=Count('id'),
        total=Sum('montant')
    ).order_by('-count'))
    
    # Données par mode de paiement
    modes_data = list(Paiement.objects.values('mode_paiement').annotate(
        count=Count('id'),
        total=Sum('montant')
    ).order_by('-count'))
    
    return JsonResponse({
        'stats': stats,
        'types_data': types_data,
        'modes_data': modes_data,
    })


@login_required
def recherche_intelligente_paiements(request):
    """Recherche intelligente des paiements."""
    # Vérification des permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE'], 'view')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('core:dashboard')
    
    query = request.GET.get('q', '')
    paiements = []
    
    if query:
        paiements = Paiement.objects.filter(
            Q(contrat__locataire__nom__icontains=query) |
            Q(contrat__locataire__prenom__icontains=query) |
            Q(contrat__propriete__adresse__icontains=query) |
            Q(type_paiement__icontains=query) |
            Q(statut__icontains=query)
        ).select_related(
            'contrat__locataire',
            'contrat__propriete'
        )[:20]
    
    context = {
        'query': query,
        'paiements': paiements,
        'title': 'Recherche intelligente des paiements'
    }
    
    return render(request, 'paiements/recherche_intelligente.html', context)


# PLACEHOLDER VIEWS pour compatibilité avec les templates existants
# Ces vues sont temporaires et doivent être implémentées complètement

@login_required
def liste_retraits(request):
    """Liste des retraits (placeholder)."""
    messages.warning(request, 'Fonctionnalité des retraits en cours de développement.')
    return redirect('paiements:liste')

@login_required
def ajouter_retrait(request):
    """Ajouter un retrait bailleur."""
    # Vérification des permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE'], 'view')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:liste')
    
    if request.method == 'POST':
        form = RetraitBailleurForm(request.POST)
        if form.is_valid():
            retrait = form.save(commit=False)
            retrait.cree_par = request.user
            
            # Traitement spécial pour le champ mois_retrait
            mois_retrait = form.cleaned_data.get('mois_retrait')
            if mois_retrait:
                # S'assurer que c'est le premier jour du mois
                if mois_retrait.day != 1:
                    mois_retrait = mois_retrait.replace(day=1)
                retrait.mois_retrait = mois_retrait
            
            retrait.save()
            messages.success(request, f'Retrait créé avec succès pour {retrait.bailleur.nom} {retrait.bailleur.prenom}')
            return redirect('paiements:retraits_liste')
        else:
            messages.error(request, 'Veuillez corriger les erreurs dans le formulaire.')
    else:
        form = RetraitBailleurForm()
    
    # Récupérer la liste des bailleurs pour le contexte
    bailleurs = Bailleur.objects.filter(est_actif=True).order_by('nom', 'prenom')
    
    context = get_context_with_entreprise_config({
        'form': form,
        'bailleurs': bailleurs,
        'title': 'Ajouter un Retrait'
    })
    
    return render(request, 'paiements/retrait_ajouter.html', context)

@login_required
def detail_retrait(request, pk):
    """Afficher le détail d'un retrait bailleur."""
    # Vérification des permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE'], 'view')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:dashboard')
    
    # Récupérer le retrait avec toutes les relations nécessaires
    retrait = get_object_or_404(
        RetraitBailleur.objects.select_related(
            'bailleur',
            'cree_par',
            'valide_par',
            'paye_par'
        ).prefetch_related(
            'paiements_concernes__contrat__locataire',
            'charges_deductibles'
        ),
        pk=pk,
        is_deleted=False
    )
    
    context = get_context_with_entreprise_config({
        'retrait': retrait,
        'title': f'Détails du Retrait #{retrait.id}'
    })
    
    return render(request, 'paiements/retraits/retrait_detail.html', context)

@login_required
def modifier_retrait(request, pk):
    """Modifier un retrait bailleur."""
    # Vérification des permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE'], 'change')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:dashboard')
    
    # Récupérer le retrait
    retrait = get_object_or_404(
        RetraitBailleur.objects.select_related('bailleur'),
        pk=pk,
        is_deleted=False
    )
    
    # Vérifier si le retrait peut être modifié
    if not retrait.peut_etre_modifie:
        messages.error(request, 'Ce retrait ne peut plus être modifié.')
        return redirect('paiements:retrait_detail', pk=pk)
    
    if request.method == 'POST':
        form = RetraitBailleurForm(request.POST, instance=retrait)
        if form.is_valid():
            retrait_modifie = form.save(commit=False)
            retrait_modifie.save()
            
            # Mettre à jour les relations many-to-many
            form.save_m2m()
            
            messages.success(request, 'Retrait modifié avec succès.')
            return redirect('paiements:retrait_detail', pk=pk)
    else:
        form = RetraitBailleurForm(instance=retrait)
    
    context = get_context_with_entreprise_config({
        'form': form,
        'retrait': retrait,
        'title': f'Modifier le Retrait #{retrait.id}'
    })
    
    return render(request, 'paiements/retraits/retrait_form.html', context)

@login_required
def retrait_list(request):
    """Liste des retraits (alias pour compatibilité)."""
    return liste_retraits(request)

@login_required
def retrait_ajouter(request):
    """Ajouter un retrait (alias pour compatibilité)."""
    return ajouter_retrait(request)

@login_required
def retrait_detail(request, pk):
    """Détail d'un retrait (alias pour compatibilité)."""
    return detail_retrait(request, pk)

@login_required
def retrait_modifier(request, pk):
    """Modifier un retrait (alias pour compatibilité)."""
    return modifier_retrait(request, pk)


# Fonctions manquantes pour compatibilité avec les templates existants
@login_required
def liste_recus(request):
    """Liste des reçus (placeholder)."""
    messages.warning(request, 'Fonctionnalité des reçus en cours de développement.')
    return redirect('paiements:liste')

@login_required
def liste_recaps_mensuels(request):
    """Liste des récapitulatifs mensuels."""
    # Vérification des permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE'], 'view')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:dashboard')
    
    # Récupérer les récapitulatifs avec filtres
    recaps = RecapMensuel.objects.all().select_related(
        'bailleur', 'cree_par', 'valide_par'
    ).prefetch_related(
        'paiements_concernes', 'charges_deductibles'
    ).order_by('-mois_recap')
    
    # Filtres
    bailleur_id = request.GET.get('bailleur')
    if bailleur_id:
        recaps = recaps.filter(bailleur_id=bailleur_id)
    
    statut = request.GET.get('statut')
    if statut:
        recaps = recaps.filter(statut=statut)
    
    mois = request.GET.get('mois')
    if mois:
        try:
            # Convertir le format YYYY-MM en date
            from datetime import datetime
            date_mois = datetime.strptime(mois, '%Y-%m').date()
            recaps = recaps.filter(mois_recap__year=date_mois.year, mois_recap__month=date_mois.month)
        except ValueError:
            pass
    
    # Pagination
    paginator = Paginator(recaps, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Récupérer tous les bailleurs pour le filtre
    from proprietes.models import Bailleur
    bailleurs = Bailleur.objects.filter(is_deleted=False).order_by('nom', 'prenom')
    
    context = get_context_with_entreprise_config({
        'recaps': page_obj,
        'bailleurs': bailleurs,
        'title': 'Récapitulatifs Mensuels',
        'is_paginated': page_obj.has_other_pages(),
        'page_obj': page_obj,
    })
    
    return render(request, 'paiements/liste_recaps_mensuels.html', context)


@login_required
def creer_recap_mensuel(request):
    """Créer un nouveau récapitulatif mensuel."""
    # Vérification des permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE'], 'add')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:liste_recaps_mensuels')
    
    if request.method == 'POST':
        # Logique de création du récapitulatif
        bailleur_id = request.POST.get('bailleur')
        mois_str = request.POST.get('mois')
        
        if bailleur_id and mois_str:
            try:
                from proprietes.models import Bailleur
                from datetime import datetime
                
                bailleur = Bailleur.objects.get(id=bailleur_id, is_deleted=False)
                mois_recap = datetime.strptime(mois_str, '%Y-%m').date()
                
                # Vérifier si un récapitulatif existe déjà pour ce bailleur et ce mois
                recap_existant = RecapMensuel.objects.filter(
                    bailleur=bailleur,
                    mois_recap__year=mois_recap.year,
                    mois_recap__month=mois_recap.month
                ).first()
                
                if recap_existant:
                    messages.warning(request, f'Un récapitulatif existe déjà pour {bailleur.get_nom_complet()} - {mois_recap.strftime("%B %Y")}')
                    return redirect('paiements:detail_recap_mensuel', recap_id=recap_existant.id)
                
                # Créer le récapitulatif
                recap = RecapMensuel.objects.create(
                    bailleur=bailleur,
                    mois_recap=mois_recap,
                    cree_par=request.user
                )
                
                # Calculer les totaux
                recap.calculer_totaux()
                
                messages.success(request, f'Récapitulatif créé avec succès pour {bailleur.get_nom_complet()} - {mois_recap.strftime("%B %Y")}')
                return redirect('paiements:detail_recap_mensuel', recap_id=recap.id)
                
            except (Bailleur.DoesNotExist, ValueError) as e:
                messages.error(request, f'Erreur lors de la création: {str(e)}')
        else:
            messages.error(request, 'Veuillez sélectionner un bailleur et un mois.')
    
    # Récupérer tous les bailleurs pour le formulaire
    from proprietes.models import Bailleur
    bailleurs = Bailleur.objects.filter(is_deleted=False).order_by('nom', 'prenom')
    
    context = get_context_with_entreprise_config({
        'bailleurs': bailleurs,
        'title': 'Créer un Récapitulatif Mensuel'
    })
    
    return render(request, 'paiements/creer_recap_mensuel.html', context)


@login_required
def detail_recap_mensuel(request, recap_id):
    """Afficher le détail d'un récapitulatif mensuel."""
    # Vérification des permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE'], 'view')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:liste_recaps_mensuels')
    
    try:
        recap = RecapMensuel.objects.select_related(
            'bailleur', 'cree_par', 'valide_par'
        ).prefetch_related(
            'paiements_concernes__contrat__locataire',
            'paiements_concernes__contrat__propriete',
            'charges_deductibles',
            'retraits_associes'
        ).get(id=recap_id)
    except RecapMensuel.DoesNotExist:
        messages.error(request, 'Récapitulatif introuvable.')
        return redirect('paiements:liste_recaps_mensuels')
    
    context = get_context_with_entreprise_config({
        'recap': recap,
        'title': f'Récapitulatif {recap.bailleur.get_nom_complet()} - {recap.mois_recap.strftime("%B %Y")}'
    })
    
    return render(request, 'paiements/detail_recap_mensuel.html', context)


@login_required
def valider_recap_mensuel(request, recap_id):
    """Valider un récapitulatif mensuel."""
    # Vérification des permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE'], 'change')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:detail_recap_mensuel', recap_id=recap_id)
    
    try:
        recap = RecapMensuel.objects.get(id=recap_id)
    except RecapMensuel.DoesNotExist:
        messages.error(request, 'Récapitulatif introuvable.')
        return redirect('paiements:liste_recaps_mensuels')
    
    if recap.statut != 'brouillon':
        messages.warning(request, 'Ce récapitulatif ne peut plus être validé.')
        return redirect('paiements:detail_recap_mensuel', recap_id=recap_id)
    
    # Valider le récapitulatif
    recap.valider_recap(request.user)
    messages.success(request, 'Récapitulatif validé avec succès.')
    
    return redirect('paiements:detail_recap_mensuel', recap_id=recap_id)


@login_required
def marquer_recap_envoye(request, recap_id):
    """Marquer un récapitulatif mensuel comme envoyé au bailleur."""
    # Vérification des permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE'], 'change')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:detail_recap_mensuel', recap_id=recap_id)
    
    try:
        recap = RecapMensuel.objects.get(id=recap_id)
    except RecapMensuel.DoesNotExist:
        messages.error(request, 'Récapitulatif introuvable.')
        return redirect('paiements:liste_recaps_mensuels')
    
    if recap.statut not in ['valide', 'envoye']:
        messages.warning(request, 'Ce récapitulatif doit être validé avant d\'être marqué comme envoyé.')
        return redirect('paiements:detail_recap_mensuel', recap_id=recap_id)
    
    # Marquer comme envoyé
    recap.marquer_envoye(request.user)
    messages.success(request, 'Récapitulatif marqué comme envoyé au bailleur.')
    
    return redirect('paiements:detail_recap_mensuel', recap_id=recap_id)


@login_required
def marquer_recap_paye(request, recap_id):
    """Marquer un récapitulatif mensuel comme payé au bailleur."""
    # Vérification des permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE'], 'change')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:detail_recap_mensuel', recap_id=recap_id)
    
    try:
        recap = RecapMensuel.objects.get(id=recap_id)
    except RecapMensuel.DoesNotExist:
        messages.error(request, 'Récapitulatif introuvable.')
        return redirect('paiements:liste_recaps_mensuels')
    
    if recap.statut not in ['envoye', 'paye']:
        messages.warning(request, 'Ce récapitulatif doit être envoyé avant d\'être marqué comme payé.')
        return redirect('paiements:detail_recap_mensuel', recap_id=recap_id)
    
    # Marquer comme payé
    recap.marquer_paye(request.user)
    messages.success(request, 'Récapitulatif marqué comme payé au bailleur.')
    
    return redirect('paiements:detail_recap_mensuel', recap_id=recap_id)


@login_required
def imprimer_recap_mensuel(request, recap_id):
    """Imprimer un récapitulatif mensuel en PDF."""
    # Vérification des permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE'], 'view')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:detail_recap_mensuel', recap_id=recap_id)
    
    try:
        recap = RecapMensuel.objects.select_related(
            'bailleur', 'cree_par', 'valide_par'
        ).prefetch_related(
            'paiements_concernes__contrat__locataire',
            'paiements_concernes__contrat__propriete',
            'charges_deductibles'
        ).get(id=recap_id)
    except RecapMensuel.DoesNotExist:
        messages.error(request, 'Récapitulatif introuvable.')
        return redirect('paiements:liste_recaps_mensuels')
    
    try:
        # Générer le PDF avec ReportLab
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.lib import colors
        from io import BytesIO
        
        # Créer le buffer pour le PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
        
        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            alignment=1,  # Centré
            textColor=colors.darkblue
        )
        
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=20,
            textColor=colors.darkblue
        )
        
        normal_style = styles['Normal']
        normal_style.fontSize = 10
        
        # Contenu du PDF
        story = []
        
        # Titre principal
        story.append(Paragraph("RÉCAPITULATIF MENSUEL", title_style))
        story.append(Spacer(1, 20))
        
        # Informations du bailleur
        story.append(Paragraph(f"<b>Bailleur:</b> {recap.bailleur.get_nom_complet()}", subtitle_style))
        story.append(Paragraph(f"<b>Mois:</b> {recap.mois_recap.strftime('%B %Y')}", normal_style))
        story.append(Spacer(1, 15))
        
        # Résumé financier
        story.append(Paragraph("RÉSUMÉ FINANCIER", subtitle_style))
        story.append(Spacer(1, 10))
        
        # Tableau des montants
        montants_data = [
            ['Description', 'Montant (XOF)'],
            ['Loyer brut total', f"{recap.total_loyers_bruts:,.0f}"],
            ['Charges déductibles', f"{recap.total_charges_deductibles:,.0f}"],
            ['Loyer net total', f"{recap.total_net_a_payer:,.0f}"],
        ]
        
        montants_table = Table(montants_data, colWidths=[8*cm, 4*cm])
        montants_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(montants_table)
        story.append(Spacer(1, 20))
        
        # Détails des propriétés
        story.append(Paragraph("DÉTAILS DES PROPRIÉTÉS", subtitle_style))
        story.append(Spacer(1, 10))
        
        proprietes_data = [['Propriété', 'Locataire', 'Loyer (XOF)']]
        for paiement in recap.paiements_concernes.all():
            propriete = paiement.contrat.propriete
            locataire = paiement.contrat.locataire
            proprietes_data.append([
                propriete.adresse,
                f"{locataire.prenom} {locataire.nom}",
                f"{paiement.montant:,.0f}"
            ])
        
        proprietes_table = Table(proprietes_data, colWidths=[6*cm, 4*cm, 2*cm])
        proprietes_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
        ]))
        
        story.append(proprietes_table)
        story.append(Spacer(1, 20))
        
        # Charges déductibles
        if recap.charges_deductibles.exists():
            story.append(Paragraph("CHARGES DÉDUCTIBLES", subtitle_style))
            story.append(Spacer(1, 10))
            
            charges_data = [['Description', 'Montant (XOF)']]
            for charge in recap.charges_deductibles.all():
                charges_data.append([charge.description, f"{charge.montant:,.0f}"])
            
            charges_table = Table(charges_data, colWidths=[8*cm, 4*cm])
            charges_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
            ]))
            
            story.append(charges_table)
            story.append(Spacer(1, 20))
        
        # Informations de statut
        story.append(Paragraph("INFORMATIONS DE STATUT", subtitle_style))
        story.append(Paragraph(f"<b>Statut:</b> {recap.get_statut_display()}", normal_style))
        if recap.date_creation:
            story.append(Paragraph(f"<b>Date de création:</b> {recap.date_creation.strftime('%d/%m/%Y')}", normal_style))
        if recap.date_validation:
            story.append(Paragraph(f"<b>Date de validation:</b> {recap.date_validation.strftime('%d/%m/%Y')}", normal_style))
        if recap.date_envoi:
            story.append(Paragraph(f"<b>Date d'envoi:</b> {recap.date_envoi.strftime('%d/%m/%Y')}", normal_style))
        if recap.date_paiement:
            story.append(Paragraph(f"<b>Date de paiement:</b> {recap.date_paiement.strftime('%d/%m/%Y')}", normal_style))
        
        # Générer le PDF
        doc.build(story)
        buffer.seek(0)
        
        # Créer la réponse HTTP
        from django.http import HttpResponse
        response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="recap_mensuel_{recap.bailleur.get_nom_complet()}_{recap.mois_recap.strftime("%Y_%m")}.pdf"'
        
        # Marquer comme imprimé si ce n'est pas déjà fait
        if recap.statut == 'envoye' and not recap.date_impression:
            recap.date_impression = timezone.now()
            recap.save()
        
        return response
        
    except ImportError:
        messages.error(request, 'La génération PDF nécessite ReportLab. Veuillez l\'installer.')
        return redirect('paiements:detail_recap_mensuel', recap_id=recap_id)
    except Exception as e:
        messages.error(request, f'Erreur lors de la génération du PDF: {str(e)}')
        return redirect('paiements:detail_recap_mensuel', recap_id=recap_id)

@login_required
def liste_retraits_bailleur(request):
    """Liste des retraits bailleur (placeholder)."""
    messages.warning(request, 'Fonctionnalité des retraits bailleur en cours de développement.')
    return redirect('paiements:liste')

@login_required
def paiement_caution_avance_create(request):
    """Créer un paiement de caution ou d'avance (placeholder)."""
    messages.warning(request, 'Fonctionnalité des paiements de caution et avance en cours de développement.')
    return redirect('paiements:ajouter')

@login_required
def paiement_caution_avance_list(request):
    """Liste des paiements de caution et avance (placeholder)."""
    messages.warning(request, 'Fonctionnalité des paiements de caution et avance en cours de développement.')
    return redirect('paiements:liste')

@login_required
def tableau_bord_list(request):
    """Liste des tableaux de bord financiers."""
    # Vérification des permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE'], 'view')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:dashboard')
    
    # Récupérer les tableaux de bord de l'utilisateur
    tableaux = TableauBordFinancier.objects.filter(
        cree_par=request.user
    ).select_related('cree_par').prefetch_related('proprietes', 'bailleurs').order_by('-date_creation')
    
    # Pagination
    paginator = Paginator(tableaux, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistiques
    total_tableaux = tableaux.count()
    tableaux_actifs = tableaux.filter(actif=True).count()
    tableaux_alerte = sum(1 for t in tableaux if t.is_alerte_active())
    
    context = get_context_with_entreprise_config({
        'tableaux': page_obj,
        'total_tableaux': total_tableaux,
        'tableaux_actifs': tableaux_actifs,
        'tableaux_alerte': tableaux_alerte,
        'title': 'Tableaux de Bord Financiers'
    })
    
    return render(request, 'paiements/tableaux_bord/tableau_list.html', context)

# Vues pour les quittances de paiement
@login_required
def quittance_detail(request, pk):
    """Afficher le détail d'une quittance de paiement."""
    # Vérification des permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE'], 'view')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:liste')
    
    quittance = get_object_or_404(
        QuittancePaiement.objects.select_related(
            'paiement__contrat__locataire',
            'paiement__contrat__propriete',
            'paiement__contrat__propriete__bailleur'
        ),
        pk=pk
    )
    
    context = get_context_with_entreprise_config({
        'quittance': quittance,
        'title': f'Quittance {quittance.numero_quittance}'
    })
    
    return render(request, 'paiements/quittance_detail.html', context)


@login_required
def quittance_list(request):
    """Liste des quittances de paiement."""
    # Vérification des permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE'], 'view')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:liste')
    
    quittances = QuittancePaiement.objects.select_related(
        'paiement__contrat__locataire',
        'paiement__contrat__propriete',
        'cree_par'
    ).order_by('-date_emission')
    
    # Pagination
    paginator = Paginator(quittances, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistiques
    total_quittances = quittances.count()
    quittances_imprimees = quittances.filter(statut='imprimee').count()
    quittances_envoyees = quittances.filter(statut='envoyee').count()
    
    context = get_context_with_entreprise_config({
        'quittances': page_obj,
        'total_quittances': total_quittances,
        'quittances_imprimees': quittances_imprimees,
        'quittances_envoyees': quittances_envoyees,
        'title': 'Liste des quittances de paiement'
    })
    
    return render(request, 'paiements/quittance_list.html', context)


@login_required
@require_POST
def marquer_quittance_imprimee(request, pk):
    """Marquer une quittance comme imprimée."""
    # Vérification des permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE'], 'modify')
    if not permissions['allowed']:
        return JsonResponse({'success': False, 'message': permissions['message']}, status=403)
    
    try:
        quittance = get_object_or_404(QuittancePaiement, pk=pk)
        quittance.marquer_imprimee()
        
        # Log d'audit
        AuditLog.objects.create(
            content_type=ContentType.objects.get_for_model(QuittancePaiement),
            object_id=quittance.pk,
            action='UPDATE',
            old_data={'statut': 'generee'},
            new_data={'statut': 'imprimee', 'date_impression': quittance.date_impression.isoformat()},
            user=request.user,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        return JsonResponse({'success': True, 'message': 'Quittance marquée comme imprimée'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@login_required
@require_POST
def marquer_quittance_envoyee(request, pk):
    """Marquer une quittance comme envoyée."""
    # Vérification des permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE'], 'modify')
    if not permissions['allowed']:
        return JsonResponse({'success': False, 'message': permissions['message']}, status=403)
    
    try:
        quittance = get_object_or_404(QuittancePaiement, pk=pk)
        quittance.marquer_envoyee()
        
        # Log d'audit
        AuditLog.objects.create(
            content_type=ContentType.objects.get_for_model(QuittancePaiement),
            object_id=quittance.pk,
            action='UPDATE',
            old_data={'statut': quittance.statut},
            new_data={'statut': 'envoyee'},
            user=request.user,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        messages.success(request, 'Quittance marquée comme envoyée')
        return redirect('paiements:quittance_detail', pk=pk)
    except Exception as e:
        messages.error(request, f'Erreur lors de la mise à jour: {str(e)}')
        return redirect('paiements:quittance_detail', pk=pk)


@login_required
@require_POST
def marquer_quittance_archivee(request, pk):
    """Marquer une quittance comme archivée."""
    # Vérification des permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE'], 'modify')
    if not permissions['allowed']:
        return JsonResponse({'success': False, 'message': permissions['message']}, status=403)
    
    try:
        quittance = get_object_or_404(QuittancePaiement, pk=pk)
        quittance.marquer_archivee()
        
        # Log d'audit
        AuditLog.objects.create(
            content_type=ContentType.objects.get_for_model(QuittancePaiement),
            object_id=quittance.pk,
            action='UPDATE',
            old_data={'statut': quittance.statut},
            new_data={'statut': 'archivée'},
            user=request.user,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        messages.success(request, 'Quittance marquée comme archivée')
        return redirect('paiements:quittance_detail', pk=pk)
    except Exception as e:
        messages.error(request, f'Erreur lors de la mise à jour: {str(e)}')
        return redirect('paiements:quittance_detail', pk=pk)


@login_required
def generer_quittance_manuelle(request, paiement_pk):
    """Générer manuellement une quittance pour un paiement existant."""
    # Vérification des permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE'], 'add')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:detail', pk=paiement_pk)
    
    try:
        paiement = get_object_or_404(Paiement, pk=paiement_pk)
        
        # Vérifier si une quittance existe déjà
        if hasattr(paiement, 'quittance'):
            messages.warning(request, 'Une quittance existe déjà pour ce paiement')
            return redirect('paiements:quittance_detail', pk=paiement.quittance.pk)
        
        # Générer la quittance
        quittance = QuittancePaiement.objects.create(
            paiement=paiement,
            cree_par=request.user
        )
        
        # Log d'audit
        AuditLog.objects.create(
            content_type=ContentType.objects.get_for_model(QuittancePaiement),
            object_id=quittance.pk,
            action='CREATE',
            old_data=None,
            new_data={f.name: getattr(quittance, f.name) for f in quittance._meta.fields},
            user=request.user,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        messages.success(request, f'Quittance {quittance.numero_quittance} générée avec succès')
        return redirect('paiements:quittance_detail', pk=quittance.pk)
    except Exception as e:
        messages.error(request, f'Erreur lors de la génération de la quittance: {str(e)}')
        return redirect('paiements:detail', pk=paiement_pk)


# =============================================================================
# VUES POUR LES TABLEAUX DE BORD FINANCIERS
# =============================================================================

@login_required
def tableau_bord_detail(request, pk):
    """Afficher le détail d'un tableau de bord financier."""
    # Vérification des permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE'], 'view')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:tableau_bord_list')
    
    tableau = get_object_or_404(
        TableauBordFinancier.objects.select_related('cree_par').prefetch_related('proprietes', 'bailleurs'),
        pk=pk
    )
    
    # Vérifier que l'utilisateur peut voir ce tableau de bord
    if tableau.cree_par != request.user and not request.user.is_superuser:
        messages.error(request, 'Vous n\'avez pas les permissions pour voir ce tableau de bord.')
        return redirect('paiements:tableau_bord_list')
    
    # Calculer les statistiques
    stats = tableau.get_statistiques_financieres()
    
    context = get_context_with_entreprise_config({
        'tableau': tableau,
        'stats': stats,
        'title': f'Tableau de Bord - {tableau.nom}'
    })
    
    return render(request, 'paiements/tableaux_bord/tableau_detail.html', context)


@login_required
def tableau_bord_create(request):
    """Créer un nouveau tableau de bord financier."""
    # Vérification des permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE'], 'add')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:tableau_bord_list')
    
    if request.method == 'POST':
        form = TableauBordFinancierForm(request.POST, user=request.user)
        if form.is_valid():
            tableau = form.save(commit=False)
            tableau.cree_par = request.user
            tableau.save()
            
            # Sauvegarder les relations many-to-many
            form.save_m2m()
            
            # Log d'audit
            AuditLog.objects.create(
                content_type=ContentType.objects.get_for_model(TableauBordFinancier),
                object_id=tableau.pk,
                action='CREATE',
                old_data=None,
                new_data={f.name: getattr(tableau, f.name) for f in tableau._meta.fields},
                user=request.user,
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            messages.success(request, f'Tableau de bord "{tableau.nom}" créé avec succès.')
            return redirect('paiements:tableau_bord_detail', pk=tableau.pk)
    else:
        form = TableauBordFinancierForm(user=request.user)
    
    context = get_context_with_entreprise_config({
        'form': form,
        'title': 'Créer un Tableau de Bord Financier'
    })
    
    return render(request, 'paiements/tableaux_bord/tableau_form.html', context)


@login_required
def tableau_bord_update(request, pk):
    """Modifier un tableau de bord financier existant."""
    # Vérification des permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE'], 'change')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:tableau_bord_list')
    
    tableau = get_object_or_404(TableauBordFinancier, pk=pk)
    
    # Vérifier que l'utilisateur peut modifier ce tableau de bord
    if tableau.cree_par != request.user and not request.user.is_superuser:
        messages.error(request, 'Vous n\'avez pas les permissions pour modifier ce tableau de bord.')
        return redirect('paiements:tableau_bord_list')
    
    if request.method == 'POST':
        form = TableauBordFinancierForm(request.POST, instance=tableau, user=request.user)
        if form.is_valid():
            # Sauvegarder les anciennes données pour l'audit
            old_data = {f.name: getattr(tableau, f.name) for f in tableau._meta.fields}
            
            tableau = form.save()
            
            # Log d'audit
            AuditLog.objects.create(
                content_type=ContentType.objects.get_for_model(TableauBordFinancier),
                object_id=tableau.pk,
                action='UPDATE',
                old_data=old_data,
                new_data={f.name: getattr(tableau, f.name) for f in tableau._meta.fields},
                user=request.user,
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            messages.success(request, f'Tableau de bord "{tableau.nom}" modifié avec succès.')
            return redirect('paiements:tableau_bord_detail', pk=tableau.pk)
    else:
        form = TableauBordFinancierForm(instance=tableau, user=request.user)
    
    context = get_context_with_entreprise_config({
        'form': form,
        'tableau': tableau,
        'title': f'Modifier le Tableau de Bord - {tableau.nom}'
    })
    
    return render(request, 'paiements/tableaux_bord/tableau_form.html', context)


@login_required
@require_POST
def tableau_bord_delete(request, pk):
    """Supprimer un tableau de bord financier."""
    # Vérification des permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE'], 'delete')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:tableau_bord_list')
    
    tableau = get_object_or_404(TableauBordFinancier, pk=pk)
    
    # Vérifier que l'utilisateur peut supprimer ce tableau de bord
    if tableau.cree_par != request.user and not request.user.is_superuser:
        messages.error(request, 'Vous n\'avez pas les permissions pour supprimer ce tableau de bord.')
        return redirect('paiements:tableau_bord_list')
    
    nom_tableau = tableau.nom
    
    try:
        # Log d'audit avant suppression
        AuditLog.objects.create(
            content_type=ContentType.objects.get_for_model(TableauBordFinancier),
            object_id=tableau.pk,
            action='DELETE',
            old_data={f.name: getattr(tableau, f.name) for f in tableau._meta.fields},
            new_data=None,
            user=request.user,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        tableau.delete()
        messages.success(request, f'Tableau de bord "{nom_tableau}" supprimé avec succès.')
        
    except Exception as e:
        messages.error(request, f'Erreur lors de la suppression: {str(e)}')
    
    return redirect('paiements:tableau_bord_list')


@login_required
def tableau_bord_export_pdf(request, pk):
    """Exporter un tableau de bord en PDF."""
    # Vérification des permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE'], 'view')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:tableau_bord_list')
    
    tableau = get_object_or_404(TableauBordFinancier, pk=pk)
    
    # Vérifier que l'utilisateur peut voir ce tableau de bord
    if tableau.cree_par != request.user and not request.user.is_superuser:
        messages.error(request, 'Vous n\'avez pas les permissions pour exporter ce tableau de bord.')
        return redirect('paiements:tableau_bord_list')
    
    try:
        # TODO: Implémenter la génération PDF
        # response = generate_tableau_bord_pdf(tableau, stats)
        messages.warning(request, 'Export PDF en cours de développement.')
        return redirect('paiements:tableau_bord_detail', pk=pk)
        
    except Exception as e:
        messages.error(request, f'Erreur lors de l\'export PDF: {str(e)}')
        return redirect('paiements:tableau_bord_detail', pk=pk)


@login_required
def tableau_bord_dashboard(request):
    """Dashboard principal des tableaux de bord financiers."""
    # Vérification des permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE'], 'view')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:dashboard')
    
    # Récupérer les tableaux de bord de l'utilisateur
    tableaux = TableauBordFinancier.objects.filter(
        cree_par=request.user,
        actif=True
    ).select_related('cree_par').prefetch_related('proprietes', 'bailleurs').order_by('-date_creation')[:6]
    
    # Statistiques globales
    total_tableaux = TableauBordFinancier.objects.filter(cree_par=request.user).count()
    tableaux_actifs = TableauBordFinancier.objects.filter(cree_par=request.user, actif=True).count()
    tableaux_alerte = sum(1 for t in tableaux if t.is_alerte_active())
    
    # Tableaux récents avec alertes
    tableaux_alertes = [t for t in tableaux if t.is_alerte_active()]
    
    context = get_context_with_entreprise_config({
        'tableaux': tableaux,
        'tableaux_alertes': tableaux_alertes,
        'total_tableaux': total_tableaux,
        'tableaux_actifs': tableaux_actifs,
        'tableaux_alerte': tableaux_alerte,
        'title': 'Dashboard des Tableaux de Bord Financiers'
    })
    
    return render(request, 'paiements/tableaux_bord/dashboard.html', context)
