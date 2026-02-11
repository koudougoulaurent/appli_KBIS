from django.http import FileResponse, HttpResponse
# --- Vue pour télécharger la quittance PDF KBIS d'un paiement ---
from django.contrib.auth.decorators import login_required
@login_required
def telecharger_quittance_kbis_pdf(request, paiement_id):
    """Permet de télécharger la quittance PDF KBIS générée pour un paiement donné (reliquat ou partiel)."""
    paiement = get_object_or_404(Paiement, pk=paiement_id)
    pdf_content = paiement.generer_quittance_kbis_dynamique(request.user)
    if pdf_content:
        response = HttpResponse(pdf_content, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="quittance_kbis_{paiement_id}.pdf"'
        return response
    else:
        messages.error(request, "Erreur lors de la génération du PDF de quittance KBIS.")
        return redirect('paiements:detail', pk=paiement_id)
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods, require_POST
from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView
from django.urls import reverse_lazy, reverse
from django.db.models import Q, Sum, Count, F, Case, When, DecimalField
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.db import transaction
from datetime import datetime, timedelta, date
from django.core.paginator import Paginator
from django.contrib.contenttypes.models import ContentType
from django.template.loader import render_to_string
from django.conf import settings
from decimal import Decimal
import json
import os

from .models import Paiement, ChargeDeductible, QuittancePaiement, RecapMensuel
from .forms import PaiementForm, ChargeDeductibleForm, RetraitBailleurForm, GenererPDFLotForm
from contrats.models import Contrat
from proprietes.models import Propriete, Locataire, Bailleur
from core.models import AuditLog, ConfigurationEntreprise
from core.utils import check_group_permissions, check_group_permissions_with_fallback, get_context_with_entreprise_config
from core.enhanced_list_view import EnhancedSearchMixin
from django.views.generic import ListView
# from .models import TableauBordFinancier  # Modèle supprimé
# from .forms import TableauBordFinancierForm  # Formulaire supprimé
from .models import RetraitBailleur
# RecapMensuel is now imported above
# from .services import generate_recap_pdf, generate_recap_pdf_batch  # Fonctions non disponibles
try:
    from devises.models import Devise
except ImportError:
    Devise = None

# -- VUE HISTORIQUE DES PAIEMENTS PARTIELS --
@login_required
def historique_paiements_partiels(request, contrat_id, mois, annee):
    """Affiche l'historique des paiements partiels pour un contrat et un mois donné."""
    try:
        # Convertir les paramètres en entiers
        mois_int = int(mois)
        annee_int = int(annee)
        
        # Valider que le mois est entre 1 et 12
        if mois_int < 1 or mois_int > 12:
            messages.error(request, f"Mois invalide: {mois}. Le mois doit être entre 1 et 12.")
            return redirect('paiements:liste')
        
        # Construire la chaîne attendue au format "Mois Année"
        mois_noms = [
            'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
            'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'
        ]
        mois_nom = mois_noms[mois_int - 1]
        mois_paye_attendu = f"{mois_nom} {annee_int}"
        
        # Le champ mois_paye est un CharField, donc on fait une recherche exacte
        paiements = Paiement.objects.filter(
            contrat_id=contrat_id,
            mois_paye=mois_paye_attendu,
            is_deleted=False
        ).order_by('date_paiement')
        
        contrat = Contrat.objects.get(pk=contrat_id)
    except (ValueError, TypeError):
        messages.error(request, f"Paramètres invalides: mois={mois}, année={annee}")
        return redirect('paiements:liste')
    except Contrat.DoesNotExist:
        messages.error(
            request,
            f"Aucun contrat trouvé avec l'identifiant {contrat_id}. "
            "Vérifiez l'ID ou <a href='/contrats/liste/'>consultez la liste des contrats</a>. "
            "Vous pouvez aussi <a href='/contrats/ajouter/'>ajouter un nouveau contrat</a>."
        )
        return render(request, 'paiements/historique_partiel.html', {'contrat': None, 'paiements': [], 'mois': mois, 'annee': annee})
    montant_du_mois = paiements.first().montant_du_mois if paiements.exists() else Decimal(str(contrat.loyer_mensuel)) if contrat.loyer_mensuel else Decimal('0')
    total_paye = sum([p.montant for p in paiements])
    montant_restant = max(montant_du_mois - total_paye, 0)
    statut = 'valide' if montant_restant == 0 else 'partiellement_payé'
    context = {
        'paiements': paiements,
        'contrat': contrat,
        'mois': mois,
        'annee': annee,
        'montant_du_mois': montant_du_mois,
        'total_paye': total_paye,
        'montant_restant': montant_restant,
        'statut': statut,
    }
    return render(request, 'paiements/historique_partiel.html', context)


# -- VUE AMÉLIORÉE POUR LES PAIEMENTS PARTIELS --
@login_required
def ajouter_paiement_partiel(request):
    """
    Vue améliorée pour ajouter un paiement partiel avec interface moderne
    et détection automatique
    """
    from .services_paiement_partiel import ServicePaiementPartiel
    from .forms import PaiementForm
    
    contrat_id = request.GET.get('contrat_id')
    contrat_obj = None
    calcul_restant = None
    
    if contrat_id:
        try:
            contrat_obj = Contrat.objects.get(pk=contrat_id, est_actif=True, is_deleted=False)
            # DÉTERMINER LE MOIS À RÉGLER EN UTILISANT LA MÊME LOGIQUE QUE LES PAIEMENTS GLOBAUX
            mois_a_regler = ServicePaiementPartiel.determiner_mois_a_regler(contrat_obj)
            calcul_restant = ServicePaiementPartiel.calculer_montant_restant(
                contrat_obj, mois_a_regler['mois_paye']
            )
            
            # NOUVEAU : Détecter les reliquats en cours pour ce contrat
            reliquats = ServicePaiementPartiel.detecter_reliquats_en_cours(contrat_obj)
        except Contrat.DoesNotExist:
            messages.error(request, "Contrat introuvable ou inactif.")
            reliquats = []
    
    if request.method == 'POST':
        form = PaiementForm(request.POST)
        if form.is_valid():
            paiement = form.save(commit=False)
            paiement.cree_par = request.user
            
            # *** NOUVEAU : VÉRIFICATION DES RELIQUATS EN COURS ***
            # Vérifier s'il y a des paiements partiels non complétés pour ce contrat
            ignorer_reliquat = request.POST.get('ignorer_reliquat', '') == 'oui'
            
            if not ignorer_reliquat and paiement.contrat:
                reliquats_post = ServicePaiementPartiel.detecter_reliquats_en_cours(paiement.contrat)
                
                if reliquats_post:
                    # Il y a des reliquats - afficher une alerte et demander confirmation
                    total_reliquat_post = sum(r['montant_restant'] for r in reliquats_post)
                    
                    # Préparer le contexte avec les reliquats
                    context_post = {
                        'form': form,
                        'contrat_obj': paiement.contrat,
                        'contrats_actifs': Contrat.objects.filter(est_actif=True, is_deleted=False).select_related('locataire', 'propriete', 'propriete__bailleur'),
                        'reliquats': reliquats_post,
                        'total_reliquat': total_reliquat_post,
                        'afficher_alerte_reliquat': True,
                        'calcul_restant': calcul_restant,
                        'mois_a_regler': mois_a_regler if 'mois_a_regler' in locals() else None,
                    }
                    
                    return render(request, 'paiements/ajouter_paiement_partiel.html', context_post)
            
            # *** VALIDATION STRICTE : Vérifier que le mois est le mois suivant le dernier paiement ***
            mois_paye_nom = request.POST.get('mois_paye', '')
            if mois_paye_nom:
                # Si le mois n'a pas d'année, construire le format complet
                import re
                if not re.search(r'\d{4}', mois_paye_nom):
                    # Pas d'année dans le mois - déterminer l'année intelligemment
                    from datetime import datetime
                    mois_francais = {
                        'janvier': 1, 'février': 2, 'mars': 3, 'avril': 4,
                        'mai': 5, 'juin': 6, 'juillet': 7, 'août': 8,
                        'septembre': 9, 'octobre': 10, 'novembre': 11, 'décembre': 12
                    }
                    annee_actuelle = datetime.now().year
                    
                    # Utiliser TOUJOURS l'année courante réelle
                    mois_paye_nom = f"{mois_paye_nom} {annee_actuelle}"
                
                # VALIDATION STRICTE pour les paiements partiels (toujours de type loyer)
                validation = ServicePaiementPartiel.valider_mois_a_regler(
                    paiement.contrat, mois_paye_nom, paiement.type_paiement or 'loyer'
                )
                
                if not validation['valide']:
                    type_erreur = validation.get('type_erreur', '')
                    
                    if type_erreur == 'mois_avance':
                        # Mois en avance (futur) - proposer d'enregistrer comme avance
                        messages.warning(
                            request,
                            f"{validation['message']} "
                            f"Les paiements partiels ne peuvent être enregistrés que pour le mois courant ou les mois passés. "
                            f"Pour payer en avance, utilisez le type 'AVANCE DE LOYER'."
                        )
                        form = PaiementForm(request.POST)
                        return render(request, 'paiements/ajouter_paiement_partiel.html', {
                            'form': form,
                            'contrat_obj': paiement.contrat,
                            'contrats_actifs': Contrat.objects.filter(est_actif=True, is_deleted=False).select_related('locataire', 'propriete', 'propriete__bailleur'),
                            'mois_attendu': validation.get('mois_attendu', ''),
                            'error': validation.get('message', ''),
                            'validation_avance': validation
                        })
                    elif type_erreur == 'mois_incorrect':
                        # Mois incorrect (pas le mois attendu) - REFUSER avec suggestion
                        messages.error(
                            request,
                            f"{validation.get('message', 'Mois invalide')} "
                            f"Les paiements partiels doivent être pour le mois attendu ({validation.get('mois_attendu', '')}) ou un mois en retard."
                        )
                        form = PaiementForm(request.POST)
                        return render(request, 'paiements/ajouter_paiement_partiel.html', {
                            'form': form,
                            'contrat_obj': paiement.contrat,
                            'contrats_actifs': Contrat.objects.filter(est_actif=True, is_deleted=False).select_related('locataire', 'propriete', 'propriete__bailleur'),
                            'mois_attendu': validation.get('mois_attendu', ''),
                            'error': validation.get('message', '')
                        })
                    elif type_erreur == 'mois_deja_paye':
                        # Mois déjà complètement payé - REFUSER
                        messages.error(request, validation.get('message', 'Mois invalide'))
                        form = PaiementForm(request.POST)
                        return render(request, 'paiements/ajouter_paiement_partiel.html', {
                            'form': form,
                            'contrat_obj': paiement.contrat,
                            'contrats_actifs': Contrat.objects.filter(est_actif=True, is_deleted=False).select_related('locataire', 'propriete', 'propriete__bailleur'),
                            'mois_attendu': validation.get('mois_attendu', ''),
                            'error': validation.get('message', '')
                        })
                    else:
                        # Autre erreur (format invalide, etc.) - REFUSER
                        messages.error(request, validation.get('message', 'Mois invalide'))
                        form = PaiementForm(request.POST)
                        return render(request, 'paiements/ajouter_paiement_partiel.html', {
                            'form': form,
                            'contrat_obj': paiement.contrat,
                            'contrats_actifs': Contrat.objects.filter(est_actif=True, is_deleted=False).select_related('locataire', 'propriete', 'propriete__bailleur'),
                            'mois_attendu': validation.get('mois_attendu', ''),
                            'error': validation.get('message', '')
                        })
                
                paiement.mois_paye = validation['mois_attendu']
                
                # Afficher un message informatif si c'est un paiement en retard
                if validation.get('est_retard'):
                    messages.info(request, validation.get('message_info', 'Paiement en retard autorisé pour se rattraper.'))
            else:
                # Si pas de mois spécifié, utiliser le mois attendu
                mois_a_regler = ServicePaiementPartiel.determiner_mois_a_regler(paiement.contrat)
                paiement.mois_paye = mois_a_regler['mois_paye']
            
            # Synchroniser automatiquement le paiement partiel
            est_partiel = ServicePaiementPartiel.synchroniser_paiement_partiel(paiement)
            paiement.save()
            
            # Générer la référence
            if not paiement.reference_paiement:
                paiement.reference_paiement = paiement.generate_reference_paiement()
                paiement.save()
            
            # VÉRIFIER SI CE PAIEMENT COMPLÈTE UN RELIQUAT
            if paiement.mois_paye:
                calcul_restant = ServicePaiementPartiel.calculer_montant_restant(
                    paiement.contrat, paiement.mois_paye
                )
                if calcul_restant.get('est_complet', False):
                    messages.success(
                        request,
                        f'✅ Reliquat complété ! Le mois {paiement.mois_paye} est maintenant entièrement payé. '
                        f'Tous les paiements partiels concernés ont été marqués comme complétés automatiquement.'
                    )
                elif est_partiel:
                    messages.success(
                        request,
                        f'Paiement partiel enregistré: {paiement.reference_paiement} - '
                        f'Montant payé: {paiement.montant} F CFA, '
                        f'Montant restant: {paiement.montant_restant_du} F CFA'
                    )
                else:
                    messages.success(
                        request,
                        f'Paiement enregistré: {paiement.reference_paiement}'
                    )
            else:
                if est_partiel:
                    messages.success(
                        request,
                        f'Paiement partiel enregistré: {paiement.reference_paiement} - '
                        f'Montant payé: {paiement.montant} F CFA, '
                        f'Montant restant: {paiement.montant_restant_du} F CFA'
                    )
                else:
                    messages.success(
                        request,
                        f'Paiement enregistré: {paiement.reference_paiement}'
                    )
            
            return redirect('paiements:liste_contrats_paiements_partiels')
    else:
        # Pré-remplir le formulaire avec le mois attendu si un contrat est sélectionné
        initial_data = {'contrat': contrat_id} if contrat_id else {}
        if contrat_obj:
            mois_a_regler = ServicePaiementPartiel.determiner_mois_a_regler(contrat_obj)
            initial_data['mois_paye'] = mois_a_regler['mois_paye']
        form = PaiementForm(initial=initial_data)
    
    # Obtenir les contrats avec paiements partiels pour le contexte
    contrats_avec_partiels = ServicePaiementPartiel.detecter_contrats_avec_paiements_partiels()
    stats = ServicePaiementPartiel.obtenir_statistiques_paiements_partiels()
    
    # Obtenir tous les contrats actifs pour le formulaire
    contrats_actifs = Contrat.objects.filter(
        est_actif=True,
        est_resilie=False,
        is_deleted=False
    ).select_related('locataire', 'propriete', 'propriete__bailleur')
    
    # DÉTERMINER LE MOIS À RÉGLER (même logique que paiements globaux)
    mois_a_regler = None
    if contrat_obj:
        mois_a_regler = ServicePaiementPartiel.determiner_mois_a_regler(contrat_obj)
    elif contrat_id:
        try:
            contrat_temp = Contrat.objects.get(pk=contrat_id, est_actif=True, is_deleted=False)
            mois_a_regler = ServicePaiementPartiel.determiner_mois_a_regler(contrat_temp)
        except:
            pass
    
    # NOUVEAU : Calculer les reliquats si contrat sélectionné
    reliquats = []
    total_reliquat = 0
    if contrat_obj:
        reliquats = ServicePaiementPartiel.detecter_reliquats_en_cours(contrat_obj)
        total_reliquat = sum(r['montant_restant'] for r in reliquats)
    
    context = {
        'form': form,
        'contrat_obj': contrat_obj,
        'calcul_restant': calcul_restant,
        'contrats_actifs': contrats_actifs,
        'contrats_avec_partiels': contrats_avec_partiels,
        'stats': stats,
        'mois_a_regler': mois_a_regler,  # NOUVEAU : Mois attendu pour le paiement
        'reliquats': reliquats,  # NOUVEAU : Reliquats détectés
        'total_reliquat': total_reliquat,  # NOUVEAU : Total des reliquats
        'afficher_alerte_reliquat': len(reliquats) > 0,  # NOUVEAU : Afficher l'alerte si reliquats
    }
    
    return render(request, 'paiements/ajouter_paiement_partiel.html', context)


# -- VUE POUR LISTER LES CONTRATS AVEC PAIEMENTS PARTIELS --
@login_required
def liste_contrats_paiements_partiels(request):
    """
    Liste tous les contrats ayant des paiements partiels en cours
    avec synchronisation dynamique, recherche, tri et filtres intelligents
    """
    from .services_paiement_partiel import ServicePaiementPartiel
    from core.utils import get_context_with_entreprise_config
    import unicodedata
    
    # Récupérer les paramètres GET
    search = request.GET.get('search', '').strip()
    sort = request.GET.get('sort', 'locataire')  # Par défaut tri par locataire
    order = request.GET.get('order', 'asc')
    statut = request.GET.get('statut', '')  # reliquat, solde, tous
    propriete_id = request.GET.get('propriete', '')
    
    # Détecter les contrats avec paiements partiels (inclut tous les paiements partiels)
    contrats_avec_partiels = ServicePaiementPartiel.detecter_contrats_avec_paiements_partiels()
    
    # Filtrage/recherche intelligent (en mémoire, car peu de contrats)
    def normalize(txt):
        if not txt:
            return ''
        return unicodedata.normalize('NFKD', str(txt)).encode('ASCII', 'ignore').decode('utf-8').lower()
    
    filtered = []
    for data in contrats_avec_partiels.values():
        contrat = data['contrat']
        locataire = contrat.locataire.get_nom_complet() if hasattr(contrat.locataire, 'get_nom_complet') else str(contrat.locataire)
        propriete = contrat.propriete.titre if hasattr(contrat.propriete, 'titre') else str(contrat.propriete)
        numero_contrat = contrat.numero_contrat
        montant_total_restant = data.get('montant_total_restant', 0)
        paiements_partiels = data.get('paiements_partiels', [])
        paiements_partiels_tous = data.get('paiements_partiels_tous', [])
        # Recherche globale
        if search:
            search_norm = normalize(search)
            if not (
                search_norm in normalize(locataire)
                or search_norm in normalize(numero_contrat)
                or search_norm in normalize(propriete)
            ):
                continue
        # Filtre propriété
        if propriete_id and str(contrat.propriete.id) != str(propriete_id):
            continue
        # Filtre statut reliquat
        if statut == 'reliquat' and not (montant_total_restant and montant_total_restant > 0):
            continue
        if statut == 'solde' and (montant_total_restant and montant_total_restant > 0):
            continue
        filtered.append(data)
    
    # Tri dynamique
    def get_sort_key(data):
        contrat = data['contrat']
        if sort == 'locataire':
            return normalize(contrat.locataire.get_nom_complet() if hasattr(contrat.locataire, 'get_nom_complet') else str(contrat.locataire))
        elif sort == 'propriete':
            return normalize(contrat.propriete.titre if hasattr(contrat.propriete, 'titre') else str(contrat.propriete))
        elif sort == 'contrat':
            return normalize(contrat.numero_contrat)
        elif sort == 'montant':
            return data.get('montant_total_restant', 0)
        elif sort == 'nb_partiels':
            return len(data.get('paiements_partiels_tous', []))
        else:
            return normalize(contrat.locataire.get_nom_complet() if hasattr(contrat.locataire, 'get_nom_complet') else str(contrat.locataire))
    reverse = (order == 'desc')
    filtered_sorted = sorted(filtered, key=get_sort_key, reverse=reverse)
    
    # Obtenir les statistiques DYNAMIQUEMENT à partir des contrats filtrés
    stats = ServicePaiementPartiel.obtenir_statistiques_paiements_partiels({i: d for i, d in enumerate(filtered_sorted)})
    
    # Pour le filtre propriété : liste des propriétés concernées
    proprietes_possibles = set()
    for data in contrats_avec_partiels.values():
        contrat = data['contrat']
        if hasattr(contrat.propriete, 'id'):
            proprietes_possibles.add((contrat.propriete.id, str(contrat.propriete)))
    proprietes_possibles = sorted(list(proprietes_possibles), key=lambda x: x[1])
    
    context = get_context_with_entreprise_config({
        'contrats_avec_partiels': {i: d for i, d in enumerate(filtered_sorted)},
        'stats': stats,
        'title': 'Contrats avec Paiements Partiels',
        'search': search,
        'sort': sort,
        'order': order,
        'statut': statut,
        'propriete_id': propriete_id,
        'proprietes_possibles': proprietes_possibles,
    })
    
    return render(request, 'paiements/contrats_paiements_partiels.html', context)


# -- VUE POUR COMPLÉTER UN RELIQUAT --
@login_required
def completer_reliquat(request, paiement_id):
    """
    Vue pour compléter un reliquat de paiement partiel avec un formulaire dédié
    """
    from .services_paiement_partiel import ServicePaiementPartiel
    
    # Récupérer le paiement initial
    paiement_initial = get_object_or_404(
        Paiement,
        pk=paiement_id,
        est_paiement_partiel=True,
        is_deleted=False
    )
    
    contrat = paiement_initial.contrat
    mois_paye = paiement_initial.mois_paye
    
    # Calculer le montant restant
    calcul = ServicePaiementPartiel.calculer_montant_restant(contrat, mois_paye)
    
    # Récupérer tous les paiements existants pour ce mois
    paiements_existants = Paiement.objects.filter(
        contrat=contrat,
        mois_paye=mois_paye,
        is_deleted=False,
        statut='valide'
    ).order_by('date_paiement')
    
    # Calculer le pourcentage de progression
    pourcentage = 0
    if calcul['montant_du_mois'] > 0:
        pourcentage = (calcul['montant_paye'] / calcul['montant_du_mois']) * 100
    
    if request.method == 'POST':
        try:
            montant = Decimal(request.POST.get('montant', 0))
            mode_paiement = request.POST.get('mode_paiement')
            date_paiement_str = request.POST.get('date_paiement')
            numero_reference = request.POST.get('numero_reference', '')
            notes = request.POST.get('notes', '')
            # Conversion de la date (str) en objet date
            from datetime import datetime
            date_paiement = None
            if date_paiement_str:
                try:
                    date_paiement = datetime.strptime(date_paiement_str, "%Y-%m-%d").date()
                except Exception:
                    messages.error(request, "Format de date invalide. Utilisez AAAA-MM-JJ.")
                    return redirect('paiements:completer_reliquat', paiement_id=paiement_id)
            
            # Validation
            if montant <= 0:
                messages.error(request, "Le montant doit être supérieur à 0.")
                return redirect('paiements:completer_reliquat', paiement_id=paiement_id)
            
            if montant > calcul['montant_restant']:
                messages.error(
                    request,
                    f"Le montant ({montant:,.0f} F) dépasse le montant restant ({calcul['montant_restant']:,.0f} F)."
                )
                return redirect('paiements:completer_reliquat', paiement_id=paiement_id)
            
            # Créer le paiement de complétion
            with transaction.atomic():
                nouveau_paiement = Paiement.objects.create(
                    contrat=contrat,
                    montant=montant,
                    type_paiement='paiement_partiel',
                    mode_paiement=mode_paiement,
                    date_paiement=date_paiement,
                    mois_paye=mois_paye,
                    montant_du_mois=calcul['montant_du_mois'],
                    est_paiement_partiel=True,
                    statut='valide',
                    notes=f"Complétion de reliquat. {notes}",
                    cree_par=request.user
                )
                
                # Ajouter référence si fournie
                if numero_reference:
                    if mode_paiement == 'cheque':
                        nouveau_paiement.numero_cheque = numero_reference
                    elif mode_paiement == 'virement':
                        nouveau_paiement.reference_virement = numero_reference
                    nouveau_paiement.save()
                
                # Vérifier et compléter automatiquement le reliquat
                completion_effectuee = ServicePaiementPartiel.verifier_et_completer_reliquat(
                    paiement=nouveau_paiement,
                    skip_save=False
                )
                
                if completion_effectuee:
                    messages.success(
                        request,
                        f"✅ Reliquat complété avec succès ! "
                        f"Le mois {mois_paye} est maintenant entièrement payé."
                    )
                else:
                    nouveau_montant_restant = calcul['montant_restant'] - montant
                    messages.success(
                        request,
                        f"✅ Paiement partiel ajouté avec succès ! "
                        f"Reste à payer : {nouveau_montant_restant:,.0f} F CFA"
                    )
                
                # Générer une quittance PDF A5 KBIS pour ce paiement
                try:
                    quittance_pdf = nouveau_paiement.generer_quittance_kbis_dynamique(request.user)
                    if quittance_pdf:
                        messages.info(request, "📄 Quittance PDF KBIS générée avec succès.")
                    else:
                        messages.warning(request, "⚠️ Paiement enregistré mais erreur lors de la génération de la quittance PDF.")
                except Exception as e:
                    messages.warning(request, f"⚠️ Paiement enregistré mais erreur quittance : {str(e)}")
                
                return redirect('paiements:liste_contrats_paiements_partiels')
                
        except Exception as e:
            messages.error(request, f"❌ Erreur lors de l'ajout du paiement : {str(e)}")
            return redirect('paiements:completer_reliquat', paiement_id=paiement_id)
    
    # GET - Afficher le formulaire
    context = get_context_with_entreprise_config({
        'paiement_initial': paiement_initial,
        'calcul': calcul,
        'paiements_existants': paiements_existants,
        'pourcentage': pourcentage,
        'date_today': timezone.now().date().isoformat(),
        'title': f'Compléter le Reliquat - {contrat.numero_contrat}'
    })
    
    return render(request, 'paiements/completer_reliquat.html', context)


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods, require_POST
from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView
from django.urls import reverse_lazy, reverse
from django.db.models import Q, Sum, Count, F, Case, When, DecimalField
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.db import transaction
from datetime import datetime, timedelta, date
from django.core.paginator import Paginator
from django.contrib.contenttypes.models import ContentType
from django.template.loader import render_to_string
from django.conf import settings
from decimal import Decimal
import json
import os

from .models import Paiement, ChargeDeductible, QuittancePaiement, RecapMensuel
from .forms import PaiementForm, ChargeDeductibleForm, RetraitBailleurForm, GenererPDFLotForm
from contrats.models import Contrat
from proprietes.models import Propriete, Locataire, Bailleur
from core.models import AuditLog, ConfigurationEntreprise
from core.utils import check_group_permissions, check_group_permissions_with_fallback, get_context_with_entreprise_config
from core.enhanced_list_view import EnhancedSearchMixin
from django.views.generic import ListView
# from .models import TableauBordFinancier  # Modèle supprimé
# from .forms import TableauBordFinancierForm  # Formulaire supprimé
from .models import RetraitBailleur
# RecapMensuel is now imported above
# from .services import generate_recap_pdf, generate_recap_pdf_batch  # Fonctions non disponibles
try:
    from devises.models import Devise
except ImportError:
    Devise = None


@login_required
def paiements_dashboard(request):
    """
    Dashboard principal des paiements SÉCURISÉ - SANS informations financières confidentielles
    """
    # Statistiques générales (NON confidentielles)
    # Optimisation : utiliser une seule requête avec annotate au lieu de 4 requêtes séparées
    from django.db.models import Count, Q
    stats_paiements = Paiement.objects.filter(is_deleted=False).aggregate(
        total=Count('id'),
        valides=Count('id', filter=Q(statut='valide')),
        en_attente=Count('id', filter=Q(statut='en_attente')),
        refuses=Count('id', filter=Q(statut='refuse'))
    )
    total_paiements = stats_paiements['total'] or 0
    paiements_valides = stats_paiements['valides'] or 0
    paiements_en_attente = stats_paiements['en_attente'] or 0
    paiements_refuses = stats_paiements['refuses'] or 0
    
    # SUPPRIMER: Tous les montants financiers pour la confidentialité
    # NE PAS calculer ou afficher de montants
    
    # Top propriétés par activité (NON par revenus)
    top_proprietes_activite = Paiement.objects.filter(
        is_deleted=False,
        statut='valide'
    ).values(
        'contrat__propriete__titre', 
        'contrat__propriete__ville'
    ).annotate(
        nombre_paiements=Count('id')  # Nombre de paiements, PAS les montants
    ).order_by('-nombre_paiements')[:5]
    
    # Paiements récents (SANS montants) - utiliser date_paiement au lieu de created_at
    paiements_recents = Paiement.objects.filter(
        is_deleted=False
    ).select_related('contrat__propriete', 'contrat__locataire').order_by('-date_paiement')[:5]
    
    # Paiements nécessitant attention (SANS montants)
    paiements_attention = Paiement.objects.filter(
        is_deleted=False
    ).filter(
        Q(statut='en_attente') | 
        Q(statut='refuse') |
        Q(date_paiement__lt=timezone.now().date() - timedelta(days=30))
    ).select_related('contrat__propriete', 'contrat__locataire')[:5]
    
    # Statistiques par mois (6 derniers mois) - UNIQUEMENT le nombre de paiements
    mois_stats = []
    for i in range(6):
        date = timezone.now() - timedelta(days=30*i)
        mois = date.month
        annee = date.year
        
        nombre_paiements_mois = Paiement.objects.filter(
            is_deleted=False,
            statut='valide',
            date_paiement__month=mois,
            date_paiement__year=annee
        ).count()  # Nombre de paiements, PAS les montants
        
        mois_stats.append({
            'mois': date.strftime('%B %Y'),
            'nombre_paiements': nombre_paiements_mois,  # Nombre, PAS montant
            'activite': 'Élevée' if nombre_paiements_mois > 10 else 'Modérée' if nombre_paiements_mois > 5 else 'Faible'
        })
    
    mois_stats.reverse()
    
    # Données des retraits bailleurs
    from django.db import models
    
    # Statistiques des retraits (simplifié)
    retraits_valides = RetraitBailleur.objects.filter(is_deleted=False, statut='valide').count()
    retraits_payes = RetraitBailleur.objects.filter(is_deleted=False, statut='paye').count()
    retraits_en_attente = RetraitBailleur.objects.filter(is_deleted=False, statut='en_attente').count()
    
    # Calcul du montant total des retraits validés
    montant_total_retraits = RetraitBailleur.objects.filter(
        is_deleted=False, 
        statut='valide'
    ).aggregate(
        total=models.Sum('montant_net_a_payer')
    )['total'] or 0
    
    # Retraits récents (5 derniers)
    retraits_recents = RetraitBailleur.objects.filter(
        is_deleted=False
    ).select_related('bailleur').order_by('-date_demande')[:5]
    
    context = {
        'total_paiements': total_paiements,
        'paiements_valides': paiements_valides,
        'paiements_en_attente': paiements_en_attente,
        'paiements_refuses': paiements_refuses,
        # SUPPRIMER: montant_total, montant_mois_courant
        'top_proprietes_activite': top_proprietes_activite,  # Activité, PAS revenus
        'paiements_recents': paiements_recents,
        'paiements_attention': paiements_attention,
        'mois_stats': mois_stats,
        # Nouvelles données pour les retraits
        'retraits_valides': retraits_valides,
        'retraits_payes': retraits_payes,
        'retraits_en_attente': retraits_en_attente,
        'montant_total_retraits': montant_total_retraits,
        'retraits_recents': retraits_recents,
    }
    
    return render(request, 'paiements/dashboard.html', context)


class PaiementListView(LoginRequiredMixin, ListView):
    model = Paiement
    template_name = 'paiements/paiement_list.html'
    context_object_name = 'paiements'
    paginate_by = 20
    
    def get_queryset(self):
        from django.db.models import Q
        queryset = super().get_queryset()
        queryset = queryset.select_related(
            'contrat__locataire',
            'contrat__propriete',
            'contrat__propriete__bailleur'
        )
        # Recherche et filtres
        query = self.request.GET.get('q', '').strip()
        statut_filter = self.request.GET.get('statut', '')
        type_filter = self.request.GET.get('type_paiement', '')
        mode_filter = self.request.GET.get('mode_paiement', '')
        # Tri dynamique
        sort = self.request.GET.get('sort', '')
        order = self.request.GET.get('order', 'asc')
        # Recherche textuelle
        if query:
            queryset = queryset.filter(
                Q(reference_paiement__icontains=query) |
                Q(contrat__numero_contrat__icontains=query) |
                Q(contrat__locataire__nom__icontains=query) |
                Q(contrat__locataire__prenom__icontains=query) |
                Q(contrat__propriete__adresse__icontains=query) |
                Q(contrat__propriete__ville__icontains=query) |
                Q(contrat__propriete__titre__icontains=query) |
                Q(libelle__icontains=query)
            )
        if statut_filter:
            queryset = queryset.filter(statut=statut_filter)
        if type_filter:
            queryset = queryset.filter(type_paiement=type_filter)
        if mode_filter:
            queryset = queryset.filter(mode_paiement=mode_filter)
        # Mapping des champs triables
        sort_fields = {
            'reference': 'reference_paiement',
            'locataire': 'contrat__locataire__nom',
            'propriete': 'contrat__propriete__titre',
            'type': 'type_paiement',
            'montant': 'montant',
            'mode': 'mode_paiement',
            'date': 'date_paiement',
            'statut': 'statut',
        }
        if sort in sort_fields:
            champ = sort_fields[sort]
            if order == 'desc':
                champ = '-' + champ
            queryset = queryset.order_by(champ)
        else:
            queryset = queryset.order_by('-created_at')
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Récupérer les paramètres de recherche pour les afficher dans le template
        context['query'] = self.request.GET.get('q', '')
        context['statut_filter'] = self.request.GET.get('statut', '')
        context['type_filter'] = self.request.GET.get('type_paiement', '')
        context['mode_filter'] = self.request.GET.get('mode_paiement', '')
        
        # Statistiques pour le contexte (basées sur les filtres actifs)
        queryset = self.get_queryset()
        context['total_paiements'] = queryset.count()
        context['paiements_valides'] = queryset.filter(statut='valide').count()
        context['paiements_en_attente'] = queryset.filter(statut='en_attente').count()
        context['paiements_refuses'] = queryset.filter(statut='refuse').count()
        
        # Montant total
        context['montant_total'] = queryset.aggregate(
            total=Sum('montant')
        )['total'] or 0
        
        # Statistiques par type
        context['stats_types'] = queryset.values('type_paiement').annotate(
            count=Count('id'),
            total=Sum('montant')
        ).order_by('-count')
        
        return context


paiement_list = PaiementListView.as_view()


class PaiementEnhancedListView(LoginRequiredMixin, EnhancedSearchMixin, ListView):
    """
    Vue de liste améliorée pour les paiements avec recherche intelligente
    """
    model = Paiement
    template_name = 'base_liste_enhanced.html'
    context_object_name = 'paiements'
    paginate_by = 20
    page_title = 'Paiements'
    page_icon = 'credit-card'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.select_related(
            'contrat__locataire',
            'contrat__propriete',
            'contrat__propriete__bailleur'
        ).order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        # S'assurer que object_list est défini
        if not hasattr(self, 'object_list'):
            self.object_list = self.get_queryset()
        context = super().get_context_data(**kwargs)
        
        # Configuration des colonnes
        context['columns'] = [
            {'field': 'numero_paiement', 'label': 'N° Paiement', 'sortable': True},
            {'field': 'contrat__locataire', 'label': 'Locataire', 'sortable': True},
            {'field': 'contrat__propriete', 'label': 'Propriété', 'sortable': True},
            {'field': 'type_paiement', 'label': 'Type', 'sortable': True},
            {'field': 'montant', 'label': 'Montant', 'sortable': True},
            {'field': 'mode_paiement', 'label': 'Mode', 'sortable': True},
            {'field': 'date_paiement', 'label': 'Date', 'sortable': True},
            {'field': 'statut', 'label': 'Statut', 'sortable': True},
        ]
        
        # Actions
        context['actions'] = [
            {'url_name': 'paiements:detail', 'icon': 'eye', 'style': 'outline-primary', 'title': 'Voir'},
            {'url_name': 'paiements:modifier', 'icon': 'pencil', 'style': 'outline-warning', 'title': 'Modifier'},
        ]
        
        # Filtres disponibles
        context['available_filters'] = {
            'statut': [
                ('valide', 'Validé'),
                ('en_attente', 'En attente'),
                ('refuse', 'Refusé'),
            ],
            'type_paiement': [
                ('loyer', 'Loyer'),
                ('caution', 'Caution'),
                ('avance', 'Avance'),
            ],
            'mode_paiement': [
                ('especes', 'Espèces'),
                ('virement', 'Virement'),
                ('cheque', 'Chèque'),
                ('mobile_money', 'Mobile Money'),
            ]
        }
        
        # Statistiques
        context['total_count'] = Paiement.objects.count()
        context['filtered_count'] = self.get_queryset().count()
        
        return context


paiement_enhanced_list = PaiementEnhancedListView.as_view()


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
    """Ajouter un nouveau paiement avec contexte intelligent."""
    # Vérification des permissions
    from core.utils import check_group_permissions
    
    # 🔍 DEBUG : Afficher les infos utilisateur et permissions (uniquement en mode DEBUG)
    if settings.DEBUG:
        print(f"🔍 DEBUG ajouter_paiement:")
        print(f"   User: {request.user.username}")
        print(f"   Authenticated: {request.user.is_authenticated}")
        print(f"   Groupe: {getattr(request.user, 'groupe_travail', None)}")
    
    permissions = check_group_permissions(request.user, [], 'add')
    if settings.DEBUG:
        print(f"   Permissions: {permissions}")
    
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        if settings.DEBUG:
            print(f"   ❌ ACCÈS REFUSÉ: {permissions['message']}")
        return redirect('paiements:liste')
    
    # Initialiser les variables pour le contexte (utilisées dans GET et POST)
    contrat_obj_get = None
    reliquats = []
    total_reliquat = 0
    mois_autorises = []  # CORRECTION: Initialiser pour éviter UnboundLocalError
    mois_attendu = ""    # CORRECTION: Initialiser pour éviter UnboundLocalError
    
    if request.method == 'POST':
        form = PaiementForm(request.POST)
        if settings.DEBUG:
            print(f"Données POST: {request.POST}")
            print(f"Formulaire valide: {form.is_valid()}")
        if not form.is_valid():
            if settings.DEBUG:
                print(f"Erreurs du formulaire: {form.errors}")
            # Si le formulaire n'est pas valide, récupérer le contrat depuis les données POST
            try:
                contrat_id_from_form = request.POST.get('contrat')
                if contrat_id_from_form:
                    contrat_obj_get = Contrat.objects.get(pk=contrat_id_from_form, is_deleted=False)
                    from .services_paiement_partiel import ServicePaiementPartiel
                    reliquats = ServicePaiementPartiel.detecter_reliquats_en_cours(contrat_obj_get)
                    total_reliquat = sum(r['montant_restant'] for r in reliquats)
            except (Contrat.DoesNotExist, ValueError):
                pass
            # Re-rendre le formulaire avec les erreurs
            contrats = Contrat.objects.filter(is_deleted=False).select_related('locataire', 'propriete')
            try:
                devise_base = Devise.objects.filter(is_devise_base=True).first()
            except:
                devise_base = None
            current_year = timezone.now().year
            annees_disponibles = list(range(current_year - 2, current_year + 3))
            
            context = {
                'form': form,
                'contrats': contrats,
                'contrat_obj': contrat_obj_get,
                'reliquats': reliquats,
                'total_reliquat': total_reliquat,
                'afficher_alerte_reliquat': len(reliquats) > 0,
                'total_charges_bailleur': 0,
                'net_a_payer': 0,
                'charges_bailleur': [],
                'devise_base': devise_base,
                'annees_disponibles': annees_disponibles,
                'title': 'Ajouter un Paiement - Contexte Intelligent',
            }
            return render(request, 'paiements/ajouter.html', context)
        if form.is_valid():
            try:
                paiement = form.save(commit=False)
                paiement.cree_par = request.user
                
                # *** NOUVEAU : VÉRIFICATION DES RELIQUATS EN COURS ***
                # Vérifier s'il y a des paiements partiels non complétés pour ce contrat
                ignorer_reliquat = request.POST.get('ignorer_reliquat', '') == 'oui'
                
                if not ignorer_reliquat and paiement.contrat:
                    from .services_paiement_partiel import ServicePaiementPartiel
                    reliquats = ServicePaiementPartiel.detecter_reliquats_en_cours(paiement.contrat)
                    
                    if reliquats:
                        # Il y a des reliquats - afficher une alerte et demander confirmation
                        total_reliquat = sum(r['montant_restant'] for r in reliquats)
                        
                        # Préparer le contexte avec les reliquats
                        context = {
                            'form': form,
                            'contrats': Contrat.objects.filter(is_deleted=False).select_related('locataire', 'propriete'),
                            'contrat_obj': paiement.contrat,
                            'reliquats': reliquats,
                            'total_reliquat': total_reliquat,
                            'afficher_alerte_reliquat': True,
                        }
                        
                        # Récupérer la devise de base
                        try:
                            from core.models import Devise
                            devise_base = Devise.objects.filter(is_devise_base=True).first()
                            context['devise_base'] = devise_base
                        except:
                            context['devise_base'] = None
                        
                        # Générer les années disponibles
                        current_year = timezone.now().year
                        context['annees_disponibles'] = list(range(current_year - 2, current_year + 3))
                        
                        return render(request, 'paiements/ajouter.html', context)
                
                # Le champ date_creation sera automatiquement défini par auto_now_add=True
                
                # *** VALIDATION STRICTE : Vérifier que le mois est le mois suivant le dernier paiement ***
                # Cette validation s'applique UNIQUEMENT pour les paiements de LOYER
                if paiement.type_paiement == 'loyer':
                    mois_paye_nom = request.POST.get('mois_paye', '')
                    annee_paiement = request.POST.get('annee_paiement', '')
                    
                    # Si pas de mois spécifié, utiliser le mois attendu
                    if not mois_paye_nom:
                        from .services_paiement_partiel import ServicePaiementPartiel
                        mois_attendu = ServicePaiementPartiel.determiner_mois_a_regler(paiement.contrat)
                        mois_paye_nom = mois_attendu['mois_paye']
                    else:
                        # Si le mois n'a pas d'année, utiliser l'année du champ annee_paiement ou l'année courante
                        import re
                        if not re.search(r'\d{4}', mois_paye_nom):
                            # Pas d'année dans le mois - utiliser l'année du champ annee_paiement
                            if annee_paiement:
                                try:
                                    annee = int(annee_paiement)
                                    mois_paye_nom = f"{mois_paye_nom} {annee}"
                                except ValueError:
                                    # Si l'année n'est pas valide, utiliser l'année courante
                                    from datetime import datetime
                                    annee_actuelle = datetime.now().year
                                    mois_paye_nom = f"{mois_paye_nom} {annee_actuelle}"
                            else:
                                # Pas d'année fournie - utiliser l'année courante
                                from datetime import datetime
                                annee_actuelle = datetime.now().year
                                mois_paye_nom = f"{mois_paye_nom} {annee_actuelle}"
                        else:
                            # Le mois contient déjà une année, mais on peut la remplacer par celle du champ annee_paiement si fournie
                            if annee_paiement:
                                try:
                                    annee = int(annee_paiement)
                                    # Remplacer l'année existante par celle du champ
                                    mois_sans_annee = re.sub(r'\s+\d{4}$', '', mois_paye_nom).strip()
                                    mois_paye_nom = f"{mois_sans_annee} {annee}"
                                except ValueError:
                                    pass  # Garder l'année existante si l'année fournie n'est pas valide
                    
                    # VALIDATION STRICTE pour les paiements de loyer
                    from .services_paiement_partiel import ServicePaiementPartiel
                    validation_mois = ServicePaiementPartiel.valider_mois_a_regler(
                        paiement.contrat, mois_paye_nom, paiement.type_paiement
                    )
                    
                    if not validation_mois['valide']:
                        # Il y a une erreur de validation
                        type_erreur = validation_mois.get('type_erreur', '')
                        
                        if type_erreur == 'mois_avance':
                            # Mois en avance (futur) - proposer d'enregistrer comme avance
                            messages.warning(
                                request,
                                f"{validation_mois['message']} "
                                f"Veuillez changer le type de paiement en 'AVANCE DE LOYER' pour enregistrer ce paiement."
                            )
                            # Recharger le formulaire avec le type changé en avance
                            form = PaiementForm(request.POST)
                            form.data = form.data.copy()
                            form.data['type_paiement'] = 'avance'
                            
                            # Préparer le contexte
                            from core.utils import get_context_with_entreprise_config
                            contrats = Contrat.objects.filter(is_deleted=False).select_related('locataire', 'propriete')
                            try:
                                from core.models import Devise
                                devise_base = Devise.objects.filter(is_devise_base=True).first()
                            except:
                                devise_base = None
                            current_year = timezone.now().year
                            annees_disponibles = list(range(current_year - 2, current_year + 3))
                            
                            context = get_context_with_entreprise_config({
                                'form': form,
                                'contrats': contrats,
                                'contrat_obj': paiement.contrat,
                                'validation_avance': validation_mois,
                                'mois_attendu': validation_mois.get('mois_attendu', ''),
                                'devise_base': devise_base,
                                'annees_disponibles': annees_disponibles,
                                'total_charges_bailleur': 0,
                                'net_a_payer': 0,
                                'charges_bailleur': [],
                            })
                            return render(request, 'paiements/ajouter.html', context)
                        elif type_erreur == 'mois_incorrect':
                            # Mois incorrect (pas le mois attendu) - REFUSER avec suggestion
                            messages.error(
                                request,
                                f"{validation_mois['message']} "
                                f"Si vous souhaitez payer plusieurs mois à l'avance, changez le type de paiement en 'AVANCE DE LOYER'."
                            )
                            return redirect('paiements:ajouter')
                        elif type_erreur == 'mois_deja_paye':
                            # Mois déjà complètement payé - REFUSER
                            messages.error(request, validation_mois['message'])
                            return redirect('paiements:ajouter')
                        else:
                            # Autre erreur (format invalide, etc.) - REFUSER
                            messages.error(request, validation_mois.get('message', 'Erreur de validation'))
                            return redirect('paiements:ajouter')
                    
                    # Validation OK - utiliser le mois validé
                    paiement.mois_paye = validation_mois['mois_attendu']
                    
                    # Afficher un message informatif si c'est un paiement en retard
                    if validation_mois.get('est_retard'):
                        messages.info(request, validation_mois.get('message_info', 'Paiement en retard autorisé pour se rattraper.'))
                elif request.POST.get('mois_paye', ''):
                    # Pour les autres types de paiement (avance, caution), utiliser le mois tel quel
                    mois_paye_nom = request.POST.get('mois_paye', '')
                    from datetime import datetime
                    import re
                    
                    # Si le mois n'a pas d'année, construire le format complet avec l'année courante réelle
                    if not re.search(r'\d{4}', mois_paye_nom):
                        annee_actuelle = datetime.now().year
                        paiement.mois_paye = f"{mois_paye_nom} {annee_actuelle}"
                    else:
                        paiement.mois_paye = mois_paye_nom
                # NOTE: Pour les paiements de loyer, le mois_paye est déjà défini par la validation stricte ci-dessus
                
                # *** DÉTECTION ET SYNCHRONISATION AUTOMATIQUE DES PAIEMENTS PARTIELS ***
                from .services_paiement_partiel import ServicePaiementPartiel
                
                # Détecter si c'est un paiement partiel
                est_partiel = ServicePaiementPartiel.synchroniser_paiement_partiel(paiement)
                
                # Sauvegarder le paiement avec les informations de paiement partiel
                paiement.save()
                
                # Générer la référence si elle n'existe pas
                if not paiement.reference_paiement:
                    paiement.reference_paiement = paiement.generate_reference_paiement()
                    paiement.save()
                
                # VÉRIFIER SI CE PAIEMENT COMPLÈTE UN RELIQUAT
                # Cette vérification est faite automatiquement dans synchroniser_paiement_partiel
                # mais on la refait ici pour s'assurer que tout est à jour
                if paiement.mois_paye:
                    calcul_restant = ServicePaiementPartiel.calculer_montant_restant(
                        paiement.contrat, paiement.mois_paye
                    )
                    if calcul_restant.get('est_complet', False):
                        messages.success(
                            request,
                            f'✅ Reliquat complété ! Le mois {paiement.mois_paye} est maintenant entièrement payé. '
                            f'Tous les paiements partiels concernés ont été marqués comme complétés.'
                        )
                    elif est_partiel:
                        messages.info(
                            request,
                            f'Paiement partiel détecté: {paiement.reference_paiement} - '
                            f'Montant payé: {paiement.montant} F CFA, '
                            f'Montant restant: {paiement.montant_restant_du} F CFA'
                        )
                
                # *** SYNCHRONISATION AUTOMATIQUE DES AVANCES ***
                # Si c'est un paiement d'avance, synchroniser automatiquement l'avance
                if paiement.type_paiement == 'avance':
                    try:
                        from .services_synchronisation_avances import ServiceSynchronisationAvances
                        avance = ServiceSynchronisationAvances.synchroniser_avance_avec_paiement(paiement)
                        if avance:
                            messages.success(request, f'Paiement {paiement.reference_paiement} créé avec succès! '
                                                    f'Avance de {avance.nombre_mois_couverts} mois synchronisée automatiquement.')
                        else:
                            messages.warning(request, f'Paiement {paiement.reference_paiement} créé, mais erreur lors de la synchronisation de l\'avance.')
                    except Exception as e:
                        messages.warning(request, f'Paiement {paiement.reference_paiement} créé, mais erreur lors de la synchronisation de l\'avance: {str(e)}')
                elif paiement.type_paiement == 'loyer':
                    # *** VALIDATION INTELLIGENTE DES PAIEMENTS DE LOYER ***
                    try:
                        from .services_avance import ServiceGestionAvance
                        from .models_avance import AvanceLoyer
                        from datetime import datetime
                        from dateutil.relativedelta import relativedelta
                        
                        # *** SYNCHRONISATION AUTOMATIQUE DES AVANCES ***
                        # Synchroniser toutes les consommations manquantes avant le traitement
                        ServiceGestionAvance.synchroniser_consommations_manquantes(paiement.contrat)
                        
                        # Déterminer le mois du paiement
                        mois_paiement = paiement.date_paiement.replace(day=1)
                        
                        # Validation 2: Vérifier les avances actives
                        avances_actives = AvanceLoyer.objects.filter(
                            contrat=paiement.contrat,
                            statut='active',
                            montant_restant__gt=0
                        )
                        
                        if avances_actives.exists():
                            # Il y a des avances actives - vérifier que le mois correspond
                            prochain_mois_attendu = ServiceGestionAvance.calculer_prochain_mois_paiement(paiement.contrat)
                            
                            if mois_paiement != prochain_mois_attendu:
                                messages.error(request, f'Avec les avances actives, vous devez payer pour {prochain_mois_attendu.strftime("%B %Y")}. '
                                                      f'Créez une avance si vous voulez payer pour un autre mois.')
                                return redirect('paiements:ajouter')
                            
                            # L'avance couvre ce mois - ajuster le montant du paiement
                            avance_couvre, montant_avance = ServiceGestionAvance.verifier_avance_pour_mois(
                                paiement.contrat, mois_paiement
                            )
                            
                            if avance_couvre:
                                paiement.montant = montant_avance
                                paiement.save()
                                
                                # Consommer l'avance pour ce mois
                                avance_consommee, montant_consomme = ServiceGestionAvance.consommer_avance_pour_mois(
                                    paiement.contrat, mois_paiement
                                )
                                
                                messages.success(request, f'Paiement {paiement.reference_paiement} ajusté avec l\'avance! '
                                                        f'Montant: {montant_consomme} F CFA pour {mois_paiement.strftime("%B %Y")}')
                            else:
                                messages.success(request, f'Paiement {paiement.reference_paiement} créé avec succès!')
                        else:
                            # Pas d'avances - la validation stricte a déjà été faite plus haut
                            # Le mois_paye a été validé et est garanti d'être le mois suivant le dernier paiement
                            messages.success(request, f'Paiement {paiement.reference_paiement} créé avec succès!')
                            
                    except Exception as e:
                        messages.warning(request, f'Paiement {paiement.reference_paiement} créé, mais erreur lors de la validation: {str(e)}')
                
                # *** NOUVEAU : Vérifier et créer des avances pour les paiements d'avance existants ***
                # Cette logique s'exécute à chaque ajout de paiement pour s'assurer que tous les paiements d'avance
                # sont convertis en AvanceLoyer actifs
                try:
                    from .models import Paiement as PaiementModel  # Import explicite
                    from .models_avance import AvanceLoyer
                    from .services_avance import ServiceGestionAvance
                    from decimal import Decimal
                    
                    # Trouver tous les paiements d'avance de ce contrat qui n'ont pas encore d'AvanceLoyer correspondant
                    paiements_avance_manquants = PaiementModel.objects.filter(
                        contrat=paiement.contrat,
                        type_paiement='avance',
                        statut='valide'
                    )
                    
                    for paiement_avance in paiements_avance_manquants:
                        # Vérifier si un AvanceLoyer existe déjà pour ce paiement
                        avance_existant = AvanceLoyer.objects.filter(
                            contrat=paiement_avance.contrat,
                            montant_avance=paiement_avance.montant,
                            date_avance=paiement_avance.date_paiement
                        ).first()
                        
                        if not avance_existant:
                            # Créer l'AvanceLoyer manquant
                            try:
                                avance = ServiceGestionAvance.creer_avance_loyer(
                                    contrat=paiement_avance.contrat,
                                    montant_avance=Decimal(str(paiement_avance.montant)),
                                    date_avance=paiement_avance.date_paiement,
                                    notes=f"Créé automatiquement depuis paiement {paiement_avance.id}"
                                )
                                print(f"AvanceLoyer créé automatiquement: {avance.id} pour paiement {paiement_avance.id}")
                            except Exception as e:
                                print(f"Erreur création AvanceLoyer pour paiement {paiement_avance.id}: {str(e)}")
                                
                except Exception as e:
                    print(f"Erreur lors de la vérification des avances manquantes: {str(e)}")
                
                return redirect('paiements:liste')
                
            except Exception as e:
                import traceback
                error_details = traceback.format_exc()
                print(f"Erreur détaillée: {error_details}")
                messages.error(request, f'Erreur lors de la validation du paiement: {str(e)}')
    else:
        # Vérifier s'il y a un contrat sélectionné dans le GET pour afficher les reliquats
        contrat_id_get = request.GET.get('contrat_id')
        
        if contrat_id_get:
            try:
                contrat_obj_get = Contrat.objects.get(pk=contrat_id_get, is_deleted=False)
                from .services_paiement_partiel import ServicePaiementPartiel
                reliquats = ServicePaiementPartiel.detecter_reliquats_en_cours(contrat_obj_get)
                total_reliquat = sum(r['montant_restant'] for r in reliquats)
                
                # Calculer les mois autorisés pour les paiements de loyer
                # Mois attendu + mois en retard (pour rattrapage)
                mois_attendu_data = ServicePaiementPartiel.determiner_mois_a_regler(contrat_obj_get)
                mois_attendu = mois_attendu_data['mois_paye']
                date_mois_attendu = mois_attendu_data['date_mois']
                
                # Construire la liste des mois autorisés
                mois_autorises = [{
                    'mois_paye': mois_attendu,
                    'mois_label': f"{mois_attendu} (Mois attendu)"
                }]
                
                # Ajouter les mois en retard (mois entre le début du contrat et le mois attendu)
                from datetime import date
                from dateutil.relativedelta import relativedelta
                mois_courant = timezone.now().date().replace(day=1)
                mois_francais = [
                    'janvier', 'février', 'mars', 'avril', 'mai', 'juin',
                    'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre'
                ]
                
                # CRITIQUE : Récupérer le dernier paiement validé pour déterminer le point de départ
                from .models import Paiement
                dernier_paiement = Paiement.objects.filter(
                    contrat=contrat_obj_get,
                    type_paiement='loyer',
                    statut='valide',
                    is_deleted=False
                ).order_by('-date_paiement').first()
                
                # Déterminer le dernier mois payé (basé sur mois_paye si disponible)
                dernier_mois_paye_date = None
                if dernier_paiement:
                    if dernier_paiement.mois_paye:
                        dernier_mois_paye_date = ServicePaiementPartiel.convertir_mois_paye_en_date(dernier_paiement.mois_paye)
                    if not dernier_mois_paye_date:
                        dernier_mois_paye_date = dernier_paiement.date_paiement.replace(day=1)
                else:
                    # Pas de paiement précédent - utiliser le début du contrat
                    dernier_mois_paye_date = contrat_obj_get.date_debut.replace(day=1) if contrat_obj_get.date_debut else None
                
                # Calculer UNIQUEMENT les mois en retard entre le dernier paiement et le mois attendu
                if dernier_mois_paye_date:
                    mois_en_retard = dernier_mois_paye_date + relativedelta(months=1)  # Commencer au mois suivant le dernier paiement
                    
                    # Parcourir uniquement les mois entre le dernier paiement et le mois attendu
                    while mois_en_retard < date_mois_attendu:
                        # Vérifier si ce mois est déjà complètement payé
                        mois_str = f"{mois_francais[mois_en_retard.month - 1]} {mois_en_retard.year}"
                        paiements_mois = Paiement.objects.filter(
                            contrat=contrat_obj_get,
                            mois_paye=mois_str,
                            type_paiement='loyer',
                            is_deleted=False,
                            statut='valide'
                        )
                        
                        if paiements_mois.exists():
                            total_paye = sum(p.montant for p in paiements_mois)
                            montant_du_mois = ServicePaiementPartiel.calculer_montant_du_mois(contrat_obj_get, mois_str)
                            # Si le mois est complètement payé, ne pas l'ajouter
                            if total_paye >= montant_du_mois:
                                mois_en_retard = mois_en_retard + relativedelta(months=1)
                                continue
                        
                        # Ajouter ce mois en retard à la liste (seulement s'il est non payé ou partiellement payé)
                        mois_autorises.append({
                            'mois_paye': mois_str,
                            'mois_label': f"{mois_str} (Rattrapage)"
                        })
                        
                        mois_en_retard = mois_en_retard + relativedelta(months=1)
                
            except Contrat.DoesNotExist:
                pass
        
        # Initialiser le formulaire avec les mois autorisés pour les paiements de loyer
        if contrat_id_get:
            form = PaiementForm(contrat_id=contrat_id_get, mois_autorises=mois_autorises, type_paiement_initial='loyer')
        else:
            form = PaiementForm()
    
    # Récupérer tous les contrats pour la sélection
    contrats = Contrat.objects.filter(is_deleted=False).select_related('locataire', 'propriete')
    
    # Récupérer la devise de base
    try:
        devise_base = Devise.objects.filter(is_devise_base=True).first()
    except:
        devise_base = None
    
    # Générer les années disponibles (année actuelle ± 2 ans)
    current_year = timezone.now().year
    annees_disponibles = list(range(current_year - 2, current_year + 3))
    
    context = {
        'form': form,
        'contrats': contrats,
        'contrat_obj': contrat_obj_get,
        'reliquats': reliquats,  # NOUVEAU : Reliquats détectés
        'total_reliquat': total_reliquat,  # NOUVEAU : Total des reliquats
        'afficher_alerte_reliquat': len(reliquats) > 0,  # NOUVEAU : Afficher l'alerte si reliquats
        'mois_attendu': mois_attendu,  # Mois attendu pour affichage
        'mois_autorises': mois_autorises,  # Liste des mois autorisés
        'total_charges_bailleur': 0,
        'net_a_payer': 0,
        'charges_bailleur': [],
        'devise_base': devise_base,
        'annees_disponibles': annees_disponibles,
        'title': 'Ajouter un Paiement - Contexte Intelligent',
    }
    
    return render(request, 'paiements/ajouter.html', context)

@login_required
def liste_paiements(request):
    """Liste des paiements avec recherche et filtres optimisés."""
    try:
        # Récupérer les filtres
        query = request.GET.get('q', '')
        statut_filter = request.GET.get('statut', '')
        type_filter = request.GET.get('type_paiement', '')
        date_debut = request.GET.get('date_debut', '')
        date_fin = request.GET.get('date_fin', '')
        
        # Base QuerySet avec annotations optimisées
        from django.db.models import Sum, Count, F, Case, When, DecimalField, Q
        
        # Filtrer les paiements en excluant les doublons et en affichant la propriété
        paiements = Paiement.objects.filter(is_deleted=False).select_related(
            'contrat__locataire', 'contrat__propriete', 'contrat__propriete__bailleur', 'cree_par'
        ).exclude(
            # Exclure les paiements de caution qui ne sont pas marqués comme payés
            Q(type_paiement='caution') & Q(contrat__caution_payee=False)
        ).exclude(
            # Exclure les paiements d'avance qui ne sont pas marqués comme payés
            Q(type_paiement='avance') & Q(contrat__avance_loyer_payee=False)
        ).distinct().annotate(  # Éviter les doublons
            # Montant total formaté
            montant_total_formatted=Case(
                When(montant__isnull=False, then='montant'),
                default=0,
                output_field=DecimalField(max_digits=10, decimal_places=2)
            ),
            # Nom complet du locataire
            locataire_nom_complet=Case(
                When(contrat__locataire__nom__isnull=False, 
                     contrat__locataire__prenom__isnull=False,
                     then=F('contrat__locataire__nom') + ' ' + F('contrat__locataire__prenom')),
                When(contrat__locataire__nom__isnull=False,
                     then=F('contrat__locataire__nom')),
                default='Locataire inconnu',
                output_field=models.CharField(max_length=200)
            ),
            # Adresse complète de la propriété
            propriete_adresse_complete=Case(
                When(contrat__propriete__adresse__isnull=False,
                     contrat__propriete__ville__isnull=False,
                     then=F('contrat__propriete__adresse') + ', ' + F('contrat__propriete__ville')),
                When(contrat__propriete__adresse__isnull=False,
                     then=F('contrat__propriete__adresse')),
                default='Adresse non renseignée',
                output_field=models.CharField(max_length=300)
            )
        ).order_by('-created_at')
        
        # Récupérer le paiement de test pour l'afficher en premier
        paiement_test = Paiement.objects.filter(
            reference_paiement__startswith='PAIEMENT-TEST',
            is_deleted=False
        ).first()
        
        # Recherche optimisée
        if query:
            paiements = paiements.filter(
                Q(reference_paiement__icontains=query) |
                Q(contrat__numero_contrat__icontains=query) |
                Q(contrat__locataire__nom__icontains=query) |
                Q(contrat__locataire__prenom__icontains=query) |
                Q(contrat__propriete__adresse__icontains=query) |
                Q(contrat__propriete__ville__icontains=query) |
                Q(contrat__propriete__titre__icontains=query) |
                Q(libelle__icontains=query)
            )
        
        # Filtres optimisés
        if statut_filter:
            paiements = paiements.filter(statut=statut_filter)
        
        if type_filter:
            paiements = paiements.filter(type_paiement=type_filter)
        
        # Filtres de dates
        if date_debut:
            paiements = paiements.filter(date_paiement__gte=date_debut)
        
        if date_fin:
            paiements = paiements.filter(date_paiement__lte=date_fin)
        
        # Calcul des statistiques avec requêtes optimisées (montant masqué pour sécurité)
        total_paiements = paiements.count()
        # montant_total masqué pour sécurité
        
        # Statistiques par statut (montants masqués pour sécurité)
        stats_par_statut = paiements.values('statut').annotate(
            count=Count('id')
        ).order_by('statut')
        
        # Statistiques par type (montants masqués pour sécurité)
        stats_par_type = paiements.values('type_paiement').annotate(
            count=Count('id')
        ).order_by('type_paiement')
        
        # Pagination
        paginator = Paginator(paiements, 20)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context = {
            'page_obj': page_obj,
            'paiements': page_obj,
            'paiement_test': paiement_test,
            'statuts': Paiement.STATUT_CHOICES,
            'types_paiement': Paiement.TYPE_PAIEMENT_CHOICES,
            'query': query,
            'statut_filter': statut_filter,
            'type_filter': type_filter,
            'date_debut': date_debut,
            'date_fin': date_fin,
            'title': 'Liste des Paiements',
            'statistiques': {
                'total_paiements': total_paiements,
                'stats_par_statut': stats_par_statut,
                'stats_par_type': stats_par_type,
            },
            'filtres_actifs': {
                'query': query,
                'statut': statut_filter,
                'type_paiement': type_filter,
                'date_debut': date_debut,
                'date_fin': date_fin,
            }
        }
        
        return render(request, 'paiements/liste.html', context)
        
    except Exception as e:
        messages.error(request, f"Erreur lors du chargement des paiements: {str(e)}")
        return render(request, 'paiements/liste.html', {'paiements': [], 'title': 'Liste des Paiements'})

@login_required
@require_POST
def valider_paiement(request, pk):
    """Valider un paiement."""
    try:
        paiement = get_object_or_404(Paiement, pk=pk, is_deleted=False)
        
        # Vérification des permissions simplifiée
        if not request.user.is_authenticated:
            return JsonResponse({
                'success': False,
                'error': 'Utilisateur non authentifié'
            }, status=403)
        
        # Vérifier que l'utilisateur est dans un des groupes autorisés
        from core.utils import check_group_permissions
        permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE', 'CAISSE'], 'change')
        
        if not permissions['allowed']:
            return JsonResponse({
                'success': False,
                'error': f'Permissions insuffisantes. {permissions["message"]}'
            }, status=403)
        
        # Vérifier que le paiement n'est pas déjà validé
        if paiement.statut == 'valide':
            return JsonResponse({
                'success': False,
                'error': 'Ce paiement est déjà validé'
            }, status=400)
        
        # Valider le paiement
        ancien_statut = paiement.statut
        paiement.statut = 'valide'
        paiement.valide_par = request.user
        paiement.date_encaissement = timezone.now().date()
        paiement.save()
        
        message_succes = '✅ Paiement validé avec succès!'
        messages.success(request, message_succes)
        
        return JsonResponse({
            'success': True,
            'message': message_succes,
            'paiement_id': paiement.pk,
            'statut': paiement.statut
        })
        
    except Exception as e:
        error_message = f'Erreur lors de la validation: {str(e)}'
        messages.error(request, error_message)
        return JsonResponse({
            'success': False,
            'error': error_message
        }, status=500)

@login_required
@require_POST
def refuser_paiement(request, pk):
    """Refuser un paiement."""
    try:
        paiement = get_object_or_404(Paiement, pk=pk, is_deleted=False)
        
        # Vérification des permissions simplifiée
        if not request.user.is_authenticated:
            return JsonResponse({
                'success': False,
                'error': 'Utilisateur non authentifié'
            }, status=403)
        
        # Vérifier que l'utilisateur est dans un des groupes autorisés
        from core.utils import check_group_permissions
        permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION'], 'change')
        
        if not permissions['allowed']:
            return JsonResponse({
                'success': False,
                'error': f'Permissions insuffisantes. {permissions["message"]}'
            }, status=403)
        
        # Vérifier que le paiement n'est pas déjà validé
        if paiement.statut == 'valide':
            return JsonResponse({
                'success': False,
                'error': 'Impossible de refuser un paiement déjà validé'
            }, status=400)
        
        # Refuser le paiement
        ancien_statut = paiement.statut
        paiement.statut = 'refuse'
        paiement.save()
        
        message_succes = '❌ Paiement refusé avec succès'
        messages.success(request, message_succes)
        
        return JsonResponse({
            'success': True,
            'message': message_succes,
            'paiement_id': paiement.pk,
            'statut': paiement.statut
        })
        
    except Exception as e:
        error_message = f'Erreur lors du refus: {str(e)}'
        messages.error(request, error_message)
        return JsonResponse({
            'success': False,
            'error': error_message
        }, status=500)

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
def modifier_paiement(request, pk):
    """Modifier un paiement existant."""
    paiement = get_object_or_404(Paiement, pk=pk)
    
    # Vérification des permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE', 'CAISSE'], 'modify')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:paiement_detail', pk=pk)
    
    old_data = {f.name: getattr(paiement, f.name) for f in paiement._meta.fields}
    
    if request.method == 'POST':
        form = PaiementForm(request.POST, instance=paiement)
        if form.is_valid():
            # Sauvegarder l'ancien statut pour vérifier les changements
            ancien_statut = paiement.statut
            form.save()
            
            # Générer automatiquement un reçu si le statut passe à "valide"
            if ancien_statut != 'valide' and paiement.statut == 'valide':
                try:
                    paiement.generer_recu_automatique(request.user)
                    messages.success(request, 'Paiement modifié et reçu généré automatiquement!')
                except Exception as e:
                    messages.warning(request, f'Paiement modifié mais erreur lors de la génération du reçu: {str(e)}')
            else:
                messages.success(request, 'Paiement modifié avec succès!')
            
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
            
            return redirect('paiements:paiement_detail', pk=pk)
    else:
        form = PaiementForm(instance=paiement)
    
    context = {
        'form': form,
        'paiement': paiement,
        'title': 'Modifier le paiement',
    }
    
    return render(request, 'paiements/paiement_form.html', context)


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
    permissions = check_group_permissions(request.user, [], 'add')
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
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE', 'CAISSE'], 'view')
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
            Q(contrat__propriete__titre__icontains=query) |
            Q(contrat__propriete__ville__icontains=query) |
            Q(contrat__numero_contrat__icontains=query) |
            Q(reference_paiement__icontains=query) |
            Q(type_paiement__icontains=query) |
            Q(statut__icontains=query) |
            Q(notes__icontains=query) |
            Q(libelle__icontains=query)
        ).select_related(
            'contrat__locataire',
            'contrat__propriete'
        ).order_by('-created_at')[:20]
    
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
    """Ajouter un retrait bailleur avec déduction automatique des charges."""
    # Vérification des permissions - Tous les groupes peuvent créer des retraits
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE', 'CAISSE', 'CONTROLES', 'GESTIONNAIRE'], 'view')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:liste')
    
    # Note: Cette vue permet la création de retraits manuels sans conditions temporelles
    # Les conditions temporelles ne s'appliquent qu'aux retraits automatiques
    
    if request.method == 'POST':
        form = RetraitBailleurForm(request.POST)
        if form.is_valid():
            # Rediriger vers le récapitulatif au lieu de créer directement
            bailleur_id = form.cleaned_data.get('bailleur').id
            mois_retrait = form.cleaned_data.get('mois_retrait')
            
            if mois_retrait:
                # S'assurer que c'est le premier jour du mois
                if mois_retrait.day != 1:
                    mois_retrait = mois_retrait.replace(day=1)
                
                # Rediriger vers le récapitulatif
                return redirect(f'{reverse("paiements:recap_retrait_bailleur", args=[bailleur_id])}?mois={mois_retrait.month}&annee={mois_retrait.year}')
            else:
                messages.error(request, 'Veuillez sélectionner un mois de retrait.')
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
def creer_retrait_depuis_recap(request):
    """Crée le retrait depuis le récapitulatif avec déduction automatique des charges."""
    # Vérification des permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE', 'CAISSE'], 'view')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:liste')
    
    if request.method == 'POST':
        # Récupérer les données du formulaire
        bailleur_id = request.POST.get('bailleur')
        mois_retrait = request.POST.get('mois_retrait')
        montant_loyers_bruts = request.POST.get('montant_loyers_bruts')
        montant_charges_deductibles = request.POST.get('montant_charges_deductibles')
        montant_net_a_payer = request.POST.get('montant_net_a_payer')
        
        try:
            from .services_retrait import ServiceGestionRetrait
            from datetime import datetime
            
            # Récupérer le bailleur
            bailleur = Bailleur.objects.get(id=bailleur_id)
            
            # Convertir la date du mois
            mois_date = datetime.strptime(mois_retrait, '%Y-%m-%d').date()
            
            # Créer le retrait avec restrictions et calcul optimisé
            resultat = ServiceGestionRetrait.creer_retrait_avec_restrictions(
                bailleur, mois_date, request.user
            )
            
            if resultat['success']:
                messages.success(request, resultat['message'])
                if resultat.get('charges_appliquees', 0) > 0:
                    messages.info(request, f"{resultat['charges_appliquees']} charge(s) appliquée(s) automatiquement")
            else:
                messages.error(request, resultat['message'])
            
            return redirect('paiements:retraits_liste')
            
        except Exception as e:
            messages.error(request, f'Erreur lors de la création du retrait: {str(e)}')
            return redirect('paiements:retraits_liste')
    
    return redirect('paiements:retraits_liste')

