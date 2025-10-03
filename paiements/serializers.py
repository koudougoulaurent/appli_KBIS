from rest_framework import serializers
from .models import Paiement
from contrats.serializers import ContratSerializer
from proprietes.serializers import BailleurSerializer
from utilisateurs.serializers import UtilisateurSerializer


class PaiementSerializer(serializers.ModelSerializer):
    """Sérialiseur pour les paiements (version liste)."""
    
    contrat = ContratSerializer(read_only=True)
    cree_par = UtilisateurSerializer(read_only=True)
    valide_par = UtilisateurSerializer(read_only=True)
    statut_color = serializers.CharField(read_only=True, source='get_statut_display_color')
    
    class Meta:
        model = Paiement
        fields = [
            'id', 'contrat', 'montant', 'type_paiement', 'statut', 'mode_paiement',
            'date_paiement', 'date_encaissement', 'numero_cheque', 'reference_virement',
            'reference_paiement', 'notes', 'cree_par', 'valide_par',
            'date_creation', 'date_modification', 'statut_color'
        ]
        read_only_fields = [
            'date_creation', 'date_modification', 'cree_par', 'valide_par',
            'date_encaissement', 'statut_color'
        ]
    
    def validate_montant(self, value):
        """Valider que le montant est positif."""
        if value <= 0:
            raise serializers.ValidationError("Le montant doit être positif.")
        return value
    
    def validate(self, data):
        """Validation globale du paiement."""
        # Validation spécifique selon le mode de paiement
        mode_paiement = data.get('mode_paiement')
        
        if mode_paiement == 'cheque' and not data.get('numero_cheque'):
            raise serializers.ValidationError({
                'numero_cheque': 'Le numéro de chèque est requis pour un paiement par chèque.'
            })
        
        if mode_paiement == 'virement' and not data.get('reference_virement'):
            raise serializers.ValidationError({
                'reference_virement': 'La référence de virement est requise pour un paiement par virement.'
            })
        
        return data


class PaiementDetailSerializer(PaiementSerializer):
    """Sérialiseur détaillé pour les paiements (version détail)."""
    
    # Informations du contrat avec plus de détails
    contrat_numero = serializers.CharField(source='contrat.numero_contrat', read_only=True)
    locataire_nom = serializers.CharField(source='contrat.locataire.nom', read_only=True)
    locataire_prenom = serializers.CharField(source='contrat.locataire.prenom', read_only=True)
    propriete_titre = serializers.CharField(source='contrat.propriete.titre', read_only=True)
    propriete_adresse = serializers.CharField(source='contrat.propriete.adresse', read_only=True)
    bailleur_nom = serializers.CharField(source='contrat.propriete.bailleur.nom', read_only=True)
    
    # Informations calculées
    type_paiement_display = serializers.CharField(source='get_type_paiement_display', read_only=True)
    mode_paiement_display = serializers.CharField(source='get_mode_paiement_display', read_only=True)
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    
    # Métadonnées
    jours_depuis_creation = serializers.SerializerMethodField()
    est_en_retard = serializers.SerializerMethodField()
    
    class Meta(PaiementSerializer.Meta):
        fields = PaiementSerializer.Meta.fields + [
            'contrat_numero', 'locataire_nom', 'locataire_prenom',
            'propriete_titre', 'propriete_adresse', 'bailleur_nom',
            'type_paiement_display', 'mode_paiement_display', 'statut_display',
            'jours_depuis_creation', 'est_en_retard'
        ]
    
    def get_jours_depuis_creation(self, obj):
        """Calculer le nombre de jours depuis la création."""
        from django.utils import timezone
        delta = timezone.now().date() - obj.date_creation.date()
        return delta.days
    
    def get_est_en_retard(self, obj):
        """Déterminer si le paiement est en retard."""
        from django.utils import timezone
        if obj.statut == 'valide':
            return False
        
        # Un paiement est considéré en retard s'il n'est pas validé
        # et que sa date de paiement est antérieure à aujourd'hui
        return obj.date_paiement < timezone.now().date()


class PaiementCreateUpdateSerializer(serializers.ModelSerializer):
    """Sérialiseur pour la création et modification de paiements."""
    
    class Meta:
        model = Paiement
        fields = [
            'contrat', 'montant', 'type_paiement', 'mode_paiement',
            'date_paiement', 'numero_cheque', 'reference_virement',
            'reference_paiement', 'notes'
        ]
    
    def validate_montant(self, value):
        """Valider que le montant est positif."""
        if value <= 0:
            raise serializers.ValidationError("Le montant doit être positif.")
        return value
    
    def validate(self, data):
        """Validation globale du paiement."""
        # Validation spécifique selon le mode de paiement
        mode_paiement = data.get('mode_paiement')
        
        if mode_paiement == 'cheque' and not data.get('numero_cheque'):
            raise serializers.ValidationError({
                'numero_cheque': 'Le numéro de chèque est requis pour un paiement par chèque.'
            })
        
        if mode_paiement == 'virement' and not data.get('reference_virement'):
            raise serializers.ValidationError({
                'reference_virement': 'La référence de virement est requise pour un paiement par virement.'
            })
        
        # Validation selon le type de paiement
        contrat = data.get('contrat')
        type_paiement = data.get('type_paiement')
        montant = data.get('montant')
        
        # Validation des montants - DÉSACTIVÉE pour permettre tous les paiements
        # Les montants sont validés côté base de données et dans les vues
        # Cette validation était trop restrictive et bloquait les paiements valides
        
        return data


class PaiementStatistiquesSerializer(serializers.Serializer):
    """Sérialiseur pour les statistiques des paiements."""
    
    total = serializers.IntegerField()
    valides = serializers.IntegerField()
    en_attente = serializers.IntegerField()
    refuses = serializers.IntegerField()
    montant_total = serializers.DecimalField(max_digits=12, decimal_places=2)
    
    # Statistiques par type
    par_type = serializers.ListField(child=serializers.DictField())
    
    # Statistiques par mode
    par_mode = serializers.ListField(child=serializers.DictField())
    
    # Évolution mensuelle
    evolution_mensuelle = serializers.ListField(child=serializers.DictField())


class PaiementRetardSerializer(serializers.Serializer):
    """Sérialiseur pour les paiements en retard."""
    
    contrat = serializers.DictField()
    date_echeance = serializers.DateField()
    jours_retard = serializers.IntegerField()
    montant_du = serializers.DecimalField(max_digits=10, decimal_places=2)
