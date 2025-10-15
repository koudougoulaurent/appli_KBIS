"""
Vues pour la gestion des unités locatives dans les grandes propriétés
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum, Avg
from django.utils import timezone
from datetime import timedelta

from .models import Propriete, UniteLocative, ReservationUnite
from .forms import UniteLocativeForm, ReservationUniteForm, UniteRechercheForm
from utilisateurs.mixins import PrivilegeButtonsMixin
from core.intelligent_views import IntelligentListView


class UniteLocativeListView(PrivilegeButtonsMixin, IntelligentListView):
    """Vue pour lister les unités locatives."""
    model = UniteLocative
    template_name = 'proprietes/unites/liste.html'
    context_object_name = 'unites'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = UniteLocative.objects.select_related(
            'propriete', 'propriete__bailleur'
        ).filter(is_deleted=False)
        
        # Filtrage par propriété
        propriete_id = self.request.GET.get('propriete')
        if propriete_id:
            queryset = queryset.filter(propriete_id=propriete_id)
        
        # Filtrage par statut
        statut = self.request.GET.get('statut')
        if statut:
            queryset = queryset.filter(statut=statut)
        
        # Filtrage par type d'unité
        type_unite = self.request.GET.get('type_unite')
        if type_unite:
            queryset = queryset.filter(type_unite=type_unite)
        
        # Recherche textuelle
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(numero_unite__icontains=search) |
                Q(nom__icontains=search) |
                Q(propriete__titre__icontains=search) |
                Q(description__icontains=search)
            )
        
        return queryset.order_by('propriete__titre', 'etage', 'numero_unite')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Statistiques générales
        context['stats'] = {
            'total_unites': UniteLocative.objects.filter(is_deleted=False).count(),
            'unites_disponibles': UniteLocative.objects.filter(
                statut='disponible', is_deleted=False
            ).count(),
            'unites_occupees': UniteLocative.objects.filter(
                statut='occupee', is_deleted=False
            ).count(),
            'unites_reservees': UniteLocative.objects.filter(
                statut='reservee', is_deleted=False
            ).count(),
        }
        
        # Filtres pour le template
        context['proprietes'] = Propriete.objects.filter(is_deleted=False)
        context['statuts'] = UniteLocative.STATUT_CHOICES
        context['types_unite'] = UniteLocative.TYPE_UNITE_CHOICES
        
        # Paramètres de filtrage actuels
        context['current_filters'] = {
            'propriete': self.request.GET.get('propriete', ''),
            'statut': self.request.GET.get('statut', ''),
            'type_unite': self.request.GET.get('type_unite', ''),
            'search': self.request.GET.get('search', ''),
        }
        
        return context


@login_required
def unite_detail(request, pk):
    """Vue détaillée d'une unité locative."""
    unite = get_object_or_404(UniteLocative, pk=pk, is_deleted=False)
    
    # Récupérer l'historique des contrats
    from contrats.models import Contrat
    contrats = Contrat.objects.filter(
        unite_locative=unite
    ).select_related('locataire').order_by('-date_debut')
    
    # Récupérer les réservations
    reservations = unite.reservations.filter(
        is_deleted=False
    ).select_related('locataire_potentiel').order_by('-date_reservation')
    
    # Calculs statistiques
    revenus_annuels = unite.get_revenus_potentiels_annuels()
    taux_occupation = unite.get_taux_occupation()
    
    context = {
        'unite': unite,
        'contrats': contrats,
        'reservations': reservations,
        'revenus_annuels': revenus_annuels,
        'taux_occupation': taux_occupation,
        'contrat_actuel': unite.get_contrat_actuel(),
        'locataire_actuel': unite.get_locataire_actuel(),
    }
    
    return render(request, 'proprietes/unites/detail.html', context)