@login_required
def recap_retrait_bailleur(request, bailleur_id):
    """Affiche le récapitulatif avant création du retrait avec les charges à déduire."""
    # Vérification des permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE', 'CAISSE'], 'view')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:liste')
    
    # Récupérer le bailleur
    bailleur = get_object_or_404(Bailleur, pk=bailleur_id)
    
    # Récupérer le mois depuis les paramètres GET
    mois = request.GET.get('mois')
    annee = request.GET.get('annee')
    
    if not mois or not annee:
        # Par défaut, mois actuel
        from django.utils import timezone
        mois_actuel = timezone.now()
        mois = mois_actuel.month
        annee = mois_actuel.year
    
    try:
        mois = int(mois)
        annee = int(annee)
    except (ValueError, TypeError):
        messages.error(request, 'Mois ou année invalide.')
        return redirect('paiements:retraits_liste')
    
    # Créer un retrait temporaire pour les calculs
    from datetime import date
    mois_retrait = date(annee, mois, 1)
    
    # Utiliser le service intelligent pour calculer le retrait
    from .services_retraits_bailleur import ServiceRetraitsBailleurIntelligent
    calcul_retrait = ServiceRetraitsBailleurIntelligent.calculer_retrait_mensuel_bailleur(
        bailleur, mois, annee
    )
    
    # Calculer les charges qui seront déduites
    retrait_temp = RetraitBailleur(
        bailleur=bailleur,
        mois_retrait=mois_retrait,
        montant_loyers_bruts=calcul_retrait['total_loyers'],
        montant_charges_deductibles=calcul_retrait['total_charges_deductibles'],
        montant_net_a_payer=calcul_retrait['montant_net']
    )
    
    charges_calcul = retrait_temp.calculer_charges_automatiquement()
    
    # Récupérer les propriétés du bailleur avec leurs unités locatives
    proprietes = Propriete.objects.filter(
        bailleur=bailleur,
        is_deleted=False
    ).select_related('type_bien').prefetch_related('unites_locatives__contrats__locataire')
    
    # Utiliser la méthode du modèle pour calculer les loyers
    proprietes_avec_loyers = []
    for propriete in proprietes:
        unites_locatives = propriete.unites_locatives.filter(is_deleted=False)
        
        proprietes_avec_loyers.append({
            'propriete': propriete,
            'loyer_total': propriete.get_loyer_actuel_calcule(),
            'unites_locatives': unites_locatives
        })
    
    context = get_context_with_entreprise_config({
        'bailleur': bailleur,
        'mois': mois,
        'annee': annee,
        'mois_retrait': mois_retrait,
        'calcul_retrait': calcul_retrait,
        'charges_calcul': charges_calcul,
        'proprietes': proprietes_avec_loyers,
        'title': f'Récapitulatif Retrait - {bailleur.nom} {bailleur.prenom}'
    })
    
    return render(request, 'paiements/recap_retrait_bailleur.html', context)

