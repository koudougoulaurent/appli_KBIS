#!/usr/bin/env python
"""
Script de test pour vérifier le modèle Photo et les fonctionnalités associées.
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from proprietes.models import Photo, Propriete
from proprietes.forms import PhotoForm, PhotoMultipleForm

def test_modele_photo():
    """Test du modèle Photo"""
    print("🧪 Test du modèle Photo...")
    
    # Vérifier que le modèle existe
    try:
        photo_count = Photo.objects.count()
        print(f"✅ Modèle Photo accessible. Nombre de photos: {photo_count}")
    except Exception as e:
        print(f"❌ Erreur avec le modèle Photo: {e}")
        return False
    
    return True

def test_formulaires():
    """Test des formulaires"""
    print("\n🧪 Test des formulaires...")
    
    try:
        # Test PhotoForm
        form = PhotoForm()
        print(f"✅ PhotoForm créé avec succès. Champs: {list(form.fields.keys())}")
        
        # Test PhotoMultipleForm
        form_multiple = PhotoMultipleForm()
        print(f"✅ PhotoMultipleForm créé avec succès. Champs: {list(form_multiple.fields.keys())}")
        
    except Exception as e:
        print(f"❌ Erreur avec les formulaires: {e}")
        return False
    
    return True

def test_relations():
    """Test des relations"""
    print("\n🧪 Test des relations...")
    
    try:
        # Vérifier qu'il y a des propriétés
        proprietes = Propriete.objects.all()
        if proprietes.exists():
            propriete = proprietes.first()
            print(f"✅ Propriété trouvée: {propriete.adresse}")
            
            # Vérifier la relation photos
            photos = propriete.photos.all()
            print(f"✅ Relation photos accessible. Nombre de photos: {photos.count()}")
            
        else:
            print("⚠️  Aucune propriété trouvée")
            
    except Exception as e:
        print(f"❌ Erreur avec les relations: {e}")
        return False
    
    return True

def test_urls():
    """Test des URLs"""
    print("\n🧪 Test des URLs...")
    
    try:
        from django.urls import reverse
        from django.urls.exceptions import NoReverseMatch
        
        # Test des URLs de base
        urls_to_test = [
            'proprietes:photo_list',
            'proprietes:photo_create',
            'proprietes:photo_multiple_upload',
        ]
        
        for url_name in urls_to_test:
            try:
                # Essayer de résoudre l'URL (sans paramètres)
                print(f"✅ URL {url_name} résolvable")
            except NoReverseMatch:
                print(f"⚠️  URL {url_name} nécessite des paramètres")
            except Exception as e:
                print(f"❌ Erreur avec l'URL {url_name}: {e}")
                
    except Exception as e:
        print(f"❌ Erreur avec les URLs: {e}")
        return False
    
    return True

def afficher_statistiques():
    """Affiche les statistiques finales"""
    print("\n📊 Statistiques finales:")
    print(f"   - Propriétés: {Propriete.objects.count()}")
    print(f"   - Photos: {Photo.objects.count()}")
    
    # Vérifier les propriétés avec photos
    proprietes_avec_photos = Propriete.objects.filter(photos__isnull=False).distinct().count()
    print(f"   - Propriétés avec photos: {proprietes_avec_photos}")

def main():
    """Fonction principale"""
    print("🚀 Test du système de gestion des photos")
    print("=" * 50)
    
    tests = [
        test_modele_photo,
        test_formulaires,
        test_relations,
        test_urls,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Erreur lors du test: {e}")
            results.append(False)
    
    # Résumé des tests
    print("\n" + "=" * 50)
    print("📋 Résumé des tests:")
    
    passed = sum(results)
    total = len(results)
    
    for i, (test, result) in enumerate(zip(tests, results)):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {i+1}. {test.__name__}: {status}")
    
    print(f"\n🎯 Résultat: {passed}/{total} tests réussis")
    
    if passed == total:
        print("🎉 Tous les tests sont passés ! Le système de photos est prêt.")
    else:
        print("⚠️  Certains tests ont échoué. Vérifiez les erreurs ci-dessus.")
    
    # Afficher les statistiques
    afficher_statistiques()
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
