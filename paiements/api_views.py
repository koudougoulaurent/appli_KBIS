from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import date
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View

from .models import Paiement
from .serializers import PaiementSerializer, PaiementDetailSerializer
from contrats.models import Contrat
from proprietes.models import Locataire, Propriete

# 🔍 API DE RECHERCHE RAPIDE DES CONTRATS
@csrf_exempt
def api_recherche_contrats_rapide(request):
    """API pour la recherche rapide de contrats."""
    if request.method == 'GET':
        query = request.GET.get('q', '')
        
        if not query or len(query) < 2:
            return JsonResponse({'resultats': []})
        
        # Recherche dans les contrats, locataires et propriétés
        contrats = Contrat.objects.filter(
            Q(numero_contrat__icontains=query) |
            Q(locataire__nom__icontains=query) |
            Q(locataire__prenom__icontains=query) |
            Q(locataire__id__icontains=query) |
            Q(propriete__adresse__icontains=query) |
            Q(propriete__titre__icontains=query),
            is_deleted=False
        ).select_related('locataire', 'propriete')[:10]
        
        resultats = []
        for contrat in contrats:
            # Calculer un score de pertinence
            score = 0
            if query.lower() in contrat.numero_contrat.lower():
                score += 100
            if query.lower() in contrat.locataire.nom.lower():
                score += 80
            if query.lower() in contrat.locataire.prenom.lower():
                score += 80
            if query.lower() in contrat.propriete.adresse.lower():
                score += 60
            
            resultats.append({
                'id': contrat.pk,
                'numero_contrat': contrat.numero_contrat,
                'locataire_nom': contrat.locataire.get_nom_complet(),
                'locataire_id': contrat.locataire.pk,
                'propriete_adresse': contrat.propriete.adresse,
                'propriete_titre': contrat.propriete.titre,
                'score': score,
                'loyer': float(contrat.loyer_mensuel) if contrat.loyer_mensuel else 0
            })
        
        # Trier par score décroissant
        resultats.sort(key=lambda x: x['score'], reverse=True)
        
        return JsonResponse({
            'success': True,
            'data': resultats,
            'count': len(resultats)
        })
    
    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)

