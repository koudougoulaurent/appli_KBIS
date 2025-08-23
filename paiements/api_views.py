from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import date

from .models import Paiement
from .serializers import PaiementSerializer, PaiementDetailSerializer


class PaiementViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des paiements via API REST.
    """
    queryset = Paiement.objects.select_related(
        'contrat__locataire',
        'contrat__propriete',
        'contrat__propriete__bailleur'
    ).order_by('-date_creation')
    
    serializer_class = PaiementSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    filterset_fields = {
        'type_paiement': ['exact'],
        'mode_paiement': ['exact'],
        'statut': ['exact'],
        'date_paiement': ['gte', 'lte', 'exact'],
        'montant': ['gte', 'lte', 'exact'],
        'contrat': ['exact'],
        'contrat__propriete': ['exact'],
        'contrat__locataire': ['exact'],
    }
    
    search_fields = [
        'reference_paiement',
        'contrat__numero_contrat',
        'contrat__locataire__nom',
        'contrat__locataire__prenom',
        'commentaire'
    ]
    
    ordering_fields = [
        'date_paiement',
        'date_creation',
        'montant',
        'statut'
    ]
    
    ordering = ['-date_creation']
    
    def get_serializer_class(self):
        """Utiliser un serializer détaillé pour les actions de détail."""
        if self.action in ['retrieve', 'list']:
            return PaiementDetailSerializer
        return PaiementSerializer
    
    def get_queryset(self):
        """Filtrer les paiements selon les permissions utilisateur."""
        queryset = super().get_queryset()
        
        # Filtrer les paiements supprimés
        queryset = queryset.filter(is_deleted=False)
        
        # Filtres additionnels selon les paramètres de requête
        mois = self.request.query_params.get('mois')
        annee = self.request.query_params.get('annee')
        
        if mois and annee:
            try:
                queryset = queryset.filter(
                    date_paiement__month=int(mois),
                    date_paiement__year=int(annee)
                )
            except (ValueError, TypeError):
                pass
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def valider(self, request, pk=None):
        """Valider un paiement."""
        paiement = self.get_object()
        
        if paiement.statut == 'valide':
            return Response(
                {'error': 'Ce paiement est déjà validé.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        paiement.statut = 'valide'
        paiement.date_validation = timezone.now()
        paiement.validé_par = request.user
        paiement.save()
        
        return Response({
            'message': 'Paiement validé avec succès.',
            'paiement': PaiementDetailSerializer(paiement).data
        })
    
    @action(detail=True, methods=['post'])
    def refuser(self, request, pk=None):
        """Refuser un paiement."""
        paiement = self.get_object()
        
        if paiement.statut == 'refuse':
            return Response(
                {'error': 'Ce paiement est déjà refusé.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        motif_refus = request.data.get('motif_refus', '')
        
        paiement.statut = 'refuse'
        paiement.commentaire = f"{paiement.commentaire}\n\nRefusé: {motif_refus}".strip()
        paiement.save()
        
        return Response({
            'message': 'Paiement refusé avec succès.',
            'paiement': PaiementDetailSerializer(paiement).data
        })
    
    @action(detail=False, methods=['get'])
    def statistiques(self, request):
        """Obtenir les statistiques des paiements."""
        queryset = self.get_queryset()
        
        # Statistiques générales
        stats = {
            'total': queryset.count(),
            'valides': queryset.filter(statut='valide').count(),
            'en_attente': queryset.filter(statut='en_attente').count(),
            'refuses': queryset.filter(statut='refuse').count(),
            'montant_total': queryset.aggregate(Sum('montant'))['montant__sum'] or 0,
        }
        
        # Statistiques par type
        stats_par_type = queryset.values('type_paiement').annotate(
            count=Count('id'),
            total=Sum('montant')
        ).order_by('-count')
        
        # Statistiques par mode
        stats_par_mode = queryset.values('mode_paiement').annotate(
            count=Count('id'),
            total=Sum('montant')
        ).order_by('-count')
        
        # Évolution mensuelle (6 derniers mois)
        from datetime import datetime, timedelta
        from django.db.models import TruncMonth
        
        six_mois_ago = timezone.now().date() - timedelta(days=180)
        evolution_mensuelle = queryset.filter(
            date_paiement__gte=six_mois_ago
        ).annotate(
            mois=TruncMonth('date_paiement')
        ).values('mois').annotate(
            count=Count('id'),
            total=Sum('montant')
        ).order_by('mois')
        
        return Response({
            'statistiques_generales': stats,
            'par_type': list(stats_par_type),
            'par_mode': list(stats_par_mode),
            'evolution_mensuelle': list(evolution_mensuelle)
        })
    
    @action(detail=False, methods=['get'])
    def paiements_en_retard(self, request):
        """Obtenir les paiements en retard."""
        from contrats.models import Contrat
        from datetime import date
        from calendar import monthrange
        
        paiements_retard = []
        contrats_actifs = Contrat.objects.filter(est_actif=True).select_related(
            'locataire', 'propriete'
        )
        
        aujourd_hui = timezone.now().date()
        
        for contrat in contrats_actifs:
            # Calculer la date d'échéance pour le mois en cours
            annee = aujourd_hui.year
            mois = aujourd_hui.month
            
            # Obtenir le dernier jour du mois
            _, dernier_jour_mois = monthrange(annee, mois)
            
            # Date d'échéance = jour de paiement du contrat ou dernier jour du mois
            jour_paiement = min(contrat.jour_paiement, dernier_jour_mois)
            date_echeance = date(annee, mois, jour_paiement)
            
            # Vérifier si le paiement pour ce mois existe et est en retard
            paiement_mois = Paiement.objects.filter(
                contrat=contrat,
                type_paiement='loyer',
                date_paiement__year=annee,
                date_paiement__month=mois,
                statut__in=['en_attente', 'valide']
            ).first()
            
            if not paiement_mois and aujourd_hui > date_echeance:
                jours_retard = (aujourd_hui - date_echeance).days
                paiements_retard.append({
                    'contrat': {
                        'id': contrat.id,
                        'numero_contrat': contrat.numero_contrat,
                        'locataire': f"{contrat.locataire.nom} {contrat.locataire.prenom}",
                        'propriete': contrat.propriete.titre,
                        'loyer_mensuel': contrat.loyer_mensuel
                    },
                    'date_echeance': date_echeance,
                    'jours_retard': jours_retard,
                    'montant_du': contrat.loyer_mensuel
                })
        
        return Response({
            'paiements_en_retard': paiements_retard,
            'total_retards': len(paiements_retard),
            'montant_total_du': sum(p['montant_du'] for p in paiements_retard)
        })
    
    @action(detail=False, methods=['post'])
    def validation_multiple(self, request):
        """Valider plusieurs paiements en une fois."""
        paiement_ids = request.data.get('paiement_ids', [])
        
        if not paiement_ids:
            return Response(
                {'error': 'Aucun paiement sélectionné.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        paiements = Paiement.objects.filter(
            id__in=paiement_ids,
            statut='en_attente'
        )
        
        if not paiements.exists():
            return Response(
                {'error': 'Aucun paiement en attente trouvé avec les IDs fournis.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Valider tous les paiements
        count = paiements.update(
            statut='valide',
            date_validation=timezone.now(),
            validé_par=request.user
        )
        
        return Response({
            'message': f'{count} paiement(s) validé(s) avec succès.',
            'paiements_valides': count
        })
    
    def perform_create(self, serializer):
        """Personnaliser la création d'un paiement."""
        # Générer automatiquement une référence si elle n'est pas fournie
        if not serializer.validated_data.get('reference_paiement'):
            from django.utils.crypto import get_random_string
            reference = f"PAY-{timezone.now().strftime('%Y%m%d')}-{get_random_string(6)}"
            serializer.validated_data['reference_paiement'] = reference
        
        serializer.save()
    
    def perform_destroy(self, instance):
        """Effectuer une suppression logique au lieu d'une suppression physique."""
        instance.is_deleted = True
        instance.deleted_at = timezone.now()
        instance.deleted_by = self.request.user
        instance.save()


class PaiementCautionAvanceViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des paiements de caution et avance via API REST.
    """
    queryset = Paiement.objects.filter(
        type_paiement__in=['caution', 'avance_loyer', 'depot_garantie']
    ).select_related(
        'contrat__locataire',
        'contrat__propriete',
        'contrat__propriete__bailleur'
    ).order_by('-date_creation')
    
    serializer_class = PaiementDetailSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    filterset_fields = {
        'type_paiement': ['exact', 'in'],
        'statut': ['exact'],
        'date_paiement': ['gte', 'lte', 'exact'],
        'montant': ['gte', 'lte', 'exact'],
        'contrat': ['exact'],
        'contrat__propriete': ['exact'],
        'contrat__locataire': ['exact'],
        'contrat__propriete__bailleur': ['exact'],
    }
    
    search_fields = [
        'reference_paiement',
        'contrat__numero_contrat',
        'contrat__locataire__nom',
        'contrat__locataire__prenom',
        'contrat__propriete__titre',
        'commentaire'
    ]
    
    ordering_fields = [
        'date_paiement',
        'date_creation',
        'montant',
        'statut'
    ]
    
    ordering = ['-date_creation']
    
    def get_queryset(self):
        """Filtrer les paiements selon les permissions utilisateur."""
        queryset = super().get_queryset()
        
        # Filtrer les paiements supprimés
        queryset = queryset.filter(is_deleted=False)
        
        # Filtres additionnels selon les paramètres de requête
        type_paiement = self.request.query_params.get('type_paiement')
        statut = self.request.query_params.get('statut')
        mois = self.request.query_params.get('mois')
        annee = self.request.query_params.get('annee')
        
        if type_paiement:
            if type_paiement == 'caution_avance':
                queryset = queryset.filter(type_paiement__in=['caution', 'avance_loyer'])
            else:
                queryset = queryset.filter(type_paiement=type_paiement)
        
        if statut:
            queryset = queryset.filter(statut=statut)
        
        if mois and annee:
            try:
                queryset = queryset.filter(
                    date_paiement__month=int(mois),
                    date_paiement__year=int(annee)
                )
            except (ValueError, TypeError):
                pass
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def statistiques(self, request):
        """Obtenir les statistiques des paiements de caution et avance."""
        queryset = self.get_queryset()
        
        # Statistiques par type de paiement
        stats_par_type = queryset.values('type_paiement').annotate(
            count=Count('id'),
            total=Sum('montant'),
            valides=Count('id', filter=Q(statut='valide')),
            en_attente=Count('id', filter=Q(statut='en_attente')),
            refuses=Count('id', filter=Q(statut='refuse'))
        ).order_by('-total')
        
        # Statistiques par statut
        stats_par_statut = queryset.values('statut').annotate(
            count=Count('id'),
            total=Sum('montant')
        ).order_by('-count')
        
        # Statistiques par mois (6 derniers mois)
        from datetime import datetime, timedelta
        from django.db.models import TruncMonth
        
        six_mois_ago = timezone.now().date() - timedelta(days=180)
        evolution_mensuelle = queryset.filter(
            date_paiement__gte=six_mois_ago
        ).annotate(
            mois=TruncMonth('date_paiement')
        ).values('mois').annotate(
            count=Count('id'),
            total=Sum('montant')
        ).order_by('mois')
        
        # Statistiques par propriétaire
        stats_par_proprietaire = queryset.values(
            'contrat__propriete__bailleur__nom',
            'contrat__propriete__bailleur__prenom'
        ).annotate(
            count=Count('id'),
            total=Sum('montant')
        ).order_by('-total')
        
        return Response({
            'statistiques_par_type': list(stats_par_type),
            'statistiques_par_statut': list(stats_par_statut),
            'evolution_mensuelle': list(evolution_mensuelle),
            'statistiques_par_proprietaire': list(stats_par_proprietaire),
            'total_paiements': queryset.count(),
            'montant_total': float(queryset.aggregate(Sum('montant'))['montant__sum'] or 0),
        })
    
    @action(detail=False, methods=['get'])
    def cautions_en_attente(self, request):
        """Obtenir les cautions en attente de paiement."""
        from contrats.models import Contrat
        
        contrats_caution_en_attente = Contrat.objects.filter(
            caution_requise=True,
            caution_payee=False,
            est_actif=True,
            est_resilie=False
        ).select_related(
            'locataire', 
            'propriete', 
            'propriete__bailleur'
        ).order_by('date_creation')
        
        data = []
        for contrat in contrats_caution_en_attente:
            data.append({
                'contrat': {
                    'id': contrat.id,
                    'numero_contrat': contrat.numero_contrat,
                    'locataire': f"{contrat.locataire.nom} {contrat.locataire.prenom}",
                    'propriete': contrat.propriete.titre,
                    'ville': contrat.propriete.ville,
                    'bailleur': f"{contrat.propriete.bailleur.nom} {contrat.propriete.bailleur.prenom}",
                },
                'caution_montant': float(contrat.caution_montant),
                'date_debut': contrat.date_debut,
                'jours_attente': (timezone.now().date() - contrat.date_debut).days,
            })
        
        return Response({
            'cautions_en_attente': data,
            'total_cautions_en_attente': len(data),
            'montant_total_en_attente': sum(item['caution_montant'] for item in data)
        })
    
    @action(detail=False, methods=['get'])
    def avances_en_attente(self, request):
        """Obtenir les avances de loyer en attente de paiement."""
        from contrats.models import Contrat
        
        contrats_avance_en_attente = Contrat.objects.filter(
            avance_requise=True,
            avance_payee=False,
            est_actif=True,
            est_resilie=False
        ).select_related(
            'locataire', 
            'propriete', 
            'propriete__bailleur'
        ).order_by('date_creation')
        
        data = []
        for contrat in contrats_avance_en_attente:
            data.append({
                'contrat': {
                    'id': contrat.id,
                    'numero_contrat': contrat.numero_contrat,
                    'locataire': f"{contrat.locataire.nom} {contrat.locataire.prenom}",
                    'propriete': contrat.propriete.titre,
                    'ville': contrat.propriete.ville,
                    'bailleur': f"{contrat.propriete.bailleur.nom} {contrat.propriete.bailleur.prenom}",
                },
                'avance_montant': float(contrat.avance_montant),
                'date_debut': contrat.date_debut,
                'jours_attente': (timezone.now().date() - contrat.date_debut).days,
            })
        
        return Response({
            'avances_en_attente': data,
            'total_avances_en_attente': len(data),
            'montant_total_en_attente': sum(item['avance_montant'] for item in data)
        })
    
    @action(detail=True, methods=['post'])
    def valider_caution_avance(self, request, pk=None):
        """Valider un paiement de caution ou avance."""
        paiement = self.get_object()
        
        if paiement.statut == 'valide':
            return Response(
                {'error': 'Ce paiement est déjà validé.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Mettre à jour le contrat correspondant
        contrat = paiement.contrat
        if paiement.type_paiement == 'caution':
            contrat.caution_payee = True
            contrat.date_paiement_caution = paiement.date_paiement
        elif paiement.type_paiement == 'avance_loyer':
            contrat.avance_payee = True
            contrat.date_paiement_avance = paiement.date_paiement
        
        contrat.save()
        
        # Valider le paiement
        paiement.statut = 'valide'
        paiement.date_validation = timezone.now()
        paiement.validé_par = request.user
        paiement.save()
        
        return Response({
            'message': f'Paiement de {paiement.get_type_paiement_display()} validé avec succès.',
            'paiement': PaiementDetailSerializer(paiement).data,
            'contrat_mis_a_jour': {
                'id': contrat.id,
                'numero_contrat': contrat.numero_contrat,
                'caution_payee': contrat.caution_payee,
                'avance_payee': contrat.avance_payee,
            }
        })
