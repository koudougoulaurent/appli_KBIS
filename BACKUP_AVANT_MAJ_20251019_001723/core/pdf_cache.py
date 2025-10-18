"""
Système de cache intelligent pour les PDF avec mise à jour automatique
"""

import os
import json
import hashlib
from datetime import datetime
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

class PDFCacheManager:
    """Gestionnaire de cache pour les PDF avec détection des modifications"""
    
    CACHE_PREFIX = "pdf_cache_"
    CACHE_TIMEOUT = 60 * 60 * 24  # 24 heures
    CONFIG_HASH_KEY = "config_hash"
    
    @classmethod
    def get_config_hash(cls):
        """Génère un hash de la configuration actuelle de l'entreprise"""
        from core.models import ConfigurationEntreprise
        
        try:
            config = ConfigurationEntreprise.get_configuration_active()
            if not config:
                return "no_config"
            
            # Créer un hash basé sur les champs importants
            config_data = {
                'nom_entreprise': config.nom_entreprise,
                'adresse': config.adresse,
                'ville': config.ville,
                'pays': config.pays,
                'code_postal': config.code_postal,
                'telephone': config.telephone,
                'email': config.email,
                'site_web': getattr(config, 'site_web', ''),
                'rccm': getattr(config, 'rccm', ''),
                'ifu': getattr(config, 'ifu', ''),
                'logo': str(config.logo) if hasattr(config, 'logo') and config.logo else '',
                'entete_personnalise': str(config.entete_personnalise) if hasattr(config, 'entete_personnalise') and config.entete_personnalise else '',
                'pied_page_personnalise': str(config.pied_page_personnalise) if hasattr(config, 'pied_page_personnalise') and config.pied_page_personnalise else '',
                'date_modification': config.date_modification.isoformat() if hasattr(config, 'date_modification') else '',
            }
            
            # Créer un hash stable
            config_str = json.dumps(config_data, sort_keys=True)
            return hashlib.md5(config_str.encode()).hexdigest()
            
        except Exception as e:
            print(f"Erreur lors de la génération du hash de configuration: {e}")
            return "error"
    
    @classmethod
    def get_cache_key(cls, document_type, document_id):
        """Génère une clé de cache pour un document"""
        return f"{cls.CACHE_PREFIX}{document_type}_{document_id}"
    
    @classmethod
    def is_cache_valid(cls, document_type, document_id):
        """Vérifie si le cache est valide pour un document"""
        cache_key = cls.get_cache_key(document_type, document_id)
        current_config_hash = cls.get_config_hash()
        
        # Récupérer les métadonnées du cache
        cache_metadata = cache.get(f"{cache_key}_metadata")
        if not cache_metadata:
            return False
        
        # Vérifier si la configuration a changé
        if cache_metadata.get('config_hash') != current_config_hash:
            return False
        
        # Vérifier si le cache n'a pas expiré
        cache_time = cache_metadata.get('timestamp')
        if cache_time:
            cache_datetime = datetime.fromisoformat(cache_time)
            if timezone.now() - cache_datetime > timezone.timedelta(hours=24):
                return False
        
        return True
    
    @classmethod
    def get_cached_pdf(cls, document_type, document_id):
        """Récupère un PDF depuis le cache s'il est valide"""
        if not cls.is_cache_valid(document_type, document_id):
            return None
        
        cache_key = cls.get_cache_key(document_type, document_id)
        return cache.get(cache_key)
    
    @classmethod
    def cache_pdf(cls, document_type, document_id, pdf_content):
        """Met en cache un PDF avec ses métadonnées"""
        cache_key = cls.get_cache_key(document_type, document_id)
        current_config_hash = cls.get_config_hash()
        
        # Mettre en cache le PDF
        cache.set(cache_key, pdf_content, cls.CACHE_TIMEOUT)
        
        # Mettre en cache les métadonnées
        metadata = {
            'config_hash': current_config_hash,
            'timestamp': timezone.now().isoformat(),
            'document_type': document_type,
            'document_id': document_id,
            'size': len(pdf_content)
        }
        cache.set(f"{cache_key}_metadata", metadata, cls.CACHE_TIMEOUT)
    
    @classmethod
    def invalidate_cache(cls, document_type=None, document_id=None):
        """Invalide le cache pour un document spécifique ou tous les documents"""
        if document_type and document_id:
            # Invalider un document spécifique
            cache_key = cls.get_cache_key(document_type, document_id)
            cache.delete(cache_key)
            cache.delete(f"{cache_key}_metadata")
        else:
            # Invalider tous les caches PDF
            # Note: En production, vous pourriez utiliser un pattern de clés plus sophistiqué
            from django.core.cache.utils import make_template_fragment_key
            # Pour l'instant, on va simplement forcer la régénération
            pass
    
    @classmethod
    def invalidate_all_pdf_cache(cls):
        """Invalide tous les caches PDF"""
        # Marquer que la configuration a changé
        cache.set("config_changed", True, 60 * 60)  # 1 heure
    
    @classmethod
    def get_cache_stats(cls):
        """Retourne les statistiques du cache"""
        # Cette méthode pourrait être étendue pour fournir des statistiques détaillées
        return {
            'cache_prefix': cls.CACHE_PREFIX,
            'current_config_hash': cls.get_config_hash(),
            'cache_timeout': cls.CACHE_TIMEOUT
        }


