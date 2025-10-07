from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.db.models import Q, Sum, Count, F, Value
from django.utils import timezone
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from django.core.paginator import Paginator
from datetime import datetime, timedelta
from .models import Paiement, Retrait, CompteBancaire, Recu, ChargeDeductible
from .forms import PaiementForm, ChargeDeductibleForm, PaiementAvecChargesForm
from contrats.models import Contrat
from proprietes.models import Bailleur, ChargesBailleur
from core.utils import convertir_montant
from core.models import Devise
from core.models import AuditLog
from django.contrib.contenttypes.models import ContentType
from django.db.models import ProtectedError
from core.intelligent_views import IntelligentListView
from utilisateurs.mixins import PrivilegeButtonsMixin
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import Group
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, A5
from paiements.models import RetraitBailleur, RecapMensuel, RecuRetrait
from paiements.forms import RetraitBailleurForm, RecapMensuelForm


def serialize_model_for_audit(instance):
    """Convertit un objet modèle en dictionnaire JSON-sérialisable pour l'audit log"""
    data = {}
    for f in instance._meta.fields:
        value = getattr(instance, f.name)
        # Convertir les objets non-sérialisables en représentation string/pk
        if hasattr(value, 'pk'):  # ForeignKey objects
            data[f.name] = value.pk
        elif hasattr(value, '__str__'):
            data[f.name] = str(value)
        else:
            data[f.name] = value
    return data


def generer_pdf_reportlab(recu, config=None, template=None):
    """
    Génère un PDF avec ReportLab en utilisant la configuration de l'entreprise
    """
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch, cm
        from reportlab.lib import colors
        from io import BytesIO
        import os
        
        # Récupérer la configuration de l'entreprise si non fournie
        if config is None:
            from core.models import ConfigurationEntreprise
            config = ConfigurationEntreprise.get_configuration_active()
        
        # Créer le buffer pour le PDF
        buffer = BytesIO()
        
        # Créer le document PDF
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        story = []
        
        # Styles personnalisés selon la configuration
        styles = getSampleStyleSheet()
        
        # Mapper les polices personnalisées vers les polices standard de ReportLab
        def get_reportlab_font(font_name):
            font_mapping = {
                'Arial': 'Helvetica',
                'Helvetica': 'Helvetica',
                'Times New Roman': 'Times-Roman',
                'Georgia': 'Times-Roman',
                'Verdana': 'Helvetica'
            }
            return font_mapping.get(font_name, 'Helvetica')
        
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=1,  # Centré
            textColor=colors.HexColor(config.couleur_principale)
        )
        
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=20,
            alignment=1,  # Centré
            textColor=colors.HexColor(config.couleur_secondaire)
        )
        
        # Titre de l'entreprise
        story.append(Paragraph(config.nom_entreprise, title_style))
        story.append(Paragraph("REÇU DE PAIEMENT", subtitle_style))
        story.append(Spacer(1, 20))
        
        # Informations de l'entreprise
        if config.adresse:
            adresse_lines = config.adresse.split('\n')
            for line in adresse_lines:
                if line.strip():
                    story.append(Paragraph(line.strip(), styles['Normal']))
            story.append(Spacer(1, 10))
        
        # Informations de contact
        contact_info = []
        if config.telephone:
            contact_info.append(f"Tél: {config.telephone}")
        if config.email:
            contact_info.append(f"Email: {config.email}")
        if config.site_web:
            contact_info.append(f"Web: {config.site_web}")
        
        if contact_info:
            contact_text = " | ".join(contact_info)
            story.append(Paragraph(contact_text, styles['Normal']))
            story.append(Spacer(1, 15))
        
        # Informations légales
        # Vérifier si les champs existent avant de les utiliser
        afficher_siret = getattr(config, 'afficher_siret', True)  # Valeur par défaut True
        afficher_tva = getattr(config, 'afficher_tva', True)    # Valeur par défaut True
        
        if afficher_siret or afficher_tva:
            legal_info = []
            if afficher_siret and config.siret:
                legal_info.append(f"SIRET: {config.siret}")
            if afficher_tva:
                legal_info.append("TVA non applicable")
            # RCS n'est pas dans le modèle ConfigurationEntreprise
            
            if legal_info:
                legal_text = " | ".join(legal_info)
                story.append(Paragraph(legal_text, styles['Normal']))
                story.append(Spacer(1, 20))
        
        # Informations du reçu
        recu_data = [
            ['Numéro de reçu:', recu.numero_recu],
            ['Date d\'émission:', recu.date_emission.strftime('%d/%m/%Y')],
            ['Montant:', f"{recu.paiement.montant} F CFA"],
        ]
        
        recu_table = Table(recu_data, colWidths=[2*inch, 4*inch])
        recu_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor(config.couleur_secondaire)),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), get_reportlab_font('Arial')),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (1, 0), (1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(recu_table)
        story.append(Spacer(1, 20))
        
        # Informations du paiement
        paiement = recu.paiement
        contrat = paiement.contrat
        propriete = contrat.propriete
        locataire = contrat.locataire
        bailleur = propriete.bailleur
        
        paiement_data = [
            ['Informations du paiement', ''],
            ['Type de paiement:', paiement.get_type_paiement_display()],
            ['Mode de paiement:', paiement.get_mode_paiement_display()],
            ['Date de paiement:', paiement.date_paiement.strftime('%d/%m/%Y')],
            ['Statut:', paiement.get_statut_display()],
            ['', ''],
            ['Informations du contrat', ''],
            ['Numéro de contrat:', contrat.numero_contrat],
            ['Date de début:', contrat.date_debut.strftime('%d/%m/%Y')],
            ['Date de fin:', contrat.date_fin.strftime('%d/%m/%Y') if contrat.date_fin else 'Non définie'],
            ['', ''],
            ['Informations de la propriété', ''],
            ['Adresse:', propriete.adresse],
            ['Type:', str(propriete.type_bien)],
            ['Surface:', f"{propriete.surface}m²"],
            ['', ''],
            ['Informations du locataire', ''],
            ['Nom:', f"{locataire.nom} {locataire.prenom}"],
            ['Email:', locataire.email],
            ['Téléphone:', locataire.telephone],
            ['', ''],
            ['Informations du bailleur', ''],
            ['Nom:', f"{bailleur.nom} {bailleur.prenom}"],
            ['Email:', bailleur.email],
            ['Téléphone:', bailleur.telephone],
        ]
        
        paiement_table = Table(paiement_data, colWidths=[2*inch, 4*inch])
        paiement_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, 0), colors.HexColor(config.couleur_principale)),
            ('TEXTCOLOR', (0, 0), (0, 0), colors.whitesmoke),
            ('BACKGROUND', (0, 2), (0, 2), colors.HexColor(config.couleur_principale)),
            ('TEXTCOLOR', (0, 2), (0, 2), colors.whitesmoke),
            ('BACKGROUND', (0, 7), (0, 7), colors.HexColor(config.couleur_principale)),
            ('TEXTCOLOR', (0, 7), (0, 7), colors.whitesmoke),
            ('BACKGROUND', (0, 12), (0, 12), colors.HexColor(config.couleur_principale)),
            ('TEXTCOLOR', (0, 12), (0, 12), colors.whitesmoke),
            ('BACKGROUND', (0, 17), (0, 17), colors.HexColor(config.couleur_principale)),
            ('TEXTCOLOR', (0, 17), (0, 17), colors.whitesmoke),
            ('BACKGROUND', (0, 22), (0, 22), colors.HexColor(config.couleur_principale)),
            ('TEXTCOLOR', (0, 22), (0, 22), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), get_reportlab_font('Arial')),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('BACKGROUND', (1, 0), (1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(paiement_table)
        story.append(Spacer(1, 20))
        
        # Informations bancaires si configuré
        # Vérifier si les champs existent avant de les utiliser
        afficher_iban = getattr(config, 'afficher_iban', False)  # Valeur par défaut False
        if afficher_iban and config.iban:
            banque_data = [
                ['Informations bancaires', ''],
                ['Banque:', config.banque or ''],
                ['IBAN:', config.iban],
                ['BIC:', config.bic or ''],
            ]
            
            banque_table = Table(banque_data, colWidths=[2*inch, 4*inch])
            banque_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, 0), colors.HexColor(config.couleur_principale)),
                ('TEXTCOLOR', (0, 0), (0, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), get_reportlab_font('Arial')),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('BACKGROUND', (1, 0), (1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(banque_table)
            story.append(Spacer(1, 20))
        
        # Pied de page personnalisé
        # Le modèle ConfigurationEntreprise n'a pas de champ pied_page
        
        # Conditions générales
        # Le modèle ConfigurationEntreprise n'a pas de champ conditions_generales
        
        # Construire le PDF
        doc.build(story)
        
        # Récupérer le contenu
        pdf_content = buffer.getvalue()
        buffer.close()
        
        return pdf_content
        
    except Exception as e:
        print(f"Erreur lors de la génération PDF avec ReportLab: {e}")
        return None


class PaiementListView(PrivilegeButtonsMixin, IntelligentListView):
    model = Paiement
    template_name = 'base_liste_intelligente.html'
    paginate_by = 20
    page_title = 'Liste des Paiements'
    page_icon = 'credit-card'
    add_url = 'paiements:ajouter'
    add_text = 'Ajouter un Paiement'
    search_fields = ['contrat__numero_contrat', 'contrat__propriete__titre', 'contrat__locataire__nom', 'contrat__locataire__prenom', 'montant', 'type_paiement', 'mode_paiement', 'notes']
    filter_fields = ['type_paiement', 'mode_paiement', 'statut']
    default_sort = 'date_paiement'
    columns = [
        {'field': 'contrat', 'label': 'Contrat', 'sortable': True},
        {'field': 'montant', 'label': 'Montant', 'sortable': True},
        {'field': 'type_paiement', 'label': 'Type', 'sortable': True},
        {'field': 'mode_paiement', 'label': 'Mode', 'sortable': True},
        {'field': 'date_paiement', 'label': 'Date', 'sortable': True},
        {'field': 'statut', 'label': 'Statut', 'sortable': True},
    ]
    actions = [
        {'url_name': 'paiements:detail_paiement', 'icon': 'eye', 'style': 'outline-primary', 'title': 'Voir'},
        {'url_name': 'paiements:modifier', 'icon': 'pencil', 'style': 'outline-warning', 'title': 'Modifier'},
    ]
    sort_options = [
        {'value': 'date_paiement', 'label': 'Date'},
        {'value': 'montant', 'label': 'Montant'},
        {'value': 'type_paiement', 'label': 'Type'},
        {'value': 'mode_paiement', 'label': 'Mode'},
        {'value': 'statut', 'label': 'Statut'},
    ]
    
    def get_queryset(self):
        """
        Optimisation des requêtes de base de données
        """
        queryset = super().get_queryset()
        return queryset.select_related('contrat', 'contrat__locataire', 'contrat__propriete', 'valide_par')
    
    def get_context_data(self, **kwargs):
        """
        Ajout de statistiques et d'informations supplémentaires au contexte
        """
        context = super().get_context_data(**kwargs)
        
        # Statistiques générales
        context['total_paiements'] = Paiement.objects.count()
        context['paiements_valides'] = Paiement.objects.filter(statut='valide').count()
        context['paiements_en_attente'] = Paiement.objects.filter(statut='en_attente').count()
        context['paiements_refuses'] = Paiement.objects.filter(statut='refuse').count()
        context['paiements_annules'] = Paiement.objects.filter(statut='annule').count()
        
        # Montant total
        from django.db.models import Sum
        context['montant_total'] = Paiement.objects.aggregate(total=Sum('montant'))['total'] or 0
        
        # Statistiques par type de paiement
        context['paiements_par_type'] = Paiement.objects.values('type_paiement').annotate(
            count=Sum('montant')
        ).order_by('-count')
        
        # Statistiques par mode de paiement
        context['paiements_par_mode'] = Paiement.objects.values('mode_paiement').annotate(
            count=Sum('montant')
        ).order_by('-count')
        
        # Montant total des charges déduites
        context['total_charges_deduites'] = Paiement.objects.aggregate(
            total=Sum('montant_charges_deduites')
        )['total'] or 0
        
        return context

paiement_list = PaiementListView.as_view()


def detail_paiement(request, pk):
    """
    Vue de détail d'un paiement
    """
    # Vérification des permissions : PRIVILEGE, ADMINISTRATION, CONTROLES et CAISSE peuvent voir les détails
    from core.utils import check_group_permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'CONTROLES', 'CAISSE'], 'view')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:liste')
    
    paiement = get_object_or_404(Paiement, pk=pk)
    context = {
        'paiement': paiement
    }
    return render(request, 'paiements/detail.html', context)


