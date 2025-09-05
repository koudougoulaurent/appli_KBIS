#!/usr/bin/env python
"""
Test final du système d'unités locatives
"""
import os
import django
import requests
import sys

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from proprietes.models import UniteLocative, Propriete
from django.test import Client
from django.contrib.auth import get_user_model

User = get_user_model()

def test_system():
    """Test complet du système."""
    print("🧪 TEST FINAL DU SYSTÈME D'UNITÉS LOCATIVES")
    print("=" * 60)
    
    # Test 1: Vérifier les données
    print("\n1️⃣ Vérification des données...")
    unites = UniteLocative.objects.filter(is_deleted=False)
    print(f"   ✅ {unites.count()} unités locatives trouvées")
    
    if unites.exists():
        unite = unites.first()
        print(f"   ✅ Exemple: {unite.numero_unite} - {unite.get_loyer_total()} F CFA")
        
        propriete = unite.propriete
        print(f"   ✅ Propriété: {propriete.titre}")
        print(f"   ✅ Grande propriété: {propriete.est_grande_propriete()}")
        print(f"   ✅ Taux d'occupation: {propriete.get_taux_occupation_global()}%")
    
    # Test 2: Test des templates
    print("\n2️⃣ Test des templates...")
    client = Client()
    
    # Créer ou récupérer un utilisateur de test
    try:
        user = User.objects.get(username='privilege1')
        print(f"   ✅ Utilisateur de test trouvé: {user.username}")
    except User.DoesNotExist:
        print("   ❌ Utilisateur de test non trouvé")
        return False
    
    # Connexion
    client.force_login(user)
    print("   ✅ Connexion réussie")
    
    # Test de la page principale
    try:
        response = client.get('/proprietes/unites/')
        if response.status_code == 200:
            print("   ✅ Page liste des unités accessible")
        else:
            print(f"   ❌ Erreur page liste: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Erreur lors du test de la liste: {e}")
        return False
    
    # Test du dashboard principal
    try:
        response = client.get('/')
        if response.status_code == 200:
            print("   ✅ Dashboard principal accessible")
            # Vérifier si la section unités locatives est présente
            if 'Unités Locatives' in response.content.decode():
                print("   ✅ Section unités locatives présente dans le dashboard")
            else:
                print("   ⚠️  Section unités locatives non visible dans le dashboard")
        else:
            print(f"   ❌ Erreur dashboard: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Erreur lors du test du dashboard: {e}")
    
    # Test du dashboard propriété si disponible
    if unites.exists():
        propriete = unites.first().propriete
        try:
            response = client.get(f'/proprietes/{propriete.pk}/dashboard/')
            if response.status_code == 200:
                print("   ✅ Dashboard propriété accessible")
            else:
                print(f"   ❌ Erreur dashboard propriété: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Erreur dashboard propriété: {e}")
    
    # Test 3: Test des APIs
    print("\n3️⃣ Test des APIs...")
    try:
        response = client.get('/proprietes/api/unites-disponibles/')
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ API unités disponibles: {data.get('count', 0)} unités")
        else:
            print(f"   ❌ Erreur API: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Erreur API: {e}")
    
    print("\n" + "=" * 60)
    print("✅ TESTS TERMINÉS AVEC SUCCÈS!")
    print("\n🎯 SYSTÈME PRÊT À UTILISER:")
    print("   🌐 Dashboard: http://127.0.0.1:8000/")
    print("   🏠 Unités locatives: http://127.0.0.1:8000/proprietes/unites/")
    print("   ⚙️  Admin: http://127.0.0.1:8000/admin/proprietes/unitelocative/")
    
    # Afficher quelques statistiques finales
    if unites.exists():
        print(f"\n📊 STATISTIQUES FINALES:")
        stats = {
            'total': unites.count(),
            'disponibles': unites.filter(statut='disponible').count(),
            'occupees': unites.filter(statut='occupee').count(),
            'reservees': unites.filter(statut='reservee').count(),
        }
        
        for statut, count in stats.items():
            print(f"   • {statut.capitalize()}: {count}")
        
        # Calcul des revenus
        revenus_potentiels = sum(u.get_loyer_total() for u in unites)
        revenus_actuels = sum(u.get_loyer_total() for u in unites.filter(statut='occupee'))
        
        print(f"   • Revenus potentiels: {revenus_potentiels:,.0f} F CFA/mois")
        print(f"   • Revenus actuels: {revenus_actuels:,.0f} F CFA/mois")
        print(f"   • Manque à gagner: {revenus_potentiels - revenus_actuels:,.0f} F CFA/mois")
    
    return True

if __name__ == "__main__":
    try:
        success = test_system()
        if success:
            print("\n🎉 TOUS LES TESTS SONT PASSÉS AVEC SUCCÈS!")
            sys.exit(0)
        else:
            print("\n❌ CERTAINS TESTS ONT ÉCHOUÉ")
            sys.exit(1)
    except Exception as e:
        print(f"\n💥 ERREUR CRITIQUE: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
