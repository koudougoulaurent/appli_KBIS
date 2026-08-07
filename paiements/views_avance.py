from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse, Http404
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
    """Dashboard principal des avances de loyer - OPTIMISÉ"""
    try:
        # *** CONSOMMATION AUTOMATIQUE AVEC CACHE ***
        from .services_optimisation_avances import ServiceOptimisationAvances
        # Consommer avec cache pour éviter les appels répétés
        ServiceOptimisationAvances.consommer_avances_avec_cache(force=False)
        
        # Statistiques optimisées en une seule requête
        context = ServiceOptimisationAvances.get_dashboard_stats_optimisees()
        
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
    Liste des avances de loyer - OPTIMISÉ avec filtres en base de données
    """
    # *** CONSOMMATION AUTOMATIQUE AVEC CACHE ***
    from .services_optimisation_avances import ServiceOptimisationAvances
    ServiceOptimisationAvances.consommer_avances_avec_cache(force=False)
    
    # Récupérer les filtres depuis la requête
    contrat_id = request.GET.get('contrat')
    statut = request.GET.get('statut')
    mois_debut = request.GET.get('mois_debut')
    mois_fin = request.GET.get('mois_fin')
    
    # Préparer les filtres pour la base de données
    filters = {}
    if contrat_id:
        try:
            filters['contrat_id'] = int(contrat_id)
        except ValueError:
            pass  # Ignorer si ce n'est pas un ID valide
    
    if statut:
        filters['statut'] = statut
    
    if mois_debut:
        try:
            filters['mois_debut'] = datetime.strptime(mois_debut, '%Y-%m').date()
        except ValueError:
            pass
    
    if mois_fin:
        try:
            filters['mois_fin'] = datetime.strptime(mois_fin, '%Y-%m').date()
        except ValueError:
            pass
    
    # Récupérer les avances optimisées avec filtres en base de données
    avances_queryset = ServiceOptimisationAvances.get_avances_optimisees(
        filters=filters,
        prefetch_consommations=True
    )
    
    # Si filtre par nom de contrat (pas ID), appliquer après récupération
    if contrat_id and not filters.get('contrat_id'):
        # Filtrer par nom de locataire (moins optimal mais nécessaire)
        avances_queryset = avances_queryset.filter(
            contrat__locataire__nom__icontains=contrat_id
        ) | avances_queryset.filter(
            contrat__locataire__prenom__icontains=contrat_id
        )
    
    # Convertir en format compatible avec le template (seulement les avances nécessaires)
    avances = []
    for avance in avances_queryset:
        # Déterminer l'URL de détail appropriée
        detail_url = None
        if avance.paiement:
            detail_url = f"/paiements/avances/paiement/{avance.paiement.id}/"
        else:
            detail_url = f"/paiements/avances/detail/{avance.id}/"
        
        avance_data = {
            'id': avance.id,
            'contrat': avance.contrat,
            'montant_avance': float(avance.montant_avance),
            'montant_restant': float(avance.montant_restant),
            'nombre_mois_couverts': avance.nombre_mois_couverts,
            'date_avance': avance.date_avance,
            'statut': avance.statut,
            'notes': avance.notes or '',
            'created_at': avance.created_at,
            'updated_at': avance.updated_at,
            'mois_debut_couverture': avance.mois_debut_couverture,
            'mois_fin_couverture': avance.mois_fin_couverture,
            'loyer_mensuel': float(avance.contrat.loyer_mensuel),
            'detail_url': detail_url,
        }
        avances.append(avance_data)
    
    # Pagination (maintenant sur la liste Python, mais beaucoup plus petite)
    from django.core.paginator import Paginator
    paginator = Paginator(avances, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistiques optimisées en base de données
    stats = ServiceOptimisationAvances.calculer_stats_avances_optimisees(filters=filters)
    
    # Contrats pour le filtre (optimisé)
    contrats = Contrat.objects.filter(est_actif=True).select_related('locataire', 'propriete').only(
        'id', 'numero_contrat', 'locataire__nom', 'locataire__prenom', 'propriete__titre'
    )
    
    context = {
        'avances': page_obj,
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
    Détail d'une avance de loyer - OPTIMISÉ avec préchargement des relations
    """
    # Récupérer l'avance avec toutes les relations préchargées
    from .services_optimisation_avances import ServiceOptimisationAvances
    from .services_consommation_dynamique import ServiceConsommationDynamique
    
    try:
        avance = ServiceOptimisationAvances.get_avance_detail_optimisee(avance_id)
    except AvanceLoyer.DoesNotExist:
        # Si l'avance n'existe pas, essayer de la synchroniser depuis le paiement
        from .services_synchronisation_avances import ServiceSynchronisationAvances
        from .models import Paiement
        
        try:
            paiement = Paiement.objects.select_related('contrat').get(id=avance_id, type_paiement='avance')
            avance = ServiceSynchronisationAvances.synchroniser_avance_avec_paiement(paiement)
            if not avance:
                raise Http404("Avance non trouvée et impossible à synchroniser")
        except Paiement.DoesNotExist:
            raise Http404("Avance non trouvée")
    
    if not avance:
        raise Http404("Avance non trouvée")
    
    # *** CONSOMMATION AVEC CACHE ***
    ServiceOptimisationAvances.consommer_avances_avec_cache(
        contrat_id=avance.contrat_id,
        force=False
    )
    
    # Synchroniser avec les paiements de loyer
    consommations_ajoutees = ServiceConsommationDynamique.synchroniser_avec_paiements(avance)
    
    # Recalculer la progression dynamique
    progression = ServiceConsommationDynamique.calculer_progression_avance(avance)
    
    # Récupérer les consommations (déjà préchargées dans avance.consommations)
    consommations = list(avance.consommations.all()) if hasattr(avance, 'consommations') else []
    if not consommations:
        # Fallback si pas préchargé
        consommations = ConsommationAvance.objects.filter(avance=avance).select_related('paiement').order_by('-mois_consomme')
    
    # Récupérer l'historique optimisé
    historique = ServiceOptimisationAvances.get_historique_paiements_optimise(avance.contrat_id, limit=12)
    
    # Statistiques dynamiques de l'avance
    stats = {
        'montant_consomme': progression['montant_consomme'],
        'pourcentage_consomme': progression['pourcentage_montant'],
        'nombre_mois_consommes': progression['mois_consommes'],
        'montant_par_mois': avance.loyer_mensuel,
        'progression': progression,
    }
    
    # *** NOUVELLES DONNÉES DÉTAILLÉES ***
    # Les imports sont déjà en haut du fichier
    
    # *** SYNCHRONISATION DES AVANCES MULTIPLES ***
    from .services_synchronisation_avances import ServiceSynchronisationAvances
    
    # Synchroniser toutes les avances du contrat
    sync_result = ServiceSynchronisationAvances.synchroniser_toutes_avances_contrat(avance.contrat)
    
    # Récupérer TOUTES les avances du contrat pour la timeline complète
    avances_contrat = AvanceLoyer.objects.filter(contrat=avance.contrat, statut='active').order_by('date_avance')
    
    # Construire la timeline complète de toutes les avances
    mois_couverts_complets = []
    for avance_contrat in avances_contrat:
        mois_avance = avance_contrat.get_mois_couverts_liste()
        mois_couverts_complets.extend(mois_avance)
    
    # Supprimer les doublons et trier
    mois_couverts_liste = sorted(list(set(mois_couverts_complets)))
    mois_actuel = date.today().replace(day=1)
    
    # Analyser chaque mois couvert avec la progression dynamique
    mois_detaille = []
    mois_consommes = progression['mois_consommes']
    mois_en_cours = None
    mois_futurs = progression['mois_restants']
    
    for mois in mois_couverts_liste:
        est_consomme = avance.est_mois_consomme(mois)
        # Comparer les mois normalisés (1er du mois)
        mois_normalise = mois.replace(day=1)
        est_actuel = mois_normalise == mois_actuel
        est_passe = mois_normalise < mois_actuel
        
        # *** LOGIQUE DYNAMIQUE : Statut basé sur la progression réelle ***
        if est_consomme:
            # Il y a un enregistrement de consommation pour ce mois
            statut = 'consomme'
            statut_label = 'Consommé'
            statut_class = 'success'  # Vert pour "Consommé" (positif)
        elif est_actuel:
            # Mois actuel : "en cours" s'il n'est pas encore consommé
            mois_en_cours = mois
            statut = 'en_cours'
            statut_label = 'En cours'
            statut_class = 'warning'  # Jaune pour "En cours"
        elif est_passe:
            # Mois passé mais pas encore consommé = automatiquement consommé
            statut = 'auto_consomme'
            statut_label = 'Auto-consommé'
            statut_class = 'info'  # Bleu pour "Auto-consommé"
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
    
    # Statistiques enrichies avec progression dynamique
    stats_enrichies = {
        **stats,
        'mois_consommes': progression['mois_consommes'],
        'mois_en_cours': mois_en_cours,
        'mois_futurs': progression['mois_restants'],
        'mois_total': progression['total_mois'],
        'date_debut_couverture': avance.mois_debut_couverture,
        'date_fin_couverture': avance.mois_fin_couverture,
        'date_fin_estimee': date_fin_estimee,
        'prochain_mois_paiement': prochain_mois_paiement,
        'pourcentage_mois_consommes': progression['pourcentage_mois'],
        'statut_avance': progression['statut'],
        'statut_label': progression['statut_label'],
        'prochaine_consommation': progression['prochaine_consommation'],
        'consommations_ajoutees': consommations_ajoutees,
    }
    
    # *** STATISTIQUES DES AVANCES MULTIPLES ***
    stats_avances_multiples = {
        'total_avances': avances_contrat.count(),
        'total_mois_couverts': sync_result.get('total_mois', 0),
        'total_montant_avances': sync_result.get('total_montant', 0),
        'avances_sync': sync_result.get('avances_sync', 0),
        'est_prolongation': avances_contrat.count() > 1,
        'avances_liste': [
            {
                'id': av.id,
                'montant': av.montant_avance,
                'mois_couverts': av.nombre_mois_couverts,
                'montant_restant': av.montant_restant,
                'date_avance': av.date_avance,
                'est_actuelle': av.id == avance.id
            }
            for av in avances_contrat
        ]
    }
    
    context = {
        'avance': avance,
        'consommations': consommations,
        'historique': historique[:12],  # 12 derniers mois
        'stats': stats_enrichies,
        'mois_detaille': mois_detaille,
        'mois_actuel': mois_actuel,
        'avances_multiples': stats_avances_multiples,
    }
    
    return render(request, 'paiements/avances/detail_avance.html', context)


