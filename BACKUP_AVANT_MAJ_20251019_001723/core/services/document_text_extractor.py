"""
Service d'extraction de texte des documents pour utilisation dans les PDF générés.
Ce service évite d'embarquer les images entières dans les documents PDF.
"""

import os
import logging
from typing import Dict, List, Optional
from django.core.files.storage import default_storage
from django.conf import settings

logger = logging.getLogger(__name__)

class DocumentTextExtractor:
    """
    Service pour extraire et utiliser le texte des documents au lieu d'embarquer les images.
    """
    
    def __init__(self):
        self.verification_service = None
        self._init_verification_service()
    
    def _init_verification_service(self):
        """Initialise le service de vérification des documents."""
        try:
            from core.services.verification_documents import DocumentVerificationService
            self.verification_service = DocumentVerificationService()
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation du service de vérification: {e}")
    
    def extract_document_info(self, document_path: str) -> Dict[str, str]:
        """
        Extrait les informations textuelles d'un document.
        
        Args:
            document_path: Chemin vers le document
            
        Returns:
            Dict contenant les informations extraites
        """
        if not self.verification_service:
            return {"error": "Service de vérification non disponible"}
        
        try:
            # Vérifier si le fichier existe
            if not os.path.exists(document_path):
                return {"error": f"Fichier non trouvé: {document_path}"}
            
            # Extraire le texte
            extracted_text = self.verification_service._extract_text(document_path)
            
            # Analyser le type de document et extraire des informations spécifiques
            document_info = self._analyze_document_content(document_path, extracted_text)
            
            return document_info
            
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction des informations du document: {e}")
            return {"error": f"Erreur d'extraction: {str(e)}"}
    
    def _analyze_document_content(self, file_path: str, extracted_text: str) -> Dict[str, str]:
        """
        Analyse le contenu extrait pour identifier les informations importantes.
        
        Args:
            file_path: Chemin du fichier
            extracted_text: Texte extrait du document
            
        Returns:
            Dict avec les informations analysées
        """
        filename = os.path.basename(file_path).lower()
        document_info = {
            "filename": os.path.basename(file_path),
            "extracted_text": extracted_text,
            "document_type": "unknown",
            "key_information": {},
            "summary": ""
        }
        
        # Identifier le type de document
        if any(keyword in filename for keyword in ['identite', 'cni', 'passeport', 'carte']):
            document_info["document_type"] = "identite"
            document_info["key_information"] = self._extract_identity_info(extracted_text)
            document_info["summary"] = "Document d'identité - Informations personnelles extraites"
            
        elif any(keyword in filename for keyword in ['edf', 'facture', 'electricite']):
            document_info["document_type"] = "facture_edf"
            document_info["key_information"] = self._extract_utility_bill_info(extracted_text)
            document_info["summary"] = "Facture EDF - Informations de consommation extraites"
            
        elif any(keyword in filename for keyword in ['rib', 'bancaire', 'attestation']):
            document_info["document_type"] = "bancaire"
            document_info["key_information"] = self._extract_banking_info(extracted_text)
            document_info["summary"] = "Document bancaire - Informations de compte extraites"
            
        elif any(keyword in filename for keyword in ['avis', 'imposition', 'fiscal']):
            document_info["document_type"] = "fiscal"
            document_info["key_information"] = self._extract_tax_info(extracted_text)
            document_info["summary"] = "Avis d'imposition - Informations fiscales extraites"
            
        elif any(keyword in filename for keyword in ['salaire', 'bulletin', 'paye']):
            document_info["document_type"] = "salaire"
            document_info["key_information"] = self._extract_salary_info(extracted_text)
            document_info["summary"] = "Bulletin de salaire - Informations de rémunération extraites"
            
        elif any(keyword in filename for keyword in ['contrat', 'bail', 'location']):
            document_info["document_type"] = "contrat"
            document_info["key_information"] = self._extract_contract_info(extracted_text)
            document_info["summary"] = "Contrat de bail - Informations contractuelles extraites"
            
        else:
            document_info["summary"] = f"Document - {filename} - Contenu extrait"
        
        return document_info
    
    def _extract_identity_info(self, text: str) -> Dict[str, str]:
        """Extrait les informations d'identité du texte."""
        info = {}
        
        # Recherche de patterns communs dans les documents d'identité
        import re
        
        # Nom et prénom
        nom_match = re.search(r'(?:NOM|Nom)[\s:]*([A-Z\s]+)', text, re.IGNORECASE)
        if nom_match:
            info["nom"] = nom_match.group(1).strip()
        
        prenom_match = re.search(r'(?:PRÉNOM|Prénom|Prenom)[\s:]*([A-Z\s]+)', text, re.IGNORECASE)
        if prenom_match:
            info["prenom"] = prenom_match.group(1).strip()
        
        # Date de naissance
        date_match = re.search(r'(?:NÉ|Né|Nee)[\s:]*([0-9]{2}[/\-\.][0-9]{2}[/\-\.][0-9]{4})', text, re.IGNORECASE)
        if date_match:
            info["date_naissance"] = date_match.group(1)
        
        # Numéro de document
        num_match = re.search(r'(?:N°|No|Numéro)[\s:]*([A-Z0-9\s]+)', text, re.IGNORECASE)
        if num_match:
            info["numero_document"] = num_match.group(1).strip()
        
        return info
    
    def _extract_utility_bill_info(self, text: str) -> Dict[str, str]:
        """Extrait les informations des factures d'électricité."""
        info = {}
        
        import re
        
        # Montant
        montant_match = re.search(r'(?:TOTAL|Total|Montant)[\s:]*([0-9\s,\.]+)', text, re.IGNORECASE)
        if montant_match:
            info["montant"] = montant_match.group(1).strip()
        
        # Période
        periode_match = re.search(r'(?:Période|Periode)[\s:]*([0-9\s/\-\.]+)', text, re.IGNORECASE)
        if periode_match:
            info["periode"] = periode_match.group(1).strip()
        
        # Adresse
        adresse_match = re.search(r'(?:Adresse|Adr)[\s:]*([A-Za-z0-9\s,\.]+)', text, re.IGNORECASE)
        if adresse_match:
            info["adresse"] = adresse_match.group(1).strip()
        
        return info
    
    def _extract_banking_info(self, text: str) -> Dict[str, str]:
        """Extrait les informations bancaires."""
        info = {}
        
        import re
        
        # IBAN
        iban_match = re.search(r'([A-Z]{2}[0-9]{2}[A-Z0-9\s]{20,})', text)
        if iban_match:
            info["iban"] = iban_match.group(1).strip()
        
        # BIC
        bic_match = re.search(r'([A-Z]{6}[A-Z0-9]{2}[A-Z0-9]{3})', text)
        if bic_match:
            info["bic"] = bic_match.group(1).strip()
        
        # Titulaire
        titulaire_match = re.search(r'(?:Titulaire|TITULAIRE)[\s:]*([A-Z\s]+)', text, re.IGNORECASE)
        if titulaire_match:
            info["titulaire"] = titulaire_match.group(1).strip()
        
        return info
    
    def _extract_tax_info(self, text: str) -> Dict[str, str]:
        """Extrait les informations fiscales."""
        info = {}
        
        import re
        
        # Revenus
        revenus_match = re.search(r'(?:Revenus|REVENUS)[\s:]*([0-9\s,\.]+)', text, re.IGNORECASE)
        if revenus_match:
            info["revenus"] = revenus_match.group(1).strip()
        
        # Impôt
        impot_match = re.search(r'(?:Impôt|IMPOT|Impots)[\s:]*([0-9\s,\.]+)', text, re.IGNORECASE)
        if impot_match:
            info["impot"] = impot_match.group(1).strip()
        
        # Année
        annee_match = re.search(r'(?:Année|Annee|Année d\'imposition)[\s:]*([0-9]{4})', text, re.IGNORECASE)
        if annee_match:
            info["annee"] = annee_match.group(1).strip()
        
        return info
    
    def _extract_salary_info(self, text: str) -> Dict[str, str]:
        """Extrait les informations de salaire."""
        info = {}
        
        import re
        
        # Salaire brut
        brut_match = re.search(r'(?:Brut|BRUT)[\s:]*([0-9\s,\.]+)', text, re.IGNORECASE)
        if brut_match:
            info["salaire_brut"] = brut_match.group(1).strip()
        
        # Salaire net
        net_match = re.search(r'(?:Net|NET)[\s:]*([0-9\s,\.]+)', text, re.IGNORECASE)
        if net_match:
            info["salaire_net"] = net_match.group(1).strip()
        
        # Période
        periode_match = re.search(r'(?:Période|Periode)[\s:]*([0-9\s/\-\.]+)', text, re.IGNORECASE)
        if periode_match:
            info["periode"] = periode_match.group(1).strip()
        
        return info
    
    def _extract_contract_info(self, text: str) -> Dict[str, str]:
        """Extrait les informations contractuelles."""
        info = {}
        
        import re
        
        # Loyer
        loyer_match = re.search(r'(?:Loyer|LOYER)[\s:]*([0-9\s,\.]+)', text, re.IGNORECASE)
        if loyer_match:
            info["loyer"] = loyer_match.group(1).strip()
        
        # Durée
        duree_match = re.search(r'(?:Durée|Duree|Durée du bail)[\s:]*([0-9\s]+)', text, re.IGNORECASE)
        if duree_match:
            info["duree"] = duree_match.group(1).strip()
        
        # Date de début
        debut_match = re.search(r'(?:Début|Debut|Date de début)[\s:]*([0-9\s/\-\.]+)', text, re.IGNORECASE)
        if debut_match:
            info["date_debut"] = debut_match.group(1).strip()
        
        return info
    
    def get_document_summary_for_pdf(self, document_path: str) -> str:
        """
        Retourne un résumé du document pour inclusion dans les PDF générés.
        
        Args:
            document_path: Chemin vers le document
            
        Returns:
            Résumé textuel du document
        """
        document_info = self.extract_document_info(document_path)
        
        if "error" in document_info:
            return f"Erreur: {document_info['error']}"
        
        summary_parts = [document_info["summary"]]
        
        # Ajouter les informations clés si disponibles
        if document_info["key_information"]:
            key_info = []
            for key, value in document_info["key_information"].items():
                if value:
                    key_info.append(f"{key.title()}: {value}")
            
            if key_info:
                summary_parts.append("Informations extraites: " + " | ".join(key_info))
        
        return " - ".join(summary_parts)
    
    def get_documents_summary_for_entity(self, entity_documents: List) -> str:
        """
        Génère un résumé de tous les documents d'une entité (bailleur, locataire, etc.).
        
        Args:
            entity_documents: Liste des documents de l'entité
            
        Returns:
            Résumé consolidé de tous les documents
        """
        summaries = []
        
        for document in entity_documents:
            if hasattr(document, 'fichier') and document.fichier:
                try:
                    document_path = document.fichier.path
                    summary = self.get_document_summary_for_pdf(document_path)
                    summaries.append(f"• {document.nom}: {summary}")
                except Exception as e:
                    logger.warning(f"Erreur lors du traitement du document {document.nom}: {e}")
                    summaries.append(f"• {document.nom}: Document joint (erreur d'extraction)")
        
        if summaries:
            return "\n".join(summaries)
        else:
            return "Aucun document joint"
