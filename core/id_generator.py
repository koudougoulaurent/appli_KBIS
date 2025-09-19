"""
Système de génération d'IDs uniques professionnels pour l'entreprise de gestion immobilière
"""

import re
from datetime import datetime
from django.db import models, transaction
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class IDGenerator:
    """
    Générateur d'IDs uniques professionnels avec formats personnalisables
    """
    
    # Configuration des formats d'IDs par type d'entité
    ID_FORMATS = {
        'bailleur': {
            'prefix': 'BAI',
            'format': 'BAI-{year}-{sequence:04d}',
            'description': 'Bailleur (BAI-YYYY-XXXX)',
            'sequence_field': 'numero_bailleur',
            'model': 'proprietes.Bailleur'
        },
        'locataire': {
            'prefix': 'LOC',
            'format': 'LOC-{year}-{sequence:04d}',
            'description': 'Locataire (LOC-YYYY-XXXX)',
            'sequence_field': 'numero_locataire',
            'model': 'proprietes.Locataire'
        },
        'propriete': {
            'prefix': 'PRO',
            'format': 'PRO-{year}-{sequence:04d}',
            'description': 'Propriété (PRO-YYYY-XXXX)',
            'sequence_field': 'numero_propriete',
            'model': 'proprietes.Propriete'
        },
        'contrat': {
            'prefix': 'CT',
            'format': 'CT-{year}-{sequence:04d}',
            'description': 'Contrat (CT-YYYY-XXXX)',
            'sequence_field': 'numero_contrat',
            'model': 'contrats.Contrat'
        },
        'paiement': {
            'prefix': 'PAY',
            'format': 'PAY-{yearmonth}-{sequence:04d}',
            'description': 'Paiement (PAY-YYYYMM-XXXX)',
            'sequence_field': 'numero_paiement',
            'model': 'paiements.Paiement'
        },
        'quittance': {
            'prefix': 'QUI',
            'format': 'QUI-{yearmonth}-{sequence:04d}',
            'description': 'Quittance (QUI-YYYYMM-XXXX)',
            'sequence_field': 'numero_quittance',
            'model': 'contrats.Quittance'
        }
    }
    
    @classmethod
    def generate_id(cls, entity_type, force_new_sequence=False, **kwargs):
        """
        Génère un ID unique pour une entité donnée
        
        Args:
            entity_type (str): Type d'entité (bailleur, locataire, propriete, etc.)
            force_new_sequence (bool): Force une nouvelle séquence même si des gaps existent
            **kwargs: Paramètres supplémentaires (ex: date_paiement pour les paiements)
        
        Returns:
            str: ID unique généré
        """
        if entity_type not in cls.ID_FORMATS:
            raise ValueError(f"Type d'entité non reconnu: {entity_type}")
        
        config = cls.ID_FORMATS[entity_type]
        
        # Obtenir l'année courante
        current_year = datetime.now().year
        
        # Obtenir la séquence suivante
        sequence = cls._get_next_sequence(entity_type, current_year, force_new_sequence=force_new_sequence, **kwargs)
        
        # Générer l'ID selon le format
        if entity_type == 'paiement':
            # Format: PAY-YYYYMM-XXXX
            yearmonth = kwargs.get('date_paiement', datetime.now()).strftime('%Y%m')
            return config['format'].format(yearmonth=yearmonth, sequence=sequence)
        
        elif entity_type == 'quittance':
            # Format: QUI-YYYYMM-XXXX
            yearmonth = kwargs.get('date_emission', datetime.now()).strftime('%Y%m')
            return config['format'].format(yearmonth=yearmonth, sequence=sequence)
        
        else:
            # Format standard: PREFIX-YYYY-XXXX
            return config['format'].format(year=current_year, sequence=sequence)
    
    @classmethod
    def _get_next_sequence(cls, entity_type, year, force_new_sequence=False, **kwargs):
        """
        Obtient la prochaine séquence disponible pour une entité et une année
        
        Args:
            force_new_sequence (bool): Si True, force une nouvelle séquence après la plus haute existante
        """
        config = cls.ID_FORMATS[entity_type]
        model_name = config['model']
        sequence_field = config['sequence_field']
        
        # Importer le modèle dynamiquement
        app_label, model_name = model_name.split('.')
        from django.apps import apps
        model = apps.get_model(app_label, model_name)
        
        # Utiliser une transaction pour éviter les conflits de concurrence
        with transaction.atomic():
            # Construire le filtre pour l'année
            if entity_type == 'paiement':
                # Pour les paiements, filtrer par mois
                if 'date_paiement' in kwargs:
                    date = kwargs['date_paiement']
                    yearmonth = date.strftime('%Y%m')
                    # Extraire l'année et le mois du numéro existant
                    existing_ids = model.objects.filter(
                        **{f"{sequence_field}__startswith": f"PAY-{yearmonth}"}
                    ).values_list(sequence_field, flat=True)
                else:
                    # Utiliser l'année courante
                    existing_ids = model.objects.filter(
                        **{f"{sequence_field}__startswith": f"PAY-{year}"}
                    ).values_list(sequence_field, flat=True)
            
            elif entity_type == 'quittance':
                # Pour les quittances, filtrer par mois
                if 'date_emission' in kwargs:
                    date = kwargs['date_emission']
                    yearmonth = date.strftime('%Y%m')
                    existing_ids = model.objects.filter(
                        **{f"{sequence_field}__startswith": f"QUI-{yearmonth}"}
                    ).values_list(sequence_field, flat=True)
                else:
                    # Utiliser l'année courante
                    existing_ids = model.objects.filter(
                        **{f"{sequence_field}__startswith": f"QUI-{year}"}
                    ).values_list(sequence_field, flat=True)
            
            else:
                # Pour les autres entités, filtrer par année
                existing_ids = model.objects.filter(
                    **{f"{sequence_field}__startswith": f"{config['prefix']}-{year}"}
                ).values_list(sequence_field, flat=True)
            
            # Extraire les séquences existantes
            sequences = []
            for id_value in existing_ids:
                if id_value:
                    # Extraire le numéro de séquence (dernière partie après le dernier tiret)
                    parts = id_value.split('-')
                    if len(parts) >= 2:
                        try:
                            seq_num = int(parts[-1])
                            sequences.append(seq_num)
                        except ValueError:
                            continue
            
            # Retourner la prochaine séquence disponible
            if sequences:
                if force_new_sequence:
                    # Forcer une nouvelle séquence après la plus haute
                    return max(sequences) + 1
                else:
                    # Chercher le premier gap ou retourner max + 1
                    sequences_sorted = sorted(sequences)
                    for i, seq in enumerate(sequences_sorted, 1):
                        if i != seq:
                            return i  # Retourner le premier gap trouvé
                    return max(sequences) + 1  # Pas de gap, retourner max + 1
            else:
                return 1
    
    @classmethod
    def validate_id_format(cls, entity_type, id_value):
        """
        Valide le format d'un ID
        
        Args:
            entity_type (str): Type d'entité
            id_value (str): ID à valider
        
        Returns:
            bool: True si le format est valide
        """
        if entity_type not in cls.ID_FORMATS:
            return False
        
        config = cls.ID_FORMATS[entity_type]
        prefix = config['prefix']
        
        # Patterns de validation selon le type
        if entity_type in ['paiement', 'quittance']:
            # Format: PAY-YYYYMM-XXXX ou QUI-YYYYMM-XXXX
            pattern = rf"^{prefix}-\d{{6}}-\d{{4}}$"
        else:
            # Format: PREFIX-YYYY-XXXX
            pattern = rf"^{prefix}-\d{{4}}-\d{{4}}$"
        
        return bool(re.match(pattern, id_value))
    
    @classmethod
    def get_id_info(cls, entity_type, id_value):
        """
        Extrait les informations d'un ID (année, séquence, etc.)
        
        Args:
            entity_type (str): Type d'entité
            id_value (str): ID à analyser
        
        Returns:
            dict: Informations extraites de l'ID
        """
        if not cls.validate_id_format(entity_type, id_value):
            return None
        
        parts = id_value.split('-')
        
        if entity_type in ['paiement', 'quittance']:
            # Format: PREFIX-YYYYMM-XXXX
            yearmonth = parts[1]
            sequence = int(parts[2])
            year = yearmonth[:4]
            month = yearmonth[4:6]
            
            return {
                'year': int(year),
                'month': int(month),
                'sequence': sequence,
                'yearmonth': yearmonth
            }
        
        else:
            # Format: PREFIX-YYYY-XXXX
            year = int(parts[1])
            sequence = int(parts[2])
            
            return {
                'year': year,
                'sequence': sequence
            }
    
    @classmethod
    def get_available_formats(cls):
        """
        Retourne tous les formats d'IDs disponibles
        
        Returns:
            dict: Formats disponibles avec descriptions
        """
        return {
            entity_type: {
                'format': config['format'],
                'description': config['description'],
                'example': cls._generate_example(entity_type)
            }
            for entity_type, config in cls.ID_FORMATS.items()
        }
    
    @classmethod
    def _generate_example(cls, entity_type):
        """
        Génère un exemple d'ID pour un type d'entité
        """
        current_year = datetime.now().year
        current_month = datetime.now().month
        current_day = datetime.now().day
        
        if entity_type == 'paiement':
            return f"PAY-{current_year:04d}{current_month:02d}-0001"
        elif entity_type == 'quittance':
            return f"QUI-{current_year:04d}{current_month:02d}-0001"
        else:
            return f"{cls.ID_FORMATS[entity_type]['prefix']}-{current_year}-0001"


