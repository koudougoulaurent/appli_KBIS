"""
Services pour la génération de PDF des paiements et récépissés.
Utilise l'extraction de texte au lieu d'embarquer les images.
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.pdfgen import canvas
from io import BytesIO
from django.conf import settings
from django.utils import timezone
from datetime import datetime
import os

class PaiementPDFService:
    """Service pour générer les PDF de paiements avec informations extraites des documents."""
    
    def __init__(self, paiement):
        self.paiement = paiement
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
        # Récupérer la configuration de l'entreprise depuis la base de données
        from core.models import ConfigurationEntreprise
        self.config_entreprise = ConfigurationEntreprise.get_configuration_active()
    
    def _setup_custom_styles(self):
        """Configure les styles personnalisés pour le PDF"""
        # Style pour le titre principal
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Title'],
            fontSize=18,
            spaceAfter=20,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        ))
        
        # Style pour les titres de section
        self.styles.add(ParagraphStyle(
            name='CustomHeading',
            parent=self.styles['Heading1'],
            fontSize=14,
            spaceAfter=12,
            spaceBefore=20,
            textColor=colors.darkblue
        ))
        
        # Style pour le corps du texte
        self.styles.add(ParagraphStyle(
            name='CustomBody',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=6,
            alignment=TA_JUSTIFY
        ))
        
        # Style pour les signatures
        self.styles.add(ParagraphStyle(
            name='CustomSignature',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=20,
            alignment=TA_CENTER
        ))

    def generate_recu_pdf(self):
        """Génère le PDF du reçu de paiement avec informations extraites des documents."""
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        # Construction du contenu du PDF
        story = []
        
        # En-tête avec informations de l'entreprise
        story.extend(self._create_header())
        story.append(Spacer(1, 20))
        
        # Informations du paiement
        story.extend(self._create_payment_info())
        story.append(Spacer(1, 20))
        
        # Informations du contrat
        story.extend(self._create_contract_info())
        story.append(Spacer(1, 20))
        
        # Documents joints (résumé au lieu d'images)
        story.extend(self._create_documents_summary())
        story.append(Spacer(1, 20))
        
        # Signatures
        story.extend(self._create_signatures())
        
        # Génération du PDF
        doc.build(story)
        buffer.seek(0)
        return buffer
    
    def _create_header(self):
        """Crée l'en-tête du document avec les informations de l'entreprise"""
        elements = []
        
        # Titre principal
        elements.append(Paragraph(
            "REÇU DE PAIEMENT",
            self.styles['CustomTitle']
        ))
        
        # Utiliser la fonction centralisée pour l'en-tête d'entreprise
        if self.config_entreprise:
            from core.utils import ajouter_en_tete_entreprise_reportlab
            ajouter_en_tete_entreprise_reportlab(elements, self.config_entreprise)
        else:
            # Fallback si pas de configuration
            elements.append(Paragraph(
                "GESTIMMOB",
                self.styles['CustomHeading']
            ))
            elements.append(Paragraph(
                "123 Rue de la Paix, 75001 Paris, France",
                self.styles['CustomBody']
            ))
        
        return elements

    def _create_payment_info(self):
        """Crée la section des informations de paiement"""
        elements = []
        
        elements.append(Paragraph("INFORMATIONS DU PAIEMENT", self.styles['CustomHeading']))
        
        # Tableau des informations de paiement
        data = [
            ['Numéro de reçu:', self.paiement.reference_paiement],
            ['Date de paiement:', self.paiement.date_paiement.strftime('%d/%m/%Y')],
            ['Montant:', f"{self.paiement.montant} F CFA"],
            ['Mode de paiement:', self.paiement.get_mode_paiement_display()],
            ['Statut:', self.paiement.get_statut_display()],
        ]
        
        table = Table(data, colWidths=[4*cm, 8*cm])
        table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ]))
        
        elements.append(table)
        
        return elements

    def _create_contract_info(self):
        """Crée la section des informations du contrat"""
        elements = []
        
        elements.append(Paragraph("INFORMATIONS DU CONTRAT", self.styles['CustomHeading']))
        
        contrat = self.paiement.contrat
        
        data_contrat = [
            ['Numéro de contrat:', contrat.numero_contrat],
            ['Propriété:', contrat.propriete.titre],
            ['Locataire:', f"{contrat.locataire.nom} {contrat.locataire.prenom}"],
            ['Bailleur:', f"{contrat.propriete.bailleur.nom} {contrat.propriete.bailleur.prenom}"],
            ['Loyer mensuel:', contrat.get_loyer_mensuel_formatted()],
            ['Charges:', contrat.get_charges_mensuelles_formatted()],
        ]
        
        table_contrat = Table(data_contrat, colWidths=[4*cm, 8*cm])
        table_contrat.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ]))
        
        elements.append(table_contrat)
        
        return elements

    def _create_documents_summary(self):
        """Crée un résumé des documents joints au lieu d'embarquer les images."""
        elements = []
        
        try:
            from core.services.document_text_extractor import DocumentTextExtractor
            extractor = DocumentTextExtractor()
            
            # Récupérer les documents du locataire
            locataire_documents = []
            if hasattr(self.paiement.contrat.locataire, 'documents'):
                locataire_documents = self.paiement.contrat.locataire.documents.all()
            
            if locataire_documents:
                elements.append(Paragraph("DOCUMENTS DU LOCATAIRE", self.styles['CustomHeading']))
                
                for document in locataire_documents:
                    if hasattr(document, 'fichier') and document.fichier:
                        try:
                            document_path = document.fichier.path
                            summary = extractor.get_document_summary_for_pdf(document_path)
                            elements.append(Paragraph(
                                f"<b>{document.nom}:</b> {summary}",
                                self.styles['CustomBody']
                            ))
                        except Exception as e:
                            elements.append(Paragraph(
                                f"<b>{document.nom}:</b> Document joint (fichier: {document.fichier.name})",
                                self.styles['CustomBody']
                            ))
                
                elements.append(Spacer(1, 10))
            
            # Récupérer les documents de la propriété
            propriete_documents = []
            if hasattr(self.paiement.contrat.propriete, 'documents'):
                propriete_documents = self.paiement.contrat.propriete.documents.all()
            
            if propriete_documents:
                elements.append(Paragraph("DOCUMENTS DE LA PROPRIÉTÉ", self.styles['CustomHeading']))
                
                for document in propriete_documents:
                    if hasattr(document, 'fichier') and document.fichier:
                        try:
                            document_path = document.fichier.path
                            summary = extractor.get_document_summary_for_pdf(document_path)
                            elements.append(Paragraph(
                                f"<b>{document.nom}:</b> {summary}",
                                self.styles['CustomBody']
                            ))
                        except Exception as e:
                            elements.append(Paragraph(
                                f"<b>{document.nom}:</b> Document joint (fichier: {document.fichier.name})",
                                self.styles['CustomBody']
                            ))
                
        except Exception as e:
            # Fallback si le service d'extraction n'est pas disponible
            elements.append(Paragraph(
                "Documents joints: Voir les fichiers attachés dans le système",
                self.styles['CustomBody']
            ))
        
        return elements

    def _create_signatures(self):
        """Crée la section des signatures"""
        elements = []
        
        elements.append(Paragraph("SIGNATURES", self.styles['CustomHeading']))
        
        # Signature du locataire
        elements.append(Paragraph(
            f"<b>Signature du locataire :</b><br/>"
            f"{self.paiement.contrat.locataire.nom} {self.paiement.contrat.locataire.prenom}<br/>"
            f"Date : _________________",
            self.styles['CustomSignature']
        ))
        
        elements.append(Spacer(1, 20))
        
        # Signature de l'agent immobilier
        if self.config_entreprise:
            elements.append(Paragraph(
                f"<b>Signature de l'agent immobilier :</b><br/>"
                f"{self.config_entreprise.nom_entreprise}<br/>"
                f"Date : _________________",
                self.styles['CustomSignature']
            ))
        
        return elements