@login_required
def unite_create(request, propriete_id=None):
    """Vue pour créer une nouvelle unité locative."""
    propriete = None
    if propriete_id:
        propriete = get_object_or_404(Propriete, pk=propriete_id, is_deleted=False)
    
    if request.method == 'POST':
        form = UniteLocativeForm(request.POST)
        if form.is_valid():
            try:
                unite = form.save(commit=False)
                if propriete:
                    unite.propriete = propriete
                
                # Si aucun bailleur spécifique n'est sélectionné, utiliser celui de la propriété
                if not unite.bailleur and unite.propriete:
                    unite.bailleur = unite.propriete.bailleur
                
                unite.save()
                
                messages.success(
                    request, 
                    f"L'unité locative '{unite.numero_unite}' a été créée avec succès."
                )
                
                # Si on vient de la création d'une propriété, proposer de créer une autre unité
                if propriete and request.GET.get('from_property') == '1':
                    messages.info(
                        request,
                        f"Unité créée ! Souhaitez-vous créer une autre unité pour '{propriete.titre}' ?"
                    )
                    return redirect('proprietes:unite_create_propriete', propriete_id=propriete.pk)
                
                return redirect('proprietes:unite_detail', pk=unite.pk)
                
            except Exception as e:
                messages.error(
                    request, 
                    f"Erreur lors de la création de l'unité locative : {str(e)}"
                )
        else:
            # Afficher les erreurs de validation
            error_messages = []
            for field, errors in form.errors.items():
                for error in errors:
                    error_messages.append(f"{field}: {error}")
            
            if error_messages:
                messages.error(
                    request, 
                    f"Erreurs de validation : {'; '.join(error_messages)}"
                )
    else:
        initial = {}
        if propriete:
            initial['propriete'] = propriete
            initial['bailleur'] = propriete.bailleur  # Pré-sélectionner le bailleur de la propriété
        form = UniteLocativeForm(initial=initial)
    
    # Ajouter des informations contextuelles
    suggestion = None
    if propriete:
        try:
            suggestion = propriete.get_suggestion_creation_unites()
        except Exception as e:
            # En cas d'erreur, on continue sans suggestion
            suggestion = None
    
    context = {
        'form': form,
        'propriete': propriete,
        'title': 'Créer une unité locative',
        'suggestion': suggestion,
        'from_property': request.GET.get('from_property') == '1',
    }
    
    return render(request, 'proprietes/unites/form_simple.html', context)


@login_required
def unite_edit(request, pk):
    """Vue pour modifier une unité locative."""
    unite = get_object_or_404(UniteLocative, pk=pk, is_deleted=False)
    
    if request.method == 'POST':
        form = UniteLocativeForm(request.POST, instance=unite)
        if form.is_valid():
            form.save()
            messages.success(
                request, 
                f"L'unité locative '{unite.numero_unite}' a été modifiée avec succès."
            )
            return redirect('proprietes:unite_detail', pk=unite.pk)
    else:
        form = UniteLocativeForm(instance=unite)
    
    context = {
        'form': form,
        'unite': unite,
        'title': f'Modifier {unite.numero_unite}'
    }
    
    return render(request, 'proprietes/unites/form_simple.html', context)


@login_required
def tableau_bord_propriete(request, propriete_id):
    """Tableau de bord spécialisé pour une propriété avec plusieurs unités."""
    propriete = get_object_or_404(Propriete, pk=propriete_id, is_deleted=False)
    
    # Vérifier si c'est une grande propriété
    if not propriete.est_grande_propriete():
        messages.info(
            request, 
            "Cette propriété n'a pas assez d'unités pour justifier un tableau de bord spécialisé."
        )
        return redirect('proprietes:detail', pk=propriete.pk)
    
    # Statistiques détaillées
    stats = propriete.get_statistiques_unites()
    
    # Unités par statut
    unites_par_statut = propriete.unites_locatives.filter(
        is_deleted=False
    ).values('statut').annotate(
        count=Count('id'),
        revenus=Sum('loyer_mensuel') + Sum('charges_mensuelles')
    ).order_by('statut')
    
    # Unités par type
    unites_par_type = propriete.unites_locatives.filter(
        is_deleted=False
    ).values('type_unite').annotate(
        count=Count('id'),
        revenus=Sum('loyer_mensuel') + Sum('charges_mensuelles')
    ).order_by('type_unite')
    
    # Unités par étage
    unites_par_etage = propriete.unites_locatives.filter(
        is_deleted=False
    ).values('etage').annotate(
        count=Count('id'),
        disponibles=Count('id', filter=Q(statut='disponible')),
        occupees=Count('id', filter=Q(statut='occupee'))
    ).order_by('etage')
    
    # Réservations en attente
    reservations_attente = ReservationUnite.objects.filter(
        unite_locative__propriete=propriete,
        statut='en_attente',
        is_deleted=False
    ).select_related('unite_locative', 'locataire_potentiel')
    
    # Revenus mensuels
    revenus_potentiels = propriete.get_revenus_mensuels_potentiels()
    revenus_actuels = propriete.get_revenus_mensuels_actuels()
    
    # Prochaines échéances (contrats se terminant dans les 60 jours)
    from contrats.models import Contrat
    date_limite = timezone.now().date() + timedelta(days=60)
    prochaines_echeances = Contrat.objects.filter(
        unite_locative__propriete=propriete,
        date_fin__lte=date_limite,
        date_fin__gte=timezone.now().date(),
        est_actif=True,
        est_resilie=False
    ).select_related('unite_locative', 'locataire')
    
    context = {
        'propriete': propriete,
        'stats': stats,
        'unites_par_statut': unites_par_statut,
        'unites_par_type': unites_par_type,
        'unites_par_etage': unites_par_etage,
        'reservations_attente': reservations_attente,
        'revenus_potentiels': revenus_potentiels,
        'revenus_actuels': revenus_actuels,
        'prochaines_echeances': prochaines_echeances,
        'taux_occupation': propriete.get_taux_occupation_global(),
        'manque_a_gagner': revenus_potentiels - revenus_actuels,
    }
    
    return render(request, 'proprietes/dashboard_propriete.html', context)