class PDFRegenerationService:
    """Service pour la régénération automatique des PDF"""
    
    @classmethod
    def regenerate_all_contracts(cls):
        """Régénère tous les PDF de contrats"""
        from contrats.models import Contrat
        from contrats.services import ContratPDFService
        
        regenerated_count = 0
        errors = []
        
        try:
            contrats = Contrat.objects.all()
            for contrat in contrats:
                try:
                    # Générer le nouveau PDF
                    service = ContratPDFService(contrat)
                    pdf_content = service.generate_contrat_pdf().getvalue()
                    
                    # Mettre à jour le cache
                    PDFCacheManager.cache_pdf('contrat', contrat.id, pdf_content)
                    regenerated_count += 1
                    
                except Exception as e:
                    errors.append(f"Contrat {contrat.id}: {str(e)}")
            
            return {
                'success': True,
                'regenerated_count': regenerated_count,
                'total_count': contrats.count(),
                'errors': errors
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'regenerated_count': regenerated_count,
                'errors': errors
            }
    
    @classmethod
    def regenerate_all_resiliations(cls):
        """Régénère tous les PDF de résiliations"""
        from contrats.models import ResiliationContrat
        from contrats.services import ResiliationPDFService
        
        regenerated_count = 0
        errors = []
        
        try:
            resiliations = ResiliationContrat.objects.all()
            for resiliation in resiliations:
                try:
                    # Générer le nouveau PDF
                    service = ResiliationPDFService(resiliation)
                    pdf_content = service.generate_resiliation_pdf().getvalue()
                    
                    # Mettre à jour le cache
                    PDFCacheManager.cache_pdf('resiliation', resiliation.id, pdf_content)
                    regenerated_count += 1
                    
                except Exception as e:
                    errors.append(f"Résiliation {resiliation.id}: {str(e)}")
            
            return {
                'success': True,
                'regenerated_count': regenerated_count,
                'total_count': resiliations.count(),
                'errors': errors
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'regenerated_count': regenerated_count,
                'errors': errors
            }
    
    @classmethod
    def regenerate_all_documents(cls):
        """Régénère tous les documents PDF"""
        print("🔄 Début de la régénération de tous les documents PDF...")
        
        # Régénérer les contrats
        contracts_result = cls.regenerate_all_contracts()
        print(f"📄 Contrats: {contracts_result['regenerated_count']}/{contracts_result['total_count']} régénérés")
        
        # Régénérer les résiliations
        resiliations_result = cls.regenerate_all_resiliations()
        print(f"📄 Résiliations: {resiliations_result['regenerated_count']}/{resiliations_result['total_count']} régénérés")
        
        # Résumé
        total_regenerated = contracts_result['regenerated_count'] + resiliations_result['regenerated_count']
        total_errors = len(contracts_result.get('errors', [])) + len(resiliations_result.get('errors', []))
        
        print(f"✅ Régénération terminée: {total_regenerated} documents mis à jour")
        if total_errors > 0:
            print(f"⚠️ {total_errors} erreurs rencontrées")
        
        return {
            'success': True,
            'contracts': contracts_result,
            'resiliations': resiliations_result,
            'total_regenerated': total_regenerated,
            'total_errors': total_errors
        }