@login_required
def detail_retrait(request, pk):
    """Afficher le détail d'un retrait bailleur SÉCURISÉ."""
    # Vérification des permissions avec fallback pour PRIVILEGE
    permissions = check_group_permissions_with_fallback(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE', 'CAISSE'], 'view')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:dashboard')
    
    # Récupérer le retrait avec toutes les relations nécessaires
    retrait = get_object_or_404(
        RetraitBailleur.objects.select_related(
            'bailleur',
            'cree_par',
            'valide_par'
        ),
        pk=pk,
        is_deleted=False
    )
    
    # Vérifier si l'utilisateur peut voir les montants (PRIVILEGE uniquement)
    can_see_amounts = check_group_permissions(request.user, ['PRIVILEGE'], 'view')['allowed']
    
    # Gérer l'affichage des montants confidentiels via session
    show_confidential = request.session.get('show_confidential_amounts', False)
    if request.GET.get('toggle_confidential') == '1':
        show_confidential = not show_confidential
        request.session['show_confidential_amounts'] = show_confidential
    
    # L'utilisateur peut voir les montants s'il a les permissions OU s'il a activé l'affichage confidentiel
    display_amounts = can_see_amounts or show_confidential
    
    # Récupérer les propriétés louées avec leurs détails pour le mois du retrait
    proprietes_louees = []
    total_loyers_bruts = Decimal('0')
    total_charges_deductibles = Decimal('0')
    total_charges_bailleur = Decimal('0')
    
    from proprietes.models import Propriete
    from contrats.models import Contrat
    from proprietes.models import ChargesBailleur
    from paiements.models import ChargeDeductible
    from decimal import Decimal
    
    # Récupérer toutes les propriétés du bailleur avec des contrats actifs et unités locatives
    proprietes = Propriete.objects.filter(
        bailleur=retrait.bailleur,
        is_deleted=False
    ).prefetch_related(
        'contrats__locataire',
        'unites_locatives__contrats__locataire'
    )
    
    for propriete in proprietes:
        # Récupérer les unités locatives de cette propriété
        unites_locatives = propriete.unites_locatives.filter(is_deleted=False)
        
        # Calculer les montants pour le mois du retrait
        mois_retrait = retrait.mois_retrait
        
        # Initialiser les valeurs par défaut
        loyer_mensuel = Decimal('0')
        charges_mensuelles = Decimal('0')
        loyer_brut = Decimal('0')
        charges_deductibles = Decimal('0')
        charges_bailleur = Decimal('0')
        montant_net = Decimal('0')
        
        # Calculer les totaux des unités locatives
        total_loyer_unites = Decimal('0')
        total_charges_unites = Decimal('0')
        total_brut_unites = Decimal('0')
        total_charges_deductibles_unites = Decimal('0')
        total_charges_bailleur_unites = Decimal('0')
        
        # Si la propriété a des unités locatives, calculer à partir des unités
        if unites_locatives.exists():
            for unite in unites_locatives:
                # Récupérer les contrats actifs de cette unité
                contrats_unite = unite.contrats.filter(
                    est_actif=True,
                    est_resilie=False
                )
                
                # Si l'unité a des contrats actifs, utiliser les montants des contrats
                if contrats_unite.exists():
                    for contrat in contrats_unite:
                        # Utiliser les montants du contrat, pas de l'unité
                        contrat_loyer = Decimal(str(contrat.loyer_mensuel or '0'))
                        contrat_charges = Decimal(str(contrat.charges_mensuelles or '0'))
                        contrat_brut = contrat_loyer + contrat_charges
                        
                        total_loyer_unites += contrat_loyer
                        total_charges_unites += contrat_charges
                        total_brut_unites += contrat_brut
                        
                        # Calculer les charges déductibles pour ce contrat
                        charges_deductibles_contrat = ChargeDeductible.objects.filter(
                            contrat=contrat,
                            date_charge__year=mois_retrait.year,
                            date_charge__month=mois_retrait.month,
                            statut='validee'
                        ).aggregate(total=Sum('montant'))['total'] or Decimal('0')
                        total_charges_deductibles_unites += charges_deductibles_contrat
                else:
                    # Si pas de contrat actif, utiliser les montants de l'unité (pour les unités libres)
                    unite_loyer = Decimal(str(unite.loyer_mensuel or '0'))
                    unite_charges = Decimal(str(unite.charges_mensuelles or '0'))
                    unite_brut = unite_loyer + unite_charges
                    
                    total_loyer_unites += unite_loyer
                    total_charges_unites += unite_charges
                    total_brut_unites += unite_brut
                
                # Calculer les charges bailleur pour cette unité (une seule fois par unité)
                charges_bailleur_unite = ChargesBailleur.objects.filter(
                    propriete=propriete,
                    date_charge__year=mois_retrait.year,
                    date_charge__month=mois_retrait.month,
                    statut__in=['en_attente', 'deduite_retrait']
                ).aggregate(total=Sum('montant_restant'))['total'] or Decimal('0')
                total_charges_bailleur_unites += charges_bailleur_unite
            
            # Utiliser les totaux des unités pour la propriété
            loyer_mensuel = total_loyer_unites
            charges_mensuelles = total_charges_unites
            loyer_brut = total_brut_unites
            charges_deductibles = total_charges_deductibles_unites
            charges_bailleur = total_charges_bailleur_unites
            montant_net = loyer_brut - charges_deductibles - charges_bailleur
            
        else:
            # Si pas d'unités, chercher un contrat direct sur la propriété
            contrat_actif = propriete.contrats.filter(
                est_actif=True,
                est_resilie=False
            ).first()
            
            if contrat_actif:
                # Loyers bruts (loyer + charges mensuelles)
                loyer_mensuel = Decimal(str(contrat_actif.loyer_mensuel or '0'))
                charges_mensuelles = Decimal(str(contrat_actif.charges_mensuelles or '0'))
                loyer_brut = loyer_mensuel + charges_mensuelles
                
                # Charges déductibles pour le mois
                charges_deductibles = ChargeDeductible.objects.filter(
                    contrat=contrat_actif,
                    date_charge__year=mois_retrait.year,
                    date_charge__month=mois_retrait.month,
                    statut='validee'
                ).aggregate(total=Sum('montant'))['total'] or Decimal('0')
                
                # Montant net pour cette propriété
                montant_net = loyer_brut - charges_deductibles - charges_bailleur
            
            # Charges bailleur pour le mois (même sans contrat actif)
            charges_bailleur = ChargesBailleur.objects.filter(
                propriete=propriete,
                date_charge__year=mois_retrait.year,
                date_charge__month=mois_retrait.month,
                statut__in=['en_attente', 'deduite_retrait']
            ).aggregate(total=Sum('montant_restant'))['total'] or Decimal('0')
        
        # Créer le détail de la propriété
        propriete_detail = {
            'propriete': propriete,
            'contrat': contrat_actif if not unites_locatives.exists() else None,
            'locataire': contrat_actif.locataire if not unites_locatives.exists() and contrat_actif else None,
            'loyer_mensuel': loyer_mensuel,
            'charges_mensuelles': charges_mensuelles,
            'loyer_brut': loyer_brut,
            'charges_deductibles': charges_deductibles,
            'charges_bailleur': charges_bailleur,
            'montant_net': montant_net,
            'statut_contrat': 'Avec unités' if unites_locatives.exists() else ('Actif' if contrat_actif else 'Aucun contrat actif'),
            'a_contrat_actif': bool(contrat_actif) or unites_locatives.exists(),
            'unites_locatives': unites_locatives,
            'total_loyer_unites': total_loyer_unites,
            'total_charges_unites': total_charges_unites,
            'total_brut_unites': total_brut_unites,
            'nombre_unites': unites_locatives.count()
        }
        
        proprietes_louees.append(propriete_detail)
        
        # Cumuler les totaux
        total_loyers_bruts += loyer_brut
        total_charges_deductibles += charges_deductibles
        total_charges_bailleur += charges_bailleur
    
    # Calculer le montant net total
    montant_net_total = total_loyers_bruts - total_charges_deductibles - total_charges_bailleur
    
    # Récupérer les charges disponibles pour ce retrait
    from paiements.services_charges_bailleur import ServiceChargesBailleurIntelligent
    charges_data = ServiceChargesBailleurIntelligent.calculer_charges_bailleur_pour_mois(
        retrait.bailleur, retrait.mois_retrait
    )
    
    # Vérifier si le retrait peut être modifié
    peut_etre_modifie = retrait.statut in ['en_attente']
    
    context = get_context_with_entreprise_config({
        'retrait': retrait,
        'can_see_amounts': can_see_amounts,  # Flag pour le template (permissions)
        'display_amounts': display_amounts,  # Flag pour l'affichage réel
        'show_confidential': show_confidential,  # Flag pour l'état de l'affichage confidentiel
        'proprietes_louees': proprietes_louees,
        'total_loyers_bruts': total_loyers_bruts,
        'total_charges_deductibles': total_charges_deductibles,
        'total_charges_bailleur': total_charges_bailleur,
        'montant_net_total': montant_net_total,
        'charges_disponibles': charges_data.get('charges_details', []),
        'total_charges_disponibles': charges_data.get('total_charges', Decimal('0')),
        'peut_etre_modifie': peut_etre_modifie,
        'title': f'Détails du Retrait #{retrait.id}'
    })
    
    return render(request, 'paiements/retraits/retrait_detail.html', context)

