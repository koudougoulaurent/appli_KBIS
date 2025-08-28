from django.db.models import Q, Sum, Count, F, Case, When, DecimalField, Max, Min
from django.db.models.functions import Coalesce, ExtractMonth, ExtractYear
from django.utils import timezone
from datetime import datetime, timedelta, date
from decimal import Decimal
import json

from .models import Paiement, ChargeDeductible, QuittancePaiement
from contrats.models import Contrat
from proprietes.models import Propriete, Locataire, Bailleur


class ServiceContexteIntelligent:
    """
    Service intelligent qui récupère automatiquement toutes les informations contextuelles
    d'un contrat pour faciliter la saisie des paiements.
    """
    
    @staticmethod
    def get_contexte_complet_contrat(contrat_id):
        """
        Récupère TOUTES les informations contextuelles d'un contrat en une seule requête.
        """
        try:
            contrat = Contrat.objects.select_related(
                'propriete', 'locataire', 'propriete__bailleur'
            ).prefetch_related(
                'paiements', 'charges_deductibles'
            ).get(id=contrat_id)
            
            # Informations de base du contrat
            contexte_contrat = {
                'contrat': {
                    'id': contrat.id,
                    'numero_contrat': contrat.numero_contrat,
                    'date_debut': contrat.date_debut.strftime('%Y-%m-%d') if contrat.date_debut else None,
                    'date_fin': contrat.date_fin.strftime('%Y-%m-%d') if contrat.date_fin else None,
                    'loyer_mensuel': str(contrat.loyer_mensuel) if contrat.loyer_mensuel else '0',
                    'charges_mensuelles': str(contrat.charges_mensuelles) if contrat.charges_mensuelles else '0',
                    'depot_garantie': str(contrat.depot_garantie) if contrat.depot_garantie else '0',
                    'avance_loyer': str(contrat.avance_loyer) if contrat.avance_loyer else '0',
                    'jour_paiement': contrat.jour_paiement,
                    'mode_paiement': contrat.get_mode_paiement_display() if hasattr(contrat, 'get_mode_paiement_display') else 'Non défini',
                    'est_actif': contrat.est_actif,
                    'est_resilie': contrat.est_resilie,
                },
                
                'propriete': {
                    'id': contrat.propriete.id,
                    'titre': contrat.propriete.titre if hasattr(contrat.propriete, 'titre') else 'Non défini',
                    'adresse': contrat.propriete.adresse if hasattr(contrat.propriete, 'adresse') else 'Non définie',
                    'ville': contrat.propriete.ville if hasattr(contrat.propriete, 'ville') else 'Non définie',
                    'code_postal': contrat.propriete.code_postal if hasattr(contrat.propriete, 'code_postal') else 'Non défini',
                    'type_propriete': contrat.propriete.get_type_propriete_display() if hasattr(contrat.propriete, 'get_type_propriete_display') else 'Non défini',
                    'surface': contrat.propriete.surface if hasattr(contrat.propriete, 'surface') else '0',
                    'nombre_pieces': contrat.propriete.nombre_pieces if hasattr(contrat.propriete, 'nombre_pieces') else '0',
                },
                
                'locataire': {
                    'id': contrat.locataire.id,
                    'nom': contrat.locataire.nom,
                    'prenom': contrat.locataire.prenom,
                    'telephone': contrat.locataire.telephone,
                    'email': contrat.locataire.email,
                    'date_naissance': contrat.locataire.date_naissance,
                    'profession': contrat.locataire.profession,
                },
                
                'bailleur': {
                    'id': contrat.propriete.bailleur.id,
                    'nom': contrat.propriete.bailleur.nom,
                    'prenom': contrat.propriete.bailleur.prenom,
                    'telephone': contrat.propriete.bailleur.telephone,
                    'email': contrat.propriete.bailleur.email,
                }
            }
            
            # Historique des paiements (5 derniers mois)
            contexte_contrat['historique_paiements'] = ServiceContexteIntelligent._get_historique_paiements(contrat)
            
            # Statut des charges et déductions
            contexte_contrat['charges_deductibles'] = ServiceContexteIntelligent._get_charges_deductibles(contrat)
            
            # Calculs automatiques
            contexte_contrat['calculs_automatiques'] = ServiceContexteIntelligent._get_calculs_automatiques(contrat)
            
            # Alertes et notifications
            contexte_contrat['alertes'] = ServiceContexteIntelligent._get_alertes(contrat)
            
            return {
                'success': True,
                'data': contexte_contrat
            }
            
        except Contrat.DoesNotExist:
            return {
                'success': False,
                'error': 'Contrat non trouvé'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Erreur lors de la récupération du contexte: {str(e)}'
            }
    
    @staticmethod
    def _get_historique_paiements(contrat):
        """
        Récupère l'historique des paiements des 5 derniers mois.
        """
        date_limite = timezone.now().date() - timedelta(days=150)  # 5 mois
        
        paiements = Paiement.objects.filter(
            contrat=contrat,
            is_deleted=False,
            date_paiement__gte=date_limite
        ).order_by('-date_paiement')
        
        historique = []
        for i in range(5):
            date_mois = timezone.now().date() - timedelta(days=30*i)
            mois = date_mois.month
            annee = date_mois.year
            
            paiements_mois = paiements.filter(
                date_paiement__month=mois,
                date_paiement__year=annee
            )
            
            total_mois = paiements_mois.aggregate(
                total=Coalesce(Sum('montant'), Decimal('0.00'))
            )['total']
            
            nombre_paiements = paiements_mois.count()
            
            historique.append({
                'mois': date_mois.strftime('%B %Y'),
                'total_paiements': total_mois,
                'nombre_paiements': nombre_paiements,
                'paiements': list(paiements_mois.values(
                    'id', 'montant', 'date_paiement', 'statut', 'type_paiement'
                )),
                'statut_mois': 'Complet' if total_mois >= Decimal(contrat.loyer_mensuel or '0') else 'Incomplet'
            })
        
        return historique
    
    @staticmethod
    def _get_charges_deductibles(contrat):
        """
        Récupère le statut des charges déductibles.
        """
        charges = ChargeDeductible.objects.filter(
            contrat=contrat,
            is_deleted=False
        ).order_by('-date_creation')
        
        total_charges = charges.aggregate(
            total=Coalesce(Sum('montant'), Decimal('0.00'))
        )['total']
        
        charges_en_attente = charges.filter(statut='en_attente').aggregate(
            total=Coalesce(Sum('montant'), Decimal('0.00'))
        )['total']
        
        charges_validees = charges.filter(statut='validee').aggregate(
            total=Coalesce(Sum('montant'), Decimal('0.00'))
        )['total']
        
        return {
            'total_charges': total_charges,
            'charges_en_attente': charges_en_attente,
            'charges_validees': charges_validees,
            'charges_recentes': list(charges[:5].values(
                'id', 'montant', 'libelle', 'type_charge', 'statut', 'date_charge'
            )),
            'nombre_charges': charges.count()
        }
    
    @staticmethod
    def _get_calculs_automatiques(contrat):
        """
        Effectue tous les calculs automatiques nécessaires.
        """
        # Calcul du solde actuel
        total_paiements = Paiement.objects.filter(
            contrat=contrat,
            is_deleted=False,
            statut='valide'
        ).aggregate(
            total=Coalesce(Sum('montant'), Decimal('0.00'))
        )['total']
        
        # Calcul des charges déductibles validées
        total_charges_validees = ChargeDeductible.objects.filter(
            contrat=contrat,
            is_deleted=False,
            statut='validee'
        ).aggregate(
            total=Coalesce(Sum('montant'), Decimal('0.00'))
        )['total']
        
        # Calcul du loyer net
        loyer_mensuel = Decimal(contrat.loyer_mensuel or '0')
        charges_mensuelles = Decimal(contrat.charges_mensuelles or '0')
        loyer_net = loyer_mensuel - charges_mensuelles
        
        # Calcul du solde
        solde_actuel = total_paiements - total_charges_validees
        
        # Prochaine échéance
        aujourd_hui = timezone.now().date()
        jour_paiement = contrat.jour_paiement
        
        if aujourd_hui.day > jour_paiement:
            # Prochaine échéance le mois prochain
            if aujourd_hui.month == 12:
                prochaine_echeance = date(aujourd_hui.year + 1, 1, jour_paiement)
            else:
                prochaine_echeance = date(aujourd_hui.year, aujourd_hui.month + 1, jour_paiement)
        else:
            # Échéance ce mois
            prochaine_echeance = date(aujourd_hui.year, aujourd_hui.month, jour_paiement)
        
        jours_avant_echeance = (prochaine_echeance - aujourd_hui).days
        
        return {
            'solde_actuel': solde_actuel,
            'total_paiements': total_paiements,
            'total_charges_validees': total_charges_validees,
            'loyer_net': loyer_net,
            'prochaine_echeance': prochaine_echeance,
            'jours_avant_echeance': jours_avant_echeance,
            'statut_solde': 'Positif' if solde_actuel >= 0 else 'Négatif',
            'montant_du': max(Decimal('0'), -solde_actuel) if solde_actuel < 0 else Decimal('0')
        }
    
    @staticmethod
    def _get_alertes(contrat):
        """
        Génère des alertes automatiques basées sur le contexte.
        """
        alertes = []
        aujourd_hui = timezone.now().date()
        
        # Alerte échéance proche
        calculs = ServiceContexteIntelligent._get_calculs_automatiques(contrat)
        if calculs['jours_avant_echeance'] <= 7:
            alertes.append({
                'type': 'echeance',
                'niveau': 'warning' if calculs['jours_avant_echeance'] <= 3 else 'info',
                'message': f'Échéance de paiement dans {calculs["jours_avant_echeance"]} jour(s)',
                'date': calculs['prochaine_echeance']
            })
        
        # Alerte solde négatif
        if calculs['solde_actuel'] < 0:
            alertes.append({
                'type': 'solde',
                'niveau': 'danger',
                'message': f'Solde négatif: {calculs["montant_du"]} FCfa dus',
                'montant': calculs['montant_du']
            })
        
        # Alerte charges en attente
        charges = ServiceContexteIntelligent._get_charges_deductibles(contrat)
        if charges['charges_en_attente'] > 0:
            alertes.append({
                'type': 'charges',
                'niveau': 'warning',
                'message': f'{charges["charges_en_attente"]} FCfa de charges en attente de validation',
                'montant': charges['charges_en_attente']
            })
        
        # Alerte contrat expirant
        if contrat.date_fin:
            jours_avant_expiration = (contrat.date_fin - aujourd_hui).days
            if jours_avant_expiration <= 30:
                alertes.append({
                    'type': 'expiration',
                    'niveau': 'warning' if jours_avant_expiration <= 15 else 'info',
                    'message': f'Contrat expire dans {jours_avant_expiration} jour(s)',
                    'date': contrat.date_fin
                })
        
        return alertes
    
    @staticmethod
    def get_suggestions_paiement(contrat_id):
        """
        Génère des suggestions intelligentes pour le paiement.
        """
        contexte = ServiceContexteIntelligent.get_contexte_complet_contrat(contrat_id)
        
        if not contexte['success']:
            return contexte
        
        data = contexte['data']
        calculs = data['calculs_automatiques']
        
        suggestions = []
        
        # Suggestion de montant basé sur le solde
        if calculs['montant_du'] > 0:
            suggestions.append({
                'type': 'reglement_solde',
                'montant': calculs['montant_du'],
                'libelle': 'Règlement du solde négatif',
                'priorite': 'haute'
            })
        
        # Suggestion de paiement du loyer
        suggestions.append({
            'type': 'loyer_mensuel',
            'montant': data['contrat']['loyer_mensuel'],
            'libelle': 'Paiement du loyer mensuel',
            'priorite': 'normale'
        })
        
        # Suggestion de charges si applicable
        if data['charges_deductibles']['charges_en_attente'] > 0:
            suggestions.append({
                'type': 'charges',
                'montant': data['charges_deductibles']['charges_en_attente'],
                'libelle': 'Validation des charges en attente',
                'priorite': 'normale'
            })
        
        return {
            'success': True,
            'suggestions': suggestions
        }
