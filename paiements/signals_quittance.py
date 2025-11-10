from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.db import transaction
from .models import Paiement, QuittancePaiement


@receiver(post_save, sender=Paiement)
def generer_quittance_automatique(sender, instance, created, **kwargs):
    """
    Génère automatiquement une quittance quand un paiement est validé
    """
    # Seulement pour les nouveaux paiements validés
    if created and instance.statut == 'valide':
        try:
            # Vérifier si une quittance existe déjà
            if not hasattr(instance, 'quittance'):
                # Créer la quittance automatiquement
                quittance = QuittancePaiement.objects.create(
                    paiement=instance,
                    cree_par=instance.cree_par if hasattr(instance, 'cree_par') else None
                )
                print(f"Quittance générée automatiquement: {quittance.numero_quittance}")
        except Exception as e:
            print(f"Erreur génération quittance automatique: {e}")


@receiver(post_save, sender=Paiement)
def generer_quittance_validation(sender, instance, created, **kwargs):
    """
    Génère une quittance quand un paiement passe de 'en_attente' à 'valide'
    """
    # Si le paiement vient d'être validé (pas créé)
    if not created and instance.statut == 'valide':
        try:
            # Vérifier si une quittance existe déjà
            if not hasattr(instance, 'quittance'):
                # Créer la quittance automatiquement
                quittance = QuittancePaiement.objects.create(
                    paiement=instance,
                    cree_par=instance.cree_par if hasattr(instance, 'cree_par') else None
                )
                print(f"Quittance générée lors de la validation: {quittance.numero_quittance}")
        except Exception as e:
            print(f"Erreur génération quittance validation: {e}")


@receiver(post_save, sender=Paiement)
def mettre_a_jour_prochain_mois_paiement(sender, instance, created, **kwargs):
    """
    Met à jour automatiquement le prochain mois de paiement après chaque paiement de loyer validé.
    Ce signal force le recalcul du prochain mois en tenant compte du mois payé et des avances actives.
    """
    # Seulement pour les paiements de loyer validés
    if instance.type_paiement == 'loyer' and instance.statut == 'valide' and instance.contrat:
        try:
            with transaction.atomic():
                # Forcer le recalcul du prochain mois de paiement
                # Le calcul est maintenant fait dynamiquement via ServiceGestionAvance.calculer_prochain_mois_paiement()
                # qui utilise le mois_paye si disponible
                
                # On force juste un refresh du contrat pour s'assurer que les données sont à jour
                # Le prochain mois sera recalculé à la prochaine demande via la méthode
                contrat = instance.contrat
                
                # Optionnel : on peut forcer un save pour déclencher d'autres signaux si nécessaire
                # Mais le calcul est déjà dynamique, donc pas besoin de stocker le prochain mois
                
                # Log pour debug
                print(f"[SIGNAL] Paiement de loyer validé pour contrat {contrat.numero_contrat}, "
                      f"mois payé: {instance.mois_paye or 'N/A'}, "
                      f"date paiement: {instance.date_paiement}")
                
        except Exception as e:
            import traceback
            print(f"Erreur lors de la mise à jour du prochain mois de paiement: {e}")
            traceback.print_exc()