@login_required
def modifier_retrait(request, pk):
    """Modifier un retrait bailleur."""
    # Vérification des permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE', 'CAISSE'], 'change')
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
    # Vérification des permissions avec fallback pour PRIVILEGE
    permissions = check_group_permissions_with_fallback(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE', 'CAISSE'], 'view')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:dashboard')
    
    # Vérifier si l'utilisateur est PRIVILEGE
    is_privilege_user = hasattr(request.user, 'groupe_travail') and request.user.groupe_travail and request.user.groupe_travail.nom == 'PRIVILEGE'
    
    # Récupérer les récapitulatifs avec filtres (non supprimés uniquement)
    recaps = RecapMensuel.objects.filter(is_deleted=False).select_related(
        'bailleur', 'cree_par', 'modifie_par'
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
    bailleurs = Bailleur.objects.all().order_by('nom', 'prenom')
    
    context = get_context_with_entreprise_config({
        'recaps': page_obj,
        'bailleurs': bailleurs,
        'title': 'Récapitulatifs Mensuels',
        'is_paginated': page_obj.has_other_pages(),
        'page_obj': page_obj,
        'is_privilege_user': is_privilege_user,
    })
    
    return render(request, 'paiements/liste_recaps_mensuels.html', context)


@login_required
def creer_recap_mensuel(request):
    """Créer un nouveau récapitulatif mensuel."""
    # Vérification des permissions avec fallback pour PRIVILEGE
    permissions = check_group_permissions(request.user, [], 'add')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:liste_recaps_mensuels_auto')
    
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
                
                # Vérifier si un récapitulatif existe déjà pour ce bailleur et ce mois (non supprimé)
                recap_existant = RecapMensuel.objects.filter(
                    bailleur=bailleur,
                    mois_recap__year=mois_recap.year,
                    mois_recap__month=mois_recap.month,
                    is_deleted=False
                ).first()
                
                if recap_existant:
                    messages.warning(request, f'Un récapitulatif existe déjà pour {bailleur.get_nom_complet()} - {mois_recap.strftime("%B %Y")}')
                    return redirect('paiements:detail_recap_mensuel_auto', recap_id=recap_existant.id)
                
                # Vérifier s'il existe un récapitulatif supprimé logiquement pour ce bailleur et ce mois
                recap_supprime = RecapMensuel.objects.filter(
                    bailleur=bailleur,
                    mois_recap__year=mois_recap.year,
                    mois_recap__month=mois_recap.month,
                    is_deleted=True
                ).first()
                
                # Si un récap supprimé existe, le supprimer physiquement avant de créer le nouveau
                if recap_supprime:
                    recap_supprime.paiements_concernes.clear()
                    recap_supprime.charges_deductibles.clear()
                    recap_supprime.delete()
                
                # Créer le récapitulatif
                recap = RecapMensuel.objects.create(
                    bailleur=bailleur,
                    mois_recap=mois_recap,
                    cree_par=request.user
                )
                
                # Calculer les totaux
                recap.calculer_totaux_bailleur()
                
                messages.success(request, f'Récapitulatif créé avec succès pour {bailleur.get_nom_complet()} - {mois_recap.strftime("%B %Y")}')
                return redirect('paiements:detail_recap_mensuel_auto', recap_id=recap.id)
                
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
    """Afficher le détail complet d'un récapitulatif mensuel."""
    # Vérification des permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE', 'CAISSE'], 'view')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:liste_recaps_mensuels')
    
    # Vérifier si l'utilisateur est PRIVILEGE
    is_privilege_user = hasattr(request.user, 'groupe_travail') and request.user.groupe_travail and request.user.groupe_travail.nom == 'PRIVILEGE'
    
    try:
        recap = RecapMensuel.objects.select_related(
            'bailleur', 'cree_par', 'modifie_par'
        ).prefetch_related(
            'paiements_concernes__contrat__propriete',
            'paiements_concernes__contrat__unite_locative',
            'paiements_concernes__contrat__locataire',
            'charges_deductibles__contrat__propriete',
            'charges_deductibles__contrat__unite_locative',
            'charges_deductibles__contrat__locataire'
        ).get(id=recap_id, is_deleted=False)
    except RecapMensuel.DoesNotExist:
        messages.error(request, 'Récapitulatif introuvable.')
        return redirect('paiements:liste_recaps_mensuels')
    
    # Vérifier que le récapitulatif a un bailleur
    if not recap.bailleur:
        messages.warning(request, 'Ce récapitulatif n\'a pas de bailleur associé. Certaines fonctionnalités peuvent être limitées.')
    
    # Recalculer automatiquement les totaux pour s'assurer qu'ils sont à jour
    # (la méthode gère déjà le cas où bailleur est None)
    recap.calculer_totaux_bailleur()
    
    # Calculer les statistiques détaillées
    stats = {
        'total_proprietes': recap.nombre_proprietes,
        'total_contrats': recap.nombre_contrats_actifs,
        'total_paiements': recap.nombre_paiements_recus,
        'total_charges': recap.total_charges_deductibles,
        'total_net': recap.total_net_a_payer,
    }
    
    # Grouper les paiements par propriété (en tenant compte des unités locatives)
    # Utiliser une clé composée (propriete, unite_locative) pour différencier les unités
    paiements_par_propriete = {}
    for paiement in recap.paiements_concernes.all():
        contrat = paiement.contrat
        propriete = contrat.propriete
        unite_locative = contrat.unite_locative
        
        # Créer une clé unique pour la propriété + unité locative
        if unite_locative:
            cle = (propriete.id, unite_locative.id)
        else:
            cle = (propriete.id, None)
        
        if cle not in paiements_par_propriete:
            from decimal import Decimal
            paiements_par_propriete[cle] = {
                'propriete': propriete,
                'unite_locative': unite_locative,
                'contrat': contrat,
                'locataire': contrat.locataire,
                'paiements': [],
                'total_loyers': Decimal('0'),
                'charges_deductibles': [],
                'total_charges': Decimal('0'),
                'montant_net': Decimal('0')
            }
        
        paiements_par_propriete[cle]['paiements'].append(paiement)
        paiements_par_propriete[cle]['total_loyers'] += paiement.montant
    
    # Ajouter les charges déductibles par propriété
    for charge in recap.charges_deductibles.all():
        contrat = charge.contrat
        propriete = contrat.propriete
        unite_locative = contrat.unite_locative
        
        # Utiliser la même clé que pour les paiements
        if unite_locative:
            cle = (propriete.id, unite_locative.id)
        else:
            cle = (propriete.id, None)
        
        if cle in paiements_par_propriete:
            paiements_par_propriete[cle]['charges_deductibles'].append(charge)
            paiements_par_propriete[cle]['total_charges'] += charge.montant
            paiements_par_propriete[cle]['montant_net'] = (
                paiements_par_propriete[cle]['total_loyers'] - 
                paiements_par_propriete[cle]['total_charges']
            )
    
    # Convertir le dictionnaire avec clés composées en liste triée pour le template
    # Trier par propriété puis par unité locative
    paiements_par_propriete_liste = sorted(
        paiements_par_propriete.values(),
        key=lambda x: (x['propriete'].adresse_complete, x['unite_locative'].numero_unite if x['unite_locative'] else '')
    )
    
    # Calculer les totaux globaux
    from decimal import Decimal
    total_global_loyers = sum(prop['total_loyers'] for prop in paiements_par_propriete.values()) or Decimal('0')
    total_global_charges = sum(prop['total_charges'] for prop in paiements_par_propriete.values()) or Decimal('0')
    total_global_net = sum(prop['montant_net'] for prop in paiements_par_propriete.values()) or Decimal('0')
    
    # Utiliser le montant réellement payé du récapitulatif (qui inclut déjà la commission)
    # Recalculer si nécessaire pour s'assurer qu'il est à jour
    recap.calculer_totaux_bailleur()
    # Utiliser getattr pour éviter les erreurs si les migrations ne sont pas encore appliquées
    total_global_net_reellement_paye = getattr(recap, 'montant_reellement_paye', None) or Decimal('0')
    
    # Préparer le titre avec gestion du bailleur None
    if recap.bailleur:
        bailleur_nom = recap.bailleur.get_nom_complet()
    else:
        bailleur_nom = "Sans bailleur"
    
    context = get_context_with_entreprise_config({
        'recap': recap,
        'stats': stats,
        'paiements_par_propriete': paiements_par_propriete_liste,  # Utiliser la liste triée
        'total_global_loyers': total_global_loyers,
        'total_global_charges': total_global_charges,
        'total_global_net': total_global_net,
        'total_global_net_reellement_paye': total_global_net_reellement_paye,
        'title': f'Récapitulatif {bailleur_nom} - {recap.mois_recap.strftime("%B %Y")}',
        'is_privilege_user': is_privilege_user,
    })
    
    return render(request, 'paiements/detail_recap_mensuel.html', context)


@login_required
def valider_recap_mensuel(request, recap_id):
    """Valider un récapitulatif mensuel."""
    # Vérification des permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE', 'CAISSE'], 'change')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:detail_recap_mensuel_auto', recap_id=recap_id)
    
    try:
        recap = RecapMensuel.objects.get(id=recap_id)
    except RecapMensuel.DoesNotExist:
        messages.error(request, 'Récapitulatif introuvable.')
        return redirect('paiements:liste_recaps_mensuels')
    
    if recap.statut != 'brouillon':
        messages.warning(request, 'Ce récapitulatif ne peut plus être validé.')
        return redirect('paiements:detail_recap_mensuel_auto', recap_id=recap_id)
    
    # Valider le récapitulatif
    recap.valider_recap(request.user)
    messages.success(request, 'Récapitulatif validé avec succès.')
    
    return redirect('paiements:detail_recap_mensuel_auto', recap_id=recap_id)


@login_required
def marquer_recap_envoye(request, recap_id):
    """Marquer un récapitulatif mensuel comme envoyé au bailleur."""
    # Vérification des permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE', 'CAISSE'], 'change')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:detail_recap_mensuel_auto', recap_id=recap_id)
    
    try:
        recap = RecapMensuel.objects.get(id=recap_id)
    except RecapMensuel.DoesNotExist:
        messages.error(request, 'Récapitulatif introuvable.')
        return redirect('paiements:liste_recaps_mensuels')
    
    if recap.statut not in ['valide', 'envoye']:
        messages.warning(request, 'Ce récapitulatif doit être validé avant d\'être marqué comme envoyé.')
        return redirect('paiements:detail_recap_mensuel_auto', recap_id=recap_id)
    
    # Marquer comme envoyé
    recap.marquer_envoye(request.user)
    messages.success(request, 'Récapitulatif marqué comme envoyé au bailleur.')
    
    return redirect('paiements:detail_recap_mensuel_auto', recap_id=recap_id)


@login_required
def marquer_recap_paye(request, recap_id):
    """Marquer un récapitulatif mensuel comme payé au bailleur."""
    # Vérification des permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE', 'CAISSE'], 'change')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:detail_recap_mensuel_auto', recap_id=recap_id)
    
    try:
        recap = RecapMensuel.objects.get(id=recap_id)
    except RecapMensuel.DoesNotExist:
        messages.error(request, 'Récapitulatif introuvable.')
        return redirect('paiements:liste_recaps_mensuels')
    
    if recap.statut not in ['envoye', 'paye']:
        messages.warning(request, 'Ce récapitulatif doit être envoyé avant d\'être marqué comme payé.')
        return redirect('paiements:detail_recap_mensuel_auto', recap_id=recap_id)
    
    # Marquer comme payé
    recap.marquer_paye(request.user)
    messages.success(request, 'Récapitulatif marqué comme payé au bailleur.')
    
    return redirect('paiements:detail_recap_mensuel_auto', recap_id=recap_id)


@login_required
def imprimer_recap_mensuel(request, recap_id):
    """Imprimer un récapitulatif mensuel en PDF."""
    # Vérification des permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE', 'CAISSE'], 'view')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:detail_recap_mensuel_auto', recap_id=recap_id)
    
    try:
        recap = RecapMensuel.objects.select_related(
            'bailleur', 'cree_par', 'modifie_par'
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
            fontSize=20,
            spaceAfter=30,
            alignment=1,  # Centré
            textColor=colors.black,
            fontName='Helvetica-Bold'
        )
        
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Heading2'],
            fontSize=16,
            spaceAfter=20,
            textColor=colors.black,
            fontName='Helvetica-Bold'
        )
        
        normal_style = styles['Normal']
        normal_style.fontSize = 12
        normal_style.textColor = colors.black
        normal_style.fontName = 'Helvetica-Bold'
        
        # Contenu du PDF
        story = []
        
        # Récupérer la configuration de l'entreprise
        from core.models import ConfigurationEntreprise
        from core.utils import ajouter_en_tete_entreprise_reportlab, ajouter_pied_entreprise_reportlab
        config = ConfigurationEntreprise.get_configuration_active()
        
        # En-tête de l'entreprise
        ajouter_en_tete_entreprise_reportlab(story, config)
        
        # Titre principal
        story.append(Paragraph("RÉCAPITULATIF MENSUEL", title_style))
        story.append(Spacer(1, 20))
        
        # Informations du bailleur
        bailleur_nom = recap.bailleur.get_nom_complet() if recap.bailleur else "Sans bailleur"
        story.append(Paragraph(f"<b>Bailleur:</b> {bailleur_nom}", subtitle_style))
        story.append(Paragraph(f"<b>Mois:</b> {recap.mois_recap.strftime('%B %Y')}", normal_style))
        story.append(Spacer(1, 15))
        
        # Résumé financier
        story.append(Paragraph("RÉSUMÉ FINANCIER", subtitle_style))
        story.append(Spacer(1, 10))
        
        # Tableau des montants
        montants_data = [
            ['Description', 'Montant (F CFA)'],
            ['Loyer brut total', f"{recap.total_loyers_bruts:,.0f}"],
            ['Charges déductibles', f"{recap.total_charges_deductibles:,.0f}"],
            ['Loyer net total', f"{recap.total_net_a_payer:,.0f}"],
        ]
        
        montants_table = Table(montants_data, colWidths=[8*cm, 4*cm])
        montants_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.black),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 1), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 2, colors.black)
        ]))
        
        story.append(montants_table)
        story.append(Spacer(1, 20))
        
        # Détails des propriétés enrichis
        story.append(Paragraph("DÉTAILS DES PROPRIÉTÉS LOUÉES", subtitle_style))
        story.append(Spacer(1, 10))
        
        # Récupérer les propriétés actives avec plus de détails
        proprietes_actives = recap.bailleur.proprietes.filter(
            contrats__est_actif=True,
            contrats__est_resilie=False
        ).distinct()
        
        proprietes_data = [['Propriété', 'Adresse', 'Locataire', 'Contact', 'Loyer', 'Charges', 'Net']]
        for propriete in proprietes_actives:
            contrat_actif = propriete.contrats.filter(est_actif=True).first()
            if contrat_actif:
                loyer = contrat_actif.loyer_mensuel or 0
                charges = contrat_actif.charges_mensuelles or 0
                net = loyer - charges
                contact = f"{contrat_actif.locataire.telephone or 'N/A'}"
                
                proprietes_data.append([
                    propriete.titre or f"Prop #{propriete.id}",
                    propriete.adresse or "N/A",
                    f"{contrat_actif.locataire.get_nom_complet()}",
                    contact,
                    f"{loyer:,.0f}",
                    f"{charges:,.0f}",
                    f"{net:,.0f}"
                ])
        
        proprietes_table = Table(proprietes_data, colWidths=[3*cm, 4*cm, 3*cm, 2*cm, 2*cm, 2*cm, 2*cm])
        proprietes_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.black),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 2, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        story.append(proprietes_table)
        story.append(Spacer(1, 20))
        
        # Statistiques et indicateurs
        story.append(Paragraph("STATISTIQUES ET INDICATEURS", subtitle_style))
        story.append(Spacer(1, 10))
        
        # Calculer les statistiques
        total_proprietes = proprietes_actives.count()
        total_contrats = proprietes_actives.filter(contrats__est_actif=True).count()
        taux_occupation = (total_contrats / total_proprietes * 100) if total_proprietes > 0 else 0
        
        stats_data = [
            ['Indicateur', 'Valeur'],
            ['Nombre de propriétés', str(total_proprietes)],
            ['Contrats actifs', str(total_contrats)],
            ['Taux d\'occupation', f"{taux_occupation:.1f}%"],
            ['Paiements reçus', str(recap.nombre_paiements_recus)],
        ]
        
        stats_table = Table(stats_data, colWidths=[6*cm, 4*cm])
        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
        ]))
        
        story.append(stats_table)
        story.append(Spacer(1, 20))
        
        # Vérification des garanties financières
        story.append(Paragraph("VÉRIFICATION DES GARANTIES FINANCIÈRES", subtitle_style))
        story.append(Spacer(1, 10))
        
        garanties_data = [['Propriété', 'Caution Requise', 'Caution Versée', 'Avance Requise', 'Avance Versée', 'Statut']]
        total_cautions_requises = 0
        total_cautions_versees = 0
        total_avances_requises = 0
        total_avances_versees = 0
        garanties_completes = 0
        
        for propriete in proprietes_actives:
            contrat_actif = propriete.contrats.filter(est_actif=True).first()
            if contrat_actif:
                caution_requise = contrat_actif.loyer_mensuel or 0
                avance_requise = contrat_actif.loyer_mensuel or 0
                
                # Récupérer les paiements de caution et d'avance
                paiements_caution = contrat_actif.paiements.filter(
                    type_paiement='caution',
                    statut='valide'
                ).aggregate(total=Sum('montant'))['total'] or 0
                
                paiements_avance = contrat_actif.paiements.filter(
                    type_paiement='avance',
                    statut='valide'
                ).aggregate(total=Sum('montant'))['total'] or 0
                
                statut = "Complètes" if (paiements_caution >= caution_requise and paiements_avance >= avance_requise) else "Incomplètes"
                
                garanties_data.append([
                    propriete.titre or f"Prop #{propriete.id}",
                    f"{caution_requise:,.0f}",
                    f"{paiements_caution:,.0f}",
                    f"{avance_requise:,.0f}",
                    f"{paiements_avance:,.0f}",
                    statut
                ])
                
                total_cautions_requises += caution_requise
                total_cautions_versees += paiements_caution
                total_avances_requises += avance_requise
                total_avances_versees += paiements_avance
                
                if paiements_caution >= caution_requise and paiements_avance >= avance_requise:
                    garanties_completes += 1
        
        # Ajouter les totaux
        garanties_data.append([
            "TOTAL",
            f"{total_cautions_requises:,.0f}",
            f"{total_cautions_versees:,.0f}",
            f"{total_avances_requises:,.0f}",
            f"{total_avances_versees:,.0f}",
            f"{garanties_completes}/{total_proprietes}"
        ])
        
        garanties_table = Table(garanties_data, colWidths=[2.5*cm, 2*cm, 2*cm, 2*cm, 2*cm, 2.5*cm])
        garanties_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkgreen),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -2), colors.lightgrey),
            ('BACKGROUND', (0, -1), (-1, -1), colors.yellow),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 7),
        ]))
        
        story.append(garanties_table)
        story.append(Spacer(1, 20))
        
        # Charges déductibles
        if recap.charges_deductibles.exists():
            story.append(Paragraph("CHARGES DÉDUCTIBLES", subtitle_style))
            story.append(Spacer(1, 10))
            
            charges_data = [['Description', 'Montant (F CFA)']]
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
        if recap.created_at:
            story.append(Paragraph(f"<b>Date de création:</b> {recap.created_at.strftime('%d/%m/%Y')}", normal_style))
        if recap.date_validation:
            story.append(Paragraph(f"<b>Date de validation:</b> {recap.date_validation.strftime('%d/%m/%Y')}", normal_style))
        if recap.date_envoi:
            story.append(Paragraph(f"<b>Date d'envoi:</b> {recap.date_envoi.strftime('%d/%m/%Y')}", normal_style))
        if recap.date_paiement:
            story.append(Paragraph(f"<b>Date de paiement:</b> {recap.date_paiement.strftime('%d/%m/%Y')}", normal_style))
        
        # Pied de page avec informations de l'entreprise
        ajouter_pied_entreprise_reportlab(story, config)
        
        # Générer le PDF
        doc.build(story)
        buffer.seek(0)
        
        # Créer la réponse HTTP
        from django.http import HttpResponse
        response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        bailleur_nom = recap.bailleur.get_nom_complet() if recap.bailleur else "sans_bailleur"
        response['Content-Disposition'] = f'attachment; filename="recap_mensuel_{bailleur_nom.replace(" ", "_")}_{recap.mois_recap.strftime("%Y_%m")}.pdf"'
        
        # Marquer comme imprimé si ce n'est pas déjà fait
        if recap.statut == 'envoye' and not recap.date_impression:
            recap.date_impression = timezone.now()
            recap.save()
        
        return response
        
    except ImportError:
        messages.error(request, 'La génération PDF nécessite ReportLab. Veuillez l\'installer.')
        return redirect('paiements:detail_recap_mensuel_auto', recap_id=recap_id)
    except Exception as e:
        messages.error(request, f'Erreur lors de la génération du PDF: {str(e)}')
        return redirect('paiements:detail_recap_mensuel_auto', recap_id=recap_id)