@login_required
def reservation_create(request, unite_id):
    """Vue pour créer une réservation."""
    unite = get_object_or_404(UniteLocative, pk=unite_id, is_deleted=False)
    
    if unite.statut not in ['disponible']:
        messages.error(request, "Cette unité n'est pas disponible pour réservation.")
        return redirect('proprietes:unite_detail', pk=unite.pk)
    
    if request.method == 'POST':
        # Ajouter l'unité locative aux données POST
        post_data = request.POST.copy()
        post_data['unite_locative'] = unite.pk
        
        form = ReservationUniteForm(post_data, unite_locative=unite)
        print(f"DEBUG - Formulaire valide: {form.is_valid()}")
        if not form.is_valid():
            print(f"DEBUG - Erreurs du formulaire: {form.errors}")
        if form.is_valid():
            try:
                reservation = form.save(commit=False)
                reservation.unite_locative = unite
                reservation.cree_par = request.user
                
                # Définir la date d'expiration (7 jours par défaut)
                if not reservation.date_expiration:
                    reservation.date_expiration = timezone.now() + timedelta(days=7)
                
                reservation.save()
            except Exception as e:
                messages.error(request, f"Erreur lors de la création de la réservation : {str(e)}")
                return render(request, 'proprietes/reservations/form.html', {
                    'form': form,
                    'unite': unite,
                    'title': f'Réserver {unite.numero_unite}'
                })
            
            # Vérifier si la conversion immédiate en contrat est demandée
            convertir_en_contrat = form.cleaned_data.get('convertir_en_contrat', False)
            
            if convertir_en_contrat:
                try:
                    # Convertir immédiatement en contrat
                    from contrats.models import Contrat
                    
                    contrat = Contrat.objects.create(
                        propriete=reservation.unite_locative.propriete,
                        locataire=reservation.locataire_potentiel,
                        unite_locative=reservation.unite_locative,
                        date_debut=reservation.date_debut_souhaitee,
                        date_fin=reservation.date_fin_prevue,
                        date_signature=timezone.now().date(),
                        loyer_mensuel=str(reservation.unite_locative.loyer_mensuel),
                        charges_mensuelles=str(reservation.unite_locative.charges_mensuelles),
                        depot_garantie=str(reservation.unite_locative.caution_demandee),
                        jour_paiement=1,  # Par défaut le 1er du mois
                        mode_paiement='virement',  # Par défaut
                        est_actif=True,
                        cree_par=request.user,
                        notes=f"Contrat créé à partir de la réservation #{reservation.pk} (conversion immédiate)"
                    )
                    
                    # Mettre à jour le statut de la réservation
                    reservation.statut = 'convertie_contrat'
                    reservation.save()
                    
                    # Mettre à jour le statut de l'unité
                    reservation.unite_locative.statut = 'occupee'
                    reservation.unite_locative.save()
                    
                    messages.success(
                        request,
                        f"Réservation créée et convertie en contrat avec succès ! "
                        f"Contrat créé : {contrat.numero_contrat}"
                    )
                    
                    return redirect('contrats:detail', pk=contrat.pk)
                    
                except Exception as e:
                    messages.error(
                        request,
                        f"Réservation créée avec succès, mais erreur lors de la conversion en contrat : {str(e)}"
                    )
                    return redirect('proprietes:unite_detail', pk=unite.pk)
            else:
                messages.success(
                    request,
                    f"Réservation créée pour l'unité '{unite.numero_unite}'."
                )
                return redirect('proprietes:unite_detail', pk=unite.pk)
        else:
            # Le formulaire n'est pas valide, afficher les erreurs
            messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{form.fields[field].label}: {error}")
    else:
        form = ReservationUniteForm(unite_locative=unite)
        # Pré-remplir l'unité locative
        form.fields['unite_locative'].initial = unite
        form.fields['unite_locative'].widget.attrs['readonly'] = True
    
    context = {
        'form': form,
        'unite': unite,
        'title': f'Réserver {unite.numero_unite}'
    }
    
    return render(request, 'proprietes/reservations/form.html', context)


