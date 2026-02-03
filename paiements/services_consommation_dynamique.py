"""
Service de consommation dynamique et réelle des avances dans le temps.
Gère la barre de progression et la consommation automatique.
"""
from django.db import transaction
from django.utils import timezone
from django.conf import settings
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
                        if settings.DEBUG:
                            print(f"OK - Avance {avance.id} consommee automatiquement ({resultat['mois_ajoutes']} mois)")
                    elif settings.DEBUG:
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
            # Normaliser le mois au 1er du mois
            mois_normalise = mois.replace(day=1)
            
            # Vérifier si ce mois n'est pas déjà consommé (double vérification)
            if not avance.est_mois_consomme(mois_normalise):
                # Recharger l'avance pour avoir les données à jour
                avance.refresh_from_db()
                
                # Calculer le montant restant après cette consommation
                montant_restant_apres = max(Decimal('0'), avance.montant_restant - avance.loyer_mensuel)
                
                if settings.DEBUG:
                    print(f"[CONSO] Création consommation pour avance {avance.id}, mois {mois_normalise}")
                    print(f"  - Montant restant avant: {avance.montant_restant}")
                    print(f"  - Montant restant après: {montant_restant_apres}")
                
                # Créer la consommation
                try:
                    consommation = ConsommationAvance.objects.create(
                        avance=avance,
                        mois_consomme=mois_normalise,
                        montant_consomme=avance.loyer_mensuel,
                        montant_restant_apres=montant_restant_apres,
                        paiement=None  # Consommation automatique, pas liée à un paiement
                    )
                    
                    if settings.DEBUG:
                        print(f"  - Consommation créée: ID {consommation.id}")
                    
                    # Mettre à jour l'avance
                    avance.montant_restant = montant_restant_apres
                    
                    # Si l'avance est épuisée, changer le statut
                    if avance.montant_restant <= 0:
                        avance.statut = 'epuisee'
                        avance.montant_restant = Decimal('0')
                        if settings.DEBUG:
                            print(f"  - Avance épuisée, statut changé à 'epuisee'")
                    
                    avance.save(update_fields=['montant_restant', 'statut'])
                    
                    mois_ajoutes += 1
                except Exception as e:
                    if settings.DEBUG:
                        print(f"  - ERREUR lors de la création de la consommation: {e}")
                    import traceback
                    traceback.print_exc()
                    # Continuer avec le mois suivant même en cas d'erreur
                    continue
        
        return {'consommee': mois_ajoutes > 0, 'mois_ajoutes': mois_ajoutes}
    
    @classmethod
    def _calculer_mois_a_consommer(cls, avance, mois_actuel):
        """
        Calcule quels mois devraient être consommés automatiquement.
        LOGIQUE CORRIGÉE : Ne consommer que les mois réellement écoulés.
        """
        if not avance.mois_debut_couverture:
            if settings.DEBUG:
                print(f"[AVANCE {avance.id}] Pas de mois_debut_couverture")
            return []
        
        # Normaliser les dates au 1er du mois pour comparaison correcte
        mois_debut = avance.mois_debut_couverture.replace(day=1)
        mois_actuel_normalise = mois_actuel.replace(day=1)
        
        mois_a_consommer = []
        mois_courant = mois_debut
        
        if settings.DEBUG:
            print(f"[AVANCE {avance.id}] Calcul mois à consommer:")
            print(f"  - Mois début: {mois_debut}")
            print(f"  - Mois actuel: {mois_actuel_normalise}")
            print(f"  - Nombre mois couverts: {avance.nombre_mois_couverts}")
        
        # Parcourir tous les mois couverts par l'avance
        for i in range(avance.nombre_mois_couverts):
            mois_courant_normalise = mois_courant.replace(day=1)
            
            # CORRECTION : Seuls les mois COMPLÈTEMENT écoulés peuvent être consommés
            # Un mois est considéré comme écoulé s'il est strictement antérieur au mois actuel
            if mois_courant_normalise < mois_actuel_normalise:
                est_deja_consomme = avance.est_mois_consomme(mois_courant_normalise)
                
                if settings.DEBUG:
                    print(f"  - Mois {mois_courant_normalise}: {'déjà consommé' if est_deja_consomme else 'à consommer'}")
                
                if not est_deja_consomme:
                    mois_a_consommer.append(mois_courant_normalise)
            
            # Passer au mois suivant
            mois_courant = mois_courant + relativedelta(months=1)
        
        if settings.DEBUG:
            print(f"[AVANCE {avance.id}] Résultat: {len(mois_a_consommer)} mois à consommer sur {avance.nombre_mois_couverts} total")
            if mois_a_consommer:
                print(f"  - Mois à consommer: {mois_a_consommer}")
        
        return mois_a_consommer
    
    @classmethod
    def calculer_progression_avance(cls, avance):
        """
        Calcule la progression réelle d'une avance.
        LOGIQUE CORRIGÉE : Distinction claire entre mois consommés, en cours, en attente et futurs.
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
        
        # NOUVELLE LOGIQUE : Calculer les mois par statut temporel
        mois_par_statut = cls._calculer_mois_par_statut_temporel(avance, mois_actuel)
        
        # Calculer le pourcentage de progression (seulement les mois réellement consommés)
        pourcentage_mois = (mois_consommes / total_mois * 100) if total_mois > 0 else 0
        
        # Calculer la progression monétaire
        montant_consomme = avance.montant_avance - avance.montant_restant
        pourcentage_montant = (montant_consomme / avance.montant_avance * 100) if avance.montant_avance > 0 else 0
        
        # Déterminer le statut global
        if mois_consommes >= total_mois:
            statut = 'terminee'
            statut_label = 'Terminée'
        elif mois_par_statut['en_cours'] > 0:
            statut = 'active'
            statut_label = 'Active'
        elif mois_par_statut['en_attente'] > 0:
            statut = 'en_attente'
            statut_label = 'En attente'
        else:
            statut = 'futur'
            statut_label = 'Futur'
        
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
            'prochaine_consommation': cls._calculer_prochaine_consommation(avance, mois_actuel),
            # NOUVEAU : Statistiques détaillées par statut temporel
            'mois_par_statut': mois_par_statut
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
    
    @classmethod
    def _calculer_mois_par_statut_temporel(cls, avance, mois_actuel):
        """
        Calcule le nombre de mois par statut temporel (consommés, en cours, en attente, futurs).
        LOGIQUE CORRIGÉE : Distinction claire entre les différents statuts temporels.
        """
        if not avance.mois_debut_couverture:
            return {
                'consommes': 0,
                'en_cours': 0,
                'en_attente': 0,
                'futurs': 0
            }
        
        mois_consommes = 0
        mois_en_cours = 0
        mois_en_attente = 0
        mois_futurs = 0
        
        mois_courant = avance.mois_debut_couverture
        
        # Parcourir tous les mois couverts par l'avance
        for _ in range(avance.nombre_mois_couverts):
            est_consomme = avance.est_mois_consomme(mois_courant)
            
            if est_consomme:
                mois_consommes += 1
            elif mois_courant < mois_actuel:
                # Mois passé mais pas encore consommé = en attente
                mois_en_attente += 1
            elif mois_courant == mois_actuel:
                # Mois actuel = en cours
                mois_en_cours += 1
            else:
                # Mois futur
                mois_futurs += 1
            
            # Passer au mois suivant
            mois_courant = mois_courant + relativedelta(months=1)
        
        return {
            'consommes': mois_consommes,
            'en_cours': mois_en_cours,
            'en_attente': mois_en_attente,
            'futurs': mois_futurs
        }
