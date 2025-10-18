"""
Service de gestion des pièces pour les propriétés
"""
from django.db import transaction
from proprietes.models import Propriete, Piece


class GestionPiecesService:
    """Service pour gérer les pièces des propriétés"""
    
    @staticmethod
    def creer_pieces_automatiques(propriete):
        """
        Crée automatiquement les pièces pour une propriété
        basé sur le nombre de pièces spécifié
        """
        if not propriete.necessite_unites_locatives():
            return []
        
        pieces_crees = []
        nombre_pieces = propriete.nombre_pieces or 0
        
        if nombre_pieces <= 0:
            return []
        
        with transaction.atomic():
            # Supprimer les pièces existantes pour cette propriété
            Piece.objects.filter(propriete=propriete).delete()
            
            # Créer les nouvelles pièces
            for i in range(1, nombre_pieces + 1):
                piece = Piece.objects.create(
                    propriete=propriete,
                    numero_piece=f"P{i:02d}",
                    type_piece="Appartement",  # Type par défaut
                    surface=0,  # Surface par défaut
                    loyer_mensuel=0,  # Loyer par défaut
                    disponible=True
                )
                pieces_crees.append(piece)
        
        return pieces_crees
    
    @staticmethod
    def calculer_surface_totale(propriete):
        """Calcule la surface totale de toutes les pièces d'une propriété"""
        pieces = Piece.objects.filter(propriete=propriete)
        return sum(piece.surface or 0 for piece in pieces)
    
    @staticmethod
    def calculer_loyer_total(propriete):
        """Calcule le loyer total de toutes les pièces d'une propriété"""
        pieces = Piece.objects.filter(propriete=propriete)
        return sum(piece.loyer_mensuel or 0 for piece in pieces)
    
    @staticmethod
    def get_pieces_disponibles(propriete):
        """Retourne les pièces disponibles d'une propriété"""
        return Piece.objects.filter(propriete=propriete, disponible=True)
    
    @staticmethod
    def get_pieces_occupees(propriete):
        """Retourne les pièces occupées d'une propriété"""
        return Piece.objects.filter(propriete=propriete, disponible=False)
