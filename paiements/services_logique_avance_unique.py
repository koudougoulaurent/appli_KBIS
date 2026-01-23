"""
Service Centralisé pour la Logique Unique des Avances
======================================================

Ce service contient LA SEULE ET UNIQUE logique pour :
1. Déterminer le mois de début de couverture d'une nouvelle avance
2. Calculer les mois de fin de couverture
3. Synchroniser avec le système de paiement

RÈGLE MÉTIER ABSOLUE :
- Une nouvelle avance commence TOUJOURS au premier mois NON PAYÉ et NON COUVERT
- Le calcul doit tenir compte :
  * Des paiements de loyer existants
  * Des avances existantes et leurs mois de couverture
  * Du contexte du contrat

"""
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from .models import Paiement
from .models_avance import AvanceLoyer
from contrats.models import Contrat


class ServiceLogiqueAvanceUnique:
    """
    Service centralisé pour TOUTE la logique des avances.
    C'est le SEUL endroit où la logique métier est définie.
    """
    
    @staticmethod
    def determiner_mois_debut_couverture_nouvelle_avance(contrat, date_avance=None):
        """
        Détermine le mois de début de couverture pour une NOUVELLE avance.
        
        LOGIQUE MÉTIER (UNIQUE ET CENTRALISÉE) :
        
        1. Trouver le dernier mois PAYÉ OU COUVERT :
           a) Chercher le dernier paiement de loyer validé
           b) Chercher la dernière avance active et son mois_fin_couverture
           c) Prendre le plus récent des deux
        
        2. Nouvelle avance commence au mois SUIVANT le dernier mois payé/couvert
        
        3. Si aucun paiement ni avance : utiliser date de début du contrat
        
        Args:
            contrat: Contrat concerné
            date_avance: Date du paiement d'avance (optionnel, pour logging)
        
        Returns:
            date: Mois de début de couverture (1er du mois)
        """
        print(f"\n{'='*80}")
        print(f"DÉTERMINATION MOIS DÉBUT COUVERTURE - Contrat #{contrat.id}")
        print(f"{'='*80}")
        
        # 1. Chercher le dernier paiement de loyer
        dernier_paiement_loyer = Paiement.objects.filter(
            contrat=contrat,
            type_paiement='loyer',
            statut='valide',
            is_deleted=False
        ).order_by('-date_paiement').first()
        
        dernier_mois_paiement = None
        if dernier_paiement_loyer:
            # Utiliser mois_paye si disponible (plus précis)
            if dernier_paiement_loyer.mois_paye:
                from .services_paiement_partiel import convertir_mois_paye_en_date
                dernier_mois_paiement = convertir_mois_paye_en_date(dernier_paiement_loyer.mois_paye)
            else:
                dernier_mois_paiement = dernier_paiement_loyer.date_paiement.replace(day=1)
            
            print(f"✓ Dernier paiement de loyer trouvé:")
            print(f"  - ID: {dernier_paiement_loyer.id}")
            print(f"  - Date: {dernier_paiement_loyer.date_paiement}")
            print(f"  - Mois payé: {dernier_mois_paiement}")
        
        # 2. Chercher la dernière avance active
        derniere_avance = AvanceLoyer.objects.filter(
            contrat=contrat,
            statut='active',
            mois_fin_couverture__isnull=False
        ).order_by('-mois_fin_couverture').first()
        
        dernier_mois_avance = None
        if derniere_avance:
            dernier_mois_avance = derniere_avance.mois_fin_couverture
            print(f"✓ Dernière avance active trouvée:")
            print(f"  - ID: {derniere_avance.id}")
            print(f"  - Montant: {derniere_avance.montant_avance} F CFA")
            print(f"  - Mois fin couverture: {dernier_mois_avance}")
        
        # 3. Prendre le plus récent
        dernier_mois_couvert = None
        
        if dernier_mois_paiement and dernier_mois_avance:
            # Comparer les deux et prendre le plus récent
            if dernier_mois_avance > dernier_mois_paiement:
                dernier_mois_couvert = dernier_mois_avance
                print(f"→ Mois le plus récent: AVANCE ({dernier_mois_avance})")
            else:
                dernier_mois_couvert = dernier_mois_paiement
                print(f"→ Mois le plus récent: PAIEMENT ({dernier_mois_paiement})")
        elif dernier_mois_paiement:
            dernier_mois_couvert = dernier_mois_paiement
            print(f"→ Mois le plus récent: PAIEMENT SEULEMENT ({dernier_mois_paiement})")
        elif dernier_mois_avance:
            dernier_mois_couvert = dernier_mois_avance
            print(f"→ Mois le plus récent: AVANCE SEULEMENT ({dernier_mois_avance})")
        
        # 4. Calculer le mois de début
        if dernier_mois_couvert:
            # Nouvelle avance commence au mois SUIVANT le dernier mois couvert
            mois_debut = dernier_mois_couvert + relativedelta(months=1)
            print(f"\n✓ MOIS DÉBUT COUVERTURE: {mois_debut}")
            print(f"  (= Dernier mois couvert {dernier_mois_couvert} + 1 mois)")
        else:
            # Aucun paiement ni avance : utiliser date de début du contrat
            if hasattr(contrat, 'date_debut') and contrat.date_debut:
                mois_debut = contrat.date_debut.replace(day=1)
                print(f"\n✓ MOIS DÉBUT COUVERTURE: {mois_debut}")
                print(f"  (= Date début contrat, aucun paiement antérieur)")
            elif hasattr(contrat, 'date_entree') and contrat.date_entree:
                mois_debut = contrat.date_entree.replace(day=1)
                print(f"\n✓ MOIS DÉBUT COUVERTURE: {mois_debut}")
                print(f"  (= Date entrée contrat, aucun paiement antérieur)")
            else:
                # Fallback : mois actuel
                mois_debut = timezone.now().date().replace(day=1)
                print(f"\n✓ MOIS DÉBUT COUVERTURE: {mois_debut}")
                print(f"  (= Mois actuel, fallback)")
        
        print(f"{'='*80}\n")
        
        return mois_debut
    
    @staticmethod
    def calculer_nombre_mois_couverts(montant_avance, loyer_mensuel):
        """
        Calcule le nombre de mois couverts par une avance.
        
        LOGIQUE :
        - Nombre de mois = montant_avance // loyer_mensuel
        - Au minimum 1 mois
        - Si reste > 50% du loyer, on compte un mois supplémentaire
        
        Args:
            montant_avance: Montant de l'avance (Decimal)
            loyer_mensuel: Loyer mensuel du contrat (Decimal)
        
        Returns:
            tuple: (nombre_mois_couverts, montant_reste)
        """
        if not isinstance(montant_avance, Decimal):
            montant_avance = Decimal(str(montant_avance))
        if not isinstance(loyer_mensuel, Decimal):
            loyer_mensuel = Decimal(str(loyer_mensuel))
        
        if loyer_mensuel <= 0:
            raise ValueError("Loyer mensuel invalide (doit être > 0)")
        
        # Calculer le nombre de mois complets
        mois_complets = int(montant_avance // loyer_mensuel)
        
        # Calculer le reste
        reste = montant_avance % loyer_mensuel
        
        # Si le reste est significatif (> 50% du loyer), compter un mois partiel
        # Note: Cette logique peut être ajustée selon les règles métier
        if reste > (loyer_mensuel * Decimal('0.5')):
            mois_complets += 1
        
        # Au minimum 1 mois
        nombre_mois = max(1, mois_complets)
        
        print(f"\nCALCUL MOIS COUVERTS:")
        print(f"  Montant avance: {montant_avance} F CFA")
        print(f"  Loyer mensuel: {loyer_mensuel} F CFA")
        print(f"  Mois complets: {mois_complets}")
        print(f"  Reste: {reste} F CFA")
        print(f"  → TOTAL MOIS COUVERTS: {nombre_mois}")
        
        return nombre_mois, reste
    
    @staticmethod
    def calculer_mois_fin_couverture(mois_debut, nombre_mois_couverts):
        """
        Calcule le mois de fin de couverture.
        
        LOGIQUE :
        - mois_fin = mois_debut + (nombre_mois_couverts - 1)
        
        Exemple :
        - Début : janvier 2026
        - Nombre de mois : 3
        - Fin : mars 2026 (janvier + 2 mois)
        
        Args:
            mois_debut: Date de début (1er du mois)
            nombre_mois_couverts: Nombre de mois couverts
        
        Returns:
            date: Mois de fin de couverture (1er du mois)
        """
        if nombre_mois_couverts <= 0:
            return mois_debut
        
        mois_fin = mois_debut + relativedelta(months=nombre_mois_couverts - 1)
        
        print(f"\nCALCUL MOIS FIN COUVERTURE:")
        print(f"  Mois début: {mois_debut}")
        print(f"  Nombre de mois: {nombre_mois_couverts}")
        print(f"  → MOIS FIN: {mois_fin}")
        
        return mois_fin
    
    @staticmethod
    def creer_avance_avec_logique_unique(contrat, montant_avance, date_avance, notes='', paiement=None):
        """
        Crée une avance en utilisant LA LOGIQUE UNIQUE.
        
        Args:
            contrat: Contrat concerné
            montant_avance: Montant de l'avance
            date_avance: Date du paiement d'avance
            notes: Notes optionnelles
            paiement: Paiement associé (optionnel)
        
        Returns:
            AvanceLoyer: L'avance créée
        """
        with transaction.atomic():
            print(f"\n{'='*80}")
            print(f"CRÉATION AVANCE AVEC LOGIQUE UNIQUE")
            print(f"{'='*80}")
            print(f"Contrat: #{contrat.id} - {contrat.locataire.get_nom_complet()}")
            print(f"Montant: {montant_avance} F CFA")
            print(f"Date: {date_avance}")
            
            # Convertir en Decimal
            if not isinstance(montant_avance, Decimal):
                montant_avance = Decimal(str(montant_avance))
            
            loyer_mensuel = Decimal(str(contrat.loyer_mensuel)) if contrat.loyer_mensuel else Decimal('0')
            
            if loyer_mensuel <= 0:
                raise ValueError("Le loyer mensuel du contrat n'est pas défini ou invalide")
            
            # 1. Déterminer le mois de début (LOGIQUE UNIQUE)
            mois_debut = ServiceLogiqueAvanceUnique.determiner_mois_debut_couverture_nouvelle_avance(
                contrat, date_avance
            )
            
            # 2. Calculer le nombre de mois couverts
            nombre_mois, reste = ServiceLogiqueAvanceUnique.calculer_nombre_mois_couverts(
                montant_avance, loyer_mensuel
            )
            
            # 3. Calculer le mois de fin
            mois_fin = ServiceLogiqueAvanceUnique.calculer_mois_fin_couverture(
                mois_debut, nombre_mois
            )
            
            # 4. Créer l'avance
            avance = AvanceLoyer.objects.create(
                contrat=contrat,
                montant_avance=montant_avance,
                loyer_mensuel=loyer_mensuel,
                nombre_mois_couverts=nombre_mois,
                montant_restant=montant_avance,
                montant_reste=reste,
                date_avance=date_avance,
                mois_debut_couverture=mois_debut,
                mois_fin_couverture=mois_fin,
                statut='active',
                notes=notes,
                paiement=paiement,
                mode_selection_mois='automatique'
            )
            
            print(f"\n✓ AVANCE CRÉÉE AVEC SUCCÈS:")
            print(f"  - ID: {avance.id}")
            print(f"  - Période: {mois_debut} → {mois_fin}")
            print(f"  - Mois couverts: {nombre_mois}")
            print(f"  - Reste: {reste} F CFA")
            print(f"{'='*80}\n")
            
            return avance
    
    @staticmethod
    def synchroniser_avance_existante(avance):
        """
        Resynchronise une avance existante avec la logique unique.
        
        ATTENTION : Ne modifie PAS le mois de début si l'avance a déjà été créée.
        Recalcule seulement le nombre de mois et le mois de fin.
        
        Args:
            avance: AvanceLoyer à resynchroniser
        
        Returns:
            AvanceLoyer: L'avance mise à jour
        """
        with transaction.atomic():
            print(f"\nRESYNCHRONISATION AVANCE #{avance.id}")
            
            loyer_mensuel = Decimal(str(avance.contrat.loyer_mensuel)) if avance.contrat.loyer_mensuel else Decimal('0')
            montant_avance = Decimal(str(avance.montant_avance))
            
            if loyer_mensuel <= 0:
                print(f"  ⚠️ Loyer mensuel invalide, skip")
                return avance
            
            # Recalculer le nombre de mois
            nombre_mois, reste = ServiceLogiqueAvanceUnique.calculer_nombre_mois_couverts(
                montant_avance, loyer_mensuel
            )
            
            # Recalculer le mois de fin (en gardant le mois de début existant)
            mois_fin = ServiceLogiqueAvanceUnique.calculer_mois_fin_couverture(
                avance.mois_debut_couverture, nombre_mois
            )
            
            # Mettre à jour
            avance.loyer_mensuel = loyer_mensuel
            avance.nombre_mois_couverts = nombre_mois
            avance.montant_reste = reste
            avance.mois_fin_couverture = mois_fin
            avance.save()
            
            print(f"  ✓ Resynchronisée: {avance.mois_debut_couverture} → {mois_fin} ({nombre_mois} mois)")
            
            return avance
    
    @staticmethod
    def get_prochain_mois_a_payer(contrat):
        """
        Détermine le prochain mois à payer pour un contrat.
        
        LOGIQUE (cohérente avec determiner_mois_debut_couverture_nouvelle_avance) :
        1. Trouver le dernier mois PAYÉ OU COUVERT
        2. Prochain mois = dernier mois + 1
        3. Vérifier que ce mois n'est PAS déjà couvert par une avance
        
        Returns:
            date: Prochain mois à payer (1er du mois)
        """
        # Utiliser la même logique que pour le début de couverture
        # Car le prochain mois à payer = le premier mois non couvert
        return ServiceLogiqueAvanceUnique.determiner_mois_debut_couverture_nouvelle_avance(contrat)
