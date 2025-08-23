from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count, Avg, Sum
from django.db.models.functions import Coalesce

from .models import Bailleur, Locataire, TypeBien, Propriete
from .serializers import (
    BailleurSerializer, BailleurListSerializer,
    LocataireSerializer, LocataireListSerializer,
    TypeBienSerializer,
    ProprieteSerializer, ProprieteListSerializer,
    ProprieteCreateSerializer, ProprieteUpdateSerializer,
    ProprieteDetailSerializer
)


class TypeBienViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des types de biens
    """
    queryset = TypeBien.objects.all()
    serializer_class = TypeBienSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nom', 'description']
    ordering_fields = ['nom', 'prix_moyen_m2']
    ordering = ['nom']
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Statistiques des types de biens"""
        stats = TypeBien.objects.annotate(
            proprietes_count=Count('propriete'),
            prix_moyen_location=Avg('propriete__loyer_actuel')
        ).values('id', 'nom', 'proprietes_count', 'prix_moyen_location')
        
        return Response(stats)


class BailleurViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des bailleurs
    """
    queryset = Bailleur.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['ville', 'pays']
    search_fields = ['nom', 'prenom', 'email', 'telephone', 'ville']
    ordering_fields = ['nom', 'prenom', 'date_creation']
    ordering = ['nom', 'prenom']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return BailleurListSerializer
        return BailleurSerializer
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Statistiques des bailleurs"""
        total_bailleurs = Bailleur.objects.count()
        bailleurs_avec_proprietes = Bailleur.objects.annotate(
            proprietes_count=Count('propriete')
        ).filter(proprietes_count__gt=0).count()
        
        # Top 5 des bailleurs avec le plus de propriétés
        top_bailleurs = Bailleur.objects.annotate(
            proprietes_count=Count('propriete')
        ).order_by('-proprietes_count')[:5]
        
        return Response({
            'total_bailleurs': total_bailleurs,
            'bailleurs_avec_proprietes': bailleurs_avec_proprietes,
            'top_bailleurs': BailleurListSerializer(top_bailleurs, many=True).data
        })
    
    @action(detail=True, methods=['get'])
    def proprietes(self, request, pk=None):
        """Récupérer les propriétés d'un bailleur"""
        bailleur = self.get_object()
        proprietes = bailleur.propriete_set.all()
        serializer = ProprieteListSerializer(proprietes, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """Recherche avancée de bailleurs"""
        query = request.query_params.get('q', '')
        if not query:
            return Response(
                {'error': 'Paramètre de recherche requis'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        bailleurs = Bailleur.objects.filter(
            Q(nom__icontains=query) |
            Q(prenom__icontains=query) |
            Q(email__icontains=query) |
            Q(telephone__icontains=query) |
            Q(ville__icontains=query)
        )
        
        serializer = BailleurListSerializer(bailleurs, many=True)
        return Response(serializer.data)


class LocataireViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des locataires
    """
    queryset = Locataire.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['ville', 'pays']
    search_fields = ['nom', 'prenom', 'email', 'telephone', 'ville']
    ordering_fields = ['nom', 'prenom', 'date_creation']
    ordering = ['nom', 'prenom']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return LocataireListSerializer
        return LocataireSerializer
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Statistiques des locataires"""
        total_locataires = Locataire.objects.count()
        # Locataires actifs (avec contrats actifs)
        locataires_actifs = Locataire.objects.filter(
            contrats__est_actif=True,
            contrats__est_resilie=False
        ).distinct().count()
        
        # Top 5 des locataires avec le plus de propriétés
        top_locataires = Locataire.objects.annotate(
            proprietes_count=Count('propriete')
        ).order_by('-proprietes_count')[:5]
        
        return Response({
            'total_locataires': total_locataires,
            'locataires_actifs': locataires_actifs,
            'top_locataires': LocataireListSerializer(top_locataires, many=True).data
        })
    
    @action(detail=True, methods=['get'])
    def proprietes(self, request, pk=None):
        """Récupérer les propriétés d'un locataire"""
        locataire = self.get_object()
        proprietes = locataire.propriete_set.all()
        serializer = ProprieteListSerializer(proprietes, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """Recherche avancée de locataires"""
        query = request.query_params.get('q', '')
        if not query:
            return Response(
                {'error': 'Paramètre de recherche requis'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        locataires = Locataire.objects.filter(
            Q(nom__icontains=query) |
            Q(prenom__icontains=query) |
            Q(email__icontains=query) |
            Q(telephone__icontains=query) |
            Q(ville__icontains=query)
        )
        
        serializer = LocataireListSerializer(locataires, many=True)
        return Response(serializer.data)


class ProprieteViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des propriétés
    """
    queryset = Propriete.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['ville', 'type_bien', 'bailleur', 'disponible', 'etat']
    search_fields = ['reference', 'titre', 'adresse', 'ville', 'description']
    ordering_fields = [
        'reference', 'titre', 'loyer_actuel', 'surface', 
        'date_creation', 'date_modification'
    ]
    ordering = ['-date_creation']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ProprieteCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return ProprieteUpdateSerializer
        elif self.action == 'retrieve':
            return ProprieteDetailSerializer
        elif self.action == 'list':
            return ProprieteListSerializer
        return ProprieteSerializer
    
    def get_queryset(self):
        """Filtrer les propriétés selon les paramètres"""
        queryset = super().get_queryset()
        
        # Filtres supplémentaires
        prix_min = self.request.query_params.get('prix_min', None)
        prix_max = self.request.query_params.get('prix_max', None)
        surface_min = self.request.query_params.get('surface_min', None)
        surface_max = self.request.query_params.get('surface_max', None)
        
        if prix_min:
            queryset = queryset.filter(loyer_actuel__gte=prix_min)
        if prix_max:
            queryset = queryset.filter(loyer_actuel__lte=prix_max)
        if surface_min:
            queryset = queryset.filter(surface__gte=surface_min)
        if surface_max:
            queryset = queryset.filter(surface__lte=surface_max)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Statistiques des propriétés"""
        from django.db.models import Q
        
        total_proprietes = Propriete.objects.count()
        
        # Propriétés louées (avec contrats actifs)
        proprietes_louees = Propriete.objects.filter(
            contrats__est_actif=True,
            contrats__est_resilie=False
        ).distinct().count()
        
        # Propriétés disponibles (pas de contrats actifs et marquées comme disponibles)
        proprietes_disponibles = Propriete.objects.filter(
            disponible=True
        ).exclude(
            contrats__est_actif=True,
            contrats__est_resilie=False
        ).count()
        
        # Propriétés en construction (état 'a_renover' ou similaire)
        proprietes_en_construction = Propriete.objects.filter(
            etat='a_renover'
        ).count()
        
        # Valeur totale du patrimoine
        valeur_totale = Propriete.objects.aggregate(
            total=Coalesce(Sum('prix_achat'), 0)
        )['total']
        
        # Revenus locatifs mensuels (propriétés avec loyer actuel)
        revenus_mensuels = Propriete.objects.filter(
            loyer_actuel__gt=0
        ).aggregate(
            total=Coalesce(Sum('loyer_actuel'), 0)
        )['total']
        
        # Prix moyen au m²
        prix_moyen_m2 = Propriete.objects.aggregate(
            moyenne=Coalesce(Avg('loyer_actuel'), 0)
        )['moyenne']
        
        return Response({
            'total_proprietes': total_proprietes,
            'proprietes_louees': proprietes_louees,
            'proprietes_disponibles': proprietes_disponibles,
            'proprietes_en_construction': proprietes_en_construction,
            'valeur_totale': valeur_totale,
            'revenus_mensuels': revenus_mensuels,
            'prix_moyen_m2': prix_moyen_m2
        })
    
    @action(detail=False, methods=['get'])
    def disponibles(self, request):
        """Récupérer les propriétés disponibles"""
        proprietes = Propriete.objects.filter(
            disponible=True
        ).exclude(
            contrats__est_actif=True,
            contrats__est_resilie=False
        )
        serializer = ProprieteListSerializer(proprietes, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def louees(self, request):
        """Récupérer les propriétés louées"""
        proprietes = Propriete.objects.filter(
            contrats__est_actif=True,
            contrats__est_resilie=False
        ).distinct()
        serializer = ProprieteListSerializer(proprietes, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def louer(self, request, pk=None):
        """Louer une propriété"""
        propriete = self.get_object()
        locataire_id = request.data.get('locataire_id')
        
        if not locataire_id:
            return Response(
                {'error': 'ID du locataire requis'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            locataire = Locataire.objects.get(id=locataire_id)
            # Marquer la propriété comme non disponible
            propriete.disponible = False
            propriete.save()
            
            serializer = ProprieteDetailSerializer(propriete)
            return Response(serializer.data)
        except Locataire.DoesNotExist:
            return Response(
                {'error': 'Locataire non trouvé'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def liberer(self, request, pk=None):
        """Libérer une propriété"""
        propriete = self.get_object()
        # Marquer la propriété comme disponible
        propriete.disponible = True
        propriete.save()
        
        serializer = ProprieteDetailSerializer(propriete)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """Recherche avancée de propriétés"""
        query = request.query_params.get('q', '')
        if not query:
            return Response(
                {'error': 'Paramètre de recherche requis'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        proprietes = Propriete.objects.filter(
            Q(reference__icontains=query) |
            Q(titre__icontains=query) |
            Q(adresse__icontains=query) |
            Q(ville__icontains=query) |
            Q(description__icontains=query)
        )
        
        serializer = ProprieteListSerializer(proprietes, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def par_ville(self, request):
        """Propriétés groupées par ville"""
        ville = request.query_params.get('ville', '')
        if not ville:
            return Response(
                {'error': 'Paramètre ville requis'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        proprietes = Propriete.objects.filter(ville__icontains=ville)
        serializer = ProprieteListSerializer(proprietes, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def par_prix(self, request):
        """Propriétés dans une fourchette de prix"""
        prix_min = request.query_params.get('prix_min', 0)
        prix_max = request.query_params.get('prix_max', 999999)
        
        proprietes = Propriete.objects.filter(
            loyer_actuel__gte=prix_min,
            loyer_actuel__lte=prix_max
        )
        serializer = ProprieteListSerializer(proprietes, many=True)
        return Response(serializer.data) 