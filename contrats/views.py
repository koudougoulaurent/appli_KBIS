from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Contrat, Quittance, EtatLieux
from proprietes.models import Propriete, Locataire
from django.utils import timezone
from django.db import models
from django.db.models import ProtectedError
from core.models import AuditLog, ConfigurationEntreprise
from django.contrib.contenttypes.models import ContentType
from core.intelligent_views import IntelligentListView
from core.enhanced_list_view import EnhancedSearchMixin
from core.utils import get_context_with_entreprise_config
from utilisateurs.mixins import PrivilegeButtonsMixin
from utilisateurs.mixins_suppression import SuppressionGeneriqueView
from datetime import datetime, timedelta
from django.core.paginator import Paginator
from django.contrib.auth.decorators import user_passes_test
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, A5
from proprietes.models import Bailleur
from .models import RecuCaution, DocumentContrat, ResiliationContrat
from .forms import ResiliationContratForm, ContratForm
from django.db.models import Count, Q


class ContratListView(PrivilegeButtonsMixin, EnhancedSearchMixin, IntelligentListView):
    model = Contrat
    template_name = 'base_liste_intelligente.html'
    paginate_by = 20
    page_title = 'Contrats'
    page_icon = 'file-contract'
    add_url = 'contrats:ajouter'
    add_text = 'Ajouter un contrat'
    search_fields = ['numero_contrat', 'propriete__titre', 'locataire__nom', 'locataire__prenom', 'notes']
    filter_fields = ['est_actif', 'est_resilie', 'mode_paiement']
    default_sort = 'date_debut'
    columns = [
        {'field': 'numero_contrat', 'label': 'N° Contrat', 'sortable': True},
        {'field': 'propriete', 'label': 'Propriété', 'sortable': True},
        {'field': 'locataire', 'label': 'Locataire', 'sortable': True},
        {'field': 'date_debut', 'label': 'Début', 'sortable': True},
        {'field': 'date_fin', 'label': 'Fin', 'sortable': True},
        {'field': 'loyer_mensuel', 'label': 'Loyer', 'sortable': True},
        {'field': 'est_actif', 'label': 'Actif', 'sortable': True},
    ]
    actions = [
        {'url_name': 'contrats:detail', 'icon': 'eye', 'style': 'outline-primary', 'title': 'Voir'},
        {'url_name': 'contrats:modifier', 'icon': 'pencil', 'style': 'outline-warning', 'title': 'Modifier'},
        {'url_name': 'contrats:supprimer_contrat', 'icon': 'trash', 'style': 'outline-danger', 'title': 'Supprimer', 'condition': 'user.is_privilege_user'},
    ]
    sort_options = [
        {'value': 'date_debut', 'label': 'Début'},
        {'value': 'date_fin', 'label': 'Fin'},
        {'value': 'loyer_mensuel', 'label': 'Loyer'},
    ]
    
    def get_queryset(self):
        """
        Optimisation des requêtes de base de données
        """
        queryset = super().get_queryset()
        return queryset.select_related('propriete', 'locataire')
    
    def get_context_data(self, **kwargs):
        """
        Ajout de statistiques et d'informations supplémentaires au contexte
        """
        context = super().get_context_data(**kwargs)
        
        # Statistiques
        context['total_contrats'] = Contrat.objects.count()
        context['contrats_actifs'] = Contrat.objects.filter(est_actif=True).count()
        context['contrats_resilies'] = Contrat.objects.filter(est_resilie=True).count()
        context['contrats_inactifs'] = Contrat.objects.filter(est_actif=False, est_resilie=False).count()
        
        # Montant total des loyers mensuels
        from django.db.models import Sum
        context['montant_total_loyers'] = Contrat.objects.filter(est_actif=True).aggregate(
            total=Sum('loyer_mensuel')
        )['total'] or 0
        
        # Statistiques par mode de paiement
        context['stats_mode_paiement'] = Contrat.objects.values('mode_paiement').annotate(
            count=Sum('loyer_mensuel')
        ).order_by('-count')
        
        # Statistiques des propriétés disponibles
        from core.property_utils import get_proprietes_disponibles_global
        proprietes_disponibles = get_proprietes_disponibles_global()
        context['proprietes_disponibles_pour_location'] = proprietes_disponibles.count()
        
        return context
    
    def dispatch(self, request, *args, **kwargs):
        """
        Vérification des permissions avant l'affichage
        """
        # Vérification des permissions : PRIVILEGE, ADMINISTRATION, CONTROLES peuvent voir la liste
        from core.utils import check_group_permissions
        permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'CONTROLES', 'CAISSE'], 'view')
        if not permissions['allowed']:
            messages.error(request, permissions['message'])
            return redirect('core:dashboard')
        
        return super().dispatch(request, *args, **kwargs)

contrat_list = ContratListView.as_view()


@login_required
def detail_contrat(request, pk):
    """
    Vue de détail d'un contrat
    """
    # Vérification des permissions : PRIVILEGE, ADMINISTRATION, CONTROLES peuvent voir les détails
    from core.utils import check_group_permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'CONTROLES', 'CAISSE'], 'view')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('contrats:liste')
    
    contrat = get_object_or_404(Contrat, pk=pk)
    
    # Navigation contextuelle
    from core.navigation_helpers import ContractNavigationHelper
    context = {
        'contrat': contrat,
        'breadcrumbs': ContractNavigationHelper.get_contract_breadcrumbs(contrat),
        'quick_actions': ContractNavigationHelper.get_contract_quick_actions(contrat, request.user),
        'context_menu': ContractNavigationHelper.get_contract_context_menu(contrat, request.user),
    }
    return render(request, 'contrats/detail.html', context)


@login_required
def ajouter_contrat(request):
    """
    Vue pour ajouter un contrat avec génération automatique de PDF et reçu de caution
    """
    # Vérification des permissions : TOUS les groupes peuvent ajouter
    from core.utils import check_group_permissions
    from core.id_generator import IDGenerator
    
    # Tous les groupes peuvent ajouter des contrats
    # permissions = check_group_permissions(request.user, ['PRIVILEGE'], 'add')
    # if not permissions['allowed']:
    #     messages.error(request, permissions['message'])
    #     return redirect('contrats:liste')
    
    if request.method == 'POST':
        form = ContratForm(request.POST, request.FILES)
        if form.is_valid():
            contrat = form.save(commit=False)
            contrat.cree_par = request.user
            
            # Générer automatiquement le numéro unique de contrat
            if not contrat.numero_contrat:
                from django.utils.crypto import get_random_string
                contrat.numero_contrat = f"CT-{get_random_string(8).upper()}"
            
            contrat.save()
            
            # Mettre à jour automatiquement la disponibilité de la propriété
            # (maintenant géré automatiquement dans le modèle)
            
            # Vérifier si l'utilisateur veut créer un paiement de caution
            creer_paiement_caution = form.cleaned_data.get('creer_paiement_caution', False)
            creer_paiement_avance = form.cleaned_data.get('creer_paiement_avance', False)
            
            if creer_paiement_caution and contrat.depot_garantie:
                try:
                    # Créer automatiquement le paiement de caution
                    from paiements.models import Paiement
                    paiement_caution = Paiement.objects.create(
                        contrat=contrat,
                        type_paiement='caution',
                        montant=contrat.depot_garantie,
                        mode_paiement=form.cleaned_data.get('mode_paiement_caution', 'especes'),
                        date_paiement=form.cleaned_data.get('date_paiement_caution', timezone.now().date()),
                        cree_par=request.user,
                        notes=f"Paiement de caution créé automatiquement lors de la création du contrat {contrat.numero_contrat}"
                    )
                    
                    messages.success(
                        request,
                        f'Contrat "{contrat.numero_contrat}" ajouté avec succès! '
                        f'Le paiement de caution de {contrat.depot_garantie} F CFA a été créé automatiquement.'
                    )
                    
                except Exception as e:
                    messages.warning(
                        request,
                        f'Contrat "{contrat.numero_contrat}" ajouté avec succès, '
                        f'mais la création du paiement de caution a échoué: {str(e)}'
                    )
            
            if creer_paiement_avance and contrat.avance_loyer:
                try:
                    # Créer automatiquement le paiement d'avance de loyer
                    from paiements.models import Paiement
                    from decimal import Decimal
                    
                    # Convertir le montant d'avance en Decimal
                    montant_avance = Decimal(str(contrat.avance_loyer)) if contrat.avance_loyer else Decimal('0')
                    
                    paiement_avance = Paiement.objects.create(
                        contrat=contrat,
                        type_paiement='avance',
                        montant=montant_avance,
                        mode_paiement=form.cleaned_data.get('mode_paiement_avance', 'especes'),
                        date_paiement=form.cleaned_data.get('date_paiement_avance', timezone.now().date()),
                        cree_par=request.user,
                        notes=f"Paiement d'avance de loyer créé automatiquement lors de la création du contrat {contrat.numero_contrat}"
                    )
                    
                    messages.success(
                        request,
                        f'Contrat "{contrat.numero_contrat}" ajouté avec succès! '
                        f'Le paiement d\'avance de loyer de {contrat.avance_loyer} F CFA a été créé automatiquement.'
                    )
                    
                except Exception as e:
                    messages.warning(
                        request,
                        f'Contrat "{contrat.numero_contrat}" ajouté avec succès, '
                        f'mais la création du paiement d\'avance de loyer a échoué: {str(e)}'
                    )
            
            # Vérifier si l'utilisateur veut générer le PDF
            telecharger_pdf = form.cleaned_data.get('telecharger_pdf', False)
            
            if telecharger_pdf:
                try:
                    # Générer le PDF du contrat avec le nouveau service
                    from .services import ContratPDFService
                    pdf_service = ContratPDFService(contrat)
                    pdf_buffer = pdf_service.generate_contrat_pdf(use_cache=False)
                    
                    # Créer la réponse HTTP avec le PDF
                    from django.http import HttpResponse
                    response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
                    response['Content-Disposition'] = f'attachment; filename="contrat_{contrat.numero_contrat}.pdf"'
                    
                    if creer_paiement_caution or creer_paiement_avance:
                        messages.success(
                            request,
                            f'Contrat "{contrat.numero_contrat}" ajouté avec succès! '
                            f'Le PDF du contrat a été généré et les paiements ont été créés.'
                        )
                    else:
                        messages.success(
                            request,
                            f'Contrat "{contrat.numero_contrat}" ajouté avec succès! '
                            f'Le PDF du contrat a été généré et téléchargé.'
                        )
                    
                    return response
                    
                except Exception as e:
                    messages.warning(
                        request,
                        f'Contrat "{contrat.numero_contrat}" ajouté avec succès, '
                        f'mais la génération du PDF a échoué: {str(e)}'
                    )
                    return redirect('contrats:detail', pk=contrat.pk)
            else:
                if creer_paiement_caution or creer_paiement_avance:
                    messages.success(
                        request,
                        f'Contrat "{contrat.numero_contrat}" ajouté avec succès! '
                        f'Les paiements ont été créés. Vous pouvez générer le PDF depuis la page de détail.'
                    )
                else:
                    messages.success(
                        request,
                        f'Contrat "{contrat.numero_contrat}" ajouté avec succès! '
                        f'Vous pouvez générer le PDF et créer les paiements depuis la page de détail.'
                    )
                return redirect('contrats:detail', pk=contrat.pk)
        else:
            # Afficher les erreurs détaillées
            error_summary = form.get_errors_summary()
            if error_summary:
                messages.error(request, f'Veuillez corriger les erreurs suivantes :\n{error_summary}')
            else:
                messages.error(request, 'Veuillez corriger les erreurs dans le formulaire.')
    else:
        form = ContratForm()
    
    # Utiliser la logique simplifiée pour éviter les erreurs
    from .utils import get_proprietes_disponibles
    proprietes_disponibles = get_proprietes_disponibles()
    
    context = {
        'form': form,
        'title': 'Ajouter un contrat',
        'proprietes': proprietes_disponibles,
        'locataires': Locataire.objects.all(),
        'proprietes_data': form.proprietes_data,
    }
    return render(request, 'contrats/contrat_form.html', context)


