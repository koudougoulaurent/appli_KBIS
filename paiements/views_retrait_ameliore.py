from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from datetime import datetime
from core.utils import check_group_permissions
from proprietes.models import Bailleur
from contrats.models import Contrat
from .services_retrait import ServiceGestionRetrait
from .services_retrait_pdf import ServiceGenerationRetraitPDF
from .models import RetraitBailleur


@login_required
def creer_retrait_automatique_ameliore(request):
    """
    Création automatique des retraits avec sélection de contrat spécifique
    """
    permissions = check_group_permissions(request.user, [], 'add')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:retraits_liste')
    
    # Vérifier la période autorisée
    periode_ok, message_periode = ServiceGestionRetrait.verifier_periode_retrait()
    
    if request.method == 'POST':
        mois_retrait = request.POST.get('mois_retrait')
        contrat_id = request.POST.get('contrat_id')
        type_generation = request.POST.get('type_generation', 'contrat_specifique')
        
        try:
            # Parser la date
            if mois_retrait:
                mois_date = datetime.strptime(mois_retrait, '%Y-%m').date()
            else:
                mois_date = timezone.now().date().replace(day=1)
            
            if type_generation == 'contrat_specifique':
                # Génération pour un contrat spécifique
                if not contrat_id:
                    messages.error(request, 'Veuillez sélectionner un contrat.')
                    return redirect('paiements:retrait_auto_create_ameliore')
                
                contrat = get_object_or_404(Contrat, id=contrat_id)
                bailleur = contrat.propriete.bailleur
                
                # Créer le retrait pour ce contrat spécifique
                resultat = ServiceGestionRetrait.creer_retrait_avec_restrictions(
                    bailleur, mois_date, request.user
                )
                
                if resultat['success']:
                    messages.success(request, f'Retrait créé avec succès pour le contrat {contrat.numero_contrat}')
                    if resultat.get('charges_appliquees', 0) > 0:
                        messages.info(request, f"{resultat['charges_appliquees']} charge(s) appliquée(s) automatiquement")
                else:
                    messages.error(request, resultat['message'])
                
            elif type_generation == 'bailleur_specifique':
                # Génération pour un bailleur spécifique
                bailleur_id = request.POST.get('bailleur_id')
                if not bailleur_id:
                    messages.error(request, 'Veuillez sélectionner un bailleur.')
                    return redirect('paiements:retrait_auto_create_ameliore')
                
                bailleur = get_object_or_404(Bailleur, id=bailleur_id)
                
                # Créer le retrait pour ce bailleur
                resultat = ServiceGestionRetrait.creer_retrait_avec_restrictions(
                    bailleur, mois_date, request.user
                )
                
                if resultat['success']:
                    messages.success(request, f'Retrait créé avec succès pour {bailleur.get_nom_complet()}')
                    if resultat.get('charges_appliquees', 0) > 0:
                        messages.info(request, f"{resultat['charges_appliquees']} charge(s) appliquée(s) automatiquement")
                else:
                    messages.error(request, resultat['message'])
                
            elif type_generation == 'tous_bailleurs':
                # Génération pour tous les bailleurs (logique existante améliorée)
                if not periode_ok:
                    messages.error(request, message_periode)
                    return redirect('paiements:retrait_auto_create_ameliore')
                
                # Récupérer tous les bailleurs avec des propriétés (pas seulement ceux avec contrats actifs)
                bailleurs = Bailleur.objects.filter(
                    proprietes__isnull=False
                ).distinct()
                
                retraits_crees = 0
                retraits_existants = 0
                erreurs = 0
                
                for bailleur in bailleurs:
                    try:
                        # Vérifier si un retrait existe déjà
                        retrait_existant = RetraitBailleur.objects.filter(
                            bailleur=bailleur,
                            mois_retrait__year=mois_date.year,
                            mois_retrait__month=mois_date.month
                        ).exists()
                        
                        if retrait_existant:
                            retraits_existants += 1
                            continue
                        
                        # Créer le retrait
                        resultat = ServiceGestionRetrait.creer_retrait_avec_restrictions(
                            bailleur, mois_date, request.user
                        )
                        
                        if resultat['success']:
                            retraits_crees += 1
                        else:
                            erreurs += 1
                            
                    except Exception as e:
                        erreurs += 1
                        continue
                
                # Messages de résultat
                if retraits_crees > 0:
                    messages.success(request, f'{retraits_crees} retrait(s) créé(s) avec succès')
                if retraits_existants > 0:
                    messages.info(request, f'{retraits_existants} retrait(s) existaient déjà')
                if erreurs > 0:
                    messages.warning(request, f'{erreurs} erreur(s) lors de la création')
            
            return redirect('paiements:retraits_liste')
            
        except Exception as e:
            messages.error(request, f'Erreur lors de la création automatique: {str(e)}')
    
    # Récupérer les données pour le formulaire
    contrats_actifs = Contrat.objects.filter(
        est_actif=True,
        est_resilie=False
    ).select_related('propriete', 'propriete__bailleur', 'locataire').order_by('propriete__bailleur__nom', 'numero_contrat')
    
    bailleurs_actifs = Bailleur.objects.filter(
        proprietes__contrats__est_actif=True,
        proprietes__contrats__est_resilie=False
    ).distinct().order_by('nom', 'prenom')
    
    # Statistiques
    total_contrats = contrats_actifs.count()
    total_bailleurs = bailleurs_actifs.count()
    
    context = {
        'periode_autorisee': periode_ok,
        'message_periode': message_periode,
        'contrats_actifs': contrats_actifs,
        'bailleurs_actifs': bailleurs_actifs,
        'total_contrats': total_contrats,
        'total_bailleurs': total_bailleurs,
        'date_actuelle': timezone.now().date(),
    }
    
    return render(request, 'paiements/retraits/creer_retrait_automatique_ameliore.html', context)


