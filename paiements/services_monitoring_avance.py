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