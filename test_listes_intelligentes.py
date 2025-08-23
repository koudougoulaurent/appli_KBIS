#!/usr/bin/env python
"""
Test script pour les listes intelligentes
Date: 20 juillet 2025
Version: 1.0

Ce script teste le système de listes intelligentes avec recherche et tri.
"""

import os
import sys
import django
from datetime import datetime, timedelta
from django.utils import timezone

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth import get_user_model
from core.intelligent_views import (
    IntelligentProprieteListView,
    IntelligentContratListView,
    IntelligentPaiementListView,
    IntelligentUtilisateurListView
)
from proprietes.models import Propriete, TypeBien
from contrats.models import Contrat
from paiements.models import Paiement
from utilisateurs.models import Utilisateur, Locataire

User = get_user_model()

def test_intelligent_propriete_list():
    """Test de la vue intelligente des propriétés"""
    print("🏠 TEST VUE INTELLIGENTE - PROPRIÉTÉS")
    print("=" * 50)
    
    # Créer une requête de test
    factory = RequestFactory()
    request = factory.get('/proprietes/')
    
    # Créer un utilisateur de test
    user, created = User.objects.get_or_create(
        username='test_user',
        defaults={'email': 'test@example.com'}
    )
    request.user = user
    
    # Créer la vue
    view = IntelligentProprieteListView()
    view.request = request
    
    # Tester le queryset
    queryset = view.get_queryset()
    print(f"📊 Queryset de base: {queryset.count()} propriétés")
    
    # Tester les statistiques
    stats = view.get_statistics()
    print(f"📈 Statistiques: {len(stats)} éléments")
    for stat in stats:
        print(f"  - {stat['label']}: {stat['value']}")
    
    # Tester les suggestions
    suggestions = view.get_suggestions()
    print(f"💡 Suggestions: {len(suggestions)} éléments")
    for suggestion in suggestions:
        print(f"  - {suggestion}")
    
    # Tester les filtres
    filters = view.get_filters()
    print(f"🔍 Filtres disponibles: {len(filters)}")
    for filter_config in filters:
        print(f"  - {filter_config['label']}: {len(filter_config['options'])} options")
    
    # Tester les colonnes
    columns = view.get_columns()
    print(f"📋 Colonnes: {len(columns)}")
    for column in columns:
        print(f"  - {column['label']} (triable: {column.get('sortable', False)})")
    
    return True

def test_intelligent_contrat_list():
    """Test de la vue intelligente des contrats"""
    print("\n📄 TEST VUE INTELLIGENTE - CONTRATS")
    print("=" * 50)
    
    # Créer une requête de test
    factory = RequestFactory()
    request = factory.get('/contrats/')
    
    # Créer un utilisateur de test
    user, created = User.objects.get_or_create(
        username='test_user',
        defaults={'email': 'test@example.com'}
    )
    request.user = user
    
    # Créer la vue
    view = IntelligentContratListView()
    view.request = request
    
    # Tester le queryset
    queryset = view.get_queryset()
    print(f"📊 Queryset de base: {queryset.count()} contrats")
    
    # Tester les statistiques
    stats = view.get_statistics()
    print(f"📈 Statistiques: {len(stats)} éléments")
    for stat in stats:
        print(f"  - {stat['label']}: {stat['value']}")
    
    # Tester les colonnes
    columns = view.get_columns()
    print(f"📋 Colonnes: {len(columns)}")
    for column in columns:
        print(f"  - {column['label']} (triable: {column.get('sortable', False)})")
    
    return True

def test_intelligent_paiement_list():
    """Test de la vue intelligente des paiements"""
    print("\n💰 TEST VUE INTELLIGENTE - PAIEMENTS")
    print("=" * 50)
    
    # Créer une requête de test
    factory = RequestFactory()
    request = factory.get('/paiements/')
    
    # Créer un utilisateur de test
    user, created = User.objects.get_or_create(
        username='test_user',
        defaults={'email': 'test@example.com'}
    )
    request.user = user
    
    # Créer la vue
    view = IntelligentPaiementListView()
    view.request = request
    
    # Tester le queryset
    queryset = view.get_queryset()
    print(f"📊 Queryset de base: {queryset.count()} paiements")
    
    # Tester les statistiques
    stats = view.get_statistics()
    print(f"📈 Statistiques: {len(stats)} éléments")
    for stat in stats:
        print(f"  - {stat['label']}: {stat['value']}")
    
    # Tester les filtres
    filters = view.get_filters()
    print(f"🔍 Filtres disponibles: {len(filters)}")
    for filter_config in filters:
        print(f"  - {filter_config['label']}: {len(filter_config['options'])} options")
    
    return True

