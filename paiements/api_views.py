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
import re

from .models import Paiement
from .serializers import PaiementSerializer, PaiementDetailSerializer
from contrats.models import Contrat
from proprietes.models import Locataire, Propriete

def clean_numeric_value(value):
    """Nettoie une valeur numérique en supprimant les caractères non numériques"""
    if not value:
        return 0.0
    
    # Convertir en string et nettoyer
    str_value = str(value)
    
    # Supprimer tous les caractères non numériques sauf le point et la virgule
    cleaned = re.sub(r'[^\d.,]', '', str_value)
    
    # Si il y a plusieurs points, garder seulement le dernier
    if cleaned.count('.') > 1:
        parts = cleaned.split('.')
        cleaned = ''.join(parts[:-1]) + '.' + parts[-1]
    
    # Si il y a plusieurs virgules, garder seulement la dernière
    if cleaned.count(',') > 1:
        parts = cleaned.split(',')
        cleaned = ''.join(parts[:-1]) + ',' + parts[-1]
    
    # Remplacer la virgule par un point
    cleaned = cleaned.replace(',', '.')
    
    try:
        return float(cleaned)
    except (ValueError, TypeError):
        return 0.0

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
                'loyer': clean_numeric_value(contrat.loyer_mensuel)
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
                    'loyer_mensuel': clean_numeric_value(contrat_actuel.loyer_mensuel) if contrat_actuel else 0,
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
                    'montant_loyers_bruts': clean_numeric_value(retrait.montant_loyers_bruts),
                    'montant_charges_deductibles': clean_numeric_value(retrait.montant_charges_deductibles),
                    'montant_net_a_payer': clean_numeric_value(retrait.montant_net_a_payer),
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
                    'total_mensuel': clean_numeric_value(total_loyers_bruts),
                    'total_annuel': clean_numeric_value(total_loyers_bruts * 12)
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
                    'moyenne_loyer': clean_numeric_value(total_loyers_bruts / proprietes_louees.count()) if proprietes_louees.count() > 0 else 0
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
            
            # *** CALCUL INTELLIGENT DU PROCHAIN MOIS DE PAIEMENT ***
            # D'abord vérifier s'il y a des avances actives
            try:
                from .services_avance import ServiceGestionAvance
                from .models_avance import AvanceLoyer
                
                # Récupérer les avances actives ET récemment épuisées (qui ont encore un impact)
                from datetime import datetime, timedelta
                from dateutil.relativedelta import relativedelta
                date_limite_avances = datetime.now() - timedelta(days=30)  # Avances des 30 derniers jours
                
                avances_actives = AvanceLoyer.objects.filter(
                    contrat=contrat,
                    statut='active'
                )
                
                # Aussi inclure les avances récemment épuisées qui peuvent encore influencer le prochain paiement
                avances_recentes = AvanceLoyer.objects.filter(
                    contrat=contrat,
                    statut='epuisee',
                    date_avance__gte=date_limite_avances
                )
                
                # Combiner les deux types d'avances
                toutes_les_avances = avances_actives.union(avances_recentes)
                
                # *** CALCULER LE PROCHAIN MOIS (avec ou sans avances) ***
                # CORRIGÉ : Utiliser toujours la méthode calculer_prochain_mois_paiement() qui prend en compte mois_paye
                prochain_mois_paiement_avec_avances = None
                try:
                    # Utiliser la méthode corrigée qui prend en compte mois_paye et les avances
                    prochain_mois_paiement_avec_avances = ServiceGestionAvance.calculer_prochain_mois_paiement(contrat)
                    prochain_mois = prochain_mois_paiement_avec_avances.month
                    
                    if toutes_les_avances.exists():
                        mois_suggere = f"Prochain paiement avec avances: {prochain_mois_paiement_avec_avances.strftime('%B %Y')}"
                    else:
                        mois_suggere = f"Prochain paiement: {prochain_mois_paiement_avec_avances.strftime('%B %Y')}"
                        
                except Exception as e:
                    print(f"Erreur calcul prochain mois: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    # Fallback : utiliser le mois actuel
                    from datetime import datetime
                    prochain_mois = datetime.now().month
                    mois_suggere = "Mois actuel"
                    prochain_mois_paiement_avec_avances = None
                            
            except Exception as e:
                # En cas d'erreur, utiliser le mois actuel
                print(f"Erreur dans le calcul du prochain mois: {str(e)}")
                import traceback
                traceback.print_exc()
                from datetime import datetime
                prochain_mois = datetime.now().month
                mois_suggere = "Mois actuel"
                prochain_mois_paiement_avec_avances = None
            
            # *** RÉCUPÉRATION DES INFORMATIONS SUR LES AVANCES ***
            try:
                # Récupérer les avances actives (seulement celles qui ont encore du montant restant)
                avances_actives = AvanceLoyer.objects.filter(
                    contrat=contrat,
                    statut='active',
                    montant_restant__gt=0  # Seulement les avances qui ont encore de l'argent
                )
                
                # Calculer le montant total des avances disponibles
                montant_avances_disponible = sum(avance.montant_restant for avance in avances_actives)
                
                # Calculer le nombre de mois couverts par les avances
                mois_couverts_par_avances = sum(avance.nombre_mois_couverts for avance in avances_actives)
                
                # *** MONITORING DES AVANCES - DÉTECTION AUTOMATIQUE DE LA PROGRESSION ***
                from .services_monitoring_avance import ServiceMonitoringAvance
                
                # Analyser la progression des avances
                progression_avances = ServiceMonitoringAvance.analyser_progression_avances(contrat)
                
                # Détecter les avances à consommer automatiquement
                avances_a_consommer = ServiceMonitoringAvance.detecter_avances_a_consommer(contrat)
                
                # Consommer automatiquement les avances manquantes
                if avances_a_consommer.get('total_mois_a_consommer', 0) > 0:
                    consommation_auto = ServiceMonitoringAvance.consommer_avances_manquantes(contrat)
                    if consommation_auto.get('success'):
                        print(f"Consommation automatique: {consommation_auto['message']}")
                        # Recharger les avances après consommation
                        avances_actives = AvanceLoyer.objects.filter(
                            contrat=contrat,
                            statut='active'
                        )
                        montant_avances_disponible = sum(avance.montant_restant for avance in avances_actives)
                        mois_couverts_par_avances = sum(avance.nombre_mois_couverts for avance in avances_actives)
                
                # Calculer le prochain mois de paiement en tenant compte des avances
                prochain_mois_paiement = ServiceGestionAvance.calculer_prochain_mois_paiement(contrat)
                montant_du_mois_prochain, montant_avance_utilisee = ServiceGestionAvance.calculer_montant_du_mois(
                    contrat, prochain_mois_paiement
                )
                
                # Calculer la date d'expiration des avances
                date_expiration_avances = ServiceGestionAvance.calculer_date_expiration_avances(contrat)
                
            except Exception as e:
                # En cas d'erreur, ne pas prendre en compte les avances
                montant_avances_disponible = 0
                mois_couverts_par_avances = 0
                prochain_mois_paiement = date.today().replace(day=1) + relativedelta(months=1)
                montant_du_mois_prochain = clean_numeric_value(contrat.loyer_mensuel)
                montant_avance_utilisee = 0
                date_expiration_avances = None
            
            contexte = {
                'contrat': {
                    'id': contrat.id,  # Ajout de l'ID pour les boutons PDF
                    'numero': contrat.numero_contrat,
                    'numero_contrat': contrat.numero_contrat,  # Alias pour compatibilité
                    'date_debut': contrat.date_debut.strftime('%d/%m/%Y') if contrat.date_debut else None,
                    'date_fin': contrat.date_fin.strftime('%d/%m/%Y') if contrat.date_fin else None,
                    'montant_loyer': clean_numeric_value(contrat.loyer_mensuel),
                    'charges': clean_numeric_value(contrat.charges_mensuelles)
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
                        'montant': clean_numeric_value(p.montant),
                        'type': p.get_type_paiement_display(),
                        'statut': p.get_statut_display(),
                        'mois_description': p.get_mois_description(),
                        'mois_paye': p.mois_paye or ''
                    } for p in paiements_recents
                ],
                # *** AJOUT DES AVANCES DANS L'HISTORIQUE ***
                'avances_recents': [
                    {
                        'date': avance.date_avance.strftime('%d/%m/%Y'),
                        'montant': clean_numeric_value(avance.montant_avance),
                        'type': 'Avance de loyer',
                        'statut': 'Active' if avance.statut == 'active' else 'Épuisée',
                        'mois_couverts': avance.nombre_mois_couverts,
                        'montant_restant': clean_numeric_value(avance.montant_restant)
                    } for avance in avances_actives
                ],
                'prochain_mois_paiement': prochain_mois,
                'prochain_mois_paiement_avec_avances': _convertir_mois_francais_api(prochain_mois_paiement_avec_avances.strftime('%B %Y')) if 'prochain_mois_paiement_avec_avances' in locals() and prochain_mois_paiement_avec_avances else None,
                'date_expiration_avances': date_expiration_avances.strftime('%d/%m/%Y') if date_expiration_avances else None,
                'mois_suggere': mois_suggere,
                'total_charges': clean_numeric_value(contrat.charges_mensuelles),
                'net_a_payer': clean_numeric_value(contrat.loyer_mensuel),
                'est_premier_paiement': len(paiements_recents) == 0,
                # *** INFORMATIONS SUR LES AVANCES ***
                'montant_avances_disponible': clean_numeric_value(montant_avances_disponible),
                'mois_couverts_par_avances': mois_couverts_par_avances,
                'montant_du_mois_prochain': clean_numeric_value(montant_du_mois_prochain),
                'montant_avance_utilisee': clean_numeric_value(montant_avance_utilisee),
                'avances_actives': avances_actives.count() if 'avances_actives' in locals() else 0,
                'progression_avances': progression_avances if 'progression_avances' in locals() else {},
                'avances_a_consommer': avances_a_consommer if 'avances_a_consommer' in locals() else {}
            }
            
            return JsonResponse(contexte)
            
        except Contrat.DoesNotExist:
            return JsonResponse({'error': 'Contrat non trouvé'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)


# 🚀 API POUR CRÉER UNE AVANCE RAPIDEMENT
@csrf_exempt
def api_creer_avance_rapide(request):
    """API pour créer une avance rapidement depuis le formulaire de paiement"""
    if request.method == 'POST':
        try:
            from .services_avance import ServiceGestionAvance
            from .models_avance import AvanceLoyer
            from contrats.models import Contrat
            from decimal import Decimal
            
            contrat_id = request.POST.get('contrat_id')
            montant_avance = request.POST.get('montant_avance')
            notes = request.POST.get('notes', '')
            
            if not contrat_id or not montant_avance:
                return JsonResponse({'success': False, 'error': 'Paramètres manquants'})
            
            # Récupérer le contrat
            contrat = Contrat.objects.get(pk=contrat_id, is_deleted=False)
            
            # Créer l'avance
            avance = ServiceGestionAvance.creer_avance_loyer(
                contrat=contrat,
                montant_avance=Decimal(montant_avance),
                date_avance=timezone.now().date(),
                notes=notes
            )
            
            return JsonResponse({
                'success': True,
                'avance_id': avance.id,
                'mois_couverts': avance.nombre_mois_couverts,
                'montant_restant': float(avance.montant_restant),
                'statut': avance.statut
            })
            
        except Contrat.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Contrat non trouvé'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Méthode non autorisée'}, status=405)

