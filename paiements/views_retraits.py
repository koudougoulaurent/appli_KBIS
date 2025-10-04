"""
Vues pour la gestion des retraits aux bailleurs
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.utils import timezone
from datetime import date, datetime
from decimal import Decimal

from proprietes.models import Bailleur
from .models import RetraitBailleur, RetraitQuittance, Paiement
from .services_retraits import ServiceCalculRetraits
from core.utils import check_group_permissions


@login_required
def liste_retraits(request):
    """
    Liste des retraits aux bailleurs
    """
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'CONTROLES', 'CAISSE'], 'view')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('core:dashboard')
    
    # Filtres
    statut = request.GET.get('statut', '')
    mois = request.GET.get('mois', '')
    bailleur_id = request.GET.get('bailleur', '')
    
    # Requête de base
    retraits = RetraitBailleur.objects.filter(
        is_deleted=False
    ).select_related('bailleur', 'cree_par').order_by('-mois_retrait', '-date_demande')
    
    # Appliquer les filtres
    if statut:
        retraits = retraits.filter(statut=statut)
    
    if mois:
        try:
            mois_date = datetime.strptime(mois, '%Y-%m').date()
            retraits = retraits.filter(mois_retrait__year=mois_date.year, mois_retrait__month=mois_date.month)
        except ValueError:
            pass
    
    if bailleur_id:
        retraits = retraits.filter(bailleur_id=bailleur_id)
    
    # Pagination
    paginator = Paginator(retraits, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistiques
    stats = {
        'total': retraits.count(),
        'en_attente': retraits.filter(statut='en_attente').count(),
        'valides': retraits.filter(statut='valide').count(),
        'payes': retraits.filter(statut='paye').count(),
        'montant_total': retraits.aggregate(total=Sum('montant_net_a_payer'))['total'] or Decimal('0'),
    }
    
    # Bailleurs pour le filtre
    bailleurs = Bailleur.objects.filter(actif=True).order_by('nom', 'prenom')
    
    context = {
        'page_obj': page_obj,
        'stats': stats,
        'bailleurs': bailleurs,
        'filters': {
            'statut': statut,
            'mois': mois,
            'bailleur': bailleur_id,
        }
    }
    
    return render(request, 'paiements/retraits/liste_retraits.html', context)


@login_required
def detail_retrait(request, pk):
    """
    Détail d'un retrait
    """
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'CONTROLES', 'CAISSE'], 'view')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:liste_retraits')
    
    retrait = get_object_or_404(RetraitBailleur, pk=pk, is_deleted=False)
    
    # Récupérer les propriétés du bailleur
    proprietes = retrait.bailleur.proprietes.filter(is_deleted=False)
    
    # Récupérer les paiements du mois
    mois_debut = retrait.mois_retrait
    if mois_debut.month == 12:
        mois_fin = date(mois_debut.year + 1, 1, 1)
    else:
        mois_fin = date(mois_debut.year, mois_debut.month + 1, 1)
    
    paiements = Paiement.objects.filter(
        contrat__propriete__bailleur=retrait.bailleur,
        date_paiement__gte=mois_debut,
        date_paiement__lt=mois_fin,
        statut='valide',
        is_deleted=False
    ).select_related('contrat', 'contrat__propriete')
    
    context = {
        'retrait': retrait,
        'proprietes': proprietes,
        'paiements': paiements,
    }
    
    return render(request, 'paiements/retraits/detail_retrait.html', context)


@login_required
def creer_retrait_automatique(request):
    """
    Création automatique des retraits
    """
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'CONTROLES', 'CAISSE'], 'add')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:liste_retraits')
    
    if request.method == 'POST':
        mois_retrait = request.POST.get('mois_retrait')
        
        try:
            # Parser la date
            if mois_retrait:
                mois_date = datetime.strptime(mois_retrait, '%Y-%m').date()
                mois = mois_date.month
                annee = mois_date.year
            else:
                mois = timezone.now().month
                annee = timezone.now().year
            
            # Créer les retraits automatiques
            resultat = ServiceCalculRetraits.creer_retraits_automatiques_mensuels(
                mois, annee, request.user
            )
            
            # Messages détaillés
            if resultat['retraits_crees'] > 0:
                messages.success(
                    request, 
                    f'{resultat["retraits_crees"]} retraits créés automatiquement avec succès'
                )
            
            # Messages informatifs
            if resultat['retraits_existants'] > 0:
                messages.info(
                    request, 
                    f'{resultat["retraits_existants"]} retraits existent déjà pour ce mois'
                )
            
            if resultat['cautions_manquantes'] > 0:
                messages.warning(
                    request, 
                    f'{resultat["cautions_manquantes"]} bailleurs ont des cautions non payées mais loyers du mois payés - retraits créés'
                )
            
            if resultat['loyers_manquants'] > 0:
                messages.error(
                    request, 
                    f'{resultat["loyers_manquants"]} bailleurs ont des cautions ET loyers manquants - retraits non créés'
                )
            
            if resultat['aucun_loyer'] > 0:
                messages.info(
                    request, 
                    f'{resultat["aucun_loyer"]} bailleurs n\'ont pas de loyers à retirer ce mois'
                )
            
            if resultat['retraits_crees'] == 0 and resultat['retraits_existants'] == 0 and resultat['cautions_manquantes'] == 0 and resultat['aucun_loyer'] == 0:
                messages.info(
                    request, 
                    'Aucun retrait à créer pour ce mois'
                )
            
            return redirect('paiements:liste_retraits')
            
        except Exception as e:
            messages.error(request, f'Erreur lors de la création automatique: {str(e)}')
    
    # Statistiques pour l'aperçu
    total_bailleurs = Bailleur.objects.filter(actif=True).count()
    bailleurs_avec_proprietes = Bailleur.objects.filter(
        actif=True,
        proprietes__is_deleted=False
    ).distinct().count()
    
    context = {
        'total_bailleurs': total_bailleurs,
        'bailleurs_avec_proprietes': bailleurs_avec_proprietes,
    }
    
    return render(request, 'paiements/retraits/creer_retrait_automatique.html', context)


@login_required
def valider_retrait(request, pk):
    """
    Valider un retrait
    """
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'CONTROLES'], 'change')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:retrait_detail', pk=pk)
    
    retrait = get_object_or_404(RetraitBailleur, pk=pk, is_deleted=False)
    
    if retrait.statut != 'en_attente':
        messages.error(request, 'Ce retrait ne peut pas être validé')
        return redirect('paiements:retrait_detail', pk=pk)
    
    retrait.valider(request.user)
    messages.success(request, 'Retrait validé avec succès')
    
    return redirect('paiements:retrait_detail', pk=pk)


@login_required
def marquer_paye(request, pk):
    """
    Effectue le retrait (marque comme payé) - Action définitive
    """
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'CAISSE'], 'change')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:retrait_detail', pk=pk)
    
    retrait = get_object_or_404(RetraitBailleur, pk=pk, is_deleted=False)
    
    if retrait.statut != 'valide':
        messages.error(request, 'Seuls les retraits validés peuvent être effectués')
        return redirect('paiements:retrait_detail', pk=pk)
    
    # Effectuer le retrait (marquer comme payé)
    retrait.marquer_paye(request.user)
    messages.success(request, 'Retrait effectué avec succès - Le montant a été retiré')
    
    return redirect('paiements:retrait_detail', pk=pk)


@login_required
def generer_quittance(request, pk):
    """
    Générer une quittance de retrait (redirige vers la version KBIS dynamique)
    """
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'CONTROLES', 'CAISSE'], 'view')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:retrait_detail', pk=pk)
    
    retrait = get_object_or_404(RetraitBailleur, pk=pk, is_deleted=False)
    
    # Créer ou récupérer la quittance
    quittance, created = RetraitQuittance.objects.get_or_create(
        retrait=retrait,
        defaults={'cree_par': request.user}
    )
    
    if created:
        messages.success(request, 'Quittance générée avec succès')
    else:
        messages.info(request, 'Quittance déjà existante')
    
    # Rediriger vers la génération de quittance KBIS dynamique
    return redirect('paiements:generer_quittance_retrait_kbis', retrait_pk=pk)


@login_required
def telecharger_quittance(request, pk):
    """
    Télécharger une quittance de retrait (redirige vers la version KBIS dynamique)
    """
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'CONTROLES', 'CAISSE'], 'view')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:retrait_detail', pk=pk)
    
    retrait = get_object_or_404(RetraitBailleur, pk=pk, is_deleted=False)
    
    # Rediriger vers la génération de quittance KBIS dynamique
    return redirect('paiements:generer_quittance_retrait_kbis', retrait_pk=pk)


@login_required
def supprimer_retrait(request, pk):
    """
    Supprimer un retrait (suppression logique)
    """
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION'], 'delete')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:retrait_detail', pk=pk)
    
    retrait = get_object_or_404(RetraitBailleur, pk=pk, is_deleted=False)
    
    if retrait.statut == 'paye':
        messages.error(request, 'Impossible de supprimer un retrait déjà payé')
        return redirect('paiements:retrait_detail', pk=pk)
    
    retrait.is_deleted = True
    retrait.save()
    
    messages.success(request, 'Retrait supprimé avec succès')
    return redirect('paiements:liste_retraits')
