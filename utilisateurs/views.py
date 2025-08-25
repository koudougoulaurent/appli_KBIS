from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden
from django.db.models import Q, Count, Sum, ProtectedError
from django.core.paginator import Paginator
from django.utils import timezone
from .models import Utilisateur, GroupeTravail
from .forms import UtilisateurForm, GroupeTravailForm
from .decorators import groupe_required
import json
from core.models import AuditLog
from django.contrib.contenttypes.models import ContentType
from core.intelligent_views import IntelligentListView
from django.views.generic import CreateView, UpdateView
from proprietes.models import Bailleur, Locataire, Propriete, TypeBien, ChargesBailleur
from core.models import TemplateRecu, Devise, ConfigurationEntreprise
from django.urls import reverse, reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .mixins import PrivilegeDeleteMixin, PrivilegeRequiredMixin, PrivilegeButtonsMixin

def connexion_groupes(request):
    """Page de connexion des groupes de travail - première page de l'application"""
    
    if request.method == 'POST':
        groupe_nom = request.POST.get('groupe')
        
        if groupe_nom:
            try:
                groupe = GroupeTravail.objects.get(nom=groupe_nom, actif=True)
                # Stocker le groupe sélectionné en session
                request.session['groupe_selectionne'] = groupe_nom
                return redirect('utilisateurs:login_groupe', groupe_nom=groupe_nom)
            except GroupeTravail.DoesNotExist:
                messages.error(request, f"Le groupe {groupe_nom} n'existe pas ou n'est pas actif.")
        else:
            messages.error(request, "Veuillez sélectionner un groupe de travail.")
    
    # Récupérer tous les groupes actifs
    groupes = GroupeTravail.objects.filter(actif=True).order_by('nom')
    
    context = {
        'groupes': groupes,
        'titre_page': 'Connexion des Utilisateurs',
        'version_app': 'GESTIMMOB version 5.0.1'
    }
    
    return render(request, 'utilisateurs/connexion_groupes.html', context)

def login_groupe(request, groupe_nom):
    """Page de connexion spécifique à un groupe - OPTIMISÉE"""
    
    # Vérifier que le groupe existe et est actif - OPTIMISÉ
    try:
        groupe = GroupeTravail.objects.select_related().get(nom=groupe_nom, actif=True)
    except GroupeTravail.DoesNotExist:
        messages.error(request, f"Le groupe {groupe_nom} n'existe pas ou n'est pas actif.")
        return redirect('utilisateurs:connexion_groupes')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        if username and password:
            # Optimisation : Authentification plus rapide
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                # Vérifier que l'utilisateur appartient au bon groupe - OPTIMISÉ
                if user.groupe_travail and user.groupe_travail.nom == groupe_nom:
                    if user.actif:
                        login(request, user)
                        
                        # Optimisation : Mise à jour de la dernière connexion sans requête supplémentaire
                        user.derniere_connexion = timezone.now()
                        user.save(update_fields=['derniere_connexion'])
                        
                        messages.success(request, f"Connexion réussie ! Bienvenue dans le groupe {groupe_nom}.")
                        
                        # Rediriger vers le dashboard du groupe
                        return redirect('utilisateurs:dashboard_groupe', groupe_nom=groupe_nom)
                    else:
                        messages.error(request, "Votre compte est désactivé. Contactez l'administrateur.")
                else:
                    messages.error(request, f"Vous n'avez pas accès au groupe {groupe_nom}.")
            else:
                messages.error(request, "Nom d'utilisateur ou mot de passe incorrect.")
        else:
            messages.error(request, "Veuillez remplir tous les champs.")
    
    context = {
        'groupe': groupe,
        'titre_page': f'Connexion - {groupe_nom}',
        'version_app': 'GESTIMMOB version 6.0'
    }
    
    return render(request, 'utilisateurs/login_groupe.html', context)

