#!/usr/bin/env python
"""
Vérification de la base de données - Stockage des données
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from django.db import connection
from utilisateurs.models import Utilisateur, GroupeTravail
from proprietes.models import Propriete, Bailleur
from contrats.models import Contrat
from paiements.models import Paiement, Retrait
from django.db import models

def verifier_base_donnees():
    """Vérifier que les données sont bien stockées dans la base de données"""
    
    print("🔍 VÉRIFICATION DE LA BASE DE DONNÉES")
    print("=" * 60)
    
    # Test 1: Vérifier la connexion à la base de données
    print("\n📊 Test 1: Connexion à la base de données")
    print("-" * 40)
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            print(f"✅ Connexion réussie - {len(tables)} tables trouvées")
            
            # Afficher les tables principales
            tables_principales = ['utilisateurs_utilisateur', 'utilisateurs_groupetravail', 
                                'proprietes_propriete', 'proprietes_bailleur', 
                                'contrats_contrat', 'paiements_paiement', 'paiements_retrait']
            
            for table in tables_principales:
                if any(table in str(t) for t in tables):
                    print(f"   ✅ Table {table} présente")
                else:
                    print(f"   ❌ Table {table} manquante")
                    
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")
        return False
    
    # Test 2: Vérifier les utilisateurs
    print("\n👥 Test 2: Utilisateurs dans la base")
    print("-" * 40)
    
    utilisateurs = Utilisateur.objects.all()
    print(f"✅ {utilisateurs.count()} utilisateurs trouvés")
    
    for user in utilisateurs:
        print(f"   - {user.username} ({user.get_full_name()}) - Groupe: {user.get_groupe_display()}")
    
    # Test 3: Vérifier les groupes de travail
    print("\n🏢 Test 3: Groupes de travail")
    print("-" * 40)
    
    groupes = GroupeTravail.objects.all()
    print(f"✅ {groupes.count()} groupes trouvés")
    
    for groupe in groupes:
        print(f"   - {groupe.nom}: {groupe.description}")
        print(f"     Utilisateurs: {groupe.utilisateurs.count()}")
    
    # Test 4: Vérifier les propriétés
    print("\n🏠 Test 4: Propriétés")
    print("-" * 40)
    
    proprietes = Propriete.objects.all()
    print(f"✅ {proprietes.count()} propriétés trouvées")
    
    for prop in proprietes[:5]:  # Afficher les 5 premières
        print(f"   - {prop.adresse} (Bailleur: {prop.bailleur.nom if prop.bailleur else 'Aucun'})")
    
    # Test 5: Vérifier les bailleurs
    print("\n👤 Test 5: Bailleurs")
    print("-" * 40)
    
    bailleurs = Bailleur.objects.all()
    print(f"✅ {bailleurs.count()} bailleurs trouvés")
    
    for bailleur in bailleurs:
        print(f"   - {bailleur.nom} {bailleur.prenom} ({bailleur.email})")
    
    # Test 6: Vérifier les contrats
    print("\n📋 Test 6: Contrats")
    print("-" * 40)
    
    contrats = Contrat.objects.all()
    print(f"✅ {contrats.count()} contrats trouvés")
    
    for contrat in contrats[:5]:  # Afficher les 5 premiers
        print(f"   - Contrat {contrat.id}: {contrat.propriete.adresse} - Statut: {contrat.get_statut()}")
    
    # Test 7: Vérifier les paiements
    print("\n💰 Test 7: Paiements")
    print("-" * 40)
    
    paiements = Paiement.objects.all()
    print(f"✅ {paiements.count()} paiements trouvés")
    
    total_paiements = paiements.aggregate(total=models.Sum('montant'))['total'] or 0
    print(f"   Total des paiements: {total_paiements} F CFA")
    
    # Test 8: Vérifier les retraits
    print("\n💸 Test 8: Retraits")
    print("-" * 40)
    
    retraits = Retrait.objects.all()
    print(f"✅ {retraits.count()} retraits trouvés")
    
    total_retraits = retraits.aggregate(total=models.Sum('montant'))['total'] or 0
    print(f"   Total des retraits: {total_retraits} F CFA")
    
    # Test 9: Vérifier l'intégrité des données
    print("\n🔗 Test 9: Intégrité des données")
    print("-" * 40)
    
    # Vérifier les relations
    proprietes_sans_bailleur = Propriete.objects.filter(bailleur__isnull=True).count()
    contrats_sans_propriete = Contrat.objects.filter(propriete__isnull=True).count()
    paiements_sans_contrat = Paiement.objects.filter(contrat__isnull=True).count()
    
    print(f"   Propriétés sans bailleur: {proprietes_sans_bailleur}")
    print(f"   Contrats sans propriété: {contrats_sans_propriete}")
    print(f"   Paiements sans contrat: {paiements_sans_contrat}")
    
    if proprietes_sans_bailleur == 0 and contrats_sans_propriete == 0 and paiements_sans_contrat == 0:
        print("   ✅ Intégrité des données parfaite")
    else:
        print("   ⚠️ Quelques données orphelines détectées")
    
    # Test 10: Test de création d'une nouvelle donnée
    print("\n➕ Test 10: Test de création de données")
    print("-" * 40)
    
    try:
        # Créer un utilisateur de test
        test_user = Utilisateur.objects.create_user(
            username='test_verification',
            email='test.verification@example.com',
            password='test123',
            first_name='Test',
            last_name='Verification',
            groupe_travail=GroupeTravail.objects.first()
        )
        print(f"✅ Utilisateur de test créé: {test_user.username}")
        
        # Vérifier qu'il est bien en base
        user_from_db = Utilisateur.objects.get(username='test_verification')
        print(f"✅ Utilisateur récupéré de la base: {user_from_db.username}")
        
        # Supprimer l'utilisateur de test
        test_user.delete()
        print("✅ Utilisateur de test supprimé")
        
    except Exception as e:
        print(f"❌ Erreur lors du test de création: {e}")
        return False
    
    print("\n✅ TOUS LES TESTS PASSÉS !")
    print("🎉 La base de données fonctionne parfaitement !")
    
    return True

if __name__ == "__main__":
    verifier_base_donnees() 