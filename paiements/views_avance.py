from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from decimal import Decimal
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
import json

from contrats.models import Contrat
from .models import Paiement
from .models_avance import AvanceLoyer, ConsommationAvance, HistoriquePaiement
from .services_avance import ServiceGestionAvance
from .forms_avance import AvanceLoyerForm, PaiementAvanceForm
from .utils_pdf import generate_historique_pdf


@login_required
def dashboard_avances(request):
    """Dashboard principal des avances de loyer"""
    try:
        # Statistiques générales
        total_avances = AvanceLoyer.objects.filter(statut='active').count()
        montant_total_avances = AvanceLoyer.objects.filter(statut='active').aggregate(
            total=Sum('montant_avance')
        )['total'] or Decimal('0')
        
        avances_epuisees = AvanceLoyer.objects.filter(statut='epuisee').count()
        avances_actives = AvanceLoyer.objects.filter(statut='active').count()
        
        # Calculer les pourcentages
        total_avances = avances_actives + avances_epuisees
        pourcentage_actives = round((avances_actives * 100) / total_avances, 1) if total_avances > 0 else 0
        pourcentage_epuisees = round((avances_epuisees * 100) / total_avances, 1) if total_avances > 0 else 0
        
        # Avances récentes
        avances_recentes = AvanceLoyer.objects.select_related('contrat__locataire', 'contrat__propriete').order_by('-created_at')[:5]
        
        # Contrats avec avances
        contrats_avec_avances = Contrat.objects.filter(
            avances_loyer__isnull=False
        ).distinct().count()
        
        # Statistiques par mois
        mois_courant = date.today().replace(day=1)
        avances_ce_mois = AvanceLoyer.objects.filter(
            date_avance__year=mois_courant.year,
            date_avance__month=mois_courant.month
        ).count()
        
        montant_avances_ce_mois = AvanceLoyer.objects.filter(
            date_avance__year=mois_courant.year,
            date_avance__month=mois_courant.month
        ).aggregate(total=Sum('montant_avance'))['total'] or Decimal('0')
        
        context = {
            'total_avances': total_avances,
            'montant_total_avances': montant_total_avances,
            'avances_epuisees': avances_epuisees,
            'avances_actives': avances_actives,
            'pourcentage_actives': pourcentage_actives,
            'pourcentage_epuisees': pourcentage_epuisees,
            'avances_recentes': avances_recentes,
            'contrats_avec_avances': contrats_avec_avances,
            'avances_ce_mois': avances_ce_mois,
            'montant_avances_ce_mois': montant_avances_ce_mois,
        }
        
        return render(request, 'paiements/avances/dashboard_avances.html', context)
        
    except Exception as e:
        messages.error(request, f"Erreur lors du chargement du dashboard: {str(e)}")
        return render(request, 'paiements/avances/dashboard_avances.html', {
            'total_avances': 0,
            'montant_total_avances': Decimal('0'),
            'avances_epuisees': 0,
            'avances_actives': 0,
            'avances_recentes': [],
            'contrats_avec_avances': 0,
            'avances_ce_mois': 0,
            'montant_avances_ce_mois': Decimal('0'),
        })


