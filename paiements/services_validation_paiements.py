"""
Service de validation intelligent pour les paiements
Système non-bloquant avec validations fortes pour :
1. Empêcher les doublons de paiement pour le même mois
2. Valider la chronologie des paiements (n+1)
3. Intégrer les avances de loyer dans la logique
"""

from django.db import transaction
from django.utils import timezone
from decimal import Decimal
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from paiements.models import Paiement
from paiements.models_avance import AvanceLoyer
from contrats.models import Contrat
from typing import Dict, List, Optional, Tuple


class ServiceValidationPaiements:
    """Service de validation intelligent pour les paiements."""
    
    @staticmethod
    def valider_paiement_intelligent(contrat, montant, date_paiement=None, type_paiement='loyer'):
        """
        Valide un paiement de manière intelligente et non-bloquante.
        
        RÈGLES DE VALIDATION :
        1. Pas de doublon pour le même mois dans la même année
        2. Paiement seulement pour le mois n+1 (n = dernier mois payé)
        3. Prise en compte des avances de loyer
        4. Validation non-bloquante (avertissements, pas d'erreurs)
        
        Args:
            contrat: Contrat concerné
            montant: Montant du paiement
            date_paiement: Date du paiement (optionnel)
            type_paiement: Type de paiement ('loyer', 'avance', etc.)
        
        Returns:
            dict: {
                'valide': bool,
                'avertissements': List[str],
                'suggestions': List[str],
                'mois_suggere': Optional[date],
                'details': Dict
            }
        """
        if not contrat or not montant:
            return {
                'valide': False,
                'avertissements': ['Contrat ou montant manquant'],
                'suggestions': [],
                'mois_suggere': None,
                'details': {}
            }
        
        date_paiement = date_paiement or timezone.now().date()
        resultat = {
            'valide': True,
            'avertissements': [],
            'suggestions': [],
            'mois_suggere': None,
            'details': {}
        }
        
        # 1. ANALYSER LES PAIEMENTS EXISTANTS
        analyse_paiements = ServiceValidationPaiements._analyser_paiements_existants(contrat)
        resultat['details']['analyse_paiements'] = analyse_paiements
        
        # 2. DÉTERMINER LE MOIS SUGGÉRÉ
        mois_suggere = ServiceValidationPaiements._determiner_mois_suggere(contrat, date_paiement)
        resultat['mois_suggere'] = mois_suggere
        
        # 3. VALIDER CONTRE LES DOUBLONS
        validation_doublons = ServiceValidationPaiements._valider_contre_doublons(
            contrat, date_paiement, analyse_paiements
        )
        if not validation_doublons['valide']:
            resultat['valide'] = False
            resultat['avertissements'].extend(validation_doublons['avertissements'])
        
        # 4. VALIDER LA CHRONOLOGIE
        validation_chronologie = ServiceValidationPaiements._valider_chronologie(
            contrat, date_paiement, analyse_paiements
        )
        if not validation_chronologie['valide']:
            resultat['valide'] = False
            resultat['avertissements'].extend(validation_chronologie['avertissements'])
        
        # 5. INTÉGRER LES AVANCES DE LOYER
        validation_avances = ServiceValidationPaiements._valider_avec_avances(
            contrat, montant, date_paiement, analyse_paiements
        )
        if not validation_avances['valide']:
            resultat['valide'] = False
            resultat['avertissements'].extend(validation_avances['avertissements'])
        
        # 6. GÉNÉRER DES SUGGESTIONS
        resultat['suggestions'] = ServiceValidationPaiements._generer_suggestions(
            contrat, date_paiement, analyse_paiements, mois_suggere
        )
        
        return resultat
    
    @staticmethod
    def _analyser_paiements_existants(contrat):
        """Analyse les paiements existants pour un contrat."""
        paiements = Paiement.objects.filter(
            contrat=contrat,
            type_paiement='loyer',
            statut='valide'
        ).order_by('date_paiement')
        
        # Grouper par mois/année
        paiements_par_mois = {}
        for paiement in paiements:
            mois_cle = paiement.date_paiement.replace(day=1)
            if mois_cle not in paiements_par_mois:
                paiements_par_mois[mois_cle] = []
            paiements_par_mois[mois_cle].append(paiement)
        
        # Analyser les avances
        avances = AvanceLoyer.objects.filter(contrat=contrat, statut='valide')
        
        return {
            'paiements': list(paiements),
            'paiements_par_mois': paiements_par_mois,
            'dernier_paiement': paiements.last() if paiements else None,
            'avances': list(avances),
            'mois_payes': list(paiements_par_mois.keys())
        }
    
    @staticmethod
    def _determiner_mois_suggere(contrat, date_paiement):
        """
        Détermine le mois suggéré pour le paiement.
        CORRIGÉ : Utilise maintenant la méthode calculer_prochain_mois_paiement() qui prend en compte mois_paye
        """
        try:
            # Utiliser la méthode corrigée qui prend en compte mois_paye et les avances
            from .services_avance import ServiceGestionAvance
            prochain_mois = ServiceGestionAvance.calculer_prochain_mois_paiement(contrat)
            return prochain_mois
        except Exception as e:
            # Fallback : utiliser l'ancienne logique si erreur
            analyse = ServiceValidationPaiements._analyser_paiements_existants(contrat)
            
            if not analyse['dernier_paiement']:
                # Premier paiement : mois de début du contrat
                if hasattr(contrat, 'date_debut') and contrat.date_debut:
                    return contrat.date_debut.replace(day=1)
                elif hasattr(contrat, 'date_entree') and contrat.date_entree:
                    return contrat.date_entree.replace(day=1)
                else:
                    return date_paiement.replace(day=1)
            
            # Dernier mois payé + 1 (utiliser mois_paye si disponible)
            dernier_paiement = analyse['dernier_paiement']
            if dernier_paiement.mois_paye:
                # Convertir mois_paye en date
                from datetime import datetime
                import re
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
                
                mois_paye_lower = dernier_paiement.mois_paye.lower().strip()
                dernier_mois_paye = None
                for mois, num in {**mois_francais, **mois_anglais}.items():
                    if mois in mois_paye_lower:
                        annee_match = re.search(r'(\d{4})', dernier_paiement.mois_paye)
                        if annee_match:
                            annee = int(annee_match.group(1))
                            dernier_mois_paye = date(annee, num, 1)
                            break
                
                if not dernier_mois_paye:
                    dernier_mois_paye = dernier_paiement.date_paiement.replace(day=1)
            else:
                dernier_mois_paye = dernier_paiement.date_paiement.replace(day=1)
            
            mois_suggere = dernier_mois_paye + relativedelta(months=1)
            
            # Vérifier si le mois suggéré n'est pas déjà payé
            if mois_suggere in analyse['mois_payes']:
                # Trouver le prochain mois disponible
                mois_courant = mois_suggere
                while mois_courant in analyse['mois_payes']:
                    mois_courant += relativedelta(months=1)
                return mois_courant
            
            return mois_suggere
    
    @staticmethod
    def _valider_contre_doublons(contrat, date_paiement, analyse_paiements):
        """Valide contre les doublons de paiement."""
        mois_paiement = date_paiement.replace(day=1)
        annee_paiement = date_paiement.year
        
        # Vérifier si ce mois est déjà payé
        if mois_paiement in analyse_paiements['mois_payes']:
            paiements_mois = analyse_paiements['paiements_par_mois'][mois_paiement]
            return {
                'valide': False,
                'avertissements': [
                    f"⚠️ DOUBLON DÉTECTÉ : Le mois {mois_paiement.strftime('%B %Y')} est déjà payé",
                    f"Paiements existants : {len(paiements_mois)} paiement(s)",
                    f"Montants : {[str(p.montant) for p in paiements_mois]}"
                ]
            }
        
        return {'valide': True, 'avertissements': []}
    
    @staticmethod
    def _valider_chronologie(contrat, date_paiement, analyse_paiements):
        """Valide la chronologie des paiements (n+1)."""
        if not analyse_paiements['dernier_paiement']:
            return {'valide': True, 'avertissements': []}
        
        dernier_mois_paye = analyse_paiements['dernier_paiement'].date_paiement.replace(day=1)
        mois_paiement = date_paiement.replace(day=1)
        
        # Calculer le mois n+1 attendu
        mois_attendu = dernier_mois_paye + relativedelta(months=1)
        
        if mois_paiement < mois_attendu:
            return {
                'valide': False,
                'avertissements': [
                    f"⚠️ CHRONOLOGIE INCORRECTE : Vous tentez de payer pour {mois_paiement.strftime('%B %Y')}",
                    f"Mais le dernier mois payé est {dernier_mois_paye.strftime('%B %Y')}",
                    f"Le prochain mois à payer devrait être {mois_attendu.strftime('%B %Y')}"
                ]
            }
        
        return {'valide': True, 'avertissements': []}
    
    @staticmethod
    def _valider_avec_avances(contrat, montant, date_paiement, analyse_paiements):
        """
        Valide en tenant compte des avances de loyer.
        CORRIGÉ : Utilise le système centralisé AvanceLoyer au lieu de recalculer.
        """
        if not analyse_paiements['avances']:
            return {'valide': True, 'avertissements': []}
        
        # CORRECTION MAJEURE : Utiliser le système d'avances centralisé (AvanceLoyer)
        # au lieu de recalculer manuellement à partir des objets Paiement
        from .services_avance import ServiceGestionAvance
        from .models_avance import AvanceLoyer
        
        # Vérifier si le paiement est couvert par une avance
        mois_paiement = date_paiement.replace(day=1)
        
        # Vérifier directement dans le système AvanceLoyer
        if ServiceGestionAvance.verifier_mois_couvert_par_avance(contrat, mois_paiement):
            # Récupérer l'avance qui couvre ce mois pour afficher les détails
            avance_couvrant = AvanceLoyer.objects.filter(
                contrat=contrat,
                statut='active',
                montant_restant__gt=0,
                mois_debut_couverture__lte=mois_paiement,
                mois_fin_couverture__gte=mois_paiement
            ).first()
            
            if avance_couvrant:
                return {
                    'valide': False,
                    'avertissements': [
                        f"⚠️ AVANCE ACTIVE : Le mois {mois_paiement.strftime('%B %Y')} est couvert par une avance",
                        f"Avance de {avance_couvrant.montant_avance} F CFA couvre {avance_couvrant.nombre_mois_couverts} mois",
                        f"Période couverte : {avance_couvrant.mois_debut_couverture.strftime('%B %Y')} à {avance_couvrant.mois_fin_couverture.strftime('%B %Y')}",
                        f"Montant restant : {avance_couvrant.montant_restant} F CFA"
                    ]
                }
        
        return {'valide': True, 'avertissements': []}
    
    @staticmethod
    def _generer_suggestions(contrat, date_paiement, analyse_paiements, mois_suggere):
        """Génère des suggestions intelligentes."""
        suggestions = []
        
        if not analyse_paiements['dernier_paiement']:
            suggestions.append("💡 Premier paiement : Vérifiez que la date correspond au début du contrat")
            return suggestions
        
        # Suggestion de mois
        if mois_suggere:
            suggestions.append(f"💡 Mois suggéré : {mois_suggere.strftime('%B %Y')}")
        
        # Suggestion sur les avances
        if analyse_paiements['avances']:
            suggestions.append("💡 Avances détectées : Vérifiez que le paiement n'est pas déjà couvert")
        
        # Suggestion sur les montants
        if contrat.loyer_mensuel:
            loyer_attendu = float(contrat.loyer_mensuel)
            montant_paiement = float(date_paiement) if hasattr(date_paiement, '__float__') else 0
            
            if montant_paiement > 0 and abs(montant_paiement - loyer_attendu) > 0.01:
                suggestions.append(f"💡 Montant suggéré : {loyer_attendu} F CFA (loyer mensuel)")
        
        return suggestions
    
    @staticmethod
    def obtenir_statut_paiements_contrat(contrat):
        """Obtient le statut complet des paiements pour un contrat."""
        analyse = ServiceValidationPaiements._analyser_paiements_existants(contrat)
        
        # Calculer les mois couverts par les avances
        # CORRECTION V10.2: Utiliser ServiceLogiqueAvanceUnique (Option A)
        mois_couverts_avances = set()
        for avance in analyse['avances']:
            if avance.montant > 0:
                from paiements.services_logique_avance_unique import ServiceLogiqueAvanceUnique
                
                # Utiliser la logique Option A (dettes prioritaires)
                mois_debut = ServiceLogiqueAvanceUnique.determiner_mois_debut_couverture_nouvelle_avance(
                    contrat, avance.date_avance
                )
                
                nombre_mois = ServiceLogiqueAvanceUnique.calculer_nombre_mois_couverts(
                    avance.montant,
                    contrat.loyer_mensuel
                )
                
                mois_fin = ServiceLogiqueAvanceUnique.calculer_mois_fin_couverture(
                    mois_debut,
                    nombre_mois
                )
                
                # Ajouter tous les mois couverts
                mois_courant = mois_debut
                while mois_courant <= mois_fin:
                    mois_couverts_avances.add(mois_courant)
                    mois_courant += relativedelta(months=1)
        
        return {
            'contrat': contrat,
            'dernier_paiement': analyse['dernier_paiement'],
            'mois_payes': analyse['mois_payes'],
            'mois_couverts_avances': list(mois_couverts_avances),
            'prochain_mois_a_payer': ServiceValidationPaiements._determiner_mois_suggere(
                contrat, timezone.now().date()
            ),
            'avances_actives': analyse['avances']
        }