@login_required
def modifier_contrat(request, pk):
    """
    Vue pour modifier un contrat avec possibilité de régénérer le PDF et gérer la caution
    """
    # Vérification des permissions : Seul PRIVILEGE peut modifier
    from core.utils import check_group_permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE'], 'modify')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('contrats:liste')
    
    contrat = get_object_or_404(Contrat, pk=pk)
    
    if request.method == 'POST':
        form = ContratForm(request.POST, request.FILES, instance=contrat)
        if form.is_valid():
            contrat = form.save(commit=False)
            contrat.save()
            
            # Vérifier si l'utilisateur veut générer le reçu de caution
            generer_recu_caution = form.cleaned_data.get('generer_recu_caution', False)
            
            if generer_recu_caution:
                try:
                    # Vérifier si un reçu de caution existe déjà
                    from .models import RecuCaution
                    recu_caution, created = RecuCaution.objects.get_or_create(
                        contrat=contrat,
                        defaults={'type_recu': 'complet'}
                    )
                    
                    if created:
                        messages.success(
                            request, 
                            f'Contrat "{contrat.numero_contrat}" modifié avec succès! '
                            f'Un nouveau reçu de caution a été généré.'
                        )
                    else:
                        messages.success(
                            request, 
                            f'Contrat "{contrat.numero_contrat}" modifié avec succès! '
                            f'Le reçu de caution existant a été mis à jour.'
                        )
                        
                except Exception as e:
                    messages.warning(
                        request, 
                        f'Contrat "{contrat.numero_contrat}" modifié avec succès, '
                        f'mais la gestion du reçu de caution a échoué: {str(e)}'
                    )
            
            # Vérifier si l'utilisateur veut régénérer le PDF
            telecharger_pdf = form.cleaned_data.get('telecharger_pdf', False)
            
            if telecharger_pdf:
                try:
                    # Régénérer le PDF du contrat avec le nouveau service
                    from .services import ContratPDFService
                    pdf_service = ContratPDFService(contrat)
                    pdf_buffer = pdf_service.generate_contrat_pdf(use_cache=False)
                    
                    # Créer la réponse HTTP avec le PDF
                    from django.http import HttpResponse
                    response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
                    response['Content-Disposition'] = f'attachment; filename="contrat_{contrat.numero_contrat}_modifie.pdf"'
                    
                    if generer_recu_caution:
                        messages.success(
                            request, 
                            f'Contrat "{contrat.numero_contrat}" modifié avec succès! '
                            f'Le PDF mis à jour et le reçu de caution ont été générés.'
                        )
                    else:
                        messages.success(
                            request, 
                            f'Contrat "{contrat.numero_contrat}" modifié avec succès! '
                            f'Le PDF mis à jour a été généré et téléchargé.'
                        )
                    
                    return response
                    
                except Exception as e:
                    messages.warning(
                        request, 
                        f'Contrat "{contrat.numero_contrat}" modifié avec succès, '
                        f'mais la génération du PDF a échoué: {str(e)}'
                    )
                    return redirect('contrats:detail', pk=pk)
            else:
                if generer_recu_caution:
                    messages.success(
                        request, 
                        f'Contrat "{contrat.numero_contrat}" modifié avec succès! '
                        f'Le reçu de caution a été mis à jour. Vous pouvez générer le PDF depuis la page de détail.'
                    )
                else:
                    messages.success(request, f'Contrat "{contrat.numero_contrat}" modifié avec succès!')
                return redirect('contrats:detail', pk=pk)
        else:
            # Afficher les erreurs détaillées
            error_summary = form.get_errors_summary()
            if error_summary:
                messages.error(request, f'Veuillez corriger les erreurs suivantes :\n{error_summary}')
            else:
                messages.error(request, 'Veuillez corriger les erreurs dans le formulaire.')
    else:
        form = ContratForm(instance=contrat)
    
    context = {
        'form': form,
        'title': f'Modifier le contrat {contrat.numero_contrat}',
        'contrat': contrat,
        'proprietes': Propriete.objects.filter(
            models.Q(disponible=True) |
            models.Q(unites_locatives__statut='disponible', unites_locatives__is_deleted=False)
        ).distinct(),
        'locataires': Locataire.objects.all(),
        'proprietes_data': form.proprietes_data,
    }
    return render(request, 'contrats/contrat_form.html', context)


@login_required
def supprimer_contrat(request, pk):
    # Vérification des permissions : Seul PRIVILEGE peut supprimer
    from core.utils import check_group_permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE'], 'delete')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('contrats:liste')
    
    contrat = get_object_or_404(Contrat, pk=pk)
    
    if request.method == 'POST':
        try:
            # Suppression logique
            old_data = {f.name: getattr(contrat, f.name) for f in contrat._meta.fields}
            contrat.is_deleted = True
            contrat.deleted_at = timezone.now()
            contrat.deleted_by = request.user
            contrat.save()
            
            # Log d'audit
            AuditLog.objects.create(
                content_type=ContentType.objects.get_for_model(Contrat),
                object_id=contrat.pk,
                action='delete',
                details={
                    'old_data': old_data,
                    'new_data': {'is_deleted': True, 'deleted_at': str(timezone.now())}
                },
                object_repr=str(contrat),
                user=request.user,
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            messages.success(request, f"Contrat {contrat.numero_contrat} supprimé avec succès.")
            return redirect('contrats:liste')
            
        except ProtectedError as e:
            messages.error(request, f"Impossible de supprimer ce contrat : {str(e)}")
            return redirect('contrats:liste')
    
    context = {
        'contrat': contrat,
    }
    return render(request, 'contrats/confirm_supprimer_contrat.html', context)


@login_required
def resilier_contrat(request, pk):
    """
    Vue pour résilier un contrat (PRIVILEGE uniquement)
    """
    # Vérification des permissions : Seul PRIVILEGE peut résilier
    from core.utils import check_group_permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE'], 'modify')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('contrats:liste')
    
    contrat = get_object_or_404(Contrat, pk=pk)
    
    # Vérifier que le contrat n'est pas déjà résilié
    if contrat.est_resilie:
        messages.warning(request, f"Le contrat {contrat.numero_contrat} est déjà résilié.")
        return redirect('contrats:detail', pk=pk)
    
    if request.method == 'POST':
        try:
            # Récupérer les données du formulaire
            date_resiliation = request.POST.get('date_resiliation')
            motif_resiliation = request.POST.get('motif_resiliation', '')
            type_resiliation = request.POST.get('type_resiliation')
            etat_lieux_sortie = request.POST.get('etat_lieux_sortie', '')
            caution_remboursee = request.POST.get('caution_remboursee') == 'on'
            montant_remboursement = request.POST.get('montant_remboursement', 0)
            date_remboursement = request.POST.get('date_remboursement')
            notes = request.POST.get('notes', '')
            
            if not all([date_resiliation, type_resiliation]):
                messages.error(request, "La date de résiliation et le type de résiliation sont obligatoires.")
                return render(request, 'contrats/resilier.html', {'contrat': contrat})
            
            # Convertir la date
            date_resiliation = datetime.strptime(date_resiliation, '%Y-%m-%d').date()
            
            # Validation de la date
            if date_resiliation < contrat.date_debut or date_resiliation > contrat.date_fin:
                messages.error(request, "La date de résiliation doit être comprise entre la date de début et la date de fin du contrat.")
                return render(request, 'contrats/resilier.html', {'contrat': contrat})
            
            # Validation des champs de remboursement
            if caution_remboursee:
                if not montant_remboursement or not date_remboursement:
                    messages.error(request, "Le montant et la date de remboursement sont requis si la caution est remboursée.")
                    return render(request, 'contrats/resilier.html', {'contrat': contrat})
                
                try:
                    montant_remboursement = float(montant_remboursement)
                    if montant_remboursement > contrat.get_total_caution_avance():
                        messages.error(request, "Le montant de remboursement ne peut pas dépasser le total des cautions et avances.")
                        return render(request, 'contrats/resilier.html', {'contrat': contrat})
                except ValueError:
                    messages.error(request, "Le montant de remboursement doit être un nombre valide.")
                    return render(request, 'contrats/resilier.html', {'contrat': contrat})
                
                date_remboursement = datetime.strptime(date_remboursement, '%Y-%m-%d').date()
            else:
                montant_remboursement = 0
                date_remboursement = None
            
            # Récupérer les données de travaux
            travaux_peinture = request.POST.get('travaux_peinture', 0)
            facture_onea = request.POST.get('facture_onea', 0)
            facture_sonabel = request.POST.get('facture_sonabel', 0)
            travaux_ventilateur = request.POST.get('travaux_ventilateur', 0)
            autres_depenses = request.POST.get('autres_depenses', 0)
            description_autres_depenses = request.POST.get('description_autres_depenses', '')
            
            # Créer la résiliation
            resiliation = ResiliationContrat.objects.create(
                contrat=contrat,
                date_resiliation=date_resiliation,
                motif_resiliation=motif_resiliation,
                type_resiliation=type_resiliation,
                etat_lieux_sortie=etat_lieux_sortie,
                caution_remboursee=caution_remboursee,
                montant_remboursement=montant_remboursement,
                date_remboursement=date_remboursement,
                notes=notes,
                cree_par=request.user,
                # Nouveaux champs de travaux
                travaux_peinture=travaux_peinture,
                facture_onea=facture_onea,
                facture_sonabel=facture_sonabel,
                travaux_ventilateur=travaux_ventilateur,
                autres_depenses=autres_depenses,
                description_autres_depenses=description_autres_depenses
            )
            
            # Mettre à jour le contrat
            old_data = {f.name: getattr(contrat, f.name) for f in contrat._meta.fields}
            contrat.est_actif = False
            contrat.est_resilie = True
            contrat.date_resiliation = date_resiliation
            contrat.motif_resiliation = motif_resiliation
            contrat.save()
            
            # La disponibilité de la propriété est maintenant gérée automatiquement dans le modèle
            # lors de la sauvegarde du contrat résilié
            
            # Log d'audit pour le contrat
            AuditLog.objects.create(
                content_type=ContentType.objects.get_for_model(Contrat),
                object_id=contrat.pk,
                action='resiliate',
                details={
                    'old_data': old_data,
                    'new_data': {
                        'date_resiliation': str(date_resiliation),
                        'est_actif': False,
                        'est_resilie': True,
                        'motif_resiliation': motif_resiliation
                    }
                },
                object_repr=str(contrat),
                user=request.user,
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            # Log d'audit pour la résiliation
            AuditLog.objects.create(
                content_type=ContentType.objects.get_for_model(ResiliationContrat),
                object_id=resiliation.pk,
                action='create',
                details={
                    'old_data': {},
                    'new_data': {
                        'contrat': str(contrat.pk),
                        'date_resiliation': str(date_resiliation),
                        'motif_resiliation': motif_resiliation,
                        'type_resiliation': type_resiliation,
                        'caution_remboursee': caution_remboursee,
                        'montant_remboursement': str(montant_remboursement)
                    }
                },
                object_repr=str(resiliation),
                user=request.user,
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            messages.success(request, f"Contrat {contrat.numero_contrat} résilié avec succès. Résiliation créée avec l'ID {resiliation.pk}.")
            return redirect('contrats:detail_resiliation', resiliation_id=resiliation.pk)
            
        except ValueError as e:
            messages.error(request, f"Erreur de format : {str(e)}")
        except Exception as e:
            messages.error(request, f"Erreur lors de la résiliation : {str(e)}")
    
    context = {
        'contrat': contrat,
    }
    return render(request, 'contrats/resilier.html', context)


# Vues pour les quittances
class QuittanceListView(PrivilegeButtonsMixin, IntelligentListView):
    model = Quittance
    template_name = 'base_liste_intelligente.html'
    paginate_by = 20
    page_title = 'Quittances'
    page_icon = 'file-invoice-dollar'
    add_url = 'contrats:quittance_ajouter'
    add_text = 'Ajouter une quittance'
    search_fields = ['contrat__numero_contrat', 'contrat__propriete__titre', 'contrat__locataire__nom', 'contrat__locataire__prenom', 'mois', 'montant_loyer', 'montant_charges', 'montant_total']
    filter_fields = ['contrat', 'mois']
    default_sort = 'mois'
    columns = [
        {'field': 'contrat', 'label': 'Contrat', 'sortable': True},
        {'field': 'mois', 'label': 'Mois', 'sortable': True},
        {'field': 'montant_loyer', 'label': 'Loyer', 'sortable': True},
        {'field': 'montant_charges', 'label': 'Charges', 'sortable': True},
        {'field': 'montant_total', 'label': 'Total', 'sortable': True},
    ]
    actions = [
        {'url_name': 'contrats:quittance_detail', 'icon': 'eye', 'style': 'outline-primary', 'title': 'Voir'},
    ]
    sort_options = [
        {'value': 'mois', 'label': 'Mois'},
        {'value': 'montant_total', 'label': 'Total'},
    ]
    
    def get_queryset(self):
        """
        Optimisation des requêtes de base de données
        """
        queryset = super().get_queryset()
        return queryset.select_related('contrat', 'contrat__locataire', 'contrat__propriete')
    
    def get_context_data(self, **kwargs):
        """
        Ajout de statistiques et d'informations supplémentaires au contexte
        """
        context = super().get_context_data(**kwargs)
        
        # Statistiques
        context['total_quittances'] = Quittance.objects.count()
        
        # Montant total des loyers
        from django.db.models import Sum
        context['montant_total_loyers'] = Quittance.objects.aggregate(
            total=Sum('montant_loyer')
        )['total'] or 0
        
        # Montant total des charges
        context['montant_total_charges'] = Quittance.objects.aggregate(
            total=Sum('montant_charges')
        )['total'] or 0
        
        # Montant total toutes charges comprises
        context['montant_total_tcc'] = Quittance.objects.aggregate(
            total=Sum('montant_total')
        )['total'] or 0
        
        # Ajouter la configuration de l'entreprise
        from core.utils import get_context_with_entreprise_config
        return get_context_with_entreprise_config(context)
    
    def dispatch(self, request, *args, **kwargs):
        """
        Vérification des permissions avant l'affichage
        """
        # Vérification des permissions : PRIVILEGE, ADMINISTRATION, CONTROLES peuvent voir la liste
        from core.utils import check_group_permissions
        permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'CONTROLES', 'CAISSE'], 'view')
        if not permissions['allowed']:
            messages.error(request, permissions['message'])
            return redirect('core:dashboard')
        
        return super().dispatch(request, *args, **kwargs)

quittance_list = QuittanceListView.as_view()


@login_required
def detail_quittance(request, pk):
    """
    Vue de détail d'une quittance
    """
    # Vérification des permissions : PRIVILEGE, ADMINISTRATION, CONTROLES peuvent voir les détails
    from core.utils import check_group_permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'CONTROLES', 'CAISSE'], 'view')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('contrats:quittances_liste')
    
    quittance = get_object_or_404(Quittance, pk=pk)
    context = get_context_with_entreprise_config({
        'quittance': quittance
    })
    return render(request, 'contrats/quittance_detail.html', context)


