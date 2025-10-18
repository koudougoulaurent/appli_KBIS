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
    
    # *** NOUVELLES DONNÉES DÉTAILLÉES ***
    # Les imports sont déjà en haut du fichier
    
    # Récupérer la liste des mois couverts avec leur statut
    mois_couverts_liste = avance.get_mois_couverts_liste()
    mois_actuel = date.today().replace(day=1)
    
    # Analyser chaque mois couvert
    mois_detaille = []
    mois_consommes = 0
    mois_en_cours = None
    mois_futurs = 0
    
    for mois in mois_couverts_liste:
        est_consomme = avance.est_mois_consomme(mois)
        # Comparer les mois normalisés (1er du mois)
        mois_normalise = mois.replace(day=1)
        est_actuel = mois_normalise == mois_actuel
        est_passe = mois_normalise < mois_actuel
        
        # *** LOGIQUE CORRIGÉE : Un mois n'est consommé que s'il y a un enregistrement ***
        if est_consomme:
            # Il y a un enregistrement de consommation pour ce mois
            mois_consommes += 1
            statut = 'consomme'
            statut_label = 'Consommé'
            statut_class = 'danger'  # Rouge pour "Consommé"
        elif est_actuel:
            # Mois actuel : toujours "en cours" s'il n'est pas encore consommé
            mois_en_cours = mois
            statut = 'en_cours'
            statut_label = 'En cours'
            statut_class = 'warning'  # Jaune pour "En cours"
        elif est_passe:
            # Mois passé mais pas encore consommé = en attente
            statut = 'en_attente'
            statut_label = 'En attente'
            statut_class = 'secondary'  # Gris pour "En attente"
        else:
            # Mois futur
            statut = 'futur'
            statut_label = 'En attente'
            statut_class = 'secondary'  # Gris pour "En attente"
        
        mois_detaille.append({
            'mois': mois,
            'mois_formate': mois.strftime('%B %Y'),
            'mois_formate_fr': avance._convertir_mois_francais(mois.strftime('%B %Y')),  # pylint: disable=protected-access
            'est_consomme': est_consomme,
            'est_actuel': est_actuel,
            'est_passe': est_passe,
            'statut': statut,
            'statut_label': statut_label,
            'statut_class': statut_class
        })
    
    # Calculer la date de fin estimée
    date_fin_estimee = None
    if avance.mois_fin_couverture:
        date_fin_estimee = avance.mois_fin_couverture
    
    # Calculer le prochain mois de paiement après l'avance
    prochain_mois_paiement = None
    if avance.mois_fin_couverture:
        prochain_mois_paiement = avance.mois_fin_couverture + relativedelta(months=1)
    
    # Statistiques enrichies
    stats_enrichies = {
        **stats,
        'mois_consommes': mois_consommes,
        'mois_en_cours': mois_en_cours,
        'mois_futurs': mois_futurs,
        'mois_total': len(mois_couverts_liste),
        'date_debut_couverture': avance.mois_debut_couverture,
        'date_fin_couverture': avance.mois_fin_couverture,
        'date_fin_estimee': date_fin_estimee,
        'prochain_mois_paiement': prochain_mois_paiement,
        'pourcentage_mois_consommes': (mois_consommes / len(mois_couverts_liste) * 100) if mois_couverts_liste else 0,
    }
    
    context = {
        'avance': avance,
        'consommations': consommations,
        'historique': historique[:12],  # 12 derniers mois
        'stats': stats_enrichies,
        'mois_detaille': mois_detaille,
        'mois_actuel': mois_actuel,
    }
    
    return render(request, 'paiements/avances/detail_avance.html', context)