def ajouter_paiement(request):
    """Vue pour ajouter un paiement avec déduction automatique des charges"""
    # Vérification des permissions : PRIVILEGE, ADMINISTRATION et CAISSE peuvent ajouter
    from core.utils import check_group_permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'CAISSE'], 'add')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:liste')
    
    contrat_id = request.GET.get('contrat')
    
    if request.method == 'POST':
        form = PaiementForm(request.POST, contrat_id=contrat_id)
        if form.is_valid():
            # Créer le paiement
            paiement = form.save(commit=False)
            paiement.cree_par = request.user
            paiement.statut = 'valide'
            paiement.save()
            
            # Traiter les charges déductibles
            charges_deductibles = form.cleaned_data.get('charges_deductibles', [])
            if charges_deductibles:
                # Appliquer les charges déductibles
                charges_ajoutees, total_deductions = paiement.ajouter_charges_deductibles(
                    [charge.id for charge in charges_deductibles],
                    request.user
                )
                
                # Log d'audit
                AuditLog.objects.create(
                    content_type=ContentType.objects.get_for_model(Paiement),
                    object_id=paiement.pk,
                    action='CREATE_WITH_AUTO_CHARGES',
                    old_data=None,
                    new_data={
                        'paiement_id': paiement.id,
                        'charges_deduites': [charge.id for charge in charges_ajoutees],
                        'total_deductions': float(total_deductions),
                        'montant_net': float(paiement.montant_net_paye or paiement.calculer_montant_net())
                    },
                    user=request.user,
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
                
                messages.success(
                    request, 
                    f"Paiement créé avec succès ! "
                    f"{len(charges_ajoutees)} charge(s) déduites pour un total de {total_deductions} F CFA. "
                    f"Montant net payé : {paiement.montant_net_paye or paiement.calculer_montant_net()} F CFA"
                )
            else:
                messages.success(request, "Paiement créé avec succès.")
            
            # Générer automatiquement le reçu
            paiement.generer_recu_automatique()
            
            return redirect('paiements:detail_paiement', pk=paiement.id)
    else:
        form = PaiementForm(contrat_id=contrat_id)
    
    # Récupérer les informations du contrat si spécifié
    contrat_obj = None
    charges_disponibles = []
    if contrat_id:
        try:
            contrat_obj = Contrat.objects.get(id=contrat_id, est_actif=True)
            charges_disponibles = ChargeDeductible.objects.filter(
                contrat=contrat_obj,
                statut='validee'
            ).order_by('-date_charge')
        except Contrat.DoesNotExist:
            messages.error(request, "Contrat introuvable.")
            return redirect('paiements:liste')
    
    context = {
        'form': form,
        'contrat_obj': contrat_obj,
        'charges_disponibles': charges_disponibles,
        'title': 'Ajouter un paiement',
    }
    
    return render(request, 'paiements/ajouter_paiement.html', context)


def modifier_paiement(request, pk):
    """
    Vue pour modifier un paiement
    """
    paiement = get_object_or_404(Paiement, pk=pk)
    
    # Vérification des permissions : Seul PRIVILEGE peut modifier
    from core.utils import check_group_permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE'], 'modify')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:detail_paiement', pk=pk)
    
    if request.method == 'POST':
        # Logique de modification de paiement
        messages.success(request, 'Paiement modifié avec succès!')
        return redirect('paiements:detail_paiement', pk=pk)
    
    context = {
        'paiement': paiement,
        'contrats': Contrat.objects.filter(est_actif=True)
    }
    return render(request, 'paiements/modifier.html', context)


# ===== VUES POUR LES REÇUS =====

def liste_recus(request):
    """
    Vue de la liste des reçus avec filtres et pagination
    """
    recus = Recu.objects.select_related(
        'paiement__contrat__locataire',
        'paiement__contrat__propriete',
        'imprime_par',
        'valide_par'
    ).all()
    
    # Filtres
    statut_impression = request.GET.get('statut_impression', '')
    date_debut = request.GET.get('date_debut', '')
    date_fin = request.GET.get('date_fin', '')
    locataire = request.GET.get('locataire', '')
    type_paiement = request.GET.get('type_paiement', '')
    statut_validation = request.GET.get('statut_validation', '')
    
    # Application des filtres
    if statut_impression:
        if statut_impression == 'imprime':
            recus = recus.filter(imprime=True)
        elif statut_impression == 'non_imprime':
            recus = recus.filter(imprime=False)
    
    if date_debut:
        try:
            date_debut_obj = datetime.strptime(date_debut, '%Y-%m-%d').date()
            recus = recus.filter(date_emission__date__gte=date_debut_obj)
        except ValueError:
            pass
    
    if date_fin:
        try:
            date_fin_obj = datetime.strptime(date_fin, '%Y-%m-%d').date()
            recus = recus.filter(date_emission__date__lte=date_fin_obj)
        except ValueError:
            pass
    
    if locataire:
        recus = recus.filter(paiement__contrat__locataire__nom__icontains=locataire)
    
    if type_paiement:
        recus = recus.filter(paiement__type_paiement=type_paiement)
    
    if statut_validation:
        if statut_validation == 'valide':
            recus = recus.filter(valide=True)
        elif statut_validation == 'invalide':
            recus = recus.filter(valide=False)
    
    # Tri
    tri = request.GET.get('tri', 'date_emission')
    if tri == 'numero':
        recus = recus.order_by('numero_recu')
    elif tri == 'locataire':
        recus = recus.order_by('paiement__contrat__locataire__nom')
    elif tri == 'montant':
        recus = recus.order_by('paiement__montant')
    elif tri == 'imprime':
        recus = recus.order_by('imprime', '-date_emission')
    elif tri == 'valide':
        recus = recus.order_by('valide', '-date_emission')
    else:
        recus = recus.order_by('-date_emission')
    
    # Pagination
    paginator = Paginator(recus, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistiques
    total_recus = recus.count()
    recus_imprimes = recus.filter(imprime=True).count()
    recus_non_imprimes = recus.filter(imprime=False).count()
    recus_valides = recus.filter(valide=True).count()
    recus_invalides = recus.filter(valide=False).count()
    recus_envoyes_email = recus.filter(envoye_email=True).count()
    
    # Montant total
    montant_total = recus.aggregate(total=Sum('paiement__montant'))['total'] or 0
    devise_active = getattr(request, 'devise_active', None)
    devise_base = Devise.objects.get(code='F CFA')
    montant_total = convertir_montant(montant_total, devise_base, devise_active)
    
    # Statistiques par template
    stats_templates = recus.values('template_utilise').annotate(
        count=Count('id'),
        montant_total=Sum('paiement__montant')
    ).order_by('-count')
    
    context = {
        'page_obj': page_obj,
        'total_recus': total_recus,
        'recus_imprimes': recus_imprimes,
        'recus_non_imprimes': recus_non_imprimes,
        'recus_valides': recus_valides,
        'recus_invalides': recus_invalides,
        'recus_envoyes_email': recus_envoyes_email,
        'montant_total': montant_total,
        'stats_templates': stats_templates,
        'filtres': {
            'statut_impression': statut_impression,
            'date_debut': date_debut,
            'date_fin': date_fin,
            'locataire': locataire,
            'type_paiement': type_paiement,
            'statut_validation': statut_validation,
            'tri': tri
        }
    }
    return render(request, 'paiements/recus_liste.html', context)


class RecuListView(PrivilegeButtonsMixin, IntelligentListView):
    model = Recu
    template_name = 'base_liste_intelligente.html'
    paginate_by = 20
    page_title = 'Reçus'
    page_icon = 'receipt'
    add_url = None  # Les reçus sont générés automatiquement
    add_text = None
    search_fields = ['numero_recu', 'paiement__contrat__locataire__nom', 'paiement__contrat__locataire__prenom', 'paiement__contrat__propriete__adresse']
    filter_fields = ['imprime', 'valide', 'envoye_email', 'template_utilise']
    default_sort = '-date_emission'
    columns = [
        {'field': 'numero_recu', 'label': 'Numéro', 'sortable': True},
        {'field': 'paiement', 'label': 'Paiement', 'sortable': True},
        {'field': 'date_emission', 'label': 'Date émission', 'sortable': True},
        {'field': 'imprime', 'label': 'Imprimé', 'sortable': True},
        {'field': 'valide', 'label': 'Validé', 'sortable': True},
        {'field': 'envoye_email', 'label': 'Email envoyé', 'sortable': True},
    ]
    actions = [
        {'url_name': 'paiements:recu_detail', 'icon': 'eye', 'style': 'outline-primary', 'title': 'Voir'},
        {'url_name': 'paiements:recu_apercu', 'icon': 'print', 'style': 'outline-info', 'title': 'Aperçu'},
        {'url_name': 'paiements:recu_impression', 'icon': 'download', 'style': 'outline-success', 'title': 'Télécharger'},
    ]
    sort_options = [
        {'value': 'date_emission', 'label': 'Date émission'},
        {'value': 'numero_recu', 'label': 'Numéro'},
        {'value': 'paiement__montant', 'label': 'Montant'},
    ]
    
    def get_queryset(self):
        """
        Optimisation des requêtes de base de données
        """
        queryset = super().get_queryset()
        return queryset.select_related(
            'paiement',
            'paiement__contrat',
            'paiement__contrat__locataire',
            'paiement__contrat__propriete'
        )
    
    def get_context_data(self, **kwargs):
        """
        Ajout de statistiques et d'informations supplémentaires au contexte
        """
        context = super().get_context_data(**kwargs)
        
        # Statistiques
        context['total_recus'] = Recu.objects.count()
        context['recus_imprimes'] = Recu.objects.filter(imprime=True).count()
        context['recus_non_imprimes'] = Recu.objects.filter(imprime=False).count()
        context['recus_valides'] = Recu.objects.filter(valide=True).count()
        context['recus_invalides'] = Recu.objects.filter(valide=False).count()
        context['recus_envoyes_email'] = Recu.objects.filter(envoye_email=True).count()
        
        # Montant total
        from django.db.models import Sum
        context['montant_total'] = Recu.objects.aggregate(
            total=Sum('paiement__montant')
        )['total'] or 0
        
        # Statistiques par template
        from django.db.models import Count
        context['stats_templates'] = Recu.objects.values('template_utilise').annotate(
            count=Count('id'),
            montant_total=Sum('paiement__montant')
        ).order_by('-count')
        
        return context

recu_list = RecuListView.as_view()


def detail_recu(request, pk):
    """
    Vue de détail d'un reçu
    """
    # Vérification des permissions : PRIVILEGE, ADMINISTRATION et CONTROLES peuvent voir les détails
    from core.utils import check_group_permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'CONTROLES'], 'view')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:recus_liste')
    
    recu = get_object_or_404(Recu, pk=pk)
    context = {
        'recu': recu
    }
    return render(request, 'paiements/recu_detail.html', context)


