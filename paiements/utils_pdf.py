from django.template.loader import render_to_string
from django.http import HttpResponse
from io import BytesIO
from datetime import datetime
import base64
import os


def generate_historique_pdf(rapport_data):
    """
    Génère un PDF détaillé de l'historique des paiements et avances
    """
    try:
        # Essayer d'utiliser reportlab si disponible
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
        
        # Créer le buffer PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
        
        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=12,
            spaceAfter=12,
            textColor=colors.darkblue
        )
        
        normal_style = styles['Normal']
        
        # Contenu du PDF
        story = []
        
        # Titre
        story.append(Paragraph("RAPPORT DÉTAILLÉ DES AVANCES DE LOYER", title_style))
        story.append(Spacer(1, 12))
        
        # Informations du contrat
        contrat = rapport_data['contrat']
        story.append(Paragraph(f"<b>Contrat:</b> {contrat.numero_contrat}", normal_style))
        story.append(Paragraph(f"<b>Locataire:</b> {contrat.locataire.get_nom_complet()}", normal_style))
        story.append(Paragraph(f"<b>Propriété:</b> {contrat.propriete.adresse}", normal_style))
        story.append(Paragraph(f"<b>Loyer mensuel:</b> {contrat.loyer_mensuel} F CFA", normal_style))
        story.append(Spacer(1, 12))
        
        # Période
        periode = rapport_data['periode']
        story.append(Paragraph(f"<b>Période:</b> {periode['debut'].strftime('%B %Y')} - {periode['fin'].strftime('%B %Y')}", normal_style))
        story.append(Spacer(1, 20))
        
        # Statistiques
        stats = rapport_data['statistiques']
        story.append(Paragraph("STATISTIQUES GÉNÉRALES", heading_style))
        
        stats_data = [
            ['Total des avances versées', f"{stats['total_avances_versees']} F CFA"],
            ['Total des avances consommées', f"{stats['total_avances_consommees']} F CFA"],
            ['Total des avances restantes', f"{stats['total_avances_restantes']} F CFA"],
            ['Nombre de mois couverts', f"{stats['nombre_mois_couverts']} mois"],
        ]
        
        stats_table = Table(stats_data, colWidths=[3*inch, 2*inch])
        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(stats_table)
        story.append(Spacer(1, 20))
        
        # Détail des avances
        if rapport_data['avances']:
            story.append(Paragraph("DÉTAIL DES AVANCES", heading_style))
            
            avances_data = [['Date', 'Montant', 'Mois couverts', 'Restant', 'Statut']]
            
            for avance in rapport_data['avances']:
                avances_data.append([
                    avance.date_avance.strftime('%d/%m/%Y'),
                    f"{avance.montant_avance} F CFA",
                    f"{avance.nombre_mois_couverts} mois",
                    f"{avance.montant_restant} F CFA",
                    avance.get_statut_display()
                ])
            
            avances_table = Table(avances_data, colWidths=[1*inch, 1.5*inch, 1*inch, 1.5*inch, 1*inch])
            avances_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(avances_table)
            story.append(Spacer(1, 20))
        
        # Historique des paiements
        if rapport_data['historique']:
            story.append(Paragraph("HISTORIQUE DES PAIEMENTS", heading_style))
            
            historique_data = [['Mois', 'Montant dû', 'Montant payé', 'Avance utilisée', 'Restant dû', 'Statut']]
            
            for hist in rapport_data['historique']:
                statut = "Réglé" if hist.mois_regle else "En attente"
                historique_data.append([
                    hist.mois_paiement.strftime('%B %Y'),
                    f"{hist.montant_du} F CFA",
                    f"{hist.montant_paye} F CFA",
                    f"{hist.montant_avance_utilisee} F CFA",
                    f"{hist.montant_restant_du} F CFA",
                    statut
                ])
            
            historique_table = Table(historique_data, colWidths=[1*inch, 1.2*inch, 1.2*inch, 1.2*inch, 1.2*inch, 1*inch])
            historique_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(historique_table)
            story.append(Spacer(1, 20))
        
        # Pied de page
        story.append(Spacer(1, 20))
        story.append(Paragraph(f"Rapport généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}", normal_style))
        story.append(Paragraph("KBIS IMMOBILIER - Système de gestion des avances", normal_style))
        
        # Construire le PDF
        doc.build(story)
        
        # Récupérer le contenu
        pdf_content = buffer.getvalue()
        buffer.close()
        
        return pdf_content
        
    except ImportError:
        # Fallback si reportlab n'est pas disponible
        return generate_historique_html(rapport_data).encode('utf-8')


def generate_historique_html(rapport_data):
    """
    Génère un HTML de l'historique des paiements (fallback)
    """
    try:
        # Charger l'image en Base64
        image_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'images', 'enteteEnImage.png')
        entete_base64 = ""
        try:
            with open(image_path, "rb") as image_file:
                entete_base64 = base64.b64encode(image_file.read()).decode('utf-8')
        except:
            entete_base64 = ""
        
        # Rendre le template HTML
        html_content = render_to_string(
            'paiements/avances/rapport_historique_pdf.html',
            {
                'rapport': rapport_data,
                'date_generation': datetime.now(),
                'entete_base64': entete_base64,
            }
        )
        
        return html_content
        
    except Exception as e:
        # HTML simple en cas d'erreur
        return f"""
        <html>
        <head><title>Rapport Historique Avances</title></head>
        <body>
            <h1>Rapport d'historique des avances</h1>
            <p>Contrat: {rapport_data['contrat'].numero_contrat}</p>
            <p>Locataire: {rapport_data['contrat'].locataire.get_nom_complet()}</p>
            <p>Erreur lors de la génération: {str(e)}</p>
        </body>
        </html>
        """
