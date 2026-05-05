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
from django.conf import settings
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
    def determiner_mois_debut_couverture_nouvelle_avance(contrat, date_avance=None, avance_a_exclure=None):
        """
        Détermine le mois de début de couverture pour une NOUVELLE avance.
        
        LOGIQUE MÉTIER V10.2 (UNIQUE ET CENTRALISÉE) :
        
        1. Trouver le dernier mois PAYÉ OU COUVERT :
           a) Chercher le dernier paiement de loyer validé
           b) Chercher la dernière avance active et son mois_fin_couverture
           c) Prendre le plus récent des deux
        
        2. GESTION DES RETARDS DE PAIEMENT (NOUVEAU V10.2) :
           a) Si retard ≤ 2 mois : Avance couvre à partir du dernier paiement + 1
           b) Si retard > 2 mois : Avance commence au mois actuel (dettes restent à payer)
        
        3. Si aucun paiement ni avance : utiliser date de début du contrat
        
        Args:
            contrat: Contrat concerné
            date_avance: Date du paiement d'avance (optionnel, pour logging)
            avance_a_exclure: AvanceLoyer à exclure de la recherche (optionnel, pour correction)
        
        Returns:
            date: Mois de début de couverture (1er du mois)
        """
        if settings.DEBUG:
            print(f"\n{'='*80}")
            print(f"DÉTERMINATION MOIS DÉBUT COUVERTURE - Contrat #{contrat.id}")
            print(f"{'='*80}")
        
        # Fonction pour convertir mois_paye en date
        def convertir_mois_paye_en_date(mois_paye_str):
            """Convertit 'Novembre 2024' ou 'November 2024' en date."""
            if not mois_paye_str:
                return None
            
            from datetime import date
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
            
            mois_paye_lower = mois_paye_str.lower().strip()
            for mois, num in {**mois_francais, **mois_anglais}.items():
                if mois in mois_paye_lower:
                    annee_match = re.search(r'(\d{4})', mois_paye_str)
                    if annee_match:
                        annee = int(annee_match.group(1))
                        return date(annee, num, 1)
            return None
        
        # *** CORRECTION CRITIQUE : Trouver le DERNIER MOIS PAYÉ parmi TOUS les paiements ***
        # Ne pas se limiter aux paiements de type 'loyer', mais chercher tous les paiements avec mois_paye
        dernier_mois_paiement = None
        dernier_paiement_loyer = None
        
        # Récupérer TOUS les paiements avec mois_paye pour trouver le mois le plus récent
        # Exclure le paiement associé à l'avance qu'on corrige (si fourni)
        paiements_avec_mois = Paiement.objects.filter(
            contrat=contrat,
            statut='valide',
            is_deleted=False
        ).exclude(
            mois_paye__isnull=True
        ).exclude(
            mois_paye=''
        )
        if avance_a_exclure and avance_a_exclure.paiement:
            paiements_avec_mois = paiements_avec_mois.exclude(id=avance_a_exclure.paiement.id)
        
        # Convertir tous les mois_paye en dates et trouver le maximum
        mois_dates = []
        for paiement in paiements_avec_mois:
            mois_date = convertir_mois_paye_en_date(paiement.mois_paye)
            if mois_date:
                mois_dates.append((mois_date, paiement))
                # Garder aussi le dernier paiement de loyer pour l'affichage
                if paiement.type_paiement == 'loyer':
                    dernier_paiement_loyer = paiement
        
        if mois_dates:
            # Trouver le mois le plus récent
            dernier_mois_paiement, dernier_paiement_trouve = max(mois_dates, key=lambda x: x[0])
            # Si le dernier paiement trouvé est un loyer, le garder pour l'affichage
            if dernier_paiement_trouve.type_paiement == 'loyer':
                dernier_paiement_loyer = dernier_paiement_trouve
        
        # Si aucun paiement avec mois_paye, chercher le dernier paiement de loyer
        if not dernier_mois_paiement:
            dernier_paiement_loyer = Paiement.objects.filter(
                contrat=contrat,
                type_paiement='loyer',
                statut='valide',
                is_deleted=False
            ).order_by('-date_paiement').first()
            
            if dernier_paiement_loyer:
                dernier_mois_paiement = dernier_paiement_loyer.date_paiement.replace(day=1)
        
        if settings.DEBUG and dernier_paiement_loyer:
            print(f"✓ Dernier paiement de loyer trouvé:")
            print(f"  - ID: {dernier_paiement_loyer.id}")
            print(f"  - Date: {dernier_paiement_loyer.date_paiement}")
            print(f"  - Mois payé: {dernier_mois_paiement}")
        
        # 2. Chercher la dernière avance active (en excluant l'avance à corriger si fournie)
        queryset_avances = AvanceLoyer.objects.filter(
            contrat=contrat,
            statut='active',
            mois_fin_couverture__isnull=False
        )
        if avance_a_exclure:
            queryset_avances = queryset_avances.exclude(id=avance_a_exclure.id)
        derniere_avance = queryset_avances.order_by('-mois_fin_couverture').first()
        
        dernier_mois_avance = None
        if derniere_avance:
            dernier_mois_avance = derniere_avance.mois_fin_couverture
            if settings.DEBUG:
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
                if settings.DEBUG:
                    print(f"→ Mois le plus récent: AVANCE ({dernier_mois_avance})")
            else:
                dernier_mois_couvert = dernier_mois_paiement
                if settings.DEBUG:
                    print(f"→ Mois le plus récent: PAIEMENT ({dernier_mois_paiement})")
        elif dernier_mois_paiement:
            dernier_mois_couvert = dernier_mois_paiement
            if settings.DEBUG:
                print(f"→ Mois le plus récent: PAIEMENT SEULEMENT ({dernier_mois_paiement})")
        elif dernier_mois_avance:
            dernier_mois_couvert = dernier_mois_avance
            if settings.DEBUG:
                print(f"→ Mois le plus récent: AVANCE SEULEMENT ({dernier_mois_avance})")
        
        # 4. Calculer le mois de début (V10.2 - Option A : Toujours couvrir les dettes)
        if dernier_mois_couvert:
            # *** LOGIQUE OPTION A : L'avance couvre TOUJOURS à partir du dernier paiement ***
            # Pas de distinction retard acceptable/problématique
            # Simple et cohérent : dernier mois payé + 1 mois
            mois_debut = dernier_mois_couvert + relativedelta(months=1)
            
            # Afficher info si retard détecté
            if date_avance:
                mois_reference = date_avance.replace(day=1) if isinstance(date_avance, date) else timezone.now().date().replace(day=1)
            else:
                mois_reference = timezone.now().date().replace(day=1)
            
            ecart_mois = (mois_reference.year - dernier_mois_couvert.year) * 12 + \
                        (mois_reference.month - dernier_mois_couvert.month)
            
            if settings.DEBUG and ecart_mois > 1:
                print(f"\n📊 ANALYSE:")
                print(f"  Dernier mois couvert: {dernier_mois_couvert}")
                print(f"  Mois de référence: {mois_reference}")
                print(f"  Écart: {ecart_mois} mois")
                print(f"  → Avance couvre d'abord les {ecart_mois} mois de retard")
            
            if settings.DEBUG:
                print(f"\n✓ MOIS DÉBUT COUVERTURE: {mois_debut}")
                print(f"  (= Dernier mois couvert {dernier_mois_couvert} + 1 mois)")
        else:
            # Aucun paiement ni avance : utiliser date de début du contrat
            if hasattr(contrat, 'date_debut') and contrat.date_debut:
                mois_debut = contrat.date_debut.replace(day=1)
                if settings.DEBUG:
                    print(f"\n✓ MOIS DÉBUT COUVERTURE: {mois_debut}")
                    print(f"  (= Date début contrat, aucun paiement antérieur)")
            elif hasattr(contrat, 'date_entree') and contrat.date_entree:
                mois_debut = contrat.date_entree.replace(day=1)
                if settings.DEBUG:
                    print(f"\n✓ MOIS DÉBUT COUVERTURE: {mois_debut}")
                    print(f"  (= Date entrée contrat, aucun paiement antérieur)")
            else:
                # Fallback : mois actuel
                mois_debut = timezone.now().date().replace(day=1)
                if settings.DEBUG:
                    print(f"\n✓ MOIS DÉBUT COUVERTURE: {mois_debut}")
                    print(f"  (= Mois actuel, fallback)")
        
        if settings.DEBUG:
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
        
        # Autoriser 0 mois pour les paiements partiels (montant < loyer mensuel)
        nombre_mois = mois_complets
        
        if settings.DEBUG:
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
        
        LOGIQUE CORRECTE :
        - mois_fin = mois_debut + (nombre_mois_couverts - 1)
        
        Exemple :
        - Dernier mois payé : novembre 2025
        - Mois début : décembre 2025 (novembre + 1)
        - Nombre de mois : 3
        - Mois fin : février 2026 (décembre + 2 mois)
        - Mois couverts : décembre 2025, janvier 2026, février 2026 (3 mois)
        
        Args:
            mois_debut: Date de début (1er du mois) = Dernier mois payé + 1
            nombre_mois_couverts: Nombre de mois couverts par l'avance
        
        Returns:
            date: Mois de fin de couverture (1er du mois)
        """
        if nombre_mois_couverts <= 0:
            return mois_debut
        
        mois_fin = mois_debut + relativedelta(months=nombre_mois_couverts - 1)
        
        if settings.DEBUG:
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
            if settings.DEBUG:
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
            
            # *** VALIDATION CRITIQUE : Vérifier qu'aucun mois n'est sauté ***
            # IMPORTANT : Pour la validation, on doit trouver le DERNIER MOIS RÉELLEMENT PAYÉ (pas couvert par avance)
            # pour détecter les mois manquants entre les paiements réels
            dernier_mois_paye_reel = ServiceLogiqueAvanceUnique._get_dernier_mois_paye_reel(contrat)
            
            if dernier_mois_paye_reel:
                # Dictionnaire de traduction des mois en français
                mois_francais = {
                    1: 'Janvier', 2: 'Février', 3: 'Mars', 4: 'Avril',
                    5: 'Mai', 6: 'Juin', 7: 'Juillet', 8: 'Août',
                    9: 'Septembre', 10: 'Octobre', 11: 'Novembre', 12: 'Décembre'
                }
                
                # Vérifier tous les mois entre dernier_mois_paye_reel + 1 et mois_debut
                # On vérifie chaque mois pour s'assurer qu'il est soit payé soit couvert par une avance
                mois_manquants = []
                mois_courant = dernier_mois_paye_reel + relativedelta(months=1)
                
                while mois_courant < mois_debut:
                    # Vérifier si ce mois est payé ou couvert par une avance
                    mois_paye_ou_couvert = ServiceLogiqueAvanceUnique._verifier_mois_paye_ou_couvert(contrat, mois_courant)
                    
                    if not mois_paye_ou_couvert:
                        mois_nom = mois_francais.get(mois_courant.month, mois_courant.strftime('%B'))
                        mois_manquants.append(f"{mois_nom} {mois_courant.year}")
                    
                    mois_courant = mois_courant + relativedelta(months=1)
                
                # Si des mois sont manquants, lever une exception avec message clair
                if mois_manquants:
                    mois_manquants_str = ", ".join(mois_manquants)
                    dernier_mois_nom = mois_francais.get(dernier_mois_paye_reel.month, dernier_mois_paye_reel.strftime('%B'))
                    mois_debut_nom = mois_francais.get(mois_debut.month, mois_debut.strftime('%B'))
                    
                    raise ValueError(
                        f"❌ IMPOSSIBLE DE CRÉER CETTE AVANCE !\n\n"
                        f"⚠️ PROBLÈME : Vous tentez de créer une avance qui commence en {mois_debut_nom} {mois_debut.year}, "
                        f"mais les mois suivants n'ont PAS été payés :\n"
                        f"   • {mois_manquants_str}\n\n"
                        f"📋 CONTEXTE :\n"
                        f"   • Dernier mois réellement payé : {dernier_mois_nom} {dernier_mois_paye_reel.year}\n"
                        f"   • Mois de début de l'avance : {mois_debut_nom} {mois_debut.year}\n\n"
                        f"✅ SOLUTION :\n"
                        f"   1. Payez d'abord les mois manquants ({mois_manquants_str})\n"
                        f"   2. OU créez une avance qui commence en {mois_manquants[0]} pour couvrir les dettes\n\n"
                        f"💡 RAPPEL : Une avance doit TOUJOURS couvrir les mois en ordre chronologique, "
                        f"sans sauter de mois non payés."
                    )
            
            # 2. Calculer le nombre de mois couverts
            nombre_mois, reste = ServiceLogiqueAvanceUnique.calculer_nombre_mois_couverts(
                montant_avance, loyer_mensuel
            )
            
            # 3. Calculer le mois de fin
            if nombre_mois > 0:
                mois_fin = ServiceLogiqueAvanceUnique.calculer_mois_fin_couverture(
                    mois_debut, nombre_mois
                )
            else:
                # Paiement partiel : aucun mois complet couvert
                # mois_fin_couverture = None pour ne pas fausser le calcul du prochain mois
                mois_fin = None
            
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
            
            if settings.DEBUG:
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
            if settings.DEBUG:
                print(f"\nRESYNCHRONISATION AVANCE #{avance.id}")
            
            loyer_mensuel = Decimal(str(avance.contrat.loyer_mensuel)) if avance.contrat.loyer_mensuel else Decimal('0')
            montant_avance = Decimal(str(avance.montant_avance))
            
            if loyer_mensuel <= 0:
                if settings.DEBUG:
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
            
            if settings.DEBUG:
                print(f"  ✓ Resynchronisée: {avance.mois_debut_couverture} → {mois_fin} ({nombre_mois} mois)")
            
            return avance
    
    @staticmethod
    def _get_dernier_mois_couvert(contrat):
        """
        Retourne le dernier mois payé ou couvert par une avance.
        Utilise la même logique que determiner_mois_debut_couverture_nouvelle_avance.
        
        Returns:
            date: Dernier mois couvert (1er du mois) ou None
        """
        # Fonction pour convertir mois_paye en date
        def convertir_mois_paye_en_date(mois_paye_str):
            """Convertit 'Novembre 2024' ou 'November 2024' en date."""
            if not mois_paye_str:
                return None
            
            from datetime import date
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
            
            mois_paye_lower = mois_paye_str.lower().strip()
            for mois, num in {**mois_francais, **mois_anglais}.items():
                if mois in mois_paye_lower:
                    annee_match = re.search(r'(\d{4})', mois_paye_str)
                    if annee_match:
                        annee = int(annee_match.group(1))
                        return date(annee, num, 1)
            return None
        
        # Trouver le dernier mois payé
        dernier_mois_paiement = None
        paiements_avec_mois = Paiement.objects.filter(
            contrat=contrat,
            statut='valide',
            is_deleted=False
        ).exclude(
            mois_paye__isnull=True
        ).exclude(
            mois_paye=''
        )
        
        mois_dates = []
        for paiement in paiements_avec_mois:
            mois_date = convertir_mois_paye_en_date(paiement.mois_paye)
            if mois_date:
                mois_dates.append(mois_date)
        
        if mois_dates:
            dernier_mois_paiement = max(mois_dates)
        
        # Trouver le dernier mois couvert par une avance
        derniere_avance = AvanceLoyer.objects.filter(
            contrat=contrat,
            statut='active',
            mois_fin_couverture__isnull=False
        ).order_by('-mois_fin_couverture').first()
        
        dernier_mois_avance = None
        if derniere_avance:
            dernier_mois_avance = derniere_avance.mois_fin_couverture
        
        # Retourner le plus récent
        if dernier_mois_paiement and dernier_mois_avance:
            return max(dernier_mois_paiement, dernier_mois_avance)
        elif dernier_mois_paiement:
            return dernier_mois_paiement
        elif dernier_mois_avance:
            return dernier_mois_avance
        else:
            return None
    
    @staticmethod
    def _get_dernier_mois_paye_reel(contrat, avance_a_exclure=None):
        """
        Retourne le DERNIER MOIS RÉELLEMENT PAYÉ OU COUVERT.
        Considère :
        1. Les paiements directs (via Paiement avec mois_paye)
        2. Les mois consommés par des avances (via ConsommationAvance)
        
        IMPORTANT : Un mois consommé par une avance équivaut à un paiement réel.
        
        Args:
            contrat: Contrat concerné
            avance_a_exclure: AvanceLoyer à exclure de la recherche (optionnel)
        
        Returns:
            date: Dernier mois réellement payé/couvert (1er du mois) ou None
        """
        # Fonction pour convertir mois_paye en date
        def convertir_mois_paye_en_date(mois_paye_str):
            """Convertit 'Novembre 2024' ou 'November 2024' en date."""
            if not mois_paye_str:
                return None
            
            from datetime import date
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
            
            mois_paye_lower = mois_paye_str.lower().strip()
            for mois, num in {**mois_francais, **mois_anglais}.items():
                if mois in mois_paye_lower:
                    annee_match = re.search(r'(\d{4})', mois_paye_str)
                    if annee_match:
                        annee = int(annee_match.group(1))
                        return date(annee, num, 1)
            return None
        
        # 1. Trouver le dernier mois payé directement (via Paiement)
        # Exclure le paiement associé à l'avance qu'on corrige (si fourni)
        dernier_mois_paiement = None
        paiements_avec_mois = Paiement.objects.filter(
            contrat=contrat,
            statut='valide',
            is_deleted=False
        ).exclude(
            mois_paye__isnull=True
        ).exclude(
            mois_paye=''
        )
        if avance_a_exclure and avance_a_exclure.paiement:
            paiements_avec_mois = paiements_avec_mois.exclude(id=avance_a_exclure.paiement.id)
        
        mois_dates_paiements = []
        for paiement in paiements_avec_mois:
            mois_date = convertir_mois_paye_en_date(paiement.mois_paye)
            if mois_date:
                mois_dates_paiements.append(mois_date)
        
        if mois_dates_paiements:
            dernier_mois_paiement = max(mois_dates_paiements)
        
        # 2. Trouver le dernier mois consommé par une avance
        # Exclure les ConsommationAvance liées à l'avance qu'on corrige (si fourni)
        from .models_avance import ConsommationAvance
        dernier_mois_consomme = None
        queryset_consommations = ConsommationAvance.objects.filter(
            avance__contrat=contrat
        )
        if avance_a_exclure:
            queryset_consommations = queryset_consommations.exclude(avance=avance_a_exclure)
        consommations = queryset_consommations.order_by('-mois_consomme').first()
        
        if consommations:
            dernier_mois_consomme = consommations.mois_consomme.replace(day=1)
        
        # 3. Retourner le plus récent entre paiement direct et consommation d'avance
        if dernier_mois_paiement and dernier_mois_consomme:
            return max(dernier_mois_paiement, dernier_mois_consomme)
        elif dernier_mois_paiement:
            return dernier_mois_paiement
        elif dernier_mois_consomme:
            return dernier_mois_consomme
        else:
            return None
    
    @staticmethod
    def _verifier_mois_paye_ou_couvert(contrat, mois_date):
        """
        Vérifie si un mois spécifique est payé ou couvert par une avance.
        
        Args:
            contrat: Contrat concerné
            mois_date: Date du mois à vérifier (1er du mois)
        
        Returns:
            bool: True si le mois est payé ou couvert, False sinon
        """
        # Fonction pour convertir mois_paye en date
        def convertir_mois_paye_en_date(mois_paye_str):
            """Convertit 'Novembre 2024' ou 'November 2024' en date."""
            if not mois_paye_str:
                return None
            
            from datetime import date
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
            
            mois_paye_lower = mois_paye_str.lower().strip()
            for mois, num in {**mois_francais, **mois_anglais}.items():
                if mois in mois_paye_lower:
                    annee_match = re.search(r'(\d{4})', mois_paye_str)
                    if annee_match:
                        annee = int(annee_match.group(1))
                        return date(annee, num, 1)
            return None
        
        # Vérifier si le mois est payé
        paiements_mois = Paiement.objects.filter(
            contrat=contrat,
            statut='valide',
            is_deleted=False
        ).exclude(
            mois_paye__isnull=True
        ).exclude(
            mois_paye=''
        )
        
        for paiement in paiements_mois:
            mois_paye_date = convertir_mois_paye_en_date(paiement.mois_paye)
            if mois_paye_date == mois_date:
                return True
        
        # Vérifier si le mois est couvert par une avance active
        avances_couvrantes = AvanceLoyer.objects.filter(
            contrat=contrat,
            statut='active',
            mois_debut_couverture__lte=mois_date,
            mois_fin_couverture__gte=mois_date
        )
        
        if avances_couvrantes.exists():
            return True
        
        return False
    
    @staticmethod
    def get_prochain_mois_a_payer(contrat):
        """
        Détermine le prochain mois à payer pour un contrat.
        
        LOGIQUE V10.2 : Utilise la même logique centralisée que determiner_mois_debut_couverture_nouvelle_avance
        car le prochain mois à payer = le mois où commencerait une nouvelle avance
        
        Returns:
            date: Prochain mois à payer (1er du mois)
        """
        # Utiliser directement la logique centralisée
        # Le prochain mois à payer est exactement le même que le mois de début d'une nouvelle avance
        return ServiceLogiqueAvanceUnique.determiner_mois_debut_couverture_nouvelle_avance(contrat)
