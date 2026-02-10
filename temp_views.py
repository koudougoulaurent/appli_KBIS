from django.http import FileResponse, HttpResponse
# --- Vue pour t├®l├®charger la quittance PDF KBIS d'un paiement ---
from django.contrib.auth.decorators import login_required
@login_required
def telecharger_quittance_kbis_pdf(request, paiement_id):
    """Permet de t├®l├®charger la quittance PDF KBIS g├®n├®r├®e pour un paiement donn├® (reliquat ou partiel)."""
    paiement = get_object_or_404(Paiement, pk=paiement_id)
    pdf_content = paiement.generer_quittance_kbis_dynamique(request.user)
    if pdf_content:
        response = HttpResponse(pdf_content, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="quittance_kbis_{paiement_id}.pdf"'
        return response
    else:
        messages.error(request, "Erreur lors de la g├®n├®ration du PDF de quittance KBIS.")
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
# from .models import TableauBordFinancier  # Mod├¿le supprim├®
# from .forms import TableauBordFinancierForm  # Formulaire supprim├®
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
    """Affiche l'historique des paiements partiels pour un contrat et un mois donn├®."""
    try:
        # Convertir les param├¿tres en entiers
        mois_int = int(mois)
        annee_int = int(annee)
        
        # Valider que le mois est entre 1 et 12
        if mois_int < 1 or mois_int > 12:
            messages.error(request, f"Mois invalide: {mois}. Le mois doit ├¬tre entre 1 et 12.")
            return redirect('paiements:liste')
        
        # Construire la cha├«ne attendue au format "Mois Ann├®e"
        mois_noms = [
            'Janvier', 'F├®vrier', 'Mars', 'Avril', 'Mai', 'Juin',
            'Juillet', 'Ao├╗t', 'Septembre', 'Octobre', 'Novembre', 'D├®cembre'
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
        messages.error(request, f"Param├¿tres invalides: mois={mois}, ann├®e={annee}")
        return redirect('paiements:liste')
    except Contrat.DoesNotExist:
        messages.error(
            request,
            f"Aucun contrat trouv├® avec l'identifiant {contrat_id}. "
            "V├®rifiez l'ID ou <a href='/contrats/liste/'>consultez la liste des contrats</a>. "
            "Vous pouvez aussi <a href='/contrats/ajouter/'>ajouter un nouveau contrat</a>."
        )
        return render(request, 'paiements/historique_partiel.html', {'contrat': None, 'paiements': [], 'mois': mois, 'annee': annee})
    montant_du_mois = paiements.first().montant_du_mois if paiements.exists() else Decimal(str(contrat.loyer_mensuel)) if contrat.loyer_mensuel else Decimal('0')
    total_paye = sum([p.montant for p in paiements])
    montant_restant = max(montant_du_mois - total_paye, 0)
    statut = 'valide' if montant_restant == 0 else 'partiellement_pay├®'
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


# -- VUE AM├ëLIOR├ëE POUR LES PAIEMENTS PARTIELS --
@login_required
def ajouter_paiement_partiel(request):
    """
    Vue am├®lior├®e pour ajouter un paiement partiel avec interface moderne
    et d├®tection automatique
    """
    from .services_paiement_partiel import ServicePaiementPartiel
    from .forms import PaiementForm
    
    contrat_id = request.GET.get('contrat_id')
    contrat_obj = None
    calcul_restant = None
    
    if contrat_id:
        try:
            contrat_obj = Contrat.objects.get(pk=contrat_id, est_actif=True, is_deleted=False)
            # D├ëTERMINER LE MOIS ├Ç R├ëGLER EN UTILISANT LA M├èME LOGIQUE QUE LES PAIEMENTS GLOBAUX
            mois_a_regler = ServicePaiementPartiel.determiner_mois_a_regler(contrat_obj)
            calcul_restant = ServicePaiementPartiel.calculer_montant_restant(
                contrat_obj, mois_a_regler['mois_paye']
            )
            
            # NOUVEAU : D├®tecter les reliquats en cours pour ce contrat
            reliquats = ServicePaiementPartiel.detecter_reliquats_en_cours(contrat_obj)
        except Contrat.DoesNotExist:
            messages.error(request, "Contrat introuvable ou inactif.")
            reliquats = []
    
    if request.method == 'POST':
        form = PaiementForm(request.POST)
        if form.is_valid():
            paiement = form.save(commit=False)
            paiement.cree_par = request.user
            
            # *** NOUVEAU : V├ëRIFICATION DES RELIQUATS EN COURS ***
            # V├®rifier s'il y a des paiements partiels non compl├®t├®s pour ce contrat
            ignorer_reliquat = request.POST.get('ignorer_reliquat', '') == 'oui'
            
            if not ignorer_reliquat and paiement.contrat:
                reliquats_post = ServicePaiementPartiel.detecter_reliquats_en_cours(paiement.contrat)
                
                if reliquats_post:
                    # Il y a des reliquats - afficher une alerte et demander confirmation
                    total_reliquat_post = sum(r['montant_restant'] for r in reliquats_post)
                    
                    # Pr├®parer le contexte avec les reliquats
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
            
            # *** VALIDATION STRICTE : V├®rifier que le mois est le mois suivant le dernier paiement ***
            mois_paye_nom = request.POST.get('mois_paye', '')
            if mois_paye_nom:
                # Si le mois n'a pas d'ann├®e, construire le format complet
                import re
                if not re.search(r'\d{4}', mois_paye_nom):
                    # Pas d'ann├®e dans le mois - d├®terminer l'ann├®e intelligemment
                    from datetime import datetime
                    mois_francais = {
                        'janvier': 1, 'f├®vrier': 2, 'mars': 3, 'avril': 4,
                        'mai': 5, 'juin': 6, 'juillet': 7, 'ao├╗t': 8,
                        'septembre': 9, 'octobre': 10, 'novembre': 11, 'd├®cembre': 12
                    }
                    annee_actuelle = datetime.now().year
                    
                    # Utiliser TOUJOURS l'ann├®e courante r├®elle
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
                            f"Les paiements partiels ne peuvent ├¬tre enregistr├®s que pour le mois courant ou les mois pass├®s. "
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
                            f"Les paiements partiels doivent ├¬tre pour le mois attendu ({validation.get('mois_attendu', '')}) ou un mois en retard."
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
                        # Mois d├®j├á compl├¿tement pay├® - REFUSER
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
                    messages.info(request, validation.get('message_info', 'Paiement en retard autoris├® pour se rattraper.'))
            else:
                # Si pas de mois sp├®cifi├®, utiliser le mois attendu
                mois_a_regler = ServicePaiementPartiel.determiner_mois_a_regler(paiement.contrat)
                paiement.mois_paye = mois_a_regler['mois_paye']
            
            # Synchroniser automatiquement le paiement partiel
            est_partiel = ServicePaiementPartiel.synchroniser_paiement_partiel(paiement)
            paiement.save()
            
            # G├®n├®rer la r├®f├®rence
            if not paiement.reference_paiement:
                paiement.reference_paiement = paiement.generate_reference_paiement()
                paiement.save()
            
            # V├ëRIFIER SI CE PAIEMENT COMPL├êTE UN RELIQUAT
            if paiement.mois_paye:
                calcul_restant = ServicePaiementPartiel.calculer_montant_restant(
                    paiement.contrat, paiement.mois_paye
                )
                if calcul_restant.get('est_complet', False):
                    messages.success(
                        request,
                        f'Ô£à Reliquat compl├®t├® ! Le mois {paiement.mois_paye} est maintenant enti├¿rement pay├®. '
                        f'Tous les paiements partiels concern├®s ont ├®t├® marqu├®s comme compl├®t├®s automatiquement.'
                    )
                elif est_partiel:
                    messages.success(
                        request,
                        f'Paiement partiel enregistr├®: {paiement.reference_paiement} - '
                        f'Montant pay├®: {paiement.montant} F CFA, '
                        f'Montant restant: {paiement.montant_restant_du} F CFA'
                    )
                else:
                    messages.success(
                        request,
                        f'Paiement enregistr├®: {paiement.reference_paiement}'
                    )
            else:
                if est_partiel:
                    messages.success(
                        request,
                        f'Paiement partiel enregistr├®: {paiement.reference_paiement} - '
                        f'Montant pay├®: {paiement.montant} F CFA, '
                        f'Montant restant: {paiement.montant_restant_du} F CFA'
                    )
                else:
                    messages.success(
                        request,
                        f'Paiement enregistr├®: {paiement.reference_paiement}'
                    )
            
            return redirect('paiements:liste_contrats_paiements_partiels')
    else:
        # Pr├®-remplir le formulaire avec le mois attendu si un contrat est s├®lectionn├®
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
    
    # D├ëTERMINER LE MOIS ├Ç R├ëGLER (m├¬me logique que paiements globaux)
    mois_a_regler = None
    if contrat_obj:
        mois_a_regler = ServicePaiementPartiel.determiner_mois_a_regler(contrat_obj)
    elif contrat_id:
        try:
            contrat_temp = Contrat.objects.get(pk=contrat_id, est_actif=True, is_deleted=False)
            mois_a_regler = ServicePaiementPartiel.determiner_mois_a_regler(contrat_temp)
        except:
            pass
    
    # NOUVEAU : Calculer les reliquats si contrat s├®lectionn├®
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
        'reliquats': reliquats,  # NOUVEAU : Reliquats d├®tect├®s
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
    
    # R├®cup├®rer les param├¿tres GET
    search = request.GET.get('search', '').strip()
    sort = request.GET.get('sort', 'locataire')  # Par d├®faut tri par locataire
    order = request.GET.get('order', 'asc')
    statut = request.GET.get('statut', '')  # reliquat, solde, tous
    propriete_id = request.GET.get('propriete', '')
    
    # D├®tecter les contrats avec paiements partiels (inclut tous les paiements partiels)
    contrats_avec_partiels = ServicePaiementPartiel.detecter_contrats_avec_paiements_partiels()
    
    # Filtrage/recherche intelligent (en m├®moire, car peu de contrats)
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
        # Filtre propri├®t├®
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
    
    # Obtenir les statistiques DYNAMIQUEMENT ├á partir des contrats filtr├®s
    stats = ServicePaiementPartiel.obtenir_statistiques_paiements_partiels({i: d for i, d in enumerate(filtered_sorted)})
    
    # Pour le filtre propri├®t├® : liste des propri├®t├®s concern├®es
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


# -- VUE POUR COMPL├ëTER UN RELIQUAT --
@login_required
def completer_reliquat(request, paiement_id):
    """
    Vue pour compl├®ter un reliquat de paiement partiel avec un formulaire d├®di├®
    """
    from .services_paiement_partiel import ServicePaiementPartiel
    
    # R├®cup├®rer le paiement initial
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
    
    # R├®cup├®rer tous les paiements existants pour ce mois
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
                messages.error(request, "Le montant doit ├¬tre sup├®rieur ├á 0.")
                return redirect('paiements:completer_reliquat', paiement_id=paiement_id)
            
            if montant > calcul['montant_restant']:
                messages.error(
                    request,
                    f"Le montant ({montant:,.0f} F) d├®passe le montant restant ({calcul['montant_restant']:,.0f} F)."
                )
                return redirect('paiements:completer_reliquat', paiement_id=paiement_id)
            
            # Cr├®er le paiement de compl├®tion
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
                    notes=f"Compl├®tion de reliquat. {notes}",
                    cree_par=request.user
                )
                
                # Ajouter r├®f├®rence si fournie
                if numero_reference:
                    if mode_paiement == 'cheque':
                        nouveau_paiement.numero_cheque = numero_reference
                    elif mode_paiement == 'virement':
                        nouveau_paiement.reference_virement = numero_reference
                    nouveau_paiement.save()
                
                # V├®rifier et compl├®ter automatiquement le reliquat
                completion_effectuee = ServicePaiementPartiel.verifier_et_completer_reliquat(
                    paiement=nouveau_paiement,
                    skip_save=False
                )
                
                if completion_effectuee:
                    messages.success(
                        request,
                        f"Ô£à Reliquat compl├®t├® avec succ├¿s ! "
                        f"Le mois {mois_paye} est maintenant enti├¿rement pay├®."
                    )
                else:
                    nouveau_montant_restant = calcul['montant_restant'] - montant
                    messages.success(
                        request,
                        f"Ô£à Paiement partiel ajout├® avec succ├¿s ! "
                        f"Reste ├á payer : {nouveau_montant_restant:,.0f} F CFA"
                    )
                
                # G├®n├®rer une quittance PDF A5 KBIS pour ce paiement
                try:
                    quittance_pdf = nouveau_paiement.generer_quittance_kbis_dynamique(request.user)
                    if quittance_pdf:
                        messages.info(request, "­ƒôä Quittance PDF KBIS g├®n├®r├®e avec succ├¿s.")
                    else:
                        messages.warning(request, "ÔÜá´©Å Paiement enregistr├® mais erreur lors de la g├®n├®ration de la quittance PDF.")
                except Exception as e:
                    messages.warning(request, f"ÔÜá´©Å Paiement enregistr├® mais erreur quittance : {str(e)}")
                
                return redirect('paiements:liste_contrats_paiements_partiels')
                
        except Exception as e:
            messages.error(request, f"ÔØî Erreur lors de l'ajout du paiement : {str(e)}")
            return redirect('paiements:completer_reliquat', paiement_id=paiement_id)
    
    # GET - Afficher le formulaire
    context = get_context_with_entreprise_config({
        'paiement_initial': paiement_initial,
        'calcul': calcul,
        'paiements_existants': paiements_existants,
        'pourcentage': pourcentage,
        'date_today': timezone.now().date().isoformat(),
        'title': f'Compl├®ter le Reliquat - {contrat.numero_contrat}'
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
# from .models import TableauBordFinancier  # Mod├¿le supprim├®
# from .forms import TableauBordFinancierForm  # Formulaire supprim├®
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
    Dashboard principal des paiements S├ëCURIS├ë - SANS informations financi├¿res confidentielles
    """
    # Statistiques g├®n├®rales (NON confidentielles)
    # Optimisation : utiliser une seule requ├¬te avec annotate au lieu de 4 requ├¬tes s├®par├®es
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
    
    # SUPPRIMER: Tous les montants financiers pour la confidentialit├®
    # NE PAS calculer ou afficher de montants
    
    # Top propri├®t├®s par activit├® (NON par revenus)
    top_proprietes_activite = Paiement.objects.filter(
        is_deleted=False,
        statut='valide'
    ).values(
        'contrat__propriete__titre', 
        'contrat__propriete__ville'
    ).annotate(
        nombre_paiements=Count('id')  # Nombre de paiements, PAS les montants
    ).order_by('-nombre_paiements')[:5]
    
    # Paiements r├®cents (SANS montants) - utiliser date_paiement au lieu de created_at
    paiements_recents = Paiement.objects.filter(
        is_deleted=False
    ).select_related('contrat__propriete', 'contrat__locataire').order_by('-date_paiement')[:5]
    
    # Paiements n├®cessitant attention (SANS montants)
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
            'activite': '├ëlev├®e' if nombre_paiements_mois > 10 else 'Mod├®r├®e' if nombre_paiements_mois > 5 else 'Faible'
        })
    
    mois_stats.reverse()
    
    # Donn├®es des retraits bailleurs
    from django.db import models
    
    # Statistiques des retraits (simplifi├®)
    retraits_valides = RetraitBailleur.objects.filter(is_deleted=False, statut='valide').count()
    retraits_payes = RetraitBailleur.objects.filter(is_deleted=False, statut='paye').count()
    retraits_en_attente = RetraitBailleur.objects.filter(is_deleted=False, statut='en_attente').count()
    
    # Calcul du montant total des retraits valid├®s
    montant_total_retraits = RetraitBailleur.objects.filter(
        is_deleted=False, 
        statut='valide'
    ).aggregate(
        total=models.Sum('montant_net_a_payer')
    )['total'] or 0
    
    # Retraits r├®cents (5 derniers)
    retraits_recents = RetraitBailleur.objects.filter(
        is_deleted=False
    ).select_related('bailleur').order_by('-date_demande')[:5]
    
    context = {
        'total_paiements': total_paiements,
        'paiements_valides': paiements_valides,
        'paiements_en_attente': paiements_en_attente,
        'paiements_refuses': paiements_refuses,
        # SUPPRIMER: montant_total, montant_mois_courant
        'top_proprietes_activite': top_proprietes_activite,  # Activit├®, PAS revenus
        'paiements_recents': paiements_recents,
        'paiements_attention': paiements_attention,
        'mois_stats': mois_stats,
        # Nouvelles donn├®es pour les retraits
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
        
        # R├®cup├®rer les param├¿tres de recherche pour les afficher dans le template
        context['query'] = self.request.GET.get('q', '')
        context['statut_filter'] = self.request.GET.get('statut', '')
        context['type_filter'] = self.request.GET.get('type_paiement', '')
        context['mode_filter'] = self.request.GET.get('mode_paiement', '')
        
        # Statistiques pour le contexte (bas├®es sur les filtres actifs)
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
    Vue de liste am├®lior├®e pour les paiements avec recherche intelligente
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
        # S'assurer que object_list est d├®fini
        if not hasattr(self, 'object_list'):
            self.object_list = self.get_queryset()
        context = super().get_context_data(**kwargs)
        
        # Configuration des colonnes
        context['columns'] = [
            {'field': 'numero_paiement', 'label': 'N┬░ Paiement', 'sortable': True},
            {'field': 'contrat__locataire', 'label': 'Locataire', 'sortable': True},
            {'field': 'contrat__propriete', 'label': 'Propri├®t├®', 'sortable': True},
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
                ('valide', 'Valid├®'),
                ('en_attente', 'En attente'),
                ('refuse', 'Refus├®'),
            ],
            'type_paiement': [
                ('loyer', 'Loyer'),
                ('caution', 'Caution'),
                ('avance', 'Avance'),
            ],
            'mode_paiement': [
                ('especes', 'Esp├¿ces'),
                ('virement', 'Virement'),
                ('cheque', 'Ch├¿que'),
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
    # V├®rification des permissions
    from core.utils import check_group_permissions
    
    # ­ƒöì DEBUG : Afficher les infos utilisateur et permissions (uniquement en mode DEBUG)
    if settings.DEBUG:
        print(f"­ƒöì DEBUG ajouter_paiement:")
        print(f"   User: {request.user.username}")
        print(f"   Authenticated: {request.user.is_authenticated}")
        print(f"   Groupe: {getattr(request.user, 'groupe_travail', None)}")
    
    permissions = check_group_permissions(request.user, [], 'add')
    if settings.DEBUG:
        print(f"   Permissions: {permissions}")
    
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        if settings.DEBUG:
            print(f"   ÔØî ACC├êS REFUS├ë: {permissions['message']}")
        return redirect('paiements:liste')
    
    # Initialiser les variables pour le contexte (utilis├®es dans GET et POST)
    contrat_obj_get = None
    reliquats = []
    total_reliquat = 0
    mois_autorises = []  # CORRECTION: Initialiser pour ├®viter UnboundLocalError
    mois_attendu = ""    # CORRECTION: Initialiser pour ├®viter UnboundLocalError
    
    if request.method == 'POST':
        form = PaiementForm(request.POST)
        if settings.DEBUG:
            print(f"Donn├®es POST: {request.POST}")
            print(f"Formulaire valide: {form.is_valid()}")
        if not form.is_valid():
            if settings.DEBUG:
                print(f"Erreurs du formulaire: {form.errors}")
            # Si le formulaire n'est pas valide, r├®cup├®rer le contrat depuis les donn├®es POST
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
                
                # *** NOUVEAU : V├ëRIFICATION DES RELIQUATS EN COURS ***
                # V├®rifier s'il y a des paiements partiels non compl├®t├®s pour ce contrat
                ignorer_reliquat = request.POST.get('ignorer_reliquat', '') == 'oui'
                
                if not ignorer_reliquat and paiement.contrat:
                    from .services_paiement_partiel import ServicePaiementPartiel
                    reliquats = ServicePaiementPartiel.detecter_reliquats_en_cours(paiement.contrat)
                    
                    if reliquats:
                        # Il y a des reliquats - afficher une alerte et demander confirmation
                        total_reliquat = sum(r['montant_restant'] for r in reliquats)
                        
                        # Pr├®parer le contexte avec les reliquats
                        context = {
                            'form': form,
                            'contrats': Contrat.objects.filter(is_deleted=False).select_related('locataire', 'propriete'),
                            'contrat_obj': paiement.contrat,
                            'reliquats': reliquats,
                            'total_reliquat': total_reliquat,
                            'afficher_alerte_reliquat': True,
                        }
                        
                        # R├®cup├®rer la devise de base
                        try:
                            from core.models import Devise
                            devise_base = Devise.objects.filter(is_devise_base=True).first()
                            context['devise_base'] = devise_base
                        except:
                            context['devise_base'] = None
                        
                        # G├®n├®rer les ann├®es disponibles
                        current_year = timezone.now().year
                        context['annees_disponibles'] = list(range(current_year - 2, current_year + 3))
                        
                        return render(request, 'paiements/ajouter.html', context)
                
                # Le champ date_creation sera automatiquement d├®fini par auto_now_add=True
                
                # *** VALIDATION STRICTE : V├®rifier que le mois est le mois suivant le dernier paiement ***
                # Cette validation s'applique UNIQUEMENT pour les paiements de LOYER
                if paiement.type_paiement == 'loyer':
                    mois_paye_nom = request.POST.get('mois_paye', '')
                    annee_paiement = request.POST.get('annee_paiement', '')
                    
                    # Si pas de mois sp├®cifi├®, utiliser le mois attendu
                    if not mois_paye_nom:
                        from .services_paiement_partiel import ServicePaiementPartiel
                        mois_attendu = ServicePaiementPartiel.determiner_mois_a_regler(paiement.contrat)
                        mois_paye_nom = mois_attendu['mois_paye']
                    else:
                        # Si le mois n'a pas d'ann├®e, utiliser l'ann├®e du champ annee_paiement ou l'ann├®e courante
                        import re
                        if not re.search(r'\d{4}', mois_paye_nom):
                            # Pas d'ann├®e dans le mois - utiliser l'ann├®e du champ annee_paiement
                            if annee_paiement:
                                try:
                                    annee = int(annee_paiement)
                                    mois_paye_nom = f"{mois_paye_nom} {annee}"
                                except ValueError:
                                    # Si l'ann├®e n'est pas valide, utiliser l'ann├®e courante
                                    from datetime import datetime
                                    annee_actuelle = datetime.now().year
                                    mois_paye_nom = f"{mois_paye_nom} {annee_actuelle}"
                            else:
                                # Pas d'ann├®e fournie - utiliser l'ann├®e courante
                                from datetime import datetime
                                annee_actuelle = datetime.now().year
                                mois_paye_nom = f"{mois_paye_nom} {annee_actuelle}"
                        else:
                            # Le mois contient d├®j├á une ann├®e, mais on peut la remplacer par celle du champ annee_paiement si fournie
                            if annee_paiement:
                                try:
                                    annee = int(annee_paiement)
                                    # Remplacer l'ann├®e existante par celle du champ
                                    mois_sans_annee = re.sub(r'\s+\d{4}$', '', mois_paye_nom).strip()
                                    mois_paye_nom = f"{mois_sans_annee} {annee}"
                                except ValueError:
                                    pass  # Garder l'ann├®e existante si l'ann├®e fournie n'est pas valide
                    
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
                            # Recharger le formulaire avec le type chang├® en avance
                            form = PaiementForm(request.POST)
                            form.data = form.data.copy()
                            form.data['type_paiement'] = 'avance'
                            
                            # Pr├®parer le contexte
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
                                f"Si vous souhaitez payer plusieurs mois ├á l'avance, changez le type de paiement en 'AVANCE DE LOYER'."
                            )
                            return redirect('paiements:ajouter')
                        elif type_erreur == 'mois_deja_paye':
                            # Mois d├®j├á compl├¿tement pay├® - REFUSER
                            messages.error(request, validation_mois['message'])
                            return redirect('paiements:ajouter')
                        else:
                            # Autre erreur (format invalide, etc.) - REFUSER
                            messages.error(request, validation_mois.get('message', 'Erreur de validation'))
                            return redirect('paiements:ajouter')
                    
                    # Validation OK - utiliser le mois valid├®
                    paiement.mois_paye = validation_mois['mois_attendu']
                    
                    # Afficher un message informatif si c'est un paiement en retard
                    if validation_mois.get('est_retard'):
                        messages.info(request, validation_mois.get('message_info', 'Paiement en retard autoris├® pour se rattraper.'))
                elif request.POST.get('mois_paye', ''):
                    # Pour les autres types de paiement (avance, caution), utiliser le mois tel quel
                    mois_paye_nom = request.POST.get('mois_paye', '')
                    from datetime import datetime
                    import re
                    
                    # Si le mois n'a pas d'ann├®e, construire le format complet avec l'ann├®e courante r├®elle
                    if not re.search(r'\d{4}', mois_paye_nom):
                        annee_actuelle = datetime.now().year
                        paiement.mois_paye = f"{mois_paye_nom} {annee_actuelle}"
                    else:
                        paiement.mois_paye = mois_paye_nom
                # NOTE: Pour les paiements de loyer, le mois_paye est d├®j├á d├®fini par la validation stricte ci-dessus
                
                # *** D├ëTECTION ET SYNCHRONISATION AUTOMATIQUE DES PAIEMENTS PARTIELS ***
                from .services_paiement_partiel import ServicePaiementPartiel
                
                # D├®tecter si c'est un paiement partiel
                est_partiel = ServicePaiementPartiel.synchroniser_paiement_partiel(paiement)
                
                # Sauvegarder le paiement avec les informations de paiement partiel
                paiement.save()
                
                # G├®n├®rer la r├®f├®rence si elle n'existe pas
                if not paiement.reference_paiement:
                    paiement.reference_paiement = paiement.generate_reference_paiement()
                    paiement.save()
                
                # V├ëRIFIER SI CE PAIEMENT COMPL├êTE UN RELIQUAT
                # Cette v├®rification est faite automatiquement dans synchroniser_paiement_partiel
                # mais on la refait ici pour s'assurer que tout est ├á jour
                if paiement.mois_paye:
                    calcul_restant = ServicePaiementPartiel.calculer_montant_restant(
                        paiement.contrat, paiement.mois_paye
                    )
                    if calcul_restant.get('est_complet', False):
                        messages.success(
                            request,
                            f'Ô£à Reliquat compl├®t├® ! Le mois {paiement.mois_paye} est maintenant enti├¿rement pay├®. '
                            f'Tous les paiements partiels concern├®s ont ├®t├® marqu├®s comme compl├®t├®s.'
                        )
                    elif est_partiel:
                        messages.info(
                            request,
                            f'Paiement partiel d├®tect├®: {paiement.reference_paiement} - '
                            f'Montant pay├®: {paiement.montant} F CFA, '
                            f'Montant restant: {paiement.montant_restant_du} F CFA'
                        )
                
                # *** SYNCHRONISATION AUTOMATIQUE DES AVANCES ***
                # Si c'est un paiement d'avance, synchroniser automatiquement l'avance
                if paiement.type_paiement == 'avance':
                    try:
                        from .services_synchronisation_avances import ServiceSynchronisationAvances
                        avance = ServiceSynchronisationAvances.synchroniser_avance_avec_paiement(paiement)
                        if avance:
                            messages.success(request, f'Paiement {paiement.reference_paiement} cr├®├® avec succ├¿s! '
                                                    f'Avance de {avance.nombre_mois_couverts} mois synchronis├®e automatiquement.')
                        else:
                            messages.warning(request, f'Paiement {paiement.reference_paiement} cr├®├®, mais erreur lors de la synchronisation de l\'avance.')
                    except Exception as e:
                        messages.warning(request, f'Paiement {paiement.reference_paiement} cr├®├®, mais erreur lors de la synchronisation de l\'avance: {str(e)}')
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
                        
                        # D├®terminer le mois du paiement
                        mois_paiement = paiement.date_paiement.replace(day=1)
                        
                        # Validation 2: V├®rifier les avances actives
                        avances_actives = AvanceLoyer.objects.filter(
                            contrat=paiement.contrat,
                            statut='active',
                            montant_restant__gt=0
                        )
                        
                        if avances_actives.exists():
                            # Il y a des avances actives - v├®rifier que le mois correspond
                            prochain_mois_attendu = ServiceGestionAvance.calculer_prochain_mois_paiement(paiement.contrat)
                            
                            if mois_paiement != prochain_mois_attendu:
                                messages.error(request, f'Avec les avances actives, vous devez payer pour {prochain_mois_attendu.strftime("%B %Y")}. '
                                                      f'Cr├®ez une avance si vous voulez payer pour un autre mois.')
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
                                
                                messages.success(request, f'Paiement {paiement.reference_paiement} ajust├® avec l\'avance! '
                                                        f'Montant: {montant_consomme} F CFA pour {mois_paiement.strftime("%B %Y")}')
                            else:
                                messages.success(request, f'Paiement {paiement.reference_paiement} cr├®├® avec succ├¿s!')
                        else:
                            # Pas d'avances - la validation stricte a d├®j├á ├®t├® faite plus haut
                            # Le mois_paye a ├®t├® valid├® et est garanti d'├¬tre le mois suivant le dernier paiement
                            messages.success(request, f'Paiement {paiement.reference_paiement} cr├®├® avec succ├¿s!')
                            
                    except Exception as e:
                        messages.warning(request, f'Paiement {paiement.reference_paiement} cr├®├®, mais erreur lors de la validation: {str(e)}')
                
                # *** NOUVEAU : V├®rifier et cr├®er des avances pour les paiements d'avance existants ***
                # Cette logique s'ex├®cute ├á chaque ajout de paiement pour s'assurer que tous les paiements d'avance
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
                        # V├®rifier si un AvanceLoyer existe d├®j├á pour ce paiement
                        avance_existant = AvanceLoyer.objects.filter(
                            contrat=paiement_avance.contrat,
                            montant_avance=paiement_avance.montant,
                            date_avance=paiement_avance.date_paiement
                        ).first()
                        
                        if not avance_existant:
                            # Cr├®er l'AvanceLoyer manquant
                            try:
                                avance = ServiceGestionAvance.creer_avance_loyer(
                                    contrat=paiement_avance.contrat,
                                    montant_avance=Decimal(str(paiement_avance.montant)),
                                    date_avance=paiement_avance.date_paiement,
                                    notes=f"Cr├®├® automatiquement depuis paiement {paiement_avance.id}"
                                )
                                print(f"AvanceLoyer cr├®├® automatiquement: {avance.id} pour paiement {paiement_avance.id}")
                            except Exception as e:
                                print(f"Erreur cr├®ation AvanceLoyer pour paiement {paiement_avance.id}: {str(e)}")
                                
                except Exception as e:
                    print(f"Erreur lors de la v├®rification des avances manquantes: {str(e)}")
                
                return redirect('paiements:liste')
                
            except Exception as e:
                import traceback
                error_details = traceback.format_exc()
                print(f"Erreur d├®taill├®e: {error_details}")
                messages.error(request, f'Erreur lors de la validation du paiement: {str(e)}')
    else:
        # V├®rifier s'il y a un contrat s├®lectionn├® dans le GET pour afficher les reliquats
        contrat_id_get = request.GET.get('contrat_id')
        
        if contrat_id_get:
            try:
                contrat_obj_get = Contrat.objects.get(pk=contrat_id_get, is_deleted=False)
                from .services_paiement_partiel import ServicePaiementPartiel
                reliquats = ServicePaiementPartiel.detecter_reliquats_en_cours(contrat_obj_get)
                total_reliquat = sum(r['montant_restant'] for r in reliquats)
                
                # Calculer les mois autoris├®s pour les paiements de loyer
                # Mois attendu + mois en retard (pour rattrapage)
                mois_attendu_data = ServicePaiementPartiel.determiner_mois_a_regler(contrat_obj_get)
                mois_attendu = mois_attendu_data['mois_paye']
                date_mois_attendu = mois_attendu_data['date_mois']
                
                # Construire la liste des mois autoris├®s
                mois_autorises = [{
                    'mois_paye': mois_attendu,
                    'mois_label': f"{mois_attendu} (Mois attendu)"
                }]
                
                # Ajouter les mois en retard (mois entre le d├®but du contrat et le mois attendu)
                from datetime import date
                from dateutil.relativedelta import relativedelta
                mois_courant = timezone.now().date().replace(day=1)
                mois_francais = [
                    'janvier', 'f├®vrier', 'mars', 'avril', 'mai', 'juin',
                    'juillet', 'ao├╗t', 'septembre', 'octobre', 'novembre', 'd├®cembre'
                ]
                
                # CRITIQUE : R├®cup├®rer le dernier paiement valid├® pour d├®terminer le point de d├®part
                from .models import Paiement
                dernier_paiement = Paiement.objects.filter(
                    contrat=contrat_obj_get,
                    type_paiement='loyer',
                    statut='valide',
                    is_deleted=False
                ).order_by('-date_paiement').first()
                
                # D├®terminer le dernier mois pay├® (bas├® sur mois_paye si disponible)
                dernier_mois_paye_date = None
                if dernier_paiement:
                    if dernier_paiement.mois_paye:
                        dernier_mois_paye_date = ServicePaiementPartiel.convertir_mois_paye_en_date(dernier_paiement.mois_paye)
                    if not dernier_mois_paye_date:
                        dernier_mois_paye_date = dernier_paiement.date_paiement.replace(day=1)
                else:
                    # Pas de paiement pr├®c├®dent - utiliser le d├®but du contrat
                    dernier_mois_paye_date = contrat_obj_get.date_debut.replace(day=1) if contrat_obj_get.date_debut else None
                
                # Calculer UNIQUEMENT les mois en retard entre le dernier paiement et le mois attendu
                if dernier_mois_paye_date:
                    mois_en_retard = dernier_mois_paye_date + relativedelta(months=1)  # Commencer au mois suivant le dernier paiement
                    
                    # Parcourir uniquement les mois entre le dernier paiement et le mois attendu
                    while mois_en_retard < date_mois_attendu:
                        # V├®rifier si ce mois est d├®j├á compl├¿tement pay├®
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
                            # Si le mois est compl├¿tement pay├®, ne pas l'ajouter
                            if total_paye >= montant_du_mois:
                                mois_en_retard = mois_en_retard + relativedelta(months=1)
                                continue
                        
                        # Ajouter ce mois en retard ├á la liste (seulement s'il est non pay├® ou partiellement pay├®)
                        mois_autorises.append({
                            'mois_paye': mois_str,
                            'mois_label': f"{mois_str} (Rattrapage)"
                        })
                        
                        mois_en_retard = mois_en_retard + relativedelta(months=1)
                
            except Contrat.DoesNotExist:
                pass
        
        # Initialiser le formulaire avec les mois autoris├®s pour les paiements de loyer
        form = PaiementForm(contrat_id=contrat_id_get, mois_autorises=mois_autorises, type_paiement_initial='loyer')
    
    # R├®cup├®rer tous les contrats pour la s├®lection
    contrats = Contrat.objects.filter(is_deleted=False).select_related('locataire', 'propriete')
    
    # R├®cup├®rer la devise de base
    try:
        devise_base = Devise.objects.filter(is_devise_base=True).first()
    except:
        devise_base = None
    
    # G├®n├®rer les ann├®es disponibles (ann├®e actuelle ┬▒ 2 ans)
    current_year = timezone.now().year
    annees_disponibles = list(range(current_year - 2, current_year + 3))
    
    context = {
        'form': form,
        'contrats': contrats,
        'contrat_obj': contrat_obj_get,
        'reliquats': reliquats,  # NOUVEAU : Reliquats d├®tect├®s
        'total_reliquat': total_reliquat,  # NOUVEAU : Total des reliquats
        'afficher_alerte_reliquat': len(reliquats) > 0,  # NOUVEAU : Afficher l'alerte si reliquats
        'mois_attendu': mois_attendu,  # Mois attendu pour affichage
        'mois_autorises': mois_autorises,  # Liste des mois autoris├®s
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
    """Liste des paiements avec recherche et filtres optimis├®s."""
    try:
        # R├®cup├®rer les filtres
        query = request.GET.get('q', '')
        statut_filter = request.GET.get('statut', '')
        type_filter = request.GET.get('type_paiement', '')
        date_debut = request.GET.get('date_debut', '')
        date_fin = request.GET.get('date_fin', '')
        
        # Base QuerySet avec annotations optimis├®es
        from django.db.models import Sum, Count, F, Case, When, DecimalField, Q
        
        # Filtrer les paiements en excluant les doublons et en affichant la propri├®t├®
        paiements = Paiement.objects.filter(is_deleted=False).select_related(
            'contrat__locataire', 'contrat__propriete', 'contrat__propriete__bailleur', 'cree_par'
        ).exclude(
            # Exclure les paiements de caution qui ne sont pas marqu├®s comme pay├®s
            Q(type_paiement='caution') & Q(contrat__caution_payee=False)
        ).exclude(
            # Exclure les paiements d'avance qui ne sont pas marqu├®s comme pay├®s
            Q(type_paiement='avance') & Q(contrat__avance_loyer_payee=False)
        ).distinct().annotate(  # ├ëviter les doublons
            # Montant total format├®
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
            # Adresse compl├¿te de la propri├®t├®
            propriete_adresse_complete=Case(
                When(contrat__propriete__adresse__isnull=False,
                     contrat__propriete__ville__isnull=False,
                     then=F('contrat__propriete__adresse') + ', ' + F('contrat__propriete__ville')),
                When(contrat__propriete__adresse__isnull=False,
                     then=F('contrat__propriete__adresse')),
                default='Adresse non renseign├®e',
                output_field=models.CharField(max_length=300)
            )
        ).order_by('-created_at')
        
        # R├®cup├®rer le paiement de test pour l'afficher en premier
        paiement_test = Paiement.objects.filter(
            reference_paiement__startswith='PAIEMENT-TEST',
            is_deleted=False
        ).first()
        
        # Recherche optimis├®e
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
        
        # Filtres optimis├®s
        if statut_filter:
            paiements = paiements.filter(statut=statut_filter)
        
        if type_filter:
            paiements = paiements.filter(type_paiement=type_filter)
        
        # Filtres de dates
        if date_debut:
            paiements = paiements.filter(date_paiement__gte=date_debut)
        
        if date_fin:
            paiements = paiements.filter(date_paiement__lte=date_fin)
        
        # Calcul des statistiques avec requ├¬tes optimis├®es (montant masqu├® pour s├®curit├®)
        total_paiements = paiements.count()
        # montant_total masqu├® pour s├®curit├®
        
        # Statistiques par statut (montants masqu├®s pour s├®curit├®)
        stats_par_statut = paiements.values('statut').annotate(
            count=Count('id')
        ).order_by('statut')
        
        # Statistiques par type (montants masqu├®s pour s├®curit├®)
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
        
        # V├®rification des permissions simplifi├®e
        if not request.user.is_authenticated:
            return JsonResponse({
                'success': False,
                'error': 'Utilisateur non authentifi├®'
            }, status=403)
        
        # V├®rifier que l'utilisateur est dans un des groupes autoris├®s
        from core.utils import check_group_permissions
        permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE', 'CAISSE'], 'change')
        
        if not permissions['allowed']:
            return JsonResponse({
                'success': False,
                'error': f'Permissions insuffisantes. {permissions["message"]}'
            }, status=403)
        
        # V├®rifier que le paiement n'est pas d├®j├á valid├®
        if paiement.statut == 'valide':
            return JsonResponse({
                'success': False,
                'error': 'Ce paiement est d├®j├á valid├®'
            }, status=400)
        
        # Valider le paiement
        ancien_statut = paiement.statut
        paiement.statut = 'valide'
        paiement.valide_par = request.user
        paiement.date_encaissement = timezone.now().date()
        paiement.save()
        
        message_succes = 'Ô£à Paiement valid├® avec succ├¿s!'
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
        
        # V├®rification des permissions simplifi├®e
        if not request.user.is_authenticated:
            return JsonResponse({
                'success': False,
                'error': 'Utilisateur non authentifi├®'
            }, status=403)
        
        # V├®rifier que l'utilisateur est dans un des groupes autoris├®s
        from core.utils import check_group_permissions
        permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION'], 'change')
        
        if not permissions['allowed']:
            return JsonResponse({
                'success': False,
                'error': f'Permissions insuffisantes. {permissions["message"]}'
            }, status=403)
        
        # V├®rifier que le paiement n'est pas d├®j├á valid├®
        if paiement.statut == 'valide':
            return JsonResponse({
                'success': False,
                'error': 'Impossible de refuser un paiement d├®j├á valid├®'
            }, status=400)
        
        # Refuser le paiement
        ancien_statut = paiement.statut
        paiement.statut = 'refuse'
        paiement.save()
        
        message_succes = 'ÔØî Paiement refus├® avec succ├¿s'
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
    
    # V├®rification des permissions
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
    
    messages.success(request, 'Paiement supprim├® avec succ├¿s (suppression logique).')
    return redirect('paiements:paiement_list')


@login_required
def modifier_paiement(request, pk):
    """Modifier un paiement existant."""
    paiement = get_object_or_404(Paiement, pk=pk)
    
    # V├®rification des permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE', 'CAISSE'], 'modify')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:paiement_detail', pk=pk)
    
    old_data = {f.name: getattr(paiement, f.name) for f in paiement._meta.fields}
    
    if request.method == 'POST':
        form = PaiementForm(request.POST, instance=paiement)
        if form.is_valid():
            # Sauvegarder l'ancien statut pour v├®rifier les changements
            ancien_statut = paiement.statut
            form.save()
            
            # G├®n├®rer automatiquement un re├ºu si le statut passe ├á "valide"
            if ancien_statut != 'valide' and paiement.statut == 'valide':
                try:
                    paiement.generer_recu_automatique(request.user)
                    messages.success(request, 'Paiement modifi├® et re├ºu g├®n├®r├® automatiquement!')
                except Exception as e:
                    messages.warning(request, f'Paiement modifi├® mais erreur lors de la g├®n├®ration du re├ºu: {str(e)}')
            else:
                messages.success(request, 'Paiement modifi├® avec succ├¿s!')
            
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


# Vues pour les charges d├®ductibles
class ChargeDeductibleListView(LoginRequiredMixin, ListView):
    model = ChargeDeductible
    template_name = 'paiements/charge_deductible_list.html'
    context_object_name = 'charges'
    paginate_by = 20


charge_deductible_list = ChargeDeductibleListView.as_view()


@login_required
def ajouter_charge_deductible(request):
    """Ajouter une nouvelle charge d├®ductible."""
    permissions = check_group_permissions(request.user, [], 'add')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:charge_deductible_list')
    
    if request.method == 'POST':
        form = ChargeDeductibleForm(request.POST)
        if form.is_valid():
            charge = form.save()
            messages.success(request, 'Charge d├®ductible ajout├®e avec succ├¿s!')
            return redirect('paiements:charge_deductible_list')
    else:
        form = ChargeDeductibleForm()
    
    context = {
        'form': form,
        'title': 'Ajouter une charge d├®ductible',
    }
    
    return render(request, 'paiements/charge_deductible_form.html', context)


@login_required
def modifier_charge_deductible(request, pk):
    """Modifier une charge d├®ductible."""
    charge = get_object_or_404(ChargeDeductible, pk=pk)
    
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION'], 'modify')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:charge_deductible_list')
    
    if request.method == 'POST':
        form = ChargeDeductibleForm(request.POST, instance=charge)
        if form.is_valid():
            form.save()
            messages.success(request, 'Charge d├®ductible modifi├®e avec succ├¿s!')
            return redirect('paiements:charge_deductible_list')
    else:
        form = ChargeDeductibleForm(instance=charge)
    
    context = {
        'form': form,
        'charge': charge,
        'title': 'Modifier la charge d├®ductible',
    }
    
    return render(request, 'paiements/charge_deductible_form.html', context)


# API Views
@login_required
@require_http_methods(["GET"])
def api_paiements_data(request):
    """API pour r├®cup├®rer les donn├®es des paiements."""
    # Statistiques de base
    stats = {
        'total': Paiement.objects.count(),
        'valides': Paiement.objects.filter(statut='valide').count(),
        'en_attente': Paiement.objects.filter(statut='en_attente').count(),
        'refuses': Paiement.objects.filter(statut='refuse').count(),
        'montant_total': Paiement.objects.aggregate(total=Sum('montant'))['total'] or 0,
    }
    
    # Donn├®es par type de paiement
    types_data = list(Paiement.objects.values('type_paiement').annotate(
        count=Count('id'),
        total=Sum('montant')
    ).order_by('-count'))
    
    # Donn├®es par mode de paiement
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
    # V├®rification des permissions
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


# PLACEHOLDER VIEWS pour compatibilit├® avec les templates existants
# Ces vues sont temporaires et doivent ├¬tre impl├®ment├®es compl├¿tement

@login_required
def liste_retraits(request):
    """Liste des retraits (placeholder)."""
    messages.warning(request, 'Fonctionnalit├® des retraits en cours de d├®veloppement.')
    return redirect('paiements:liste')

@login_required
def ajouter_retrait(request):
    """Ajouter un retrait bailleur avec d├®duction automatique des charges."""
    # V├®rification des permissions - Tous les groupes peuvent cr├®er des retraits
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE', 'CAISSE', 'CONTROLES', 'GESTIONNAIRE'], 'view')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:liste')
    
    # Note: Cette vue permet la cr├®ation de retraits manuels sans conditions temporelles
    # Les conditions temporelles ne s'appliquent qu'aux retraits automatiques
    
    if request.method == 'POST':
        form = RetraitBailleurForm(request.POST)
        if form.is_valid():
            # Rediriger vers le r├®capitulatif au lieu de cr├®er directement
            bailleur_id = form.cleaned_data.get('bailleur').id
            mois_retrait = form.cleaned_data.get('mois_retrait')
            
            if mois_retrait:
                # S'assurer que c'est le premier jour du mois
                if mois_retrait.day != 1:
                    mois_retrait = mois_retrait.replace(day=1)
                
                # Rediriger vers le r├®capitulatif
                return redirect(f'{reverse("paiements:recap_retrait_bailleur", args=[bailleur_id])}?mois={mois_retrait.month}&annee={mois_retrait.year}')
            else:
                messages.error(request, 'Veuillez s├®lectionner un mois de retrait.')
        else:
            messages.error(request, 'Veuillez corriger les erreurs dans le formulaire.')
    else:
        form = RetraitBailleurForm()
    
    # R├®cup├®rer la liste des bailleurs pour le contexte
    bailleurs = Bailleur.objects.filter(actif=True).order_by('nom', 'prenom')
    
    context = get_context_with_entreprise_config({
        'form': form,
        'bailleurs': bailleurs,
        'title': 'Ajouter un Retrait'
    })
    
    return render(request, 'paiements/retrait_ajouter.html', context)

@login_required
def creer_retrait_depuis_recap(request):
    """Cr├®e le retrait depuis le r├®capitulatif avec d├®duction automatique des charges."""
    # V├®rification des permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE', 'CAISSE'], 'view')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:liste')
    
    if request.method == 'POST':
        # R├®cup├®rer les donn├®es du formulaire
        bailleur_id = request.POST.get('bailleur')
        mois_retrait = request.POST.get('mois_retrait')
        montant_loyers_bruts = request.POST.get('montant_loyers_bruts')
        montant_charges_deductibles = request.POST.get('montant_charges_deductibles')
        montant_net_a_payer = request.POST.get('montant_net_a_payer')
        
        try:
            from .services_retrait import ServiceGestionRetrait
            from datetime import datetime
            
            # R├®cup├®rer le bailleur
            bailleur = Bailleur.objects.get(id=bailleur_id)
            
            # Convertir la date du mois
            mois_date = datetime.strptime(mois_retrait, '%Y-%m-%d').date()
            
            # Cr├®er le retrait avec restrictions et calcul optimis├®
            resultat = ServiceGestionRetrait.creer_retrait_avec_restrictions(
                bailleur, mois_date, request.user
            )
            
            if resultat['success']:
                messages.success(request, resultat['message'])
                if resultat.get('charges_appliquees', 0) > 0:
                    messages.info(request, f"{resultat['charges_appliquees']} charge(s) appliqu├®e(s) automatiquement")
            else:
                messages.error(request, resultat['message'])
            
            return redirect('paiements:retraits_liste')
            
        except Exception as e:
            messages.error(request, f'Erreur lors de la cr├®ation du retrait: {str(e)}')
            return redirect('paiements:retraits_liste')
    
    return redirect('paiements:retraits_liste')

@login_required
def recap_retrait_bailleur(request, bailleur_id):
    """Affiche le r├®capitulatif avant cr├®ation du retrait avec les charges ├á d├®duire."""
    # V├®rification des permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE', 'CAISSE'], 'view')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:liste')
    
    # R├®cup├®rer le bailleur
    bailleur = get_object_or_404(Bailleur, pk=bailleur_id)
    
    # R├®cup├®rer le mois depuis les param├¿tres GET
    mois = request.GET.get('mois')
    annee = request.GET.get('annee')
    
    if not mois or not annee:
        # Par d├®faut, mois actuel
        from django.utils import timezone
        mois_actuel = timezone.now()
        mois = mois_actuel.month
        annee = mois_actuel.year
    
    try:
        mois = int(mois)
        annee = int(annee)
    except (ValueError, TypeError):
        messages.error(request, 'Mois ou ann├®e invalide.')
        return redirect('paiements:retraits_liste')
    
    # Cr├®er un retrait temporaire pour les calculs
    from datetime import date
    mois_retrait = date(annee, mois, 1)
    
    # Utiliser le service intelligent pour calculer le retrait
    from .services_retraits_bailleur import ServiceRetraitsBailleurIntelligent
    calcul_retrait = ServiceRetraitsBailleurIntelligent.calculer_retrait_mensuel_bailleur(
        bailleur, mois, annee
    )
    
    # Calculer les charges qui seront d├®duites
    retrait_temp = RetraitBailleur(
        bailleur=bailleur,
        mois_retrait=mois_retrait,
        montant_loyers_bruts=calcul_retrait['total_loyers'],
        montant_charges_deductibles=calcul_retrait['total_charges_deductibles'],
        montant_net_a_payer=calcul_retrait['montant_net']
    )
    
    charges_calcul = retrait_temp.calculer_charges_automatiquement()
    
    # R├®cup├®rer les propri├®t├®s du bailleur avec leurs unit├®s locatives
    proprietes = Propriete.objects.filter(
        bailleur=bailleur,
        is_deleted=False
    ).select_related('type_bien').prefetch_related('unites_locatives__contrats__locataire')
    
    # Utiliser la m├®thode du mod├¿le pour calculer les loyers
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
        'title': f'R├®capitulatif Retrait - {bailleur.nom} {bailleur.prenom}'
    })
    
    return render(request, 'paiements/recap_retrait_bailleur.html', context)

@login_required
def detail_retrait(request, pk):
    """Afficher le d├®tail d'un retrait bailleur S├ëCURIS├ë."""
    # V├®rification des permissions avec fallback pour PRIVILEGE
    permissions = check_group_permissions_with_fallback(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE', 'CAISSE'], 'view')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:dashboard')
    
    # R├®cup├®rer le retrait avec toutes les relations n├®cessaires
    retrait = get_object_or_404(
        RetraitBailleur.objects.select_related(
            'bailleur',
            'cree_par',
            'valide_par'
        ),
        pk=pk,
        is_deleted=False
    )
    
    # V├®rifier si l'utilisateur peut voir les montants (PRIVILEGE uniquement)
    can_see_amounts = check_group_permissions(request.user, ['PRIVILEGE'], 'view')['allowed']
    
    # G├®rer l'affichage des montants confidentiels via session
    show_confidential = request.session.get('show_confidential_amounts', False)
    if request.GET.get('toggle_confidential') == '1':
        show_confidential = not show_confidential
        request.session['show_confidential_amounts'] = show_confidential
    
    # L'utilisateur peut voir les montants s'il a les permissions OU s'il a activ├® l'affichage confidentiel
    display_amounts = can_see_amounts or show_confidential
    
    # R├®cup├®rer les propri├®t├®s lou├®es avec leurs d├®tails pour le mois du retrait
    proprietes_louees = []
    total_loyers_bruts = Decimal('0')
    total_charges_deductibles = Decimal('0')
    total_charges_bailleur = Decimal('0')
    
    from proprietes.models import Propriete
    from contrats.models import Contrat
    from proprietes.models import ChargesBailleur
    from paiements.models import ChargeDeductible
    from decimal import Decimal
    
    # R├®cup├®rer toutes les propri├®t├®s du bailleur avec des contrats actifs et unit├®s locatives
    proprietes = Propriete.objects.filter(
        bailleur=retrait.bailleur,
        is_deleted=False
    ).prefetch_related(
        'contrats__locataire',
        'unites_locatives__contrats__locataire'
    )
    
    for propriete in proprietes:
        # R├®cup├®rer les unit├®s locatives de cette propri├®t├®
        unites_locatives = propriete.unites_locatives.filter(is_deleted=False)
        
        # Calculer les montants pour le mois du retrait
        mois_retrait = retrait.mois_retrait
        
        # Initialiser les valeurs par d├®faut
        loyer_mensuel = Decimal('0')
        charges_mensuelles = Decimal('0')
        loyer_brut = Decimal('0')
        charges_deductibles = Decimal('0')
        charges_bailleur = Decimal('0')
        montant_net = Decimal('0')
        
        # Calculer les totaux des unit├®s locatives
        total_loyer_unites = Decimal('0')
        total_charges_unites = Decimal('0')
        total_brut_unites = Decimal('0')
        total_charges_deductibles_unites = Decimal('0')
        total_charges_bailleur_unites = Decimal('0')
        
        # Si la propri├®t├® a des unit├®s locatives, calculer ├á partir des unit├®s
        if unites_locatives.exists():
            for unite in unites_locatives:
                # R├®cup├®rer les contrats actifs de cette unit├®
                contrats_unite = unite.contrats.filter(
                    est_actif=True,
                    est_resilie=False
                )
                
                # Si l'unit├® a des contrats actifs, utiliser les montants des contrats
                if contrats_unite.exists():
                    for contrat in contrats_unite:
                        # Utiliser les montants du contrat, pas de l'unit├®
                        contrat_loyer = Decimal(str(contrat.loyer_mensuel or '0'))
                        contrat_charges = Decimal(str(contrat.charges_mensuelles or '0'))
                        contrat_brut = contrat_loyer + contrat_charges
                        
                        total_loyer_unites += contrat_loyer
                        total_charges_unites += contrat_charges
                        total_brut_unites += contrat_brut
                        
                        # Calculer les charges d├®ductibles pour ce contrat
                        charges_deductibles_contrat = ChargeDeductible.objects.filter(
                            contrat=contrat,
                            date_charge__year=mois_retrait.year,
                            date_charge__month=mois_retrait.month,
                            statut='validee'
                        ).aggregate(total=Sum('montant'))['total'] or Decimal('0')
                        total_charges_deductibles_unites += charges_deductibles_contrat
                else:
                    # Si pas de contrat actif, utiliser les montants de l'unit├® (pour les unit├®s libres)
                    unite_loyer = Decimal(str(unite.loyer_mensuel or '0'))
                    unite_charges = Decimal(str(unite.charges_mensuelles or '0'))
                    unite_brut = unite_loyer + unite_charges
                    
                    total_loyer_unites += unite_loyer
                    total_charges_unites += unite_charges
                    total_brut_unites += unite_brut
                
                # Calculer les charges bailleur pour cette unit├® (une seule fois par unit├®)
                charges_bailleur_unite = ChargesBailleur.objects.filter(
                    propriete=propriete,
                    date_charge__year=mois_retrait.year,
                    date_charge__month=mois_retrait.month,
                    statut__in=['en_attente', 'deduite_retrait']
                ).aggregate(total=Sum('montant_restant'))['total'] or Decimal('0')
                total_charges_bailleur_unites += charges_bailleur_unite
            
            # Utiliser les totaux des unit├®s pour la propri├®t├®
            loyer_mensuel = total_loyer_unites
            charges_mensuelles = total_charges_unites
            loyer_brut = total_brut_unites
            charges_deductibles = total_charges_deductibles_unites
            charges_bailleur = total_charges_bailleur_unites
            montant_net = loyer_brut - charges_deductibles - charges_bailleur
            
        else:
            # Si pas d'unit├®s, chercher un contrat direct sur la propri├®t├®
            contrat_actif = propriete.contrats.filter(
                est_actif=True,
                est_resilie=False
            ).first()
            
            if contrat_actif:
                # Loyers bruts (loyer + charges mensuelles)
                loyer_mensuel = Decimal(str(contrat_actif.loyer_mensuel or '0'))
                charges_mensuelles = Decimal(str(contrat_actif.charges_mensuelles or '0'))
                loyer_brut = loyer_mensuel + charges_mensuelles
                
                # Charges d├®ductibles pour le mois
                charges_deductibles = ChargeDeductible.objects.filter(
                    contrat=contrat_actif,
                    date_charge__year=mois_retrait.year,
                    date_charge__month=mois_retrait.month,
                    statut='validee'
                ).aggregate(total=Sum('montant'))['total'] or Decimal('0')
                
                # Montant net pour cette propri├®t├®
                montant_net = loyer_brut - charges_deductibles - charges_bailleur
            
            # Charges bailleur pour le mois (m├¬me sans contrat actif)
            charges_bailleur = ChargesBailleur.objects.filter(
                propriete=propriete,
                date_charge__year=mois_retrait.year,
                date_charge__month=mois_retrait.month,
                statut__in=['en_attente', 'deduite_retrait']
            ).aggregate(total=Sum('montant_restant'))['total'] or Decimal('0')
        
        # Cr├®er le d├®tail de la propri├®t├®
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
            'statut_contrat': 'Avec unit├®s' if unites_locatives.exists() else ('Actif' if contrat_actif else 'Aucun contrat actif'),
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
    
    # R├®cup├®rer les charges disponibles pour ce retrait
    from paiements.services_charges_bailleur import ServiceChargesBailleurIntelligent
    charges_data = ServiceChargesBailleurIntelligent.calculer_charges_bailleur_pour_mois(
        retrait.bailleur, retrait.mois_retrait
    )
    
    # V├®rifier si le retrait peut ├¬tre modifi├®
    peut_etre_modifie = retrait.statut in ['en_attente']
    
    context = get_context_with_entreprise_config({
        'retrait': retrait,
        'can_see_amounts': can_see_amounts,  # Flag pour le template (permissions)
        'display_amounts': display_amounts,  # Flag pour l'affichage r├®el
        'show_confidential': show_confidential,  # Flag pour l'├®tat de l'affichage confidentiel
        'proprietes_louees': proprietes_louees,
        'total_loyers_bruts': total_loyers_bruts,
        'total_charges_deductibles': total_charges_deductibles,
        'total_charges_bailleur': total_charges_bailleur,
        'montant_net_total': montant_net_total,
        'charges_disponibles': charges_data.get('charges_details', []),
        'total_charges_disponibles': charges_data.get('total_charges', Decimal('0')),
        'peut_etre_modifie': peut_etre_modifie,
        'title': f'D├®tails du Retrait #{retrait.id}'
    })
    
    return render(request, 'paiements/retraits/retrait_detail.html', context)

@login_required
def modifier_retrait(request, pk):
    """Modifier un retrait bailleur."""
    # V├®rification des permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE', 'CAISSE'], 'change')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:dashboard')
    
    # R├®cup├®rer le retrait
    retrait = get_object_or_404(
        RetraitBailleur.objects.select_related('bailleur'),
        pk=pk,
        is_deleted=False
    )
    
    # V├®rifier si le retrait peut ├¬tre modifi├®
    if not retrait.peut_etre_modifie:
        messages.error(request, 'Ce retrait ne peut plus ├¬tre modifi├®.')
        return redirect('paiements:retrait_detail', pk=pk)
    
    if request.method == 'POST':
        form = RetraitBailleurForm(request.POST, instance=retrait)
        if form.is_valid():
            retrait_modifie = form.save(commit=False)
            retrait_modifie.save()
            
            # Mettre ├á jour les relations many-to-many
            form.save_m2m()
            
            messages.success(request, 'Retrait modifi├® avec succ├¿s.')
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
    """Liste des retraits (alias pour compatibilit├®)."""
    return liste_retraits(request)

@login_required
def retrait_ajouter(request):
    """Ajouter un retrait (alias pour compatibilit├®)."""
    return ajouter_retrait(request)

@login_required
def retrait_detail(request, pk):
    """D├®tail d'un retrait (alias pour compatibilit├®)."""
    return detail_retrait(request, pk)

@login_required
def retrait_modifier(request, pk):
    """Modifier un retrait (alias pour compatibilit├®)."""
    return modifier_retrait(request, pk)


# Fonctions manquantes pour compatibilit├® avec les templates existants
@login_required
def liste_recus(request):
    """Liste des re├ºus (placeholder)."""
    messages.warning(request, 'Fonctionnalit├® des re├ºus en cours de d├®veloppement.')
    return redirect('paiements:liste')

@login_required
def liste_recaps_mensuels(request):
    """Liste des r├®capitulatifs mensuels."""
    # V├®rification des permissions avec fallback pour PRIVILEGE
    permissions = check_group_permissions_with_fallback(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE', 'CAISSE'], 'view')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:dashboard')
    
    # V├®rifier si l'utilisateur est PRIVILEGE
    is_privilege_user = hasattr(request.user, 'groupe_travail') and request.user.groupe_travail and request.user.groupe_travail.nom == 'PRIVILEGE'
    
    # R├®cup├®rer les r├®capitulatifs avec filtres (non supprim├®s uniquement)
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
    
    # R├®cup├®rer tous les bailleurs pour le filtre
    from proprietes.models import Bailleur
    bailleurs = Bailleur.objects.all().order_by('nom', 'prenom')
    
    context = get_context_with_entreprise_config({
        'recaps': page_obj,
        'bailleurs': bailleurs,
        'title': 'R├®capitulatifs Mensuels',
        'is_paginated': page_obj.has_other_pages(),
        'page_obj': page_obj,
        'is_privilege_user': is_privilege_user,
    })
    
    return render(request, 'paiements/liste_recaps_mensuels.html', context)


@login_required
def creer_recap_mensuel(request):
    """Cr├®er un nouveau r├®capitulatif mensuel."""
    # V├®rification des permissions avec fallback pour PRIVILEGE
    permissions = check_group_permissions(request.user, [], 'add')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:liste_recaps_mensuels_auto')
    
    if request.method == 'POST':
        # Logique de cr├®ation du r├®capitulatif
        bailleur_id = request.POST.get('bailleur')
        mois_str = request.POST.get('mois')
        
        if bailleur_id and mois_str:
            try:
                from proprietes.models import Bailleur
                from datetime import datetime
                
                bailleur = Bailleur.objects.get(id=bailleur_id, is_deleted=False)
                mois_recap = datetime.strptime(mois_str, '%Y-%m').date()
                
                # V├®rifier si un r├®capitulatif existe d├®j├á pour ce bailleur et ce mois (non supprim├®)
                recap_existant = RecapMensuel.objects.filter(
                    bailleur=bailleur,
                    mois_recap__year=mois_recap.year,
                    mois_recap__month=mois_recap.month,
                    is_deleted=False
                ).first()
                
                if recap_existant:
                    messages.warning(request, f'Un r├®capitulatif existe d├®j├á pour {bailleur.get_nom_complet()} - {mois_recap.strftime("%B %Y")}')
                    return redirect('paiements:detail_recap_mensuel_auto', recap_id=recap_existant.id)
                
                # V├®rifier s'il existe un r├®capitulatif supprim├® logiquement pour ce bailleur et ce mois
                recap_supprime = RecapMensuel.objects.filter(
                    bailleur=bailleur,
                    mois_recap__year=mois_recap.year,
                    mois_recap__month=mois_recap.month,
                    is_deleted=True
                ).first()
                
                # Si un r├®cap supprim├® existe, le supprimer physiquement avant de cr├®er le nouveau
                if recap_supprime:
                    recap_supprime.paiements_concernes.clear()
                    recap_supprime.charges_deductibles.clear()
                    recap_supprime.delete()
                
                # Cr├®er le r├®capitulatif
                recap = RecapMensuel.objects.create(
                    bailleur=bailleur,
                    mois_recap=mois_recap,
                    cree_par=request.user
                )
                
                # Calculer les totaux
                recap.calculer_totaux_bailleur()
                
                messages.success(request, f'R├®capitulatif cr├®├® avec succ├¿s pour {bailleur.get_nom_complet()} - {mois_recap.strftime("%B %Y")}')
                return redirect('paiements:detail_recap_mensuel_auto', recap_id=recap.id)
                
            except (Bailleur.DoesNotExist, ValueError) as e:
                messages.error(request, f'Erreur lors de la cr├®ation: {str(e)}')
        else:
            messages.error(request, 'Veuillez s├®lectionner un bailleur et un mois.')
    
    # R├®cup├®rer tous les bailleurs pour le formulaire
    from proprietes.models import Bailleur
    bailleurs = Bailleur.objects.filter(is_deleted=False).order_by('nom', 'prenom')
    
    context = get_context_with_entreprise_config({
        'bailleurs': bailleurs,
        'title': 'Cr├®er un R├®capitulatif Mensuel'
    })
    
    return render(request, 'paiements/creer_recap_mensuel.html', context)


@login_required
def detail_recap_mensuel(request, recap_id):
    """Afficher le d├®tail complet d'un r├®capitulatif mensuel."""
    # V├®rification des permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE', 'CAISSE'], 'view')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:liste_recaps_mensuels')
    
    # V├®rifier si l'utilisateur est PRIVILEGE
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
        messages.error(request, 'R├®capitulatif introuvable.')
        return redirect('paiements:liste_recaps_mensuels')
    
    # V├®rifier que le r├®capitulatif a un bailleur
    if not recap.bailleur:
        messages.warning(request, 'Ce r├®capitulatif n\'a pas de bailleur associ├®. Certaines fonctionnalit├®s peuvent ├¬tre limit├®es.')
    
    # Recalculer automatiquement les totaux pour s'assurer qu'ils sont ├á jour
    # (la m├®thode g├¿re d├®j├á le cas o├╣ bailleur est None)
    recap.calculer_totaux_bailleur()
    
    # Calculer les statistiques d├®taill├®es
    stats = {
        'total_proprietes': recap.nombre_proprietes,
        'total_contrats': recap.nombre_contrats_actifs,
        'total_paiements': recap.nombre_paiements_recus,
        'total_charges': recap.total_charges_deductibles,
        'total_net': recap.total_net_a_payer,
    }
    
    # Grouper les paiements par propri├®t├® (en tenant compte des unit├®s locatives)
    # Utiliser une cl├® compos├®e (propriete, unite_locative) pour diff├®rencier les unit├®s
    paiements_par_propriete = {}
    for paiement in recap.paiements_concernes.all():
        contrat = paiement.contrat
        propriete = contrat.propriete
        unite_locative = contrat.unite_locative
        
        # Cr├®er une cl├® unique pour la propri├®t├® + unit├® locative
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
    
    # Ajouter les charges d├®ductibles par propri├®t├®
    for charge in recap.charges_deductibles.all():
        contrat = charge.contrat
        propriete = contrat.propriete
        unite_locative = contrat.unite_locative
        
        # Utiliser la m├¬me cl├® que pour les paiements
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
    
    # Convertir le dictionnaire avec cl├®s compos├®es en liste tri├®e pour le template
    # Trier par propri├®t├® puis par unit├® locative
    paiements_par_propriete_liste = sorted(
        paiements_par_propriete.values(),
        key=lambda x: (x['propriete'].adresse_complete, x['unite_locative'].numero_unite if x['unite_locative'] else '')
    )
    
    # Calculer les totaux globaux
    from decimal import Decimal
    total_global_loyers = sum(prop['total_loyers'] for prop in paiements_par_propriete.values()) or Decimal('0')
    total_global_charges = sum(prop['total_charges'] for prop in paiements_par_propriete.values()) or Decimal('0')
    total_global_net = sum(prop['montant_net'] for prop in paiements_par_propriete.values()) or Decimal('0')
    
    # Utiliser le montant r├®ellement pay├® du r├®capitulatif (qui inclut d├®j├á la commission)
    # Recalculer si n├®cessaire pour s'assurer qu'il est ├á jour
    recap.calculer_totaux_bailleur()
    # Utiliser getattr pour ├®viter les erreurs si les migrations ne sont pas encore appliqu├®es
    total_global_net_reellement_paye = getattr(recap, 'montant_reellement_paye', None) or Decimal('0')
    
    # Pr├®parer le titre avec gestion du bailleur None
    if recap.bailleur:
        bailleur_nom = recap.bailleur.get_nom_complet()
    else:
        bailleur_nom = "Sans bailleur"
    
    context = get_context_with_entreprise_config({
        'recap': recap,
        'stats': stats,
        'paiements_par_propriete': paiements_par_propriete_liste,  # Utiliser la liste tri├®e
        'total_global_loyers': total_global_loyers,
        'total_global_charges': total_global_charges,
        'total_global_net': total_global_net,
        'total_global_net_reellement_paye': total_global_net_reellement_paye,
        'title': f'R├®capitulatif {bailleur_nom} - {recap.mois_recap.strftime("%B %Y")}',
        'is_privilege_user': is_privilege_user,
    })
    
    return render(request, 'paiements/detail_recap_mensuel.html', context)


@login_required
def valider_recap_mensuel(request, recap_id):
    """Valider un r├®capitulatif mensuel."""
    # V├®rification des permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE', 'CAISSE'], 'change')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:detail_recap_mensuel_auto', recap_id=recap_id)
    
    try:
        recap = RecapMensuel.objects.get(id=recap_id)
    except RecapMensuel.DoesNotExist:
        messages.error(request, 'R├®capitulatif introuvable.')
        return redirect('paiements:liste_recaps_mensuels')
    
    if recap.statut != 'brouillon':
        messages.warning(request, 'Ce r├®capitulatif ne peut plus ├¬tre valid├®.')
        return redirect('paiements:detail_recap_mensuel_auto', recap_id=recap_id)
    
    # Valider le r├®capitulatif
    recap.valider_recap(request.user)
    messages.success(request, 'R├®capitulatif valid├® avec succ├¿s.')
    
    return redirect('paiements:detail_recap_mensuel_auto', recap_id=recap_id)


@login_required
def marquer_recap_envoye(request, recap_id):
    """Marquer un r├®capitulatif mensuel comme envoy├® au bailleur."""
    # V├®rification des permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE', 'CAISSE'], 'change')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:detail_recap_mensuel_auto', recap_id=recap_id)
    
    try:
        recap = RecapMensuel.objects.get(id=recap_id)
    except RecapMensuel.DoesNotExist:
        messages.error(request, 'R├®capitulatif introuvable.')
        return redirect('paiements:liste_recaps_mensuels')
    
    if recap.statut not in ['valide', 'envoye']:
        messages.warning(request, 'Ce r├®capitulatif doit ├¬tre valid├® avant d\'├¬tre marqu├® comme envoy├®.')
        return redirect('paiements:detail_recap_mensuel_auto', recap_id=recap_id)
    
    # Marquer comme envoy├®
    recap.marquer_envoye(request.user)
    messages.success(request, 'R├®capitulatif marqu├® comme envoy├® au bailleur.')
    
    return redirect('paiements:detail_recap_mensuel_auto', recap_id=recap_id)


@login_required
def marquer_recap_paye(request, recap_id):
    """Marquer un r├®capitulatif mensuel comme pay├® au bailleur."""
    # V├®rification des permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE', 'CAISSE'], 'change')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:detail_recap_mensuel_auto', recap_id=recap_id)
    
    try:
        recap = RecapMensuel.objects.get(id=recap_id)
    except RecapMensuel.DoesNotExist:
        messages.error(request, 'R├®capitulatif introuvable.')
        return redirect('paiements:liste_recaps_mensuels')
    
    if recap.statut not in ['envoye', 'paye']:
        messages.warning(request, 'Ce r├®capitulatif doit ├¬tre envoy├® avant d\'├¬tre marqu├® comme pay├®.')
        return redirect('paiements:detail_recap_mensuel_auto', recap_id=recap_id)
    
    # Marquer comme pay├®
    recap.marquer_paye(request.user)
    messages.success(request, 'R├®capitulatif marqu├® comme pay├® au bailleur.')
    
    return redirect('paiements:detail_recap_mensuel_auto', recap_id=recap_id)


@login_required
def imprimer_recap_mensuel(request, recap_id):
    """Imprimer un r├®capitulatif mensuel en PDF."""
    # V├®rification des permissions
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
        messages.error(request, 'R├®capitulatif introuvable.')
        return redirect('paiements:liste_recaps_mensuels')
    
    try:
        # G├®n├®rer le PDF avec ReportLab
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.lib import colors
        from io import BytesIO
        
        # Cr├®er le buffer pour le PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
        
        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=20,
            spaceAfter=30,
            alignment=1,  # Centr├®
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
        
        # R├®cup├®rer la configuration de l'entreprise
        from core.models import ConfigurationEntreprise
        from core.utils import ajouter_en_tete_entreprise_reportlab, ajouter_pied_entreprise_reportlab
        config = ConfigurationEntreprise.get_configuration_active()
        
        # En-t├¬te de l'entreprise
        ajouter_en_tete_entreprise_reportlab(story, config)
        
        # Titre principal
        story.append(Paragraph("R├ëCAPITULATIF MENSUEL", title_style))
        story.append(Spacer(1, 20))
        
        # Informations du bailleur
        bailleur_nom = recap.bailleur.get_nom_complet() if recap.bailleur else "Sans bailleur"
        story.append(Paragraph(f"<b>Bailleur:</b> {bailleur_nom}", subtitle_style))
        story.append(Paragraph(f"<b>Mois:</b> {recap.mois_recap.strftime('%B %Y')}", normal_style))
        story.append(Spacer(1, 15))
        
        # R├®sum├® financier
        story.append(Paragraph("R├ëSUM├ë FINANCIER", subtitle_style))
        story.append(Spacer(1, 10))
        
        # Tableau des montants
        montants_data = [
            ['Description', 'Montant (F CFA)'],
            ['Loyer brut total', f"{recap.total_loyers_bruts:,.0f}"],
            ['Charges d├®ductibles', f"{recap.total_charges_deductibles:,.0f}"],
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
        
        # D├®tails des propri├®t├®s enrichis
        story.append(Paragraph("D├ëTAILS DES PROPRI├ëT├ëS LOU├ëES", subtitle_style))
        story.append(Spacer(1, 10))
        
        # R├®cup├®rer les propri├®t├®s actives avec plus de d├®tails
        proprietes_actives = recap.bailleur.proprietes.filter(
            contrats__est_actif=True,
            contrats__est_resilie=False
        ).distinct()
        
        proprietes_data = [['Propri├®t├®', 'Adresse', 'Locataire', 'Contact', 'Loyer', 'Charges', 'Net']]
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
            ['Nombre de propri├®t├®s', str(total_proprietes)],
            ['Contrats actifs', str(total_contrats)],
            ['Taux d\'occupation', f"{taux_occupation:.1f}%"],
            ['Paiements re├ºus', str(recap.nombre_paiements_recus)],
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
        
        # V├®rification des garanties financi├¿res
        story.append(Paragraph("V├ëRIFICATION DES GARANTIES FINANCI├êRES", subtitle_style))
        story.append(Spacer(1, 10))
        
        garanties_data = [['Propri├®t├®', 'Caution Requise', 'Caution Vers├®e', 'Avance Requise', 'Avance Vers├®e', 'Statut']]
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
                
                # R├®cup├®rer les paiements de caution et d'avance
                paiements_caution = contrat_actif.paiements.filter(
                    type_paiement='caution',
                    statut='valide'
                ).aggregate(total=Sum('montant'))['total'] or 0
                
                paiements_avance = contrat_actif.paiements.filter(
                    type_paiement='avance',
                    statut='valide'
                ).aggregate(total=Sum('montant'))['total'] or 0
                
                statut = "Compl├¿tes" if (paiements_caution >= caution_requise and paiements_avance >= avance_requise) else "Incompl├¿tes"
                
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
        
        # Charges d├®ductibles
        if recap.charges_deductibles.exists():
            story.append(Paragraph("CHARGES D├ëDUCTIBLES", subtitle_style))
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
            story.append(Paragraph(f"<b>Date de cr├®ation:</b> {recap.created_at.strftime('%d/%m/%Y')}", normal_style))
        if recap.date_validation:
            story.append(Paragraph(f"<b>Date de validation:</b> {recap.date_validation.strftime('%d/%m/%Y')}", normal_style))
        if recap.date_envoi:
            story.append(Paragraph(f"<b>Date d'envoi:</b> {recap.date_envoi.strftime('%d/%m/%Y')}", normal_style))
        if recap.date_paiement:
            story.append(Paragraph(f"<b>Date de paiement:</b> {recap.date_paiement.strftime('%d/%m/%Y')}", normal_style))
        
        # Pied de page avec informations de l'entreprise
        ajouter_pied_entreprise_reportlab(story, config)
        
        # G├®n├®rer le PDF
        doc.build(story)
        buffer.seek(0)
        
        # Cr├®er la r├®ponse HTTP
        from django.http import HttpResponse
        response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        bailleur_nom = recap.bailleur.get_nom_complet() if recap.bailleur else "sans_bailleur"
        response['Content-Disposition'] = f'attachment; filename="recap_mensuel_{bailleur_nom.replace(" ", "_")}_{recap.mois_recap.strftime("%Y_%m")}.pdf"'
        
        # Marquer comme imprim├® si ce n'est pas d├®j├á fait
        if recap.statut == 'envoye' and not recap.date_impression:
            recap.date_impression = timezone.now()
            recap.save()
        
        return response
        
    except ImportError:
        messages.error(request, 'La g├®n├®ration PDF n├®cessite ReportLab. Veuillez l\'installer.')
        return redirect('paiements:detail_recap_mensuel_auto', recap_id=recap_id)
    except Exception as e:
        messages.error(request, f'Erreur lors de la g├®n├®ration du PDF: {str(e)}')
        return redirect('paiements:detail_recap_mensuel_auto', recap_id=recap_id)

@login_required
def liste_retraits_bailleur(request):
    """Liste des retraits bailleur S├ëCURIS├ëE."""
    # V├®rification des permissions avec fallback pour PRIVILEGE
    permissions = check_group_permissions_with_fallback(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE', 'CAISSE'], 'view')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:dashboard')
    
    # R├®cup├®rer tous les retraits avec relations (non supprim├®s)
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
    
    # V├®rifier si l'utilisateur peut voir les montants (PRIVILEGE uniquement)
    can_see_amounts = check_group_permissions(request.user, ['PRIVILEGE'], 'view')['allowed']
    
    # Statistiques dynamiques et exactes
    from proprietes.models import Propriete
    
    # Compter seulement les retraits pour des bailleurs qui ont des propri├®t├®s lou├®es
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
    
    # R├®cup├®rer tous les bailleurs pour le filtre
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
    """Cr├®er un paiement de caution ou d'avance (placeholder)."""
    messages.warning(request, 'Fonctionnalit├® des paiements de caution et avance en cours de d├®veloppement.')
    return redirect('paiements:ajouter')

@login_required
def paiement_caution_avance_list(request):
    """Liste des paiements de caution et avance (placeholder)."""
    messages.warning(request, 'Fonctionnalit├® des paiements de caution et avance en cours de d├®veloppement.')
    return redirect('paiements:liste')

@login_required
def tableau_bord_list(request):
    """Liste des tableaux de bord financiers."""
    # V├®rification des permissions avec fallback pour PRIVILEGE
    permissions = check_group_permissions_with_fallback(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE', 'CAISSE'], 'view')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:dashboard')
    
    # R├®cup├®rer les tableaux de bord de l'utilisateur
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
    """Afficher le d├®tail d'une quittance de paiement avec le nouveau syst├¿me A5 unifi├®."""
    # V├®rification des permissions
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
        # Utiliser le nouveau syst├¿me A5 unifi├®
        from .services_document_unifie_complet import DocumentUnifieA5ServiceComplet
        
        service = DocumentUnifieA5ServiceComplet()
        # Utiliser le paiement principal ou le premier paiement de la liste
        paiement_id = quittance.paiement_principal.id if quittance.paiement_principal else quittance.paiements.first().id
        html_content = service.generer_document_unifie('paiement_quittance', paiement_id=paiement_id)
        
        return HttpResponse(html_content, content_type='text/html')
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        messages.error(request, f'Erreur lors de la g├®n├®ration: {str(e)}')
        return redirect('paiements:quittance_list')


@login_required
def corriger_annees_mois_paye(request):
    """Vue secr├¿te pour corriger les ann├®es incorrectes dans mois_paye des paiements existants."""
    from core.utils import check_group_permissions
    from django.db import transaction
    from datetime import datetime
    from dateutil.relativedelta import relativedelta
    import re
    
    # V├®rification des permissions : Seuls PRIVILEGE peuvent ex├®cuter cette action
    permissions = check_group_permissions(request.user, ['PRIVILEGE'], 'view')
    if not permissions['allowed']:
        messages.error(request, 'Acc├¿s refus├®.')
        return redirect('paiements:liste')
    
    try:
        # Mapping des mois fran├ºais
        mois_francais = {
            'janvier': 1, 'f├®vrier': 2, 'mars': 3, 'avril': 4,
            'mai': 5, 'juin': 6, 'juillet': 7, 'ao├╗t': 8,
            'septembre': 9, 'octobre': 10, 'novembre': 11, 'd├®cembre': 12
        }
        
        # R├®cup├®rer tous les paiements avec mois_paye
        paiements = Paiement.objects.filter(
            Q(mois_paye__isnull=False) & ~Q(mois_paye='')
        ).select_related('contrat').order_by('date_paiement')
        
        mois_actuel = datetime.now().month
        annee_actuelle = datetime.now().year
        
        corrections = []
        
        for paiement in paiements:
            if not paiement.mois_paye:
                continue
                
            # Extraire le mois et l'ann├®e de mois_paye
            mois_paye_str = paiement.mois_paye.strip()
            
            # Trouver le mois dans la cha├«ne
            mois_num = None
            mois_nom = None
            for nom_mois, num in mois_francais.items():
                if nom_mois.lower() in mois_paye_str.lower():
                    mois_num = num
                    mois_nom = nom_mois
                    break
            
            if not mois_num:
                continue
            
            # Extraire l'ann├®e
            annee_match = re.search(r'(\d{4})', mois_paye_str)
            if not annee_match:
                continue
            
            annee_actuelle_paye = int(annee_match.group(1))
            
            # V├®rifier si l'ann├®e est incorrecte
            correction_necessaire = False
            nouvelle_annee = annee_actuelle_paye
            
            # Cas 1: On est en d├®cembre et le mois pay├® est janvier de la m├¬me ann├®e
            # (devrait ├¬tre l'ann├®e suivante)
            if mois_actuel == 12 and mois_num == 1 and annee_actuelle_paye == annee_actuelle:
                nouvelle_annee = annee_actuelle + 1
                correction_necessaire = True
            
            # Cas 2: On est en novembre/d├®cembre 2025 et le mois pay├® est janvier 2025
            # mais la date de paiement est en 2025 (devrait ├¬tre janvier 2026)
            elif mois_actuel >= 11 and mois_num == 1:
                # V├®rifier si c'est un paiement r├®cent (cr├®├® en novembre/d├®cembre 2025)
                if paiement.date_paiement.year == annee_actuelle and paiement.date_paiement.month >= 11:
                    if annee_actuelle_paye == annee_actuelle:
                        nouvelle_annee = annee_actuelle + 1
                        correction_necessaire = True
            
            # Cas 3: Le mois pay├® est avant le mois actuel de la m├¬me ann├®e
            # et on est en fin d'ann├®e (novembre/d├®cembre), c'est probablement l'ann├®e suivante
            elif mois_actuel >= 11 and mois_num < mois_actuel and annee_actuelle_paye == annee_actuelle:
                # V├®rifier si le paiement a ├®t├® fait r├®cemment
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
                f'{len(corrections)} paiement(s) corrig├®(s) avec succ├¿s!'
            )
        else:
            messages.info(request, 'Aucune correction n├®cessaire.')
            
    except Exception as e:
        messages.error(request, f'Erreur lors de la correction : {str(e)}')
    
    return redirect('paiements:liste')


@login_required
def quittance_list(request):
    """Liste des r├®c├®piss├®s de paiement."""
    # V├®rification des permissions
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
        'title': 'Liste des r├®c├®piss├®s de paiement'
    })
    
    return render(request, 'paiements/quittance_list.html', context)


@login_required
@require_POST
def marquer_quittance_imprimee(request, pk):
    """Marquer une quittance comme imprim├®e."""
    # V├®rification des permissions
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
        
        return JsonResponse({'success': True, 'message': 'Quittance marqu├®e comme imprim├®e'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@login_required
@require_POST
def marquer_quittance_envoyee(request, pk):
    """Marquer une quittance comme envoy├®e."""
    # V├®rification des permissions
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
        
        messages.success(request, 'Quittance marqu├®e comme envoy├®e')
        return redirect('paiements:quittance_detail', pk=pk)
    except Exception as e:
        messages.error(request, f'Erreur lors de la mise ├á jour: {str(e)}')
        return redirect('paiements:quittance_detail', pk=pk)


@login_required
@require_POST
def marquer_quittance_archivee(request, pk):
    """Marquer une quittance comme archiv├®e."""
    # V├®rification des permissions
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
            new_data={'statut': 'archiv├®e'},
            user=request.user,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        messages.success(request, 'Quittance marqu├®e comme archiv├®e')
        return redirect('paiements:quittance_detail', pk=pk)
    except Exception as e:
        messages.error(request, f'Erreur lors de la mise ├á jour: {str(e)}')
        return redirect('paiements:quittance_detail', pk=pk)


@login_required
def generer_quittance_manuelle(request, paiement_pk):
    """G├®n├®rer manuellement une quittance pour un paiement existant avec le syst├¿me A5 unifi├®."""
    # V├®rification des permissions
    permissions = check_group_permissions(request.user, [], 'add')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:detail', pk=paiement_pk)
    
    try:
        paiement = get_object_or_404(Paiement, pk=paiement_pk)
        
        # Utiliser le nouveau syst├¿me A5 unifi├® directement
        from .services_document_unifie_complet import DocumentUnifieA5ServiceComplet
        
        service = DocumentUnifieA5ServiceComplet()
        html_content = service.generer_document_unifie('paiement_quittance', paiement_id=paiement.id)
        
        return HttpResponse(html_content, content_type='text/html')
        
    except Exception as e:
        messages.error(request, f'Erreur lors de la g├®n├®ration de la quittance: {str(e)}')
        return redirect('paiements:detail', pk=paiement_pk)


# =============================================================================
# VUES POUR LES TABLEAUX DE BORD FINANCIERS
# =============================================================================

@login_required
def tableau_bord_detail(request, pk):
    """Afficher le d├®tail d'un tableau de bord financier."""
    # V├®rification des permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE', 'CAISSE'], 'view')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:tableau_bord_list')
    
    tableau = get_object_or_404(
        TableauBordFinancier.objects.select_related('cree_par').prefetch_related('proprietes', 'bailleurs'),
        pk=pk
    )
    
    # V├®rifier que l'utilisateur peut voir ce tableau de bord
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
    """Cr├®er un nouveau tableau de bord financier."""
    # V├®rification des permissions
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
            
            messages.success(request, f'Tableau de bord "{tableau.nom}" cr├®├® avec succ├¿s.')
            return redirect('paiements:tableau_bord_detail', pk=tableau.pk)
    else:
        form = TableauBordFinancierForm(user=request.user)
    
    context = get_context_with_entreprise_config({
        'form': form,
        'title': 'Cr├®er un Tableau de Bord Financier'
    })
    
    return render(request, 'paiements/tableaux_bord/tableau_form.html', context)


@login_required
def tableau_bord_update(request, pk):
    """Modifier un tableau de bord financier existant."""
    # V├®rification des permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE', 'CAISSE'], 'change')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:tableau_bord_list')
    
    tableau = get_object_or_404(TableauBordFinancier, pk=pk)
    
    # V├®rifier que l'utilisateur peut modifier ce tableau de bord
    if tableau.cree_par != request.user and not request.user.is_superuser:
        messages.error(request, 'Vous n\'avez pas les permissions pour modifier ce tableau de bord.')
        return redirect('paiements:tableau_bord_list')
    
    if request.method == 'POST':
        form = TableauBordFinancierForm(request.POST, instance=tableau, user=request.user)
        if form.is_valid():
            # Sauvegarder les anciennes donn├®es pour l'audit
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
            
            messages.success(request, f'Tableau de bord "{tableau.nom}" modifi├® avec succ├¿s.')
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
    # V├®rification des permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE'], 'delete')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:tableau_bord_list')
    
    tableau = get_object_or_404(TableauBordFinancier, pk=pk)
    
    # V├®rifier que l'utilisateur peut supprimer ce tableau de bord
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
        messages.success(request, f'Tableau de bord "{nom_tableau}" supprim├® avec succ├¿s.')
        
    except Exception as e:
        messages.error(request, f'Erreur lors de la suppression: {str(e)}')
    
    return redirect('paiements:tableau_bord_list')


@login_required
def tableau_bord_export_pdf(request, pk):
    """Exporter un tableau de bord en PDF."""
    # V├®rification des permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE', 'CAISSE'], 'view')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:tableau_bord_list')
    
    tableau = get_object_or_404(TableauBordFinancier, pk=pk)
    
    # V├®rifier que l'utilisateur peut voir ce tableau de bord
    if tableau.cree_par != request.user and not request.user.is_superuser:
        messages.error(request, 'Vous n\'avez pas les permissions pour exporter ce tableau de bord.')
        return redirect('paiements:tableau_bord_list')
    
    try:
        # TODO: Impl├®menter la g├®n├®ration PDF
        # response = generate_tableau_bord_pdf(tableau, stats)
        messages.warning(request, 'Export PDF en cours de d├®veloppement.')
        return redirect('paiements:tableau_bord_detail', pk=pk)
        
    except Exception as e:
        messages.error(request, f'Erreur lors de l\'export PDF: {str(e)}')
        return redirect('paiements:tableau_bord_detail', pk=pk)


@login_required
def tableau_bord_list(request):
    # Vue d├®sactiv├®e : mod├¿le TableauBordFinancier supprim├®
    messages.error(request, "La fonctionnalit├® Tableau de Bord Financier a ├®t├® d├®sactiv├®e (mod├¿le supprim├®).")
    return redirect('paiements:dashboard')

@login_required
def generer_recap_mensuel_automatique(request):
    """G├®n├¿re automatiquement les r├®capitulatifs mensuels pour tous les bailleurs actifs."""
    # V├®rification des permissions avec fallback pour PRIVILEGE
    permissions = check_group_permissions_with_fallback(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE', 'CAISSE'], 'view')
    
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:dashboard')
    
    if request.method == 'POST':
        mois_recap = request.POST.get('mois_recap')
        forcer_regeneration = request.POST.get('forcer_regeneration') == 'on'
        bailleur_id = request.POST.get('bailleur_id')  # Nouveau : s├®lection de bailleur
        
        if not mois_recap:
            messages.error(request, _("Veuillez s├®lectionner un mois."))
            return redirect('paiements:generer_recap_mensuel_automatique')
        
        try:
            from .services_retrait import ServiceGestionRetrait
            
            # Convertir la date
            mois_date = datetime.strptime(mois_recap, '%Y-%m-%d').date()
            
            # V├®rifier les restrictions de p├®riode
            periode_ok, message_periode = ServiceGestionRetrait.verifier_periode_retrait()
            if not periode_ok:
                messages.error(request, message_periode)
                return redirect('paiements:generer_recap_mensuel_automatique')
            
            # R├®cup├®rer les bailleurs selon la s├®lection
            if bailleur_id and bailleur_id != 'tous':
                # G├®n├®ration pour un bailleur sp├®cifique
                bailleurs = Bailleur.objects.filter(id=bailleur_id, is_deleted=False)
                if not bailleurs.exists():
                    messages.error(request, _("Bailleur s├®lectionn├® introuvable."))
                    return redirect('paiements:generer_recap_mensuel_automatique')
            else:
                # G├®n├®ration pour tous les bailleurs
                bailleurs = Bailleur.objects.filter(is_deleted=False)
            
            # V├®rifier s'il existe d├®j├á des r├®capitulatifs pour ce mois et ces bailleurs (non supprim├®s)
            recaps_existants = RecapMensuel.objects.filter(
                mois_recap__year=mois_date.year,
                mois_recap__month=mois_date.month,
                bailleur__in=bailleurs,
                is_deleted=False
            )
            
            if recaps_existants.exists() and not forcer_regeneration:
                messages.warning(request, _("Des r├®capitulatifs existent d├®j├á pour ce mois. Cochez 'Forcer la r├®g├®n├®ration' pour les recr├®er."))
                return redirect('paiements:generer_recap_mensuel_automatique')
            
            # Supprimer physiquement les anciens r├®capitulatifs si r├®g├®n├®ration forc├®e
            if forcer_regeneration and recaps_existants.exists():
                # Supprimer d'abord les relations ManyToMany
                for recap in recaps_existants:
                    recap.paiements_concernes.clear()
                    recap.charges_deductibles.clear()
                # Supprimer physiquement les r├®capitulatifs
                recaps_existants.delete()
                messages.info(request, _("Anciens r├®capitulatifs supprim├®s. G├®n├®ration en cours..."))
            
            if not bailleurs.exists():
                messages.warning(request, _("Aucun bailleur actif trouv├®."))
                return redirect('paiements:generer_recap_mensuel_automatique')
            
            recaps_crees = []
            recaps_avec_garanties = []
            recaps_sans_garanties = []
            
            with transaction.atomic():
                for bailleur in bailleurs:
                    try:
                        # V├®rifier si le bailleur a des propri├®t├®s lou├®es
                        proprietes_louees = bailleur.proprietes.filter(
                            contrats__est_actif=True,
                            contrats__est_resilie=False
                        ).distinct()
                        
                        if not proprietes_louees.exists():
                            continue
                        
                        # V├®rifier s'il existe un r├®capitulatif supprim├® logiquement pour ce bailleur et ce mois
                        recap_supprime = RecapMensuel.objects.filter(
                            bailleur=bailleur,
                            mois_recap__year=mois_date.year,
                            mois_recap__month=mois_date.month,
                            is_deleted=True
                        ).first()
                        
                        # Si un r├®cap supprim├® existe, le supprimer physiquement avant de cr├®er le nouveau
                        if recap_supprime:
                            recap_supprime.paiements_concernes.clear()
                            recap_supprime.charges_deductibles.clear()
                            recap_supprime.delete()
                        
                        # Cr├®er le r├®capitulatif
                        recap = RecapMensuel.objects.create(
                            bailleur=bailleur,
                            mois_recap=mois_date,
                            cree_par=request.user
                        )
                        
                        # Calculer automatiquement tous les totaux et v├®rifier les garanties
                        recap.calculer_totaux_bailleur()
                        
                        # Classer selon les garanties financi├¿res
                        if recap.garanties_suffisantes:
                            recaps_avec_garanties.append(recap)
                            recap.statut = 'valide'  # Pr├¬t pour paiement
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
                        f"{len(recaps_crees)} r├®capitulatifs cr├®├®s avec succ├¿s pour {mois_date.strftime('%B %Y')}.")
                    
                    if recaps_avec_garanties:
                        messages.success(request, 
                            f"{len(recaps_avec_garanties)} r├®capitulatifs sont pr├¬ts pour paiement (garanties suffisantes).")
                    
                    if recaps_sans_garanties:
                        messages.warning(request, 
                            f"{len(recaps_sans_garanties)} r├®capitulatifs sont en attente des garanties financi├¿res (cautions et avances).")
                    
                    return redirect('paiements:liste_recaps_mensuels_auto')
                else:
                    messages.warning(request, _("Aucun r├®capitulatif n'a pu ├¬tre cr├®├®."))
                    
        except ValueError:
            messages.error(request, _("Format de date invalide."))
        except Exception as e:
            messages.error(request, f"Erreur lors de la g├®n├®ration: {str(e)}")
    
    # Pr├®parer les 12 derniers mois pour le s├®lecteur
    mois_disponibles = []
    date_courante = datetime.now()
    
    for i in range(12):
        date_mois = date_courante - timedelta(days=30*i)
        mois_disponibles.append({
            'value': date_mois.strftime('%Y-%m-%d'),
            'label': date_mois.strftime('%B %Y')
        })
    
    # R├®cup├®rer les informations de d├®tection automatique pour chaque bailleur
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
        'bailleurs_actifs': bailleurs_actifs,  # Nouveau : liste des bailleurs pour la s├®lection
        'title': 'G├®n├®ration Automatique des R├®capitulatifs Mensuels',
        'description': 'G├®n├®ration automatique avec d├®tection intelligente du mois bas├®e sur le dernier r├®capitulatif par bailleur'
    })
    
    return render(request, 'paiements/generer_recap_automatique.html', context)

@login_required
def get_calculation_preview(request):
    """API AJAX pour obtenir l'aper├ºu des calculs en temps r├®el."""
    if request.method != 'GET':
        return JsonResponse({'error': 'M├®thode non autoris├®e'}, status=405)
    
    # V├®rification des permissions avec fallback pour PRIVILEGE
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
        
        # R├®cup├®rer les bailleurs selon la s├®lection
        if bailleur_id and bailleur_id != 'tous':
            bailleurs = Bailleur.objects.filter(id=bailleur_id, is_deleted=False)
        else:
            bailleurs = Bailleur.objects.filter(is_deleted=False)
        
        if not bailleurs.exists():
            return JsonResponse({'error': 'Aucun bailleur trouv├®'}, status=404)
        
        # Calculer les totaux pour l'aper├ºu
        total_loyers = Decimal('0')
        total_charges = Decimal('0')
        total_charges_bailleur = Decimal('0')  # NOUVEAU
        nombre_proprietes = 0
        nombre_contrats = 0
        nombre_paiements = 0
        
        for bailleur in bailleurs:
            # R├®cup├®rer les propri├®t├®s actives du bailleur
            proprietes_actives = bailleur.proprietes.filter(
                contrats__est_actif=True,
                contrats__est_resilie=False
            ).distinct()
            
            nombre_proprietes += proprietes_actives.count()
            
            for propriete in proprietes_actives:
                # Contrats actifs de cette propri├®t├®
                contrats_actifs = propriete.contrats.filter(
                    est_actif=True,
                    est_resilie=False
                )
                nombre_contrats += contrats_actifs.count()
                
                for contrat in contrats_actifs:
                    # Loyers du mois (bas├®s sur le montant du contrat, pas les paiements re├ºus)
                    loyer_mensuel = contrat.montant_loyer or Decimal('0')
                    total_loyers += loyer_mensuel
                    
                    # Paiements re├ºus du mois (pour information)
                    paiements_mois = contrat.paiements.filter(
                        date_paiement__year=mois_date.year,
                        date_paiement__month=mois_date.month,
                        statut='valide',
                        type_paiement='loyer'
                    )
                    nombre_paiements += paiements_mois.count()
                    
                    # Charges d├®ductibles du mois
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
        
        # V├®rifier s'il existe d├®j├á des r├®capitulatifs pour ce mois
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
    """Tableau de bord sp├®cialis├® pour les r├®capitulatifs mensuels."""
    # V├®rification des permissions avec fallback pour PRIVILEGE
    permissions = check_group_permissions_with_fallback(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE', 'CAISSE'], 'view')
    
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:dashboard')
    
    from datetime import datetime, timedelta
    from django.db.models import Sum, Count, Avg
    from proprietes.models import Bailleur
    
    # Ann├®e courante
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
    
    # R├®capitulatifs r├®cents
    recaps_recents = RecapMensuel.objects.filter(
        is_deleted=False
    ).select_related('bailleur').order_by('-created_at')[:10]
    
    # Statistiques financi├¿res
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
        'title': 'Tableau de Bord - R├®capitulatifs Mensuels',
    })
    
    return render(request, 'paiements/tableau_bord_recaps_mensuels.html', context)

