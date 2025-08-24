from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from .models import Piece, PieceContrat
from contrats.models import Contrat
from django.db import models


class ValidationContratService:
    """Service pour valider les contrats et éviter les conflits de pièces."""
    
    @staticmethod
    def verifier_disponibilite_pieces(propriete_id, pieces_ids, date_debut, date_fin, contrat_existant=None):
        """
        Vérifie si les pièces sont disponibles pour la période donnée.
        
        Args:
            propriete_id: ID de la propriété
            pieces_ids: Liste des IDs des pièces à vérifier
            date_debut: Date de début du contrat
            date_fin: Date de fin du contrat
            contrat_existant: Contrat existant à exclure de la vérification (pour modifications)
        
        Returns:
            tuple: (disponible, conflits)
        """
        if not pieces_ids:
            return True, []
        
        pieces = Piece.objects.filter(
            id__in=pieces_ids,
            propriete_id=propriete_id,
            is_deleted=False
        )
        
        conflits = []
        
        for piece in pieces:
            # Vérifier le statut de la pièce
            if piece.statut != 'disponible':
                conflits.append({
                    'piece': piece.nom,
                    'raison': f"Pièce {piece.get_statut_display().lower()}",
                    'type': 'statut'
                })
                continue
            
            # Vérifier les contrats conflictuels
            queryset = Contrat.objects.filter(
                pieces=piece,
                est_actif=True,
                est_resilie=False,
                is_deleted=False
            )
            
            # Exclure le contrat existant si on modifie
            if contrat_existant:
                queryset = queryset.exclude(id=contrat_existant.id)
            
            # Vérifier les chevauchements de dates
            contrats_conflictuels = queryset.filter(
                date_debut__lt=date_fin,
                date_fin__gt=date_debut
            )
            
            for contrat in contrats_conflictuels:
                conflits.append({
                    'piece': piece.nom,
                    'raison': f"Pièce déjà louée par {contrat.locataire.get_nom_complet()}",
                    'contrat_existant': contrat.numero_contrat,
                    'locataire_existant': contrat.locataire.get_nom_complet(),
                    'periode': f"{contrat.date_debut} à {contrat.date_fin}",
                    'type': 'conflit_dates'
                })
        
        return len(conflits) == 0, conflits
    
    @staticmethod
    def valider_contrat(contrat_data):
        """
        Valide un contrat avant création/modification.
        
        Args:
            contrat_data: Dictionnaire contenant les données du contrat
            
        Returns:
            tuple: (valide, erreurs)
        """
        erreurs = []
        
        # Vérifications de base
        if not contrat_data.get('date_debut'):
            erreurs.append(_("La date de début est obligatoire"))
        
        if not contrat_data.get('date_fin'):
            erreurs.append(_("La date de fin est obligatoire"))
        
        if not contrat_data.get('pieces'):
            erreurs.append(_("Au moins une pièce doit être sélectionnée"))
        
        # Vérifier que la date de fin est après la date de début
        date_debut = contrat_data.get('date_debut')
        date_fin = contrat_data.get('date_fin')
        
        if date_debut and date_fin and date_fin <= date_debut:
            erreurs.append(_("La date de fin doit être postérieure à la date de début"))
        
        # Vérifier la disponibilité des pièces
        if date_debut and date_fin and contrat_data.get('pieces'):
            disponible, conflits = ValidationContratService.verifier_disponibilite_pieces(
                propriete_id=contrat_data.get('propriete_id'),
                pieces_ids=contrat_data.get('pieces'),
                date_debut=date_debut,
                date_fin=date_fin,
                contrat_existant=contrat_data.get('contrat_existant')
            )
            
            if not disponible:
                for conflit in conflits:
                    if conflit['type'] == 'conflit_dates':
                        erreurs.append(
                            _("Conflit pour la pièce '{piece}': {raison} "
                              "(Contrat {contrat} - {locataire} du {periode})").format(
                                piece=conflit['piece'],
                                raison=conflit['raison'],
                                contrat=conflit['contrat_existant'],
                                locataire=conflit['locataire_existant'],
                                periode=conflit['periode']
                            )
                        )
                    else:
                        erreurs.append(
                            _("Conflit pour la pièce '{piece}': {raison}").format(
                                piece=conflit['piece'],
                                raison=conflit['raison']
                            )
                        )
        
        return len(erreurs) == 0, erreurs
    
    @staticmethod
    def creer_contrat_avec_pieces(contrat_data):
        """
        Crée un contrat et assigne les pièces avec validation.
        
        Args:
            contrat_data: Dictionnaire contenant les données du contrat
            
        Returns:
            tuple: (contrat, erreurs)
        """
        # Valider le contrat
        valide, erreurs = ValidationContratService.valider_contrat(contrat_data)
        
        if not valide:
            return None, erreurs
        
        try:
            # Créer le contrat
            from contrats.models import Contrat
            contrat = Contrat.objects.create(
                numero_contrat=contrat_data['numero_contrat'],
                propriete_id=contrat_data['propriete_id'],
                locataire_id=contrat_data['locataire_id'],
                date_debut=contrat_data['date_debut'],
                date_fin=contrat_data['date_fin'],
                date_signature=contrat_data.get('date_signature', timezone.now().date()),
                loyer_mensuel=contrat_data['loyer_mensuel'],
                charges_mensuelles=contrat_data.get('charges_mensuelles', '0.00'),
                depot_garantie=contrat_data.get('depot_garantie', '0.00'),
                avance_loyer=contrat_data.get('avance_loyer', '0.00'),
                jour_paiement=contrat_data.get('jour_paiement', 1),
                mode_paiement=contrat_data.get('mode_paiement', 'virement'),
                cree_par=contrat_data.get('cree_par')
            )
            
            # Assigner les pièces
            pieces_data = []
            for piece_id in contrat_data['pieces']:
                pieces_data.append({
                    'piece_id': piece_id,
                    'loyer_piece': contrat_data.get('loyer_piece', {}).get(str(piece_id)),
                    'charges_piece': contrat_data.get('charges_piece', {}).get(str(piece_id), 0),
                    'date_debut_occupation': contrat_data['date_debut'],
                    'date_fin_occupation': contrat_data['date_fin']
                })
            
            contrat.assigner_pieces(pieces_data)
            
            # Marquer les pièces comme occupées
            for piece in contrat.pieces.all():
                piece.marquer_occupee()
            
            return contrat, []
            
        except Exception as e:
            return None, [str(e)]
    
    @staticmethod
    def modifier_contrat_avec_pieces(contrat, contrat_data):
        """
        Modifie un contrat existant et met à jour les pièces avec validation.
        
        Args:
            contrat: Contrat existant à modifier
            contrat_data: Dictionnaire contenant les nouvelles données
            
        Returns:
            tuple: (contrat, erreurs)
        """
        # Ajouter l'ID du contrat existant pour la validation
        contrat_data['contrat_existant'] = contrat
        
        # Valider le contrat
        valide, erreurs = ValidationContratService.valider_contrat(contrat_data)
        
        if not valide:
            return None, erreurs
        
        try:
            # Marquer les anciennes pièces comme disponibles
            anciennes_pieces = list(contrat.pieces.all())
            
            # Mettre à jour le contrat
            contrat.date_debut = contrat_data['date_debut']
            contrat.date_fin = contrat_data['date_fin']
            contrat.loyer_mensuel = contrat_data['loyer_mensuel']
            contrat.charges_mensuelles = contrat_data.get('charges_mensuelles', '0.00')
            contrat.save()
            
            # Assigner les nouvelles pièces
            pieces_data = []
            for piece_id in contrat_data['pieces']:
                pieces_data.append({
                    'piece_id': piece_id,
                    'loyer_piece': contrat_data.get('loyer_piece', {}).get(str(piece_id)),
                    'charges_piece': contrat_data.get('charges_piece', {}).get(str(piece_id), 0),
                    'date_debut_occupation': contrat_data['date_debut'],
                    'date_fin_occupation': contrat_data['date_fin']
                })
            
            contrat.assigner_pieces(pieces_data)
            
            # Marquer les anciennes pièces comme disponibles
            for piece in anciennes_pieces:
                if piece not in contrat.pieces.all():
                    piece.marquer_disponible()
            
            # Marquer les nouvelles pièces comme occupées
            for piece in contrat.pieces.all():
                piece.marquer_occupee()
            
            return contrat, []
            
        except Exception as e:
            return None, [str(e)]
    
    @staticmethod
    def resiliere_contrat(contrat, motif_resiliation=None):
        """
        Résilie un contrat et libère les pièces.
        
        Args:
            contrat: Contrat à résilier
            motif_resiliation: Motif de la résiliation
            
        Returns:
            tuple: (succes, erreurs)
        """
        try:
            # Marquer le contrat comme résilié
            contrat.est_resilie = True
            contrat.est_actif = False
            contrat.date_resiliation = timezone.now().date()
            if motif_resiliation:
                contrat.motif_resiliation = motif_resiliation
            contrat.save()
            
            # Libérer les pièces
            for piece in contrat.pieces.all():
                piece.marquer_disponible()
            
            # Désactiver les liaisons pièce-contrat
            contrat.pieces_contrat.update(actif=False)
            
            return True, []
            
        except Exception as e:
            return False, [str(e)]


