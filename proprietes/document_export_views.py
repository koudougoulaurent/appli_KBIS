"""
Vues pour l'export des documents
"""
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Q
from django.core.paginator import Paginator
from django.utils import timezone
from django.conf import settings

from .models import Document, Propriete, Bailleur, Locataire
from .forms import DocumentSearchForm
from .services.export_documents import DocumentExportService


@login_required
@require_http_methods(["GET", "POST"])
def document_export(request):
    """
    Vue pour l'export des documents avec options de format
    """
    # Vérifier les permissions
    is_privilege_user = hasattr(request.user, 'groupe_travail') and request.user.groupe_travail and request.user.groupe_travail.nom == 'PRIVILEGE'
    
    # Base queryset
    documents = Document.objects.select_related(
        'propriete', 'bailleur', 'locataire', 'cree_par'
    ).prefetch_related('propriete__type_bien')
    
    # Filtrer les documents confidentiels pour les utilisateurs non privilégiés
    if not is_privilege_user:
        documents = documents.filter(confidentiel=False)
    
    # Appliquer les filtres de recherche
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
    
    # Si c'est une requête AJAX pour l'export
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        export_format = request.GET.get('format', 'excel')
        
        try:
            export_service = DocumentExportService()
            
            if export_format == 'excel':
                return export_service.export_to_excel(documents)
            elif export_format == 'pdf':
                return export_service.export_to_pdf(documents)
            elif export_format == 'csv':
                return export_service.export_to_csv(documents)
            else:
                return JsonResponse({'error': 'Format non supporté'}, status=400)
                
        except Exception as e:
            return JsonResponse({'error': f'Erreur lors de l\'export: {str(e)}'}, status=500)
    
    # Si c'est une requête normale, afficher la page d'export
    context = {
        'form': form,
        'documents': documents[:100],  # Limiter pour l'affichage
        'total_documents': documents.count(),
        'is_privilege_user': is_privilege_user,
        'export_formats': [
            {'value': 'excel', 'label': 'Excel (.xlsx)', 'icon': 'fas fa-file-excel'},
            {'value': 'pdf', 'label': 'PDF (.pdf)', 'icon': 'fas fa-file-pdf'},
            {'value': 'csv', 'label': 'CSV (.csv)', 'icon': 'fas fa-file-csv'},
        ]
    }
    
    return render(request, 'proprietes/documents/document_export.html', context)


@login_required
def document_export_preview(request):
    """
    Aperçu des documents avant export
    """
    # Récupérer les paramètres de recherche
    search_params = request.GET.copy()
    
    # Base queryset
    documents = Document.objects.select_related(
        'propriete', 'bailleur', 'locataire', 'cree_par'
    )
    
    # Appliquer les mêmes filtres que l'export
    form = DocumentSearchForm(search_params)
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
    
    # Pagination pour l'aperçu
    paginator = Paginator(documents, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistiques
    export_service = DocumentExportService()
    stats = export_service.get_export_statistics(documents)
    
    context = {
        'page_obj': page_obj,
        'total_documents': documents.count(),
        'stats': stats,
        'search_params': search_params.urlencode()
    }
    
    return render(request, 'proprietes/documents/document_export_preview.html', context)


@login_required
def document_export_statistics(request):
    """
    API pour obtenir les statistiques d'export
    """
    # Récupérer les paramètres de recherche
    search_params = request.GET.copy()
    
    # Base queryset
    documents = Document.objects.all()
    
    # Appliquer les filtres
    form = DocumentSearchForm(search_params)
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
    
    # Calculer les statistiques
    export_service = DocumentExportService()
    stats = export_service.get_export_statistics(documents)
    
    return JsonResponse(stats)


@login_required
def document_bulk_export(request):
    """
    Export en lot de documents sélectionnés
    """
    if request.method == 'POST':
        document_ids = request.POST.getlist('document_ids')
        export_format = request.POST.get('format', 'excel')
        
        if not document_ids:
            messages.error(request, 'Aucun document sélectionné.')
            return redirect('proprietes:document_export')
        
        # Récupérer les documents
        documents = Document.objects.filter(id__in=document_ids)
        
        try:
            export_service = DocumentExportService()
            
            if export_format == 'excel':
                return export_service.export_to_excel(documents)
            elif export_format == 'pdf':
                return export_service.export_to_pdf(documents)
            elif export_format == 'csv':
                return export_service.export_to_csv(documents)
            else:
                messages.error(request, 'Format d\'export non supporté.')
                return redirect('proprietes:document_export')
                
        except Exception as e:
            messages.error(request, f'Erreur lors de l\'export: {str(e)}')
            return redirect('proprietes:document_export')
    
    return redirect('proprietes:document_export')