@login_required
def ajouter_quittance(request):
    """
    Vue pour ajouter une quittance
    """
    # Vérification des permissions : TOUS les groupes peuvent ajouter
    from core.utils import check_group_permissions
    
    # Tous les groupes peuvent ajouter des quittances
    # permissions = check_group_permissions(request.user, ['PRIVILEGE'], 'add')
    # if not permissions['allowed']:
    #     messages.error(request, permissions['message'])
    #     return redirect('contrats:quittances_liste')
    
    if request.method == 'POST':
        # Logique d'ajout de quittance
        messages.success(request, 'Quittance ajoutée avec succès!')
        return redirect('contrats:quittances_liste')
    
    context = get_context_with_entreprise_config({
        'contrats': Contrat.objects.filter(est_actif=True)
    })
    return render(request, 'contrats/quittance_ajouter.html', context)


# Vues pour les états des lieux
class EtatLieuxListView(PrivilegeButtonsMixin, IntelligentListView):
    model = EtatLieux
    template_name = 'base_liste_intelligente.html'
    paginate_by = 20
    page_title = 'États des lieux'
    page_icon = 'clipboard-list'
    add_url = 'contrats:etat_lieux_ajouter'
    add_text = 'Ajouter un état des lieux'
    search_fields = ['contrat__numero_contrat', 'contrat__propriete__titre', 'contrat__locataire__nom', 'contrat__locataire__prenom', 'type_etat', 'date_etat', 'observations_generales']
    filter_fields = ['contrat', 'type_etat', 'date_etat']
    default_sort = 'date_etat'
    columns = [
        {'field': 'contrat', 'label': 'Contrat', 'sortable': True},
        {'field': 'type_etat', 'label': 'Type', 'sortable': True},
        {'field': 'date_etat', 'label': 'Date', 'sortable': True},
        {'field': 'etat_murs', 'label': 'Murs', 'sortable': True},
        {'field': 'etat_sol', 'label': 'Sol', 'sortable': True},
        {'field': 'etat_plomberie', 'label': 'Plomberie', 'sortable': True},
        {'field': 'etat_electricite', 'label': 'Électricité', 'sortable': True},
    ]
    actions = [
        {'url_name': 'contrats:etat_lieux_detail', 'icon': 'eye', 'style': 'outline-primary', 'title': 'Voir'},
    ]
    sort_options = [
        {'value': 'date_etat', 'label': 'Date'},
        {'value': 'type_etat', 'label': 'Type'},
    ]
    
    def get_queryset(self):
        """
        Optimisation des requêtes de base de données
        """
        queryset = super().get_queryset()
        return queryset.select_related('contrat', 'contrat__locataire', 'contrat__propriete')
    
    def get_context_data(self, **kwargs):
        """
        Ajout de statistiques et d'informations supplémentaires au contexte
        """
        context = super().get_context_data(**kwargs)
        
        # Statistiques
        context['total_etats_lieux'] = EtatLieux.objects.count()
        context['entrees_etats_lieux'] = EtatLieux.objects.filter(type_etat='entree').count()
        context['sorties_etats_lieux'] = EtatLieux.objects.filter(type_etat='sortie').count()
        
        return context
    
    def dispatch(self, request, *args, **kwargs):
        """
        Vérification des permissions avant l'affichage
        """
        # Vérification des permissions : PRIVILEGE, ADMINISTRATION, CONTROLES peuvent voir la liste
        from core.utils import check_group_permissions
        permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'CONTROLES', 'CAISSE'], 'view')
        if not permissions['allowed']:
            messages.error(request, permissions['message'])
            return redirect('core:dashboard')
        
        return super().dispatch(request, *args, **kwargs)

etat_lieux_list = EtatLieuxListView.as_view()


@login_required
def detail_etat_lieux(request, pk):
    """
    Vue de détail d'un état des lieux
    """
    # Vérification des permissions : PRIVILEGE, ADMINISTRATION, CONTROLES peuvent voir les détails
    from core.utils import check_group_permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'CONTROLES', 'CAISSE'], 'view')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('contrats:etats_lieux_liste')
    
    etat_lieux = get_object_or_404(EtatLieux, pk=pk)
    context = {
        'etat_lieux': etat_lieux
    }
    return render(request, 'contrats/etat_lieux_detail.html', context)


