#!/usr/bin/env python
"""
Services pour la génération de PDF des récapitulatifs mensuels
"""

import os
from datetime import datetime
from decimal import Decimal
from django.conf import settings
from django.template.loader import render_to_string
from django.http import HttpResponse
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.platypus.flowables import HRFlowable
from reportlab.pdfgen import canvas
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

class PDFGeneratorService:
    """Service pour la génération de PDF des récapitulatifs mensuels."""
    
    def __init__(self, recap_mensuel):
        self.recap = recap_mensuel
        self.styles = self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Configure les styles personnalisés pour le PDF."""
        styles = getSampleStyleSheet()
        
        # Style pour le titre principal
        styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        ))
        
        # Style pour les sous-titres
        styles.add(ParagraphStyle(
            name='CustomSubtitle',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=20,
            alignment=TA_LEFT,
            textColor=colors.darkblue
        ))
        
        # Style pour le texte normal
        styles.add(ParagraphStyle(
            name='CustomNormal',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=12,
            alignment=TA_LEFT
        ))
        
        # Style pour les informations importantes
        styles.add(ParagraphStyle(
            name='CustomImportant',
            parent=styles['Normal'],
            fontSize=11,
            spaceAfter=12,
            alignment=TA_LEFT,
            textColor=colors.darkred,
            fontName='Helvetica-Bold'
        ))
        
        return styles
    
    def _get_entreprise_config(self):
        """Récupère la configuration de l'entreprise."""
        try:
            from core.models import ConfigurationEntreprise
            return ConfigurationEntreprise.objects.first()
        except:
            return None
    
    def generate_pdf_reportlab(self):
        """Génère un PDF avec ReportLab (rapide et fiable)."""
        try:
            # Créer le document PDF
            response = HttpResponse(content_type='application/pdf')
            filename = f"recap_mensuel_{self.recap.bailleur.get_nom_complet()}_{self.recap.mois_recap.strftime('%B_%Y')}.pdf"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            # Créer le document ReportLab
            doc = SimpleDocTemplate(response, pagesize=A4)
            story = []
            
            # En-tête avec logo et informations de l'entreprise
            story.extend(self._create_header())
            
            # Titre principal
            story.append(Paragraph(
                f"RÉCAPITULATIF MENSUEL - {self.recap.mois_recap.strftime('%B %Y').upper()}",
                self.styles['CustomTitle']
            ))
            
            # Informations du bailleur
            story.extend(self._create_bailleur_section())
            
            # Résumé financier
            story.extend(self._create_financial_summary())
            
            # Détails des propriétés
            story.extend(self._create_property_details())
            
            # Vérification des garanties financières
            story.extend(self._create_guarantee_verification())
            
            # Pied de page
            story.extend(self._create_footer())
            
            # Construire le PDF
            doc.build(story)
            
            return response
            
        except Exception as e:
            raise Exception(f"Erreur lors de la génération PDF avec ReportLab: {str(e)}")
    
    def _create_header(self):
        """Crée l'en-tête du document."""
        story = []
        
        # Logo et nom de l'entreprise
        entreprise_config = self._get_entreprise_config()
        if entreprise_config:
            story.append(Paragraph(
                entreprise_config.nom_entreprise or "GESTION IMMOBILIÈRE",
                self.styles['CustomSubtitle']
            ))
            if entreprise_config.adresse:
                story.append(Paragraph(
                    entreprise_config.adresse,
                    self.styles['CustomNormal']
                ))
        
        story.append(Spacer(1, 20))
        
        # Informations du document
        story.append(Paragraph(
            f"<b>Date de génération:</b> {datetime.now().strftime('%d/%m/%Y à %H:%M')}",
            self.styles['CustomNormal']
        ))
        story.append(Paragraph(
            f"<b>Période:</b> {self.recap.mois_recap.strftime('%B %Y')}",
            self.styles['CustomNormal']
        ))
        
        story.append(HRFlowable(width="100%", thickness=1, color=colors.grey))
        story.append(Spacer(1, 20))
        
        return story
    
    def _create_bailleur_section(self):
        """Crée la section d'informations du bailleur."""
        story = []
        
        story.append(Paragraph("INFORMATIONS DU BAILLEUR", self.styles['CustomSubtitle']))
        
        bailleur = self.recap.bailleur
        story.append(Paragraph(
            f"<b>Nom:</b> {bailleur.get_nom_complet()}",
            self.styles['CustomNormal']
        ))
        
        if bailleur.telephone:
            story.append(Paragraph(
                f"<b>Téléphone:</b> {bailleur.telephone}",
                self.styles['CustomNormal']
            ))
        
        if bailleur.email:
            story.append(Paragraph(
                f"<b>Email:</b> {bailleur.email}",
                self.styles['CustomNormal']
            ))
        
        story.append(Spacer(1, 20))
        return story
    
    def _create_financial_summary(self):
        """Crée le résumé financier."""
        story = []
        
        story.append(Paragraph("RÉSUMÉ FINANCIER", self.styles['CustomSubtitle']))
        
        # Tableau des totaux
        data = [
            ['Description', 'Montant (F CFA)'],
            ['Total des loyers bruts', f"{self.recap.total_loyers_bruts:.2f}"],
            ['Total des charges déductibles', f"{self.recap.total_charges_deductibles:.2f}"],
            ['', ''],
            ['<b>TOTAL NET À PAYER</b>', f"<b>{self.recap.total_net_a_payer:.2f}</b>"]
        ]
        
        table = Table(data, colWidths=[300, 100])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -2), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        story.append(table)
        story.append(Spacer(1, 20))
        return story
    
    def _create_property_details(self):
        """Crée les détails des propriétés."""
        story = []
        
        story.append(Paragraph("DÉTAILS DES PROPRIÉTÉS", self.styles['CustomSubtitle']))
        
        # Récupérer les propriétés actives du bailleur
        proprietes_actives = self.recap.bailleur.proprietes.filter(
            contrats__est_actif=True,
            contrats__est_resilie=False
        ).distinct()
        
        if proprietes_actives.exists():
            for propriete in proprietes_actives:
                contrat_actif = propriete.contrats.filter(est_actif=True).first()
                if contrat_actif:
                    story.append(Paragraph(
                        f"<b>Propriété:</b> {propriete.adresse}",
                        self.styles['CustomNormal']
                    ))
                    story.append(Paragraph(
                        f"<b>Locataire:</b> {contrat_actif.locataire.get_nom_complet()}",
                        self.styles['CustomNormal']
                    ))
                    story.append(Paragraph(
                        f"<b>Loyer mensuel:</b> {contrat_actif.loyer_mensuel:.0f} F CFA",
                        self.styles['CustomNormal']
                    ))
                    story.append(Paragraph(
                        f"<b>Charges mensuelles:</b> {contrat_actif.charges_mensuelles:.0f} F CFA",
                        self.styles['CustomNormal']
                    ))
                    story.append(Spacer(1, 10))
        else:
            story.append(Paragraph(
                "Aucune propriété active pour ce mois.",
                self.styles['CustomNormal']
            ))
        
        story.append(Spacer(1, 20))
        return story
    
    def _create_guarantee_verification(self):
        """Crée la vérification des garanties financières."""
        story = []
        
        story.append(Paragraph("VÉRIFICATION DES GARANTIES FINANCIÈRES", self.styles['CustomSubtitle']))
        
        # Tableau des garanties
        data = [
            ['Type de garantie', 'Montant requis', 'Montant versé', 'Statut'],
            ['Cautions', f"{self.recap.total_cautions_requises:.0f} F CFA", f"{self.recap.total_cautions_versees:.0f} F CFA", 
             "✅ Suffisant" if self.recap.total_cautions_versees >= self.recap.total_cautions_requises else "❌ Insuffisant"],
            ['Avances', f"{self.recap.total_avances_requises:.0f} F CFA", f"{self.recap.total_avances_versees:.0f} F CFA",
             "✅ Suffisant" if self.recap.total_avances_versees >= self.recap.total_avances_requises else "❌ Insuffisant"]
        ]
        
        table = Table(data, colWidths=[150, 100, 100, 150])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        story.append(table)
        story.append(Spacer(1, 10))
        
        # Statut global des garanties
        if self.recap.garanties_suffisantes:
            story.append(Paragraph(
                "✅ <b>GARANTIES FINANCIÈRES SUFFISANTES</b> - Le paiement peut être effectué.",
                self.styles['CustomImportant']
            ))
        else:
            story.append(Paragraph(
                "❌ <b>GARANTIES FINANCIÈRES INSUFFISANTES</b> - Le paiement ne peut pas être effectué.",
                self.styles['CustomImportant']
            ))
        
        story.append(Spacer(1, 20))
        return story
    
    def _create_footer(self):
        """Crée le pied de page."""
        story = []
        
        story.append(HRFlowable(width="100%", thickness=1, color=colors.grey))
        story.append(Spacer(1, 20))
        
        story.append(Paragraph(
            "Ce document a été généré automatiquement par le système de gestion immobilière.",
            self.styles['CustomNormal']
        ))
        
        story.append(Paragraph(
            f"Document généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}",
            self.styles['CustomNormal']
        ))
        
        return story