@login_required
def api_progression_avance(request, avance_id):
    """
    API pour récupérer la progression dynamique d'une avance
    """
    try:
        avance = AvanceLoyer.objects.get(id=avance_id)
        from .services_consommation_dynamique import ServiceConsommationDynamique
        
        # Consommer automatiquement et calculer la progression
        ServiceConsommationDynamique.consommer_avances_automatiquement(avance.contrat)
        progression = ServiceConsommationDynamique.calculer_progression_avance(avance)
        
        return JsonResponse({
            'success': True,
            'progression': progression,
            'timestamp': timezone.now().isoformat()
        })
        
    except AvanceLoyer.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Avance non trouvée'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
def api_consommer_auto(request):
    """
    API pour consommer automatiquement toutes les avances
    """
    try:
        from .services_consommation_dynamique import ServiceConsommationDynamique
        
        contrat_id = request.GET.get('contrat_id')
        if contrat_id:
            resultat = ServiceConsommationDynamique.consommer_avances_automatiquement(int(contrat_id))
        else:
            resultat = ServiceConsommationDynamique.consommer_avances_automatiquement()
        
        return JsonResponse({
            'success': True,
            'resultat': resultat,
            'timestamp': timezone.now().isoformat()
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
def detail_avance_paiement(request, paiement_id):
    """
    Détail d'une avance via l'ID du paiement - Pour compatibilité avec les liens existants
    """
    from .models import Paiement
    from .services_synchronisation_avances import ServiceSynchronisationAvances
    
    # Récupérer le paiement d'avance
    paiement = get_object_or_404(Paiement, id=paiement_id, type_paiement='avance')
    
    # Synchroniser l'avance si nécessaire
    avance = ServiceSynchronisationAvances.synchroniser_avance_avec_paiement(paiement)
    
    if not avance:
        messages.error(request, "Impossible de synchroniser l'avance avec le paiement.")
        return redirect('paiements:avances:liste_avances')
    
    # Rediriger vers la vue de détail normale
    return redirect('paiements:avances:detail_avance', avance_id=avance.id)


@login_required
def creer_avance(request):
    """
    Créer une nouvelle avance de loyer avec vérification des avances existantes
    IMPORTANT : Consomme automatiquement les avances du contrat concerné avant de créer une nouvelle
    """
    # NOTE : La consommation automatique sera faite pour le contrat spécifique lors de la soumission du formulaire
    # Ne pas consommer toutes les avances ici pour éviter les timeouts
    
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
                        messages.error(request, "ERREUR - Contrat : Veuillez sélectionner un contrat valide.")
                    elif field == 'montant_avance':
                        messages.error(request, "ERREUR - Montant : Le montant doit être un nombre positif.")
                    elif field == 'date_avance':
                        messages.error(request, "ERREUR - Date : Veuillez sélectionner une date valide.")
                    elif field == 'notes':
                        messages.error(request, f"ERREUR - Notes : {error}")
                    else:
                        messages.error(request, f"ERREUR - {field} : {error}")
        
        if form.is_valid():
            try:
                # Utiliser le service au lieu du formulaire pour une gestion robuste
                contrat = form.cleaned_data['contrat']
                
                # *** CONSOMMATION AUTOMATIQUE PRIORITAIRE POUR CE CONTRAT ***
                from .services_consommation_dynamique import ServiceConsommationDynamique
                # Consommer automatiquement toutes les avances du contrat pour les mois écoulés
                ServiceConsommationDynamique.consommer_avances_automatiquement(contrat)
                
                montant_avance = form.cleaned_data['montant_avance']
                date_avance = form.cleaned_data['date_avance']
                notes = form.cleaned_data.get('notes', '')
                
                # Récupérer les paramètres depuis la requête POST
                mode_selection = request.POST.get('mode_selection_mois', 'automatique')
                mois_couverts_manuels = request.POST.get('mois_couverts_manuels', '[]')
                
                print(f"Mode sélection: {mode_selection}")
                print(f"Mois couverts manuels: {mois_couverts_manuels}")
                
                # *** VÉRIFICATION DES AVANCES EXISTANTES ***
                try:
                    avance_existante = form.verifier_avance_existante(contrat)
                    if avance_existante:
                        # Ajouter une note de prolongation
                        if not notes:
                            notes = f"[PROLONGATION] - Avance supplémentaire ajoutée à l'avance existante #{avance_existante.id}"
                        else:
                            notes += f"\n\n[PROLONGATION] - Avance supplémentaire ajoutée à l'avance existante #{avance_existante.id}"
                except Exception as e:
                    print(f"Erreur lors de la vérification des avances existantes: {e}")
                    # Continuer sans vérification si erreur
                
                # *** CALCULS AUTOMATIQUES ***
                try:
                    nombre_mois_couverts, montant_reste = form.calculer_mois_et_reste(contrat, montant_avance)
                except Exception as e:
                    print(f"Erreur lors du calcul des mois et reste: {e}")
                    # Utiliser des valeurs par défaut
                    nombre_mois_couverts = 0
                    montant_reste = montant_avance
                
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
                
                # *** NOUVELLE LOGIQUE : Utiliser le service avec logique unique ***
                from .services_logique_avance_unique import ServiceLogiqueAvanceUnique
                
                try:
                    # Si mode manuel et mois spécifiques sélectionnés, utiliser l'ancien service
                    # Sinon, utiliser la LOGIQUE UNIQUE (recommandé)
                    if mode_selection == 'manuel' and mois_couverts_liste and mois_effet_personnalise:
                        # Mode manuel : utiliser l'ancien service avec mois personnalisé
                        avance = ServiceGestionAvance.creer_avance_loyer(
                            contrat=contrat,
                            montant_avance=montant_avance,
                            date_avance=date_avance,
                            notes=notes,
                            mois_effet_personnalise=mois_effet_personnalise,
                            mode_selection_mois=mode_selection,
                            mois_couverts_manuels=mois_couverts_liste
                        )
                    else:
                        # Mode automatique : utiliser la LOGIQUE UNIQUE
                        avance = ServiceLogiqueAvanceUnique.creer_avance_avec_logique_unique(
                            contrat=contrat,
                            montant_avance=montant_avance,
                            date_avance=date_avance,
                            notes=notes if notes else f"Avance créée le {date_avance}"
                        )
                except ValueError as e:
                    # Erreur de validation métier (mois manquants, etc.) - afficher le message complet
                    error_message = str(e)
                    # Remplacer \n par <br> pour l'affichage HTML
                    from django.utils.safestring import mark_safe
                    messages.error(request, mark_safe(error_message.replace('\n', '<br>')))
                    return render(request, 'paiements/avances/creer_avance_manuel.html', {
                        'form': form,
                        'contrats': Contrat.objects.filter(est_actif=True, est_resilie=False).select_related('locataire', 'propriete'),
                    })
                except Exception as e:
                    print(f"Erreur lors de la création de l'avance: {e}")
                    import traceback
                    traceback.print_exc()
                    messages.error(request, f"Erreur lors de la création de l'avance: {str(e)}")
                    return render(request, 'paiements/avances/creer_avance_manuel.html', {
                        'form': form,
                        'contrats': Contrat.objects.filter(est_actif=True, est_resilie=False).select_related('locataire', 'propriete'),
                    })
                
                # *** CRITIQUE : Créer automatiquement le paiement correspondant ***
                from .models import Paiement
                from core.id_generator import IDGenerator
                from .validators import ValidateurPaiementUnique
                
                # *** NOUVELLE VALIDATION (V9) : Vérifier les doublons ***
                est_valide, message_erreur = ValidateurPaiementUnique.valider_unicite_paiement(
                    contrat=contrat,
                    type_paiement='avance',
                    date_paiement=date_avance
                )
                
                if not est_valide:
                    messages.error(request, message_erreur)
                    return render(request, 'paiements/avances/creer_avance_manuel.html', {
                        'form': form,
                        'contrats': Contrat.objects.filter(est_actif=True, est_resilie=False).select_related('locataire', 'propriete'),
                    })
                
                # Générer un numéro de paiement unique
                numero_paiement = IDGenerator.generate_id('paiement', date_paiement=date_avance)

                # *** CORRECTION : Enregistrer le DERNIER MOIS COUVERT dans mois_paye ***
                # Sans cela, le paiement d'avance ne gardait aucune trace des mois
                # couverts : une fois l'avance épuisée, le système "oubliait" la
                # couverture et revenait au mois présent.
                mois_fr_noms = {
                    1: 'Janvier', 2: 'Février', 3: 'Mars', 4: 'Avril',
                    5: 'Mai', 6: 'Juin', 7: 'Juillet', 8: 'Août',
                    9: 'Septembre', 10: 'Octobre', 11: 'Novembre', 12: 'Décembre'
                }
                mois_reference_avance = avance.mois_fin_couverture or avance.mois_debut_couverture
                mois_paye_avance = ''
                if mois_reference_avance:
                    mois_paye_avance = f"{mois_fr_noms[mois_reference_avance.month]} {mois_reference_avance.year}"

                # Créer le paiement d'avance (EN ATTENTE - validation manuelle requise)
                paiement = Paiement.objects.create(
                    contrat=contrat,
                    montant=montant_avance,
                    date_paiement=date_avance,
                    type_paiement='avance',
                    statut='en_attente',  # ← CORRIGÉ : Validation manuelle requise
                    numero_paiement=numero_paiement,
                    mois_paye=mois_paye_avance,
                    notes=f"Paiement d'avance créé automatiquement - {avance.nombre_mois_couverts} mois couverts - VALIDATION REQUISE"
                )
                
                # Lier l'avance au paiement
                avance.paiement = paiement
                avance.save()
                
                # *** SYNCHRONISATION DES AVANCES MULTIPLES ***
                from .services_synchronisation_avances import ServiceSynchronisationAvances
                
                # Synchroniser toutes les avances du contrat pour calculer les totaux
                ServiceSynchronisationAvances.synchroniser_toutes_avances_contrat(contrat)
                
                # *** RE-EXÉCUTER CONSOMMATION APRÈS CRÉATION pour avoir les données à jour ***
                ServiceConsommationDynamique.consommer_avances_automatiquement(contrat)
                
                # Récupérer les statistiques globales des avances du contrat (recharger après consommation)
                avances_contrat = list(AvanceLoyer.objects.filter(
                    contrat=contrat, 
                    statut='active',
                    montant_restant__gt=0  # Seulement celles qui ont encore de l'argent
                ))
                total_mois_couverts = sum(avance.nombre_mois_couverts for avance in avances_contrat)
                total_montant_restant = sum(avance.montant_restant for avance in avances_contrat)
                
                # Message de confirmation détaillé
                # CORRECTION : avances_contrat est une liste → len(), pas .count()
                # (.count() sans argument levait TypeError après CHAQUE création :
                # l'avance était créée mais l'utilisateur voyait une erreur)
                if len(avances_contrat) > 1:
                    messages.success(request,
                        f"SUCCES - AVANCE DE PROLONGATION CREE AVEC SUCCES !\n\n"
                        f"Montant : {avance.montant_avance:,.0f} F CFA\n"
                        f"Mois couverts par cette avance : {avance.nombre_mois_couverts}\n"
                        f"TOTAL CONTRAT : {len(avances_contrat)} avances actives\n"
                        f"TOTAL MOIS COUVERTS : {total_mois_couverts} mois\n"
                        f"MONTANT RESTANT TOTAL : {total_montant_restant:,.0f} F CFA\n\n"
                        f"Synchronisation automatique effectuee !"
                    )
                else:
                    messages.success(request, 
                        f"SUCCES - AVANCE CREE AVEC SUCCES !\n\n"
                        f"Montant : {avance.montant_avance:,.0f} F CFA\n"
                        f"Mois couverts : {avance.nombre_mois_couverts}\n"
                        f"Integree au systeme de paiement !"
                    )
                
                return redirect('paiements:avances:detail_avance', avance_id=avance.id)
            except Exception as e:
                print(f"Erreur lors de la création de l'avance: {e}")
                import traceback
                traceback.print_exc()
                
                # Messages d'erreur plus clairs selon le type d'erreur
                if "contrat" in str(e).lower():
                    messages.error(request, "ERREUR - Contrat : Le contrat selectionne n'est pas valide.")
                elif "montant" in str(e).lower():
                    messages.error(request, "ERREUR - Montant : Le montant saisi n'est pas valide.")
                elif "date" in str(e).lower():
                    messages.error(request, "ERREUR - Date : La date selectionnee n'est pas valide.")
                else:
                    messages.error(request, f"ERREUR - Erreur inattendue : {str(e)}")
    else:
        form = AvanceLoyerForm()
    
    # NOTE : Ne pas consommer toutes les avances ici pour éviter les timeouts
    # La consommation sera faite dynamiquement via AJAX quand un contrat est sélectionné
    
    context = {
        'form': form,
        'title': 'Créer une avance de loyer'
    }
    
    return render(request, 'paiements/avances/creer_avance_manuel.html', context)


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
                paiement.type_paiement = 'avance'
                paiement.statut = 'valide'
                paiement.save()
                
                # Traiter l'avance automatiquement
                avance = ServiceGestionAvance.traiter_paiement_avance(paiement)
                
                messages.success(request, f"Paiement d'avance de {paiement.montant} F CFA enregistré. "
                                        f"Avance créée couvrant {avance.nombre_mois_couverts} mois.")
                return redirect('paiements:avances:detail_avance', avance_id=avance.id)
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
            # Si pas trouvé, essayer avec type_paiement='avance'
            try:
                paiement_avance = Paiement.objects.get(pk=avance_id, type_paiement='avance')
            except Paiement.DoesNotExist:
                # Si toujours pas trouvé, chercher n'importe quel paiement avec cet ID
                try:
                    paiement_avance = Paiement.objects.get(pk=avance_id)
                except Paiement.DoesNotExist:
                    messages.error(request, f'Aucun paiement trouvé avec l\'ID {avance_id}')
                    return redirect('paiements:liste')
        
        # Utiliser le nouveau système A5 unifié (même que la liste des paiements)
        from .services_document_unifie_complet import DocumentUnifieA5ServiceComplet
        
        service = DocumentUnifieA5ServiceComplet()
        html_content = service.generer_document_unifie('paiement_recu', paiement_id=paiement_avance.id)
        
        return HttpResponse(html_content, content_type='text/html')
            
    except Exception as e:
        messages.error(request, f'Erreur lors de la génération du récépissé: {str(e)}')
        return redirect('paiements:liste')


@login_required
def generer_recu_avance_unifie(request, avance_id):
    """Génère un récépissé d'avance avec le système A5 unifié (nouvelle version)"""
    try:
        # Récupérer l'avance
        from .models_avance import AvanceLoyer
        
        try:
            avance = AvanceLoyer.objects.get(pk=avance_id)
        except AvanceLoyer.DoesNotExist:
            messages.error(request, f'Aucune avance trouvée avec l\'ID {avance_id}')
            return redirect('paiements:avances:liste_avances')
        
        # Récupérer le paiement associé
        if not avance.paiement:
            messages.error(request, f'Aucun paiement associé à l\'avance {avance_id}')
            return redirect('paiements:avances:liste_avances')
        
        # Utiliser le système A5 unifié (même que la liste des paiements)
        from .services_document_unifie_complet import DocumentUnifieA5ServiceComplet
        
        service = DocumentUnifieA5ServiceComplet()
        html_content = service.generer_document_unifie('paiement_recu', paiement_id=avance.paiement.id)
        
        return HttpResponse(html_content, content_type='text/html')
            
    except Exception as e:
        messages.error(request, f'Erreur lors de la génération du récépissé: {str(e)}')
        return redirect('paiements:avances:liste_avances')


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
            
            # *** CALCUL DU PROCHAIN MOIS SUGGÉRÉ (logique unique centralisée) ***
            prochain_mois_suggere = None
            prochain_mois_suggere_formate = None
            try:
                from .services_logique_avance_unique import ServiceLogiqueAvanceUnique
                mois_debut = ServiceLogiqueAvanceUnique.determiner_mois_debut_couverture_nouvelle_avance(contrat)
                prochain_mois_suggere = mois_debut.strftime('%Y-%m-%d')
                # Formatage en français
                mois_fr = {
                    1: 'Janvier', 2: 'Février', 3: 'Mars', 4: 'Avril',
                    5: 'Mai', 6: 'Juin', 7: 'Juillet', 8: 'Août',
                    9: 'Septembre', 10: 'Octobre', 11: 'Novembre', 12: 'Décembre'
                }
                prochain_mois_suggere_formate = f"{mois_fr[mois_debut.month]} {mois_debut.year}"
                prochain_mois_num = mois_debut.month
                prochain_mois_annee = mois_debut.year
            except Exception as e:
                print(f"Erreur lors du calcul du prochain mois suggéré: {e}")
                prochain_mois_num = None
                prochain_mois_annee = None
            
            return JsonResponse({
                'success': True,
                'loyer_mensuel': float(contrat.loyer_mensuel or 0),
                'charges_mensuelles': float(contrat.charges_mensuelles or 0),
                'depot_garantie': float(contrat.depot_garantie or 0),
                'avance': float(contrat.avance_loyer or 0),
                'numero_contrat': contrat.numero_contrat,
                'locataire_nom': f"{contrat.locataire.nom} {contrat.locataire.prenom}",
                'propriete_titre': contrat.propriete.titre,
                'date_debut': contrat.date_debut.strftime('%Y-%m-%d') if contrat.date_debut else None,
                'date_fin': contrat.date_fin.strftime('%Y-%m-%d') if contrat.date_fin else None,
                # *** NOUVELLES DONNÉES : Informations sur les avances existantes ***
                'avances_existantes': avances_info,
                # *** PROCHAIN MOIS SUGGÉRÉ (basé sur paiements ET avances existantes) ***
                'prochain_mois_suggere': prochain_mois_suggere,
                'prochain_mois_suggere_formate': prochain_mois_suggere_formate,
                'prochain_mois_num': prochain_mois_num,
                'prochain_mois_annee': prochain_mois_annee,
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
    from django.db.models import Sum
    from paiements.models import Paiement
    
    contrat = get_object_or_404(Contrat, id=contrat_id)
    
    # *** CONSOMMATION AUTOMATIQUE DES AVANCES PASSÉES ***
    from .services_consommation_dynamique import ServiceConsommationDynamique
    # Consommer automatiquement toutes les avances du contrat pour les mois écoulés
    ServiceConsommationDynamique.consommer_avances_automatiquement(contrat)
    
    # Filtres de date
    mois_debut = request.GET.get('mois_debut')
    mois_fin = request.GET.get('mois_fin')
    
    if mois_debut:
        try:
            mois_debut_date = datetime.strptime(mois_debut, '%Y-%m').date()
        except ValueError:
            mois_debut_date = contrat.date_debut or (date.today().replace(day=1) - relativedelta(months=12))
    else:
        mois_debut_date = contrat.date_debut or (date.today().replace(day=1) - relativedelta(months=12))
    
    if mois_fin:
        try:
            mois_fin_date = datetime.strptime(mois_fin, '%Y-%m').date()
        except ValueError:
            mois_fin_date = date.today().replace(day=1)
    else:
        mois_fin_date = date.today().replace(day=1)
    
    # Récupérer TOUS les paiements du contrat (pas de dépendance sur HistoriquePaiement)
    paiements_query = Paiement.objects.filter(
        contrat=contrat,
        is_deleted=False,
        date_paiement__gte=mois_debut_date,
        date_paiement__lte=mois_fin_date
    ).order_by('-date_paiement')
    
    # Créer l'historique dynamiquement
    historique = []
    for paiement in paiements_query:
        # CORRECTION V11 : mois REGLE (mois_paye), pas la date d'encaissement.
        mois_paiement = paiement.get_mois_regle()
        historique.append({
            'id': paiement.id,
            'contrat': contrat,
            'paiement': paiement,
            'mois_paiement': mois_paiement,
            'montant_paye': paiement.montant,
            'montant_du': contrat.loyer_mensuel if paiement.type_paiement == 'loyer' else paiement.montant,
            'montant_avance_utilisee': 0,  # Sera calculé si nécessaire
            'montant_restant_du': 0,
            'mois_regle': paiement.statut == 'valide',
            'type_paiement': paiement.get_type_paiement_display(),
            'mois_description': paiement.get_mois_description(),
            'statut': paiement.get_statut_display(),
            'mode_paiement': paiement.get_mode_paiement_display(),
        })
    
    # Calculer le nombre de mois depuis le début du contrat
    mois_depuis_debut = 0
    if contrat.date_debut:
        mois_actuel = date.today().replace(day=1)
        mois_debut_contrat = contrat.date_debut.replace(day=1)
        mois_depuis_debut = (mois_actuel.year - mois_debut_contrat.year) * 12 + (mois_actuel.month - mois_debut_contrat.month) + 1
    
    # Statistiques DYNAMIQUES calculées depuis les vrais paiements
    paiements_valides = paiements_query.filter(statut='valide')
    paiements_en_attente = paiements_query.filter(statut='en_attente')
    
    stats = {
        'total_mois': mois_depuis_debut,
        'mois_regles': paiements_valides.count(),
        'mois_en_attente': paiements_en_attente.count(),
        'montant_total_paye': paiements_valides.aggregate(total=Sum('montant'))['total'] or 0,
        'montant_total_du': contrat.loyer_mensuel * mois_depuis_debut if contrat.loyer_mensuel else 0,
        'montant_avance_utilisee': 0,  # Sera calculé depuis les avances
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