@login_required
def creer_avance(request):
    """
    Créer une nouvelle avance de loyer avec vérification des avances existantes
    """
    if request.method == 'POST':
        print("=== SOUMISSION FORMULAIRE ===")
        print("POST data:", request.POST)
        print("User:", request.user)
        
        form = AvanceLoyerForm(request.POST)
        print("Form valid:", form.is_valid())
        if not form.is_valid():
            print("Form errors:", form.errors)
            # Messages d'erreur clairs pour chaque champ
            for field, errors in form.errors.items():
                for error in errors:
                    if field == 'contrat':
                        messages.error(request, "❌ Contrat : Veuillez sélectionner un contrat valide.")
                    elif field == 'montant_avance':
                        messages.error(request, "❌ Montant : Le montant doit être un nombre positif.")
                    elif field == 'date_avance':
                        messages.error(request, "❌ Date : Veuillez sélectionner une date valide.")
                    elif field == 'notes':
                        messages.error(request, f"❌ Notes : {error}")
                    else:
                        messages.error(request, f"❌ {field} : {error}")
        
        if form.is_valid():
            try:
                # Utiliser le service au lieu du formulaire pour une gestion robuste
                contrat = form.cleaned_data['contrat']
                montant_avance = form.cleaned_data['montant_avance']
                date_avance = form.cleaned_data['date_avance']
                notes = form.cleaned_data.get('notes', '')
                
                # Récupérer les paramètres depuis la requête POST
                mode_selection = request.POST.get('mode_selection_mois', 'automatique')
                mois_couverts_manuels = request.POST.get('mois_couverts_manuels', '[]')
                
                print(f"Mode sélection: {mode_selection}")
                print(f"Mois couverts manuels: {mois_couverts_manuels}")
                
                # *** NOUVELLE LOGIQUE : Gestion des mois sélectionnés manuellement ***
                mois_effet_personnalise = None
                if mode_selection == 'manuel' and mois_couverts_manuels:
                    try:
                        import json
                        mois_liste = json.loads(mois_couverts_manuels)
                        if mois_liste:
                            # Utiliser le premier mois sélectionné comme mois d'effet
                            from datetime import datetime
                            mois_effet_personnalise = datetime.strptime(mois_liste[0], '%Y-%m-%d').date()
                    except (json.JSONDecodeError, ValueError):
                        pass
                
                # *** NOUVELLE LOGIQUE : Parser les mois sélectionnés manuellement ***
                mois_couverts_liste = []
                if mode_selection == 'manuel' and mois_couverts_manuels:
                    try:
                        import json
                        mois_couverts_liste = json.loads(mois_couverts_manuels)
                    except (json.JSONDecodeError, ValueError):
                        pass
                
                # Créer l'avance via le service avec tous les paramètres
                avance = ServiceGestionAvance.creer_avance_loyer(
                    contrat=contrat,
                    montant_avance=montant_avance,
                    date_avance=date_avance,
                    notes=notes,
                    mois_effet_personnalise=mois_effet_personnalise,
                    mode_selection_mois=mode_selection,
                    mois_couverts_manuels=mois_couverts_liste
                )
                
                # *** CRITIQUE : Créer automatiquement le paiement correspondant ***
                from .models import Paiement
                from .id_generator import IDGenerator
                
                # Générer un numéro de paiement unique
                numero_paiement = IDGenerator.generate_id('paiement', date_paiement=date_avance)
                
                # Créer le paiement d'avance
                paiement = Paiement.objects.create(
                    contrat=contrat,
                    montant=montant_avance,
                    date_paiement=date_avance,
                    type_paiement='avance_loyer',
                    statut='valide',
                    numero_paiement=numero_paiement,
                    notes=f"Paiement d'avance automatique - {avance.nombre_mois_couverts} mois couverts",
                    created_by=request.user
                )
                
                # Lier l'avance au paiement
                avance.paiement = paiement
                avance.save()
                
                messages.success(request, f"✅ Avance de {avance.montant_avance:,.0f} F CFA créée et intégrée au système de paiement ! "
                                        f"Elle couvre {avance.nombre_mois_couverts} mois de loyer.")
                return redirect('paiements:detail_avance', avance_id=avance.id)
            except Exception as e:
                print(f"Erreur lors de la création de l'avance: {e}")
                import traceback
                traceback.print_exc()
                
                # Messages d'erreur plus clairs selon le type d'erreur
                if "contrat" in str(e).lower():
                    messages.error(request, "❌ Erreur de contrat : Le contrat sélectionné n'est pas valide.")
                elif "montant" in str(e).lower():
                    messages.error(request, "❌ Erreur de montant : Le montant saisi n'est pas valide.")
                elif "date" in str(e).lower():
                    messages.error(request, "❌ Erreur de date : La date sélectionnée n'est pas valide.")
                else:
                    messages.error(request, f"❌ Erreur inattendue : {str(e)}")
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
    """Génère un récépissé d'avance avec le système A5 unifié"""
    try:
        # Récupérer le paiement d'avance correspondant
        from .models import Paiement
        
        # Essayer d'abord avec type_paiement='avance'
        try:
            paiement_avance = Paiement.objects.get(pk=avance_id, type_paiement='avance')
        except Paiement.DoesNotExist:
            # Si pas trouvé, essayer avec type_paiement='avance_loyer'
            try:
                paiement_avance = Paiement.objects.get(pk=avance_id, type_paiement='avance_loyer')
            except Paiement.DoesNotExist:
                # Si toujours pas trouvé, chercher n'importe quel paiement avec cet ID
                try:
                    paiement_avance = Paiement.objects.get(pk=avance_id)
                except Paiement.DoesNotExist:
                    messages.error(request, f'Aucun paiement trouvé avec l\'ID {avance_id}')
                    return redirect('paiements:liste')
        
        # Utiliser le nouveau système A5 unifié
        from .services_document_unifie_complet import DocumentUnifieA5ServiceComplet
        
        service = DocumentUnifieA5ServiceComplet()
        html_content = service.generer_document_unifie('paiement_avance', paiement_id=paiement_avance.id)
        
        return HttpResponse(html_content, content_type='text/html')
            
    except Exception as e:
        messages.error(request, f'Erreur lors de la génération du récépissé: {str(e)}')
        return redirect('paiements:liste')


