"""
Vues spécialisées pour la gestion documentaire par entité
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.utils import timezone
from django.http import JsonResponse

from .models import Document, Propriete, Bailleur, Locataire
from .forms import DocumentForm, DocumentSearchForm


@login_required
def document_archive_by_entity(request):
    """
    Vue principale d'archivage des documents organisés par entité
    """
    # Vérifier les permissions
    is_privilege_user = hasattr(request.user, 'groupe_travail') and request.user.groupe_travail and request.user.groupe_travail.nom == 'PRIVILEGE'
    
    # Statistiques globales
    total_documents = Document.objects.count()
    documents_confidentiels = Document.objects.filter(confidentiel=True).count() if is_privilege_user else 0
    documents_expires = Document.objects.filter(
        date_expiration__lt=timezone.now().date()
    ).count()
    
    # Documents par entité
    documents_par_propriete = Document.objects.filter(
        propriete__isnull=False
    ).values('propriete__titre', 'propriete__numero_propriete').annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    documents_par_bailleur = Document.objects.filter(
        bailleur__isnull=False
    ).values('bailleur__nom', 'bailleur__prenom', 'bailleur__numero_bailleur').annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    documents_par_locataire = Document.objects.filter(
        locataire__isnull=False
    ).values('locataire__nom', 'locataire__prenom', 'locataire__numero_locataire').annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    # Documents récents
    documents_recents = Document.objects.select_related(
        'propriete', 'bailleur', 'locataire'
    ).order_by('-date_creation')[:5]
    
    context = {
        'total_documents': total_documents,
        'documents_confidentiels': documents_confidentiels,
        'documents_expires': documents_expires,
        'documents_par_propriete': documents_par_propriete,
        'documents_par_bailleur': documents_par_bailleur,
        'documents_par_locataire': documents_par_locataire,
        'documents_recents': documents_recents,
        'is_privilege_user': is_privilege_user,
    }
    
    return render(request, 'proprietes/documents/document_archive.html', context)


@login_required
def document_list_by_propriete(request, propriete_id):
    """
    Liste des documents pour une propriété spécifique
    """
    propriete = get_object_or_404(Propriete, pk=propriete_id)
    
    # Vérifier les permissions
    is_privilege_user = hasattr(request.user, 'groupe_travail') and request.user.groupe_travail and request.user.groupe_travail.nom == 'PRIVILEGE'
    
    # Documents de la propriété
    documents = Document.objects.filter(propriete=propriete)
    
    if not is_privilege_user:
        documents = documents.filter(confidentiel=False)
    
    # Filtres
    form = DocumentSearchForm(request.GET)
    if form.is_valid():
        search = form.cleaned_data.get('search')
        type_document = form.cleaned_data.get('type_document')
        statut = form.cleaned_data.get('statut')
        
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
    
    # Pagination
    paginator = Paginator(documents.order_by('-date_creation'), 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistiques
    stats = {
        'total': documents.count(),
        'par_type': documents.values('type_document').annotate(count=Count('id')),
        'expires': documents.filter(date_expiration__lt=timezone.now().date()).count(),
    }
    
    context = {
        'propriete': propriete,
        'page_obj': page_obj,
        'search_form': form,
        'stats': stats,
        'is_privilege_user': is_privilege_user,
    }
    
    return render(request, 'proprietes/documents/document_list_by_propriete.html', context)


@login_required
def document_list_by_bailleur(request, bailleur_id):
    """
    Liste des documents pour un bailleur spécifique
    """
    bailleur = get_object_or_404(Bailleur, pk=bailleur_id)
    
    # Vérifier les permissions
    is_privilege_user = hasattr(request.user, 'groupe_travail') and request.user.groupe_travail and request.user.groupe_travail.nom == 'PRIVILEGE'
    
    # Documents du bailleur
    documents = Document.objects.filter(bailleur=bailleur)
    
    if not is_privilege_user:
        documents = documents.filter(confidentiel=False)
    
    # Filtres
    form = DocumentSearchForm(request.GET)
    if form.is_valid():
        search = form.cleaned_data.get('search')
        type_document = form.cleaned_data.get('type_document')
        statut = form.cleaned_data.get('statut')
        
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
    
    # Pagination
    paginator = Paginator(documents.order_by('-date_creation'), 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistiques
    stats = {
        'total': documents.count(),
        'par_type': documents.values('type_document').annotate(count=Count('id')),
        'expires': documents.filter(date_expiration__lt=timezone.now().date()).count(),
    }
    
    context = {
        'bailleur': bailleur,
        'page_obj': page_obj,
        'search_form': form,
        'stats': stats,
        'is_privilege_user': is_privilege_user,
    }
    
    return render(request, 'proprietes/documents/document_list_by_bailleur.html', context)


@login_required
def document_list_by_locataire(request, locataire_id):
    """
    Liste des documents pour un locataire spécifique
    """
    locataire = get_object_or_404(Locataire, pk=locataire_id)
    
    # Vérifier les permissions
    is_privilege_user = hasattr(request.user, 'groupe_travail') and request.user.groupe_travail and request.user.groupe_travail.nom == 'PRIVILEGE'
    
    # Documents du locataire
    documents = Document.objects.filter(locataire=locataire)
    
    if not is_privilege_user:
        documents = documents.filter(confidentiel=False)
    
    # Filtres
    form = DocumentSearchForm(request.GET)
    if form.is_valid():
        search = form.cleaned_data.get('search')
        type_document = form.cleaned_data.get('type_document')
        statut = form.cleaned_data.get('statut')
        
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
    
    # Pagination
    paginator = Paginator(documents.order_by('-date_creation'), 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistiques
    stats = {
        'total': documents.count(),
        'par_type': documents.values('type_document').annotate(count=Count('id')),
        'expires': documents.filter(date_expiration__lt=timezone.now().date()).count(),
    }
    
    context = {
        'locataire': locataire,
        'page_obj': page_obj,
        'search_form': form,
        'stats': stats,
        'is_privilege_user': is_privilege_user,
    }
    
    return render(request, 'proprietes/documents/document_list_by_locataire.html', context)


@login_required
def document_search_advanced(request):
    """
    Recherche avancée de documents avec filtres multiples
    """
    # Vérifier les permissions
    is_privilege_user = hasattr(request.user, 'groupe_travail') and request.user.groupe_travail and request.user.groupe_travail.nom == 'PRIVILEGE'
    
    # Base queryset
    documents = Document.objects.select_related(
        'propriete', 'bailleur', 'locataire', 'cree_par'
    )
    
    if not is_privilege_user:
        documents = documents.filter(confidentiel=False)
    
    # Filtres avancés
    form = DocumentSearchForm(request.GET)
    if form.is_valid():
        search = form.cleaned_data.get('search')
        type_document = form.cleaned_data.get('type_document')
        statut = form.cleaned_data.get('statut')
        propriete = form.cleaned_data.get('propriete')
        bailleur = form.cleaned_data.get('bailleur')
        locataire = form.cleaned_data.get('locataire')
        confidentiel = form.cleaned_data.get('confidentiel')
        taille_min = form.cleaned_data.get('taille_min')
        taille_max = form.cleaned_data.get('taille_max')
        tags = form.cleaned_data.get('tags')
        date_debut = form.cleaned_data.get('date_debut')
        date_fin = form.cleaned_data.get('date_fin')
        date_expiration_debut = form.cleaned_data.get('date_expiration_debut')
        date_expiration_fin = form.cleaned_data.get('date_expiration_fin')
        
        # Recherche textuelle étendue
        if search:
            documents = documents.filter(
                Q(nom__icontains=search) |
                Q(description__icontains=search) |
                Q(tags__icontains=search) |
                Q(propriete__titre__icontains=search) |
                Q(propriete__numero_propriete__icontains=search) |
                Q(bailleur__nom__icontains=search) |
                Q(bailleur__prenom__icontains=search) |
                Q(bailleur__numero_bailleur__icontains=search) |
                Q(locataire__nom__icontains=search) |
                Q(locataire__prenom__icontains=search) |
                Q(locataire__numero_locataire__icontains=search) |
                Q(cree_par__username__icontains=search) |
                Q(cree_par__first_name__icontains=search) |
                Q(cree_par__last_name__icontains=search)
            )
        
        # Filtres de base
        if type_document:
            documents = documents.filter(type_document=type_document)
        
        if statut:
            documents = documents.filter(statut=statut)
        
        if propriete:
            documents = documents.filter(propriete=propriete)
        
        if bailleur:
            documents = documents.filter(bailleur=bailleur)
        
        if locataire:
            documents = documents.filter(locataire=locataire)
        
        # Filtre de confidentialité
        if confidentiel == 'true':
            documents = documents.filter(confidentiel=True)
        elif confidentiel == 'false':
            documents = documents.filter(confidentiel=False)
        
        # Filtres de taille
        if taille_min:
            documents = documents.filter(taille_fichier__gte=taille_min * 1024)
        
        if taille_max:
            documents = documents.filter(taille_fichier__lte=taille_max * 1024)
        
        # Filtre par tags
        if tags:
            tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
            for tag in tag_list:
                documents = documents.filter(tags__icontains=tag)
        
        # Filtres de dates
        if date_debut:
            documents = documents.filter(date_creation__date__gte=date_debut)
        
        if date_fin:
            documents = documents.filter(date_creation__date__lte=date_fin)
        
        # Filtres de date d'expiration
        if date_expiration_debut:
            documents = documents.filter(date_expiration__gte=date_expiration_debut)
        
        if date_expiration_fin:
            documents = documents.filter(date_expiration__lte=date_expiration_fin)
    
    # Tri intelligent
    sort_by = request.GET.get('sort', 'date_creation')
    sort_order = request.GET.get('order', 'desc')
    
    if sort_order == 'asc':
        sort_field = sort_by
    else:
        sort_field = f'-{sort_by}'
    
    documents = documents.order_by(sort_field)
    
    # Pagination
    paginator = Paginator(documents, 30)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistiques de recherche avancées
    stats = {
        'total_results': documents.count(),
        'par_type': documents.values('type_document').annotate(count=Count('id')).order_by('-count'),
        'par_statut': documents.values('statut').annotate(count=Count('id')).order_by('-count'),
        'par_entite': {
            'proprietes': documents.filter(propriete__isnull=False).count(),
            'bailleurs': documents.filter(bailleur__isnull=False).count(),
            'locataires': documents.filter(locataire__isnull=False).count(),
        },
        'taille_totale': sum(doc.taille_fichier or 0 for doc in documents),
        'confidentiels': documents.filter(confidentiel=True).count(),
        'expires': documents.filter(date_expiration__lt=timezone.now().date()).count(),
    }
    
    # Options de tri
    sort_options = [
        {'value': 'date_creation', 'label': 'Date de création'},
        {'value': 'date_modification', 'label': 'Date de modification'},
        {'value': 'nom', 'label': 'Nom du document'},
        {'value': 'type_document', 'label': 'Type de document'},
        {'value': 'statut', 'label': 'Statut'},
        {'value': 'taille_fichier', 'label': 'Taille du fichier'},
    ]
    
    context = {
        'page_obj': page_obj,
        'search_form': form,
        'stats': stats,
        'is_privilege_user': is_privilege_user,
        'sort_options': sort_options,
        'current_sort': sort_by,
        'current_order': sort_order,
    }
    
    return render(request, 'proprietes/documents/document_search_advanced.html', context)


@login_required
def document_quick_upload(request):
    """
    Upload rapide de documents avec association automatique à une entité
    """
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.cree_par = request.user
            document.save()
            
            messages.success(request, f'Document "{document.nom}" ajouté avec succès!')
            
            # Redirection vers la liste des documents de l'entité
            if document.propriete:
                return redirect('proprietes:document_list_by_propriete', propriete_id=document.propriete.id)
            elif document.bailleur:
                return redirect('proprietes:document_list_by_bailleur', bailleur_id=document.bailleur.id)
            elif document.locataire:
                return redirect('proprietes:document_list_by_locataire', locataire_id=document.locataire.id)
            else:
                return redirect('proprietes:document_archive')
    else:
        form = DocumentForm()
    
    context = {
        'form': form,
    }
    
    return render(request, 'proprietes/documents/document_quick_upload.html', context)


@login_required
def document_stats_api(request):
    """
    API pour les statistiques des documents (AJAX)
    """
    # Vérifier les permissions
    is_privilege_user = hasattr(request.user, 'groupe_travail') and request.user.groupe_travail and request.user.groupe_travail.nom == 'PRIVILEGE'
    
    documents = Document.objects.all()
    if not is_privilege_user:
        documents = documents.filter(confidentiel=False)
    
    # Statistiques par type
    stats_by_type = list(documents.values('type_document').annotate(
        count=Count('id')
    ).order_by('-count'))
    
    # Statistiques par mois (12 derniers mois)
    from django.db.models.functions import TruncMonth
    stats_by_month = list(documents.annotate(
        month=TruncMonth('date_creation')
    ).values('month').annotate(
        count=Count('id')
    ).order_by('month')[-12:])
    
    # Documents expirés par type
    expired_by_type = list(documents.filter(
        date_expiration__lt=timezone.now().date()
    ).values('type_document').annotate(
        count=Count('id')
    ).order_by('-count'))
    
    return JsonResponse({
        'by_type': stats_by_type,
        'by_month': stats_by_month,
        'expired_by_type': expired_by_type,
    })