@login_required
def generer_pdf_recap_mensuel(request, recap_id):
    """G├®n├¿re un PDF pour un r├®capitulatif mensuel sp├®cifique."""
    from django.http import HttpResponse
    from core.utils import check_group_permissions_with_fallback
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        recap = get_object_or_404(RecapMensuel, id=recap_id)
        
        # V├®rifier les permissions
        permissions = check_group_permissions_with_fallback(
            request.user, 
            ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE', 'CAISSE'], 
            'view'
        )
        if not permissions['allowed']:
            messages.error(request, permissions['message'])
            return redirect('paiements:detail_recap_mensuel_auto', recap_id=recap_id)
        
        # V├®rifier que le bailleur existe
        if not recap.bailleur:
            messages.error(request, 'Ce r├®capitulatif n\'a pas de bailleur associ├®. Impossible de g├®n├®rer le PDF.')
            return redirect('paiements:detail_recap_mensuel_auto', recap_id=recap_id)
        
        # G├®n├®rer le PDF en utilisant la m├®thode du mod├¿le
        try:
            pdf_content = recap.generer_pdf_recapitulatif(user=request.user)
            
            # Cr├®er la r├®ponse HTTP
            response = HttpResponse(pdf_content, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{recap.get_nom_fichier_pdf()}"'
            
            # Log de l'action
            logger.info(
                f"PDF du r├®capitulatif {recap.pk} t├®l├®charg├® par {request.user.username}"
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Erreur lors de la g├®n├®ration du PDF du r├®capitulatif {recap.pk}: {e}", exc_info=True)
            messages.error(request, f'Erreur lors de la g├®n├®ration du PDF: {str(e)}')
            return redirect('paiements:detail_recap_mensuel_auto', recap_id=recap_id)
        
    except Exception as e:
        logger.error(f"Erreur lors de la g├®n├®ration du PDF: {str(e)}", exc_info=True)
        messages.error(request, f"Erreur lors de la g├®n├®ration du PDF: {str(e)}")
        return redirect('paiements:detail_recap_mensuel_auto', recap_id=recap_id)

@login_required
def generer_pdf_recaps_lot(request):
    """G├®n├¿re des PDF en lot pour un mois donn├®."""
    if request.method == 'POST':
        form = GenererPDFLotForm(request.POST)
        if form.is_valid():
            mois_recap = form.cleaned_data['mois_recap']
            
            try:
                # G├®n├®rer le PDF en lot avec ReportLab (seule option disponible sur Windows)
                # pdf_response = generate_recap_pdf_batch(mois_recap, method='reportlab')  # Fonction non disponible
                
                messages.error(request, "G├®n├®ration PDF en lot temporairement d├®sactiv├®e - Fonction en cours de d├®veloppement")
                return redirect('paiements:generer_pdf_lot')
                
            except Exception as e:
                messages.error(request, f"Erreur lors de la g├®n├®ration des PDFs en lot: {str(e)}")
    else:
        form = GenererPDFLotForm()
    
    return render(request, 'paiements/generer_pdf_lot.html', {
        'form': form,
        'page_title': 'G├®n├®ration PDF en Lot'
    })

@login_required
def supprimer_recap_mensuel(request, recap_id):
    """Supprime un r├®capitulatif mensuel (suppression logique)."""
    try:
        recap = get_object_or_404(RecapMensuel, id=recap_id, is_deleted=False)
        
        # V├®rifier les permissions - Seuls les superusers et le groupe PRIVILEGE peuvent supprimer
        is_privilege_user = hasattr(request.user, 'groupe_travail') and request.user.groupe_travail and request.user.groupe_travail.nom == 'PRIVILEGE'
        if not (request.user.is_superuser or is_privilege_user):
            messages.error(request, "Vous n'avez pas les permissions pour supprimer un r├®capitulatif.")
            return redirect('paiements:detail_recap_mensuel_auto', recap_id=recap_id)
        
        if request.method == 'POST':
            # Effectuer la suppression logique
            recap.is_deleted = True
            recap.deleted_at = timezone.now()
            recap.deleted_by = request.user
            recap.save()
            
            # G├®rer le cas o├╣ le bailleur pourrait ├¬tre None (pour les anciens r├®capitulatifs)
            if recap.bailleur:
                bailleur_nom = recap.bailleur.get_nom_complet()
            else:
                bailleur_nom = "Sans bailleur"
            
            messages.success(request, f"Le r├®capitulatif de {bailleur_nom} pour {recap.mois_recap.strftime('%B %Y')} a ├®t├® supprim├® avec succ├¿s.")
            return redirect('paiements:liste_recaps_mensuels_auto')
        
        # Afficher la page de confirmation
        # G├®rer le cas o├╣ le bailleur pourrait ├¬tre None
        if recap.bailleur:
            bailleur_nom = recap.bailleur.get_nom_complet()
        else:
            bailleur_nom = "Sans bailleur"
        
        context = get_context_with_entreprise_config({
            'recap': recap,
            'page_title': 'Confirmer la suppression',
            'title': f'Supprimer le r├®capitulatif - {bailleur_nom}',
        })
        
        return render(request, 'paiements/confirmer_suppression_recap.html', context)
        
    except Exception as e:
        messages.error(request, f"Erreur lors de la suppression du r├®capitulatif: {str(e)}")
        return redirect('paiements:liste_recaps_mensuels_auto')

@login_required
def restaurer_recap_mensuel(request, recap_id):
    """Restaure un r├®capitulatif mensuel supprim├®."""
    try:
        recap = get_object_or_404(RecapMensuel, id=recap_id, is_deleted=True)
        
        # V├®rifier les permissions - Seuls les superusers et le groupe PRIVILEGE peuvent restaurer
        is_privilege_user = hasattr(request.user, 'groupe_travail') and request.user.groupe_travail and request.user.groupe_travail.nom == 'PRIVILEGE'
        if not (request.user.is_superuser or is_privilege_user):
            messages.error(request, "Vous n'avez pas les permissions pour restaurer un r├®capitulatif.")
            return redirect('paiements:liste_recaps_mensuels_auto')
        
        # Restaurer le r├®capitulatif
        recap.is_deleted = False
        recap.deleted_at = None
        recap.deleted_by = None
        recap.save()
        
        # G├®rer le cas o├╣ le bailleur pourrait ├¬tre None (pour les anciens r├®capitulatifs)
        if recap.bailleur:
            bailleur_nom = recap.bailleur.get_nom_complet()
        else:
            bailleur_nom = "Sans bailleur"
        
        messages.success(request, f"Le r├®capitulatif de {bailleur_nom} pour {recap.mois_recap.strftime('%B %Y')} a ├®t├® restaur├® avec succ├¿s.")
        return redirect('paiements:detail_recap_mensuel_auto', recap_id=recap_id)
        
    except Exception as e:
        messages.error(request, f"Erreur lors de la restauration du r├®capitulatif: {str(e)}")
        return redirect('paiements:liste_recaps_mensuels_auto')

@login_required
def liste_recaps_supprimes(request):
    """Liste les r├®capitulatifs supprim├®s (superuser et PRIVILEGE uniquement)."""
    # V├®rifier les permissions
    is_privilege_user = hasattr(request.user, 'groupe_travail') and request.user.groupe_travail and request.user.groupe_travail.nom == 'PRIVILEGE'
    if not (request.user.is_superuser or is_privilege_user):
        messages.error(request, "Vous n'avez pas les permissions pour voir les r├®capitulatifs supprim├®s.")
        return redirect('paiements:liste_recaps_mensuels_auto')
    
    # R├®cup├®rer les r├®capitulatifs supprim├®s
    recaps_supprimes = RecapMensuel.objects.filter(is_deleted=True).order_by('-deleted_at')
    
    # Pagination
    paginator = Paginator(recaps_supprimes, 20)
    page_number = request.GET.get('page')
    recaps = paginator.get_page(page_number)
    
    context = get_context_with_entreprise_config({
        'recaps': recaps,
        'page_title': 'R├®capitulatifs Supprim├®s',
        'title': 'R├®capitulatifs Supprim├®s',
        'total_supprimes': recaps_supprimes.count(),
    })
    
    return render(request, 'paiements/recaps_supprimes.html', context)

@login_required
def apercu_pdf_recap_mensuel(request, recap_id):
    """Affiche un aper├ºu HTML du r├®capitulatif mensuel."""
    try:
        recap = get_object_or_404(RecapMensuel, id=recap_id)
        
        # V├®rifier les permissions
        if not request.user.has_perm('paiements.view_recapmensuel'):
            messages.error(request, "Vous n'avez pas les permissions pour voir ce r├®capitulatif.")
            return redirect('paiements:tableau_bord_recaps_mensuels')
        
        bailleur_nom = recap.bailleur.get_nom_complet() if recap.bailleur else "Sans bailleur"
        return render(request, 'paiements/apercu_pdf_recap_mensuel.html', {
            'recap': recap,
            'page_title': f'Aper├ºu - {bailleur_nom} - {recap.mois_recap.strftime("%B %Y")}'
        })
        
    except Exception as e:
        messages.error(request, f"Erreur lors de l'affichage de l'aper├ºu: {str(e)}")
        return redirect('paiements:tableau_bord_recaps_mensuels')

@login_required
def creer_recap_mensuel_bailleur(request, bailleur_id):
    """Cr├®e un r├®capitulatif mensuel pour un bailleur sp├®cifique avec d├®tection automatique du mois."""
    try:
        from proprietes.models import Bailleur
        
        bailleur = get_object_or_404(Bailleur, id=bailleur_id)
        
        # D├®tection automatique du mois de r├®capitulatif
        mois_info = RecapMensuel.get_mois_recap_suggere_pour_bailleur(bailleur)
        mois_recap = mois_info['mois_suggere']
        
        # V├®rifier si un r├®capitulatif existe d├®j├á pour ce mois et ce bailleur (non supprim├®)
        recap_existant = RecapMensuel.objects.filter(
            bailleur=bailleur,
            mois_recap=mois_recap,
            is_deleted=False
        ).first()
        
        if recap_existant:
            messages.info(request, f"Un r├®capitulatif existe d├®j├á pour {bailleur.get_nom_complet()} - {mois_info['mois_suggere_formate']}")
            return redirect('paiements:detail_recap_mensuel_auto', recap_id=recap_existant.id)
        
        # V├®rifier s'il existe un r├®capitulatif supprim├® logiquement pour ce bailleur et ce mois
        recap_supprime = RecapMensuel.objects.filter(
            bailleur=bailleur,
            mois_recap=mois_recap,
            is_deleted=True
        ).first()
        
        # Si un r├®cap supprim├® existe, le supprimer physiquement avant de cr├®er le nouveau
        if recap_supprime:
            recap_supprime.paiements_concernes.clear()
            recap_supprime.charges_deductibles.clear()
            recap_supprime.delete()
        
        # Cr├®er le nouveau r├®capitulatif
        recap = RecapMensuel.objects.create(
            bailleur=bailleur,
            mois_recap=mois_recap,
            cree_par=request.user
        )
        
        # Calculer les totaux automatiquement
        recap.calculer_totaux_bailleur()
        recap.save()
        
        # Message de succ├¿s avec information sur la d├®tection automatique
        message_succes = (
            f"R├®capitulatif cr├®├® avec succ├¿s pour {bailleur.get_nom_complet()} - {mois_info['mois_suggere_formate']}. "
            f"({mois_info['raison']})"
        )
        messages.success(request, message_succes)
        return redirect('paiements:detail_recap_mensuel_auto', recap_id=recap.id)
        
    except Exception as e:
        messages.error(request, f"Erreur lors de la cr├®ation du r├®capitulatif: {str(e)}")
        return redirect('paiements:tableau_bord_recaps_mensuels')

@login_required
def liste_bailleurs_recaps(request):
    """Liste des bailleurs pour cr├®er des r├®capitulatifs mensuels avec d├®tection automatique du mois."""
    try:
        from proprietes.models import Bailleur
        from datetime import date
        
        # R├®cup├®rer tous les bailleurs avec des propri├®t├®s actives
        bailleurs = Bailleur.objects.filter(
            propriete__contrats__est_actif=True,
            propriete__contrats__est_resilie=False
        ).distinct().order_by('nom')
        
        # Pour chaque bailleur, d├®terminer le mois sugg├®r├® et les informations contextuelles
        mois_actuel = date.today().replace(day=1)
        for bailleur in bailleurs:
            # Obtenir les informations de d├®tection automatique du mois
            mois_info = RecapMensuel.get_mois_recap_suggere_pour_bailleur(bailleur)
            bailleur.mois_suggere = mois_info['mois_suggere']
            bailleur.mois_suggere_formate = mois_info['mois_suggere_formate']
            bailleur.raison_suggestion = mois_info['raison']
            bailleur.dernier_mois = mois_info['dernier_mois']
            bailleur.recap_existant = mois_info['recap_existant']
            
            # R├®cup├®rer le r├®capitulatif existant pour le mois sugg├®r├®
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
            'page_title': 'Cr├®er des R├®capitulatifs Mensuels',
            'page_icon': 'calendar-plus',
            'description': 'Cr├®ation de r├®capitulatifs mensuels avec d├®tection automatique du mois bas├®e sur le dernier r├®capitulatif par bailleur'
        }
        
        return render(request, 'paiements/liste_bailleurs_recaps.html', context)
        
    except Exception as e:
        messages.error(request, f"Erreur lors du chargement des bailleurs: {str(e)}")
        return redirect('paiements:tableau_bord_recaps_mensuels')

@login_required
def creer_recap_avec_detection_auto(request, bailleur_id):
    """Cr├®e un r├®capitulatif avec d├®tection automatique du mois et possibilit├® de modification."""
    try:
        from proprietes.models import Bailleur
        from datetime import date
        
        bailleur = get_object_or_404(Bailleur, id=bailleur_id)
        
        if request.method == 'POST':
            # R├®cup├®rer le mois s├®lectionn├® par l'utilisateur
            mois_recap_str = request.POST.get('mois_recap')
            if not mois_recap_str:
                messages.error(request, "Veuillez s├®lectionner un mois.")
                return redirect('paiements:creer_recap_avec_detection_auto', bailleur_id=bailleur_id)
            
            mois_recap = datetime.strptime(mois_recap_str, '%Y-%m-%d').date()
            # Normaliser la date au premier jour du mois pour garantir la coh├®rence
            mois_recap = mois_recap.replace(day=1)
            
            # Obtenir les informations de d├®tection automatique pour validation
            mois_info = RecapMensuel.get_mois_recap_suggere_pour_bailleur(bailleur)
            
            # Validation stricte : v├®rifier que le mois s├®lectionn├® est bien le mois sugg├®r├®
            if mois_recap != mois_info['mois_suggere']:
                messages.error(request, 
                    f"Erreur de validation : Vous devez s├®lectionner le mois sugg├®r├® automatiquement "
                    f"({mois_info['mois_suggere_formate']}) pour maintenir la continuit├® des r├®capitulatifs. "
                    f"Raison : {mois_info['raison']}"
                )
                return redirect('paiements:creer_recap_avec_detection_auto', bailleur_id=bailleur_id)
            
            # V├®rifier si un r├®capitulatif existe d├®j├á pour ce mois et ce bailleur (comparaison par ann├®e et mois)
            recap_existant = RecapMensuel.objects.filter(
                bailleur=bailleur,
                mois_recap__year=mois_recap.year,
                mois_recap__month=mois_recap.month,
                is_deleted=False
            ).first()
            
            if recap_existant:
                messages.info(request, f"Un r├®capitulatif existe d├®j├á pour {bailleur.get_nom_complet()} - {mois_recap.strftime('%B %Y')}")
                return redirect('paiements:detail_recap_mensuel_auto', recap_id=recap_existant.id)
            
            # V├®rifier s'il existe un r├®capitulatif supprim├® logiquement pour ce bailleur et ce mois (comparaison par ann├®e et mois)
            recap_supprime = RecapMensuel.objects.filter(
                bailleur=bailleur,
                mois_recap__year=mois_recap.year,
                mois_recap__month=mois_recap.month,
                is_deleted=True
            ).first()
            
            # Si un r├®cap supprim├® existe, le supprimer physiquement avant de cr├®er le nouveau
            if recap_supprime:
                try:
                    recap_supprime.paiements_concernes.clear()
                    recap_supprime.charges_deductibles.clear()
                    recap_supprime.delete()
                    messages.info(request, f"L'ancien r├®capitulatif supprim├® a ├®t├® d├®finitivement supprim├® pour permettre la cr├®ation d'un nouveau.")
                except Exception as e:
                    messages.warning(request, f"Attention: Impossible de supprimer l'ancien r├®capitulatif: {str(e)}")
            
            # Cr├®er le nouveau r├®capitulatif
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
                messages.error(request, f"Erreur lors de la cr├®ation du r├®capitulatif: {str(e)}")
                # Log l'erreur compl├¿te pour le d├®bogage
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Erreur cr├®ation r├®capitulatif: {error_details}")
                return redirect('paiements:creer_recap_avec_detection_auto', bailleur_id=bailleur_id)
            
            messages.success(request, 
                f"R├®capitulatif cr├®├® avec succ├¿s pour {bailleur.get_nom_complet()} - {mois_recap.strftime('%B %Y')}. "
                f"({mois_info['raison']})"
            )
            return redirect('paiements:detail_recap_mensuel_auto', recap_id=recap.id)
        
        # Obtenir les informations de d├®tection automatique du mois
        mois_info = RecapMensuel.get_mois_recap_suggere_pour_bailleur(bailleur)
        
        # Pr├®parer les mois disponibles (12 derniers mois + mois sugg├®r├®)
        mois_disponibles = []
        date_courante = datetime.now()
        
        # Ajouter le mois sugg├®r├® en premier
        mois_suggere = mois_info['mois_suggere']
        mois_disponibles.append({
            'value': mois_suggere.strftime('%Y-%m-%d'),
            'label': f"{mois_info['mois_suggere_formate']} (Sugg├®r├® - {mois_info['raison']})",
            'is_suggested': True
        })
        
        # Ajouter les 12 derniers mois
        for i in range(12):
            date_mois = date_courante - timedelta(days=30*i)
            if date_mois != mois_suggere:  # ├ëviter les doublons
                mois_disponibles.append({
                    'value': date_mois.strftime('%Y-%m-%d'),
                    'label': date_mois.strftime('%B %Y'),
                    'is_suggested': False
                })
        
        context = {
            'bailleur': bailleur,
            'mois_info': mois_info,
            'mois_disponibles': mois_disponibles,
            'page_title': f'Cr├®er un R├®capitulatif - {bailleur.get_nom_complet()}',
            'page_icon': 'calendar-plus',
            'description': 'Cr├®ation de r├®capitulatif avec d├®tection automatique du mois'
        }
        
        return render(request, 'paiements/creer_recap_avec_detection.html', context)
        
    except Exception as e:
        messages.error(request, f"Erreur lors de la cr├®ation du r├®capitulatif: {str(e)}")
        return redirect('paiements:liste_bailleurs_recaps')

@login_required
def generer_pdf_recap_detaille_paysage(request, recap_id):
    """G├®n├¿re un PDF d├®taill├® en format A4 paysage avec toutes les informations enrichies."""
    try:
        recap = get_object_or_404(RecapMensuel, id=recap_id, is_deleted=False)
        
        # V├®rification des permissions
        permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE', 'CAISSE'], 'view')
        if not permissions['allowed']:
            messages.error(request, permissions['message'])
            return redirect('paiements:tableau_bord_recaps_mensuels')
        
        # R├®cup├®rer les d├®tails des propri├®t├®s avec informations enrichies
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
                # Calculer les garanties financi├¿res
                caution_requise = contrat_actif.loyer_mensuel or Decimal('0')
                avance_requise = contrat_actif.loyer_mensuel or Decimal('0')
                
                # R├®cup├®rer les paiements de caution et d'avance
                paiements_caution = contrat_actif.paiements.filter(
                    type_paiement='caution',
                    statut='valide'
                ).aggregate(total=Sum('montant'))['total'] or Decimal('0')
                
                paiements_avance = contrat_actif.paiements.filter(
                    type_paiement='avance',
                    statut='valide'
                ).aggregate(total=Sum('montant'))['total'] or Decimal('0')
                
                # V├®rifier les retards de paiement
                paiements_en_retard = contrat_actif.paiements.filter(
                    type_paiement='loyer',
                    statut='en_retard'
                ).count()
                
                # Calculer les charges du mois
                charges_mensuelles = contrat_actif.charges_mensuelles or Decimal('0')
                charges_bailleur = Decimal('0')  # ├Ç calculer selon la logique m├®tier
                
                # Montant net pour cette propri├®t├®
                montant_net = (contrat_actif.loyer_mensuel or Decimal('0')) - charges_mensuelles - charges_bailleur
                
                garanties_suffisantes = (
                    paiements_caution >= caution_requise and
                    paiements_avance >= avance_requise
                )
                
                propriete_detail = {
                    'id': propriete.id,
                    'nom': propriete.titre or f"Propri├®t├® #{propriete.id}",
                    'adresse': propriete.adresse or "Adresse non renseign├®e",
                    'ville': propriete.ville or "Ville non renseign├®e",
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
                    'statut_garanties': 'Compl├¿tes' if garanties_suffisantes else 'Incompl├¿tes',
                    'contact_locataire': f"{contrat_actif.locataire.telephone or 'N/A'} / {contrat_actif.locataire.email or 'N/A'}",
                }
                proprietes_details.append(propriete_detail)
                
                # Mettre ├á jour les statistiques globales
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
        
        # R├®cup├®rer l'historique des paiements du mois
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
                        'propriete': propriete.titre or f"Propri├®t├® #{propriete.id}",
                        'locataire': contrat_actif.locataire.get_nom_complet(),
                        'montant': paiement.montant,
                        'date_paiement': paiement.date_paiement,
                        'statut': paiement.get_statut_display(),
                        'methode_paiement': paiement.get_methode_paiement_display(),
                    })
        
        # R├®cup├®rer la configuration de l'entreprise
        from core.models import ConfigurationEntreprise
        entreprise_config = ConfigurationEntreprise.get_configuration_active()
        
        # G├®n├®rer le PDF avec xhtml2pdf
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
        
        # Cr├®er le PDF
        pdf_buffer = BytesIO()
        pisa_status = pisa.CreatePDF(html_content, dest=pdf_buffer)
        
        if pisa_status.err:
            messages.error(request, f"Erreur lors de la g├®n├®ration du PDF: {pisa_status.err}")
            return redirect('paiements:detail_recap_mensuel_auto', recap_id=recap.id)
        
        # Pr├®parer la r├®ponse
        pdf_content = pdf_buffer.getvalue()
        pdf_buffer.close()
        
        response = HttpResponse(pdf_content, content_type='application/pdf')
        bailleur_nom = recap.bailleur.get_nom_complet() if recap.bailleur else "sans_bailleur"
        response['Content-Disposition'] = f'attachment; filename="recapitulatif_detaille_{bailleur_nom.replace(" ", "_")}_{recap.mois_recap.strftime("%Y_%m")}.pdf"'
        
        return response
        
    except Exception as e:
        messages.error(request, f"Erreur lors de la g├®n├®ration du PDF d├®taill├®: {str(e)}")
        return redirect('paiements:detail_recap_mensuel_auto', recap_id=recap_id)


# Vues de suppression g├®n├®riques
from utilisateurs.mixins_suppression import SuppressionGeneriqueView

class SupprimerPaiementView(SuppressionGeneriqueView):
    model = Paiement
    
    def get_redirect_url(self, obj):
        return 'paiements:liste'
    
    def get_success_message(self, obj):
        return f"Paiement #{obj.id} supprim├® avec succ├¿s."