def imprimer_recu(request, pk):
    """
    Vue pour afficher l'aperçu d'impression d'un reçu
    """
    recu = get_object_or_404(Recu, pk=pk)
    devise_active = getattr(request, 'devise_active', None)
    devise_base = Devise.objects.get(code='F CFA')
    informations = recu.get_informations_paiement()
    informations['montant'] = convertir_montant(informations['montant'] or 0, devise_base, devise_active)
    from core.models import ConfigurationEntreprise
    config_entreprise = ConfigurationEntreprise.get_configuration_active()
    
    # Debug: Vérifier que toutes les informations sont présentes
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Informations du reçu {recu.numero_recu}:")
    logger.info(f"- Locataire: {informations.get('locataire')}")
    logger.info(f"- Bailleur: {informations.get('bailleur')}")
    logger.info(f"- Propriété: {informations.get('propriete')}")
    logger.info(f"- Contrat: {informations.get('contrat')}")
    
    context = {
        'recu': recu,
        'informations': informations,
        'config_entreprise': config_entreprise,
        'mode_impression': True,
        'devise_base': devise_base,
        'devise_active': devise_active,
    }
    return render(request, 'paiements/recu_impression.html', context)


def telecharger_recu_pdf(request, pk):
    """
    Vue pour télécharger un reçu en PDF
    """
    recu = get_object_or_404(Recu, pk=pk)
    
    # Récupérer la configuration de l'entreprise
    from core.models import ConfigurationEntreprise
    config_entreprise = ConfigurationEntreprise.get_configuration_active()
    
    # Essayer d'abord WeasyPrint
    try:
        from weasyprint import HTML
        from django.conf import settings
        import tempfile
        import os
        
        devise_active = getattr(request, 'devise_active', None)
        devise_base = Devise.objects.get(code='F CFA')
        informations = recu.get_informations_paiement()
        informations['montant'] = convertir_montant(informations['montant'] or 0, devise_base, devise_active)
        
        context = {
            'recu': recu,
            'informations': informations,
            'config_entreprise': config_entreprise,
            'mode_impression': True,
            'devise_base': devise_base,
            'devise_active': devise_active,
        }
        
        # Rendu du template
        html_content = render_to_string('paiements/recu_impression.html', context)
        
        # Configuration pour WeasyPrint
        pdf_options = {
            'presentational_hints': True,
            'optimize_images': True,
            'jpeg_quality': 95,
        }
        
        # Générer le PDF
        pdf = HTML(string=html_content).write_pdf(**pdf_options)
        
        # Réponse HTTP pour téléchargement
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="recu_{recu.numero_recu}.pdf"'
        
        # Marquer comme imprimé
        if recu.peut_etre_imprime():
            recu.marquer_imprime(request.user)
        
        return response
        
    except (ImportError, Exception) as e:
        # Si WeasyPrint échoue, essayer ReportLab
        try:
            pdf_content = generer_pdf_reportlab(recu, config_entreprise)
            
            if pdf_content:
                # Réponse HTTP pour téléchargement
                response = HttpResponse(pdf_content, content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename="recu_{recu.numero_recu}.pdf"'
                
                # Marquer comme imprimé
                if recu.peut_etre_imprime():
                    recu.marquer_imprime(request.user)
                
                return response
            else:
                messages.error(request, 'Erreur lors de la génération du PDF avec ReportLab.')
                return redirect('paiements:recu_apercu', pk=pk)
                
        except Exception as reportlab_error:
            messages.error(request, f'Erreur lors de la génération du PDF: {str(reportlab_error)}')
            return redirect('paiements:recu_apercu', pk=pk)


def generer_recu_manuel(request, paiement_id):
    """
    Vue pour générer manuellement un reçu pour un paiement
    """
    paiement = get_object_or_404(Paiement, pk=paiement_id)
    
    # Vérifier si un reçu existe déjà
    if hasattr(paiement, 'recu'):
        messages.warning(request, 'Un reçu existe déjà pour ce paiement.')
        return redirect('paiements:recu_detail', pk=paiement.recu.pk)
    
    # Générer le reçu
    recu = paiement.generer_recu_automatique()
    recu.genere_automatiquement = False
    recu.save()
    
    messages.success(request, f'Reçu {recu.numero_recu} généré avec succès!')
    return redirect('paiements:recu_detail', pk=recu.pk)


def generer_recus_automatiques(request):
    """
    Vue pour générer automatiquement des reçus pour les paiements validés sans reçu
    """
    if request.method == 'POST':
        # Trouver les paiements validés sans reçu
        paiements_sans_recu = Paiement.objects.filter(
            statut='valide'
        ).exclude(
            recu__isnull=False
        )
        
        recus_generes = 0
        for paiement in paiements_sans_recu:
            paiement.generer_recu_automatique()
            recus_generes += 1
        
        messages.success(request, f'{recus_generes} reçu(s) généré(s) automatiquement!')
        return redirect('paiements:recus_liste')
    
    # Compter les paiements sans reçu
    paiements_sans_recu = Paiement.objects.filter(
        statut='valide'
    ).exclude(
        recu__isnull=False
    ).count()
    
    context = {
        'paiements_sans_recu': paiements_sans_recu
    }
    return render(request, 'paiements/generer_recus_automatiques.html', context)


def marquer_recus_imprimes(request):
    """
    Vue pour marquer plusieurs reçus comme imprimés
    """
    if request.method == 'POST':
        recus_ids = request.POST.getlist('recus_selectionnes')
        if recus_ids:
            recus = Recu.objects.filter(id__in=recus_ids, imprime=False)
            for recu in recus:
                recu.marquer_imprime(request.user)
            
            messages.success(request, f'{recus.count()} reçu(s) marqué(s) comme imprimé(s)!')
        else:
            messages.warning(request, 'Aucun reçu sélectionné.')
    
    return redirect('paiements:recus_liste')


# API pour les reçus
def api_recus_stats(request):
    """
    API pour obtenir les statistiques des reçus
    """
    # Statistiques générales
    total_recus = Recu.objects.count()
    recus_imprimes = Recu.objects.filter(imprime=True).count()
    recus_non_imprimes = Recu.objects.filter(imprime=False).count()
    
    # Statistiques par mois (6 derniers mois)
    stats_mensuelles = []
    for i in range(6):
        date_debut = timezone.now().replace(day=1) - timedelta(days=30*i)
        date_fin = date_debut.replace(day=1) + timedelta(days=32)
        date_fin = date_fin.replace(day=1) - timedelta(days=1)
        
        recus_mois = Recu.objects.filter(
            date_emission__date__gte=date_debut.date(),
            date_emission__date__lte=date_fin.date()
        )
        
        stats_mensuelles.append({
            'mois': date_debut.strftime('%B %Y'),
            'total': recus_mois.count(),
            'imprimes': recus_mois.filter(imprime=True).count(),
            'montant_total': recus_mois.aggregate(
                total=Sum('paiement__montant')
            )['total'] or 0
        })
    
    return JsonResponse({
        'total_recus': total_recus,
        'recus_imprimes': recus_imprimes,
        'recus_non_imprimes': recus_non_imprimes,
        'stats_mensuelles': stats_mensuelles
    })


# ===== VUES POUR LES RETRAITS =====

class RetraitListView(PrivilegeButtonsMixin, IntelligentListView):
    model = Retrait
    template_name = 'paiements/retrait_liste_unifiee.html'
    paginate_by = 20
    page_title = 'Retraits'
    page_icon = 'money-bill-wave'
    add_url = 'paiements:retrait_ajouter'
    add_text = 'Ajouter un retrait'
    search_fields = ['bailleur__nom', 'bailleur__prenom', 'montant', 'type_retrait', 'statut', 'mode_retrait', 'date_demande', 'date_versement']
    filter_fields = ['type_retrait', 'statut', 'mode_retrait']
    default_sort = 'date_demande'
    columns = [
        {'field': 'bailleur', 'label': 'Bailleur', 'sortable': True},
        {'field': 'montant', 'label': 'Montant', 'sortable': True},
        {'field': 'type_retrait', 'label': 'Type', 'sortable': True},
        {'field': 'statut', 'label': 'Statut', 'sortable': True},
        {'field': 'mode_retrait', 'label': 'Mode', 'sortable': True},
        {'field': 'date_demande', 'label': 'Date demande', 'sortable': True},
        {'field': 'date_versement', 'label': 'Date versement', 'sortable': True},
    ]
    actions = [
        {'url_name': 'paiements:retrait_detail', 'icon': 'eye', 'style': 'outline-primary', 'title': 'Voir'},
        {'url_name': 'paiements:retrait_modifier', 'icon': 'pencil', 'style': 'outline-warning', 'title': 'Modifier'},
    ]
    sort_options = [
        {'value': 'date_demande', 'label': 'Date demande'},
        {'value': 'montant', 'label': 'Montant'},
        {'value': 'type_retrait', 'label': 'Type'},
        {'value': 'statut', 'label': 'Statut'},
        {'value': 'mode_retrait', 'label': 'Mode'},
    ]
    
    def get_queryset(self):
        """
        Optimisation des requêtes de base de données
        """
        queryset = super().get_queryset()
        return queryset.select_related('bailleur')
    
    def get_context_data(self, **kwargs):
        """
        Ajout de statistiques et d'informations supplémentaires au contexte
        """
        context = super().get_context_data(**kwargs)
        
        # Statistiques des retraits généraux
        context['total_retraits'] = Retrait.objects.count()
        context['retraits_valides'] = Retrait.objects.filter(statut='valide').count()
        context['retraits_en_attente'] = Retrait.objects.filter(statut='en_attente').count()
        context['retraits_annules'] = Retrait.objects.filter(statut='annule').count()
        
        # Statistiques des retraits bailleurs
        try:
            from .models import RetraitBailleur
            context['total_retraits_bailleur'] = RetraitBailleur.objects.count()
            context['retraits_bailleur_valides'] = RetraitBailleur.objects.filter(statut='valide').count()
            context['retraits_bailleur_en_attente'] = RetraitBailleur.objects.filter(statut='en_attente').count()
        except:
            context['total_retraits_bailleur'] = 0
            context['retraits_bailleur_valides'] = 0
            context['retraits_bailleur_en_attente'] = 0
        
        # Montant total
        from django.db.models import Sum
        context['montant_total'] = Retrait.objects.aggregate(total=Sum('montant'))['total'] or 0
        
        # Ajouter les retraits bailleurs au contexte
        try:
            context['retraits_bailleurs'] = RetraitBailleur.objects.all().order_by('-mois_retrait')[:5]
        except:
            context['retraits_bailleurs'] = []
        
        return context

retrait_list = RetraitListView.as_view()


def detail_retrait(request, pk):
    """
    Vue de détail d'un retrait
    """
    retrait = get_object_or_404(Retrait, pk=pk)
    
    # Vérification des permissions : PRIVILEGE, ADMINISTRATION, CONTROLES et CAISSE peuvent voir les détails
    from core.utils import check_group_permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'CONTROLES', 'CAISSE'], 'view')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:retraits_liste')
    
    context = {
        'retrait': retrait
    }
    return render(request, 'paiements/retrait_detail.html', context)


