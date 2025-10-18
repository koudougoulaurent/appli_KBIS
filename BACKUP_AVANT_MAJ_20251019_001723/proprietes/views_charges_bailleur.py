"""
Vues pour la gestion des charges bailleur avec intégration intelligente.
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from decimal import Decimal
from datetime import date, datetime
from typing import Dict, List

from proprietes.models import ChargesBailleur, Bailleur, Propriete
from contrats.models import Contrat
from paiements.services_charges_bailleur import ServiceChargesBailleurIntelligent
from core.utils import check_group_permissions_with_fallback


@login_required
def liste_charges_bailleur(request):
    """
    Liste toutes les charges bailleur avec filtres et recherche.
    """
    # Vérification des permissions
    permissions = check_group_permissions_with_fallback(
        request.user, 
        ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE'], 
        'view'
    )
    
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('core:accueil')
    
    # Filtres
    search = request.GET.get('search', '')
    statut = request.GET.get('statut', '')
    priorite = request.GET.get('priorite', '')
    type_charge = request.GET.get('type_charge', '')
    bailleur_id = request.GET.get('bailleur', '')
    propriete_id = request.GET.get('propriete', '')
    mois = request.GET.get('mois', '')
    
    # Base queryset
    charges = ChargesBailleur.objects.select_related(
        'propriete', 'propriete__bailleur', 'cree_par'
    ).order_by('-date_creation')
    
    # Appliquer les filtres
    if search:
        charges = charges.filter(
            Q(titre__icontains=search) |
            Q(description__icontains=search) |
            Q(numero_charge__icontains=search) |
            Q(propriete__adresse__icontains=search) |
            Q(propriete__bailleur__nom__icontains=search)
        )
    
    if statut:
        charges = charges.filter(statut=statut)
    
    if priorite:
        charges = charges.filter(priorite=priorite)
    
    if type_charge:
        charges = charges.filter(type_charge=type_charge)
    
    if bailleur_id:
        charges = charges.filter(propriete__bailleur_id=bailleur_id)
    
    if propriete_id:
        charges = charges.filter(propriete_id=propriete_id)
    
    if mois:
        try:
            mois_date = datetime.strptime(mois, '%Y-%m').date()
            charges = charges.filter(
                date_charge__year=mois_date.year,
                date_charge__month=mois_date.month
            )
        except ValueError:
            pass
    
    # Pagination
    paginator = Paginator(charges, 20)
    page_number = request.GET.get('page')
    charges_page = paginator.get_page(page_number)
    
    # Statistiques
    stats = {
        'total_charges': charges.count(),
        'total_montant': charges.aggregate(total=Sum('montant'))['total'] or Decimal('0'),
        'total_restant': charges.aggregate(total=Sum('montant_restant'))['total'] or Decimal('0'),
        'charges_en_attente': charges.filter(statut='en_attente').count(),
        'charges_deduites': charges.filter(statut='deduite_retrait').count(),
        'charges_remboursees': charges.filter(statut='remboursee').count(),
    }
    
    # Options pour les filtres
    bailleurs = Bailleur.objects.filter(proprietes__charges_bailleur__isnull=False).distinct()
    proprietes = Propriete.objects.filter(charges_bailleur__isnull=False).distinct()
    
    context = {
        'charges': charges_page,
        'stats': stats,
        'bailleurs': bailleurs,
        'proprietes': proprietes,
        'filters': {
            'search': search,
            'statut': statut,
            'priorite': priorite,
            'type_charge': type_charge,
            'bailleur_id': bailleur_id,
            'propriete_id': propriete_id,
            'mois': mois,
        },
        'statut_choices': ChargesBailleur.STATUT_CHOICES,
        'priorite_choices': ChargesBailleur.PRIORITE_CHOICES,
        'type_charge_choices': ChargesBailleur.TYPE_CHARGE_CHOICES,
    }
    
    return render(request, 'proprietes/charges_bailleur/liste.html', context)


@login_required
def detail_charge_bailleur(request, pk):
    """
    Détail d'une charge bailleur avec historique et impact.
    """
    # Vérification des permissions
    permissions = check_group_permissions_with_fallback(
        request.user, 
        ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE'], 
        'view'
    )
    
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('core:accueil')
    
    charge = get_object_or_404(ChargesBailleur, pk=pk)
    
    # Historique des déductions
    historique = charge.get_historique_deductions()
    
    # Impact sur les retraits
    impact_retrait = charge.get_impact_sur_retrait()
    
    # Résumé financier
    resume_financier = charge.get_resume_financier()
    
    # Charges similaires de la même propriété
    charges_similaires = ChargesBailleur.objects.filter(
        propriete=charge.propriete,
        type_charge=charge.type_charge
    ).exclude(pk=charge.pk).order_by('-date_creation')[:5]
    
    context = {
        'charge': charge,
        'historique': historique,
        'impact_retrait': impact_retrait,
        'resume_financier': resume_financier,
        'charges_similaires': charges_similaires,
    }
    
    return render(request, 'proprietes/charges_bailleur/detail.html', context)


@login_required
def creer_charge_bailleur(request):
    """
    Création d'une nouvelle charge bailleur.
    """
    # Vérification des permissions
    permissions = check_group_permissions_with_fallback(
        request.user, 
        ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE'], 
        'add'
    )
    
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('core:accueil')
    
    if request.method == 'POST':
        # Récupérer les données du formulaire
        propriete_id = request.POST.get('propriete')
        titre = request.POST.get('titre', '').strip()
        description = request.POST.get('description', '').strip()
        type_charge = request.POST.get('type_charge')
        priorite = request.POST.get('priorite', 'normale')
        montant = request.POST.get('montant', '').strip()
        date_charge = request.POST.get('date_charge')
        date_echeance = request.POST.get('date_echeance', '').strip()
        
        # Validation détaillée
        errors = []
        
        if not propriete_id:
            errors.append('La propriété est obligatoire.')
        elif not Propriete.objects.filter(pk=propriete_id).exists():
            errors.append('La propriété sélectionnée n\'existe pas.')
        
        if not titre:
            errors.append('Le titre de la charge est obligatoire.')
        elif len(titre) < 3:
            errors.append('Le titre doit contenir au moins 3 caractères.')
        
        if not description:
            errors.append('La description détaillée est obligatoire.')
        elif len(description) < 10:
            errors.append('La description doit contenir au moins 10 caractères.')
        
        if not type_charge:
            errors.append('Le type de charge est obligatoire.')
        elif type_charge not in [choice[0] for choice in ChargesBailleur.TYPE_CHARGE_CHOICES]:
            errors.append('Le type de charge sélectionné n\'est pas valide.')
        
        if not montant:
            errors.append('Le montant est obligatoire.')
        else:
            try:
                # Remplacer les virgules par des points pour la conversion
                montant_clean = montant.replace(',', '.')
                montant_decimal = Decimal(montant_clean)
                if montant_decimal <= 0:
                    errors.append('Le montant doit être supérieur à 0.')
                elif montant_decimal > Decimal('999999999.99'):
                    errors.append('Le montant est trop élevé (maximum 999,999,999.99 F CFA).')
            except (ValueError, TypeError):
                errors.append('Le montant doit être un nombre valide.')
        
        if not date_charge:
            errors.append('La date de la charge est obligatoire.')
        else:
            try:
                date_charge_obj = datetime.strptime(date_charge, '%Y-%m-%d').date()
                if date_charge_obj > date.today():
                    errors.append('La date de la charge ne peut pas être dans le futur.')
            except ValueError:
                errors.append('Le format de la date est invalide (utilisez YYYY-MM-DD).')
        
        if date_echeance:
            try:
                date_echeance_obj = datetime.strptime(date_echeance, '%Y-%m-%d').date()
                if date_charge and date_charge_obj and date_echeance_obj < date_charge_obj:
                    errors.append('La date d\'échéance ne peut pas être antérieure à la date de la charge.')
            except ValueError:
                errors.append('Le format de la date d\'échéance est invalide (utilisez YYYY-MM-DD).')
        
        # Si des erreurs existent, les afficher
        if errors:
            for error in errors:
                messages.error(request, error)
            
            # Retourner au formulaire avec les données saisies
            context = {
                'proprietes': Propriete.objects.filter(contrats__est_actif=True).distinct().order_by('adresse'),
                'type_charge_choices': ChargesBailleur.TYPE_CHARGE_CHOICES,
                'priorite_choices': ChargesBailleur.PRIORITE_CHOICES,
                'form_data': {
                    'propriete_id': propriete_id,
                    'titre': titre,
                    'description': description,
                    'type_charge': type_charge,
                    'priorite': priorite,
                    'montant': montant,
                    'date_charge': date_charge,
                    'date_echeance': date_echeance,
                }
            }
            return render(request, 'proprietes/charges_bailleur/creer.html', context)
        
        # Si pas d'erreurs, créer la charge
        try:
            # Nettoyer le montant (remplacer virgules par points)
            montant_clean = montant.replace(',', '.')
            
            charge = ChargesBailleur.objects.create(
                propriete_id=propriete_id,
                titre=titre,
                description=description,
                type_charge=type_charge,
                priorite=priorite,
                montant=Decimal(montant_clean),
                date_charge=datetime.strptime(date_charge, '%Y-%m-%d').date(),
                date_echeance=datetime.strptime(date_echeance, '%Y-%m-%d').date() if date_echeance else None,
                cree_par=request.user
            )
            
            messages.success(request, f'Charge "{charge.titre}" créée avec succès.')
            return redirect('proprietes:detail_charge_bailleur', pk=charge.pk)
            
        except Exception as e:
            messages.error(request, f'Erreur lors de la création de la charge: {str(e)}')
            # Retourner au formulaire avec les données saisies
            context = {
                'proprietes': Propriete.objects.filter(contrats__est_actif=True).distinct().order_by('adresse'),
                'type_charge_choices': ChargesBailleur.TYPE_CHARGE_CHOICES,
                'priorite_choices': ChargesBailleur.PRIORITE_CHOICES,
                'form_data': {
                    'propriete_id': propriete_id,
                    'titre': titre,
                    'description': description,
                    'type_charge': type_charge,
                    'priorite': priorite,
                    'montant': montant,
                    'date_charge': date_charge,
                    'date_echeance': date_echeance,
                }
            }
            return render(request, 'proprietes/charges_bailleur/creer.html', context)
    
    # Options pour le formulaire - toutes les propriétés disponibles
    proprietes = Propriete.objects.filter(
        is_deleted=False
    ).select_related('bailleur').order_by('adresse')
    
    
    context = {
        'proprietes': proprietes,
        'type_charge_choices': ChargesBailleur.TYPE_CHARGE_CHOICES,
        'priorite_choices': ChargesBailleur.PRIORITE_CHOICES,
    }
    
    return render(request, 'proprietes/charges_bailleur/creer.html', context)


@login_required
def modifier_charge_bailleur(request, pk):
    """
    Modification d'une charge bailleur.
    """
    # Vérification des permissions
    permissions = check_group_permissions_with_fallback(
        request.user, 
        ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE'], 
        'change'
    )
    
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('core:accueil')
    
    charge = get_object_or_404(ChargesBailleur, pk=pk)
    
    # Vérifier si la charge peut être modifiée
    if not charge.peut_etre_modifiee():
        messages.error(request, 'Cette charge ne peut pas être modifiée.')
        return redirect('proprietes:detail_charge_bailleur', pk=charge.pk)
    
    if request.method == 'POST':
        try:
            # Mettre à jour les champs modifiables
            charge.titre = request.POST.get('titre', charge.titre)
            charge.description = request.POST.get('description', charge.description)
            charge.type_charge = request.POST.get('type_charge', charge.type_charge)
            charge.priorite = request.POST.get('priorite', charge.priorite)
            charge.montant = Decimal(request.POST.get('montant', charge.montant))
            charge.date_charge = datetime.strptime(
                request.POST.get('date_charge'), '%Y-%m-%d'
            ).date()
            
            date_echeance = request.POST.get('date_echeance', '')
            if date_echeance:
                charge.date_echeance = datetime.strptime(date_echeance, '%Y-%m-%d').date()
            else:
                charge.date_echeance = None
            
            charge.save()
            
            messages.success(request, f'Charge "{charge.titre}" modifiée avec succès.')
            return redirect('proprietes:detail_charge_bailleur', pk=charge.pk)
            
        except Exception as e:
            messages.error(request, f'Erreur lors de la modification: {str(e)}')
    
    context = {
        'charge': charge,
        'type_charge_choices': ChargesBailleur.TYPE_CHARGE_CHOICES,
        'priorite_choices': ChargesBailleur.PRIORITE_CHOICES,
    }
    
    return render(request, 'proprietes/charges_bailleur/modifier.html', context)


@login_required
def annuler_charge_bailleur(request, pk):
    """
    Annulation d'une charge bailleur.
    """
    # Vérification des permissions
    permissions = check_group_permissions_with_fallback(
        request.user, 
        ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE'], 
        'delete'
    )
    
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('core:accueil')
    
    charge = get_object_or_404(ChargesBailleur, pk=pk)
    
    # Vérifier si la charge peut être annulée
    if not charge.peut_etre_annulee():
        messages.error(request, 'Cette charge ne peut pas être annulée.')
        return redirect('proprietes:detail_charge_bailleur', pk=charge.pk)
    
    if request.method == 'POST':
        try:
            charge.statut = 'annulee'
            charge.save()
            
            messages.success(request, f'Charge "{charge.titre}" annulée avec succès.')
            return redirect('proprietes:liste_charges_bailleur')
            
        except Exception as e:
            messages.error(request, f'Erreur lors de l\'annulation: {str(e)}')
    
    context = {
        'charge': charge,
    }
    
    return render(request, 'proprietes/charges_bailleur/annuler.html', context)


@login_required
def rapport_charges_bailleur(request):
    """
    Rapport détaillé des charges bailleur pour un mois donné.
    """
    # Vérification des permissions
    permissions = check_group_permissions_with_fallback(
        request.user, 
        ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE'], 
        'view'
    )
    
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('core:accueil')
    
    # Paramètres du rapport
    mois = request.GET.get('mois', timezone.now().strftime('%Y-%m'))
    bailleur_id = request.GET.get('bailleur', '')
    
    try:
        mois_date = datetime.strptime(mois, '%Y-%m').date()
    except ValueError:
        mois_date = timezone.now().date().replace(day=1)
    
    # Récupérer le bailleur si spécifié
    bailleur = None
    if bailleur_id:
        try:
            bailleur = Bailleur.objects.get(pk=bailleur_id)
        except Bailleur.DoesNotExist:
            pass
    
    # Générer le rapport
    if bailleur:
        rapport = ServiceChargesBailleurIntelligent.generer_rapport_charges_bailleur(
            bailleur, mois_date
        )
    else:
        # Rapport global pour tous les bailleurs
        rapport = ServiceChargesBailleurIntelligent.generer_rapport_global_charges_bailleur(
            mois_date
        )
    
    # Options pour les filtres
    bailleurs = Bailleur.objects.filter(proprietes__charges_bailleur__isnull=False).distinct()
    
    context = {
        'rapport': rapport,
        'mois': mois,
        'bailleur_id': bailleur_id,
        'bailleurs': bailleurs,
        'mois_formate': mois_date.strftime('%B %Y'),
    }
    
    return render(request, 'proprietes/charges_bailleur/rapport.html', context)


@login_required
def api_charges_bailleur_mois(request):
    """
    API pour récupérer les charges bailleur d'un mois donné.
    """
    # Vérification des permissions
    permissions = check_group_permissions_with_fallback(
        request.user, 
        ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE'], 
        'view'
    )
    
    if not permissions['allowed']:
        return JsonResponse({'error': 'Permission refusée'}, status=403)
    
    mois = request.GET.get('mois')
    bailleur_id = request.GET.get('bailleur')
    
    if not mois:
        return JsonResponse({'error': 'Paramètre mois requis'}, status=400)
    
    try:
        mois_date = datetime.strptime(mois, '%Y-%m').date()
    except ValueError:
        return JsonResponse({'error': 'Format de mois invalide'}, status=400)
    
    try:
        if bailleur_id:
            bailleur = Bailleur.objects.get(pk=bailleur_id)
            charges_data = ServiceChargesBailleurIntelligent.calculer_charges_bailleur_pour_mois(
                bailleur, mois_date
            )
        else:
            # Toutes les charges du mois
            charges = ChargesBailleur.objects.filter(
                date_charge__year=mois_date.year,
                date_charge__month=mois_date.month
            ).select_related('propriete', 'propriete__bailleur')
            
            charges_data = {
                'total_charges': sum(charge.montant_restant for charge in charges),
                'nombre_charges': charges.count(),
                'charges_details': [
                    {
                        'id': charge.id,
                        'titre': charge.titre,
                        'montant': float(charge.montant),
                        'montant_restant': float(charge.montant_restant),
                        'statut': charge.statut,
                        'propriete': charge.propriete.adresse,
                        'bailleur': charge.propriete.bailleur.get_nom_complet(),
                    }
                    for charge in charges
                ]
            }
        
        return JsonResponse({
            'success': True,
            'data': charges_data
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