def test_intelligent_utilisateur_list():
    """Test de la vue intelligente des utilisateurs"""
    print("\n👥 TEST VUE INTELLIGENTE - UTILISATEURS")
    print("=" * 50)
    
    # Créer une requête de test
    factory = RequestFactory()
    request = factory.get('/utilisateurs/')
    
    # Créer un utilisateur de test
    user, created = User.objects.get_or_create(
        username='test_user',
        defaults={'email': 'test@example.com'}
    )
    request.user = user
    
    # Créer la vue
    view = IntelligentUtilisateurListView()
    view.request = request
    
    # Tester le queryset
    queryset = view.get_queryset()
    print(f"📊 Queryset de base: {queryset.count()} utilisateurs")
    
    # Tester les statistiques
    stats = view.get_statistics()
    print(f"📈 Statistiques: {len(stats)} éléments")
    for stat in stats:
        print(f"  - {stat['label']}: {stat['value']}")
    
    # Tester les actions
    actions = view.get_actions()
    print(f"🔧 Actions disponibles: {len(actions)}")
    for action in actions:
        print(f"  - {action['title']} ({action['url_name']})")
    
    return True

def test_search_functionality():
    """Test de la fonctionnalité de recherche"""
    print("\n🔍 TEST DE LA FONCTIONNALITÉ DE RECHERCHE")
    print("=" * 50)
    
    # Créer des données de test
    create_test_data()
    
    # Test recherche propriétés
    factory = RequestFactory()
    request = factory.get('/proprietes/?search=Test')
    user = User.objects.get(username='test_user')
    request.user = user
    
    view = IntelligentProprieteListView()
    view.request = request
    
    queryset = view.get_queryset()
    print(f"🔍 Recherche 'Test' dans propriétés: {queryset.count()} résultats")
    
    # Test recherche contrats
    request = factory.get('/contrats/?search=CON')
    view = IntelligentContratListView()
    view.request = request
    
    queryset = view.get_queryset()
    print(f"🔍 Recherche 'CON' dans contrats: {queryset.count()} résultats")
    
    # Test recherche paiements
    request = factory.get('/paiements/?search=PAI')
    view = IntelligentPaiementListView()
    view.request = request
    
    queryset = view.get_queryset()
    print(f"🔍 Recherche 'PAI' dans paiements: {queryset.count()} résultats")
    
    return True

def test_filter_functionality():
    """Test de la fonctionnalité de filtrage"""
    print("\n🔧 TEST DE LA FONCTIONNALITÉ DE FILTRAGE")
    print("=" * 50)
    
    # Test filtres propriétés
    factory = RequestFactory()
    request = factory.get('/proprietes/?disponible=true')
    user = User.objects.get(username='test_user')
    request.user = user
    
    view = IntelligentProprieteListView()
    view.request = request
    
    queryset = view.get_queryset()
    print(f"🔧 Filtre 'disponible=true': {queryset.count()} propriétés")
    
    # Test filtres paiements
    request = factory.get('/paiements/?statut=valide')
    view = IntelligentPaiementListView()
    view.request = request
    
    queryset = view.get_queryset()
    print(f"🔧 Filtre 'statut=valide': {queryset.count()} paiements")
    
    return True

def test_sorting_functionality():
    """Test de la fonctionnalité de tri"""
    print("\n📊 TEST DE LA FONCTIONNALITÉ DE TRI")
    print("=" * 50)
    
    # Test tri propriétés
    factory = RequestFactory()
    request = factory.get('/proprietes/?sort=loyer_actuel&order=desc')
    user = User.objects.get(username='test_user')
    request.user = user
    
    view = IntelligentProprieteListView()
    view.request = request
    
    queryset = view.get_queryset()
    print(f"📊 Tri propriétés par loyer décroissant: {queryset.count()} résultats")
    
    # Test tri contrats
    request = factory.get('/contrats/?sort=date_debut&order=asc')
    view = IntelligentContratListView()
    view.request = request
    
    queryset = view.get_queryset()
    print(f"📊 Tri contrats par date début croissant: {queryset.count()} résultats")
    
    return True

