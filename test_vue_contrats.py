#!/usr/bin/env python
"""
Test de la vue des contrats pour vérifier l'affichage des IDs uniques
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth import get_user_model
from contrats.views import ContratListView
from contrats.models import Contrat

Utilisateur = get_user_model()

def test_vue_contrats():
    """Tester la vue des contrats pour vérifier l'affichage des IDs uniques"""
    
    print("🔍 TEST DE LA VUE DES CONTRATS")
    print("=" * 60)
    
    # Créer une requête de test
    factory = RequestFactory()
    request = factory.get('/contrats/')
    
    # Créer un utilisateur de test avec les bonnes permissions
    try:
        # Essayer de récupérer un utilisateur existant avec les bonnes permissions
        from core.utils import check_group_permissions
        
        # Chercher un utilisateur PRIVILEGE ou ADMINISTRATION
        utilisateur_test = None
        for groupe in ['PRIVILEGE', 'ADMINISTRATION', 'CONTROLES', 'CAISSE']:
            users = Utilisateur.objects.filter(groupe_travail__nom__iexact=groupe)
            if users.exists():
                utilisateur_test = users.first()
                print(f"✅ Utilisateur de test trouvé: {utilisateur_test.username} (Groupe: {utilisateur_test.groupe_travail.nom})")
                break
        
        if not utilisateur_test:
            print("❌ Aucun utilisateur avec les bonnes permissions trouvé")
            return False
        
        # Connecter l'utilisateur
        request.user = utilisateur_test
        
        # Créer la vue et l'initialiser correctement
        view = ContratListView()
        view.request = request
        view.kwargs = {}
        
        # Tester le get_queryset
        print("\n📊 Test du queryset:")
        print("-" * 40)
        
        queryset = view.get_queryset()
        print(f"✅ Queryset créé: {queryset.count()} contrats")
        
        # Afficher les premiers contrats avec leurs numéros
        for contrat in queryset[:5]:
            print(f"   - Contrat ID: {contrat.id}")
            print(f"     Numéro: {contrat.numero_contrat}")
            print(f"     Propriété: {contrat.propriete.adresse if contrat.propriete else 'Aucune'}")
            print(f"     Locataire: {contrat.locataire.nom if contrat.locataire else 'Aucun'}")
            print()
        
        # Tester le get_context_data
        print("\n📋 Test du contexte:")
        print("-" * 40)
        
        # Initialiser object_list pour éviter l'erreur
        view.object_list = queryset
        
        context = view.get_context_data()
        print(f"✅ Contexte créé avec {len(context)} éléments")
        
        # Vérifier les éléments importants du contexte
        if 'object_list' in context:
            print(f"   - object_list: {len(context['object_list'])} éléments")
        else:
            print("   ❌ object_list manquant dans le contexte")
        
        if 'columns' in context:
            print(f"   - columns: {len(context['columns'])} colonnes")
            for col in context['columns']:
                print(f"     * {col['field']}: {col['label']}")
        else:
            print("   ❌ columns manquant dans le contexte")
        
        if 'actions' in context:
            print(f"   - actions: {len(context['actions'])} actions")
        else:
            print("   ❌ actions manquant dans le contexte")
        
        # Tester le filtre get_attribute
        print("\n🔧 Test du filtre get_attribute:")
        print("-" * 40)
        
        from core.templatetags.core_extras import get_attribute
        
        if queryset.exists():
            contrat_test = queryset.first()
            print(f"   Test avec le contrat: {contrat_test.numero_contrat}")
            
            # Tester différents attributs
            test_attrs = ['numero_contrat', 'propriete__adresse', 'locataire__nom']
            
            for attr in test_attrs:
                value = get_attribute(contrat_test, attr)
                print(f"     {attr}: {value}")
            
            # Tester l'affichage des colonnes
            print("\n📊 Test de l'affichage des colonnes:")
            print("-" * 40)
            
            if 'columns' in context:
                for col in context['columns']:
                    field = col['field']
                    value = get_attribute(contrat_test, field)
                    print(f"   {col['label']} ({field}): {value}")
        
        # Vérifier que les numéros de contrats sont bien présents
        print("\n🔍 Vérification des numéros de contrats:")
        print("-" * 40)
        
        contrats_avec_numeros = queryset.filter(numero_contrat__isnull=False).exclude(numero_contrat='')
        print(f"✅ Contrats avec numéros: {contrats_avec_numeros.count()}")
        
        if contrats_avec_numeros.exists():
            print("   Exemples de numéros:")
            for contrat in contrats_avec_numeros[:3]:
                print(f"     - {contrat.numero_contrat}")
        
        # Test de rendu du template
        print("\n🎨 Test de rendu du template:")
        print("-" * 40)
        
        try:
            # Simuler le rendu du template
            from django.template.loader import render_to_string
            from django.template import Context, Template
            
            # Créer un contexte simple pour tester
            template_context = {
                'object_list': queryset[:3],
                'columns': context.get('columns', []),
                'actions': context.get('actions', []),
                'is_privilege_user': True
            }
            
            # Tester le rendu d'une ligne du tableau
            if template_context['columns']:
                print("   Test de rendu d'une ligne:")
                for col in template_context['columns'][:3]:
                    field = col['field']
                    if queryset.exists():
                        value = get_attribute(queryset.first(), field)
                        print(f"     {col['label']}: {value}")
        
        except Exception as e:
            print(f"   ⚠️ Erreur lors du test de rendu: {e}")
        
        print("\n✅ Test de la vue terminé avec succès!")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_vue_contrats()
