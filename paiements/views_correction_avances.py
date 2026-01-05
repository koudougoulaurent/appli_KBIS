"""
Vue pour corriger les avances mal configurées depuis l'interface web
"""
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from paiements.models_avance import AvanceLoyer
from decimal import Decimal
from dateutil.relativedelta import relativedelta
import json


@staff_member_required
def page_correction_avances(request):
    """Page d'administration pour corriger les avances"""
    return render(request, 'paiements/admin/corriger_avances.html')


@staff_member_required
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


@staff_member_required
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


@staff_member_required
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
