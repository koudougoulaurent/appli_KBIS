"""
Services spécialisés pour la gestion des paiements et retraits avec les unités locatives
"""
from django.db.models import Sum, Q, Count
from django.utils import timezone
from decimal import Decimal
from datetime import datetime, date
from typing import Dict, List, Optional

from .models import Paiement, RetraitBailleur, ChargeDeductible
from contrats.models import Contrat
from proprietes.models import UniteLocative, Propriete, Bailleur


class ServiceUnitesLocativesFinancier:
    """Service pour gérer les calculs financiers spécifiques aux unités locatives."""
    
    @staticmethod
    def calculer_revenus_par_unite(bailleur: Bailleur, mois: date) -> Dict:
        """
        Calcule les revenus détaillés par unité locative pour un bailleur donné.
        
        Args:
            bailleur: Le bailleur concerné
            mois: Le mois pour lequel calculer les revenus
            
        Returns:
            Dict avec les détails par unité locative
        """
        debut_mois = mois.replace(day=1)
        if mois.month == 12:
            fin_mois = date(mois.year + 1, 1, 1)
        else:
            fin_mois = date(mois.year, mois.month + 1, 1)
        
        # Récupérer toutes les unités du bailleur avec contrats actifs
        unites_avec_contrats = UniteLocative.objects.filter(
            propriete__bailleur=bailleur,
            contrats__est_actif=True,
            contrats__est_resilie=False,
            is_deleted=False
        ).distinct()
        
        resultats = {
            'unites': [],
            'totaux': {
                'loyers_bruts': Decimal('0'),
                'charges_locataires': Decimal('0'),
                'charges_deductibles': Decimal('0'),
                'revenus_nets': Decimal('0'),
                'nombre_unites_occupees': 0,
                'nombre_unites_total': 0
            }
        }
        
        # Calculer pour chaque unité
        for unite in unites_avec_contrats:
            contrat_actif = unite.contrats.filter(
                est_actif=True, 
                est_resilie=False
            ).first()
            
            if not contrat_actif:
                continue
                
            # Paiements reçus pour cette unité ce mois
            paiements_unite = Paiement.objects.filter(
                contrat=contrat_actif,
                date_paiement__gte=debut_mois,
                date_paiement__lt=fin_mois,
                statut='valide',
                is_deleted=False
            )
            
            total_paiements = paiements_unite.aggregate(
                total=Sum('montant')
            )['total'] or Decimal('0')
            
            # Charges déductibles pour cette unité ce mois
            charges_deductibles = ChargeDeductible.objects.filter(
                contrat=contrat_actif,
                date_charge__gte=debut_mois,
                date_charge__lt=fin_mois,
                statut='validee',
                is_deleted=False
            ).aggregate(total=Sum('montant'))['total'] or Decimal('0')
            
            # Loyer mensuel théorique de l'unité
            loyer_theorique = unite.loyer_mensuel or Decimal('0')
            charges_theoriques = unite.charges_mensuelles or Decimal('0')
            
            # Calculs pour cette unité
            revenus_nets_unite = total_paiements - charges_deductibles
            
            unite_data = {
                'unite': unite,
                'contrat': contrat_actif,
                'locataire': contrat_actif.locataire,
                'loyer_theorique': loyer_theorique,
                'charges_theoriques': charges_theoriques,
                'paiements_recus': total_paiements,
                'charges_deductibles': charges_deductibles,
                'revenus_nets': revenus_nets_unite,
                'taux_paiement': (total_paiements / (loyer_theorique + charges_theoriques) * 100) if (loyer_theorique + charges_theoriques) > 0 else 0,
                'statut_paiement': 'Complet' if total_paiements >= (loyer_theorique + charges_theoriques) else 'Partiel' if total_paiements > 0 else 'Impayé'
            }
            
            resultats['unites'].append(unite_data)
            
            # Mise à jour des totaux
            resultats['totaux']['loyers_bruts'] += loyer_theorique
            resultats['totaux']['charges_locataires'] += charges_theoriques
            resultats['totaux']['charges_deductibles'] += charges_deductibles
            resultats['totaux']['revenus_nets'] += revenus_nets_unite
            resultats['totaux']['nombre_unites_occupees'] += 1
        
        # Nombre total d'unités du bailleur (occupées et libres)
        resultats['totaux']['nombre_unites_total'] = UniteLocative.objects.filter(
            propriete__bailleur=bailleur,
            is_deleted=False
        ).count()
        
        # Taux d'occupation
        if resultats['totaux']['nombre_unites_total'] > 0:
            resultats['totaux']['taux_occupation'] = (
                resultats['totaux']['nombre_unites_occupees'] / 
                resultats['totaux']['nombre_unites_total'] * 100
            )
        else:
            resultats['totaux']['taux_occupation'] = 0
            
        return resultats
    
    @staticmethod
    def calculer_retrait_avec_unites(bailleur: Bailleur, mois: date) -> Dict:
        """
        Calcule un retrait en tenant compte des détails par unité locative.
        
        Args:
            bailleur: Le bailleur concerné
            mois: Le mois pour lequel calculer le retrait
            
        Returns:
            Dict avec les calculs détaillés par unité
        """
        revenus_par_unite = ServiceUnitesLocativesFinancier.calculer_revenus_par_unite(
            bailleur, mois
        )
        
        # Charges du bailleur pour ce mois (non liées aux unités spécifiques)
        debut_mois = mois.replace(day=1)
        if mois.month == 12:
            fin_mois = date(mois.year + 1, 1, 1)
        else:
            fin_mois = date(mois.year, mois.month + 1, 1)
            
        # Charges du bailleur pour ce mois (utilisation du modèle existant)
        try:
            from proprietes.models import ChargesBailleur
            charges_bailleur = ChargesBailleur.objects.filter(
                propriete__bailleur=bailleur,
                date_charge__gte=debut_mois,
                date_charge__lt=fin_mois,
                statut__in=['en_attente', 'deduite_retrait']
            ).aggregate(total=Sum('montant_restant'))['total'] or Decimal('0')
        except ImportError:
            # Si le modèle n'existe pas encore, utiliser 0
            charges_bailleur = Decimal('0')
        
        # Si le modèle ChargesBailleur n'est pas disponible, utiliser les charges déductibles
        if charges_bailleur == Decimal('0'):
            charges_bailleur = ChargeDeductible.objects.filter(
                contrat__propriete__bailleur=bailleur,
                contrat__est_actif=True,
                date_charge__gte=debut_mois,
                date_charge__lt=fin_mois,
                statut='validee',
                is_deleted=False
            ).aggregate(total=Sum('montant'))['total'] or Decimal('0')
        
        # Calculs finaux
        total_revenus_bruts = revenus_par_unite['totaux']['revenus_nets']
        total_charges_bailleur = charges_bailleur
        montant_net_retrait = total_revenus_bruts - total_charges_bailleur
        
        return {
            'revenus_par_unite': revenus_par_unite,
            'charges_bailleur': charges_bailleur,
            'calculs_retrait': {
                'revenus_bruts_total': total_revenus_bruts,
                'charges_bailleur_total': total_charges_bailleur,
                'montant_net_retrait': montant_net_retrait,
                'nombre_unites_rentables': len([
                    u for u in revenus_par_unite['unites'] 
                    if u['revenus_nets'] > 0
                ]),
                'revenus_moyen_par_unite': (
                    total_revenus_bruts / len(revenus_par_unite['unites'])
                    if revenus_par_unite['unites'] else Decimal('0')
                )
            }
        }
    
    @staticmethod
    def generer_rapport_performance_unites(bailleur: Bailleur, periode_debut: date, periode_fin: date) -> Dict:
        """
        Génère un rapport de performance détaillé par unité locative.
        
        Args:
            bailleur: Le bailleur concerné
            periode_debut: Début de la période d'analyse
            periode_fin: Fin de la période d'analyse
            
        Returns:
            Dict avec l'analyse de performance par unité
        """
        unites = UniteLocative.objects.filter(
            propriete__bailleur=bailleur,
            is_deleted=False
        )
        
        rapport = {
            'periode': {
                'debut': periode_debut,
                'fin': periode_fin
            },
            'unites_performance': [],
            'statistiques_globales': {
                'nombre_unites_total': unites.count(),
                'nombre_unites_occupees': 0,
                'revenus_total': Decimal('0'),
                'charges_total': Decimal('0'),
                'benefice_net': Decimal('0')
            }
        }
        
        for unite in unites:
            # Contrats pendant la période
            contrats_periode = unite.contrats.filter(
                Q(date_debut__lte=periode_fin) &
                (Q(date_fin__gte=periode_debut) | Q(date_fin__isnull=True)),
                is_deleted=False
            )
            
            if not contrats_periode.exists():
                continue
                
            # Paiements pendant la période
            paiements_periode = Paiement.objects.filter(
                contrat__in=contrats_periode,
                date_paiement__range=[periode_debut, periode_fin],
                statut='valide',
                is_deleted=False
            )
            
            total_paiements = paiements_periode.aggregate(
                total=Sum('montant')
            )['total'] or Decimal('0')
            
            # Charges déductibles pendant la période
            charges_periode = ChargeDeductible.objects.filter(
                contrat__in=contrats_periode,
                date_charge__range=[periode_debut, periode_fin],
                statut='validee',
                is_deleted=False
            ).aggregate(total=Sum('montant'))['total'] or Decimal('0')
            
            # Calcul de la rentabilité
            revenus_nets = total_paiements - charges_periode
            loyer_theorique_periode = (unite.loyer_mensuel or Decimal('0')) * (
                (periode_fin - periode_debut).days / 30  # Approximation mensuelle
            )
            
            unite_performance = {
                'unite': unite,
                'revenus_bruts': total_paiements,
                'charges_deductibles': charges_periode,
                'revenus_nets': revenus_nets,
                'loyer_theorique': loyer_theorique_periode,
                'taux_occupation': (total_paiements / loyer_theorique_periode * 100) if loyer_theorique_periode > 0 else 0,
                'rentabilite': 'Excellente' if revenus_nets > loyer_theorique_periode * Decimal('0.9') else
                              'Bonne' if revenus_nets > loyer_theorique_periode * Decimal('0.7') else
                              'Moyenne' if revenus_nets > 0 else 'Déficitaire',
                'nombre_contrats': contrats_periode.count(),
                'nombre_paiements': paiements_periode.count()
            }
            
            rapport['unites_performance'].append(unite_performance)
            
            # Mise à jour des statistiques globales
            if contrats_periode.filter(est_actif=True).exists():
                rapport['statistiques_globales']['nombre_unites_occupees'] += 1
            rapport['statistiques_globales']['revenus_total'] += total_paiements
            rapport['statistiques_globales']['charges_total'] += charges_periode
            rapport['statistiques_globales']['benefice_net'] += revenus_nets
        
        # Calculs des moyennes
        nb_unites = len(rapport['unites_performance'])
        if nb_unites > 0:
            rapport['statistiques_globales']['revenus_moyen_par_unite'] = (
                rapport['statistiques_globales']['revenus_total'] / nb_unites
            )
            rapport['statistiques_globales']['taux_occupation_global'] = (
                rapport['statistiques_globales']['nombre_unites_occupees'] / 
                rapport['statistiques_globales']['nombre_unites_total'] * 100
            )
        
        return rapport


class ServiceStatistiquesUnites:
    """Service pour les statistiques spécialisées des unités locatives."""
    
    @staticmethod
    def get_unites_les_plus_rentables(bailleur: Bailleur, limite: int = 10) -> List[Dict]:
        """Retourne les unités les plus rentables du bailleur."""
        # Implémentation des statistiques de rentabilité
        pass
    
    @staticmethod
    def get_unites_problematiques(bailleur: Bailleur) -> List[Dict]:
        """Retourne les unités avec des problèmes de paiement."""
        # Implémentation de la détection des unités problématiques
        pass
    
    @staticmethod
    def calculer_previsions_revenus(bailleur: Bailleur, mois_futurs: int = 12) -> Dict:
        """Calcule les prévisions de revenus basées sur les unités actuelles."""
        # Implémentation des prévisions
        pass
