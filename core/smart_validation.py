"""
Système de validation intelligente avec suggestions automatiques
Remplace les erreurs brutes par des solutions intelligentes
"""

import logging
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.db.models import Q
from datetime import datetime
import re

logger = logging.getLogger(__name__)

class SmartValidationSystem:
    """
    Système de validation intelligente qui propose des solutions au lieu d'erreurs
    """
    
    @staticmethod
    def validate_property_number_with_suggestion(numero_propriete, exclude_pk=None):
        """
        Valide un numéro de propriété et propose une alternative si nécessaire
        
        Args:
            numero_propriete (str): Numéro à valider
            exclude_pk (int): PK à exclure (pour les modifications)
        
        Returns:
            tuple: (is_valid, suggested_number, message)
        """
        from proprietes.models import Propriete
        from core.id_generator import IDGenerator
        
        try:
            # Vérifier si le numéro existe déjà
            queryset = Propriete.objects.filter(
                numero_propriete=numero_propriete,
                is_deleted=False
            )
            
            if exclude_pk:
                queryset = queryset.exclude(pk=exclude_pk)
            
            if not queryset.exists():
                return True, numero_propriete, "Numéro disponible"
            
            # Le numéro existe, proposer une alternative intelligente
            suggested_number = SmartValidationSystem._generate_smart_suggestion(
                numero_propriete, exclude_pk
            )
            
            message = f"Ce numéro existe déjà. Suggestion: {suggested_number}"
            
            logger.info(
                f"SUGGESTION_GENEREE: Numéro '{numero_propriete}' existe. "
                f"Suggestion: '{suggested_number}'"
            )
            
            return False, suggested_number, message
            
        except Exception as e:
            logger.error(f"Erreur lors de la validation du numéro: {e}")
            # En cas d'erreur, générer un numéro de secours
            generator = IDGenerator()
            try:
                fallback = generator.generate_id('propriete')
                return False, fallback, f"Erreur de validation. Numéro suggéré: {fallback}"
            except:
                # Dernière option de secours
                timestamp = datetime.now().strftime('%H%M%S%f')[:-3]
                fallback = f"PRO-{datetime.now().year}-{timestamp}"
                return False, fallback, f"Erreur de validation. Numéro suggéré: {fallback}"
    
    @staticmethod
    def _generate_smart_suggestion(original_number, exclude_pk=None):
        """
        Génère une suggestion intelligente basée sur le numéro original
        """
        from proprietes.models import Propriete
        from core.id_generator import IDGenerator
        
        # Essayer différentes stratégies de suggestion
        strategies = [
            lambda: SmartValidationSystem._strategy_append_number(original_number, exclude_pk),
            lambda: SmartValidationSystem._strategy_increment_suffix(original_number, exclude_pk),
            lambda: SmartValidationSystem._strategy_add_timestamp(original_number),
            lambda: SmartValidationSystem._strategy_generate_new(original_number)
        ]
        
        for strategy in strategies:
            try:
                suggestion = strategy()
                if suggestion and SmartValidationSystem._is_number_available(suggestion, exclude_pk):
                    return suggestion
            except Exception as e:
                logger.warning(f"Stratégie de suggestion échouée: {e}")
                continue
        
        # Si toutes les stratégies échouent, utiliser le générateur
        try:
            generator = IDGenerator()
            return generator.generate_id('propriete')
        except:
            # Dernière option de secours
            timestamp = datetime.now().strftime('%H%M%S%f')[:-3]
            return f"PRO-{datetime.now().year}-{timestamp}"
    
    @staticmethod
    def _strategy_append_number(original_number, exclude_pk=None):
        """Stratégie 1: Ajouter un numéro à la fin"""
        base_number = original_number.rstrip('0123456789')
        # Trouver le prochain numéro disponible
        for i in range(1, 1000):
            suggestion = f"{base_number}{i:03d}"
            if SmartValidationSystem._is_number_available(suggestion, exclude_pk):
                return suggestion
        return None
    
    @staticmethod
    def _strategy_increment_suffix(original_number, exclude_pk=None):
        """Stratégie 2: Incrémenter le suffixe numérique"""
        # Extraire le suffixe numérique
        match = re.search(r'(\d+)$', original_number)
        if match:
            suffix = int(match.group(1))
            base = original_number[:match.start()]
            for i in range(suffix + 1, suffix + 100):
                suggestion = f"{base}{i:0{len(match.group(1))}d}"
                if SmartValidationSystem._is_number_available(suggestion, exclude_pk):
                    return suggestion
        return None
    
    @staticmethod
    def _strategy_add_timestamp(original_number):
        """Stratégie 3: Ajouter un timestamp"""
        timestamp = datetime.now().strftime('%H%M%S')
        return f"{original_number}-{timestamp}"
    
    @staticmethod
    def _strategy_generate_new(original_number):
        """Stratégie 4: Générer un nouveau numéro basé sur le pattern"""
        # Analyser le pattern du numéro original
        if original_number.startswith('PRO-'):
            year = datetime.now().year
            return f"PRO-{year}-{datetime.now().strftime('%m%d%H%M')}"
        elif original_number.startswith('PR'):
            return f"PR{datetime.now().strftime('%Y%m%d%H%M')}"
        else:
            return f"PRO-{datetime.now().year}-{datetime.now().strftime('%m%d%H%M')}"
    
    @staticmethod
    def _is_number_available(numero_propriete, exclude_pk=None):
        """Vérifie si un numéro est disponible"""
        from proprietes.models import Propriete
        
        queryset = Propriete.objects.filter(
            numero_propriete=numero_propriete,
            is_deleted=False
        )
        
        if exclude_pk:
            queryset = queryset.exclude(pk=exclude_pk)
        
        return not queryset.exists()
    
    @staticmethod
    def validate_tenant_email_with_suggestion(email, exclude_pk=None):
        """
        Valide un email de locataire et propose une alternative si nécessaire
        """
        from proprietes.models import Locataire
        
        if not email:
            return True, email, "Email valide"
        
        queryset = Locataire.objects.filter(email=email, is_deleted=False)
        if exclude_pk:
            queryset = queryset.exclude(pk=exclude_pk)
        
        if not queryset.exists():
            return True, email, "Email disponible"
        
        # Proposer une alternative
        base_email = email.split('@')[0]
        domain = email.split('@')[1] if '@' in email else 'example.com'
        
        for i in range(1, 100):
            suggestion = f"{base_email}{i}@{domain}"
            if not Locataire.objects.filter(email=suggestion, is_deleted=False).exists():
                return False, suggestion, f"Cet email existe déjà. Suggestion: {suggestion}"
        
        return False, email, "Email déjà utilisé"
    
    @staticmethod
    def validate_contract_number_with_suggestion(numero_contrat, exclude_pk=None):
        """
        Valide un numéro de contrat et propose une alternative si nécessaire
        """
        from contrats.models import Contrat
        
        if not numero_contrat:
            return True, numero_contrat, "Numéro valide"
        
        queryset = Contrat.objects.filter(numero_contrat=numero_contrat, is_deleted=False)
        if exclude_pk:
            queryset = queryset.exclude(pk=exclude_pk)
        
        if not queryset.exists():
            return True, numero_contrat, "Numéro disponible"
        
        # Proposer une alternative
        base_number = numero_contrat.rstrip('0123456789')
        for i in range(1, 1000):
            suggestion = f"{base_number}{i:03d}"
            if not Contrat.objects.filter(numero_contrat=suggestion, is_deleted=False).exists():
                return False, suggestion, f"Ce numéro existe déjà. Suggestion: {suggestion}"
        
        return False, numero_contrat, "Numéro déjà utilisé"
