"""
Signals pour la gestion automatique des contrats de gestion immobilière
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from django.utils import timezone
from .models import Bailleur, Propriete, ContratGestion
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Propriete)
def creer_contrat_gestion_automatique(sender, instance, created, **kwargs):
    """
    Crée automatiquement un contrat de gestion UNIQUE pour un bailleur.
    Un bailleur ne peut avoir qu'UN SEUL contrat de gestion qui inclut TOUTES ses propriétés.
    """
    if not created:
        return
    
    if not instance.bailleur:
        return
    
    try:
        with transaction.atomic():
            bailleur = instance.bailleur
            
            # Récupérer ou créer le contrat de gestion UNIQUE pour ce bailleur
            contrat_gestion = ContratGestion.objects.filter(
                bailleur=bailleur,
                is_deleted=False
            ).first()
            
            if contrat_gestion:
                # Le contrat existe déjà, ajouter la nouvelle propriété et s'assurer que toutes les propriétés sont incluses
                contrat_gestion.proprietes.add(instance)
                # Mettre à jour pour inclure toutes les propriétés du bailleur
                proprietes_bailleur = Propriete.objects.filter(
                    bailleur=bailleur,
                    is_deleted=False
                )
                contrat_gestion.proprietes.set(proprietes_bailleur)
                logger.info(f"Propriété {instance.id} ajoutée au contrat de gestion unique {contrat_gestion.numero_contrat}")
            else:
                # Créer un nouveau contrat de gestion UNIQUE pour ce bailleur
                proprietes_bailleur = Propriete.objects.filter(
                    bailleur=bailleur,
                    is_deleted=False
                )
                
                if not proprietes_bailleur.exists():
                    return
                
                contrat_gestion = ContratGestion.objects.create(
                    bailleur=bailleur,
                    date_signature=timezone.now().date(),
                    date_debut=timezone.now().date(),
                    commission_percentage=10.00,  # Commission par défaut de 10%
                    est_actif=True,
                    est_resilie=False,
                )
                
                # Ajouter TOUTES les propriétés du bailleur au contrat
                contrat_gestion.proprietes.set(proprietes_bailleur)
                
                logger.info(f"Contrat de gestion UNIQUE {contrat_gestion.numero_contrat} créé automatiquement pour le bailleur {bailleur.id}")
                logger.info(f"Contrat de gestion {contrat_gestion.numero_contrat} prêt pour génération PDF automatique")
            
    except Exception as e:
        logger.error(f"Erreur lors de la création automatique du contrat de gestion: {str(e)}")
        # Ne pas bloquer la création de la propriété en cas d'erreur


@receiver(post_save, sender=Bailleur)
def creer_contrat_gestion_apres_bailleur(sender, instance, created, **kwargs):
    """
    Crée un contrat de gestion UNIQUE si le bailleur a déjà des propriétés lors de sa création.
    Un bailleur ne peut avoir qu'UN SEUL contrat de gestion.
    Note: Ce signal est déclenché après la création du bailleur, mais les propriétés
    sont généralement créées après, donc le signal sur Propriete est plus approprié.
    """
    if not created:
        return
    
    try:
        # Vérifier si le bailleur a déjà des propriétés (cas rare mais possible)
        proprietes_bailleur = Propriete.objects.filter(
            bailleur=instance,
            is_deleted=False
        )
        
        if proprietes_bailleur.exists():
            # Vérifier si un contrat existe déjà - UN SEUL contrat par bailleur
            contrat_existant = ContratGestion.objects.filter(
                bailleur=instance,
                is_deleted=False
            ).first()
            
            if not contrat_existant:
                with transaction.atomic():
                    # Créer le contrat de gestion UNIQUE pour ce bailleur
                    contrat_gestion = ContratGestion.objects.create(
                        bailleur=instance,
                        date_signature=timezone.now().date(),
                        date_debut=timezone.now().date(),
                        commission_percentage=10.00,
                        est_actif=True,
                        est_resilie=False,
                    )
                    
                    # Ajouter TOUTES les propriétés du bailleur au contrat
                    contrat_gestion.proprietes.set(proprietes_bailleur)
                    
                    logger.info(f"Contrat de gestion UNIQUE {contrat_gestion.numero_contrat} créé automatiquement pour le bailleur {instance.id}")
                    logger.info(f"Contrat de gestion {contrat_gestion.numero_contrat} prêt pour génération PDF automatique")
            else:
                # Le contrat existe déjà, s'assurer que toutes les propriétés sont incluses
                contrat_existant.proprietes.set(proprietes_bailleur)
                logger.info(f"Contrat de gestion existant {contrat_existant.numero_contrat} mis à jour avec toutes les propriétés du bailleur {instance.id}")
                    
    except Exception as e:
        logger.error(f"Erreur lors de la création automatique du contrat de gestion après création du bailleur: {str(e)}")


