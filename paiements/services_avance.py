from django.db import transaction
from django.utils import timezone
from decimal import Decimal
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from .models import Paiement
from .models_avance import AvanceLoyer, ConsommationAvance, HistoriquePaiement
from contrats.models import Contrat


class ServiceGestionAvance:
    """
    Service intelligent pour la gestion des avances de loyer
    """
    
    @staticmethod
    def creer_avance_loyer(contrat, montant_avance, date_avance, notes="", mois_effet_personnalise=None, mode_selection_mois='automatique', mois_couverts_manuels=None):
        """
        Crée une nouvelle avance de loyer avec gestion intelligente des mois
        """
        try:
            with transaction.atomic():
                # Récupérer le loyer mensuel du contrat
                loyer_mensuel = contrat.loyer_mensuel
                
                # Convertir en Decimal pour la comparaison
                try:
                    if loyer_mensuel is None or loyer_mensuel == '' or loyer_mensuel == '0':
                        loyer_mensuel_decimal = Decimal('0')
                    else:
                        loyer_mensuel_decimal = Decimal(str(loyer_mensuel))
                except (ValueError, TypeError, AttributeError):
                    loyer_mensuel_decimal = Decimal('0')
                
                if not loyer_mensuel or loyer_mensuel_decimal <= 0:
                    raise ValueError("Le loyer mensuel du contrat n'est pas défini ou invalide. Veuillez définir un loyer mensuel pour ce contrat avant de créer une avance.")
                
                # *** NOUVELLE LOGIQUE : Vérifier les avances existantes ***
                avances_existantes = ServiceGestionAvance.verifier_avances_existantes(contrat)
                
                # Créer l'avance
                avance = AvanceLoyer.objects.create(
                    contrat=contrat,
                    montant_avance=montant_avance,
                    loyer_mensuel=loyer_mensuel_decimal,
                    date_avance=date_avance,
                    notes=notes,
                    mois_effet_personnalise=mois_effet_personnalise,
                    mode_selection_mois=mode_selection_mois,
                    mois_couverts_manuels=mois_couverts_manuels or []
                )
                
                # Le calcul des mois est fait automatiquement dans save()
                
                # *** NOUVELLE LOGIQUE : Gérer les avances multiples et la prolongation ***
                if avances_existantes['has_avances']:
                    avance = ServiceGestionAvance.gerer_prolongation_avances(contrat, avance, avances_existantes)
                else:
                    avance = ServiceGestionAvance.gerer_avances_multiples(contrat, avance)
                
                return avance
                
        except Exception as e:
            raise Exception(f"Erreur lors de la création de l'avance: {str(e)}")
    
    @staticmethod
    def gerer_prolongation_avances(contrat, nouvelle_avance, avances_existantes):
        """
        Gère la prolongation des avances existantes avec la nouvelle avance
        """
        try:
            # Calculer le total des mois couverts par toutes les avances
            total_mois_existants = sum(avance['nombre_mois_couverts'] for avance in avances_existantes['avances'])
            mois_nouvelle_avance = nouvelle_avance.nombre_mois_couverts
            
            # Calculer la date de fin de la dernière avance existante
            derniere_avance = avances_existantes['derniere_avance']
            date_fin_derniere_avance = datetime.strptime(derniere_avance['date_avance'], '%Y-%m-%d').date()
            
            # Calculer la date de début de la nouvelle avance
            if nouvelle_avance.mode_selection_mois == 'manuel' and nouvelle_avance.mois_couverts_manuels:
                # En mode manuel, utiliser le premier mois sélectionné
                premier_mois = min(nouvelle_avance.mois_couverts_manuels)
                date_debut_nouvelle_avance = datetime.strptime(premier_mois, '%Y-%m-%d').date()
            else:
                # En mode automatique, commencer après la dernière avance
                from dateutil.relativedelta import relativedelta
                date_debut_nouvelle_avance = date_fin_derniere_avance + relativedelta(months=1)
            
            # Mettre à jour les dates de la nouvelle avance
            nouvelle_avance.mois_debut_couverture = date_debut_nouvelle_avance
            
            # Recalculer la fin de couverture
            if nouvelle_avance.mode_selection_mois == 'manuel' and nouvelle_avance.mois_couverts_manuels:
                # En mode manuel, utiliser le dernier mois sélectionné
                dernier_mois = max(nouvelle_avance.mois_couverts_manuels)
                nouvelle_avance.mois_fin_couverture = datetime.strptime(dernier_mois, '%Y-%m-%d').date()
            else:
                # En mode automatique, calculer normalement
                nouvelle_avance.mois_fin_couverture = date_debut_nouvelle_avance + relativedelta(months=mois_nouvelle_avance - 1)
            
            # Mettre à jour les notes pour indiquer la prolongation
            notes_originales = nouvelle_avance.notes or ""
            nouvelle_avance.notes = f"{notes_originales} (Prolongation - Avances multiples: {len(avances_existantes['avances']) + 1} avances, {total_mois_existants + mois_nouvelle_avance} mois couverts total)"
            
            # Sauvegarder les modifications
            nouvelle_avance.save()
            
            return nouvelle_avance
            
        except Exception as e:
            print(f"Erreur lors de la gestion de la prolongation des avances: {str(e)}")
            return nouvelle_avance
    
    @staticmethod
    def traiter_paiement_avance(paiement):
        """
        Traite un paiement d'avance et calcule automatiquement les mois couverts
        """
        try:
            with transaction.atomic():
                # Vérifier que c'est bien un paiement d'avance
                if paiement.type_paiement not in ['avance', 'avance_loyer']:
                    return False
                
                # Créer l'avance de loyer
                avance = ServiceGestionAvance.creer_avance_loyer(
                    contrat=paiement.contrat,
                    montant_avance=paiement.montant,
                    date_avance=paiement.date_paiement,
                    notes=f"Avance créée automatiquement depuis le paiement {paiement.numero_paiement}"
                )
                
                # Mettre à jour le paiement avec l'avance
                paiement.notes = f"Avance de {avance.nombre_mois_couverts} mois créée automatiquement"
                paiement.save()
                
                return avance
                
        except Exception as e:
            raise Exception(f"Erreur lors du traitement du paiement d'avance: {str(e)}")
    
    @staticmethod
    def verifier_avances_existantes(contrat):
        """
        Vérifie si un contrat a déjà des avances actives
        Retourne les informations sur les avances existantes
        """
        try:
            avances_actives = AvanceLoyer.objects.filter(
                contrat=contrat,
                statut='active',
                montant_restant__gt=0
            ).order_by('-date_avance')
            
            if not avances_actives.exists():
                return {
                    'has_avances': False,
                    'message': None,
                    'avances': []
                }
            
            # Calculer les statistiques des avances existantes
            montant_total_restant = sum(avance.montant_restant for avance in avances_actives)
            mois_couverts_restants = sum(avance.nombre_mois_couverts for avance in avances_actives)
            
            # Récupérer la dernière avance
            derniere_avance = avances_actives.first()
            
            message = f"⚠️ Ce contrat a déjà {avances_actives.count()} avance(s) active(s) :\n"
            message += f"• Montant restant total : {montant_total_restant:,.0f} F CFA\n"
            message += f"• Mois couverts restants : {mois_couverts_restants}\n"
            message += f"• Dernière avance : {derniere_avance.montant_avance:,.0f} F CFA du {derniere_avance.date_avance.strftime('%d/%m/%Y')}\n\n"
            message += "Voulez-vous ajouter une nouvelle avance pour prolonger la couverture ?"
            
            return {
                'has_avances': True,
                'message': message,
                'avances': list(avances_actives.values(
                    'id', 'montant_avance', 'montant_restant', 'date_avance', 
                    'nombre_mois_couverts', 'mois_debut_couverture', 'mois_fin_couverture'
                )),
                'montant_total_restant': float(montant_total_restant),
                'mois_couverts_restants': mois_couverts_restants,
                'derniere_avance': {
                    'id': derniere_avance.id,
                    'montant_avance': float(derniere_avance.montant_avance),
                    'date_avance': derniere_avance.date_avance.strftime('%Y-%m-%d'),
                    'nombre_mois_couverts': derniere_avance.nombre_mois_couverts
                }
            }
            
        except Exception as e:
            return {
                'has_avances': False,
                'message': f"Erreur lors de la vérification des avances : {str(e)}",
                'avances': []
            }
    
    @staticmethod
    def get_suggestions_mois_couverts(contrat, montant_avance, loyer_mensuel):
        """
        Génère des suggestions dynamiques pour les mois couverts basées sur l'historique des paiements
        """
        try:
            from .models import Paiement
            from dateutil.relativedelta import relativedelta
            
            # Récupérer les 12 derniers mois de paiements
            date_actuelle = date.today()
            date_debut = date_actuelle - relativedelta(months=12)
            
            paiements_recents = Paiement.objects.filter(
                contrat=contrat,
                date_paiement__gte=date_debut,
                type_paiement__in=['loyer', 'paiement_partiel']
            ).order_by('-date_paiement')
            
            # Calculer le nombre de mois que peut couvrir cette avance
            mois_complets_possibles = int(montant_avance // loyer_mensuel)
            
            # Générer les suggestions de mois
            suggestions = []
            
            # Option 1: Mois suivant le dernier paiement
            if paiements_recents.exists():
                dernier_paiement = paiements_recents.first()
                mois_suivant = dernier_paiement.date_paiement.replace(day=1) + relativedelta(months=1)
                
                for i in range(min(mois_complets_possibles, 12)):  # Limiter à 12 mois max
                    mois_suggestion = mois_suivant + relativedelta(months=i)
                    suggestions.append({
                        'mois': mois_suggestion,
                        'mois_formate': mois_suggestion.strftime('%B %Y'),
                        'mois_formate_fr': ServiceGestionAvance._convertir_mois_francais(mois_suggestion.strftime('%B %Y')),
                        'description': f"Mois suivant le dernier paiement + {i} mois" if i > 0 else "Mois suivant le dernier paiement",
                        'recommandé': i == 0
                    })
            else:
                # Si pas de paiements récents, commencer à partir du mois actuel
                mois_actuel = date_actuelle.replace(day=1)
                
                for i in range(min(mois_complets_possibles, 12)):
                    mois_suggestion = mois_actuel + relativedelta(months=i)
                    suggestions.append({
                        'mois': mois_suggestion,
                        'mois_formate': mois_suggestion.strftime('%B %Y'),
                        'mois_formate_fr': ServiceGestionAvance._convertir_mois_francais(mois_suggestion.strftime('%B %Y')),
                        'description': f"Mois actuel + {i} mois" if i > 0 else "Mois actuel",
                        'recommandé': i == 0
                    })
            
            return {
                'suggestions': suggestions,
                'mois_complets_possibles': mois_complets_possibles,
                'montant_par_mois': float(loyer_mensuel),
                'montant_total': float(montant_avance)
            }
            
        except Exception as e:
            return {
                'suggestions': [],
                'mois_complets_possibles': 0,
                'montant_par_mois': float(loyer_mensuel),
                'montant_total': float(montant_avance),
                'erreur': str(e)
            }
    
    @staticmethod
    def _convertir_mois_francais(mois_anglais):
        """Convertit un mois anglais en français et corrige le format des années"""
        traductions = {
            'January': 'Janvier', 'February': 'Février', 'March': 'Mars',
            'April': 'Avril', 'May': 'Mai', 'June': 'Juin',
            'July': 'Juillet', 'August': 'Août', 'September': 'Septembre',
            'October': 'Octobre', 'November': 'Novembre', 'December': 'Décembre'
        }
        
        for en, fr in traductions.items():
            mois_anglais = mois_anglais.replace(en, fr)
        
        # Corriger le format des années (0225 -> 2025, 0226 -> 2026, etc.)
        import re
        mois_anglais = re.sub(r'\b0(\d{2})\b', r'20\1', mois_anglais)
        
        return mois_anglais

    @staticmethod
    def gerer_avances_multiples(contrat, nouvelle_avance):
        """
        Gère l'ajout d'une nouvelle avance quand il y en a déjà une en cours
        """
        try:
            # Récupérer les avances actives existantes
            avances_actives = AvanceLoyer.objects.filter(
                contrat=contrat,
                statut='active'
            ).order_by('date_avance')
            
            if not avances_actives.exists():
                return nouvelle_avance
            
            # Calculer le total des mois couverts par toutes les avances
            total_mois_existants = sum(avance.nombre_mois_couverts for avance in avances_actives)
            mois_nouvelle_avance = nouvelle_avance.nombre_mois_couverts
            
            # Calculer le prochain mois de paiement en tenant compte de toutes les avances
            prochain_mois = ServiceGestionAvance.calculer_prochain_mois_paiement(contrat)
            
            # Mettre à jour les notes pour indiquer qu'il y a plusieurs avances
            notes_originales = nouvelle_avance.notes or ""
            nouvelle_avance.notes = f"{notes_originales} (Avance multiple - Total: {len(avances_actives) + 1} avances, {total_mois_existants + mois_nouvelle_avance} mois couverts)"
            nouvelle_avance.save()
            
            return nouvelle_avance
            
        except Exception as e:
            print(f"Erreur lors de la gestion des avances multiples: {str(e)}")
            return nouvelle_avance
    
    @staticmethod
    def verifier_avance_pour_mois(contrat, mois):
        """
        Vérifie si une avance couvre un mois donné et retourne le montant
        """
        try:
            # Trouver les avances actives qui couvrent ce mois
            avances_actives = AvanceLoyer.objects.filter(
                contrat=contrat,
                statut='active',
                mois_debut_couverture__lte=mois,
                mois_fin_couverture__gte=mois
            ).order_by('date_avance')
            
            if not avances_actives.exists():
                return False, Decimal('0')
            
            # Vérifier si ce mois n'a pas déjà été consommé
            for avance in avances_actives:
                deja_consomme = ConsommationAvance.objects.filter(
                    avance=avance,
                    mois_consomme=mois
                ).exists()
                
                if not deja_consomme:
                    return True, avance.loyer_mensuel
            
            return False, Decimal('0')
            
        except Exception as e:
            return False, Decimal('0')
    
    @staticmethod
    def consommer_avance_pour_mois(contrat, mois):
        """
        Consomme l'avance disponible pour un mois donné
        Synchronise automatiquement les consommations basées sur les mois écoulés
        """
        try:
            with transaction.atomic():
                # D'abord, synchroniser toutes les consommations manquantes
                ServiceGestionAvance.synchroniser_consommations_manquantes(contrat)
                
                # Trouver les avances actives pour ce contrat
                avances_actives = AvanceLoyer.objects.filter(
                    contrat=contrat,
                    statut='active',
                    mois_debut_couverture__lte=mois,
                    mois_fin_couverture__gte=mois
                ).order_by('date_avance')
                
                if not avances_actives.exists():
                    return False, Decimal('0')
                
                # Prendre la première avance disponible
                avance = avances_actives.first()
                
                # Vérifier si ce mois a déjà été consommé
                consommation_existante = ConsommationAvance.objects.filter(
                    avance=avance,
                    mois_consomme=mois
                ).exists()
                
                if consommation_existante:
                    # Le mois a déjà été consommé, retourner le montant
                    return True, avance.loyer_mensuel
                
                # Consommer un mois
                if avance.consommer_mois(mois):
                    # Créer l'enregistrement de consommation
                    ConsommationAvance.objects.create(
                        avance=avance,
                        paiement=None,  # Sera mis à jour plus tard
                        mois_consomme=mois,
                        montant_consomme=avance.loyer_mensuel,
                        montant_restant_apres=avance.montant_restant
                    )
                    
                    return True, avance.loyer_mensuel
                
                return False, Decimal('0')
                
        except Exception as e:
            raise Exception(f"Erreur lors de la consommation de l'avance: {str(e)}")
    
    @staticmethod
    def synchroniser_consommations_manquantes(contrat):
        """
        Synchronise automatiquement les consommations d'avances basées sur les mois écoulés
        """
        try:
            from django.utils import timezone
            from dateutil.relativedelta import relativedelta
            
            # Récupérer toutes les avances actives du contrat
            avances_actives = AvanceLoyer.objects.filter(
                contrat=contrat,
                statut='active',
                montant_restant__gt=0
            )
            
            for avance in avances_actives:
                # Calculer les mois écoulés depuis le début de couverture
                aujourd_hui = timezone.now().date()
                mois_ecoules = 0
                
                if avance.mois_debut_couverture:
                    mois_ecoules = ((aujourd_hui.year - avance.mois_debut_couverture.year) * 12 +
                                   (aujourd_hui.month - avance.mois_debut_couverture.month))
                    
                    # Si on est au 20 du mois ou plus, considérer qu'un mois s'est écoulé
                    if aujourd_hui.day >= 20:
                        mois_ecoules += 1
                
                # Calculer combien de mois devraient être consommés selon la logique du 20
                # Un mois n'est consommé que si on est au 20 du mois ou plus
                mois_devraient_etre_consommes = 0
                if mois_ecoules > 0:
                    # Vérifier si on est au 20 du mois ou plus pour le mois actuel
                    if aujourd_hui.day >= 20:
                        mois_devraient_etre_consommes = min(mois_ecoules, avance.nombre_mois_couverts)
                    else:
                        # Si on n'est pas au 20, ne consommer que les mois précédents
                        mois_devraient_etre_consommes = min(mois_ecoules - 1, avance.nombre_mois_couverts)
                        mois_devraient_etre_consommes = max(0, mois_devraient_etre_consommes)
                
                # Calculer combien de mois ont déjà été consommés
                mois_deja_consommes = ConsommationAvance.objects.filter(avance=avance).count()
                
                # Consommer les mois manquants
                mois_a_consommer = mois_devraient_etre_consommes - mois_deja_consommes
                
                for i in range(mois_a_consommer):
                    mois_a_consommer_date = avance.mois_debut_couverture + relativedelta(months=mois_deja_consommes + i)
                    
                    # Vérifier si ce mois est dans la période de couverture
                    if (avance.mois_debut_couverture <= mois_a_consommer_date <= avance.mois_fin_couverture):
                        # Consommer ce mois
                        if avance.consommer_mois(mois_a_consommer_date):
                            # Créer l'enregistrement de consommation
                            ConsommationAvance.objects.create(
                                avance=avance,
                                paiement=None,  # Consommation automatique
                                mois_consomme=mois_a_consommer_date,
                                montant_consomme=avance.loyer_mensuel,
                                montant_restant_apres=avance.montant_restant
                            )
                            
                            # Mettre à jour le statut si l'avance est épuisée
                            if avance.montant_restant <= 0:
                                avance.statut = 'epuisee'
                                avance.save()
                
        except Exception as e:
            print(f"Erreur lors de la synchronisation des consommations: {str(e)}")
            # Ne pas lever l'exception pour ne pas bloquer le processus principal
    
    @staticmethod
    def calculer_montant_du_mois(contrat, mois):
        """
        Calcule le montant dû pour un mois en tenant compte des avances
        Synchronise automatiquement les consommations avant le calcul
        """
        try:
            # D'abord, synchroniser toutes les consommations manquantes
            ServiceGestionAvance.synchroniser_consommations_manquantes(contrat)
            
            # Montant du loyer mensuel (conversion en Decimal)
            loyer_mensuel = Decimal(str(contrat.loyer_mensuel)) if contrat.loyer_mensuel else Decimal('0')
            charges_mensuelles = Decimal(str(contrat.charges_mensuelles)) if contrat.charges_mensuelles else Decimal('0')
            montant_total_du = loyer_mensuel + charges_mensuelles
            
            # Vérifier s'il y a des avances disponibles pour ce mois
            avance_disponible, montant_avance = ServiceGestionAvance.consommer_avance_pour_mois(contrat, mois)
            
            if avance_disponible:
                montant_restant = montant_total_du - montant_avance
                return max(montant_restant, Decimal('0')), montant_avance
            else:
                return montant_total_du, Decimal('0')
                
        except Exception as e:
            raise Exception(f"Erreur lors du calcul du montant dû: {str(e)}")
    
    @staticmethod
    def synchroniser_toutes_avances():
        """
        Synchronise toutes les avances de tous les contrats
        À appeler périodiquement pour maintenir la cohérence
        """
        try:
            from contrats.models import Contrat
            
            contrats_avec_avances = Contrat.objects.filter(avances_loyer__isnull=False).distinct()
            total_synchronise = 0
            
            for contrat in contrats_avec_avances:
                try:
                    ServiceGestionAvance.synchroniser_consommations_manquantes(contrat)
                    total_synchronise += 1
                except Exception as e:
                    print(f"Erreur lors de la synchronisation du contrat {contrat.id}: {str(e)}")
                    continue
            
            return {
                'success': True,
                'contrats_traites': total_synchronise,
                'message': f'{total_synchronise} contrats synchronisés'
            }
            
        except Exception as e:
            return {
                'success': False,
                'erreur': str(e)
            }
    
    @staticmethod
    def traiter_paiement_mensuel(paiement):
        """
        Traite un paiement mensuel en tenant compte des avances
        """
        try:
            with transaction.atomic():
                contrat = paiement.contrat
                mois_paiement = paiement.date_paiement.replace(day=1)
                
                # Calculer le montant dû et l'avance utilisée
                montant_du, montant_avance_utilisee = ServiceGestionAvance.calculer_montant_du_mois(
                    contrat, mois_paiement
                )
                
                # Mettre à jour le paiement
                paiement.montant_du_mois = montant_du + montant_avance_utilisee
                paiement.montant_restant_du = max(montant_du - paiement.montant, Decimal('0'))
                
                # Créer ou mettre à jour l'historique
                historique, created = HistoriquePaiement.objects.get_or_create(
                    contrat=contrat,
                    mois_paiement=mois_paiement,
                    defaults={
                        'paiement': paiement,
                        'montant_paye': paiement.montant,
                        'montant_du': paiement.montant_du_mois,
                        'montant_avance_utilisee': montant_avance_utilisee,
                        'montant_restant_du': paiement.montant_restant_du,
                        'mois_regle': paiement.montant_restant_du <= 0
                    }
                )
                
                if not created:
                    # Mettre à jour l'historique existant
                    historique.paiement = paiement
                    historique.montant_paye += paiement.montant
                    historique.montant_avance_utilisee += montant_avance_utilisee
                    historique.montant_restant_du = max(historique.montant_du - historique.montant_paye, Decimal('0'))
                    historique.mois_regle = historique.montant_restant_du <= 0
                    historique.save()
                
                # Mettre à jour la consommation d'avance si applicable
                if montant_avance_utilisee > 0:
                    consommation = ConsommationAvance.objects.filter(
                        avance__contrat=contrat,
                        mois_consomme=mois_paiement
                    ).first()
                    
                    if consommation:
                        consommation.paiement = paiement
                        consommation.save()
                
                return historique
                
        except Exception as e:
            raise Exception(f"Erreur lors du traitement du paiement mensuel: {str(e)}")
    
    @staticmethod
    def get_avances_actives_contrat(contrat):
        """
        Retourne les avances actives pour un contrat
        """
        return AvanceLoyer.objects.filter(
            contrat=contrat,
            statut='active'
        ).order_by('-date_avance')
    
    @staticmethod
    def get_historique_paiements_contrat(contrat, mois_debut=None, mois_fin=None):
        """
        Retourne l'historique des paiements pour un contrat
        """
        queryset = HistoriquePaiement.objects.filter(contrat=contrat)
        
        if mois_debut:
            queryset = queryset.filter(mois_paiement__gte=mois_debut)
        
        if mois_fin:
            queryset = queryset.filter(mois_paiement__lte=mois_fin)
        
        return queryset.order_by('-mois_paiement')
    
    @staticmethod
    def get_statut_avances_contrat(contrat):
        """
        Retourne le statut des avances pour un contrat
        """
        avances_actives = ServiceGestionAvance.get_avances_actives_contrat(contrat)
        
        total_avance = sum(avance.montant_restant for avance in avances_actives)
        total_mois_couverts = sum(avance.nombre_mois_couverts for avance in avances_actives)
        
        return {
            'nombre_avances_actives': avances_actives.count(),
            'total_avance_restante': total_avance,
            'total_mois_couverts': total_mois_couverts,
            'avances': avances_actives
        }
    
    @staticmethod
    def generer_rapport_avances_contrat(contrat, mois_debut=None, mois_fin=None):
        """
        Génère un rapport détaillé des avances pour un contrat
        """
        # Récupérer les données
        avances = ServiceGestionAvance.get_avances_actives_contrat(contrat)
        
        # Calculer la période réelle de couverture des avances
        periode_debut = None
        periode_fin = None
        
        if avances:
            # Trouver la date de début la plus ancienne
            dates_debut = [avance.mois_debut_couverture for avance in avances if avance.mois_debut_couverture]
            if dates_debut:
                periode_debut = min(dates_debut)
            
            # Trouver la date de fin la plus récente
            dates_fin = [avance.mois_fin_couverture for avance in avances if avance.mois_fin_couverture]
            if dates_fin:
                periode_fin = max(dates_fin)
        
        # Si pas de période calculée, utiliser les paramètres par défaut
        if not periode_debut:
            if not mois_debut:
                periode_debut = date.today().replace(day=1) - relativedelta(months=12)
            else:
                periode_debut = mois_debut
        
        if not periode_fin:
            if not mois_fin:
                periode_fin = date.today().replace(day=1)
            else:
                periode_fin = mois_fin
        
        # Récupérer l'historique des paiements pour la période calculée
        historique = ServiceGestionAvance.get_historique_paiements_contrat(contrat, periode_debut, periode_fin)
        
        # Calculer les statistiques
        total_avances_versees = sum(avance.montant_avance for avance in avances)
        total_avances_consommees = sum(avance.montant_avance - avance.montant_restant for avance in avances)
        total_avances_restantes = sum(avance.montant_restant for avance in avances)
        
        return {
            'contrat': contrat,
            'periode': {
                'debut': periode_debut,
                'fin': periode_fin
            },
            'avances': avances,
            'historique': historique,
            'statistiques': {
                'total_avances_versees': total_avances_versees,
                'total_avances_consommees': total_avances_consommees,
                'total_avances_restantes': total_avances_restantes,
                'nombre_mois_couverts': sum(avance.nombre_mois_couverts for avance in avances)
            }
        }

    @staticmethod
    def calculer_prochain_mois_paiement(contrat):
        """
        Calcule le prochain mois où un paiement sera dû en tenant compte de toutes les avances
        CORRIGÉ : Utilise le mois_paye si disponible, sinon date_paiement
        """
        try:
            from datetime import datetime
            import re
            
            # Récupérer le dernier paiement de loyer validé (pas d'avance)
            try:
                from .models import Paiement
                dernier_paiement = Paiement.objects.filter(
                    contrat=contrat,
                    type_paiement='loyer',
                    statut='valide',
                    is_deleted=False
                ).order_by('-date_paiement').first()
            except ImportError:
                dernier_paiement = None
            
            # Fonction pour convertir mois_paye (ex: "Novembre 2024") en date
            def convertir_mois_paye_en_date(mois_paye_str):
                """Convertit 'Novembre 2024' ou 'November 2024' en date"""
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
                
                # Extraire mois et année
                mois_paye_lower = mois_paye_str.lower().strip()
                for mois, num in {**mois_francais, **mois_anglais}.items():
                    if mois in mois_paye_lower:
                        # Extraire l'année
                        annee_match = re.search(r'(\d{4})', mois_paye_str)
                        if annee_match:
                            annee = int(annee_match.group(1))
                            return timezone.now().date().replace(year=annee, month=num, day=1)
                return None
            
            # Déterminer le dernier mois payé
            dernier_mois_paye = None
            if dernier_paiement:
                # Priorité au mois_paye si disponible
                if dernier_paiement.mois_paye:
                    dernier_mois_paye = convertir_mois_paye_en_date(dernier_paiement.mois_paye)
                
                # Sinon utiliser date_paiement
                if not dernier_mois_paye:
                    dernier_mois_paye = dernier_paiement.date_paiement.replace(day=1)
            
            # Récupérer seulement les avances actives qui ont encore du montant restant
            avances_actives = AvanceLoyer.objects.filter(
                contrat=contrat,
                statut='active',
                montant_restant__gt=0  # Seulement les avances qui ont encore de l'argent
            )
            
            if not avances_actives.exists():
                # *** PAS D'AVANCES : Prochain paiement = mois suivant le dernier paiement ***
                if dernier_mois_paye:
                    return dernier_mois_paye + relativedelta(months=1)
                else:
                    # Pas de paiement précédent, prochain paiement = mois prochain
                    return timezone.now().date().replace(day=1) + relativedelta(months=1)
            
            # *** AVEC AVANCES : Calculer le prochain mois en tenant compte des avances ***
            # Calculer le nombre total de mois couverts par les avances
            total_mois_couverts = sum(avance.nombre_mois_couverts for avance in avances_actives)
            
            if total_mois_couverts <= 0:
                # Avances épuisées, revenir au calcul normal
                if dernier_mois_paye:
                    return dernier_mois_paye + relativedelta(months=1)
                else:
                    return timezone.now().date().replace(day=1) + relativedelta(months=1)
            
            # *** LOGIQUE CORRIGÉE : Calculer le prochain mois après consommation des avances ***
            # Trouver le mois de début de couverture le plus récent
            mois_debut_couverture = max(avance.mois_debut_couverture for avance in avances_actives)
            
            # Le prochain paiement = mois de début + nombre de mois couverts
            prochain_mois = mois_debut_couverture + relativedelta(months=total_mois_couverts)
            
            return prochain_mois
            
        except Exception as e:
            print(f"Erreur calcul prochain mois: {str(e)}")
            import traceback
            traceback.print_exc()
            # En cas d'erreur, retourner le mois prochain
            return timezone.now().date().replace(day=1) + relativedelta(months=1)

    @staticmethod
    def calculer_mois_couverts_par_avances(contrat):
        """
        Calcule le nombre total de mois couverts par toutes les avances actives
        """
        try:
            avances_actives = AvanceLoyer.objects.filter(
                contrat=contrat,
                statut='active'
            )
            
            total_mois = 0
            for avance in avances_actives:
                total_mois += avance.nombre_mois_couverts
            
            return total_mois
            
        except Exception as e:
            return 0

    @staticmethod
    def calculer_date_expiration_avances(contrat):
        """
        Calcule la date d'expiration de toutes les avances (la plus tardive)
        """
        try:
            avances_actives = AvanceLoyer.objects.filter(
                contrat=contrat,
                statut='active'
            )
            
            if not avances_actives.exists():
                return None
            
            # Trouver la date d'expiration la plus tardive
            date_expiration_max = None
            for avance in avances_actives:
                if avance.mois_fin_couverture:
                    if date_expiration_max is None or avance.mois_fin_couverture > date_expiration_max:
                        date_expiration_max = avance.mois_fin_couverture
            
            return date_expiration_max
            
        except Exception as e:
            return None
