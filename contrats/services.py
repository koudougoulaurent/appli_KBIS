from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
# from reportlab.pdfgen import canvas  # Non utilisé directement
from io import BytesIO

class ProprieteValidationService:
    """Service pour valider la disponibilité et la cohérence des propriétés."""
    
    @staticmethod
    def verifier_disponibilite_propriete(propriete, date_debut=None, date_fin=None, contrat_exclu=None):
        """
        Vérifie si une propriété est disponible pour la location.
        
        Args:
            propriete: Instance de Propriete
            date_debut: Date de début du contrat (optionnel)
            date_fin: Date de fin du contrat (optionnel)
            contrat_exclu: Contrat à exclure de la vérification (pour les modifications)
        
        Returns:
            dict: Résultat de la validation avec statut et messages
        """
        from contrats.models import Contrat
        
        resultat = {
            'disponible': True,
            'messages': [],
            'contrats_conflictuels': []
        }
        
        # Vérifier le statut de disponibilité de la propriété
        if not propriete.disponible:
            resultat['disponible'] = False
            resultat['messages'].append(f"La propriété {propriete.titre} n'est pas marquée comme disponible.")
        
        # Vérifier les contrats actifs existants
        contrats_actifs = Contrat.objects.filter(
            propriete=propriete,
            est_actif=True,
            est_resilie=False
        )
        
        if contrat_exclu:
            contrats_actifs = contrats_actifs.exclude(pk=contrat_exclu.pk)
        
        if contrats_actifs.exists():
            resultat['disponible'] = False
            resultat['messages'].append(f"La propriété {propriete.titre} a déjà des contrats actifs.")
            resultat['contrats_conflictuels'] = list(contrats_actifs)
        
        # Vérifier les chevauchements de dates si spécifiées
        if date_debut and date_fin:
            contrats_chevauchants = Contrat.objects.filter(
                propriete=propriete,
                est_actif=True,
                est_resilie=False
            )
            
            if contrat_exclu:
                contrats_chevauchants = contrats_chevauchants.exclude(pk=contrat_exclu.pk)
            
            for contrat in contrats_chevauchants:
                if (date_debut < contrat.date_fin and date_fin > contrat.date_debut):
                    resultat['disponible'] = False
                    resultat['messages'].append(
                        f"Chevauchement de dates avec le contrat {contrat.numero_contrat} "
                        f"({contrat.date_debut} - {contrat.date_fin})"
                    )
                    resultat['contrats_conflictuels'].append(contrat)
        
        return resultat
    
    @staticmethod
    def synchroniser_disponibilite_propriete(propriete):
        """
        Synchronise le statut de disponibilité d'une propriété avec ses contrats actifs.
        
        Args:
            propriete: Instance de Propriete
        
        Returns:
            bool: True si la synchronisation a été effectuée
        """
        from contrats.models import Contrat
        
        contrats_actifs = Contrat.objects.filter(
            propriete=propriete,
            est_actif=True,
            est_resilie=False
        )
        
        nouvelle_disponibilite = not contrats_actifs.exists()
        
        if propriete.disponible != nouvelle_disponibilite:
            propriete.disponible = nouvelle_disponibilite
            propriete.save(update_fields=['disponible'])
            return True
        
        return False
    
    @staticmethod
    def valider_integrite_proprietes():
        """
        Valide l'intégrité de toutes les propriétés et corrige les incohérences.
        
        Returns:
            dict: Rapport de validation avec corrections effectuées
        """
        from proprietes.models import Propriete
        from contrats.models import Contrat
        
        rapport = {
            'proprietes_verifiees': 0,
            'corrections_effectuees': 0,
            'erreurs_trouvees': [],
            'corrections': []
        }
        
        proprietes = Propriete.objects.all()
        
        for propriete in proprietes:
            rapport['proprietes_verifiees'] += 1
            
            try:
                # Vérifier la cohérence
                contrats_actifs = Contrat.objects.filter(
                    propriete=propriete,
                    est_actif=True,
                    est_resilie=False
                )
                
                disponibilite_correcte = not contrats_actifs.exists()
                
                if propriete.disponible != disponibilite_correcte:
                    rapport['corrections_effectuees'] += 1
                    rapport['corrections'].append({
                        'propriete': propriete.titre,
                        'ancien_statut': propriete.disponible,
                        'nouveau_statut': disponibilite_correcte,
                        'contrats_actifs': list(contrats_actifs.values_list('numero_contrat', flat=True))
                    })
                    
                    # Corriger la disponibilité
                    propriete.disponible = disponibilite_correcte
                    propriete.save(update_fields=['disponible'])
                
            except (OSError, IOError, ValueError) as e:
                rapport['erreurs_trouvees'].append({
                    'propriete': propriete.titre,
                    'erreur': str(e)
                })
        
        return rapport


