"""
Service de recherche amélioré pour toutes les listes
Recherche intelligente par numéro, nom, téléphone, etc.
"""

from django.db.models import Q, F, Value, CharField
from django.db.models.functions import Concat, Cast, Coalesce
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import datetime, timedelta
import re


class EnhancedSearchService:
    """
    Service de recherche amélioré pour toutes les listes
    """
    
    @staticmethod
    def search_bailleurs(queryset, search_term):
        """
        Recherche intelligente dans les bailleurs
        """
        if not search_term:
            return queryset
            
        # Nettoyer le terme de recherche
        search_term = search_term.strip()
        
        # Créer les conditions de recherche
        q_objects = Q()
        
        # Recherche par numéro (exacte)
        if search_term.isdigit():
            q_objects |= Q(numero_bailleur__icontains=search_term)
        
        # Recherche par nom/prénom (insensible à la casse)
        search_words = search_term.split()
        for word in search_words:
            q_objects |= (
                Q(nom__icontains=word) |
                Q(prenom__icontains=word) |
                Q(nom__icontains=search_term) |
                Q(prenom__icontains=search_term)
            )
        
        # Recherche par email
        if '@' in search_term:
            q_objects |= Q(email__icontains=search_term)
        
        # Recherche par téléphone (nettoyer les espaces et tirets)
        phone_clean = re.sub(r'[\s\-\.]', '', search_term)
        if phone_clean.isdigit() and len(phone_clean) >= 8:
            q_objects |= (
                Q(telephone__icontains=phone_clean) |
                Q(telephone_mobile__icontains=phone_clean) |
                Q(telephone__icontains=search_term) |
                Q(telephone_mobile__icontains=search_term)
            )
        
        # Recherche par adresse
        q_objects |= Q(adresse__icontains=search_term)
        
        # Recherche par ville
        q_objects |= Q(ville__icontains=search_term)
        
        return queryset.filter(q_objects).distinct()
    
    @staticmethod
    def search_locataires(queryset, search_term):
        """
        Recherche intelligente dans les locataires
        """
        if not search_term:
            return queryset
            
        search_term = search_term.strip()
        q_objects = Q()
        
        # Recherche par numéro
        if search_term.isdigit():
            q_objects |= Q(numero_locataire__icontains=search_term)
        
        # Recherche par nom/prénom
        search_words = search_term.split()
        for word in search_words:
            q_objects |= (
                Q(nom__icontains=word) |
                Q(prenom__icontains=word) |
                Q(nom__icontains=search_term) |
                Q(prenom__icontains=search_term)
            )
        
        # Recherche par email
        if '@' in search_term:
            q_objects |= Q(email__icontains=search_term)
        
        # Recherche par téléphone
        phone_clean = re.sub(r'[\s\-\.]', '', search_term)
        if phone_clean.isdigit() and len(phone_clean) >= 8:
            q_objects |= (
                Q(telephone__icontains=phone_clean) |
                Q(telephone_mobile__icontains=phone_clean) |
                Q(garant_telephone__icontains=phone_clean) |
                Q(telephone__icontains=search_term) |
                Q(telephone_mobile__icontains=search_term) |
                Q(garant_telephone__icontains=search_term)
            )
        
        # Recherche par adresse
        q_objects |= Q(adresse__icontains=search_term)
        
        # Recherche par ville
        q_objects |= Q(ville__icontains=search_term)
        
        # Recherche par employeur
        q_objects |= Q(employeur__icontains=search_term)
        
        # Recherche par garant
        q_objects |= (
            Q(garant_nom__icontains=search_term) |
            Q(garant_prenom__icontains=search_term)
        )
        
        return queryset.filter(q_objects).distinct()
    
    @staticmethod
    def search_proprietes(queryset, search_term):
        """
        Recherche intelligente dans les propriétés
        """
        if not search_term:
            return queryset
            
        search_term = search_term.strip()
        q_objects = Q()
        
        # Recherche par numéro
        if search_term.isdigit():
            q_objects |= Q(numero_propriete__icontains=search_term)
        
        # Recherche par titre
        q_objects |= Q(titre__icontains=search_term)
        
        # Recherche par adresse
        q_objects |= Q(adresse__icontains=search_term)
        
        # Recherche par ville
        q_objects |= Q(ville__icontains=search_term)
        
        # Recherche par bailleur
        q_objects |= (
            Q(bailleur__nom__icontains=search_term) |
            Q(bailleur__prenom__icontains=search_term) |
            Q(bailleur__nom__icontains=search_term.split()[0]) if search_term.split() else Q()
        )
        
        # Recherche par type de bien
        q_objects |= Q(type_bien__nom__icontains=search_term)
        
        # Recherche par surface (si c'est un nombre)
        if search_term.isdigit():
            q_objects |= Q(surface__gte=int(search_term))
        
        return queryset.filter(q_objects).distinct()
    
    @staticmethod
    def search_contrats(queryset, search_term):
        """
        Recherche intelligente dans les contrats
        """
        if not search_term:
            return queryset
            
        search_term = search_term.strip()
        q_objects = Q()
        
        # Recherche par numéro de contrat
        q_objects |= Q(numero_contrat__icontains=search_term)
        
        # Recherche par propriété
        q_objects |= (
            Q(propriete__titre__icontains=search_term) |
            Q(propriete__adresse__icontains=search_term) |
            Q(propriete__numero_propriete__icontains=search_term)
        )
        
        # Recherche par locataire
        search_words = search_term.split()
        for word in search_words:
            q_objects |= (
                Q(locataire__nom__icontains=word) |
                Q(locataire__prenom__icontains=word) |
                Q(locataire__nom__icontains=search_term) |
                Q(locataire__prenom__icontains=search_term)
            )
        
        # Recherche par bailleur
        q_objects |= (
            Q(propriete__bailleur__nom__icontains=search_term) |
            Q(propriete__bailleur__prenom__icontains=search_term)
        )
        
        # Recherche par loyer (si c'est un nombre)
        if search_term.isdigit():
            q_objects |= Q(loyer_mensuel__gte=int(search_term))
        
        # Recherche par notes
        q_objects |= Q(notes__icontains=search_term)
        
        return queryset.filter(q_objects).distinct()
    
    @staticmethod
    def search_paiements(queryset, search_term):
        """
        Recherche intelligente dans les paiements
        """
        if not search_term:
            return queryset
            
        search_term = search_term.strip()
        q_objects = Q()
        
        # Recherche par numéro de paiement
        q_objects |= Q(numero_paiement__icontains=search_term)
        
        # Recherche par référence
        q_objects |= Q(reference_paiement__icontains=search_term)
        
        # Recherche par montant (si c'est un nombre)
        if search_term.isdigit():
            q_objects |= Q(montant__gte=int(search_term))
        
        # Recherche par locataire
        search_words = search_term.split()
        for word in search_words:
            q_objects |= (
                Q(contrat__locataire__nom__icontains=word) |
                Q(contrat__locataire__prenom__icontains=word) |
                Q(contrat__locataire__nom__icontains=search_term) |
                Q(contrat__locataire__prenom__icontains=search_term)
            )
        
        # Recherche par bailleur
        q_objects |= (
            Q(contrat__propriete__bailleur__nom__icontains=search_term) |
            Q(contrat__propriete__bailleur__prenom__icontains=search_term)
        )
        
        # Recherche par propriété
        q_objects |= (
            Q(contrat__propriete__titre__icontains=search_term) |
            Q(contrat__propriete__adresse__icontains=search_term)
        )
        
        # Recherche par type de paiement
        q_objects |= Q(type_paiement__icontains=search_term)
        
        # Recherche par mode de paiement
        q_objects |= Q(mode_paiement__icontains=search_term)
        
        return queryset.filter(q_objects).distinct()
    
    @staticmethod
    def search_retraits(queryset, search_term):
        """
        Recherche intelligente dans les retraits
        """
        if not search_term:
            return queryset
            
        search_term = search_term.strip()
        q_objects = Q()
        
        # Recherche par bailleur
        search_words = search_term.split()
        for word in search_words:
            q_objects |= (
                Q(bailleur__nom__icontains=word) |
                Q(bailleur__prenom__icontains=word) |
                Q(bailleur__nom__icontains=search_term) |
                Q(bailleur__prenom__icontains=search_term)
            )
        
        # Recherche par montant (si c'est un nombre)
        if search_term.isdigit():
            q_objects |= Q(montant_net_a_payer__gte=int(search_term))
        
        # Recherche par statut
        q_objects |= Q(statut__icontains=search_term)
        
        return queryset.filter(q_objects).distinct()
    
    @staticmethod
    def get_search_suggestions(model_name, search_term):
        """
        Obtenir des suggestions de recherche
        """
        suggestions = []
        
        if not search_term or len(search_term) < 2:
            return suggestions
        
        # Suggestions basées sur le modèle
        if model_name == 'bailleur':
            suggestions = [
                "Recherche par : nom, prénom, email, téléphone, adresse",
                "Exemple : 'Jean Dupont' ou '0123456789' ou 'jean@email.com'"
            ]
        elif model_name == 'locataire':
            suggestions = [
                "Recherche par : nom, prénom, email, téléphone, employeur, garant",
                "Exemple : 'Marie Martin' ou '0123456789' ou 'garant'"
            ]
        elif model_name == 'propriete':
            suggestions = [
                "Recherche par : titre, adresse, ville, bailleur, type",
                "Exemple : 'Villa' ou 'Ouagadougou' ou 'bailleur'"
            ]
        elif model_name == 'contrat':
            suggestions = [
                "Recherche par : numéro, propriété, locataire, bailleur",
                "Exemple : 'CON-001' ou 'Villa' ou 'locataire'"
            ]
        elif model_name == 'paiement':
            suggestions = [
                "Recherche par : numéro, montant, locataire, type, mode",
                "Exemple : 'PAI-001' ou '50000' ou 'loyer'"
            ]
        
        return suggestions
