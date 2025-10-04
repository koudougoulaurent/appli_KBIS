"""
Service intelligent pour la gestion des retraits bailleur avec intégration des charges.
"""

from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from datetime import date
from .models import RetraitBailleur, RecapMensuel
from proprietes.models import ChargesBailleur, Propriete
from core.models import AuditLog
from django.contrib.contenttypes.models import ContentType


class ServiceRetraitsBailleurIntelligent:
    """
    Service intelligent pour gérer les retraits bailleur avec intégration automatique des charges.
    """
    
    @staticmethod
    def calculer_retrait_mensuel_bailleur(bailleur, mois=None, annee=None):
        """
        Calcule le retrait mensuel d'un bailleur en intégrant automatiquement les charges.
        
        Args:
            bailleur: Instance du bailleur
            mois: Mois (par défaut mois actuel)
            annee: Année (par défaut année actuelle)
        
        Returns:
            dict: Détails du calcul du retrait
        """
        if mois is None:
            mois = timezone.now().month
        if annee is None:
            annee = timezone.now().year
        
        # Date de début du mois
        mois_retrait = date(annee, mois, 1)
        
        from django.db import models
        
        # Calculer le total des loyers basé sur les contrats actifs
        from contrats.models import Contrat
        total_loyers = Contrat.objects.filter(
            propriete__bailleur=bailleur,
            propriete__is_deleted=False,
            est_actif=True,
            est_resilie=False
        ).aggregate(
            total=models.Sum('loyer_mensuel')
        )['total'] or Decimal('0')
        
        # Calculer le total des charges déductibles
        from contrats.models import Contrat
        total_charges_deductibles = Contrat.objects.filter(
            propriete__bailleur=bailleur,
            est_actif=True
        ).aggregate(
            total=models.Sum('charges_deductibles')
        )['total'] or Decimal('0')
        
        # Calculer le total des charges bailleur en cours
        total_charges_bailleur = ChargesBailleur.objects.filter(
            propriete__bailleur=bailleur,
            statut__in=['en_attente', 'deduite_retrait']
        ).aggregate(
            total=models.Sum('montant_restant')
        )['total'] or Decimal('0')
        
        # Montant net à verser au bailleur
        montant_net = total_loyers - total_charges_deductibles - total_charges_bailleur
        
        return {
            'bailleur': bailleur,
            'mois': mois,
            'annee': annee,
            'total_loyers': total_loyers,
            'total_charges_deductibles': total_charges_deductibles,
            'total_charges_bailleur': total_charges_bailleur,
            'montant_net': max(Decimal('0'), montant_net),
            'date_calcul': timezone.now()
        }
    
    @staticmethod
    def creer_ou_mettre_a_jour_retrait_mensuel(bailleur, mois=None, annee=None, user=None):
        """
        Crée ou met à jour le retrait mensuel d'un bailleur.
        
        Args:
            bailleur: Instance du bailleur
            mois: Mois (par défaut mois actuel)
            annee: Année (par défaut année actuelle)
            user: Utilisateur qui effectue l'action
        
        Returns:
            RetraitBailleur: Instance du retrait créé ou mis à jour
        """
        if mois is None:
            mois = timezone.now().month
        if annee is None:
            annee = timezone.now().year
        
        # Calculer le retrait mensuel
        calcul = ServiceRetraitsBailleurIntelligent.calculer_retrait_mensuel_bailleur(
            bailleur, mois, annee
        )
        
        # Date de début du mois
        mois_retrait = date(annee, mois, 1)
        
        with transaction.atomic():
            # Récupérer ou créer le retrait mensuel
            retrait, created = RetraitBailleur.objects.get_or_create(
                bailleur=bailleur,
                mois_retrait=mois_retrait,
                defaults={
                    'montant_loyers_bruts': calcul['total_loyers'],
                    'montant_charges_deductibles': calcul['total_charges_deductibles'],
                    'montant_net_a_payer': calcul['montant_net'],
                    'statut': 'en_attente',
                    'type_retrait': 'mensuel',
                    'mode_retrait': 'virement',
                    'date_demande': timezone.now().date(),
                    'cree_par': user
                }
            )
            
            if not created:
                # Mettre à jour les montants
                retrait.montant_loyers_bruts = calcul['total_loyers']
                retrait.montant_charges_deductibles = calcul['total_charges_deductibles']
                retrait.montant_net_a_payer = calcul['montant_net']
                retrait.save()
            
            # Intégrer les charges bailleur en cours
            charges_bailleur = ChargesBailleur.objects.filter(
                propriete__bailleur=bailleur,
                statut='en_attente'
            )
            
            for charge in charges_bailleur:
                retrait.charges_bailleur.add(charge)
                # Marquer la charge comme déduite du retrait
                charge.statut = 'deduite_retrait'
                charge.save()
            
            # Créer un log d'audit
            ServiceRetraitsBailleurIntelligent._log_creation_retrait(
                retrait, created, calcul, user
            )
        
        return retrait
    
    @staticmethod
    def integrer_charge_dans_retrait(charge, montant_deduit, user=None):
        """
        Intègre une charge spécifique dans le retrait mensuel du bailleur.
        
        Args:
            charge: Instance de la charge à intégrer
            montant_deduit: Montant à déduire
            user: Utilisateur qui effectue l'action
        
        Returns:
            RetraitBailleur: Instance du retrait mis à jour
        """
        from django.db import models
        
        # Récupérer le retrait mensuel du bailleur
        mois_actuel = timezone.now().replace(day=1)
        retrait, created = RetraitBailleur.objects.get_or_create(
            bailleur=charge.propriete.bailleur,
            mois_retrait=mois_actuel.date(),
            defaults={
                'montant_loyers_bruts': 0,
                'montant_charges_deductibles': 0,
                'montant_net_a_payer': 0,
                'statut': 'en_attente',
                'type_retrait': 'mensuel',
                'mode_retrait': 'virement',
                'date_demande': timezone.now().date(),
                'cree_par': user
            }
        )
        
        with transaction.atomic():
            # Déduire le montant du retrait
            retrait.montant_net_a_payer -= montant_deduit
            retrait.save()
            
            # Ajouter la charge au retrait
            retrait.charges_bailleur.add(charge)
            
            # Marquer la charge comme déduite
            charge.marquer_comme_deduit(montant_deduit)
            
            # Créer un log d'audit
            ServiceRetraitsBailleurIntelligent._log_integration_charge(
                retrait, charge, montant_deduit, user
            )
        
        return retrait
    
    @staticmethod
    def generer_rapport_retraits_mensuels(mois=None, annee=None):
        """
        Génère un rapport des retraits mensuels avec intégration des charges.
        
        Args:
            mois: Mois (par défaut mois actuel)
            annee: Année (par défaut année actuelle)
        
        Returns:
            dict: Rapport des retraits mensuels
        """
        if mois is None:
            mois = timezone.now().month
        if annee is None:
            annee = timezone.now().year
        
        # Récupérer tous les retraits du mois
        retraits = RetraitBailleur.objects.filter(
            mois_retrait__year=annee,
            mois_retrait__month=mois
        ).select_related('bailleur').prefetch_related('charges_bailleur')
        
        total_retraits = sum(retrait.montant_net_a_payer for retrait in retraits)
        total_charges_integre = sum(
            sum(charge.montant for charge in retrait.charges_bailleur.all())
            for retrait in retraits
        )
        
        return {
            'mois': mois,
            'annee': annee,
            'retraits': retraits,
            'total_retraits': total_retraits,
            'total_charges_integre': total_charges_integre,
            'nombre_retraits': retraits.count()
        }
    
    @staticmethod
    def _log_creation_retrait(retrait, created, calcul, user):
        """Crée un log d'audit pour la création/mise à jour d'un retrait."""
        try:
            content_type = ContentType.objects.get_for_model(RetraitBailleur)
            AuditLog.objects.create(
                content_type=content_type,
                object_id=retrait.id,
                action='create' if created else 'update',
                user=user,
                details={
                    'description': f'{"Création" if created else "Mise à jour"} du retrait mensuel',
                    'bailleur': retrait.bailleur.get_nom_complet(),
                    'montant': str(retrait.montant_net_a_payer),
                    'mois': retrait.mois_retrait.strftime('%Y-%m'),
                    'total_loyers': str(calcul['total_loyers']),
                    'total_charges_deductibles': str(calcul['total_charges_deductibles']),
                    'total_charges_bailleur': str(calcul['total_charges_bailleur'])
                }
            )
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Erreur lors de la création du log de retrait: {e}")
    
    @staticmethod
    def _log_integration_charge(retrait, charge, montant_deduit, user):
        """Crée un log d'audit pour l'intégration d'une charge."""
        try:
            content_type = ContentType.objects.get_for_model(RetraitBailleur)
            AuditLog.objects.create(
                content_type=content_type,
                object_id=retrait.id,
                action='update',
                user=user,
                details={
                    'description': f'Intégration de la charge "{charge.titre}" dans le retrait',
                    'charge_id': charge.id,
                    'montant_deduit': str(montant_deduit),
                    'montant_retrait_apres': str(retrait.montant_net_a_payer)
                }
            )
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Erreur lors de la création du log d'intégration: {e}")