@groupe_required
def dashboard_groupe(request, groupe_nom):
    """Dashboard spécifique au groupe de travail - OPTIMISÉ"""
    utilisateur = request.user
    
    # Vérifier que l'utilisateur appartient au bon groupe
    if not utilisateur.groupe_travail or utilisateur.groupe_travail.nom != groupe_nom:
        messages.error(request, "Vous n'avez pas accès à ce dashboard.")
        return redirect('utilisateurs:connexion_groupes')
    
    groupe = utilisateur.groupe_travail
    
    # Récupérer les modules accessibles au groupe
    modules_accessibles = groupe.get_permissions_list()
    
    # Statistiques selon le groupe avec vraies données - OPTIMISÉ
    stats = {}
    derniers_elements = {}
    
    if groupe_nom == 'CAISSE':
        from paiements.models import Paiement, Retrait
        from django.db.models import Sum
        from datetime import datetime
        
        # Optimisation : Une seule requête pour toutes les stats
        mois_courant = datetime.now().month
        annee_courante = datetime.now().year
        
        # Requête optimisée pour les statistiques
        stats_paiements = Paiement.objects.filter(
            date_paiement__month=mois_courant,
            date_paiement__year=annee_courante
        ).aggregate(
            total_paiements=Sum('montant'),
            count_paiements=Count('id')
        )
        
        stats_retraits = Retrait.objects.filter(
            date_demande__month=mois_courant,
            date_demande__year=annee_courante
        ).aggregate(
            total_retraits=Sum('montant_net_a_payer')
        )
        
        stats_cautions = Paiement.objects.filter(
            type_paiement='depot_garantie',
            statut='valide'
        ).aggregate(
            total_cautions=Sum('montant')
        )
        
        stats_attente = Paiement.objects.filter(statut='en_attente').count()
        
        stats = {
            'paiements_mois': stats_paiements['total_paiements'] or 0,
            'retraits_mois': stats_retraits['total_retraits'] or 0,
            'cautions_cours': stats_cautions['total_cautions'] or 0,
            'paiements_attente': stats_attente,
        }
        
        # Derniers paiements avec select_related pour optimiser
        derniers_elements['derniers_paiements'] = Paiement.objects.select_related(
            'contrat__locataire', 'contrat__propriete'
        ).order_by('-date_paiement')[:5]
        
    elif groupe_nom == 'ADMINISTRATION':
        from proprietes.models import Propriete, Bailleur
        from contrats.models import Contrat
        from datetime import datetime, timedelta
        
        # Optimisation : Requêtes groupées
        stats_proprietes = Propriete.objects.aggregate(
            total=Count('id')
        )
        
        stats_contrats = Contrat.objects.aggregate(
            actifs=Count('id', filter=Q(est_actif=True)),
            renouveler=Count('id', filter=Q(
                date_fin__lte=datetime.now() + timedelta(days=30),
                est_actif=True
            ))
        )
        
        stats_bailleurs = Bailleur.objects.aggregate(
            total=Count('id')
        )
        
        stats = {
            'total_proprietes': stats_proprietes['total'],
            'contrats_actifs': stats_contrats['actifs'],
            'total_bailleurs': stats_bailleurs['total'],
            'contrats_renouveler': stats_contrats['renouveler'],
        }
        
        # Derniers contrats avec select_related
        derniers_contrats = Contrat.objects.select_related(
            'locataire', 'propriete'
        ).order_by('-date_debut')[:5]
        
        # Ajouter le montant du loyer annuel à chaque contrat
        for contrat in derniers_contrats:
            contrat.montant_loyer_annuel = contrat.loyer_mensuel * 12
        
        derniers_elements['derniers_contrats'] = derniers_contrats
        
    elif groupe_nom == 'CONTROLES':
        from paiements.models import Paiement
        from contrats.models import Contrat
        
        # Optimisation : Requêtes groupées
        stats_controles = Paiement.objects.aggregate(
            a_valider=Count('id', filter=Q(statut='en_attente'))
        )
        
        stats_contrats = Contrat.objects.aggregate(
            a_verifier=Count('id', filter=Q(est_actif=True))
        )
        
        stats = {
            'paiements_a_valider': stats_controles['a_valider'],
            'contrats_a_verifier': stats_contrats['a_verifier'],
            'anomalies': 0,  # À implémenter selon vos besoins
            'rapports_generes': 0,  # À implémenter selon vos besoins
        }
        
        # Derniers contrôles (à adapter selon vos besoins)
        derniers_elements['derniers_controles'] = []
        
    elif groupe_nom == 'PRIVILEGE':
        from proprietes.models import Propriete, Bailleur, Locataire
        from utilisateurs.models import Utilisateur
        from paiements.models import Paiement
        from contrats.models import Contrat
        from notifications.models import Notification
        
        # Optimisation : Requêtes groupées
        stats_systeme = {
            'proprietes': Propriete.objects.count(),
            'utilisateurs': Utilisateur.objects.count(),
            'contrats': Contrat.objects.count(),
            'paiements': Paiement.objects.count(),
            'groupes': GroupeTravail.objects.count(),
            'notifications': Notification.objects.count(),
            'utilisateurs_actifs': Utilisateur.objects.filter(actif=True).count(),
            'bailleurs': Bailleur.objects.filter(actif=True).count(),
            'locataires': Locataire.objects.filter(statut='actif').count(),
            'contrats_actifs': Contrat.objects.filter(est_actif=True).count(),
        }
        
        stats = {
            'total_proprietes': stats_systeme['proprietes'],
            'total_utilisateurs': stats_systeme['utilisateurs'],
            'total_contrats': stats_systeme['contrats'],
            'total_paiements': stats_systeme['paiements'],
            'total_groupes': stats_systeme['groupes'],
            'total_notifications': stats_systeme['notifications'],
            'utilisateurs_actifs': stats_systeme['utilisateurs_actifs'],
            'total_bailleurs': stats_systeme['bailleurs'],
            'total_locataires': stats_systeme['locataires'],
            'contrats_actifs': stats_systeme['contrats_actifs'],
        }
        
        # Activité récente (à adapter selon vos besoins)
        derniers_elements['activite_recente'] = []
    
    # Déterminer le template selon le groupe
    template_mapping = {
        'CAISSE': 'utilisateurs/dashboard_caisse.html',
        'ADMINISTRATION': 'utilisateurs/dashboard_administration.html',
        'CONTROLES': 'utilisateurs/dashboard_controles.html',
        'PRIVILEGE': 'utilisateurs/dashboard_privilege.html',
    }
    
    template_name = template_mapping.get(groupe_nom, 'utilisateurs/dashboard_groupe.html')
    
    context = {
        'groupe': groupe,
        'utilisateur': utilisateur,
        'modules_accessibles': modules_accessibles,
        'stats': stats,
        'derniers_elements': derniers_elements,
        'titre_page': f'Dashboard - {groupe_nom}',
        'version_app': 'GESTIMMOB version 6.0'
    }
    

    
    return render(request, template_name, context)

def logout_groupe(request):
    """Déconnexion et retour à la page de sélection des groupes"""
    logout(request)
    if 'groupe_selectionne' in request.session:
        del request.session['groupe_selectionne']
    messages.success(request, "Vous avez été déconnecté avec succès.")
    return redirect('utilisateurs:connexion_groupes')

