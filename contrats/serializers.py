from rest_framework import serializers
from .models import Contrat, Quittance, EtatLieux
from proprietes.serializers import ProprieteSerializer, LocataireSerializer
from utilisateurs.serializers import UtilisateurSerializer


class QuittanceSerializer(serializers.ModelSerializer):
    """Sérialiseur pour les quittances."""
    
    class Meta:
        model = Quittance
        fields = [
            'id', 'contrat', 'mois', 'montant_loyer', 'montant_charges', 
            'montant_total', 'date_creation', 'date_emission', 'numero_quittance'
        ]
        read_only_fields = ['montant_total', 'numero_quittance']


class EtatLieuxSerializer(serializers.ModelSerializer):
    """Sérialiseur pour les états des lieux."""
    
    cree_par = UtilisateurSerializer(read_only=True)
    
    class Meta:
        model = EtatLieux
        fields = [
            'id', 'contrat', 'type_etat', 'date_etat', 'observations_generales',
            'etat_murs', 'etat_sol', 'etat_plomberie', 'etat_electricite',
            'date_creation', 'notes', 'cree_par'
        ]


class ContratSerializer(serializers.ModelSerializer):
    """Sérialiseur pour les contrats (version liste)."""
    
    propriete = ProprieteSerializer(read_only=True)
    locataire = LocataireSerializer(read_only=True)
    cree_par = UtilisateurSerializer(read_only=True)
    statut = serializers.CharField(read_only=True)
    loyer_total = serializers.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        read_only=True,
        source='get_loyer_total'
    )
    duree_mois = serializers.IntegerField(read_only=True, source='get_duree_mois')
    
    class Meta:
        model = Contrat
        fields = [
            'id', 'numero_contrat', 'propriete', 'locataire', 'date_debut', 
            'date_fin', 'date_signature', 'loyer_mensuel', 'charges_mensuelles',
            'depot_garantie', 'jour_paiement', 'mode_paiement', 'est_actif',
            'est_resilie', 'date_resiliation', 'motif_resiliation',
            'date_creation', 'date_modification', 'notes', 'cree_par',
            'statut', 'loyer_total', 'duree_mois'
        ]
        read_only_fields = ['numero_contrat', 'date_creation', 'date_modification']


class ContratDetailSerializer(ContratSerializer):
    """Sérialiseur pour les contrats (version détail avec relations)."""
    
    quittances = QuittanceSerializer(many=True, read_only=True)
    etats_lieux = EtatLieuxSerializer(many=True, read_only=True)
    
    class Meta(ContratSerializer.Meta):
        fields = ContratSerializer.Meta.fields + ['quittances', 'etats_lieux']


class ContratCreateSerializer(serializers.ModelSerializer):
    """Sérialiseur pour la création de contrats."""
    
    class Meta:
        model = Contrat
        fields = [
            'propriete', 'locataire', 'date_debut', 'date_fin', 'date_signature',
            'loyer_mensuel', 'charges_mensuelles', 'depot_garantie',
            'jour_paiement', 'mode_paiement', 'notes'
        ]

    def validate(self, data):
        """Validation personnalisée pour les contrats."""
        # Vérifier que la date de fin est après la date de début
        if data['date_fin'] <= data['date_debut']:
            raise serializers.ValidationError(
                "La date de fin doit être postérieure à la date de début."
            )
        
        # Vérifier que la propriété n'a pas déjà un contrat actif
        propriete = data['propriete']
        if propriete.contrats.filter(est_actif=True, est_resilie=False).exists():
            raise serializers.ValidationError(
                "Cette propriété a déjà un contrat actif."
            )
        
        # Vérifier que le locataire n'a pas déjà un contrat actif
        locataire = data['locataire']
        if locataire.contrats.filter(est_actif=True, est_resilie=False).exists():
            raise serializers.ValidationError(
                "Ce locataire a déjà un contrat actif."
            )
        
        return data


class QuittanceCreateSerializer(serializers.ModelSerializer):
    """Sérialiseur pour la création de quittances."""
    
    class Meta:
        model = Quittance
        fields = ['contrat', 'mois', 'montant_loyer', 'montant_charges']

    def validate(self, data):
        """Validation personnalisée pour les quittances."""
        # Vérifier qu'il n'y a pas déjà une quittance pour ce contrat et ce mois
        contrat = data['contrat']
        mois = data['mois']
        
        if Quittance.objects.filter(contrat=contrat, mois=mois).exists():
            raise serializers.ValidationError(
                "Une quittance existe déjà pour ce contrat et ce mois."
            )
        
        return data


class EtatLieuxCreateSerializer(serializers.ModelSerializer):
    """Sérialiseur pour la création d'états des lieux."""
    
    class Meta:
        model = EtatLieux
        fields = [
            'contrat', 'type_etat', 'date_etat', 'observations_generales',
            'etat_murs', 'etat_sol', 'etat_plomberie', 'etat_electricite', 'notes'
        ]

    def validate(self, data):
        """Validation personnalisée pour les états des lieux."""
        # Vérifier qu'il n'y a pas déjà un état des lieux de ce type pour ce contrat
        contrat = data['contrat']
        type_etat = data['type_etat']
        
        if EtatLieux.objects.filter(contrat=contrat, type_etat=type_etat).exists():
            raise serializers.ValidationError(
                f"Un état des lieux de type '{type_etat}' existe déjà pour ce contrat."
            )
        
        return data


class ContratStatsSerializer(serializers.Serializer):
    """Sérialiseur pour les statistiques des contrats."""
    
    total_contrats = serializers.IntegerField()
    contrats_actifs = serializers.IntegerField()
    contrats_resilies = serializers.IntegerField()
    contrats_expires = serializers.IntegerField()
    revenu_mensuel = serializers.DecimalField(max_digits=10, decimal_places=2)
    contrats_expirant_soon = serializers.IntegerField()


class QuittanceStatsSerializer(serializers.Serializer):
    """Sérialiseur pour les statistiques des quittances."""
    
    total_quittances = serializers.IntegerField()
    montant_total = serializers.DecimalField(max_digits=10, decimal_places=2)
    quittances_mois_courant = serializers.IntegerField()


class EtatLieuxStatsSerializer(serializers.Serializer):
    """Sérialiseur pour les statistiques des états des lieux."""
    
    total_etats = serializers.IntegerField()
    etats_entree = serializers.IntegerField()
    etats_sortie = serializers.IntegerField()
    etats_mois_courant = serializers.IntegerField() 