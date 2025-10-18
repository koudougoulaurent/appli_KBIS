"""
Utilitaires simples pour la gestion des contrats - Version sans erreurs
"""
from proprietes.models import Propriete, UniteLocative
from contrats.models import Contrat
from django.utils import timezone


def get_proprietes_disponibles():
    """
    Retourne les propriétés disponibles pour un nouveau contrat.
    Utilise la fonction globale pour assurer la cohérence.
    """
    from core.property_utils import get_proprietes_disponibles_global
    return get_proprietes_disponibles_global()


def get_proprietes_disponibles_optimise():
    """
    Version optimisée qui utilise la méthode du modèle Propriete.
    Plus lente mais plus fiable pour les cas complexes.
    """
    proprietes = Propriete.objects.filter(is_deleted=False)
    return [p for p in proprietes if p.est_disponible_pour_location()]


def get_unites_locatives_disponibles(propriete=None):
    """
    Retourne les unités locatives vraiment disponibles pour un nouveau contrat.
    Exclut celles qui sont déjà louées par des contrats actifs.
    """
    from core.property_utils import get_unites_locatives_disponibles_global
    return get_unites_locatives_disponibles_global(propriete)


def get_pieces_disponibles(propriete=None):
    """
    Retourne les pièces vraiment disponibles pour un nouveau contrat.
    Exclut celles qui sont déjà louées par des contrats actifs.
    """
    from core.property_utils import get_pieces_disponibles_global
    return get_pieces_disponibles_global(propriete)


def verifier_disponibilite_propriete(propriete):
    """
    Vérifie si une propriété est disponible.
    """
    # Vérifier s'il y a des contrats actifs pour cette propriété
    contrats_actifs = Contrat.objects.filter(
        propriete=propriete,
        est_actif=True,
        est_resilie=False,
        date_debut__lte=timezone.now().date(),
        date_fin__gte=timezone.now().date(),
        is_deleted=False
    ).exists()
    
    if contrats_actifs:
        return False
    
    # Vérifier s'il y a des unités locatives disponibles
    unites_disponibles = UniteLocative.objects.filter(
        propriete=propriete,
        statut='disponible',
        is_deleted=False
    ).exists()
    
    return unites_disponibles
