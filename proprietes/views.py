from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q, Sum, ProtectedError
from django.http import JsonResponse, FileResponse
from django.utils import timezone
from datetime import timedelta
import os
from .models import Propriete, Bailleur, Locataire, TypeBien, ChargesBailleur
from .forms import ProprieteForm, BailleurForm, LocataireForm, TypeBienForm, ChargesBailleurForm, ChargesBailleurDeductionForm
from core.utils import convertir_montant
from core.models import Devise
from core.mixins import DetailViewQuickActionsMixin, ListViewQuickActionsMixin
from core.quick_actions_generator import QuickActionsGenerator
from contrats.models import Contrat
from core.models import AuditLog
from django.contrib.contenttypes.models import ContentType
from paiements.models import Paiement
from django.core.paginator import Paginator
from django.db import models
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Photo
from .forms import PhotoForm, PhotoMultipleForm
from proprietes.models import Document
from proprietes.forms import DocumentSearchForm, DocumentForm
# from proprietes.specialized_forms import DiagnosticForm, AssuranceForm, EtatLieuxForm  # Module supprimé
from django.http import HttpResponse
# from .document_viewer import DocumentViewerView, document_content_view, document_pdf_viewer, document_secure_proxy  # Module supprimé
# from .document_debug import document_debug_info, document_test_download  # Module supprimé
# from .simple_download import simple_document_download, simple_document_view  # Module supprimé

@login_required
def document_test_page(request):
    """Page de test pour les documents"""
    return render(request, 'proprietes/documents/document_test.html')


from core.intelligent_views import IntelligentListView
from .models import TypeBien
from utilisateurs.mixins import PrivilegeButtonsMixin
from utilisateurs.mixins_suppression import SuppressionGeneriqueView


class ProprieteListView(PrivilegeButtonsMixin, IntelligentListView):
    model = Propriete
    template_name = 'base_liste_intelligente.html'
    paginate_by = 20
    page_title = 'Propriétés'
    page_icon = 'home'
    
    def get_queryset(self):
        """Optimisation des requêtes avec select_related et prefetch_related"""
        return Propriete.objects.filter(is_deleted=False).select_related(
            'bailleur', 'type_bien', 'cree_par'
        ).prefetch_related(
            'unites_locatives', 'pieces'
        ).only(
            'id', 'numero_propriete', 'titre', 'surface', 'nombre_pieces', 
            'nombre_chambres', 'nombre_salles_bain', 'etat', 'disponible',
            'loyer_actuel', 'charges_locataire', 'date_creation', 'type_gestion',
            'bailleur__nom', 'bailleur__prenom', 'type_bien__nom'
        )
    add_url = 'proprietes:ajouter'
    add_text = 'Ajouter une propriété'
    search_fields = ['titre', 'adresse', 'ville', 'bailleur__nom', 'bailleur__prenom']
    filter_fields = ['etat', 'type_bien', 'disponible']
    default_sort = 'ville'
    columns = [
        {'field': 'numero_propriete', 'label': 'N° Propriété', 'sortable': True},
        {'field': 'titre', 'label': 'Titre', 'sortable': True},
        {'field': 'adresse', 'label': 'Adresse', 'sortable': True},
        {'field': 'ville', 'label': 'Ville', 'sortable': True},
        {'field': 'bailleur', 'label': 'Bailleur', 'sortable': True},
        {'field': 'type_bien', 'label': 'Type', 'sortable': True},
        {'field': 'loyer_actuel', 'label': 'Loyer', 'sortable': True},
        {'field': 'surface', 'label': 'Surface (m²)', 'sortable': True},
        {'field': 'disponible', 'label': 'Disponible', 'sortable': True},
    ]
    actions = [
        {'url_name': 'proprietes:detail', 'icon': 'eye', 'style': 'outline-primary', 'title': 'Voir'},
        {'url_name': 'proprietes:modifier', 'icon': 'pencil', 'style': 'outline-warning', 'title': 'Modifier'},
        {'url_name': 'proprietes:supprimer_propriete', 'icon': 'trash', 'style': 'outline-danger', 'title': 'Supprimer', 'condition': 'user.is_privilege_user'},
    ]
    sort_options = [
        {'value': 'ville', 'label': 'Ville'},
        {'value': 'loyer_actuel', 'label': 'Loyer'},
        {'value': 'surface', 'label': 'Surface'},
        {'value': 'date_creation', 'label': 'Date'},
    ]
    
    def get_queryset(self):
        """
        Optimisation des requêtes de base de données
        """
        queryset = super().get_queryset()
        return queryset.select_related('bailleur', 'type_bien')
    
    def get_context_data(self, **kwargs):
        """
        Ajout de statistiques et d'informations supplémentaires au contexte
        """
        context = super().get_context_data(**kwargs)
        
        # Statistiques
        context['total_proprietes'] = Propriete.objects.count()
        context['proprietes_louees'] = Propriete.objects.filter(disponible=False).count()
        
        # Utiliser la nouvelle logique de disponibilité
        from core.property_utils import get_proprietes_disponibles_global
        proprietes_disponibles_pour_location = get_proprietes_disponibles_global()
        context['proprietes_disponibles'] = proprietes_disponibles_pour_location.count()
        
        context['proprietes_en_travaux'] = Propriete.objects.filter(etat='mauvais').count()
        
        # SUPPRIMER: Calculs financiers pour la confidentialité
        # NE PAS afficher de revenus ou valeurs de patrimoine
        
        # Indicateurs d'activité non confidentiels
        context['proprietes_actives'] = Propriete.objects.filter(
            disponible=False,
            contrats__est_actif=True
        ).distinct().count()
        
        context['proprietes_avec_documents'] = Propriete.objects.filter(
            documents__isnull=False
        ).distinct().count()
        
        return context

liste_proprietes = ProprieteListView.as_view()


@login_required
def detail_propriete(request, pk):
    """
    Vue de détail d'une propriété - Optimisée pour la performance
    """
    # Vérification des permissions : PRIVILEGE, ADMINISTRATION, CONTROLES peuvent voir les détails
    from core.utils import check_group_permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'CONTROLES', 'CAISSE'], 'view')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('proprietes:liste')
    
    # Optimisation : select_related pour éviter les requêtes N+1
    propriete = get_object_or_404(
        Propriete.objects.select_related('bailleur', 'type_bien', 'cree_par'),
        pk=pk
    )
    
    # Optimisation : requêtes limitées et optimisées
    contrats = Contrat.objects.filter(propriete=propriete).select_related(
        'locataire', 'propriete'
    ).order_by('-date_debut')[:5]  # Limité à 5 contrats récents
    
    # Optimisation : paiements récents seulement
    paiements = Paiement.objects.filter(
        contrat__propriete=propriete
    ).select_related('contrat__locataire').order_by('-date_paiement')[:5]  # Limité à 5 paiements récents
    
    # Récupérer les charges bailleur
    charges_bailleur = ChargesBailleur.objects.filter(
        propriete=propriete
    ).order_by('-date_charge')[:5]
    
    context = {
        'propriete': propriete,
        'contrats': contrats,
        'paiements': paiements,
        'charges_bailleur': charges_bailleur,
    }
    return render(request, 'proprietes/detail.html', context)


@login_required
def detail_propriete_ajax(request, pk, section):
    """
    Vues AJAX pour le chargement différé des sections de détail
    """
    from core.utils import check_group_permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'CONTROLES', 'CAISSE'], 'view')
    if not permissions['allowed']:
        return JsonResponse({'error': 'Permission refusée'}, status=403)
    
    propriete = get_object_or_404(Propriete, pk=pk)
    
    if section == 'stats':
        # Statistiques optimisées
        context = {
            'propriete': propriete,
            'loyer_total': propriete.loyer_actuel or 0,
            'charges_bailleur': propriete.charges_bailleur.filter(is_deleted=False).aggregate(
                total=Sum('montant')
            )['total'] or 0,
        }
        return render(request, 'proprietes/partials/stats.html', context)
    
    elif section == 'contrats':
        # Contrats récents optimisés
        contrats = Contrat.objects.filter(propriete=propriete).select_related(
            'locataire', 'propriete'
        ).order_by('-date_debut')[:5]
        
        context = {
            'contrats': contrats,
            'propriete': propriete
        }
        return render(request, 'proprietes/partials/contrats.html', context)
    
    elif section == 'paiements':
        # Paiements récents optimisés
        paiements = Paiement.objects.filter(
            contrat__propriete=propriete
        ).select_related('contrat__locataire').order_by('-date_paiement')[:5]
        
        context = {
            'paiements': paiements,
            'propriete': propriete
        }
        return render(request, 'proprietes/partials/paiements.html', context)
    
    return JsonResponse({'error': 'Section non trouvée'}, status=404)


@login_required
def ajouter_propriete(request):
    """
    Vue pour ajouter une propriété avec documents
    """
    # Vérification des permissions : ADMINISTRATION et PRIVILEGE peuvent ajouter
    from core.utils import check_group_permissions
    from core.id_generator import IDGenerator
    
    permissions = check_group_permissions(request.user, ['PRIVILEGE'], 'add')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('proprietes:liste')
    
    if request.method == 'POST':
        form = ProprieteForm(request.POST, request.FILES)
        if form.is_valid():
            propriete = form.save(commit=False)
            propriete.cree_par = request.user
            
            # Vérifier si un numéro a été généré automatiquement
            if hasattr(form, '_auto_generated') and form._auto_generated:
                original_number = getattr(form, '_original_number', '')
                messages.info(
                    request,
                    f'Le numéro "{original_number}" existait déjà. '
                    f'Un numéro unique a été généré automatiquement: {propriete.numero_propriete}'
                )
            
            # Générer automatiquement le numéro unique de propriété avec garantie d'unicité absolue
            if not propriete.numero_propriete:
                from core.robust_id_generator import RobustIDGenerator
                try:
                    propriete.numero_propriete = RobustIDGenerator.generate_property_id()
                except Exception as e:
                    # En cas d'erreur, générer un ID de secours avec timestamp
                    from datetime import datetime
                    import uuid
                    timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')[:-3]
                    unique_id = str(uuid.uuid4())[:8]
                    propriete.numero_propriete = f"PRO-{timestamp}-{unique_id}"
            
            propriete.save()
            
            # Utiliser la méthode save du formulaire pour gérer les documents
            form.save(user=request.user)
            
            messages.success(
                request, 
                f'Propriété "{propriete.titre}" ajoutée avec succès! '
                f'Numéro: {propriete.numero_propriete}. '
                f'Documents associés créés automatiquement.'
            )
            
            # Vérifier si cette propriété nécessite des unités locatives
            if propriete.necessite_unites_locatives():
                # Créer automatiquement les pièces
                from .services import GestionPiecesService
                try:
                    pieces_crees = GestionPiecesService.creer_pieces_automatiques(propriete)
                    messages.success(
                        request,
                        f'{len(pieces_crees)} pièces créées automatiquement pour la propriété "{propriete.titre}".'
                    )
                except Exception as e:
                    messages.error(
                        request,
                        f'Erreur lors de la création automatique des pièces : {str(e)}'
                    )
            
            return redirect('proprietes:detail', pk=propriete.pk)
        else:
            messages.error(request, 'Veuillez corriger les erreurs dans le formulaire.')
    else:
        form = ProprieteForm()
        # Pré-générer le numéro unique pour l'affichage
        try:
            generator = IDGenerator()
            initial_numero = generator.generate_id('propriete')
            form.fields['numero_propriete'].initial = initial_numero
        except Exception as e:
            print(f"Erreur lors de la génération du numéro: {e}")
    
    context = {
        'form': form,
        'bailleurs': Bailleur.objects.all(),
        'types_bien': TypeBien.objects.all()
    }
    return render(request, 'proprietes/propriete_form.html', context)


@login_required
def modifier_propriete(request, pk):
    """
    Vue pour modifier une propriété
    """
    # Vérification des permissions : Seul PRIVILEGE peut modifier
    from core.utils import check_group_permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE'], 'modify')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('proprietes:liste')
    
    propriete = get_object_or_404(Propriete, pk=pk)
    
    if request.method == 'POST':
        form = ProprieteForm(request.POST, request.FILES, instance=propriete)
        if form.is_valid():
            # Vérifier si un numéro a été généré automatiquement
            if hasattr(form, '_auto_generated') and form._auto_generated:
                original_number = getattr(form, '_original_number', '')
                messages.info(
                    request,
                    f'Le numéro "{original_number}" existait déjà. '
                    f'Un numéro unique a été généré automatiquement: {form.cleaned_data["numero_propriete"]}'
                )
            
            form.save(user=request.user)
            messages.success(request, f'Propriété "{propriete.titre}" modifiée avec succès!')
            return redirect('proprietes:detail', pk=pk)
        else:
            messages.error(request, 'Veuillez corriger les erreurs dans le formulaire.')
    else:
        form = ProprieteForm(instance=propriete)
    
    context = {
        'form': form,
        'propriete': propriete,
        'bailleurs': Bailleur.objects.all(),
        'types_bien': TypeBien.objects.all()
    }
    return render(request, 'proprietes/propriete_form.html', context)


