from rest_framework import serializers
from .models import Utilisateur


class UtilisateurSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour le modèle Utilisateur
    """
    nom_complet = serializers.SerializerMethodField()
    groupe_display = serializers.CharField(source='get_groupe_display', read_only=True)
    
    class Meta:
        model = Utilisateur
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 
            'nom_complet', 'groupe', 'groupe_display', 'telephone',
            'adresse', 'date_naissance', 'date_embauche', 'salaire',
            'is_active', 'date_joined', 'last_login'
        ]
        read_only_fields = ['id', 'date_joined', 'last_login']
        extra_kwargs = {
            'password': {'write_only': True}
        }
    
    def get_nom_complet(self, obj):
        """Retourne le nom complet de l'utilisateur"""
        return f"{obj.first_name} {obj.last_name}".strip()
    
    def create(self, validated_data):
        """Créer un nouvel utilisateur avec mot de passe hashé"""
        password = validated_data.pop('password', None)
        user = super().create(validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user


class UtilisateurListSerializer(serializers.ModelSerializer):
    """
    Sérialiseur simplifié pour la liste des utilisateurs
    """
    nom_complet = serializers.SerializerMethodField()
    groupe_display = serializers.CharField(source='get_groupe_display', read_only=True)
    
    class Meta:
        model = Utilisateur
        fields = [
            'id', 'username', 'email', 'nom_complet', 
            'groupe', 'groupe_display', 'telephone', 'is_active'
        ]
    
    def get_nom_complet(self, obj):
        """Retourne le nom complet de l'utilisateur"""
        return f"{obj.first_name} {obj.last_name}".strip()


class UtilisateurCreateSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour la création d'utilisateur
    """
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = Utilisateur
        fields = [
            'username', 'email', 'password', 'password_confirm',
            'first_name', 'last_name', 'groupe', 'telephone',
            'adresse', 'date_naissance', 'date_embauche', 'salaire'
        ]
    
    def validate(self, attrs):
        """Validation personnalisée"""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Les mots de passe ne correspondent pas.")
        return attrs
    
    def create(self, validated_data):
        """Créer un nouvel utilisateur"""
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = Utilisateur.objects.create(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UtilisateurUpdateSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour la mise à jour d'utilisateur
    """
    class Meta:
        model = Utilisateur
        fields = [
            'email', 'first_name', 'last_name', 'groupe', 
            'telephone', 'adresse', 'date_naissance', 
            'date_embauche', 'salaire', 'is_active'
        ] 