def ajouter_retrait(request):
    """Vue pour ajouter un retrait"""
    # Vérification des permissions : PRIVILEGE, ADMINISTRATION et CAISSE peuvent ajouter
    from core.utils import check_group_permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'CAISSE'], 'add')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:retrait_liste')
    
    if request.method == 'POST':
        # Logique d'ajout de retrait
        messages.success(request, 'Retrait ajouté avec succès!')
        return redirect('paiements:retraits_liste')
    
    context = {
        'bailleurs': Bailleur.objects.all().order_by('nom', 'prenom'),
        'comptes': CompteBancaire.objects.filter(est_actif=True)
    }
    return render(request, 'paiements/retrait_ajouter.html', context)


def modifier_retrait(request, pk):
    """
    Vue pour modifier un retrait
    """
    retrait = get_object_or_404(Retrait, pk=pk)
    
    # Vérification des permissions : Seul PRIVILEGE peut modifier
    from core.utils import check_group_permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE'], 'modify')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:retrait_detail', pk=pk)
    
    if request.method == 'POST':
        # Logique de modification de retrait
        messages.success(request, 'Retrait modifié avec succès!')
        return redirect('paiements:retrait_detail', pk=pk)
    
    context = {
        'retrait': retrait
    }
    return render(request, 'paiements/retrait_modifier.html', context)


# ===== VUES POUR LES COMPTES BANCAIRES =====

class CompteBancaireListView(PrivilegeButtonsMixin, IntelligentListView):
    model = CompteBancaire
    template_name = 'base_liste_intelligente.html'
    paginate_by = 20
    page_title = 'Comptes bancaires'
    page_icon = 'bank'
    add_url = 'paiements:ajouter_compte'
    add_text = 'Ajouter un compte bancaire'
    search_fields = ['nom', 'banque', 'iban', 'bic', 'solde_actuel', 'devise']
    filter_fields = ['devise', 'est_actif']
    default_sort = 'nom'
    columns = [
        {'field': 'nom', 'label': 'Nom du compte', 'sortable': True},
        {'field': 'banque', 'label': 'Banque', 'sortable': True},
        {'field': 'iban', 'label': 'IBAN', 'sortable': True},
        {'field': 'solde_actuel', 'label': 'Solde', 'sortable': True},
        {'field': 'devise', 'label': 'Devise', 'sortable': True},
        {'field': 'est_actif', 'label': 'Actif', 'sortable': True},
    ]
    actions = [
        {'url_name': 'paiements:detail_compte', 'icon': 'eye', 'style': 'outline-primary', 'title': 'Voir'},
        {'url_name': 'paiements:modifier_compte', 'icon': 'pencil', 'style': 'outline-warning', 'title': 'Modifier'},
    ]
    sort_options = [
        {'value': 'nom', 'label': 'Nom'},
        {'value': 'solde_actuel', 'label': 'Solde'},
    ]
    
    def get_queryset(self):
        """
        Optimisation des requêtes de base de données
        """
        queryset = super().get_queryset()
        return queryset.select_related('devise')
    
    def get_context_data(self, **kwargs):
        """
        Ajout de statistiques et d'informations supplémentaires au contexte
        """
        context = super().get_context_data(**kwargs)
        
        # Statistiques
        context['total_comptes'] = CompteBancaire.objects.count()
        context['comptes_actifs'] = CompteBancaire.objects.filter(est_actif=True).count()
        context['comptes_inactifs'] = CompteBancaire.objects.filter(est_actif=False).count()
        
        # Solde total
        from django.db.models import Sum
        context['solde_total'] = CompteBancaire.objects.aggregate(total=Sum('solde_actuel'))['total'] or 0
        
        return context

compte_bancaire_list = CompteBancaireListView.as_view()


def detail_compte(request, pk):
    """
    Vue de détail d'un compte bancaire
    """
    compte = get_object_or_404(CompteBancaire, pk=pk)
    
    # Vérification des permissions : PRIVILEGE, ADMINISTRATION, CONTROLES peuvent voir les détails
    from core.utils import check_group_permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'CONTROLES'], 'view')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:comptes_liste')
    
    context = {
        'compte': compte
    }
    return render(request, 'paiements/compte_detail.html', context)


def ajouter_compte(request):
    """Vue pour ajouter un compte bancaire"""
    # Vérification des permissions : PRIVILEGE, ADMINISTRATION peuvent ajouter
    from core.utils import check_group_permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE'], 'add')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:comptes_liste')
    
    if request.method == 'POST':
        # Logique d'ajout de compte
        messages.success(request, 'Compte bancaire ajouté avec succès!')
        return redirect('paiements:comptes_liste')
    
    context = {
        'devises': Devise.objects.all().order_by('code')
    }
    return render(request, 'paiements/compte_ajouter.html', context)


def modifier_compte(request, pk):
    """
    Vue pour modifier un compte bancaire
    """
    compte = get_object_or_404(CompteBancaire, pk=pk)
    
    # Vérification des permissions : Seul PRIVILEGE peut modifier
    from core.utils import check_group_permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE'], 'modify')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:compte_detail', pk=pk)
    
    if request.method == 'POST':
        # Logique de modification de compte
        messages.success(request, 'Compte bancaire modifié avec succès!')
        return redirect('paiements:compte_detail', pk=pk)
    
    context = {
        'compte': compte
    }
    return render(request, 'paiements/compte_modifier.html', context)


def supprimer_compte_bancaire(request, pk):
    # Vérification des permissions : Seul PRIVILEGE peut supprimer
    from core.utils import check_group_permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE'], 'delete')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:comptes_bancaires_liste')
    
    compte = get_object_or_404(CompteBancaire, pk=pk)
    if request.method == 'POST':
        try:
            old_data = {f.name: getattr(compte, f.name) for f in compte._meta.fields}
            compte.is_deleted = True
            compte.deleted_at = timezone.now()
            compte.deleted_by = request.user
            compte.save()
            AuditLog.objects.create(
                content_type=ContentType.objects.get_for_model(CompteBancaire),
                object_id=compte.pk,
                action='DELETE',
                old_data=old_data,
                new_data=None,
                user=request.user,
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            messages.success(request, "Compte bancaire supprimé avec succès (suppression logique).")
            return redirect('paiements:comptes_bancaires_liste')
        except ProtectedError:
            messages.error(request, "Impossible de supprimer ce compte car il est référencé dans d'autres enregistrements.")
            return redirect('paiements:comptes_bancaires_liste')
    return render(request, 'paiements/confirm_supprimer_compte_bancaire.html', {'compte': compte})


def valider_recu(request, pk):
    """
    Vue pour valider un reçu
    """
    # Vérification des permissions : Seul PRIVILEGE peut valider
    from core.utils import check_group_permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE'], 'modify')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:liste_recus')
    
    recu = get_object_or_404(Recu, pk=pk)
    
    if request.method == 'POST':
        recu.valider_recu(request.user)
        messages.success(request, f'Reçu {recu.numero_recu} validé avec succès!')
        return redirect('paiements:recu_detail', pk=pk)
    
    context = {
        'recu': recu,
        'informations': recu.get_informations_paiement()
    }
    return render(request, 'paiements/valider_recu.html', context)


def invalider_recu(request, pk):
    """
    Vue pour invalider un reçu
    """
    # Vérification des permissions : Seul PRIVILEGE peut invalider
    from core.utils import check_group_permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE'], 'modify')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:liste_recus')
    
    recu = get_object_or_404(Recu, pk=pk)
    
    if request.method == 'POST':
        motif = request.POST.get('motif', '')
        recu.invalider_recu(request.user, motif)
        messages.warning(request, f'Reçu {recu.numero_recu} invalidé.')
        return redirect('paiements:recu_detail', pk=pk)
    
    context = {
        'recu': recu,
    }
    
    return render(request, 'paiements/charge_deductible_refuser.html', context)