@login_required
def ajouter_etat_lieux(request):
    """
    Vue pour ajouter un état des lieux
    """
    # Tous les groupes peuvent ajouter des états des lieux
    # permissions = check_group_permissions(request.user, ['PRIVILEGE'], 'add')
    # if not permissions['allowed']:
    #     messages.error(request, permissions['message'])
    #     return redirect('contrats:etats_lieux_liste')
    
    if request.method == 'POST':
        try:
            # Récupérer les données du formulaire
            contrat_id = request.POST.get('contrat')
            type_etat = request.POST.get('type_etat')
            date_etat = request.POST.get('date_etat')
            observations_generales = request.POST.get('observations_generales', '')
            etat_murs = request.POST.get('etat_murs', 'bon')
            etat_sol = request.POST.get('etat_sol', 'bon')
            etat_plomberie = request.POST.get('etat_plomberie', 'bon')
            etat_electricite = request.POST.get('etat_electricite', 'bon')
            notes = request.POST.get('notes', '')
            
            # Validation des données
            if not all([contrat_id, type_etat, date_etat]):
                messages.error(request, 'Tous les champs obligatoires doivent être remplis.')
                return redirect('contrats:ajouter_etat_lieux')
            
            # Récupérer le contrat
            contrat = get_object_or_404(Contrat, id=contrat_id, est_actif=True)
            
            # Vérifier si un état des lieux de ce type existe déjà pour ce contrat
            if EtatLieux.objects.filter(contrat=contrat, type_etat=type_etat).exists():
                messages.error(request, f'Un état des lieux de type "{type_etat}" existe déjà pour ce contrat.')
                return redirect('contrats:ajouter_etat_lieux')
            
            # Créer l'état des lieux
            etat_lieux = EtatLieux.objects.create(
                contrat=contrat,
                type_etat=type_etat,
                date_etat=date_etat,
                observations_generales=observations_generales,
                etat_murs=etat_murs,
                etat_sol=etat_sol,
                etat_plomberie=etat_plomberie,
                etat_electricite=etat_electricite,
                notes=notes,
                cree_par=request.user
            )
            
            # Log d'audit
            from django.contrib.contenttypes.models import ContentType
            from core.models import AuditLog
            
            AuditLog.objects.create(
                content_type=ContentType.objects.get_for_model(EtatLieux),
                object_id=etat_lieux.pk,
                action='CREATE',
                old_data=None,
                new_data={
                    'contrat': contrat.numero_contrat,
                    'type_etat': type_etat,
                    'date_etat': str(date_etat),
                    'etat_murs': etat_murs,
                    'etat_sol': etat_sol,
                    'etat_plomberie': etat_plomberie,
                    'etat_electricite': etat_electricite,
                },
                user=request.user,
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            messages.success(request, f'État des lieux de type "{type_etat}" ajouté avec succès pour le contrat {contrat.numero_contrat}!')
            return redirect('contrats:etats_lieux_liste')
            
        except Exception as e:
            messages.error(request, f'Erreur lors de la création de l\'état des lieux: {str(e)}')
            return redirect('contrats:ajouter_etat_lieux')
    
    # Récupérer les contrats actifs avec leurs propriétés et locataires
    contrats = Contrat.objects.filter(
        est_actif=True
    ).select_related('propriete', 'locataire').order_by('-date_debut')
    
    context = {
        'contrats': contrats,
        'contrat_selectionne': None
    }
    return render(request, 'contrats/etat_lieux_ajouter.html', context)


@login_required
def modifier_etat_lieux(request, pk):
    """
    Vue pour modifier un état des lieux existant
    """
    # Vérification des permissions : PRIVILEGE peut modifier
    from core.utils import check_group_permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE'], 'modify')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('contrats:etats_lieux_liste')
    
    etat_lieux = get_object_or_404(EtatLieux, pk=pk)
    
    if request.method == 'POST':
        try:
            # Récupérer les données du formulaire
            type_etat = request.POST.get('type_etat')
            date_etat = request.POST.get('date_etat')
            observations_generales = request.POST.get('observations_generales', '')
            etat_murs = request.POST.get('etat_murs', 'bon')
            etat_sol = request.POST.get('etat_sol', 'bon')
            etat_plomberie = request.POST.get('etat_plomberie', 'bon')
            etat_electricite = request.POST.get('etat_electricite', 'bon')
            notes = request.POST.get('notes', '')
            
            # Validation des données
            if not all([type_etat, date_etat]):
                messages.error(request, 'Tous les champs obligatoires doivent être remplis.')
                return redirect('contrats:modifier_etat_lieux', pk=pk)
            
            # Vérifier si un autre état des lieux de ce type existe pour ce contrat
            if EtatLieux.objects.filter(contrat=etat_lieux.contrat, type_etat=type_etat).exclude(pk=pk).exists():
                messages.error(request, f'Un état des lieux de type "{type_etat}" existe déjà pour ce contrat.')
                return redirect('contrats:modifier_etat_lieux', pk=pk)
            
            # Sauvegarder les anciennes données pour l'audit
            old_data = {f.name: getattr(etat_lieux, f.name) for f in etat_lieux._meta.fields}
            
            # Mettre à jour l'état des lieux
            etat_lieux.type_etat = type_etat
            etat_lieux.date_etat = date_etat
            etat_lieux.observations_generales = observations_generales
            etat_lieux.etat_murs = etat_murs
            etat_lieux.etat_sol = etat_sol
            etat_lieux.etat_plomberie = etat_plomberie
            etat_lieux.etat_electricite = etat_electricite
            etat_lieux.notes = notes
            etat_lieux.save()
            
            # Log d'audit
            from django.contrib.contenttypes.models import ContentType
            from core.models import AuditLog
            
            AuditLog.objects.create(
                content_type=ContentType.objects.get_for_model(EtatLieux),
                object_id=etat_lieux.pk,
                action='UPDATE',
                old_data=old_data,
                new_data={
                    'contrat': etat_lieux.contrat.numero_contrat,
                    'type_etat': type_etat,
                    'date_etat': str(date_etat),
                    'etat_murs': etat_murs,
                    'etat_sol': etat_sol,
                    'etat_plomberie': etat_plomberie,
                    'etat_electricite': etat_electricite,
                },
                user=request.user,
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            messages.success(request, f'État des lieux modifié avec succès!')
            return redirect('contrats:etat_lieux_detail', pk=pk)
            
        except Exception as e:
            messages.error(request, f'Erreur lors de la modification de l\'état des lieux: {str(e)}')
            return redirect('contrats:modifier_etat_lieux', pk=pk)
    
    # Récupérer les contrats actifs pour le formulaire
    contrats = Contrat.objects.filter(est_actif=True).select_related('propriete', 'locataire').order_by('-date_debut')
    
    context = {
        'etat_lieux': etat_lieux,
        'contrats': contrats,
        'contrat_selectionne': etat_lieux.contrat
    }
    return render(request, 'contrats/etat_lieux_modifier.html', context)


@login_required
def supprimer_etat_lieux(request, pk):
    """
    Vue pour supprimer un état des lieux
    """
    # Vérification des permissions : PRIVILEGE peut supprimer
    from core.utils import check_group_permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE'], 'delete')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('contrats:etats_lieux_liste')
    
    etat_lieux = get_object_or_404(EtatLieux, pk=pk)
    
    if request.method == 'POST':
        try:
            # Sauvegarder les données pour l'audit
            old_data = {f.name: getattr(etat_lieux, f.name) for f in etat_lieux._meta.fields}
            
            # Log d'audit avant suppression
            from django.contrib.contenttypes.models import ContentType
            from core.models import AuditLog
            
            AuditLog.objects.create(
                content_type=ContentType.objects.get_for_model(EtatLieux),
                object_id=etat_lieux.pk,
                action='DELETE',
                old_data=old_data,
                new_data=None,
                user=request.user,
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            # Supprimer l'état des lieux
            contrat_numero = etat_lieux.contrat.numero_contrat
            etat_lieux.delete()
            
            messages.success(request, f'État des lieux pour le contrat {contrat_numero} supprimé avec succès!')
            return redirect('contrats:etats_lieux_liste')
            
        except Exception as e:
            messages.error(request, f'Erreur lors de la suppression de l\'état des lieux: {str(e)}')
            return redirect('contrats:etat_lieux_detail', pk=pk)
    
    # Rediriger vers la page de détail si ce n'est pas une requête POST
    return redirect('contrats:etat_lieux_detail', pk=pk)


@login_required
def contrats_orphelins(request):
    """
    Vue pour afficher et gérer les contrats orphelins (locataire supprimé)
    """
    # VÉRIFICATION CRITIQUE : Seul PRIVILEGE peut accéder aux contrats orphelins
    groupe = getattr(request.user, 'groupe_travail', None)
    if not groupe or groupe.nom.upper() != 'PRIVILEGE':
        messages.error(request, "Seuls les utilisateurs du groupe PRIVILEGE peuvent accéder aux contrats orphelins.")
        return redirect('contrats:liste')
    
    # Récupérer les contrats dont le locataire a été supprimé logiquement
    contrats_orphelins = Contrat.objects.filter(
        locataire__is_deleted=True,
        est_actif=True
    ).select_related('locataire', 'propriete').order_by('-date_debut')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        contrats_ids = request.POST.getlist('contrats')
        
        if action == 'supprimer' and contrats_ids:
            # Supprimer les contrats orphelins sélectionnés
            contrats_a_supprimer = Contrat.objects.filter(id__in=contrats_ids)
            for contrat in contrats_a_supprimer:
                # Log d'audit avant suppression
                old_data = {f.name: getattr(contrat, f.name) for f in contrat._meta.fields}
                AuditLog.objects.create(
                    content_type=ContentType.objects.get_for_model(Contrat),
                    object_id=contrat.pk,
                    action='DELETE_ORPHANED',
                    old_data=old_data,
                    new_data=None,
                    user=request.user,
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
                contrat.delete()
            
            messages.success(request, f"{contrats_a_supprimer.count()} contrat(s) orphelin(s) supprimé(s) avec succès.")
            return redirect('contrats:orphelins')
            
        elif action == 'restaurer_locataire' and contrats_ids:
            # Restaurer le locataire du premier contrat sélectionné
            contrat = Contrat.objects.filter(id__in=contrats_ids).first()
            if contrat and contrat.locataire:
                locataire = contrat.locataire
                locataire.is_deleted = False
                locataire.deleted_at = None
                locataire.deleted_by = None
                locataire.save()
                
                # Log d'audit
                AuditLog.objects.create(
                    content_type=ContentType.objects.get_for_model(Locataire),
                    object_id=locataire.pk,
                    action='RESTORE_FROM_ORPHANED',
                    old_data={'is_deleted': True},
                    new_data={'is_deleted': False},
                    user=request.user,
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
                
                messages.success(request, f"Locataire {locataire.nom} {locataire.prenom} restauré avec succès.")
                return redirect('contrats:orphelins')
    
    # Pagination
    paginator = Paginator(contrats_orphelins, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Calculer les statistiques
    total_contrats = contrats_orphelins.count()
    
    # Compter les locataires supprimés (uniques)
    from django.db.models import Count
    total_locataires = contrats_orphelins.values('locataire').distinct().count()
    
    context = {
        'contrats_orphelins': page_obj,
        'page_obj': page_obj,
        'total_contrats': total_contrats,
        'total_locataires': total_locataires,
    }
    
    return render(request, 'contrats/orphelins.html', context)


# Vues pour la gestion des cautions et avances
@login_required
def liste_contrats_caution(request):
    """Liste des contrats avec gestion des cautions et avances."""
    
    # Vérification des permissions : PRIVILEGE, ADMINISTRATION, CONTROLES, CAISSE peuvent voir la liste
    from core.utils import check_group_permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'CONTROLES', 'CAISSE'], 'view')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('core:dashboard')
    
    # CORRECTION AUTOMATIQUE DES STATUTS - Force la correction à chaque chargement
    try:
        from django.db import transaction
        from decimal import Decimal
        from paiements.models import Paiement
        
        with transaction.atomic():
            # Récupérer tous les contrats actifs
            contrats_a_corriger = Contrat.objects.filter(
                est_actif=True,
                est_resilie=False
            ).select_related('propriete', 'locataire')
            
            contrats_corriges = 0
            
            for contrat in contrats_a_corriger:
                # Montants requis
                caution_requise = Decimal(str(contrat.depot_garantie)) if contrat.depot_garantie else Decimal('0')
                avance_requise = Decimal(str(contrat.avance_loyer)) if contrat.avance_loyer else Decimal('0')
                
                # Calculer les montants payés avec tous les types possibles
                paiements_caution = Paiement.objects.filter(
                    contrat=contrat,
                    type_paiement='caution',
                    statut='valide'
                )
                
                montant_caution_paye = sum(p.montant for p in paiements_caution)
                
                paiements_avance = Paiement.objects.filter(
                    contrat=contrat,
                    type_paiement='avance',
                    statut='valide'
                )
                
                montant_avance_paye = sum(p.montant for p in paiements_avance)
                
                # Vérifier les statuts
                caution_payee = montant_caution_paye >= caution_requise if caution_requise > 0 else True
                avance_payee = montant_avance_paye >= avance_requise if avance_requise > 0 else True
                
                # Mettre à jour les champs du contrat
                contrat_modified = False
                
                if contrat.caution_payee != caution_payee:
                    contrat.caution_payee = caution_payee
                    contrat_modified = True
                
                if contrat.avance_loyer_payee != avance_payee:
                    contrat.avance_loyer_payee = avance_payee
                    contrat_modified = True
                
                if contrat_modified:
                    contrat.save()
                    contrats_corriges += 1
            
            if contrats_corriges > 0:
                messages.info(request, f'Correction automatique effectuée : {contrats_corriges} contrats mis à jour.')
                
    except Exception as e:
        messages.warning(request, f'Erreur lors de la correction automatique : {str(e)}')
    
    # Récupérer les filtres
    statut_caution = request.GET.get('statut_caution', '')
    statut_avance = request.GET.get('statut_avance', '')
    bailleur_id = request.GET.get('bailleur', '')
    
    # Base QuerySet avec annotations pour les paiements
    from django.db.models import Sum, Case, When, DecimalField, Q, F
    from decimal import Decimal
    
    contrats = Contrat.objects.filter(
        est_actif=True,
        est_resilie=False
    ).select_related('propriete', 'locataire', 'propriete__bailleur').annotate(
        # Montants requis
        montant_caution_requis=Case(
            When(depot_garantie__isnull=False, then='depot_garantie'),
            default=0,
            output_field=DecimalField(max_digits=10, decimal_places=2)
        ),
        montant_avance_requis=Case(
            When(avance_loyer__isnull=False, then='avance_loyer'),
            default=0,
            output_field=DecimalField(max_digits=10, decimal_places=2)
        ),
        # Montants payés - Correction pour inclure tous les types de paiement possibles
        montant_caution_paye=Sum(
            'paiements__montant',
            filter=Q(paiements__type_paiement__in=['caution', 'depot_garantie'], paiements__statut='valide'),
            default=0
        ),
        montant_avance_paye=Sum(
            'paiements__montant',
            filter=Q(paiements__type_paiement='avance', paiements__statut='valide'),
            default=0
        )
    ).order_by('-date_creation')
    
    # CORRECTION CRITIQUE : Mettre à jour les annotations avec les vrais statuts des contrats
    # Car les annotations ne reflètent pas les changements en temps réel
    for contrat in contrats:
        # Recalculer les montants payés en temps réel
        paiements_caution = Paiement.objects.filter(
            contrat=contrat,
            type_paiement__in=['caution', 'depot_garantie'],
            statut='valide'
        )
        montant_caution_paye = sum(p.montant for p in paiements_caution)
        
        paiements_avance = Paiement.objects.filter(
            contrat=contrat,
            type_paiement='avance',
            statut='valide'
        )
        montant_avance_paye = sum(p.montant for p in paiements_avance)
        
        # Mettre à jour les annotations avec les vrais montants
        contrat.montant_caution_paye = montant_caution_paye
        contrat.montant_avance_paye = montant_avance_paye
    
    # Appliquer les filtres par bailleur en premier (plus efficace)
    if bailleur_id:
        contrats = contrats.filter(propriete__bailleur_id=bailleur_id)
    
    # Appliquer les filtres de statut avec des requêtes optimisées
    if statut_caution == 'complet':
        # Contrats où caution ET avance sont payées
        contrats = contrats.filter(
            Q(montant_caution_requis__lte=F('montant_caution_paye')) &
            Q(montant_avance_requis__lte=F('montant_avance_paye'))
        )
    elif statut_caution == 'caution_seule':
        # Contrats où seule la caution est payée
        contrats = contrats.filter(
            Q(montant_caution_requis__lte=F('montant_caution_paye')) &
            Q(montant_avance_requis__gt=F('montant_avance_paye'))
        )
    elif statut_caution == 'avance_seule':
        # Contrats où seule l'avance est payée
        contrats = contrats.filter(
            Q(montant_caution_requis__gt=F('montant_caution_paye')) &
            Q(montant_avance_requis__lte=F('montant_avance_paye'))
        )
    elif statut_caution == 'en_attente':
        # Contrats en attente (aucun paiement)
        contrats = contrats.filter(
            Q(montant_caution_requis__gt=F('montant_caution_paye')) &
            Q(montant_avance_requis__gt=F('montant_avance_paye'))
        )
    
    # Filtre par statut d'avance
    if statut_avance == 'payee':
        contrats = contrats.filter(montant_avance_requis__lte=F('montant_avance_paye'))
    elif statut_avance == 'non_payee':
        contrats = contrats.filter(montant_avance_requis__gt=F('montant_avance_paye'))
    
    # Calculer les statistiques avec des requêtes optimisées
    from django.db.models import Count
    
    # Statistiques générales
    total_contrats = contrats.count()
    
    # Contrats complets (caution ET avance payées)
    contrats_complets = contrats.filter(
        Q(montant_caution_requis__lte=F('montant_caution_paye')) &
        Q(montant_avance_requis__lte=F('montant_avance_paye'))
    ).count()
    
    # Contrats en attente (aucun paiement)
    contrats_en_attente = contrats.filter(
        Q(montant_caution_requis__gt=F('montant_caution_paye')) &
        Q(montant_avance_requis__gt=F('montant_avance_paye'))
    ).count()
    
    # Cautions payées
    cautions_payees = contrats.filter(
        montant_caution_requis__lte=F('montant_caution_paye')
    ).count()
    
    # Avances payées
    avances_payees = contrats.filter(
        montant_avance_requis__lte=F('montant_avance_paye')
    ).count()
    
    # Pagination
    paginator = Paginator(contrats, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Filtres pour le formulaire
    from proprietes.models import Bailleur
    bailleurs = Bailleur.objects.all()
    
    context = {
        'page_obj': page_obj,
        'bailleurs': bailleurs,
        'statuts_caution': [
            ('complet', 'Complet'),
            ('caution_seule', 'Caution payée'),
            ('avance_seule', 'Avance payée'),
            ('en_attente', 'En attente'),
        ],
        'statuts_avance': [
            ('payee', 'Payée'),
            ('non_payee', 'Non payée'),
        ],
        'statistiques': {
            'total_contrats': total_contrats,
            'contrats_complets': contrats_complets,
            'contrats_en_attente': contrats_en_attente,
            'cautions_payees': cautions_payees,
            'avances_payees': avances_payees,
        },
        'filtres_actifs': {
            'statut_caution': statut_caution,
            'statut_avance': statut_avance,
            'bailleur': bailleur_id,
        }
    }
    
    return render(request, 'contrats/liste_contrats_caution.html', context)


@login_required
def marquer_caution_payee(request, contrat_id):
    """Marquer la caution comme payée."""
    
    # Vérification des permissions : PRIVILEGE, ADMINISTRATION, CAISSE peuvent marquer les cautions
    from core.utils import check_group_permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'CAISSE'], 'modify')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('contrats:liste_contrats_caution')
    
    try:
        contrat = Contrat.objects.get(id=contrat_id)
    except Contrat.DoesNotExist:
        messages.error(request, 'Contrat non trouvé.')
        return redirect('contrats:liste_contrats_caution')
    
    if request.method == 'POST':
        date_paiement = request.POST.get('date_paiement')
        if date_paiement:
            try:
                date_paiement = datetime.strptime(date_paiement, '%Y-%m-%d').date()
            except ValueError:
                messages.error(request, 'Date de paiement invalide.')
                return redirect('contrats:liste_contrats_caution')
        else:
            date_paiement = timezone.now().date()
        
        # Créer un vrai paiement de caution dans la base de données
        from paiements.models import Paiement
        from decimal import Decimal
        
        # Convertir le montant de caution en Decimal
        montant_caution = Decimal(str(contrat.depot_garantie)) if contrat.depot_garantie else Decimal('0')
        
        paiement = Paiement.objects.create(
            contrat=contrat,
            type_paiement='caution',
            montant=montant_caution,
            mode_paiement='especes',
            date_paiement=date_paiement,
            statut='valide',
            cree_par=request.user,
            notes=f'Paiement de caution marqué comme payé pour le contrat {contrat.numero_contrat}'
        )
        
        # Marquer le contrat comme payé
        contrat.marquer_caution_payee(date_paiement)
        messages.success(request, 'Caution marquée comme payée.')
        
        # Créer le reçu de caution
        recu, created = RecuCaution.objects.get_or_create(contrat=contrat)
        
        # Vider le cache PDF pour ce reçu
        from core.pdf_cache import PDFCacheManager
        PDFCacheManager.invalidate_cache('recu_caution', recu.id)
        
        return redirect('contrats:liste_contrats_caution')
    
    return render(request, 'contrats/marquer_caution_payee.html', {'contrat': contrat})


@login_required
def marquer_avance_payee(request, contrat_id):
    """Marquer l'avance de loyer comme payée."""
    
    # Vérification des permissions : PRIVILEGE, ADMINISTRATION, CAISSE peuvent marquer les avances
    from core.utils import check_group_permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'CAISSE'], 'modify')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('contrats:liste_contrats_caution')
    
    try:
        contrat = Contrat.objects.get(id=contrat_id)
    except Contrat.DoesNotExist:
        messages.error(request, 'Contrat non trouvé.')
        return redirect('contrats:liste_contrats_caution')
    
    if request.method == 'POST':
        date_paiement = request.POST.get('date_paiement')
        if date_paiement:
            try:
                date_paiement = datetime.strptime(date_paiement, '%Y-%m-%d').date()
            except ValueError:
                messages.error(request, 'Date de paiement invalide.')
                return redirect('contrats:liste_contrats_caution')
        else:
            date_paiement = timezone.now().date()
        
        # Créer un vrai paiement d'avance dans la base de données
        from paiements.models import Paiement
        from decimal import Decimal
        
        # Convertir le montant d'avance en Decimal
        montant_avance = Decimal(str(contrat.avance_loyer)) if contrat.avance_loyer else Decimal('0')
        
        paiement = Paiement.objects.create(
            contrat=contrat,
            type_paiement='avance',
            montant=montant_avance,
            mode_paiement='especes',
            date_paiement=date_paiement,
            statut='valide',
            cree_par=request.user,
            notes=f'Paiement d\'avance marqué comme payé pour le contrat {contrat.numero_contrat}'
        )
        
        # Marquer le contrat comme payé
        contrat.marquer_avance_payee(date_paiement)
        messages.success(request, 'Avance de loyer marquée comme payée.')
        
        # Créer le reçu de caution
        recu, created = RecuCaution.objects.get_or_create(contrat=contrat)
        
        # Vider le cache PDF pour ce reçu
        from core.pdf_cache import PDFCacheManager
        PDFCacheManager.invalidate_cache('recu_caution', recu.id)
        
        return redirect('contrats:liste_contrats_caution')
    
    return render(request, 'contrats/marquer_avance_payee.html', {'contrat': contrat})


@login_required
def detail_contrat_caution(request, contrat_id):
    """Détail d'un contrat avec gestion des cautions."""
    
    # Vérification des permissions : PRIVILEGE, ADMINISTRATION, COMPTABILITE, CAISSE peuvent voir les détails
    from core.utils import check_group_permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE', 'CAISSE'], 'view')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('contrats:liste_contrats_caution')
    
    try:
        contrat = Contrat.objects.get(id=contrat_id)
    except Contrat.DoesNotExist:
        messages.error(request, 'Contrat non trouvé.')
        return redirect('contrats:liste_contrats_caution')
    
    # Récupérer ou créer le reçu de caution
    recu_caution, created = RecuCaution.objects.get_or_create(contrat=contrat)
    
    # Récupérer ou créer le document de contrat
    document_contrat, created = DocumentContrat.objects.get_or_create(contrat=contrat)
    
    context = {
        'contrat': contrat,
        'recu_caution': recu_caution,
        'document_contrat': document_contrat,
    }
    
    return render(request, 'contrats/detail_contrat_caution.html', context)


@login_required
def imprimer_recu_caution(request, contrat_id):
    """Imprimer le reçu de caution."""
    
    # Vérification des permissions : PRIVILEGE, ADMINISTRATION, CAISSE peuvent imprimer les reçus
    from core.utils import check_group_permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'CAISSE'], 'view')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('contrats:detail_contrat_caution', contrat_id=contrat_id)
    
    try:
        contrat = Contrat.objects.get(id=contrat_id)
    except Contrat.DoesNotExist:
        messages.error(request, 'Contrat non trouvé.')
        return redirect('contrats:liste_contrats_caution')
    
    # Récupérer ou créer le reçu
    recu, created = RecuCaution.objects.get_or_create(contrat=contrat)
    
    # Marquer comme imprimé
    recu.marquer_imprime(request.user)
    
    # Utiliser le service PDF professionnel avec la bonne image d'en-tête
    from contrats.services import RecuCautionPDFService
    pdf_service = RecuCautionPDFService(recu)
    pdf_buffer = pdf_service.generate_recu_pdf(user=request.user)
    
    # Créer la réponse HTTP
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="recu_caution_{recu.numero_recu}.pdf"'
    response.write(pdf_buffer.getvalue())
    
    return response