@login_required
def api_unites_disponibles(request):
    """API pour récupérer les unités disponibles (format JSON)."""
    propriete_id = request.GET.get('propriete_id')
    
    queryset = UniteLocative.objects.filter(
        statut='disponible',
        is_deleted=False
    ).select_related('propriete')
    
    if propriete_id:
        queryset = queryset.filter(propriete_id=propriete_id)
    
    unites = []
    for unite in queryset:
        unites.append({
            'id': unite.id,
            'numero_unite': unite.numero_unite,
            'nom': unite.nom,
            'type_unite': unite.get_type_unite_display(),
            'loyer_mensuel': float(unite.loyer_mensuel),
            'charges_mensuelles': float(unite.charges_mensuelles),
            'loyer_total': float(unite.get_loyer_total()),
            'propriete': unite.propriete.titre,
            'etage': unite.etage,
            'surface': float(unite.surface) if unite.surface else None,
        })
    
    return JsonResponse({
        'unites': unites,
        'count': len(unites)
    })


@login_required
def api_statistiques_propriete(request, propriete_id):
    """API pour récupérer les statistiques d'une propriété (format JSON)."""
    propriete = get_object_or_404(Propriete, pk=propriete_id, is_deleted=False)
    
    stats = propriete.get_statistiques_unites()
    stats['revenus_potentiels'] = float(propriete.get_revenus_mensuels_potentiels())
    stats['revenus_actuels'] = float(propriete.get_revenus_mensuels_actuels())
    stats['taux_occupation_global'] = propriete.get_taux_occupation_global()
    
    # Convertir les Decimal en float pour la sérialisation JSON
    for key, value in stats.items():
        if hasattr(value, '__float__'):
            stats[key] = float(value)
    
    return JsonResponse(stats)