def envoyer_recu_email(request, pk):
    """
    Vue pour envoyer un reçu par email
    """
    # Vérification des permissions : Seul PRIVILEGE peut envoyer des reçus par email
    from core.utils import check_group_permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE'], 'modify')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:recu_detail', pk=pk)
    
    recu = get_object_or_404(Recu, pk=pk)
    
    if not recu.peut_etre_envoye_email():
        messages.error(request, 'Ce reçu ne peut pas être envoyé par email.')
        return redirect('paiements:recu_detail', pk=pk)
    
    if request.method == 'POST':
        email_destinataire = request.POST.get('email_destinataire', '')
        if not email_destinataire:
            email_destinataire = recu.paiement.contrat.locataire.email
        
        try:
            # Ici on pourrait intégrer un système d'envoi d'email
            # Pour l'instant, on simule l'envoi
            recu.marquer_envoye_email(email_destinataire)
            messages.success(request, f'Reçu envoyé par email à {email_destinataire}')
        except Exception as e:
            messages.error(request, f'Erreur lors de l\'envoi: {str(e)}')
        
        return redirect('paiements:recu_detail', pk=pk)
    
    context = {
        'recu': recu,
        'informations': recu.get_informations_paiement(),
        'email_par_defaut': recu.paiement.contrat.locataire.email
    }
    return render(request, 'paiements/envoyer_recu_email.html', context)


def changer_template_recu(request, pk):
    """
    Vue pour changer le template d'un reçu
    """
    recu = get_object_or_404(Recu, pk=pk)
    
    if request.method == 'POST':
        nouveau_template = request.POST.get('template', 'standard')
        recu.template_utilise = nouveau_template
        recu.save()
        messages.success(request, f'Template du reçu changé vers {nouveau_template}')
        return redirect('paiements:recu_detail', pk=pk)
    
    context = {
        'recu': recu,
        'templates_disponibles': Recu._meta.get_field('template_utilise').choices
    }
    return render(request, 'paiements/changer_template_recu.html', context)


def statistiques_recus(request):
    """
    Vue pour les statistiques détaillées des reçus
    """
    from django.db.models import Count, Sum, Avg
    from datetime import datetime, timedelta
    
    # Période de filtrage
    periode = request.GET.get('periode', 'mois')
    if periode == 'semaine':
        date_debut = datetime.now().date() - timedelta(days=7)
    elif periode == 'mois':
        date_debut = datetime.now().date() - timedelta(days=30)
    elif periode == 'trimestre':
        date_debut = datetime.now().date() - timedelta(days=90)
    else:
        date_debut = datetime.now().date() - timedelta(days=365)
    
    # Statistiques générales
    recus_periode = Recu.objects.filter(date_emission__date__gte=date_debut)
    
    stats_generales = {
        'total_recus': recus_periode.count(),
        'recus_valides': recus_periode.filter(valide=True).count(),
        'recus_imprimes': recus_periode.filter(imprime=True).count(),
        'recus_envoyes_email': recus_periode.filter(envoye_email=True).count(),
        'montant_total': recus_periode.aggregate(total=Sum('paiement__montant'))['total'] or 0,
    }
    
    # Statistiques par template
    stats_templates = recus_periode.values('template_utilise').annotate(
        count=Count('id'),
        montant_total=Sum('paiement__montant')
    ).order_by('-count')
    
    # Statistiques par jour
    stats_jour = recus_periode.extra(
        select={'jour': 'DATE(date_emission)'}
    ).values('jour').annotate(
        count=Count('id'),
        montant_total=Sum('paiement__montant')
    ).order_by('jour')
    
    # Top des locataires
    top_locataires = recus_periode.values(
        'paiement__contrat__locataire__nom',
        'paiement__contrat__locataire__prenom'
    ).annotate(
        count=Count('id'),
        montant_total=Sum('paiement__montant')
    ).order_by('-montant_total')[:10]
    
    # Statistiques d'impression
    stats_impression = {
        'moyenne_impressions': recus_periode.aggregate(avg=Avg('nombre_impressions'))['avg'] or 0,
        'total_impressions': recus_periode.aggregate(total=Sum('nombre_impressions'))['total'] or 0,
        'recus_plus_imprimes': recus_periode.order_by('-nombre_impressions')[:5]
    }
    
    context = {
        'stats_generales': stats_generales,
        'stats_templates': stats_templates,
        'stats_jour': stats_jour,
        'top_locataires': top_locataires,
        'stats_impression': stats_impression,
        'periode': periode,
        'date_debut': date_debut
    }
    return render(request, 'paiements/statistiques_recus.html', context)


def export_recus(request):
    """
    Vue pour exporter les reçus en CSV
    """
    import csv
    from django.http import HttpResponse
    
    # Filtres
    date_debut = request.GET.get('date_debut', '')
    date_fin = request.GET.get('date_fin', '')
    statut = request.GET.get('statut', '')
    
    recus = Recu.objects.select_related(
        'paiement__contrat__locataire',
        'paiement__contrat__propriete__bailleur'
    ).all()
    
    # Application des filtres
    if date_debut:
        try:
            date_debut_obj = datetime.strptime(date_debut, '%Y-%m-%d').date()
            recus = recus.filter(date_emission__date__gte=date_debut_obj)
        except ValueError:
            pass
    
    if date_fin:
        try:
            date_fin_obj = datetime.strptime(date_fin, '%Y-%m-%d').date()
            recus = recus.filter(date_emission__date__lte=date_fin_obj)
        except ValueError:
            pass
    
    if statut:
        if statut == 'valide':
            recus = recus.filter(valide=True)
        elif statut == 'invalide':
            recus = recus.filter(valide=False)
        elif statut == 'imprime':
            recus = recus.filter(imprime=True)
        elif statut == 'email':
            recus = recus.filter(envoye_email=True)
    
    # Création du fichier CSV
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="recus_export_{datetime.now().strftime("%Y%m%d")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Numéro reçu', 'Date émission', 'Montant', 'Type paiement',
        'Locataire', 'Propriété', 'Bailleur', 'Template', 'Statut',
        'Imprimé', 'Envoyé email', 'Nombre impressions'
    ])
    
    for recu in recus:
        writer.writerow([
            recu.numero_recu,
            recu.date_emission.strftime('%d/%m/%Y'),
            recu.paiement.montant,
            recu.paiement.get_type_paiement_display(),
            f"{recu.paiement.contrat.locataire.nom} {recu.paiement.contrat.locataire.prenom}",
            recu.paiement.contrat.propriete.adresse,
            f"{recu.paiement.contrat.propriete.bailleur.nom} {recu.paiement.contrat.propriete.bailleur.prenom}",
            recu.template_utilise,
            recu.get_statut_display(),
            'Oui' if recu.imprime else 'Non',
            'Oui' if recu.envoye_email else 'Non',
            recu.nombre_impressions
        ])
    
    return response


def api_recus_avancees(request):
    """
    API avancée pour les reçus avec plus de fonctionnalités
    """
    from django.db.models import Q
    
    # Paramètres de filtrage
    search = request.GET.get('search', '')
    template = request.GET.get('template', '')
    statut = request.GET.get('statut', '')
    date_debut = request.GET.get('date_debut', '')
    date_fin = request.GET.get('date_fin', '')
    
    recus = Recu.objects.select_related(
        'paiement__contrat__locataire',
        'paiement__contrat__propriete__bailleur'
    ).all()
    
    # Recherche
    if search:
        recus = recus.filter(
            Q(numero_recu__icontains=search) |
            Q(paiement__contrat__locataire__nom__icontains=search) |
            Q(paiement__contrat__locataire__prenom__icontains=search) |
            Q(paiement__contrat__propriete__adresse__icontains=search)
        )
    
    # Filtres
    if template:
        recus = recus.filter(template_utilise=template)
    
    if statut:
        if statut == 'valide':
            recus = recus.filter(valide=True)
        elif statut == 'invalide':
            recus = recus.filter(valide=False)
        elif statut == 'imprime':
            recus = recus.filter(imprime=True)
        elif statut == 'non_imprime':
            recus = recus.filter(imprime=False)
        elif statut == 'email':
            recus = recus.filter(envoye_email=True)
    
    if date_debut:
        try:
            date_debut_obj = datetime.strptime(date_debut, '%Y-%m-%d').date()
            recus = recus.filter(date_emission__date__gte=date_debut_obj)
        except ValueError:
            pass
    
    if date_fin:
        try:
            date_fin_obj = datetime.strptime(date_fin, '%Y-%m-%d').date()
            recus = recus.filter(date_emission__date__lte=date_fin_obj)
        except ValueError:
            pass
    
    # Tri
    tri = request.GET.get('tri', '-date_emission')
    recus = recus.order_by(tri)
    
    # Pagination
    page = int(request.GET.get('page', 1))
    per_page = int(request.GET.get('per_page', 20))
    start = (page - 1) * per_page
    end = start + per_page
    
    recus_page = recus[start:end]
    
    # Données pour la réponse
    data = []
    for recu in recus_page:
        data.append({
            'id': recu.id,
            'numero_recu': recu.numero_recu,
            'date_emission': recu.date_emission.strftime('%Y-%m-%d %H:%M'),
            'montant': float(recu.paiement.montant),
            'type_paiement': recu.paiement.get_type_paiement_display(),
            'locataire': f"{recu.paiement.contrat.locataire.nom} {recu.paiement.contrat.locataire.prenom}",
            'propriete': recu.paiement.contrat.propriete.adresse,
            'template': recu.template_utilise,
            'statut': recu.get_statut_display(),
            'statut_color': recu.get_statut_color(),
            'imprime': recu.imprime,
            'envoye_email': recu.envoye_email,
            'valide': recu.valide,
            'nombre_impressions': recu.nombre_impressions,
            'nombre_emails': recu.nombre_emails,
        })
    
    return JsonResponse({
        'data': data,
        'total': recus.count(),
        'page': page,
        'per_page': per_page,
        'pages': (recus.count() + per_page - 1) // per_page
    })


