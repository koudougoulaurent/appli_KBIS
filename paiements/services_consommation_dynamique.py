"""
Service de consommation dynamique et réelle des avances dans le temps.
Gère la barre de progression et la consommation automatique.
"""
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from .models_avance import AvanceLoyer, ConsommationAvance
from .models import Paiement


class ServiceConsommationDynamique:
    """Service pour gérer la consommation dynamique des avances."""
    
    @classmethod
    def consommer_avances_automatiquement(cls, contrat=None):
        """
        Consomme automatiquement les avances en fonction du temps écoulé.
        """
        if contrat:
            avances = AvanceLoyer.objects.filter(contrat=contrat, statut='active')
        else:
            avances = AvanceLoyer.objects.filter(statut='active')
        
        consommees = 0
        erreurs = 0
        
        for avance in avances:
            try:
                with transaction.atomic():
                    resultat = cls._consommer_avance_par_temps(avance)
                    if resultat['consommee']:
                        consommees += 1
                        print(f"OK - Avance {avance.id} consommee automatiquement")
                    else:
                        print(f"INFO - Avance {avance.id} pas encore a consommer")
            except Exception as e:
                erreurs += 1
                print(f"ERREUR - Avance {avance.id}: {str(e)}")
        
        return {
            'consommees': consommees,
            'erreurs': erreurs,
            'total': avances.count()
        }
    
    @classmethod
    def _consommer_avance_par_temps(cls, avance):
        """
        Consomme une avance en fonction du temps écoulé depuis sa création.
        """
        aujourd_hui = date.today()
        mois_actuel = aujourd_hui.replace(day=1)
        
        # Calculer les mois qui devraient être consommés
        mois_a_consommer = cls._calculer_mois_a_consommer(avance, mois_actuel)
        
        if not mois_a_consommer:
            return {'consommee': False, 'mois_ajoutes': 0}
        
        mois_ajoutes = 0
        for mois in mois_a_consommer:
            # Vérifier si ce mois n'est pas déjà consommé
            if not avance.est_mois_consomme(mois):
                # Créer la consommation
                consommation = ConsommationAvance.objects.create(
                    avance=avance,
                    mois_consomme=mois,
                    montant_consomme=avance.loyer_mensuel,
                    montant_restant_apres=avance.montant_restant - avance.loyer_mensuel,
                    paiement=None  # Consommation automatique, pas liée à un paiement
                )
                
                # Mettre à jour l'avance
                avance.montant_restant = max(0, avance.montant_restant - avance.loyer_mensuel)
                avance.save()
                
                mois_ajoutes += 1
        
        return {'consommee': mois_ajoutes > 0, 'mois_ajoutes': mois_ajoutes}
    
    @classmethod
    def _calculer_mois_a_consommer(cls, avance, mois_actuel):
        """
        Calcule quels mois devraient être consommés automatiquement.
        """
        if not avance.mois_debut_couverture:
            return []
        
        mois_a_consommer = []
        mois_courant = avance.mois_debut_couverture
        
        # Parcourir tous les mois couverts par l'avance
        for _ in range(avance.nombre_mois_couverts):
            # Si le mois est dans le passé et pas encore consommé
            if mois_courant < mois_actuel and not avance.est_mois_consomme(mois_courant):
                mois_a_consommer.append(mois_courant)
            
            # Passer au mois suivant
            mois_courant = mois_courant + relativedelta(months=1)
        
        return mois_a_consommer
    
    @classmethod
    def calculer_progression_avance(cls, avance):
        """
        Calcule la progression réelle d'une avance.
        """
        aujourd_hui = date.today()
        mois_actuel = aujourd_hui.replace(day=1)
        
        # Consommer automatiquement les mois passés
        cls._consommer_avance_par_temps(avance)
        
        # Recalculer les statistiques
        avance.refresh_from_db()
        
        # Calculer la progression
        total_mois = avance.nombre_mois_couverts
        mois_consommes = ConsommationAvance.objects.filter(avance=avance).count()
        
        # Calculer le pourcentage de progression
        pourcentage_mois = (mois_consommes / total_mois * 100) if total_mois > 0 else 0
        
        # Calculer la progression monétaire
        montant_consomme = avance.montant_avance - avance.montant_restant
        pourcentage_montant = (montant_consomme / avance.montant_avance * 100) if avance.montant_avance > 0 else 0
        
        # Déterminer le statut
        if mois_consommes >= total_mois:
            statut = 'terminee'
            statut_label = 'Terminée'
        elif mois_actuel >= avance.mois_debut_couverture and mois_actuel <= (avance.mois_fin_couverture or mois_actuel):
            statut = 'active'
            statut_label = 'Active'
        else:
            statut = 'en_attente'
            statut_label = 'En attente'
        
        return {
            'total_mois': total_mois,
            'mois_consommes': mois_consommes,
            'mois_restants': total_mois - mois_consommes,
            'pourcentage_mois': round(pourcentage_mois, 1),
            'montant_total': float(avance.montant_avance),
            'montant_consomme': float(montant_consomme),
            'montant_restant': float(avance.montant_restant),
            'pourcentage_montant': round(pourcentage_montant, 1),
            'statut': statut,
            'statut_label': statut_label,
            'prochaine_consommation': cls._calculer_prochaine_consommation(avance, mois_actuel)
        }
    
    @classmethod
    def _calculer_prochaine_consommation(cls, avance, mois_actuel):
        """
        Calcule quand aura lieu la prochaine consommation automatique.
        """
        if not avance.mois_debut_couverture:
            return None
        
        mois_courant = avance.mois_debut_couverture
        
        for _ in range(avance.nombre_mois_couverts):
            if mois_courant >= mois_actuel and not avance.est_mois_consomme(mois_courant):
                return mois_courant
            mois_courant = mois_courant + relativedelta(months=1)
        
        return None
    
    @classmethod
    def synchroniser_avec_paiements(cls, avance):
        """
        Synchronise la consommation de l'avance avec les paiements de loyer.
        """
        # Récupérer les paiements de loyer du contrat
        paiements_loyer = Paiement.objects.filter(
            contrat=avance.contrat,
            type_paiement='loyer',
            statut='valide'
        ).order_by('date_paiement')
        
        consommations_ajoutees = 0
        
        for paiement in paiements_loyer:
            mois_paiement = paiement.date_paiement.replace(day=1)
            
            # Vérifier si ce mois est couvert par l'avance
            if (avance.mois_debut_couverture and 
                avance.mois_fin_couverture and
                avance.mois_debut_couverture <= mois_paiement <= avance.mois_fin_couverture):
                
                # Vérifier si ce mois n'est pas déjà consommé
                if not avance.est_mois_consomme(mois_paiement):
                    # Créer la consommation
                    ConsommationAvance.objects.create(
                        avance=avance,
                        mois_consomme=mois_paiement,
                        montant_consomme=avance.loyer_mensuel,
                        montant_restant_apres=avance.montant_restant - avance.loyer_mensuel,
                        paiement=paiement
                    )
                    
                    # Mettre à jour l'avance
                    avance.montant_restant = max(0, avance.montant_restant - avance.loyer_mensuel)
                    avance.save()
                    
                    consommations_ajoutees += 1
        
        return consommations_ajoutees
