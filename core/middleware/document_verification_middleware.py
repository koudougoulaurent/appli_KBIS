#!/usr/bin/env python3
"""
Middleware de Vérification Automatique des Documents
===================================================

Ce middleware intercepte automatiquement tous les uploads de fichiers
et applique la vérification de véracité avant que les documents
passent dans les formulaires.

Auteur: Assistant IA
Date: 2025
"""

import os
import tempfile
import logging
from django.http import JsonResponse
from django.core.files.uploadedfile import UploadedFile
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
from django import forms

# Import du service de vérification
from core.services.verification_documents import document_verification_service

logger = logging.getLogger(__name__)


class DocumentVerificationMiddleware(MiddlewareMixin):
    """
    Middleware qui vérifie automatiquement la véracité des documents uploadés.
    
    Fonctionnalités :
    - Interception automatique des uploads
    - Vérification en temps réel
    - Blocage des documents suspects
    - Feedback immédiat à l'utilisateur
    - Historique de vérification
    """
    
    def __init__(self, get_response=None):
        super().__init__(get_response)
        self.verification_service = document_verification_service
        
        # Configuration des types de documents à vérifier
        self.document_type_mapping = {
            'piece_identite': ['piece_identite', 'identite', 'cni', 'passeport'],
            'justificatif_domicile': ['justificatif_domicile', 'domicile', 'facture', 'edf'],
            'attestation_bancaire': ['attestation_bancaire', 'bancaire', 'rib', 'iban'],
            'avis_imposition': ['avis_imposition', 'imposition', 'fisc', 'impots'],
            'justificatifs_revenus': ['justificatifs_revenus', 'revenus', 'salaire', 'bulletin'],
            'garant_caution': ['garant_caution', 'garant', 'caution', 'assurance'],
            'documents_propriete': ['documents_propriete', 'propriete', 'acte', 'titre'],
            'diagnostic_energetique': ['diagnostic_energetique', 'dpe', 'energie'],
            'diagnostic_plomb': ['diagnostic_plomb', 'plomb'],
            'diagnostic_amiante': ['diagnostic_amiante', 'amiante'],
            'attestation_assurance_habitation': ['attestation_assurance_habitation', 'assurance_habitation'],
            'contrat_bail': ['contrat_bail', 'contrat', 'bail'],
            'etat_lieux': ['etat_lieux', 'etat', 'lieux'],
            'quittance_loyer': ['quittance_loyer', 'quittance', 'loyer']
        }
    
    def process_request(self, request):
        """
        Traite la requête et vérifie les fichiers uploadés.
        """
        # Vérifier si c'est une requête POST avec des fichiers
        if request.method == 'POST' and request.FILES:
            try:
                # Vérifier chaque fichier uploadé
                verification_results = {}
                files_to_reject = []
                
                for field_name, uploaded_file in request.FILES.items():
                    # Déterminer le type de document
                    document_type = self._determine_document_type(field_name)
                    
                    if document_type:
                        # Vérifier le document
                        result = self._verify_uploaded_file(uploaded_file, document_type)
                        verification_results[field_name] = result
                        
                        # Marquer pour rejet si invalide
                        if not result.is_valid:
                            files_to_reject.append(field_name)
                
                # Si des documents sont rejetés, retourner une erreur
                if files_to_reject:
                    return self._create_verification_error_response(
                        verification_results, files_to_reject
                    )
                
                # Stocker les résultats de vérification dans la session
                if verification_results:
                    request.session['document_verification_results'] = {
                        field: {
                            'is_valid': result.is_valid,
                            'confidence_score': result.confidence_score,
                            'warnings': result.warnings,
                            'errors': result.errors,
                            'fraud_indicators': result.fraud_indicators,
                            'recommendations': result.recommendations
                        }
                        for field, result in verification_results.items()
                    }
                
            except Exception as e:
                logger.error(f"Erreur lors de la vérification des documents: {e}")
                # En cas d'erreur, on laisse passer mais on log
                request.session['document_verification_error'] = str(e)
        
        return None
    
    def _determine_document_type(self, field_name: str) -> str:
        """
        Détermine le type de document basé sur le nom du champ.
        
        Args:
            field_name: Nom du champ de formulaire
            
        Returns:
            str: Type de document identifié ou None
        """
        field_name_lower = field_name.lower()
        
        for doc_type, keywords in self.document_type_mapping.items():
            if any(keyword in field_name_lower for keyword in keywords):
                return doc_type
        
        return None
    
    def _verify_uploaded_file(self, uploaded_file: UploadedFile, document_type: str):
        """
        Vérifie un fichier uploadé.
        
        Args:
            uploaded_file: Fichier Django uploadé
            document_type: Type de document identifié
            
        Returns:
            VerificationResult: Résultat de la vérification
        """
        try:
            # Créer un fichier temporaire pour la vérification
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as temp_file:
                # Écrire le contenu du fichier uploadé
                for chunk in uploaded_file.chunks():
                    temp_file.write(chunk)
                
                temp_file_path = temp_file.name
            
            try:
                # Vérifier le document
                result = self.verification_service.verify_document(
                    temp_file_path, 
                    document_type
                )
                
                return result
                
            finally:
                # Nettoyer le fichier temporaire
                try:
                    os.unlink(temp_file_path)
                except OSError:
                    pass  # Ignorer les erreurs de suppression
                    
        except Exception as e:
            logger.error(f"Erreur lors de la vérification du fichier {uploaded_file.name}: {e}")
            
            # Retourner un résultat d'erreur
            from core.services.verification_documents import VerificationResult
            return VerificationResult(
                is_valid=False,
                confidence_score=0.0,
                warnings=[],
                errors=[f"Erreur de vérification: {str(e)}"],
                extracted_text="",
                metadata={},
                fraud_indicators=[],
                recommendations=["Contactez l'administrateur système"]
            )
    
    def _create_verification_error_response(self, verification_results: dict, 
                                          files_to_reject: list) -> JsonResponse:
        """
        Crée une réponse d'erreur pour les documents rejetés.
        
        Args:
            verification_results: Résultats de vérification
            files_to_reject: Liste des champs rejetés
            
        Returns:
            JsonResponse: Réponse d'erreur JSON
        """
        error_data = {
            'success': False,
            'message': 'Documents rejetés lors de la vérification de véracité',
            'rejected_files': files_to_reject,
            'verification_details': {}
        }
        
        # Ajouter les détails de vérification pour chaque fichier rejeté
        for field_name in files_to_reject:
            if field_name in verification_results:
                result = verification_results[field_name]
                error_data['verification_details'][field_name] = {
                    'confidence_score': result.confidence_score,
                    'warnings': result.warnings,
                    'errors': result.errors,
                    'fraud_indicators': result.fraud_indicators,
                    'recommendations': result.recommendations
                }
        
        return JsonResponse(error_data, status=400)
    
    def process_response(self, request, response):
        """
        Traite la réponse et ajoute les informations de vérification si nécessaire.
        """
        # Ajouter les résultats de vérification dans les en-têtes de réponse
        if hasattr(request, 'session') and 'document_verification_results' in request.session:
            verification_results = request.session['document_verification_results']
            
            # Ajouter un en-tête personnalisé avec le résumé
            valid_count = sum(1 for result in verification_results.values() if result['is_valid'])
            total_count = len(verification_results)
            
            response['X-Document-Verification'] = f"{valid_count}/{total_count} documents validés"
            
            # Nettoyer la session
            del request.session['document_verification_results']
        
        return response