# 🔍 API DE RECHERCHE DE BAILLEUR
@csrf_exempt
def api_recherche_bailleur(request):
    """API pour rechercher un bailleur par nom ou numéro et récupérer toutes ses informations."""
    if request.method == 'GET':
        query = request.GET.get('q', '').strip()
        
        if not query:
            return JsonResponse({
                'success': False,
                'error': 'Terme de recherche requis'
            }, status=400)
        
        try:
            from proprietes.models import Bailleur
            from contrats.models import Contrat
            from .models import RetraitBailleur
            
            # Recherche du bailleur (nom, prénom, numéro, email)
            bailleur = Bailleur.objects.filter(
                Q(nom__icontains=query) |
                Q(prenom__icontains=query) |
                Q(numero_bailleur__icontains=query) |
                Q(email__icontains=query) |
                Q(telephone__icontains=query)
            ).filter(actif=True).first()
            
            if not bailleur:
                return JsonResponse({
                    'success': False,
                    'error': 'Aucun bailleur trouvé avec ces critères'
                }, status=404)
            
            # Récupérer toutes les propriétés louées du bailleur
            proprietes_louees = Propriete.objects.filter(
                bailleur=bailleur,
                disponible=False
            ).select_related('bailleur')
            
            # Récupérer les contrats actifs
            contrats_actifs = Contrat.objects.filter(
                propriete__bailleur=bailleur,
                est_actif=True
            ).select_related('propriete', 'locataire')
            
            # Calculer le total des loyers bruts
            total_loyers_bruts = contrats_actifs.aggregate(
                total=Sum('loyer_mensuel')
            )['total'] or 0
            
            # Récupérer les retraits précédents
            retraits_precedents = RetraitBailleur.objects.filter(
                bailleur=bailleur
            ).order_by('-date_demande')[:10]
            
            # Préparer les données des propriétés
            proprietes_data = []
            for propriete in proprietes_louees:
                contrat_actuel = contrats_actifs.filter(propriete=propriete).first()
                
                propriete_info = {
                    'id': propriete.id,
                    'titre': propriete.titre,
                    'adresse': propriete.adresse,
                    'ville': propriete.ville,
                    'code_postal': propriete.code_postal,
                    'type_propriete': propriete.type_bien.nom if propriete.type_bien else 'Non défini',
                    'disponibilite': 'Occupée' if not propriete.disponible else 'Disponible',
                    'loyer_mensuel': float(contrat_actuel.loyer_mensuel) if contrat_actuel else 0,
                    'locataire': {
                        'nom': contrat_actuel.locataire.nom if contrat_actuel and contrat_actuel.locataire else None,
                        'prenom': contrat_actuel.locataire.prenom if contrat_actuel and contrat_actuel.locataire else None,
                        'email': contrat_actuel.locataire.email if contrat_actuel and contrat_actuel.locataire else None,
                        'telephone': contrat_actuel.locataire.telephone if contrat_actuel and contrat_actuel.locataire else None
                    } if contrat_actuel else None,
                    'date_debut_bail': contrat_actuel.date_debut.strftime('%d/%m/%Y') if contrat_actuel and contrat_actuel.date_debut else None,
                    'date_fin_bail': contrat_actuel.date_fin.strftime('%d/%m/%Y') if contrat_actuel and contrat_actuel.date_fin else None
                }
                proprietes_data.append(propriete_info)
            
            # Préparer les données des retraits précédents
            retraits_data = []
            for retrait in retraits_precedents:
                retrait_info = {
                    'id': retrait.id,
                    'mois_retrait': retrait.mois_retrait.strftime('%B %Y') if retrait.mois_retrait else 'Date non définie',
                    'montant_loyers_bruts': float(retrait.montant_loyers_bruts) if retrait.montant_loyers_bruts else 0,
                    'montant_charges_deductibles': float(retrait.montant_charges_deductibles) if retrait.montant_charges_deductibles else 0,
                    'montant_net_a_payer': float(retrait.montant_net_a_payer) if retrait.montant_net_a_payer else 0,
                    'date_demande': retrait.date_demande.strftime('%d/%m/%Y') if retrait.date_demande else 'Date non définie',
                    'statut': retrait.get_statut_display() if hasattr(retrait, 'get_statut_display') else 'Non défini',
                    'type_retrait': retrait.get_type_retrait_display() if hasattr(retrait, 'get_type_retrait_display') else 'Non défini'
                }
                retraits_data.append(retrait_info)
            
            # Réponse complète
            response_data = {
                'success': True,
                'bailleur': {
                    'id': bailleur.id,
                    'nom': bailleur.nom,
                    'prenom': bailleur.prenom,
                    'numero_bailleur': bailleur.numero_bailleur,
                    'email': bailleur.email,
                    'telephone': bailleur.telephone,
                    'adresse': bailleur.adresse,
                    'ville': bailleur.ville,
                    'code_postal': bailleur.code_postal,
                    'date_inscription': bailleur.date_creation.strftime('%d/%m/%Y') if bailleur.date_creation else None
                },
                'proprietes': {
                    'total': proprietes_louees.count(),
                    'liste': proprietes_data
                },
                'loyers': {
                    'total_mensuel': float(total_loyers_bruts),
                    'total_annuel': float(total_loyers_bruts * 12)
                },
                'retraits': {
                    'total': retraits_precedents.count(),
                    'liste': retraits_data,
                    'dernier_retrait': retraits_data[0] if retraits_data else None
                },
                'mois_retrait_suivant': 'Date non définie',  # À implémenter si nécessaire
                'statistiques': {
                    'nombre_proprietes': proprietes_louees.count(),
                    'nombre_contrats_actifs': contrats_actifs.count(),
                    'moyenne_loyer': float(total_loyers_bruts / proprietes_louees.count()) if proprietes_louees.count() > 0 else 0
                }
            }
            
            return JsonResponse(response_data)
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Erreur lors de la recherche : {str(e)}'
            }, status=500)
    
    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)

