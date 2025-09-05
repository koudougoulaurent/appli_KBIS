from django.db.models import Q, Sum, Count, F, Case, When, DecimalField, Max, Min
from django.db.models.functions import Coalesce, ExtractMonth, ExtractYear
from django.utils import timezone
from datetime import datetime, timedelta, date
from decimal import Decimal
import json

from .models import RetraitBailleur, Paiement, ChargeDeductible
from contrats.models import Contrat
from proprietes.models import Propriete, Locataire, Bailleur, ChargesBailleur


class ServiceContexteIntelligentRetraits:
    """
    Service intelligent qui récupère automatiquement toutes les informations contextuelles
    d'un bailleur pour faciliter la création des retraits.
    """
    
    @staticmethod
    def get_contexte_complet_bailleur(bailleur_id):
        """
        Récupère TOUTES les informations contextuelles d'un bailleur en une seule requête.
        """
        try:
            bailleur = Bailleur.objects.select_related().get(id=bailleur_id)
        except Bailleur.DoesNotExist:
            return {
                'success': False,
                'error': 'Bailleur non trouvé'
            }
        
        try:
            # Récupération des informations de base
            contexte = {
                'bailleur': ServiceContexteIntelligentRetraits._get_infos_bailleur(bailleur),
                'proprietes': ServiceContexteIntelligentRetraits._get_proprietes_bailleur(bailleur),
                'contrats_actifs': ServiceContexteIntelligentRetraits._get_contrats_actifs(bailleur),
                'paiements_recents': ServiceContexteIntelligentRetraits._get_paiements_recents(bailleur),
                'charges_deductibles': ServiceContexteIntelligentRetraits._get_charges_deductibles(bailleur),
                'charges_bailleur': ServiceContexteIntelligentRetraits._get_charges_bailleur(bailleur),
                'retraits_recents': ServiceContexteIntelligentRetraits._get_retraits_recents(bailleur),
                'calculs_automatiques': ServiceContexteIntelligentRetraits._get_calculs_automatiques(bailleur),
                'alertes': ServiceContexteIntelligentRetraits._get_alertes(bailleur),
                'suggestions': ServiceContexteIntelligentRetraits._get_suggestions_retrait(bailleur)
            }
            
            return {
                'success': True,
                'data': contexte
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Erreur lors de la récupération du contexte: {str(e)}'
            }
    
    @staticmethod
    def _get_infos_bailleur(bailleur):
        """Récupère les informations de base du bailleur."""
        return {
            'id': bailleur.id,
            'nom': bailleur.nom,
            'prenom': bailleur.prenom,
            'email': bailleur.email,
            'telephone': bailleur.telephone,
            'adresse': bailleur.adresse,
            'code_bailleur': bailleur.code_bailleur,
            'actif': bailleur.actif,
            'date_creation': bailleur.date_creation.isoformat() if bailleur.date_creation else None,
            'get_nom_complet': bailleur.get_nom_complet()
        }
    
    @staticmethod
    def _get_proprietes_bailleur(bailleur):
        """Récupère les propriétés du bailleur avec statistiques."""
        proprietes = Propriete.objects.filter(
            bailleur=bailleur,
            is_deleted=False
        ).select_related('bailleur')
        
        proprietes_data = []
        total_surface = 0
        total_pieces = 0
        
        for propriete in proprietes:
            # Contrats actifs pour cette propriété
            contrats_actifs = propriete.contrats.filter(est_actif=True, is_deleted=False)
            loyer_mensuel = sum(float(contrat.loyer_mensuel or 0) for contrat in contrats_actifs)
            
            propriete_info = {
                'id': propriete.id,
                'adresse': propriete.adresse,
                'ville': propriete.ville,
                'code_postal': propriete.code_postal,
                'type_propriete': propriete.type_bien.nom if propriete.type_bien else 'Non défini',
                'surface': propriete.surface,
                'nombre_pieces': propriete.nombre_pieces,
                'loyer_mensuel': loyer_mensuel,
                'contrats_actifs': contrats_actifs.count(),
                'statut': propriete.etat
            }
            
            proprietes_data.append(propriete_info)
            total_surface += float(propriete.surface or 0)
            total_pieces += int(propriete.nombre_pieces or 0)
        
        return {
            'proprietes': proprietes_data,
            'total_proprietes': len(proprietes_data),
            'total_surface': total_surface,
            'total_pieces': total_pieces,
            'total_loyer_mensuel': sum(p['loyer_mensuel'] for p in proprietes_data)
        }
    
    @staticmethod
    def _get_contrats_actifs(bailleur):
        """Récupère les contrats actifs du bailleur."""
        contrats = Contrat.objects.filter(
            propriete__bailleur=bailleur,
            est_actif=True,
            is_deleted=False
        ).select_related('propriete', 'locataire')
        
        contrats_data = []
        total_loyer_mensuel = 0
        
        for contrat in contrats:
            contrat_info = {
                'id': contrat.id,
                'numero_contrat': contrat.numero_contrat,
                'propriete_adresse': contrat.propriete.adresse,
                'locataire_nom': contrat.locataire.get_nom_complet(),
                'loyer_mensuel': contrat.loyer_mensuel,
                'charges_mensuelles': contrat.charges_mensuelles,
                'date_debut': contrat.date_debut.isoformat() if contrat.date_debut else None,
                'date_fin': contrat.date_fin.isoformat() if contrat.date_fin else None,
                'jour_paiement': contrat.jour_paiement,
                'est_actif': contrat.est_actif
            }
            
            contrats_data.append(contrat_info)
            total_loyer_mensuel += float(contrat.loyer_mensuel or 0)
        
        return {
            'contrats': contrats_data,
            'total_contrats': len(contrats_data),
            'total_loyer_mensuel': total_loyer_mensuel
        }
    
    @staticmethod
    def _get_paiements_recents(bailleur):
        """Récupère l'historique des paiements des 5 derniers mois."""
        aujourd_hui = timezone.now()
        mois_debut = (aujourd_hui - timedelta(days=150)).replace(day=1)
        
        paiements = Paiement.objects.filter(
            contrat__propriete__bailleur=bailleur,
            contrat__est_actif=True,
            date_paiement__gte=mois_debut,
            statut='valide',
            is_deleted=False
        ).select_related('contrat', 'contrat__propriete', 'contrat__locataire')
        
        # Grouper par mois
        paiements_par_mois = {}
        total_general = 0
        
        for paiement in paiements:
            mois_key = paiement.date_paiement.strftime('%Y-%m')
            if mois_key not in paiements_par_mois:
                paiements_par_mois[mois_key] = {
                    'mois': mois_key,
                    'paiements': [],
                    'total_mois': 0,
                    'nombre_paiements': 0
                }
            
            paiement_info = {
                'id': paiement.id,
                'montant': paiement.montant,
                'date_paiement': paiement.date_paiement.isoformat(),
                'type_paiement': paiement.type_paiement,
                'contrat_numero': paiement.contrat.numero_contrat,
                'propriete_adresse': paiement.contrat.propriete.adresse,
                'locataire_nom': paiement.contrat.locataire.get_nom_complet()
            }
            
            paiements_par_mois[mois_key]['paiements'].append(paiement_info)
            paiements_par_mois[mois_key]['total_mois'] += paiement.montant
            paiements_par_mois[mois_key]['nombre_paiements'] += 1
            total_general += paiement.montant
        
        # Convertir en liste et trier par mois
        paiements_liste = list(paiements_par_mois.values())
        paiements_liste.sort(key=lambda x: x['mois'], reverse=True)
        
        return {
            'paiements_par_mois': paiements_liste[:5],  # 5 derniers mois
            'total_general': total_general,
            'moyenne_mensuelle': total_general / len(paiements_liste) if paiements_liste else 0
        }
    
    @staticmethod
    def _get_charges_deductibles(bailleur):
        """Récupère les charges déductibles du bailleur."""
        charges = ChargeDeductible.objects.filter(
            contrat__propriete__bailleur=bailleur,
            contrat__est_actif=True,
            is_deleted=False
        ).select_related('contrat', 'contrat__propriete')
        
        charges_data = []
        total_charges = 0
        charges_en_attente = 0
        
        for charge in charges:
            charge_info = {
                'id': charge.id,
                'titre': charge.titre,
                'montant': charge.montant,
                'date_charge': charge.date_charge.isoformat() if charge.date_charge else None,
                'statut': charge.statut,
                'contrat_numero': charge.contrat.numero_contrat,
                'propriete_adresse': charge.contrat.propriete.adresse
            }
            
            charges_data.append(charge_info)
            total_charges += charge.montant
            
            if charge.statut == 'en_attente':
                charges_en_attente += charge.montant
        
        return {
            'charges': charges_data,
            'total_charges': total_charges,
            'charges_en_attente': charges_en_attente,
            'nombre_charges': len(charges_data)
        }
    
    @staticmethod
    def _get_charges_bailleur(bailleur):
        """Récupère les charges spécifiques au bailleur."""
        charges = ChargesBailleur.objects.filter(
            propriete__bailleur=bailleur
        ).select_related('propriete')
        
        charges_data = []
        total_charges = 0
        charges_en_attente = 0
        
        for charge in charges:
            charge_info = {
                'id': charge.id,
                'titre': charge.titre,
                'montant': charge.montant,
                'montant_restant': charge.montant_restant,
                'date_charge': charge.date_charge.isoformat() if charge.date_charge else None,
                'statut': charge.statut,
                'propriete_adresse': charge.propriete.adresse,
                'progression_deduction': charge.get_progression_deduction()
            }
            
            charges_data.append(charge_info)
            total_charges += charge.montant
            
            if charge.statut in ['en_attente', 'deduite_retrait']:
                charges_en_attente += charge.montant_restant
        
        return {
            'charges': charges_data,
            'total_charges': total_charges,
            'charges_en_attente': charges_en_attente,
            'nombre_charges': len(charges_data)
        }
    
    @staticmethod
    def _get_retraits_recents(bailleur):
        """Récupère l'historique des retraits des 5 derniers mois."""
        aujourd_hui = timezone.now()
        mois_debut = (aujourd_hui - timedelta(days=150)).replace(day=1)
        
        retraits = RetraitBailleur.objects.filter(
            bailleur=bailleur,
            mois_retrait__gte=mois_debut,
            is_deleted=False
        ).order_by('-mois_retrait')
        
        retraits_data = []
        total_retraits = 0
        
        for retrait in retraits:
            retrait_info = {
                'id': retrait.id,
                'mois_retrait': retrait.mois_retrait.isoformat(),
                'montant_loyers_bruts': retrait.montant_loyers_bruts,
                'montant_charges_deductibles': retrait.montant_charges_deductibles,
                'montant_net_a_payer': retrait.montant_net_a_payer,
                'type_retrait': retrait.type_retrait,
                'statut': retrait.statut,
                'mode_retrait': retrait.mode_retrait,
                'date_demande': retrait.date_demande.isoformat() if retrait.date_demande else None
            }
            
            retraits_data.append(retrait_info)
            total_retraits += retrait.montant_net_a_payer
        
        return {
            'retraits': retraits_data[:5],  # 5 derniers retraits
            'total_retraits': total_retraits,
            'nombre_retraits': len(retraits_data)
        }
    
    @staticmethod
    def _get_calculs_automatiques(bailleur):
        """Calcule automatiquement les montants pour le retrait."""
        # Mois actuel
        mois_actuel = timezone.now().replace(day=1)
        
        # Loyers perçus ce mois
        loyers_ce_mois = Paiement.objects.filter(
            contrat__propriete__bailleur=bailleur,
            contrat__est_actif=True,
            date_paiement__year=mois_actuel.year,
            date_paiement__month=mois_actuel.month,
            statut='valide',
            is_deleted=False
        ).aggregate(total=Sum('montant'))['total'] or 0
        
        # Charges déductibles ce mois
        charges_ce_mois = ChargeDeductible.objects.filter(
            contrat__propriete__bailleur=bailleur,
            contrat__est_actif=True,
            date_charge__year=mois_actuel.year,
            date_charge__month=mois_actuel.month,
            statut='validee',
            is_deleted=False
        ).aggregate(total=Sum('montant'))['total'] or 0
        
        # Charges de bailleur ce mois
        charges_bailleur_ce_mois = ChargesBailleur.objects.filter(
            propriete__bailleur=bailleur,
            date_charge__year=mois_actuel.year,
            date_charge__month=mois_actuel.month,
            statut__in=['en_attente', 'deduite_retrait']
        ).aggregate(total=Sum('montant_restant'))['total'] or 0
        
        # Total des charges
        total_charges = charges_ce_mois + charges_bailleur_ce_mois
        
        # Montant net à payer
        montant_net = loyers_ce_mois - total_charges
        
        # Vérifier s'il y a déjà un retrait pour ce mois
        retrait_existant = RetraitBailleur.objects.filter(
            bailleur=bailleur,
            mois_retrait__year=mois_actuel.year,
            mois_retrait__month=mois_actuel.month,
            is_deleted=False
        ).first()
        
        return {
            'mois_courant': mois_actuel.strftime('%B %Y'),
            'loyers_ce_mois': loyers_ce_mois,
            'charges_ce_mois': charges_ce_mois,
            'charges_bailleur_ce_mois': charges_bailleur_ce_mois,
            'total_charges': total_charges,
            'montant_net_a_payer': montant_net,
            'retrait_existant': retrait_existant.id if retrait_existant else None,
            'peut_creer_retrait': montant_net > 0 and not retrait_existant
        }
    
    @staticmethod
    def _get_alertes(bailleur):
        """Génère des alertes intelligentes pour le bailleur."""
        alertes = []
        
        # Vérifier les contrats sans paiement récent
        contrats_actifs = Contrat.objects.filter(
            propriete__bailleur=bailleur,
            est_actif=True,
            is_deleted=False
        )
        
        for contrat in contrats_actifs:
            # Dernier paiement
            dernier_paiement = Paiement.objects.filter(
                contrat=contrat,
                statut='valide',
                is_deleted=False
            ).order_by('-date_paiement').first()
            
            if dernier_paiement:
                jours_sans_paiement = (timezone.now().date() - dernier_paiement.date_paiement).days
                
                if jours_sans_paiement > 45:  # Plus d'1 mois et demi
                    alertes.append({
                        'type': 'retard_paiement',
                        'severite': 'haute',
                        'message': f'Retard de paiement pour {contrat.locataire.get_nom_complet()} - {contrat.propriete.adresse}',
                        'contrat_id': contrat.id,
                        'jours_retard': jours_sans_paiement
                    })
        
        # Vérifier les charges en attente
        charges_en_attente = ChargesBailleur.objects.filter(
            propriete__bailleur=bailleur,
            statut='en_attente'
        )
        
        if charges_en_attente.exists():
            total_charges = sum(charge.montant_restant for charge in charges_en_attente)
            alertes.append({
                'type': 'charges_en_attente',
                'severite': 'normale',
                'message': f'{charges_en_attente.count()} charges en attente pour un total de {total_charges} F CFA',
                'total_charges': total_charges
            })
        
        return alertes
    
    @staticmethod
    def _get_suggestions_retrait(bailleur):
        """Génère des suggestions intelligentes pour le retrait."""
        calculs = ServiceContexteIntelligentRetraits._get_calculs_automatiques(bailleur)
        
        suggestions = []
        
        # Suggestion de retrait mensuel
        if calculs['peut_creer_retrait']:
            suggestions.append({
                'type': 'retrait_mensuel',
                'montant_loyers': calculs['loyers_ce_mois'],
                'montant_charges': calculs['total_charges'],
                'montant_net': calculs['montant_net_a_payer'],
                'libelle': f'Retrait mensuel {calculs["mois_courant"]}',
                'priorite': 'haute' if calculs['montant_net_a_payer'] > 0 else 'normale'
            })
        
        # Suggestion de retrait exceptionnel si montant élevé
        if calculs['montant_net_a_payer'] > 100000:  # Plus de 100k F CFA
            suggestions.append({
                'type': 'retrait_exceptionnel',
                'montant': calculs['montant_net_a_payer'],
                'libelle': 'Retrait exceptionnel - Montant élevé',
                'priorite': 'normale'
            })
        
        return suggestions
    
    @staticmethod
    def get_suggestions_retrait(bailleur_id):
        """
        Génère des suggestions intelligentes pour le retrait.
        """
        contexte = ServiceContexteIntelligentRetraits.get_contexte_complet_bailleur(bailleur_id)
        
        if not contexte['success']:
            return contexte
        
        data = contexte['data']
        suggestions = data['suggestions']
        
        return {
            'success': True,
            'suggestions': suggestions
        }
