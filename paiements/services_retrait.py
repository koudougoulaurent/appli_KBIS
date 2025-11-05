from django.db import transaction
from django.utils import timezone
from decimal import Decimal
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from django.contrib import messages
from django.db.models import Sum
from .models import RetraitBailleur, RecapMensuel, ChargeDeductible, ChargeBailleur
from proprietes.models import Bailleur


class ServiceGestionRetrait:
    """
    Service intelligent pour la gestion des retraits avec restrictions et améliorations
    """
    
    @staticmethod
    def verifier_periode_retrait():
        """
        Vérifie si on est dans la période autorisée pour générer des retraits
        Du 25 du mois au 5 du mois suivant
        """
        aujourd_hui = date.today()
        jour_actuel = aujourd_hui.day
        
        # Période autorisée : du 25 au 5 du mois suivant
        if jour_actuel >= 25 or jour_actuel <= 5:
            return True, "Période autorisée pour les retraits"
        else:
            return False, f"Les retraits ne peuvent être générés que du 25 au 5 du mois suivant. Aujourd'hui : {aujourd_hui.strftime('%d/%m/%Y')}"
    
    @staticmethod
    def verifier_mois_retrait_approprié(bailleur, mois_retrait):
        """
        Vérifie que le mois de retrait est approprié par rapport aux contrats du bailleur
        Un retrait n'est possible qu'à partir du mois de commencement de chaque contrat
        """
        from contrats.models import Contrat
        from paiements.models import Paiement
        
        # Récupérer tous les contrats actifs du bailleur
        contrats_actifs = Contrat.objects.filter(
            propriete__bailleur=bailleur,
            est_actif=True,
            est_resilie=False
        )
        
        if not contrats_actifs.exists():
            return False, f"Aucun contrat actif trouvé pour {bailleur.get_nom_complet()}"
        
        # Vérifier pour chaque contrat
        contrats_problematiques = []
        
        for contrat in contrats_actifs:
            # Récupérer le premier paiement du contrat (mois de commencement)
            premier_paiement = Paiement.objects.filter(
                contrat=contrat,
                statut='valide'
            ).order_by('date_paiement').first()
            
            if premier_paiement:
                mois_commencement = premier_paiement.date_paiement.replace(day=1)
                
                # Vérifier si le mois de retrait est antérieur au mois de commencement
                if mois_retrait < mois_commencement:
                    contrats_problematiques.append({
                        'contrat': contrat.numero_contrat,
                        'mois_commencement': mois_commencement.strftime('%B %Y'),
                        'mois_retrait': mois_retrait.strftime('%B %Y')
                    })
        
        if contrats_problematiques:
            message = f"Retrait impossible pour {mois_retrait.strftime('%B %Y')}. "
            message += "Les contrats suivants n'ont pas encore commencé : "
            for contrat_info in contrats_problematiques:
                message += f"{contrat_info['contrat']} (commencé en {contrat_info['mois_commencement']}), "
            message = message.rstrip(', ')
            return False, message
        
        return True, "Mois de retrait approprié"
    
    @staticmethod
    def calculer_retrait_optimise(bailleur, mois_retrait):
        """
        Calcule le retrait optimisé avec sommation des loyers et charges bailleur
        """
        try:
            # Récupérer les propriétés actives du bailleur
            proprietes_actives = bailleur.proprietes.filter(
                contrats__est_actif=True,
                contrats__est_resilie=False
            ).distinct()
            
            if not proprietes_actives.exists():
                return {
                    'success': False,
                    'message': 'Aucune propriété louée trouvée pour ce bailleur'
                }
            
            total_loyers_bruts = Decimal('0')
            total_charges_deductibles = Decimal('0')
            total_charges_bailleur = Decimal('0')
            details_proprietes = []
            
            for propriete in proprietes_actives:
                # Récupérer les contrats actifs de cette propriété
                contrats_actifs = propriete.contrats.filter(
                    est_actif=True,
                    est_resilie=False
                )
                
                loyer_propriete = Decimal('0')
                charges_propriete = Decimal('0')
                
                for contrat in contrats_actifs:
                    # Loyer mensuel du contrat
                    loyer_mensuel = Decimal(str(contrat.loyer_mensuel or '0'))
                    charges_mensuelles = Decimal(str(contrat.charges_mensuelles or '0'))
                    loyer_propriete += loyer_mensuel + charges_mensuelles
                    
                    # Charges déductibles pour le mois
                    charges_deductibles = ChargeDeductible.objects.filter(
                        contrat=contrat,
                        date_charge__year=mois_retrait.year,
                        date_charge__month=mois_retrait.month,
                        est_valide=True
                    ).aggregate(total=Sum('montant'))['total'] or Decimal('0')
                    
                    charges_propriete += charges_deductibles
                
                # Charges bailleur pour cette propriété (via le bailleur)
                charges_bailleur_propriete = ChargeBailleur.objects.filter(
                    bailleur=bailleur,
                    date_charge__year=mois_retrait.year,
                    date_charge__month=mois_retrait.month,
                    statut__in=['en_attente', 'valide']
                ).aggregate(total=Sum('montant'))['total'] or Decimal('0')
                
                # Montant net pour cette propriété
                montant_net_propriete = loyer_propriete - charges_propriete - charges_bailleur_propriete
                
                # Ajouter aux totaux
                total_loyers_bruts += loyer_propriete
                total_charges_deductibles += charges_propriete
                total_charges_bailleur += charges_bailleur_propriete
                
                # Détails de la propriété
                details_proprietes.append({
                    'propriete': propriete,
                    'loyer_brut': loyer_propriete,
                    'charges_deductibles': charges_propriete,
                    'charges_bailleur': charges_bailleur_propriete,
                    'montant_net': montant_net_propriete,
                    'contrats_count': contrats_actifs.count()
                })
            
            # Montant net total
            montant_net_total = total_loyers_bruts - total_charges_deductibles - total_charges_bailleur
            
            # Commission agence = 10% du montant net à payer (obligatoire)
            commission_agence = montant_net_total * Decimal('0.10')
            
            # Montant réellement payé = montant net - commission agence - charges bailleur
            # Note: Les charges bailleur sont déjà déduites dans montant_net_total,
            # donc montant_reellement_paye = montant_net_total - commission_agence
            # Mais selon la demande, on déduit aussi les charges bailleur si elles existent
            montant_reellement_paye = montant_net_total - commission_agence - total_charges_bailleur
            
            return {
                'success': True,
                'montant_loyers_bruts': total_loyers_bruts,
                'montant_charges_deductibles': total_charges_deductibles,
                'montant_charges_bailleur': total_charges_bailleur,
                'montant_net_total': montant_net_total,
                'commission_agence': commission_agence,
                'montant_reellement_paye': montant_reellement_paye,
                'details_proprietes': details_proprietes,
                'proprietes_count': proprietes_actives.count()
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Erreur lors du calcul: {str(e)}'
            }
    
    @staticmethod
    def creer_retrait_avec_restrictions(bailleur, mois_retrait, request_user):
        """
        Crée un retrait en respectant les restrictions de période
        """
        # Vérifier la période autorisée
        periode_ok, message_periode = ServiceGestionRetrait.verifier_periode_retrait()
        
        if not periode_ok:
            return {
                'success': False,
                'message': message_periode
            }
        
        # Vérifier que le mois de retrait est approprié par rapport aux contrats
        mois_ok, message_mois = ServiceGestionRetrait.verifier_mois_retrait_approprié(bailleur, mois_retrait)
        
        if not mois_ok:
            return {
                'success': False,
                'message': message_mois
            }
        
        # Vérifier s'il existe déjà un retrait pour ce bailleur et ce mois
        retrait_existant = RetraitBailleur.objects.filter(
            bailleur=bailleur,
            mois_retrait__year=mois_retrait.year,
            mois_retrait__month=mois_retrait.month,
            is_deleted=False
        ).first()
        
        if retrait_existant:
            return {
                'success': False,
                'message': f'Un retrait existe déjà pour {bailleur.get_nom_complet()} pour le mois de {mois_retrait.strftime("%B %Y")}'
            }
        
        # Calculer le retrait optimisé
        calcul = ServiceGestionRetrait.calculer_retrait_optimise(bailleur, mois_retrait)
        
        if not calcul['success']:
            return calcul
        
        try:
            with transaction.atomic():
                # Créer le retrait
                retrait = RetraitBailleur.objects.create(
                    bailleur=bailleur,
                    mois_retrait=mois_retrait,
                    montant_loyers_bruts=calcul['montant_loyers_bruts'],
                    montant_charges_deductibles=calcul['montant_charges_deductibles'],
                    montant_charges_bailleur=calcul['montant_charges_bailleur'],
                    montant_net_a_payer=calcul['montant_net_total'],
                    commission_agence=calcul.get('commission_agence', Decimal('0')),
                    montant_reellement_paye=calcul.get('montant_reellement_paye', Decimal('0')),
                    statut='en_attente',
                    type_retrait='mensuel',
                    mode_retrait='virement',
                    date_demande=timezone.now().date(),
                    cree_par=request_user
                )
                
                # Appliquer automatiquement les charges de bailleur
                resultat_charges = retrait.appliquer_charges_automatiquement()
                
                return {
                    'success': True,
                    'retrait': retrait,
                    'message': f'Retrait créé avec succès pour {bailleur.get_nom_complet()}',
                    'charges_appliquees': resultat_charges.get('charges_appliquees', 0),
                    'details': calcul
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'Erreur lors de la création du retrait: {str(e)}'
            }
    
    @staticmethod
    def mettre_a_jour_charges_immediatement(propriete, mois_retrait):
        """
        Met à jour immédiatement les retraits existants quand des charges sont ajoutées
        """
        try:
            # Récupérer les retraits en attente pour ce bailleur et ce mois
            retraits_a_mettre_a_jour = RetraitBailleur.objects.filter(
                bailleur__proprietes=propriete,
                mois_retrait__year=mois_retrait.year,
                mois_retrait__month=mois_retrait.month,
                statut='en_attente'
            )
            
            for retrait in retraits_a_mettre_a_jour:
                # Recalculer le retrait
                calcul = ServiceGestionRetrait.calculer_retrait_optimise(retrait.bailleur, retrait.mois_retrait)
                
                if calcul['success']:
                    # Mettre à jour les montants
                    retrait.montant_loyers_bruts = calcul['montant_loyers_bruts']
                    retrait.montant_charges_deductibles = calcul['montant_charges_deductibles']
                    retrait.montant_charges_bailleur = calcul['montant_charges_bailleur']
                    retrait.montant_net_a_payer = calcul['montant_net_total']
                    retrait.commission_agence = calcul.get('commission_agence', Decimal('0'))
                    retrait.montant_reellement_paye = calcul.get('montant_reellement_paye', Decimal('0'))
                    retrait.save()
            
            return {
                'success': True,
                'retraits_mis_a_jour': retraits_a_mettre_a_jour.count(),
                'message': f'{retraits_a_mettre_a_jour.count()} retrait(s) mis à jour'
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Erreur lors de la mise à jour: {str(e)}'
            }
    
    @staticmethod
    def generer_recap_mensuel_avec_restrictions(mois_date, request_user):
        """
        Génère les récapitulatifs mensuels avec vérification des restrictions
        """
        # Vérifier la période autorisée
        periode_ok, message_periode = ServiceGestionRetrait.verifier_periode_retrait()
        
        if not periode_ok:
            return {
                'success': False,
                'message': message_periode
            }
        
        try:
            # Récupérer tous les bailleurs avec des propriétés louées
            bailleurs = Bailleur.objects.filter(
                proprietes__contrats__est_actif=True,
                proprietes__contrats__est_resilie=False
            ).distinct()
            
            recaps_crees = []
            
            with transaction.atomic():
                for bailleur in bailleurs:
                    try:
                        # Vérifier si le bailleur a des propriétés louées
                        proprietes_louees = bailleur.proprietes.filter(
                            contrats__est_actif=True,
                            contrats__est_resilie=False
                        ).distinct()
                        
                        if not proprietes_louees.exists():
                            continue
                        
                        # Vérifier si un récap existe déjà pour ce mois (non supprimé)
                        recap_existant = RecapMensuel.objects.filter(
                            bailleur=bailleur,
                            mois_recap__year=mois_date.year,
                            mois_recap__month=mois_date.month,
                            is_deleted=False
                        ).first()
                        
                        if recap_existant:
                            # Mettre à jour le récap existant
                            recap_existant.calculer_totaux_bailleur()
                            recap_existant.save()
                            recaps_crees.append(recap_existant)
                        else:
                            # Vérifier s'il existe un récapitulatif supprimé logiquement pour ce bailleur et ce mois
                            recap_supprime = RecapMensuel.objects.filter(
                                bailleur=bailleur,
                                mois_recap__year=mois_date.year,
                                mois_recap__month=mois_date.month,
                                is_deleted=True
                            ).first()
                            
                            # Si un récap supprimé existe, le supprimer physiquement avant de créer le nouveau
                            if recap_supprime:
                                recap_supprime.paiements_concernes.clear()
                                recap_supprime.charges_deductibles.clear()
                                recap_supprime.delete()
                            
                            # Créer un nouveau récap
                            recap = RecapMensuel.objects.create(
                                bailleur=bailleur,
                                mois_recap=mois_date,
                                cree_par=request_user
                            )
                            
                            # Calculer automatiquement tous les totaux
                            recap.calculer_totaux_bailleur()
                            recap.save()
                            recaps_crees.append(recap)
                        
                    except Exception as e:
                        continue
            
            return {
                'success': True,
                'recaps_crees': len(recaps_crees),
                'message': f'{len(recaps_crees)} récapitulatif(s) généré(s) avec succès'
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Erreur lors de la génération: {str(e)}'
            }
