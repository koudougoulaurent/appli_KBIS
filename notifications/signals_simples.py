"""
Signaux Simples pour les Notifications
Gestion automatique simple des notifications
"""
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import datetime, timedelta, date
import logging

from .services_notifications_simples import ServiceNotificationsSimples
from paiements.models import Paiement, AvanceLoyer
from contrats.models import Contrat
from proprietes.models import Locataire, Bailleur
from paiements.models import RetraitBailleur

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Paiement)
def notifier_paiement_recu_simple(sender, instance, created, **kwargs):
    """
    Notification simple pour paiement reçu
    """
    if created and instance.statut == 'valide':
        try:
            ServiceNotificationsSimples.notifier_paiement_recu_simple(instance)
            logger.info(f"Notification simple paiement créée pour {instance.id}")
        except Exception as e:
            logger.error(f"Erreur notification simple paiement {instance.id}: {str(e)}")


@receiver(pre_save, sender=Paiement)
def detecter_paiement_partiel_simple(sender, instance, **kwargs):
    """
    Détection simple des paiements partiels
    """
    if instance.pk:  # Modification d'un paiement existant
        try:
            ancien_paiement = Paiement.objects.get(pk=instance.pk)
            
            # Vérifier si le montant a changé et si c'est un paiement partiel
            if (ancien_paiement.montant != instance.montant and 
                instance.montant < instance.montant_du_mois and
                instance.montant_du_mois > 0):
                
                instance.est_paiement_partiel = True
                instance.montant_restant_du = instance.montant_du_mois - instance.montant
                
                # Ajouter des données extra
                instance.data_extra = {
                    'montant_original': float(ancien_paiement.montant),
                    'montant_nouveau': float(instance.montant),
                    'montant_du': float(instance.montant_du_mois),
                    'montant_restant': float(instance.montant_restant_du),
                    'pourcentage_paye': round((instance.montant / instance.montant_du_mois) * 100, 2)
                }
                
        except Paiement.DoesNotExist:
            pass


@receiver(post_save, sender=RetraitBailleur)
def notifier_retrait_cree_simple(sender, instance, created, **kwargs):
    """
    Notification simple pour retrait créé
    """
    if created:
        try:
            ServiceNotificationsSimples.notifier_retrait_cree_simple(instance)
            logger.info(f"Notification simple retrait créée pour {instance.id}")
        except Exception as e:
            logger.error(f"Erreur notification simple retrait {instance.id}: {str(e)}")


@receiver(post_save, sender=Contrat)
def notifier_contrat_expirant_simple(sender, instance, created, **kwargs):
    """
    Notification simple pour contrat expirant (30 jours avant)
    """
    if not created:  # Modification d'un contrat existant
        try:
            aujourd_hui = date.today()
            jours_restants = (instance.date_fin - aujourd_hui).days
            
            # Notifier si le contrat expire dans 30 jours ou moins
            if 0 <= jours_restants <= 30:
                ServiceNotificationsSimples.notifier_contrat_expirant_simple(instance, jours_restants)
                logger.info(f"Notification simple contrat expirant pour {instance.id}")
        except Exception as e:
            logger.error(f"Erreur notification simple contrat {instance.id}: {str(e)}")


# ===== NOTIFICATIONS PÉRIODIQUES SIMPLES =====

def verifier_retards_paiement_simple():
    """
    Vérifie les retards de paiement et envoie des notifications simples
    """
    try:
        aujourd_hui = date.today()
        
        # Récupérer tous les contrats actifs
        contrats = Contrat.objects.filter(
            date_fin__gte=aujourd_hui,
            is_deleted=False
        )
        
        for contrat in contrats:
            # Vérifier si le loyer du mois est en retard
            premier_du_mois = aujourd_hui.replace(day=1)
            dernier_du_mois = (premier_du_mois + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            
            # Vérifier s'il y a un paiement pour ce mois
            paiement_mois = Paiement.objects.filter(
                contrat=contrat,
                date_paiement__gte=premier_du_mois,
                date_paiement__lte=dernier_du_mois,
                statut='valide'
            ).first()
            
            if not paiement_mois and aujourd_hui.day > 5:  # Retard après le 5 du mois
                jours_retard = aujourd_hui.day - 5
                ServiceNotificationsSimples.notifier_retard_paiement_simple(contrat, jours_retard)
                
    except Exception as e:
        logger.error(f"Erreur vérification retards simples: {str(e)}")


def verifier_contrats_expirants_simple():
    """
    Vérifie les contrats expirants et envoie des notifications simples
    """
    try:
        aujourd_hui = date.today()
        
        # Contrats expirant dans 30 jours
        date_limite = aujourd_hui + timedelta(days=30)
        
        contrats_expirants = Contrat.objects.filter(
            date_fin__lte=date_limite,
            date_fin__gte=aujourd_hui,
            is_deleted=False
        )
        
        for contrat in contrats_expirants:
            jours_restants = (contrat.date_fin - aujourd_hui).days
            ServiceNotificationsSimples.notifier_contrat_expirant_simple(contrat, jours_restants)
            
    except Exception as e:
        logger.error(f"Erreur vérification contrats expirants simples: {str(e)}")


def nettoyer_notifications_anciennes_simple():
    """
    Nettoie les notifications anciennes de manière simple
    """
    try:
        count = ServiceNotificationsSimples.nettoyer_notifications_anciennes_simple(30)
        logger.info(f"Notifications anciennes nettoyées: {count}")
    except Exception as e:
        logger.error(f"Erreur nettoyage notifications simples: {str(e)}")


# ===== NOTIFICATIONS SYSTÈME SIMPLES =====

def notifier_erreur_systeme_simple(message):
    """
    Notification simple d'erreur système
    """
    try:
        ServiceNotificationsSimples.notifier_alerte_systeme_simple(message)
        logger.error(f"Notification simple erreur système: {message}")
    except Exception as e:
        logger.error(f"Erreur notification simple système: {str(e)}")


def notifier_info_systeme_simple(message):
    """
    Notification simple d'information système
    """
    try:
        from utilisateurs.models import Utilisateur
        recipients = Utilisateur.objects.filter(
            groupe_travail__nom__in=['PRIVILEGE', 'ADMINISTRATION']
        )
        
        for recipient in recipients:
            ServiceNotificationsSimples.notifier_info_simple(recipient, message)
            
    except Exception as e:
        logger.error(f"Erreur notification simple info: {str(e)}")


# ===== COMMANDES DE GESTION SIMPLES =====

def envoyer_notifications_retards_simple():
    """
    Envoie les notifications de retard de paiement de manière simple
    """
    verifier_retards_paiement_simple()


def envoyer_notifications_contrats_simple():
    """
    Envoie les notifications de contrats expirants de manière simple
    """
    verifier_contrats_expirants_simple()


def maintenance_notifications_simple():
    """
    Maintenance simple des notifications
    """
    nettoyer_notifications_anciennes_simple()