# Vues existantes mises à jour
class UtilisateurListView(PrivilegeButtonsMixin, IntelligentListView):
    model = Utilisateur
    template_name = 'base_liste_intelligente.html'
    paginate_by = 20
    page_title = 'Utilisateurs'
    page_icon = 'users'
    add_url = 'utilisateurs:ajouter_utilisateur'
    add_text = 'Ajouter un utilisateur'
    search_fields = ['username', 'first_name', 'last_name', 'email', 'telephone', 'poste', 'departement']
    filter_fields = ['groupe_travail', 'actif']
    default_sort = 'username'
    columns = [
        {'field': 'username', 'label': 'Nom d\'utilisateur', 'sortable': True},
        {'field': 'first_name', 'label': 'Prénom', 'sortable': True},
        {'field': 'last_name', 'label': 'Nom', 'sortable': True},
        {'field': 'email', 'label': 'Email', 'sortable': True},
        {'field': 'telephone', 'label': 'Téléphone', 'sortable': True},
        {'field': 'poste', 'label': 'Poste', 'sortable': True},
        {'field': 'departement', 'label': 'Département', 'sortable': True},
        {'field': 'actif', 'label': 'Actif', 'sortable': True},
    ]
    actions = [
        {'url_name': 'utilisateurs:detail_utilisateur', 'icon': 'eye', 'style': 'outline-primary', 'title': 'Voir'},
        {'url_name': 'utilisateurs:modifier_utilisateur', 'icon': 'pencil', 'style': 'outline-warning', 'title': 'Modifier'},
    ]
    sort_options = [
        {'value': 'username', 'label': 'Nom d\'utilisateur'},
        {'value': 'first_name', 'label': 'Prénom'},
        {'value': 'last_name', 'label': 'Nom'},
        {'value': 'email', 'label': 'Email'},
        {'value': 'poste', 'label': 'Poste'},
        {'value': 'departement', 'label': 'Département'},
    ]
    
    def get_queryset(self):
        """
        Optimisation des requêtes de base de données
        """
        queryset = super().get_queryset()
        return queryset.select_related('groupe_travail').prefetch_related('groups', 'user_permissions')
    
    def get_context_data(self, **kwargs):
        """
        Ajout de statistiques et d'informations supplémentaires au contexte
        """
        context = super().get_context_data(**kwargs)
        
        # Statistiques
        context['total_utilisateurs'] = Utilisateur.objects.count()
        context['utilisateurs_actifs'] = Utilisateur.objects.filter(actif=True).count()
        context['utilisateurs_inactifs'] = Utilisateur.objects.filter(actif=False).count()
        
        # Groupes pour les filtres
        context['groupes'] = GroupeTravail.objects.all()
        
        return context

utilisateur_list = UtilisateurListView.as_view()

@login_required
def detail_utilisateur(request, pk):
    """Détail d'un utilisateur"""
    # Vérification des permissions : PRIVILEGE, ADMINISTRATION, CONTROLES peuvent voir les détails
    from core.utils import check_group_permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'CONTROLES', 'CAISSE'], 'view')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('utilisateurs:liste')
    
    utilisateur = get_object_or_404(Utilisateur, pk=pk)
    
    context = {
        'utilisateur': utilisateur,
    }
    
    return render(request, 'utilisateurs/detail.html', context)

@login_required
def ajouter_utilisateur(request):
    """Ajouter un nouvel utilisateur"""
    # Vérification des permissions : PRIVILEGE et ADMINISTRATION peuvent ajouter
    from core.utils import check_group_permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE'], 'add')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('utilisateurs:liste_utilisateurs')
    
    if request.method == 'POST':
        # Créer une copie des données POST pour inclure country_code
        post_data = request.POST.copy()
        
        # Si country_code est dans request.POST, l'ajouter explicitement
        if 'country_code' in request.POST:
            post_data['country_code'] = request.POST['country_code']
        
        form = UtilisateurForm(post_data, request.FILES)
        if form.is_valid():
            utilisateur = form.save(commit=False)
            utilisateur.set_password(form.cleaned_data['password'])
            utilisateur.save()
            messages.success(request, f"Utilisateur {utilisateur.username} créé avec succès.")
            return redirect('utilisateurs:detail_utilisateur', pk=utilisateur.pk)
        else:
            print(f"DEBUG - Erreurs de validation du formulaire:")
            print(f"  {form.errors}")
    else:
        form = UtilisateurForm()
    
    context = {
        'form': form,
        'titre': 'Ajouter un utilisateur'
    }
    
    return render(request, 'utilisateurs/ajouter.html', context)

@login_required
def modifier_utilisateur(request, pk):
    """Modifier un utilisateur existant"""
    # Vérification des permissions : Seul PRIVILEGE peut modifier
    from core.utils import check_group_permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE'], 'modify')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('utilisateurs:liste_utilisateurs')
    
    utilisateur = get_object_or_404(Utilisateur, pk=pk)
    
    if request.method == 'POST':
        form = UtilisateurForm(request.POST, request.FILES, instance=utilisateur)
        if form.is_valid():
            form.save()
            messages.success(request, f"Utilisateur {utilisateur.username} modifié avec succès.")
            return redirect('utilisateurs:detail_utilisateur', pk=utilisateur.pk)
    else:
        form = UtilisateurForm(instance=utilisateur)
    
    context = {
        'form': form,
        'utilisateur': utilisateur,
        'titre': 'Modifier un utilisateur'
    }
    
    return render(request, 'utilisateurs/ajouter.html', context)

