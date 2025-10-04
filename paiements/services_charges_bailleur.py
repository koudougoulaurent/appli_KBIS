"""
Service intelligent pour l'intégration automatique des charges bailleur
dans les paiements et récapitulatifs mensuels.
"""

from django.db.models import Sum, Q, F
from django.utils import timezone
from decimal import Decimal
from datetime import date, datetime
from typing import Dict, List, Optional, Tuple
from proprietes.models import ChargesBailleur, Bailleur, Propriete
from contrats.models import Contrat
from paiements.models import Paiement, RetraitBailleur, RecapMensuel
from core.models import AuditLog


class ServiceChargesBailleurIntelligent:
    """
    Service intelligent pour gérer l'intégration automatique des charges bailleur
    dans les systèmes de paiement et de récapitulatif.
    """
    
    @staticmethod
    def calculer_charges_bailleur_pour_mois(bailleur: Bailleur, mois: date) -> Dict:
        """
        Calcule toutes les charges bailleur pour un mois donné.
        
        Args:
            bailleur: Instance du bailleur
            mois: Date du mois (premier jour du mois)
            
        Returns:
            Dict contenant les détails des charges calculées
        """
        try:
            # Récupérer toutes les charges du bailleur pour le mois
            charges = ChargesBailleur.objects.filter(
                propriete__bailleur=bailleur,
                date_charge__year=mois.year,
                date_charge__month=mois.month,
                statut__in=['en_attente', 'deduite_retrait']
            ).select_related('propriete')
            
            total_charges = Decimal('0')
            charges_details = []
            charges_par_propriete = {}
            
            for charge in charges:
                montant_deductible = charge.get_montant_deductible()
                if montant_deductible > 0:
                    total_charges += montant_deductible
                    
                    # Détails de la charge
                    charge_detail = {
                        'charge': charge,
                        'montant_deductible': montant_deductible,
                        'propriete': charge.propriete,
                        'type_charge': charge.get_type_charge_display(),
                        'priorite': charge.get_priorite_display(),
                        'date_charge': charge.date_charge,
                        'statut': charge.get_statut_display()
                    }
                    charges_details.append(charge_detail)
                    
                    # Grouper par propriété
                    propriete_id = charge.propriete.id
                    if propriete_id not in charges_par_propriete:
                        charges_par_propriete[propriete_id] = {
                            'propriete': charge.propriete,
                            'charges': [],
                            'total_charges': Decimal('0')
                        }
                    charges_par_propriete[propriete_id]['charges'].append(charge_detail)
                    charges_par_propriete[propriete_id]['total_charges'] += montant_deductible
            
            return {
                'total_charges': total_charges,
                'nombre_charges': len(charges_details),
                'charges_details': charges_details,
                'charges_par_propriete': charges_par_propriete,
                'mois': mois,
                'bailleur': bailleur
            }
            
        except Exception as e:
            # Log de l'erreur
            ServiceChargesBailleurIntelligent._log_erreur(
                'calculer_charges_bailleur_pour_mois',
                f'Erreur lors du calcul des charges pour {bailleur} - {mois}: {str(e)}'
            )
            return {
                'total_charges': Decimal('0'),
                'nombre_charges': 0,
                'charges_details': [],
                'charges_par_propriete': {},
                'mois': mois,
                'bailleur': bailleur,
                'erreur': str(e)
            }
    
    @staticmethod
    def integrer_charges_dans_retrait(retrait: RetraitBailleur, mois: date = None) -> Dict:
        """
        Intègre automatiquement les charges bailleur dans un retrait mensuel.
        
        Args:
            retrait: Instance du retrait
            mois: Mois à traiter (par défaut: mois du retrait)
            
        Returns:
            Dict contenant le résumé de l'intégration
        """
        try:
            if mois is None:
                mois = retrait.mois_retrait
            
            # Calculer les charges pour le mois
            charges_data = ServiceChargesBailleurIntelligent.calculer_charges_bailleur_pour_mois(
                retrait.bailleur, mois
            )
            
            if charges_data.get('erreur'):
                return charges_data
            
            total_charges = charges_data['total_charges']
            charges_details = charges_data['charges_details']
            
            # Mettre à jour le montant du retrait
            montant_initial = retrait.montant_retrait
            montant_net = montant_initial - total_charges
            
            # Mettre à jour le retrait
            retrait.montant_retrait = montant_net
            retrait.charges_deductibles = total_charges
            retrait.save()
            
            # Marquer les charges comme déduites
            charges_deduites = []
            for charge_detail in charges_details:
                charge = charge_detail['charge']
                montant_deduit = charge.marquer_comme_deduit(charge_detail['montant_deductible'])
                if montant_deduit > 0:
                    charges_deduites.append({
                        'charge': charge,
                        'montant_deduit': montant_deduit
                    })
            
            # Créer un log d'intégration
            ServiceChargesBailleurIntelligent._log_integration_retrait(
                retrait, charges_deduites, total_charges
            )
            
            return {
                'success': True,
                'montant_initial': montant_initial,
                'total_charges': total_charges,
                'montant_net': montant_net,
                'charges_deduites': charges_deduites,
                'nombre_charges': len(charges_deduites)
            }
            
        except Exception as e:
            ServiceChargesBailleurIntelligent._log_erreur(
                'integrer_charges_dans_retrait',
                f'Erreur lors de l\'intégration des charges dans le retrait {retrait.id}: {str(e)}'
            )
            return {
                'success': False,
                'erreur': str(e)
            }
    
    @staticmethod
    def integrer_charges_dans_recap(recap: RecapMensuel, mois: date = None) -> Dict:
        """
        Intègre automatiquement les charges bailleur dans un récapitulatif mensuel.
        
        Args:
            recap: Instance du récapitulatif
            mois: Mois à traiter (par défaut: mois du récapitulatif)
            
        Returns:
            Dict contenant le résumé de l'intégration
        """
        try:
            if mois is None:
                mois = recap.mois_recap
            
            # Calculer les charges pour le mois
            charges_data = ServiceChargesBailleurIntelligent.calculer_charges_bailleur_pour_mois(
                recap.bailleur, mois
            )
            
            if charges_data.get('erreur'):
                return charges_data
            
            total_charges = charges_data['total_charges']
            
            # Mettre à jour le récapitulatif
            montant_initial = recap.total_net_a_payer
            montant_net = montant_initial - total_charges
            
            recap.total_charges_deductibles += total_charges
            recap.total_net_a_payer = montant_net
            recap.save()
            
            # Créer un log d'intégration
            ServiceChargesBailleurIntelligent._log_integration_recap(
                recap, charges_data['charges_details'], total_charges
            )
            
            return {
                'success': True,
                'montant_initial': montant_initial,
                'total_charges': total_charges,
                'montant_net': montant_net,
                'nombre_charges': charges_data['nombre_charges']
            }
            
        except Exception as e:
            ServiceChargesBailleurIntelligent._log_erreur(
                'integrer_charges_dans_recap',
                f'Erreur lors de l\'intégration des charges dans le récapitulatif {recap.id}: {str(e)}'
            )
            return {
                'success': False,
                'erreur': str(e)
            }
    
    @staticmethod
    def calculer_impact_charges_sur_paiements(bailleur: Bailleur, mois: date) -> Dict:
        """
        Calcule l'impact des charges bailleur sur les paiements mensuels.
        
        Args:
            bailleur: Instance du bailleur
            mois: Mois à analyser
            
        Returns:
            Dict contenant l'analyse d'impact
        """
        try:
            # Récupérer les propriétés actives du bailleur
            proprietes = Propriete.objects.filter(
                bailleur=bailleur,
                contrats__est_actif=True,
                contrats__est_resilie=False
            ).distinct()
            
            analyse_impact = {
                'bailleur': bailleur,
                'mois': mois,
                'proprietes_analysees': [],
                'total_loyers_bruts': Decimal('0'),
                'total_charges_bailleur': Decimal('0'),
                'total_charges_deductibles': Decimal('0'),
                'montant_net_final': Decimal('0'),
                'impact_par_propriete': {}
            }
            
            for propriete in proprietes:
                # Contrat actif de la propriété
                contrat = propriete.contrats.filter(
                    est_actif=True,
                    est_resilie=False
                ).first()
                
                if not contrat:
                    continue
                
                # Loyers bruts de la propriété
                loyer_mensuel = Decimal(str(contrat.loyer_mensuel or '0'))
                charges_mensuelles = Decimal(str(contrat.charges_mensuelles or '0'))
                loyer_brut = loyer_mensuel + charges_mensuelles
                
                # Charges déductibles (avancées par le locataire)
                charges_deductibles = ChargeDeductible.objects.filter(
                    contrat=contrat,
                    date_charge__year=mois.year,
                    date_charge__month=mois.month,
                    statut='validee'
                ).aggregate(total=Sum('montant'))['total'] or Decimal('0')
                
                # Charges bailleur (à déduire du retrait)
                charges_bailleur = ChargesBailleur.objects.filter(
                    propriete=propriete,
                    date_charge__year=mois.year,
                    date_charge__month=mois.month,
                    statut__in=['en_attente', 'deduite_retrait']
                ).aggregate(total=Sum('montant_restant'))['total'] or Decimal('0')
                
                # Calcul du montant net pour cette propriété
                montant_net_propriete = loyer_brut - charges_deductibles - charges_bailleur
                
                # Détails de la propriété
                propriete_detail = {
                    'propriete': propriete,
                    'contrat': contrat,
                    'loyer_brut': loyer_brut,
                    'charges_deductibles': charges_deductibles,
                    'charges_bailleur': charges_bailleur,
                    'montant_net': montant_net_propriete
                }
                
                analyse_impact['proprietes_analysees'].append(propriete_detail)
                analyse_impact['total_loyers_bruts'] += loyer_brut
                analyse_impact['total_charges_deductibles'] += charges_deductibles
                analyse_impact['total_charges_bailleur'] += charges_bailleur
                analyse_impact['impact_par_propriete'][propriete.id] = propriete_detail
            
            # Montant net final
            analyse_impact['montant_net_final'] = (
                analyse_impact['total_loyers_bruts'] - 
                analyse_impact['total_charges_deductibles'] - 
                analyse_impact['total_charges_bailleur']
            )
            
            return analyse_impact
            
        except Exception as e:
            ServiceChargesBailleurIntelligent._log_erreur(
                'calculer_impact_charges_sur_paiements',
                f'Erreur lors du calcul de l\'impact pour {bailleur} - {mois}: {str(e)}'
            )
            return {
                'erreur': str(e),
                'bailleur': bailleur,
                'mois': mois
            }
    
    @staticmethod
    def generer_rapport_charges_bailleur(bailleur: Bailleur, mois: date) -> Dict:
        """
        Génère un rapport détaillé des charges bailleur pour un mois donné.
        
        Args:
            bailleur: Instance du bailleur
            mois: Mois du rapport
            
        Returns:
            Dict contenant le rapport détaillé
        """
        try:
            # Calculer les charges
            charges_data = ServiceChargesBailleurIntelligent.calculer_charges_bailleur_pour_mois(
                bailleur, mois
            )
            
            # Calculer l'impact sur les paiements
            impact_data = ServiceChargesBailleurIntelligent.calculer_impact_charges_sur_paiements(
                bailleur, mois
            )
            
            # Statistiques par type de charge
            stats_par_type = {}
            for charge_detail in charges_data['charges_details']:
                charge = charge_detail['charge']
                type_charge = charge.type_charge
                if type_charge not in stats_par_type:
                    stats_par_type[type_charge] = {
                        'nombre': 0,
                        'montant_total': Decimal('0'),
                        'montant_deductible': Decimal('0')
                    }
                stats_par_type[type_charge]['nombre'] += 1
                stats_par_type[type_charge]['montant_total'] += charge.montant
                stats_par_type[type_charge]['montant_deductible'] += charge_detail['montant_deductible']
            
            # Statistiques par priorité
            stats_par_priorite = {}
            for charge_detail in charges_data['charges_details']:
                charge = charge_detail['charge']
                priorite = charge.priorite
                if priorite not in stats_par_priorite:
                    stats_par_priorite[priorite] = {
                        'nombre': 0,
                        'montant_total': Decimal('0'),
                        'montant_deductible': Decimal('0')
                    }
                stats_par_priorite[priorite]['nombre'] += 1
                stats_par_priorite[priorite]['montant_total'] += charge.montant
                stats_par_priorite[priorite]['montant_deductible'] += charge_detail['montant_deductible']
            
            return {
                'bailleur': bailleur,
                'mois': mois,
                'charges_data': charges_data,
                'impact_data': impact_data,
                'stats_par_type': stats_par_type,
                'stats_par_priorite': stats_par_priorite,
                'resume': {
                    'total_charges': charges_data['total_charges'],
                    'nombre_charges': charges_data['nombre_charges'],
                    'montant_net_final': impact_data.get('montant_net_final', Decimal('0')),
                    'impact_sur_retrait': charges_data['total_charges'],
                    'pourcentage_impact': (
                        (charges_data['total_charges'] / impact_data.get('total_loyers_bruts', Decimal('1'))) * 100
                        if impact_data.get('total_loyers_bruts', Decimal('0')) > 0 else 0
                    )
                }
            }
            
        except Exception as e:
            ServiceChargesBailleurIntelligent._log_erreur(
                'generer_rapport_charges_bailleur',
                f'Erreur lors de la génération du rapport pour {bailleur} - {mois}: {str(e)}'
            )
            return {
                'erreur': str(e),
                'bailleur': bailleur,
                'mois': mois
            }
    
    @staticmethod
    def generer_rapport_global_charges_bailleur(mois: date) -> Dict:
        """
        Génère un rapport global des charges bailleur pour tous les bailleurs d'un mois donné.
        
        Args:
            mois: Mois du rapport
            
        Returns:
            Dict contenant le rapport global
        """
        try:
            # Récupérer tous les bailleurs ayant des charges ce mois
            bailleurs_avec_charges = Bailleur.objects.filter(
                proprietes__charges_bailleur__date_charge__year=mois.year,
                proprietes__charges_bailleur__date_charge__month=mois.month
            ).distinct()
            
            rapport_global = {
                'mois': mois,
                'bailleurs_rapports': [],
                'totaux_globaux': {
                    'total_charges': Decimal('0'),
                    'nombre_charges': 0,
                    'nombre_bailleurs': 0,
                    'montant_moyen_par_bailleur': Decimal('0')
                },
                'stats_par_type': {},
                'stats_par_priorite': {}
            }
            
            # Générer le rapport pour chaque bailleur
            for bailleur in bailleurs_avec_charges:
                rapport_bailleur = ServiceChargesBailleurIntelligent.generer_rapport_charges_bailleur(
                    bailleur, mois
                )
                
                if not rapport_bailleur.get('erreur'):
                    rapport_global['bailleurs_rapports'].append(rapport_bailleur)
                    
                    # Ajouter aux totaux globaux
                    rapport_global['totaux_globaux']['total_charges'] += rapport_bailleur['resume']['total_charges']
                    rapport_global['totaux_globaux']['nombre_charges'] += rapport_bailleur['resume']['nombre_charges']
                    rapport_global['totaux_globaux']['nombre_bailleurs'] += 1
                    
                    # Agréger les statistiques par type
                    for type_charge, stats in rapport_bailleur.get('stats_par_type', {}).items():
                        if type_charge not in rapport_global['stats_par_type']:
                            rapport_global['stats_par_type'][type_charge] = {
                                'nombre': 0,
                                'montant_total': Decimal('0'),
                                'montant_deductible': Decimal('0')
                            }
                        rapport_global['stats_par_type'][type_charge]['nombre'] += stats['nombre']
                        rapport_global['stats_par_type'][type_charge]['montant_total'] += stats['montant_total']
                        rapport_global['stats_par_type'][type_charge]['montant_deductible'] += stats['montant_deductible']
                    
                    # Agréger les statistiques par priorité
                    for priorite, stats in rapport_bailleur.get('stats_par_priorite', {}).items():
                        if priorite not in rapport_global['stats_par_priorite']:
                            rapport_global['stats_par_priorite'][priorite] = {
                                'nombre': 0,
                                'montant_total': Decimal('0'),
                                'montant_deductible': Decimal('0')
                            }
                        rapport_global['stats_par_priorite'][priorite]['nombre'] += stats['nombre']
                        rapport_global['stats_par_priorite'][priorite]['montant_total'] += stats['montant_total']
                        rapport_global['stats_par_priorite'][priorite]['montant_deductible'] += stats['montant_deductible']
            
            # Calculer la moyenne par bailleur
            if rapport_global['totaux_globaux']['nombre_bailleurs'] > 0:
                rapport_global['totaux_globaux']['montant_moyen_par_bailleur'] = (
                    rapport_global['totaux_globaux']['total_charges'] / 
                    rapport_global['totaux_globaux']['nombre_bailleurs']
                )
            
            return rapport_global
            
        except Exception as e:
            ServiceChargesBailleurIntelligent._log_erreur(
                'generer_rapport_global_charges_bailleur',
                f'Erreur lors de la génération du rapport global pour {mois}: {str(e)}'
            )
            return {
                'erreur': str(e),
                'mois': mois
            }
    
    @staticmethod
    def _log_integration_retrait(retrait: RetraitBailleur, charges_deduites: List, total_charges: Decimal):
        """Crée un log d'intégration des charges dans un retrait."""
        try:
            from django.contrib.contenttypes.models import ContentType
            content_type = ContentType.objects.get_for_model(RetraitBailleur)
            AuditLog.objects.create(
                content_type=content_type,
                object_id=retrait.id,
                action='update',
                user=retrait.cree_par,
                details={
                    'description': f'Intégration automatique de {len(charges_deduites)} charges pour {total_charges} F CFA',
                    'nombre_charges': len(charges_deduites),
                    'total_charges': str(total_charges),
                    'montant_net': str(retrait.montant_retrait)
                }
            )
        except Exception:
            pass  # Ne pas faire échouer l'intégration pour un problème de log
    
    @staticmethod
    def _log_integration_recap(recap: RecapMensuel, charges_details: List, total_charges: Decimal):
        """Crée un log d'intégration des charges dans un récapitulatif."""
        try:
            from django.contrib.contenttypes.models import ContentType
            content_type = ContentType.objects.get_for_model(RecapMensuel)
            AuditLog.objects.create(
                content_type=content_type,
                object_id=recap.id,
                action='update',
                user=recap.cree_par,
                details={
                    'description': f'Intégration automatique de {len(charges_details)} charges pour {total_charges} F CFA',
                    'nombre_charges': len(charges_details),
                    'total_charges': str(total_charges),
                    'montant_net': str(recap.total_net_a_payer)
                }
            )
        except Exception:
            pass  # Ne pas faire échouer l'intégration pour un problème de log
    
    @staticmethod
    def _log_erreur(methode: str, message: str):
        """Crée un log d'erreur."""
        try:
            from django.contrib.contenttypes.models import ContentType
            # Utiliser un ContentType générique pour les erreurs de service
            content_type = ContentType.objects.get(app_label='core', model='auditlog')
            AuditLog.objects.create(
                content_type=content_type,
                object_id=0,
                action='update',
                user=None,
                details={
                    'description': f'Erreur dans {methode}: {message}',
                    'methode': methode,
                    'message': message
                }
            )
        except Exception:
            pass  # Ne pas faire échouer l'opération pour un problème de log