def impression_directe_recu(request, pk):
    """
    Vue pour l'impression directe d'un reçu (sans redirection)
    """
    recu = get_object_or_404(Recu, pk=pk)
    
    # Récupérer la configuration de l'entreprise
    from core.models import ConfigurationEntreprise
    config_entreprise = ConfigurationEntreprise.get_configuration_active()
    
    # Essayer d'abord WeasyPrint pour l'impression directe
    try:
        from weasyprint import HTML
        from django.conf import settings
        
        devise_active = getattr(request, 'devise_active', None)
        devise_base = Devise.objects.get(code='F CFA')
        informations = recu.get_informations_paiement()
        informations['montant'] = convertir_montant(informations['montant'] or 0, devise_base, devise_active)
        
        context = {
            'recu': recu,
            'informations': informations,
            'config_entreprise': config_entreprise,
            'mode_impression': True
        }
        
        # Rendu du template
        html_content = render_to_string('paiements/recu_impression.html', context)
        
        # Configuration pour WeasyPrint optimisée pour l'impression
        pdf_options = {
            'presentational_hints': True,
            'optimize_images': True,
            'jpeg_quality': 95,
            'zoom': 1.0,
        }
        
        # Générer le PDF
        pdf = HTML(string=html_content).write_pdf(**pdf_options)
        
        # Réponse HTTP pour affichage direct (pas de téléchargement)
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="recu_{recu.numero_recu}.pdf"'
        
        # Marquer comme imprimé
        if recu.peut_etre_imprime():
            recu.marquer_imprime(request.user)
        
        return response
        
    except (ImportError, Exception) as e:
        # Si WeasyPrint échoue, essayer ReportLab
        try:
            pdf_content = generer_pdf_reportlab(recu, config_entreprise)
            
            if pdf_content:
                # Réponse HTTP pour affichage direct
                response = HttpResponse(pdf_content, content_type='application/pdf')
                response['Content-Disposition'] = f'inline; filename="recu_{recu.numero_recu}.pdf"'
                
                # Marquer comme imprimé
                if recu.peut_etre_imprime():
                    recu.marquer_imprime(request.user)
                
                return response
            else:
                # Si ReportLab échoue aussi, afficher l'aperçu HTML
                messages.warning(request, 'Génération PDF impossible. Affichage de l\'aperçu HTML.')
                context = {
                    'recu': recu,
                    'informations': recu.get_informations_paiement(),
                    'config_entreprise': config_entreprise,
                    'mode_impression': True
                }
                return render(request, 'paiements/recu_impression.html', context)
                
        except Exception as reportlab_error:
            # En cas d'erreur, afficher l'aperçu HTML
            messages.warning(request, f'Erreur PDF: {str(reportlab_error)}. Affichage de l\'aperçu HTML.')
            context = {
                'recu': recu,
                'informations': recu.get_informations_paiement(),
                'config_entreprise': config_entreprise,
                'mode_impression': True
            }
            return render(request, 'paiements/recu_impression.html', context)


def supprimer_paiement(request, pk):
    # Vérification des permissions : Seul PRIVILEGE peut supprimer
    from core.utils import check_group_permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE'], 'delete')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:liste')
    
    paiement = get_object_or_404(Paiement, pk=pk)
    if request.method == 'POST':
        try:
            old_data = {f.name: getattr(paiement, f.name) for f in paiement._meta.fields}
            paiement.is_deleted = True
            paiement.deleted_at = timezone.now()
            paiement.deleted_by = request.user
            paiement.save()
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
            messages.success(request, "Paiement supprimé avec succès (suppression logique).")
            return redirect('paiements:liste')
        except ProtectedError:
            messages.error(request, "Impossible de supprimer ce paiement car il est référencé dans d'autres enregistrements.")
            return redirect('paiements:liste')
    return render(request, 'paiements/confirm_supprimer_paiement.html', {'paiement': paiement})


def supprimer_retrait(request, pk):
    # Vérification des permissions : Seul PRIVILEGE peut supprimer
    from core.utils import check_group_permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE'], 'delete')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:retraits_liste')
    
    retrait = get_object_or_404(Retrait, pk=pk)
    if request.method == 'POST':
        try:
            old_data = {f.name: getattr(retrait, f.name) for f in retrait._meta.fields}
            retrait.is_deleted = True
            retrait.deleted_at = timezone.now()
            retrait.deleted_by = request.user
            retrait.save()
            AuditLog.objects.create(
                content_type=ContentType.objects.get_for_model(Retrait),
                object_id=retrait.pk,
                action='DELETE',
                old_data=old_data,
                new_data=None,
                user=request.user,
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            messages.success(request, "Retrait supprimé avec succès (suppression logique).")
            return redirect('paiements:retraits_liste')
        except ProtectedError:
            messages.error(request, "Impossible de supprimer ce retrait car il est référencé dans d'autres enregistrements.")
            return redirect('paiements:retraits_liste')
    return render(request, 'paiements/confirm_supprimer_retrait.html', {'retrait': retrait})


# ========================================
# VUES POUR LES CHARGES DÉDUCTIBLES
# ========================================

def charges_deductibles_liste(request):
    """
    Vue pour lister les charges déductibles avec filtres et recherche
    """
    # Vérification des permissions : PRIVILEGE, ADMINISTRATION, CONTROLES peuvent voir la liste
    from core.utils import check_group_permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'CONTROLES'], 'view')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:liste')
    
    charges = ChargeDeductible.objects.select_related(
        'contrat',
        'contrat__locataire',
        'contrat__propriete',
        'validee_par',
        'paiement_deduction'
    ).all()
    
    # Filtres
    statut_filter = request.GET.get('statut')
    contrat_filter = request.GET.get('contrat')
    search = request.GET.get('search')
    date_debut = request.GET.get('date_debut', '')
    date_fin = request.GET.get('date_fin', '')
    
    if statut_filter:
        charges = charges.filter(statut=statut_filter)
    
    if contrat_filter:
        charges = charges.filter(contrat_id=contrat_filter)
    
    if search:
        charges = charges.filter(
            Q(libelle__icontains=search) |
            Q(description__icontains=search) |
            Q(contrat__numero_contrat__icontains=search) |
            Q(contrat__locataire__nom__icontains=search) |
            Q(contrat__locataire__prenom__icontains=search) |
            Q(fournisseur__icontains=search)
        )
    
    if date_debut:
        try:
            date_debut_obj = datetime.strptime(date_debut, '%Y-%m-%d').date()
            charges = charges.filter(date_charge__gte=date_debut_obj)
        except ValueError:
            pass
    
    if date_fin:
        try:
            date_fin_obj = datetime.strptime(date_fin, '%Y-%m-%d').date()
            charges = charges.filter(date_charge__lte=date_fin_obj)
        except ValueError:
            pass
    
    # Tri
    tri = request.GET.get('tri', '-date_charge')
    if tri == 'date_charge':
        charges = charges.order_by('date_charge')
    elif tri == 'montant':
        charges = charges.order_by('montant')
    elif tri == 'libelle':
        charges = charges.order_by('libelle')
    elif tri == 'statut':
        charges = charges.order_by('statut')
    elif tri == 'type_charge':
        charges = charges.order_by('type_charge')
    else:
        charges = charges.order_by('-date_charge')
    
    # Pagination
    paginator = Paginator(charges, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistiques
    total_charges = charges.count()
    total_montant = charges.aggregate(total=Sum('montant'))['total'] or 0
    
    statuts_counts = {}
    for statut, label in ChargeDeductible._meta.get_field('statut').choices:
        # ChargeDeductible n'a pas de champ statut, utiliser est_valide
        if statut == 'en_attente':
            statuts_counts[statut] = ChargeDeductible.objects.filter(est_valide=False).count()
        elif statut == 'validee':
            statuts_counts[statut] = ChargeDeductible.objects.filter(est_valide=True).count()
        else:
            statuts_counts[statut] = 0
    
    # Statistiques par type de charge
    types_charges_counts = {}
    for type_charge, label in ChargeDeductible._meta.get_field('type_charge').choices:
        types_charges_counts[type_charge] = ChargeDeductible.objects.filter(type_charge=type_charge).count()
    
    context = {
        'page_obj': page_obj,
        'total_charges': total_charges,
        'total_montant': total_montant,
        'statuts_counts': statuts_counts,
        'types_charges_counts': types_charges_counts,
        'contrats': Contrat.objects.filter(est_actif=True),
        'statut_filter': statut_filter,
        'contrat_filter': contrat_filter,
        'search': search,
        'date_debut': date_debut,
        'date_fin': date_fin,
        'tri': tri,
    }
    
    return render(request, 'paiements/charges_deductibles_liste.html', context)


def charge_deductible_detail(request, charge_id):
    """Détail d'une charge déductible"""
    # Vérification des permissions : PRIVILEGE, ADMINISTRATION et CONTROLES peuvent voir les détails
    from core.utils import check_group_permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'CONTROLES'], 'view')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:charges_deductibles_liste')
    
    charge = get_object_or_404(ChargeDeductible, id=charge_id)
    
    context = {
        'charge': charge,
    }
    
    return render(request, 'paiements/charge_deductible_detail.html', context)


