from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db import transaction
from .models import Contrat
from proprietes.models import Propriete, Bailleur, Locataire


@receiver(post_save, sender=Contrat)
def synchroniser_disponibilite_propriete_apres_sauvegarde(sender, instance, created, **kwargs):
    """
    Signal pour synchroniser automatiquement la disponibilité d'une propriété
    après la sauvegarde d'un contrat.
    CORRIGÉ : Utilise all_objects pour vérifier tous les contrats, même supprimés logiquement
    """
    if not instance.propriete:
        return
    
    # Utiliser une transaction pour éviter les problèmes de concurrence
    with transaction.atomic():
        # CORRIGÉ : Utiliser all_objects pour inclure les contrats supprimés logiquement
        # Vérifier s'il y a d'autres contrats actifs pour cette propriété
        contrats_actifs = Contrat.all_objects.filter(
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


@receiver(post_save, sender=Contrat)
def synchroniser_disponibilite_unite_locative_apres_sauvegarde(sender, instance, created, **kwargs):
    """
    Signal pour synchroniser automatiquement la disponibilité d'une unité locative
    après la sauvegarde d'un contrat.
    CORRIGÉ : Met à jour le statut de l'unité locative en fonction des contrats actifs
    """
    if not instance.unite_locative:
        return
    
    # Utiliser une transaction pour éviter les problèmes de concurrence
    with transaction.atomic():
        # CORRIGÉ : Utiliser all_objects pour inclure les contrats supprimés logiquement
        # Vérifier s'il y a d'autres contrats actifs pour cette unité locative
        contrats_actifs_unite = Contrat.all_objects.filter(
            unite_locative=instance.unite_locative,
            est_actif=True,
            est_resilie=False
        ).exclude(pk=instance.pk)
        
        # Déterminer le nouveau statut
        if instance.est_actif and not instance.est_resilie:
            # Contrat actif = unité occupée
            nouveau_statut = 'occupee'
        else:
            # Contrat inactif ou résilié = unité disponible (si pas d'autres contrats actifs)
            nouveau_statut = 'disponible' if not contrats_actifs_unite.exists() else 'occupee'
        
        # Mettre à jour l'unité locative si nécessaire
        if instance.unite_locative.statut != nouveau_statut:
            instance.unite_locative.statut = nouveau_statut
            instance.unite_locative.save(update_fields=['statut'])


@receiver(post_delete, sender=Contrat)
def synchroniser_disponibilite_propriete_apres_suppression(sender, instance, **kwargs):
    """
    Signal pour synchroniser automatiquement la disponibilité d'une propriété
    après la suppression d'un contrat.
    CORRIGÉ : Utilise all_objects pour vérifier tous les contrats, même supprimés logiquement
    """
    if not instance.propriete:
        return
    
    # Utiliser une transaction pour éviter les problèmes de concurrence
    with transaction.atomic():
        # CORRIGÉ : Utiliser all_objects pour inclure les contrats supprimés logiquement
        # Vérifier s'il y a d'autres contrats actifs pour cette propriété
        contrats_actifs = Contrat.all_objects.filter(
            propriete=instance.propriete,
            est_actif=True,
            est_resilie=False
        )
        
        # Marquer la propriété comme disponible s'il n'y a plus de contrats actifs
        if not contrats_actifs.exists() and not instance.propriete.disponible:
            instance.propriete.disponible = True
            instance.propriete.save(update_fields=['disponible'])


@receiver(post_delete, sender=Contrat)
def synchroniser_disponibilite_unite_locative_apres_suppression(sender, instance, **kwargs):
    """
    Signal pour synchroniser automatiquement la disponibilité d'une unité locative
    après la suppression d'un contrat.
    CORRIGÉ : Met à jour le statut de l'unité locative pour qu'elle redevienne disponible
    """
    if not instance.unite_locative:
        return
    
    # Utiliser une transaction pour éviter les problèmes de concurrence
    with transaction.atomic():
        # CORRIGÉ : Utiliser all_objects pour inclure les contrats supprimés logiquement
        # Vérifier s'il y a d'autres contrats actifs pour cette unité locative
        contrats_actifs_unite = Contrat.all_objects.filter(
            unite_locative=instance.unite_locative,
            est_actif=True,
            est_resilie=False
        )
        
        # Marquer l'unité locative comme disponible s'il n'y a plus de contrats actifs
        if not contrats_actifs_unite.exists() and instance.unite_locative.statut != 'disponible':
            instance.unite_locative.statut = 'disponible'
            instance.unite_locative.save(update_fields=['statut'])


@receiver(post_save, sender=Propriete)
def valider_coherence_propriete_apres_sauvegarde(sender, instance, created, **kwargs):
    """
    Signal pour valider la cohérence d'une propriété après sa sauvegarde.
    CORRIGÉ : Utilise all_objects pour vérifier tous les contrats, même supprimés logiquement
    """
    if created:
        return
    
    # CORRIGÉ : Utiliser all_objects pour inclure les contrats supprimés logiquement
    # Vérifier la cohérence entre la disponibilité et les contrats actifs
    contrats_actifs = Contrat.all_objects.filter(
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


@receiver(post_save, sender=Contrat)
def mettre_a_jour_statuts_bailleur_locataire(sender, instance, created, **kwargs):
    """
    Signal pour mettre à jour automatiquement les statuts actifs du bailleur et du locataire
    en fonction des contrats actifs.
    CORRIGÉ : Met à jour automatiquement les statuts lors de création/modification/suppression de contrats
    """
    try:
        with transaction.atomic():
            # Mettre à jour le statut du bailleur
            if instance.propriete and instance.propriete.bailleur:
                bailleur = instance.propriete.bailleur
                a_contrats_actifs = bailleur.a_des_proprietes_louees()
                
                # Si le bailleur a des contrats actifs, le marquer comme actif
                if a_contrats_actifs and not bailleur.actif:
                    bailleur.actif = True
                    bailleur.save(update_fields=['actif'])
            
            # Mettre à jour le statut du locataire
            if instance.locataire:
                locataire = instance.locataire
                a_contrats_actifs = locataire.a_des_contrats_actifs()
                
                # Si le locataire a des contrats actifs, le marquer comme actif
                if a_contrats_actifs and locataire.statut != 'actif':
                    locataire.statut = 'actif'
                    locataire.save(update_fields=['statut'])
                    
    except Exception as e:
        print(f"Erreur lors de la mise a jour des statuts: {str(e)}")
        import traceback
        traceback.print_exc()


@receiver(post_delete, sender=Contrat)
def mettre_a_jour_statuts_apres_suppression_contrat(sender, instance, **kwargs):
    """
    Signal pour mettre à jour les statuts après suppression d'un contrat.
    """
    try:
        with transaction.atomic():
            # Mettre à jour le statut du bailleur
            if instance.propriete and instance.propriete.bailleur:
                bailleur = instance.propriete.bailleur
                a_contrats_actifs = bailleur.a_des_proprietes_louees()
                
                # Si le bailleur n'a plus de contrats actifs, on peut le passer en inactif
                # Mais on garde le statut actif s'il est déjà actif (pas de changement automatique)
                # Cette logique peut être ajustée selon les besoins métier
                if not a_contrats_actifs and bailleur.actif:
                    # Optionnel : passer en inactif si plus de contrats
                    # bailleur.actif = False
                    # bailleur.save(update_fields=['actif'])
                    pass
            
            # Mettre à jour le statut du locataire
            if instance.locataire:
                locataire = instance.locataire
                a_contrats_actifs = locataire.a_des_contrats_actifs()
                
                # Si le locataire n'a plus de contrats actifs, on peut le passer en inactif
                # Mais on garde le statut actif s'il est déjà actif (pas de changement automatique)
                if not a_contrats_actifs and locataire.statut == 'actif':
                    # Optionnel : passer en inactif si plus de contrats
                    # locataire.statut = 'inactif'
                    # locataire.save(update_fields=['statut'])
                    pass
                    
    except Exception as e:
        print(f"Erreur lors de la mise a jour des statuts apres suppression: {str(e)}")
        import traceback
        traceback.print_exc()