@login_required
def supprimer_utilisateur(request, pk):
    # Vérification des permissions : Seul PRIVILEGE peut supprimer
    from core.utils import check_group_permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE'], 'delete')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('utilisateurs:liste_utilisateurs')
    utilisateur = get_object_or_404(Utilisateur, pk=pk)
    if request.method == 'POST':
        try:
            old_data = {f.name: getattr(utilisateur, f.name) for f in utilisateur._meta.fields}
            utilisateur.is_deleted = True
            utilisateur.deleted_at = timezone.now()
            utilisateur.deleted_by = request.user
            utilisateur.save()
            AuditLog.objects.create(
                content_type=ContentType.objects.get_for_model(Utilisateur),
                object_id=utilisateur.pk,
                action='DELETE',
                old_data=old_data,
                new_data=None,
                user=request.user,
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            messages.success(request, "Utilisateur supprimé avec succès (suppression logique).")
            return redirect('utilisateurs:liste_utilisateurs')
        except ProtectedError:
            messages.error(request, "Impossible de supprimer cet utilisateur car il est référencé dans d'autres enregistrements.")
            return redirect('utilisateurs:liste_utilisateurs')
    return render(request, 'utilisateurs/confirm_supprimer.html', {'utilisateur': utilisateur})

# Vues pour les groupes de travail
@login_required
def liste_groupes(request):
    """Liste des groupes de travail"""
    groupes = GroupeTravail.objects.all()
    
    context = {
        'groupes': groupes,
    }
    
    return render(request, 'utilisateurs/groupes/liste.html', context)

@login_required
def detail_groupe(request, pk):
    """Détail d'un groupe de travail"""
    # Vérification des permissions : PRIVILEGE, ADMINISTRATION, CONTROLES peuvent voir les détails
    from core.utils import check_group_permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'CONTROLES', 'CAISSE'], 'view')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('utilisateurs:liste_groupes')
    
    groupe = get_object_or_404(GroupeTravail, pk=pk)
    utilisateurs = groupe.utilisateurs.all()
    
    context = {
        'groupe': groupe,
        'utilisateurs': utilisateurs,
    }
    
    return render(request, 'utilisateurs/groupes/detail.html', context)

@login_required
def ajouter_groupe(request):
    """Ajouter un nouveau groupe de travail"""
    # Vérification des permissions : PRIVILEGE et ADMINISTRATION peuvent ajouter
    from core.utils import check_group_permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE'], 'add')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('utilisateurs:liste_groupes')
    
    if request.method == 'POST':
        form = GroupeTravailForm(request.POST)
        if form.is_valid():
            groupe = form.save()
            messages.success(request, f"Groupe {groupe.nom} créé avec succès.")
            return redirect('utilisateurs:detail_groupe', pk=groupe.pk)
    else:
        form = GroupeTravailForm()
    
    context = {
        'form': form,
        'titre': 'Ajouter un groupe de travail'
    }
    
    return render(request, 'utilisateurs/groupes/ajouter.html', context)

@login_required
def modifier_groupe(request, pk):
    """Modifier un groupe de travail"""
    # Vérification des permissions : Seul PRIVILEGE peut modifier
    from core.utils import check_group_permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE'], 'modify')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('utilisateurs:liste_groupes')
    
    groupe = get_object_or_404(GroupeTravail, pk=pk)
    
    if request.method == 'POST':
        form = GroupeTravailForm(request.POST, instance=groupe)
        if form.is_valid():
            form.save()
            messages.success(request, f"Groupe {groupe.nom} modifié avec succès.")
            return redirect('utilisateurs:detail_groupe', pk=groupe.pk)
    else:
        form = GroupeTravailForm(instance=groupe)
    
    context = {
        'form': form,
        'groupe': groupe,
        'titre': 'Modifier un groupe de travail'
    }
    
    return render(request, 'utilisateurs/groupes/ajouter.html', context)

@login_required
def profile(request):
    """Profil utilisateur"""
    user = request.user
    
    context = {
        'user': user,
        'groupe': user.groupe_travail,
        'modules_accessibles': user.get_accessible_modules() if user.groupe_travail else [],
    }
    
    return render(request, 'utilisateurs/profile.html', context)

# === VUES SPÉCIALES POUR LE GROUPE PRIVILEGE ===

def privilege_required(view_func):
    """Décorateur pour vérifier que l'utilisateur appartient au groupe PRIVILEGE"""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('utilisateurs:connexion_groupes')
        
        if not request.user.is_privilege_user():
            messages.error(request, "Accès refusé. Seuls les utilisateurs du groupe PRIVILEGE peuvent accéder à cette fonctionnalité.")
            return redirect('utilisateurs:dashboard_groupe', groupe_nom=request.user.get_groupe_display())
        
        return view_func(request, *args, **kwargs)
    return wrapper


class PrivilegeRequiredMixin(UserPassesTestMixin):
    """Mixin pour vérifier que l'utilisateur appartient au groupe PRIVILEGE"""
    
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_privilege_user()
    
    def handle_no_permission(self):
        messages.error(self.request, "Accès refusé. Seuls les utilisateurs du groupe PRIVILEGE peuvent accéder à cette fonctionnalité.")
        return redirect('utilisateurs:dashboard_groupe', groupe_nom=self.request.user.get_groupe_display())


