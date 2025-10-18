"""
Fonctions de service pour la génération de PDF des paiements.
Ces fonctions sont importées par views.py.
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from io import BytesIO


def generate_recap_pdf(recap, method='reportlab'):
    """
    Génère un PDF de récapitulatif mensuel.
    
    Args:
        recap: Instance de RecapMensuel
        method: Méthode de génération ('reportlab' ou 'weasyprint')
    
    Returns:
        HttpResponse avec le PDF généré
    """
    try:
        if method == 'reportlab':
            # Utiliser ReportLab pour la génération
            from django.http import HttpResponse
            from io import BytesIO
            
            # Créer le PDF avec ReportLab
            buffer = BytesIO()
            doc = SimpleDocTemplate(
                buffer,
                pagesize=A4,
                rightMargin=2*cm,
                leftMargin=2*cm,
                topMargin=2*cm,
                bottomMargin=2*cm
            )
            
            # Styles
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=16,
                spaceAfter=30,
                alignment=1,  # Centré
                textColor=colors.darkblue
            )
            
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
            story.append(Paragraph(f"<b>Bailleur:</b> {recap.bailleur.get_nom_complet()}", styles['Heading2']))
            story.append(Paragraph(f"<b>Mois:</b> {recap.mois_recap.strftime('%B %Y')}", styles['Normal']))
            
            # Pied de page
            ajouter_pied_entreprise_reportlab(story, config)
            
            # Générer le PDF
            doc.build(story)
            buffer.seek(0)
            
            # Créer la réponse HTTP
            response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="recap_{recap.bailleur.get_nom_complet()}_{recap.mois_recap.strftime("%Y_%m")}.pdf"'
            
            return response
            
        else:
            # Fallback vers WeasyPrint si disponible
            from django.http import HttpResponse
            from django.template.loader import render_to_string
            
            context = {
                'recap': recap,
                'config_entreprise': ConfigurationEntreprise.get_configuration_active()
            }
            
            html_content = render_to_string('paiements/recap_pdf.html', context)
            
            from weasyprint import HTML
            pdf = HTML(string=html_content).write_pdf()
            
            response = HttpResponse(pdf, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="recap_{recap.bailleur.get_nom_complet()}_{recap.mois_recap.strftime("%Y_%m")}.pdf"'
            
            return response
            
    except Exception as e:
        from django.http import HttpResponse
        return HttpResponse(f"Erreur lors de la génération du PDF: {str(e)}", content_type='text/plain')


def generate_recap_pdf_batch(mois_recap, method='reportlab'):
    """
    Génère des PDF de récapitulatifs mensuels en lot.
    
    Args:
        mois_recap: Mois pour lequel générer les récapitulatifs
        method: Méthode de génération ('reportlab' ou 'weasyprint')
    
    Returns:
        HttpResponse avec le PDF généré
    """
    try:
        from .models import RecapMensuel
        from django.http import HttpResponse
        from io import BytesIO
        
        # Récupérer tous les récapitulatifs du mois
        recaps = RecapMensuel.objects.filter(mois_recap=mois_recap, is_deleted=False)
        
        if not recaps.exists():
            return HttpResponse("Aucun récapitulatif trouvé pour ce mois.", content_type='text/plain')
        
        # Créer un PDF combiné
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            alignment=1,  # Centré
            textColor=colors.darkblue
        )
        
        # Contenu du PDF
        story = []
        
        # Récupérer la configuration de l'entreprise
        from core.models import ConfigurationEntreprise
        from core.utils import ajouter_en_tete_entreprise_reportlab, ajouter_pied_entreprise_reportlab
        config = ConfigurationEntreprise.get_configuration_active()
        
        # En-tête de l'entreprise
        ajouter_en_tete_entreprise_reportlab(story, config)
        
        # Titre principal
        story.append(Paragraph("RÉCAPITULATIFS MENSUELS - LOT", title_style))
        story.append(Paragraph(f"<b>Mois:</b> {mois_recap.strftime('%B %Y')}", styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Ajouter chaque récapitulatif
        for recap in recaps:
            story.append(Paragraph(f"<b>Bailleur:</b> {recap.bailleur.get_nom_complet()}", styles['Heading2']))
            story.append(Spacer(1, 10))
        
        # Pied de page
        ajouter_pied_entreprise_reportlab(story, config)
        
        # Générer le PDF
        doc.build(story)
        buffer.seek(0)
        
        # Créer la réponse HTTP
        response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="recaps_lot_{mois_recap.strftime("%Y_%m")}.pdf"'
        
        return response
        
    except Exception as e:
        from django.http import HttpResponse
        return HttpResponse(f"Erreur lors de la génération du PDF en lot: {str(e)}", content_type='text/plain')