def create_test_data():
    """Créer des données de test"""
    print("\n📝 CRÉATION DES DONNÉES DE TEST")
    print("=" * 50)
    
    # Créer un type de bien
    type_bien, created = TypeBien.objects.get_or_create(
        nom='Appartement',
        defaults={'description': 'Appartement standard'}
    )
    
    if created:
        print(f"✅ Type de bien créé: {type_bien.nom}")
    
    # Créer des propriétés de test
    proprietes_created = 0
    for i in range(5):
        propriete, created = Propriete.objects.get_or_create(
            titre=f'Appartement Test {i+1}',
            defaults={
                'adresse': f'{100+i} Rue Test',
                'ville': 'Paris',
                'code_postal': '75001',
                'loyer_actuel': 1000 + (i * 100),
                'disponible': i % 2 == 0,
                'etat': 'bon',
                'type_bien': type_bien
            }
        )
        if created:
            proprietes_created += 1
    
    print(f"✅ {proprietes_created} propriétés créées")
    
    # Créer des utilisateurs de test
    users_created = 0
    for i in range(3):
        user, created = User.objects.get_or_create(
            username=f'test_user_{i+1}',
            defaults={
                'email': f'test{i+1}@example.com',
                'first_name': f'Prénom{i+1}',
                'last_name': f'Nom{i+1}'
            }
        )
        if created:
            users_created += 1
    
    print(f"✅ {users_created} utilisateurs créés")
    
    # Créer des locataires
    locataires_created = 0
    for i in range(3):
        locataire, created = Locataire.objects.get_or_create(
            nom=f'Nom{i+1}',
            prenom=f'Prénom{i+1}',
            defaults={
                'email': f'locataire{i+1}@example.com',
                'telephone': f'+3312345678{i}'
            }
        )
        if created:
            locataires_created += 1
    
    print(f"✅ {locataires_created} locataires créés")
    
    # Créer des contrats
    contrats_created = 0
    proprietes = Propriete.objects.all()[:3]
    locataires = Locataire.objects.all()[:3]
    
    for i, (propriete, locataire) in enumerate(zip(proprietes, locataires)):
        contrat, created = Contrat.objects.get_or_create(
            propriete=propriete,
            locataire=locataire,
            defaults={
                'date_debut': timezone.now().date() - timedelta(days=30),
                'date_fin': timezone.now().date() + timedelta(days=335),
                'loyer_mensuel': propriete.loyer_actuel,
                'jour_paiement': 1,
                'statut': 'actif'
            }
        )
        if created:
            contrats_created += 1
    
    print(f"✅ {contrats_created} contrats créés")
    
    # Créer des paiements
    paiements_created = 0
    contrats = Contrat.objects.all()[:3]
    
    for i, contrat in enumerate(contrats):
        paiement, created = Paiement.objects.get_or_create(
            contrat=contrat,
            date_paiement=timezone.now().date() - timedelta(days=i*10),
            defaults={
                'montant': contrat.loyer_mensuel,
                'methode_paiement': 'virement',
                'type_paiement': 'loyer',
                'statut': 'valide'
            }
        )
        if created:
            paiements_created += 1
    
    print(f"✅ {paiements_created} paiements créés")

def test_template_rendering():
    """Test du rendu des templates"""
    print("\n🎨 TEST DU RENDU DES TEMPLATES")
    print("=" * 50)
    
    # Test avec propriétés
    factory = RequestFactory()
    request = factory.get('/proprietes/')
    user = User.objects.get(username='test_user')
    request.user = user
    
    view = IntelligentProprieteListView()
    view.request = request
    
    # Obtenir le contexte
    context = view.get_context_data()
    
    print(f"📋 Titre de la page: {context['page_title']}")
    print(f"📋 Icône: {context['page_icon']}")
    print(f"📋 URL d'ajout: {context['add_url']}")
    print(f"📋 Statistiques: {len(context['stats'])}")
    print(f"📋 Colonnes: {len(context['columns'])}")
    print(f"📋 Actions: {len(context['actions'])}")
    print(f"📋 Filtres: {len(context['filters'])}")
    print(f"📋 Options de tri: {len(context['sort_options'])}")
    
    return True

def main():
    """Fonction principale de test"""
    print("🚀 DÉMARRAGE DES TESTS DES LISTES INTELLIGENTES")
    print("=" * 60)
    
    results = {}
    
    try:
        # Test 1: Vue intelligente propriétés
        results['propriete_list'] = test_intelligent_propriete_list()
        
        # Test 2: Vue intelligente contrats
        results['contrat_list'] = test_intelligent_contrat_list()
        
        # Test 3: Vue intelligente paiements
        results['paiement_list'] = test_intelligent_paiement_list()
        
        # Test 4: Vue intelligente utilisateurs
        results['utilisateur_list'] = test_intelligent_utilisateur_list()
        
        # Test 5: Fonctionnalité de recherche
        results['search'] = test_search_functionality()
        
        # Test 6: Fonctionnalité de filtrage
        results['filter'] = test_filter_functionality()
        
        # Test 7: Fonctionnalité de tri
        results['sorting'] = test_sorting_functionality()
        
        # Test 8: Rendu des templates
        results['template'] = test_template_rendering()
        
    except Exception as e:
        print(f"❌ Erreur lors des tests: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Résumé des tests
    print("\n" + "=" * 60)
    print("📋 RÉSUMÉ DES TESTS")
    print("=" * 60)
    
    for test_name, result in results.items():
        status = "✅ RÉUSSI" if result else "❌ ÉCHOUÉ"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
    
    success_count = sum(1 for result in results.values() if result)
    total_count = len(results)
    
    print(f"\n📊 Résultat global: {success_count}/{total_count} tests réussis")
    
    if success_count == total_count:
        print("🎉 TOUS LES TESTS SONT RÉUSSIS !")
        return True
    else:
        print("⚠️ Certains tests ont échoué")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 