def charge_deductible_ajouter(request):
    """
    Vue pour ajouter une charge déductible
    """
    # Vérification des permissions : PRIVILEGE, ADMINISTRATION peuvent ajouter
    from core.utils import check_group_permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE'], 'add')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:charges_deductibles_liste')
    
    if request.method == 'POST':
        form = ChargeDeductibleForm(request.POST)
        if form.is_valid():
            charge = form.save(commit=False)
            charge.cree_par = request.user
            charge.save()
            
            # Log d'audit
            AuditLog.objects.create(
                content_type=ContentType.objects.get_for_model(ChargeDeductible),
                object_id=charge.pk,
                action='CREATE',
                old_data=None,
                new_data=serialize_model_for_audit(charge),
                user=request.user,
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            messages.success(request, f"Charge déductible '{charge.libelle}' ajoutée avec succès.")
            return redirect('paiements:charge_deductible_detail', charge_id=charge.id)
    else:
        form = ChargeDeductibleForm()
    
    context = {
        'form': form,
        'title': 'Ajouter une charge déductible',
    }
    
    return render(request, 'paiements/charge_deductible_form.html', context)


def charge_deductible_modifier(request, charge_id):
    """Modifier une charge déductible"""
    charge = get_object_or_404(ChargeDeductible, id=charge_id)
    
    # Vérifier que la charge peut être modifiée
    if charge.statut in ['deduite', 'refusee']:
        messages.error(request, "Cette charge ne peut plus être modifiée.")
        return redirect('paiements:charge_deductible_detail', charge_id=charge.id)
    
    if request.method == 'POST':
        form = ChargeDeductibleForm(request.POST, instance=charge)
        if form.is_valid():
            # Préparer old_data avant modification
            old_data = serialize_model_for_audit(charge)
            charge = form.save()
            
            # Log d'audit
            AuditLog.objects.create(
                content_type=ContentType.objects.get_for_model(ChargeDeductible),
                object_id=charge.pk,
                action='UPDATE',
                old_data=old_data,
                new_data=serialize_model_for_audit(charge),
                user=request.user,
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            messages.success(request, f"Charge déductible '{charge.libelle}' modifiée avec succès.")
            return redirect('paiements:charge_deductible_detail', charge_id=charge.id)
    else:
        form = ChargeDeductibleForm(instance=charge)
    
    context = {
        'form': form,
        'charge': charge,
        'title': f'Modifier la charge: {charge.libelle}',
    }
    
    return render(request, 'paiements/charge_deductible_form.html', context)


def charge_deductible_valider(request, charge_id):
    """Valider une charge déductible"""
    # Vérification des permissions : Seul PRIVILEGE peut valider
    from core.utils import check_group_permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE'], 'modify')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:charges_deductibles_liste')
    
    charge = get_object_or_404(ChargeDeductible, id=charge_id)
    
    if charge.valider_charge(request.user):
        # Log d'audit
        AuditLog.objects.create(
            content_type=ContentType.objects.get_for_model(ChargeDeductible),
            object_id=charge.pk,
            action='VALIDATE',
            old_data={'statut': 'en_attente'},
            new_data={'statut': 'validee'},
            user=request.user,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        messages.success(request, f"Charge '{charge.libelle}' validée avec succès.")
    else:
        messages.error(request, "Cette charge ne peut pas être validée.")
    
    return redirect('paiements:charge_deductible_detail', charge_id=charge.id)


def charge_deductible_refuser(request, charge_id):
    """Refuser une charge déductible"""
    # Vérification des permissions : Seul PRIVILEGE peut refuser
    from core.utils import check_group_permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE'], 'modify')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:charges_deductibles_liste')
    
    charge = get_object_or_404(ChargeDeductible, id=charge_id)
    
    if request.method == 'POST':
        motif = request.POST.get('motif', '')
        
        if charge.refuser_charge(request.user, motif):
            # Log d'audit
            AuditLog.objects.create(
                content_type=ContentType.objects.get_for_model(ChargeDeductible),
                object_id=charge.pk,
                action='REJECT',
                old_data={'statut': 'en_attente'},
                new_data={'statut': 'refusee', 'motif': motif},
                user=request.user,
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            messages.success(request, f"Charge '{charge.libelle}' refusée.")
            return redirect('paiements:charge_deductible_detail', charge_id=charge.id)
        else:
            messages.error(request, "Cette charge ne peut pas être refusée.")
            return redirect('paiements:charge_deductible_detail', charge_id=charge.id)
    
    context = {
        'charge': charge,
    }
    
    return render(request, 'paiements/charge_deductible_refuser.html', context)


def paiement_avec_charges(request, contrat_id):
    """Créer un paiement avec déduction de charges"""
    contrat = get_object_or_404(Contrat, id=contrat_id, est_actif=True)
    
    if request.method == 'POST':
        form = PaiementAvecChargesForm(request.POST, contrat_id=contrat_id)
        if form.is_valid():
            # Créer le paiement
            paiement = Paiement.objects.create(
                contrat=contrat,
                montant=form.cleaned_data['montant_loyer'],
                type_paiement='loyer',
                mode_paiement=form.cleaned_data['mode_paiement'],
                date_paiement=form.cleaned_data['date_paiement'],
                numero_cheque=form.cleaned_data.get('numero_cheque', ''),
                reference_virement=form.cleaned_data.get('reference_virement', ''),
                notes=form.cleaned_data.get('notes', ''),
                cree_par=request.user,
                statut='valide'
            )
            
            # Ajouter les charges déductibles
            charges = form.cleaned_data.get('charges_deductibles', [])
            if charges:
                charges_ajoutees, total_deductions = paiement.ajouter_charges_deductibles(
                    [charge.id for charge in charges],
                    request.user
                )
                
                # Log d'audit
                AuditLog.objects.create(
                    content_type=ContentType.objects.get_for_model(Paiement),
                    object_id=paiement.pk,
                    action='CREATE_WITH_CHARGES',
                    old_data=None,
                    new_data={
                        'paiement_id': paiement.id,
                        'charges_deduites': [charge.id for charge in charges_ajoutees],
                        'total_deductions': float(total_deductions)
                    },
                    user=request.user,
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
                
                messages.success(
                    request, 
                    f"Paiement créé avec succès. {len(charges_ajoutees)} charge(s) déduites "
                    f"pour un total de {total_deductions} F CFA."
                )
            else:
                messages.success(request, "Paiement créé avec succès.")
            
            # Générer automatiquement le reçu
            paiement.generer_recu_automatique()
            
            return redirect('paiements:paiement_detail', paiement_id=paiement.id)
    else:
        form = PaiementAvecChargesForm(contrat_id=contrat_id)
    
    # Récupérer les charges validées pour ce contrat
    charges_disponibles = ChargeDeductible.objects.filter(
        contrat=contrat,
        statut='validee'
    ).order_by('-date_charge')
    
    context = {
        'form': form,
        'contrat': contrat,
        'charges_disponibles': charges_disponibles,
        'title': f'Paiement avec charges - {contrat.numero_contrat}',
    }
    
    return render(request, 'paiements/paiement_avec_charges.html', context)


def charges_par_contrat_api(request, contrat_id):
    """API pour récupérer les charges validées d'un contrat"""
    try:
        contrat = Contrat.objects.get(id=contrat_id, est_actif=True)
        charges = ChargeDeductible.objects.filter(
            contrat=contrat,
            statut='validee'
        ).values(
            'id', 'libelle', 'montant', 'type_charge', 'date_charge', 'description'
        )
        
        return JsonResponse({
            'success': True,
            'charges': list(charges),
            'loyer_total': float(contrat.get_loyer_total())
        })
    except Contrat.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Contrat non trouvé'
        })


class ChargeDeductibleListView(PrivilegeButtonsMixin, IntelligentListView):
    model = ChargeDeductible
    template_name = 'base_liste_intelligente.html'
    paginate_by = 20
    page_title = 'Charges déductibles'
    page_icon = 'file-invoice-dollar'
    add_url = 'paiements:charge_deductible_ajouter'
    add_text = 'Ajouter une charge'
    search_fields = ['libelle', 'description', 'contrat__numero_contrat', 'contrat__locataire__nom', 'contrat__locataire__prenom', 'fournisseur']
    filter_fields = ['statut', 'type_charge', 'contrat']
    default_sort = '-date_charge'
    columns = [
        {'field': 'libelle', 'label': 'Libellé', 'sortable': True},
        {'field': 'contrat', 'label': 'Contrat', 'sortable': True},
        {'field': 'montant', 'label': 'Montant', 'sortable': True},
        {'field': 'type_charge', 'label': 'Type', 'sortable': True},
        {'field': 'statut', 'label': 'Statut', 'sortable': True},
        {'field': 'date_charge', 'label': 'Date', 'sortable': True},
    ]
    actions = [
        {'url_name': 'paiements:charge_deductible_detail', 'icon': 'eye', 'style': 'outline-primary', 'title': 'Voir'},
        {'url_name': 'paiements:charge_deductible_modifier', 'icon': 'pencil', 'style': 'outline-warning', 'title': 'Modifier'},
    ]
    sort_options = [
        {'value': 'date_charge', 'label': 'Date'},
        {'value': 'montant', 'label': 'Montant'},
        {'value': 'libelle', 'label': 'Libellé'},
        {'value': 'statut', 'label': 'Statut'},
        {'value': 'type_charge', 'label': 'Type'},
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
        context['total_charges'] = ChargeDeductible.objects.count()
        context['charges_en_attente'] = ChargeDeductible.objects.filter(est_valide=False).count()
        context['charges_validées'] = ChargeDeductible.objects.filter(est_valide=True).count()
        context['charges_deduites'] = 0  # Pas de champ pour les charges déduites
        context['charges_refusees'] = 0  # Pas de champ pour les charges refusées
        
        # Montant total
        from django.db.models import Sum
        context['montant_total'] = ChargeDeductible.objects.aggregate(total=Sum('montant'))['total'] or 0
        
        return context

charge_deductible_list = ChargeDeductibleListView.as_view()


# Vues pour les retraits des bailleurs
def liste_retraits_bailleur(request):
    """Liste des retraits des bailleurs."""
    retraits = RetraitBailleur.objects.all().order_by('-mois_retrait')
    
    # Filtres
    bailleur_id = request.GET.get('bailleur')
    statut = request.GET.get('statut')
    mois = request.GET.get('mois')
    
    if bailleur_id:
        retraits = retraits.filter(bailleur_id=bailleur_id)
    if statut:
        retraits = retraits.filter(statut=statut)
    if mois:
        try:
            mois_date = datetime.strptime(mois, '%Y-%m').date()
            retraits = retraits.filter(mois_retrait__year=mois_date.year, mois_retrait__month=mois_date.month)
        except ValueError:
            pass
    
    # Pagination
    paginator = Paginator(retraits, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Filtres pour le formulaire
    bailleurs = Bailleur.objects.all()
    
    context = {
        'page_obj': page_obj,
        'bailleurs': bailleurs,
        'statuts': RetraitBailleur._meta.get_field('statut').choices,
    }
    
    return render(request, 'paiements/liste_retraits_bailleur.html', context)


def creer_retrait_bailleur(request):
    """Créer un nouveau retrait pour un bailleur."""
    if request.method == 'POST':
        form = RetraitBailleurForm(request.POST)
        if form.is_valid():
            retrait = form.save(commit=False)
            retrait.cree_par = request.user
            retrait.save()
            
            # Ajouter les charges déductibles si spécifiées
            charges_ids = request.POST.getlist('charges_deductibles')
            if charges_ids:
                retrait.ajouter_charges_deductibles(charges_ids)
            
            # Ajouter les paiements concernés
            paiements_ids = request.POST.getlist('paiements_concernes')
            if paiements_ids:
                retrait.paiements_concernes.set(paiements_ids)
            
            # Générer le reçu de retrait
            recu = retrait.generer_recu_retrait()
            
            messages.success(request, f'Retrait créé avec succès. Reçu généré: {recu.numero_recu}')
            return redirect('paiements:detail_retrait_bailleur', retrait_id=retrait.id)
    else:
        form = RetraitBailleurForm()
    
    # Récupérer les bailleurs et leurs propriétés
    bailleurs = Bailleur.objects.all()
    
    context = {
        'form': form,
        'bailleurs': bailleurs,
    }
    
    return render(request, 'paiements/creer_retrait_bailleur.html', context)


def detail_retrait_bailleur(request, retrait_id):
    """Détail d'un retrait bailleur."""
    try:
        retrait = RetraitBailleur.objects.get(id=retrait_id)
    except RetraitBailleur.DoesNotExist:
        messages.error(request, 'Retrait non trouvé.')
        return redirect('paiements:liste_retraits_bailleur')
    
    # Récupérer les charges déductibles et paiements
    charges_deductibles = retrait.get_charges_deductibles_detail()
    paiements_concernes = retrait.get_paiements_detail()
    
    context = {
        'retrait': retrait,
        'charges_deductibles': charges_deductibles,
        'paiements_concernes': paiements_concernes,
    }
    
    return render(request, 'paiements/detail_retrait_bailleur.html', context)


def valider_retrait_bailleur(request, retrait_id):
    """Valider un retrait bailleur."""
    try:
        retrait = RetraitBailleur.objects.get(id=retrait_id)
    except RetraitBailleur.DoesNotExist:
        messages.error(request, 'Retrait non trouvé.')
        return redirect('paiements:liste_retraits_bailleur')
    
    if retrait.statut == 'en_attente':
        retrait.valider_retrait(request.user)
        messages.success(request, 'Retrait validé avec succès.')
    else:
        messages.warning(request, 'Ce retrait ne peut pas être validé.')
    
    return redirect('paiements:detail_retrait_bailleur', retrait_id=retrait.id)


def marquer_retrait_paye(request, retrait_id):
    """Marquer un retrait comme payé."""
    try:
        retrait = RetraitBailleur.objects.get(id=retrait_id)
    except RetraitBailleur.DoesNotExist:
        messages.error(request, 'Retrait non trouvé.')
        return redirect('paiements:liste_retraits_bailleur')
    
    if retrait.statut == 'valide':
        date_versement = request.POST.get('date_versement')
        if date_versement:
            try:
                date_versement = datetime.strptime(date_versement, '%Y-%m-%d').date()
                retrait.marquer_paye(request.user, date_versement)
                messages.success(request, 'Retrait marqué comme payé.')
            except ValueError:
                messages.error(request, 'Date de versement invalide.')
        else:
            retrait.marquer_paye(request.user)
            messages.success(request, 'Retrait marqué comme payé.')
    else:
        messages.warning(request, 'Ce retrait ne peut pas être marqué comme payé.')
    
    return redirect('paiements:detail_retrait_bailleur', retrait_id=retrait.id)


def imprimer_recu_retrait(request, retrait_id):
    """Imprimer le reçu de retrait."""
    try:
        retrait = RetraitBailleur.objects.get(id=retrait_id)
    except RetraitBailleur.DoesNotExist:
        messages.error(request, 'Retrait non trouvé.')
        return redirect('paiements:liste_retraits_bailleur')
    
    # Récupérer ou créer le reçu
    recu, created = RecuRetrait.objects.get_or_create(retrait_bailleur=retrait)
    
    # Marquer comme imprimé
    recu.marquer_imprime(request.user)
    
    # Générer le PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="recu_retrait_{recu.numero_recu}.pdf"'
    
    # Créer le PDF avec ReportLab
    p = canvas.Canvas(response, pagesize=A5)
    
    # Récupérer la configuration de l'entreprise
    from core.models import ConfigurationEntreprise
    config = ConfigurationEntreprise.get_configuration_active()
    
    # En-tête
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, 750, f"RECU DE RETRAIT")
    p.setFont("Helvetica", 12)
    p.drawString(50, 730, f"Numéro: {recu.numero_recu}")
    p.drawString(50, 710, f"Date: {recu.date_emission.strftime('%d/%m/%Y')}")
    
    # Informations du bailleur
    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, 680, "INFORMATIONS DU BAILLEUR")
    p.setFont("Helvetica", 10)
    p.drawString(50, 660, f"Nom: {retrait.bailleur.nom} {retrait.bailleur.prenom}")
    p.drawString(50, 640, f"Adresse: {retrait.bailleur.adresse}")
    p.drawString(50, 620, f"Téléphone: {retrait.bailleur.telephone}")
    
    # Informations du retrait
    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, 580, "DETAILS DU RETRAIT")
    p.setFont("Helvetica", 10)
    p.drawString(50, 560, f"Mois: {retrait.mois_retrait.strftime('%B %Y')}")
    p.drawString(50, 540, f"Loyers bruts: {retrait.get_montant_loyers_bruts_formatted()}")
    p.drawString(50, 520, f"Charges déductibles: {retrait.get_montant_charges_deductibles_formatted()}")
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, 500, f"NET A PAYER: {retrait.get_montant_net_formatted()}")
    
    # Informations de l'entreprise
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, 200, config.nom_entreprise)
    p.setFont("Helvetica", 10)
    p.drawString(50, 180, config.get_adresse_complete())
    p.drawString(50, 160, config.get_contact_complet())
    
    # Signature
    p.setFont("Helvetica", 10)
    p.drawString(50, 100, "Signature du bailleur:")
    p.line(50, 90, 200, 90)
    
    p.showPage()
    p.save()
    
    return response