@csrf_exempt
def api_convertir_avances_existantes(request):
    """API pour convertir tous les paiements d'avance d'un contrat en AvanceLoyer actifs"""
    if request.method == 'POST':
        try:
            from .services_avance import ServiceGestionAvance
            from .models_avance import AvanceLoyer
            from contrats.models import Contrat
            from decimal import Decimal
            
            contrat_id = request.POST.get('contrat_id')
            
            if not contrat_id:
                return JsonResponse({'success': False, 'error': 'ID du contrat manquant'})
            
            contrat = Contrat.objects.get(pk=contrat_id, is_deleted=False)
            
            # Trouver tous les paiements d'avance de ce contrat
            paiements_avance = Paiement.objects.filter(
                contrat=contrat,
                type_paiement='avance',
                statut='valide'
            )
            
            avances_creees = 0
            erreurs = []
            
            for paiement in paiements_avance:
                # Vérifier si un AvanceLoyer existe déjà pour ce paiement
                avance_existant = AvanceLoyer.objects.filter(
                    contrat=paiement.contrat,
                    montant_avance=paiement.montant,
                    date_avance=paiement.date_paiement
                ).first()
                
                if not avance_existant:
                    # Créer l'AvanceLoyer manquant
                    try:
                        avance = ServiceGestionAvance.creer_avance_loyer(
                            contrat=paiement.contrat,
                            montant_avance=Decimal(str(paiement.montant)),
                            date_avance=paiement.date_paiement,
                            notes=f"Converti depuis paiement {paiement.id}"
                        )
                        # S'assurer que l'avance est active
                        avance.statut = 'active'
                        avance.save()
                        avances_creees += 1
                        print(f"OK - Avance creee pour paiement {paiement.id} (contrat {contrat_id})")
                    except Exception as e:
                        erreur_msg = f"Erreur creation AvanceLoyer pour paiement {paiement.id}: {str(e)}"
                        print(erreur_msg)
                        erreurs.append(erreur_msg)
                        continue
                else:
                    print(f"IGNORE - Avance existe deja pour paiement {paiement.id} (contrat {contrat_id})")
            
            # Si aucune avance n'a été créée pour ce contrat, vérifier s'il y a des contrats avec des avances manquantes
            if avances_creees == 0:
                print(f"VERIFICATION - Aucune avance creee pour le contrat {contrat_id}, verification globale...")
                
                # Vérifier tous les contrats qui ont des paiements d'avance sans AvanceLoyer
                contrats_avec_avances_manquantes = Contrat.objects.filter(
                    paiements__type_paiement__in=['avance_loyer', 'avance'],
                    paiements__statut='valide'
                ).distinct()
                
                total_avances_manquantes = 0
                for contrat_verif in contrats_avec_avances_manquantes:
                    paiements_verif = Paiement.objects.filter(
                        contrat=contrat_verif,
                        type_paiement='avance',
                        statut='valide'
                    )
                    
                    for paiement_verif in paiements_verif:
                        avance_existante_verif = AvanceLoyer.objects.filter(
                            contrat=paiement_verif.contrat,
                            montant_avance=paiement_verif.montant,
                            date_avance=paiement_verif.date_paiement
                        ).first()
                        
                        if not avance_existante_verif:
                            total_avances_manquantes += 1
                            print(f"ATTENTION - Contrat {contrat_verif.id}: Paiement {paiement_verif.id} sans AvanceLoyer")
                
                if total_avances_manquantes > 0:
                    message = f"Aucune avance créée pour ce contrat, mais {total_avances_manquantes} avances manquantes détectées dans d'autres contrats. Utilisez la conversion globale."
                else:
                    message = "Toutes les avances sont déjà converties."
            else:
                message = f'{avances_creees} avances créées avec succès'
            
            return JsonResponse({
                'success': True,
                'avances_creees': avances_creees,
                'message': message,
                'erreurs': erreurs
            })
            
        except Contrat.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Contrat non trouvé'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Méthode non autorisée'}, status=405)

