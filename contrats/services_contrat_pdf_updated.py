#!/usr/bin/env python
"""
Service de génération PDF pour les contrats avec templates mis à jour
"""

import logging
from datetime import datetime
from decimal import Decimal
from django.utils import timezone
from django.template.loader import render_to_string
from django.http import HttpResponse
from io import BytesIO

from core.models import ConfigurationEntreprise
from .models import Contrat

logger = logging.getLogger(__name__)


class ContratPDFServiceUpdated:
    """Service pour la génération de PDF de contrats avec templates mis à jour."""
    
    def __init__(self, contrat):
        self.contrat = contrat
        self.logger = logger
    
    def generate_contrat_pdf(self):
        """
        Génère un PDF de contrat avec le template mis à jour.
        
        Returns:
            BytesIO: PDF généré
        """
        try:
            # Récupérer la configuration de l'entreprise
            config = ConfigurationEntreprise.get_configuration_active()
            
            # Préparer les données pour le template
            donnees_contrat = self._preparer_donnees_contrat()
            
            # Convertir l'image en base64
            import os
            import base64
            from django.conf import settings
            
            image_path = os.path.join(settings.STATIC_ROOT, 'images', 'enteteEnImage.png')
            if not os.path.exists(image_path):
                image_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'enteteEnImage.png')
            
            image_base64 = ""
            if os.path.exists(image_path):
                with open(image_path, 'rb') as img_file:
                    image_data = base64.b64encode(img_file.read()).decode('utf-8')
                    image_base64 = f"data:image/png;base64,{image_data}"
            
            # Générer le HTML avec le template
            html_content = render_to_string(
                'contrats/contrat_pdf_updated.html',
                {
                    'contrat': self.contrat,
                    'donnees': donnees_contrat,
                    'config': config,
                    'image_base64': image_base64,
                    'date_generation': timezone.now(),
                }
            )
            
            # Générer le PDF avec xhtml2pdf
            from xhtml2pdf import pisa
            pdf_buffer = BytesIO()
            pisa_status = pisa.CreatePDF(html_content, dest=pdf_buffer)
            
            if pisa_status.err:
                self.logger.error("Erreur lors de la génération PDF: %s", pisa_status.err)
                raise Exception(f"Erreur lors de la génération PDF: {pisa_status.err}")
            
            return pdf_buffer
            
        except Exception as e:
            self.logger.error("Erreur lors de la génération PDF du contrat: %s", str(e))
            raise
    
    def generate_etat_lieux_pdf(self):
        """
        Génère un PDF d'état des lieux.
        
        Returns:
            BytesIO: PDF généré
        """
        try:
            # Récupérer la configuration de l'entreprise
            config = ConfigurationEntreprise.get_configuration_active()
            
            # Générer le HTML avec le template
            html_content = render_to_string(
                'contrats/etat_lieux_pdf.html',
                {
                    'contrat': self.contrat,
                    'config': config,
                    'date_generation': timezone.now(),
                }
            )
            
            # Générer le PDF avec xhtml2pdf
            from xhtml2pdf import pisa
            pdf_buffer = BytesIO()
            pisa_status = pisa.CreatePDF(html_content, dest=pdf_buffer)
            
            if pisa_status.err:
                self.logger.error("Erreur lors de la génération PDF état des lieux: %s", pisa_status.err)
                raise Exception(f"Erreur lors de la génération PDF: {pisa_status.err}")
            
            return pdf_buffer
            
        except Exception as e:
            self.logger.error("Erreur lors de la génération PDF état des lieux: %s", str(e))
            raise
    
    def generate_garantie_pdf(self):
        """
        Génère un PDF de garantie.
        
        Returns:
            BytesIO: PDF généré
        """
        try:
            # Récupérer la configuration de l'entreprise
            config = ConfigurationEntreprise.get_configuration_active()
            
            # Générer le HTML avec le template
            html_content = render_to_string(
                'contrats/garantie_pdf.html',
                {
                    'contrat': self.contrat,
                    'config': config,
                    'date_generation': timezone.now(),
                }
            )
            
            # Générer le PDF avec xhtml2pdf
            from xhtml2pdf import pisa
            pdf_buffer = BytesIO()
            pisa_status = pisa.CreatePDF(html_content, dest=pdf_buffer)
            
            if pisa_status.err:
                self.logger.error("Erreur lors de la génération PDF garantie: %s", pisa_status.err)
                raise Exception(f"Erreur lors de la génération PDF: {pisa_status.err}")
            
            return pdf_buffer
            
        except Exception as e:
            self.logger.error("Erreur lors de la génération PDF garantie: %s", str(e))
            raise
    
    def _preparer_donnees_contrat(self):
        """Prépare les données du contrat pour le template."""
        # Récupérer les montants numériques
        loyer_numerique = self._get_numeric_value(self.contrat.loyer_mensuel)
        depot_numerique = self._get_numeric_value(self.contrat.depot_garantie)
        
        # Calculer le montant maximum de garantie (6 mois de loyer)
        montant_garantie_max = loyer_numerique * 6
        
        # Préparer les données
        donnees = {
            'loyer_mensuel_numerique': str(int(loyer_numerique)),
            'loyer_mensuel_texte': self._nombre_en_lettres(int(loyer_numerique)),
            'depot_garantie_numerique': str(int(depot_numerique)),
            'depot_garantie_texte': self._nombre_en_lettres(int(depot_numerique)),
            'montant_garantie_max': str(int(montant_garantie_max)),
            'montant_garantie_max_texte': self._nombre_en_lettres(int(montant_garantie_max)),
            'nombre_mois_caution': self._calculer_mois_caution(depot_numerique, loyer_numerique),
            'mois_debut_paiement': self._get_mois_debut_paiement(),
        }
        
        return donnees
    
    def _get_numeric_value(self, value_str):
        """Convertit une chaîne en valeur numérique."""
        if not value_str:
            return 0
        try:
            # Nettoyer la chaîne (enlever les espaces, virgules, etc.)
            cleaned = str(value_str).replace(' ', '').replace(',', '').replace('F', '').replace('CFA', '')
            return float(cleaned) if cleaned else 0
        except (ValueError, TypeError):
            return 0
    
    def _nombre_en_lettres(self, nombre):
        """Convertit un nombre en lettres (version simplifiée)."""
        if nombre == 0:
            return "ZÉRO"
        
        # Dictionnaire des nombres de base
        nombres = {
            0: "zéro", 1: "un", 2: "deux", 3: "trois", 4: "quatre", 5: "cinq",
            6: "six", 7: "sept", 8: "huit", 9: "neuf", 10: "dix",
            11: "onze", 12: "douze", 13: "treize", 14: "quatorze", 15: "quinze",
            16: "seize", 17: "dix-sept", 18: "dix-huit", 19: "dix-neuf",
            20: "vingt", 30: "trente", 40: "quarante", 50: "cinquante",
            60: "soixante", 70: "soixante-dix", 80: "quatre-vingt", 90: "quatre-vingt-dix",
            100: "cent", 1000: "mille", 1000000: "million"
        }
        
        if nombre in nombres:
            return nombres[nombre].upper()
        
        # Conversion simplifiée pour les montants courants
        if nombre < 100:
            dizaines = (nombre // 10) * 10
            unites = nombre % 10
            if dizaines in nombres and unites in nombres:
                if unites == 0:
                    return nombres[dizaines].upper()
                else:
                    return f"{nombres[dizaines].upper()}-{nombres[unites].upper()}"
        
        # Pour les montants plus élevés, utiliser une conversion de base
        if nombre >= 1000:
            milliers = nombre // 1000
            reste = nombre % 1000
            if milliers == 1:
                result = "MILLE"
            else:
                result = f"{self._nombre_en_lettres(milliers)} MILLE"
            
            if reste > 0:
                result += f" {self._nombre_en_lettres(reste)}"
            return result
        
        if nombre >= 100:
            centaines = nombre // 100
            reste = nombre % 100
            if centaines == 1:
                result = "CENT"
            else:
                result = f"{self._nombre_en_lettres(centaines)} CENT"
            
            if reste > 0:
                result += f" {self._nombre_en_lettres(reste)}"
            return result
        
        return str(nombre)
    
    def _calculer_mois_caution(self, depot, loyer):
        """Calcule le nombre de mois de caution."""
        if loyer == 0:
            return "Zéro"
        
        mois = int(depot / loyer)
        if mois == 1:
            return "Un (01)"
        elif mois == 2:
            return "Deux (02)"
        elif mois == 3:
            return "Trois (03)"
        elif mois == 6:
            return "Six (06)"
        else:
            return f"{self._nombre_en_lettres(mois)} ({mois:02d})"
    
    def _get_mois_debut_paiement(self):
        """Récupère le mois de début de paiement."""
        if self.contrat.mois_debut_paiement:
            return self.contrat.mois_debut_paiement.upper()
        
        # Utiliser le mois suivant la date de signature
        mois_suivant = self.contrat.date_signature.month + 1
        if mois_suivant > 12:
            mois_suivant = 1
        
        mois_noms = {
            1: "JANVIER", 2: "FÉVRIER", 3: "MARS", 4: "AVRIL",
            5: "MAI", 6: "JUIN", 7: "JUILLET", 8: "AOÛT",
            9: "SEPTEMBRE", 10: "OCTOBRE", 11: "NOVEMBRE", 12: "DÉCEMBRE"
        }
        
        return mois_noms.get(mois_suivant, "AOÛT")
    
    def auto_remplir_champs_contrat(self):
        """Remplit automatiquement les champs du contrat avec les valeurs par défaut."""
        # Remplir les informations financières
        loyer_numerique = self._get_numeric_value(self.contrat.loyer_mensuel)
        depot_numerique = self._get_numeric_value(self.contrat.depot_garantie)
        
        if not self.contrat.loyer_mensuel_numerique:
            self.contrat.loyer_mensuel_numerique = str(int(loyer_numerique))
        
        if not self.contrat.loyer_mensuel_texte:
            self.contrat.loyer_mensuel_texte = self._nombre_en_lettres(int(loyer_numerique))
        
        if not self.contrat.depot_garantie_numerique:
            self.contrat.depot_garantie_numerique = str(int(depot_numerique))
        
        if not self.contrat.depot_garantie_texte:
            self.contrat.depot_garantie_texte = self._nombre_en_lettres(int(depot_numerique))
        
        if not self.contrat.nombre_mois_caution:
            self.contrat.nombre_mois_caution = self._calculer_mois_caution(depot_numerique, loyer_numerique)
        
        # Calculer le montant maximum de garantie
        montant_garantie_max = loyer_numerique * 6
        if not self.contrat.montant_garantie_max:
            self.contrat.montant_garantie_max = str(int(montant_garantie_max))
        
        if not self.contrat.montant_garantie_max_texte:
            self.contrat.montant_garantie_max_texte = self._nombre_en_lettres(int(montant_garantie_max))
        
        # Remplir le mois de début de paiement
        if not self.contrat.mois_debut_paiement:
            self.contrat.mois_debut_paiement = self._get_mois_debut_paiement()
        
        # Remplir les informations de la propriété
        if not self.contrat.numero_maison:
            self.contrat.numero_maison = f"E-{self.contrat.id % 1000:03d}"
        
        if not self.contrat.secteur:
            self.contrat.secteur = self.contrat.propriete.ville or "Ouagadougou"
        
        # Sauvegarder les modifications
        self.contrat.save()
        
        return self.contrat