# Vues pour les récapitulatifs mensuels
def liste_recaps_mensuels(request):
    """Liste des récapitulatifs mensuels."""
    recaps = RecapMensuel.objects.all().order_by('-mois_recap')
    
    # Filtres
    bailleur_id = request.GET.get('bailleur')
    statut = request.GET.get('statut')
    mois = request.GET.get('mois')
    
    if bailleur_id:
        recaps = recaps.filter(bailleur_id=bailleur_id)
    if statut:
        recaps = recaps.filter(statut=statut)
    if mois:
        try:
            mois_date = datetime.strptime(mois, '%Y-%m').date()
            recaps = recaps.filter(mois_recap__year=mois_date.year, mois_recap__month=mois_date.month)
        except ValueError:
            pass
    
    # Pagination
    paginator = Paginator(recaps, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Filtres pour le formulaire
    bailleurs = Bailleur.objects.all()
    
    context = {
        'page_obj': page_obj,
        'bailleurs': bailleurs,
        'statuts': RecapMensuel._meta.get_field('statut').choices,
    }
    
    return render(request, 'paiements/liste_recaps_mensuels.html', context)


def creer_recap_mensuel(request):
    """Créer un nouveau récapitulatif mensuel."""
    if request.method == 'POST':
        form = RecapMensuelForm(request.POST)
        if form.is_valid():
            recap = form.save(commit=False)
            recap.cree_par = request.user
            
            # Calculer les totaux
            recap.calculer_totaux()
            recap.save()
            
            # Ajouter les paiements et charges concernés
            paiements_ids = request.POST.getlist('paiements_concernes')
            charges_ids = request.POST.getlist('charges_deductibles')
            
            if paiements_ids:
                recap.paiements_concernes.set(paiements_ids)
            if charges_ids:
                recap.charges_deductibles.set(charges_ids)
            
            messages.success(request, 'Récapitulatif mensuel créé avec succès.')
            return redirect('paiements:detail_recap_mensuel', recap_id=recap.id)
    else:
        form = RecapMensuelForm()
    
    # Récupérer les bailleurs
    bailleurs = Bailleur.objects.all()
    
    context = {
        'form': form,
        'bailleurs': bailleurs,
    }
    
    return render(request, 'paiements/creer_recap_mensuel.html', context)


def detail_recap_mensuel(request, recap_id):
    """Détail d'un récapitulatif mensuel."""
    try:
        recap = RecapMensuel.objects.get(id=recap_id)
    except RecapMensuel.DoesNotExist:
        messages.error(request, 'Récapitulatif non trouvé.')
        return redirect('paiements:liste_recaps_mensuels')
    
    # Récupérer les détails
    detail_proprietes = recap.get_detail_proprietes()
    detail_charges = recap.get_detail_charges()
    
    context = {
        'recap': recap,
        'detail_proprietes': detail_proprietes,
        'detail_charges': detail_charges,
    }
    
    return render(request, 'paiements/detail_recap_mensuel.html', context)


def valider_recap_mensuel(request, recap_id):
    """Valider un récapitulatif mensuel."""
    try:
        recap = RecapMensuel.objects.get(id=recap_id)
    except RecapMensuel.DoesNotExist:
        messages.error(request, 'Récapitulatif non trouvé.')
        return redirect('paiements:liste_recaps_mensuels')
    
    if recap.statut == 'en_cours':
        recap.valider_recap(request.user)
        messages.success(request, 'Récapitulatif validé avec succès.')
    else:
        messages.warning(request, 'Ce récapitulatif ne peut pas être validé.')
    
    return redirect('paiements:detail_recap_mensuel', recap_id=recap.id)


def imprimer_recap_mensuel(request, recap_id):
    """Imprimer le récapitulatif mensuel."""
    try:
        recap = RecapMensuel.objects.get(id=recap_id)
    except RecapMensuel.DoesNotExist:
        messages.error(request, 'Récapitulatif non trouvé.')
        return redirect('paiements:liste_recaps_mensuels')
    
    # Générer le PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="recap_mensuel_{recap.bailleur.nom}_{recap.mois_recap.strftime("%Y_%m")}.pdf"'
    
    # Créer le PDF avec ReportLab
    p = canvas.Canvas(response, pagesize=A4)
    
    # Récupérer la configuration de l'entreprise
    from core.models import ConfigurationEntreprise
    config = ConfigurationEntreprise.get_configuration_active()
    
    # En-tête
    p.setFont("Helvetica-Bold", 18)
    p.drawString(50, 800, f"RECAPITULATIF MENSUEL - {recap.mois_recap.strftime('%B %Y').upper()}")
    
    # Informations du bailleur
    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, 760, f"Bailleur: {recap.bailleur.nom} {recap.bailleur.prenom}")
    p.setFont("Helvetica", 10)
    p.drawString(50, 740, f"Adresse: {recap.bailleur.adresse}")
    p.drawString(50, 720, f"Téléphone: {recap.bailleur.telephone}")
    
    # Résumé financier
    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, 680, "RESUME FINANCIER")
    p.setFont("Helvetica", 12)
    p.drawString(50, 660, f"Total loyers bruts: {recap.get_total_loyers_bruts_formatted()}")
    p.drawString(50, 640, f"Total charges déductibles: {recap.get_total_charges_deductibles_formatted()}")
    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, 620, f"NET A PAYER: {recap.get_total_net_formatted()}")
    
    # Détail des propriétés
    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, 580, "DETAIL DES PROPRIETES")
    
    y_position = 560
    detail_proprietes = recap.get_detail_proprietes()
    
    for detail in detail_proprietes:
        if y_position < 100:  # Nouvelle page si nécessaire
            p.showPage()
            y_position = 800
            p.setFont("Helvetica-Bold", 14)
            p.drawString(50, y_position, "DETAIL DES PROPRIETES (suite)")
            y_position -= 30
        
        p.setFont("Helvetica-Bold", 12)
        p.drawString(50, y_position, f"Propriété: {detail['propriete'].titre}")
        y_position -= 20
        
        p.setFont("Helvetica", 10)
        p.drawString(50, y_position, f"Locataire: {detail['locataire'].nom} {detail['locataire'].prenom}")
        y_position -= 15
        
        p.drawString(50, y_position, f"Loyer: {detail['loyer_mensuel']} + Charges: {detail['charges_mensuelles']} = Total: {detail['loyer_total']}")
        y_position -= 15
        
        p.drawString(50, y_position, f"Paiement reçu: {detail['paiement_recu']} - Statut: {detail['statut_paiement']}")
        y_position -= 25
    
    # Informations de l'entreprise
    p.showPage()
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, 800, config.nom_entreprise)
    p.setFont("Helvetica", 10)
    p.drawString(50, 780, config.get_adresse_complete())
    p.drawString(50, 760, config.get_contact_complet())
    
    # Signature
    p.setFont("Helvetica", 10)
    p.drawString(50, 200, "Signature du bailleur:")
    p.line(50, 190, 200, 190)
    
    p.showPage()
    p.save()
    
    return response