# Vues pour les charges bailleur
@login_required
def liste_charges_bailleur(request):
    """
    Vue de la liste des charges bailleur
    """
    charges = ChargesBailleur.objects.select_related('propriete', 'propriete__bailleur').all()
    
    # Filtres
    statut_filter = request.GET.get('statut', '')
    type_filter = request.GET.get('type', '')
    propriete_filter = request.GET.get('propriete', '')
    
    if statut_filter:
        charges = charges.filter(statut=statut_filter)
    
    if type_filter:
        charges = charges.filter(type_charge=type_filter)
    
    if propriete_filter:
        charges = charges.filter(propriete_id=propriete_filter)
    
    # Tri
    tri = request.GET.get('tri', 'date')
    if tri == 'montant':
        charges = charges.order_by('-montant')
    elif tri == 'priorite':
        charges = charges.order_by('-priorite')
    else:
        charges = charges.order_by('-date_charge')
    
    # Statistiques
    total_charges = charges.count()
    charges_en_attente = charges.filter(statut='en_attente').count()
    montant_total_en_attente = charges.filter(statut='en_attente').aggregate(
        total=Sum('montant')
    )['total'] or 0
    
    # Récupérer le locataire actif pour chaque charge (contrat actif au moment de la charge)
    charges_with_locataire = []
    for charge in charges:
        contrat = Contrat.objects.filter(propriete=charge.propriete, est_actif=True).order_by('-date_debut').first()
        locataire = contrat.locataire if contrat else None
        charges_with_locataire.append({
            'charge': charge,
            'locataire': locataire
        })
    
    context = {
        'charges': charges,
        'charges_with_locataire': charges_with_locataire,
        'total_charges': total_charges,
        'charges_en_attente': charges_en_attente,
        'montant_total_en_attente': montant_total_en_attente,
        'proprietes': Propriete.objects.filter(disponible=False),
        'filtres': {
            'statut': statut_filter,
            'type': type_filter,
            'propriete': propriete_filter,
            'tri': tri
        }
    }
    return render(request, 'proprietes/charges_bailleur_liste.html', context)


@login_required
def ajouter_charge_bailleur(request):
    """
    Vue pour ajouter une charge bailleur avec documents
    Redirige vers la nouvelle vue intelligente
    """
    # Redirection vers la nouvelle vue intelligente
    return redirect('proprietes:creer_charge_bailleur')


@login_required
def modifier_charge_bailleur(request, pk):
    """
    Vue pour modifier une charge bailleur
    """
    # Vérification des permissions : Seul PRIVILEGE peut modifier
    from core.utils import check_group_permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE'], 'modify')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('proprietes:liste_charges_bailleur')
    
    charge = get_object_or_404(ChargesBailleur, pk=pk)
    
    if request.method == 'POST':
        form = ChargesBailleurForm(request.POST, request.FILES, instance=charge)
        if form.is_valid():
            form.save(user=request.user)
            messages.success(request, f'Charge "{charge.titre}" modifiée avec succès!')
            return redirect('proprietes:liste_charges_bailleur')
        else:
            messages.error(request, 'Veuillez corriger les erreurs dans le formulaire.')
    else:
        form = ChargesBailleurForm(instance=charge)
    
    context = {
        'form': form,
        'charge': charge,
        'title': f'Modifier la charge "{charge.titre}"'
    }
    return render(request, 'proprietes/charge_bailleur_modifier.html', context)


@login_required
def detail_charge_bailleur(request, pk):
    """
    Vue de détail d'une charge bailleur
    """
    # Vérification des permissions : PRIVILEGE, ADMINISTRATION, CONTROLES peuvent voir les détails
    from core.utils import check_group_permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'CONTROLES', 'CAISSE'], 'view')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('proprietes:charges_bailleur_liste')
    
    charge = get_object_or_404(ChargesBailleur, pk=pk)
    
    context = {
        'charge': charge
    }
    return render(request, 'proprietes/charge_bailleur_detail.html', context)


@login_required
def deduction_charge_bailleur(request, pk):
    """
    Vue pour déduire une charge bailleur du retrait mensuel du bailleur
    """
    # Vérification des permissions : Seul PRIVILEGE peut modifier
    from core.utils import check_group_permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE'], 'modify')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('proprietes:charges_bailleur_liste')
    
    charge = get_object_or_404(ChargesBailleur, pk=pk)
    
    if request.method == 'POST':
        form = ChargesBailleurDeductionForm(charge.propriete, request.POST)
        if form.is_valid():
            montant_deduit = form.cleaned_data['montant_deduction']
            motif = form.cleaned_data.get('motif', '')
            notes = form.cleaned_data.get('notes', '')
            
            # Appliquer la déduction
            montant_effectivement_deduit = charge.marquer_comme_deduit(montant_deduit)
            
            # Intégrer la charge dans le retrait mensuel du bailleur
            from paiements.services_retraits_bailleur import ServiceRetraitsBailleurIntelligent
            
            # Utiliser le service intelligent pour intégrer la charge
            retrait = ServiceRetraitsBailleurIntelligent.integrer_charge_dans_retrait(
                charge=charge,
                montant_deduit=montant_effectivement_deduit,
                user=request.user
            )
            
            # Ajouter le motif et les notes à la charge
            if motif:
                charge.motif_deduction = motif
            if notes:
                charge.notes_deduction = notes
            charge.save()
            
            messages.success(
                request, 
                f'Déduction de {montant_effectivement_deduit} F CFA appliquée avec succès! '
                f'La charge a été intégrée dans le retrait mensuel du bailleur. '
                f'Motif: {motif}'
            )
            return redirect('proprietes:detail_charge_bailleur', pk=pk)
        else:
            # Afficher les erreurs spécifiques
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{form.fields[field].label}: {error}')
    else:
        form = ChargesBailleurDeductionForm(charge.propriete)
    
    context = {
        'form': form,
        'charge': charge
    }
    return render(request, 'proprietes/charge_bailleur_deduction.html', context)


@login_required
def marquer_charge_remboursee(request, pk):
    """
    Vue pour marquer une charge comme entièrement remboursée
    """
    # Vérification des permissions : Seul PRIVILEGE peut modifier
    from core.utils import check_group_permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE'], 'modify')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('proprietes:charges_bailleur_liste')
    
    charge = get_object_or_404(ChargesBailleur, pk=pk)
    
    if request.method == 'POST':
        charge.marquer_comme_rembourse()
        messages.success(request, f'Charge "{charge.titre}" marquée comme remboursée!')
        return redirect('proprietes:detail_charge_bailleur', pk=pk)
    
    context = {
        'charge': charge
    }
    return render(request, 'proprietes/charge_bailleur_remboursement.html', context)


# Vues pour les bailleurs
class BailleurListView(PrivilegeButtonsMixin, IntelligentListView):
    model = Bailleur
    template_name = 'base_liste_intelligente.html'
    paginate_by = 20
    page_title = 'Bailleurs'
    page_icon = 'user-tie'
    add_url = 'proprietes:ajouter_bailleur'
    add_text = 'Ajouter un bailleur'
    search_fields = ['nom', 'prenom', 'email', 'telephone', 'adresse']
    filter_fields = []
    default_sort = 'nom'
    columns = [
        {'field': 'numero_bailleur', 'label': 'N° Bailleur', 'sortable': True},
        {'field': 'nom', 'label': 'Nom', 'sortable': True},
        {'field': 'prenom', 'label': 'Prénom', 'sortable': True},
        {'field': 'email', 'label': 'Email', 'sortable': True},
        {'field': 'telephone', 'label': 'Téléphone', 'sortable': True},
        {'field': 'adresse', 'label': 'Adresse', 'sortable': True},
    ]
    actions = [
        {'url_name': 'proprietes:detail_bailleur', 'icon': 'eye', 'style': 'outline-primary', 'title': 'Voir'},
        {'url_name': 'proprietes:modifier_bailleur', 'icon': 'pencil', 'style': 'outline-warning', 'title': 'Modifier'},
    ]
    sort_options = [
        {'value': 'nom', 'label': 'Nom'},
        {'value': 'prenom', 'label': 'Prénom'},
        {'value': 'date_creation', 'label': 'Date'},
    ]
    
    def get_context_data(self, **kwargs):
        """
        Ajout de statistiques et d'informations supplémentaires au contexte
        """
        context = super().get_context_data(**kwargs)
        
        # Statistiques
        context['total_bailleurs'] = Bailleur.objects.count()
        
        return context

liste_bailleurs = BailleurListView.as_view()


@login_required
def detail_bailleur(request, pk):
    """Vue détaillée d'un bailleur avec statistiques de paiement."""
    from core.utils import check_group_permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'CONTROLES', 'CAISSE'], 'view')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('proprietes:bailleurs_liste')
    
    bailleur = get_object_or_404(Bailleur, pk=pk)
    
    # Récupérer les statistiques (optimisé)
    stats = bailleur.get_statistiques_paiements()
    
    # Récupérer les propriétés (optimisé)
    proprietes = bailleur.proprietes.select_related('type_bien').prefetch_related('contrats').order_by('-date_creation')[:10]
    
    # Récupérer les derniers paiements (optimisé)
    from paiements.models import Paiement
    derniers_paiements = Paiement.objects.filter(
        contrat__propriete__bailleur=bailleur,
        statut='valide'
    ).select_related('contrat__propriete', 'contrat__locataire').order_by('-date_paiement')[:5]
    
    # Récupérer les contrats actifs (optimisé)
    from contrats.models import Contrat
    contrats_actifs = Contrat.objects.filter(
        propriete__bailleur=bailleur,
        est_actif=True,
        est_resilie=False
    ).select_related('propriete', 'locataire')[:5]
    
    # Générer les actions rapides automatiquement
    context = {
        'bailleur': bailleur,
        'stats': stats,
        'proprietes': proprietes,
        'derniers_paiements': derniers_paiements,
        'contrats_actifs': contrats_actifs,
        'breadcrumbs': [
            {'url': 'core:dashboard', 'label': 'Tableau de bord'},
            {'url': 'proprietes:bailleurs_liste', 'label': 'Bailleurs'},
            {'label': bailleur.get_nom_complet()}
        ]
    }
    
    # Ajouter les actions rapides automatiquement
    context['quick_actions'] = QuickActionsGenerator.get_actions_for_bailleur(bailleur, request)
    
    return render(request, 'proprietes/detail_bailleur.html', context)


@login_required
def ajouter_bailleur(request):
    """
    Vue pour ajouter un bailleur avec identifiant unique et documents
    """
    # Vérification des permissions : ADMINISTRATION et PRIVILEGE peuvent ajouter
    from core.utils import check_group_permissions
    from core.id_generator import IDGenerator
    
    permissions = check_group_permissions(request.user, ['PRIVILEGE'], 'add')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('proprietes:bailleurs_liste')
    
    if request.method == 'POST':
        # Gérer les valeurs par défaut avant la validation
        post_data = request.POST.copy()
        if not post_data.get('civilite'):
            post_data['civilite'] = 'M'
        
        form = BailleurForm(post_data, request.FILES)
        if form.is_valid():
            bailleur = form.save(commit=False)
            bailleur.cree_par = request.user
            
            # Générer automatiquement le numéro unique de bailleur
            if not bailleur.numero_bailleur:
                generator = IDGenerator()
                # Essayer de générer un ID unique, réessayer en cas de conflit
                max_attempts = 10
                for attempt in range(max_attempts):
                    try:
                        candidate_id = generator.generate_id('bailleur')
                        # Vérifier si l'ID existe déjà
                        if not Bailleur.objects.filter(numero_bailleur=candidate_id).exists():
                            bailleur.numero_bailleur = candidate_id
                            break
                        else:
                            # Forcer une nouvelle séquence en ajoutant un offset
                            continue
                    except Exception as e:
                        if attempt == max_attempts - 1:
                            # Dernière tentative, générer un ID avec timestamp
                            from datetime import datetime
                            timestamp = datetime.now().strftime('%H%M%S')
                            bailleur.numero_bailleur = f"BAI-{datetime.now().year}-{timestamp}"
                            break
            
            bailleur.save()
            
            # Utiliser la méthode save du formulaire pour gérer les documents
            form.save(user=request.user)
            
            messages.success(
                request, 
                f'✅ <strong>Bailleur ajouté avec succès !</strong><br>'
                f'👤 <strong>Nom complet :</strong> {bailleur.get_nom_complet()}<br>'
                f'🔢 <strong>Numéro unique :</strong> {bailleur.numero_bailleur}<br>'
                f'📧 <strong>Email :</strong> {bailleur.email or "Non renseigné"}<br>'
                f'📞 <strong>Téléphone :</strong> {bailleur.telephone}<br>'
                f'📁 <strong>Documents :</strong> Dossier confidentiel créé automatiquement'
            )
            return redirect('proprietes:detail_bailleur', pk=bailleur.pk)
        else:
            # Afficher les erreurs détaillées pour le bailleur
            error_messages = []
            for field, errors in form.errors.items():
                if field != '__all__':
                    field_name = form.fields[field].label if field in form.fields else field
                    error_messages.append(f"<strong>{field_name}:</strong> {', '.join(errors)}")
                else:
                    for error in errors:
                        error_messages.append(f"<strong>Erreur générale:</strong> {error}")
            
            if error_messages:
                # Messages d'erreur plus clairs pour les champs civilité
                clear_errors = []
                for msg in error_messages:
                    if 'civilite' in msg.lower():
                        clear_errors.append('👤 <strong>Civilité :</strong> Veuillez sélectionner Monsieur, Madame ou Mademoiselle')
                    else:
                        clear_errors.append(f"<strong>{msg.split(':')[0]}:</strong> {':'.join(msg.split(':')[1:])}")
                
                messages.error(
                    request, 
                    f'❌ <strong>Erreurs de validation détectées :</strong><br>' + 
                    '<br>'.join(clear_errors)
                )
            else:
                messages.error(request, '❌ <strong>Veuillez corriger les erreurs dans le formulaire.</strong>')
    else:
        form = BailleurForm()
        # Pré-générer le numéro unique pour l'affichage
        try:
            generator = IDGenerator()
            initial_numero = generator.generate_id('bailleur')
            form.fields['numero_bailleur'].initial = initial_numero
        except Exception as e:
            print(f"Erreur lors de la génération du numéro: {e}")
    
    context = {
        'form': form,
        'title': 'Ajouter un bailleur',
        'breadcrumbs': [
            {'url': 'core:dashboard', 'label': 'Tableau de bord'},
            {'url': 'proprietes:bailleurs_liste', 'label': 'Bailleurs'},
            {'label': 'Ajouter'}
        ]
    }
    return render(request, 'proprietes/bailleurs/bailleur_form.html', context)