@csrf_exempt
def api_convertir_toutes_avances_existantes(request):
    """API pour convertir TOUS les paiements d'avance de TOUS les contrats en AvanceLoyer actifs"""
    if request.method == 'POST':
        try:
            from .services_avance import ServiceGestionAvance
            from .models_avance import AvanceLoyer
            from contrats.models import Contrat
            from decimal import Decimal
            
            # Trouver tous les contrats qui ont des paiements d'avance
            # Récupérer d'abord tous les paiements d'avance, puis les contrats uniques
            paiements_avance = Paiement.objects.filter(
                type_paiement='avance',
                statut='valide'
            )
            
            # Récupérer les contrats uniques
            contrats_ids = set(p.contrat_id for p in paiements_avance)
            contrats_avec_avances = Contrat.objects.filter(id__in=contrats_ids)
            
            total_avances_creees = 0
            total_erreurs = []
            contrats_traites = []
            
            for contrat in contrats_avec_avances:
                print(f"Traitement du contrat {contrat.id}...")
                contrats_traites.append(contrat.id)
                
                # Trouver tous les paiements d'avance de ce contrat
                paiements_avance = Paiement.objects.filter(
                    contrat=contrat,
                    type_paiement='avance',
                    statut='valide'
                )
                
                avances_creees_contrat = 0
                
                for paiement in paiements_avance:
                    # Vérifier si un AvanceLoyer existe déjà pour ce paiement
                    avance_existant = AvanceLoyer.objects.filter(
                        contrat=paiement.contrat,
                        montant_avance=paiement.montant,
                        date_avance=paiement.date_paiement
                    ).first()
                    
                    if not avance_existant:
                        # Créer l'AvanceLoyer manquant
                        try:
                            avance = ServiceGestionAvance.creer_avance_loyer(
                                contrat=paiement.contrat,
                                montant_avance=Decimal(str(paiement.montant)),
                                date_avance=paiement.date_paiement,
                                notes=f"Converti depuis paiement {paiement.id}"
                            )
                            # S'assurer que l'avance est active
                            avance.statut = 'active'
                            avance.save()
                            avances_creees_contrat += 1
                            print(f"OK - Avance creee pour paiement {paiement.id} (contrat {contrat.id})")
                        except Exception as e:
                            erreur_msg = f"Contrat {contrat.id}, Paiement {paiement.id}: {str(e)}"
                            print(f"ERREUR - {erreur_msg}")
                            total_erreurs.append(erreur_msg)
                            continue
                    else:
                        print(f"IGNORE - Avance existe deja pour paiement {paiement.id} (contrat {contrat.id})")
                
                total_avances_creees += avances_creees_contrat
                print(f"RESULTAT Contrat {contrat.id}: {avances_creees_contrat} avances creees")
            
            print(f"RESULTAT FINAL: {total_avances_creees} avances creees au total")
            
            return JsonResponse({
                'success': True,
                'avances_creees': total_avances_creees,
                'contrats_traites': len(contrats_traites),
                'message': f'Conversion globale terminée: {total_avances_creees} avances créées pour {len(contrats_traites)} contrats',
                'erreurs': total_erreurs
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Méthode non autorisée'}, status=405)


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
        'notes',
        'libelle'
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
        paiement.notes = f"{paiement.notes}\n\nRefusé: {motif_refus}".strip()
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
        type_paiement__in=['caution', 'avance']
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
        'notes',
        'libelle'
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
                queryset = queryset.filter(type_paiement__in=['caution', 'avance'])
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
        # Vérification des permissions
        from core.utils import check_group_permissions
        permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE', 'CAISSE'], 'change')
        if not permissions['allowed']:
            return Response(
                {'error': f'Permissions insuffisantes. {permissions["message"]}'},
                status=status.HTTP_403_FORBIDDEN
            )
        
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
        elif paiement.type_paiement == 'avance':
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
            # Convertir les paramètres en entiers
            mois_int = int(mois)
            annee_int = int(annee)
            
            # Valider que le mois est entre 1 et 12
            if mois_int < 1 or mois_int > 12:
                return JsonResponse({
                    'doublon_existe': False,
                    'erreur': 'Mois invalide (doit être entre 1 et 12)'
                })
            
            # Formater le nom du mois pour construire la chaîne de recherche
            mois_noms = [
                'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
                'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'
            ]
            mois_nom = mois_noms[mois_int - 1]
            
            # Construire la chaîne attendue au format "Mois Année"
            mois_paye_attendu = f"{mois_nom} {annee_int}"
            
            # Vérifier s'il existe un paiement pour ce contrat dans ce mois
            # Le champ mois_paye est un CharField, donc on fait une recherche exacte
            existing_payment = Paiement.objects.filter(
                contrat_id=contrat_id,
                mois_paye=mois_paye_attendu,
                is_deleted=False
            ).first()
            
            if existing_payment:
                return JsonResponse({
                    'doublon_existe': True,
                    'mois_nom': f"{mois_nom} {annee_int}",
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
                
        except (ValueError, TypeError) as e:
            return JsonResponse({
                'doublon_existe': False,
                'erreur': f'Paramètres invalides: {str(e)}'
            })
        except Contrat.DoesNotExist:
            return JsonResponse({
                'doublon_existe': False,
                'erreur': 'Contrat introuvable'
            })
        except Exception as e:
            return JsonResponse({
                'doublon_existe': False,
                'erreur': f'Erreur lors de la vérification: {str(e)}'
            })
    
    return JsonResponse({
        'doublon_existe': False,
        'erreur': 'Méthode non autorisée'
    })

def _convertir_mois_francais_api(mois_anglais):
    """Convertit les mois anglais en français pour l'API"""
    if not mois_anglais:
        return mois_anglais
        
    mois_francais = {
        'January': 'Janvier',
        'February': 'Février', 
        'March': 'Mars',
        'April': 'Avril',
        'May': 'Mai',
        'June': 'Juin',
        'July': 'Juillet',
        'August': 'Août',
        'September': 'Septembre',
        'October': 'Octobre',
        'November': 'Novembre',
        'December': 'Décembre'
    }
    
    # Remplacer tous les mois anglais par les mois français
    resultat = mois_anglais
    for mois_en, mois_fr in mois_francais.items():
        resultat = resultat.replace(mois_en, mois_fr)
    
    return resultat
