"""
Système de prévention des doublons pour garantir l'unicité absolue
"""

import logging
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db.models import Q

logger = logging.getLogger(__name__)

class DuplicatePreventionSystem:
    """
    Système de prévention des doublons avec monitoring et alertes
    """
    
    @staticmethod
    def check_property_number_uniqueness(numero_propriete, exclude_pk=None):
        """
        Vérifie l'unicité d'un numéro de propriété avec monitoring
        
        Args:
            numero_propriete (str): Numéro à vérifier
            exclude_pk (int): PK à exclure (pour les modifications)
        
        Returns:
            bool: True si unique, False si doublon
        """
        from proprietes.models import Propriete
        
        try:
            queryset = Propriete.objects.filter(
                numero_propriete=numero_propriete,
                is_deleted=False
            )
            
            if exclude_pk:
                queryset = queryset.exclude(pk=exclude_pk)
            
            is_unique = not queryset.exists()
            
            if not is_unique:
                # Log de l'alerte de doublon
                logger.warning(
                    f"DOUBLON_DETECTE: Numéro de propriété '{numero_propriete}' existe déjà. "
                    f"Exclude PK: {exclude_pk}, Time: {timezone.now()}"
                )
                
                # Envoyer une alerte de sécurité
                DuplicatePreventionSystem._send_duplicate_alert(
                    'property_number',
                    numero_propriete,
                    'Numéro de propriété dupliqué détecté'
                )
            
            return is_unique
            
        except Exception as e:
            logger.error(f"Erreur lors de la vérification d'unicité: {e}")
            return False
    
    @staticmethod
    def check_bailleur_number_uniqueness(numero_bailleur, exclude_pk=None):
        """
        Vérifie l'unicité d'un numéro de bailleur
        """
        from proprietes.models import Bailleur
        
        try:
            queryset = Bailleur.objects.filter(
                numero_bailleur=numero_bailleur,
                is_deleted=False
            )
            
            if exclude_pk:
                queryset = queryset.exclude(pk=exclude_pk)
            
            is_unique = not queryset.exists()
            
            if not is_unique:
                logger.warning(
                    f"DOUBLON_DETECTE: Numéro de bailleur '{numero_bailleur}' existe déjà. "
                    f"Exclude PK: {exclude_pk}, Time: {timezone.now()}"
                )
                
                DuplicatePreventionSystem._send_duplicate_alert(
                    'bailleur_number',
                    numero_bailleur,
                    'Numéro de bailleur dupliqué détecté'
                )
            
            return is_unique
            
        except Exception as e:
            logger.error(f"Erreur lors de la vérification d'unicité bailleur: {e}")
            return False
    
    @staticmethod
    def check_locataire_number_uniqueness(numero_locataire, exclude_pk=None):
        """
        Vérifie l'unicité d'un numéro de locataire
        """
        from proprietes.models import Locataire
        
        try:
            queryset = Locataire.objects.filter(
                numero_locataire=numero_locataire,
                is_deleted=False
            )
            
            if exclude_pk:
                queryset = queryset.exclude(pk=exclude_pk)
            
            is_unique = not queryset.exists()
            
            if not is_unique:
                logger.warning(
                    f"DOUBLON_DETECTE: Numéro de locataire '{numero_locataire}' existe déjà. "
                    f"Exclude PK: {exclude_pk}, Time: {timezone.now()}"
                )
                
                DuplicatePreventionSystem._send_duplicate_alert(
                    'locataire_number',
                    numero_locataire,
                    'Numéro de locataire dupliqué détecté'
                )
            
            return is_unique
            
        except Exception as e:
            logger.error(f"Erreur lors de la vérification d'unicité locataire: {e}")
            return False
    
    @staticmethod
    def _send_duplicate_alert(alert_type, value, message):
        """
        Envoie une alerte de doublon détecté
        """
        try:
            # Log structuré pour monitoring
            logger.error(
                f"DUPLICATE_ALERT: Type={alert_type}, Value={value}, "
                f"Message={message}, Time={timezone.now()}"
            )
            
            # TODO: Intégrer avec un système d'alertes (email, Slack, etc.)
            # Pour l'instant, on log seulement
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi d'alerte: {e}")
    
    @staticmethod
    def get_duplicate_statistics():
        """
        Obtient les statistiques de doublons détectés
        """
        from proprietes.models import Propriete, Bailleur, Locataire
        
        stats = {
            'property_duplicates': 0,
            'bailleur_duplicates': 0,
            'locataire_duplicates': 0,
            'total_duplicates': 0
        }
        
        try:
            # Compter les doublons de propriétés
            property_duplicates = Propriete.objects.values('numero_propriete').annotate(
                count=models.Count('id')
            ).filter(count__gt=1, is_deleted=False)
            stats['property_duplicates'] = property_duplicates.count()
            
            # Compter les doublons de bailleurs
            bailleur_duplicates = Bailleur.objects.values('numero_bailleur').annotate(
                count=models.Count('id')
            ).filter(count__gt=1, is_deleted=False)
            stats['bailleur_duplicates'] = bailleur_duplicates.count()
            
            # Compter les doublons de locataires
            locataire_duplicates = Locataire.objects.values('numero_locataire').annotate(
                count=models.Count('id')
            ).filter(count__gt=1, is_deleted=False)
            stats['locataire_duplicates'] = locataire_duplicates.count()
            
            stats['total_duplicates'] = (
                stats['property_duplicates'] + 
                stats['bailleur_duplicates'] + 
                stats['locataire_duplicates']
            )
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul des statistiques de doublons: {e}")
        
        return stats
    
    @staticmethod
    def cleanup_duplicates():
        """
        Nettoie les doublons existants (à utiliser avec précaution)
        """
        from proprietes.models import Propriete, Bailleur, Locataire
        from django.db import models
        
        cleaned_count = 0
        
        try:
            # Nettoyer les doublons de propriétés
            property_duplicates = Propriete.objects.values('numero_propriete').annotate(
                count=models.Count('id')
            ).filter(count__gt=1, is_deleted=False)
            
            for duplicate in property_duplicates:
                numero = duplicate['numero_propriete']
                # Garder le plus ancien, marquer les autres comme supprimés
                properties = Propriete.objects.filter(
                    numero_propriete=numero,
                    is_deleted=False
                ).order_by('date_creation')
                
                # Garder le premier, supprimer les autres
                for i, prop in enumerate(properties):
                    if i > 0:  # Pas le premier
                        prop.is_deleted = True
                        prop.save()
                        cleaned_count += 1
                        logger.info(f"Doublon de propriété supprimé: {numero} (PK: {prop.pk})")
            
            # Répéter pour bailleurs et locataires...
            
        except Exception as e:
            logger.error(f"Erreur lors du nettoyage des doublons: {e}")
        
        return cleaned_count


class DuplicatePreventionMiddleware:
    """
    Middleware pour surveiller les tentatives de création de doublons
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Surveiller les erreurs de validation de doublons
        if hasattr(request, 'duplicate_attempts'):
            for attempt in request.duplicate_attempts:
                logger.warning(
                    f"TENTATIVE_DOUBLON: {attempt['type']} = {attempt['value']}, "
                    f"IP: {request.META.get('REMOTE_ADDR')}, "
                    f"User: {getattr(request, 'user', 'Anonymous')}"
                )
        
        return response