@privilege_required
def privilege_dashboard_advanced(request):
    """Dashboard avancé pour le groupe PRIVILEGE avec fonctionnalités spéciales"""
    
    # Statistiques générales
    stats = {
        'total_utilisateurs': Utilisateur.objects.count(),
        'utilisateurs_actifs': Utilisateur.objects.filter(actif=True).count(),
        'total_bailleurs': Bailleur.objects.count(),
        'bailleurs_actifs': Bailleur.objects.filter(actif=True).count(),
        'total_locataires': Locataire.objects.count(),
        'locataires_actifs': Locataire.objects.filter(statut='actif').count(),
        'total_proprietes': Propriete.objects.count(),
        'proprietes_actives': Propriete.objects.filter(actif=True).count(),
        'total_types_bien': TypeBien.objects.count(),
        'types_bien_actifs': TypeBien.objects.filter(is_deleted=False).count(),
        'total_templates': TemplateRecu.objects.count(),
        'templates_actifs': TemplateRecu.objects.filter(actif=True).count(),
        'total_devises': Devise.objects.count(),
        'devises_actives': Devise.objects.filter(actif=True).count(),
    }
    
    # Éléments supprimés logiquement
    elements_supprimes = {
        'utilisateurs': Utilisateur.all_objects.filter(is_deleted=True).count(),
        'bailleurs': Bailleur.all_objects.filter(is_deleted=True).count(),
        'locataires': Locataire.all_objects.filter(is_deleted=True).count(),
        'proprietes': Propriete.all_objects.filter(is_deleted=True).count(),
        'types_bien': TypeBien.all_objects.filter(is_deleted=True).count(),
        'templates': 0,  # TemplateRecu n'a pas de suppression logique
        'charges_bailleur': ChargesBailleur.all_objects.filter(is_deleted=True).count(),
    }
    
    # Éléments désactivés
    elements_desactives = {
        'bailleurs': Bailleur.objects.filter(actif=False).count(),
        'locataires': Locataire.objects.filter(statut='inactif').count(),
        'proprietes': Propriete.objects.filter(actif=False).count(),
        'templates': TemplateRecu.objects.filter(actif=False).count(),
        'devises': Devise.objects.filter(actif=False).count(),
    }
    
    context = {
        'stats': stats,
        'elements_supprimes': elements_supprimes,
        'elements_desactives': elements_desactives,
        'groupe_nom': 'PRIVILEGE',
        'page_title': 'Dashboard PRIVILEGE - Gestion Avancée',
    }
    
    return render(request, 'utilisateurs/dashboard_privilege_advanced.html', context)


@privilege_required
def privilege_element_management(request):
    """Interface de gestion des éléments pour le groupe PRIVILEGE"""
    
    # Récupérer les types d'éléments disponibles
    element_types = [
        {'name': 'Bailleur', 'model': Bailleur, 'verbose_name': 'Bailleurs'},
        {'name': 'Locataire', 'model': Locataire, 'verbose_name': 'Locataires'},
        {'name': 'Propriete', 'model': Propriete, 'verbose_name': 'Propriétés'},
        {'name': 'TypeBien', 'model': TypeBien, 'verbose_name': 'Types de bien'},
        {'name': 'TemplateRecu', 'model': TemplateRecu, 'verbose_name': 'Templates de reçus'},
        {'name': 'Devise', 'model': Devise, 'verbose_name': 'Devises'},
        {'name': 'ChargesBailleur', 'model': ChargesBailleur, 'verbose_name': 'Charges bailleur'},
    ]
    
    # Statistiques par type d'élément
    element_stats = {}
    for element_type in element_types:
        model = element_type['model']
        # Compter les éléments supprimés logiquement
        supprimes = 0
        if hasattr(model, 'all_objects'):
            supprimes = model.all_objects.filter(is_deleted=True).count()
        elif hasattr(model, 'objects') and hasattr(model.objects, 'all_with_deleted'):
            supprimes = model.objects.all_with_deleted().filter(is_deleted=True).count()
        
        element_stats[element_type['name']] = {
            'total': model.objects.count(),
            'actifs': model.objects.filter(actif=True).count() if hasattr(model, 'actif') else model.objects.count(),
            'supprimes': supprimes,
            'desactives': model.objects.filter(actif=False).count() if hasattr(model, 'actif') else 0,
        }
    
    context = {
        'element_types': element_types,
        'element_stats': element_stats,
        'groupe_nom': 'PRIVILEGE',
        'page_title': 'Gestion des Éléments - PRIVILEGE',
    }
    
    return render(request, 'utilisateurs/privilege_element_management.html', context)


@privilege_required
def privilege_element_list(request, model_name):
    """Liste des éléments d'un type spécifique avec options de suppression/désactivation"""
    
    # Mapper les noms de modèles
    model_map = {
        'bailleur': Bailleur,
        'locataire': Locataire,
        'propriete': Propriete,
        'typebien': TypeBien,
        'templaterecu': TemplateRecu,
        'devise': Devise,
        'chargesbailleur': ChargesBailleur,
    }
    
    model_class = model_map.get(model_name.lower())
    if not model_class:
        messages.error(request, "Type d'élément non reconnu.")
        return redirect('utilisateurs:privilege_element_management')
    
    # Récupérer les éléments
    elements = model_class.objects.all()
    
    # Analyser chaque élément pour les permissions de suppression
    elements_with_permissions = []
    for element in elements:
        peut_supprimer, peut_désactiver, raison, détails_références = request.user.can_delete_any_element(element)
        elements_with_permissions.append({
            'element': element,
            'peut_supprimer': peut_supprimer,
            'peut_desactiver': peut_désactiver,
            'raison': raison,
            'détails_références': détails_références,
        })
    
    context = {
        'model_name': model_name,
        'model_class': model_class,
        'elements': elements_with_permissions,
        'groupe_nom': 'PRIVILEGE',
        'page_title': f'Gestion des {model_class._meta.verbose_name_plural} - PRIVILEGE',
    }
    
    return render(request, 'utilisateurs/privilege_element_list.html', context)


