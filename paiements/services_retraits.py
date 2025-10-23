"""
Services pour le calcul des retraits aux bailleurs
"""
from decimal import Decimal
from datetime import date
from django.db.models import Sum, Q
from proprietes.models import Bailleur, Propriete
from contrats.models import Contrat
from paiements.models import Paiement, ChargeDeductible, RetraitBailleur


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
    def verifier_cautions_payees(bailleur):
        """
        Vérifie que tous les locataires de toutes les propriétés du bailleur ont payé leur caution
        """
        # Récupérer toutes les propriétés du bailleur
        proprietes = bailleur.proprietes.filter(is_deleted=False)
        
        for propriete in proprietes:
            # Récupérer tous les contrats actifs de cette propriété
            contrats_actifs = Contrat.objects.filter(
                propriete=propriete,
                is_deleted=False,
                est_actif=True
            )
            
            for contrat in contrats_actifs:
                # Vérifier si la caution a été payée
                caution_payee = Paiement.objects.filter(
                    contrat=contrat,
                    type_paiement__in=['caution', 'depot_garantie'],
                    statut='valide',
                    is_deleted=False
                ).exists()
                
                if not caution_payee:
                    return False, f"Caution non payée pour le contrat {contrat.numero_contrat} (Propriété: {propriete.adresse})"
        
        return True, "Toutes les cautions sont payées"
    
    @staticmethod
    def verifier_loyers_mois_courant(bailleur, mois, annee):
        """
        Vérifie que tous les locataires de toutes les propriétés du bailleur ont payé leur loyer du mois courant
        """
        # Date de début et fin du mois
        date_debut = date(annee, mois, 1)
        if mois == 12:
            date_fin = date(annee + 1, 1, 1)
        else:
            date_fin = date(annee, mois + 1, 1)
        
        # Récupérer toutes les propriétés du bailleur
        proprietes = bailleur.proprietes.filter(is_deleted=False)
        
        for propriete in proprietes:
            # Récupérer tous les contrats actifs de cette propriété
            contrats_actifs = Contrat.objects.filter(
                propriete=propriete,
                is_deleted=False,
                est_actif=True
            )
            
            for contrat in contrats_actifs:
                # Vérifier si le loyer du mois a été payé
                loyer_paye = Paiement.objects.filter(
                    contrat=contrat,
                    type_paiement='loyer',
                    statut='valide',
                    is_deleted=False,
                    date_paiement__gte=date_debut,
                    date_paiement__lt=date_fin
                ).exists()
                
                if not loyer_paye:
                    return False, f"Loyer du mois non payé pour le contrat {contrat.numero_contrat} (Propriété: {propriete.adresse})"
        
        return True, "Tous les loyers du mois sont payés"
    
    @staticmethod
    def verifier_conditions_temporelles():
        """
        Vérifie si la génération automatique des retraits est autorisée selon les conditions temporelles.
        
        RÈGLE : Génération possible uniquement du 25 du mois courant au 5 du mois suivant
        """
        from datetime import date as dt_date
        
        aujourd_hui = dt_date.today()
        jour_actuel = aujourd_hui.day
        
        # Condition : entre le 25 du mois courant et le 5 du mois suivant
        if jour_actuel >= 25 or jour_actuel <= 5:
            return True, f"Génération autorisée (jour {jour_actuel} - période du 25 au 5)"
        else:
            return False, f"Génération non autorisée (jour {jour_actuel} - période autorisée : du 25 au 5)"
    
    @staticmethod
    def creer_retrait_automatique(bailleur, mois, annee, user=None):
        """
        Crée automatiquement un retrait pour un bailleur
        Applique la logique des conditions temporelles et des deux conditions alternatives :
        1. Vérification des conditions temporelles (25 du mois au 5 du mois suivant) - UNIQUEMENT pour les retraits automatiques
        2. Si toutes les cautions sont payées → retrait possible même sans loyers du mois
        3. Sinon → tous les loyers du mois doivent être payés
        """
        # Vérification des conditions temporelles (UNIQUEMENT pour les retraits automatiques)
        conditions_temporelles_ok, message_temporel = ServiceCalculRetraits.verifier_conditions_temporelles()
        
        if not conditions_temporelles_ok:
            print(f"RETRAIT AUTOMATIQUE NON CRÉÉ pour {bailleur.nom} {bailleur.prenom}: {message_temporel}")
            return None
        # Condition 1 : Vérifier si toutes les cautions sont payées
        cautions_ok, message_cautions = ServiceCalculRetraits.verifier_cautions_payees(bailleur)
        
        if cautions_ok:
            # Toutes les cautions sont payées → on peut créer le retrait même sans loyers du mois
            print(f"Toutes les cautions payées pour {bailleur.nom} {bailleur.prenom} - Retrait possible")
        else:
            # Condition 2 : Vérifier que tous les loyers du mois sont payés
            loyers_ok, message_loyers = ServiceCalculRetraits.verifier_loyers_mois_courant(bailleur, mois, annee)
            
            if not loyers_ok:
                print(f"Retrait non créé pour {bailleur.nom} {bailleur.prenom}: {message_loyers}")
                return None
        
        # Calculer les montants
        calcul = ServiceCalculRetraits.calculer_retrait_mensuel_bailleur(
            bailleur, mois, annee
        )
        
        # Vérifier s'il y a des loyers à payer
        if calcul['total_loyers'] <= 0:
            print(f"Retrait non créé pour {bailleur.nom} {bailleur.prenom}: Aucun loyer perçu")
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
    def creer_retrait_manuel(bailleur, mois, annee, user=None):
        """
        Crée un retrait manuel pour un bailleur
        N'APPLIQUE PAS les conditions temporelles - permet la création à tout moment
        Applique uniquement les conditions logiques :
        1. Si toutes les cautions sont payées → retrait possible même sans loyers du mois
        2. Sinon → tous les loyers du mois doivent être payés
        """
        print(f"CRÉATION RETRAIT MANUEL pour {bailleur.nom} {bailleur.prenom} - Aucune restriction temporelle")
        
        # Condition 1 : Vérifier si toutes les cautions sont payées
        cautions_ok, message_cautions = ServiceCalculRetraits.verifier_cautions_payees(bailleur)
        
        if cautions_ok:
            # Toutes les cautions sont payées → on peut créer le retrait même sans loyers du mois
            print(f"Toutes les cautions payées pour {bailleur.nom} {bailleur.prenom} - Retrait possible")
        else:
            # Condition 2 : Vérifier que tous les loyers du mois sont payés
            loyers_ok, message_loyers = ServiceCalculRetraits.verifier_loyers_mois_courant(bailleur, mois, annee)
            
            if not loyers_ok:
                print(f"Retrait manuel non créé pour {bailleur.nom} {bailleur.prenom}: {message_loyers}")
                return None
        
        # Calculer les montants
        calcul = ServiceCalculRetraits.calculer_retrait_mensuel_bailleur(
            bailleur, mois, annee
        )
        
        # Vérifier s'il y a des loyers à payer
        if calcul['total_loyers'] <= 0:
            print(f"Retrait manuel non créé pour {bailleur.nom} {bailleur.prenom}: Aucun loyer perçu")
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
        
        print(f"RETRAIT MANUEL CRÉÉ pour {bailleur.nom} {bailleur.prenom} - Montant: {retrait.montant_net_a_payer} F CFA")
        return retrait
    
    @staticmethod
    def creer_retraits_automatiques_mensuels(mois, annee, user=None):
        """
        Crée automatiquement des retraits pour tous les bailleurs éligibles du mois donné.
        Applique toutes les conditions : temporelles, cautions et loyers.
        """
        from proprietes.models import Bailleur as BailleurModel
        
        # Vérification des conditions temporelles
        conditions_temporelles_ok, message_temporel = ServiceCalculRetraits.verifier_conditions_temporelles()
        
        if not conditions_temporelles_ok:
            print(f"CRÉATION AUTOMATIQUE ANNULÉE: {message_temporel}")
            return {
                'success': False,
                'message': message_temporel,
                'retraits_crees': 0,
                'retraits_ignores': 0,
                'retraits_existants': 0,
                'cautions_manquantes': 0,
                'loyers_manquants': 0,
                'aucun_loyer': 0,
                'details': []
            }
        
        print(f"CRÉATION AUTOMATIQUE AUTORISÉE: {message_temporel}")
        
        # Récupérer tous les bailleurs actifs
        bailleurs = BailleurModel.objects.filter(is_deleted=False)
        
        retraits_crees = 0
        retraits_ignores = 0
        details = []
        
        for bailleur in bailleurs:
            try:
                retrait = ServiceCalculRetraits.creer_retrait_automatique(bailleur, mois, annee, user)
                
                if retrait:
                    retraits_crees += 1
                    details.append(f"✅ Retrait créé pour {bailleur.nom} {bailleur.prenom} - Montant: {retrait.montant_net_a_payer} F CFA")
                else:
                    retraits_ignores += 1
                    details.append(f"❌ Retrait ignoré pour {bailleur.nom} {bailleur.prenom}")
                    
            except Exception as e:
                retraits_ignores += 1
                details.append(f"❌ Erreur pour {bailleur.nom} {bailleur.prenom}: {str(e)}")
        
        return {
            'success': True,
            'message': f"Génération terminée: {retraits_crees} retraits créés, {retraits_ignores} ignorés",
            'retraits_crees': retraits_crees,
            'retraits_ignores': retraits_ignores,
            'retraits_existants': 0,  # Pas de retraits existants dans cette méthode
            'cautions_manquantes': 0,  # Pas de décompte séparé dans cette méthode
            'loyers_manquants': 0,  # Pas de décompte séparé dans cette méthode
            'aucun_loyer': 0,  # Pas de décompte séparé dans cette méthode
            'details': details
        }
    
    @staticmethod
    def creer_retraits_automatiques_mensuels_legacy(mois, annee, user=None):
        """
        Ancienne méthode de création automatique des retraits (pour compatibilité)
        """
        # Vérifier la période autorisée pour les retraits
        from .services_retrait import ServiceGestionRetrait
        periode_ok, message_periode = ServiceGestionRetrait.verifier_periode_retrait()
        if not periode_ok:
            return {
                'success': False,
                'message': message_periode,
                'retraits_crees': 0,
                'retraits_existants': 0,
                'cautions_manquantes': 0,
                'loyers_manquants': 0
            }
        
        # Récupérer tous les bailleurs actifs avec des propriétés
        bailleurs = Bailleur.objects.filter(
            actif=True,
            proprietes__is_deleted=False
        ).distinct()
        
        retraits_crees = 0
        retraits_existants = 0
        cautions_manquantes = 0
        loyers_manquants = 0
        aucun_loyer = 0
        
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
            
            # Vérifier les conditions alternatives
            cautions_ok, message_cautions = ServiceCalculRetraits.verifier_cautions_payees(bailleur)
            
            if not cautions_ok:
                # Cautions manquantes → vérifier les loyers du mois
                loyers_ok, message_loyers = ServiceCalculRetraits.verifier_loyers_mois_courant(bailleur, mois, annee)
                
                if not loyers_ok:
                    loyers_manquants += 1
                    continue
                else:
                    cautions_manquantes += 1
            
            # Créer le retrait
            retrait = ServiceCalculRetraits.creer_retrait_automatique(
                bailleur, mois, annee, user
            )
            
            if retrait:
                retraits_crees += 1
            else:
                # Si pas de retrait créé, c'est probablement qu'il n'y a pas de loyers
                aucun_loyer += 1
        
        return {
            'retraits_crees': retraits_crees,
            'retraits_existants': retraits_existants,
            'cautions_manquantes': cautions_manquantes,
            'loyers_manquants': loyers_manquants,
            'aucun_loyer': aucun_loyer,
            'total_bailleurs': bailleurs.count()
        }
