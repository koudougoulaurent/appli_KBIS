from rest_framework import serializers
from .models import Bailleur, Locataire, TypeBien, Propriete


class TypeBienSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour le modèle TypeBien
    """
    class Meta:
        model = TypeBien
        fields = ['id', 'nom', 'description', 'prix_moyen_m2']


class BailleurSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour le modèle Bailleur
    """
    proprietes_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Bailleur
        fields = [
            'id', 'nom', 'prenom', 'email', 'telephone', 'adresse',
            'ville', 'code_postal', 'pays', 'date_naissance',
            'profession', 'revenus_mensuels', 'proprietes_count',
            'date_creation', 'date_modification'
        ]
        read_only_fields = ['id', 'date_creation', 'date_modification']
    
    def get_proprietes_count(self, obj):
        """Retourne le nombre de propriétés du bailleur"""
        return obj.proprietes.count()


class BailleurListSerializer(serializers.ModelSerializer):
    """
    Sérialiseur simplifié pour la liste des bailleurs
    """
    nom_complet = serializers.SerializerMethodField()
    proprietes_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Bailleur
        fields = [
            'id', 'nom', 'prenom', 'nom_complet', 'email', 
            'telephone', 'ville', 'proprietes_count'
        ]
    
    def get_nom_complet(self, obj):
        """Retourne le nom complet du bailleur"""
        return f"{obj.prenom} {obj.nom}".strip()
    
    def get_proprietes_count(self, obj):
        """Retourne le nombre de propriétés du bailleur"""
        return obj.proprietes.count()


class LocataireSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour le modèle Locataire
    """
    proprietes_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Locataire
        fields = [
            'id', 'nom', 'prenom', 'email', 'telephone', 'adresse',
            'ville', 'code_postal', 'pays', 'date_naissance',
            'profession', 'revenus_mensuels', 'garant_nom',
            'garant_telephone', 'proprietes_count', 'date_creation',
            'date_modification'
        ]
        read_only_fields = ['id', 'date_creation', 'date_modification']
    
    def get_proprietes_count(self, obj):
        """Retourne le nombre de propriétés louées par le locataire"""
        return obj.proprietes.count()


class LocataireListSerializer(serializers.ModelSerializer):
    """
    Sérialiseur simplifié pour la liste des locataires
    """
    nom_complet = serializers.SerializerMethodField()
    proprietes_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Locataire
        fields = [
            'id', 'nom', 'prenom', 'nom_complet', 'email', 
            'telephone', 'ville', 'proprietes_count'
        ]
    
    def get_nom_complet(self, obj):
        """Retourne le nom complet du locataire"""
        return f"{obj.prenom} {obj.nom}".strip()
    
    def get_proprietes_count(self, obj):
        """Retourne le nombre de propriétés louées par le locataire"""
        return obj.proprietes.count()


class ProprieteSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour le modèle Propriete
    """
    bailleur_nom = serializers.CharField(source='bailleur.nom_complet', read_only=True)
    locataire_nom = serializers.CharField(source='locataire.nom_complet', read_only=True)
    type_bien_nom = serializers.CharField(source='type_bien.nom', read_only=True)
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    
    class Meta:
        model = Propriete
        fields = [
            'id', 'reference', 'titre', 'description', 'adresse',
            'ville', 'code_postal', 'pays', 'surface', 'nombre_pieces',
            'nombre_chambres', 'nombre_salles_bain', 'etage',
            'annee_construction', 'prix_achat', 'prix_location',
            'charges_mensuelles', 'statut', 'statut_display',
            'bailleur', 'bailleur_nom', 'locataire', 'locataire_nom',
            'type_bien', 'type_bien_nom', 'date_creation',
            'date_modification'
        ]
        read_only_fields = ['id', 'reference', 'date_creation', 'date_modification']


class ProprieteListSerializer(serializers.ModelSerializer):
    """
    Sérialiseur simplifié pour la liste des propriétés
    """
    bailleur_nom = serializers.CharField(source='bailleur.nom_complet', read_only=True)
    locataire_nom = serializers.CharField(source='locataire.nom_complet', read_only=True)
    type_bien_nom = serializers.CharField(source='type_bien.nom', read_only=True)
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    
    class Meta:
        model = Propriete
        fields = [
            'id', 'reference', 'titre', 'adresse', 'ville',
            'surface', 'nombre_pieces', 'prix_location',
            'statut', 'statut_display', 'bailleur_nom',
            'locataire_nom', 'type_bien_nom'
        ]


class ProprieteCreateSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour la création de propriété
    """
    class Meta:
        model = Propriete
        fields = [
            'titre', 'description', 'adresse', 'ville', 'code_postal',
            'pays', 'surface', 'nombre_pieces', 'nombre_chambres',
            'nombre_salles_bain', 'etage', 'annee_construction',
            'prix_achat', 'prix_location', 'charges_mensuelles',
            'statut', 'bailleur', 'locataire', 'type_bien'
        ]
    
    def validate(self, attrs):
        """Validation personnalisée"""
        # Vérifier que le prix de location est positif
        if attrs.get('prix_location', 0) <= 0:
            raise serializers.ValidationError("Le prix de location doit être positif.")
        
        # Vérifier que la surface est positive
        if attrs.get('surface', 0) <= 0:
            raise serializers.ValidationError("La surface doit être positive.")
        
        return attrs


class ProprieteUpdateSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour la mise à jour de propriété
    """
    class Meta:
        model = Propriete
        fields = [
            'titre', 'description', 'adresse', 'ville', 'code_postal',
            'pays', 'surface', 'nombre_pieces', 'nombre_chambres',
            'nombre_salles_bain', 'etage', 'annee_construction',
            'prix_achat', 'prix_location', 'charges_mensuelles',
            'statut', 'bailleur', 'locataire', 'type_bien'
        ]


class ProprieteDetailSerializer(serializers.ModelSerializer):
    """
    Sérialiseur détaillé pour une propriété
    """
    bailleur = BailleurSerializer(read_only=True)
    locataire = LocataireSerializer(read_only=True)
    type_bien = TypeBienSerializer(read_only=True)
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    
    class Meta:
        model = Propriete
        fields = [
            'id', 'reference', 'titre', 'description', 'adresse',
            'ville', 'code_postal', 'pays', 'surface', 'nombre_pieces',
            'nombre_chambres', 'nombre_salles_bain', 'etage',
            'annee_construction', 'prix_achat', 'prix_location',
            'charges_mensuelles', 'statut', 'statut_display',
            'bailleur', 'locataire', 'type_bien', 'date_creation',
            'date_modification'
        ] 