@login_required
def modifier_bailleur(request, pk):
    """
    Vue pour modifier un bailleur
    """
    # Vérification des permissions : Seul PRIVILEGE peut modifier
    from core.utils import check_group_permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE'], 'modify')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('proprietes:bailleurs_liste')
    
    bailleur = get_object_or_404(Bailleur, pk=pk)
    
    if request.method == 'POST':
        form = BailleurForm(request.POST, request.FILES, instance=bailleur)
        if form.is_valid():
            form.save(user=request.user)
            messages.success(
                request, 
                f'✅ <strong>Bailleur modifié avec succès !</strong><br>'
                f'👤 <strong>Nom complet :</strong> {bailleur.get_nom_complet()}<br>'
                f'🔢 <strong>Numéro unique :</strong> {bailleur.numero_bailleur}<br>'
                f'📧 <strong>Email :</strong> {bailleur.email or "Non renseigné"}<br>'
                f'📞 <strong>Téléphone :</strong> {bailleur.telephone}<br>'
                f'📁 <strong>Documents :</strong> Dossier mis à jour automatiquement'
            )
            return redirect('proprietes:detail_bailleur', pk=pk)
        else:
            # Afficher les erreurs détaillées pour la modification du bailleur
            error_messages = []
            for field, errors in form.errors.items():
                if field != '__all__':
                    field_name = form.fields[field].label if field in form.fields else field
                    error_messages.append(f"<strong>{field_name}:</strong> {', '.join(errors)}")
                else:
                    for error in errors:
                        error_messages.append(f"<strong>Erreur générale:</strong> {error}")
            
            if error_messages:
                messages.error(
                    request, 
                    f'❌ <strong>Erreurs de validation détectées :</strong><br>' + 
                    '<br>'.join(error_messages)
                )
            else:
                messages.error(request, '❌ <strong>Veuillez corriger les erreurs dans le formulaire.</strong>')
    else:
        form = BailleurForm(instance=bailleur)
    
    context = {
        'form': form,
        'bailleur': bailleur,
        'title': f'Modifier le bailleur "{bailleur.get_nom_complet()}"'
    }
    return render(request, 'proprietes/bailleurs/bailleur_form.html', context)


@login_required
def proprietes_bailleur(request, pk):
    """Vue pour afficher les propriétés d'un bailleur spécifique."""
    from core.utils import check_group_permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'CONTROLES', 'CAISSE'], 'view')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('proprietes:bailleurs_liste')
    
    bailleur = get_object_or_404(Bailleur, pk=pk)
    proprietes = bailleur.proprietes.select_related('type_bien', 'bailleur').prefetch_related('contrats').order_by('-date_creation')
    
    # Statistiques des propriétés (optimisées)
    stats = {
        'total': proprietes.count(),
        'disponibles': proprietes.filter(disponible=True).count(),
        'occupees': proprietes.filter(disponible=False).count(),
        'avec_contrats': proprietes.filter(contrats__isnull=False).distinct().count(),
    }
    
    context = {
        'bailleur': bailleur,
        'proprietes': proprietes,
        'stats': stats,
        'breadcrumbs': [
            {'url': 'core:dashboard', 'label': 'Tableau de bord'},
            {'url': 'proprietes:bailleurs_liste', 'label': 'Bailleurs'},
            {'url': f'/proprietes/bailleurs/{bailleur.pk}/', 'label': bailleur.get_nom_complet()},
            {'label': 'Ses Propriétés'}
        ],
        'quick_actions': [
            {'url': f'/proprietes/bailleurs/{bailleur.pk}/', 'label': 'Retour au Bailleur', 'icon': 'arrow-left', 'style': 'btn-secondary'},
            {'url': '/proprietes/ajouter/', 'label': 'Ajouter Propriété', 'icon': 'plus-circle', 'style': 'btn-success'},
            {'url': f'/proprietes/bailleurs/{bailleur.pk}/modifier/', 'label': 'Modifier Bailleur', 'icon': 'pencil', 'style': 'btn-primary'},
        ]
    }
    
    return render(request, 'proprietes/proprietes_bailleur.html', context)


@login_required
def test_quick_actions(request):
    """Vue de test pour les actions rapides."""
    context = {
        'quick_actions': [
            {'url': '/proprietes/bailleurs/1/modifier/', 'label': 'Modifier', 'icon': 'pencil', 'style': 'btn-primary'},
            {'url': '/proprietes/ajouter/', 'label': 'Ajouter Propriété', 'icon': 'plus-circle', 'style': 'btn-success'},
            {'url': '/paiements/liste/', 'label': 'Voir Paiements', 'icon': 'cash-coin', 'style': 'btn-info'},
            {'url': '/proprietes/bailleurs/1/proprietes/', 'label': 'Ses Propriétés', 'icon': 'house', 'style': 'btn-outline-primary'},
            {'url': '/contrats/ajouter/?bailleur=1', 'label': 'Nouveau Contrat', 'icon': 'file-contract', 'style': 'btn-outline-success'},
        ]
    }
    return render(request, 'test_quick_actions.html', context)


