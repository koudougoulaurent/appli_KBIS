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
    Liste des avances de loyer - Synchronisées parfaitement avec les paiements
    """
    # SYNCHRONISATION AUTOMATIQUE : S'assurer que toutes les avances sont synchronisées
    from .services_synchronisation_avances import ServiceSynchronisationAvances
    
    # Vérifier et synchroniser les avances
    incohérences = ServiceSynchronisationAvances.verifier_coherence_avances()
    if incohérences:
        # Synchroniser automatiquement les avances incohérentes
        ServiceSynchronisationAvances.synchroniser_toutes_avances()
    
    # Récupérer les avances synchronisées (sans doublons)
    from .models_avance import AvanceLoyer
    avances_queryset = AvanceLoyer.objects.select_related(
        'contrat__locataire', 
        'contrat__propriete',
        'contrat__propriete__bailleur',
        'paiement'
    ).distinct().order_by('-date_avance')
    
    # Convertir en format compatible avec le template
    avances = []
    for avance in avances_queryset:
        # Déterminer l'URL de détail appropriée
        detail_url = None
        if hasattr(avance, 'paiement') and avance.paiement:
            # Si l'avance est liée à un paiement, utiliser l'URL du paiement
            detail_url = f"/paiements/avances/paiement/{avance.paiement.id}/"
        else:
            # Sinon, utiliser l'URL de l'avance
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
            'detail_url': detail_url,
        }
        avances.append(avance_data)
    
    # Filtres sur la liste des avances
    contrat_id = request.GET.get('contrat')
    statut = request.GET.get('statut')
    mois_debut = request.GET.get('mois_debut')
    mois_fin = request.GET.get('mois_fin')
    
    # Appliquer les filtres
    if contrat_id:
        try:
            # Si c'est un ID numérique
            contrat_id_int = int(contrat_id)
            avances = [a for a in avances if a['contrat'].id == contrat_id_int]
        except ValueError:
            # Si c'est un nom de contrat, chercher par nom
            avances = [a for a in avances if contrat_id.lower() in a['contrat'].locataire.nom_complet.lower()]
    
    if statut:
        avances = [a for a in avances if a['statut'] == statut]
    
    if mois_debut:
        try:
            mois_debut_date = datetime.strptime(mois_debut, '%Y-%m').date()
            avances = [a for a in avances if a['date_avance'] >= mois_debut_date]
        except ValueError:
            pass
    
    if mois_fin:
        try:
            mois_fin_date = datetime.strptime(mois_fin, '%Y-%m').date()
            avances = [a for a in avances if a['date_avance'] <= mois_fin_date]
        except ValueError:
            pass
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(avances, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistiques
    stats = {
        'total_avances': len(avances),
        'avances_actives': len([a for a in avances if a['statut'] == 'active']),
        'avances_epuisees': len([a for a in avances if a['statut'] == 'epuisee']),
        'montant_total_avances': sum(a['montant_avance'] for a in avances),
        'montant_restant': sum(a['montant_restant'] for a in avances),
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
    Détail d'une avance de loyer - Compatible avec le système synchronisé
    """
    # Essayer d'abord de récupérer l'avance via le modèle AvanceLoyer
    try:
        avance = AvanceLoyer.objects.get(id=avance_id)
    except AvanceLoyer.DoesNotExist:
        # Si l'avance n'existe pas, essayer de la synchroniser depuis le paiement
        from .services_synchronisation_avances import ServiceSynchronisationAvances
        from .models import Paiement
        
        # Chercher un paiement d'avance avec cet ID
        try:
            paiement = Paiement.objects.get(id=avance_id, type_paiement='avance')
            # Synchroniser l'avance
            avance = ServiceSynchronisationAvances.synchroniser_avance_avec_paiement(paiement)
            if not avance:
                raise Http404("Avance non trouvée et impossible à synchroniser")
        except Paiement.DoesNotExist:
            raise Http404("Avance non trouvée")
    
    if not avance:
        raise Http404("Avance non trouvée")
    
    # *** CONSOMMATION DYNAMIQUE ET RÉELLE ***
    from .services_consommation_dynamique import ServiceConsommationDynamique
    
    # Synchroniser avec les paiements de loyer
    consommations_ajoutees = ServiceConsommationDynamique.synchroniser_avec_paiements(avance)
    
    # Consommer automatiquement les mois passés
    ServiceConsommationDynamique.consommer_avances_automatiquement(avance.contrat)
    
    # Recalculer la progression dynamique
    progression = ServiceConsommationDynamique.calculer_progression_avance(avance)
    
    # Récupérer les consommations mises à jour
    consommations = ConsommationAvance.objects.filter(avance=avance).order_by('-mois_consomme')
    
    # Récupérer l'historique des paiements du contrat
    historique = ServiceGestionAvance.get_historique_paiements_contrat(avance.contrat)
    
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
                
                # Créer l'avance via le service avec tous les paramètres
                try:
                    avance = ServiceGestionAvance.creer_avance_loyer(
                        contrat=contrat,
                        montant_avance=montant_avance,
                        date_avance=date_avance,
                        notes=notes,
                        mois_effet_personnalise=mois_effet_personnalise,
                        mode_selection_mois=mode_selection,
                        mois_couverts_manuels=mois_couverts_liste
                    )
                except Exception as e:
                    print(f"Erreur lors de la création de l'avance: {e}")
                    messages.error(request, f"Erreur lors de la création de l'avance: {str(e)}")
                    return render(request, 'paiements/avances/creer_avance_manuel.html', {
                        'form': form,
                        'contrats': Contrat.objects.filter(est_actif=True, est_resilie=False).select_related('locataire', 'propriete'),
                    })
                
                # *** CRITIQUE : Créer automatiquement le paiement correspondant ***
                from .models import Paiement
                from core.id_generator import IDGenerator
                
                # Générer un numéro de paiement unique
                numero_paiement = IDGenerator.generate_id('paiement', date_paiement=date_avance)
                
                # Créer le paiement d'avance
                paiement = Paiement.objects.create(
                    contrat=contrat,
                    montant=montant_avance,
                    date_paiement=date_avance,
                    type_paiement='avance',
                    statut='valide',
                    numero_paiement=numero_paiement,
                    notes=f"Paiement d'avance automatique - {avance.nombre_mois_couverts} mois couverts"
                )
                
                # Lier l'avance au paiement
                avance.paiement = paiement
                avance.save()
                
                # *** SYNCHRONISATION DES AVANCES MULTIPLES ***
                from .services_synchronisation_avances import ServiceSynchronisationAvances
                
                # Synchroniser toutes les avances du contrat pour calculer les totaux
                ServiceSynchronisationAvances.synchroniser_toutes_avances_contrat(contrat)
                
                # Récupérer les statistiques globales des avances du contrat
                avances_contrat = AvanceLoyer.objects.filter(contrat=contrat, statut='active')
                total_mois_couverts = sum(avance.nombre_mois_couverts for avance in avances_contrat)
                total_montant_restant = sum(avance.montant_restant for avance in avances_contrat)
                
                # Message de confirmation détaillé
                if avances_contrat.count() > 1:
                    messages.success(request, 
                        f"SUCCES - AVANCE DE PROLONGATION CREE AVEC SUCCES !\n\n"
                        f"Montant : {avance.montant_avance:,.0f} F CFA\n"
                        f"Mois couverts par cette avance : {avance.nombre_mois_couverts}\n"
                        f"TOTAL CONTRAT : {avances_contrat.count()} avances actives\n"
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
                'avance': float(contrat.avance_loyer or 0),
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
