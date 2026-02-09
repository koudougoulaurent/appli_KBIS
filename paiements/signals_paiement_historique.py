"""
Signaux pour la gestion automatique des paiements historiques et synchronisation
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Paiement


@receiver(post_save, sender=Paiement)
def synchroniser_prochain_paiement_apres_ajout(sender, instance, created, **kwargs):
    """
    Signal qui se déclenche automatiquement après la création ou modification d'un paiement.
    Recalcule le prochain paiement dû pour le contrat concerné.
    
    Particulièrement utile pour les paiements historiques importés de l'ancienne plateforme.
    """
    # Ne rien faire si le paiement est supprimé logiquement
    if instance.is_deleted:
        return
    
    # Ne rien faire si le paiement n'est pas validé
    if instance.statut != 'valide':
        return
    
    # Ne synchroniser que pour les paiements de loyer
    if instance.type_paiement not in ['loyer', 'avance', 'avance_loyer']:
        return
    
    try:
        from paiements.services_avance import ServiceGestionAvance
        
        # Recalculer le prochain mois de paiement
        contrat = instance.contrat
        prochain_mois = ServiceGestionAvance.calculer_prochain_mois_paiement(contrat)
        
        # Log pour debug (visible dans la console)
        prefix = "📦 HISTORIQUE" if instance.est_saisie_manuelle_historique else "🔄"
        print(f"{prefix} Contrat {contrat.numero_contrat} synchronisé - "
              f"Prochain paiement: {prochain_mois.strftime('%B %Y')}")
        
    except Exception as e:
        # Log l'erreur sans bloquer la sauvegarde
        print(f"⚠️ Erreur lors de la synchronisation du contrat {instance.contrat.numero_contrat}: {str(e)}")