@login_required
def get_contrat_details_ajax(request):
    """
    API AJAX pour récupérer les détails d'un contrat
    """
    contrat_id = request.GET.get('contrat_id')
    
    if not contrat_id:
        return JsonResponse({'error': 'ID de contrat requis'}, status=400)
    
    try:
        contrat = Contrat.objects.select_related(
            'propriete', 'propriete__bailleur', 'locataire'
        ).get(id=contrat_id)
        
        # Calculer les détails du contrat
        details = {
            'contrat_id': contrat.id,
            'numero_contrat': contrat.numero_contrat,
            'bailleur': contrat.propriete.bailleur.get_nom_complet(),
            'locataire': contrat.locataire.get_nom_complet(),
            'propriete': contrat.propriete.titre,
            'loyer_mensuel': float(contrat.loyer_mensuel or 0),
            'charges_mensuelles': float(contrat.charges_mensuelles or 0),
            'montant_total': float((contrat.loyer_mensuel or 0) + (contrat.charges_mensuelles or 0)),
            'date_debut': contrat.date_debut.strftime('%d/%m/%Y'),
            'date_fin': contrat.date_fin.strftime('%d/%m/%Y') if contrat.date_fin else 'Non définie',
            'statut': 'Actif' if contrat.est_actif else 'Inactif'
        }
        
        return JsonResponse({'success': True, 'details': details})
        
    except Contrat.DoesNotExist:
        return JsonResponse({'error': 'Contrat non trouvé'}, status=404)
    except Exception as e:
        return JsonResponse({'error': f'Erreur: {str(e)}'}, status=500)


@login_required
def generer_pdf_retrait(request, retrait_id):
    """
    Génère un PDF pour un retrait spécifique avec template.
    """
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE', 'CAISSE', 'CONTROLES', 'GESTIONNAIRE'], 'view')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:retraits_liste')
    
    try:
        retrait = get_object_or_404(RetraitBailleur, id=retrait_id)
        
        # Générer le PDF avec le service
        service_pdf = ServiceGenerationRetraitPDF()
        response = service_pdf.generer_pdf_retrait(retrait, user=request.user)
        
        return response
        
    except Exception as e:
        messages.error(request, f'Erreur lors de la génération du PDF: {str(e)}')
        return redirect('paiements:retraits_liste')


@login_required
def generer_pdf_retraits_multiple(request):
    """
    Génère un PDF consolidé pour plusieurs retraits.
    """
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE', 'CAISSE', 'CONTROLES', 'GESTIONNAIRE'], 'view')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:retraits_liste')
    
    try:
        # Récupérer les retraits sélectionnés
        retrait_ids = request.GET.getlist('retrait_ids')
        if not retrait_ids:
            messages.error(request, 'Aucun retrait sélectionné.')
            return redirect('paiements:retraits_liste')
        
        retraits = RetraitBailleur.objects.filter(id__in=retrait_ids)
        
        if not retraits.exists():
            messages.error(request, 'Aucun retrait trouvé.')
            return redirect('paiements:retraits_liste')
        
        # Générer le PDF consolidé
        service_pdf = ServiceGenerationRetraitPDF()
        response = service_pdf.generer_pdf_retrait_multiple(retraits, user=request.user)
        
        return response
        
    except Exception as e:
        messages.error(request, f'Erreur lors de la génération du PDF consolidé: {str(e)}')
        return redirect('paiements:retraits_liste')


@login_required
def generer_pdf_retraits_mois(request):
    """
    Génère un PDF consolidé pour tous les retraits d'un mois.
    """
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE', 'CAISSE', 'CONTROLES', 'GESTIONNAIRE'], 'view')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:retraits_liste')
    
    try:
        mois = request.GET.get('mois')
        annee = request.GET.get('annee')
        
        if not mois or not annee:
            messages.error(request, 'Mois et année requis.')
            return redirect('paiements:retraits_liste')
        
        # Récupérer tous les retraits du mois
        retraits = RetraitBailleur.objects.filter(
            mois_retrait__year=annee,
            mois_retrait__month=mois
        )
        
        if not retraits.exists():
            messages.error(request, f'Aucun retrait trouvé pour {mois}/{annee}.')
            return redirect('paiements:retraits_liste')
        
        # Générer le PDF consolidé
        service_pdf = ServiceGenerationRetraitPDF()
        response = service_pdf.generer_pdf_retrait_multiple(retraits, user=request.user)
        
        return response
        
    except Exception as e:
        messages.error(request, f'Erreur lors de la génération du PDF du mois: {str(e)}')
        return redirect('paiements:retraits_liste')