class ContratPDFService:
    def __init__(self, contrat):
        self.contrat = contrat
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

    def generate_contrat_pdf(self, use_cache=True):
        """Génère le PDF du contrat de bail avec en-tête et pied de page fixes"""
        from core.pdf_cache import PDFCacheManager
        
        # Vérifier le cache si demandé
        if use_cache:
            cached_pdf = PDFCacheManager.get_cached_pdf('contrat', self.contrat.id)
            if cached_pdf:
                buffer = BytesIO()
                buffer.write(cached_pdf)
                buffer.seek(0)
                return buffer
        
        # Générer le PDF
        buffer = BytesIO()
        
        # Récupérer la configuration de l'entreprise
        from core.models import ConfigurationEntreprise
        self.config_entreprise = ConfigurationEntreprise.get_configuration_active()
        
        # Créer le document avec des marges ajustées pour éviter le chevauchement
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=4*cm,  # Plus d'espace pour l'en-tête
            bottomMargin=2*cm  # Moins d'espace pour le pied de page simplifié
        )
        
        # Construction du contenu du PDF
        story = []
        
        # Titre principal du contrat
        story.append(Paragraph(
            "CONTRAT DE LOCATION",
            self.styles['CustomTitle']
        ))
        story.append(Spacer(1, 20))
        
        # Informations de base du contrat
        story.extend(self._create_basic_info())
        story.append(Spacer(1, 20))
        
        # Conditions de location
        story.extend(self._create_rental_conditions())
        story.append(Spacer(1, 20))
        
        # Obligations et conditions
        story.extend(self._create_obligations())
        story.append(Spacer(1, 20))
        
        # Signatures
        story.extend(self._create_signatures())
        
        # Génération du PDF avec en-tête et pied de page personnalisés
        doc.build(story, onFirstPage=self._add_header_footer, onLaterPages=self._add_header_footer)
        buffer.seek(0)
        
        # Mettre en cache le PDF généré
        if use_cache:
            pdf_content = buffer.getvalue()
            PDFCacheManager.cache_pdf('contrat', self.contrat.id, pdf_content)
            buffer.seek(0)  # Remettre le pointeur au début
        
        return buffer

    def _create_header(self):
        """Crée l'en-tête du document avec les informations de l'entreprise"""
        elements = []
        
        # Titre principal
        elements.append(Paragraph(
            "CONTRAT DE BAIL D'HABITATION",
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

    def _add_header_footer(self, canvas_obj, doc):
        """Ajoute l'en-tête et le pied de page fixes sur chaque page"""
        import os
        
        # Dimensions de la page
        page_width, page_height = A4
        
        # === EN-TÊTE ===
        if self.config_entreprise:
            # Utiliser l'image d'en-tête personnalisée KBIS
            try:
                entete_path = self.config_entreprise.get_entete_prioritaire()
                if entete_path and os.path.exists(entete_path):
                    # Utiliser l'image d'en-tête personnalisée
                    from reportlab.lib.utils import ImageReader
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
                    # Fallback vers l'ancien système si l'image n'existe pas
                    # En-tête avec couleur de fond
                    canvas_obj.setFillColor(colors.lightblue)
                    canvas_obj.rect(0, page_height - 3*cm, page_width, 3*cm, fill=1, stroke=0)
                    
                    # Bordure en bas de l'en-tête
                    canvas_obj.setStrokeColor(colors.darkblue)
                    canvas_obj.setLineWidth(2)
                    canvas_obj.line(0, page_height - 3*cm, page_width, page_height - 3*cm)
                    
                    # Logo de l'entreprise (si disponible)
                    try:
                        logo_path = self.config_entreprise.get_logo_prioritaire()
                        if logo_path and os.path.exists(logo_path):
                            # Redimensionner le logo pour l'en-tête
                            logo_width = 2*cm
                            logo_height = 1.5*cm
                            
                            # Positionner le logo à gauche
                            logo_x = 1*cm
                            logo_y = page_height - 2.5*cm
                            
                            canvas_obj.drawImage(logo_path, logo_x, logo_y, logo_width, logo_height)
                            
                            # Texte de l'entreprise à droite du logo
                            text_x = logo_x + logo_width + 0.5*cm
                            text_y = page_height - 2.2*cm
                        else:
                            # Pas de logo - centrer le texte
                            text_x = 2*cm
                            text_y = page_height - 2.2*cm
                            
                    except (OSError, IOError, ValueError):
                        # En cas d'erreur avec le logo
                        text_x = 2*cm
                        text_y = page_height - 2.2*cm
                    
                    # Nom de l'entreprise
                    canvas_obj.setFillColor(colors.darkblue)
                    canvas_obj.setFont("Helvetica-Bold", 16)
                    canvas_obj.drawString(text_x, text_y, self.config_entreprise.nom_entreprise)
                    
                    # Adresse complète
                    canvas_obj.setFont("Helvetica", 10)
                    canvas_obj.drawString(text_x, text_y - 0.4*cm, self.config_entreprise.get_adresse_complete())
                    
                    # Informations de contact complètes
                    canvas_obj.setFont("Helvetica", 9)
                    canvas_obj.drawString(text_x, text_y - 0.8*cm, self.config_entreprise.get_contact_complet())
                    
            except (OSError, IOError, ValueError, AttributeError) as e:
                print(f"Erreur lors de l'ajout de l'en-tête personnalisé: {e}")
                # Fallback vers l'ancien système en cas d'erreur
                canvas_obj.setFillColor(colors.lightblue)
                canvas_obj.rect(0, page_height - 3*cm, page_width, 3*cm, fill=1, stroke=0)
                canvas_obj.setFillColor(colors.darkblue)
                canvas_obj.setFont("Helvetica-Bold", 16)
                canvas_obj.drawString(2*cm, page_height - 2.2*cm, self.config_entreprise.nom_entreprise)
        
        # === PIED DE PAGE SIMPLIFIÉ ===
        # Fond du pied de page réduit
        canvas_obj.setFillColor(colors.lightgrey)
        canvas_obj.rect(0, 0, page_width, 1.5*cm, fill=1, stroke=0)
        
        # Bordure en haut du pied de page
        canvas_obj.setStrokeColor(colors.grey)
        canvas_obj.setLineWidth(1)
        canvas_obj.line(0, 1.5*cm, page_width, 1.5*cm)
        
        if self.config_entreprise:
            # Informations de l'entreprise simplifiées dans le pied de page
            canvas_obj.setFillColor(colors.darkgrey)
            canvas_obj.setFont("Helvetica", 7)
            
            # Nom de l'entreprise uniquement
            canvas_obj.drawString(2*cm, 1*cm, f"{self.config_entreprise.nom_entreprise}")
            
            # Contact simplifié
            canvas_obj.drawString(2*cm, 0.6*cm, f"Tél: {self.config_entreprise.telephone} | Email: {self.config_entreprise.email}")
            
            # Numéro de page
            canvas_obj.setFont("Helvetica-Bold", 7)
            canvas_obj.drawRightString(page_width - 2*cm, 0.6*cm, f"Page {doc.page}")

    def _create_basic_info(self):
        """Crée la section des informations de base du contrat"""
        elements = []
        
        elements.append(Paragraph("INFORMATIONS DU CONTRAT", self.styles['CustomHeading']))
        
        # Tableau des informations
        data = [
            ['Numéro de contrat:', self.contrat.numero_contrat],
            ['Date de signature:', self.contrat.date_signature.strftime('%d/%m/%Y')],
            ['Date de début:', self.contrat.date_debut.strftime('%d/%m/%Y')],
            ['Date de fin:', self.contrat.date_fin.strftime('%d/%m/%Y') if self.contrat.date_fin else 'Indéterminée'],
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
        elements.append(Spacer(1, 15))
        
        # Informations de la propriété
        elements.append(Paragraph("INFORMATIONS DE LA PROPRIÉTÉ", self.styles['CustomHeading']))
        
        data_propriete = [
            ['Titre:', self.contrat.propriete.titre],
            ['Adresse:', self.contrat.propriete.adresse],
            ['Code postal:', self.contrat.propriete.code_postal],
            ['Ville:', self.contrat.propriete.ville],
            ['Type:', str(self.contrat.propriete.type_bien)],
            ['Surface:', f"{self.contrat.propriete.surface} m²"],
        ]
        
        table_propriete = Table(data_propriete, colWidths=[4*cm, 8*cm])
        table_propriete.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ]))
        
        elements.append(table_propriete)
        elements.append(Spacer(1, 15))
        
        # Informations du locataire
        elements.append(Paragraph("INFORMATIONS DU LOCATAIRE", self.styles['CustomHeading']))
        
        data_locataire = [
            ['Nom:', f"{self.contrat.locataire.nom} {self.contrat.locataire.prenom}"],
            ['Adresse:', self.contrat.locataire.adresse],
            ['Code postal:', self.contrat.locataire.code_postal],
            ['Ville:', self.contrat.locataire.ville],
            ['Téléphone:', self.contrat.locataire.telephone],
            ['Email:', self.contrat.locataire.email],
        ]
        
        table_locataire = Table(data_locataire, colWidths=[4*cm, 8*cm])
        table_locataire.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ]))
        
        elements.append(table_locataire)
        
        return elements

    def _create_rental_conditions(self):
        """Crée la section des conditions de location"""
        elements = []
        
        elements.append(Paragraph("CONDITIONS DE LOCATION", self.styles['CustomHeading']))
        
        # Tableau des conditions financières
        data_conditions = [
            ['Loyer mensuel:', self.contrat.get_loyer_mensuel_formatted()],
            ['Charges mensuelles:', self.contrat.get_charges_mensuelles_formatted()],
            ['Dépôt de garantie:', self.contrat.get_depot_garantie_formatted()],
            ['Avance de loyer:', self.contrat.get_avance_loyer_formatted()],
            ['Jour de paiement:', f"Le {self.contrat.jour_paiement} de chaque mois"],
            ['Mode de paiement:', self.contrat.get_mode_paiement_display()],
        ]
        
        table_conditions = Table(data_conditions, colWidths=[5*cm, 7*cm])
        table_conditions.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ]))
        
        elements.append(table_conditions)
        
        return elements

    def _create_obligations(self):
        """Crée la section des obligations et conditions"""
        elements = []
        
        elements.append(Paragraph("OBLIGATIONS ET CONDITIONS", self.styles['CustomHeading']))
        
        # Texte des obligations (personnalisable via la configuration)
        if self.config_entreprise and hasattr(self.config_entreprise, 'texte_contrat') and self.config_entreprise.texte_contrat:
            obligations_text = self.config_entreprise.texte_contrat
        else:
            # Texte par défaut si pas de configuration personnalisée
            obligations_text = """
            <b>Obligations du locataire :</b><br/>
            • Payer le loyer et les charges dans les délais convenus<br/>
            • Entretenir les lieux loués<br/>
            • Respecter le règlement intérieur<br/>
            • Ne pas effectuer de travaux sans autorisation<br/>
            • Assurer le logement contre les risques locatifs<br/>
            • Respecter la destination des lieux<br/><br/>
            
            <b>Obligations du bailleur :</b><br/>
            • Livrer le logement en bon état d'usage<br/>
            • Effectuer les réparations locatives<br/>
            • Respecter les obligations de sécurité<br/>
            • Garantir la jouissance paisible des lieux
            """
        
        elements.append(Paragraph(obligations_text, self.styles['CustomBody']))
        
        return elements

    def _create_signatures(self):
        """Crée la section des signatures"""
        elements = []
        
        elements.append(Paragraph("SIGNATURES", self.styles['CustomHeading']))
        
        # Ligne de séparation
        elements.append(Paragraph("<hr/>", self.styles['CustomBody']))
        elements.append(Spacer(1, 30))
        
        # Tableau des signatures pour éviter le chevauchement
        signature_data = [
            ['Signature du locataire', 'Signature de l\'agent immobilier'],
            ['', ''],
            [f"{self.contrat.locataire.nom} {self.contrat.locataire.prenom}", 
             f"{self.config_entreprise.nom_entreprise if self.config_entreprise else 'KBIS IMMOBILIER'}"],
            ['Date : _________________', 'Date : _________________']
        ]
        
        signature_table = Table(signature_data, colWidths=[8*cm, 8*cm])
        signature_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('LINEBELOW', (0, 1), (0, 1), 1, colors.black),
            ('LINEBELOW', (1, 1), (1, 1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        elements.append(signature_table)
        elements.append(Spacer(1, 30))
        
        # Ajouter les informations des documents joints (au lieu d'embarquer les images)
        elements.extend(self._create_documents_summary())
        
        return elements
    
    def _create_documents_summary(self):
        """Crée un résumé des documents joints au lieu d'embarquer les images."""
        elements = []
        
        try:
            from core.services.document_text_extractor import DocumentTextExtractor
            extractor = DocumentTextExtractor()
            
            # Récupérer les documents du locataire
            locataire_documents = []
            if hasattr(self.contrat.locataire, 'documents'):
                locataire_documents = self.contrat.locataire.documents.all()
            
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
                        except (OSError, IOError, ValueError):
                            elements.append(Paragraph(
                                f"<b>{document.nom}:</b> Document joint (fichier: {document.fichier.name})",
                                self.styles['CustomBody']
                            ))
                
                elements.append(Spacer(1, 10))
            
            # Récupérer les documents de la propriété
            propriete_documents = []
            if hasattr(self.contrat.propriete, 'documents'):
                propriete_documents = self.contrat.propriete.documents.all()
            
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
                        except (OSError, IOError, ValueError):
                            elements.append(Paragraph(
                                f"<b>{document.nom}:</b> Document joint (fichier: {document.fichier.name})",
                                self.styles['CustomBody']
                            ))
                
        except (OSError, IOError, ValueError):
            # Fallback si le service d'extraction n'est pas disponible
            elements.append(Paragraph(
                "Documents joints: Voir les fichiers attachés dans le système",
                self.styles['CustomBody']
            ))
        
        return elements


class RecuCautionPDFService:
    def __init__(self, recu):
        self.recu = recu
        self.contrat = recu.contrat
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
            textColor=colors.darkgreen
        ))
        
        # Style pour les titres de section
        self.styles.add(ParagraphStyle(
            name='CustomHeading',
            parent=self.styles['Heading1'],
            fontSize=14,
            spaceAfter=12,
            spaceBefore=20,
            textColor=colors.darkgreen
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

    def generate_recu_pdf(self, use_cache=True):
        """Génère le PDF du reçu de caution avec en-tête et pied de page fixes"""
        from core.pdf_cache import PDFCacheManager
        
        # Vérifier le cache si demandé
        if use_cache:
            cached_pdf = PDFCacheManager.get_cached_pdf('recu_caution', self.recu.id)
            if cached_pdf:
                buffer = BytesIO()
                buffer.write(cached_pdf)
                buffer.seek(0)
                return buffer
        
        # Générer le PDF
        buffer = BytesIO()
        
        # Créer le document avec des marges ajustées pour éviter le chevauchement
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=4*cm,  # Plus d'espace pour l'en-tête
            bottomMargin=2*cm  # Moins d'espace pour le pied de page simplifié
        )
        
        # Construction du contenu du PDF
        story = []
        
        # Titre principal du reçu
        story.append(Paragraph(
            "RECU DE CAUTION ET AVANCE",
            self.styles['CustomTitle']
        ))
        story.append(Spacer(1, 20))
        
        # Informations du reçu
        story.extend(self._create_receipt_info())
        story.append(Spacer(1, 20))
        
        # Informations du contrat
        story.extend(self._create_contract_info())
        story.append(Spacer(1, 20))
        
        # Détails financiers
        story.extend(self._create_financial_details())
        story.append(Spacer(1, 20))
        
        # Statut des paiements
        story.extend(self._create_payment_status())
        story.append(Spacer(1, 20))
        
        # Signatures
        story.extend(self._create_signatures())
        
        # Génération du PDF avec en-tête uniquement sur la première page
        doc.build(story, onFirstPage=self._add_header_footer, onLaterPages=self._add_footer_only)
        buffer.seek(0)
        
        # Mettre en cache le PDF généré
        if use_cache:
            pdf_content = buffer.getvalue()
            PDFCacheManager.cache_pdf('recu_caution', self.recu.id, pdf_content)
            buffer.seek(0)  # Remettre le pointeur au début
        
        return buffer

    def _add_footer_only(self, canvas_obj, doc):
        """Ajoute uniquement le pied de page (sans en-tête) sur les pages suivantes"""
        import os
        
        # Dimensions de la page
        page_width, page_height = A4
        
        # === PIED DE PAGE SIMPLIFIÉ ===
        # Fond du pied de page réduit
        canvas_obj.setFillColor(colors.lightgrey)
        canvas_obj.rect(0, 0, page_width, 1.5*cm, fill=1, stroke=0)
        
        # Informations de l'entreprise dans le pied de page
        if self.config_entreprise:
            canvas_obj.setFillColor(colors.black)
            canvas_obj.setFont("Helvetica", 8)
            
            # Nom de l'entreprise
            canvas_obj.drawString(1*cm, 0.8*cm, self.config_entreprise.nom_entreprise)
            
            # Adresse
            adresse_complete = self.config_entreprise.get_adresse_complete()
            if adresse_complete and adresse_complete != "Adresse non configurée":
                canvas_obj.drawString(1*cm, 0.5*cm, adresse_complete)
            
            # Téléphone et email
            contact_info = []
            if self.config_entreprise.telephone:
                contact_info.append(f"Tel: {self.config_entreprise.telephone}")
            if self.config_entreprise.email:
                contact_info.append(f"Email: {self.config_entreprise.email}")
            
            if contact_info:
                canvas_obj.drawString(1*cm, 0.2*cm, " | ".join(contact_info))
        
        # Numéro de page
        canvas_obj.setFillColor(colors.black)
        canvas_obj.setFont("Helvetica", 8)
        canvas_obj.drawRightString(page_width - 1*cm, 0.5*cm, f"Page {doc.page}")

    def _add_header_footer(self, canvas_obj, doc):
        """Ajoute l'en-tête et le pied de page fixes sur chaque page"""
        import os
        
        # Dimensions de la page
        page_width, page_height = A4
        
        # === EN-TÊTE ===
        if self.config_entreprise:
            # Utiliser l'image d'en-tête personnalisée KBIS
            try:
                entete_path = self.config_entreprise.get_entete_prioritaire()
                if entete_path and os.path.exists(entete_path):
                    # Utiliser l'image d'en-tête personnalisée
                    from reportlab.lib.utils import ImageReader
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
                    # Fallback vers l'ancien système si l'image n'existe pas
                    # En-tête avec couleur de fond
                    canvas_obj.setFillColor(colors.lightgreen)
                    canvas_obj.rect(0, page_height - 3*cm, page_width, 3*cm, fill=1, stroke=0)
                    
                    # Bordure en bas de l'en-tête
                    canvas_obj.setStrokeColor(colors.darkgreen)
                    canvas_obj.setLineWidth(2)
                    canvas_obj.line(0, page_height - 3*cm, page_width, page_height - 3*cm)
                    
                    # Logo de l'entreprise (si disponible)
                    try:
                        logo_path = self.config_entreprise.get_logo_prioritaire()
                        if logo_path and os.path.exists(logo_path):
                            # Redimensionner le logo pour l'en-tête
                            logo_width = 2*cm
                            logo_height = 1.5*cm
                            
                            # Positionner le logo à gauche
                            logo_x = 1*cm
                            logo_y = page_height - 2.5*cm
                            
                            canvas_obj.drawImage(logo_path, logo_x, logo_y, logo_width, logo_height)
                            
                            # Texte de l'entreprise à droite du logo
                            text_x = logo_x + logo_width + 0.5*cm
                            text_y = page_height - 2.2*cm
                        else:
                            # Pas de logo - centrer le texte
                            text_x = 2*cm
                            text_y = page_height - 2.2*cm
                            
                    except (OSError, IOError, ValueError):
                        # En cas d'erreur avec le logo
                        text_x = 2*cm
                        text_y = page_height - 2.2*cm
                    
                    # Nom de l'entreprise
                    canvas_obj.setFillColor(colors.darkgreen)
                    canvas_obj.setFont("Helvetica-Bold", 16)
                    canvas_obj.drawString(text_x, text_y, self.config_entreprise.nom_entreprise)
                    
                    # Adresse complète
                    canvas_obj.setFont("Helvetica", 10)
                    canvas_obj.drawString(text_x, text_y - 0.4*cm, self.config_entreprise.get_adresse_complete())
                    
                    # Informations de contact complètes
                    canvas_obj.setFont("Helvetica", 9)
                    canvas_obj.drawString(text_x, text_y - 0.8*cm, self.config_entreprise.get_contact_complet())
                    
            except (OSError, IOError, ValueError, AttributeError) as e:
                print(f"Erreur lors de l'ajout de l'en-tête personnalisé: {e}")
                # Fallback vers l'ancien système en cas d'erreur
                canvas_obj.setFillColor(colors.lightgreen)
                canvas_obj.rect(0, page_height - 3*cm, page_width, 3*cm, fill=1, stroke=0)
                canvas_obj.setFillColor(colors.darkgreen)
                canvas_obj.setFont("Helvetica-Bold", 16)
                canvas_obj.drawString(2*cm, page_height - 2.2*cm, self.config_entreprise.nom_entreprise)
        
        # === PIED DE PAGE SIMPLIFIÉ ===
        # Fond du pied de page réduit
        canvas_obj.setFillColor(colors.lightgrey)
        canvas_obj.rect(0, 0, page_width, 1.5*cm, fill=1, stroke=0)
        
        # Bordure en haut du pied de page
        canvas_obj.setStrokeColor(colors.grey)
        canvas_obj.setLineWidth(1)
        canvas_obj.line(0, 1.5*cm, page_width, 1.5*cm)
        
        if self.config_entreprise:
            # Informations de l'entreprise simplifiées dans le pied de page
            canvas_obj.setFillColor(colors.darkgrey)
            canvas_obj.setFont("Helvetica", 7)
            
            # Nom de l'entreprise uniquement
            canvas_obj.drawString(2*cm, 1*cm, f"{self.config_entreprise.nom_entreprise}")
            
            # Contact simplifié
            canvas_obj.drawString(2*cm, 0.6*cm, f"Tél: {self.config_entreprise.telephone} | Email: {self.config_entreprise.email}")
            
            # Numéro de page
            canvas_obj.setFont("Helvetica-Bold", 7)
            canvas_obj.drawRightString(page_width - 2*cm, 0.6*cm, f"Page {doc.page}")

    def _create_receipt_info(self):
        """Crée la section des informations du reçu"""
        elements = []
        
        elements.append(Paragraph("INFORMATIONS DU RECU", self.styles['CustomHeading']))
        
        # Tableau des informations du reçu
        data = [
            ['Numéro:', self.recu.numero_recu],
            ['Date:', self.recu.date_emission.strftime('%d/%m/%Y')],
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
        
        # Tableau des informations du contrat
        data = [
            ['Numéro:', self.contrat.numero_contrat],
            ['Propriété:', self.contrat.propriete.titre],
            ['Locataire:', f"{self.contrat.locataire.nom} {self.contrat.locataire.prenom}"],
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

    def _create_financial_details(self):
        """Crée la section des détails financiers"""
        elements = []
        
        elements.append(Paragraph("DETAILS FINANCIERS", self.styles['CustomHeading']))
        
        # Calculer les mois couverts par l'avance
        mois_couverts_info = self._calculer_mois_couverts_avance()
        
        # Tableau des détails financiers
        data = [
            ['Description', 'Montant'],
            ['Loyer mensuel:', self.contrat.get_loyer_mensuel_formatted()],
            ['Charges mensuelles:', self.contrat.get_charges_mensuelles_formatted()],
            ['Dépôt de garantie:', self.contrat.get_depot_garantie_formatted()],
            ['Avance de loyer:', self.contrat.get_avance_loyer_formatted()],
            ['TOTAL:', self.contrat.get_total_caution_avance_formatted()],
        ]
        
        # Créer le tableau principal des détails financiers
        table = Table(data, colWidths=[8*cm, 4*cm])
        table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (0, -2), 'Helvetica'),
            ('FONTNAME', (1, 1), (1, -2), 'Helvetica'),
            ('FONTNAME', (0, -1), (1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('BACKGROUND', (0, -1), (-1, -1), colors.lightblue),
        ]))
        
        elements.append(table)
        
        # Ajouter un tableau séparé pour les informations sur l'avance avec cellules fusionnées
        if mois_couverts_info and self.contrat.avance_loyer and self.contrat.avance_loyer > 0:
            elements.append(Spacer(1, 10))
            
            # Préparer les informations sur les mois couverts avec gestion des retours à la ligne
            mois_liste = mois_couverts_info.get('mois_liste', [])
            if mois_liste:
                # Gérer les retours à la ligne pour éviter le débordement
                mois_texte_complet = ', '.join(mois_liste)
                # Diviser le texte en lignes de 50 caractères maximum
                if len(mois_texte_complet) > 50:
                    mots = mois_texte_complet.split(', ')
                    lignes = []
                    ligne_actuelle = []
                    longueur_actuelle = 0
                    
                    for mot in mots:
                        if longueur_actuelle + len(mot) + 2 > 50 and ligne_actuelle:  # +2 pour ", "
                            lignes.append(', '.join(ligne_actuelle))
                            ligne_actuelle = [mot]
                            longueur_actuelle = len(mot)
                        else:
                            ligne_actuelle.append(mot)
                            longueur_actuelle += len(mot) + 2 if ligne_actuelle else 0
                    
                    if ligne_actuelle:
                        lignes.append(', '.join(ligne_actuelle))
                    
                    mois_info = f"{mois_couverts_info['nombre']} mois ({'<br/>'.join(lignes)})"
                else:
                    mois_info = f"{mois_couverts_info['nombre']} mois ({mois_texte_complet})"
            else:
                mois_info = f"{mois_couverts_info['nombre']} mois ({mois_couverts_info['mois_texte']})"
            
            # Convertir les mois en français
            mois_debut_fr = self._convertir_mois_francais(mois_couverts_info['date_debut'])
            mois_fin_fr = self._convertir_mois_francais(mois_couverts_info['date_fin'])
            periode_info = f"{mois_debut_fr} {mois_couverts_info['date_debut'].year} à {mois_fin_fr} {mois_couverts_info['date_fin'].year}"
            
            # Créer un tableau avec cellules fusionnées pour les informations sur l'avance
            avance_data = [
                ['INFORMATIONS SUR L\'AVANCE DE LOYER'],
                ['Mois couverts:', mois_info],
                ['Période de couverture:', periode_info]
            ]
            
            avance_table = Table(avance_data, colWidths=[4*cm, 8*cm])
            avance_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                ('TOPPADDING', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgreen),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightgreen),
                ('SPAN', (0, 0), (1, 0)),  # Fusionner la première ligne
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),  # Alignement en haut pour gérer les retours à la ligne
                ('WORDWRAP', (1, 1), (1, -1)),  # Permettre le retour à la ligne dans la colonne de droite
            ]))
            
            elements.append(avance_table)
        
        return elements

    def _calculer_mois_couverts_avance(self):
        """Calcule les mois couverts par l'avance de loyer"""
        if not self.contrat.avance_loyer or self.contrat.avance_loyer <= 0:
            return None
            
        if not self.contrat.loyer_mensuel or self.contrat.loyer_mensuel <= 0:
            return None
        
        try:
            # Utiliser le service corrigé pour calculer les mois couverts
            from paiements.services_avance_corrige import ServiceAvanceCorrige
            
            mois_couverts_data = ServiceAvanceCorrige.calculer_mois_couverts_correct(
                self.contrat, self.contrat.avance_loyer, None
            )
            
            if mois_couverts_data:
                return {
                    'nombre': mois_couverts_data['nombre'],
                    'mois_texte': mois_couverts_data['mois_texte'],
                    'date_debut': mois_couverts_data['date_debut'],
                    'date_fin': mois_couverts_data['date_fin']
                }
        except Exception as e:
            print(f"[DEBUG] Erreur lors du calcul des mois couverts: {e}")
            pass
        
        return None

    def _convertir_mois_francais(self, date_obj):
        """Convertit un mois en français"""
        mois_francais = {
            1: 'Janvier', 2: 'Février', 3: 'Mars', 4: 'Avril',
            5: 'Mai', 6: 'Juin', 7: 'Juillet', 8: 'Août',
            9: 'Septembre', 10: 'Octobre', 11: 'Novembre', 12: 'Décembre'
        }
        return mois_francais.get(date_obj.month, date_obj.strftime('%B'))

    def _create_payment_status(self):
        """Crée la section du statut des paiements"""
        elements = []
        
        elements.append(Paragraph("STATUT DES PAIEMENTS", self.styles['CustomHeading']))
        
        # Tableau du statut des paiements
        # Utiliser les méthodes dynamiques basées sur les vrais paiements
        caution_ok = self.contrat.get_caution_payee_dynamique()
        avance_ok = self.contrat.get_avance_payee_dynamique()
        
        caution_statut = '✓ Payée' if caution_ok else ('Non requise' if caution_ok is None else '✗ En attente')
        avance_statut = '✓ Payée' if avance_ok else ('Non requise' if avance_ok is None else '✗ En attente')
        
        # Calculer les mois couverts par l'avance
        mois_couverts_info = self._calculer_mois_couverts_avance()
        
        data = [
            ['Type de paiement', 'Statut'],
            ['Caution:', caution_statut],
            ['Avance:', avance_statut],
        ]
        
        # Ne pas répéter les informations sur les mois couverts dans le statut des paiements
        # (elles sont déjà affichées dans les détails financiers)
        
        table = Table(data, colWidths=[6*cm, 6*cm])
        table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ]))
        
        elements.append(table)
        return elements

    def _create_signatures(self):
        """Crée la section des signatures"""
        elements = []
        
        elements.append(Paragraph("SIGNATURES", self.styles['CustomHeading']))
        elements.append(Spacer(1, 20))
        
        # Tableau des signatures amélioré
        signature_data = [
            ['Signature du locataire', 'Signature de l\'agent immobilier'],
            ['', ''],  # Lignes de signature
            ['', ''],  # Lignes de signature supplémentaires
            [f"{self.contrat.locataire.nom} {self.contrat.locataire.prenom}", 
             f"{self.config_entreprise.nom_entreprise if self.config_entreprise else 'KBIS IMMOBILIER'}"],
            ['Date : _________________', 'Date : _________________']
        ]
        
        signature_table = Table(signature_data, colWidths=[8*cm, 8*cm])
        signature_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (0, 2), 'Helvetica'),  # Lignes de signature
            ('FONTNAME', (0, 3), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
            ('TOPPADDING', (0, 0), (-1, -1), 15),
            ('LINEBELOW', (0, 1), (0, 2), 2, colors.black),  # Ligne de signature plus épaisse
            ('LINEBELOW', (1, 1), (1, 2), 2, colors.black),  # Ligne de signature plus épaisse
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ]))
        
        elements.append(signature_table)
        elements.append(Spacer(1, 30))
        
        return elements