@login_required
def imprimer_document_contrat(request, contrat_id):
    """Imprimer le document de contrat avec le nouveau contenu unifié."""
    
    # Vérification des permissions avec la nouvelle logique
    from core.utils import check_group_permissions
    permissions = check_group_permissions(request.user, [], 'view')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('contrats:detail_contrat_caution', contrat_id=contrat_id)
    
    try:
        contrat = Contrat.objects.get(id=contrat_id)
    except Contrat.DoesNotExist:
        messages.error(request, 'Contrat non trouvé.')
        return redirect('contrats:liste_contrats_caution')
    
    # Récupérer ou créer le document
    document, created = DocumentContrat.objects.get_or_create(contrat=contrat)
    
    # Marquer comme imprimé
    document.marquer_imprime(request.user)
    
    # Récupérer la configuration de l'entreprise
    from core.models import ConfigurationEntreprise
    config = ConfigurationEntreprise.get_configuration_active()
    
    try:
        # Utiliser le nouveau service avec le contenu unifié
        from .services import ContratPDFService
        service = ContratPDFService(contrat)
        
        # Générer le PDF du contrat avec le nouveau contenu
        pdf_buffer = service.generate_contrat_pdf(use_cache=False)
        
        # Créer la réponse HTTP avec le PDF
        response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="contrat_{contrat.numero_contrat}_unifie.pdf"'
        
        messages.success(request, f'Document de contrat {contrat.numero_contrat} généré avec le nouveau contenu unifié!')
        return response
        
    except Exception as e:
        messages.error(request, f'Erreur lors de la génération du document: {str(e)}')
        return redirect('contrats:detail_contrat_caution', contrat_id=contrat_id)


