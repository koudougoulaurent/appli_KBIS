"""
Vues de diagnostic pour les avances - Accessible via l'interface web
"""
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.conf import settings
from datetime import date
from dateutil.relativedelta import relativedelta

from contrats.models import Contrat
from .models_avance import AvanceLoyer, ConsommationAvance
from .services_consommation_dynamique import ServiceConsommationDynamique


@login_required
def diagnostic_avances_contrat(request, contrat_id):
    """
    Page de diagnostic pour les avances d'un contrat
    Accessible via l'interface web pour diagnostiquer les problèmes de consommation
    """
    contrat = get_object_or_404(Contrat, id=contrat_id)
    
    # Récupérer toutes les avances du contrat
    avances = AvanceLoyer.objects.filter(contrat=contrat).order_by('-date_avance')
    
    diagnostic_data = []
    mois_actuel = date.today().replace(day=1)
    
    for avance in avances:
        # Informations de base
        info = {
            'id': avance.id,
            'montant_avance': float(avance.montant_avance),
            'montant_restant': float(avance.montant_restant),
            'loyer_mensuel': float(avance.loyer_mensuel),
            'nombre_mois_couverts': avance.nombre_mois_couverts,
            'statut': avance.statut,
            'date_avance': avance.date_avance.strftime('%d/%m/%Y') if avance.date_avance else None,
            'mois_debut_couverture': avance.mois_debut_couverture.strftime('%d/%m/%Y') if avance.mois_debut_couverture else 'NON DÉFINI',
            'mois_fin_couverture': avance.mois_fin_couverture.strftime('%d/%m/%Y') if avance.mois_fin_couverture else None,
            'mois_actuel': mois_actuel.strftime('%d/%m/%Y'),
            'problemes': [],
            'mois_a_consommer': [],
            'consommations_existantes': []
        }
        
        # Vérifier les problèmes potentiels
        if not avance.mois_debut_couverture:
            info['problemes'].append('⚠️ mois_debut_couverture n\'est pas défini')
        
        if avance.mois_debut_couverture:
            mois_debut_norm = avance.mois_debut_couverture.replace(day=1)
            if mois_debut_norm >= mois_actuel:
                info['problemes'].append(f'⚠️ Mois début ({mois_debut_norm.strftime("%B %Y")}) est dans le futur ou actuel')
            
            # Calculer les mois qui devraient être consommés
            mois_courant = mois_debut_norm
            for _ in range(avance.nombre_mois_couverts):
                mois_courant_norm = mois_courant.replace(day=1)
                if mois_courant_norm < mois_actuel:
                    est_consomme = avance.est_mois_consomme(mois_courant_norm)
                    mois_info = {
                        'mois': mois_courant_norm.strftime('%B %Y'),
                        'date': mois_courant_norm.strftime('%d/%m/%Y'),
                        'est_consomme': est_consomme,
                        'devrait_etre_consomme': True
                    }
                    if not est_consomme:
                        info['mois_a_consommer'].append(mois_info)
                    else:
                        # Vérifier la consommation existante
                        consommations = ConsommationAvance.objects.filter(
                            avance=avance,
                            mois_consomme__year=mois_courant_norm.year,
                            mois_consomme__month=mois_courant_norm.month
                        )
                        for c in consommations:
                            info['consommations_existantes'].append({
                                'mois': mois_courant_norm.strftime('%B %Y'),
                                'date_consommation': c.mois_consomme.strftime('%d/%m/%Y'),
                                'montant_consomme': float(c.montant_consomme),
                                'montant_restant_apres': float(c.montant_restant_apres)
                            })
                mois_courant = mois_courant + relativedelta(months=1)
        
        # Compter les consommations réelles
        consommations_count = ConsommationAvance.objects.filter(avance=avance).count()
        info['consommations_count'] = consommations_count
        
        # Calculer la progression
        if avance.nombre_mois_couverts > 0:
            info['progression_pourcentage'] = round((consommations_count / avance.nombre_mois_couverts) * 100, 2)
        else:
            info['progression_pourcentage'] = 0
        
        diagnostic_data.append(info)
    
    context = {
        'contrat': contrat,
        'avances': avances,
        'diagnostic_data': diagnostic_data,
        'mois_actuel': mois_actuel.strftime('%d/%m/%Y')
    }
    
    return render(request, 'paiements/avances/diagnostic_avances.html', context)


