"""
Vues pour la gestion des retraits avec conditions temporelles
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from datetime import date

from .services_retraits import ServiceCalculRetraits
from core.utils import check_group_permissions


@login_required
def test_conditions_temporelles(request):
    """
    Teste les conditions temporelles pour la génération automatique des retraits
    """
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE', 'CAISSE', 'CONTROLES', 'GESTIONNAIRE'], 'view')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('core:dashboard')
    
    # Vérifier les conditions temporelles
    conditions_ok, message = ServiceCalculRetraits.verifier_conditions_temporelles()
    
    aujourd_hui = date.today()
    jour_actuel = aujourd_hui.day
    
    context = {
        'conditions_ok': conditions_ok,
        'message': message,
        'jour_actuel': jour_actuel,
        'aujourd_hui': aujourd_hui,
        'periode_autorisee': 'Du 25 du mois courant au 5 du mois suivant'
    }
    
    return render(request, 'paiements/test_conditions_temporelles.html', context)


@login_required
def generer_retraits_automatiques(request):
    """
    Génère automatiquement les retraits pour tous les bailleurs éligibles
    avec vérification des conditions temporelles
    """
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE', 'CAISSE', 'CONTROLES', 'GESTIONNAIRE'], 'add')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('core:dashboard')
    
    if request.method == 'POST':
        # Récupérer le mois et l'année depuis le formulaire
        mois = int(request.POST.get('mois', timezone.now().month))
        annee = int(request.POST.get('annee', timezone.now().year))
        
        # Générer les retraits automatiques
        resultat = ServiceCalculRetraits.creer_retraits_automatiques_mensuels(mois, annee, request.user)
        
        if resultat['success']:
            messages.success(request, resultat['message'])
        else:
            messages.error(request, resultat['message'])
        
        # Afficher les détails
        for detail in resultat.get('details', []):
            if '✅' in detail:
                messages.success(request, detail)
            else:
                messages.warning(request, detail)
        
        return redirect('paiements:test_conditions_temporelles')
    
    # Afficher le formulaire
    aujourd_hui = timezone.now().date()
    context = {
        'aujourd_hui': aujourd_hui,
        'mois_actuel': aujourd_hui.month,
        'annee_actuelle': aujourd_hui.year
    }
    
    return render(request, 'paiements/generer_retraits_automatiques.html', context)


@login_required
def creer_retrait_manuel(request):
    """
    Crée un retrait manuel pour un bailleur spécifique
    N'APPLIQUE PAS les conditions temporelles - permet la création à tout moment
    """
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE', 'CAISSE', 'CONTROLES', 'GESTIONNAIRE'], 'add')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('core:dashboard')
    
    if request.method == 'POST':
        bailleur_id = request.POST.get('bailleur_id')
        mois = int(request.POST.get('mois', timezone.now().month))
        annee = int(request.POST.get('annee', timezone.now().year))
        
        try:
            from proprietes.models import Bailleur
            bailleur = Bailleur.objects.get(id=bailleur_id, is_deleted=False)
            
            # Créer le retrait manuel (sans conditions temporelles)
            retrait = ServiceCalculRetraits.creer_retrait_manuel(bailleur, mois, annee, request.user)
            
            if retrait:
                messages.success(request, f"Retrait manuel créé avec succès pour {bailleur.nom} {bailleur.prenom} - Montant: {retrait.montant_net_a_payer} F CFA")
                return redirect('paiements:retrait_detail', pk=retrait.id)
            else:
                messages.error(request, f"Impossible de créer le retrait manuel pour {bailleur.nom} {bailleur.prenom}")
                
        except Exception as e:
            messages.error(request, f"Erreur lors de la création du retrait manuel: {str(e)}")
    
    # Afficher le formulaire
    from proprietes.models import Bailleur
    bailleurs = Bailleur.objects.filter(is_deleted=False).order_by('nom', 'prenom')
    
    aujourd_hui = timezone.now().date()
    context = {
        'bailleurs': bailleurs,
        'aujourd_hui': aujourd_hui,
        'mois_actuel': aujourd_hui.month,
        'annee_actuelle': aujourd_hui.year
    }
    
    return render(request, 'paiements/creer_retrait_manuel.html', context)


@login_required
def api_conditions_temporelles(request):
    """
    API pour vérifier les conditions temporelles (AJAX)
    """
    conditions_ok, message = ServiceCalculRetraits.verifier_conditions_temporelles()
    
    return JsonResponse({
        'conditions_ok': conditions_ok,
        'message': message,
        'jour_actuel': date.today().day
    })