# Vues pour la gestion des résiliations
@login_required
def liste_resiliations(request):
    """Liste des résiliations de contrats."""
    
    # Vérification des permissions : PRIVILEGE, ADMINISTRATION, CONTROLES peuvent voir la liste
    from core.utils import check_group_permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'CONTROLES'], 'view')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('core:dashboard')
    
    resiliations = ResiliationContrat.objects.all().order_by('-date_resiliation')
    
    # Filtres
    statut = request.GET.get('statut')
    type_resiliation = request.GET.get('type_resiliation')
    
    if statut:
        resiliations = resiliations.filter(statut=statut)
    if type_resiliation:
        resiliations = resiliations.filter(type_resiliation=type_resiliation)
    
    # Pagination
    paginator = Paginator(resiliations, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'resiliations': page_obj,  # Pour la compatibilité avec le template
        'statuts': ResiliationContrat._meta.get_field('statut').choices,
        'types_resiliation': ResiliationContrat._meta.get_field('type_resiliation').choices,
        'bailleurs': Bailleur.objects.all(),  # Pour le filtre par bailleur
        'stats': {
            'total_en_cours': ResiliationContrat.objects.filter(statut='en_cours').count(),
            'total_validees': ResiliationContrat.objects.filter(statut='validee').count(),
            'total_terminees': ResiliationContrat.objects.filter(statut='terminee').count(),
            'total_annulees': ResiliationContrat.objects.filter(statut='annulee').count(),
        }
    }
    
    return render(request, 'contrats/liste_resiliations.html', context)


@login_required
def creer_resiliation(request, contrat_id):
    """Créer une résiliation pour un contrat."""
    
    # Tous les groupes peuvent créer des résiliations
    # permissions = check_group_permissions(request.user, ['PRIVILEGE'], 'add')
    # if not permissions['allowed']:
    #     messages.error(request, permissions['message'])
    #     return redirect('contrats:liste_resiliations')
    
    try:
        contrat = Contrat.objects.get(id=contrat_id)
    except Contrat.DoesNotExist:
        messages.error(request, 'Contrat non trouvé.')
        return redirect('contrats:liste')
    
    if request.method == 'POST':
        form = ResiliationContratForm(request.POST)
        if form.is_valid():
            resiliation = form.save(commit=False)
            resiliation.contrat = contrat
            resiliation.cree_par = request.user
            resiliation.save()
            
            messages.success(request, 'Résiliation créée avec succès.')
            return redirect('contrats:detail_resiliation', resiliation_id=resiliation.id)
    else:
        form = ResiliationContratForm(initial={'contrat': contrat})
    
    context = {
        'form': form,
        'contrat': contrat,
    }
    
    return render(request, 'contrats/creer_resiliation.html', context)


@login_required
def detail_resiliation(request, resiliation_id):
    """Détail d'une résiliation."""
    
    # Vérification des permissions : PRIVILEGE, ADMINISTRATION, CONTROLES peuvent voir les détails
    from core.utils import check_group_permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'CONTROLES'], 'view')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('contrats:liste_resiliations')
    
    try:
        resiliation = ResiliationContrat.objects.get(id=resiliation_id)
    except ResiliationContrat.DoesNotExist:
        messages.error(request, 'Résiliation non trouvée.')
        return redirect('contrats:liste_resiliations')
    
    context = {
        'resiliation': resiliation,
    }
    
    return render(request, 'contrats/detail_resiliation.html', context)


@login_required
def valider_resiliation(request, resiliation_id):
    """Valider une résiliation."""
    
    # Vérification des permissions : Seul PRIVILEGE peut valider des résiliations
    from core.utils import check_group_permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE'], 'validate')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('contrats:detail_resiliation', resiliation_id=resiliation_id)
    
    try:
        resiliation = ResiliationContrat.objects.get(id=resiliation_id)
    except ResiliationContrat.DoesNotExist:
        messages.error(request, 'Résiliation non trouvée.')
        return redirect('contrats:liste_resiliations')
    
    if resiliation.statut == 'en_cours':
        resiliation.valider_resiliation(request.user)
        messages.success(request, 'Résiliation validée avec succès.')
    else:
        messages.warning(request, 'Cette résiliation ne peut pas être validée.')
    
    return redirect('contrats:detail_resiliation', resiliation_id=resiliation.id)


@login_required
def supprimer_resiliation(request, resiliation_id):
    """Supprimer définitivement une résiliation et le contrat."""
    
    # Vérification des permissions : Seul PRIVILEGE peut supprimer des résiliations
    from core.utils import check_group_permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE'], 'delete')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('contrats:detail_resiliation', resiliation_id=resiliation_id)
    
    try:
        resiliation = ResiliationContrat.objects.get(id=resiliation_id)
    except ResiliationContrat.DoesNotExist:
        messages.error(request, 'Résiliation non trouvée.')
        return redirect('contrats:liste_resiliations')
    
    if request.method == 'POST':
        motif = request.POST.get('motif', '')
        if resiliation.supprimer_definitivement(request.user, motif):
            messages.success(request, 'Résiliation et contrat supprimés définitivement.')
            return redirect('contrats:liste_resiliations')
        else:
            messages.error(request, 'Cette résiliation ne peut pas être supprimée.')
    
    context = {
        'resiliation': resiliation,
    }
    
    return render(request, 'contrats/supprimer_resiliation.html', context)