# 🧠 API DE CONTEXTE INTELLIGENT
@csrf_exempt
def api_contexte_intelligent_contrat(request, contrat_id):
    """API pour récupérer le contexte intelligent d'un contrat."""
    if request.method == 'GET':
        try:
            contrat = Contrat.objects.select_related(
                'locataire', 'propriete', 'propriete__bailleur'
            ).get(pk=contrat_id, is_deleted=False)
            
            # Récupérer l'historique des paiements (5 derniers mois)
            from datetime import datetime, timedelta
            date_limite = datetime.now() - timedelta(days=150)
            
            paiements_recents = Paiement.objects.filter(
                contrat=contrat,
                date_paiement__gte=date_limite,
                is_deleted=False
            ).order_by('-date_paiement')[:5]
            
            # Calculer le prochain mois de paiement
            derniers_mois = [p.date_paiement.month for p in paiements_recents if p.date_paiement]
            prochain_mois = None
            mois_suggere = None
            
            if derniers_mois:
                # Si il y a des paiements, calculer le mois suivant
                dernier_mois = max(derniers_mois)
                prochain_mois = (dernier_mois % 12) + 1
                mois_suggere = f"Suivant le dernier paiement ({prochain_mois})"
            else:
                # Premier paiement : utiliser le mois actuel ou le mois de début de contrat
                from datetime import datetime
                mois_actuel = datetime.now().month
                if contrat.date_debut:
                    mois_debut = contrat.date_debut.month
                    if mois_debut == mois_actuel:
                        prochain_mois = mois_actuel
                        mois_suggere = "Mois actuel (début de contrat)"
                    else:
                        prochain_mois = mois_debut
                        mois_suggere = f"Mois de début de contrat ({mois_debut})"
                else:
                    prochain_mois = mois_actuel
                    mois_suggere = "Mois actuel"
            
            contexte = {
                'contrat': {
                    'numero': contrat.numero_contrat,
                    'date_debut': contrat.date_debut.strftime('%d/%m/%Y') if contrat.date_debut else None,
                    'date_fin': contrat.date_fin.strftime('%d/%m/%Y') if contrat.date_fin else None,
                    'montant_loyer': float(contrat.loyer_mensuel) if contrat.loyer_mensuel else 0,
                    'charges': float(contrat.charges_mensuelles) if contrat.charges_mensuelles else 0
                },
                'locataire': {
                    'nom_complet': contrat.locataire.get_nom_complet(),
                    'telephone': contrat.locataire.telephone,
                    'email': contrat.locataire.email
                },
                'propriete': {
                    'adresse': contrat.propriete.adresse,
                    'titre': contrat.propriete.titre,
                    'type': str(contrat.propriete.type_propriete) if hasattr(contrat.propriete, 'type_propriete') else 'Non défini',
                    'surface': contrat.propriete.surface
                },
                'paiements_recents': [
                    {
                        'date': p.date_paiement.strftime('%d/%m/%Y'),
                        'montant': float(p.montant),
                        'type': p.get_type_paiement_display(),
                        'statut': p.get_statut_display()
                    } for p in paiements_recents
                ],
                'prochain_mois_paiement': prochain_mois,
                'mois_suggere': mois_suggere,
                'total_charges': float(contrat.charges_mensuelles) if contrat.charges_mensuelles else 0,
                'net_a_payer': float(contrat.loyer_mensuel) if contrat.loyer_mensuel else 0,
                'est_premier_paiement': len(paiements_recents) == 0
            }
            
            return JsonResponse(contexte)
            
        except Contrat.DoesNotExist:
            return JsonResponse({'error': 'Contrat non trouvé'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)


class PaiementViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des paiements via API REST.
    """
    queryset = Paiement.objects.select_related(
        'contrat__locataire',
        'contrat__propriete',
        'contrat__propriete__bailleur'
        ).order_by('-date_paiement')
    
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
        'created_at',
        'montant',
        'statut'
    ]
    
    ordering = ['-created_at']
    
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
        ).order_by('-date_paiement')
    
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
        'created_at',
        'montant',
        'statut'
    ]
    
    ordering = ['-created_at']
    
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
        ).order_by('created_at')
        
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
        ).order_by('created_at')
        
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


# 🔍 API DE VÉRIFICATION DES DOUBLONS DE PAIEMENT
@csrf_exempt
def api_verifier_doublon_paiement(request):
    """API pour vérifier s'il existe déjà un paiement pour un contrat dans un mois donné."""
    if request.method == 'GET':
        contrat_id = request.GET.get('contrat_id')
        mois = request.GET.get('mois')
        annee = request.GET.get('annee')
        
        if not all([contrat_id, mois, annee]):
            return JsonResponse({
                'doublon_existe': False,
                'erreur': 'Paramètres manquants'
            })
        
        try:
            # Vérifier s'il existe un paiement pour ce contrat dans ce mois
            existing_payment = Paiement.objects.filter(
                contrat_id=contrat_id,
                mois_paye__year=int(annee),
                mois_paye__month=int(mois),
                is_deleted=False
            ).first()
            
            if existing_payment:
                # Formater le nom du mois
                mois_noms = [
                    'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
                    'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'
                ]
                mois_nom = mois_noms[int(mois) - 1]
                
                return JsonResponse({
                    'doublon_existe': True,
                    'mois_nom': f"{mois_nom} {annee}",
                    'paiement_existant': {
                        'reference': existing_payment.reference_paiement,
                        'date': existing_payment.date_paiement.strftime('%d/%m/%Y'),
                        'montant': f"{existing_payment.montant:,.0f}",
                        'type': existing_payment.get_type_paiement_display()
                    }
                })
            else:
                return JsonResponse({
                    'doublon_existe': False
                })
                
        except (ValueError, Contrat.DoesNotExist):
            return JsonResponse({
                'doublon_existe': False,
                'erreur': 'Contrat introuvable'
            })
    
    return JsonResponse({
        'doublon_existe': False,
        'erreur': 'Méthode non autorisée'
    })
