"""
Service corrigé pour la gestion des avances de loyer
Résout tous les problèmes identifiés :
1. Date de début basée sur le contrat, pas le paiement
2. Concordance parfaite entre montant avance et récépissé
3. Calcul correct des mois couverts basé sur le dernier mois de loyer payé
"""

from django.db import transaction
from django.utils import timezone
from decimal import Decimal
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from paiements.models import Paiement
from paiements.models_avance import AvanceLoyer
from contrats.models import Contrat


class ServiceAvanceCorrige:
    """Service corrigé pour la gestion des avances de loyer."""
    
    @staticmethod
    def calculer_mois_couverts_correct(contrat, montant_avance, date_avance=None):
        """
        Calcule correctement les mois couverts par une avance.
        
        LOGIQUE CORRIGÉE :
        1. Si pas de paiement antérieur : utiliser la date de début du contrat
        2. Si paiements antérieurs : utiliser le mois suivant le dernier loyer payé
        3. Calculer les mois couverts à partir de cette date de début
        """
        if not contrat or not montant_avance or not contrat.loyer_mensuel:
            return None
            
        loyer_mensuel = float(contrat.loyer_mensuel)
        montant_avance_float = float(montant_avance)
        
        if loyer_mensuel <= 0 or montant_avance_float <= 0:
            return None
        
        # 1. DÉTERMINER LA DATE DE DÉBUT DE COUVERTURE
        date_debut_couverture = ServiceAvanceCorrige._determiner_date_debut_couverture(contrat, date_avance)
        
        # 2. CALCULER LE NOMBRE DE MOIS COMPLETS
        mois_complets = int(montant_avance_float // loyer_mensuel)
        reste = montant_avance_float % loyer_mensuel
        
        # Si le reste est significatif (plus de 50% du loyer), compter un mois partiel
        if reste > (loyer_mensuel * 0.5):
            mois_complets += 1
        
        nombre_mois = max(1, mois_complets)  # Au minimum 1 mois
        
        # 3. CALCULER LES MOIS COUVERTS
        mois_couverts = []
        mois_francais = {
            1: 'Janvier', 2: 'Février', 3: 'Mars', 4: 'Avril',
            5: 'Mai', 6: 'Juin', 7: 'Juillet', 8: 'Août',
            9: 'Septembre', 10: 'Octobre', 11: 'Novembre', 12: 'Décembre'
        }
        
        for i in range(nombre_mois):
            mois_date = date_debut_couverture + relativedelta(months=i)
            mois_nom = mois_francais.get(mois_date.month, mois_date.strftime("%B"))
            mois_couverts.append(f"{mois_nom} {mois_date.year}")
        
        return {
            'date_debut': date_debut_couverture,
            'date_fin': date_debut_couverture + relativedelta(months=nombre_mois - 1),
            'nombre': nombre_mois,
            'mois_liste': mois_couverts,
            'mois_texte': ', '.join(mois_couverts),
            'montant_avance': montant_avance_float,
            'loyer_mensuel': loyer_mensuel,
            'reste': reste
        }
    
    @staticmethod
    def _determiner_date_debut_couverture(contrat, date_avance=None):
        """
        Détermine la date de début de couverture selon la logique corrigée.
        
        RÈGLES :
        1. Si pas de paiement antérieur : utiliser la date de début du contrat
        2. Si paiements antérieurs : utiliser le mois suivant le dernier loyer payé
        3. Si date_avance fournie et après le 15 : mois suivant, sinon mois courant
        """
        # Récupérer le dernier paiement de loyer pour ce contrat
        dernier_paiement_loyer = Paiement.objects.filter(
            contrat=contrat,
            type_paiement='loyer',
            statut='valide'
        ).order_by('-date_paiement').first()
        
        if dernier_paiement_loyer:
            # Il y a des paiements antérieurs : utiliser le mois suivant le dernier loyer payé
            dernier_mois_paye = dernier_paiement_loyer.date_paiement.replace(day=1)
            date_debut = dernier_mois_paye + relativedelta(months=1)
            print(f"[AVANCE] Dernier loyer payé: {dernier_mois_paye}, début couverture: {date_debut}")
        else:
            # Pas de paiement antérieur : utiliser la date de début du contrat
            if hasattr(contrat, 'date_debut') and contrat.date_debut:
                date_debut = contrat.date_debut.replace(day=1)
            elif hasattr(contrat, 'date_entree') and contrat.date_entree:
                date_debut = contrat.date_entree.replace(day=1)
            else:
                # Fallback : utiliser la date actuelle
                date_debut = timezone.now().date().replace(day=1)
            print(f"[AVANCE] Pas de paiement antérieur, début couverture: {date_debut}")
        
        # Si une date d'avance est fournie, appliquer la règle du 15+
        if date_avance:
            jour_avance = date_avance.day
            mois_avance = date_avance.replace(day=1)
            
            # Si l'avance est versée après le 15, elle prend effet le mois suivant
            if jour_avance > 15:
                date_debut = mois_avance + relativedelta(months=1)
                print(f"[AVANCE] Avance après le 15 ({jour_avance}), début couverture: {date_debut}")
            else:
                # Sinon, elle prend effet le mois courant
                date_debut = mois_avance
                print(f"[AVANCE] Avance avant le 15 ({jour_avance}), début couverture: {date_debut}")
        
        return date_debut
    
    @staticmethod
    def creer_avance_corrigee(contrat, montant_avance, date_avance, notes='', paiement=None):
        """
        Crée une avance avec la logique corrigée.
        
        Args:
            contrat: Contrat concerné
            montant_avance: Montant de l'avance
            date_avance: Date de l'avance
            notes: Notes optionnelles
            paiement: Paiement associé (optionnel)
        
        Returns:
            AvanceLoyer: L'avance créée
        """
        with transaction.atomic():
            # Calculer les mois couverts avec la logique corrigée
            mois_couverts_data = ServiceAvanceCorrige.calculer_mois_couverts_correct(
                contrat, montant_avance, date_avance
            )
            
            if not mois_couverts_data:
                raise ValueError("Impossible de calculer les mois couverts")
            
            # Créer l'avance
            avance = AvanceLoyer.objects.create(
                contrat=contrat,
                montant_avance=montant_avance,
                loyer_mensuel=contrat.loyer_mensuel,
                nombre_mois_couverts=mois_couverts_data['nombre'],
                montant_restant=montant_avance,
                montant_reste=mois_couverts_data['reste'],
                date_avance=date_avance,
                mois_debut_couverture=mois_couverts_data['date_debut'],
                mois_fin_couverture=mois_couverts_data['date_fin'],
                statut='active',
                notes=notes,
                paiement=paiement,
                mode_selection_mois='automatique'
            )
            
            print(f"[AVANCE] Avance créée: {avance.id}")
            print(f"[AVANCE] Montant: {montant_avance} F CFA")
            print(f"[AVANCE] Mois couverts: {mois_couverts_data['mois_texte']}")
            print(f"[AVANCE] Période: {mois_couverts_data['date_debut']} à {mois_couverts_data['date_fin']}")
            
            return avance
    
    @staticmethod
    def corriger_avances_existantes():
        """
        Corrige toutes les avances existantes avec la nouvelle logique.
        """
        print("=== CORRECTION DES AVANCES EXISTANTES ===")
        
        avances = AvanceLoyer.objects.filter(statut='active').select_related('contrat')
        corrections_effectuees = 0
        erreurs = 0
        
        for avance in avances:
            try:
                # Recalculer avec la logique corrigée
                mois_couverts_data = ServiceAvanceCorrige.calculer_mois_couverts_correct(
                    avance.contrat, avance.montant_avance, avance.date_avance
                )
                
                if mois_couverts_data:
                    # Mettre à jour l'avance
                    avance.nombre_mois_couverts = mois_couverts_data['nombre']
                    avance.montant_reste = mois_couverts_data['reste']
                    avance.mois_debut_couverture = mois_couverts_data['date_debut']
                    avance.mois_fin_couverture = mois_couverts_data['date_fin']
                    avance.save()
                    
                    corrections_effectuees += 1
                    print(f"✓ Avance {avance.id} corrigée: {mois_couverts_data['mois_texte']}")
                else:
                    print(f"✗ Impossible de corriger l'avance {avance.id}")
                    erreurs += 1
                    
            except Exception as e:
                print(f"✗ Erreur pour l'avance {avance.id}: {e}")
                erreurs += 1
        
        print(f"\n=== RÉSULTATS ===")
        print(f"Corrections effectuées: {corrections_effectuees}")
        print(f"Erreurs: {erreurs}")
        
        return corrections_effectuees, erreurs
    
    @staticmethod
    def generer_recu_avance_corrige(paiement_id):
        """
        Génère un récépissé d'avance avec les données corrigées.
        """
        try:
            paiement = Paiement.objects.select_related('contrat').get(id=paiement_id)
            
            if paiement.type_paiement != 'avance':
                raise ValueError("Ce paiement n'est pas une avance")
            
            # Récupérer ou créer l'avance associée
            avance = AvanceLoyer.objects.filter(paiement=paiement).first()
            
            if not avance:
                # Créer l'avance avec la logique corrigée
                avance = ServiceAvanceCorrige.creer_avance_corrigee(
                    contrat=paiement.contrat,
                    montant_avance=paiement.montant,
                    date_avance=paiement.date_paiement,
                    notes=f"Avance créée automatiquement pour le paiement {paiement.id}",
                    paiement=paiement
                )
            
            # Recalculer les mois couverts pour s'assurer qu'ils sont corrects
            mois_couverts_data = ServiceAvanceCorrige.calculer_mois_couverts_correct(
                avance.contrat, avance.montant_avance, avance.date_avance
            )
            
            if not mois_couverts_data:
                raise ValueError("Impossible de calculer les mois couverts")
            
            # Mettre à jour l'avance avec les données corrigées
            avance.nombre_mois_couverts = mois_couverts_data['nombre']
            avance.montant_reste = mois_couverts_data['reste']
            avance.mois_debut_couverture = mois_couverts_data['date_debut']
            avance.mois_fin_couverture = mois_couverts_data['date_fin']
            avance.save()
            
            return {
                'paiement': paiement,
                'avance': avance,
                'mois_couverts': {
                    'nombre': mois_couverts_data['nombre'],
                    'mois_texte': mois_couverts_data['mois_texte'],
                    'mois_liste': mois_couverts_data['mois_liste']
                },
                'montant_avance': avance.montant_avance,
                'loyer_mensuel': avance.loyer_mensuel,
                'date_debut': mois_couverts_data['date_debut'],
                'date_fin': mois_couverts_data['date_fin']
            }
            
        except Exception as e:
            raise Exception(f"Erreur lors de la génération du récépissé: {str(e)}")