@require_POST
@privilege_required
def privilege_delete_element(request, model_name, element_id):
    """Supprime ou désactive un élément selon les permissions PRIVILEGE"""
    
    # Mapper les noms de modèles
    model_map = {
        'bailleur': Bailleur,
        'locataire': Locataire,
        'propriete': Propriete,
        'typebien': TypeBien,
        'templaterecu': TemplateRecu,
        'devise': Devise,
        'chargesbailleur': ChargesBailleur,
    }
    
    model_class = model_map.get(model_name.lower())
    if not model_class:
        return JsonResponse({'success': False, 'message': "Type d'élément non reconnu."})
    
    try:
        element = model_class.objects.get(id=element_id)
    except model_class.DoesNotExist:
        return JsonResponse({'success': False, 'message': "Élément non trouvé."})
    
    # Utiliser la méthode de suppression sécurisée
    success, message, action, détails_références = request.user.safe_delete_element(element, request)
    
    if success:
        messages.success(request, message)
    else:
        messages.error(request, message)
    
    return JsonResponse({
        'success': success,
        'message': message,
        'action': action,
        'détails_références': détails_références,
    })


@privilege_required
def privilege_profile_management(request):
    """Gestion des profils utilisateurs pour le groupe PRIVILEGE"""
    
    # Récupérer tous les utilisateurs
    utilisateurs = Utilisateur.objects.all().order_by('username')
    
    # Statistiques des utilisateurs
    stats = {
        'total': utilisateurs.count(),
        'actifs': utilisateurs.filter(actif=True).count(),
        'inactifs': utilisateurs.filter(actif=False).count(),
        'supprimes': Utilisateur.all_objects.filter(is_deleted=True).count(),
        'par_groupe': {}
    }
    
    # Statistiques par groupe
    for groupe in GroupeTravail.objects.all():
        stats['par_groupe'][groupe.nom] = utilisateurs.filter(groupe_travail=groupe).count()
    
    context = {
        'utilisateurs': utilisateurs,
        'stats': stats,
        'groupes': GroupeTravail.objects.all(),
        'groupe_nom': 'PRIVILEGE',
        'page_title': 'Gestion des Profils - PRIVILEGE',
    }
    
    return render(request, 'utilisateurs/privilege_profile_management.html', context)


class PrivilegeUtilisateurCreateView(PrivilegeRequiredMixin, CreateView):
    """Vue de création d'utilisateur pour le groupe PRIVILEGE"""
    model = Utilisateur
    form_class = UtilisateurForm
    template_name = 'utilisateurs/privilege_utilisateur_form.html'
    success_url = reverse_lazy('utilisateurs:privilege_profile_management')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"Utilisateur {self.object.username} créé avec succès.")
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['groupe_nom'] = 'PRIVILEGE'
        context['page_title'] = 'Créer un Utilisateur - PRIVILEGE'
        context['action'] = 'create'
        return context


class PrivilegeUtilisateurUpdateView(PrivilegeRequiredMixin, UpdateView):
    """Vue de modification d'utilisateur pour le groupe PRIVILEGE"""
    model = Utilisateur
    form_class = UtilisateurForm
    template_name = 'utilisateurs/privilege_utilisateur_form.html'
    success_url = reverse_lazy('utilisateurs:privilege_profile_management')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"Utilisateur {self.object.username} modifié avec succès.")
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['groupe_nom'] = 'PRIVILEGE'
        context['page_title'] = f'Modifier {self.object.username} - PRIVILEGE'
        context['action'] = 'update'
        return context


@require_POST
@privilege_required
def privilege_delete_utilisateur(request, user_id):
    """Supprime un utilisateur (suppression logique)"""
    
    try:
        utilisateur = Utilisateur.objects.get(id=user_id)
    except Utilisateur.DoesNotExist:
        return JsonResponse({'success': False, 'message': "Utilisateur non trouvé."})
    
    # Vérifier qu'on ne supprime pas soi-même
    if utilisateur == request.user:
        return JsonResponse({'success': False, 'message': "Vous ne pouvez pas supprimer votre propre compte."})
    
    # Utiliser la méthode de suppression sécurisée
    success, message, action = request.user.safe_delete_element(utilisateur, request)
    
    if success:
        messages.success(request, message)
    else:
        messages.error(request, message)
    
    return JsonResponse({
        'success': success,
        'message': message,
        'action': action,
    })


@require_POST
@privilege_required
def privilege_disable_utilisateur(request, element_id):
    """Désactive un utilisateur"""
    
    try:
        utilisateur = Utilisateur.objects.get(id=element_id)
    except Utilisateur.DoesNotExist:
        return JsonResponse({'success': False, 'message': "Utilisateur non trouvé."})
    
    # Vérifier qu'on ne désactive pas soi-même
    if utilisateur == request.user:
        return JsonResponse({'success': False, 'message': "Vous ne pouvez pas désactiver votre propre compte."})
    
    success, message, action = request.user.safe_delete_element(utilisateur, request)
    
    if success:
        messages.success(request, message)
    else:
        messages.error(request, message)
    
    return JsonResponse({
        'success': success,
        'message': message,
        'action': action,
    })


@privilege_required
def privilege_audit_log(request):
    """Journal d'audit pour le groupe PRIVILEGE"""
    
    from core.models import AuditLog
    
    # Récupérer les logs d'audit
    logs = AuditLog.objects.all().order_by('-timestamp')
    
    # Filtres
    action_filter = request.GET.get('action')
    user_filter = request.GET.get('user')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    if action_filter:
        logs = logs.filter(action=action_filter)
    
    if user_filter:
        logs = logs.filter(user__username__icontains=user_filter)
    
    if date_from:
        logs = logs.filter(timestamp__date__gte=date_from)
    
    if date_to:
        logs = logs.filter(timestamp__date__lte=date_to)
    
    # Pagination
    paginator = Paginator(logs, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'logs': page_obj,
        'action_choices': AuditLog.ACTION_CHOICES,
        'groupe_nom': 'PRIVILEGE',
        'page_title': 'Journal d\'Audit - PRIVILEGE',
    }
    
    return render(request, 'utilisateurs/privilege_audit_log.html', context)