class GestionPiecesService:
    """Service pour gérer les pièces d'une propriété."""
    
    @staticmethod
    def creer_pieces_automatiques(propriete):
        """
        Crée automatiquement les pièces d'une propriété basées sur ses caractéristiques.
        
        Args:
            propriete: Instance de la propriété
            
        Returns:
            list: Liste des pièces créées
        """
        pieces_crees = []
        
        # Créer les chambres
        for i in range(propriete.nombre_chambres):
            piece = Piece.objects.create(
                propriete=propriete,
                nom=f"Chambre {i+1}",
                type_piece='chambre',
                numero_piece=f"C{i+1}",
                surface=propriete.surface / propriete.nombre_pieces if propriete.surface and propriete.nombre_pieces else None
            )
            pieces_crees.append(piece)
        
        # Créer le salon
        if propriete.nombre_pieces > propriete.nombre_chambres:
            piece = Piece.objects.create(
                propriete=propriete,
                nom="Salon",
                type_piece='salon',
                numero_piece="S1",
                surface=propriete.surface / propriete.nombre_pieces if propriete.surface and propriete.nombre_pieces else None
            )
            pieces_crees.append(piece)
        
        # Créer la cuisine
        piece = Piece.objects.create(
            propriete=propriete,
            nom="Cuisine",
            type_piece='cuisine',
            numero_piece="CU1"
        )
        pieces_crees.append(piece)
        
        # Créer les salles de bain
        for i in range(propriete.nombre_salles_bain):
            piece = Piece.objects.create(
                propriete=propriete,
                nom=f"Salle de bain {i+1}",
                type_piece='salle_bain',
                numero_piece=f"SB{i+1}"
            )
            pieces_crees.append(piece)
        
        # Créer les toilettes
        piece = Piece.objects.create(
            propriete=propriete,
            nom="Toilettes",
            type_piece='toilettes',
            numero_piece="WC1"
        )
        pieces_crees.append(piece)
        
        # Créer le couloir
        piece = Piece.objects.create(
            propriete=propriete,
            nom="Couloir",
            type_piece='couloir',
            numero_piece="CO1"
        )
        pieces_crees.append(piece)
        
        # Créer les équipements optionnels
        if propriete.balcon:
            piece = Piece.objects.create(
                propriete=propriete,
                nom="Balcon",
                type_piece='balcon',
                numero_piece="B1"
            )
            pieces_crees.append(piece)
        
        if propriete.parking:
            piece = Piece.objects.create(
                propriete=propriete,
                nom="Parking",
                type_piece='parking',
                numero_piece="P1"
            )
            pieces_crees.append(piece)
        
        if propriete.jardin:
            piece = Piece.objects.create(
                propriete=propriete,
                nom="Jardin",
                type_piece='jardin',
                numero_piece="J1"
            )
            pieces_crees.append(piece)
        
        return pieces_crees
    
    @staticmethod
    def get_pieces_disponibles(propriete_id, date_debut=None, date_fin=None):
        """
        Retourne les pièces disponibles d'une propriété pour une période donnée.
        
        Args:
            propriete_id: ID de la propriété
            date_debut: Date de début (optionnel)
            date_fin: Date de fin (optionnel)
            
        Returns:
            QuerySet: Pièces disponibles
        """
        pieces = Piece.objects.filter(
            propriete_id=propriete_id,
            statut='disponible',
            is_deleted=False
        )
        
        if date_debut and date_fin:
            # Filtrer les pièces qui n'ont pas de contrats conflictuels
            pieces_conflictuels = Piece.objects.filter(
                propriete_id=propriete_id,
                contrats__est_actif=True,
                contrats__est_resilie=False,
                contrats__date_debut__lt=date_fin,
                contrats__date_fin__gt=date_debut,
                is_deleted=False
            ).values_list('id', flat=True)
            
            pieces = pieces.exclude(id__in=pieces_conflictuels)
        
        return pieces
    
    @staticmethod
    def get_statistiques_pieces(propriete_id):
        """
        Retourne les statistiques des pièces d'une propriété.
        
        Args:
            propriete_id: ID de la propriété
            
        Returns:
            dict: Statistiques des pièces
        """
        pieces = Piece.objects.filter(
            propriete_id=propriete_id,
            is_deleted=False
        )
        
        total_pieces = pieces.count()
        pieces_disponibles = pieces.filter(statut='disponible').count()
        pieces_occupees = pieces.filter(statut='occupee').count()
        pieces_renovation = pieces.filter(statut='en_renovation').count()
        
        # Calculer le taux d'occupation
        taux_occupation = (pieces_occupees / total_pieces * 100) if total_pieces > 0 else 0
        
        # Calculer la surface totale
        surface_totale = pieces.aggregate(
            total=models.Sum('surface')
        )['total'] or 0
        
        return {
            'total_pieces': total_pieces,
            'pieces_disponibles': pieces_disponibles,
            'pieces_occupees': pieces_occupees,
            'pieces_renovation': pieces_renovation,
            'taux_occupation': round(taux_occupation, 2),
            'surface_totale': surface_totale
        }