@login_required
def recherche_unites(request):
    """Vue de recherche avancée pour les unités locatives optimisée."""
    form = UniteRechercheForm(request.GET or None)
    unites = UniteLocative.objects.none()
    stats = {}
    recherche_effectuee = False
    
    if form.is_valid():
        # Base QuerySet avec annotations optimisées
        from django.db.models import Sum, Count, F, Case, When, DecimalField, Q
        
        unites = UniteLocative.objects.select_related(
            'propriete', 
            'propriete__bailleur', 
            'propriete__type_bien',
            'bailleur'
        ).prefetch_related(
            'pieces',
            'reservations'
        ).filter(is_deleted=False).annotate(
            # Loyer formaté
            loyer_formatted=Case(
                When(loyer_mensuel__isnull=False, then='loyer_mensuel'),
                default=0,
                output_field=DecimalField(max_digits=10, decimal_places=2)
            ),
            # Nom complet du bailleur
            bailleur_nom_complet=Case(
                When(bailleur__nom__isnull=False, 
                     bailleur__prenom__isnull=False,
                     then=F('bailleur__nom') + ' ' + F('bailleur__prenom')),
                When(bailleur__nom__isnull=False,
                     then=F('bailleur__nom')),
                When(propriete__bailleur__nom__isnull=False,
                     propriete__bailleur__prenom__isnull=False,
                     then=F('propriete__bailleur__nom') + ' ' + F('propriete__bailleur__prenom')),
                When(propriete__bailleur__nom__isnull=False,
                     then=F('propriete__bailleur__nom')),
                default='Bailleur inconnu',
                output_field=models.CharField(max_length=200)
            ),
            # Adresse complète de la propriété
            propriete_adresse_complete=Case(
                When(propriete__adresse__isnull=False,
                     propriete__ville__isnull=False,
                     then=F('propriete__adresse') + ', ' + F('propriete__ville')),
                When(propriete__adresse__isnull=False,
                     then=F('propriete__adresse')),
                default='Adresse non renseignée',
                output_field=models.CharField(max_length=300)
            ),
            # Nombre de pièces
            nombre_pieces=Count('pieces', distinct=True),
            # Nombre de réservations
            nombre_reservations=Count('reservations', distinct=True)
        )
        
        # Application des filtres
        search = form.cleaned_data.get('search')
        if search:
            unites = unites.filter(
                Q(numero_unite__icontains=search) |
                Q(nom__icontains=search) |
                Q(propriete__titre__icontains=search) |
                Q(propriete__adresse__icontains=search) |
                Q(propriete__ville__icontains=search) |
                Q(description__icontains=search) |
                Q(propriete__bailleur__nom__icontains=search) |
                Q(propriete__bailleur__prenom__icontains=search) |
                Q(bailleur__nom__icontains=search) |
                Q(bailleur__prenom__icontains=search)
            )
        
        propriete = form.cleaned_data.get('propriete')
        if propriete:
            unites = unites.filter(propriete=propriete)
            
        bailleur = form.cleaned_data.get('bailleur')
        if bailleur:
            unites = unites.filter(
                Q(bailleur=bailleur) | Q(propriete__bailleur=bailleur)
            )
        
        statut = form.cleaned_data.get('statut')
        if statut:
            unites = unites.filter(statut=statut)
            
        type_unite = form.cleaned_data.get('type_unite')
        if type_unite:
            unites = unites.filter(type_unite=type_unite)
        
        # Filtres numériques
        etage_min = form.cleaned_data.get('etage_min')
        if etage_min is not None:
            unites = unites.filter(etage__gte=etage_min)
            
        etage_max = form.cleaned_data.get('etage_max')
        if etage_max is not None:
            unites = unites.filter(etage__lte=etage_max)
        
        loyer_min = form.cleaned_data.get('loyer_min')
        if loyer_min is not None:
            unites = unites.filter(loyer_mensuel__gte=loyer_min)
            
        loyer_max = form.cleaned_data.get('loyer_max')
        if loyer_max is not None:
            unites = unites.filter(loyer_mensuel__lte=loyer_max)
            
        surface_min = form.cleaned_data.get('surface_min')
        if surface_min is not None:
            unites = unites.filter(surface__gte=surface_min)
            
        surface_max = form.cleaned_data.get('surface_max')
        if surface_max is not None:
            unites = unites.filter(surface__lte=surface_max)
            
        nombre_pieces_min = form.cleaned_data.get('nombre_pieces_min')
        if nombre_pieces_min is not None:
            unites = unites.filter(nombre_pieces__gte=nombre_pieces_min)
            
        nombre_pieces_max = form.cleaned_data.get('nombre_pieces_max')
        if nombre_pieces_max is not None:
            unites = unites.filter(nombre_pieces__lte=nombre_pieces_max)
        
        # Filtres booléens pour les équipements
        meuble = form.cleaned_data.get('meuble')
        if meuble == 'true':
            unites = unites.filter(meuble=True)
        elif meuble == 'false':
            unites = unites.filter(meuble=False)
            
        balcon = form.cleaned_data.get('balcon')
        if balcon == 'true':
            unites = unites.filter(balcon=True)
        elif balcon == 'false':
            unites = unites.filter(balcon=False)
            
        parking_inclus = form.cleaned_data.get('parking_inclus')
        if parking_inclus == 'true':
            unites = unites.filter(parking_inclus=True)
        elif parking_inclus == 'false':
            unites = unites.filter(parking_inclus=False)
            
        climatisation = form.cleaned_data.get('climatisation')
        if climatisation == 'true':
            unites = unites.filter(climatisation=True)
        elif climatisation == 'false':
            unites = unites.filter(climatisation=False)
        
        # Filtres de dates
        date_disponibilite_debut = form.cleaned_data.get('date_disponibilite_debut')
        if date_disponibilite_debut:
            unites = unites.filter(
                Q(date_disponibilite__gte=date_disponibilite_debut) |
                Q(date_disponibilite__isnull=True, statut='disponible')
            )
            
        date_disponibilite_fin = form.cleaned_data.get('date_disponibilite_fin')
        if date_disponibilite_fin:
            unites = unites.filter(
                Q(date_disponibilite__lte=date_disponibilite_fin) |
                Q(date_disponibilite__isnull=True)
            )
        
        # Tri
        tri = form.cleaned_data.get('tri', 'numero_unite')
        unites = unites.order_by(tri)
        
        recherche_effectuee = True
        
        # Calcul des statistiques optimisées
        if unites.exists():
            # Statistiques de base avec requêtes optimisées
            total_unites = unites.count()
            
            # Statistiques par statut en une seule requête
            stats_par_statut = unites.values('statut').annotate(
                count=Count('id'),
                loyer_total=Sum('loyer_mensuel')
            ).order_by('statut')
            
            # Calcul des totaux
            stats = {
                'total_unites': total_unites,
                'unites_disponibles': 0,
                'unites_occupees': 0,
                'unites_reservees': 0,
                'loyer_moyen': 0,
                'loyer_total': 0,
                'surface_moyenne': 0,
                'surface_totale': 0,
            }
            
            # Remplir les statistiques par statut
            for stat in stats_par_statut:
                if stat['statut'] == 'disponible':
                    stats['unites_disponibles'] = stat['count']
                elif stat['statut'] == 'occupee':
                    stats['unites_occupees'] = stat['count']
                elif stat['statut'] == 'reservee':
                    stats['unites_reservees'] = stat['count']
            
            # Calculs agrégés optimisés
            from django.db.models import Avg
            agregats = unites.aggregate(
                loyer_moyen=Avg('loyer_mensuel'),
                loyer_total=Sum('loyer_mensuel'),
                surface_moyenne=Avg('surface'),
                surface_totale=Sum('surface')
            )
            
            stats.update({
                'loyer_moyen': agregats['loyer_moyen'] or 0,
                'loyer_total': agregats['loyer_total'] or 0,
                'surface_moyenne': agregats['surface_moyenne'] or 0,
                'surface_totale': agregats['surface_totale'] or 0,
            })
            
            # Répartition par type (optimisée)
            stats['repartition_types'] = list(unites.values('type_unite').annotate(
                count=Count('id'),
                loyer_total=Sum('loyer_mensuel')
            ).order_by('-count'))
            
            # Répartition par statut (déjà calculée)
            stats['repartition_statuts'] = list(stats_par_statut)
            
            # Répartition par propriété (optimisée)
            stats['repartition_proprietes'] = list(unites.values(
                'propriete__titre', 'propriete__id'
            ).annotate(
                count=Count('id'),
                loyer_total=Sum('loyer_mensuel')
            ).order_by('-count')[:10])
            
            # Statistiques par bailleur
            stats['repartition_bailleurs'] = list(unites.values(
                'bailleur_nom_complet'
            ).annotate(
                count=Count('id'),
                loyer_total=Sum('loyer_mensuel')
            ).order_by('-count')[:10])
    
    # Pagination
    paginator = Paginator(unites, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'form': form,
        'unites': page_obj,
        'stats': stats,
        'recherche_effectuee': recherche_effectuee,
        'total_results': unites.count() if recherche_effectuee else 0,
        'page_title': 'Recherche d\'unités locatives',
        'page_icon': 'search',
    }
    
    return render(request, 'proprietes/unites/recherche.html', context)


