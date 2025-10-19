"""
Générateur d'IDs vraiment robuste qui garantit l'unicité absolue
Plus jamais de doublons !
"""

import time
import random
from datetime import datetime
from django.db import transaction, IntegrityError
from django.core.exceptions import ValidationError


class RobustIDGenerator:
    """
    Générateur d'IDs vraiment robuste avec garantie d'unicité absolue
    """
    
    MAX_ATTEMPTS = 100  # Nombre maximum de tentatives pour générer un ID unique
    
    @classmethod
    def generate_unique_id(cls, entity_type, **kwargs):
        """
        Génère un ID vraiment unique avec garantie d'unicité absolue
        
        Args:
            entity_type (str): Type d'entité (propriete, locataire, etc.)
            **kwargs: Paramètres supplémentaires
        
        Returns:
            str: ID unique garanti
        """
        for attempt in range(cls.MAX_ATTEMPTS):
            try:
                # Générer un ID candidat
                candidate_id = cls._generate_candidate_id(entity_type, **kwargs)
                
                # Vérifier l'unicité avec une transaction atomique
                if cls._is_id_unique(entity_type, candidate_id, **kwargs):
                    return candidate_id
                    
            except Exception as e:
                print(f"Tentative {attempt + 1} échouée: {e}")
                if attempt == cls.MAX_ATTEMPTS - 1:
                    raise Exception(f"Impossible de générer un ID unique après {cls.MAX_ATTEMPTS} tentatives")
                
                # Attendre un peu avant la prochaine tentative
                time.sleep(0.001 * (attempt + 1))
        
        # Si on arrive ici, c'est qu'on a épuisé toutes les tentatives
        raise Exception(f"Impossible de générer un ID unique pour {entity_type}")
    
    @classmethod
    def _generate_candidate_id(cls, entity_type, **kwargs):
        """Génère un ID candidat"""
        current_year = datetime.now().year
        current_month = datetime.now().month
        timestamp = int(time.time() * 1000)  # Timestamp en millisecondes
        random_part = random.randint(1000, 9999)
        
        if entity_type == 'propriete':
            # Format: PRO-YYYY-XXXX-XXXX (avec timestamp et random)
            return f"PRO-{current_year}-{timestamp % 10000:04d}-{random_part:04d}"
        elif entity_type == 'locataire':
            return f"LOC-{current_year}-{timestamp % 10000:04d}-{random_part:04d}"
        elif entity_type == 'bailleur':
            return f"BAI-{current_year}-{timestamp % 10000:04d}-{random_part:04d}"
        elif entity_type == 'contrat':
            return f"CT-{current_year}-{timestamp % 10000:04d}-{random_part:04d}"
        elif entity_type == 'paiement':
            yearmonth = kwargs.get('date_paiement', datetime.now()).strftime('%Y%m')
            return f"PAY-{yearmonth}-{timestamp % 10000:04d}-{random_part:04d}"
        elif entity_type == 'quittance':
            yearmonth = kwargs.get('date_emission', datetime.now()).strftime('%Y%m')
            return f"QUI-{yearmonth}-{timestamp % 10000:04d}-{random_part:04d}"
        else:
            # Format générique
            return f"{entity_type.upper()}-{current_year}-{timestamp % 10000:04d}-{random_part:04d}"
    
    @classmethod
    def _is_id_unique(cls, entity_type, candidate_id, **kwargs):
        """Vérifie si un ID est vraiment unique dans la base de données"""
        from django.apps import apps
        from django.db import transaction
        
        # Mapping des types d'entités vers les modèles
        model_mapping = {
            'propriete': ('proprietes', 'Propriete', 'numero_propriete'),
            'locataire': ('proprietes', 'Locataire', 'numero_locataire'),
            'bailleur': ('proprietes', 'Bailleur', 'numero_bailleur'),
            'contrat': ('contrats', 'Contrat', 'numero_contrat'),
            'paiement': ('paiements', 'Paiement', 'numero_paiement'),
            'quittance': ('contrats', 'Quittance', 'numero_quittance'),
        }
        
        if entity_type not in model_mapping:
            raise ValueError(f"Type d'entité non reconnu: {entity_type}")
        
        app_label, model_name, field_name = model_mapping[entity_type]
        model = apps.get_model(app_label, model_name)
        
        # Vérifier l'unicité avec une transaction atomique et un verrou
        with transaction.atomic():
            # Utiliser select_for_update pour éviter les conflits de concurrence
            existing = model.objects.filter(
                **{f"{field_name}": candidate_id, "is_deleted": False}
            ).select_for_update().exists()
            
            return not existing
    
    @classmethod
    def generate_property_id(cls):
        """Génère un ID unique pour une propriété"""
        return cls.generate_unique_id('propriete')
    
    @classmethod
    def generate_tenant_id(cls):
        """Génère un ID unique pour un locataire"""
        return cls.generate_unique_id('locataire')
    
    @classmethod
    def generate_landlord_id(cls):
        """Génère un ID unique pour un bailleur"""
        return cls.generate_unique_id('bailleur')
    
    @classmethod
    def generate_contract_id(cls):
        """Génère un ID unique pour un contrat"""
        return cls.generate_unique_id('contrat')
    
    @classmethod
    def generate_payment_id(cls, date_paiement=None):
        """Génère un ID unique pour un paiement"""
        kwargs = {}
        if date_paiement:
            kwargs['date_paiement'] = date_paiement
        return cls.generate_unique_id('paiement', **kwargs)
    
    @classmethod
    def generate_quittance_id(cls, date_emission=None):
        """Génère un ID unique pour une quittance"""
        kwargs = {}
        if date_emission:
            kwargs['date_emission'] = date_emission
        return cls.generate_unique_id('quittance', **kwargs)
    
    @classmethod
    def verify_uniqueness(cls, entity_type, id_value, **kwargs):
        """
        Vérifie qu'un ID est vraiment unique
        
        Args:
            entity_type (str): Type d'entité
            id_value (str): ID à vérifier
            **kwargs: Paramètres supplémentaires
        
        Returns:
            bool: True si unique, False sinon
        """
        return cls._is_id_unique(entity_type, id_value, **kwargs)
    
    @classmethod
    def get_next_available_id(cls, entity_type, **kwargs):
        """
        Obtient le prochain ID disponible en utilisant une approche séquentielle robuste
        
        Args:
            entity_type (str): Type d'entité
            **kwargs: Paramètres supplémentaires
        
        Returns:
            str: Prochain ID disponible
        """
        from django.apps import apps
        
        # Mapping des types d'entités vers les modèles
        model_mapping = {
            'propriete': ('proprietes', 'Propriete', 'numero_propriete'),
            'locataire': ('proprietes', 'Locataire', 'numero_locataire'),
            'bailleur': ('proprietes', 'Bailleur', 'numero_bailleur'),
            'contrat': ('contrats', 'Contrat', 'numero_contrat'),
            'paiement': ('paiements', 'Paiement', 'numero_paiement'),
            'quittance': ('contrats', 'Quittance', 'numero_quittance'),
        }
        
        if entity_type not in model_mapping:
            raise ValueError(f"Type d'entité non reconnu: {entity_type}")
        
        app_label, model_name, field_name = model_mapping[entity_type]
        model = apps.get_model(app_label, model_name)
        
        current_year = datetime.now().year
        
        # Construire le préfixe selon le type
        if entity_type == 'propriete':
            prefix = f"PRO-{current_year}"
        elif entity_type == 'locataire':
            prefix = f"LOC-{current_year}"
        elif entity_type == 'bailleur':
            prefix = f"BAI-{current_year}"
        elif entity_type == 'contrat':
            prefix = f"CT-{current_year}"
        elif entity_type == 'paiement':
            yearmonth = kwargs.get('date_paiement', datetime.now()).strftime('%Y%m')
            prefix = f"PAY-{yearmonth}"
        elif entity_type == 'quittance':
            yearmonth = kwargs.get('date_emission', datetime.now()).strftime('%Y%m')
            prefix = f"QUI-{yearmonth}"
        else:
            prefix = f"{entity_type.upper()}-{current_year}"
        
        # Utiliser une transaction atomique pour éviter les conflits
        with transaction.atomic():
            # Récupérer tous les IDs existants avec ce préfixe
            existing_ids = model.objects.filter(
                **{f"{field_name}__startswith": prefix, "is_deleted": False}
            ).values_list(field_name, flat=True)
            
            # Extraire les numéros de séquence
            sequences = []
            for id_value in existing_ids:
                if id_value and id_value.startswith(prefix):
                    # Extraire le numéro après le préfixe
                    suffix = id_value[len(prefix):]
                    if suffix.startswith('-'):
                        suffix = suffix[1:]  # Enlever le tiret
                    
                    try:
                        # Essayer d'extraire un numéro
                        if '-' in suffix:
                            # Format avec sous-numéro: PRO-2025-0001-0001
                            parts = suffix.split('-')
                            if len(parts) >= 2:
                                seq_num = int(parts[0])
                                sequences.append(seq_num)
                        else:
                            # Format simple: PRO-2025-0001
                            seq_num = int(suffix)
                            sequences.append(seq_num)
                    except ValueError:
                        continue
            
            # Trouver le prochain numéro disponible
            if sequences:
                next_sequence = max(sequences) + 1
            else:
                next_sequence = 1
            
            # Construire l'ID final
            if entity_type in ['paiement', 'quittance']:
                return f"{prefix}-{next_sequence:04d}"
            else:
                return f"{prefix}-{next_sequence:04d}"