class DocumentVerificationFormMixin:
    """
    Mixin pour les formulaires Django qui ajoute la vérification automatique.
    
    Usage:
        class MonFormulaire(DocumentVerificationFormMixin, forms.ModelForm):
            pass
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.verification_service = document_verification_service
        self.verification_results = {}
    
    def clean(self):
        """
        Validation personnalisée avec vérification des documents.
        """
        cleaned_data = super().clean()
        
        # Vérifier les fichiers uploadés
        for field_name, field in self.fields.items():
            if isinstance(field, forms.FileField) and field_name in self.data:
                uploaded_file = self.files.get(field_name)
                if uploaded_file:
                    # Déterminer le type de document
                    document_type = self._determine_document_type(field_name)
                    
                    if document_type:
                        # Vérifier le document
                        result = self._verify_uploaded_file(uploaded_file, document_type)
                        self.verification_results[field_name] = result
                        
                        # Si le document est invalide, lever une erreur
                        if not result.is_valid:
                            error_messages = []
                            if result.errors:
                                error_messages.extend(result.errors)
                            if result.fraud_indicators:
                                error_messages.append("Document suspect détecté")
                            
                            raise forms.ValidationError({
                                field_name: error_messages
                            })
        
        return cleaned_data
    
    def _determine_document_type(self, field_name: str) -> str:
        """Détermine le type de document basé sur le nom du champ."""
        field_name_lower = field_name.lower()
        
        document_type_mapping = {
            'piece_identite': ['piece_identite', 'identite', 'cni', 'passeport'],
            'justificatif_domicile': ['justificatif_domicile', 'domicile', 'facture', 'edf'],
            'attestation_bancaire': ['attestation_bancaire', 'bancaire', 'rib', 'iban'],
            'avis_imposition': ['avis_imposition', 'imposition', 'fisc', 'impots'],
            'justificatifs_revenus': ['justificatifs_revenus', 'revenus', 'salaire', 'bulletin'],
            'garant_caution': ['garant_caution', 'garant', 'caution', 'assurance'],
            'documents_propriete': ['documents_propriete', 'propriete', 'acte', 'titre'],
            'diagnostic_energetique': ['diagnostic_energetique', 'dpe', 'energie'],
            'diagnostic_plomb': ['diagnostic_plomb', 'plomb'],
            'diagnostic_amiante': ['diagnostic_amiante', 'amiante'],
            'attestation_assurance_habitation': ['attestation_assurance_habitation', 'assurance_habitation'],
            'contrat_bail': ['contrat_bail', 'contrat', 'bail'],
            'etat_lieux': ['etat_lieux', 'etat', 'lieux'],
            'quittance_loyer': ['quittance_loyer', 'quittance', 'loyer']
        }
        
        for doc_type, keywords in document_type_mapping.items():
            if any(keyword in field_name_lower for keyword in keywords):
                return doc_type
        
        return None
    
    def _verify_uploaded_file(self, uploaded_file: UploadedFile, document_type: str):
        """Vérifie un fichier uploadé."""
        try:
            # Créer un fichier temporaire pour la vérification
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as temp_file:
                # Écrire le contenu du fichier uploadé
                for chunk in uploaded_file.chunks():
                    temp_file.write(chunk)
                
                temp_file_path = temp_file.name
            
            try:
                # Vérifier le document
                result = self.verification_service.verify_document(
                    temp_file_path, 
                    document_type
                )
                
                return result
                
            finally:
                # Nettoyer le fichier temporaire
                try:
                    os.unlink(temp_file_path)
                except OSError:
                    pass  # Ignorer les erreurs de suppression
                    
        except Exception as e:
            logger.error(f"Erreur lors de la vérification du fichier {uploaded_file.name}: {e}")
            
            # Retourner un résultat d'erreur
            from core.services.verification_documents import VerificationResult
            return VerificationResult(
                is_valid=False,
                confidence_score=0.0,
                warnings=[],
                errors=[f"Erreur de vérification: {str(e)}"],
                extracted_text="",
                metadata={},
                fraud_indicators=[],
                recommendations=["Contactez l'administrateur système"]
            )
    
    def get_verification_results(self) -> dict:
        """Récupère les résultats de vérification."""
        return self.verification_results.copy()
    
    def get_verification_summary(self) -> dict:
        """Récupère un résumé des vérifications."""
        if not self.verification_results:
            return {}
        
        total_files = len(self.verification_results)
        valid_files = sum(1 for result in self.verification_results.values() if result.is_valid)
        
        # Calcul du score moyen
        confidence_scores = [
            result.confidence_score 
            for result in self.verification_results.values()
        ]
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
        
        return {
            'total_files': total_files,
            'valid_files': valid_files,
            'invalid_files': total_files - valid_files,
            'success_rate': (valid_files / total_files) * 100 if total_files > 0 else 0,
            'average_confidence': avg_confidence
        }