@login_required
def liste_retraits_bailleur(request):
    """Liste des retraits bailleur SÉCURISÉE."""
    # Vérification des permissions avec fallback pour PRIVILEGE
    permissions = check_group_permissions_with_fallback(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE', 'CAISSE'], 'view')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:dashboard')
    
    # Récupérer tous les retraits avec relations (non supprimés)
    retraits = RetraitBailleur.objects.filter(is_deleted=False).select_related(
        'bailleur', 'cree_par', 'valide_par'
    ).order_by('-created_at')
    
    # Filtres
    statut = request.GET.get('statut')
    if statut:
        retraits = retraits.filter(statut=statut)
    
    bailleur_id = request.GET.get('bailleur')
    if bailleur_id:
        retraits = retraits.filter(bailleur_id=bailleur_id)
    
    mois = request.GET.get('mois')
    if mois:
        try:
            from datetime import datetime
            date_mois = datetime.strptime(mois, '%Y-%m').date()
            retraits = retraits.filter(mois_retrait__year=date_mois.year, mois_retrait__month=date_mois.month)
        except ValueError:
            pass
    
    # Vérifier si l'utilisateur peut voir les montants (PRIVILEGE uniquement)
    can_see_amounts = check_group_permissions(request.user, ['PRIVILEGE'], 'view')['allowed']
    
    # Statistiques dynamiques et exactes
    from proprietes.models import Propriete
    
    # Compter seulement les retraits pour des bailleurs qui ont des propriétés louées
    retraits_avec_proprietes = RetraitBailleur.objects.filter(
        bailleur__proprietes__contrats__est_actif=True,
        bailleur__proprietes__contrats__est_resilie=False
    ).distinct()
    
    total_retraits = retraits_avec_proprietes.count()
    montant_total = retraits_avec_proprietes.aggregate(total=Sum('montant_net_a_payer'))['total'] or 0
    en_attente = retraits_avec_proprietes.filter(statut='en_attente').count()
    payes = retraits_avec_proprietes.filter(statut='paye').count()
    
    # Pagination
    paginator = Paginator(retraits, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Récupérer tous les bailleurs pour le filtre
    from proprietes.models import Bailleur
    bailleurs = Bailleur.objects.all().order_by('nom', 'prenom')
    
    context = get_context_with_entreprise_config({
        'page_obj': page_obj,
        'can_see_amounts': can_see_amounts,
        'stats': {
            'total_retraits': total_retraits,
            'total_montant': montant_total,
            'retraits_en_attente': en_attente,
            'retraits_payes': payes,
        },
        'bailleurs': bailleurs,
        'title': 'Retraits aux Bailleurs'
    })
    
    return render(request, 'paiements/retraits/retrait_list.html', context)

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
    # Vérification des permissions avec fallback pour PRIVILEGE
    permissions = check_group_permissions_with_fallback(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE', 'CAISSE'], 'view')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:dashboard')
    
    # Récupérer les tableaux de bord de l'utilisateur
    tableaux = TableauBordFinancier.objects.filter(
        cree_par=request.user
    ).select_related('cree_par').prefetch_related('proprietes', 'bailleurs').order_by('-created_at')
    
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
    """Afficher le détail d'une quittance de paiement avec le nouveau système A5 unifié."""
    # Vérification des permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE', 'CAISSE'], 'view')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:liste')
    
    quittance = get_object_or_404(
        QuittancePaiement.objects.prefetch_related('paiements').select_related(
            'paiement_principal__contrat__locataire',
            'paiement_principal__contrat__propriete',
            'paiement_principal__contrat__propriete__bailleur'
        ),
        pk=pk
    )
    
    try:
        # Utiliser le nouveau système A5 unifié
        from .services_document_unifie_complet import DocumentUnifieA5ServiceComplet
        
        service = DocumentUnifieA5ServiceComplet()
        # Utiliser le paiement principal ou le premier paiement de la liste
        paiement_id = quittance.paiement_principal.id if quittance.paiement_principal else quittance.paiements.first().id
        html_content = service.generer_document_unifie('paiement_quittance', paiement_id=paiement_id)
        
        return HttpResponse(html_content, content_type='text/html')
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        messages.error(request, f'Erreur lors de la génération: {str(e)}')
        return redirect('paiements:quittance_list')


@login_required
def corriger_annees_mois_paye(request):
    """Vue secrète pour corriger les années incorrectes dans mois_paye des paiements existants."""
    from core.utils import check_group_permissions
    from django.db import transaction
    from datetime import datetime
    from dateutil.relativedelta import relativedelta
    import re
    
    # Vérification des permissions : Seuls PRIVILEGE peuvent exécuter cette action
    permissions = check_group_permissions(request.user, ['PRIVILEGE'], 'view')
    if not permissions['allowed']:
        messages.error(request, 'Accès refusé.')
        return redirect('paiements:liste')
    
    try:
        # Mapping des mois français
        mois_francais = {
            'janvier': 1, 'février': 2, 'mars': 3, 'avril': 4,
            'mai': 5, 'juin': 6, 'juillet': 7, 'août': 8,
            'septembre': 9, 'octobre': 10, 'novembre': 11, 'décembre': 12
        }
        
        # Récupérer tous les paiements avec mois_paye
        paiements = Paiement.objects.filter(
            Q(mois_paye__isnull=False) & ~Q(mois_paye='')
        ).select_related('contrat').order_by('date_paiement')
        
        mois_actuel = datetime.now().month
        annee_actuelle = datetime.now().year
        
        corrections = []
        
        for paiement in paiements:
            if not paiement.mois_paye:
                continue
                
            # Extraire le mois et l'année de mois_paye
            mois_paye_str = paiement.mois_paye.strip()
            
            # Trouver le mois dans la chaîne
            mois_num = None
            mois_nom = None
            for nom_mois, num in mois_francais.items():
                if nom_mois.lower() in mois_paye_str.lower():
                    mois_num = num
                    mois_nom = nom_mois
                    break
            
            if not mois_num:
                continue
            
            # Extraire l'année
            annee_match = re.search(r'(\d{4})', mois_paye_str)
            if not annee_match:
                continue
            
            annee_actuelle_paye = int(annee_match.group(1))
            
            # Vérifier si l'année est incorrecte
            correction_necessaire = False
            nouvelle_annee = annee_actuelle_paye
            
            # Cas 1: On est en décembre et le mois payé est janvier de la même année
            # (devrait être l'année suivante)
            if mois_actuel == 12 and mois_num == 1 and annee_actuelle_paye == annee_actuelle:
                nouvelle_annee = annee_actuelle + 1
                correction_necessaire = True
            
            # Cas 2: On est en novembre/décembre 2025 et le mois payé est janvier 2025
            # mais la date de paiement est en 2025 (devrait être janvier 2026)
            elif mois_actuel >= 11 and mois_num == 1:
                # Vérifier si c'est un paiement récent (créé en novembre/décembre 2025)
                if paiement.date_paiement.year == annee_actuelle and paiement.date_paiement.month >= 11:
                    if annee_actuelle_paye == annee_actuelle:
                        nouvelle_annee = annee_actuelle + 1
                        correction_necessaire = True
            
            # Cas 3: Le mois payé est avant le mois actuel de la même année
            # et on est en fin d'année (novembre/décembre), c'est probablement l'année suivante
            elif mois_actuel >= 11 and mois_num < mois_actuel and annee_actuelle_paye == annee_actuelle:
                # Vérifier si le paiement a été fait récemment
                if paiement.date_paiement.year == annee_actuelle:
                    nouvelle_annee = annee_actuelle + 1
                    correction_necessaire = True
            
            if correction_necessaire:
                nouveau_mois_paye = f"{mois_nom} {nouvelle_annee}"
                corrections.append({
                    'paiement': paiement,
                    'ancien': paiement.mois_paye,
                    'nouveau': nouveau_mois_paye,
                })
        
        if corrections:
            with transaction.atomic():
                for corr in corrections:
                    corr['paiement'].mois_paye = corr['nouveau']
                    corr['paiement'].save(update_fields=['mois_paye'])
            
            messages.success(
                request,
                f'{len(corrections)} paiement(s) corrigé(s) avec succès!'
            )
        else:
            messages.info(request, 'Aucune correction nécessaire.')
            
    except Exception as e:
        messages.error(request, f'Erreur lors de la correction : {str(e)}')
    
    return redirect('paiements:liste')


@login_required
def quittance_list(request):
    """Liste des récépissés de paiement."""
    # Vérification des permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE', 'CAISSE'], 'view')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:liste')
    
    quittances = QuittancePaiement.objects.prefetch_related('paiements').select_related(
        'paiement_principal__contrat__locataire',
        'paiement_principal__contrat__propriete',
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
    quittances_cumulees = quittances.filter(est_cumulee=True).count()
    
    context = get_context_with_entreprise_config({
        'quittances': page_obj,
        'total_quittances': total_quittances,
        'quittances_imprimees': quittances_imprimees,
        'quittances_envoyees': quittances_envoyees,
        'quittances_cumulees': quittances_cumulees,
        'title': 'Liste des récépissés de paiement'
    })
    
    return render(request, 'paiements/quittance_list.html', context)


@login_required
@require_POST
def marquer_quittance_imprimee(request, pk):
    """Marquer une quittance comme imprimée."""
    # Vérification des permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE', 'CAISSE'], 'modify')
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
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE', 'CAISSE'], 'modify')
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
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE', 'CAISSE'], 'modify')
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
    """Générer manuellement une quittance pour un paiement existant avec le système A5 unifié."""
    # Vérification des permissions
    permissions = check_group_permissions(request.user, [], 'add')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:detail', pk=paiement_pk)
    
    try:
        paiement = get_object_or_404(Paiement, pk=paiement_pk)
        
        # Utiliser le nouveau système A5 unifié directement
        from .services_document_unifie_complet import DocumentUnifieA5ServiceComplet
        
        service = DocumentUnifieA5ServiceComplet()
        html_content = service.generer_document_unifie('paiement_quittance', paiement_id=paiement.id)
        
        return HttpResponse(html_content, content_type='text/html')
        
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
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE', 'CAISSE'], 'view')
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
    permissions = check_group_permissions(request.user, [], 'add')
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
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE', 'CAISSE'], 'change')
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
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE', 'CAISSE'], 'view')
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
def tableau_bord_list(request):
    # Vue désactivée : modèle TableauBordFinancier supprimé
    messages.error(request, "La fonctionnalité Tableau de Bord Financier a été désactivée (modèle supprimé).")
    return redirect('paiements:dashboard')

@login_required
def generer_recap_mensuel_automatique(request):
    """Génère automatiquement les récapitulatifs mensuels pour tous les bailleurs actifs."""
    # Vérification des permissions avec fallback pour PRIVILEGE
    permissions = check_group_permissions_with_fallback(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE', 'CAISSE'], 'view')
    
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:dashboard')
    
    if request.method == 'POST':
        mois_recap = request.POST.get('mois_recap')
        forcer_regeneration = request.POST.get('forcer_regeneration') == 'on'
        bailleur_id = request.POST.get('bailleur_id')  # Nouveau : sélection de bailleur
        
        if not mois_recap:
            messages.error(request, _("Veuillez sélectionner un mois."))
            return redirect('paiements:generer_recap_mensuel_automatique')
        
        try:
            from .services_retrait import ServiceGestionRetrait
            
            # Convertir la date
            mois_date = datetime.strptime(mois_recap, '%Y-%m-%d').date()
            
            # Vérifier les restrictions de période
            periode_ok, message_periode = ServiceGestionRetrait.verifier_periode_retrait()
            if not periode_ok:
                messages.error(request, message_periode)
                return redirect('paiements:generer_recap_mensuel_automatique')
            
            # Récupérer les bailleurs selon la sélection
            if bailleur_id and bailleur_id != 'tous':
                # Génération pour un bailleur spécifique
                bailleurs = Bailleur.objects.filter(id=bailleur_id, is_deleted=False)
                if not bailleurs.exists():
                    messages.error(request, _("Bailleur sélectionné introuvable."))
                    return redirect('paiements:generer_recap_mensuel_automatique')
            else:
                # Génération pour tous les bailleurs
                bailleurs = Bailleur.objects.filter(is_deleted=False)
            
            # Vérifier s'il existe déjà des récapitulatifs pour ce mois et ces bailleurs (non supprimés)
            recaps_existants = RecapMensuel.objects.filter(
                mois_recap__year=mois_date.year,
                mois_recap__month=mois_date.month,
                bailleur__in=bailleurs,
                is_deleted=False
            )
            
            if recaps_existants.exists() and not forcer_regeneration:
                messages.warning(request, _("Des récapitulatifs existent déjà pour ce mois. Cochez 'Forcer la régénération' pour les recréer."))
                return redirect('paiements:generer_recap_mensuel_automatique')
            
            # Supprimer physiquement les anciens récapitulatifs si régénération forcée
            if forcer_regeneration and recaps_existants.exists():
                # Supprimer d'abord les relations ManyToMany
                for recap in recaps_existants:
                    recap.paiements_concernes.clear()
                    recap.charges_deductibles.clear()
                # Supprimer physiquement les récapitulatifs
                recaps_existants.delete()
                messages.info(request, _("Anciens récapitulatifs supprimés. Génération en cours..."))
            
            if not bailleurs.exists():
                messages.warning(request, _("Aucun bailleur actif trouvé."))
                return redirect('paiements:generer_recap_mensuel_automatique')
            
            recaps_crees = []
            recaps_avec_garanties = []
            recaps_sans_garanties = []
            
            with transaction.atomic():
                for bailleur in bailleurs:
                    try:
                        # Vérifier si le bailleur a des propriétés louées
                        proprietes_louees = bailleur.proprietes.filter(
                            contrats__est_actif=True,
                            contrats__est_resilie=False
                        ).distinct()
                        
                        if not proprietes_louees.exists():
                            continue
                        
                        # Vérifier s'il existe un récapitulatif supprimé logiquement pour ce bailleur et ce mois
                        recap_supprime = RecapMensuel.objects.filter(
                            bailleur=bailleur,
                            mois_recap__year=mois_date.year,
                            mois_recap__month=mois_date.month,
                            is_deleted=True
                        ).first()
                        
                        # Si un récap supprimé existe, le supprimer physiquement avant de créer le nouveau
                        if recap_supprime:
                            recap_supprime.paiements_concernes.clear()
                            recap_supprime.charges_deductibles.clear()
                            recap_supprime.delete()
                        
                        # Créer le récapitulatif
                        recap = RecapMensuel.objects.create(
                            bailleur=bailleur,
                            mois_recap=mois_date,
                            cree_par=request.user
                        )
                        
                        # Calculer automatiquement tous les totaux et vérifier les garanties
                        recap.calculer_totaux_bailleur()
                        
                        # Classer selon les garanties financières
                        if recap.garanties_suffisantes:
                            recaps_avec_garanties.append(recap)
                            recap.statut = 'valide'  # Prêt pour paiement
                        else:
                            recaps_sans_garanties.append(recap)
                            recap.statut = 'brouillon'  # En attente des garanties
                        
                        recap.save()
                        recaps_crees.append(recap)
                        
                    except Exception as e:
                        messages.error(request, f"Erreur pour {bailleur.get_nom_complet()}: {str(e)}")
                        continue
                
                if recaps_crees:
                    messages.success(request, 
                        f"{len(recaps_crees)} récapitulatifs créés avec succès pour {mois_date.strftime('%B %Y')}.")
                    
                    if recaps_avec_garanties:
                        messages.success(request, 
                            f"{len(recaps_avec_garanties)} récapitulatifs sont prêts pour paiement (garanties suffisantes).")
                    
                    if recaps_sans_garanties:
                        messages.warning(request, 
                            f"{len(recaps_sans_garanties)} récapitulatifs sont en attente des garanties financières (cautions et avances).")
                    
                    return redirect('paiements:liste_recaps_mensuels_auto')
                else:
                    messages.warning(request, _("Aucun récapitulatif n'a pu être créé."))
                    
        except ValueError:
            messages.error(request, _("Format de date invalide."))
        except Exception as e:
            messages.error(request, f"Erreur lors de la génération: {str(e)}")
    
    # Préparer les 12 derniers mois pour le sélecteur
    mois_disponibles = []
    date_courante = datetime.now()
    
    for i in range(12):
        date_mois = date_courante - timedelta(days=30*i)
        mois_disponibles.append({
            'value': date_mois.strftime('%Y-%m-%d'),
            'label': date_mois.strftime('%B %Y')
        })
    
    # Récupérer les informations de détection automatique pour chaque bailleur
    bailleurs_actifs = Bailleur.objects.filter(is_deleted=False)
    suggestions_mois = {}
    
    for bailleur in bailleurs_actifs:
        mois_info = RecapMensuel.get_mois_recap_suggere_pour_bailleur(bailleur)
        suggestions_mois[bailleur.id] = {
            'bailleur_nom': bailleur.get_nom_complet(),
            'mois_suggere': mois_info['mois_suggere'].strftime('%Y-%m-%d'),
            'mois_suggere_formate': mois_info['mois_suggere_formate'],
            'raison': mois_info['raison'],
            'dernier_mois': mois_info['dernier_mois'].strftime('%B %Y') if mois_info['dernier_mois'] else 'Aucun',
            'recap_existant': mois_info['recap_existant']
        }
    
    context = get_context_with_entreprise_config({
        'mois_disponibles': mois_disponibles,
        'suggestions_mois': suggestions_mois,
        'bailleurs_actifs': bailleurs_actifs,  # Nouveau : liste des bailleurs pour la sélection
        'title': 'Génération Automatique des Récapitulatifs Mensuels',
        'description': 'Génération automatique avec détection intelligente du mois basée sur le dernier récapitulatif par bailleur'
    })
    
    return render(request, 'paiements/generer_recap_automatique.html', context)

@login_required
def get_calculation_preview(request):
    """API AJAX pour obtenir l'aperçu des calculs en temps réel."""
    if request.method != 'GET':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
    
    # Vérification des permissions avec fallback pour PRIVILEGE
    permissions = check_group_permissions_with_fallback(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE', 'CAISSE'], 'view')
    
    if not permissions['allowed']:
        return JsonResponse({'error': permissions['message']}, status=403)
    
    try:
        mois_str = request.GET.get('mois')
        bailleur_id = request.GET.get('bailleur_id')
        
        if not mois_str:
            return JsonResponse({'error': 'Mois requis'}, status=400)
        
        # Convertir la date
        mois_date = datetime.strptime(mois_str, '%Y-%m-%d').date()
        
        # Récupérer les bailleurs selon la sélection
        if bailleur_id and bailleur_id != 'tous':
            bailleurs = Bailleur.objects.filter(id=bailleur_id, is_deleted=False)
        else:
            bailleurs = Bailleur.objects.filter(is_deleted=False)
        
        if not bailleurs.exists():
            return JsonResponse({'error': 'Aucun bailleur trouvé'}, status=404)
        
        # Calculer les totaux pour l'aperçu
        total_loyers = Decimal('0')
        total_charges = Decimal('0')
        total_charges_bailleur = Decimal('0')  # NOUVEAU
        nombre_proprietes = 0
        nombre_contrats = 0
        nombre_paiements = 0
        
        for bailleur in bailleurs:
            # Récupérer les propriétés actives du bailleur
            proprietes_actives = bailleur.proprietes.filter(
                contrats__est_actif=True,
                contrats__est_resilie=False
            ).distinct()
            
            nombre_proprietes += proprietes_actives.count()
            
            for propriete in proprietes_actives:
                # Contrats actifs de cette propriété
                contrats_actifs = propriete.contrats.filter(
                    est_actif=True,
                    est_resilie=False
                )
                nombre_contrats += contrats_actifs.count()
                
                for contrat in contrats_actifs:
                    # Loyers du mois (basés sur le montant du contrat, pas les paiements reçus)
                    loyer_mensuel = contrat.montant_loyer or Decimal('0')
                    total_loyers += loyer_mensuel
                    
                    # Paiements reçus du mois (pour information)
                    paiements_mois = contrat.paiements.filter(
                        date_paiement__year=mois_date.year,
                        date_paiement__month=mois_date.month,
                        statut='valide',
                        type_paiement='loyer'
                    )
                    nombre_paiements += paiements_mois.count()
                    
                    # Charges déductibles du mois
                    charges_mois = contrat.charges_deductibles.filter(
                        date_charge__year=mois_date.year,
                        date_charge__month=mois_date.month,
                        statut='validee'
                    )
                    total_charges += sum(charge.montant for charge in charges_mois)
                    
                    # NOUVEAU : Charges bailleur du mois
                    charges_bailleur_mois = propriete.charges_bailleur.filter(
                        date_charge__year=mois_date.year,
                        date_charge__month=mois_date.month,
                        statut__in=['en_attente', 'deduite_retrait']
                    )
                    total_charges_bailleur += sum(charge.montant_restant for charge in charges_bailleur_mois)
        
        # Calculer le montant net (incluant les charges bailleur)
        total_net = total_loyers - total_charges - total_charges_bailleur
        
        # Vérifier s'il existe déjà des récapitulatifs pour ce mois
        recaps_existants = RecapMensuel.objects.filter(
            mois_recap__year=mois_date.year,
            mois_recap__month=mois_date.month,
            bailleur__in=bailleurs
        ).count()
        
        return JsonResponse({
            'success': True,
            'data': {
                'total_loyers': float(total_loyers),
                'total_charges': float(total_charges),
                'total_charges_bailleur': float(total_charges_bailleur),  # NOUVEAU
                'total_net': float(total_net),
                'nombre_proprietes': nombre_proprietes,
                'nombre_contrats': nombre_contrats,
                'nombre_paiements': nombre_paiements,
                'recaps_existants': recaps_existants,
                'mois_formate': mois_date.strftime('%B %Y'),
                'bailleurs_count': bailleurs.count()
            }
        })
        
    except ValueError as e:
        return JsonResponse({'error': f'Format de date invalide: {str(e)}'}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'Erreur lors du calcul: {str(e)}'}, status=500)

@login_required
def tableau_bord_recaps_mensuels(request):
    """Tableau de bord spécialisé pour les récapitulatifs mensuels."""
    # Vérification des permissions avec fallback pour PRIVILEGE
    permissions = check_group_permissions_with_fallback(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE', 'CAISSE'], 'view')
    
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:dashboard')
    
    from datetime import datetime, timedelta
    from django.db.models import Sum, Count, Avg
    from proprietes.models import Bailleur
    
    # Année courante
    current_year = datetime.now().year
    
    # Statistiques globales
    total_recaps = RecapMensuel.objects.filter(is_deleted=False).count()
    total_bailleurs = Bailleur.objects.filter(is_deleted=False).count()
    
    # Statistiques par statut
    stats_par_statut = RecapMensuel.objects.filter(is_deleted=False).values('statut').annotate(
        nombre=Count('id'),
        total_montant=Sum('total_net_a_payer')
    ).order_by('statut')
    
    # Statistiques des 6 derniers mois
    date_limite = datetime.now() - timedelta(days=180)
    recaps_6_mois = RecapMensuel.objects.filter(
        is_deleted=False,
        mois_recap__gte=date_limite
    ).values('mois_recap').annotate(
        nombre=Count('id'),
        total_loyers=Sum('total_loyers_bruts'),
        total_charges=Sum('total_charges_deductibles'),
        total_net=Sum('total_net_a_payer')
    ).order_by('-mois_recap')[:6]
    
    # Top 5 des bailleurs par montant net
    top_bailleurs = RecapMensuel.objects.filter(
        is_deleted=False,
        mois_recap__year=current_year
    ).values('bailleur__nom', 'bailleur__prenom').annotate(
        total_net=Sum('total_net_a_payer'),
        nombre_recaps=Count('id')
    ).order_by('-total_net')[:5]
    
    # Récapitulatifs récents
    recaps_recents = RecapMensuel.objects.filter(
        is_deleted=False
    ).select_related('bailleur').order_by('-created_at')[:10]
    
    # Statistiques financières
    total_loyers_annee = RecapMensuel.objects.filter(
        is_deleted=False,
        mois_recap__year=current_year
    ).aggregate(total=Sum('total_loyers_bruts'))['total'] or 0
    
    total_charges_annee = RecapMensuel.objects.filter(
        is_deleted=False,
        mois_recap__year=current_year
    ).aggregate(total=Sum('total_charges_deductibles'))['total'] or 0
    
    total_net_annee = RecapMensuel.objects.filter(
        is_deleted=False,
        mois_recap__year=current_year
    ).aggregate(total=Sum('total_net_a_payer'))['total'] or 0
    
    context = get_context_with_entreprise_config({
        'current_year': current_year,
        'total_recaps': total_recaps,
        'total_bailleurs': total_bailleurs,
        'stats_par_statut': stats_par_statut,
        'recaps_6_mois': recaps_6_mois,
        'top_bailleurs': top_bailleurs,
        'recaps_recents': recaps_recents,
        'total_loyers_annee': total_loyers_annee,
        'total_charges_annee': total_charges_annee,
        'total_net_annee': total_net_annee,
        'title': 'Tableau de Bord - Récapitulatifs Mensuels',
    })
    
    return render(request, 'paiements/tableau_bord_recaps_mensuels.html', context)

@login_required
def generer_pdf_recap_mensuel(request, recap_id):
    """Génère un PDF pour un récapitulatif mensuel spécifique."""
    from django.http import HttpResponse
    from core.utils import check_group_permissions_with_fallback
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        recap = get_object_or_404(RecapMensuel, id=recap_id)
        
        # Vérifier les permissions
        permissions = check_group_permissions_with_fallback(
            request.user, 
            ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE', 'CAISSE'], 
            'view'
        )
        if not permissions['allowed']:
            messages.error(request, permissions['message'])
            return redirect('paiements:detail_recap_mensuel_auto', recap_id=recap_id)
        
        # Vérifier que le bailleur existe
        if not recap.bailleur:
            messages.error(request, 'Ce récapitulatif n\'a pas de bailleur associé. Impossible de générer le PDF.')
            return redirect('paiements:detail_recap_mensuel_auto', recap_id=recap_id)
        
        # Générer le PDF en utilisant la méthode du modèle
        try:
            pdf_content = recap.generer_pdf_recapitulatif(user=request.user)
            
            # Créer la réponse HTTP
            response = HttpResponse(pdf_content, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{recap.get_nom_fichier_pdf()}"'
            
            # Log de l'action
            logger.info(
                f"PDF du récapitulatif {recap.pk} téléchargé par {request.user.username}"
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération du PDF du récapitulatif {recap.pk}: {e}", exc_info=True)
            messages.error(request, f'Erreur lors de la génération du PDF: {str(e)}')
            return redirect('paiements:detail_recap_mensuel_auto', recap_id=recap_id)
        
    except Exception as e:
        logger.error(f"Erreur lors de la génération du PDF: {str(e)}", exc_info=True)
        messages.error(request, f"Erreur lors de la génération du PDF: {str(e)}")
        return redirect('paiements:detail_recap_mensuel_auto', recap_id=recap_id)

@login_required
def generer_pdf_recaps_lot(request):
    """Génère des PDF en lot pour un mois donné."""
    if request.method == 'POST':
        form = GenererPDFLotForm(request.POST)
        if form.is_valid():
            mois_recap = form.cleaned_data['mois_recap']
            
            try:
                # Générer le PDF en lot avec ReportLab (seule option disponible sur Windows)
                # pdf_response = generate_recap_pdf_batch(mois_recap, method='reportlab')  # Fonction non disponible
                
                messages.error(request, "Génération PDF en lot temporairement désactivée - Fonction en cours de développement")
                return redirect('paiements:generer_pdf_lot')
                
            except Exception as e:
                messages.error(request, f"Erreur lors de la génération des PDFs en lot: {str(e)}")
    else:
        form = GenererPDFLotForm()
    
    return render(request, 'paiements/generer_pdf_lot.html', {
        'form': form,
        'page_title': 'Génération PDF en Lot'
    })

@login_required
def supprimer_recap_mensuel(request, recap_id):
    """Supprime un récapitulatif mensuel (suppression logique)."""
    try:
        recap = get_object_or_404(RecapMensuel, id=recap_id, is_deleted=False)
        
        # Vérifier les permissions - Seuls les superusers et le groupe PRIVILEGE peuvent supprimer
        is_privilege_user = hasattr(request.user, 'groupe_travail') and request.user.groupe_travail and request.user.groupe_travail.nom == 'PRIVILEGE'
        if not (request.user.is_superuser or is_privilege_user):
            messages.error(request, "Vous n'avez pas les permissions pour supprimer un récapitulatif.")
            return redirect('paiements:detail_recap_mensuel_auto', recap_id=recap_id)
        
        if request.method == 'POST':
            # Effectuer la suppression logique
            recap.is_deleted = True
            recap.deleted_at = timezone.now()
            recap.deleted_by = request.user
            recap.save()
            
            # Gérer le cas où le bailleur pourrait être None (pour les anciens récapitulatifs)
            if recap.bailleur:
                bailleur_nom = recap.bailleur.get_nom_complet()
            else:
                bailleur_nom = "Sans bailleur"
            
            messages.success(request, f"Le récapitulatif de {bailleur_nom} pour {recap.mois_recap.strftime('%B %Y')} a été supprimé avec succès.")
            return redirect('paiements:liste_recaps_mensuels_auto')
        
        # Afficher la page de confirmation
        # Gérer le cas où le bailleur pourrait être None
        if recap.bailleur:
            bailleur_nom = recap.bailleur.get_nom_complet()
        else:
            bailleur_nom = "Sans bailleur"
        
        context = get_context_with_entreprise_config({
            'recap': recap,
            'page_title': 'Confirmer la suppression',
            'title': f'Supprimer le récapitulatif - {bailleur_nom}',
        })
        
        return render(request, 'paiements/confirmer_suppression_recap.html', context)
        
    except Exception as e:
        messages.error(request, f"Erreur lors de la suppression du récapitulatif: {str(e)}")
        return redirect('paiements:liste_recaps_mensuels_auto')

@login_required
def restaurer_recap_mensuel(request, recap_id):
    """Restaure un récapitulatif mensuel supprimé."""
    try:
        recap = get_object_or_404(RecapMensuel, id=recap_id, is_deleted=True)
        
        # Vérifier les permissions - Seuls les superusers et le groupe PRIVILEGE peuvent restaurer
        is_privilege_user = hasattr(request.user, 'groupe_travail') and request.user.groupe_travail and request.user.groupe_travail.nom == 'PRIVILEGE'
        if not (request.user.is_superuser or is_privilege_user):
            messages.error(request, "Vous n'avez pas les permissions pour restaurer un récapitulatif.")
            return redirect('paiements:liste_recaps_mensuels_auto')
        
        # Restaurer le récapitulatif
        recap.is_deleted = False
        recap.deleted_at = None
        recap.deleted_by = None
        recap.save()
        
        # Gérer le cas où le bailleur pourrait être None (pour les anciens récapitulatifs)
        if recap.bailleur:
            bailleur_nom = recap.bailleur.get_nom_complet()
        else:
            bailleur_nom = "Sans bailleur"
        
        messages.success(request, f"Le récapitulatif de {bailleur_nom} pour {recap.mois_recap.strftime('%B %Y')} a été restauré avec succès.")
        return redirect('paiements:detail_recap_mensuel_auto', recap_id=recap_id)
        
    except Exception as e:
        messages.error(request, f"Erreur lors de la restauration du récapitulatif: {str(e)}")
        return redirect('paiements:liste_recaps_mensuels_auto')

@login_required
def liste_recaps_supprimes(request):
    """Liste les récapitulatifs supprimés (superuser et PRIVILEGE uniquement)."""
    # Vérifier les permissions
    is_privilege_user = hasattr(request.user, 'groupe_travail') and request.user.groupe_travail and request.user.groupe_travail.nom == 'PRIVILEGE'
    if not (request.user.is_superuser or is_privilege_user):
        messages.error(request, "Vous n'avez pas les permissions pour voir les récapitulatifs supprimés.")
        return redirect('paiements:liste_recaps_mensuels_auto')
    
    # Récupérer les récapitulatifs supprimés
    recaps_supprimes = RecapMensuel.objects.filter(is_deleted=True).order_by('-deleted_at')
    
    # Pagination
    paginator = Paginator(recaps_supprimes, 20)
    page_number = request.GET.get('page')
    recaps = paginator.get_page(page_number)
    
    context = get_context_with_entreprise_config({
        'recaps': recaps,
        'page_title': 'Récapitulatifs Supprimés',
        'title': 'Récapitulatifs Supprimés',
        'total_supprimes': recaps_supprimes.count(),
    })
    
    return render(request, 'paiements/recaps_supprimes.html', context)

@login_required
def apercu_pdf_recap_mensuel(request, recap_id):
    """Affiche un aperçu HTML du récapitulatif mensuel."""
    try:
        recap = get_object_or_404(RecapMensuel, id=recap_id)
        
        # Vérifier les permissions
        if not request.user.has_perm('paiements.view_recapmensuel'):
            messages.error(request, "Vous n'avez pas les permissions pour voir ce récapitulatif.")
            return redirect('paiements:tableau_bord_recaps_mensuels')
        
        bailleur_nom = recap.bailleur.get_nom_complet() if recap.bailleur else "Sans bailleur"
        return render(request, 'paiements/apercu_pdf_recap_mensuel.html', {
            'recap': recap,
            'page_title': f'Aperçu - {bailleur_nom} - {recap.mois_recap.strftime("%B %Y")}'
        })
        
    except Exception as e:
        messages.error(request, f"Erreur lors de l'affichage de l'aperçu: {str(e)}")
        return redirect('paiements:tableau_bord_recaps_mensuels')

@login_required
def creer_recap_mensuel_bailleur(request, bailleur_id):
    """Crée un récapitulatif mensuel pour un bailleur spécifique avec détection automatique du mois."""
    try:
        from proprietes.models import Bailleur
        
        bailleur = get_object_or_404(Bailleur, id=bailleur_id)
        
        # Détection automatique du mois de récapitulatif
        mois_info = RecapMensuel.get_mois_recap_suggere_pour_bailleur(bailleur)
        mois_recap = mois_info['mois_suggere']
        
        # Vérifier si un récapitulatif existe déjà pour ce mois et ce bailleur (non supprimé)
        recap_existant = RecapMensuel.objects.filter(
            bailleur=bailleur,
            mois_recap=mois_recap,
            is_deleted=False
        ).first()
        
        if recap_existant:
            messages.info(request, f"Un récapitulatif existe déjà pour {bailleur.get_nom_complet()} - {mois_info['mois_suggere_formate']}")
            return redirect('paiements:detail_recap_mensuel_auto', recap_id=recap_existant.id)
        
        # Vérifier s'il existe un récapitulatif supprimé logiquement pour ce bailleur et ce mois
        recap_supprime = RecapMensuel.objects.filter(
            bailleur=bailleur,
            mois_recap=mois_recap,
            is_deleted=True
        ).first()
        
        # Si un récap supprimé existe, le supprimer physiquement avant de créer le nouveau
        if recap_supprime:
            recap_supprime.paiements_concernes.clear()
            recap_supprime.charges_deductibles.clear()
            recap_supprime.delete()
        
        # Créer le nouveau récapitulatif
        recap = RecapMensuel.objects.create(
            bailleur=bailleur,
            mois_recap=mois_recap,
            cree_par=request.user
        )
        
        # Calculer les totaux automatiquement
        recap.calculer_totaux_bailleur()
        recap.save()
        
        # Message de succès avec information sur la détection automatique
        message_succes = (
            f"Récapitulatif créé avec succès pour {bailleur.get_nom_complet()} - {mois_info['mois_suggere_formate']}. "
            f"({mois_info['raison']})"
        )
        messages.success(request, message_succes)
        return redirect('paiements:detail_recap_mensuel_auto', recap_id=recap.id)
        
    except Exception as e:
        messages.error(request, f"Erreur lors de la création du récapitulatif: {str(e)}")
        return redirect('paiements:tableau_bord_recaps_mensuels')

@login_required
def liste_bailleurs_recaps(request):
    """Liste des bailleurs pour créer des récapitulatifs mensuels avec détection automatique du mois."""
    try:
        from proprietes.models import Bailleur
        from datetime import date
        
        # Récupérer tous les bailleurs avec des propriétés actives
        bailleurs = Bailleur.objects.filter(
            propriete__contrats__est_actif=True,
            propriete__contrats__est_resilie=False
        ).distinct().order_by('nom')
        
        # Pour chaque bailleur, déterminer le mois suggéré et les informations contextuelles
        mois_actuel = date.today().replace(day=1)
        for bailleur in bailleurs:
            # Obtenir les informations de détection automatique du mois
            mois_info = RecapMensuel.get_mois_recap_suggere_pour_bailleur(bailleur)
            bailleur.mois_suggere = mois_info['mois_suggere']
            bailleur.mois_suggere_formate = mois_info['mois_suggere_formate']
            bailleur.raison_suggestion = mois_info['raison']
            bailleur.dernier_mois = mois_info['dernier_mois']
            bailleur.recap_existant = mois_info['recap_existant']
            
            # Récupérer le récapitulatif existant pour le mois suggéré
            if mois_info['recap_existant']:
                bailleur.recap_existant_obj = RecapMensuel.objects.filter(
                    bailleur=bailleur,
                    mois_recap=mois_info['mois_suggere'],
                    is_deleted=False
                ).first()
            else:
                bailleur.recap_existant_obj = None
        
        context = {
            'bailleurs': bailleurs,
            'mois_actuel': mois_actuel,
            'page_title': 'Créer des Récapitulatifs Mensuels',
            'page_icon': 'calendar-plus',
            'description': 'Création de récapitulatifs mensuels avec détection automatique du mois basée sur le dernier récapitulatif par bailleur'
        }
        
        return render(request, 'paiements/liste_bailleurs_recaps.html', context)
        
    except Exception as e:
        messages.error(request, f"Erreur lors du chargement des bailleurs: {str(e)}")
        return redirect('paiements:tableau_bord_recaps_mensuels')

@login_required
def creer_recap_avec_detection_auto(request, bailleur_id):
    """Crée un récapitulatif avec détection automatique du mois et possibilité de modification."""
    try:
        from proprietes.models import Bailleur
        from datetime import date
        
        bailleur = get_object_or_404(Bailleur, id=bailleur_id)
        
        if request.method == 'POST':
            # Récupérer le mois sélectionné par l'utilisateur
            mois_recap_str = request.POST.get('mois_recap')
            if not mois_recap_str:
                messages.error(request, "Veuillez sélectionner un mois.")
                return redirect('paiements:creer_recap_avec_detection_auto', bailleur_id=bailleur_id)
            
            mois_recap = datetime.strptime(mois_recap_str, '%Y-%m-%d').date()
            # Normaliser la date au premier jour du mois pour garantir la cohérence
            mois_recap = mois_recap.replace(day=1)
            
            # Obtenir les informations de détection automatique pour validation
            mois_info = RecapMensuel.get_mois_recap_suggere_pour_bailleur(bailleur)
            
            # Validation stricte : vérifier que le mois sélectionné est bien le mois suggéré
            if mois_recap != mois_info['mois_suggere']:
                messages.error(request, 
                    f"Erreur de validation : Vous devez sélectionner le mois suggéré automatiquement "
                    f"({mois_info['mois_suggere_formate']}) pour maintenir la continuité des récapitulatifs. "
                    f"Raison : {mois_info['raison']}"
                )
                return redirect('paiements:creer_recap_avec_detection_auto', bailleur_id=bailleur_id)
            
            # Vérifier si un récapitulatif existe déjà pour ce mois et ce bailleur (comparaison par année et mois)
            recap_existant = RecapMensuel.objects.filter(
                bailleur=bailleur,
                mois_recap__year=mois_recap.year,
                mois_recap__month=mois_recap.month,
                is_deleted=False
            ).first()
            
            if recap_existant:
                messages.info(request, f"Un récapitulatif existe déjà pour {bailleur.get_nom_complet()} - {mois_recap.strftime('%B %Y')}")
                return redirect('paiements:detail_recap_mensuel_auto', recap_id=recap_existant.id)
            
            # Vérifier s'il existe un récapitulatif supprimé logiquement pour ce bailleur et ce mois (comparaison par année et mois)
            recap_supprime = RecapMensuel.objects.filter(
                bailleur=bailleur,
                mois_recap__year=mois_recap.year,
                mois_recap__month=mois_recap.month,
                is_deleted=True
            ).first()
            
            # Si un récap supprimé existe, le supprimer physiquement avant de créer le nouveau
            if recap_supprime:
                try:
                    recap_supprime.paiements_concernes.clear()
                    recap_supprime.charges_deductibles.clear()
                    recap_supprime.delete()
                    messages.info(request, f"L'ancien récapitulatif supprimé a été définitivement supprimé pour permettre la création d'un nouveau.")
                except Exception as e:
                    messages.warning(request, f"Attention: Impossible de supprimer l'ancien récapitulatif: {str(e)}")
            
            # Créer le nouveau récapitulatif
            try:
                recap = RecapMensuel.objects.create(
                    bailleur=bailleur,
                    mois_recap=mois_recap,
                    cree_par=request.user
                )
                
                # Calculer les totaux automatiquement
                recap.calculer_totaux_bailleur()
                recap.save()
            except Exception as e:
                import traceback
                error_details = traceback.format_exc()
                messages.error(request, f"Erreur lors de la création du récapitulatif: {str(e)}")
                # Log l'erreur complète pour le débogage
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Erreur création récapitulatif: {error_details}")
                return redirect('paiements:creer_recap_avec_detection_auto', bailleur_id=bailleur_id)
            
            messages.success(request, 
                f"Récapitulatif créé avec succès pour {bailleur.get_nom_complet()} - {mois_recap.strftime('%B %Y')}. "
                f"({mois_info['raison']})"
            )
            return redirect('paiements:detail_recap_mensuel_auto', recap_id=recap.id)
        
        # Obtenir les informations de détection automatique du mois
        mois_info = RecapMensuel.get_mois_recap_suggere_pour_bailleur(bailleur)
        
        # Préparer les mois disponibles (12 derniers mois + mois suggéré)
        mois_disponibles = []
        date_courante = datetime.now()
        
        # Ajouter le mois suggéré en premier
        mois_suggere = mois_info['mois_suggere']
        mois_disponibles.append({
            'value': mois_suggere.strftime('%Y-%m-%d'),
            'label': f"{mois_info['mois_suggere_formate']} (Suggéré - {mois_info['raison']})",
            'is_suggested': True
        })
        
        # Ajouter les 12 derniers mois
        for i in range(12):
            date_mois = date_courante - timedelta(days=30*i)
            if date_mois != mois_suggere:  # Éviter les doublons
                mois_disponibles.append({
                    'value': date_mois.strftime('%Y-%m-%d'),
                    'label': date_mois.strftime('%B %Y'),
                    'is_suggested': False
                })
        
        context = {
            'bailleur': bailleur,
            'mois_info': mois_info,
            'mois_disponibles': mois_disponibles,
            'page_title': f'Créer un Récapitulatif - {bailleur.get_nom_complet()}',
            'page_icon': 'calendar-plus',
            'description': 'Création de récapitulatif avec détection automatique du mois'
        }
        
        return render(request, 'paiements/creer_recap_avec_detection.html', context)
        
    except Exception as e:
        messages.error(request, f"Erreur lors de la création du récapitulatif: {str(e)}")
        return redirect('paiements:liste_bailleurs_recaps')

@login_required
def generer_pdf_recap_detaille_paysage(request, recap_id):
    """Génère un PDF détaillé en format A4 paysage avec toutes les informations enrichies."""
    try:
        recap = get_object_or_404(RecapMensuel, id=recap_id, is_deleted=False)
        
        # Vérification des permissions
        permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE', 'CAISSE'], 'view')
        if not permissions['allowed']:
            messages.error(request, permissions['message'])
            return redirect('paiements:tableau_bord_recaps_mensuels')
        
        # Récupérer les détails des propriétés avec informations enrichies
        proprietes_details = []
        proprietes_actives = recap.bailleur.proprietes.filter(
            contrats__est_actif=True,
            contrats__est_resilie=False
        ).distinct()
        
        # Statistiques globales
        stats_globales = {
            'total_proprietes': 0,
            'total_contrats_actifs': 0,
            'total_loyers_bruts': Decimal('0'),
            'total_charges_deductibles': Decimal('0'),
            'total_charges_bailleur': Decimal('0'),
            'total_net_a_payer': Decimal('0'),
            'total_cautions_requises': Decimal('0'),
            'total_avances_requises': Decimal('0'),
            'total_cautions_versees': Decimal('0'),
            'total_avances_versees': Decimal('0'),
            'proprietes_avec_garanties_completes': 0,
            'proprietes_avec_retards': 0,
            'taux_occupation': 0,
        }
        
        for propriete in proprietes_actives:
            contrat_actif = propriete.contrats.filter(est_actif=True).first()
            if contrat_actif:
                # Calculer les garanties financières
                caution_requise = contrat_actif.loyer_mensuel or Decimal('0')
                avance_requise = contrat_actif.loyer_mensuel or Decimal('0')
                
                # Récupérer les paiements de caution et d'avance
                paiements_caution = contrat_actif.paiements.filter(
                    type_paiement='caution',
                    statut='valide'
                ).aggregate(total=Sum('montant'))['total'] or Decimal('0')
                
                paiements_avance = contrat_actif.paiements.filter(
                    type_paiement='avance',
                    statut='valide'
                ).aggregate(total=Sum('montant'))['total'] or Decimal('0')
                
                # Vérifier les retards de paiement
                paiements_en_retard = contrat_actif.paiements.filter(
                    type_paiement='loyer',
                    statut='en_retard'
                ).count()
                
                # Calculer les charges du mois
                charges_mensuelles = contrat_actif.charges_mensuelles or Decimal('0')
                charges_bailleur = Decimal('0')  # À calculer selon la logique métier
                
                # Montant net pour cette propriété
                montant_net = (contrat_actif.loyer_mensuel or Decimal('0')) - charges_mensuelles - charges_bailleur
                
                garanties_suffisantes = (
                    paiements_caution >= caution_requise and
                    paiements_avance >= avance_requise
                )
                
                propriete_detail = {
                    'id': propriete.id,
                    'nom': propriete.titre or f"Propriété #{propriete.id}",
                    'adresse': propriete.adresse or "Adresse non renseignée",
                    'ville': propriete.ville or "Ville non renseignée",
                    'locataire': contrat_actif.locataire,
                    'loyer_mensuel': contrat_actif.loyer_mensuel or Decimal('0'),
                    'charges_mensuelles': charges_mensuelles,
                    'charges_bailleur': charges_bailleur,
                    'montant_net': montant_net,
                    'contrat_actif': True,
                    'date_debut': contrat_actif.date_debut,
                    'date_fin': contrat_actif.date_fin,
                    'caution_requise': caution_requise,
                    'avance_requise': avance_requise,
                    'caution_versee': paiements_caution,
                    'avance_versee': paiements_avance,
                    'garanties_suffisantes': garanties_suffisantes,
                    'retards_paiement': paiements_en_retard,
                    'statut_garanties': 'Complètes' if garanties_suffisantes else 'Incomplètes',
                    'contact_locataire': f"{contrat_actif.locataire.telephone or 'N/A'} / {contrat_actif.locataire.email or 'N/A'}",
                }
                proprietes_details.append(propriete_detail)
                
                # Mettre à jour les statistiques globales
                stats_globales['total_proprietes'] += 1
                stats_globales['total_contrats_actifs'] += 1
                stats_globales['total_loyers_bruts'] += contrat_actif.loyer_mensuel or Decimal('0')
                stats_globales['total_charges_deductibles'] += charges_mensuelles
                stats_globales['total_charges_bailleur'] += charges_bailleur
                stats_globales['total_net_a_payer'] += montant_net
                stats_globales['total_cautions_requises'] += caution_requise
                stats_globales['total_avances_requises'] += avance_requise
                stats_globales['total_cautions_versees'] += paiements_caution
                stats_globales['total_avances_versees'] += paiements_avance
                
                if garanties_suffisantes:
                    stats_globales['proprietes_avec_garanties_completes'] += 1
                
                if paiements_en_retard > 0:
                    stats_globales['proprietes_avec_retards'] += 1
        
        # Calculer le taux d'occupation
        if stats_globales['total_proprietes'] > 0:
            stats_globales['taux_occupation'] = (stats_globales['total_contrats_actifs'] / stats_globales['total_proprietes']) * 100
        
        # Récupérer l'historique des paiements du mois
        historique_paiements = []
        for propriete in proprietes_actives:
            contrat_actif = propriete.contrats.filter(est_actif=True).first()
            if contrat_actif:
                paiements_mois = contrat_actif.paiements.filter(
                    date_paiement__year=recap.mois_recap.year,
                    date_paiement__month=recap.mois_recap.month,
                    type_paiement='loyer'
                ).order_by('-date_paiement')
                
                for paiement in paiements_mois:
                    historique_paiements.append({
                        'propriete': propriete.titre or f"Propriété #{propriete.id}",
                        'locataire': contrat_actif.locataire.get_nom_complet(),
                        'montant': paiement.montant,
                        'date_paiement': paiement.date_paiement,
                        'statut': paiement.get_statut_display(),
                        'methode_paiement': paiement.get_methode_paiement_display(),
                    })
        
        # Récupérer la configuration de l'entreprise
        from core.models import ConfigurationEntreprise
        entreprise_config = ConfigurationEntreprise.get_configuration_active()
        
        # Générer le PDF avec xhtml2pdf
        from django.template.loader import render_to_string
        from xhtml2pdf import pisa
        from io import BytesIO
        from django.http import HttpResponse
        
        html_content = render_to_string(
            'paiements/recapitulatif_mensuel_detaille_paysage.html',
            {
                'recap': recap,
                'proprietes_details': proprietes_details,
                'stats_globales': stats_globales,
                'historique_paiements': historique_paiements,
                'entreprise_config': entreprise_config,
                'date_generation': timezone.now(),
            }
        )
        
        # Créer le PDF
        pdf_buffer = BytesIO()
        pisa_status = pisa.CreatePDF(html_content, dest=pdf_buffer)
        
        if pisa_status.err:
            messages.error(request, f"Erreur lors de la génération du PDF: {pisa_status.err}")
            return redirect('paiements:detail_recap_mensuel_auto', recap_id=recap.id)
        
        # Préparer la réponse
        pdf_content = pdf_buffer.getvalue()
        pdf_buffer.close()
        
        response = HttpResponse(pdf_content, content_type='application/pdf')
        bailleur_nom = recap.bailleur.get_nom_complet() if recap.bailleur else "sans_bailleur"
        response['Content-Disposition'] = f'attachment; filename="recapitulatif_detaille_{bailleur_nom.replace(" ", "_")}_{recap.mois_recap.strftime("%Y_%m")}.pdf"'
        
        return response
        
    except Exception as e:
        messages.error(request, f"Erreur lors de la génération du PDF détaillé: {str(e)}")
        return redirect('paiements:detail_recap_mensuel_auto', recap_id=recap_id)


# Vues de suppression génériques
from utilisateurs.mixins_suppression import SuppressionGeneriqueView

class SupprimerPaiementView(SuppressionGeneriqueView):
    model = Paiement
    
    def get_redirect_url(self, obj):
        return 'paiements:liste'
    
    def get_success_message(self, obj):
        return f"Paiement #{obj.id} supprimé avec succès."