class QuittancePDFService:
    """Service pour générer les PDF de quittances avec informations extraites des documents."""
    
    def __init__(self, quittance):
        self.quittance = quittance
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
        # Récupérer la configuration de l'entreprise depuis la base de données
        from core.models import ConfigurationEntreprise
        self.config_entreprise = ConfigurationEntreprise.get_configuration_active()

    def _setup_custom_styles(self):
        """Configure les styles personnalisés pour le PDF"""
        # Style pour le titre principal
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Title'],
            fontSize=18,
            spaceAfter=20,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        ))
        
        # Style pour les titres de section
        self.styles.add(ParagraphStyle(
            name='CustomHeading',
            parent=self.styles['Heading1'],
            fontSize=14,
            spaceAfter=12,
            spaceBefore=20,
            textColor=colors.darkblue
        ))
        
        # Style pour le corps du texte
        self.styles.add(ParagraphStyle(
            name='CustomBody',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=6,
            alignment=TA_JUSTIFY
        ))

    def generate_quittance_pdf(self):
        """Génère le PDF de la quittance avec informations extraites des documents."""
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        # Construction du contenu du PDF
        story = []
        
        # En-tête avec informations de l'entreprise
        story.extend(self._create_header())
        story.append(Spacer(1, 20))
        
        # Informations de la quittance
        story.extend(self._create_quittance_info())
        story.append(Spacer(1, 20))
        
        # Documents joints (résumé au lieu d'images)
        story.extend(self._create_documents_summary())
        
        # Génération du PDF
        doc.build(story)
        buffer.seek(0)
        return buffer

    def _create_header(self):
        """Crée l'en-tête du document avec les informations de l'entreprise"""
        elements = []
        
        # Titre principal
        elements.append(Paragraph(
            "RÉCÉPISSÉ DE LOYER",
            self.styles['CustomTitle']
        ))
        
        # Utiliser la fonction centralisée pour l'en-tête d'entreprise
        if self.config_entreprise:
            from core.utils import ajouter_en_tete_entreprise_reportlab
            ajouter_en_tete_entreprise_reportlab(elements, self.config_entreprise)
        else:
            # Fallback si pas de configuration
            elements.append(Paragraph(
                "GESTIMMOB",
                self.styles['CustomHeading']
            ))
            elements.append(Paragraph(
                "123 Rue de la Paix, 75001 Paris, France",
                self.styles['CustomBody']
            ))
        
        return elements

    def _create_quittance_info(self):
        """Crée la section des informations de la quittance"""
        elements = []
        
        elements.append(Paragraph("INFORMATIONS DU RÉCÉPISSÉ", self.styles['CustomHeading']))
        
        # Tableau des informations de la quittance
        data = [
            ['Numéro de récépissé:', self.quittance.numero_quittance],
            ['Période:', f"{self.quittance.mois_quittance.strftime('%B %Y')}"],
            ['Loyer:', f"{self.quittance.montant_loyer} F CFA"],
            ['Charges:', f"{self.quittance.montant_charges} F CFA"],
            ['Total:', f"{self.quittance.montant_total} F CFA"],
            ['Date d\'émission:', self.quittance.date_emission.strftime('%d/%m/%Y')],
        ]
        
        table = Table(data, colWidths=[4*cm, 8*cm])
        table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ]))
        
        elements.append(table)
        
        return elements

    def _create_documents_summary(self):
        """Crée un résumé des documents joints au lieu d'embarquer les images."""
        elements = []
        
        try:
            from core.services.document_text_extractor import DocumentTextExtractor
            extractor = DocumentTextExtractor()
            
            # Récupérer les documents du locataire
            locataire_documents = []
            if hasattr(self.quittance.contrat.locataire, 'documents'):
                locataire_documents = self.quittance.contrat.locataire.documents.all()
            
            if locataire_documents:
                elements.append(Paragraph("DOCUMENTS DU LOCATAIRE", self.styles['CustomHeading']))
                
                for document in locataire_documents:
                    if hasattr(document, 'fichier') and document.fichier:
                        try:
                            document_path = document.fichier.path
                            summary = extractor.get_document_summary_for_pdf(document_path)
                            elements.append(Paragraph(
                                f"<b>{document.nom}:</b> {summary}",
                                self.styles['CustomBody']
                            ))
                        except Exception as e:
                            elements.append(Paragraph(
                                f"<b>{document.nom}:</b> Document joint (fichier: {document.fichier.name})",
                                self.styles['CustomBody']
                            ))
                
        except Exception as e:
            # Fallback si le service d'extraction n'est pas disponible
            elements.append(Paragraph(
                "Documents joints: Voir les fichiers attachés dans le système",
                self.styles['CustomBody']
            ))
        
        return elements