@require_POST
@privilege_required
def privilege_disable_element(request, model_name, element_id):
    """Désactive un élément (désactivation logique)"""
    
    try:
        # Obtenir la classe du modèle
        model_class = get_model_class(model_name)
        if not model_class:
            return JsonResponse({'success': False, 'message': f"Modèle {model_name} non supporté."})
        
        # Récupérer l'élément
        element = model_class.objects.get(id=element_id)
    except model_class.DoesNotExist:
        return JsonResponse({'success': False, 'message': f"Élément non trouvé."})
    
    # Utiliser la méthode de désactivation sécurisée
    success, message, action = request.user.safe_delete_element(element, request)
    
    if success:
        messages.success(request, message)
    else:
        messages.error(request, message)
    
    return JsonResponse({
        'success': success,
        'message': message,
        'action': action,
    })


@require_POST
@privilege_required
def privilege_delete_bailleur(request, element_id):
    """Supprime un bailleur (suppression logique)"""
    from proprietes.models import Bailleur
    
    try:
        bailleur = Bailleur.objects.get(id=element_id)
    except Bailleur.DoesNotExist:
        return JsonResponse({'success': False, 'message': "Bailleur non trouvé."})
    
    success, message, action = request.user.safe_delete_element(bailleur, request)
    
    if success:
        messages.success(request, message)
    else:
        messages.error(request, message)
    
    return JsonResponse({
        'success': success,
        'message': message,
        'action': action,
    })


@require_POST
@privilege_required
def privilege_delete_locataire(request, element_id):
    """Supprime un locataire (suppression logique)"""
    from proprietes.models import Locataire
    
    try:
        locataire = Locataire.objects.get(id=element_id)
    except Locataire.DoesNotExist:
        return JsonResponse({'success': False, 'message': "Locataire non trouvé."})
    
    success, message, action = request.user.safe_delete_element(locataire, request)
    
    if success:
        messages.success(request, message)
    else:
        messages.error(request, message)
    
    return JsonResponse({
        'success': success,
        'message': message,
        'action': action,
    })


@require_POST
@privilege_required
def privilege_delete_propriete(request, element_id):
    """Supprime une propriété (suppression logique)"""
    from proprietes.models import Propriete
    
    try:
        propriete = Propriete.objects.get(id=element_id)
    except Propriete.DoesNotExist:
        return JsonResponse({'success': False, 'message': "Propriété non trouvée."})
    
    success, message, action = request.user.safe_delete_element(propriete, request)
    
    if success:
        messages.success(request, message)
    else:
        messages.error(request, message)
    
    return JsonResponse({
        'success': success,
        'message': message,
        'action': action,
    })


@require_POST
@privilege_required
def privilege_delete_type_bien(request, element_id):
    """Supprime un type de bien (suppression logique)"""
    from proprietes.models import TypeBien
    
    try:
        type_bien = TypeBien.objects.get(id=element_id)
    except TypeBien.DoesNotExist:
        return JsonResponse({'success': False, 'message': "Type de bien non trouvé."})
    
    success, message, action = request.user.safe_delete_element(type_bien, request)
    
    if success:
        messages.success(request, message)
    else:
        messages.error(request, message)
    
    return JsonResponse({
        'success': success,
        'message': message,
        'action': action,
    })


@require_POST
@privilege_required
def privilege_delete_charges_bailleur(request, element_id):
    """Supprime des charges bailleur (suppression logique)"""
    from proprietes.models import ChargesBailleur
    
    try:
        charges = ChargesBailleur.objects.get(id=element_id)
    except ChargesBailleur.DoesNotExist:
        return JsonResponse({'success': False, 'message': "Charges bailleur non trouvées."})
    
    success, message, action = request.user.safe_delete_element(charges, request)
    
    if success:
        messages.success(request, message)
    else:
        messages.error(request, message)
    
    return JsonResponse({
        'success': success,
        'message': message,
        'action': action,
    })


@require_POST
@privilege_required
def privilege_disable_bailleur(request, element_id):
    """Désactive un bailleur"""
    from proprietes.models import Bailleur
    
    try:
        bailleur = Bailleur.objects.get(id=element_id)
    except Bailleur.DoesNotExist:
        return JsonResponse({'success': False, 'message': "Bailleur non trouvé."})
    
    success, message, action = request.user.safe_delete_element(bailleur, request)
    
    if success:
        messages.success(request, message)
    else:
        messages.error(request, message)
    
    return JsonResponse({
        'success': success,
        'message': message,
        'action': action,
    })


@require_POST
@privilege_required
def privilege_disable_locataire(request, element_id):
    """Désactive un locataire"""
    from proprietes.models import Locataire
    
    try:
        locataire = Locataire.objects.get(id=element_id)
    except Locataire.DoesNotExist:
        return JsonResponse({'success': False, 'message': "Locataire non trouvé."})
    
    success, message, action = request.user.safe_delete_element(locataire, request)
    
    if success:
        messages.success(request, message)
    else:
        messages.error(request, message)
    
    return JsonResponse({
        'success': success,
        'message': message,
        'action': action,
    })


@require_POST
@privilege_required
def privilege_disable_propriete(request, element_id):
    """Désactive une propriété"""
    from proprietes.models import Propriete
    
    try:
        propriete = Propriete.objects.get(id=element_id)
    except Propriete.DoesNotExist:
        return JsonResponse({'success': False, 'message': "Propriété non trouvée."})
    
    success, message, action = request.user.safe_delete_element(propriete, request)
    
    if success:
        messages.success(request, message)
    else:
        messages.error(request, message)
    
    return JsonResponse({
        'success': success,
        'message': message,
        'action': action,
    })


