"""
Vue pour corriger les avances mal configurées depuis l'interface web
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Count
from paiements.models_avance import AvanceLoyer
from contrats.models import Contrat
from decimal import Decimal
from dateutil.relativedelta import relativedelta
import json


@login_required
def page_correction_avances(request):
    """Page d'administration pour corriger les avances"""
    try:
        # Récupérer tous les contrats actifs
        contrats = Contrat.objects.filter(
            is_deleted=False
        ).select_related('locataire', 'propriete').order_by('-date_debut')[:100]  # Limiter à 100
        
        return render(request, 'paiements/admin/corriger_avances.html', {
            'contrats': contrats
        })
    except Exception as e:
        # En cas d'erreur, afficher une page simple
        return render(request, 'paiements/admin/corriger_avances.html', {
            'contrats': [],
            'error': str(e)
        })


@login_required
@require_http_methods(["GET"])
def api_diagnostic_avances(request):
    """API pour diagnostiquer les avances problématiques"""
    try:
        avances = AvanceLoyer.objects.filter(
            statut='active',
            montant_restant__gt=0
        ).select_related('contrat')
        
        problemes = []
        
        for avance in avances:
            try:
                # Récupérer le loyer du contrat
                loyer_contrat = avance.contrat.get_loyer_total()
                if isinstance(loyer_contrat, str):
                    loyer_contrat = Decimal(loyer_contrat.replace(',', '').replace(' ', ''))
                else:
                    loyer_contrat = Decimal(str(loyer_contrat))
                
                # Calculer le nombre de mois selon le loyer du contrat
                mois_calcules_contrat = int(avance.montant_avance // loyer_contrat) if loyer_contrat > 0 else 0
                mois_enregistres = avance.nombre_mois_couverts
                
                # Vérifier s'il y a une incohérence
                difference_loyer = abs(avance.loyer_mensuel - loyer_contrat)
                
                if difference_loyer > 100 or mois_calcules_contrat != mois_enregistres:
                    problemes.append({
                        'id': avance.id,
                        'contrat': str(avance.contrat),
                        'contrat_id': avance.contrat.id,
                        'date_avance': avance.date_avance.strftime('%d/%m/%Y'),
                        'montant_avance': float(avance.montant_avance),
                        'loyer_avance': float(avance.loyer_mensuel),
                        'loyer_contrat': float(loyer_contrat),
                        'difference_loyer': float(difference_loyer),
                        'mois_enregistres': mois_enregistres,
                        'mois_calcules': mois_calcules_contrat,
                        'mois_debut': avance.mois_debut_couverture.strftime('%B %Y'),
                        'mois_fin': avance.mois_fin_couverture.strftime('%B %Y'),
                        'montant_restant': float(avance.montant_restant),
                        'correction_suggeree': {
                            'nouveau_loyer': float(loyer_contrat),
                            'nouveau_nombre_mois': mois_calcules_contrat,
                            'nouvelle_fin': (avance.mois_debut_couverture + relativedelta(months=mois_calcules_contrat - 1)).strftime('%B %Y') if mois_calcules_contrat > 0 else avance.mois_debut_couverture.strftime('%B %Y')
                        }
                    })
            except Exception as e:
                continue
        
        return JsonResponse({
            'success': True,
            'total_avances': avances.count(),
            'problemes_trouves': len(problemes),
            'avances_problematiques': problemes
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
def api_corriger_avance(request):
    """API pour corriger une avance spécifique"""
    try:
        data = json.loads(request.body)
        avance_id = data.get('avance_id')
        
        avance = AvanceLoyer.objects.get(id=avance_id)
        
        # Récupérer le loyer du contrat
        loyer_contrat = avance.contrat.get_loyer_total()
        if isinstance(loyer_contrat, str):
            loyer_contrat = Decimal(loyer_contrat.replace(',', '').replace(' ', ''))
        else:
            loyer_contrat = Decimal(str(loyer_contrat))
        
        # Calculer le nouveau nombre de mois
        nouveau_nombre_mois = int(avance.montant_avance // loyer_contrat) if loyer_contrat > 0 else 0
        
        # Sauvegarder les anciennes valeurs
        ancien_loyer = avance.loyer_mensuel
        ancien_nombre_mois = avance.nombre_mois_couverts
        ancienne_fin = avance.mois_fin_couverture
        
        # Appliquer la correction
        avance.loyer_mensuel = loyer_contrat
        avance.nombre_mois_couverts = nouveau_nombre_mois
        
        # Recalculer la fin de couverture
        if nouveau_nombre_mois > 0:
            avance.mois_fin_couverture = avance.mois_debut_couverture + relativedelta(months=nouveau_nombre_mois - 1)
        else:
            avance.mois_fin_couverture = avance.mois_debut_couverture
        
        avance.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Avance corrigée avec succès',
            'avance_id': avance.id,
            'changements': {
                'loyer': {
                    'avant': float(ancien_loyer),
                    'apres': float(avance.loyer_mensuel)
                },
                'mois': {
                    'avant': ancien_nombre_mois,
                    'apres': avance.nombre_mois_couverts
                },
                'fin_couverture': {
                    'avant': ancienne_fin.strftime('%B %Y'),
                    'apres': avance.mois_fin_couverture.strftime('%B %Y')
                }
            }
        })
    
    except AvanceLoyer.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Avance non trouvée'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
def api_corriger_toutes_avances(request):
    """API pour corriger toutes les avances problématiques d'un coup"""
    try:
        avances = AvanceLoyer.objects.filter(
            statut='active',
            montant_restant__gt=0
        ).select_related('contrat')
        
        corrections_appliquees = 0
        erreurs = []
        
        for avance in avances:
            try:
                # Récupérer le loyer du contrat
                loyer_contrat = avance.contrat.get_loyer_total()
                if isinstance(loyer_contrat, str):
                    loyer_contrat = Decimal(loyer_contrat.replace(',', '').replace(' ', ''))
                else:
                    loyer_contrat = Decimal(str(loyer_contrat))
                
                # Calculer le nombre de mois selon le loyer du contrat
                mois_calcules_contrat = int(avance.montant_avance // loyer_contrat) if loyer_contrat > 0 else 0
                
                # Vérifier s'il y a une incohérence
                difference_loyer = abs(avance.loyer_mensuel - loyer_contrat)
                
                if difference_loyer > 100 or mois_calcules_contrat != avance.nombre_mois_couverts:
                    # Appliquer la correction
                    avance.loyer_mensuel = loyer_contrat
                    avance.nombre_mois_couverts = mois_calcules_contrat
                    
                    # Recalculer la fin de couverture
                    if mois_calcules_contrat > 0:
                        avance.mois_fin_couverture = avance.mois_debut_couverture + relativedelta(months=mois_calcules_contrat - 1)
                    else:
                        avance.mois_fin_couverture = avance.mois_debut_couverture
                    
                    avance.save()
                    corrections_appliquees += 1
            except Exception as e:
                erreurs.append({
                    'avance_id': avance.id,
                    'erreur': str(e)
                })
        
        return JsonResponse({
            'success': True,
            'total_avances': avances.count(),
            'corrections_appliquees': corrections_appliquees,
            'erreurs': erreurs
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["GET"])
def api_diagnostic_contrat(request, contrat_id):
    """API pour diagnostiquer les avances d'un contrat spécifique"""
    try:
        contrat = Contrat.objects.get(pk=contrat_id, is_deleted=False)
        loyer_contrat = Decimal(str(contrat.get_loyer_total()))
        
        avances = AvanceLoyer.objects.filter(contrat=contrat).order_by('-date_avance')
        
        # Détecter les doublons
        doublons_groups = AvanceLoyer.objects.filter(
            contrat=contrat
        ).values('date_avance', 'montant_avance').annotate(
            count=Count('id')
        ).filter(count__gt=1)
        
        avances_data = []
        doublons_ids = []
        problemes = []
        
        for avance in avances:
            mois_calcules = int(avance.montant_avance // loyer_contrat) if loyer_contrat > 0 else 0
            loyer_incorrect = abs(avance.loyer_mensuel - loyer_contrat) > 100
            mois_incorrects = mois_calcules != avance.nombre_mois_couverts
            
            avance_data = {
                'id': avance.id,
                'date_avance': str(avance.date_avance),
                'montant': float(avance.montant_avance),
                'loyer_mensuel': float(avance.loyer_mensuel),
                'mois_couverts': avance.nombre_mois_couverts,
                'mois_debut': str(avance.mois_debut_couverture),
                'mois_fin': str(avance.mois_fin_couverture),
                'montant_restant': float(avance.montant_restant),
                'statut': avance.statut,
                'loyer_incorrect': loyer_incorrect,
                'mois_incorrects': mois_incorrects,
                'mois_corriges': mois_calcules
            }
            avances_data.append(avance_data)
            
            if loyer_incorrect or mois_incorrects:
                problemes.append(avance.id)
        
        # Identifier les doublons
        for groupe in doublons_groups:
            avances_dup = AvanceLoyer.objects.filter(
                contrat=contrat,
                date_avance=groupe['date_avance'],
                montant_avance=groupe['montant_avance']
            ).order_by('id')
            # Garder le premier, marquer les autres comme doublons
            for avance in avances_dup.exclude(id=avances_dup.first().id):
                doublons_ids.append(avance.id)
        
        return JsonResponse({
            'success': True,
            'contrat': {
                'id': contrat.id,
                'numero': contrat.numero_contrat,
                'locataire': str(contrat.locataire),
                'loyer_mensuel': float(loyer_contrat)
            },
            'avances': avances_data,
            'doublons_ids': doublons_ids,
            'problemes_ids': problemes,
            'total_avances': len(avances_data),
            'total_doublons': len(doublons_ids),
            'total_problemes': len(problemes)
        })
    
    except Contrat.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Contrat introuvable'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def api_corriger_contrat(request, contrat_id):
    """API pour corriger toutes les avances d'un contrat"""
    try:
        contrat = Contrat.objects.get(pk=contrat_id, is_deleted=False)
        loyer_contrat = Decimal(str(contrat.get_loyer_total()))
        
        # 1. Supprimer les doublons
        doublons_groups = AvanceLoyer.objects.filter(
            contrat=contrat
        ).values('date_avance', 'montant_avance').annotate(
            count=Count('id')
        ).filter(count__gt=1)
        
        doublons_supprimes = 0
        for groupe in doublons_groups:
            avances_dup = AvanceLoyer.objects.filter(
                contrat=contrat,
                date_avance=groupe['date_avance'],
                montant_avance=groupe['montant_avance']
            ).order_by('id')
            # Supprimer tous sauf le premier
            count = avances_dup.exclude(id=avances_dup.first().id).count()
            avances_dup.exclude(id=avances_dup.first().id).delete()
            doublons_supprimes += count
        
        # 2. Corriger les avances mal configurées
        avances = AvanceLoyer.objects.filter(contrat=contrat)
        avances_corrigees = 0
        
        for avance in avances:
            mois_calcules = int(avance.montant_avance // loyer_contrat) if loyer_contrat > 0 else 0
            loyer_incorrect = abs(avance.loyer_mensuel - loyer_contrat) > 100
            mois_incorrects = mois_calcules != avance.nombre_mois_couverts
            
            if loyer_incorrect or mois_incorrects:
                avance.loyer_mensuel = loyer_contrat
                avance.nombre_mois_couverts = mois_calcules
                
                if mois_calcules > 0:
                    avance.mois_fin_couverture = avance.mois_debut_couverture + relativedelta(months=mois_calcules - 1)
                else:
                    avance.mois_fin_couverture = avance.mois_debut_couverture
                
                avance.save()
                avances_corrigees += 1
        
        return JsonResponse({
            'success': True,
            'doublons_supprimes': doublons_supprimes,
            'avances_corrigees': avances_corrigees,
            'message': f'{doublons_supprimes} doublon(s) supprimé(s), {avances_corrigees} avance(s) corrigée(s)'
        })
    
    except Contrat.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Contrat introuvable'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def api_corriger_mois_couverture(request):
    """Corrige le mois_debut_couverture des avances créées avec la mauvaise logique.
    Utilise ServiceLogiqueAvanceUnique pour recalculer le bon mois de début.
    Traite les avances par ordre chronologique pour éviter les effets de cascade.
    """
    try:
        from paiements.services_logique_avance_unique import ServiceLogiqueAvanceUnique

        avances = AvanceLoyer.objects.filter(
            statut='active'
        ).select_related('contrat').order_by('contrat_id', 'date_avance')

        corrections = []
        erreurs = []

        for avance in avances:
            try:
                # Calculer le mois attendu en excluant cette avance du calcul
                mois_debut_attendu = ServiceLogiqueAvanceUnique.determiner_mois_debut_couverture_nouvelle_avance(
                    avance.contrat,
                    date_avance=avance.date_avance,
                    avance_a_exclure=avance
                )

                mois_debut_actuel = avance.mois_debut_couverture

                if mois_debut_attendu != mois_debut_actuel:
                    ancien_debut = mois_debut_actuel
                    ancienne_fin = avance.mois_fin_couverture

                    nombre_mois = avance.nombre_mois_couverts
                    if nombre_mois > 0:
                        nouvelle_fin = mois_debut_attendu + relativedelta(months=nombre_mois - 1)
                    else:
                        nouvelle_fin = mois_debut_attendu

                    avance.mois_debut_couverture = mois_debut_attendu
                    avance.mois_fin_couverture = nouvelle_fin
                    avance.save()

                    corrections.append({
                        'avance_id': avance.id,
                        'contrat': str(avance.contrat),
                        'contrat_id': avance.contrat.id,
                        'ancien_debut': ancien_debut.strftime('%B %Y'),
                        'nouveau_debut': mois_debut_attendu.strftime('%B %Y'),
                        'ancienne_fin': ancienne_fin.strftime('%B %Y') if ancienne_fin else None,
                        'nouvelle_fin': nouvelle_fin.strftime('%B %Y'),
                    })
            except Exception as e:
                erreurs.append({'avance_id': avance.id, 'erreur': str(e)})

        return JsonResponse({
            'success': True,
            'total_avances_analysees': avances.count(),
            'corrections_appliquees': len(corrections),
            'corrections': corrections,
            'erreurs': erreurs
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
