"""
Service de monitoring des avances pour détecter la progression de consommation
"""
from django.utils import timezone
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from .models_avance import AvanceLoyer, ConsommationAvance
from .models import Paiement

class ServiceMonitoringAvance:
    """Service pour surveiller et analyser la progression des avances"""
    
    @staticmethod
    def analyser_progression_avances(contrat):
        """
        Analyse la progression de consommation des avances pour un contrat
        """
        try:
            # Récupérer toutes les avances du contrat
            avances = AvanceLoyer.objects.filter(contrat=contrat).order_by('date_avance')
            
            if not avances.exists():
                return {
                    'avances_trouvees': False,
                    'message': 'Aucune avance trouvée pour ce contrat'
                }
            
            resultats = {
                'avances_trouvees': True,
                'total_avances': avances.count(),
                'avances_actives': 0,
                'avances_epuisees': 0,
                'montant_total_avances': 0,
                'montant_restant_total': 0,
                'mois_couverts_total': 0,
                'mois_consommes_total': 0,
                'progression_globale': 0,
                'details_avances': []
            }
            
            for avance in avances:
                # Calculer les mois consommés
                mois_consommes = ConsommationAvance.objects.filter(avance=avance).count()
                
                # Calculer la progression
                progression = (mois_consommes / avance.nombre_mois_couverts * 100) if avance.nombre_mois_couverts > 0 else 0
                
                # Mettre à jour les totaux
                resultats['montant_total_avances'] += float(avance.montant_avance)
                resultats['montant_restant_total'] += float(avance.montant_restant)
                resultats['mois_couverts_total'] += avance.nombre_mois_couverts
                resultats['mois_consommes_total'] += mois_consommes
                
                if avance.statut == 'active':
                    resultats['avances_actives'] += 1
                elif avance.statut == 'epuisee':
                    resultats['avances_epuisees'] += 1
                
                # Détails de chaque avance
                resultats['details_avances'].append({
                    'id': avance.id,
                    'montant_avance': float(avance.montant_avance),
                    'montant_restant': float(avance.montant_restant),
                    'mois_couverts': avance.nombre_mois_couverts,
                    'mois_consommes': mois_consommes,
                    'progression': round(progression, 2),
                    'statut': avance.statut,
                    'date_avance': avance.date_avance,
                    'mois_debut': avance.mois_debut_couverture,
                    'mois_fin': avance.mois_fin_couverture
                })
            
            # Calculer la progression globale
            if resultats['mois_couverts_total'] > 0:
                resultats['progression_globale'] = round(
                    (resultats['mois_consommes_total'] / resultats['mois_couverts_total']) * 100, 2
                )
            
            return resultats
            
        except Exception as e:
            return {
                'avances_trouvees': False,
                'erreur': str(e)
            }
    
    @staticmethod
    def detecter_avances_a_consommer(contrat):
        """
        Détecte les avances qui devraient être consommées pour les mois passés
        """
        try:
            aujourd_hui = timezone.now().date()
            mois_actuel = aujourd_hui.replace(day=1)
            
            # Trouver les paiements de loyer des 6 derniers mois
            date_limite = mois_actuel - relativedelta(months=6)
            
            paiements_loyer = Paiement.objects.filter(
                contrat=contrat,
                type_paiement='loyer',
                statut='valide',
                date_paiement__gte=date_limite
            ).order_by('date_paiement')
            
            mois_payes = set()
            for paiement in paiements_loyer:
                mois_payes.add(paiement.date_paiement.replace(day=1))
            
            # Trouver les avances actives
            avances_actives = AvanceLoyer.objects.filter(
                contrat=contrat,
                statut='active'
            )
            
            avances_a_consommer = []
            
            for avance in avances_actives:
                if not avance.mois_debut_couverture or not avance.mois_fin_couverture:
                    continue
                
                # Vérifier chaque mois couvert par l'avance
                mois_courant = avance.mois_debut_couverture.replace(day=1)
                mois_fin = avance.mois_fin_couverture.replace(day=1)
                
                while mois_courant <= mois_fin and mois_courant < mois_actuel:
                    # Si ce mois n'a pas été payé et n'a pas été consommé
                    if mois_courant not in mois_payes:
                        # Vérifier si ce mois n'a pas déjà été consommé
                        deja_consomme = ConsommationAvance.objects.filter(
                            avance=avance,
                            mois_consomme=mois_courant
                        ).exists()
                        
                        if not deja_consomme:
                            avances_a_consommer.append({
                                'avance_id': avance.id,
                                'mois_a_consommer': mois_courant,
                                'montant': float(avance.loyer_mensuel)
                            })
                    
                    mois_courant = mois_courant + relativedelta(months=1)
            
            return {
                'avances_a_consommer': avances_a_consommer,
                'total_mois_a_consommer': len(avances_a_consommer),
                'montant_total_a_consommer': sum(a['montant'] for a in avances_a_consommer)
            }
            
        except Exception as e:
            return {
                'erreur': str(e),
                'avances_a_consommer': []
            }
    
    @staticmethod
    def consommer_avances_manquantes(contrat):
        """
        Consomme automatiquement les avances pour les mois qui n'ont pas été payés
        """
        try:
            from .services_avance import ServiceGestionAvance
            
            detection = ServiceMonitoringAvance.detecter_avances_a_consommer(contrat)
            
            if 'erreur' in detection:
                return detection
            
            avances_consommees = 0
            montant_total_consomme = 0
            
            for avance_info in detection['avances_a_consommer']:
                try:
                    # Trouver l'avance
                    avance = AvanceLoyer.objects.get(id=avance_info['avance_id'])
                    
                    # Consommer le mois
                    if avance.consommer_mois(avance_info['mois_a_consommer']):
                        # Créer l'enregistrement de consommation
                        ConsommationAvance.objects.create(
                            avance=avance,
                            paiement=None,
                            mois_consomme=avance_info['mois_a_consommer'],
                            montant_consomme=avance.loyer_mensuel,
                            montant_restant_apres=avance.montant_restant
                        )
                        
                        avances_consommees += 1
                        montant_total_consomme += float(avance.loyer_mensuel)
                        
                except Exception as e:
                    print(f"Erreur consommation avance {avance_info['avance_id']}: {str(e)}")
                    continue
            
            return {
                'success': True,
                'avances_consommees': avances_consommees,
                'montant_total_consomme': montant_total_consomme,
                'message': f'{avances_consommees} mois d\'avance consommés automatiquement'
            }
            
        except Exception as e:
            return {
                'success': False,
                'erreur': str(e)
            }
    
    @staticmethod
    def generer_rapport_progression():
        """
        Génère un rapport global de progression de toutes les avances
        """
        try:
            # Récupérer toutes les avances
            avances = AvanceLoyer.objects.select_related('contrat', 'contrat__locataire').all()
            
            if not avances.exists():
                return {
                    'total_avances': 0,
                    'avances_actives': 0,
                    'avances_epuisees': 0,
                    'montant_total_avances': 0,
                    'montant_restant_total': 0,
                    'progression_moyenne': 0,
                    'avances_critiques': 0,
                    'message': 'Aucune avance trouvée'
                }
            
            # Statistiques globales
            total_avances = avances.count()
            avances_actives = avances.filter(statut='active').count()
            avances_epuisees = avances.filter(statut='epuisee').count()
            
            montant_total_avances = sum(float(a.montant_avance) for a in avances)
            montant_restant_total = sum(float(a.montant_restant) for a in avances)
            
            # Calculer la progression moyenne
            progressions = []
            avances_critiques = 0
            
            for avance in avances:
                mois_consommes = ConsommationAvance.objects.filter(avance=avance).count()
                progression = (mois_consommes / avance.nombre_mois_couverts * 100) if avance.nombre_mois_couverts > 0 else 0
                progressions.append(progression)
                
                # Avance critique si progression > 80% et statut actif
                if progression > 80 and avance.statut == 'active':
                    avances_critiques += 1
            
            progression_moyenne = sum(progressions) / len(progressions) if progressions else 0
            
            return {
                'total_avances': total_avances,
                'avances_actives': avances_actives,
                'avances_epuisees': avances_epuisees,
                'montant_total_avances': round(montant_total_avances, 2),
                'montant_restant_total': round(montant_restant_total, 2),
                'progression_moyenne': round(progression_moyenne, 2),
                'avances_critiques': avances_critiques,
                'pourcentage_consomme': round(((montant_total_avances - montant_restant_total) / montant_total_avances * 100) if montant_total_avances > 0 else 0, 2)
            }
            
        except Exception as e:
            return {
                'erreur': str(e),
                'total_avances': 0
            }
    
    @staticmethod
    def detecter_avances_critiques():
        """
        Détecte les avances qui nécessitent une attention particulière
        """
        try:
            avances_critiques = []
            
            # Avances bientôt épuisées (progression > 80%)
            avances_actives = AvanceLoyer.objects.filter(statut='active')
            
            for avance in avances_actives:
                mois_consommes = ConsommationAvance.objects.filter(avance=avance).count()
                progression = (mois_consommes / avance.nombre_mois_couverts * 100) if avance.nombre_mois_couverts > 0 else 0
                
                if progression > 80:
                    avances_critiques.append({
                        'avance': avance,
                        'progression': round(progression, 2),
                        'type_alerte': 'bientot_epuisee',
                        'message': f'Avance {avance.id} bientôt épuisée ({progression:.1f}%)'
                    })
                
                # Avances expirées mais non consommées
                if avance.mois_fin_couverture and avance.mois_fin_couverture < timezone.now().date().replace(day=1):
                    if progression < 100:
                        avances_critiques.append({
                            'avance': avance,
                            'progression': round(progression, 2),
                            'type_alerte': 'expiree_non_consommee',
                            'message': f'Avance {avance.id} expirée mais non entièrement consommée'
                        })
            
            return avances_critiques
            
        except Exception as e:
            return []
    
    @staticmethod
    def analyser_progression_avance(avance):
        """
        Analyse détaillée de la progression d'une avance spécifique
        Basée sur les mois écoulés réels depuis le début de couverture
        """
        try:
            from dateutil.relativedelta import relativedelta
            
            # Calculer les mois consommés (enregistrements de consommation)
            mois_consommes = ConsommationAvance.objects.filter(avance=avance).count()

            # Calculer le montant réel consommé basé sur les enregistrements
            montant_consomme = sum(
                float(c.montant_consomme) for c in ConsommationAvance.objects.filter(avance=avance)
            )

            # Calculer les mois écoulés depuis le début de couverture
            aujourd_hui = timezone.now().date()
            mois_ecoules = 0
            
            if avance.mois_debut_couverture:
                # Calculer la différence en mois entre aujourd'hui et le début de couverture
                mois_ecoules = ((aujourd_hui.year - avance.mois_debut_couverture.year) * 12 +
                               (aujourd_hui.month - avance.mois_debut_couverture.month))
                
                # Si on est au 20 du mois ou plus, considérer qu'un mois s'est écoulé
                if aujourd_hui.day >= 20:
                    mois_ecoules += 1
            else:
                # Si pas de date de début, utiliser la date d'avance
                if avance.date_avance:
                    mois_ecoules = ((aujourd_hui.year - avance.date_avance.year) * 12 +
                                   (aujourd_hui.month - avance.date_avance.month))
                    if aujourd_hui.day >= 20:
                        mois_ecoules += 1

            # La progression réelle est basée sur les consommations enregistrées
            # Utiliser le nombre réel de consommations enregistrées
            mois_consommes_reels = mois_consommes
            
            # Calculer la progression basée sur les mois écoulés
            progression_reelle = (mois_consommes_reels / avance.nombre_mois_couverts * 100) if avance.nombre_mois_couverts > 0 else 0
            
            # Calculer le montant réel consommé basé sur les enregistrements de consommation
            montant_reel_consomme = sum(
                float(c.montant_consomme) for c in ConsommationAvance.objects.filter(avance=avance)
            )
            
            # Calculer le pourcentage réel basé sur le montant réel consommé
            pourcentage_reel = (montant_reel_consomme / float(avance.montant_avance) * 100) if avance.montant_avance > 0 else 0

            # Estimer les mois restants
            mois_restants_estimes = max(0, avance.nombre_mois_couverts - mois_consommes_reels)

            # Estimer la date d'expiration
            date_expiration_estimee = None
            if avance.mois_fin_couverture:
                date_expiration_estimee = avance.mois_fin_couverture
            elif avance.mois_debut_couverture:
                date_expiration_estimee = avance.mois_debut_couverture + relativedelta(months=avance.nombre_mois_couverts)

            # Déterminer le statut de progression basé sur la progression réelle
            if progression_reelle >= 100:
                statut_progression = 'epuisee'
            elif progression_reelle >= 80:
                statut_progression = 'critique'
            elif progression_reelle >= 50:
                statut_progression = 'en_cours'
            else:
                statut_progression = 'debut'

            return {
                'progression': round(progression_reelle, 2),
                'mois_consommes': mois_consommes_reels,
                'mois_ecoules': mois_ecoules,
                'mois_restants_estimes': mois_restants_estimes,
                'montant_reel_consomme': round(montant_reel_consomme, 2),
                'pourcentage_reel': round(pourcentage_reel, 2),
                'date_expiration_estimee': date_expiration_estimee,
                'statut_progression': statut_progression
            }

        except Exception as e:
            return {
                'erreur': str(e),
                'progression': 0,
                'mois_consommes': 0,
                'mois_ecoules': 0,
                'mois_restants_estimes': 0,
                'montant_reel_consomme': 0,
                'pourcentage_reel': 0,
                'statut_progression': 'erreur'
            }
    
    @staticmethod
    def synchroniser_consommations():
        """
        Synchronise automatiquement les consommations d'avances
        """
        try:
            contrats_avec_avances = AvanceLoyer.objects.values_list('contrat', flat=True).distinct()
            total_synchronise = 0
            
            for contrat_id in contrats_avec_avances:
                resultat = ServiceMonitoringAvance.consommer_avances_manquantes(contrat_id)
                if resultat.get('success', False):
                    total_synchronise += resultat.get('avances_consommees', 0)
            
            return {
                'success': True,
                'total_synchronise': total_synchronise,
                'message': f'{total_synchronise} mois d\'avance synchronisés'
            }
            
        except Exception as e:
            return {
                'success': False,
                'erreur': str(e)
            }
    
    @staticmethod
    def envoyer_alertes():
        """
        Envoie les alertes pour les avances critiques
        """
        try:
            avances_critiques = ServiceMonitoringAvance.detecter_avances_critiques()
            alertes_envoyees = 0
            
            for alerte in avances_critiques:
                # Ici, on pourrait intégrer un système d'envoi d'emails ou de notifications
                # Pour l'instant, on simule l'envoi
                print(f"ALERTE: {alerte['message']}")
                alertes_envoyees += 1
            
            return {
                'success': True,
                'alertes_envoyees': alertes_envoyees,
                'message': f'{alertes_envoyees} alertes envoyées'
            }
            
        except Exception as e:
            return {
                'success': False,
                'erreur': str(e)
            }