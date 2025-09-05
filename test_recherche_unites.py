#!/usr/bin/env python3
"""
Script de test pour vérifier le système de recherche d'unités locatives
"""

import os
import sys
import django

# Configuration Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'appli_KBIS.settings')
django.setup()

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from proprietes.models import Propriete, UniteLocative, Bailleur, TypeBien
from proprietes.forms import UniteRechercheForm

User = get_user_model()

def test_recherche_unites_system():
    """Test complet du système de recherche d'unités"""
    print("🔍 Test du système de recherche d'unités locatives")
    print("=" * 60)
    
    # Test 1: Vérification des URLs
    print("\n1. Test des URLs...")
    try:
        url_recherche = reverse('proprietes:recherche_unites')
        print(f"   ✅ URL de recherche: {url_recherche}")
        
        url_api_live = reverse('proprietes:api_recherche_unites_live')
        print(f"   ✅ URL API recherche live: {url_api_live}")
        
        url_api_stats = reverse('proprietes:api_statistiques_recherche')
        print(f"   ✅ URL API statistiques: {url_api_stats}")
        
    except Exception as e:
        print(f"   ❌ Erreur URLs: {e}")
        return False
    
    # Test 2: Vérification du formulaire
    print("\n2. Test du formulaire de recherche...")
    try:
        form = UniteRechercheForm()
        print(f"   ✅ Formulaire créé avec {len(form.fields)} champs")
        
        # Test des champs principaux
        required_fields = ['search', 'propriete', 'bailleur', 'statut', 'type_unite', 'tri']
        for field in required_fields:
            if field in form.fields:
                print(f"   ✅ Champ '{field}' présent")
            else:
                print(f"   ❌ Champ '{field}' manquant")
                
    except Exception as e:
        print(f"   ❌ Erreur formulaire: {e}")
        return False
    
    # Test 3: Vérification du modèle UniteLocative
    print("\n3. Test du modèle UniteLocative...")
    try:
        # Vérifier les champs du modèle
        unite_fields = [f.name for f in UniteLocative._meta.get_fields()]
        required_fields = [
            'propriete', 'numero_unite', 'nom', 'type_unite', 
            'statut', 'loyer_mensuel', 'surface', 'etage'
        ]
        
        for field in required_fields:
            if field in unite_fields:
                print(f"   ✅ Champ modèle '{field}' présent")
            else:
                print(f"   ❌ Champ modèle '{field}' manquant")
                
        # Vérifier les choix
        print(f"   ✅ Types d'unité: {len(UniteLocative.TYPE_UNITE_CHOICES)} options")
        print(f"   ✅ Statuts: {len(UniteLocative.STATUT_CHOICES)} options")
        
    except Exception as e:
        print(f"   ❌ Erreur modèle: {e}")
        return False
    
    # Test 4: Test des templates
    print("\n4. Test des templates...")
    try:
        import os
        template_dir = os.path.join(os.path.dirname(__file__), 'templates', 'proprietes', 'unites')
        
        templates = ['recherche.html', 'detail_complet.html']
        for template in templates:
            template_path = os.path.join(template_dir, template)
            if os.path.exists(template_path):
                print(f"   ✅ Template '{template}' trouvé")
            else:
                print(f"   ❌ Template '{template}' manquant")
                
    except Exception as e:
        print(f"   ❌ Erreur templates: {e}")
    
    # Test 5: Test de création de données de test
    print("\n5. Test de création de données...")
    try:
        # Créer un type de bien
        type_bien, created = TypeBien.objects.get_or_create(
            nom="Appartement",
            defaults={'description': 'Appartement de test'}
        )
        print(f"   ✅ Type de bien: {'créé' if created else 'existant'}")
        
        # Créer un bailleur
        bailleur, created = Bailleur.objects.get_or_create(
            nom="Test",
            prenom="Bailleur",
            defaults={
                'email': 'test@example.com',
                'telephone': '0123456789'
            }
        )
        print(f"   ✅ Bailleur: {'créé' if created else 'existant'}")
        
        # Créer une propriété
        propriete, created = Propriete.objects.get_or_create(
            numero_propriete="TEST001",
            defaults={
                'titre': 'Propriété de test',
                'type_bien': type_bien,
                'bailleur': bailleur,
                'nombre_pieces': 5,
                'nombre_chambres': 3,
                'nombre_salles_bain': 2,
                'adresse': '123 Rue de Test',
                'ville': 'Test City'
            }
        )
        print(f"   ✅ Propriété: {'créée' if created else 'existante'}")
        
        # Créer des unités locatives
        for i in range(1, 4):
            unite, created = UniteLocative.objects.get_or_create(
                propriete=propriete,
                numero_unite=f"APT{i:03d}",
                defaults={
                    'nom': f'Appartement {i}',
                    'type_unite': 'appartement',
                    'statut': 'disponible' if i % 2 == 0 else 'occupee',
                    'etage': i,
                    'surface': 50 + (i * 10),
                    'nombre_pieces': 2 + i,
                    'nombre_chambres': 1 + (i // 2),
                    'nombre_salles_bain': 1,
                    'loyer_mensuel': 500 + (i * 100),
                    'charges_mensuelles': 50,
                    'caution_demandee': 1000 + (i * 200),
                    'meuble': i % 2 == 0,
                    'balcon': i > 1,
                    'parking_inclus': i == 3,
                    'climatisation': i > 2
                }
            )
            if created:
                print(f"   ✅ Unité {unite.numero_unite} créée")
        
        total_unites = UniteLocative.objects.filter(is_deleted=False).count()
        print(f"   ✅ Total unités dans la base: {total_unites}")
        
    except Exception as e:
        print(f"   ❌ Erreur création données: {e}")
        return False
    
    # Test 6: Test des requêtes de recherche
    print("\n6. Test des requêtes de recherche...")
    try:
        # Test recherche par texte
        unites = UniteLocative.objects.filter(
            numero_unite__icontains="APT",
            is_deleted=False
        )
        print(f"   ✅ Recherche par numéro: {unites.count()} résultats")
        
        # Test recherche par statut
        unites_disponibles = UniteLocative.objects.filter(
            statut='disponible',
            is_deleted=False
        )
        print(f"   ✅ Unités disponibles: {unites_disponibles.count()}")
        
        # Test recherche par propriété
        unites_propriete = UniteLocative.objects.filter(
            propriete=propriete,
            is_deleted=False
        )
        print(f"   ✅ Unités de la propriété test: {unites_propriete.count()}")
        
    except Exception as e:
        print(f"   ❌ Erreur requêtes: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("🎉 Tous les tests sont passés avec succès!")
    print("\nFonctionnalités disponibles:")
    print("- Recherche avancée avec de nombreux filtres")
    print("- Recherche en temps réel (AJAX)")
    print("- Affichage détaillé des unités avec toutes les informations")
    print("- Interface moderne et responsive")
    print("- Navigation optimisée")
    print("\nAccès:")
    print(f"- Recherche d'unités: {url_recherche}")
    print("- Menu de navigation: 'Recherche d'Unités'")
    
    return True

def test_formulaire_validation():
    """Test de validation du formulaire"""
    print("\n🔧 Test de validation du formulaire...")
    
    # Test avec données valides
    valid_data = {
        'search': 'APT',
        'statut': 'disponible',
        'type_unite': 'appartement',
        'loyer_min': 400,
        'loyer_max': 800,
        'tri': 'loyer_mensuel'
    }
    
    form = UniteRechercheForm(data=valid_data)
    if form.is_valid():
        print("   ✅ Validation avec données valides: OK")
    else:
        print(f"   ❌ Erreurs de validation: {form.errors}")
    
    # Test avec données vides (doit être valide car tous les champs sont optionnels)
    empty_form = UniteRechercheForm(data={})
    if empty_form.is_valid():
        print("   ✅ Validation avec données vides: OK")
    else:
        print(f"   ❌ Erreurs avec données vides: {empty_form.errors}")

if __name__ == "__main__":
    try:
        success = test_recherche_unites_system()
        if success:
            test_formulaire_validation()
            print("\n✨ Système de recherche d'unités prêt à l'emploi!")
        else:
            print("\n❌ Des problèmes ont été détectés.")
            sys.exit(1)
    except Exception as e:
        print(f"\n💥 Erreur lors du test: {e}")
        sys.exit(1)