@login_required
def selectionner_contrat_resiliation(request):
    """Vue pour sélectionner un contrat à résilier."""
    
    # Tous les groupes peuvent créer des résiliations
    # permissions = check_group_permissions(request.user, ['PRIVILEGE'], 'add')
    # if not permissions['allowed']:
    #     messages.error(request, permissions['message'])
    #     return redirect('contrats:liste_resiliations')
    
    # Récupérer les contrats actifs non résiliés
    contrats = Contrat.objects.filter(
        est_actif=True,
        est_resilie=False
    ).select_related('propriete', 'locataire', 'propriete__bailleur').order_by('-date_debut')
    
    # Filtres
    bailleur_id = request.GET.get('bailleur')
    ville = request.GET.get('ville')
    locataire = request.GET.get('locataire')
    
    if bailleur_id:
        contrats = contrats.filter(propriete__bailleur_id=bailleur_id)
    if ville:
        contrats = contrats.filter(propriete__ville__icontains=ville)
    if locataire:
        contrats = contrats.filter(
            locataire__nom__icontains=locataire
        ) | contrats.filter(
            locataire__prenom__icontains=locataire
        )
    
    # Pagination
    paginator = Paginator(contrats, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Filtres pour le formulaire
    bailleurs = Bailleur.objects.all()
    villes = Propriete.objects.values_list('ville', flat=True).distinct().order_by('ville')
    
    context = {
        'page_obj': page_obj,
        'contrats': page_obj,  # Pour la compatibilité avec le template
        'bailleurs': bailleurs,
        'villes': villes,
        'total_contrats': contrats.count(),
    }
    
    return render(request, 'contrats/selectionner_contrat_resiliation.html', context)


@login_required
def resiliation_professionnelle(request, pk):
    """Vue pour afficher le formulaire de résiliation professionnel."""
    
    # Tous les groupes peuvent créer des résiliations
    # permissions = check_group_permissions(request.user, ['PRIVILEGE'], 'add')
    # if not permissions['allowed']:
    #     messages.error(request, permissions['message'])
    #     return redirect('contrats:liste_resiliations')
    
    contrat = get_object_or_404(Contrat, pk=pk)
    
    if request.method == 'POST':
        # Traitement du formulaire de résiliation professionnelle
        date_resiliation = request.POST.get('date_resiliation')
        date_liberation = request.POST.get('date_liberation')
        motif_resiliation = request.POST.get('motif_resiliation')
        delai_preavis = request.POST.get('delai_preavis')
        type_resiliation = request.POST.get('type_resiliation')
        caution_remboursee = request.POST.get('caution_remboursee') == 'on'
        charges_reglees = request.POST.get('charges_reglees') == 'on'
        observations = request.POST.get('observations', '')
        
        if date_resiliation and date_liberation and motif_resiliation:
            try:
                date_resiliation = datetime.strptime(date_resiliation, '%Y-%m-%d').date()
                date_liberation = datetime.strptime(date_liberation, '%Y-%m-%d').date()
                
                # Créer la résiliation
                resiliation = ResiliationContrat.objects.create(
                    contrat=contrat,
                    date_resiliation=date_resiliation,
                    date_liberation=date_liberation,
                    motif_resiliation=motif_resiliation,
                    delai_preavis=delai_preavis,
                    type_resiliation=type_resiliation,
                    caution_remboursee=caution_remboursee,
                    charges_reglees=charges_reglees,
                    observations=observations,
                    statut='EN_COURS',
                    cree_par=request.user
                )
                
                # Mettre à jour le contrat
                old_data = {f.name: getattr(contrat, f.name) for f in contrat._meta.fields}
                contrat.est_actif = False
                contrat.est_resilie = True
                contrat.date_resiliation = date_resiliation
                contrat.motif_resiliation = motif_resiliation
                contrat.save()
                
                # La disponibilité de la propriété est maintenant gérée automatiquement dans le modèle
                # lors de la sauvegarde du contrat résilié
                
                # Créer l'audit log
                AuditLog.objects.create(
                    utilisateur=request.user,
                    action='RESILIATION_PRO_CREEE',
                    modele='ResiliationContrat',
                    instance_id=resiliation.pk,
                    anciennes_donnees={
                        'contrat_id': contrat.pk,
                        'statut': 'ACTIF'
                    },
                    nouvelles_donnees={
                        'contrat_id': contrat.pk,
                        'statut': 'RESILIE',
                        'date_resiliation': str(date_resiliation),
                        'motif_resiliation': motif_resiliation
                    },
                    ip_address=request.META.get('REMOTE_ADDR', ''),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
                
                messages.success(request, 'Résiliation professionnelle créée avec succès.')
                return redirect('contrats:detail_resiliation', resiliation_id=resiliation.pk)
                
            except Exception as e:
                messages.error(request, f'Erreur lors de la création de la résiliation: {str(e)}')
        else:
            messages.error(request, 'Veuillez remplir tous les champs obligatoires.')
    
    context = get_context_with_entreprise_config({
        'contrat': contrat,
        'breadcrumbs': [
            {'url': 'core:dashboard', 'label': 'Tableau de bord'},
            {'url': 'contrats:liste', 'label': 'Contrats'},
            {'url': 'contrats:liste_resiliations', 'label': 'Résiliations'},
            {'label': 'Formulaire Pro'}
        ],
        'quick_actions': [
            {'url': 'contrats:detail', 'pk': contrat.pk, 'label': 'Voir le contrat', 'icon': 'bi-eye'},
            {'url': 'contrats:liste_resiliations', 'label': 'Liste des résiliations', 'icon': 'bi-list'},
        ]
    })
    
    return render(request, 'contrats/resiliation_pro.html', context)


@login_required
def telecharger_resiliation_pdf(request, pk):
    """Vue pour télécharger le formulaire de résiliation en PDF."""
    
    # Vérification des permissions : Seul PRIVILEGE peut télécharger des résiliations
    from core.utils import check_group_permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE'], 'view')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('contrats:liste_resiliations')
    
    contrat = get_object_or_404(Contrat, pk=pk)
    
    # Créer le PDF
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib import colors
    from reportlab.pdfgen import canvas
    from io import BytesIO
    from django.http import HttpResponse
    
    # Créer le buffer pour le PDF
    buffer = BytesIO()
    
    # Créer le document PDF
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        alignment=1,  # Centré
        textColor=colors.darkblue
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=20,
        textColor=colors.darkblue
    )
    
    normal_style = styles['Normal']
    normal_style.fontSize = 10
    normal_style.spaceAfter = 12
    
    # Contenu du PDF
    story = []
    
    # Titre principal
    story.append(Paragraph("FORMULAIRE DE RÉSILIATION DE BAIL", title_style))
    story.append(Spacer(1, 20))
    
    # Informations du contrat
    story.append(Paragraph("INFORMATIONS DU CONTRAT", subtitle_style))
    story.append(Paragraph(f"<b>Numéro de contrat :</b> {contrat.numero_contrat}", normal_style))
    story.append(Paragraph(f"<b>Date de création :</b> {contrat.date_creation.strftime('%d/%m/%Y')}", normal_style))
    story.append(Spacer(1, 15))
    
    # Informations du bailleur
    story.append(Paragraph("INFORMATIONS DU BAILLEUR", subtitle_style))
    story.append(Paragraph(f"<b>Nom et prénom :</b> {contrat.propriete.bailleur.nom} {contrat.propriete.bailleur.prenom}", normal_style))
    story.append(Paragraph(f"<b>Adresse :</b> {contrat.propriete.bailleur.adresse}", normal_style))
    story.append(Paragraph(f"<b>Téléphone :</b> {contrat.propriete.bailleur.telephone}", normal_style))
    story.append(Paragraph(f"<b>Email :</b> {contrat.propriete.bailleur.email}", normal_style))
    story.append(Spacer(1, 15))
    
    # Informations du locataire
    story.append(Paragraph("INFORMATIONS DU LOCATAIRE", subtitle_style))
    story.append(Paragraph(f"<b>Nom et prénom :</b> {contrat.locataire.nom} {contrat.locataire.prenom}", normal_style))
    story.append(Paragraph(f"<b>Adresse :</b> {contrat.locataire.adresse}", normal_style))
    story.append(Paragraph(f"<b>Téléphone :</b> {contrat.locataire.telephone}", normal_style))
    story.append(Paragraph(f"<b>Email :</b> {contrat.locataire.email}", normal_style))
    story.append(Spacer(1, 15))
    
    # Informations du bien
    story.append(Paragraph("INFORMATIONS DU BIEN", subtitle_style))
    story.append(Paragraph(f"<b>Adresse :</b> {contrat.propriete.adresse}", normal_style))
    story.append(Paragraph(f"<b>Ville :</b> {contrat.propriete.ville}", normal_style))
    story.append(Paragraph(f"<b>Code postal :</b> {contrat.propriete.code_postal}", normal_style))
    story.append(Paragraph(f"<b>Type :</b> {contrat.propriete.get_type_display()}", normal_style))
    story.append(Spacer(1, 15))
    
    # Détails du contrat
    story.append(Paragraph("DÉTAILS DU CONTRAT", subtitle_style))
    story.append(Paragraph(f"<b>Date de début :</b> {contrat.date_debut.strftime('%d/%m/%Y')}", normal_style))
    story.append(Paragraph(f"<b>Date de fin initiale :</b> {contrat.date_fin.strftime('%d/%m/%Y') if contrat.date_fin else 'Non définie'}", normal_style))
    story.append(Paragraph(f"<b>Loyer mensuel :</b> {contrat.get_loyer_mensuel_formatted()}", normal_style))
    story.append(Paragraph(f"<b>Charges mensuelles :</b> {contrat.get_charges_mensuelles_formatted()}", normal_style))
    story.append(Spacer(1, 20))
    
    # Section résiliation
    story.append(Paragraph("INFORMATIONS DE RÉSILIATION", subtitle_style))
    story.append(Paragraph("Ce formulaire doit être complété avec les informations suivantes :", normal_style))
    story.append(Spacer(1, 15))
    
    # Tableau des informations à remplir
    data = [
        ['Champ', 'Valeur à remplir'],
        ['Date de résiliation', '_________________'],
        ['Date de libération', '_________________'],
        ['Motif de résiliation', '_________________'],
        ['Délai de préavis', '_________________'],
        ['Type de résiliation', '_________________'],
    ]
    
    table = Table(data, colWidths=[6*cm, 8*cm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(table)
    story.append(Spacer(1, 20))
    
    # Conditions et signatures
    story.append(Paragraph("CONDITIONS ET SIGNATURES", subtitle_style))
    story.append(Paragraph("Ce formulaire doit être signé par les deux parties pour être valide.", normal_style))
    story.append(Spacer(1, 20))
    
    # Espaces pour signatures
    signature_data = [
        ['Signature du bailleur', 'Signature du locataire'],
        ['', ''],
        ['', ''],
        ['', ''],
        ['Date: _____________', 'Date: _____________'],
    ]
    
    signature_table = Table(signature_data, colWidths=[8*cm, 8*cm])
    signature_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('MINIMUMHEIGHT', (0, 1), (-1, 3), 60),  # Hauteur pour les signatures
    ]))
    
    story.append(signature_table)
    
    # Construire le PDF
    doc.build(story)
    
    # Récupérer le contenu du buffer
    pdf = buffer.getvalue()
    buffer.close()
    
    # Créer la réponse HTTP
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="resiliation_professionnelle_{contrat.numero_contrat}.pdf"'
    response.write(pdf)
    
    return response


# Nouvelles vues pour la génération PDF
@login_required
def generer_contrat_pdf(request, pk):
    """
    Vue pour générer le PDF d'un contrat existant
    """
    # Vérification des permissions
    from core.utils import check_group_permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'CONTROLES'], 'view')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('contrats:liste')
    
    contrat = get_object_or_404(Contrat, pk=pk)
    
    try:
        # Générer le PDF du contrat avec le service mis à jour
        from .services import ContratPDFService
        pdf_service = ContratPDFService(contrat)
        pdf_buffer = pdf_service.generate_contrat_pdf(use_cache=False, user=request.user)
        
        # Créer la réponse HTTP avec le PDF
        from django.http import HttpResponse
        response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="contrat_{contrat.numero_contrat}.pdf"'
        
        messages.success(request, f'PDF du contrat {contrat.numero_contrat} généré avec succès!')
        return response
        
    except Exception as e:
        messages.error(request, f'Erreur lors de la génération du PDF: {str(e)}')
        return redirect('contrats:detail', pk=pk)


@login_required
def generer_resiliation_pdf(request, pk):
    """
    Vue pour générer le PDF d'une résiliation existante
    """
    # Vérification des permissions
    from core.utils import check_group_permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'CONTROLES'], 'view')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('contrats:liste')
    
    resiliation = get_object_or_404(ResiliationContrat, pk=pk)
    
    try:
        # Générer le PDF de la résiliation
        from .services import ResiliationPDFService
        pdf_service = ResiliationPDFService(resiliation)
        pdf_buffer = pdf_service.generate_resiliation_pdf(user=request.user)
        
        # Créer la réponse HTTP avec le PDF
        from django.http import HttpResponse
        response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="resiliation_{resiliation.contrat.numero_contrat}.pdf"'
        
        messages.success(request, f'PDF de la résiliation du contrat {resiliation.contrat.numero_contrat} généré avec succès!')
        return response
        
    except Exception as e:
        messages.error(request, f'Erreur lors de la génération du PDF: {str(e)}')
        return redirect('contrats:detail_resiliation', resiliation_id=pk)


@login_required
def generer_resiliation_contrat_pdf(request, pk):
    """
    Vue pour générer le PDF de résiliation d'un contrat existant
    """
    # Vérification des permissions
    from core.utils import check_group_permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'CONTROLES'], 'view')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('contrats:liste')
    
    contrat = get_object_or_404(Contrat, pk=pk)
    
    try:
        # Créer une résiliation temporaire pour la génération du PDF
        from .models import ResiliationContrat
        resiliation_temp = ResiliationContrat(
            contrat=contrat,
            date_resiliation=timezone.now().date(),
            motif_resiliation="À compléter",
            type_resiliation="locataire",
            cree_par=request.user
        )
        
        # Générer le PDF de la résiliation
        from .services import ResiliationPDFService
        pdf_service = ResiliationPDFService(resiliation_temp)
        pdf_buffer = pdf_service.generate_resiliation_pdf(user=request.user)
        
        # Créer la réponse HTTP avec le PDF
        from django.http import HttpResponse
        response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="resiliation_{contrat.numero_contrat}.pdf"'
        
        messages.success(request, f'PDF de résiliation pour le contrat {contrat.numero_contrat} généré avec succès!')
        return response
        
    except Exception as e:
        messages.error(request, f'Erreur lors de la génération du PDF: {str(e)}')
        return redirect('contrats:detail', pk=pk)


def contrats_dashboard(request):
    """
    Dashboard principal des contrats avec vue d'ensemble et accès contextuel aux listes
    """
    # Statistiques générales
    total_contrats = Contrat.objects.filter(is_deleted=False).count()
    contrats_actifs = Contrat.objects.filter(is_deleted=False, est_actif=True).count()
    contrats_expires = Contrat.objects.filter(is_deleted=False, est_actif=False).count()
    contrats_resilies = Contrat.objects.filter(is_deleted=False, est_resilie=True).count()
    
    # Contrats expirant bientôt (dans les 30 prochains jours)
    date_limite = timezone.now().date() + timedelta(days=30)
    contrats_expiration_proche = Contrat.objects.filter(
        is_deleted=False,
        est_actif=True,
        date_fin__lte=date_limite
    ).select_related('propriete', 'locataire')[:5]
    
    # Contrats récents
    contrats_recents = Contrat.objects.filter(
        is_deleted=False
    ).select_related('propriete', 'locataire').order_by('-date_creation')[:5]
    
    # Contrats nécessitant attention
    contrats_attention = Contrat.objects.filter(
        is_deleted=False
    ).filter(
        Q(est_actif=True, date_fin__lt=timezone.now().date()) |
        Q(est_actif=True, date_fin__lte=date_limite)
    ).select_related('propriete', 'locataire')[:5]
    
    # Top propriétés par nombre de contrats
    top_proprietes_contrats = Contrat.objects.filter(
        is_deleted=False
    ).values(
        'propriete__titre', 
        'propriete__ville'
    ).annotate(
        count=Count('id')
    ).order_by('-count')[:5]
    
    context = {
        'total_contrats': total_contrats,
        'contrats_actifs': contrats_actifs,
        'contrats_expires': contrats_expires,
        'contrats_resilies': contrats_resilies,
        'contrats_expiration_proche': contrats_expiration_proche,
        'contrats_recents': contrats_recents,
        'contrats_attention': contrats_attention,
        'top_proprietes_contrats': top_proprietes_contrats,
    }
    
    return render(request, 'contrats/dashboard.html', context)


