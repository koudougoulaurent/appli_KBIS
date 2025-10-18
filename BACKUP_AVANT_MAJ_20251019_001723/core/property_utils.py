"""
Utilitaires globaux pour la gestion des propriétés disponibles
"""
from django.db.models import Q, Exists, OuterRef
from proprietes.models import Propriete, UniteLocative
from contrats.models import Contrat
from django.utils import timezone


def get_proprietes_disponibles_global():
    """
    Fonction globale pour récupérer les propriétés disponibles.
    Utilisée dans toute l'application pour assurer la cohérence.
    Tient compte des contrats individuels sur les unités et pièces.
    """
    # Récupérer toutes les propriétés non supprimées
    proprietes_queryset = Propriete.objects.filter(is_deleted=False)
    
    # Sous-requête pour les contrats actifs qui couvrent la propriété entière
    contrats_propriete_complete = Contrat.objects.filter(
        propriete=OuterRef('pk'),
        est_actif=True,
        est_resilie=False,
        date_debut__lte=timezone.now().date(),
        date_fin__gte=timezone.now().date(),
        is_deleted=False,
        unite_locative__isnull=True  # Pas d'unité locative = propriété complète
    )
    
    # Sous-requête pour les unités locatives disponibles (non louées individuellement)
    unites_disponibles = UniteLocative.objects.filter(
        propriete=OuterRef('pk'),
        statut='disponible',
        is_deleted=False
    ).exclude(
        contrats__est_actif=True,
        contrats__est_resilie=False,
        contrats__date_debut__lte=timezone.now().date(),
        contrats__date_fin__gte=timezone.now().date(),
        contrats__is_deleted=False
    )
    
    # Sous-requête pour les pièces disponibles (non louées individuellement)
    from proprietes.models import Piece
    pieces_disponibles = Piece.objects.filter(
        propriete=OuterRef('pk'),
        statut='disponible',
        is_deleted=False
    ).exclude(
        contrats__est_actif=True,
        contrats__est_resilie=False,
        contrats__date_debut__lte=timezone.now().date(),
        contrats__date_fin__gte=timezone.now().date(),
        contrats__is_deleted=False
    )
    
    # Filtrer les propriétés disponibles
    # Une propriété est disponible si :
    # 1. Elle n'a pas de contrat actif complet ET (elle est marquée comme disponible OU elle a des unités/pièces disponibles)
    proprietes_disponibles = proprietes_queryset.filter(
        ~Exists(contrats_propriete_complete) & (
            Q(disponible=True) | 
            Q(Exists(unites_disponibles)) |
            Q(Exists(pieces_disponibles))
        )
    )
    
    return proprietes_disponibles


def get_proprietes_occupees():
    """
    Récupère les propriétés entièrement occupées.
    """
    # Récupérer toutes les propriétés non supprimées
    proprietes_queryset = Propriete.objects.filter(is_deleted=False)
    
    # Sous-requête pour les contrats actifs qui couvrent la propriété entière
    contrats_propriete_complete = Contrat.objects.filter(
        propriete=OuterRef('pk'),
        est_actif=True,
        est_resilie=False,
        date_debut__lte=timezone.now().date(),
        date_fin__gte=timezone.now().date(),
        is_deleted=False,
        unite_locative__isnull=True  # Pas d'unité locative = propriété complète
    )
    
    # Propriétés avec contrats actifs complets
    proprietes_occupees = proprietes_queryset.filter(
        Exists(contrats_propriete_complete)
    )
    
    return proprietes_occupees


def get_proprietes_avec_unites_disponibles():
    """
    Récupère les propriétés qui ont des unités locatives disponibles.
    """
    # Récupérer toutes les propriétés non supprimées
    proprietes_queryset = Propriete.objects.filter(is_deleted=False)
    
    # Sous-requête pour les unités locatives disponibles
    unites_disponibles = UniteLocative.objects.filter(
        propriete=OuterRef('pk'),
        statut='disponible',
        is_deleted=False
    )
    
    # Propriétés avec unités disponibles
    proprietes_avec_unites = proprietes_queryset.filter(
        Exists(unites_disponibles)
    )
    
    return proprietes_avec_unites


def get_unites_locatives_disponibles_global(propriete=None):
    """
    Récupère les unités locatives vraiment disponibles (non louées individuellement).
    """
    from proprietes.models import UniteLocative
    
    queryset = UniteLocative.objects.filter(
        statut='disponible',
        is_deleted=False
    ).exclude(
        contrats__est_actif=True,
        contrats__est_resilie=False,
        contrats__date_debut__lte=timezone.now().date(),
        contrats__date_fin__gte=timezone.now().date(),
        contrats__is_deleted=False
    )
    
    if propriete:
        queryset = queryset.filter(propriete=propriete)
    
    return queryset


def get_pieces_disponibles_global(propriete=None):
    """
    Récupère les pièces vraiment disponibles (non louées individuellement).
    """
    from proprietes.models import Piece
    
    queryset = Piece.objects.filter(
        statut='disponible',
        is_deleted=False
    ).exclude(
        contrats__est_actif=True,
        contrats__est_resilie=False,
        contrats__date_debut__lte=timezone.now().date(),
        contrats__date_fin__gte=timezone.now().date(),
        contrats__is_deleted=False
    )
    
    if propriete:
        queryset = queryset.filter(propriete=propriete)
    
    return queryset


def get_statistiques_proprietes():
    """
    Récupère les statistiques complètes des propriétés.
    """
    total_proprietes = Propriete.objects.filter(is_deleted=False).count()
    proprietes_disponibles = get_proprietes_disponibles_global().count()
    proprietes_occupees = get_proprietes_occupees().count()
    proprietes_avec_unites = get_proprietes_avec_unites_disponibles().count()
    
    # Statistiques des unités et pièces disponibles
    unites_disponibles = get_unites_locatives_disponibles_global().count()
    pieces_disponibles = get_pieces_disponibles_global().count()
    
    return {
        'total': total_proprietes,
        'disponibles': proprietes_disponibles,
        'occupees': proprietes_occupees,
        'avec_unites_disponibles': proprietes_avec_unites,
        'unites_disponibles': unites_disponibles,
        'pieces_disponibles': pieces_disponibles,
        'taux_disponibilite': (proprietes_disponibles / total_proprietes * 100) if total_proprietes > 0 else 0,
    }
