"""
Validateurs pour éviter les doublons et incohérences dans les paiements
"""
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from datetime import date


class ValidateurPaiementUnique:
    """
    Validateur pour garantir qu'un seul paiement par type/mois/contrat.
    Empêche les doublons non professionnels.
    """
    
    @staticmethod
    def valider_unicite_paiement(contrat, type_paiement, mois_paye=None, date_paiement=None, paiement_id=None):
        """
        Vérifie qu'il n'existe pas déjà un paiement validé pour ce contrat/type/mois.
        
        Args:
            contrat: Contrat concerné
            type_paiement: Type de paiement ('loyer', 'avance', 'caution', etc.)
            mois_paye: Mois payé (format "janvier 2026") - pour type 'loyer'
            date_paiement: Date du paiement - pour calculer le mois si mois_paye non fourni
            paiement_id: ID du paiement en cours de modification (pour exclure de la recherche)
        
        Raises:
            ValidationError: Si un doublon est détecté
        
        Returns:
            tuple: (bool, str) - (est_valide, message_erreur)
        """
        from .models import Paiement
        
        # Construire la requête de base
        query = Paiement.objects.filter(
            contrat=contrat,
            type_paiement=type_paiement,
            statut__in=['valide', 'en_attente'],  # Inclure "en_attente" aussi
            is_deleted=False
        )
        
        # Exclure le paiement actuel si on modifie
        if paiement_id:
            query = query.exclude(id=paiement_id)
        
        # Filtrer selon le type de paiement
        if type_paiement == 'loyer':
            # Pour les loyers, vérifier par mois_paye
            if mois_paye:
                query = query.filter(mois_paye=mois_paye)
            elif date_paiement:
                # Calculer le mois depuis la date
                mois_date = date_paiement.replace(day=1)
                # Chercher tous les paiements du même mois
                query = query.filter(
                    date_paiement__year=mois_date.year,
                    date_paiement__month=mois_date.month
                )
        
        elif type_paiement in ['avance', 'avance_loyer']:
            # Pour les avances, vérifier par mois couvert (via mois_paye si renseigné)
            if mois_paye:
                query = query.filter(mois_paye__icontains=mois_paye)
            elif date_paiement:
                # Chercher les avances du même mois
                mois_date = date_paiement.replace(day=1)
                query = query.filter(
                    date_paiement__year=mois_date.year,
                    date_paiement__month=mois_date.month
                )
        
        elif type_paiement == 'caution':
            # Pour la caution, UN SEUL paiement par contrat (sauf suppression)
            # Pas de filtre de date
            pass
        
        # Vérifier si un doublon existe
        doublons = query.exists()
        
        if doublons:
            paiement_existant = query.first()
            
            # Message d'erreur personnalisé selon le type
            if type_paiement == 'caution':
                message = (
                    f"❌ DOUBLON DÉTECTÉ : Une caution est déjà enregistrée pour ce contrat.\n"
                    f"   Paiement existant : {paiement_existant.numero_paiement}\n"
                    f"   Date : {paiement_existant.date_paiement}\n"
                    f"   Montant : {paiement_existant.montant} F CFA\n"
                    f"   Statut : {paiement_existant.get_statut_display()}\n\n"
                    f"⚠️  Vous ne pouvez pas créer une deuxième caution pour le même contrat.\n"
                    f"   Si vous devez remplacer l'ancienne, supprimez-la d'abord (privilèges requis)."
                )
            elif type_paiement in ['avance', 'avance_loyer']:
                message = (
                    f"❌ DOUBLON DÉTECTÉ : Une avance est déjà enregistrée pour ce mois/contrat.\n"
                    f"   Paiement existant : {paiement_existant.numero_paiement}\n"
                    f"   Date : {paiement_existant.date_paiement}\n"
                    f"   Montant : {paiement_existant.montant} F CFA\n"
                    f"   Statut : {paiement_existant.get_statut_display()}\n\n"
                    f"⚠️  Vous ne pouvez pas créer une deuxième avance pour le même mois.\n"
                    f"   Si vous devez la remplacer, supprimez l'ancienne d'abord (privilèges requis)."
                )
            else:  # loyer
                message = (
                    f"❌ DOUBLON DÉTECTÉ : Un paiement de loyer est déjà enregistré pour {mois_paye or 'ce mois'}.\n"
                    f"   Paiement existant : {paiement_existant.numero_paiement}\n"
                    f"   Date : {paiement_existant.date_paiement}\n"
                    f"   Montant : {paiement_existant.montant} F CFA\n"
                    f"   Statut : {paiement_existant.get_statut_display()}\n\n"
                    f"⚠️  Vous ne pouvez pas créer un deuxième paiement pour le même mois.\n"
                    f"   Si vous devez le remplacer, supprimez l'ancien d'abord (privilèges requis)."
                )
            
            return False, message
        
        # Pas de doublon détecté
        return True, ""
    
    @staticmethod
    def nettoyer_doublons_existants(contrat, type_paiement, dry_run=True):
        """
        Nettoie les doublons existants en gardant le plus récent.
        
        Args:
            contrat: Contrat à nettoyer
            type_paiement: Type de paiement à vérifier
            dry_run: Si True, affiche sans supprimer
        
        Returns:
            dict: Rapport du nettoyage
        """
        from .models import Paiement
        from collections import defaultdict
        
        # Récupérer tous les paiements du type
        paiements = Paiement.objects.filter(
            contrat=contrat,
            type_paiement=type_paiement,
            is_deleted=False
        ).order_by('-date_paiement')
        
        # Grouper par mois
        paiements_par_mois = defaultdict(list)
        
        for paiement in paiements:
            if type_paiement == 'caution':
                cle = 'caution'
            elif paiement.mois_paye:
                cle = paiement.mois_paye
            else:
                cle = f"{paiement.date_paiement.year}-{paiement.date_paiement.month:02d}"
            
            paiements_par_mois[cle].append(paiement)
        
        # Identifier les doublons
        doublons_trouves = []
        doublons_supprimes = []
        
        for mois, liste_paiements in paiements_par_mois.items():
            if len(liste_paiements) > 1:
                # Garder le plus récent (premier de la liste car order_by('-date_paiement'))
                paiement_a_garder = liste_paiements[0]
                paiements_a_supprimer = liste_paiements[1:]
                
                doublons_trouves.append({
                    'mois': mois,
                    'nombre': len(liste_paiements),
                    'garde': paiement_a_garder,
                    'a_supprimer': paiements_a_supprimer
                })
                
                if not dry_run:
                    for paiement in paiements_a_supprimer:
                        paiement.is_deleted = True
                        paiement.save()
                        doublons_supprimes.append(paiement)
        
        return {
            'doublons_trouves': len(doublons_trouves),
            'doublons_supprimes': len(doublons_supprimes),
            'details': doublons_trouves
        }


