from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db import transaction
from .models import Contrat
from proprietes.models import Propriete


@receiver(post_save, sender=Contrat)
def synchroniser_disponibilite_propriete_apres_sauvegarde(sender, instance, created, **kwargs):
    """
    Signal pour synchroniser automatiquement la disponibilité d'une propriété
    après la sauvegarde d'un contrat.
    """
    if not instance.propriete:
        return
    
    # Utiliser une transaction pour éviter les problèmes de concurrence
    with transaction.atomic():
        # Vérifier s'il y a d'autres contrats actifs pour cette propriété
        contrats_actifs = Contrat.objects.filter(
            propriete=instance.propriete,
            est_actif=True,
            est_resilie=False
        ).exclude(pk=instance.pk)
        
        # Déterminer la nouvelle disponibilité
        nouvelle_disponibilite = not contrats_actifs.exists()
        
        # Mettre à jour la propriété si nécessaire
        if instance.propriete.disponible != nouvelle_disponibilite:
            instance.propriete.disponible = nouvelle_disponibilite
            instance.propriete.save(update_fields=['disponible'])


@receiver(post_delete, sender=Contrat)
def synchroniser_disponibilite_propriete_apres_suppression(sender, instance, **kwargs):
    """
    Signal pour synchroniser automatiquement la disponibilité d'une propriété
    après la suppression d'un contrat.
    """
    if not instance.propriete:
        return
    
    # Utiliser une transaction pour éviter les problèmes de concurrence
    with transaction.atomic():
        # Vérifier s'il y a d'autres contrats actifs pour cette propriété
        contrats_actifs = Contrat.objects.filter(
            propriete=instance.propriete,
            est_actif=True,
            est_resilie=False
        )
        
        # Marquer la propriété comme disponible s'il n'y a plus de contrats actifs
        if not contrats_actifs.exists() and not instance.propriete.disponible:
            instance.propriete.disponible = True
            instance.propriete.save(update_fields=['disponible'])


@receiver(post_save, sender=Propriete)
def valider_coherence_propriete_apres_sauvegarde(sender, instance, created, **kwargs):
    """
    Signal pour valider la cohérence d'une propriété après sa sauvegarde.
    """
    if created:
        return
    
    # Vérifier la cohérence entre la disponibilité et les contrats actifs
    contrats_actifs = Contrat.objects.filter(
        propriete=instance,
        est_actif=True,
        est_resilie=False
    )
    
    disponibilite_correcte = not contrats_actifs.exists()
    
    # Si la disponibilité est incorrecte, la corriger
    if instance.disponible != disponibilite_correcte:
        instance.disponible = disponibilite_correcte
        # Éviter la récursion en utilisant update
        Propriete.objects.filter(pk=instance.pk).update(disponible=disponibilite_correcte)


@receiver(post_save, sender=Contrat)
def creer_avance_loyer_automatique(sender, instance, created, **kwargs):
    """
    Signal pour créer automatiquement une avance de loyer quand elle est marquée comme payée.
    """
    # Ne traiter que les mises à jour (pas les créations)
    if created:
        return
    
    # Vérifier si l'avance est marquée comme payée
    if not instance.avance_loyer_payee:
        return
    
    # Vérifier si une avance existe déjà
    from paiements.models_avance import AvanceLoyer
    if AvanceLoyer.objects.filter(contrat=instance).exists():
        return
    
    # Créer l'avance automatiquement
    try:
        instance._creer_avance_loyer_automatique()
    except Exception as e:
        print(f"Erreur lors de la création automatique de l'avance: {str(e)}")
