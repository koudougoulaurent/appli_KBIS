from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth import authenticate
from django.db.models import Q

from .models import Utilisateur
from .serializers import (
    UtilisateurSerializer, 
    UtilisateurListSerializer,
    UtilisateurCreateSerializer,
    UtilisateurUpdateSerializer
)


class UtilisateurViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des utilisateurs via API
    """
    queryset = Utilisateur.objects.all()
    permission_classes = [IsAuthenticated, IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['groupe', 'is_active', 'date_joined']
    search_fields = ['username', 'email', 'first_name', 'last_name', 'telephone']
    ordering_fields = ['username', 'first_name', 'last_name', 'date_joined', 'last_login']
    ordering = ['-date_joined']
    
    def get_serializer_class(self):
        """Retourne le sérialiseur approprié selon l'action"""
        if self.action == 'create':
            return UtilisateurCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return UtilisateurUpdateSerializer
        elif self.action == 'list':
            return UtilisateurListSerializer
        return UtilisateurSerializer
    
    def get_queryset(self):
        """Filtrer les utilisateurs selon les permissions"""
        queryset = super().get_queryset()
        
        # Filtres supplémentaires
        groupe = self.request.query_params.get('groupe', None)
        if groupe:
            queryset = queryset.filter(groupe=groupe)
        
        is_active = self.request.query_params.get('is_active', None)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Statistiques des utilisateurs"""
        total_users = Utilisateur.objects.count()
        active_users = Utilisateur.objects.filter(is_active=True).count()
        inactive_users = total_users - active_users
        
        # Statistiques par groupe
        groupe_stats = {}
        for groupe, _ in Utilisateur.GROUPE_CHOICES:
            count = Utilisateur.objects.filter(groupe=groupe).count()
            groupe_stats[groupe] = count
        
        return Response({
            'total_users': total_users,
            'active_users': active_users,
            'inactive_users': inactive_users,
            'groupe_stats': groupe_stats
        })
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activer un utilisateur"""
        user = self.get_object()
        user.is_active = True
        user.save()
        return Response({'status': 'Utilisateur activé'})
    
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Désactiver un utilisateur"""
        user = self.get_object()
        user.is_active = False
        user.save()
        return Response({'status': 'Utilisateur désactivé'})
    
    @action(detail=True, methods=['post'])
    def reset_password(self, request, pk=None):
        """Réinitialiser le mot de passe d'un utilisateur"""
        user = self.get_object()
        new_password = request.data.get('new_password')
        
        if not new_password:
            return Response(
                {'error': 'Nouveau mot de passe requis'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user.set_password(new_password)
        user.save()
        return Response({'status': 'Mot de passe réinitialisé'})
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """Recherche avancée d'utilisateurs"""
        query = request.query_params.get('q', '')
        if not query:
            return Response(
                {'error': 'Paramètre de recherche requis'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        users = Utilisateur.objects.filter(
            Q(username__icontains=query) |
            Q(email__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(telephone__icontains=query)
        )
        
        serializer = UtilisateurListSerializer(users, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Récupérer les informations de l'utilisateur connecté"""
        serializer = UtilisateurSerializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def bulk_activate(self, request):
        """Activer plusieurs utilisateurs en masse"""
        user_ids = request.data.get('user_ids', [])
        if not user_ids:
            return Response(
                {'error': 'Liste d\'utilisateurs requise'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        Utilisateur.objects.filter(id__in=user_ids).update(is_active=True)
        return Response({'status': f'{len(user_ids)} utilisateurs activés'})
    
    @action(detail=False, methods=['post'])
    def bulk_deactivate(self, request):
        """Désactiver plusieurs utilisateurs en masse"""
        user_ids = request.data.get('user_ids', [])
        if not user_ids:
            return Response(
                {'error': 'Liste d\'utilisateurs requise'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        Utilisateur.objects.filter(id__in=user_ids).update(is_active=False)
        return Response({'status': f'{len(user_ids)} utilisateurs désactivés'})


class UtilisateurAuthViewSet(viewsets.ViewSet):
    """
    ViewSet pour l'authentification des utilisateurs
    """
    permission_classes = []
    
    @action(detail=False, methods=['post'])
    def login(self, request):
        """Authentification d'un utilisateur"""
        username = request.data.get('username')
        password = request.data.get('password')
        
        if not username or not password:
            return Response(
                {'error': 'Nom d\'utilisateur et mot de passe requis'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = authenticate(username=username, password=password)
        if user is None:
            return Response(
                {'error': 'Identifiants invalides'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        if not user.is_active:
            return Response(
                {'error': 'Compte désactivé'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        serializer = UtilisateurSerializer(user)
        return Response({
            'user': serializer.data,
            'message': 'Connexion réussie'
        })
    
    @action(detail=False, methods=['post'])
    def change_password(self, request):
        """Changer le mot de passe de l'utilisateur connecté"""
        user = request.user
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')
        
        if not user.check_password(old_password):
            return Response(
                {'error': 'Ancien mot de passe incorrect'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user.set_password(new_password)
        user.save()
        return Response({'message': 'Mot de passe modifié avec succès'}) 