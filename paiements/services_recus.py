#!/usr/bin/env python
"""
Services pour la génération automatique des reçus de récapitulatifs
"""

import logging
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Q
from django.contrib.auth import get_user_model

from .models import RecuRecapitulatif, RecapMensuel

logger = logging.getLogger(__name__)
User = get_user_model()


class ServiceGenerationRecus:
    """Service pour la génération automatique des reçus de récapitulatifs."""
    
    def __init__(self):
        self.logger = logger
    
    def generer_recu_automatique(self, recapitulatif, utilisateur=None):
        """
        Génère automatiquement un reçu pour un récapitulatif.
        
        Args:
            recapitulatif: Instance de RecapMensuel
            utilisateur: Utilisateur qui génère le reçu (optionnel)
        
        Returns:
            RecuRecapitulatif: Instance du reçu créé
        """
        try:
            # Vérifier si un reçu existe déjà
            if hasattr(recapitulatif, 'recu'):
                self.logger.warning(f"Un reçu existe déjà pour le récapitulatif {recapitulatif.pk}")
                return recapitulatif.recu
            
            # Créer le reçu
            recu = RecuRecapitulatif.objects.create(
                recapitulatif=recapitulatif,
                type_recu='recapitulatif',
                template_utilise='professionnel',
                format_impression='A4_paysage',
                cree_par=utilisateur,
                statut='brouillon'
            )
            
            # Générer le hash de sécurité
            recu.generer_hash_securite()
            
            self.logger.info(f"Reçu automatique créé: {recu.numero_recu} pour le récapitulatif {recapitulatif.pk}")
            
            return recu
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la génération automatique du reçu: {str(e)}")
            raise
    
    def generer_recu_gestimmob_automatique(self, recapitulatif, utilisateur=None):
        """
        Génère automatiquement un reçu GESTIMMOB pour un récapitulatif.
        
        Args:
            recapitulatif: Instance de RecapMensuel
            utilisateur: Utilisateur qui génère le reçu (optionnel)
        
        Returns:
            RecuRecapitulatif: Instance du reçu créé
        """
        try:
            # Vérifier si un reçu GESTIMMOB existe déjà
            existing_recu = RecuRecapitulatif.objects.filter(
                recapitulatif=recapitulatif,
                template_utilise='gestimmob'
            ).first()
            
            if existing_recu:
                self.logger.warning(f"Un reçu GESTIMMOB existe déjà pour le récapitulatif {recapitulatif.pk}")
                return existing_recu
            
            # Créer le reçu GESTIMMOB
            recu = RecuRecapitulatif.objects.create(
                recapitulatif=recapitulatif,
                type_recu='recapitulatif',
                template_utilise='gestimmob',
                format_impression='A4_paysage',
                cree_par=utilisateur,
                statut='brouillon'
            )
            
            # Générer le hash de sécurité
            recu.generer_hash_securite()
            
            self.logger.info(f"Reçu GESTIMMOB automatique créé: {recu.numero_recu} pour le récapitulatif {recapitulatif.pk}")
            
            return recu
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la génération automatique du reçu GESTIMMOB: {str(e)}")
            raise
    
    def generer_recus_lot(self, recapitulatifs, utilisateur=None):
        """
        Génère des reçus en lot pour plusieurs récapitulatifs.
        
        Args:
            recapitulatifs: QuerySet ou liste de RecapMensuel
            utilisateur: Utilisateur qui génère les reçus (optionnel)
        
        Returns:
            list: Liste des reçus créés
        """
        recus_crees = []
        
        for recapitulatif in recapitulatifs:
            try:
                recu = self.generer_recu_automatique(recapitulatif, utilisateur)
                recus_crees.append(recu)
            except Exception as e:
                self.logger.error(f"Erreur lors de la génération du reçu pour le récapitulatif {recapitulatif.pk}: {str(e)}")
                continue
        
        self.logger.info(f"Génération en lot terminée: {len(recus_crees)} reçus créés")
        
        return recus_crees
    
    def generer_recus_mois(self, mois, utilisateur=None):
        """
        Génère des reçus pour tous les récapitulatifs d'un mois donné.
        
        Args:
            mois: Date du mois (premier jour du mois)
            utilisateur: Utilisateur qui génère les reçus (optionnel)
        
        Returns:
            list: Liste des reçus créés
        """
        # Récupérer tous les récapitulatifs du mois
        recapitulatifs = RecapMensuel.objects.filter(
            mois_recap=mois,
            statut__in=['valide', 'envoye']
        ).exclude(
            recu__isnull=False
        )
        
        return self.generer_recus_lot(recapitulatifs, utilisateur)
    
    def generer_recus_bailleur(self, bailleur, utilisateur=None):
        """
        Génère des reçus pour tous les récapitulatifs d'un bailleur.
        
        Args:
            bailleur: Instance de Bailleur
            utilisateur: Utilisateur qui génère les reçus (optionnel)
        
        Returns:
            list: Liste des reçus créés
        """
        # Récupérer tous les récapitulatifs du bailleur sans reçu
        recapitulatifs = RecapMensuel.objects.filter(
            bailleur=bailleur,
            statut__in=['valide', 'envoye']
        ).exclude(
            recu__isnull=False
        )
        
        return self.generer_recus_lot(recapitulatifs, utilisateur)
    
    def valider_recus_lot(self, recus, utilisateur):
        """
        Valide plusieurs reçus en lot.
        
        Args:
            recus: QuerySet ou liste de RecuRecapitulatif
            utilisateur: Utilisateur qui valide les reçus
        
        Returns:
            int: Nombre de reçus validés
        """
        count = 0
        
        for recu in recus:
            if recu.statut == 'brouillon':
                recu.statut = 'valide'
                recu.save()
                count += 1
        
        self.logger.info(f"Validation en lot terminée: {count} reçus validés")
        
        return count
    
    def marquer_recus_imprimes(self, recus, utilisateur):
        """
        Marque plusieurs reçus comme imprimés.
        
        Args:
            recus: QuerySet ou liste de RecuRecapitulatif
            utilisateur: Utilisateur qui imprime les reçus
        
        Returns:
            int: Nombre de reçus marqués comme imprimés
        """
        count = 0
        
        for recu in recus:
            recu.marquer_imprime(utilisateur)
            count += 1
        
        self.logger.info(f"Marquage en lot terminé: {count} reçus marqués comme imprimés")
        
        return count
    
    def marquer_recus_envoyes(self, recus, mode_envoi='email'):
        """
        Marque plusieurs reçus comme envoyés.
        
        Args:
            recus: QuerySet ou liste de RecuRecapitulatif
            mode_envoi: Mode d'envoi ('email', 'courrier', 'remise_main', 'fax')
        
        Returns:
            int: Nombre de reçus marqués comme envoyés
        """
        count = 0
        
        for recu in recus:
            recu.marquer_envoye(mode_envoi)
            count += 1
        
        self.logger.info(f"Marquage en lot terminé: {count} reçus marqués comme envoyés")
        
        return count
    
    def archiver_recus_anciens(self, jours=365):
        """
        Archive les reçus anciens.
        
        Args:
            jours: Nombre de jours après lesquels archiver (défaut: 365)
        
        Returns:
            int: Nombre de reçus archivés
        """
        date_limite = timezone.now() - timedelta(days=jours)
        
        recus_anciens = RecuRecapitulatif.objects.filter(
            date_creation__lt=date_limite,
            statut__in=['envoye', 'imprime']
        )
        
        count = recus_anciens.update(statut='archive')
        
        self.logger.info(f"Archivage terminé: {count} reçus archivés")
        
        return count
    
    def nettoyer_recus_brouillons(self, jours=30):
        """
        Nettoie les reçus en brouillon anciens.
        
        Args:
            jours: Nombre de jours après lesquels nettoyer (défaut: 30)
        
        Returns:
            int: Nombre de reçus supprimés
        """
        date_limite = timezone.now() - timedelta(days=jours)
        
        recus_brouillons = RecuRecapitulatif.objects.filter(
            statut='brouillon',
            date_creation__lt=date_limite
        )
        
        count = recus_brouillons.count()
        recus_brouillons.delete()
        
        self.logger.info(f"Nettoyage terminé: {count} reçus brouillons supprimés")
        
        return count
    
    def generer_rapport_recus(self, date_debut, date_fin):
        """
        Génère un rapport des reçus pour une période donnée.
        
        Args:
            date_debut: Date de début
            date_fin: Date de fin
        
        Returns:
            dict: Rapport des reçus
        """
        recus = RecuRecapitulatif.objects.filter(
            date_creation__date__range=[date_debut, date_fin]
        )
        
        rapport = {
            'periode': {
                'debut': date_debut,
                'fin': date_fin
            },
            'statistiques': {
                'total': recus.count(),
                'brouillons': recus.filter(statut='brouillon').count(),
                'valides': recus.filter(statut='valide').count(),
                'imprimes': recus.filter(imprime=True).count(),
                'envoyes': recus.filter(envoye=True).count(),
                'archives': recus.filter(statut='archive').count(),
            },
            'par_type': {},
            'par_template': {},
            'par_format': {},
            'par_mois': {},
        }
        
        # Statistiques par type
        for type_recu, _ in RecuRecapitulatif._meta.get_field('type_recu').choices:
            rapport['par_type'][type_recu] = recus.filter(type_recu=type_recu).count()
        
        # Statistiques par template
        for template, _ in RecuRecapitulatif._meta.get_field('template_utilise').choices:
            rapport['par_template'][template] = recus.filter(template_utilise=template).count()
        
        # Statistiques par format
        for format_imp, _ in RecuRecapitulatif._meta.get_field('format_impression').choices:
            rapport['par_format'][format_imp] = recus.filter(format_impression=format_imp).count()
        
        # Statistiques par mois
        from django.db.models.functions import TruncMonth
        recus_par_mois = recus.annotate(
            mois=TruncMonth('date_creation')
        ).values('mois').annotate(
            count=Count('id')
        ).order_by('mois')
        
        for item in recus_par_mois:
            rapport['par_mois'][item['mois'].strftime('%Y-%m')] = item['count']
        
        return rapport


# Instance globale du service
service_recus = ServiceGenerationRecus()


def generer_recu_automatique(recapitulatif, utilisateur=None):
    """Fonction utilitaire pour générer un reçu automatiquement."""
    return service_recus.generer_recu_automatique(recapitulatif, utilisateur)


def generer_recus_lot(recapitulatifs, utilisateur=None):
    """Fonction utilitaire pour générer des reçus en lot."""
    return service_recus.generer_recus_lot(recapitulatifs, utilisateur)


def generer_recus_mois(mois, utilisateur=None):
    """Fonction utilitaire pour générer des reçus pour un mois."""
    return service_recus.generer_recus_mois(mois, utilisateur)


def generer_recus_bailleur(bailleur, utilisateur=None):
    """Fonction utilitaire pour générer des reçus pour un bailleur."""
    return service_recus.generer_recus_bailleur(bailleur, utilisateur)


def generer_recu_gestimmob_automatique(recapitulatif, utilisateur=None):
    """Fonction utilitaire pour générer un reçu GESTIMMOB automatiquement."""
    return service_recus.generer_recu_gestimmob_automatique(recapitulatif, utilisateur)
