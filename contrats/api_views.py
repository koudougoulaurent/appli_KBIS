from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import date

from .models import Contrat, Quittance, EtatLieux
from .serializers import (
    ContratSerializer, 
    QuittanceSerializer, 
    EtatLieuxSerializer,
    ContratDetailSerializer
)


class ContratViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des contrats via API REST.
    """
    queryset = Contrat.objects.all()
    serializer_class = ContratSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['est_actif', 'est_resilie', 'mode_paiement', 'propriete__ville']
    search_fields = ['numero_contrat', 'propriete__titre', 'locataire__nom', 'locataire__prenom']
    ordering_fields = ['date_debut', 'date_fin', 'loyer_mensuel', 'date_creation']
    ordering = ['-date_debut']

    def get_serializer_class(self):
        """Retourne le serializer approprié selon l'action."""
        if self.action == 'retrieve':
            return ContratDetailSerializer
        return ContratSerializer

    def perform_create(self, serializer):
        """Assigne l'utilisateur connecté comme créateur."""
        serializer.save(cree_par=self.request.user)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Retourne les statistiques des contrats."""
        total_contrats = Contrat.objects.count()
        contrats_actifs = Contrat.objects.filter(est_actif=True, est_resilie=False).count()
        contrats_resilies = Contrat.objects.filter(est_resilie=True).count()
        contrats_expires = Contrat.objects.filter(date_fin__lt=date.today()).count()
        
        # Calcul du revenu mensuel total
        revenu_mensuel = Contrat.objects.filter(
            est_actif=True, 
            est_resilie=False
        ).aggregate(
            total=Sum('loyer_mensuel')
        )['total'] or 0
        
        # Contrats expirant dans les 30 prochains jours
        date_limite = date.today() + timezone.timedelta(days=30)
        contrats_expirant_soon = Contrat.objects.filter(
            date_fin__lte=date_limite,
            date_fin__gte=date.today(),
            est_actif=True,
            est_resilie=False
        ).count()

        return Response({
            'total_contrats': total_contrats,
            'contrats_actifs': contrats_actifs,
            'contrats_resilies': contrats_resilies,
            'contrats_expires': contrats_expires,
            'revenu_mensuel': float(revenu_mensuel),
            'contrats_expirant_soon': contrats_expirant_soon,
        })

    @action(detail=False, methods=['get'])
    def actifs(self, request):
        """Retourne uniquement les contrats actifs."""
        contrats = Contrat.objects.filter(est_actif=True, est_resilie=False)
        page = self.paginate_queryset(contrats)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(contrats, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def expirant_soon(self, request):
        """Retourne les contrats expirant dans les 30 prochains jours."""
        date_limite = date.today() + timezone.timedelta(days=30)
        contrats = Contrat.objects.filter(
            date_fin__lte=date_limite,
            date_fin__gte=date.today(),
            est_actif=True,
            est_resilie=False
        )
        page = self.paginate_queryset(contrats)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(contrats, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def resilier(self, request, pk=None):
        """Résilie un contrat."""
        contrat = self.get_object()
        motif = request.data.get('motif', '')
        
        if contrat.est_resilie:
            return Response(
                {'error': 'Ce contrat est déjà résilié.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        contrat.est_resilie = True
        contrat.date_resiliation = date.today()
        contrat.motif_resiliation = motif
        contrat.save()
        
        return Response({'message': 'Contrat résilié avec succès.'})

    @action(detail=True, methods=['post'])
    def reactiver(self, request, pk=None):
        """Réactive un contrat résilié."""
        contrat = self.get_object()
        
        if not contrat.est_resilie:
            return Response(
                {'error': 'Ce contrat n\'est pas résilié.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        contrat.est_resilie = False
        contrat.date_resiliation = None
        contrat.motif_resiliation = ''
        contrat.save()
        
        return Response({'message': 'Contrat réactivé avec succès.'})

    @action(detail=True, methods=['get'])
    def quittances(self, request, pk=None):
        """Retourne les quittances d'un contrat."""
        contrat = self.get_object()
        quittances = contrat.quittances.all()
        serializer = QuittanceSerializer(quittances, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def etats_lieux(self, request, pk=None):
        """Retourne les états des lieux d'un contrat."""
        contrat = self.get_object()
        etats_lieux = contrat.etats_lieux.all()
        serializer = EtatLieuxSerializer(etats_lieux, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def par_ville(self, request):
        """Retourne les contrats groupés par ville."""
        contrats = Contrat.objects.values('propriete__ville').annotate(
            total=Count('id'),
            actifs=Count('id', filter=Q(est_actif=True, est_resilie=False))
        ).order_by('-total')
        
        return Response(contrats)

    @action(detail=False, methods=['get'])
    def par_prix(self, request):
        """Retourne les contrats groupés par fourchette de prix."""
        contrats = Contrat.objects.extra(
            select={
                'fourchette': """
                    CASE 
                                    WHEN loyer_mensuel < 500 THEN '0-500 F CFA'
            WHEN loyer_mensuel < 1000 THEN '500-1000 F CFA'
            WHEN loyer_mensuel < 1500 THEN '1000-1500 F CFA'
            WHEN loyer_mensuel < 2000 THEN '1500-2000 F CFA'
            ELSE '2000 F CFA+'
                    END
                """
            }
        ).values('fourchette').annotate(
            total=Count('id'),
            actifs=Count('id', filter=Q(est_actif=True, est_resilie=False))
        ).order_by('fourchette')
        
        return Response(contrats)


class QuittanceViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des quittances via API REST.
    """
    queryset = Quittance.objects.all()
    serializer_class = QuittanceSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['contrat__numero_contrat', 'mois']
    search_fields = ['numero_quittance', 'contrat__numero_contrat']
    ordering_fields = ['mois', 'date_creation', 'montant_total']
    ordering = ['-mois']

    def perform_create(self, serializer):
        """Assigne l'utilisateur connecté comme créateur."""
        serializer.save()

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Retourne les statistiques des quittances."""
        total_quittances = Quittance.objects.count()
        montant_total = Quittance.objects.aggregate(
            total=Sum('montant_total')
        )['total'] or 0
        
        # Quittances du mois en cours
        mois_courant = date.today().replace(day=1)
        quittances_mois = Quittance.objects.filter(mois=mois_courant).count()
        
        return Response({
            'total_quittances': total_quittances,
            'montant_total': float(montant_total),
            'quittances_mois_courant': quittances_mois,
        })


class EtatLieuxViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des états des lieux via API REST.
    """
    queryset = EtatLieux.objects.all()
    serializer_class = EtatLieuxSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['contrat__numero_contrat', 'type_etat']
    search_fields = ['contrat__numero_contrat']
    ordering_fields = ['date_etat', 'date_creation']
    ordering = ['-date_etat']

    def perform_create(self, serializer):
        """Assigne l'utilisateur connecté comme créateur."""
        serializer.save(cree_par=self.request.user)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Retourne les statistiques des états des lieux."""
        total_etats = EtatLieux.objects.count()
        etats_entree = EtatLieux.objects.filter(type_etat='entree').count()
        etats_sortie = EtatLieux.objects.filter(type_etat='sortie').count()
        
        # États des lieux du mois en cours
        mois_courant = date.today().replace(day=1)
        etats_mois = EtatLieux.objects.filter(
            date_etat__gte=mois_courant
        ).count()
        
        return Response({
            'total_etats': total_etats,
            'etats_entree': etats_entree,
            'etats_sortie': etats_sortie,
            'etats_mois_courant': etats_mois,
        }) 


class CautionViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des cautions et avances via API REST.
    """
    queryset = Contrat.objects.filter(
        est_actif=True, 
        est_resilie=False
    ).select_related(
        'locataire', 
        'propriete', 
        'propriete__bailleur'
    ).order_by('-date_creation')
    
    serializer_class = ContratDetailSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    filterset_fields = {
        'caution_requise': ['exact'],
        'caution_payee': ['exact'],
        'avance_requise': ['exact'],
        'avance_payee': ['exact'],
        'propriete__ville': ['exact'],
        'propriete__bailleur': ['exact'],
    }
    
    search_fields = [
        'numero_contrat',
        'propriete__titre',
        'locataire__nom',
        'locataire__prenom'
    ]
    
    ordering_fields = [
        'date_creation',
        'caution_montant',
        'avance_montant',
        'loyer_mensuel'
    ]
    
    ordering = ['-date_creation']
    
    def get_queryset(self):
        """Filtrer les contrats selon les paramètres de requête."""
        queryset = super().get_queryset()
        
        # Filtres additionnels
        statut_caution = self.request.query_params.get('statut_caution')
        statut_avance = self.request.query_params.get('statut_avance')
        
        if statut_caution == 'payee':
            queryset = queryset.filter(caution_payee=True)
        elif statut_caution == 'non_payee':
            queryset = queryset.filter(caution_payee=False, caution_requise=True)
            
        if statut_avance == 'payee':
            queryset = queryset.filter(avance_payee=True)
        elif statut_avance == 'non_payee':
            queryset = queryset.filter(avance_payee=False, avance_requise=True)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def statistiques(self, request):
        """Obtenir les statistiques des cautions et avances."""
        queryset = self.get_queryset()
        
        # Statistiques des cautions
        total_cautions_requises = queryset.filter(caution_requise=True).count()
        total_cautions_payees = queryset.filter(caution_payee=True).count()
        total_cautions_en_attente = queryset.filter(
            caution_requise=True, 
            caution_payee=False
        ).count()
        
        # Montants des cautions
        montant_cautions_payees = queryset.filter(
            caution_payee=True
        ).aggregate(
            total=Sum('caution_montant')
        )['total'] or 0
        
        montant_cautions_en_attente = queryset.filter(
            caution_requise=True, 
            caution_payee=False
        ).aggregate(
            total=Sum('caution_montant')
        )['total'] or 0
        
        # Statistiques des avances
        total_avances_requises = queryset.filter(avance_requise=True).count()
        total_avances_payees = queryset.filter(avance_payee=True).count()
        total_avances_en_attente = queryset.filter(
            avance_requise=True, 
            avance_payee=False
        ).count()
        
        # Montants des avances
        montant_avances_payees = queryset.filter(
            avance_payee=True
        ).aggregate(
            total=Sum('avance_montant')
        )['total'] or 0
        
        montant_avances_en_attente = queryset.filter(
            avance_requise=True, 
            avance_payee=False
        ).aggregate(
            total=Sum('avance_montant')
        )['total'] or 0
        
        return Response({
            'cautions': {
                'total_requises': total_cautions_requises,
                'total_payees': total_cautions_payees,
                'total_en_attente': total_cautions_en_attente,
                'montant_paye': float(montant_cautions_payees),
                'montant_en_attente': float(montant_cautions_en_attente),
            },
            'avances': {
                'total_requises': total_avances_requises,
                'total_payees': total_avances_payees,
                'total_en_attente': total_avances_en_attente,
                'montant_paye': float(montant_avances_payees),
                'montant_en_attente': float(montant_avances_en_attente),
            },
            'total_contrats': queryset.count(),
        })
    
    @action(detail=True, methods=['post'])
    def marquer_caution_payee(self, request, pk=None):
        """Marquer la caution comme payée."""
        # Vérification des permissions
        from core.utils import check_group_permissions
        permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE', 'CAISSE'], 'modify')
        if not permissions['allowed']:
            return Response(
                {'error': f'Permissions insuffisantes. {permissions["message"]}'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        contrat = self.get_object()
        
        if contrat.caution_payee:
            return Response(
                {'error': 'La caution est déjà marquée comme payée.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        contrat.caution_payee = True
        contrat.date_paiement_caution = timezone.now().date()
        contrat.save()
        
        return Response({
            'message': 'Caution marquée comme payée avec succès.',
            'contrat': ContratDetailSerializer(contrat).data
        })
    
    @action(detail=True, methods=['post'])
    def marquer_avance_payee(self, request, pk=None):
        """Marquer l'avance comme payée."""
        # Vérification des permissions
        from core.utils import check_group_permissions
        permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE', 'CAISSE'], 'modify')
        if not permissions['allowed']:
            return Response(
                {'error': f'Permissions insuffisantes. {permissions["message"]}'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        contrat = self.get_object()
        
        if contrat.avance_payee:
            return Response(
                {'error': 'L\'avance est déjà marquée comme payée.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        contrat.avance_payee = True
        contrat.date_paiement_avance = timezone.now().date()
        contrat.save()
        
        return Response({
            'message': 'Avance marquée comme payée avec succès.',
            'contrat': ContratDetailSerializer(contrat).data
        })
    
    @action(detail=True, methods=['get'])
    def recu_caution(self, request, pk=None):
        """Obtenir les informations du reçu de caution."""
        # Vérification des permissions
        from core.utils import check_group_permissions
        permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE', 'CAISSE'], 'view')
        if not permissions['allowed']:
            return Response(
                {'error': f'Permissions insuffisantes. {permissions["message"]}'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        contrat = self.get_object()
        
        if not contrat.caution_payee:
            return Response(
                {'error': 'La caution n\'est pas encore payée.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Simuler les données du reçu (à adapter selon votre modèle RecuCaution)
        recu_data = {
            'contrat': ContratDetailSerializer(contrat).data,
            'type_recu': 'caution',
            'montant': contrat.caution_montant,
            'date_paiement': contrat.date_paiement_caution,
            'reference': f"RECU-CAUTION-{contrat.numero_contrat}",
        }
        
        return Response(recu_data) 