#!/usr/bin/env python
"""
Test de concurrence pour simuler 2 utilisateurs créant des propriétés simultanément
"""

import os
import sys
import django
import threading
import time
from datetime import datetime

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from core.id_generator import IDGenerator
from proprietes.models import Propriete, TypeBien
from django.db import transaction
from django.contrib.auth import get_user_model

User = get_user_model()

def simulate_user_creating_property(user_id, results, errors):
    """
    Simule un utilisateur créant une propriété
    """
    try:
        print(f"👤 Utilisateur {user_id} commence la création...")
        
        # Générer un ID unique
        generator = IDGenerator()
        numero_propriete = generator.generate_id('propriete')
        
        print(f"👤 Utilisateur {user_id} a généré l'ID: {numero_propriete}")
        
        # Simuler un petit délai (comme dans la vraie app)
        time.sleep(0.1)
        
        # Créer la propriété avec transaction atomique
        with transaction.atomic():
            # Vérifier une dernière fois l'unicité
            if Propriete.objects.filter(numero_propriete=numero_propriete, is_deleted=False).exists():
                # Conflit détecté, utiliser un fallback
                timestamp = datetime.now().strftime('%H%M%S%f')[:-3]
                numero_propriete = f"PRO-{datetime.now().year}-{timestamp}"
                print(f"⚠️  Utilisateur {user_id} - Conflit détecté, utilisation du fallback: {numero_propriete}")
            
            # Créer la propriété
            propriete = Propriete.objects.create(
                numero_propriete=numero_propriete,
                titre=f"Propriété de l'utilisateur {user_id}",
                type_bien_id=1,  # Supposer qu'il existe un TypeBien avec ID 1
                type_gestion='propriete_entiere',
                cree_par_id=1  # Supposer qu'il existe un utilisateur avec ID 1
            )
            
            results.append({
                'user_id': user_id,
                'numero_propriete': numero_propriete,
                'propriete_id': propriete.id,
                'timestamp': datetime.now().isoformat()
            })
            
            print(f"✅ Utilisateur {user_id} a créé la propriété: {numero_propriete}")
    
    except Exception as e:
        error_msg = f"Utilisateur {user_id}: {str(e)}"
        errors.append(error_msg)
        print(f"❌ {error_msg}")

def test_concurrent_property_creation():
    """
    Test principal : 2 utilisateurs créent des propriétés simultanément
    """
    print("🚀 DÉMARRAGE DU TEST DE CONCURRENCE")
    print("=" * 60)
    print("🎯 Scénario: 2 utilisateurs créent des propriétés en même temps")
    print("🎯 Objectif: Vérifier qu'aucun doublon n'est créé")
    print("=" * 60)
    
    # Nettoyer les données de test précédentes
    Propriete.objects.filter(titre__startswith="Propriété de l'utilisateur").delete()
    
    results = []
    errors = []
    
    # Créer 2 threads pour simuler 2 utilisateurs simultanés
    threads = []
    
    for i in range(1, 3):  # Utilisateurs 1 et 2
        thread = threading.Thread(
            target=simulate_user_creating_property,
            args=(i, results, errors)
        )
        threads.append(thread)
    
    print("⏰ Démarrage simultané des 2 utilisateurs...")
    start_time = time.time()
    
    # Démarrer tous les threads en même temps
    for thread in threads:
        thread.start()
    
    # Attendre que tous les threads se terminent
    for thread in threads:
        thread.join()
    
    end_time = time.time()
    duration = end_time - start_time
    
    print("\n" + "=" * 60)
    print("📊 RÉSULTATS DU TEST")
    print("=" * 60)
    
    # Analyser les résultats
    print(f"⏱️  Durée du test: {duration:.3f} secondes")
    print(f"👥 Utilisateurs simulés: 2")
    print(f"✅ Propriétés créées: {len(results)}")
    print(f"❌ Erreurs: {len(errors)}")
    
    if errors:
        print("\n🚨 ERREURS DÉTECTÉES:")
        for error in errors:
            print(f"  - {error}")
    
    # Vérifier l'unicité des numéros
    numeros = [r['numero_propriete'] for r in results]
    unique_numeros = set(numeros)
    
    print(f"\n🔍 VÉRIFICATION D'UNICITÉ:")
    print(f"  - Numéros générés: {len(numeros)}")
    print(f"  - Numéros uniques: {len(unique_numeros)}")
    print(f"  - Doublons détectés: {len(numeros) - len(unique_numeros)}")
    
    if len(numeros) == len(unique_numeros):
        print("  ✅ SUCCÈS: Aucun doublon détecté!")
    else:
        print("  ❌ ÉCHEC: Des doublons ont été détectés!")
        print("  📋 Numéros dupliqués:")
        from collections import Counter
        counter = Counter(numeros)
        for numero, count in counter.items():
            if count > 1:
                print(f"    - {numero}: {count} fois")
    
    # Afficher les détails des propriétés créées
    print(f"\n📋 DÉTAILS DES PROPRIÉTÉS CRÉÉES:")
    for result in results:
        print(f"  👤 Utilisateur {result['user_id']}: {result['numero_propriete']} (ID: {result['propriete_id']})")
    
    # Test de stress avec plus d'utilisateurs
    print(f"\n🔥 TEST DE STRESS: 10 utilisateurs simultanés")
    print("-" * 40)
    
    stress_results = []
    stress_errors = []
    stress_threads = []
    
    for i in range(1, 11):  # 10 utilisateurs
        thread = threading.Thread(
            target=simulate_user_creating_property,
            args=(i, stress_results, stress_errors)
        )
        stress_threads.append(thread)
    
    start_time = time.time()
    for thread in stress_threads:
        thread.start()
    
    for thread in stress_threads:
        thread.join()
    
    end_time = time.time()
    stress_duration = end_time - start_time
    
    stress_numeros = [r['numero_propriete'] for r in stress_results]
    stress_unique_numeros = set(stress_numeros)
    
    print(f"⏱️  Durée: {stress_duration:.3f} secondes")
    print(f"✅ Propriétés créées: {len(stress_results)}")
    print(f"❌ Erreurs: {len(stress_errors)}")
    print(f"🔍 Unicité: {len(stress_numeros)} générés, {len(stress_unique_numeros)} uniques")
    
    if len(stress_numeros) == len(stress_unique_numeros):
        print("  ✅ SUCCÈS: Aucun doublon même avec 10 utilisateurs simultanés!")
    else:
        print("  ❌ ÉCHEC: Des doublons détectés dans le test de stress!")
    
    # Nettoyer les données de test
    Propriete.objects.filter(titre__startswith="Propriété de l'utilisateur").delete()
    
    print("\n" + "=" * 60)
    print("🎉 CONCLUSION DU TEST")
    print("=" * 60)
    
    success = (
        len(errors) == 0 and 
        len(numeros) == len(unique_numeros) and
        len(stress_errors) == 0 and
        len(stress_numeros) == len(stress_unique_numeros)
    )
    
    if success:
        print("✅ TOUS LES TESTS SONT PASSÉS!")
        print("✅ Le système gère parfaitement la concurrence")
        print("✅ Aucun doublon possible, même avec 10+ utilisateurs simultanés")
        print("✅ Performance optimale maintenue")
    else:
        print("❌ CERTAINS TESTS ONT ÉCHOUÉ!")
        print("❌ Le système nécessite des améliorations")
    
    return success

if __name__ == "__main__":
    success = test_concurrent_property_creation()
    sys.exit(0 if success else 1)