@login_required
def unite_detail_complet(request, pk):
    """Vue détaillée complète d'une unité locative avec toutes les informations."""
    unite = get_object_or_404(
        UniteLocative.objects.select_related(
            'propriete',
            'propriete__bailleur',
            'propriete__type_bien',
            'bailleur'
        ).prefetch_related(
            'pieces',
            'reservations'
        ), 
        pk=pk, 
        is_deleted=False
    )
    
    # Récupérer l'historique des contrats
    from contrats.models import Contrat
    contrats = Contrat.objects.filter(
        unite_locative=unite
    ).select_related('locataire').order_by('-date_debut')
    
    # Contrat actuel et locataire actuel
    contrat_actuel = unite.get_contrat_actuel()
    locataire_actuel = unite.get_locataire_actuel()
    
    # Récupérer les réservations actives
    reservations_actives = unite.reservations.filter(
        is_deleted=False,
        statut__in=['en_attente', 'confirmee']
    ).select_related('locataire_potentiel').order_by('-date_reservation')
    
    # Récupérer toutes les pièces de l'unité
    pieces_unite = unite.pieces.filter(is_deleted=False).order_by('type_piece', 'nom')
    
    # Statistiques de l'unité
    stats_unite = {
        'revenus_annuels_potentiels': unite.get_revenus_potentiels_annuels(),
        'taux_occupation': unite.get_taux_occupation(),
        'nombre_contrats_total': contrats.count(),
        'nombre_reservations_total': unite.reservations.filter(is_deleted=False).count(),
        'duree_moyenne_occupation': unite.get_duree_moyenne_occupation(),
    }
    
    # Informations sur la propriété parente
    propriete_stats = {
        'total_unites': unite.propriete.unites_locatives.filter(is_deleted=False).count(),
        'unites_disponibles': unite.propriete.unites_locatives.filter(
            statut='disponible', is_deleted=False
        ).count(),
        'taux_occupation_propriete': unite.propriete.get_taux_occupation_global(),
        'revenus_mensuels_propriete': unite.propriete.get_revenus_mensuels_actuels(),
    }
    
    # Bailleur effectif (spécifique à l'unité ou celui de la propriété)
    bailleur_effectif = unite.bailleur or unite.propriete.bailleur
    
    # Historique des paiements (si contrat actuel)
    historique_paiements = []
    if contrat_actuel:
        from paiements.models import Paiement
        historique_paiements = Paiement.objects.filter(
            contrat=contrat_actuel
        ).order_by('-date_paiement')[:10]
    
    # Prochaines échéances
    prochaines_echeances = []
    if contrat_actuel and not contrat_actuel.est_resilie:
        # Calculer les prochaines échéances de loyer
        from dateutil.relativedelta import relativedelta
        date_actuelle = timezone.now().date()
        for i in range(3):  # 3 prochains mois
            date_echeance = date_actuelle + relativedelta(months=i+1)
            prochaines_echeances.append({
                'date': date_echeance,
                'montant': unite.get_loyer_total(),
                'type': 'Loyer mensuel'
            })
    
    # Alertes et notifications
    alertes = []
    
    # Alerte si réservation expire bientôt
    for reservation in reservations_actives:
        if reservation.date_expiration and reservation.date_expiration <= timezone.now().date() + timedelta(days=7):
            alertes.append({
                'type': 'warning',
                'message': f'La réservation de {reservation.locataire_potentiel} expire le {reservation.date_expiration}'
            })
    
    # Alerte si contrat se termine bientôt
    if contrat_actuel and contrat_actuel.date_fin:
        jours_restants = (contrat_actuel.date_fin - timezone.now().date()).days
        if jours_restants <= 60:
            alertes.append({
                'type': 'danger' if jours_restants <= 30 else 'warning',
                'message': f'Le contrat se termine dans {jours_restants} jours'
            })
    
    # Alerte si unité nécessite maintenance
    if unite.statut == 'en_renovation':
        alertes.append({
            'type': 'info',
            'message': 'Unité en cours de rénovation'
        })
    
    context = {
        'unite': unite,
        'bailleur_effectif': bailleur_effectif,
        'contrats': contrats,
        'contrat_actuel': contrat_actuel,
        'locataire_actuel': locataire_actuel,
        'reservations_actives': reservations_actives,
        'pieces_unite': pieces_unite,
        'stats_unite': stats_unite,
        'propriete_stats': propriete_stats,
        'historique_paiements': historique_paiements,
        'prochaines_echeances': prochaines_echeances,
        'alertes': alertes,
        'page_title': f'Unité {unite.numero_unite}',
        'page_icon': 'building',
    }
    
    return render(request, 'proprietes/unites/detail_complet.html', context)


