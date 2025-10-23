"""
Signaux Ultra-Intelligents pour les Notifications Dynamiques
Gestion automatique des notifications basée sur les événements système
"""
from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from datetime import datetime, timedelta, date
import logging

from .models import Notification
from .services_notifications_dynamiques import ServiceNotificationsDynamiques
from paiements.models import Paiement, AvanceLoyer
from contrats.models import Contrat
from proprietes.models import Locataire, Bailleur
from paiements.models_retraits import RetraitBailleur

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Paiement)
def notifier_paiement_recu(sender, instance, created, **kwargs):
    """
    Notification automatique pour paiement reçu
    """
    if created and instance.statut == 'valide':
        try:
            ServiceNotificationsDynamiques.notifier_paiement_recu(instance)
            logger.info(f"Notification paiement créée pour {instance.id}")
        except Exception as e:
            logger.error(f"Erreur notification paiement {instance.id}: {str(e)}")


@receiver(pre_save, sender=Paiement)
def detecter_paiement_partiel(sender, instance, **kwargs):
    """
    Détection automatique des paiements partiels
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


@receiver(post_save, sender=AvanceLoyer)
def notifier_avance_consommee(sender, instance, created, **kwargs):
    """
    Notification pour consommation d'avance
    """
    if not created and instance.statut == 'consommee':
        try:
            # Calculer les mois consommés
            mois_consommes = instance.nombre_mois_couverts - (instance.montant_restant / instance.contrat.loyer_mensuel)
            ServiceNotificationsDynamiques.notifier_avance_consommee(instance, int(mois_consommes))
            logger.info(f"Notification avance consommée pour {instance.id}")
        except Exception as e:
            logger.error(f"Erreur notification avance {instance.id}: {str(e)}")


@receiver(post_save, sender=RetraitBailleur)
def notifier_retrait_cree(sender, instance, created, **kwargs):
    """
    Notification pour retrait créé
    """
    if created:
        try:
            ServiceNotificationsDynamiques.notifier_retrait_cree(instance)
            logger.info(f"Notification retrait créée pour {instance.id}")
        except Exception as e:
            logger.error(f"Erreur notification retrait {instance.id}: {str(e)}")


@receiver(post_save, sender=Contrat)
def notifier_contrat_expirant(sender, instance, created, **kwargs):
    """
    Notification pour contrat expirant (30 jours avant)
    """
    if not created:  # Modification d'un contrat existant
        try:
            aujourd_hui = date.today()
            jours_restants = (instance.date_fin - aujourd_hui).days
            
            # Notifier si le contrat expire dans 30 jours ou moins
            if 0 <= jours_restants <= 30:
                ServiceNotificationsDynamiques.notifier_contrat_expirant(instance, jours_restants)
                logger.info(f"Notification contrat expirant pour {instance.id}")
        except Exception as e:
            logger.error(f"Erreur notification contrat {instance.id}: {str(e)}")


# ===== NOTIFICATIONS PÉRIODIQUES =====

def verifier_retards_paiement():
    """
    Vérifie les retards de paiement et envoie des notifications
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
                ServiceNotificationsDynamiques.notifier_retard_paiement(contrat, jours_retard)
                
    except Exception as e:
        logger.error(f"Erreur vérification retards: {str(e)}")


def verifier_contrats_expirants():
    """
    Vérifie les contrats expirants et envoie des notifications
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
            ServiceNotificationsDynamiques.notifier_contrat_expirant(contrat, jours_restants)
            
    except Exception as e:
        logger.error(f"Erreur vérification contrats expirants: {str(e)}")


def nettoyer_notifications_anciennes():
    """
    Nettoie les notifications anciennes (plus de 30 jours)
    """
    try:
        count = ServiceNotificationsDynamiques.nettoyer_notifications_anciennes(30)
        logger.info(f"Notifications anciennes nettoyées: {count}")
    except Exception as e:
        logger.error(f"Erreur nettoyage notifications: {str(e)}")


# ===== NOTIFICATIONS SYSTÈME =====

def notifier_erreur_systeme(message, details=None):
    """
    Notification d'erreur système
    """
    try:
        message_complet = f"Erreur système: {message}"
        if details:
            message_complet += f" Détails: {details}"
            
        ServiceNotificationsDynamiques.notifier_alerte_systeme(message_complet, 'high')
        logger.error(f"Notification erreur système: {message}")
    except Exception as e:
        logger.error(f"Erreur notification système: {str(e)}")


def notifier_synchronisation_complete(type_sync, details):
    """
    Notification de synchronisation terminée
    """
    try:
        ServiceNotificationsDynamiques.notifier_synchronisation_complete(type_sync, details)
        logger.info(f"Notification synchronisation: {type_sync}")
    except Exception as e:
        logger.error(f"Erreur notification synchronisation: {str(e)}")


# ===== COMMANDES DE GESTION =====

def envoyer_notifications_retards():
    """
    Envoie les notifications de retard de paiement
    """
    verifier_retards_paiement()


def envoyer_notifications_contrats():
    """
    Envoie les notifications de contrats expirants
    """
    verifier_contrats_expirants()


def maintenance_notifications():
    """
    Maintenance des notifications
    """
    nettoyer_notifications_anciennes()


