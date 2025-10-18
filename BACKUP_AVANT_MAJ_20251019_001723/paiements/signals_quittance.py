from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
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
