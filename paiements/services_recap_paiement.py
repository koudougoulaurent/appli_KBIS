#!/usr/bin/env python3
"""
Service pour générer le récapitulatif mensuel d'état de paiement des loyers
pour chaque bailleur
"""

import logging
from dateutil.relativedelta import relativedelta
from decimal import Decimal
from django.utils import timezone
from django.db.models import Q, Sum
from paiements.models import Paiement
from proprietes.models import Propriete
from contrats.models import Contrat

logger = logging.getLogger(__name__)

# Dictionnaire des mois en français
MOIS_FRANCAIS = {
    1: 'Janvier', 2: 'Février', 3: 'Mars', 4: 'Avril',
    5: 'Mai', 6: 'Juin', 7: 'Juillet', 8: 'Août',
    9: 'Septembre', 10: 'Octobre', 11: 'Novembre', 12: 'Décembre'
}


def formater_mois_francais(date_obj):
    """
    Formate une date pour afficher le mois en français (ex: "Avril 2025")
    """
    if not date_obj:
        return ""
    return f"{MOIS_FRANCAIS[date_obj.month]} {date_obj.year}"


class ServiceRecapPaiementMensuel:
    """Service pour générer le récapitulatif d'état de paiement mensuel par bailleur."""
    
    @staticmethod
    def preparer_donnees_recap_paiement(bailleur, mois_recap):
        """
        Prépare les données pour le récapitulatif de paiement mensuel.
        
        Args:
            bailleur: Instance de Bailleur
            mois_recap: Date du mois à récapituler (premier jour du mois)
        
        Returns:
            dict: Dictionnaire contenant toutes les données pour le récapitulatif
        """
        # Calculer les dates de début et fin du mois
        mois_debut = mois_recap.replace(day=1)
        if mois_recap.month == 12:
            mois_fin = mois_recap.replace(year=mois_recap.year + 1, month=1, day=1) - relativedelta(days=1)
        else:
            mois_fin = mois_recap.replace(month=mois_recap.month + 1, day=1) - relativedelta(days=1)
        
        # Récupérer les propriétés du bailleur avec contrats actifs (même logique que RecapMensuel)
        # Pour garantir la cohérence entre les deux documents
        proprietes_louees = bailleur.proprietes.filter(
            is_deleted=False,
            contrats__est_actif=True,
            contrats__est_resilie=False,
            contrats__date_debut__lte=mois_fin
        ).filter(
            Q(contrats__date_fin__gte=mois_debut) | Q(contrats__date_fin__isnull=True)
        ).distinct().select_related('type_bien', 'bailleur').prefetch_related(
            'contrats__locataire'
        )
        
        # Log pour déboguer
        logger.debug("Bailleur %s: %d propriétés trouvées avec contrats pour le mois %s",
                    bailleur.get_nom_complet(),
                    proprietes_louees.count(),
                    formater_mois_francais(mois_recap))
        
        proprietes_avec_statut = []
        total_proprietes = 0
        total_reglees = 0
        total_en_retard = 0
        
        for propriete in proprietes_louees:
            # Récupérer TOUS les contrats actifs et non résiliés qui couvrent ce mois
            # (même logique que RecapMensuel.get_proprietes_details pour la cohérence)
            contrats_actifs = propriete.contrats.filter(
                est_actif=True,
                est_resilie=False,
                date_debut__lte=mois_fin
            ).filter(
                Q(date_fin__gte=mois_debut) | Q(date_fin__isnull=True)
            ).select_related('locataire').order_by('-date_debut')
            
            # Si aucun contrat ne couvre exactement ce mois, récupérer les contrats récents
            if not contrats_actifs.exists():
                contrats_actifs = propriete.contrats.filter(
                    est_resilie=False,
                    date_debut__lte=mois_fin
                ).select_related('locataire').order_by('-date_debut')
            
            # Si toujours rien, passer à la propriété suivante
            if not contrats_actifs.exists():
                logger.debug("Propriété %s: aucun contrat trouvé", propriete.titre or propriete.adresse)
                continue
            
            # Traiter TOUS les contrats (pour cohérence avec RecapMensuel)
            for contrat_actif in contrats_actifs:
                # Vérifier si le contrat couvre vraiment ce mois spécifique
                contrat_couvre_mois = (
                    contrat_actif.date_debut <= mois_fin and
                    (contrat_actif.date_fin is None or contrat_actif.date_fin >= mois_debut)
                )
                
                # Log pour déboguer
                logger.debug("Propriété %s: contrat %s - début: %s, fin: %s, couvre mois: %s, actif: %s",
                            propriete.titre or propriete.adresse,
                            contrat_actif.numero_contrat,
                            contrat_actif.date_debut,
                            contrat_actif.date_fin,
                            contrat_couvre_mois,
                            contrat_actif.est_actif)
                
                # Vérifier si le loyer du mois est payé (seulement si le contrat couvre le mois)
                if contrat_couvre_mois:
                    statut_paiement = ServiceRecapPaiementMensuel._verifier_statut_paiement(
                        contrat_actif, mois_debut, mois_fin
                    )
                else:
                    # Si le contrat ne couvre pas le mois, marquer comme non applicable
                    date_debut_str = contrat_actif.date_debut.strftime("%d/%m/%Y") if contrat_actif.date_debut else "N/A"
                    if contrat_actif.date_fin:
                        date_fin_str = contrat_actif.date_fin.strftime("%d/%m/%Y")
                    else:
                        date_fin_str = "Indéfini"
                    
                    statut_paiement = {
                        'statut': 'non_applicable',
                        'statut_display': 'NON APPLICABLE',
                        'montant_paye': Decimal('0'),
                        'montant_attendu': Decimal('0'),
                        'details': f'Contrat du {date_debut_str} au {date_fin_str}'
                    }
                
                # Préparer les données de la propriété avec tous les détails du contrat
                donnees_propriete = {
                    'propriete': propriete,
                    'contrat': contrat_actif,
                    'locataire': contrat_actif.locataire,
                    'numero_contrat': contrat_actif.numero_contrat,
                    'date_debut_contrat': contrat_actif.date_debut,
                    'date_fin_contrat': contrat_actif.date_fin,
                    'loyer_mensuel': contrat_actif.loyer_mensuel or Decimal('0'),
                    'charges_mensuelles': contrat_actif.charges_mensuelles or Decimal('0'),
                    'contrat_est_actif': contrat_actif.est_actif,
                    'contrat_couvre_mois': contrat_couvre_mois,
                    'statut': statut_paiement['statut'],
                    'statut_display': statut_paiement['statut_display'],
                    'montant_paye': statut_paiement['montant_paye'],
                    'montant_attendu': statut_paiement['montant_attendu'],
                    'date_paiement': statut_paiement.get('date_paiement'),
                    'details_paiement': statut_paiement.get('details', '')
                }
                
                proprietes_avec_statut.append(donnees_propriete)
                
                # Compter seulement si le contrat couvre vraiment le mois
                if contrat_couvre_mois:
                    total_proprietes += 1
                    if statut_paiement['statut'] == 'regle':
                        total_reglees += 1
                    elif statut_paiement['statut'] == 'en_retard':
                        total_en_retard += 1
        
        # Trier par statut (en retard en premier, puis réglées)
        proprietes_avec_statut.sort(key=lambda x: (x['statut'] == 'regle', x['propriete'].titre or ''))
        
        # Préparer le récapitulatif global
        recap_data = {
            'bailleur': bailleur,
            'mois_recap': mois_recap,
            'mois_debut': mois_debut,
            'mois_fin': mois_fin,
            'mois_display': formater_mois_francais(mois_recap),  # Format français garanti
            'proprietes': proprietes_avec_statut,
            'total_proprietes': total_proprietes,
            'total_reglees': total_reglees,
            'total_en_retard': total_en_retard,
            'date_generation': timezone.now(),
        }
        
        return recap_data
    
    @staticmethod
    def _verifier_statut_paiement(contrat, mois_debut, mois_fin):
        """
        Vérifie le statut de paiement du loyer pour un contrat donné.
        Prend en compte les avances (détecte automatiquement si montant >= loyer mensuel)
        et marque tous les mois couverts comme réglés, y compris les mois futurs.
        
        Args:
            contrat: Instance de Contrat
            mois_debut: Date de début du mois à vérifier
            mois_fin: Date de fin du mois à vérifier
        
        Returns:
            dict: Dictionnaire avec le statut et les détails
        """
        loyer_mensuel = contrat.loyer_mensuel or Decimal('0')
        if loyer_mensuel <= 0:
            return {
                'statut': 'non_applicable',
                'statut_display': 'NON APPLICABLE',
                'montant_paye': Decimal('0'),
                'montant_attendu': Decimal('0'),
                'details': 'Loyer mensuel non défini'
            }
        
        # 1. Récupérer TOUS les paiements validés (dans l'ordre chronologique)
        # Un paiement >= loyer_mensuel est considéré comme une avance (même si type='loyer')
        tous_paiements = Paiement.objects.filter(
            contrat=contrat,
            statut='valide'
        ).filter(
            Q(type_paiement='loyer') | 
            Q(type_paiement='paiement_partiel') |
            Q(type_paiement='avance')
        ).order_by('date_paiement')
        
        # 2. Simuler l'application des paiements mois par mois
        # pour déterminer si ce mois est couvert
        mois_debut_contrat = contrat.date_debut.replace(day=1)
        mois_courant = mois_debut_contrat
        montant_restant = Decimal('0')
        dernier_paiement_utilise = None
        mois_trouve = False
        
        for paiement in tous_paiements:
            montant_paiement = paiement.montant_net_paye or paiement.montant or Decimal('0')
            
            # Ajouter le montant restant précédent
            montant_total = montant_restant + montant_paiement
            
            # Si le montant total >= loyer_mensuel, on peut payer des mois
            while montant_total >= loyer_mensuel:
                # Avancer au mois suivant (qui sera payé)
                mois_suivant = mois_courant + relativedelta(months=1)
                
                # Si ce mois suivant est exactement le mois à vérifier, il est payé
                if mois_suivant == mois_debut:
                    # Ce mois est couvert par une avance
                    mois_trouve = True
                    dernier_paiement_utilise = paiement
                elif mois_suivant > mois_debut:
                    # On a dépassé le mois, donc il était payé avant
                    mois_trouve = True
                    if not dernier_paiement_utilise:
                        dernier_paiement_utilise = paiement
                
                # Payer ce mois
                mois_courant = mois_suivant
                montant_total = montant_total - loyer_mensuel
                
                # Si on a dépassé le mois à vérifier, on peut arrêter
                if mois_courant > mois_debut and mois_trouve:
                    break
            
            # Conserver le reste pour le prochain paiement
            montant_restant = montant_total
            
            # Si le mois est trouvé, sortir de la boucle
            if mois_trouve and mois_courant > mois_debut:
                break
        
        # Si le mois est trouvé dans les avances, il est réglé
        if mois_trouve or mois_courant > mois_debut:
            montant_total_paye = loyer_mensuel
            
            # Détecter si c'est une avance multi-mois
            details_parts = []
            if dernier_paiement_utilise:
                montant_paiement_ref = dernier_paiement_utilise.montant_net_paye or dernier_paiement_utilise.montant or Decimal('0')
                if montant_paiement_ref >= loyer_mensuel:
                    nombre_mois = int(montant_paiement_ref // loyer_mensuel)
                    if nombre_mois > 1:
                        details_parts.append(f'Avance de {nombre_mois} mois ({montant_paiement_ref:.0f} F CFA)')
            
            details = f'Loyer payé ({montant_total_paye:.0f} F CFA)'
            if details_parts:
                details += ' - ' + ' '.join(details_parts)
            
            return {
                'statut': 'regle',
                'statut_display': 'RÉGLÉ',
                'montant_paye': montant_total_paye,
                'montant_attendu': loyer_mensuel,
                'date_paiement': dernier_paiement_utilise.date_paiement if dernier_paiement_utilise else None,
                'details': details
            }
        
        # Si on arrive ici, le mois n'est pas encore couvert
        # Vérifier s'il y a des paiements partiels pour ce mois spécifique
        paiements_mois = Paiement.objects.filter(
            contrat=contrat,
            statut='valide',
            date_paiement__gte=mois_debut,
            date_paiement__lte=mois_fin
        ).filter(
            Q(type_paiement='loyer') | 
            Q(type_paiement='paiement_partiel')
        )
        
        montant_partiel = paiements_mois.aggregate(
            total=Sum('montant_net_paye')
        )['total'] or Decimal('0')
        
        if montant_partiel == Decimal('0'):
            montant_partiel = paiements_mois.aggregate(
                total=Sum('montant')
            )['total'] or Decimal('0')
        
        # Ajouter le reste éventuel
        if mois_courant == mois_debut and montant_restant > 0:
            montant_partiel += montant_restant
        
        montant_total_paye = montant_partiel
        
        if montant_total_paye >= loyer_mensuel:
            dernier_paiement = paiements_mois.order_by('-date_paiement').first()
            return {
                'statut': 'regle',
                'statut_display': 'RÉGLÉ',
                'montant_paye': montant_total_paye,
                'montant_attendu': loyer_mensuel,
                'date_paiement': dernier_paiement.date_paiement if dernier_paiement else None,
                'details': f'Loyer payé ({montant_total_paye:.0f} F CFA)'
            }
        else:
            # Le loyer est en retard - calculer le nombre de mois de retard
            # Le dernier mois réglé est mois_courant (le dernier mois qui a été payé)
            dernier_mois_regle = mois_courant
            mois_en_retard = []
            
            # Calculer tous les mois en retard depuis le dernier mois réglé jusqu'au mois vérifié
            mois_retard = dernier_mois_regle + relativedelta(months=1)
            while mois_retard <= mois_debut:
                mois_en_retard.append(mois_retard)
                mois_retard = mois_retard + relativedelta(months=1)
            
            # Formater les mois en français
            mois_liste_str = []
            for mois in mois_en_retard:
                mois_liste_str.append(formater_mois_francais(mois))
            
            nombre_mois_retard = len(mois_en_retard)
            
            montant_manquant = loyer_mensuel - montant_total_paye
            
            # Préparer le message de détails avec les mois en retard
            if nombre_mois_retard > 0:
                details_retard = f'Retard de {nombre_mois_retard} mois'
                if mois_liste_str:
                    details_retard += f' : {", ".join(mois_liste_str)}'
                details_retard += f' - Manque {montant_manquant:.0f} F CFA sur {loyer_mensuel:.0f} F CFA'
            else:
                details_retard = f'Manque {montant_manquant:.0f} F CFA sur {loyer_mensuel:.0f} F CFA'
            
            return {
                'statut': 'en_retard',
                'statut_display': 'EN RETARD',
                'montant_paye': montant_total_paye,
                'montant_attendu': loyer_mensuel,
                'montant_manquant': montant_manquant,
                'nombre_mois_retard': nombre_mois_retard,
                'mois_en_retard': mois_liste_str,
                'details': details_retard
            }
    
    @staticmethod
    def _avance_couvre_mois(avance_paiement, mois_debut):
        """
        Vérifie si une avance de loyer couvre le mois donné.
        
        Args:
            avance_paiement: Instance de Paiement de type 'avance'
            mois_debut: Date de début du mois à vérifier
        
        Returns:
            bool: True si l'avance couvre le mois
        """
        # Calculer le dernier mois payé avec les paiements précédents
        dernier_mois_paiement = ServiceRecapPaiementMensuel._get_dernier_mois_paiement_avance(
            avance_paiement.contrat, avance_paiement.date_paiement
        )
        
        if not dernier_mois_paiement:
            # Si pas de paiement précédent, l'avance commence au mois suivant la date de paiement
            mois_couvert_debut = avance_paiement.date_paiement.replace(day=1) + relativedelta(months=1)
        else:
            # L'avance commence au mois suivant le dernier paiement
            mois_couvert_debut = dernier_mois_paiement + relativedelta(months=1)
        
        # Calculer le nombre de mois couverts par l'avance
        loyer_mensuel = avance_paiement.contrat.loyer_mensuel or Decimal('0')
        if loyer_mensuel <= 0:
            return False
        
        # Utiliser montant_net_paye ou montant
        montant_avance = avance_paiement.montant_net_paye or avance_paiement.montant or Decimal('0')
        nombre_mois = int(montant_avance // loyer_mensuel)
        
        if nombre_mois <= 0:
            return False
        
        mois_couvert_fin = mois_couvert_debut + relativedelta(months=nombre_mois - 1)
        
        # Vérifier si le mois donné est dans la plage couverte
        return mois_debut >= mois_couvert_debut and mois_debut <= mois_couvert_fin
    
    @staticmethod
    def _get_dernier_mois_paiement_avance(contrat, date_reference):
        """
        Récupère le dernier mois de paiement (dernière quittance de loyer)
        avant une date de référence.
        
        Args:
            contrat: Instance de Contrat
            date_reference: Date de référence
        
        Returns:
            date: Date du dernier mois payé (premier jour du mois) ou None
        """
        dernier_paiement_loyer = Paiement.objects.filter(
            contrat=contrat,
            statut='valide',
            type_paiement='loyer',
            date_paiement__lt=date_reference
        ).order_by('-date_paiement').first()
        
        if dernier_paiement_loyer:
            return dernier_paiement_loyer.date_paiement.replace(day=1)
        
        return None
    
    @staticmethod
    def preparer_donnees_recap_locataires(bailleur, mois_recap):
        """
        Prépare les données pour le récapitulatif de paiement mensuel par locataire.
        Pour un bailleur donné, liste tous ses locataires avec leur statut de paiement.
        
        Args:
            bailleur: Instance de Bailleur
            mois_recap: Date du mois à récapituler (premier jour du mois)
        
        Returns:
            dict: Dictionnaire contenant toutes les données pour le récapitulatif par locataire
        """
        # Calculer les dates de début et fin du mois
        mois_debut = mois_recap.replace(day=1)
        if mois_recap.month == 12:
            mois_fin = mois_recap.replace(year=mois_recap.year + 1, month=1, day=1) - relativedelta(days=1)
        else:
            mois_fin = mois_recap.replace(month=mois_recap.month + 1, day=1) - relativedelta(days=1)
        
        # Récupérer tous les contrats actifs du bailleur pour ce mois
        contrats_actifs_qs = Contrat.objects.filter(
            propriete__bailleur=bailleur,
            propriete__is_deleted=False,
            est_actif=True,
            est_resilie=False,
            date_debut__lte=mois_fin
        ).filter(
            Q(date_fin__gte=mois_debut) | Q(date_fin__isnull=True)
        ).select_related('locataire', 'propriete').order_by('locataire__nom', 'locataire__prenom')
        
        # FORCER la conversion en liste Python standard pour éviter NotImplementedType
        # Évaluer le QuerySet immédiatement
        contrats_actifs = []
        try:
            # Forcer l'évaluation du QuerySet en itérant explicitement
            for contrat in contrats_actifs_qs:
                # S'assurer que tous les attributs sont accessibles
                try:
                    _ = contrat.id
                    _ = contrat.locataire
                    _ = contrat.propriete
                    contrats_actifs.append(contrat)
                except Exception as e:
                    logger.warning(f"Erreur lors de l'accès aux attributs du contrat {contrat.pk}: {e}")
                    continue
        except Exception as e:
            logger.error(f"Erreur lors de la conversion des contrats en liste: {e}", exc_info=True)
            contrats_actifs = []
        
        # Grouper par locataire
        locataires_dict = {}
        total_locataires = 0
        total_reglees = 0
        total_en_retard = 0
        
        for contrat in contrats_actifs:
            locataire = contrat.locataire
            if not locataire:
                continue
            
            # Vérifier si le contrat couvre ce mois
            contrat_couvre_mois = (
                contrat.date_debut <= mois_fin and
                (contrat.date_fin is None or contrat.date_fin >= mois_debut)
            )
            
            # Obtenir le statut de paiement
            if contrat_couvre_mois:
                statut_paiement = ServiceRecapPaiementMensuel._verifier_statut_paiement(
                    contrat, mois_debut, mois_fin
                )
            else:
                date_debut_str = contrat.date_debut.strftime("%d/%m/%Y") if contrat.date_debut else "N/A"
                date_fin_str = contrat.date_fin.strftime("%d/%m/%Y") if contrat.date_fin else "Indéfini"
                statut_paiement = {
                    'statut': 'non_applicable',
                    'statut_display': 'NON APPLICABLE',
                    'montant_paye': Decimal('0'),
                    'montant_attendu': Decimal('0'),
                    'details': f'Contrat du {date_debut_str} au {date_fin_str}'
                }
            
            # Créer ou mettre à jour l'entrée du locataire
            if locataire.id not in locataires_dict:
                locataires_dict[locataire.id] = {
                    'locataire': locataire,
                    'contrats': [],
                    'statut_global': statut_paiement['statut'],
                    'statut_global_display': statut_paiement['statut_display'],
                    'total_montant_paye': Decimal('0'),
                    'total_montant_attendu': Decimal('0'),
                }
            
            # Ajouter le contrat - S'assurer que tous les attributs sont des valeurs Python simples
            try:
                numero_contrat = str(contrat.numero_contrat) if contrat.numero_contrat else "N/A"
                date_debut_contrat = contrat.date_debut if contrat.date_debut else None
                date_fin_contrat = contrat.date_fin if contrat.date_fin else None
                loyer_mensuel = Decimal(str(contrat.loyer_mensuel)) if contrat.loyer_mensuel else Decimal('0')
                charges_mensuelles = Decimal(str(contrat.charges_mensuelles)) if contrat.charges_mensuelles else Decimal('0')
                
                # Créer un dictionnaire avec les valeurs nécessaires
                # Garder les objets Django pour le template mais s'assurer qu'ils sont accessibles
                contrat_dict = {
                    'contrat': contrat,  # Objet complet pour compatibilité
                    'contrat_id': contrat.id,
                    'propriete': contrat.propriete,  # Objet complet
                    'propriete_id': contrat.propriete.id if contrat.propriete else None,
                    'numero_contrat': numero_contrat,
                    'date_debut_contrat': date_debut_contrat,
                    'date_fin_contrat': date_fin_contrat,
                    'statut': str(statut_paiement['statut']),
                    'statut_display': str(statut_paiement['statut_display']),
                    'montant_paye': Decimal(str(statut_paiement['montant_paye'])),
                    'montant_attendu': Decimal(str(statut_paiement['montant_attendu'])),
                    'date_paiement': statut_paiement.get('date_paiement'),
                    'details_paiement': str(statut_paiement.get('details', '')),
                    'loyer_mensuel': loyer_mensuel,
                    'charges_mensuelles': charges_mensuelles,
                }
                locataires_dict[locataire.id]['contrats'].append(contrat_dict)
            except Exception as e:
                logger.error(f"Erreur lors de la création du dictionnaire de contrat: {e}", exc_info=True)
                continue
            
            # Mettre à jour les totaux du locataire
            locataires_dict[locataire.id]['total_montant_paye'] += statut_paiement['montant_paye']
            locataires_dict[locataire.id]['total_montant_attendu'] += statut_paiement['montant_attendu']
            
            # Mettre à jour le statut global (le pire statut)
            if statut_paiement['statut'] == 'en_retard':
                locataires_dict[locataire.id]['statut_global'] = 'en_retard'
                locataires_dict[locataire.id]['statut_global_display'] = 'EN RETARD'
            elif statut_paiement['statut'] == 'regle' and locataires_dict[locataire.id]['statut_global'] != 'en_retard':
                locataires_dict[locataire.id]['statut_global'] = 'regle'
                locataires_dict[locataire.id]['statut_global_display'] = 'RÉGLÉ'
        
        # Convertir en liste et compter - FORCER en liste Python standard
        try:
            locataires_avec_statut = list(locataires_dict.values())
        except (TypeError, AttributeError) as e:
            logger.error(f"Erreur lors de la conversion des locataires en liste: {e}")
            locataires_avec_statut = []
        
        # S'assurer que chaque locataire a une liste de contrats
        for locataire_data in locataires_avec_statut:
            if 'contrats' not in locataire_data:
                locataire_data['contrats'] = []
            elif not isinstance(locataire_data['contrats'], list):
                try:
                    locataire_data['contrats'] = list(locataire_data['contrats'])
                except (TypeError, AttributeError):
                    locataire_data['contrats'] = []
        
        for locataire_data in locataires_avec_statut:
            # Compter seulement si au moins un contrat couvre le mois
            a_contrat_couvrant_mois = any(
                c.get('statut') != 'non_applicable' for c in locataire_data.get('contrats', [])
            )
            
            if a_contrat_couvrant_mois:
                total_locataires += 1
                if locataire_data['statut_global'] == 'regle':
                    total_reglees += 1
                elif locataire_data['statut_global'] == 'en_retard':
                    total_en_retard += 1
        
        # Trier par statut (en retard en premier, puis réglés), puis par nom
        # S'assurer que tous les champs existent avant de trier
        try:
            locataires_avec_statut.sort(key=lambda x: (
                x.get('statut_global', '') != 'en_retard',  # En retard en premier
                x.get('statut_global', '') == 'regle',  # Puis réglés
                getattr(x.get('locataire'), 'nom', '') or '',
                getattr(x.get('locataire'), 'prenom', '') or ''
            ))
        except Exception as e:
            logger.error(f"Erreur lors du tri des locataires: {e}")
            # Si le tri échoue, on garde l'ordre original
        
        # Préparer le récapitulatif global
        recap_data = {
            'bailleur': bailleur,
            'mois_recap': mois_recap,
            'mois_debut': mois_debut,
            'mois_fin': mois_fin,
            'mois_display': formater_mois_francais(mois_recap),
            'locataires': locataires_avec_statut,
            'total_locataires': total_locataires,
            'total_reglees': total_reglees,
            'total_en_retard': total_en_retard,
            'date_generation': timezone.now(),
        }
        
        return recap_data

