from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count
from django.utils import timezone
from django.template.loader import render_to_string
from django.contrib.auth import get_user_model
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import json

from .models import (
    RetraitBailleur, RetraitChargeDeductible, RecuRetrait,
    Paiement, ChargeDeductible
)
from .forms import RetraitBailleurForm
from proprietes.models import Bailleur
from core.utils import format_currency_xof, get_context_with_entreprise_config

Utilisateur = get_user_model()


@login_required
def retrait_list(request):
    """Vue pour lister tous les retraits aux bailleurs."""
    # Récupérer les paramètres de filtrage
    statut = request.GET.get('statut', '')
    bailleur_id = request.GET.get('bailleur', '')
    mois = request.GET.get('mois', '')
    
    # Construire la requête de base
    retraits = RetraitBailleur.objects.select_related(
        'bailleur', 'cree_par', 'valide_par'
    ).order_by('-date_creation')
    
    # Appliquer les filtres
    if statut:
        retraits = retraits.filter(statut=statut)
    
    if bailleur_id:
        retraits = retraits.filter(bailleur_id=bailleur_id)
    
    if mois:
        try:
            mois_date = datetime.strptime(mois, '%Y-%m').date()
            retraits = retraits.filter(mois_retrait__year=mois_date.year, 
                                     mois_retrait__month=mois_date.month)
        except ValueError:
            pass
    
    # Pagination
    paginator = Paginator(retraits, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistiques
    stats = {
        'total_retraits': RetraitBailleur.objects.count(),
        'total_montant': RetraitBailleur.objects.aggregate(
            total=Sum('montant_net_a_payer')
        )['total'] or 0,
        'retraits_en_attente': RetraitBailleur.objects.filter(statut='en_attente').count(),
        'retraits_payes': RetraitBailleur.objects.filter(statut='paye').count(),
    }
    
    # Bailleurs pour le filtre
    bailleurs = Bailleur.objects.all().order_by('nom')
    
    # Filtres appliqués
    filtres = {
        'statut': statut,
        'bailleur_id': bailleur_id,
        'mois': mois,
    }
    
    context = {
        'page_obj': page_obj,
        'stats': stats,
        'bailleurs': bailleurs,
        'filtres': filtres,
    }
    
    return render(request, 'paiements/retraits/retrait_list.html', context)


@login_required
def retrait_create(request):
    """Vue pour créer un nouveau retrait."""
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
            
            # Créer automatiquement un reçu de retrait
            try:
                recu = RecuRetrait.objects.create(
                    retrait_bailleur=retrait,
                    genere_automatiquement=True
                )
                messages.success(request, f'Retrait créé avec succès pour {retrait.bailleur.nom} {retrait.bailleur.prenom}. Reçu généré: {recu.numero_recu}')
            except Exception as e:
                messages.warning(request, f'Retrait créé mais erreur lors de la génération du reçu: {str(e)}')
            
            return redirect('paiements:retraits_liste')
        else:
            messages.error(request, 'Veuillez corriger les erreurs dans le formulaire.')
    else:
        form = RetraitBailleurForm()
    
    # Récupérer la liste des bailleurs pour le contexte
    bailleurs = Bailleur.objects.filter(actif=True).order_by('nom', 'prenom')
    
    context = get_context_with_entreprise_config({
        'form': form,
        'bailleurs': bailleurs,
        'title': 'Ajouter un Retrait'
    })
    
    return render(request, 'paiements/retrait_ajouter.html', context)


@login_required
def retrait_auto_create(request):
    """Vue pour la création automatique des retraits."""
    if request.method == 'POST':
        mois_retrait = request.POST.get('mois_retrait')
        type_retrait = request.POST.get('type_retrait')
        mode_retrait_default = request.POST.get('mode_retrait_default')
        inclure_charges = request.POST.get('inclure_charges') == 'on'
        
        try:
            # Logique de création automatique
            # Ici vous implémenteriez la logique pour créer automatiquement
            # les retraits pour tous les bailleurs concernés
            
            messages.success(request, 'Retraits créés automatiquement avec succès')
            return redirect('paiements:retraits_liste')
            
        except Exception as e:
            messages.error(request, f'Erreur lors de la création automatique: {str(e)}')
    
    # Statistiques pour l'aperçu
    total_bailleurs = Bailleur.objects.count()
    bailleurs_avec_proprietes = Bailleur.objects.filter(
        proprietes__contrats__est_actif=True
    ).distinct().count()
    contrats_actifs = sum(
        bailleur.proprietes.filter(contrats__est_actif=True).count()
        for bailleur in Bailleur.objects.all()
    )
    
    # Bailleurs concernés
    bailleurs_concernes = Bailleur.objects.filter(
        proprietes__contrats__est_actif=True
    ).distinct().annotate(
        nombre_proprietes=Count('proprietes')
    )[:10]  # Limiter à 10 pour l'aperçu
    
    context = {
        'total_bailleurs': total_bailleurs,
        'bailleurs_avec_proprietes': bailleurs_avec_proprietes,
        'contrats_actifs': contrats_actifs,
        'bailleurs_concernes': bailleurs_concernes,
    }
    
    return render(request, 'paiements/retraits/retrait_auto_create.html', context)


@login_required
def retrait_detail(request, pk):
    """Vue pour afficher les détails d'un retrait."""
    retrait = get_object_or_404(RetraitBailleur, id=pk)
    
    context = {
        'retrait': retrait,
    }
    
    return render(request, 'paiements/retraits/retrait_detail.html', context)


@login_required
def retrait_edit(request, pk):
    """Vue pour modifier un retrait."""
    retrait = get_object_or_404(RetraitBailleur, id=pk)
    
    if request.method == 'POST':
        # Logique de modification
        pass
    
    context = {
        'retrait': retrait,
    }
    
    return render(request, 'paiements/retraits/retrait_edit.html', context)


@login_required
def retrait_validate(request, pk):
    """Vue pour valider un retrait."""
    if request.method == 'POST':
        retrait = get_object_or_404(RetraitBailleur, id=pk)
        
        try:
            retrait.valider_retrait(request.user)
            messages.success(request, 'Retrait validé avec succès')
        except Exception as e:
            messages.error(request, f'Erreur lors de la validation: {str(e)}')
    
    return redirect('paiements:retrait_detail', pk=pk)


@login_required
def retrait_mark_paid(request, pk):
    """Vue pour marquer un retrait comme payé."""
    if request.method == 'POST':
        retrait = get_object_or_404(RetraitBailleur, id=pk)
        
        try:
            retrait.marquer_paye(request.user)
            messages.success(request, 'Retrait marqué comme payé')
        except Exception as e:
            messages.error(request, f'Erreur: {str(e)}')
    
    return redirect('paiements:retrait_detail', pk=pk)


@login_required
def retrait_cancel(request, pk):
    """Vue pour annuler un retrait."""
    if request.method == 'POST':
        retrait = get_object_or_404(RetraitBailleur, id=pk)
        motif = request.POST.get('motif', '')
        
        try:
            retrait.annuler_retrait(request.user, motif)
            messages.success(request, 'Retrait annulé avec succès')
        except Exception as e:
            messages.error(request, f'Erreur lors de l\'annulation: {str(e)}')
    
    return redirect('paiements:retraits_liste')


@login_required
def recu_retrait_view(request, recu_id):
    """Vue pour afficher un reçu de retrait."""
    recu = get_object_or_404(RecuRetrait, id=recu_id)
    
    # Récupérer la configuration de l'entreprise
    from core.models import ConfigurationEntreprise
    config = ConfigurationEntreprise.get_configuration_active()
    
    context = {
        'recu': recu,
        'config': config,
    }
    
    return render(request, 'paiements/retraits/recu_retrait_paysage.html', context)


@login_required
def recu_retrait_print(request, recu_id):
    """Vue pour imprimer un reçu de retrait."""
    recu = get_object_or_404(RecuRetrait, id=recu_id)
    
    # Marquer comme imprimé
    recu.marquer_imprime(request.user)
    
    # Récupérer la configuration de l'entreprise
    from core.models import ConfigurationEntreprise
    config = ConfigurationEntreprise.get_configuration_active()
    
    # Rendu du template pour impression
    html_content = render_to_string('paiements/retraits/recu_retrait_paysage.html', {
        'recu': recu,
        'config': config,
        'print_mode': True
    })
    
    response = HttpResponse(html_content, content_type='text/html')
    response['Content-Disposition'] = f'inline; filename="recu_retrait_{recu.numero_recu}.html"'
    
    return response


@login_required
def retrait_report(request):
    """Vue pour les rapports de retraits."""
    # Logique des rapports
    context = {}
    return render(request, 'paiements/retraits/retrait_report.html', context)


@login_required
def get_bailleur_retrait_data(request, bailleur_id):
    """API pour récupérer les données d'un bailleur pour les retraits."""
    try:
        bailleur = get_object_or_404(Bailleur, id=bailleur_id)
        
        # Calculer les montants pour le mois actuel
        mois_actuel = timezone.now().replace(day=1)
        
        # Loyers perçus
        loyers_bruts = Paiement.objects.filter(
            contrat__propriete__bailleur=bailleur,
            contrat__est_actif=True,
            date_paiement__year=mois_actuel.year,
            date_paiement__month=mois_actuel.month,
            statut='valide'
        ).aggregate(total=Sum('montant'))['total'] or 0
        
        # Charges déductibles
        charges = ChargeDeductible.objects.filter(
            contrat__propriete__bailleur=bailleur,
            contrat__est_actif=True,
            date_charge__year=mois_actuel.year,
            date_charge__month=mois_actuel.month,
            statut='validee'
        ).aggregate(total=Sum('montant'))['total'] or 0
        
        data = {
            'bailleur_id': bailleur.id,
            'bailleur_nom': bailleur.get_nom_complet(),
            'mois': mois_actuel.strftime('%Y-%m'),
            'loyers_bruts': float(loyers_bruts),
            'charges_deductibles': float(charges),
            'net_a_payer': float(loyers_bruts - charges),
            'proprietes_count': bailleur.proprietes.filter(contrats__est_actif=True).distinct().count()
        }
        
        return JsonResponse(data)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