class ValidateurCoherenceAvance:
    """
    Validateur pour garantir la cohérence des avances avec les mois de couverture.
    """
    
    @staticmethod
    def valider_coherence_avance_prochain_mois(contrat):
        """
        Vérifie la cohérence entre :
        - Les avances actives et leurs mois de couverture
        - Le calcul du prochain mois de paiement
        
        Returns:
            dict: Rapport de cohérence
        """
        from .models_avance import AvanceLoyer
        from .services_logique_avance_unique import ServiceLogiqueAvanceUnique
        from datetime import date
        
        aujourd_hui = date.today().replace(day=1)
        
        # Récupérer les avances actives
        avances_actives = AvanceLoyer.objects.filter(
            contrat=contrat,
            statut='active',
            montant_restant__gt=0
        ).order_by('mois_debut_couverture')
        
        # Calculer le prochain mois selon la logique unique
        prochain_mois = ServiceLogiqueAvanceUnique.get_prochain_mois_a_payer(contrat)
        
        # Analyser les avances
        mois_couverts = []
        dernier_mois_couvert = None
        
        for avance in avances_actives:
            mois_couverts.append({
                'avance_id': avance.id,
                'debut': avance.mois_debut_couverture,
                'fin': avance.mois_fin_couverture,
                'nombre_mois': avance.nombre_mois_couverts,
                'montant': avance.montant_avance
            })
            
            if not dernier_mois_couvert or avance.mois_fin_couverture > dernier_mois_couvert:
                dernier_mois_couvert = avance.mois_fin_couverture
        
        # Vérifier la cohérence
        coherent = True
        message = "Cohérent"
        
        if dernier_mois_couvert:
            # Le prochain mois devrait être dernier_mois_couvert + 1
            from dateutil.relativedelta import relativedelta
            prochain_attendu = dernier_mois_couvert + relativedelta(months=1)
            
            if prochain_mois != prochain_attendu:
                coherent = False
                message = (
                    f"Incohérence détectée :\n"
                    f"- Dernière avance couvre jusqu'à : {dernier_mois_couvert.strftime('%B %Y')}\n"
                    f"- Prochain mois attendu : {prochain_attendu.strftime('%B %Y')}\n"
                    f"- Prochain mois calculé : {prochain_mois.strftime('%B %Y')}\n"
                    f"→ Écart de {(prochain_mois.year - prochain_attendu.year) * 12 + (prochain_mois.month - prochain_attendu.month)} mois"
                )
        
        return {
            'coherent': coherent,
            'message': message,
            'avances_actives': len(avances_actives),
            'mois_couverts': mois_couverts,
            'dernier_mois_couvert': dernier_mois_couvert,
            'prochain_mois_calcule': prochain_mois
        }
