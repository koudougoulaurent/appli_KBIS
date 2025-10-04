"""
Services pour le calcul des retraits aux bailleurs
"""
from decimal import Decimal
from datetime import date
from django.db.models import Sum, Q
from proprietes.models import Bailleur, Propriete
from contrats.models import Contrat
from paiements.models import Paiement, ChargeDeductible


class ServiceCalculRetraits:
    """
    Service pour calculer les retraits aux bailleurs
    """
    
    @staticmethod
    def calculer_retrait_mensuel_bailleur(bailleur, mois, annee):
        """
        Calcule le retrait mensuel pour un bailleur donné
        """
        # Date de début et fin du mois
        date_debut = date(annee, mois, 1)
        if mois == 12:
            date_fin = date(annee + 1, 1, 1)
        else:
            date_fin = date(annee, mois + 1, 1)
        
        # Récupérer les propriétés du bailleur
        proprietes = bailleur.proprietes.filter(is_deleted=False)
        
        total_loyers = Decimal('0')
        total_charges_deductibles = Decimal('0')
        total_charges_bailleur = Decimal('0')
        
        # Calculer pour chaque propriété
        for propriete in proprietes:
            # Loyers de la propriété
            loyers_propriete = ServiceCalculRetraits._calculer_loyers_propriete(
                propriete, date_debut, date_fin
            )
            total_loyers += loyers_propriete
            
            # Charges déductibles
            charges_deductibles = ServiceCalculRetraits._calculer_charges_deductibles(
                propriete, date_debut, date_fin
            )
            total_charges_deductibles += charges_deductibles
            
            # Charges bailleur
            charges_bailleur = ServiceCalculRetraits._calculer_charges_bailleur(
                propriete, date_debut, date_fin
            )
            total_charges_bailleur += charges_bailleur
        
        # Montant net
        montant_net = total_loyers - total_charges_deductibles - total_charges_bailleur
        
        return {
            'total_loyers': total_loyers,
            'total_charges_deductibles': total_charges_deductibles,
            'total_charges_bailleur': total_charges_bailleur,
            'montant_net': max(montant_net, Decimal('0')),
            'proprietes_count': proprietes.count()
        }
    
    @staticmethod
    def _calculer_loyers_propriete(propriete, date_debut, date_fin):
        """Calcule les loyers perçus pour une propriété"""
        # Récupérer les paiements de loyers pour cette propriété
        paiements = Paiement.objects.filter(
            contrat__propriete=propriete,
            date_paiement__gte=date_debut,
            date_paiement__lt=date_fin,
            statut='valide',
            is_deleted=False
        )
        
        # Somme des montants de loyers
        total = paiements.aggregate(
            total=Sum('montant')
        )['total'] or Decimal('0')
        
        return Decimal(str(total))
    
    @staticmethod
    def _calculer_charges_deductibles(propriete, date_debut, date_fin):
        """Calcule les charges déductibles pour une propriété"""
        # Récupérer les charges déductibles
        charges = ChargeDeductible.objects.filter(
            contrat__propriete=propriete,
            date_charge__gte=date_debut,
            date_charge__lt=date_fin,
            statut='validee',
            is_deleted=False
        )
        
        # Somme des montants
        total = charges.aggregate(
            total=Sum('montant')
        )['total'] or Decimal('0')
        
        return Decimal(str(total))
    
    @staticmethod
    def _calculer_charges_bailleur(propriete, date_debut, date_fin):
        """Calcule les charges bailleur pour une propriété"""
        # Pour l'instant, on utilise les charges mensuelles de la propriété
        # Dans une version plus avancée, on pourrait avoir des charges spécifiques
        charges_mensuelles = propriete.charges_locataire or Decimal('0')
        
        # Calculer le nombre de mois (généralement 1)
        nb_mois = 1
        return charges_mensuelles * nb_mois
    
    @staticmethod
    def creer_retrait_automatique(bailleur, mois, annee, user=None):
        """
        Crée automatiquement un retrait pour un bailleur
        """
        from paiements.models_retraits import RetraitBailleur
        
        # Calculer les montants
        calcul = ServiceCalculRetraits.calculer_retrait_mensuel_bailleur(
            bailleur, mois, annee
        )
        
        # Vérifier s'il y a des loyers à payer
        if calcul['total_loyers'] <= 0:
            return None
        
        # Date du mois de retrait
        mois_retrait = date(annee, mois, 1)
        
        # Créer le retrait
        retrait = RetraitBailleur.objects.create(
            bailleur=bailleur,
            mois_retrait=mois_retrait,
            montant_loyers_bruts=calcul['total_loyers'],
            montant_charges_deductibles=calcul['total_charges_deductibles'],
            montant_charges_bailleur=calcul['total_charges_bailleur'],
            montant_net_a_payer=calcul['montant_net'],
            statut='en_attente',
            type_retrait='mensuel',
            mode_retrait='virement',
            cree_par=user
        )
        
        return retrait
    
    @staticmethod
    def creer_retraits_automatiques_mensuels(mois, annee, user=None):
        """
        Crée automatiquement tous les retraits mensuels
        """
        # Récupérer tous les bailleurs actifs avec des propriétés
        bailleurs = Bailleur.objects.filter(
            actif=True,
            proprietes__is_deleted=False
        ).distinct()
        
        retraits_crees = 0
        retraits_existants = 0
        
        for bailleur in bailleurs:
            # Vérifier si un retrait existe déjà
            mois_retrait = date(annee, mois, 1)
            retrait_existant = RetraitBailleur.objects.filter(
                bailleur=bailleur,
                mois_retrait=mois_retrait,
                is_deleted=False
            ).first()
            
            if retrait_existant:
                retraits_existants += 1
                continue
            
            # Créer le retrait
            retrait = ServiceCalculRetraits.creer_retrait_automatique(
                bailleur, mois, annee, user
            )
            
            if retrait:
                retraits_crees += 1
        
        return {
            'retraits_crees': retraits_crees,
            'retraits_existants': retraits_existants,
            'total_bailleurs': bailleurs.count()
        }