def generate_recap_pdf(recap_mensuel, method='reportlab'):
    """
    Fonction utilitaire pour générer un PDF de récapitulatif mensuel.
    
    Args:
        recap_mensuel: Instance du modèle RecapMensuel
        method: 'reportlab' (seule option disponible sur Windows)
    
    Returns:
        HttpResponse avec le PDF généré
    """
    try:
        generator = PDFGeneratorService(recap_mensuel)
        return generator.generate_pdf_reportlab()
    except Exception as e:
        raise Exception(f"Erreur lors de la génération du PDF: {str(e)}")

def generate_recap_pdf_batch(mois_recap, method='reportlab'):
    """
    Fonction utilitaire pour générer des PDF en lot pour un mois donné.
    
    Args:
        mois_recap: Date du mois pour lequel générer les PDFs
        method: 'reportlab' (seule option disponible sur Windows)
    
    Returns:
        HttpResponse avec le PDF généré
    """
    try:
        from .models import RecapMensuel
        
        # Récupérer tous les récapitulatifs pour ce mois
        recaps = RecapMensuel.objects.filter(mois_recap=mois_recap)
        
        if not recaps.exists():
            raise Exception("Aucun récapitulatif trouvé pour ce mois.")
        
        # Pour l'instant, on génère un seul PDF avec tous les récapitulatifs
        # TODO: Implémenter la génération de PDF multiples
        recap = recaps.first()
        return generate_recap_pdf(recap, method)
        
    except Exception as e:
        raise Exception(f"Erreur lors de la génération des PDFs en lot: {str(e)}")