@require_POST
@privilege_required
def privilege_disable_type_bien(request, element_id):
    """Désactive un type de bien"""
    from proprietes.models import TypeBien
    
    try:
        type_bien = TypeBien.objects.get(id=element_id)
    except TypeBien.DoesNotExist:
        return JsonResponse({'success': False, 'message': "Type de bien non trouvé."})
    
    success, message, action = request.user.safe_delete_element(type_bien, request)
    
    if success:
        messages.success(request, message)
    else:
        messages.error(request, message)
    
    return JsonResponse({
        'success': success,
        'message': message,
        'action': action,
    })


@require_POST
@privilege_required
def privilege_disable_charges_bailleur(request, element_id):
    """Désactive des charges bailleur"""
    from proprietes.models import ChargesBailleur
    
    try:
        charges = ChargesBailleur.objects.get(id=element_id)
    except ChargesBailleur.DoesNotExist:
        return JsonResponse({'success': False, 'message': "Charges bailleur non trouvées."})
    
    success, message, action = request.user.safe_delete_element(charges, request)
    
    if success:
        messages.success(request, message)
    else:
        messages.error(request, message)
    
    return JsonResponse({
        'success': success,
        'message': message,
        'action': action,
    })


@require_POST
@privilege_required
def privilege_bulk_actions(request):
    """Actions en lot pour le groupe PRIVILEGE"""
    
    action_type = request.POST.get('action_type')
    element_ids = request.POST.getlist('element_ids')
    model_name = request.POST.get('model_name')
    
    if not action_type or not element_ids or not model_name:
        return JsonResponse({'success': False, 'message': "Paramètres manquants."})
    
    # Obtenir la classe du modèle
    model_class = get_model_class(model_name)
    if not model_class:
        return JsonResponse({'success': False, 'message': f"Modèle {model_name} non supporté."})
    
    success_count = 0
    error_count = 0
    messages_list = []
    
    for element_id in element_ids:
        try:
            element = model_class.objects.get(id=element_id)
            success, message, action = request.user.safe_delete_element(element, request)
            
            if success:
                success_count += 1
                messages_list.append(f"Élément {element_id}: {message}")
            else:
                error_count += 1
                messages_list.append(f"Élément {element_id}: {message}")
                
        except model_class.DoesNotExist:
            error_count += 1
            messages_list.append(f"Élément {element_id}: Non trouvé")
    
    # Message de résumé
    if success_count > 0:
        messages.success(request, f"{success_count} élément(s) traité(s) avec succès.")
    
    if error_count > 0:
        messages.warning(request, f"{error_count} élément(s) avec erreur(s).")
    
    return JsonResponse({
        'success': True,
        'message': f"Traitement terminé: {success_count} succès, {error_count} erreurs",
        'success_count': success_count,
        'error_count': error_count,
        'details': messages_list
    })


def get_model_class(model_name):
    """Retourne la classe du modèle correspondant au nom"""
    model_mapping = {
        'bailleur': 'proprietes.Bailleur',
        'locataire': 'proprietes.Locataire',
        'propriete': 'proprietes.Propriete',
        'typebien': 'proprietes.TypeBien',
        'chargesbailleur': 'proprietes.ChargesBailleur',
        'utilisateur': 'utilisateurs.Utilisateur',
        'paiement': 'paiements.Paiement',
        'recu': 'paiements.Recu',
        'retrait': 'paiements.Retrait',
        'comptebancaire': 'paiements.CompteBancaire',
        'chargedeductible': 'paiements.ChargeDeductible',
        'contrat': 'contrats.Contrat',
        'quittance': 'contrats.Quittance',
        'etatlieux': 'contrats.EtatLieux',
        'notification': 'notifications.Notification',
    }
    
    if model_name not in model_mapping:
        return None
    
    try:
        app_label, model_class_name = model_mapping[model_name].split('.')
        from django.apps import apps
        return apps.get_model(app_label, model_class_name)
    except (ValueError, LookupError):
        return None


@login_required
def utilisateurs_dashboard(request):
    """Dashboard principal des utilisateurs avec vue d'ensemble et accès contextuel aux listes."""
    # Vérification des permissions
    from core.utils import check_group_permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE'], 'view')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('core:dashboard')
    
    # Statistiques générales
    from django.contrib.auth import get_user_model
    User = get_user_model()
    total_utilisateurs = User.objects.filter(is_active=True).count()
    utilisateurs_actifs = User.objects.filter(is_active=True, last_login__isnull=False).count()
    utilisateurs_inactifs = User.objects.filter(is_active=True, last_login__isnull=True).count()
    utilisateurs_privilege = User.objects.filter(groups__name='PRIVILEGE').count()
    
    # Utilisateurs récents
    utilisateurs_recents = User.objects.filter(
        is_active=True
    ).order_by('-date_joined')[:5]
    
    # Groupes d'utilisateurs
    groupes = GroupeTravail.objects.filter(actif=True).order_by('-date_creation')[:5]
    
    # Actions récentes
    actions_recentes = AuditLog.objects.select_related('user', 'content_type').order_by('-timestamp')[:10]
    
    context = {
        'total_utilisateurs': total_utilisateurs,
        'utilisateurs_actifs': utilisateurs_actifs,
        'utilisateurs_inactifs': utilisateurs_inactifs,
        'utilisateurs_privilege': utilisateurs_privilege,
        'utilisateurs_recents': utilisateurs_recents,
        'groupes': groupes,
        'actions_recentes': actions_recentes,
        'title': 'Dashboard Utilisateurs'
    }
    
    return render(request, 'utilisateurs/dashboard_principal.html', context)