@login_required
def liste_avances(request):
    """
    Liste des avances de loyer
    """
    # Récupérer les avances avec pagination
    avances = AvanceLoyer.objects.select_related('contrat', 'contrat__locataire', 'contrat__propriete').all()
    
    # Filtres
    contrat_id = request.GET.get('contrat')
    statut = request.GET.get('statut')
    mois_debut = request.GET.get('mois_debut')
    mois_fin = request.GET.get('mois_fin')
    
    if contrat_id:
        avances = avances.filter(contrat_id=contrat_id)
    
    if statut:
        avances = avances.filter(statut=statut)
    
    if mois_debut:
        try:
            mois_debut_date = datetime.strptime(mois_debut, '%Y-%m').date()
            avances = avances.filter(mois_debut_couverture__gte=mois_debut_date)
        except ValueError:
            pass
    
    if mois_fin:
        try:
            mois_fin_date = datetime.strptime(mois_fin, '%Y-%m').date()
            avances = avances.filter(mois_fin_couverture__lte=mois_fin_date)
        except ValueError:
            pass
    
    # Pagination
    paginator = Paginator(avances, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistiques
    stats = {
        'total_avances': avances.count(),
        'avances_actives': avances.filter(statut='active').count(),
        'avances_epuisees': avances.filter(statut='epuisee').count(),
        'montant_total_avances': avances.aggregate(total=Sum('montant_avance'))['total'] or 0,
        'montant_restant': avances.aggregate(total=Sum('montant_restant'))['total'] or 0,
    }
    
    # Contrats pour le filtre
    contrats = Contrat.objects.filter(est_actif=True).select_related('locataire', 'propriete')
    
    context = {
        'avances': page_obj,  # Passer page_obj comme avances pour le template
        'page_obj': page_obj,
        'stats': stats,
        'contrats': contrats,
        'filters': {
            'contrat_id': contrat_id,
            'statut': statut,
            'mois_debut': mois_debut,
            'mois_fin': mois_fin,
        }
    }
    
    return render(request, 'paiements/avances/liste_avances.html', context)


@login_required
def detail_avance(request, avance_id):
    """
    Détail d'une avance de loyer
    """
    avance = get_object_or_404(AvanceLoyer, id=avance_id)
    
    # Récupérer les consommations
    consommations = ConsommationAvance.objects.filter(avance=avance).order_by('-mois_consomme')
    
    # Récupérer l'historique des paiements du contrat
    historique = ServiceGestionAvance.get_historique_paiements_contrat(avance.contrat)
    
    # Statistiques de l'avance
    stats = {
        'montant_consomme': avance.montant_avance - avance.montant_restant,
        'pourcentage_consomme': (avance.montant_avance - avance.montant_restant) / avance.montant_avance * 100,
        'nombre_mois_consommes': consommations.count(),
        'montant_par_mois': avance.loyer_mensuel,
    }
    
    context = {
        'avance': avance,
        'consommations': consommations,
        'historique': historique[:12],  # 12 derniers mois
        'stats': stats,
    }
    
    return render(request, 'paiements/avances/detail_avance.html', context)


@login_required
def creer_avance(request):
    """
    Créer une nouvelle avance de loyer
    """
    if request.method == 'POST':
        form = AvanceLoyerForm(request.POST)
        if form.is_valid():
            try:
                # Utiliser le service au lieu du formulaire pour une gestion robuste
                contrat = form.cleaned_data['contrat']
                montant_avance = form.cleaned_data['montant_avance']
                date_avance = form.cleaned_data['date_avance']
                notes = form.cleaned_data.get('notes', '')
                
                # Créer l'avance via le service
                avance = ServiceGestionAvance.creer_avance_loyer(
                    contrat=contrat,
                    montant_avance=montant_avance,
                    date_avance=date_avance,
                    notes=notes
                )
                
                messages.success(request, f"Avance de {avance.montant_avance} F CFA créée avec succès. "
                                        f"Elle couvre {avance.nombre_mois_couverts} mois.")
                return redirect('paiements:detail_avance', avance_id=avance.id)
            except Exception as e:
                messages.error(request, f"Erreur lors de la création de l'avance: {str(e)}")
    else:
        form = AvanceLoyerForm()
    
    context = {
        'form': form,
        'title': 'Créer une avance de loyer'
    }
    
    return render(request, 'paiements/avances/creer_avance.html', context)


@login_required
def paiement_avance(request):
    """
    Interface pour enregistrer un paiement d'avance
    """
    if request.method == 'POST':
        form = PaiementAvanceForm(request.POST)
        if form.is_valid():
            try:
                # Créer le paiement
                paiement = form.save(commit=False)
                paiement.type_paiement = 'avance_loyer'
                paiement.statut = 'valide'
                paiement.save()
                
                # Traiter l'avance automatiquement
                avance = ServiceGestionAvance.traiter_paiement_avance(paiement)
                
                messages.success(request, f"Paiement d'avance de {paiement.montant} F CFA enregistré. "
                                        f"Avance créée couvrant {avance.nombre_mois_couverts} mois.")
                return redirect('paiements:detail_avance', avance_id=avance.id)
            except Exception as e:
                messages.error(request, f"Erreur lors de l'enregistrement du paiement: {str(e)}")
    else:
        form = PaiementAvanceForm()
    
    context = {
        'form': form,
        'title': 'Enregistrer un paiement d\'avance'
    }
    
    return render(request, 'paiements/avances/paiement_avance.html', context)


@login_required
def generer_recu_avance(request, avance_id):
    """Génère un reçu d'avance avec le système KBIS unifié"""
    try:
        avance = get_object_or_404(AvanceLoyer, pk=avance_id)
        
        # Générer le reçu avec le système KBIS unifié
        html_recu = avance.generer_recu_avance_kbis()
        
        if html_recu:
            # Retourner directement le HTML (format A5 prêt pour impression)
            return HttpResponse(html_recu, content_type='text/html')
        else:
            messages.error(request, 'Erreur lors de la génération du reçu d\'avance')
            return redirect('paiements:liste_avances')
            
    except Exception as e:
        messages.error(request, f'Erreur lors de la génération du reçu: {str(e)}')
        return redirect('paiements:liste_avances')


@login_required
def get_contrat_details_ajax(request):
    """
    Récupérer les détails d'un contrat via AJAX (loyer mensuel, etc.)
    """
    if request.method == 'GET':
        try:
            contrat_id = request.GET.get('contrat_id')
            if not contrat_id:
                return JsonResponse({'error': 'ID du contrat requis'}, status=400)
            
            contrat = Contrat.objects.select_related('propriete', 'locataire').get(
                id=contrat_id, 
                est_actif=True, 
                est_resilie=False
            )
            
            return JsonResponse({
                'success': True,
                'loyer_mensuel': float(contrat.loyer_mensuel or 0),
                'charges_mensuelles': float(contrat.charges_mensuelles or 0),
                'depot_garantie': float(contrat.depot_garantie or 0),
                'avance_loyer': float(contrat.avance_loyer or 0),
                'numero_contrat': contrat.numero_contrat,
                'locataire_nom': f"{contrat.locataire.nom} {contrat.locataire.prenom}",
                'propriete_titre': contrat.propriete.titre,
                'date_debut': contrat.date_debut.strftime('%Y-%m-%d') if contrat.date_debut else None,
                'date_fin': contrat.date_fin.strftime('%Y-%m-%d') if contrat.date_fin else None,
            })
            
        except Contrat.DoesNotExist:
            return JsonResponse({'error': 'Contrat non trouvé'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)


@login_required
def calculer_avance_ajax(request):
    """
    Calculer automatiquement les mois d'avance via AJAX
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            montant_avance = Decimal(str(data.get('montant_avance', 0)))
            loyer_mensuel = Decimal(str(data.get('loyer_mensuel', 0)))
            
            if loyer_mensuel <= 0:
                return JsonResponse({'error': 'Loyer mensuel invalide'}, status=400)
            
            # Calculer les mois
            mois_complets = int(montant_avance // loyer_mensuel)
            reste = montant_avance % loyer_mensuel
            
            return JsonResponse({
                'mois_complets': mois_complets,
                'reste': float(reste),
                'montant_par_mois': float(loyer_mensuel),
                'montant_total': float(montant_avance)
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)


@login_required
def historique_paiements_contrat(request, contrat_id):
    """
    Historique détaillé des paiements pour un contrat
    """
    contrat = get_object_or_404(Contrat, id=contrat_id)
    
    # Filtres de date
    mois_debut = request.GET.get('mois_debut')
    mois_fin = request.GET.get('mois_fin')
    
    if mois_debut:
        try:
            mois_debut_date = datetime.strptime(mois_debut, '%Y-%m').date()
        except ValueError:
            mois_debut_date = None
    else:
        mois_debut_date = date.today().replace(day=1) - relativedelta(months=12)
    
    if mois_fin:
        try:
            mois_fin_date = datetime.strptime(mois_fin, '%Y-%m').date()
        except ValueError:
            mois_fin_date = None
    else:
        mois_fin_date = date.today().replace(day=1)
    
    # Récupérer l'historique
    historique = ServiceGestionAvance.get_historique_paiements_contrat(
        contrat, mois_debut_date, mois_fin_date
    )
    
    # Statistiques
    stats = {
        'total_mois': historique.count(),
        'mois_regles': historique.filter(mois_regle=True).count(),
        'mois_en_attente': historique.filter(mois_regle=False).count(),
        'montant_total_paye': historique.aggregate(total=Sum('montant_paye'))['total'] or 0,
        'montant_total_du': historique.aggregate(total=Sum('montant_du'))['total'] or 0,
        'montant_avance_utilisee': historique.aggregate(total=Sum('montant_avance_utilisee'))['total'] or 0,
    }
    
    # Statut des avances
    statut_avances = ServiceGestionAvance.get_statut_avances_contrat(contrat)
    
    context = {
        'contrat': contrat,
        'historique': historique,
        'stats': stats,
        'statut_avances': statut_avances,
        'filters': {
            'mois_debut': mois_debut,
            'mois_fin': mois_fin,
        }
    }
    
    return render(request, 'paiements/avances/historique_contrat.html', context)


@login_required
def generer_rapport_avances_pdf(request, contrat_id):
    """
    Génère un rapport PDF des avances pour un contrat
    """
    contrat = get_object_or_404(Contrat, id=contrat_id)
    
    # Paramètres de période
    mois_debut = request.GET.get('mois_debut')
    mois_fin = request.GET.get('mois_fin')
    
    if mois_debut:
        try:
            mois_debut_date = datetime.strptime(mois_debut, '%Y-%m').date()
        except ValueError:
            mois_debut_date = None
    else:
        mois_debut_date = date.today().replace(day=1) - relativedelta(months=12)
    
    if mois_fin:
        try:
            mois_fin_date = datetime.strptime(mois_fin, '%Y-%m').date()
        except ValueError:
            mois_fin_date = None
    else:
        mois_fin_date = date.today().replace(day=1)
    
    # Générer le rapport
    rapport = ServiceGestionAvance.generer_rapport_avances_contrat(
        contrat, mois_debut_date, mois_fin_date
    )
    
    # Générer le PDF
    pdf_content = generate_historique_pdf(rapport)
    
    # Retourner le PDF
    response = HttpResponse(pdf_content, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="rapport_avances_{contrat.id}_{date.today().strftime("%Y%m%d")}.pdf"'
    
    return response
