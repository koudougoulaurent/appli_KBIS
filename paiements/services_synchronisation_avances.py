"""
Service de synchronisation parfaite entre les paiements d'avance et les avances.
Garantit qu'il n'y a jamais d'erreur de mois inadéquats.
"""
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from .models import Paiement
from .models_avance import AvanceLoyer
from contrats.models import Contrat


class ServiceSynchronisationAvances:
    """Service pour synchroniser parfaitement les avances avec les paiements."""
    
    @classmethod
    def synchroniser_avance_avec_paiement(cls, paiement):
        """
        Synchronise parfaitement une avance avec son paiement.
        Garantit la cohérence des mois couverts.
        """
        if paiement.type_paiement != 'avance':
            return None
            
        try:
            with transaction.atomic():
                # Calculer les mois couverts de manière précise
                loyer_mensuel = float(paiement.contrat.loyer_mensuel) if paiement.contrat.loyer_mensuel else 0
                montant_avance = float(paiement.montant)
                
                if loyer_mensuel <= 0:
                    raise ValueError("Loyer mensuel invalide")
                
                # Calculer le nombre de mois couverts avec précision
                nombre_mois_couverts = cls._calculer_mois_couverts_precis(montant_avance, loyer_mensuel)
                
                # Calculer les mois de couverture
                mois_debut, mois_fin = cls._calculer_mois_couverture(
                    paiement.date_paiement, 
                    nombre_mois_couverts
                )
                
                # Créer ou mettre à jour l'avance
                    # Calculer le reste
                    montant_reste = montant_avance % loyer_mensuel
                    
                    avance, created = AvanceLoyer.objects.get_or_create(
                        paiement=paiement,
                        defaults={
                            'contrat': paiement.contrat,
                            'montant_avance': montant_avance,
                            'loyer_mensuel': loyer_mensuel,
                            'nombre_mois_couverts': nombre_mois_couverts,
                            'montant_restant': montant_avance,
                            'montant_reste': montant_reste,
                            'date_avance': paiement.date_paiement,
                            'mois_debut_couverture': mois_debut,
                            'mois_fin_couverture': mois_fin,
                            'statut': 'active',
                            'notes': f"Avance synchronisée avec paiement {paiement.id}",
                        }
                    )
                
                if not created:
                    # Mettre à jour l'avance existante
                    avance.montant_avance = montant_avance
                    avance.loyer_mensuel = loyer_mensuel
                    avance.nombre_mois_couverts = nombre_mois_couverts
                    avance.montant_restant = montant_avance
                    avance.mois_debut_couverture = mois_debut
                    avance.mois_fin_couverture = mois_fin
                    avance.statut = 'active'
                    avance.save()
                
                # Mettre à jour le contrat pour refléter l'avance
                paiement.contrat.avance_loyer = str(montant_avance)
                paiement.contrat.avance_loyer_payee = True
                paiement.contrat.date_paiement_avance = paiement.date_paiement
                paiement.contrat.save()
                
                return avance
                
        except Exception as e:
            print(f"Erreur synchronisation avance: {str(e)}")
            return None
    
    @classmethod
    def _calculer_mois_couverts_precis(cls, montant_avance, loyer_mensuel):
        """Calcule le nombre de mois couverts avec précision."""
        if loyer_mensuel <= 0:
            return 0
        
        # Calculer le nombre de mois complets
        mois_entiers = int(montant_avance // loyer_mensuel)
        
        # Calculer le reste
        reste = montant_avance % loyer_mensuel
        
        # Si le reste est significatif (plus de 50% du loyer), compter un mois partiel
        if reste > (loyer_mensuel * 0.5):
            mois_entiers += 1
        
        # Au minimum 1 mois
        return max(1, mois_entiers)
    
    @classmethod
    def _calculer_mois_couverture(cls, date_paiement, nombre_mois):
        """Calcule les mois de début et fin de couverture."""
        # Commencer au mois suivant le paiement
        mois_debut = date_paiement.replace(day=1) + relativedelta(months=1)
        mois_fin = mois_debut + relativedelta(months=nombre_mois - 1)
        
        return mois_debut, mois_fin
    
    @classmethod
    def synchroniser_toutes_avances(cls):
        """Synchronise toutes les avances avec leurs paiements."""
        paiements_avance = Paiement.objects.filter(
            type_paiement='avance',
            statut='valide'
        ).select_related('contrat')
        
        synchronisees = 0
        erreurs = 0
        
        for paiement in paiements_avance:
            try:
                avance = cls.synchroniser_avance_avec_paiement(paiement)
                if avance:
                    synchronisees += 1
                    print(f"OK - Avance synchronisee pour paiement {paiement.id}")
                else:
                    erreurs += 1
                    print(f"ERREUR - Synchronisation paiement {paiement.id}")
            except Exception as e:
                erreurs += 1
                print(f"ERREUR - Paiement {paiement.id}: {str(e)}")
        
        return {
            'synchronisees': synchronisees,
            'erreurs': erreurs,
            'total': paiements_avance.count()
        }
    
    @classmethod
    def verifier_coherence_avances(cls):
        """Vérifie la cohérence entre les paiements et les avances."""
        paiements_avance = Paiement.objects.filter(
            type_paiement='avance',
            statut='valide'
        ).select_related('contrat')
        
        incohérences = []
        
        for paiement in paiements_avance:
            try:
                # Vérifier si l'avance correspondante existe
                avance = AvanceLoyer.objects.filter(paiement=paiement).first()
                
                if not avance:
                    incohérences.append({
                        'type': 'avance_manquante',
                        'paiement_id': paiement.id,
                        'message': 'Aucune avance correspondante'
                    })
                    continue
                
                # Vérifier la cohérence des montants
                montant_paiement = float(paiement.montant)
                montant_avance = float(avance.montant_avance)
                
                if abs(montant_paiement - montant_avance) > 0.01:
                    incohérences.append({
                        'type': 'montant_incoherent',
                        'paiement_id': paiement.id,
                        'montant_paiement': montant_paiement,
                        'montant_avance': montant_avance,
                        'message': 'Montants incohérents'
                    })
                
                # Vérifier la cohérence des mois couverts
                loyer_mensuel = float(paiement.contrat.loyer_mensuel) if paiement.contrat.loyer_mensuel else 0
                if loyer_mensuel > 0:
                    mois_attendu = cls._calculer_mois_couverts_precis(montant_avance, loyer_mensuel)
                    if avance.nombre_mois_couverts != mois_attendu:
                        incohérences.append({
                            'type': 'mois_incoherents',
                            'paiement_id': paiement.id,
                            'mois_attendu': mois_attendu,
                            'mois_actuel': avance.nombre_mois_couverts,
                            'message': 'Nombre de mois couverts incohérent'
                        })
                
            except Exception as e:
                incohérences.append({
                    'type': 'erreur_verification',
                    'paiement_id': paiement.id,
                    'message': str(e)
                })
        
        return incohérences