class ResiliationPDFService:
    def __init__(self, resiliation):
        self.resiliation = resiliation
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
            textColor=colors.darkred
        ))
        
        # Style pour les titres de section
        self.styles.add(ParagraphStyle(
            name='CustomHeading',
            parent=self.styles['Heading1'],
            fontSize=14,
            spaceAfter=12,
            spaceBefore=20,
            textColor=colors.darkred
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

    def generate_resiliation_pdf(self, use_cache=True):
        """Génère le PDF de résiliation avec en-tête et pied de page fixes"""
        from core.pdf_cache import PDFCacheManager
        
        # Vérifier le cache si demandé
        if use_cache:
            cached_pdf = PDFCacheManager.get_cached_pdf('resiliation', self.resiliation.id)
            if cached_pdf:
                buffer = BytesIO()
                buffer.write(cached_pdf)
                buffer.seek(0)
                return buffer
        
        # Générer le PDF
        buffer = BytesIO()
        
        # Récupérer la configuration de l'entreprise
        from core.models import ConfigurationEntreprise
        self.config_entreprise = ConfigurationEntreprise.get_configuration_active()
        
        # Créer le document avec des marges ajustées pour éviter le chevauchement
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=4*cm,  # Plus d'espace pour l'en-tête
            bottomMargin=2*cm  # Moins d'espace pour le pied de page simplifié
        )
        
        # Construction du contenu du PDF
        story = []
        
        # Titre principal de la résiliation
        story.append(Paragraph(
            "AVIS DE RÉSILIATION DE CONTRAT",
            self.styles['CustomTitle']
        ))
        story.append(Spacer(1, 20))
        
        # Informations de la résiliation
        story.extend(self._create_resiliation_info())
        story.append(Spacer(1, 20))
        
        # Informations du contrat
        story.extend(self._create_contract_info())
        story.append(Spacer(1, 20))
        
        # Motifs et conditions
        story.extend(self._create_termination_details())
        story.append(Spacer(1, 20))
        
        # Signatures
        story.extend(self._create_signatures())
        
        # Génération du PDF avec en-tête et pied de page personnalisés
        doc.build(story, onFirstPage=self._add_header_footer, onLaterPages=self._add_header_footer)
        buffer.seek(0)
        
        # Mettre en cache le PDF généré
        if use_cache:
            pdf_content = buffer.getvalue()
            PDFCacheManager.cache_pdf('resiliation', self.resiliation.id, pdf_content)
            buffer.seek(0)  # Remettre le pointeur au début
        
        return buffer

    def _create_header(self):
        """Crée l'en-tête du document avec les informations de l'entreprise"""
        elements = []
        
        # Titre principal
        elements.append(Paragraph(
            "AVIS DE RÉSILIATION DE CONTRAT DE BAIL",
            self.styles['CustomTitle']
        ))
        
        # Informations de l'entreprise
        if self.config_entreprise:
            elements.append(Paragraph(
                f"<b>{self.config_entreprise.nom_entreprise}</b>",
                self.styles['CustomHeading']
            ))
            elements.append(Paragraph(
                self.config_entreprise.get_adresse_complete(),
                self.styles['CustomBody']
            ))
            elements.append(Paragraph(
                self.config_entreprise.get_contact_complet(),
                self.styles['CustomBody']
            ))
            if self.config_entreprise.siret:
                elements.append(Paragraph(
                    f"SIRET: {self.config_entreprise.siret}",
                    self.styles['CustomBody']
                ))
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

    def _add_header_footer(self, canvas_obj, doc):
        """Ajoute l'en-tête et le pied de page fixes sur chaque page"""
        import os
        
        # Dimensions de la page
        page_width, page_height = A4
        
        # === EN-TÊTE ===
        if self.config_entreprise:
            # En-tête avec couleur de fond
            canvas_obj.setFillColor(colors.lightcoral)
            canvas_obj.rect(0, page_height - 3*cm, page_width, 3*cm, fill=1, stroke=0)
            
            # Bordure en bas de l'en-tête
            canvas_obj.setStrokeColor(colors.darkred)
            canvas_obj.setLineWidth(2)
            canvas_obj.line(0, page_height - 3*cm, page_width, page_height - 3*cm)
            
            # Logo de l'entreprise (si disponible)
            try:
                logo_path = self.config_entreprise.get_logo_prioritaire()
                if logo_path and os.path.exists(logo_path):
                    # Redimensionner le logo pour l'en-tête
                    logo_width = 2*cm
                    logo_height = 1.5*cm
                    
                    # Positionner le logo à gauche
                    logo_x = 1*cm
                    logo_y = page_height - 2.5*cm
                    
                    canvas_obj.drawImage(logo_path, logo_x, logo_y, logo_width, logo_height)
                    
                    # Texte de l'entreprise à droite du logo
                    text_x = logo_x + logo_width + 0.5*cm
                    text_y = page_height - 2.2*cm
                else:
                    # Pas de logo - centrer le texte
                    text_x = 2*cm
                    text_y = page_height - 2.2*cm
                    
            except (OSError, IOError, ValueError):
                # En cas d'erreur avec le logo
                text_x = 2*cm
                text_y = page_height - 2.2*cm
            
            # Nom de l'entreprise
            canvas_obj.setFillColor(colors.darkred)
            canvas_obj.setFont("Helvetica-Bold", 16)
            canvas_obj.drawString(text_x, text_y, self.config_entreprise.nom_entreprise)
            
            # Adresse
            canvas_obj.setFont("Helvetica", 10)
            canvas_obj.drawString(text_x, text_y - 0.4*cm, self.config_entreprise.get_adresse_complete())
            
            # Informations de contact
            contact_info = []
            if self.config_entreprise.telephone:
                contact_info.append(f"Tél: {self.config_entreprise.telephone}")
            if self.config_entreprise.email:
                contact_info.append(f"Email: {self.config_entreprise.email}")
            
            if contact_info:
                canvas_obj.setFont("Helvetica", 9)
                canvas_obj.drawString(text_x, text_y - 0.8*cm, " | ".join(contact_info))
        
        # === PIED DE PAGE SIMPLIFIÉ ===
        # Fond du pied de page réduit
        canvas_obj.setFillColor(colors.lightgrey)
        canvas_obj.rect(0, 0, page_width, 1.5*cm, fill=1, stroke=0)
        
        # Bordure en haut du pied de page
        canvas_obj.setStrokeColor(colors.grey)
        canvas_obj.setLineWidth(1)
        canvas_obj.line(0, 1.5*cm, page_width, 1.5*cm)
        
        if self.config_entreprise:
            # Informations de l'entreprise simplifiées dans le pied de page
            canvas_obj.setFillColor(colors.darkgrey)
            canvas_obj.setFont("Helvetica", 7)
            
            # Nom de l'entreprise uniquement
            canvas_obj.drawString(2*cm, 1*cm, f"{self.config_entreprise.nom_entreprise}")
            
            # Contact simplifié
            canvas_obj.drawString(2*cm, 0.6*cm, f"Tél: {self.config_entreprise.telephone} | Email: {self.config_entreprise.email}")
            
            # Numéro de page
            canvas_obj.setFont("Helvetica-Bold", 7)
            canvas_obj.drawRightString(page_width - 2*cm, 0.6*cm, f"Page {doc.page}")

    def _create_resiliation_info(self):
        """Crée la section des informations de résiliation"""
        elements = []
        
        elements.append(Paragraph("INFORMATIONS DE LA RÉSILIATION", self.styles['CustomHeading']))
        
        # Tableau des informations
        data = [
            ['ID de résiliation:', str(self.resiliation.id)],
            ['Date de résiliation:', self.resiliation.date_resiliation.strftime('%d/%m/%Y')],
            ['Type de résiliation:', self.resiliation.get_type_resiliation_display()],
            ['Statut:', self.resiliation.get_statut_display()],
            ['Motif:', self.resiliation.motif_resiliation[:50] + '...' if len(self.resiliation.motif_resiliation) > 50 else self.resiliation.motif_resiliation],
        ]
        
        table = Table(data, colWidths=[5*cm, 7*cm])
        table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ]))
        
        elements.append(table)
        
        return elements

    def _create_contract_info(self):
        """Crée la section des informations du contrat"""
        elements = []
        
        elements.append(Paragraph("INFORMATIONS DU CONTRAT", self.styles['CustomHeading']))
        
        contrat = self.resiliation.contrat
        
        data_contrat = [
            ['Numéro de contrat:', contrat.numero_contrat],
            ['Date de signature:', contrat.date_signature.strftime('%d/%m/%Y')],
            ['Date de début:', contrat.date_debut.strftime('%d/%m/%Y')],
            ['Propriété:', contrat.propriete.titre],
            ['Locataire:', f"{contrat.locataire.nom} {contrat.locataire.prenom}"],
            ['Loyer mensuel:', contrat.get_loyer_mensuel_formatted()],
        ]
        
        table_contrat = Table(data_contrat, colWidths=[5*cm, 7*cm])
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

    def _create_termination_details(self):
        """Crée la section des détails de la résiliation"""
        elements = []
        
        elements.append(Paragraph("DÉTAILS DE LA RÉSILIATION", self.styles['CustomHeading']))
        
        # Motifs de résiliation
        if self.resiliation.motif_resiliation:
            elements.append(Paragraph(
                f"<b>Motifs de la résiliation :</b><br/>{self.resiliation.motif_resiliation}",
                self.styles['CustomBody']
            ))
            elements.append(Spacer(1, 10))
        
        # Conditions de sortie
        if self.config_entreprise and hasattr(self.config_entreprise, 'texte_resiliation') and self.config_entreprise.texte_resiliation:
            conditions_text = self.config_entreprise.texte_resiliation
        else:
            # Texte par défaut si pas de configuration personnalisée
            conditions_text = """
            <b>Conditions de sortie :</b><br/>
            • Le locataire doit libérer les lieux dans l'état où il les a reçus<br/>
            • Un état des lieux de sortie sera effectué<br/>
            • La caution sera restituée après déduction des éventuels dommages<br/>
            • Les clés doivent être remises le jour de la sortie
            """
        
        elements.append(Paragraph(conditions_text, self.styles['CustomBody']))
        
        return elements

    def _create_signatures(self):
        """Crée la section des signatures"""
        elements = []
        
        elements.append(Paragraph("SIGNATURES", self.styles['CustomHeading']))
        
        # Ligne de séparation
        elements.append(Paragraph("<hr/>", self.styles['CustomBody']))
        elements.append(Spacer(1, 30))
        
        # Tableau des signatures pour éviter le chevauchement
        signature_data = [
            ['Signature du bailleur', 'Signature du locataire'],
            ['', ''],
            [f"{self.resiliation.contrat.propriete.bailleur.nom} {self.resiliation.contrat.propriete.bailleur.prenom}", 
             f"{self.resiliation.contrat.locataire.nom} {self.resiliation.contrat.locataire.prenom}"],
            ['Date : _________________', 'Date : _________________']
        ]
        
        signature_table = Table(signature_data, colWidths=[8*cm, 8*cm])
        signature_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('LINEBELOW', (0, 1), (0, 1), 1, colors.black),
            ('LINEBELOW', (1, 1), (1, 1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        elements.append(signature_table)
        elements.append(Spacer(1, 30))
        
        # Signature de l'agent immobilier séparée
        if self.config_entreprise:
            elements.append(Paragraph(
                f"<b>Signature de l'agent immobilier :</b><br/>"
                f"{self.config_entreprise.nom_entreprise}<br/>"
                f"Date : _________________",
                self.styles['CustomSignature']
            ))
            elements.append(Spacer(1, 30))
        
        # Ajouter les informations des documents joints (au lieu d'embarquer les images)
        elements.extend(self._create_documents_summary())
        
        return elements
    
    def _create_documents_summary(self):
        """Crée un résumé des documents joints au lieu d'embarquer les images."""
        elements = []
        
        try:
            from core.services.document_text_extractor import DocumentTextExtractor
            extractor = DocumentTextExtractor()
            
            # Récupérer les documents du bailleur
            bailleur_documents = []
            if hasattr(self.resiliation.contrat.propriete.bailleur, 'documents'):
                bailleur_documents = self.resiliation.contrat.propriete.bailleur.documents.all()
            
            if bailleur_documents:
                elements.append(Paragraph("DOCUMENTS DU BAILLEUR", self.styles['CustomHeading']))
                
                for document in bailleur_documents:
                    if hasattr(document, 'fichier') and document.fichier:
                        try:
                            document_path = document.fichier.path
                            summary = extractor.get_document_summary_for_pdf(document_path)
                            elements.append(Paragraph(
                                f"<b>{document.nom}:</b> {summary}",
                                self.styles['CustomBody']
                            ))
                        except (OSError, IOError, ValueError):
                            elements.append(Paragraph(
                                f"<b>{document.nom}:</b> Document joint (fichier: {document.fichier.name})",
                                self.styles['CustomBody']
                            ))
                
                elements.append(Spacer(1, 10))
            
            # Récupérer les documents du locataire
            locataire_documents = []
            if hasattr(self.resiliation.contrat.locataire, 'documents'):
                locataire_documents = self.resiliation.contrat.locataire.documents.all()
            
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
                        except (OSError, IOError, ValueError):
                            elements.append(Paragraph(
                                f"<b>{document.nom}:</b> Document joint (fichier: {document.fichier.name})",
                                self.styles['CustomBody']
                            ))
                
        except (OSError, IOError, ValueError):
            # Fallback si le service d'extraction n'est pas disponible
            elements.append(Paragraph(
                "Documents joints: Voir les fichiers attachés dans le système",
                self.styles['CustomBody']
            ))
        
        return elements