@login_required
def supprimer_bailleur(request, pk):
    # Vérification des permissions : Seul PRIVILEGE peut supprimer
    from core.utils import check_group_permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE'], 'delete')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('proprietes:bailleurs_liste')
    
    bailleur = get_object_or_404(Bailleur, pk=pk)
    
    if request.method == 'POST':
        try:
            # Suppression logique
            old_data = {f.name: getattr(bailleur, f.name) for f in bailleur._meta.fields}
            bailleur.est_supprime = True
            bailleur.date_suppression = timezone.now()
            bailleur.save()
            
            # Log d'audit
            AuditLog.objects.create(
                content_type=ContentType.objects.get_for_model(Bailleur),
                object_id=bailleur.pk,
                action='delete',
                details={
                    'old_data': old_data,
                    'new_data': {'est_supprime': True, 'date_suppression': str(timezone.now())}
                },
                object_repr=str(bailleur),
                user=request.user,
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            messages.success(request, f"Bailleur {bailleur.nom} {bailleur.prenom} supprimé avec succès.")
            return redirect('proprietes:bailleurs_liste')
            
        except ProtectedError as e:
            messages.error(request, f"Impossible de supprimer ce bailleur : {str(e)}")
            return redirect('proprietes:bailleurs_liste')
    
    context = {
        'bailleur': bailleur,
    }
    return render(request, 'proprietes/confirm_supprimer_bailleur.html', context)


# Vues pour les locataires
class LocataireListView(PrivilegeButtonsMixin, IntelligentListView):
    model = Locataire
    template_name = 'base_liste_intelligente.html'
    paginate_by = 20
    page_title = 'Locataires'
    page_icon = 'user'
    add_url = 'proprietes:ajouter_locataire'
    add_text = 'Ajouter un locataire'
    search_fields = ['nom', 'prenom', 'email', 'telephone', 'adresse']
    filter_fields = ['statut']
    default_sort = 'nom'
    columns = [
        {'field': 'numero_locataire', 'label': 'N° Locataire', 'sortable': True},
        {'field': 'nom', 'label': 'Nom', 'sortable': True},
        {'field': 'prenom', 'label': 'Prénom', 'sortable': True},
        {'field': 'email', 'label': 'Email', 'sortable': True},
        {'field': 'telephone', 'label': 'Téléphone', 'sortable': True},
        {'field': 'adresse', 'label': 'Adresse', 'sortable': True},
        {'field': 'statut', 'label': 'Statut', 'sortable': True},
    ]
    actions = [
        {'url_name': 'proprietes:detail_locataire', 'icon': 'eye', 'style': 'outline-primary', 'title': 'Voir'},
        {'url_name': 'proprietes:modifier_locataire', 'icon': 'pencil', 'style': 'outline-warning', 'title': 'Modifier'},
        {'url_name': 'proprietes:supprimer_locataire', 'icon': 'trash', 'style': 'outline-danger', 'title': 'Supprimer', 'condition': 'user.is_privilege_user'},
    ]
    sort_options = [
        {'value': 'nom', 'label': 'Nom'},
        {'value': 'prenom', 'label': 'Prénom'},
        {'value': 'date_creation', 'label': 'Date'},
    ]
    
    def get_context_data(self, **kwargs):
        """
        Ajout de statistiques et d'informations supplémentaires au contexte
        """
        context = super().get_context_data(**kwargs)
        
        # Statistiques
        context['total_locataires'] = Locataire.objects.count()
        context['locataires_actifs'] = Locataire.objects.filter(statut='actif').count()
        context['locataires_inactifs'] = Locataire.objects.filter(statut='inactif').count()
        
        return context

liste_locataires = LocataireListView.as_view()


# Vues de suppression génériques
class SupprimerProprieteView(SuppressionGeneriqueView):
    model = Propriete
    
    def get_redirect_url(self, obj):
        return 'proprietes:liste'
    
    def get_success_message(self, obj):
        return f"Propriété {obj.titre} supprimée avec succès."


class SupprimerLocataireView(SuppressionGeneriqueView):
    model = Locataire
    
    def get_redirect_url(self, obj):
        return 'proprietes:locataires_liste'
    
    def get_success_message(self, obj):
        return f"Locataire {obj.get_nom_complet()} supprimé avec succès."
    
    def get_object(self):
        """Récupère l'objet à supprimer."""
        return get_object_or_404(self.model, pk=self.kwargs['pk'])
    
    def get_template_names(self):
        """Retourne le template approprié selon le contexte."""
        obj = self.get_object()
        
        # Si le locataire a des contrats actifs, utiliser le template avancé
        if obj.a_des_contrats_actifs():
            return ['proprietes/confirm_supprimer_locataire_avance.html']
        else:
            # Sinon, utiliser le template de suppression définitive
            return ['proprietes/confirm_supprimer_locataire_definitif.html']
    
    def get_context_data(self, **kwargs):
        """Ajoute des informations sur les contrats actifs au contexte."""
        context = {}
        obj = self.get_object()
        
        # Vérifier les contrats actifs
        contrats_actifs = obj.get_contrats_actifs()
        context['contrats_actifs'] = contrats_actifs
        context['a_des_contrats_actifs'] = obj.a_des_contrats_actifs()
        context['peut_etre_supprime_definitivement'] = obj.peut_etre_supprime_definitivement()
        
        # Pour le template avancé, ajouter d'autres informations
        if obj.a_des_contrats_actifs():
            from contrats.models import Contrat
            from paiements.models import Paiement
            
            # Contrats inactifs
            contrats_inactifs = Contrat.objects.filter(
                locataire=obj,
                est_actif=False,
                is_deleted=False
            )
            context['contrats_inactifs'] = contrats_inactifs
            
            # Nombre de paiements
            paiements_count = Paiement.objects.filter(contrat__locataire=obj).count()
            context['paiements_count'] = paiements_count
            
            # Recommandation
            context['recommandation'] = 'desactiver' if contrats_actifs.exists() else 'supprimer'
            
            # Autres locataires pour le transfert
            autres_locataires = Locataire.objects.filter(
                statut='actif',
                est_supprime=False
            ).exclude(pk=obj.pk)
            context['autres_locataires'] = autres_locataires
        
        return context
    
    def get(self, request, *args, **kwargs):
        """Affiche le template de confirmation de suppression."""
        obj = self.get_object()
        context = self.get_context_data()
        template_name = self.get_template_names()[0]
        return render(request, template_name, context)
    
    def post(self, request, *args, **kwargs):
        """Gère la suppression avec vérifications de sécurité."""
        print(f"POST reçu pour suppression locataire: {request.POST}")
        obj = self.get_object()
        print(f"Objet récupéré: {obj}")
        
        # Vérifier les permissions
        from core.utils import check_group_permissions
        permissions = check_group_permissions(request.user, ['PRIVILEGE'], 'delete')
        if not permissions['allowed']:
            messages.error(request, permissions['message'])
            return redirect(self.get_redirect_url(obj))
        
        action = request.POST.get('action')
        
        if action == 'logical_delete':
            # Suppression logique (mise en corbeille) - toujours autorisée
            return self.logical_delete(request, obj)
            
        elif action == 'permanent_delete':
            # Suppression définitive - nécessite des vérifications
            return self.permanent_delete(request, obj)
            
        elif action == 'cancel':
            return redirect(self.get_redirect_url(obj))
        
        return redirect(self.get_redirect_url(obj))
    
    def logical_delete(self, request, obj):
        """Effectue une suppression logique (mise en corbeille)."""
        from django.utils import timezone
        from core.models import AuditLog
        from django.contrib.contenttypes.models import ContentType
        
        # Log d'audit - filtrer les champs non sérialisables
        old_data = {}
        for f in obj._meta.fields:
            try:
                value = getattr(obj, f.name)
                # Convertir les objets non sérialisables en string
                if hasattr(value, 'url'):  # FieldFile
                    old_data[f.name] = str(value.url) if value else None
                elif hasattr(value, 'pk'):  # ForeignKey
                    old_data[f.name] = value.pk if value else None
                elif isinstance(value, (str, int, float, bool, type(None))):
                    old_data[f.name] = value
                else:
                    old_data[f.name] = str(value)
            except Exception:
                old_data[f.name] = str(getattr(obj, f.name, None))
        obj.est_supprime = True
        obj.date_suppression = timezone.now()
        obj.save()
        
        # Log d'audit
        AuditLog.objects.create(
            content_type=ContentType.objects.get_for_model(Locataire),
            object_id=obj.pk,
            action='delete',
            details={
                'old_data': old_data,
                'new_data': {'est_supprime': True, 'date_suppression': str(timezone.now())},
                'action_type': 'LOGICAL_DELETE'
            },
            object_repr=str(obj),
            user=request.user,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        messages.success(request, f"Locataire {obj.get_nom_complet()} supprimé logiquement et placé dans la corbeille.")
        return redirect(self.get_redirect_url(obj))
    
    def permanent_delete(self, request, obj):
        """Effectue une suppression définitive avec vérifications de sécurité."""
        from core.models import AuditLog
        from django.contrib.contenttypes.models import ContentType
        
        # Vérification 1: Le locataire ne doit pas avoir de contrats actifs
        if obj.a_des_contrats_actifs():
            contrats_actifs = obj.get_contrats_actifs()
            messages.error(
                request, 
                f"Impossible de supprimer définitivement {obj.get_nom_complet()}. "
                f"Ce locataire a {contrats_actifs.count()} contrat(s) actif(s). "
                f"Veuillez d'abord résilier ou transférer ces contrats."
            )
            return redirect(self.get_redirect_url(obj))
        
        # Vérification 2: Confirmation multiple
        confirmation_1 = request.POST.get('confirmation_1') == 'on'
        confirmation_2 = request.POST.get('confirmation_2') == 'on'
        confirmation_3 = request.POST.get('confirmation_3') == 'on'
        
        if not (confirmation_1 and confirmation_2 and confirmation_3):
            messages.error(
                request, 
                "Vous devez confirmer les trois cases de sécurité pour effectuer une suppression définitive."
            )
            return redirect(self.get_redirect_url(obj))
        
        # Vérification 3: Mot de passe de confirmation
        password_confirmation = request.POST.get('password_confirmation', '')
        if not request.user.check_password(password_confirmation):
            messages.error(request, "Le mot de passe de confirmation est incorrect.")
            return redirect(self.get_redirect_url(obj))
        
        # Log d'audit avant suppression - filtrer les champs non sérialisables
        old_data = {}
        for f in obj._meta.fields:
            try:
                value = getattr(obj, f.name)
                # Convertir les objets non sérialisables en string
                if hasattr(value, 'url'):  # FieldFile
                    old_data[f.name] = str(value.url) if value else None
                elif hasattr(value, 'pk'):  # ForeignKey
                    old_data[f.name] = value.pk if value else None
                elif isinstance(value, (str, int, float, bool, type(None))):
                    old_data[f.name] = value
                else:
                    old_data[f.name] = str(value)
            except Exception:
                old_data[f.name] = str(getattr(obj, f.name, None))
        AuditLog.objects.create(
            content_type=ContentType.objects.get_for_model(Locataire),
            object_id=obj.pk,
            action='delete',
            details={
                'old_data': old_data,
                'new_data': None,
                'action_type': 'PERMANENT_DELETE'
            },
            object_repr=str(obj),
            user=request.user,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        # Suppression définitive
        nom_complet = obj.get_nom_complet()
        obj.delete()
        
        messages.success(request, f"Locataire {nom_complet} supprimé définitivement de la base de données.")
        return redirect(self.get_redirect_url(obj))


class SupprimerBailleurView(SuppressionGeneriqueView):
    model = Bailleur
    
    def get_redirect_url(self, obj):
        return 'proprietes:bailleurs_liste'
    
    def get_success_message(self, obj):
        return f"Bailleur {obj.get_nom_complet()} supprimé avec succès."


class SupprimerTypeBienView(SuppressionGeneriqueView):
    model = TypeBien
    
    def get_redirect_url(self, obj):
        return 'proprietes:liste_types_bien'
    
    def get_success_message(self, obj):
        return f"Type de bien {obj.nom} supprimé avec succès."


class TypeBienListView(PrivilegeButtonsMixin, IntelligentListView):
    model = TypeBien
    template_name = 'base_liste_intelligente.html'
    paginate_by = 20
    page_title = 'Types de biens'
    page_icon = 'building'
    add_url = None  # Pas de fonction d'ajout disponible
    add_text = 'Ajouter un type de bien'
    search_fields = ['nom', 'description']
    filter_fields = []
    default_sort = 'nom'
    columns = [
        {'field': 'nom', 'label': 'Nom', 'sortable': True},
        {'field': 'description', 'label': 'Description', 'sortable': True},
    ]
    actions = [
        {'url_name': 'proprietes:modifier_type_bien', 'icon': 'pencil', 'style': 'outline-warning', 'title': 'Modifier'},
        {'url_name': 'proprietes:supprimer_type_bien', 'icon': 'trash', 'style': 'outline-danger', 'title': 'Supprimer', 'condition': 'user.is_privilege_user'},
    ]
    sort_options = [
        {'value': 'nom', 'label': 'Nom'},
    ]
    
    def get_context_data(self, **kwargs):
        """
        Ajout de statistiques et d'informations supplémentaires au contexte
        """
        context = super().get_context_data(**kwargs)
        
        # Statistiques
        context['total_types_biens'] = TypeBien.objects.count()
        
        return context

liste_types_biens = TypeBienListView.as_view()


class ChargesBailleurListView(PrivilegeButtonsMixin, IntelligentListView):
    model = ChargesBailleur
    template_name = 'base_liste_intelligente.html'
    paginate_by = 20
    page_title = 'Charges bailleur'
    page_icon = 'file-invoice'
    add_url = 'proprietes:ajouter_charge_bailleur'
    add_text = 'Ajouter une charge'
    search_fields = ['titre', 'description', 'propriete__titre', 'propriete__bailleur__nom', 'propriete__bailleur__prenom']
    filter_fields = ['statut', 'type_charge', 'priorite']
    default_sort = '-date_charge'
    columns = [
        {'field': 'titre', 'label': 'Titre', 'sortable': True},
        {'field': 'propriete', 'label': 'Propriété', 'sortable': True},
        {'field': 'montant', 'label': 'Montant', 'sortable': True},
        {'field': 'statut', 'label': 'Statut', 'sortable': True},
        {'field': 'type_charge', 'label': 'Type', 'sortable': True},
        {'field': 'priorite', 'label': 'Priorité', 'sortable': True},
        {'field': 'date_charge', 'label': 'Date', 'sortable': True},
    ]
    actions = [
        {'url_name': 'proprietes:detail_charge_bailleur', 'icon': 'eye', 'style': 'outline-primary', 'title': 'Voir'},
        {'url_name': 'proprietes:modifier_charge_bailleur', 'icon': 'pencil', 'style': 'outline-warning', 'title': 'Modifier'},
    ]
    sort_options = [
        {'value': 'date_charge', 'label': 'Date'},
        {'value': 'montant', 'label': 'Montant'},
        {'value': 'titre', 'label': 'Titre'},
        {'value': 'statut', 'label': 'Statut'},
        {'value': 'type_charge', 'label': 'Type'},
        {'value': 'priorite', 'label': 'Priorité'},
    ]
    
    def get_queryset(self):
        """
        Optimisation des requêtes de base de données
        """
        queryset = super().get_queryset()
        return queryset.select_related('propriete', 'propriete__bailleur')
    
    def get_context_data(self, **kwargs):
        """
        Ajout de statistiques et d'informations supplémentaires au contexte
        """
        context = super().get_context_data(**kwargs)
        
        # Statistiques
        context['total_charges'] = ChargesBailleur.objects.count()
        context['charges_en_attente'] = ChargesBailleur.objects.filter(statut='en_attente').count()
        context['charges_remboursees'] = ChargesBailleur.objects.filter(statut='rembourse').count()
        context['charges_deduites'] = ChargesBailleur.objects.filter(statut='deduit_loyer').count()
        
        # Montant total
        from django.db.models import Sum
        context['montant_total'] = ChargesBailleur.objects.aggregate(total=Sum('montant'))['total'] or 0
        
        return context

liste_charges_bailleur = ChargesBailleurListView.as_view()


@login_required
def detail_locataire(request, pk):
    """Vue détaillée d'un locataire avec statistiques de paiement."""
    from core.utils import check_group_permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'CONTROLES', 'CAISSE'], 'view')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('proprietes:locataires_liste')
    
    locataire = get_object_or_404(Locataire, pk=pk)
    
    # Récupérer les statistiques
    stats = locataire.get_statistiques_paiements()
    
    # Récupérer les contrats
    contrats = locataire.contrats.all().order_by('-date_debut')
    
    # Récupérer les derniers paiements
    from paiements.models import Paiement
    derniers_paiements = Paiement.objects.filter(
        contrat__locataire=locataire,
        statut='valide'
    ).order_by('-date_paiement')[:10]
    
    # Récupérer le contrat actuel
    from contrats.models import Contrat
    from django.utils import timezone
    
    contrat_actuel = Contrat.objects.filter(
        locataire=locataire,
        est_actif=True,
        est_resilie=False,
        date_debut__lte=timezone.now().date(),
        date_fin__gte=timezone.now().date()
    ).first()
    
    # Récupérer les charges déductibles
    from paiements.models import ChargeDeductible
    charges_deductibles = ChargeDeductible.objects.filter(
        contrat__locataire=locataire
    ).order_by('-date_charge')[:5]
    
    context = {
        'locataire': locataire,
        'stats': stats,
        'contrats': contrats,
        'contrat_actuel': contrat_actuel,
        'derniers_paiements': derniers_paiements,
        'charges_deductibles': charges_deductibles,
        'breadcrumbs': [
            {'url': 'core:dashboard', 'label': 'Tableau de bord'},
            {'url': 'proprietes:locataires_liste', 'label': 'Locataires'},
            {'label': locataire.get_nom_complet()}
        ],
        'quick_actions': QuickActionsGenerator.get_actions_for_locataire(locataire, request)
    }
    
    return render(request, 'proprietes/detail_locataire.html', context)


@login_required
def ajouter_locataire(request):
    """
    Vue pour ajouter un locataire avec documents
    """
    # Vérification des permissions : ADMINISTRATION et PRIVILEGE peuvent ajouter
    from core.utils import check_group_permissions
    from core.id_generator import IDGenerator
    
    permissions = check_group_permissions(request.user, ['PRIVILEGE'], 'add')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('proprietes:locataires_liste')
    
    if request.method == 'POST':
        # Gérer les valeurs par défaut avant la validation
        post_data = request.POST.copy()
        if not post_data.get('civilite'):
            post_data['civilite'] = 'M'
        if not post_data.get('statut'):
            post_data['statut'] = 'actif'
        
        form = LocataireForm(post_data, request.FILES)
        if form.is_valid():
            locataire = form.save(commit=False)
            locataire.cree_par = request.user
            
            # Générer automatiquement un numéro unique de locataire
            from datetime import datetime
            import uuid
            
            # Utiliser un timestamp + UUID court pour garantir l'unicité
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            unique_id = str(uuid.uuid4())[:8].upper()
            locataire.numero_locataire = f"LOC-{timestamp}-{unique_id}"
            
            locataire.save()
            
            messages.success(
                request, 
                f'✅ <strong>Locataire ajouté avec succès !</strong><br>'
                f'👤 <strong>Nom complet :</strong> {locataire.get_nom_complet()}<br>'
                f'🔢 <strong>Numéro unique :</strong> {locataire.numero_locataire}<br>'
                f'📧 <strong>Email :</strong> {locataire.email or "Non renseigné"}<br>'
                f'📞 <strong>Téléphone :</strong> {locataire.telephone}<br>'
                f'🏠 <strong>Statut :</strong> {locataire.get_statut_display()}<br>'
                f'📁 <strong>Documents :</strong> Dossier confidentiel créé automatiquement'
            )
            return redirect('proprietes:detail_locataire', pk=locataire.pk)
        else:
            # Afficher les erreurs détaillées
            error_messages = []
            for field, errors in form.errors.items():
                if field != '__all__':
                    field_name = form.fields[field].label if field in form.fields else field
                    error_messages.append(f"{field_name}: {', '.join(errors)}")
                else:
                    for error in errors:
                        error_messages.append(f"Erreur générale: {error}")
            
            if error_messages:
                # Messages d'erreur plus clairs pour les champs civilité et statut
                clear_errors = []
                for msg in error_messages:
                    if 'civilite' in msg.lower():
                        clear_errors.append('👤 <strong>Civilité :</strong> Veuillez sélectionner Monsieur, Madame ou Mademoiselle')
                    elif 'statut' in msg.lower():
                        clear_errors.append('🏠 <strong>Statut :</strong> Veuillez sélectionner Actif, Inactif ou Suspendu')
                    else:
                        clear_errors.append(f"<strong>{msg.split(':')[0]}:</strong> {':'.join(msg.split(':')[1:])}")
                
                messages.error(
                    request, 
                    f'❌ <strong>Erreurs de validation détectées :</strong><br>' + 
                    '<br>'.join(clear_errors)
                )
            else:
                messages.error(request, '❌ <strong>Veuillez corriger les erreurs dans le formulaire.</strong>')
    else:
        form = LocataireForm()
    
    context = {
        'form': form,
        'title': 'Ajouter un locataire'
    }
    return render(request, 'proprietes/locataires/locataire_form.html', context)


@login_required
def modifier_locataire(request, pk):
    """
    Vue pour modifier un locataire
    """
    # Vérification des permissions : Seul PRIVILEGE peut modifier
    from core.utils import check_group_permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE'], 'modify')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('proprietes:locataires_liste')
    
    locataire = get_object_or_404(Locataire, pk=pk)
    
    if request.method == 'POST':
        form = LocataireForm(request.POST, request.FILES, instance=locataire)
        if form.is_valid():
            locataire = form.save(commit=False)
            locataire.modifie_par = request.user
            locataire.save()
            messages.success(
                request, 
                f'✅ <strong>Locataire modifié avec succès !</strong><br>'
                f'👤 <strong>Nom complet :</strong> {locataire.get_nom_complet()}<br>'
                f'🔢 <strong>Numéro unique :</strong> {locataire.numero_locataire}<br>'
                f'📧 <strong>Email :</strong> {locataire.email or "Non renseigné"}<br>'
                f'📞 <strong>Téléphone :</strong> {locataire.telephone}<br>'
                f'🏠 <strong>Statut :</strong> {locataire.get_statut_display()}<br>'
                f'📁 <strong>Documents :</strong> Dossier mis à jour automatiquement'
            )
            return redirect('proprietes:detail_locataire', pk=pk)
        else:
            # Afficher les erreurs détaillées pour la modification du locataire
            error_messages = []
            for field, errors in form.errors.items():
                if field != '__all__':
                    field_name = form.fields[field].label if field in form.fields else field
                    error_messages.append(f"<strong>{field_name}:</strong> {', '.join(errors)}")
                else:
                    for error in errors:
                        error_messages.append(f"<strong>Erreur générale:</strong> {error}")
            
            if error_messages:
                messages.error(
                    request, 
                    f'❌ <strong>Erreurs de validation détectées :</strong><br>' + 
                    '<br>'.join(error_messages)
                )
            else:
                messages.error(request, '❌ <strong>Veuillez corriger les erreurs dans le formulaire.</strong>')
    else:
        form = LocataireForm(instance=locataire)
    
    context = {
        'form': form,
        'locataire': locataire,
        'title': f'Modifier le locataire "{locataire.get_nom_complet()}"'
    }
    return render(request, 'proprietes/locataires/locataire_form.html', context)


@login_required
def supprimer_locataire(request, pk):
    """
    Vue améliorée pour supprimer un locataire avec gestion des références
    """
    # Vérification des permissions : Seul PRIVILEGE peut supprimer
    from core.utils import check_group_permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE'], 'delete')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('proprietes:locataires_liste')
    
    locataire = get_object_or_404(Locataire, pk=pk)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'logical_delete':
            # Suppression logique
            old_data = {f.name: getattr(locataire, f.name) for f in locataire._meta.fields}
            locataire.est_supprime = True
            locataire.date_suppression = timezone.now()
            locataire.save()
            
            # Log d'audit
            AuditLog.objects.create(
                content_type=ContentType.objects.get_for_model(Locataire),
                object_id=locataire.pk,
                action='delete',
                details={
                    'old_data': old_data,
                    'new_data': {'est_supprime': True, 'date_suppression': str(timezone.now())}
                },
                object_repr=str(locataire),
                user=request.user,
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            messages.success(request, f"Locataire {locataire.nom} {locataire.prenom} supprimé logiquement et placé dans la corbeille.")
            return redirect('proprietes:locataires_liste')
            
        elif action == 'deactivate':
            # Désactivation
            old_data = {f.name: getattr(locataire, f.name) for f in locataire._meta.fields}
            locataire.statut = 'inactif'
            locataire.save()
            
            # Log d'audit
            AuditLog.objects.create(
                content_type=ContentType.objects.get_for_model(Locataire),
                object_id=locataire.pk,
                action='update',
                details={
                    'old_data': old_data,
                    'new_data': {'statut': 'inactif'}
                },
                object_repr=str(locataire),
                user=request.user,
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            messages.success(request, f"Locataire {locataire.nom} {locataire.prenom} désactivé avec succès.")
            return redirect('proprietes:locataires_liste')
            
        elif action == 'transfer_contracts':
            # Transfert des contrats vers un autre locataire
            nouveau_locataire_id = request.POST.get('nouveau_locataire')
            if nouveau_locataire_id:
                try:
                    nouveau_locataire = Locataire.objects.get(id=nouveau_locataire_id)
                    contrats_transferes = Contrat.objects.filter(locataire=locataire, est_actif=True)
                    contrats_transferes.update(locataire=nouveau_locataire)
                    
                    # Log d'audit
                    AuditLog.objects.create(
                        content_type=ContentType.objects.get_for_model(Locataire),
                        object_id=locataire.pk,
                        action='update',
                        details={
                            'old_data': {'contrats_count': contrats_transferes.count()},
                            'new_data': {'nouveau_locataire_id': nouveau_locataire_id}
                        },
                        object_repr=str(locataire),
                        user=request.user,
                        ip_address=request.META.get('REMOTE_ADDR'),
                        user_agent=request.META.get('HTTP_USER_AGENT', '')
                    )
                    
                    messages.success(request, f"Contrats transférés vers {nouveau_locataire.nom} {nouveau_locataire.prenom}")
                    return redirect('proprietes:locataires_liste')
                except Locataire.DoesNotExist:
                    messages.error(request, "Nouveau locataire non trouvé.")
            else:
                messages.error(request, "Veuillez sélectionner un nouveau locataire.")
    
    # Récupérer les informations sur les références
    contrats = Contrat.objects.filter(locataire=locataire, est_actif=True)
    paiements = Paiement.objects.filter(contrat__locataire=locataire)
    
    # Récupérer tous les locataires actifs pour le transfert
    autres_locataires = Locataire.objects.filter(statut='actif').exclude(pk=locataire.pk)
    
    context = {
        'locataire': locataire,
        'contrats_count': contrats.count(),
        'paiements_count': paiements.count(),
        'autres_locataires': autres_locataires,
    }
    
    return render(request, 'proprietes/confirm_supprimer_locataire_avance.html', context)


@login_required
def corbeille_locataires(request):
    """
    Vue pour gérer la corbeille des locataires supprimés
    """
    # VÉRIFICATION CRITIQUE : Seul PRIVILEGE peut accéder à la corbeille
    groupe = getattr(request.user, 'groupe_travail', None)
    if not groupe or groupe.nom.upper() != 'PRIVILEGE':
        messages.error(request, "Seuls les utilisateurs du groupe PRIVILEGE peuvent accéder à la corbeille des locataires.")
        return redirect('proprietes:locataires_liste')
    
    # Récupérer les locataires supprimés logiquement
    locataires_supprimes = Locataire.objects.filter(est_supprime=True).order_by('-date_suppression')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        locataires_ids = request.POST.getlist('locataires')
        
        if action == 'restaurer' and locataires_ids:
            # Restaurer les locataires sélectionnés
            locataires_a_restaurer = Locataire.objects.filter(id__in=locataires_ids, est_supprime=True)
            for locataire in locataires_a_restaurer:
                locataire.est_supprime = False
                locataire.date_suppression = None
                locataire.save()
                
                # Log d'audit
                AuditLog.objects.create(
                    content_type=ContentType.objects.get_for_model(Locataire),
                    object_id=locataire.pk,
                    action='update',
                    details={
                        'old_data': {'est_supprime': True},
                        'new_data': {'est_supprime': False}
                    },
                    object_repr=str(locataire),
                    user=request.user,
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
            
            messages.success(request, f"{locataires_a_restaurer.count()} locataire(s) restauré(s) avec succès.")
            return redirect('proprietes:corbeille_locataires')
            
        elif action == 'supprimer_definitivement' and locataires_ids:
            # Suppression définitive avec vérifications de sécurité
            locataires_a_supprimer = Locataire.objects.filter(id__in=locataires_ids, est_supprime=True)
            locataires_supprimes_avec_succes = []
            locataires_avec_contrats_actifs = []
            
            for locataire in locataires_a_supprimer:
                # Vérifier s'il a des contrats actifs
                if locataire.a_des_contrats_actifs():
                    locataires_avec_contrats_actifs.append(locataire)
                    continue
                
                # Log d'audit avant suppression
                old_data = {f.name: getattr(locataire, f.name) for f in locataire._meta.fields}
                AuditLog.objects.create(
                    content_type=ContentType.objects.get_for_model(Locataire),
                    object_id=locataire.pk,
                    action='delete',
                    details={
                        'old_data': old_data,
                        'new_data': None
                    },
                    object_repr=str(locataire),
                    user=request.user,
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
                locataire.delete()
                locataires_supprimes_avec_succes.append(locataire)
            
            # Messages de résultat
            if locataires_supprimes_avec_succes:
                messages.success(request, f"{len(locataires_supprimes_avec_succes)} locataire(s) supprimé(s) définitivement.")
            
            if locataires_avec_contrats_actifs:
                noms_locataires = [loc.get_nom_complet() for loc in locataires_avec_contrats_actifs]
                messages.error(
                    request, 
                    f"Impossible de supprimer définitivement {len(locataires_avec_contrats_actifs)} locataire(s) "
                    f"car ils ont des contrats actifs : {', '.join(noms_locataires)}. "
                    f"Veuillez d'abord résilier ou transférer leurs contrats."
                )
            
            return redirect('proprietes:corbeille_locataires')
    
    # Analyser les locataires pour les statistiques
    locataires_avec_contrats_actifs = []
    locataires_restaurables = []
    
    for locataire in locataires_supprimes:
        if locataire.a_des_contrats_actifs():
            locataires_avec_contrats_actifs.append(locataire)
        else:
            locataires_restaurables.append(locataire)
    
    # Pagination
    paginator = Paginator(locataires_supprimes, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'locataires': page_obj,
        'page_obj': page_obj,
        'locataires_supprimes': locataires_supprimes,
        'locataires_avec_contrats': locataires_avec_contrats_actifs,
        'locataires_restaurables': locataires_restaurables,
    }
    
    return render(request, 'proprietes/corbeille_locataires.html', context)


@login_required
def desactiver_locataire(request, pk):
    # Vérification des permissions : Seul PRIVILEGE peut désactiver
    from core.utils import check_group_permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE'], 'modify')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('proprietes:locataires_liste')
    locataire = get_object_or_404(Locataire, pk=pk)
    if request.method == 'POST':
        if locataire.statut == 'actif':
            locataire.statut = 'inactif'
            messages.success(request, "Locataire désactivé avec succès.")
        else:
            locataire.statut = 'actif'
            messages.success(request, "Locataire réactivé avec succès.")
        locataire.save()
        return redirect('proprietes:locataires_liste')
    return render(request, 'proprietes/confirm_desactiver_locataire.html', {'locataire': locataire})


# API pour les calculs en temps réel
@login_required
def api_calcul_loyer_net(request, propriete_id):
    """
    API pour calculer le loyer net après déduction des charges bailleur
    """
    try:
        propriete = get_object_or_404(Propriete, pk=propriete_id)
        
        loyer_total = propriete.get_loyer_total()
        charges_bailleur = propriete.get_charges_bailleur_en_cours()
        loyer_net = propriete.get_loyer_net_apres_deduction()
        
        return JsonResponse({
            'success': True,
            'loyer_total': float(loyer_total),
            'charges_bailleur': float(charges_bailleur),
            'loyer_net': float(loyer_net),
            'propriete_titre': propriete.titre
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
def ajouter_charge_bailleur_rapide(request):
    # Vérification des permissions : PRIVILEGE et ADMINISTRATION peuvent ajouter
    from core.utils import check_group_permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE'], 'add')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('proprietes:liste')
    
    if request.method == 'POST':
        propriete_id = request.POST.get('propriete_id')
        titre = request.POST.get('titre')
        montant = request.POST.get('montant')
        type_charge = request.POST.get('type_charge')
        if propriete_id and titre and montant and type_charge:
            propriete = Propriete.objects.get(pk=propriete_id)
            charge = ChargesBailleur.objects.create(
                propriete=propriete,
                titre=titre,
                montant=montant,
                type_charge=type_charge,
                statut='en_attente',
                cree_par=request.user
            )
            messages.success(request, f'Charge "{titre}" ajoutée avec succès !')
            # Rediriger vers l'ajout de paiement avec le contrat lié à la propriété
            contrat = propriete.contrats.filter(est_actif=True).first()
            if contrat:
                return redirect(f'/paiements/ajouter/?contrat={contrat.id}')
            else:
                return redirect('/paiements/ajouter/')
        else:
            messages.error(request, "Tous les champs sont obligatoires pour ajouter une charge.")
            return redirect(request.META.get('HTTP_REFERER', '/paiements/ajouter/'))


@login_required
def supprimer_propriete(request, pk):
    # Vérification des permissions : Seul PRIVILEGE peut supprimer
    from core.utils import check_group_permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE'], 'delete')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('proprietes:liste')
    
    propriete = get_object_or_404(Propriete, pk=pk)
    
    if request.method == 'POST':
        try:
            # Suppression logique
            old_data = {f.name: getattr(propriete, f.name) for f in propriete._meta.fields}
            propriete.est_supprime = True
            propriete.date_suppression = timezone.now()
            propriete.save()
            
            # Log d'audit
            AuditLog.objects.create(
                content_type=ContentType.objects.get_for_model(Propriete),
                object_id=propriete.pk,
                action='DELETE',
                old_data=old_data,
                new_data={'est_supprime': True, 'date_suppression': str(timezone.now())},
                user=request.user,
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            messages.success(request, f"Propriété {propriete.titre} supprimée avec succès.")
            return redirect('proprietes:liste')
            
        except ProtectedError as e:
            messages.error(request, f"Impossible de supprimer cette propriété : {str(e)}")
            return redirect('proprietes:liste')
    
    context = {
        'propriete': propriete,
    }
    return render(request, 'proprietes/confirm_supprimer_propriete.html', context)


@login_required
def supprimer_type_bien(request, pk):
    # Vérification des permissions : Seul PRIVILEGE peut supprimer
    from core.utils import check_group_permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE'], 'delete')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('proprietes:types_biens_liste')
    
    type_bien = get_object_or_404(TypeBien, pk=pk)
    
    if request.method == 'POST':
        try:
            # Suppression logique
            old_data = {f.name: getattr(type_bien, f.name) for f in type_bien._meta.fields}
            type_bien.est_supprime = True
            type_bien.date_suppression = timezone.now()
            type_bien.save()
            
            # Log d'audit
            AuditLog.objects.create(
                content_type=ContentType.objects.get_for_model(TypeBien),
                object_id=type_bien.pk,
                action='DELETE',
                old_data=old_data,
                new_data={'est_supprime': True, 'date_suppression': str(timezone.now())},
                user=request.user,
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            messages.success(request, f"Type de bien {type_bien.nom} supprimé avec succès.")
            return redirect('proprietes:types_biens_liste')
            
        except ProtectedError as e:
            messages.error(request, f"Impossible de supprimer ce type de bien : {str(e)}")
            return redirect('proprietes:types_biens_liste')
    
    context = {
        'type_bien': type_bien,
    }
    return render(request, 'proprietes/confirm_supprimer_type_bien.html', context)


@login_required
def supprimer_charge_bailleur(request, pk):
    # Vérification des permissions : Seul PRIVILEGE peut supprimer
    from core.utils import check_group_permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE'], 'delete')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('proprietes:charges_bailleur_liste')
    
    charge = get_object_or_404(ChargesBailleur, pk=pk)
    
    if request.method == 'POST':
        try:
            # Suppression logique
            old_data = {f.name: getattr(charge, f.name) for f in charge._meta.fields}
            charge.est_supprime = True
            charge.date_suppression = timezone.now()
            charge.save()
            
            # Log d'audit
            AuditLog.objects.create(
                content_type=ContentType.objects.get_for_model(ChargesBailleur),
                object_id=charge.pk,
                action='DELETE',
                old_data=old_data,
                new_data={'est_supprime': True, 'date_suppression': str(timezone.now())},
                user=request.user,
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            messages.success(request, f"Charge bailleur {charge.libelle} supprimée avec succès.")
            return redirect('proprietes:charges_bailleur_liste')
            
        except ProtectedError as e:
            messages.error(request, f"Impossible de supprimer cette charge bailleur : {str(e)}")
            return redirect('proprietes:charges_bailleur_liste')
    
    context = {
        'charge': charge,
    }
    return render(request, 'proprietes/confirm_supprimer_charge_bailleur.html', context)


@login_required
def recherche_avancee_bailleurs(request):
    """Recherche avancée des bailleurs avec filtres."""
    from core.utils import check_group_permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'CONTROLES', 'CAISSE'], 'view')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('proprietes:bailleurs_liste')
    
    # Récupérer les paramètres de recherche
    nom = request.GET.get('nom', '')
    ville = request.GET.get('ville', '')
    statut_paiement = request.GET.get('statut_paiement', '')
    annee = request.GET.get('annee', '')
    
    # Construire la requête
    bailleurs = Bailleur.objects.all()
    
    if nom:
        bailleurs = bailleurs.filter(
            models.Q(nom__icontains=nom) | 
            models.Q(prenom__icontains=nom) |
            models.Q(code_bailleur__icontains=nom)
        )
    
    if ville:
        bailleurs = bailleurs.filter(proprietes__ville__icontains=ville).distinct()
    
    # Filtrer par statut de paiement
    if statut_paiement:
        from paiements.models import Paiement
        if statut_paiement == 'avec_paiements':
            bailleurs = bailleurs.filter(
                proprietes__contrats__paiements__isnull=False
            ).distinct()
        elif statut_paiement == 'sans_paiements':
            bailleurs = bailleurs.filter(
                proprietes__contrats__paiements__isnull=True
            ).distinct()
    
    # Filtrer par année
    if annee:
        from paiements.models import Paiement
        bailleurs = bailleurs.filter(
            proprietes__contrats__paiements__date_paiement__year=annee
        ).distinct()
    
    # Pagination
    paginator = Paginator(bailleurs, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistiques globales
    total_revenus = sum(b.get_total_revenus_mensuels() for b in bailleurs)
    total_proprietes = sum(b.get_proprietes_count() for b in bailleurs)
    
    context = {
        'page_obj': page_obj,
        'bailleurs': page_obj,
        'total_revenus': total_revenus,
        'total_proprietes': total_proprietes,
        'filtres': {
            'nom': nom,
            'ville': ville,
            'statut_paiement': statut_paiement,
            'annee': annee,
        },
        'annees': range(2020, timezone.now().year + 1),
    }
    
    return render(request, 'proprietes/recherche_avancee_bailleurs.html', context)


@login_required
def recherche_avancee_locataires(request):
    """Recherche avancée des locataires avec filtres."""
    from core.utils import check_group_permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'CONTROLES', 'CAISSE'], 'view')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('proprietes:locataires_liste')
    
    # Récupérer les paramètres de recherche
    nom = request.GET.get('nom', '')
    ville = request.GET.get('ville', '')
    statut_paiement = request.GET.get('statut_paiement', '')
    annee = request.GET.get('annee', '')
    
    # Construire la requête
    locataires = Locataire.objects.all()
    
    if nom:
        locataires = locataires.filter(
            models.Q(nom__icontains=nom) | 
            models.Q(prenom__icontains=nom) |
            models.Q(code_locataire__icontains=nom)
        )
    
    if ville:
        locataires = locataires.filter(contrats__propriete__ville__icontains=ville).distinct()
    
    # Filtrer par statut de paiement
    if statut_paiement:
        from paiements.models import Paiement
        if statut_paiement == 'avec_paiements':
            locataires = locataires.filter(
                contrats__paiements__isnull=False
            ).distinct()
        elif statut_paiement == 'sans_paiements':
            locataires = locataires.filter(
                contrats__paiements__isnull=True
            ).distinct()
        elif statut_paiement == 'en_retard':
            # Filtrer les locataires en retard de paiement
            locataires_en_retard = []
            for locataire in locataires:
                if locataire.get_retard_paiement() > 0:
                    locataires_en_retard.append(locataire.pk)
            locataires = locataires.filter(pk__in=locataires_en_retard)
    
    # Filtrer par année
    if annee:
        from paiements.models import Paiement
        locataires = locataires.filter(
            contrats__paiements__date_paiement__year=annee
        ).distinct()
    
    # Pagination
    paginator = Paginator(locataires, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistiques globales
    total_loyers = sum(l.get_total_loyer_mensuel() for l in locataires)
    total_contrats_actifs = sum(l.get_contrats_actifs_count() for l in locataires)
    
    context = {
        'page_obj': page_obj,
        'locataires': page_obj,
        'total_loyers': total_loyers,
        'total_contrats_actifs': total_contrats_actifs,
        'filtres': {
            'nom': nom,
            'ville': ville,
            'statut_paiement': statut_paiement,
            'annee': annee,
        },
        'annees': range(2020, timezone.now().year + 1),
    }
    
    return render(request, 'proprietes/recherche_avancee_locataires.html', context)

# ========================================
# VUES POUR LA GESTION DES PHOTOS
# ========================================

class PhotoListView(LoginRequiredMixin, ListView):
    """Vue pour afficher la liste des photos d'une propriété"""
    model = Photo
    template_name = 'proprietes/photo_list.html'
    context_object_name = 'photos'
    
    def get_queryset(self):
        propriete_id = self.kwargs.get('propriete_id')
        return Photo.objects.filter(propriete_id=propriete_id).order_by('ordre')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        propriete_id = self.kwargs.get('propriete_id')
        context['propriete'] = get_object_or_404(Propriete, id=propriete_id)
        return context

class PhotoCreateView(LoginRequiredMixin, CreateView):
    """Vue pour ajouter une nouvelle photo"""
    model = Photo
    form_class = PhotoForm
    template_name = 'proprietes/photo_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        propriete_id = self.kwargs.get('propriete_id')
        context['propriete'] = get_object_or_404(Propriete, id=propriete_id)
        return context
    
    def form_valid(self, form):
        propriete_id = self.kwargs.get('propriete_id')
        propriete = get_object_or_404(Propriete, id=propriete_id)
        form.instance.propriete = propriete
        form.instance.cree_par = self.request.user
        
        # Si c'est la première photo, la définir comme principale
        if not Photo.objects.filter(propriete=propriete).exists():
            form.instance.est_principale = True
        
        return super().form_valid(form)
    
    def get_success_url(self):
        propriete_id = self.kwargs.get('propriete_id')
        return reverse_lazy('proprietes:photo_list', kwargs={'propriete_id': propriete_id})

class PhotoUpdateView(LoginRequiredMixin, UpdateView):
    """Vue pour modifier une photo existante"""
    model = Photo
    form_class = PhotoForm
    template_name = 'proprietes/photo_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['propriete'] = self.object.propriete
        return context
    
    def get_success_url(self):
        return reverse_lazy('proprietes:photo_list', kwargs={'propriete_id': self.object.propriete.id})

class PhotoDeleteView(LoginRequiredMixin, DeleteView):
    """Vue pour supprimer une photo"""
    model = Photo
    template_name = 'proprietes/photo_confirm_delete.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['propriete'] = self.object.propriete
        return context
    
    def get_success_url(self):
        return reverse_lazy('proprietes:photo_list', kwargs={'propriete_id': self.object.propriete.id})

class PhotoMultipleUploadView(LoginRequiredMixin, View):
    """Vue pour l'upload multiple de photos"""
    template_name = 'proprietes/photo_multiple_upload.html'
    
    def get(self, request, propriete_id):
        propriete = get_object_or_404(Propriete, id=propriete_id)
        form = PhotoMultipleForm()
        return render(request, self.template_name, {
            'form': form,
            'propriete': propriete
        })
    
    def post(self, request, propriete_id):
        propriete = get_object_or_404(Propriete, id=propriete_id)
        form = PhotoMultipleForm(request.POST, request.FILES)
        
        if form.is_valid():
            images = form.cleaned_data['images']
            photos_crees = []
            
            # Récupérer l'ordre maximum actuel
            max_ordre = Photo.objects.filter(propriete=propriete).aggregate(
                max_ordre=models.Max('ordre')
            )['max_ordre'] or 0
            
            for i, image in enumerate(images):
                # Créer un titre par défaut
                titre = f"Photo {max_ordre + i + 1}"
                
                # Créer la photo
                photo = Photo.objects.create(
                    propriete=propriete,
                    image=image,
                    titre=titre,
                    ordre=max_ordre + i + 1,
                    est_principale=(max_ordre + i == 0)  # Première photo = principale
                )
                photos_crees.append(photo)
            
            messages.success(
                request, 
                f"{len(photos_crees)} photo(s) ajoutée(s) avec succès à la propriété {propriete.adresse}"
            )
            
            return redirect('proprietes:photo_list', propriete_id=propriete_id)
        
        return render(request, self.template_name, {
            'form': form,
            'propriete': propriete
        })

class PhotoReorderView(LoginRequiredMixin, View):
    """Vue pour réorganiser l'ordre des photos"""
    
    def post(self, request, propriete_id):
        propriete = get_object_or_404(Propriete, id=propriete_id)
        photo_orders = request.POST.getlist('photo_order[]')
        
        try:
            for i, photo_id in enumerate(photo_orders):
                photo = Photo.objects.get(id=photo_id, propriete=propriete)
                photo.ordre = i
                photo.save()
            
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

class PhotoGalleryView(LoginRequiredMixin, DetailView):
    """Vue pour afficher la galerie photos d'une propriété"""
    model = Propriete
    template_name = 'proprietes/photo_gallery.html'
    context_object_name = 'propriete'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['photos'] = self.object.photos.all().order_by('ordre')
        context['photo_principale'] = self.object.photos.filter(est_principale=True).first()
        return context

# ========================================
# VUES AJAX POUR LA GESTION DES PHOTOS
# ========================================

class PhotoSetMainView(LoginRequiredMixin, View):
    """Vue AJAX pour définir une photo comme principale"""
    
    def post(self, request, photo_id):
        try:
            photo = get_object_or_404(Photo, id=photo_id)
            
            # Vérifier que l'utilisateur a accès à cette propriété
            if not request.user.has_perm('proprietes.view_propriete', photo.propriete):
                return JsonResponse({'status': 'error', 'message': 'Permission refusée'})
            
            # Désactiver toutes les autres photos principales
            Photo.objects.filter(
                propriete=photo.propriete,
                est_principale=True
            ).update(est_principale=False)
            
            # Activer cette photo comme principale
            photo.est_principale = True
            photo.save()
            
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

class PhotoDeleteAjaxView(LoginRequiredMixin, View):
    """Vue AJAX pour supprimer une photo"""
    
    def post(self, request, photo_id):
        try:
            photo = get_object_or_404(Photo, id=photo_id)
            
            # Vérifier que l'utilisateur a accès à cette propriété
            if not request.user.has_perm('proprietes.view_propriete', photo.propriete):
                return JsonResponse({'status': 'error', 'message': 'Permission refusée'})
            
            propriete_id = photo.propriete.id
            photo.delete()
            
            # Si c'était la photo principale, définir la première comme principale
            if not Photo.objects.filter(propriete_id=propriete_id, est_principale=True).exists():
                premiere_photo = Photo.objects.filter(propriete_id=propriete_id).first()
                if premiere_photo:
                    premiere_photo.est_principale = True
                    premiere_photo.save()
            
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

# Vues pour la gestion des documents
@login_required
def document_list(request):
    """Vue pour lister tous les documents avec fonctionnalités avancées pour les utilisateurs privilégiés."""
    # Vérifier les permissions utilisateur
    is_privilege_user = hasattr(request.user, 'groupe_travail') and request.user.groupe_travail and request.user.groupe_travail.nom == 'PRIVILEGE'
    
    # Base queryset avec optimisations
    documents = Document.objects.select_related(
        'propriete', 'bailleur', 'locataire', 'cree_par'
    ).prefetch_related('propriete__type_bien')
    
    # Filtrer les documents confidentiels pour les utilisateurs non privilégiés
    if not is_privilege_user:
        documents = documents.filter(confidentiel=False)
    
    # Filtres de recherche
    form = DocumentSearchForm(request.GET)
    if form.is_valid():
        search = form.cleaned_data.get('search')
        type_document = form.cleaned_data.get('type_document')
        statut = form.cleaned_data.get('statut')
        propriete = form.cleaned_data.get('propriete')
        date_debut = form.cleaned_data.get('date_debut')
        date_fin = form.cleaned_data.get('date_fin')
        
        if search:
            documents = documents.filter(
                Q(nom__icontains=search) |
                Q(description__icontains=search) |
                Q(tags__icontains=search)
            )
        
        if type_document:
            documents = documents.filter(type_document=type_document)
        
        if statut:
            documents = documents.filter(statut=statut)
        
        if propriete:
            documents = documents.filter(propriete=propriete)
        
        if date_debut:
            documents = documents.filter(date_creation__date__gte=date_debut)
        
        if date_fin:
            documents = documents.filter(date_creation__date__lte=date_fin)
    
    # Statistiques avancées pour les utilisateurs privilégiés
    stats = {}
    if is_privilege_user:
        stats = {
            'total_documents': documents.count(),
            'documents_expires': documents.filter(
                date_expiration__lt=timezone.now().date()
            ).count(),
            'documents_confidentiels': documents.filter(confidentiel=True).count(),
            'documents_par_type': documents.values('type_document').annotate(
                count=Count('id')
            ).order_by('-count'),
            'documents_par_statut': documents.values('statut').annotate(
                count=Count('id')
            ).order_by('-count'),
            'documents_recents': documents.filter(
                date_creation__gte=timezone.now() - timedelta(days=30)
            ).count(),
        }
    
    # Pagination avec plus d'éléments pour les utilisateurs privilégiés
    items_per_page = 50 if is_privilege_user else 20
    paginator = Paginator(documents.order_by('-date_creation'), items_per_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_form': form,
        'is_privilege_user': is_privilege_user,
        'stats': stats,
        'total_documents': documents.count(),
        'documents_expires': documents.filter(
            date_expiration__lt=timezone.now().date()
        ).count(),
    }
    
    # Template différent pour les utilisateurs privilégiés
    template_name = 'proprietes/documents/document_list_privilege.html' if is_privilege_user else 'proprietes/documents/document_list.html'
    
    return render(request, template_name, context)


@login_required
def document_detail(request, pk):
    """Vue pour afficher le détail d'un document avec fonctionnalités avancées."""
    document = get_object_or_404(Document, pk=pk)
    
    # Vérifier les permissions utilisateur
    is_privilege_user = hasattr(request.user, 'groupe_travail') and request.user.groupe_travail and request.user.groupe_travail.nom == 'PRIVILEGE'
    
    # Vérifier l'accès aux documents confidentiels
    if document.confidentiel and not is_privilege_user:
        messages.error(request, "Vous n'avez pas les permissions pour consulter ce document confidentiel.")
        return redirect('proprietes:document_list')
    
    # Informations supplémentaires pour les utilisateurs privilégiés
    extra_info = {}
    if is_privilege_user:
        # Historique des modifications (si implémenté)
        extra_info['can_edit'] = True
        extra_info['can_delete'] = True
        extra_info['file_size'] = document.taille_fichier if hasattr(document, 'taille_fichier') else None
        
        # Documents liés de la même propriété
        if document.propriete:
            extra_info['related_documents'] = Document.objects.filter(
                propriete=document.propriete
            ).exclude(pk=document.pk).select_related('cree_par')[:5]
        
        # Métadonnées du fichier
        if document.fichier:
            import os
            extra_info['file_info'] = {
                'name': os.path.basename(document.fichier.name),
                'extension': os.path.splitext(document.fichier.name)[1],
                'url': document.fichier.url,
            }
    
    context = {
        'document': document,
        'is_privilege_user': is_privilege_user,
        'extra_info': extra_info,
    }
    
    # Template différent pour les utilisateurs privilégiés
    template_name = 'proprietes/documents/document_detail_privilege.html' if is_privilege_user else 'proprietes/documents/document_detail.html'
    
    return render(request, template_name, context)


@login_required
def document_create(request):
    """Vue pour créer un nouveau document."""
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.cree_par = request.user
            document.save()
            
            messages.success(
                request,
                f'Document "{document.nom}" créé avec succès!'
            )
            
            return redirect('proprietes:document_detail', pk=document.pk)
    else:
        form = DocumentForm()
    
    context = {
        'form': form,
        'title': 'Ajouter un document',
        'submit_text': 'Créer le document'
    }
    
    return render(request, 'proprietes/documents/document_form.html', context)


@login_required
def document_update(request, pk):
    """Vue pour modifier un document existant."""
    document = get_object_or_404(Document, pk=pk)
    
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES, instance=document)
        if form.is_valid():
            form.save()
            
            messages.success(
                request,
                f'Document "{document.nom}" modifié avec succès!'
            )
            
            return redirect('proprietes:document_detail', pk=document.pk)
    else:
        form = DocumentForm(instance=document)
    
    context = {
        'form': form,
        'document': document,
        'title': f'Modifier le document "{document.nom}"',
        'submit_text': 'Mettre à jour'
    }
    
    return render(request, 'proprietes/documents/document_form.html', context)


@login_required
def document_delete(request, pk):
    """Vue pour supprimer un document."""
    document = get_object_or_404(Document, pk=pk)
    
    if request.method == 'POST':
        nom_document = document.nom
        document.delete()
        
        messages.success(
            request,
            f'Document "{nom_document}" supprimé avec succès!'
        )
        
        return redirect('proprietes:document_list')
    
    context = {
        'document': document,
    }
    
    return render(request, 'proprietes/documents/document_confirm_delete.html', context)


@login_required
def document_download(request, pk):
    """Vue pour télécharger un document."""
    document = get_object_or_404(Document, pk=pk)
    
    # Vérifier que le fichier existe
    if not document.fichier:
        messages.error(request, "Ce document n'a pas de fichier associé.")
        return redirect('proprietes:document_list')
    
    # Vérifier les permissions si le document est confidentiel
    if document.confidentiel:
        # Vérifier si l'utilisateur est privilégié
        is_privilege_user = (hasattr(request.user, 'groupe_travail') and 
                           request.user.groupe_travail and 
                           request.user.groupe_travail.nom == 'PRIVILEGE')
        
        if not is_privilege_user:
            messages.error(request, "Vous n'avez pas l'autorisation de télécharger ce document confidentiel.")
            return redirect('proprietes:document_list')
    
    try:
        # Utiliser FileResponse pour un téléchargement correct
        response = FileResponse(
            open(document.fichier.path, 'rb'),
            as_attachment=True,
            filename=os.path.basename(document.fichier.name)
        )
        
        # Headers de sécurité
        response['X-Content-Type-Options'] = 'nosniff'
        
        # Log du téléchargement
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Document {document.pk} ({document.nom}) téléchargé par {request.user.username}")
        
        return response
        
    except FileNotFoundError:
        messages.error(request, f"Le fichier '{document.fichier.name}' est introuvable sur le serveur.")
        return redirect('proprietes:document_list')
    except Exception as e:
        messages.error(request, f"Erreur lors du téléchargement : {str(e)}")
        return redirect('proprietes:document_list')


# ========================================
# VUES POUR LES FORMULAIRES SPÉCIALISÉS
# ========================================

@login_required
def diagnostic_form_view(request):
    """Vue pour le formulaire de diagnostics."""
    from core.utils import check_group_permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE'], 'add')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('proprietes:liste')
    
    if request.method == 'POST':
        form = DiagnosticForm(request.POST, request.FILES)
        if form.is_valid():
            form.save_diagnostics(user=request.user)
            messages.success(
                request, 
                f'Diagnostics enregistrés avec succès pour la propriété "{form.cleaned_data["propriete"]}"!'
            )
            return redirect('proprietes:detail', pk=form.cleaned_data['propriete'].pk)
    else:
        form = DiagnosticForm()
    
    context = {
        'form': form,
        'title': 'Formulaire de Diagnostics Immobiliers'
    }
    return render(request, 'proprietes/formulaires_specialises/diagnostic_form.html', context)


@login_required
def assurance_form_view(request):
    """Vue pour le formulaire d'assurances."""
    from core.utils import check_group_permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE'], 'add')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('proprietes:liste')
    
    if request.method == 'POST':
        form = AssuranceForm(request.POST, request.FILES)
        if form.is_valid():
            form.save_assurances(user=request.user)
            messages.success(
                request, 
                f'Assurances enregistrées avec succès pour la propriété "{form.cleaned_data["propriete"]}"!'
            )
            return redirect('proprietes:detail', pk=form.cleaned_data['propriete'].pk)
    else:
        form = AssuranceForm()
    
    context = {
        'form': form,
        'title': 'Formulaire d\'Assurances Immobilières'
    }
    return render(request, 'proprietes/formulaires_specialises/assurance_form.html', context)


@login_required
def etat_lieux_form_view(request):
    """Vue pour le formulaire d'état des lieux."""
    from core.utils import check_group_permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE'], 'add')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('proprietes:liste')
    
    if request.method == 'POST':
        form = EtatLieuxForm(request.POST, request.FILES)
        if form.is_valid():
            form.save_etat_lieux(user=request.user)
            messages.success(
                request, 
                f'État des lieux enregistré avec succès pour la propriété "{form.cleaned_data["propriete"]}"!'
            )
            return redirect('proprietes:detail', pk=form.cleaned_data['propriete'].pk)
    else:
        form = EtatLieuxForm()
    
    context = {
        'form': form,
        'title': 'Formulaire d\'État des Lieux'
    }
    return render(request, 'proprietes/formulaires_specialises/etat_lieux_form.html', context)

def proprietes_dashboard(request):
    """
    Dashboard principal des propriétés avec vue d'ensemble et accès contextuel aux listes
    """
    from django.db.models import Q, Count
    from django.utils import timezone
    from contrats.models import Contrat
    
    # Statistiques générales
    total_proprietes = Propriete.objects.filter(is_deleted=False).count()
    
    # Propriétés louées (avec contrats actifs)
    proprietes_louees = Propriete.objects.filter(
        is_deleted=False,
        contrats__est_actif=True,
        contrats__est_resilie=False
    ).distinct().count()
    
    # Propriétés disponibles (pas de contrats actifs et marquées comme disponibles)
    proprietes_disponibles = Propriete.objects.filter(
        is_deleted=False,
        disponible=True
    ).exclude(
        contrats__est_actif=True,
        contrats__est_resilie=False
    ).count()
    
    # Propriétés en construction (état 'a_renover' ou similaire)
    proprietes_en_construction = Propriete.objects.filter(
        is_deleted=False,
        etat='a_renover'
    ).count()
    
    # Top propriétés par activité (NON par loyer pour la confidentialité)
    top_proprietes = Propriete.objects.filter(
        is_deleted=False
    ).annotate(
        nombre_contrats=Count('contrats', filter=Q(contrats__est_actif=True))
    ).order_by('-nombre_contrats')[:5]
    
    # Propriétés par ville
    proprietes_par_ville = Propriete.objects.filter(
        is_deleted=False
    ).values('ville').annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    # Propriétés récentes
    proprietes_recentes = Propriete.objects.filter(
        is_deleted=False
    ).order_by('-date_creation')[:5]
    
    # Propriétés nécessitant attention
    proprietes_attention = Propriete.objects.filter(
        is_deleted=False
    ).filter(
        Q(disponible=True) | 
        Q(contrats__isnull=True) |
        Q(contrats__date_fin__lt=timezone.now().date())
    )[:5]
    
    # Statistiques des bailleurs et locataires
    total_bailleurs = Bailleur.objects.filter(is_deleted=False).count()
    bailleurs_actifs = Bailleur.objects.filter(is_deleted=False, actif=True).count()
    
    total_locataires = Locataire.objects.filter(is_deleted=False).count()
    locataires_actifs = Locataire.objects.filter(is_deleted=False, statut='actif').count()
    
    context = {
        'total_proprietes': total_proprietes,
        'proprietes_louees': proprietes_louees,
        'proprietes_disponibles': proprietes_disponibles,
        'proprietes_en_construction': proprietes_en_construction,
        'top_proprietes': top_proprietes,
        'proprietes_par_ville': proprietes_par_ville,
        'proprietes_recentes': proprietes_recentes,
        'proprietes_attention': proprietes_attention,
        'total_bailleurs': total_bailleurs,
        'bailleurs_actifs': bailleurs_actifs,
        'total_locataires': total_locataires,
        'locataires_actifs': locataires_actifs,
    }
    
    return render(request, 'proprietes/dashboard.html', context)

# ============================================================================
# VUES POUR LA GESTION DES PIÈCES
# ============================================================================

@login_required
def gestion_pieces(request, propriete_id):
    """Vue pour la gestion des pièces d'une propriété."""
    propriete = get_object_or_404(Propriete, pk=propriete_id, is_deleted=False)
    
    # Vérifier que la propriété est de type "unités multiples"
    if propriete.type_gestion != 'unites_multiples':
        messages.warning(request, "La gestion des pièces n'est disponible que pour les propriétés avec unités multiples.")
        return redirect('proprietes:detail', pk=propriete_id)
    
    # Récupérer les pièces de la propriété
    pieces = propriete.pieces.filter(is_deleted=False)
    
    # Appliquer les filtres
    statut = request.GET.get('statut')
    type_piece = request.GET.get('type_piece')
    recherche = request.GET.get('recherche')
    
    if statut:
        pieces = pieces.filter(statut=statut)
    
    if type_piece:
        pieces = pieces.filter(type_piece=type_piece)
    
    if recherche:
        pieces = pieces.filter(
            Q(nom__icontains=recherche) |
            Q(description__icontains=recherche) |
            Q(numero_piece__icontains=recherche)
        )
    
    # Statistiques des pièces
    from .services import GestionPiecesService
    stats = GestionPiecesService.get_statistiques_pieces(propriete_id)
    
    # Créer le formulaire pour l'ajout de pièces
    from .forms import PieceForm
    form = PieceForm(propriete=propriete)
    
    context = {
        'propriete': propriete,
        'pieces': pieces,
        'stats': stats,
        'form': form,
        'filtres': {
            'statut': statut,
            'type_piece': type_piece,
            'recherche': recherche
        }
    }
    
    return render(request, 'proprietes/pieces_gestion.html', context)


@login_required
def creer_piece(request, propriete_id):
    """Vue pour créer une nouvelle pièce."""
    from .forms import PieceForm
    
    propriete = get_object_or_404(Propriete, pk=propriete_id, is_deleted=False)
    
    # Vérifier que la propriété est de type "unités multiples"
    if propriete.type_gestion != 'unites_multiples':
        messages.warning(request, "La création de pièces n'est disponible que pour les propriétés avec unités multiples.")
        return redirect('proprietes:detail', pk=propriete_id)
    
    if request.method == 'POST':
        form = PieceForm(propriete=propriete, data=request.POST)
        if form.is_valid():
            try:
                piece = form.save(commit=False)
                piece.propriete = propriete
                piece.save()
                
                messages.success(request, f'Pièce "{piece.nom}" créée avec succès.')
                return redirect('proprietes:gestion_pieces', propriete_id=propriete_id)
                
            except Exception as e:
                messages.error(request, f'Erreur lors de la création de la pièce : {str(e)}')
        else:
            # Afficher les erreurs de validation
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = PieceForm(propriete=propriete)
    
    # Récupérer les pièces existantes pour l'affichage
    pieces = propriete.pieces.filter(is_deleted=False)
    
    # Statistiques des pièces
    from .services import GestionPiecesService
    stats = GestionPiecesService.get_statistiques_pieces(propriete_id)
    
    context = {
        'propriete': propriete,
        'pieces': pieces,
        'stats': stats,
        'form': form,
        'filtres': {
            'statut': None,
            'type_piece': None,
            'recherche': None
        }
    }
    
    return render(request, 'proprietes/pieces_gestion.html', context)


@login_required
def creer_pieces_auto(request, propriete_id):
    """Vue pour créer automatiquement les pièces d'une propriété."""
    propriete = get_object_or_404(Propriete, pk=propriete_id, is_deleted=False)
    
    try:
        from .services import GestionPiecesService
        
        pieces_crees = GestionPiecesService.creer_pieces_automatiques(propriete)
        
        messages.success(
            request, 
            f'{len(pieces_crees)} pièces créées automatiquement pour la propriété "{propriete.titre}".'
        )
        
    except Exception as e:
        messages.error(request, f'Erreur lors de la création automatique des pièces : {str(e)}')
    
    return redirect('proprietes:gestion_pieces', propriete_id=propriete_id)


@login_required
def planifier_renovation(request, propriete_id):
    """Vue pour planifier une rénovation de pièces."""
    propriete = get_object_or_404(Propriete, pk=propriete_id, is_deleted=False)
    
    if request.method == 'POST':
        pieces_ids = request.POST.getlist('pieces')
        date_debut = request.POST.get('date_debut_renovation')
        date_fin = request.POST.get('date_fin_renovation')
        motif = request.POST.get('motif_renovation')
        
        try:
            from .models import Piece
            from django.utils.dateparse import parse_date
            
            pieces = Piece.objects.filter(
                id__in=pieces_ids,
                propriete=propriete,
                is_deleted=False
            )
            
            for piece in pieces:
                piece.statut = 'en_renovation'
                piece.save()
            
            messages.success(
                request, 
                f'{len(pieces)} pièce(s) mise(s) en rénovation avec succès.'
            )
            
        except Exception as e:
            messages.error(request, f'Erreur lors de la planification de la rénovation : {str(e)}')
    
    return redirect('proprietes:gestion_pieces', propriete_id=propriete_id)


@login_required
def detail_piece(request, piece_id):
    """Vue pour afficher les détails d'une pièce."""
    from .models import Piece
    piece = get_object_or_404(Piece, pk=piece_id, is_deleted=False)
    
    context = {
        'piece': piece,
        'propriete': piece.propriete,
        'contrat_actuel': piece.get_contrat_actuel(),
        'locataire_actuel': piece.get_locataire_actuel(),
        'historique_contrats': piece.get_historique_contrats(),
        'statistiques': piece.get_statistiques_occupation()
    }
    
    return render(request, 'proprietes/piece_detail.html', context)


@login_required
def modifier_piece(request, piece_id):
    """Vue pour modifier une pièce."""
    from .models import Piece
    piece = get_object_or_404(Piece, pk=piece_id, is_deleted=False)
    
    if request.method == 'POST':
        piece.nom = request.POST.get('nom')
        piece.type_piece = request.POST.get('type_piece')
        piece.numero_piece = request.POST.get('numero_piece')
        piece.surface = request.POST.get('surface') if request.POST.get('surface') else None
        piece.description = request.POST.get('description')
        piece.statut = request.POST.get('statut')
        
        try:
            piece.save()
            messages.success(request, f'Pièce "{piece.nom}" modifiée avec succès.')
            return redirect('proprietes:detail_piece', piece_id=piece_id)
            
        except Exception as e:
            messages.error(request, f'Erreur lors de la modification de la pièce : {str(e)}')
    
    context = {
        'piece': piece,
        'propriete': piece.propriete
    }
    
    return render(request, 'proprietes/piece_form.html', context)


@login_required
def liberer_piece(request, piece_id):
    """Vue AJAX pour libérer une pièce."""
    from .models import Piece
    piece = get_object_or_404(Piece, pk=piece_id, is_deleted=False)
    
    try:
        # Vérifier si la pièce est actuellement louée
        contrat_actuel = piece.get_contrat_actuel()
        
        if contrat_actuel:
            # Marquer le contrat comme résilié
            contrat_actuel.est_resilie = True
            contrat_actuel.est_actif = False
            contrat_actuel.date_resiliation = timezone.now().date()
            contrat_actuel.save()
            
            # Désactiver les liaisons pièce-contrat
            contrat_actuel.pieces_contrat.filter(piece=piece).update(actif=False)
        
        # Marquer la pièce comme disponible
        piece.statut = 'disponible'
        piece.save()
        
        return JsonResponse({'success': True, 'message': 'Pièce libérée avec succès'})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def export_pieces(request, propriete_id):
    """Vue pour exporter les pièces d'une propriété."""
    propriete = get_object_or_404(Propriete, pk=propriete_id, is_deleted=False)
    pieces = propriete.pieces.filter(is_deleted=False)
    
    import csv
    from django.http import HttpResponse
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="pieces_{propriete.numero_propriete}.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Nom', 'Type', 'Numéro', 'Surface (m²)', 'Statut', 'Description'])
    
    for piece in pieces:
        writer.writerow([
            piece.nom,
            piece.get_type_piece_display(),
            piece.numero_piece or '',
            piece.surface or '',
            piece.get_statut_display(),
            piece.description or ''
        ])
    
    return response


# ============================================================================
# VUES AJAX POUR LA GESTION DES PIÈCES
# ============================================================================

@login_required
def api_pieces_disponibles(request, propriete_id):
    """API pour récupérer les pièces disponibles d'une propriété."""
    try:
        from .services import GestionPiecesService
        
        date_debut = request.GET.get('date_debut')
        date_fin = request.GET.get('date_fin')
        
        pieces = GestionPiecesService.get_pieces_disponibles(
            propriete_id, 
            date_debut, 
            date_fin
        )
        
        pieces_data = []
        for piece in pieces:
            pieces_data.append({
                'id': piece.id,
                'nom': piece.nom,
                'type_piece': piece.type_piece,
                'surface': float(piece.surface) if piece.surface else None,
                'numero_piece': piece.numero_piece
            })
        
        return JsonResponse({'pieces': pieces_data})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
def api_verifier_disponibilite(request):
    """API pour vérifier la disponibilité des pièces."""
    try:
        from .services import ValidationContratService
        
        propriete_id = request.POST.get('propriete_id')
        pieces_ids = request.POST.getlist('pieces')
        date_debut = request.POST.get('date_debut')
        date_fin = request.POST.get('date_fin')
        
        if not all([propriete_id, pieces_ids, date_debut, date_fin]):
            return JsonResponse({'error': 'Tous les paramètres sont requis'}, status=400)
        
        from django.utils.dateparse import parse_date
        date_debut = parse_date(date_debut)
        date_fin = parse_date(date_fin)
        
        disponible, conflits = ValidationContratService.verifier_disponibilite_pieces(
            propriete_id=int(propriete_id),
            pieces_ids=[int(pid) for pid in pieces_ids],
            date_debut=date_debut,
            date_fin=date_fin
        )
        
        return JsonResponse({
            'disponible': disponible,
            'conflits': conflits
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
