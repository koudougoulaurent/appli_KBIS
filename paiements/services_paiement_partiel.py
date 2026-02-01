"""
Service pour gérer la logique des paiements partiels
RESPECTE À LA LETTRE TOUTES LES LOGIQUES DU PAIEMENT GLOBAL
"""
from decimal import Decimal
from django.db.models import Sum, Q
from django.utils import timezone
from django.core.cache import cache
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
            
            # 2. VALIDATION CRITIQUE : Si le mois proposé est AVANT le mois attendu, il est DÉJÀ COUVERT
            # Si le mois attendu est janvier 2026, alors décembre 2025 est déjà couvert (payé ou avance)
            if date_mois_propose < date_mois_attendu:
                # VÉRIFIER si le mois proposé est couvert par une avance active
                from .models_avance import AvanceLoyer
                avances_actives = AvanceLoyer.objects.filter(
                    contrat=contrat,
                    statut='active',
                    montant_restant__gt=0
                )
                
                mois_couvert_par_avance = False
                for avance in avances_actives:
                    if avance.mois_debut_couverture and avance.mois_fin_couverture:
                        if avance.mois_debut_couverture <= date_mois_propose <= avance.mois_fin_couverture:
                            mois_couvert_par_avance = True
                            break
                
                if mois_couvert_par_avance:
                    # Le mois est couvert par une avance - REFUSER
                    return {
                        'valide': False,
                        'message': f"❌ IMPOSSIBLE : Le mois {mois_paye_str} est déjà couvert par une avance active. "
                                  f"Le prochain mois à payer est {mois_attendu['mois_paye']} (mois suivant le dernier paiement).",
                        'mois_attendu': mois_attendu['mois_paye'],
                        'mois_propose': mois_paye_str,
                        'type_erreur': 'mois_couvert_avance',
                        'suggestion': f"Ce mois est déjà couvert par une avance. Le prochain mois à payer est {mois_attendu['mois_paye']}."
                    }
                
                # Récupérer le dernier paiement validé pour ce contrat
                from .models import Paiement
                dernier_paiement = Paiement.objects.filter(
                    contrat=contrat,
                    type_paiement='loyer',
                    statut='valide',
                    is_deleted=False
                ).order_by('-date_paiement').first()
                
                # Déterminer le dernier mois payé (basé sur mois_paye si disponible, sinon date_paiement)
                dernier_mois_paye_date = None
                if dernier_paiement:
                    if dernier_paiement.mois_paye:
                        # Utiliser le mois_paye du dernier paiement
                        dernier_mois_paye_date = ServicePaiementPartiel.convertir_mois_paye_en_date(dernier_paiement.mois_paye)
                    else:
                        # Fallback sur date_paiement
                        dernier_mois_paye_date = dernier_paiement.date_paiement.replace(day=1)
                else:
                    # Pas de paiement précédent - utiliser le début du contrat
                    dernier_mois_paye_date = contrat.date_debut.replace(day=1) if contrat.date_debut else None
                
                # VALIDATION CRITIQUE : Le mois proposé doit être entre le dernier mois payé et le mois attendu
                if dernier_mois_paye_date and date_mois_propose < dernier_mois_paye_date:
                    # Le mois proposé est AVANT le dernier paiement - REFUSER
                    return {
                        'valide': False,
                        'message': f"❌ IMPOSSIBLE : Le mois {mois_paye_str} est antérieur au dernier paiement validé. "
                                  f"Vous devez payer les mois non payés entre le dernier paiement et le mois attendu ({mois_attendu['mois_paye']}).",
                        'mois_attendu': mois_attendu['mois_paye'],
                        'mois_propose': mois_paye_str,
                        'type_erreur': 'mois_trop_ancien',
                        'suggestion': f"Le prochain mois à payer est {mois_attendu['mois_paye']}. "
                                     f"Vous ne pouvez payer que les mois non payés entre le dernier paiement et ce mois."
                    }
                
                # Si le mois proposé est entre le dernier paiement et le mois attendu, il est DÉJÀ COUVERT
                # Car le mois attendu = mois suivant le dernier paiement (ou après avances)
                # Donc tout mois < mois attendu est déjà couvert
                return {
                    'valide': False,
                    'message': f"❌ IMPOSSIBLE : Le mois {mois_paye_str} est déjà couvert. "
                              f"Le prochain mois à payer est {mois_attendu['mois_paye']} (mois suivant le dernier paiement). "
                              f"Si le mois attendu est {mois_attendu['mois_paye']}, alors tous les mois précédents sont déjà payés ou couverts par des avances.",
                    'mois_attendu': mois_attendu['mois_paye'],
                    'mois_propose': mois_paye_str,
                    'type_erreur': 'mois_deja_couvert',
                    'suggestion': f"Le prochain mois à payer est {mois_attendu['mois_paye']}. "
                                 f"Vous ne pouvez pas payer un mois qui est déjà couvert."
                }
                
                # RÈGLE ABSOLUE : Si le mois proposé est < mois attendu, il est DÉJÀ COUVERT
                # Le mois attendu = mois suivant le dernier paiement (ou après avances)
                # Donc tout mois < mois attendu est déjà payé ou couvert par une avance
                # AUCUNE EXCEPTION : on ne peut pas payer un mois qui est avant le mois attendu
                return {
                    'valide': False,
                    'message': f"❌ IMPOSSIBLE : Le mois {mois_paye_str} est déjà couvert. "
                              f"Le prochain mois à payer est {mois_attendu['mois_paye']}. "
                              f"Si le mois attendu est {mois_attendu['mois_paye']}, alors tous les mois précédents (y compris {mois_paye_str}) sont déjà payés ou couverts par des avances.",
                    'mois_attendu': mois_attendu['mois_paye'],
                    'mois_propose': mois_paye_str,
                    'type_erreur': 'mois_deja_couvert',
                    'suggestion': f"Le prochain mois à payer est {mois_attendu['mois_paye']}. "
                                 f"Vous ne pouvez pas payer un mois qui est avant le mois attendu."
                }
            
            # 3. VALIDATION STRICTE : Le mois proposé doit être EXACTEMENT le mois attendu
            # Après un paiement de décembre, seul janvier doit être accepté, pas n'importe quel mois
            if date_mois_propose == date_mois_attendu:
                # Le mois proposé est exactement le mois attendu - VALIDER
                return {
                    'valide': True,
                    'mois_attendu': mois_attendu['mois_paye'],
                    'date_mois': date_mois_attendu
                }
            else:
                # Le mois proposé n'est ni en retard ni exactement le mois attendu - REFUSER
                # C'est probablement un mois futur entre le mois attendu et le mois courant
                return {
                    'valide': False,
                    'message': f"❌ MOIS INCORRECT : Vous devez payer le mois {mois_attendu['mois_paye']} (mois suivant le dernier paiement), "
                              f"pas {mois_paye_str}. "
                              f"Si vous souhaitez payer plusieurs mois à l'avance, utilisez le type de paiement 'AVANCE DE LOYER'.",
                    'mois_attendu': mois_attendu['mois_paye'],
                    'mois_propose': mois_paye_str,
                    'type_erreur': 'mois_incorrect',
                    'suggestion': f"Le prochain mois à payer est {mois_attendu['mois_paye']}. "
                                 f"Pour payer plusieurs mois à l'avance, changez le type de paiement en 'AVANCE DE LOYER'."
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
        Détermine le mois à régler.
        RÈGLE ABSOLUE : Le mois attendu est TOUJOURS le mois suivant le dernier paiement validé.
        Si aucun paiement n'existe, retourne le mois suivant le mois actuel.
        """
        try:
            # Utiliser la méthode qui calcule le prochain mois (toujours = dernier paiement + 1 mois)
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
            # Fallback : mois suivant le mois actuel
            from dateutil.relativedelta import relativedelta
            now = timezone.now().date().replace(day=1)
            prochain_mois = now + relativedelta(months=1)
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
                'montant_paye': total_paye,
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
                'montant_paye': Decimal('0'),
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
                # Utiliser la nouvelle méthode verifier_et_completer_reliquat
                if not skip_verification:
                    ServicePaiementPartiel.verifier_et_completer_reliquat(
                        paiement=paiement,
                        skip_save=True
                    )
                
                return True
            else:
                # Si le paiement est complet, vérifier s'il complète d'autres paiements partiels du même mois
                if not skip_verification:
                    ServicePaiementPartiel.verifier_et_completer_reliquat(
                        paiement=paiement,
                        skip_save=True
                    )
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
    def detecter_contrats_avec_paiements_partiels(force_refresh=False):
        """
        Détecte tous les contrats ayant des paiements partiels en cours
        Inclut TOUS les paiements partiels, même ceux complétés
        OPTIMISÉ avec cache pour améliorer les performances
        """
        # Utiliser le cache pour éviter les requêtes répétées (cache 5 minutes)
        cache_key = 'contrats_avec_paiements_partiels'
        if not force_refresh:
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result
        
        try:
            # OPTIMISATION : Une seule requête pour récupérer tous les paiements partiels
            # Utiliser only() pour limiter les champs récupérés
            paiements_partiels_all = Paiement.objects.filter(
                est_paiement_partiel=True,
                is_deleted=False,
                statut__in=['valide', 'en_attente']
            ).select_related('contrat', 'contrat__locataire', 'contrat__propriete').only(
                'id', 'montant', 'montant_restant_du', 'montant_du_mois', 'mois_paye',
                'date_paiement', 'est_paiement_partiel', 'statut',
                'contrat__id', 'contrat__numero_contrat', 'contrat__loyer_mensuel',
                'contrat__locataire__id', 'contrat__locataire__nom', 'contrat__locataire__prenom',
                'contrat__propriete__id', 'contrat__propriete__titre', 'contrat__propriete__ville'
            ).order_by('date_paiement')
            
            # Séparer actifs et tous en Python (plus rapide que 2 requêtes)
            paiements_partiels_actifs = [p for p in paiements_partiels_all if p.montant_restant_du and p.montant_restant_du > 0]
            paiements_partiels_tous = list(paiements_partiels_all)
            
            # DÉSACTIVER la vérification dynamique par défaut pour améliorer les performances
            # Elle peut être réactivée si nécessaire avec un paramètre
            # LIMITER drastiquement : seulement les 10 derniers paiements récents
            paiements_a_verifier = []
            # Désactivé par défaut pour améliorer les performances
            # paiements_a_verifier = Paiement.objects.filter(
            #     is_deleted=False,
            #     statut__in=['valide', 'en_attente'],
            #     mois_paye__isnull=False
            # ).exclude(
            #     est_paiement_partiel=True
            # ).select_related('contrat', 'contrat__locataire', 'contrat__propriete').order_by('-date_paiement')[:10]
            
            # DÉSACTIVÉ : Vérification dynamique désactivée pour améliorer les performances
            # Elle peut être réactivée si nécessaire mais ralentit considérablement l'application
            paiements_partiels_non_synchronises = []
            
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
            
            # OPTIMISATION : Simplifier le recalcul - utiliser les valeurs déjà en base
            # Le recalcul dynamique est très coûteux, on utilise les valeurs existantes
            for contrat_id in contrats_avec_partiels:
                data = contrats_avec_partiels[contrat_id]
                
                # Utiliser directement les paiements actifs filtrés
                paiements_actifs = [p for p in data['paiements_partiels'] if p.montant_restant_du and p.montant_restant_du > 0]
                montant_total = sum(p.montant_restant_du for p in paiements_actifs)
                
                # Mettre à jour les données
                data['paiements_partiels'] = paiements_actifs
                data['montant_total_restant'] = montant_total
                
                # Trier tous les paiements partiels par date
                data['paiements_partiels'].sort(key=lambda x: x.date_paiement, reverse=True)
                data['paiements_partiels_tous'].sort(key=lambda x: x.date_paiement, reverse=True)
            
            # Mettre en cache le résultat (5 minutes)
            cache.set(cache_key, contrats_avec_partiels, 300)
            
            return contrats_avec_partiels
            
        except Exception as e:
            logger.error(f"Erreur lors de la détection des contrats: {str(e)}")
            return {}
    
    @staticmethod
    def obtenir_statistiques_paiements_partiels(contrats_avec_partiels=None):
        """
        Obtient des statistiques sur les paiements partiels
        OPTIMISÉ avec cache pour améliorer les performances
        """
        # Utiliser le cache pour éviter les requêtes répétées
        cache_key = 'statistiques_paiements_partiels'
        if contrats_avec_partiels is None:
            cached_stats = cache.get(cache_key)
            if cached_stats is not None:
                return cached_stats
        
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
                
                stats = {
                    'total_paiements_partiels': total_paiements_partiels_actifs,
                    'montant_total_restant': montant_total_restant,
                    'contrats_concernes': contrats_concernes
                }
                # Mettre en cache (5 minutes)
                cache.set(cache_key, stats, 300)
                return stats
            
            # Sinon, calculer depuis la base de données (méthode de fallback optimisée)
            # OPTIMISATION : Une seule requête avec aggregate
            from django.db.models import Count
            stats = Paiement.objects.filter(
                est_paiement_partiel=True,
                montant_restant_du__gt=0,
                is_deleted=False,
                statut__in=['valide', 'en_attente']
            ).aggregate(
                total_partiels=Count('id'),
                montant_total=Sum('montant_restant_du'),
                contrats_concernes=Count('contrat', distinct=True)
            )
            
            result = {
                'total_paiements_partiels': stats['total_partiels'] or 0,
                'montant_total_restant': stats['montant_total'] or Decimal('0'),
                'contrats_concernes': stats['contrats_concernes'] or 0
            }
            
            # Mettre en cache (5 minutes)
            cache.set(cache_key, result, 300)
            return result
            
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
    
    @staticmethod
    def verifier_et_completer_reliquat(paiement, skip_save=False):
        """
        Vérifie si un paiement complète automatiquement un reliquat de paiement partiel.
        Met à jour DYNAMIQUEMENT tous les paiements partiels du même mois.
        
        PROCESSUS :
        1. Calcule le montant total payé pour le mois du paiement
        2. Compare avec le montant dû pour ce mois
        3. Si le montant total >= montant dû, marque TOUS les paiements partiels du mois comme complétés
        4. Sinon, met à jour les montants restants de tous les paiements partiels
        
        Args:
            paiement: Instance de Paiement (nouveau paiement ou existant)
            skip_save: Si True, utilise update() au lieu de save() pour éviter les signaux
        
        Returns:
            bool: True si le reliquat a été complété, False sinon
        """
        try:
            # ÉVITER LA RÉCURSION : Vérifier si on est déjà en train de traiter
            if hasattr(paiement, '_en_completion_reliquat'):
                return False
            
            # Marquer pour éviter la récursion
            paiement._en_completion_reliquat = True
            
            contrat = paiement.contrat
            if not contrat or not paiement.mois_paye:
                logger.warning(
                    f"⚠️ Paiement {paiement.id} sans contrat ou mois_paye - "
                    f"impossible de vérifier la complétion"
                )
                return False
            
            # ÉTAPE 1 : Calculer le montant total payé pour ce mois
            # Inclure TOUS les paiements validés pour ce mois (partiels ou complets)
            calcul = ServicePaiementPartiel.calculer_montant_restant(
                contrat, paiement.mois_paye
            )
            
            montant_du_mois = calcul['montant_du_mois']
            total_paye = calcul['total_paye']
            montant_restant = calcul['montant_restant']
            
            logger.info(
                f"📊 VÉRIFICATION RELIQUAT - Contrat: {contrat.numero_contrat}, "
                f"Mois: {paiement.mois_paye}, Dû: {montant_du_mois}, "
                f"Payé: {total_paye}, Restant: {montant_restant}"
            )
            
            # ÉTAPE 2 : Récupérer TOUS les paiements partiels actifs pour ce mois
            paiements_partiels = Paiement.objects.filter(
                contrat=contrat,
                mois_paye=paiement.mois_paye,  # Correspondance exacte
                est_paiement_partiel=True,
                is_deleted=False,
                statut__in=['valide', 'en_attente']
            )
            
            # ÉTAPE 3 : Vérifier si le reliquat est complété
            if montant_restant <= 0:
                # ✅ RELIQUAT COMPLÉTÉ - Marquer TOUS les paiements partiels comme complétés
                count = paiements_partiels.update(
                    est_paiement_partiel=False,
                    montant_restant_du=Decimal('0'),
                    montant_du_mois=montant_du_mois
                )
                
                logger.info(
                    f"✅ RELIQUAT COMPLÉTÉ pour {contrat.numero_contrat} - {paiement.mois_paye}. "
                    f"{count} paiement(s) marqué(s) comme complété(s). "
                    f"Total payé: {total_paye}, Dû: {montant_du_mois}"
                )
                
                # Invalider le cache pour forcer un rafraîchissement
                cache_key = 'contrats_avec_paiements_partiels'
                cache.delete(cache_key)
                cache_key_stats = 'statistiques_paiements_partiels'
                cache.delete(cache_key_stats)
                
                return True
            else:
                # ⚠️ RELIQUAT NON COMPLÉTÉ - Mettre à jour les montants restants
                # Pour chaque paiement partiel, recalculer son montant restant individuel
                paiements_a_mettre_a_jour = []
                for pp in paiements_partiels:
                    # Le montant restant du mois est partagé proportionnellement
                    # Mais pour simplifier, on met à jour seulement le montant_du_mois
                    # et on garde le montant_restant_du calculé par rapport au montant individuel
                    pp.montant_du_mois = montant_du_mois
                    
                    # Calculer le montant restant pour ce paiement individuel
                    # Si le paiement individuel couvre le montant dû, il est complet
                    if pp.montant >= montant_du_mois:
                        pp.est_paiement_partiel = False
                        pp.montant_restant_du = Decimal('0')
                    else:
                        # Sinon, calculer combien il reste à payer au total pour le mois
                        # et mettre à jour le montant restant
                        pp.montant_restant_du = montant_restant
                    
                    paiements_a_mettre_a_jour.append(pp)
                
                # Utiliser bulk_update pour éviter les signaux multiples
                if paiements_a_mettre_a_jour:
                    Paiement.objects.bulk_update(
                        paiements_a_mettre_a_jour,
                        ['est_paiement_partiel', 'montant_restant_du', 'montant_du_mois']
                    )
                    
                    logger.info(
                        f"📊 RELIQUAT MIS À JOUR pour {contrat.numero_contrat} - {paiement.mois_paye}. "
                        f"{len(paiements_a_mettre_a_jour)} paiement(s) mis à jour. "
                        f"Restant: {montant_restant}"
                    )
                
                # Invalider le cache pour forcer un rafraîchissement
                cache_key = 'contrats_avec_paiements_partiels'
                cache.delete(cache_key)
                cache_key_stats = 'statistiques_paiements_partiels'
                cache.delete(cache_key_stats)
                
                return False
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la vérification de complétion du reliquat: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return False
        finally:
            # Retirer le flag
            if hasattr(paiement, '_en_completion_reliquat'):
                delattr(paiement, '_en_completion_reliquat')

