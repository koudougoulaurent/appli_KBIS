#!/usr/bin/env python
"""
Script de nettoyage agressif de la base de données - Suppression de toutes les données de test
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from django.db import connection, transaction
from django.contrib.auth import get_user_model
from utilisateurs.models import Utilisateur, GroupeTravail
from proprietes.models import Propriete, Bailleur, Locataire
from contrats.models import Contrat
from paiements.models import Paiement, Retrait, Recu
from contrats.models import Quittance

Utilisateur = get_user_model()

def nettoyer_base_agressif():
    """Nettoyage agressif de toutes les données de test"""
    
    print("🧹 NETTOYAGE AGRESSIF DE LA BASE DE DONNÉES")
    print("=" * 60)
    
    with transaction.atomic():
        print("\n🔍 Recherche de toutes les données de test...")
        
        # 1. Supprimer les utilisateurs de test
        print("\n👥 Suppression des utilisateurs de test...")
        utilisateurs_test = Utilisateur.objects.filter(
            username__startswith='test_'
        ).exclude(
            username='admin'
        )
        count_utilisateurs = utilisateurs_test.count()
        if count_utilisateurs > 0:
            utilisateurs_test.delete()
            print(f"   ✅ {count_utilisateurs} utilisateurs de test supprimés")
        else:
            print("   ℹ️ Aucun utilisateur de test trouvé")
        
        # 2. Suppression directe en base pour éviter les contraintes
        print("\n🗄️ Suppression directe en base de données...")
        
        with connection.cursor() as cursor:
            # Supprimer les propriétés de test
            cursor.execute("""
                DELETE FROM proprietes_propriete 
                WHERE adresse LIKE '%test%' OR adresse LIKE '%Test%'
            """)
            count_prop = cursor.rowcount
            print(f"   ✅ {count_prop} propriétés de test supprimées en base")
            
            # Supprimer les contrats de test
            cursor.execute("""
                DELETE FROM contrats_contrat 
                WHERE id IN (
                    SELECT c.id FROM contrats_contrat c
                    JOIN proprietes_propriete p ON c.propriete_id = p.id
                    WHERE p.adresse LIKE '%test%' OR p.adresse LIKE '%Test%'
                )
            """)
            count_contrats = cursor.rowcount
            print(f"   ✅ {count_contrats} contrats de test supprimés en base")
            
            # Supprimer les paiements de test
            cursor.execute("""
                DELETE FROM paiements_paiement 
                WHERE id IN (
                    SELECT p.id FROM paiements_paiement p
                    JOIN contrats_contrat c ON p.contrat_id = c.id
                    JOIN proprietes_propriete prop ON c.propriete_id = prop.id
                    WHERE prop.adresse LIKE '%test%' OR prop.adresse LIKE '%Test%'
                )
            """)
            count_paiements = cursor.rowcount
            print(f"   ✅ {count_paiements} paiements de test supprimés en base")
            
            # Supprimer les reçus de test
            cursor.execute("""
                DELETE FROM paiements_recu 
                WHERE id IN (
                    SELECT r.id FROM paiements_recu r
                    JOIN paiements_paiement p ON r.paiement_id = p.id
                    JOIN contrats_contrat c ON p.contrat_id = c.id
                    JOIN proprietes_propriete prop ON c.propriete_id = prop.id
                    WHERE prop.adresse LIKE '%test%' OR prop.adresse LIKE '%Test%'
                )
            """)
            count_recus = cursor.rowcount
            print(f"   ✅ {count_recus} reçus de test supprimés en base")
            
            # Supprimer les quittances de test
            cursor.execute("""
                DELETE FROM contrats_quittance 
                WHERE id IN (
                    SELECT q.id FROM contrats_quittance q
                    JOIN contrats_contrat c ON q.contrat_id = c.id
                    JOIN proprietes_propriete p ON c.propriete_id = p.id
                    WHERE p.adresse LIKE '%test%' OR p.adresse LIKE '%Test%'
                )
            """)
            count_quittances = cursor.rowcount
            print(f"   ✅ {count_quittances} quittances de test supprimées en base")
            
            # Supprimer les charges déductibles de test
            try:
                cursor.execute("""
                    DELETE FROM paiements_chargedeductible 
                    WHERE id IN (
                        SELECT cd.id FROM paiements_chargedeductible cd
                        JOIN contrats_contrat c ON cd.contrat_id = c.id
                        JOIN proprietes_propriete p ON c.propriete_id = p.id
                        WHERE p.adresse LIKE '%test%' OR p.adresse LIKE '%Test%'
                    )
                """)
                count_charges = cursor.rowcount
                print(f"   ✅ {count_charges} charges déductibles de test supprimées en base")
            except Exception as e:
                print(f"   ℹ️ Table charges déductibles non disponible: {e}")
            
            # Maintenant supprimer les bailleurs de test
            cursor.execute("""
                DELETE FROM proprietes_bailleur 
                WHERE nom LIKE '%test%' OR nom LIKE '%Test%'
            """)
            count_bailleurs = cursor.rowcount
            print(f"   ✅ {count_bailleurs} bailleurs de test supprimés en base")
            
            # Supprimer les locataires de test
            cursor.execute("""
                DELETE FROM proprietes_locataire 
                WHERE nom LIKE '%test%' OR nom LIKE '%Test%'
            """)
            count_locataires = cursor.rowcount
            print(f"   ✅ {count_locataires} locataires de test supprimés en base")
        
        print("\n✅ Nettoyage agressif terminé !")

def verifier_nettoyage():
    """Vérifie que le nettoyage a bien fonctionné"""
    
    print("\n🔍 VÉRIFICATION DU NETTOYAGE")
    print("=" * 60)
    
    # Vérifier les données restantes
    proprietes_test = Propriete.objects.filter(
        adresse__icontains='test'
    )
    bailleurs_test = Bailleur.objects.filter(
        nom__icontains='test'
    )
    locataires_test = Locataire.objects.filter(
        nom__icontains='test'
    )
    contrats_test = Contrat.objects.filter(
        propriete__adresse__icontains='test'
    )
    paiements_test = Paiement.objects.filter(
        contrat__propriete__adresse__icontains='test'
    )
    
    print(f"   Propriétés de test restantes: {proprietes_test.count()}")
    print(f"   Bailleurs de test restants: {bailleurs_test.count()}")
    print(f"   Locataires de test restants: {locataires_test.count()}")
    print(f"   Contrats de test restants: {contrats_test.count()}")
    print(f"   Paiements de test restants: {paiements_test.count()}")
    
    if (proprietes_test.count() == 0 and 
        bailleurs_test.count() == 0 and 
        locataires_test.count() == 0 and 
        contrats_test.count() == 0 and 
        paiements_test.count() == 0):
        print("\n✅ Toutes les données de test ont été supprimées !")
        return True
    else:
        print("\n⚠️  Il reste encore des données de test")
        return False

def main():
    """Fonction principale"""
    
    print("🧹 NETTOYAGE AGRESSIF DE LA BASE DE DONNÉES")
    print("=" * 80)
    
    try:
        # 1. Nettoyage agressif
        nettoyer_base_agressif()
        
        # 2. Vérification
        verifier_nettoyage()
        
        print("\n🎉 Nettoyage terminé avec succès !")
        
    except Exception as e:
        print(f"\n❌ ERREUR LORS DU NETTOYAGE: {e}")
        return False
    
    return True

if __name__ == "__main__":
    main()
