#!/usr/bin/env python
"""
Service de génération PDF pour les contrats de gestion immobilière
"""

import logging
from datetime import datetime
from decimal import Decimal
from django.utils import timezone
from django.template.loader import render_to_string
from django.http import HttpResponse
from io import BytesIO

from core.models import ConfigurationEntreprise
from .models import ContratGestion

logger = logging.getLogger(__name__)


class ContratGestionPDFService:
    """Service pour la génération de PDF de contrats de gestion immobilière."""
    
    def __init__(self, contrat_gestion):
        self.contrat_gestion = contrat_gestion
        self.logger = logger
    
    def generate_contrat_pdf(self, user=None):
        """
        Génère un PDF de contrat de gestion avec le template.
        
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
                'proprietes/contrat_gestion_pdf.html',
                {
                    'contrat': self.contrat_gestion,
                    'donnees': donnees_contrat,
                    'config': config,
                    'image_base64': image_base64,
                    'date_generation': timezone.now(),
                    'user': user,
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
            self.logger.error("Erreur lors de la génération PDF du contrat de gestion: %s", str(e))
            raise
    
    def _preparer_donnees_contrat(self):
        """Prépare les données du contrat pour le template."""
        # Récupérer les propriétés
        proprietes = self.contrat_gestion.get_proprietes_list()
        
        # Calculer le nombre total de propriétés
        nombre_proprietes = proprietes.count()
        
        # Préparer la liste des propriétés
        liste_proprietes = []
        for propriete in proprietes:
            # Construire l'adresse complète
            adresse_parts = []
            if propriete.adresse:
                adresse_parts.append(propriete.adresse)
            if propriete.ville:
                adresse_parts.append(propriete.ville)
            if propriete.code_postal:
                adresse_parts.append(propriete.code_postal)
            adresse_complete = ', '.join(adresse_parts) if adresse_parts else 'Non spécifiée'
            
            # Construire la description
            description_parts = []
            if propriete.type_bien:
                description_parts.append(propriete.type_bien.nom)
            if hasattr(propriete, 'nombre_pieces') and propriete.nombre_pieces:
                description_parts.append(f"{propriete.nombre_pieces} pièce(s)")
            if hasattr(propriete, 'surface') and propriete.surface:
                description_parts.append(f"{propriete.surface} m²")
            description = ' '.join(description_parts) if description_parts else 'Maison'
            
            # Récupérer l'état
            etat = 'bon'
            if hasattr(propriete, 'etat'):
                if hasattr(propriete, 'get_etat_display'):
                    etat = propriete.get_etat_display()
                else:
                    etat = propriete.etat or 'bon'
            
            liste_proprietes.append({
                'titre': propriete.titre,
                'numero': propriete.numero_propriete,
                'adresse': adresse_complete,
                'type': propriete.type_bien.nom if propriete.type_bien else 'Non spécifié',
                'description': description,
                'etat': etat,
            })
        
        # Formater la commission
        commission = float(self.contrat_gestion.commission_percentage)
        
        # Préparer les données
        donnees = {
            'nombre_proprietes': nombre_proprietes,
            'nombre_proprietes_texte': self._nombre_en_lettres(nombre_proprietes),
            'liste_proprietes': liste_proprietes,
            'commission_percentage': f"{commission:.2f}",
            'commission_texte': self._nombre_en_lettres(int(commission)),
        }
        
        return donnees
    
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