@login_required
def forcer_consommation_avances_ajax(request, contrat_id):
    """
    Endpoint AJAX pour forcer la consommation des avances d'un contrat
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Méthode non autorisée'}, status=405)
    
    try:
        contrat = get_object_or_404(Contrat, id=contrat_id)
        
        # D'abord corriger les mois_debut_couverture incorrects
        avances = AvanceLoyer.objects.filter(contrat=contrat)
        corrections = []
        
        for avance in avances:
            mois_debut_actuel = avance.mois_debut_couverture
            date_avance = avance.date_avance
            mois_actuel = date.today().replace(day=1)
            
            if mois_debut_actuel:
                mois_avance = date_avance.replace(day=1)
                mois_debut_norm = mois_debut_actuel.replace(day=1)
                
                # Calculer le mois début correct (en excluant cette avance pour éviter les boucles)
                from .services_logique_avance_unique import ServiceLogiqueAvanceUnique
                mois_debut_correct = ServiceLogiqueAvanceUnique.determiner_mois_debut_couverture_nouvelle_avance(
                    contrat, date_avance, avance_a_exclure=avance
                )
                
                # Normaliser les dates pour comparaison
                mois_debut_correct_norm = mois_debut_correct.replace(day=1) if mois_debut_correct else None
                
                # Logique de correction améliorée :
                # 1. Si le mois début actuel est différent du mois début correct
                # 2. ET que l'avance date d'il y a plus d'un mois (donc devrait être consommée)
                # 3. OU que le mois début actuel est dans le futur alors que l'avance est ancienne
                should_correct = False
                if mois_debut_correct_norm and mois_debut_correct_norm != mois_debut_norm:
                    # Cas 1: Avance ancienne (plus d'un mois) avec mois début incorrect
                    if date_avance < date.today() - relativedelta(months=1):
                        should_correct = True
                    # Cas 2: Mois début actuel dans le futur alors que l'avance est ancienne
                    elif mois_debut_norm >= mois_actuel and date_avance < date.today():
                        should_correct = True
                    # Cas 3: Mois début actuel très différent du mois début correct (écart > 2 mois)
                    elif abs((mois_debut_norm.year - mois_debut_correct_norm.year) * 12 + 
                            (mois_debut_norm.month - mois_debut_correct_norm.month)) > 2:
                        should_correct = True
                
                if should_correct:
                    # Corriger le mois début
                    avance.mois_debut_couverture = mois_debut_correct
                    if avance.nombre_mois_couverts > 0:
                        avance.mois_fin_couverture = mois_debut_correct + relativedelta(months=avance.nombre_mois_couverts - 1)
                    avance.save()
                    corrections.append({
                        'id': avance.id,
                        'ancien_mois': mois_debut_actuel.strftime('%d/%m/%Y'),
                        'nouveau_mois': mois_debut_correct.strftime('%d/%m/%Y')
                    })
        
        # Ensuite forcer la consommation automatique
        resultat = ServiceConsommationDynamique.consommer_avances_automatiquement(contrat)
        
        # Récupérer les avances après consommation
        avances = AvanceLoyer.objects.filter(contrat=contrat)
        details_avances = []
        
        for avance in avances:
            consommations_count = ConsommationAvance.objects.filter(avance=avance).count()
            details_avances.append({
                'id': avance.id,
                'statut': avance.statut,
                'montant_restant': float(avance.montant_restant),
                'mois_consommes': consommations_count,
                'mois_couverts': avance.nombre_mois_couverts,
                'progression': round((consommations_count / avance.nombre_mois_couverts * 100) if avance.nombre_mois_couverts > 0 else 0, 2)
            })
        
        message = f'Consommation forcée : {resultat["consommees"]} avance(s) consommée(s)'
        if corrections:
            message += f' | {len(corrections)} mois_debut_couverture corrigé(s)'
        
        return JsonResponse({
            'success': True,
            'message': message,
            'resultat': resultat,
            'corrections': corrections,
            'details_avances': details_avances
        })
        
    except Exception as e:
        import traceback
        return JsonResponse({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc() if settings.DEBUG else None
        }, status=500)