@login_required
def api_recherche_unites_live(request):
    """API pour la recherche en temps réel des unités."""
    search = request.GET.get('search', '').strip()
    
    if len(search) < 2:
        return JsonResponse({'unites': [], 'count': 0})
    
    # Recherche rapide
    unites = UniteLocative.objects.select_related(
        'propriete', 'propriete__bailleur', 'bailleur'
    ).filter(
        Q(numero_unite__icontains=search) |
        Q(nom__icontains=search) |
        Q(propriete__titre__icontains=search) |
        Q(propriete__ville__icontains=search),
        is_deleted=False
    )[:10]
    
    results = []
    for unite in unites:
        bailleur_effectif = unite.bailleur or unite.propriete.bailleur
        results.append({
            'id': unite.id,
            'numero_unite': unite.numero_unite,
            'nom': unite.nom,
            'propriete': unite.propriete.titre,
            'ville': unite.propriete.ville or '',
            'adresse': unite.propriete.adresse or '',
            'statut': unite.get_statut_display(),
            'statut_code': unite.statut,
            'type_unite': unite.get_type_unite_display(),
            'loyer_mensuel': float(unite.loyer_mensuel),
            'loyer_total': float(unite.get_loyer_total()),
            'surface': float(unite.surface) if unite.surface else None,
            'etage': unite.etage,
            'bailleur': f"{bailleur_effectif.nom} {bailleur_effectif.prenom}" if bailleur_effectif else '',
            'url_detail': f"/proprietes/unites/{unite.id}/",
            'url_detail_complet': f"/proprietes/unites/{unite.id}/detail-complet/",
        })
    
    return JsonResponse({
        'unites': results,
        'count': len(results)
    })


