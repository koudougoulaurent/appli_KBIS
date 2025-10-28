from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_RIGHT
# from reportlab.pdfgen import canvas  # Non utilisé directement
from io import BytesIO
from datetime import datetime

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

    def generate_contrat_pdf(self, use_cache=False, user=None):
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
        
        # Stocker l'utilisateur pour l'affichage
        self.user = user
        
        # Créer le document avec des marges optimisées pour éviter le chevauchement
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=1.5*cm,
            leftMargin=1.5*cm,
            topMargin=4*cm,  # Marge supérieure augmentée pour éviter le chevauchement
            bottomMargin=1*cm  # Marge inférieure pour le pied de page
        )
        
        # Construction du contenu du PDF
        story = []
        
        # Titre principal du contrat avec espacement pour éviter le chevauchement
        story.append(Paragraph(
            "CONTRAT DE LOCATION",
            self.styles['CustomTitle']
        ))
        story.append(Spacer(1, 15))  # Espacement réduit pour éviter la page vide
        
        # Informations de base du contrat
        story.extend(self._create_basic_info())
        story.append(PageBreak())  # Saut de page pour le module suivant
        
        # Conditions de location
        story.extend(self._create_rental_conditions())
        story.append(PageBreak())  # Saut de page pour le module suivant
        
        # Obligations et conditions
        story.extend(self._create_obligations())
        story.append(PageBreak())  # Saut de page pour le module suivant
        
        # État des lieux
        story.extend(self._create_etat_des_lieux())
        story.append(PageBreak())  # Saut de page pour le module suivant
        
        # Signatures (engagement à la fin)
        story.extend(self._create_signatures())
        
        # Génération du PDF avec en-tête première page seulement et pied de page dernière page seulement
        doc.build(story, onFirstPage=self._add_header_only, onLaterPages=self._add_footer_last_page_only)
        buffer.seek(0)
        
        # Mettre en cache le PDF généré
        if use_cache:
            pdf_content = buffer.getvalue()
            PDFCacheManager.cache_pdf('contrat', self.contrat.id, pdf_content)
            buffer.seek(0)  # Remettre le pointeur au début
        
        return buffer

    @classmethod
    def clear_contrat_cache(cls, contrat_id=None):
        """Vide le cache des contrats"""
        from core.pdf_cache import PDFCacheManager
        
        if contrat_id:
            # Vider le cache d'un contrat spécifique
            PDFCacheManager.invalidate_cache('contrat', contrat_id)
        else:
            # Vider tout le cache des contrats
            PDFCacheManager.invalidate_all_pdf_cache()

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
        """Crée la section des informations de base du contrat selon le nouveau format"""
        elements = []
        
        # Date et lieu - alignée à droite
        date_contrat = self.contrat.date_signature.strftime('%d/%m/%Y')
        date_style = ParagraphStyle(
            'DateRight',
            parent=self.styles['CustomBody'],
            alignment=TA_RIGHT,
            fontSize=10
        )
        elements.append(Paragraph(f"Ouagadougou, {date_contrat}", date_style))
        elements.append(Spacer(1, 10))
        
        # Entre les parties (en bleu à la place du titre redondant) - titre en gras centré
        entre_style = ParagraphStyle(
            'EntreHeading',
            parent=self.styles['CustomHeading'],
            alignment=TA_CENTER,
            fontSize=14,
            textColor=colors.darkblue,
            spaceAfter=10
        )
        elements.append(Paragraph("Entre d'une part,", entre_style))
        elements.append(Spacer(1, 5))
        
        # Informations de l'agence - INFORMATIONS DYNAMIQUES EN GRAS
        agence_info = f"""L'Agence <b>KBIS IMMOBILIER</b> située au <b>secteur 26 Pissy</b> représentée, par <b>M. NIKIEMA PA MAMDOU</b> Tel <b>70-20-64-91</b>"""
        elements.append(Paragraph(agence_info, self.styles['CustomBody']))
        elements.append(Spacer(1, 10))
        
        # D'autre part
        elements.append(Paragraph("D'autre part (une copie de votre CNIB doit être jointe à la présente)", self.styles['CustomBody']))
        elements.append(Spacer(1, 5))
        
        # Informations du locataire - récupération des vraies données
        locataire = self.contrat.locataire
        
        # Récupérer les vraies données de la base
        locataire_nom = locataire.nom.upper() if locataire.nom else '....................'
        locataire_prenom = locataire.prenom.upper() if locataire.prenom else '....................'
        locataire_cnib = getattr(locataire, 'numero_cnib', None) or '....................'
        locataire_profession = getattr(locataire, 'profession', None) or '....................'
        locataire_adresse = locataire.adresse if locataire.adresse else '....................'
        locataire_tel = locataire.telephone if locataire.telephone else '....................'
        
        # Logique des civilités selon les données de la base
        civilité = self._determiner_civilite_locataire(locataire)
        
        locataire_info = f"""{civilité} <b>{locataire_nom} {locataire_prenom}</b> N° CNIB <b>{locataire_cnib}</b> Dénommée(é) le locataire<br/>
Profession <b>{locataire_profession}</b> adresse : <b>{locataire_adresse}</b> Tel : <b>{locataire_tel}</b>"""
        elements.append(Paragraph(locataire_info, self.styles['CustomBody']))
        elements.append(Spacer(1, 10))
        
        # Personne garant (avec pointillés pour champs vides)
        garant_nom = getattr(self.contrat, 'garant_nom', 'NOM DU GARANT')
        garant_profession = getattr(self.contrat, 'garant_profession', 'PROFESSION')
        garant_adresse = getattr(self.contrat, 'garant_adresse', 'ADRESSE')
        garant_tel = getattr(self.contrat, 'garant_telephone', 'TEL')
        
        # Remplacer les valeurs par défaut par des pointillés bien espacés
        if garant_nom == 'NOM DU GARANT':
            garant_nom = '....................'
        if garant_profession == 'PROFESSION':
            garant_profession = '....................'
        if garant_adresse == 'ADRESSE':
            garant_adresse = '....................'
        if garant_tel == 'TEL':
            garant_tel = '....................'
            
        garant_info = f"""Personne garant M, Mme, {garant_nom} profession {garant_profession} Adresse {garant_adresse} tel : {garant_tel}"""
        elements.append(Paragraph(garant_info, self.styles['CustomBody']))
        elements.append(Spacer(1, 10))
        
        # Informations de la propriété - récupération des vraies données
        propriete = self.contrat.propriete
        
        # Utiliser le numéro de l'unité locative si disponible, sinon le numéro de propriété
        propriete_numero = '....................'
        if hasattr(self.contrat, 'unite_locative') and self.contrat.unite_locative:
            # Pour les unités locatives, afficher le numéro de l'unité avec des détails
            propriete_numero = f"{self.contrat.unite_locative.numero_unite}"
            if hasattr(propriete, 'numero_propriete') and propriete.numero_propriete:
                propriete_numero = f"{propriete.numero_propriete} - {propriete_numero}"
        elif hasattr(propriete, 'numero_propriete') and propriete.numero_propriete:
            propriete_numero = propriete.numero_propriete
            
        propriete_ville = propriete.ville if propriete.ville else '....................'
        propriete_quartier = getattr(propriete, 'quartier', None) or '....................'
        
        # Informations complètes de la propriété avec ville et quartier - EN GRAS
        propriete_info = f"""pour la location de la maison n° <b>{propriete_numero}</b> Située à <b>{propriete_ville}</b>, quartier <b>{propriete_quartier}</b> Pour un loyer mensuel de : <b>{self.contrat.get_loyer_mensuel_formatted()}</b>"""
        elements.append(Paragraph(propriete_info, self.styles['CustomBody']))
        elements.append(Spacer(1, 10))
        
        # Reçu de la caution - EN GRAS
        caution_montant = self.contrat.get_depot_garantie_formatted()
        elements.append(Paragraph(f"<b>KBIS IMMOBILIER</b> reconnait avoir reçu la somme <b>{caution_montant}</b>", self.styles['CustomBody']))
        elements.append(Paragraph("Représentant <b>Trois (03) Mois de caution</b>.", self.styles['CustomBody']))
        elements.append(Spacer(1, 10))
        
        # Conditions de paiement - EN GRAS
        mois_debut = self.contrat.date_debut.strftime('%B %Y')
        elements.append(Paragraph(f"Le paiement mensuel du loyer commence à partir de la fin du mois de <b>{mois_debut.upper()}</b>", self.styles['CustomBody']))
        elements.append(Paragraph(f"<b>{civilité} {locataire_nom} {locataire_prenom}</b> s'engage à payer au plus tard le <b>03 du mois suivant</b>", self.styles['CustomBody']))
        elements.append(Spacer(1, 10))
        
        return elements

    def _create_rental_conditions(self):
        """Crée la section des conditions de location selon le nouveau format"""
        elements = []
        
        # Conditions de caution - CIVILITÉ CORRECTE
        civilite_locataire = self._determiner_civilite_locataire(self.contrat.locataire)
        elements.append(Paragraph(f"{civilite_locataire} {self.contrat.locataire.nom.upper()} {self.contrat.locataire.prenom.upper()} sachez que votre caution ne vous sera remboursé à la sortie qu'après avoir libéré la maison, l'avoir remis en état (peinture, plomberie etc.,) tel que décrété sur la page état de lieu résilier et payer vos factures de la SONABEL et de l'ONEA. Dans le cas contraire la caution servira à assurer ces frais et quitter les lieux.", self.styles['CustomBody']))
        elements.append(Spacer(1, 10))
        
        # Pouvoir d'expulsion
        elements.append(Paragraph("Il donne par la même occasion pouvoir à l'agence d'introduire une instance aux fins de l'expulsion du locataire sans aucune autre forme de préavis.", self.styles['CustomBody']))
        elements.append(Spacer(1, 10))
        
        # Décision et remise
        elements.append(Paragraph("Prenez librement vos décisions avant de signer le présent contrat car toute somme versée est remisée sans délai au bailleur. Encas de changement d'avis vous avez 48 heures pour annuler votre contrat auprès de votre agence. Passé ce délai, un (01) mois de loyer sera déduit de votre caution car les maisons confiées à l'agence sont à titre commerciale et ne doivent pas rester inoccupées.", self.styles['CustomBody']))
        elements.append(Spacer(1, 10))
        
        # Résiliation
        elements.append(Paragraph("Résiliation : Le locataire peut demander la résiliation de ce contrat avec un mois de preavis.la date de remise des clés est fixe au 01er du mois suivant pour permettre à votre remplaçant d'accéder à la maison, faute de quoi le mois entier sera dû.L'agence peut résilier ce contrat avec un préavis de trois mois. Le remboursement de la caution sera effectué dans les mêmes conditions.", self.styles['CustomBody']))
        elements.append(Spacer(1, 10))
        
        # Notes importantes
        elements.append(Paragraph("● NB : LES MAISONS SONT A PAYER AVANT DE CONSOMMER", self.styles['CustomBody']))
        elements.append(Paragraph("● LU ET APPROUVE BON POUR ACCORD", self.styles['CustomBody']))
        elements.append(Spacer(1, 15))
        
        return elements

    def _create_obligations(self):
        """Crée la section des obligations et conditions selon le nouveau format"""
        elements = []
        
        # Section des obligations générales (sans la personne garant) - TITRE EN BLEU CENTRÉ
        obligations_style = ParagraphStyle(
            'ObligationsHeading',
            parent=self.styles['CustomHeading'],
            alignment=TA_CENTER,
            fontSize=14,
            textColor=colors.darkblue,
            spaceAfter=10
        )
        elements.append(Paragraph("OBLIGATIONS ET CONDITIONS", obligations_style))
        elements.append(Spacer(1, 10))
        
        # Obligations générales
        obligations_text = """Le locataire s'engage à :
• Respecter les conditions de paiement convenues
• Maintenir la propriété en bon état
• Informer l'agence de tout problème
• Respecter les règles de vie en communauté"""
        
        elements.append(Paragraph(obligations_text, self.styles['CustomBody']))
        elements.append(Spacer(1, 15))
        
        return elements

    def _create_signatures(self):
        """Crée la section des signatures selon le nouveau format"""
        elements = []
        
        # Section Personne garant du paiement des loyers - MAINTENANT À LA FIN - EN BLEU CENTRÉ
        garant_style = ParagraphStyle(
            'GarantHeading',
            parent=self.styles['CustomHeading'],
            alignment=TA_CENTER,
            fontSize=14,
            textColor=colors.darkblue,
            spaceAfter=10
        )
        elements.append(Paragraph("● Personne garant du paiement des loyers", garant_style))
        elements.append(Spacer(1, 10))
        
        # Engagement du garant - INFORMATIONS DYNAMIQUES EN GRAS
        garant_nom = getattr(self.contrat, 'garant_nom', 'N/A')
        garant_profession = getattr(self.contrat, 'garant_profession', 'N/A')
        garant_adresse = getattr(self.contrat, 'garant_adresse', 'N/A')
        garant_telephone = getattr(self.contrat, 'garant_telephone', 'N/A')
        
        # Remplacer les valeurs par défaut par des pointillés
        if garant_nom == 'N/A':
            garant_nom = '....................'
        if garant_profession == 'N/A':
            garant_profession = '....................'
        if garant_adresse == 'N/A':
            garant_adresse = '....................'
        if garant_telephone == 'N/A':
            garant_telephone = '....................'
        
        # Calculer le montant de la responsabilité (6 mois de loyer)
        from decimal import Decimal
        try:
            loyer_decimal = Decimal(str(self.contrat.loyer_mensuel)) if self.contrat.loyer_mensuel else Decimal('0')
            responsabilite_montant = loyer_decimal * 6
            responsabilite_formatted = f"{responsabilite_montant:,.0f} F CFA"
        except:
            responsabilite_formatted = "...................."
        
        # Redéfinir le numéro de propriété pour cette section
        propriete = self.contrat.propriete
        propriete_numero = '....................'
        if hasattr(self.contrat, 'unite_locative') and self.contrat.unite_locative:
            propriete_numero = self.contrat.unite_locative.numero_unite
        elif hasattr(propriete, 'numero_propriete') and propriete.numero_propriete:
            propriete_numero = propriete.numero_propriete

        # Déterminer la civilité du garant et du locataire
        civilite_garant = self._determiner_civilite_garant(garant_nom)
        civilite_locataire = self._determiner_civilite_locataire(self.contrat.locataire)
        
        garant_engagement = f"""Je soussigné(e) <b>{civilite_garant} {garant_nom}</b> <b>Profession : {garant_profession}</b> <b>adresse : {garant_adresse}</b> <b>tel : {garant_telephone}</b>

Je me porte garant de la caution solitaire de <b>{civilite_locataire} {self.contrat.locataire.nom.upper()} {self.contrat.locataire.prenom.upper()}</b> <b>Tel : {self.contrat.locataire.telephone}</b> locataire de la maison n° <b>{propriete_numero}</b> Située à <b>{self.contrat.propriete.ville}</b> pour

Le paiement mensuel du loyer de <b>{self.contrat.get_loyer_mensuel_formatted()}</b> commence à partir de la fin du mois de <b>{self.contrat.date_debut.strftime('%B %Y').lower()}</b>

En cas de retard de payement du loyer supérieur à un mois. Je m'engage à payer leur correspondant à la place du locataire dans un délai d'une semaine dès que je serai avise du retard de payement. Ma responsabilité est limitée à six mois (06) mois de loyer, soit la somme de <b>{responsabilite_formatted}</b>

Le paiement sera effectué auprès de l'agence <b>KBIS IMMOBILIER</b> au secteur 26 PISSY. Situé sur la route du CMA DE PISSY tel : <b>+226 79.18.32.32./70.20.64.91/79.18.39.39/66..66.45.60</b>

Si en fin de Contrat, cette garantie a été utilisé, et si toute ou une partie de la caution doit être restitué au locataire après remise en état de la maison, elle sera remboursée à <b>{civilite_garant} {garant_nom}</b> (Personnes garante) du payement des loyers de <b>{civilite_locataire} {self.contrat.locataire.nom.upper()} {self.contrat.locataire.prenom.upper()}</b> Jusqu'à concurrence des sommes qu'elle aura versées et le reste sera remboursés au locataire.

Une copie de la CNIB du garant doit être jointe à la présente

Merci pour votre compréhension"""
        
        elements.append(Paragraph(garant_engagement, self.styles['CustomBody']))
        elements.append(Spacer(1, 10))
        
        # Section Engagement - EN BLEU CENTRÉ
        engagement_style = ParagraphStyle(
            'EngagementHeading',
            parent=self.styles['CustomHeading'],
            alignment=TA_CENTER,
            fontSize=14,
            textColor=colors.darkblue,
            spaceAfter=5
        )
        elements.append(Paragraph("Engagement", engagement_style))
        elements.append(Spacer(1, 5))
        
        # Texte d'engagement - INFORMATIONS DYNAMIQUES EN GRAS
        engagement_text = f"""Je soussigné(e) <b>{self.contrat.locataire.nom.upper()} {self.contrat.locataire.prenom.upper()}</b> reconnait avoir loué une maison, avec l'agence <b>KBIS IMMOBILIER</b> le <b>{self.contrat.date_signature.strftime('%d/%m/%Y')}</b> Et je m'engage à respecter le délai du payement de mon loyer prévu au plus tard le <b>03 du mois</b>, je reconnais que la réfection des différents points cites ci-dessus sont à ma charge au moment de libérer la maison.

<b>Lu et approuvé bon pour accord</b>"""
        
        elements.append(Paragraph(engagement_text, self.styles['CustomBody']))
        elements.append(Spacer(1, 5))
        
        # Tableau des signatures final
        signature_final_data = [
            ['L\'agence', 'le locataire', 'Personne Garant'],
            ['', '', ''],
            ['', '', ''],
        ]
        
        signature_final_table = Table(signature_final_data, colWidths=[5*cm, 5*cm, 5*cm])
        signature_final_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            # Suppression des traits (LINEBELOW) - remplacés par le pied de page dynamique
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        elements.append(signature_final_table)
        elements.append(Spacer(1, 10))
        
        # Date et lieu final
        date_contrat = self.contrat.date_signature.strftime('%d-%m-%Y')
        elements.append(Paragraph(f"Fait en deux exemplaires à Ouagadougou, le {date_contrat}", self.styles['CustomBody']))
        elements.append(Spacer(1, 10))
        
        # Ajouter le nom de l'utilisateur qui a généré le document
        if hasattr(self, 'user') and self.user:
            user_name = self.user.get_full_name() or self.user.username
            elements.append(Paragraph(f"<b>Document généré par :</b> {user_name}", self.styles['CustomBody']))
            elements.append(Spacer(1, 10))
        
        # Le pied de page sera géré par _add_footer_only (vrai pied de page)
        
        return elements
    
    def _create_etat_des_lieux(self):
        """Crée la section état des lieux avec le tableau fourni"""
        elements = []
        
        # Titre de la section - EN BLEU CENTRÉ
        etat_style = ParagraphStyle(
            'EtatHeading',
            parent=self.styles['CustomHeading'],
            alignment=TA_CENTER,
            fontSize=14,
            textColor=colors.darkblue,
            spaceAfter=15
        )
        elements.append(Paragraph("Etat des lieux", etat_style))
        elements.append(Spacer(1, 15))
        
        # Données du tableau état des lieux exactement comme dans les images (6 colonnes)
        etat_lieux_data = [
            ['N°', 'Description', 'OK', '', 'NON', ''],
            ['1', 'INDEXE DU COMPTEUR DE SONABEL', 'OUI', '', '', ''],
            ['2', 'INDEXE DU COMPTEUR DE L\'ONEA', 'OUI', '', '', ''],
            ['3', 'ETAT DE LA PEINTURE', 'OK', '', 'PASSABLE', ''],
            ['4', 'ETAT DE PEINTURE DES COUVERTURES', 'OK', '', 'PASSABLE', ''],
            ['5', 'PEINTURE DU PLAFOND', 'OK', '', 'PASSABLE', ''],
            ['6', 'ETAT DE CREMONE DE VITRE', 'OK', '', 'PASSABLE', ''],
            ['7', 'ETAT DE PRISE ELECTRIQUE', 'OK', '', 'PASSABLE', ''],
            ['8', 'NOMBRE DES CLES DU GRAND PORTAIL', 'OUI', '', 'NON', ''],
            ['9', 'NOMBRE DES CLES DE LA PORTE DU SALON', 'OUI', '', 'NON', ''],
            ['10', 'NOMBRE DES CLES ISO PLANES', 'OUI', '', 'NON', ''],
            ['11', 'PORTE RIDEAU', 'OUI', '', 'NON', ''],
            ['12', 'NOMBRE DES CLES DU PLACARD', 'OUI', '', 'NON', ''],
            ['13', 'NOMBRE DE REGLETTES', 'OK', '', 'NON', ''],
            ['14', 'NOMBRE DE VEILLEUSE', 'OK', '', 'NON', ''],
            ['15', 'NOMBRE DE VENTILATEURS', 'OK', '', 'NON', ''],
            ['16', 'ROBINETS DE LA CUISINE', 'OK', '', 'NON', ''],
            ['17', 'LES DES PLACARDS DE LA CUISINE', 'OK', '', 'NON', ''],
            ['18', 'ETAT DE LA SONNERIE', 'OK', '', 'NON', ''],
            ['19', 'LES WC', 'OK', '', 'NON', ''],
            ['20', 'LES LAVABOS', 'OK', '', 'NON', ''],
            ['21', 'LE MIROIR', 'OK', '', 'NON', ''],
            ['22', 'FLEXIBLE DE DOUCHE\n(COLONNE)', 'OK', '', 'NON', ''],
            ['23', 'LES ACCESSOIRES\n(porte savon, porte serviette,\nporte papier de toilette)', 'OK', '', 'NON', ''],
            ['24', 'LAMPES SANITAIRE', 'OK', '', 'NON', ''],
            ['25', 'CHAUFFE-EAU', 'OK', '', 'NON', ''],
            ['26', 'CLIMATISEUR\n(entretien)', 'OK', '', 'NON', ''],
        ]
        
        # Créer le tableau exactement comme dans les images (6 colonnes)
        etat_table = Table(etat_lieux_data, colWidths=[1*cm, 8*cm, 1.5*cm, 1*cm, 1.5*cm, 1*cm])
        etat_table.setStyle(TableStyle([
            # Style général
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            
            # En-tête
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            
            # Bordures
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('LINEBELOW', (0, 0), (-1, 0), 2, colors.black),
            
            # Padding réduit pour optimiser l'affichage
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('LEFTPADDING', (0, 0), (-1, -1), 3),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3),
            
            # Alignement des colonnes exactement comme dans les images
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),  # N°
            ('ALIGN', (2, 1), (2, -1), 'CENTER'),  # OK
            ('ALIGN', (4, 1), (4, -1), 'CENTER'),  # NON
            
            # Retour à la ligne automatique pour éviter le débordement
            ('WORDWRAP', (0, 0), (-1, -1), 'CJK'),  # Active le retour à la ligne automatique
        ]))
        
        elements.append(etat_table)
        elements.append(Spacer(1, 10))
        
        # Section Observation (rectangle simple - une seule colonne)
        elements.append(Paragraph("Observation", self.styles['CustomHeading']))
        elements.append(Spacer(1, 10))
        
        # Zone d'observation (rectangle simple - une seule ligne)
        observation_data = [
            [''],
        ]
        
        observation_table = Table(observation_data, colWidths=[16*cm])
        observation_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 20),
            ('TOPPADDING', (0, 0), (-1, -1), 20),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ]))
        
        elements.append(observation_table)
        
        return elements

    def _add_footer_only(self, canvas_obj, doc):
        """Ajoute uniquement le pied de page (sans en-tête) sur les pages suivantes"""
        import os
        
        # Dimensions de la page
        page_width, page_height = A4
        
        # === PIED DE PAGE DYNAMIQUE COLLÉ EN BAS ===
        # Récupérer le pied de page personnalisé depuis la configuration
        if self.config_entreprise:
            pied_page_text = getattr(self.config_entreprise, 'pied_page_personnalise', '')
            if pied_page_text:
                # Utiliser le pied de page personnalisé
                canvas_obj.setFillColor(colors.black)
                canvas_obj.setFont("Helvetica", 8)
                
                # Centrer le texte en bas de page
                text_width = canvas_obj.stringWidth(pied_page_text, "Helvetica", 8)
                text_x = (page_width - text_width) / 2
                text_y = 0.3*cm  # Collé en bas
                
                canvas_obj.drawString(text_x, text_y, pied_page_text)
            else:
                # Pied de page par défaut
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

    def _add_header_only(self, canvas_obj, doc):
        """Ajoute uniquement l'en-tête sur la première page (sans pied de page)"""
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

    def _add_no_footer(self, canvas_obj, doc):
        """N'ajoute rien sur les pages intermédiaires (pas de pied de page)"""
        # Ne rien ajouter - pages intermédiaires sans pied de page
        pass

    def _add_no_header_footer(self, canvas_obj, doc):
        """N'ajoute rien sur la première page (pas d'en-tête ni de pied de page)"""
        # Ne rien ajouter - première page sans en-tête ni pied de page
        pass

    def _add_footer_last_page_only(self, canvas_obj, doc):
        """Ajoute uniquement le pied de page sur la dernière page, rien sur les pages intermédiaires"""
        import os
        
        # Dimensions de la page
        page_width, page_height = A4
        
        # Vérifier si c'est la dernière page
        if hasattr(doc, 'page') and hasattr(doc, 'pages'):
            if doc.page == doc.pages:  # Dernière page seulement
                # === PIED DE PAGE DYNAMIQUE ===
                if self.config_entreprise:
                    pied_page_text = getattr(self.config_entreprise, 'pied_page_personnalise', '')
                    if not pied_page_text:
                        # Pied de page par défaut centré
                        pied_page_text = f"{self.config_entreprise.nom_entreprise} | {self.config_entreprise.get_adresse_complete()} | Tel: {self.config_entreprise.telephone} | Email: {self.config_entreprise.email}"
                    
                    # Utiliser le pied de page
                    canvas_obj.setFillColor(colors.black)
                    canvas_obj.setFont("Helvetica", 8)
                    
                    # Centrer le texte en bas de page (remplace les traits)
                    text_width = canvas_obj.stringWidth(pied_page_text, "Helvetica", 8)
                    text_x = (page_width - text_width) / 2
                    text_y = 0.3*cm  # Position très bas pour remplacer les traits
                    
                    canvas_obj.drawString(text_x, text_y, pied_page_text)
            # Si ce n'est pas la dernière page, ne rien ajouter (pages intermédiaires vides)
    
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

    def _determiner_civilite_locataire(self, locataire):
        """Détermine la civilité appropriée selon les données de la base"""
        # Vérifier si c'est une société/personne morale
        if hasattr(locataire, 'type_personne') and locataire.type_personne == 'societe':
            return locataire.nom.upper() if locataire.nom else 'SOCIÉTÉ'
        
        # Vérifier si c'est une personne physique
        if hasattr(locataire, 'civilite'):
            civilité = locataire.civilite
            if civilité == 'M':
                return 'M.'
            elif civilité == 'Mme':
                return 'Mme'
            elif civilité == 'Mlle':
                return 'Mlle'
            elif civilité == 'Mademoiselle':
                return 'Mlle'
        
        # Vérifier le genre si disponible
        if hasattr(locataire, 'genre'):
            if locataire.genre == 'M':
                return 'M.'
            elif locataire.genre == 'F':
                # Par défaut, utiliser Mme pour les femmes
                return 'Mme'
        
        # Vérifier le prénom pour deviner le genre (approximation)
        if locataire.prenom:
            prenom_lower = locataire.prenom.lower()
            # Noms typiquement féminins
            noms_feminins = ['marie', 'marie-claire', 'fatou', 'aminata', 'aicha', 'kadiatou', 'mariama']
            if any(nom in prenom_lower for nom in noms_feminins):
                return 'Mme'
        
        # Par défaut, utiliser M.
        return 'M.'
    
    def _determiner_civilite_garant(self, garant_nom):
        """Détermine la civilité appropriée pour le garant"""
        # Pour le garant, on utilise une logique simple basée sur le nom
        # Si le nom contient des mots-clés de société, on l'affiche tel quel
        if garant_nom and any(mot in garant_nom.upper() for mot in ['SARL', 'SA', 'SOCIÉTÉ', 'SOCIETE', 'ENTREPRISE', 'COMPANY', 'LTD']):
            return garant_nom.upper()
        
        # Sinon, on utilise M. par défaut (le garant est généralement un homme dans ce contexte)
        return 'M.'


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

    def generate_recu_pdf(self, use_cache=True, user=None):
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
        
        # Stocker l'utilisateur pour l'affichage
        self.user = user
        
        # Créer le document avec des marges optimisées pour éviter le chevauchement
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=1.5*cm,
            leftMargin=1.5*cm,
            topMargin=4*cm,  # Marge supérieure augmentée pour éviter le chevauchement
            bottomMargin=1*cm  # Marge inférieure pour le pied de page
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
        
        # === PIED DE PAGE DYNAMIQUE COLLÉ EN BAS ===
        # Récupérer le pied de page personnalisé depuis la configuration
        if self.config_entreprise:
            pied_page_text = getattr(self.config_entreprise, 'pied_page_personnalise', '')
            if pied_page_text:
                # Utiliser le pied de page personnalisé
                canvas_obj.setFillColor(colors.black)
                canvas_obj.setFont("Helvetica", 8)
                
                # Centrer le texte en bas de page
                text_width = canvas_obj.stringWidth(pied_page_text, "Helvetica", 8)
                text_x = (page_width - text_width) / 2
                text_y = 0.3*cm  # Collé en bas
                
                canvas_obj.drawString(text_x, text_y, pied_page_text)
            else:
                # Pied de page par défaut
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
        
        # Ajouter un tableau séparé pour les informations sur les mois réglés
        # Afficher les mois réglés pour les avances ET pour les paiements de loyer normaux
        if mois_couverts_info:
            elements.append(Spacer(1, 10))
            
            # Préparer les informations sur les mois couverts avec gestion des retours à la ligne
            mois_liste = mois_couverts_info.get('mois_liste', [])
            if mois_liste:
                # Gérer les retours à la ligne pour éviter le débordement
                mois_texte_complet = ', '.join(mois_liste)
                # Diviser le texte en lignes de 40 caractères maximum pour éviter le débordement
                if len(mois_texte_complet) > 40:
                    mots = mois_texte_complet.split(', ')
                    lignes = []
                    ligne_actuelle = []
                    longueur_actuelle = 0
                    
                    for mot in mots:
                        if longueur_actuelle + len(mot) + 2 > 40 and ligne_actuelle:  # +2 pour ", "
                            lignes.append(', '.join(ligne_actuelle))
                            ligne_actuelle = [mot]
                            longueur_actuelle = len(mot)
                        else:
                            ligne_actuelle.append(mot)
                            longueur_actuelle += len(mot) + 2 if ligne_actuelle else 0
                    
                    if ligne_actuelle:
                        lignes.append(', '.join(ligne_actuelle))
                    
                    # Utiliser des retours à la ligne pour le PDF
                    mois_info = f"{mois_couverts_info['nombre']} mois ({'<br/>'.join(lignes)})"
                else:
                    mois_info = f"{mois_couverts_info['nombre']} mois ({mois_texte_complet})"
            else:
                mois_info = f"{mois_couverts_info['nombre']} mois ({mois_couverts_info['mois_texte']})"
            
            # Convertir les mois en français
            mois_debut_fr = self._convertir_mois_francais(mois_couverts_info['date_debut'])
            mois_fin_fr = self._convertir_mois_francais(mois_couverts_info['date_fin'])
            
            # Si c'est un seul mois, afficher seulement ce mois
            if mois_couverts_info['date_debut'] == mois_couverts_info['date_fin']:
                periode_info = f"{mois_debut_fr} {mois_couverts_info['date_debut'].year}"
            else:
                periode_info = f"{mois_debut_fr} {mois_couverts_info['date_debut'].year} à {mois_fin_fr} {mois_couverts_info['date_fin'].year}"
            
            # Créer un tableau avec cellules fusionnées pour les informations sur l'avance
            # Utiliser Paragraph pour gérer les retours à la ligne
            avance_data = [
                ['INFORMATIONS SUR L\'AVANCE DE LOYER'],
                ['Mois couverts:', Paragraph(mois_info, self.styles['CustomBody'])],
                ['Période de couverture:', Paragraph(periode_info, self.styles['CustomBody'])]
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
        """Calcule les mois couverts par l'avance de loyer ou les mois réglés"""
        # Calculer les mois même pour les paiements de loyer normaux
        if not self.contrat.loyer_mensuel or self.contrat.loyer_mensuel <= 0:
            return None
        
        try:
            # Utiliser le service corrigé pour calculer les mois couverts
            from paiements.services_avance_corrige import ServiceAvanceCorrige
            
            # Calculer les mois même si pas d'avance (pour les paiements de loyer normaux)
            montant_a_calculer = self.contrat.avance_loyer if self.contrat.avance_loyer else self.contrat.loyer_mensuel
            
            mois_couverts_data = ServiceAvanceCorrige.calculer_mois_couverts_correct(
                self.contrat, montant_a_calculer, None
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
        
        # Ajouter le nom de l'utilisateur qui a généré le document
        if hasattr(self, 'user') and self.user:
            user_name = self.user.get_full_name() or self.user.username
            elements.append(Paragraph(f"<b>Document généré par :</b> {user_name}", self.styles['CustomBody']))
            elements.append(Spacer(1, 10))
        
        return elements


class ResiliationPDFService:
    def __init__(self, resiliation, user=None):
        self.resiliation = resiliation
        self.user = user
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

    def generate_resiliation_pdf(self, use_cache=True, user=None):
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
        
        # Créer le document avec des marges optimisées pour éviter le chevauchement
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=1*cm,
            leftMargin=1*cm,
            topMargin=3.5*cm,  # Marge supérieure réduite
            bottomMargin=0.5*cm  # Marge inférieure très réduite
        )
        
        # Construction du contenu du PDF
        story = []
        
        # Titre principal de la résiliation
        story.append(Paragraph(
            "AVIS DE RÉSILIATION DE CONTRAT",
            self.styles['CustomTitle']
        ))
        story.append(Spacer(1, 10))  # Réduit de 20 à 10
        
        # Informations de la résiliation
        story.extend(self._create_resiliation_info())
        story.append(Spacer(1, 10))  # Réduit de 20 à 10
        
        # Informations du contrat
        story.extend(self._create_contract_info())
        story.append(Spacer(1, 10))  # Réduit de 20 à 10
        
        # Motifs et conditions
        story.extend(self._create_termination_details())
        story.append(Spacer(1, 10))  # Réduit de 20 à 10
        
        # Signatures (locataire et agent immobilier uniquement)
        story.extend(self._create_signatures())
        
        # Ajouter le footer comme contenu à la fin (apparaîtra seulement sur la dernière page)
        story.extend(self._create_footer_content())
        
        # Génération du PDF avec en-tête uniquement sur la première page
        doc.build(story, onFirstPage=self._add_first_page_header_footer, onLaterPages=self._add_later_pages_header_footer)
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

    def _add_first_page_header_footer(self, canvas_obj, doc):
        """Ajoute l'en-tête uniquement sur la première page (pas de pied de page)"""
        import os
        from django.conf import settings
        
        # Dimensions de la page
        page_width, page_height = A4
        
        # === EN-TÊTE AVEC IMAGE STATIQUE (PREMIÈRE PAGE UNIQUEMENT) ===
        try:
            # Chemin de l'image d'en-tête
            image_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'enteteEnImage.png')
            
            if os.path.exists(image_path):
                # Hauteur de l'image (3.5 cm pour correspondre à l'en-tête)
                header_height = 3.5*cm
                
                # Calculer la largeur de l'image en conservant le ratio
                image_width = page_width
                
                # Dessiner l'image d'en-tête
                canvas_obj.drawImage(
                    image_path,
                    0, page_height - header_height,  # Position
                    image_width, header_height,     # Dimensions
                    preserveAspectRatio=True,
                    anchor='n'
                )
                
                # Dessiner une bordure en bas de l'en-tête
                canvas_obj.setStrokeColor(colors.darkred)
                canvas_obj.setLineWidth(2)
                canvas_obj.line(0, page_height - header_height, page_width, page_height - header_height)
            else:
                # Fallback si l'image n'existe pas
                canvas_obj.setFillColor(colors.lightcoral)
                canvas_obj.rect(0, page_height - 3.5*cm, page_width, 3.5*cm, fill=1, stroke=0)
                
                if self.config_entreprise:
                    canvas_obj.setFillColor(colors.white)
                    canvas_obj.setFont("Helvetica-Bold", 16)
                    canvas_obj.drawString(2*cm, page_height - 2*cm, self.config_entreprise.nom_entreprise)
                    
        except Exception as e:
            # En cas d'erreur, utiliser un en-tête simple
            canvas_obj.setFillColor(colors.lightcoral)
            canvas_obj.rect(0, page_height - 3.5*cm, page_width, 3.5*cm, fill=1, stroke=0)
    
    def _add_later_pages_header_footer(self, canvas_obj, doc):
        """Ajoute le footer en bas de la dernière page uniquement"""
        # Initialiser le compteur de pages au début
        if not hasattr(self, '_total_pages'):
            self._total_pages = doc.page
        
        # Mettre à jour le total de pages au fur et à mesure
        if doc.page > self._total_pages:
            self._total_pages = doc.page
        
        # Dessiner le footer seulement sur la dernière page
        # Note: doc.page est le numéro de la page ACTUELLE, mais on ne connaît pas encore le total final
        # Donc on ne dessine PAS le footer ici, on le laissera dans le contenu
        pass
    
    def _add_footer(self, canvas_obj, doc):
        """Ajoute le pied de page avec les infos de configuration"""
        page_width = A4[0]
        footer_height = 2*cm
        
        # Fond du pied de page
        canvas_obj.setFillColor(colors.lightgrey)
        canvas_obj.rect(0, 0, page_width, footer_height, fill=1, stroke=0)
        
        # Bordure en haut du pied de page
        canvas_obj.setStrokeColor(colors.grey)
        canvas_obj.setLineWidth(1)
        canvas_obj.line(0, footer_height, page_width, footer_height)
        
        if self.config_entreprise:
            canvas_obj.setFillColor(colors.darkgrey)
            
            # Nom de l'entreprise
            canvas_obj.setFont("Helvetica-Bold", 8)
            canvas_obj.drawString(2*cm, 1.3*cm, self.config_entreprise.nom_entreprise)
            
            # Contact
            if self.config_entreprise.telephone or self.config_entreprise.email:
                canvas_obj.setFont("Helvetica", 7)
                contact_parts = []
                if self.config_entreprise.telephone:
                    contact_parts.append(f"Tél: {self.config_entreprise.telephone}")
                if self.config_entreprise.email:
                    contact_parts.append(f"Email: {self.config_entreprise.email}")
                canvas_obj.drawString(2*cm, 0.8*cm, " | ".join(contact_parts))
            
            # Adresse
            if self.config_entreprise.adresse_ligne1:
                canvas_obj.setFont("Helvetica", 7)
                adresse_complete = self.config_entreprise.get_adresse_complete()
                canvas_obj.drawString(2*cm, 0.3*cm, adresse_complete)
            
            # Numéro de page à gauche
            canvas_obj.setFont("Helvetica-Bold", 8)
            canvas_obj.drawString(2*cm, 0.3*cm, f"Page {doc.page}")
            
            # Informations de génération à droite (avec nom d'utilisateur)
            if self.user:
                user_name = self.user.get_full_name() or self.user.username
                canvas_obj.setFont("Helvetica", 7)
                canvas_obj.drawRightString(page_width - 2*cm, 0.8*cm, f"Document généré par: {user_name}")
            canvas_obj.setFont("Helvetica", 7)
            canvas_obj.drawRightString(page_width - 2*cm, 0.3*cm, f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}")
    
    def _draw_footer_on_canvas(self, canvas_obj, doc):
        """Alias pour _add_footer pour cohérence avec les appels"""
        self._add_footer(canvas_obj, doc)

    def _create_footer_content(self):
        """Crée le pied de page avec les informations de configuration et le nom de l'utilisateur"""
        elements = []
        
        # Espace minimal avant le footer pour coller aux signatures
        elements.append(Spacer(1, 5))
        
        # Informations de l'entreprise compactes
        if self.config_entreprise:
            # Nom de l'entreprise et contact sur une ligne
            contact_parts = [self.config_entreprise.nom_entreprise]
            if self.config_entreprise.telephone:
                contact_parts.append(f"Tél: {self.config_entreprise.telephone}")
            if self.config_entreprise.email:
                contact_parts.append(f"Email: {self.config_entreprise.email}")
            
            elements.append(Paragraph(
                " | ".join(contact_parts),
                ParagraphStyle(
                    'FooterCompact',
                    parent=self.styles['Normal'],
                    fontSize=7,
                    alignment=TA_CENTER
                )
            ))
            
            # Adresse compacte
            if self.config_entreprise.adresse_ligne1:
                elements.append(Paragraph(
                    self.config_entreprise.get_adresse_complete(),
                    ParagraphStyle(
                        'FooterAddress',
                        parent=self.styles['Normal'],
                        fontSize=7,
                        alignment=TA_CENTER
                    )
                ))
        
        # Informations de génération compactes
        if self.user:
            user_name = self.user.get_full_name() or self.user.username
            elements.append(Paragraph(
                f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')} par {user_name}",
                ParagraphStyle(
                    'FooterGeneration',
                    parent=self.styles['Normal'],
                    fontSize=6,
                    alignment=TA_CENTER
                )
            ))
        else:
            elements.append(Paragraph(
                f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}",
                ParagraphStyle(
                    'FooterGeneration',
                    parent=self.styles['Normal'],
                    fontSize=6,
                    alignment=TA_CENTER
                )
            ))
        
        return elements
    
    def _create_signatures(self):
        """Crée la section des signatures (locataire et agent immobilier uniquement)"""
        elements = []
        
        elements.append(Paragraph("SIGNATURES", self.styles['CustomHeading']))
        elements.append(Spacer(1, 10))  # Réduit de 20 à 10
        
        # Tableau des signatures compact
        signature_data = [
            [Paragraph('<b>Signature du locataire</b>', self.styles['CustomBody']), 
             Paragraph('<b>Signature de l\'agent immobilier</b>', self.styles['CustomBody'])],
            ['', ''],  # Lignes de signature
            [Paragraph(f"{self.resiliation.contrat.locataire.nom} {self.resiliation.contrat.locataire.prenom}", self.styles['CustomBody']), 
             Paragraph(f"{self.config_entreprise.nom_entreprise if self.config_entreprise else 'KBIS IMMOBILIER'}", self.styles['CustomBody'])],
            ['Date : _________________', 'Date : _________________']
        ]
        
        signature_table = Table(signature_data, colWidths=[8*cm, 8*cm])
        signature_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTNAME', (0, 1), (0, 1), 'Helvetica'),  # Lignes de signature
            ('FONTNAME', (0, 2), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('LINEBELOW', (0, 1), (0, 1), 2, colors.black),  # Ligne de signature épaisse
            ('LINEBELOW', (1, 1), (1, 1), 2, colors.black),  # Ligne de signature épaisse
            ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey),
        ]))
        
        elements.append(signature_table)
        elements.append(Spacer(1, 5))  # Espace minimal pour coller le footer
        
        return elements
    
    def _create_resiliation_info(self):
        """Crée la section des informations de résiliation"""
        elements = []
        
        elements.append(Paragraph("INFORMATIONS DE LA RÉSILIATION", self.styles['CustomHeading']))
        
        # Tableau des informations condensé
        data = [
            ['Date:', self.resiliation.date_resiliation.strftime('%d/%m/%Y')],
            ['Type:', self.resiliation.get_type_resiliation_display()],
            ['Motif:', self.resiliation.motif_resiliation[:40] + '...' if len(self.resiliation.motif_resiliation) > 40 else self.resiliation.motif_resiliation],
        ]
        
        table = Table(data, colWidths=[3*cm, 9*cm])
        table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
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
        
        # Tableau condensé avec informations essentielles
        data_contrat = [
            ['Contrat:', contrat.numero_contrat],
            ['Propriété:', contrat.propriete.titre[:30] + '...' if len(contrat.propriete.titre) > 30 else contrat.propriete.titre],
            ['Locataire:', f"{contrat.locataire.nom} {contrat.locataire.prenom}"],
            ['Loyer:', contrat.get_loyer_mensuel_formatted()],
        ]
        
        table_contrat = Table(data_contrat, colWidths=[3*cm, 9*cm])
        table_contrat.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
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
        elements.append(Spacer(1, 15))
        
    def _create_termination_details(self):
        """Crée la section des détails de la résiliation"""
        elements = []
        
        elements.append(Paragraph("DÉTAILS DE LA RÉSILIATION", self.styles['CustomHeading']))
        
        # Motifs de résiliation (condensé)
        if self.resiliation.motif_resiliation:
            elements.append(Paragraph(
                f"<b>Motif :</b> {self.resiliation.motif_resiliation[:60]}{'...' if len(self.resiliation.motif_resiliation) > 60 else ''}",
                self.styles['CustomBody']
            ))
        
        # Conditions de sortie (version courte)
        conditions_text = """
        <b>Conditions :</b> Libération des lieux, état des lieux, restitution caution après déduction dommages.
        """
        
        elements.append(Paragraph(conditions_text, self.styles['CustomBody']))
        elements.append(Spacer(1, 8))
        
        # SECTION DES TRAVAUX ET DÉPENSES + RÉSUMÉ FINANCIER (tableau unifié)
        elements.append(Paragraph("TRAVAUX ET RÉSUMÉ FINANCIER", self.styles['CustomHeading']))
        elements.append(Spacer(1, 5))
        
        # Créer un tableau unifié
        all_data = []
        
        # En-tête
        all_data.append([Paragraph('<b>DESCRIPTION</b>', self.styles['CustomBody']), Paragraph('<b>MONTANT</b>', self.styles['CustomBody'])])
        
        # Ligne de séparation "TRAVAUX"
        all_data.append([Paragraph('<b>TRAVAUX ET DÉPENSES</b>', self.styles['CustomBody']), Paragraph('', self.styles['CustomBody'])])
        
        # Dépenses dynamiques
        has_travaux = False
        for depense in self.resiliation.depenses.all():
            all_data.append([
                Paragraph(depense.description, self.styles['CustomBody']), 
                Paragraph(f"{float(depense.montant):,.0f} F CFA", self.styles['CustomBody'])
            ])
            has_travaux = True
        
        if not has_travaux:
            all_data.append([Paragraph('<i>Aucun travail effectué</i>', self.styles['CustomBody']), Paragraph('', self.styles['CustomBody'])])
        
        # Ligne de séparation "RÉSUMÉ FINANCIER"
        all_data.append([Paragraph('<b>RÉSUMÉ FINANCIER</b>', self.styles['CustomBody']), Paragraph('', self.styles['CustomBody'])])
        
        # Résumé financier
        caution_versee = self.resiliation.recuperer_caution_contractuelle()
        total_depenses = self.resiliation.calculer_total_depenses()
        solde_restant = caution_versee - total_depenses
        
        all_data.append([Paragraph('Caution versée', self.styles['CustomBody']), Paragraph(f"{float(caution_versee):,.0f} F CFA", self.styles['CustomBody'])])
        all_data.append([Paragraph('Total dépenses', self.styles['CustomBody']), Paragraph(f"{float(total_depenses):,.0f} F CFA", self.styles['CustomBody'])])
        all_data.append([Paragraph('<b>Solde restant</b>', self.styles['CustomBody']), Paragraph(f"<b>{float(solde_restant):,.0f} F CFA</b>", self.styles['CustomBody'])])
        
        # Créer le tableau avec style optimisé
        table = Table(all_data, colWidths=[7*cm, 5*cm])
        table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (1, 0), colors.lightblue),
            ('TEXTCOLOR', (0, 0), (1, 0), colors.black),
            ('BACKGROUND', (0, 1), (1, 1), colors.lightgrey),  # TRAVAUX ET DÉPENSES
            ('BACKGROUND', (0, -3), (1, -3), colors.lightgrey),  # RÉSUMÉ FINANCIER
        ]))
        
        elements.append(table)
        
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
