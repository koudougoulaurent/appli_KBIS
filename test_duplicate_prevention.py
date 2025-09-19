#!/usr/bin/env python
"""
Script de test pour vérifier la prévention des doublons
"""

import os
import sys
import django
from datetime import datetime

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from core.id_generator import IDGenerator
from core.duplicate_prevention import DuplicatePreventionSystem
from proprietes.models import Propriete
from django.db import transaction
import threading
import time

def test_concurrent_id_generation():
    """
    Test de génération concurrente d'IDs pour vérifier l'absence de doublons
    """
    print("🧪 Test de génération concurrente d'IDs...")
    
    generated_ids = []
    errors = []
    
    def generate_id_worker(worker_id):
        """Worker pour générer des IDs en concurrence"""
        try:
            generator = IDGenerator()
            for i in range(10):  # 10 IDs par worker
                id_value = generator.generate_id('propriete')
                generated_ids.append((worker_id, i, id_value))
                time.sleep(0.01)  # Petite pause pour simuler la concurrence
        except Exception as e:
            errors.append((worker_id, str(e)))
    
    # Créer 5 threads qui génèrent des IDs en concurrence
    threads = []
    for i in range(5):
        thread = threading.Thread(target=generate_id_worker, args=(i,))
        threads.append(thread)
        thread.start()
    
    # Attendre que tous les threads se terminent
    for thread in threads:
        thread.join()
    
    # Vérifier les résultats
    unique_ids = set()
    duplicates = []
    
    for worker_id, iteration, id_value in generated_ids:
        if id_value in unique_ids:
            duplicates.append((worker_id, iteration, id_value))
        else:
            unique_ids.add(id_value)
    
    print(f"✅ IDs générés: {len(generated_ids)}")
    print(f"✅ IDs uniques: {len(unique_ids)}")
    print(f"❌ Doublons détectés: {len(duplicates)}")
    print(f"❌ Erreurs: {len(errors)}")
    
    if duplicates:
        print("🚨 DOUBLONS TROUVÉS:")
        for worker_id, iteration, id_value in duplicates:
            print(f"  Worker {worker_id}, Iteration {iteration}: {id_value}")
    
    if errors:
        print("🚨 ERREURS:")
        for worker_id, error in errors:
            print(f"  Worker {worker_id}: {error}")
    
    return len(duplicates) == 0 and len(errors) == 0

def test_duplicate_prevention_system():
    """
    Test du système de prévention des doublons
    """
    print("\n🧪 Test du système de prévention des doublons...")
    
    # Créer une propriété de test
    test_property = Propriete.objects.create(
        numero_propriete="TEST-DUPLICATE-001",
        titre="Propriété de test",
        type_bien_id=1,  # Supposer qu'il existe un TypeBien avec ID 1
        type_gestion='propriete_entiere'
    )
    
    try:
        # Tester la détection de doublon
        is_unique = DuplicatePreventionSystem.check_property_number_uniqueness(
            "TEST-DUPLICATE-001"
        )
        
        if not is_unique:
            print("✅ Système de détection de doublon fonctionne")
        else:
            print("❌ Système de détection de doublon ne fonctionne pas")
            return False
        
        # Tester avec un numéro unique
        is_unique = DuplicatePreventionSystem.check_property_number_uniqueness(
            "TEST-UNIQUE-001"
        )
        
        if is_unique:
            print("✅ Système de détection d'unicité fonctionne")
        else:
            print("❌ Système de détection d'unicité ne fonctionne pas")
            return False
        
        return True
        
    finally:
        # Nettoyer
        test_property.delete()

def test_form_validation():
    """
    Test de la validation côté formulaire
    """
    print("\n🧪 Test de la validation côté formulaire...")
    
    from proprietes.forms import ProprieteForm
    from proprietes.models import TypeBien
    
    # Créer un type de bien si nécessaire
    type_bien, created = TypeBien.objects.get_or_create(
        nom="Test",
        defaults={'description': 'Type de test'}
    )
    
    # Créer une propriété de test
    test_property = Propriete.objects.create(
        numero_propriete="TEST-FORM-001",
        titre="Propriété de test form",
        type_bien=type_bien,
        type_gestion='propriete_entiere'
    )
    
    try:
        # Tester la validation avec un doublon
        form_data = {
            'numero_propriete': 'TEST-FORM-001',
            'titre': 'Nouvelle propriété',
            'type_bien': type_bien.id,
            'type_gestion': 'propriete_entiere'
        }
        
        form = ProprieteForm(data=form_data)
        is_valid = form.is_valid()
        
        if not is_valid and 'numero_propriete' in form.errors:
            print("✅ Validation de doublon fonctionne")
        else:
            print("❌ Validation de doublon ne fonctionne pas")
            return False
        
        # Tester la validation avec un numéro unique
        form_data['numero_propriete'] = 'TEST-FORM-UNIQUE-001'
        form = ProprieteForm(data=form_data)
        is_valid = form.is_valid()
        
        if is_valid:
            print("✅ Validation d'unicité fonctionne")
        else:
            print(f"❌ Validation d'unicité ne fonctionne pas: {form.errors}")
            return False
        
        return True
        
    finally:
        # Nettoyer
        test_property.delete()

def main():
    """
    Fonction principale de test
    """
    print("🚀 Démarrage des tests de prévention des doublons")
    print("=" * 60)
    
    tests = [
        test_concurrent_id_generation,
        test_duplicate_prevention_system,
        test_form_validation
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
                print("✅ Test réussi")
            else:
                print("❌ Test échoué")
        except Exception as e:
            print(f"❌ Test échoué avec erreur: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 Résultats: {passed}/{total} tests réussis")
    
    if passed == total:
        print("🎉 Tous les tests sont passés ! Le système de prévention des doublons fonctionne.")
    else:
        print("⚠️  Certains tests ont échoué. Vérifiez le système.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)


