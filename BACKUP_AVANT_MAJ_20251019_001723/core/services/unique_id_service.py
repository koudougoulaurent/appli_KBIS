"""
Service centralisé pour la génération d'identifiants uniques
"""

from django.utils.crypto import get_random_string
from typing import Dict, Callable, Any
import re


class UniqueIdService:
    """Service pour générer des identifiants uniques pour tous les modèles."""
    
    # Configuration des préfixes et formats pour chaque modèle
    ID_CONFIGS = {
        'bailleur': {
            'prefix': 'BL',
            'length': 8,
            'format': '{prefix}-{code}',
            'description': 'Code Bailleur',
        },
        'locataire': {
            'prefix': 'LT',
            'length': 8,
            'format': '{prefix}-{code}',
            'description': 'Code Locataire',
        },
        'paiement': {
            'prefix': 'PAY',
            'length': 8,
            'format': '{prefix}-{code}',
            'description': 'Référence Paiement',
        },
        'contrat': {
            'prefix': 'CT',
            'length': 10,
            'format': '{prefix}-{code}',
            'description': 'Numéro Contrat',
        },
        'propriete': {
            'prefix': 'PR',
            'length': 8,
            'format': '{prefix}-{code}',
            'description': 'Code Propriété',
        },
        'recu': {
            'prefix': 'RC',
            'length': 8,
            'format': '{prefix}-{code}',
            'description': 'Numéro Reçu',
        },
        'facture': {
            'prefix': 'FC',
            'length': 8,
            'format': '{prefix}-{code}',
            'description': 'Numéro Facture',
        },
        'charge': {
            'prefix': 'CH',
            'length': 8,
            'format': '{prefix}-{code}',
            'description': 'Code Charge',
        },
    }
    
    @classmethod
    def generate_code(cls, entity_type: str, custom_length: int = None) -> str:
        """
        Génère un code unique pour un type d'entité donné.
        
        Args:
            entity_type: Type d'entité ('bailleur', 'locataire', etc.)
            custom_length: Longueur personnalisée du code (optionnel)
            
        Returns:
            Code unique formaté
            
        Raises:
            ValueError: Si le type d'entité n'est pas configuré
        """
        if entity_type not in cls.ID_CONFIGS:
            raise ValueError(f"Type d'entité '{entity_type}' non configuré")
        
        config = cls.ID_CONFIGS[entity_type]
        length = custom_length or config['length']
        
        # Générer le code aléatoire
        code = get_random_string(
            length, 
            'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
        )
        
        # Formater selon la configuration
        return config['format'].format(
            prefix=config['prefix'],
            code=code
        )
    
    @classmethod
    def generate_unique_code(cls, entity_type: str, model_class: Any, 
                           field_name: str, custom_length: int = None) -> str:
        """
        Génère un code unique en vérifiant l'unicité dans la base de données.
        
        Args:
            entity_type: Type d'entité
            model_class: Classe du modèle Django
            field_name: Nom du champ contenant l'identifiant
            custom_length: Longueur personnalisée du code
            
        Returns:
            Code unique garanti
        """
        max_attempts = 100  # Éviter les boucles infinies
        attempts = 0
        
        while attempts < max_attempts:
            code = cls.generate_code(entity_type, custom_length)
            
            # Vérifier l'unicité
            if not model_class.objects.filter(**{field_name: code}).exists():
                return code
            
            attempts += 1
        
        raise RuntimeError(f"Impossible de générer un code unique après {max_attempts} tentatives")
    
    @classmethod
    def validate_code_format(cls, code: str, entity_type: str) -> bool:
        """
        Valide le format d'un code pour un type d'entité.
        
        Args:
            code: Code à valider
            entity_type: Type d'entité
            
        Returns:
            True si le format est valide, False sinon
        """
        if entity_type not in cls.ID_CONFIGS:
            return False
        
        config = cls.ID_CONFIGS[entity_type]
        prefix = config['prefix']
        length = config['length']
        
        # Pattern: PREFIX-XXXXXXXX (où X = lettre ou chiffre)
        pattern = f"^{prefix}-[A-Z0-9]{{{length}}}$"
        return bool(re.match(pattern, code))
    
    @classmethod
    def get_next_sequential_code(cls, entity_type: str, model_class: Any, 
                               field_name: str) -> str:
        """
        Génère un code séquentiel (optionnel pour certains cas d'usage).
        
        Args:
            entity_type: Type d'entité
            model_class: Classe du modèle Django
            field_name: Nom du champ contenant l'identifiant
            
        Returns:
            Code séquentiel unique
        """
        if entity_type not in cls.ID_CONFIGS:
            raise ValueError(f"Type d'entité '{entity_type}' non configuré")
        
        config = cls.ID_CONFIGS[entity_type]
        prefix = config['prefix']
        
        # Trouver le dernier numéro utilisé
        last_code = model_class.objects.filter(
            **{f"{field_name}__startswith": f"{prefix}-"}
        ).order_by(f"-{field_name}").first()
        
        if last_code:
            last_number = getattr(last_code, field_name).split('-')[-1]
            try:
                next_number = int(last_number) + 1
            except ValueError:
                # Si ce n'est pas un nombre, commencer à 1
                next_number = 1
        else:
            next_number = 1
        
        # Formater avec des zéros à gauche
        length = config['length']
        return f"{prefix}-{next_number:0{length}d}"
    
    @classmethod
    def get_entity_description(cls, entity_type: str) -> str:
        """Retourne la description d'un type d'entité."""
        return cls.ID_CONFIGS.get(entity_type, {}).get('description', entity_type)
    
    @classmethod
    def get_all_entity_types(cls) -> list:
        """Retourne tous les types d'entités configurés."""
        return list(cls.ID_CONFIGS.keys())
    
    @classmethod
    def preview_code_format(cls, entity_type: str) -> str:
        """Retourne un exemple de format de code pour un type d'entité."""
        if entity_type not in cls.ID_CONFIGS:
            return "Format non configuré"
        
        config = cls.ID_CONFIGS[entity_type]
        example_code = 'X' * config['length']
        return config['format'].format(
            prefix=config['prefix'],
            code=example_code
        )


# Fonctions utilitaires pour une utilisation simplifiée
def generate_bailleur_code():
    """Génère un code unique pour un bailleur."""
    from proprietes.models import Bailleur
    return UniqueIdService.generate_unique_code('bailleur', Bailleur, 'code_bailleur')


def generate_locataire_code():
    """Génère un code unique pour un locataire."""
    from proprietes.models import Locataire
    return UniqueIdService.generate_unique_code('locataire', Locataire, 'code_locataire')


def generate_paiement_reference():
    """Génère une référence unique pour un paiement."""
    from paiements.models import Paiement
    return UniqueIdService.generate_unique_code('paiement', Paiement, 'reference_paiement')


def generate_contrat_number():
    """Génère un numéro unique pour un contrat."""
    from contrats.models import Contrat
    return UniqueIdService.generate_unique_code('contrat', Contrat, 'numero_contrat')


def validate_unique_id(code: str, entity_type: str) -> Dict[str, Any]:
    """
    Valide un identifiant unique.
    
    Returns:
        Dict avec 'valid' (bool) et 'message' (str)
    """
    if not code:
        return {'valid': False, 'message': 'Code requis'}
    
    if not UniqueIdService.validate_code_format(code, entity_type):
        expected_format = UniqueIdService.preview_code_format(entity_type)
        return {
            'valid': False, 
            'message': f'Format invalide. Format attendu: {expected_format}'
        }
    
    return {'valid': True, 'message': 'Format valide'}
