from django.template.loader import render_to_string
from django.http import HttpResponse
from io import BytesIO
from datetime import datetime
import base64
import os

# Dictionnaire des mois en français
MOIS_FRANCAIS = {
    1: 'Janvier', 2: 'Février', 3: 'Mars', 4: 'Avril',
    5: 'Mai', 6: 'Juin', 7: 'Juillet', 8: 'Août',
    9: 'Septembre', 10: 'Octobre', 11: 'Novembre', 12: 'Décembre'
}

def formater_date_francais(date_obj):
    """
    Formate une date en français (ex: "Octobre 2025")
    """
    if not date_obj:
        return ""
    return f"{MOIS_FRANCAIS[date_obj.month]} {date_obj.year}"


def add_header_footer(canvas_obj, doc):
    """Ajoute l'en-tête statique et le pied de page dynamique"""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.utils import ImageReader
    from reportlab.lib.units import cm
    import os
    
    # Dimensions de la page
    page_width, page_height = A4
    
    # === EN-TÊTE STATIQUE ===
    try:
        # Chemin vers l'image d'en-tête
        entete_path = os.path.join('static', 'images', 'enteteEnImage.png')
        
        if os.path.exists(entete_path):
            # Utiliser l'image d'en-tête personnalisée
            img = ImageReader(entete_path)
            img_width, img_height = img.getSize()
            
            # Calculer les dimensions optimales pour l'en-tête
            max_width = page_width - 2*cm  # Largeur maximale de la page
            max_height = 4*cm  # Hauteur maximale pour l'en-tête
            
            # Redimensionner proportionnellement
            aspect_ratio = img_width / img_height
            if aspect_ratio > (max_width / max_height):
                entete_width = max_width
                entete_height = max_width / aspect_ratio
            else:
                entete_height = max_height
                entete_width = max_height * aspect_ratio
            
            # Centrer l'en-tête
            entete_x = (page_width - entete_width) / 2
            entete_y = page_height - entete_height - 0.5*cm
            
            canvas_obj.drawImage(entete_path, entete_x, entete_y, entete_width, entete_height)
        else:
            # Fallback si l'image n'existe pas
            canvas_obj.setFillColor(colors.lightblue)
            canvas_obj.rect(0, page_height - 3*cm, page_width, 3*cm, fill=1, stroke=0)
            
            canvas_obj.setFillColor(colors.darkblue)
            canvas_obj.setFont("Helvetica-Bold", 16)
            canvas_obj.drawString(2*cm, page_height - 2.2*cm, "KBIS IMMOBILIER")
            
    except Exception as e:
        print(f"Erreur lors de l'ajout de l'en-tête: {e}")
    
    # === PIED DE PAGE DYNAMIQUE ===
    # Fond du pied de page
    canvas_obj.setFillColor(colors.lightgrey)
    canvas_obj.rect(0, 0, page_width, 1.5*cm, fill=1, stroke=0)
    
    # Informations de l'entreprise
    canvas_obj.setFillColor(colors.black)
    canvas_obj.setFont("Helvetica", 8)
    
    # Informations de contact
    contact_info = "KBIS IMMOBILIER - pissy 10050 ouagadougou Burkina Faso, Quartier Centre-Ville, BP 440 ouagadougou, Burkina Faso"
    canvas_obj.drawString(1*cm, 0.8*cm, contact_info)
    
    # Téléphone et email
    tel_email = "Tél: +226 70 20 54 91 | Email: kbissarl2022@gmail.com"
    canvas_obj.drawString(1*cm, 0.4*cm, tel_email)
    
    # Informations légales
    legal_info = "RCCM: CI-ABJ-XXXX-X-XXXXX | IFU: XXXXXXXXXX"
    canvas_obj.drawString(1*cm, 0.1*cm, legal_info)
    
    # Numéro de page
    canvas_obj.setFont("Helvetica-Bold", 8)
    page_num = f"Page {doc.page}"
    canvas_obj.drawRightString(page_width - 1*cm, 0.4*cm, page_num)


def generate_historique_pdf(rapport_data):
    """
    Génère un PDF détaillé de l'historique des paiements et avances
    avec en-tête statique et pied de page dynamique
    """
    try:
        # Essayer d'utiliser reportlab si disponible
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch, cm
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
        from reportlab.lib.utils import ImageReader
        import os
        
        # Créer le buffer PDF avec marges ajustées pour l'en-tête
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer, 
            pagesize=A4, 
            rightMargin=2*cm, 
            leftMargin=2*cm, 
            topMargin=4*cm,  # Plus d'espace pour l'en-tête
            bottomMargin=2*cm
        )
        
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
        story.append(Paragraph(f"<b>Période:</b> {formater_date_francais(periode['debut'])} - {formater_date_francais(periode['fin'])}", normal_style))
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
        
        # Consommation progressive des avances
        story.append(Paragraph("CONSOMMATION PROGRESSIVE DES AVANCES", heading_style))
        story.append(Spacer(1, 12))
        
        # Récupérer les consommations pour chaque avance
        for avance in rapport_data['avances']:
            from paiements.models_avance import ConsommationAvance
            consommations = ConsommationAvance.objects.filter(avance=avance).order_by('mois_consomme')
            
            if consommations.exists():
                # Tableau de consommation pour cette avance
                story.append(Paragraph(f"<b>Avance du {avance.date_avance.strftime('%d/%m/%Y')} - {avance.montant_avance} F CFA</b>", normal_style))
                story.append(Spacer(1, 8))
                
                # En-tête du tableau de consommation
                consommation_data = [['Mois', 'Montant Consommé', 'Montant Restant', 'Statut']]
                
                for consommation in consommations:
                    statut = "Consommé" if consommation.montant_consomme > 0 else "En attente"
                    consommation_data.append([
                        formater_date_francais(consommation.mois_consomme),
                        f"{consommation.montant_consomme} F CFA",
                        f"{consommation.montant_restant_apres} F CFA",
                        statut
                    ])
                
                # Créer le tableau de consommation
                consommation_table = Table(consommation_data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 1*inch])
                consommation_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.lightblue),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                
                story.append(consommation_table)
                story.append(Spacer(1, 15))
            else:
                # Aucune consommation enregistrée
                story.append(Paragraph(f"<b>Avance du {avance.date_avance.strftime('%d/%m/%Y')} - {avance.montant_avance} F CFA</b>", normal_style))
                story.append(Paragraph("<i>Aucune consommation enregistrée pour le moment</i>", normal_style))
                story.append(Spacer(1, 15))
        
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
                    formater_date_francais(hist.mois_paiement),
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
        
        # Note de génération (le pied de page est géré par add_header_footer)
        story.append(Spacer(1, 20))
        story.append(Paragraph(f"<i>Rapport généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}</i>", normal_style))
        
        # Construire le PDF avec en-tête et pied de page
        doc.build(story, onFirstPage=add_header_footer, onLaterPages=add_header_footer)
        
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