@login_required
def api_statistiques_recherche(request):
    """API pour récupérer les statistiques générales des unités."""
    stats = {
        'total_unites': UniteLocative.objects.filter(is_deleted=False).count(),
        'unites_disponibles': UniteLocative.objects.filter(
            statut='disponible', is_deleted=False
        ).count(),
        'unites_occupees': UniteLocative.objects.filter(
            statut='occupee', is_deleted=False
        ).count(),
        'unites_reservees': UniteLocative.objects.filter(
            statut='reservee', is_deleted=False
        ).count(),
        'revenus_mensuels_total': float(
            UniteLocative.objects.filter(
                is_deleted=False
            ).aggregate(Sum('loyer_mensuel'))['loyer_mensuel__sum'] or 0
        ),
    }
    
    # Répartition par type
    stats['repartition_types'] = list(
        UniteLocative.objects.filter(is_deleted=False).values(
            'type_unite'
        ).annotate(
            count=Count('id'),
            label=Count('type_unite')
        ).order_by('-count')
    )
    
    # Top 5 des propriétés avec le plus d'unités
    stats['top_proprietes'] = list(
        Propriete.objects.filter(
            unites_locatives__is_deleted=False
        ).annotate(
            nb_unites=Count('unites_locatives')
        ).order_by('-nb_unites')[:5].values(
            'id', 'titre', 'nb_unites'
        )
    )
    
    return JsonResponse(stats)


@login_required
def convertir_reservation_en_contrat(request, reservation_id):
    """Vue pour convertir une réservation confirmée en contrat."""
    # Vérification des permissions : Seul PRIVILEGE peut convertir
    from core.utils import check_group_permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE'], 'add')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('proprietes:unites_liste')
    
    reservation = get_object_or_404(ReservationUnite, pk=reservation_id, is_deleted=False)
    
    # Vérifier que la réservation peut être convertie
    if not reservation.peut_etre_convertie_en_contrat():
        messages.error(
            request,
            "Cette réservation ne peut pas être convertie en contrat. "
            "Elle doit être confirmée et toujours active."
        )
        return redirect('proprietes:unite_detail', pk=reservation.unite_locative.pk)
    
    if request.method == 'POST':
        try:
            # Créer le contrat à partir de la réservation
            from contrats.models import Contrat
            
            contrat = Contrat.objects.create(
                propriete=reservation.unite_locative.propriete,
                locataire=reservation.locataire_potentiel,
                unite_locative=reservation.unite_locative,
                date_debut=reservation.date_debut_souhaitee,
                date_fin=reservation.date_fin_prevue,
                date_signature=timezone.now().date(),
                loyer_mensuel=str(reservation.unite_locative.loyer_mensuel),
                charges_mensuelles=str(reservation.unite_locative.charges_mensuelles),
                depot_garantie=str(reservation.unite_locative.caution_demandee),
                jour_paiement=1,  # Par défaut le 1er du mois
                mode_paiement='virement',  # Par défaut
                est_actif=True,
                cree_par=request.user,
                notes=f"Contrat créé à partir de la réservation #{reservation.pk}"
            )
            
            # Mettre à jour le statut de la réservation
            reservation.statut = 'convertie_contrat'
            reservation.save()
            
            # Mettre à jour le statut de l'unité
            reservation.unite_locative.statut = 'occupee'
            reservation.unite_locative.save()
            
            messages.success(
                request,
                f"Réservation convertie en contrat avec succès ! "
                f"Contrat créé : {contrat.numero_contrat}"
            )
            
            return redirect('contrats:detail', pk=contrat.pk)
            
        except Exception as e:
            messages.error(
                request,
                f"Erreur lors de la conversion de la réservation en contrat : {str(e)}"
            )
            return redirect('proprietes:unite_detail', pk=reservation.unite_locative.pk)
    
    # Afficher une page de confirmation
    context = {
        'reservation': reservation,
        'unite': reservation.unite_locative,
        'locataire': reservation.locataire_potentiel,
    }
    
    return render(request, 'proprietes/reservations/confirmation_conversion.html', context)
