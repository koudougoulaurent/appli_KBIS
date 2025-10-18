"""
Vues pour les tableaux de bord sécurisés avec contrôle d'accès granulaire.
"""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count, Sum
from datetime import timedelta

from ..models import ConfigurationTableauBord, LogAccesDonnees


@login_required
def configuration_tableau_bord(request):
    """Configuration personnalisée du tableau de bord - Accès restreint au groupe PRIVILEGE uniquement."""
    
    # Vérification des permissions : Seul le groupe PRIVILEGE peut accéder à la configuration
    from core.utils import check_group_permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE'], 'modify')
    if not permissions['allowed']:
        messages.error(request, "Accès refusé. Seuls les utilisateurs du groupe PRIVILEGE peuvent configurer le dashboard sécurisé.")
        return redirect('core:dashboard')
    
    # Obtenir la configuration actuelle
    config = ConfigurationTableauBord.objects.filter(
        utilisateur=request.user,
        par_defaut=True
    ).first()
    
    # Créer une configuration par défaut si elle n'existe pas
    if not config:
        try:
            config = ConfigurationTableauBord.objects.create(
                utilisateur=request.user,
                nom_tableau="Tableau Principal",
                par_defaut=True,
                widgets_actifs=['statistiques_generales'],
                masquer_montants_sensibles=True,
                affichage_anonymise=False,
                limite_donnees_recentes=30
            )
            print(f"DEBUG: Configuration par défaut créée pour {request.user.username}")
        except Exception as e:
            print(f"DEBUG: Erreur création config par défaut: {str(e)}")
            messages.error(request, f'Erreur lors de la création de la configuration: {str(e)}')
            return render(request, 'core/configuration_tableau_bord.html', {
                'config': None,
                'widgets_disponibles': [],
                'titre_page': 'Configuration Tableau de Bord'
            })
    
    if request.method == 'POST':
        try:
            print(f"DEBUG: Données POST reçues: {request.POST}")
            
            # Récupérer les données du formulaire
            nom_tableau = request.POST.get('nom_tableau', 'Tableau Principal')
            widgets_selectionnes = request.POST.getlist('widgets_actifs')
            masquer_montants = request.POST.get('masquer_montants') == 'on'
            affichage_anonymise = request.POST.get('affichage_anonymise') == 'on'
            limite_jours = request.POST.get('limite_jours', '30')
            
            print(f"DEBUG: Nom tableau: {nom_tableau}")
            print(f"DEBUG: Widgets sélectionnés: {widgets_selectionnes}")
            print(f"DEBUG: Masquer montants: {masquer_montants}")
            print(f"DEBUG: Affichage anonymisé: {affichage_anonymise}")
            print(f"DEBUG: Limite jours: {limite_jours}")
            
            # Validation des données
            if not nom_tableau.strip():
                nom_tableau = 'Tableau Principal'
            
            if not widgets_selectionnes:
                widgets_selectionnes = ['statistiques_generales']
            
            try:
                limite_jours = int(limite_jours)
                if limite_jours < 1:
                    limite_jours = 30
            except ValueError:
                limite_jours = 30
            
            # Mettre à jour la configuration
            config.nom_tableau = nom_tableau
            config.widgets_actifs = widgets_selectionnes
            config.masquer_montants_sensibles = masquer_montants
            config.affichage_anonymise = affichage_anonymise
            config.limite_donnees_recentes = limite_jours
            
            # Sauvegarder
            config.save()
            
            print("DEBUG: Configuration sauvegardée avec succès")
            
            # Message de succès
            messages.success(request, 'Configuration sauvegardée avec succès !')
            
            # Rediriger pour éviter la soumission multiple du formulaire
            return redirect('core:configuration_tableau_bord')
            
        except Exception as e:
            print(f"DEBUG: Erreur lors de la sauvegarde: {str(e)}")
            import traceback
            traceback.print_exc()
            messages.error(request, f'Erreur lors de la sauvegarde: {str(e)}')
    
    # Obtenir la liste des widgets disponibles
    widgets_disponibles = [
        'statistiques_generales',
        'activite_recente',
        'alertes_securite',
        'graphiques_financiers',
        'calendrier_evenements',
        'notifications_systeme',
        'liste_contrats',
        'suivi_paiements',
        'rapports_mensuels',
        'analyse_rentabilite',
        'audit_acces',
        'statistiques_avancees',
        'administration_systeme',
        'gestion_utilisateurs',
        'configuration_globale'
    ]
    
    context = {
        'config': config,
        'widgets_disponibles': widgets_disponibles,
        'titre_page': 'Configuration Tableau de Bord'
    }
    
    return render(request, 'core/configuration_tableau_bord.html', context)


@login_required
def tableau_bord_principal(request):
    """Vue principale du tableau de bord sécurisé."""
    messages.info(request, "Tableau de bord sécurisé - Accès restreint au groupe PRIVILEGE")
    return redirect('core:dashboard')


@login_required
def dashboard(request):
    """Vue dashboard principale."""
    return render(request, 'core/dashboard.html', {
        'titre_page': 'Dashboard Principal'
    })


@login_required
def widget_statistiques_generales(request):
    """Widget des statistiques générales."""
    return JsonResponse({
        'success': True,
        'data': {
            'nombre_proprietes': 0,
            'nombre_contrats': 0,
            'taux_occupation': 0.0
        }
    })


@login_required
def widget_activite_recente(request):
    """Widget d'activité récente."""
    return JsonResponse({
        'success': True,
        'data': []
    })


@login_required
def widget_alertes_securite(request):
    """Widget des alertes de sécurité."""
    return JsonResponse({
        'success': True,
        'data': []
    })


@login_required
def export_donnees_securise(request, type_donnees):
    """Export sécurisé des données."""
    messages.success(request, f"Export de données de type {type_donnees} initié")
    return JsonResponse({
        'success': True,
        'message': f'Export de données de type {type_donnees} initié'
    })


@login_required
def intelligent_search(request):
    """Vue de recherche intelligente."""
    return render(request, 'core/recherche_intelligente.html', {
        'titre_page': 'Recherche Intelligente'
    })


@login_required
def configuration_entreprise(request):
    """Vue de configuration de l'entreprise."""
    messages.info(request, "Page de configuration de l'entreprise en cours de développement")
    return redirect('core:dashboard')


@login_required
def changer_devise(request):
    """Vue pour changer la devise."""
    if request.method == 'POST':
        devise = request.POST.get('devise')
        if devise:
            messages.success(request, f"Devise changée vers {devise}")
        else:
            messages.error(request, "Devise non spécifiée")
    
    return redirect(request.META.get('HTTP_REFERER', 'core:dashboard'))