@login_required
def occupation_propriete(request, propriete_id):
    """
    Vue unifiée pour visualiser l'occupation des unités et pièces d'une grande propriété.
    """
    from core.utils import check_group_permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'CONTROLES'], 'view')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('proprietes:liste')
    
    propriete = get_object_or_404(Propriete, pk=propriete_id)
    
    # Récupérer toutes les unités locatives de cette propriété
    from proprietes.models import UniteLocative, Piece, PieceContrat
    unites_locatives = UniteLocative.objects.filter(propriete=propriete)
    
    # Récupérer toutes les pièces de cette propriété
    pieces = Piece.objects.filter(propriete=propriete)
    
    # Contrats actifs pour cette propriété
    contrats_actifs = Contrat.objects.filter(
        propriete=propriete,
        est_actif=True,
        est_resilie=False
    ).select_related('locataire', 'unite_locative')
    
    # Statistiques d'occupation
    occupation_data = {
        'unites_locatives': [],
        'pieces_individuelles': [],
        'statistiques': {
            'total_unites': unites_locatives.count(),
            'unites_occupees': 0,
            'total_pieces': pieces.count(),
            'pieces_occupees': 0,
            'revenus_mensuels_total': 0,
            'taux_occupation_unites': 0,
            'taux_occupation_pieces': 0,
        }
    }
    
    # Traitement des unités locatives
    for unite in unites_locatives:
        contrat_unite = contrats_actifs.filter(unite_locative=unite).first()
        unite_data = {
            'unite': unite,
            'contrat': contrat_unite,
            'statut': 'occupee' if contrat_unite else 'libre',
            'locataire': contrat_unite.locataire if contrat_unite else None,
            'loyer_mensuel': float(contrat_unite.loyer_mensuel) if contrat_unite and contrat_unite.loyer_mensuel else 0,
            'charges_mensuelles': float(contrat_unite.charges_mensuelles) if contrat_unite and contrat_unite.charges_mensuelles else 0,
            'date_debut': contrat_unite.date_debut if contrat_unite else None,
            'date_fin': contrat_unite.date_fin if contrat_unite else None,
        }
        occupation_data['unites_locatives'].append(unite_data)
        
        if contrat_unite:
            occupation_data['statistiques']['unites_occupees'] += 1
            occupation_data['statistiques']['revenus_mensuels_total'] += unite_data['loyer_mensuel'] + unite_data['charges_mensuelles']
    
    # Traitement des pièces individuelles
    for piece in pieces:
        # Récupérer les contrats actifs pour cette pièce
        pieces_contrats = PieceContrat.objects.filter(
            piece=piece,
            actif=True,
            contrat__est_actif=True,
            contrat__est_resilie=False
        ).select_related('contrat', 'contrat__locataire')
        
        piece_data = {
            'piece': piece,
            'contrats': [],
            'statut': 'occupee' if pieces_contrats.exists() else 'libre',
            'revenus_mensuels': 0,
        }
        
        for piece_contrat in pieces_contrats:
            contrat_data = {
                'contrat': piece_contrat.contrat,
                'locataire': piece_contrat.contrat.locataire,
                'loyer_piece': float(piece_contrat.loyer_piece) if piece_contrat.loyer_piece else 0,
                'charges_piece': float(piece_contrat.charges_piece) if piece_contrat.charges_piece else 0,
                'date_debut': piece_contrat.date_debut_occupation,
                'date_fin': piece_contrat.date_fin_occupation,
            }
            piece_data['contrats'].append(contrat_data)
            piece_data['revenus_mensuels'] += contrat_data['loyer_piece'] + contrat_data['charges_piece']
        
        occupation_data['pieces_individuelles'].append(piece_data)
        
        if pieces_contrats.exists():
            occupation_data['statistiques']['pieces_occupees'] += 1
            occupation_data['statistiques']['revenus_mensuels_total'] += piece_data['revenus_mensuels']
    
    # Calcul des taux d'occupation
    if occupation_data['statistiques']['total_unites'] > 0:
        occupation_data['statistiques']['taux_occupation_unites'] = round(
            (occupation_data['statistiques']['unites_occupees'] / occupation_data['statistiques']['total_unites']) * 100, 1
        )
    
    if occupation_data['statistiques']['total_pieces'] > 0:
        occupation_data['statistiques']['taux_occupation_pieces'] = round(
            (occupation_data['statistiques']['pieces_occupees'] / occupation_data['statistiques']['total_pieces']) * 100, 1
        )
    
    # Informations générales sur la propriété
    context = {
        'propriete': propriete,
        'occupation_data': occupation_data,
        'contrats_actifs': contrats_actifs,
        'date_actuelle': timezone.now().date(),
    }
    
    return render(request, 'contrats/occupation_propriete.html', context)


@login_required
def gestion_cautions(request):
    """
    Vue principale pour la gestion des cautions
    """
    # Vérification des permissions : PRIVILEGE, ADMINISTRATION, COMPTABILITE, CAISSE peuvent gérer les cautions
    from core.utils import check_group_permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE', 'CAISSE'], 'view')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('contrats:liste')
    
    # Récupérer les contrats avec leurs cautions
    contrats_avec_cautions = Contrat.objects.filter(
        depot_garantie__isnull=False
    ).exclude(
        depot_garantie__exact=''
    ).exclude(
        depot_garantie__exact='0.00'
    ).select_related('propriete', 'locataire')
    
    # Statistiques des cautions
    total_cautions = sum(float(contrat.depot_garantie) for contrat in contrats_avec_cautions if contrat.depot_garantie)
    cautions_payees = 0
    cautions_en_attente = 0
    cautions_remboursees = 0
    
    # Récupérer les paiements de caution
    from paiements.models import Paiement
    paiements_caution = Paiement.objects.filter(
        type_paiement__in=['caution', 'depot_garantie']
    ).select_related('contrat', 'contrat__propriete', 'contrat__locataire')
    
    # Calculer les statistiques
    for contrat in contrats_avec_cautions:
        montant_caution = float(contrat.depot_garantie) if contrat.depot_garantie else 0
        paiements_contrat = paiements_caution.filter(contrat=contrat)
        
        if paiements_contrat.exists():
            montant_paye = sum(float(p.montant) for p in paiements_contrat)
            if montant_paye >= montant_caution:
                cautions_payees += montant_caution
            else:
                cautions_en_attente += montant_caution
        else:
            cautions_en_attente += montant_caution
    
    # Récupérer les remboursements de caution
    remboursements_caution = Paiement.objects.filter(
        type_paiement='remboursement_caution'
    ).select_related('contrat', 'contrat__propriete', 'contrat__locataire')
    
    cautions_remboursees = sum(float(r.montant) for r in remboursements_caution)
    
    # Calculer le pourcentage de paiement
    pourcentage_paiement = 0
    if total_cautions > 0:
        pourcentage_paiement = (cautions_payees / total_cautions) * 100
    
    context = {
        'title': 'Gestion des Cautions',
        'contrats_avec_cautions': contrats_avec_cautions,
        'paiements_caution': paiements_caution,
        'remboursements_caution': remboursements_caution,
        'statistiques': {
            'total_cautions': total_cautions,
            'cautions_payees': cautions_payees,
            'cautions_en_attente': cautions_en_attente,
            'cautions_remboursees': cautions_remboursees,
            'nombre_contrats': contrats_avec_cautions.count(),
            'nombre_paiements': paiements_caution.count(),
            'nombre_remboursements': remboursements_caution.count(),
            'pourcentage_paiement': pourcentage_paiement,
        }
    }
    
    return render(request, 'contrats/gestion_cautions.html', context)


@login_required
def forcer_correction_statuts(request):
    """Force la correction des statuts de paiement pour tous les contrats."""
    
    # Vérification des permissions : Seuls PRIVILEGE et ADMINISTRATION peuvent forcer la correction
    from core.utils import check_group_permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE'], 'view')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('contrats:liste')
    
    if request.method == 'POST':
        try:
            from django.db import transaction
            from decimal import Decimal
            
            contrats_corriges = 0
            contrats_avec_problemes = 0
            
            with transaction.atomic():
                # Récupérer tous les contrats actifs
                contrats = Contrat.objects.filter(
                    est_actif=True,
                    est_resilie=False
                ).select_related('propriete', 'locataire')
                
                for contrat in contrats:
                    # Montants requis
                    caution_requise = Decimal(str(contrat.depot_garantie)) if contrat.depot_garantie else Decimal('0')
                    avance_requise = Decimal(str(contrat.avance_loyer)) if contrat.avance_loyer else Decimal('0')
                    
                    # Calculer les montants payés avec tous les types possibles
                    paiements_caution = Paiement.objects.filter(
                        contrat=contrat,
                        type_paiement='caution',
                        statut='valide'
                    )
                    
                    montant_caution_paye = sum(p.montant for p in paiements_caution)
                    
                    paiements_avance = Paiement.objects.filter(
                        contrat=contrat,
                        type_paiement='avance',
                        statut='valide'
                    )
                    
                    montant_avance_paye = sum(p.montant for p in paiements_avance)
                    
                    # Vérifier les statuts
                    caution_payee = montant_caution_paye >= caution_requise if caution_requise > 0 else True
                    avance_payee = montant_avance_paye >= avance_requise if avance_requise > 0 else True
                    
                    # Mettre à jour les champs du contrat
                    contrat_modified = False
                    
                    if contrat.caution_payee != caution_payee:
                        contrat.caution_payee = caution_payee
                        contrat_modified = True
                    
                    if contrat.avance_loyer_payee != avance_payee:
                        contrat.avance_loyer_payee = avance_payee
                        contrat_modified = True
                    
                    if contrat_modified:
                        contrat.save()
                        contrats_corriges += 1
                    
                    # Vérifier les problèmes
                    if caution_requise > 0 and not caution_payee:
                        contrats_avec_problemes += 1
                    
                    if avance_requise > 0 and not avance_payee:
                        contrats_avec_problemes += 1
            
            messages.success(
                request, 
                f'Correction terminée ! {contrats_corriges} contrats corrigés, {contrats_avec_problemes} contrats avec des problèmes.'
            )
            
        except Exception as e:
            messages.error(request, f'Erreur lors de la correction : {str(e)}')
    
    return redirect('contrats:liste_contrats_caution')


# Vues de suppression génériques
class SupprimerContratView(SuppressionGeneriqueView):
    model = Contrat
    
    def get_redirect_url(self, obj):
        return 'contrats:liste'
    
    def get_success_message(self, obj):
        return f"Contrat {obj.numero_contrat} supprimé avec succès."