def get_contrat_details_ajax(request):
    """
    Récupérer les détails d'un contrat via AJAX (loyer mensuel, etc.)
    """
    # Vérifier l'authentification manuellement
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentification requise'}, status=401)
    
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
            
            # *** NOUVELLE FONCTIONNALITÉ : Vérifier les avances existantes ***
            avances_info = {'has_avances': False, 'message': None, 'avances': []}
            try:
                avances_info = ServiceGestionAvance.verifier_avances_existantes(contrat)
            except Exception as e:
                print(f"Erreur lors de la vérification des avances: {e}")
                # En cas d'erreur, on continue sans les informations d'avances
            
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
                # *** NOUVELLES DONNÉES : Informations sur les avances existantes ***
                'avances_existantes': avances_info
            })
            
        except Contrat.DoesNotExist:
            return JsonResponse({'error': 'Contrat non trouvé'}, status=404)
        except Exception as e:
            print(f"Erreur dans get_contrat_details_ajax: {e}")
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
def get_suggestions_mois_ajax(request):
    """
    Récupérer les suggestions de mois couverts via AJAX
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            contrat_id = data.get('contrat_id')
            montant_avance = Decimal(str(data.get('montant_avance', 0)))
            loyer_mensuel = Decimal(str(data.get('loyer_mensuel', 0)))
            
            if not contrat_id:
                return JsonResponse({'error': 'ID du contrat requis'}, status=400)
            
            if loyer_mensuel <= 0:
                return JsonResponse({'error': 'Loyer mensuel invalide'}, status=400)
            
            contrat = Contrat.objects.get(id=contrat_id)
            
            # *** NOUVELLE FONCTIONNALITÉ : Obtenir les suggestions de mois ***
            suggestions_info = ServiceGestionAvance.get_suggestions_mois_couverts(
                contrat, montant_avance, loyer_mensuel
            )
            
            return JsonResponse({
                'success': True,
                'suggestions': suggestions_info['suggestions'],
                'mois_complets_possibles': suggestions_info['mois_complets_possibles'],
                'montant_par_mois': suggestions_info['montant_par_mois'],
                'montant_total': suggestions_info['montant_total']
            })
            
        except Contrat.DoesNotExist:
            return JsonResponse({'error': 'Contrat non trouvé'}, status=404)
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
