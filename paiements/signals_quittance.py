from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.db import transaction
from .models import Paiement, QuittancePaiement


def _detecter_et_regrouper_paiements(paiement_instance):
    """
    Détecte et regroupe les paiements de LOYER multiples du même jour pour le même contrat.
    Utilisé quand un locataire règle plusieurs mois de retard en une seule fois.
    Exclut les avances et tous les autres types de paiements.
    
    Returns:
        tuple: (quittance, liste_paiements, est_nouvelle)
    """
    # Ne regrouper QUE les paiements de loyer
    if paiement_instance.type_paiement != 'loyer':
        return None, [paiement_instance], False
    
    # Chercher les autres paiements de LOYER du même jour pour le même contrat
    paiements_meme_jour = Paiement.objects.filter(
        contrat=paiement_instance.contrat,
        date_paiement=paiement_instance.date_paiement,
        type_paiement='loyer',  # UNIQUEMENT les loyers
        statut='valide',
        is_deleted=False
    ).order_by('date_creation')
    
    # Si un seul paiement, pas de regroupement
    if paiements_meme_jour.count() <= 1:
        return None, [paiement_instance], False
    
    # Vérifier s'il existe déjà une quittance pour ces paiements
    quittance_existante = QuittancePaiement.objects.filter(
        paiements__in=paiements_meme_jour,
        is_deleted=False
    ).first()
    
    if quittance_existante:
        # Ajouter le nouveau paiement à la quittance existante si pas déjà dedans
        if not quittance_existante.paiements.filter(id=paiement_instance.id).exists():
            quittance_existante.paiements.add(paiement_instance)
            quittance_existante.est_cumulee = True
            quittance_existante.save()
            print(f"Paiement {paiement_instance.id} ajouté à la quittance cumulée {quittance_existante.numero_quittance}")
        return quittance_existante, list(paiements_meme_jour), False
    
    # Créer une nouvelle quittance cumulée
    return None, list(paiements_meme_jour), True


@receiver(post_save, sender=Paiement)
def generer_quittance_automatique(sender, instance, created, **kwargs):
    """
    Génère automatiquement une quittance quand un paiement est validé.
    Regroupe automatiquement les paiements multiples du même jour (hors avances).
    """
    # Seulement pour les nouveaux paiements validés
    if created and instance.statut == 'valide':
        try:
            # Synchroniser le paiement partiel avant de générer la quittance
            if instance.est_paiement_partiel or instance.type_paiement == 'paiement_partiel':
                from .services_paiement_partiel import ServicePaiementPartiel
                ServicePaiementPartiel.synchroniser_paiement_partiel(instance)
            
            # Vérifier si le paiement fait partie d'une quittance cumulée
            quittance_existante, paiements_a_grouper, creer_nouvelle = _detecter_et_regrouper_paiements(instance)
            
            if quittance_existante:
                # Déjà ajouté à une quittance existante
                return
            
            if creer_nouvelle and len(paiements_a_grouper) > 1:
                # Créer une quittance cumulée
                with transaction.atomic():
                    quittance = QuittancePaiement.objects.create(
                        paiement_principal=paiements_a_grouper[0],
                        est_cumulee=True,
                        cree_par=instance.cree_par if hasattr(instance, 'cree_par') else None
                    )
                    quittance.paiements.set(paiements_a_grouper)
                    print(f"Quittance cumulée générée: {quittance.numero_quittance} pour {len(paiements_a_grouper)} paiements")
            elif len(paiements_a_grouper) == 1:
                # Créer une quittance simple
                quittance = QuittancePaiement.objects.create(
                    paiement_principal=instance,
                    est_cumulee=False,
                    cree_par=instance.cree_par if hasattr(instance, 'cree_par') else None
                )
                quittance.paiements.add(instance)
                print(f"Quittance simple générée: {quittance.numero_quittance}")
                
        except Exception as e:
            import traceback
            print(f"Erreur génération quittance automatique: {e}")
            traceback.print_exc()


@receiver(post_save, sender=Paiement)
def generer_quittance_validation(sender, instance, created, **kwargs):
    """
    Génère une quittance quand un paiement passe de 'en_attente' à 'valide'.
    Regroupe automatiquement les paiements multiples du même jour (hors avances).
    """
    # Si le paiement vient d'être validé (pas créé)
    if not created and instance.statut == 'valide':
        try:
            # ÉVITER LA RÉCURSION
            if hasattr(instance, '_en_synchronisation') or hasattr(instance, '_en_verification_completion'):
                return
            
            from .services_paiement_partiel import ServicePaiementPartiel
            
            # Synchroniser et vérifier la complétion
            ServicePaiementPartiel.synchroniser_paiement_partiel(instance, skip_verification=False)
            
            # Vérifier si le paiement fait partie d'une quittance cumulée
            quittance_existante, paiements_a_grouper, creer_nouvelle = _detecter_et_regrouper_paiements(instance)
            
            if quittance_existante:
                # Déjà ajouté à une quittance existante
                return
            
            # Vérifier si une quittance existe déjà pour ce paiement
            quittance_existante_paiement = QuittancePaiement.objects.filter(
                paiements=instance,
                is_deleted=False
            ).first()
            
            if quittance_existante_paiement:
                print(f"Quittance déjà existante pour le paiement {instance.id}: {quittance_existante_paiement.numero_quittance}")
                return
            
            if creer_nouvelle and len(paiements_a_grouper) > 1:
                # Créer une quittance cumulée
                with transaction.atomic():
                    quittance = QuittancePaiement.objects.create(
                        paiement_principal=paiements_a_grouper[0],
                        est_cumulee=True,
                        cree_par=instance.cree_par if hasattr(instance, 'cree_par') else None
                    )
                    quittance.paiements.set(paiements_a_grouper)
                    print(f"Quittance cumulée générée lors de la validation: {quittance.numero_quittance} pour {len(paiements_a_grouper)} paiements")
            elif len(paiements_a_grouper) == 1:
                # Créer une quittance simple
                quittance = QuittancePaiement.objects.create(
                    paiement_principal=instance,
                    est_cumulee=False,
                    cree_par=instance.cree_par if hasattr(instance, 'cree_par') else None
                )
                quittance.paiements.add(instance)
                print(f"Quittance simple générée lors de la validation: {quittance.numero_quittance}")
                
        except Exception as e:
            import traceback
            print(f"Erreur génération quittance validation: {e}")
            traceback.print_exc()


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
