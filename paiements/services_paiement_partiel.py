"""
Service pour gérer la logique des paiements partiels
RESPECTE À LA LETTRE TOUTES LES LOGIQUES DU PAIEMENT GLOBAL
"""
from decimal import Decimal
from django.db.models import Sum, Q
from django.utils import timezone
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from .models import Paiement, Contrat
import logging
import re

logger = logging.getLogger(__name__)


class ServicePaiementPartiel:
    """Service pour gérer les paiements partiels de manière intelligente"""
    
    @staticmethod
    def valider_mois_a_regler(contrat, mois_paye_str, type_paiement='loyer'):
        """
        Valide le mois à régler selon les règles :
        - Si le mois proposé est dans le FUTUR (avance) : proposer d'enregistrer comme avance de loyer
        - Si le mois proposé est en RETARD (passé) : AUTORISER jusqu'au mois courant pour se rattraper
        - Le mois courant et les mois passés non payés sont autorisés
        """
        try:
            # Pour les avances et cautions, la validation est différente
            if type_paiement in ['avance', 'caution', 'autre']:
                return {
                    'valide': True,
                    'mois_attendu': mois_paye_str,
                    'date_mois': ServicePaiementPartiel.convertir_mois_paye_en_date(mois_paye_str)
                }
            
            # Déterminer le mois attendu (mois suivant le dernier paiement)
            mois_attendu = ServicePaiementPartiel.determiner_mois_a_regler(contrat)
            date_mois_attendu = mois_attendu['date_mois']
            
            # Convertir le mois_paye en date
            date_mois_propose = ServicePaiementPartiel.convertir_mois_paye_en_date(mois_paye_str)
            
            if not date_mois_propose:
                return {
                    'valide': False,
                    'message': f"Format de mois invalide: {mois_paye_str}",
                    'mois_attendu': mois_attendu['mois_paye'],
                    'type_erreur': 'format_invalide'
                }
            
            # Déterminer le mois courant (premier jour du mois actuel)
            mois_courant = timezone.now().date().replace(day=1)
            
            # VALIDATION : 
            # 1. Si le mois proposé est dans le FUTUR (après le mois courant) - PROPOSER AVANCE
            if date_mois_propose > mois_courant:
                # Le mois proposé est dans le futur - PROPOSER AVANCE DE LOYER
                return {
                    'valide': False,
                    'message': f"⚠️ AVANCE DÉTECTÉE : Vous tentez de payer pour {mois_paye_str}, "
                              f"mais ce mois est dans le futur (mois courant: {mois_courant.strftime('%B %Y')}). "
                              f"Ce paiement couvrira plusieurs mois dans le futur.",
                    'mois_attendu': mois_attendu['mois_paye'],
                    'mois_propose': mois_paye_str,
                    'type_erreur': 'mois_avance',
                    'suggestion': f"Enregistrer ce paiement comme 'AVANCE DE LOYER' pour couvrir les mois futurs",
                    'proposer_avance': True
                }
            
            # 2. Si le mois proposé est en RETARD mais <= mois courant - AUTORISER (rattrapage)
            if date_mois_propose < date_mois_attendu:
                # Vérifier si le mois proposé est déjà payé
                from .models import Paiement
                paiements_mois = Paiement.objects.filter(
                    contrat=contrat,
                    mois_paye=mois_paye_str,
                    type_paiement='loyer',
                    is_deleted=False,
                    statut='valide'
                )
                
                if paiements_mois.exists():
                    # Ce mois est déjà payé - vérifier s'il est complètement payé
                    total_paye = sum(p.montant for p in paiements_mois)
                    montant_du_mois = ServicePaiementPartiel.calculer_montant_du_mois(contrat, mois_paye_str)
                    
                    if total_paye >= montant_du_mois:
                        return {
                            'valide': False,
                            'message': f"❌ IMPOSSIBLE : Le mois {mois_paye_str} est déjà complètement payé.",
                            'mois_attendu': mois_attendu['mois_paye'],
                            'mois_propose': mois_paye_str,
                            'type_erreur': 'mois_deja_paye',
                            'suggestion': f"Ce mois est déjà payé. Le prochain mois à payer est {mois_attendu['mois_paye']}"
                        }
                    else:
                        # C'est un paiement partiel - AUTORISER pour compléter
                        return {
                            'valide': True,
                            'mois_attendu': mois_paye_str,
                            'date_mois': date_mois_propose,
                            'est_retard': True,
                            'message_info': f"Paiement en retard autorisé pour se rattraper. Mois proposé: {mois_paye_str}, Prochain mois attendu: {mois_attendu['mois_paye']}"
                        }
                else:
                    # Mois en retard non payé - AUTORISER pour se rattraper
                    return {
                        'valide': True,
                        'mois_attendu': mois_paye_str,
                        'date_mois': date_mois_propose,
                        'est_retard': True,
                        'message_info': f"Paiement en retard autorisé pour se rattraper. Mois proposé: {mois_paye_str}, Prochain mois attendu: {mois_attendu['mois_paye']}"
                    }
            
            # 3. Le mois est exactement le mois attendu ou entre le mois attendu et le mois courant - VALIDER
            return {
                'valide': True,
                'mois_attendu': mois_attendu['mois_paye'],
                'date_mois': date_mois_attendu
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la validation du mois à régler: {str(e)}")
            return {
                'valide': False,
                'message': f"Erreur lors de la validation: {str(e)}",
                'type_erreur': 'erreur_systeme'
            }
    
    @staticmethod
    def detecter_paiement_partiel(paiement):
        """
        Détecte automatiquement si un paiement est partiel
        UTILISE LA MÊME LOGIQUE QUE LES PAIEMENTS GLOBAUX
        """
        try:
            contrat = paiement.contrat
            if not contrat:
                return False
            
            # Convertir mois_paye en date si disponible
            date_mois = None
            if paiement.mois_paye:
                date_mois = ServicePaiementPartiel.convertir_mois_paye_en_date(paiement.mois_paye)
            
            # Calculer le montant dû pour le mois (avec avances si applicable)
            montant_du_mois = ServicePaiementPartiel.calculer_montant_du_mois(
                contrat, paiement.mois_paye, date_mois
            )
            
            if montant_du_mois <= 0:
                return False
            
            # Vérifier si le montant payé est inférieur au montant dû
            if paiement.montant < montant_du_mois:
                paiement.est_paiement_partiel = True
                paiement.montant_du_mois = montant_du_mois
                paiement.montant_restant_du = montant_du_mois - paiement.montant
                
                # Calculer le pourcentage payé
                pourcentage_paye = (paiement.montant / montant_du_mois) * 100
                
                logger.info(
                    f"Paiement partiel détecté: {paiement.reference_paiement} - "
                    f"Mois: {paiement.mois_paye or 'N/A'} - "
                    f"Payé: {paiement.montant}, Dû: {montant_du_mois}, "
                    f"Restant: {paiement.montant_restant_du}, "
                    f"Pourcentage: {pourcentage_paye:.2f}%"
                )
                
                return True
            else:
                paiement.est_paiement_partiel = False
                paiement.montant_du_mois = montant_du_mois
                paiement.montant_restant_du = Decimal('0')
                return False
                
        except Exception as e:
            logger.error(f"Erreur lors de la détection du paiement partiel: {str(e)}")
            return False
    
    @staticmethod
    def determiner_mois_a_regler(contrat):
        """
        Détermine le mois à régler en utilisant EXACTEMENT la même logique que les paiements globaux.
        Prend en compte :
        - Le dernier paiement de loyer validé (avec mois_paye si disponible)
        - Les avances actives
        - Le prochain mois attendu
        """
        try:
            # Utiliser la même méthode que les paiements globaux
            from .services_avance import ServiceGestionAvance
            prochain_mois = ServiceGestionAvance.calculer_prochain_mois_paiement(contrat)
            
            # Convertir en format "mois année" (ex: "décembre 2024")
            mois_francais = [
                'janvier', 'février', 'mars', 'avril', 'mai', 'juin',
                'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre'
            ]
            
            mois_str = f"{mois_francais[prochain_mois.month - 1]} {prochain_mois.year}"
            
            return {
                'mois_paye': mois_str,
                'date_mois': prochain_mois,
                'mois': prochain_mois.month,
                'annee': prochain_mois.year
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la détermination du mois à régler: {str(e)}")
            # Fallback : mois actuel
            now = timezone.now()
            mois_francais = [
                'janvier', 'février', 'mars', 'avril', 'mai', 'juin',
                'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre'
            ]
            mois_str = f"{mois_francais[now.month - 1]} {now.year}"
            return {
                'mois_paye': mois_str,
                'date_mois': now.date().replace(day=1),
                'mois': now.month,
                'annee': now.year
            }
    
    @staticmethod
    def convertir_mois_paye_en_date(mois_paye_str):
        """
        Convertit 'mois année' (ex: "Novembre 2024") ou 'mois' (ex: "novembre") en date.
        Si l'année n'est pas fournie, détermine l'année intelligemment.
        Utilise la même logique que ServiceGestionAvance.
        """
        if not mois_paye_str:
            return None
        
        mois_francais = {
            'janvier': 1, 'février': 2, 'mars': 3, 'avril': 4,
            'mai': 5, 'juin': 6, 'juillet': 7, 'août': 8,
            'septembre': 9, 'octobre': 10, 'novembre': 11, 'décembre': 12
        }
        mois_anglais = {
            'january': 1, 'february': 2, 'march': 3, 'april': 4,
            'may': 5, 'june': 6, 'july': 7, 'august': 8,
            'september': 9, 'october': 10, 'november': 11, 'december': 12
        }
        
        mois_paye_lower = mois_paye_str.lower().strip()
        mois_num = None
        
        # Trouver le mois
        for mois, num in {**mois_francais, **mois_anglais}.items():
            if mois in mois_paye_lower:
                mois_num = num
                break
        
        if not mois_num:
            return None
        
        # Extraire l'année si présente
        annee_match = re.search(r'(\d{4})', mois_paye_str)
        if annee_match:
            annee = int(annee_match.group(1))
            return date(annee, mois_num, 1)
        
        # Si pas d'année, utiliser TOUJOURS l'année courante réelle
        annee_actuelle = timezone.now().year
        
        return date(annee_actuelle, mois_num, 1)
    
    @staticmethod
    def calculer_montant_du_mois(contrat, mois_paye=None, date_mois=None):
        """
        Calcule le montant total dû pour un mois donné
        UTILISE LA MÊME LOGIQUE QUE LES PAIEMENTS GLOBAUX
        (loyer + charges - charges déductibles - charges bailleur - avances actives)
        """
        try:
            from .models import ChargeDeductible
            from paiements.models import ChargeBailleur
            from .services_avance import ServiceGestionAvance
            from django.db.models import Sum
            
            # Déterminer le mois et l'année
            if date_mois:
                mois_num = date_mois.month
                annee = date_mois.year
            elif mois_paye:
                date_mois_obj = ServicePaiementPartiel.convertir_mois_paye_en_date(mois_paye)
                if date_mois_obj:
                    mois_num = date_mois_obj.month
                    annee = date_mois_obj.year
                else:
                    mois_num = datetime.now().month
                    annee = datetime.now().year
            else:
                mois_num = datetime.now().month
                annee = datetime.now().year
            
            # UTILISER LA MÊME MÉTHODE QUE LES PAIEMENTS GLOBAUX
            # ServiceGestionAvance.calculer_montant_du_mois() prend en compte les avances
            date_mois_calculee = date(annee, mois_num, 1)
            montant_du_mois, montant_avance_utilisee = ServiceGestionAvance.calculer_montant_du_mois(
                contrat, date_mois_calculee
            )
            
            return montant_du_mois
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul du montant dû: {str(e)}")
            # Fallback : calcul simple sans avances
            try:
                montant_base = Decimal(str(contrat.loyer_mensuel or '0'))
                charges_mensuelles = Decimal(str(contrat.charges_mensuelles or '0'))
                return max(montant_base + charges_mensuelles, Decimal('0'))
            except:
                return Decimal('0')
    
    @staticmethod
    def calculer_montant_restant(contrat, mois_paye):
        """
        Calcule le montant restant à payer pour un mois donné
        en tenant compte de tous les paiements partiels
        UTILISE LA MÊME LOGIQUE QUE LES PAIEMENTS GLOBAUX
        """
        try:
            # Convertir mois_paye en date
            date_mois = ServicePaiementPartiel.convertir_mois_paye_en_date(mois_paye)
            
            # Calculer le montant dû (avec avances si applicable)
            montant_du_mois = ServicePaiementPartiel.calculer_montant_du_mois(
                contrat, mois_paye, date_mois
            )
            
            # Calculer le total des paiements pour ce mois (exact match du mois_paye)
            # Utiliser une correspondance exacte pour éviter les faux positifs
            paiements_mois = Paiement.objects.filter(
                contrat=contrat,
                mois_paye=mois_paye,  # Correspondance exacte
                is_deleted=False,
                statut__in=['valide', 'en_attente']
            )
            
            total_paye = paiements_mois.aggregate(
                total=Sum('montant')
            )['total'] or Decimal('0')
            
            montant_restant = max(montant_du_mois - total_paye, Decimal('0'))
            
            return {
                'montant_du_mois': montant_du_mois,
                'total_paye': total_paye,
                'montant_restant': montant_restant,
                'est_complet': montant_restant == Decimal('0'),
                'nombre_paiements': paiements_mois.count(),
                'date_mois': date_mois
            }
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul du montant restant: {str(e)}")
            return {
                'montant_du_mois': Decimal('0'),
                'total_paye': Decimal('0'),
                'montant_restant': Decimal('0'),
                'est_complet': True,
                'nombre_paiements': 0,
                'date_mois': None
            }
    
    @staticmethod
    def synchroniser_paiement_partiel(paiement, skip_verification=False):
        """
        Synchronise un paiement partiel avec le système
        et met à jour les statuts appropriés
        Vérifie automatiquement si un reliquat est complété et met à jour tous les paiements concernés
        
        Args:
            paiement: Instance de Paiement
            skip_verification: Si True, ne vérifie pas la complétion (évite la récursion)
        """
        try:
            # ÉVITER LA RÉCURSION : Vérifier si on est déjà en train de traiter ce paiement
            if hasattr(paiement, '_en_synchronisation'):
                return paiement.est_paiement_partiel
            
            # Marquer pour éviter la récursion
            paiement._en_synchronisation = True
            
            # Détecter si c'est un paiement partiel
            est_partiel = ServicePaiementPartiel.detecter_paiement_partiel(paiement)
            
            if est_partiel:
                # Marquer le type de paiement comme partiel
                if paiement.type_paiement != 'paiement_partiel':
                    paiement.type_paiement = 'paiement_partiel'
                
                # Sauvegarder les modifications SANS déclencher les signaux pour éviter la récursion
                # Utiliser update_fields pour limiter les signaux
                paiement.save(update_fields=['est_paiement_partiel', 'montant_restant_du', 'montant_du_mois', 'type_paiement'])
                
                logger.info(
                    f"Paiement partiel synchronisé: {paiement.reference_paiement}"
                )
                
                # VÉRIFIER SI CE PAIEMENT COMPLÈTE UN RELIQUAT (seulement si pas skip)
                if not skip_verification:
                    ServicePaiementPartiel.verifier_completion_paiement(paiement, skip_save=True)
                
                return True
            else:
                # Si le paiement est complet, vérifier s'il y avait des paiements partiels précédents
                if not skip_verification:
                    ServicePaiementPartiel.verifier_completion_paiement(paiement, skip_save=True)
                return False
                
        except Exception as e:
            logger.error(f"Erreur lors de la synchronisation: {str(e)}")
            return False
        finally:
            # Retirer le flag
            if hasattr(paiement, '_en_synchronisation'):
                delattr(paiement, '_en_synchronisation')
    
    @staticmethod
    def verifier_completion_paiement(paiement, skip_save=False):
        """
        Vérifie si un paiement complète un paiement partiel précédent
        MET À JOUR AUTOMATIQUEMENT tous les paiements partiels concernés
        
        Args:
            paiement: Instance de Paiement
            skip_save: Si True, utilise update() au lieu de save() pour éviter les signaux
        """
        try:
            # ÉVITER LA RÉCURSION : Vérifier si on est déjà en train de traiter
            if hasattr(paiement, '_en_verification_completion'):
                return False
            
            # Marquer pour éviter la récursion
            paiement._en_verification_completion = True
            
            contrat = paiement.contrat
            if not contrat or not paiement.mois_paye:
                return False
            
            # Vérifier si le montant restant est maintenant à zéro
            calcul = ServicePaiementPartiel.calculer_montant_restant(
                contrat, paiement.mois_paye
            )
            
            if calcul['est_complet']:
                # Marquer TOUS les paiements partiels de ce mois comme complétés
                # Utiliser UPDATE() au lieu de save() pour éviter les signaux et la récursion
                paiements_partiels = Paiement.objects.filter(
                    contrat=contrat,
                    mois_paye=paiement.mois_paye,  # Correspondance exacte
                    est_paiement_partiel=True,
                    is_deleted=False,
                    statut__in=['valide', 'en_attente']
                )
                
                # Utiliser update() pour éviter les signaux
                count = paiements_partiels.update(
                    est_paiement_partiel=False,
                    montant_restant_du=Decimal('0')
                )
                
                logger.info(
                    f"✅ RELIQUAT COMPLÉTÉ pour {contrat.numero_contrat} - {paiement.mois_paye}. "
                    f"{count} paiement(s) marqué(s) comme complété(s)"
                )
                
                return True
            else:
                # Même si le mois n'est pas complété, mettre à jour les montants restants
                # de tous les paiements partiels de ce mois pour qu'ils soient à jour
                paiements_partiels = Paiement.objects.filter(
                    contrat=contrat,
                    mois_paye=paiement.mois_paye,
                    est_paiement_partiel=True,
                    is_deleted=False,
                    statut__in=['valide', 'en_attente']
                )
                
                # Recalculer le montant restant pour chaque paiement partiel
                montant_du_mois = calcul.get('montant_du_mois', Decimal('0'))
                montant_restant_mois = calcul.get('montant_restant', Decimal('0'))
                
                # Utiliser bulk_update pour éviter les signaux multiples
                paiements_a_mettre_a_jour = []
                for pp in paiements_partiels:
                    # Mettre à jour le montant du mois
                    pp.montant_du_mois = montant_du_mois
                    
                    # Si le mois est complété, marquer ce paiement comme complété
                    if montant_restant_mois == 0:
                        pp.est_paiement_partiel = False
                        pp.montant_restant_du = Decimal('0')
                    else:
                        # Sinon, mettre à jour le montant restant du paiement individuel
                        montant_restant_paiement = max(
                            montant_du_mois - pp.montant,
                            Decimal('0')
                        )
                        pp.montant_restant_du = montant_restant_paiement
                        # Si le montant restant est 0, le paiement individuel est complet
                        if pp.montant_restant_du == 0:
                            pp.est_paiement_partiel = False
                    
                    paiements_a_mettre_a_jour.append(pp)
                
                # Utiliser bulk_update pour éviter les signaux
                if paiements_a_mettre_a_jour and not skip_save:
                    Paiement.objects.bulk_update(
                        paiements_a_mettre_a_jour,
                        ['est_paiement_partiel', 'montant_restant_du', 'montant_du_mois']
                    )
                
                return False
            
        except Exception as e:
            logger.error(f"Erreur lors de la vérification de complétion: {str(e)}")
            return False
        finally:
            # Retirer le flag
            if hasattr(paiement, '_en_verification_completion'):
                delattr(paiement, '_en_verification_completion')
    
    @staticmethod
    def detecter_contrats_avec_paiements_partiels():
        """
        Détecte tous les contrats ayant des paiements partiels en cours
        Inclut TOUS les paiements partiels, même ceux complétés
        Détecte aussi les paiements partiels non synchronisés
        """
        try:
            # Trouver tous les paiements partiels actifs (avec montant restant > 0)
            paiements_partiels_actifs = Paiement.objects.filter(
                est_paiement_partiel=True,
                montant_restant_du__gt=0,
                is_deleted=False,
                statut__in=['valide', 'en_attente']
            ).select_related('contrat', 'contrat__locataire', 'contrat__propriete').order_by('date_paiement')
            
            # AUSSI : Trouver tous les paiements partiels (même complétés) pour l'historique complet
            paiements_partiels_tous = Paiement.objects.filter(
                est_paiement_partiel=True,
                is_deleted=False,
                statut__in=['valide', 'en_attente']
            ).select_related('contrat', 'contrat__locataire', 'contrat__propriete').order_by('date_paiement')
            
            # DÉTECTION DYNAMIQUE : Vérifier aussi les paiements qui pourraient être partiels mais non synchronisés
            # Pour chaque paiement avec un mois_paye, vérifier s'il est partiel
            paiements_a_verifier = Paiement.objects.filter(
                is_deleted=False,
                statut__in=['valide', 'en_attente'],
                mois_paye__isnull=False
            ).exclude(
                est_paiement_partiel=True
            ).select_related('contrat', 'contrat__locataire', 'contrat__propriete')
            
            # Vérifier dynamiquement si ces paiements sont partiels
            paiements_partiels_non_synchronises = []
            for paiement in paiements_a_verifier:
                if ServicePaiementPartiel.detecter_paiement_partiel(paiement):
                    # Si c'est un paiement partiel, l'ajouter à la liste
                    paiements_partiels_non_synchronises.append(paiement)
                    # Synchroniser le paiement pour mettre à jour les champs
                    ServicePaiementPartiel.synchroniser_paiement_partiel(paiement)
                    paiement.save()
            
            # Grouper par contrat
            contrats_avec_partiels = {}
            
            # D'abord, identifier les contrats avec paiements partiels actifs
            for paiement in paiements_partiels_actifs:
                contrat_id = paiement.contrat.id
                if contrat_id not in contrats_avec_partiels:
                    contrats_avec_partiels[contrat_id] = {
                        'contrat': paiement.contrat,
                        'paiements_partiels': [],
                        'paiements_partiels_tous': [],  # Tous les paiements partiels (historique complet)
                        'montant_total_restant': Decimal('0')
                    }
                
                contrats_avec_partiels[contrat_id]['paiements_partiels'].append(paiement)
                contrats_avec_partiels[contrat_id]['montant_total_restant'] += paiement.montant_restant_du
            
            # Ajouter les paiements partiels non synchronisés
            for paiement in paiements_partiels_non_synchronises:
                contrat_id = paiement.contrat.id
                if contrat_id not in contrats_avec_partiels:
                    contrats_avec_partiels[contrat_id] = {
                        'contrat': paiement.contrat,
                        'paiements_partiels': [],
                        'paiements_partiels_tous': [],
                        'montant_total_restant': Decimal('0')
                    }
                
                if paiement.montant_restant_du > 0:
                    contrats_avec_partiels[contrat_id]['paiements_partiels'].append(paiement)
                    contrats_avec_partiels[contrat_id]['montant_total_restant'] += paiement.montant_restant_du
            
            # Ensuite, ajouter TOUS les paiements partiels (y compris complétés) pour chaque contrat
            for paiement in paiements_partiels_tous:
                contrat_id = paiement.contrat.id
                if contrat_id in contrats_avec_partiels:
                    # Ajouter à la liste complète si pas déjà présent
                    if paiement not in contrats_avec_partiels[contrat_id]['paiements_partiels_tous']:
                        contrats_avec_partiels[contrat_id]['paiements_partiels_tous'].append(paiement)
            
            # Ajouter aussi les paiements partiels non synchronisés à la liste complète
            for paiement in paiements_partiels_non_synchronises:
                contrat_id = paiement.contrat.id
                if contrat_id in contrats_avec_partiels:
                    if paiement not in contrats_avec_partiels[contrat_id]['paiements_partiels_tous']:
                        contrats_avec_partiels[contrat_id]['paiements_partiels_tous'].append(paiement)
            
            # RECALCULER DYNAMIQUEMENT le montant restant pour chaque contrat
            # pour garantir que les données sont à jour et cohérentes
            for contrat_id in contrats_avec_partiels:
                data = contrats_avec_partiels[contrat_id]
                contrat = data['contrat']
                
                # Recalculer le montant total restant à partir des paiements actifs
                montant_total_restant_recalcule = Decimal('0')
                paiements_actifs_recalcules = []
                
                # Grouper les paiements par mois pour recalculer correctement
                paiements_par_mois = {}
                for paiement in data['paiements_partiels_tous']:
                    mois_cle = paiement.mois_paye or 'non_specifie'
                    if mois_cle not in paiements_par_mois:
                        paiements_par_mois[mois_cle] = []
                    paiements_par_mois[mois_cle].append(paiement)
                
                # Recalculer pour chaque mois
                for mois_cle, paiements_mois in paiements_par_mois.items():
                    if mois_cle != 'non_specifie':
                        # Calculer le montant restant TOTAL pour ce mois
                        calcul_restant = ServicePaiementPartiel.calculer_montant_restant(
                            contrat, mois_cle
                        )
                        montant_du_mois = calcul_restant.get('montant_du_mois', Decimal('0'))
                        montant_restant_mois = calcul_restant.get('montant_restant', Decimal('0'))
                        est_complet = calcul_restant.get('est_complet', False)
                        
                        # Mettre à jour chaque paiement de ce mois
                        for paiement in paiements_mois:
                            paiement.montant_du_mois = montant_du_mois
                            
                            if est_complet or montant_restant_mois == 0:
                                # Le mois est complété, donc ce paiement n'a plus de montant restant
                                paiement.montant_restant_du = Decimal('0')
                                paiement.est_paiement_partiel = False
                            else:
                                # Le mois n'est pas complété
                                # Le montant restant du paiement individuel = montant_du_mois - montant_paye
                                # Mais seulement si le paiement est vraiment partiel
                                montant_restant_paiement = max(
                                    montant_du_mois - paiement.montant,
                                    Decimal('0')
                                )
                                
                                # Si le paiement individuel a un montant restant, l'utiliser
                                # Sinon, utiliser le montant restant du mois divisé par le nombre de paiements
                                if montant_restant_paiement > 0:
                                    paiement.montant_restant_du = montant_restant_paiement
                                else:
                                    # Le paiement individuel est complet, mais le mois ne l'est pas
                                    # Donc le montant restant est 0 pour ce paiement
                                    paiement.montant_restant_du = Decimal('0')
                                
                                # Si le paiement a encore un montant restant, l'ajouter aux actifs
                                if paiement.montant_restant_du > 0:
                                    paiements_actifs_recalcules.append(paiement)
                                    montant_total_restant_recalcule += paiement.montant_restant_du
                    
                    else:
                        # Pour les paiements sans mois spécifié, utiliser le montant restant existant
                        for paiement in paiements_mois:
                            if paiement.montant_restant_du and paiement.montant_restant_du > 0:
                                paiements_actifs_recalcules.append(paiement)
                                montant_total_restant_recalcule += paiement.montant_restant_du
                
                # Mettre à jour les données avec les valeurs recalculées
                data['paiements_partiels'] = paiements_actifs_recalcules
                data['montant_total_restant'] = montant_total_restant_recalcule
                
                # Trier tous les paiements partiels par date
                data['paiements_partiels'].sort(key=lambda x: x.date_paiement, reverse=True)
                data['paiements_partiels_tous'].sort(key=lambda x: x.date_paiement, reverse=True)
            
            return contrats_avec_partiels
            
        except Exception as e:
            logger.error(f"Erreur lors de la détection des contrats: {str(e)}")
            return {}
    
    @staticmethod
    def obtenir_statistiques_paiements_partiels(contrats_avec_partiels=None):
        """
        Obtient des statistiques sur les paiements partiels
        CALCULE DYNAMIQUEMENT à partir des contrats détectés pour garantir la cohérence
        """
        try:
            # Si les contrats sont fournis, calculer les stats à partir de ces données
            if contrats_avec_partiels is not None:
                total_paiements_partiels_actifs = 0
                montant_total_restant = Decimal('0')
                contrats_concernes = len(contrats_avec_partiels)
                
                for contrat_id, data in contrats_avec_partiels.items():
                    # Compter seulement les paiements partiels actifs (avec montant restant > 0)
                    paiements_actifs = [p for p in data['paiements_partiels'] if p.montant_restant_du > 0]
                    total_paiements_partiels_actifs += len(paiements_actifs)
                    montant_total_restant += data['montant_total_restant']
                
                return {
                    'total_paiements_partiels': total_paiements_partiels_actifs,
                    'montant_total_restant': montant_total_restant,
                    'contrats_concernes': contrats_concernes
                }
            
            # Sinon, calculer depuis la base de données (méthode de fallback)
            paiements_partiels_actifs = Paiement.objects.filter(
                est_paiement_partiel=True,
                montant_restant_du__gt=0,
                is_deleted=False,
                statut__in=['valide', 'en_attente']
            )
            
            total_partiels = paiements_partiels_actifs.count()
            montant_total_restant = paiements_partiels_actifs.aggregate(
                total=Sum('montant_restant_du')
            )['total'] or Decimal('0')
            
            # Contrats avec paiements partiels actifs
            contrats_avec_partiels_count = paiements_partiels_actifs.values(
                'contrat'
            ).distinct().count()
            
            return {
                'total_paiements_partiels': total_partiels,
                'montant_total_restant': montant_total_restant,
                'contrats_concernes': contrats_avec_partiels_count
            }
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul des statistiques: {str(e)}")
            return {
                'total_paiements_partiels': 0,
                'montant_total_restant': Decimal('0'),
                'contrats_concernes': 0
            }
    
    @staticmethod
    def detecter_reliquats_en_cours(contrat):
        """
        Détecte tous les reliquats (paiements partiels non complétés) pour un contrat donné.
        Retourne une liste de dictionnaires avec les détails de chaque reliquat.
        """
        try:
            # Trouver tous les paiements partiels non complétés pour ce contrat
            paiements_partiels = Paiement.objects.filter(
                contrat=contrat,
                est_paiement_partiel=True,
                montant_restant_du__gt=0,
                is_deleted=False,
                statut__in=['valide', 'en_attente']
            ).order_by('mois_paye', 'date_paiement')
            
            if not paiements_partiels.exists():
                return []
            
            # Grouper par mois_paye pour avoir un résumé par mois
            reliquats_par_mois = {}
            
            for paiement in paiements_partiels:
                mois_cle = paiement.mois_paye or 'Non spécifié'
                
                if mois_cle not in reliquats_par_mois:
                    # Calculer le montant restant total pour ce mois
                    calcul_restant = ServicePaiementPartiel.calculer_montant_restant(
                        contrat, paiement.mois_paye
                    )
                    
                    reliquats_par_mois[mois_cle] = {
                        'mois_paye': paiement.mois_paye,
                        'montant_du_mois': calcul_restant['montant_du_mois'],
                        'total_paye': calcul_restant['total_paye'],
                        'montant_restant': calcul_restant['montant_restant'],
                        'nombre_paiements': calcul_restant['nombre_paiements'],
                        'paiements': [],
                        'date_mois': calcul_restant.get('date_mois'),
                        'est_complet': calcul_restant['est_complet']
                    }
                
                reliquats_par_mois[mois_cle]['paiements'].append({
                    'id': paiement.id,
                    'reference': paiement.reference_paiement or f"PAI-{paiement.id}",
                    'date_paiement': paiement.date_paiement,
                    'montant_paye': paiement.montant,
                    'montant_restant': paiement.montant_restant_du,
                    'statut': paiement.get_statut_display()
                })
            
            # Convertir en liste
            reliquats = []
            for mois_cle, details in reliquats_par_mois.items():
                if not details['est_complet'] and details['montant_restant'] > 0:
                    reliquats.append(details)
            
            # Trier par date (le plus ancien en premier)
            reliquats.sort(key=lambda x: x['date_mois'] if x['date_mois'] else date(1900, 1, 1))
            
            return reliquats
            
        except Exception as e:
            logger.error(f"Erreur lors de la détection des reliquats: {str(e)}")
            return []
    
    @staticmethod
    def detecter_reliquats_en_cours(contrat):
        """
        Détecte les reliquats (paiements partiels non complétés) pour un contrat donné.
        Retourne une liste des reliquats avec leurs détails.
        """
        try:
            # Trouver tous les paiements partiels actifs pour ce contrat
            paiements_partiels = Paiement.objects.filter(
                contrat=contrat,
                est_paiement_partiel=True,
                montant_restant_du__gt=0,
                is_deleted=False,
                statut__in=['valide', 'en_attente']
            ).order_by('mois_paye', 'date_paiement')
            
            reliquats = []
            for paiement in paiements_partiels:
                # Calculer le montant restant pour ce mois
                calcul_restant = ServicePaiementPartiel.calculer_montant_restant(
                    contrat, paiement.mois_paye or ''
                )
                
                if calcul_restant['montant_restant'] > 0:
                    reliquats.append({
                        'paiement': paiement,
                        'mois_paye': paiement.mois_paye or 'Non spécifié',
                        'montant_paye': paiement.montant,
                        'montant_du_mois': calcul_restant['montant_du_mois'],
                        'montant_restant': calcul_restant['montant_restant'],
                        'total_paye_pour_mois': calcul_restant['total_paye'],
                        'nombre_paiements': calcul_restant['nombre_paiements'],
                        'date_paiement': paiement.date_paiement,
                        'pourcentage_paye': (calcul_restant['total_paye'] / calcul_restant['montant_du_mois'] * 100) if calcul_restant['montant_du_mois'] > 0 else 0
                    })
            
            return reliquats
            
        except Exception as e:
            logger.error(f"Erreur lors de la détection des reliquats: {str(e)}")
            return []