class IDConfiguration:
    """
    Configuration des IDs uniques pour l'entreprise
    """
    
    @classmethod
    def get_company_prefix(cls):
        """
        Retourne le préfixe de l'entreprise (configurable)
        """
        # TODO: Rendre configurable via les paramètres de l'entreprise
        return "GESTIMMOB"
    
    @classmethod
    def get_custom_formats(cls):
        """
        Retourne des formats personnalisés pour l'entreprise
        """
        return {
            'bailleur': {
                'prefix': 'BLR',
                'format': '{company}-BLR-{year}-{sequence:04d}',
                'description': 'Bailleur avec préfixe entreprise'
            },
            'locataire': {
                'prefix': 'LOC',
                'format': '{company}-LOC-{year}-{sequence:04d}',
                'description': 'Locataire avec préfixe entreprise'
            }
        }
    
    @classmethod
    def get_sequence_reset_policy(cls):
        """
        Définit la politique de réinitialisation des séquences
        """
        return {
            'bailleur': 'yearly',      # Réinitialisation annuelle
            'locataire': 'yearly',     # Réinitialisation annuelle
            'propriete': 'yearly',     # Réinitialisation annuelle
            'contrat': 'yearly',       # Réinitialisation annuelle
            'paiement': 'monthly',     # Réinitialisation mensuelle
            'quittance': 'monthly'     # Réinitialisation mensuelle
        }


# Fonctions utilitaires pour faciliter l'utilisation
def generate_bailleur_id():
    """Génère un ID unique pour un bailleur"""
    return IDGenerator.generate_id('bailleur')

def generate_locataire_id():
    """Génère un ID unique pour un locataire"""
    return IDGenerator.generate_id('locataire')

def generate_propriete_id():
    """Génère un ID unique pour une propriété"""
    return IDGenerator.generate_id('propriete')

def generate_contrat_id():
    """Génère un ID unique pour un contrat"""
    return IDGenerator.generate_id('contrat')

def generate_paiement_id(date_paiement=None):
    """Génère un ID unique pour un paiement"""
    kwargs = {}
    if date_paiement:
        kwargs['date_paiement'] = date_paiement
    return IDGenerator.generate_id('paiement', **kwargs)

def generate_quittance_id(date_emission=None):
    """Génère un ID unique pour une quittance"""
    kwargs = {}
    if date_emission:
        kwargs['date_emission'] = date_emission
    return IDGenerator.generate_id('quittance', **kwargs)
