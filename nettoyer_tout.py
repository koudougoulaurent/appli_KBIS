#!/usr/bin/env python
"""
Script de nettoyage simple - Suppression de toutes les données de test
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from django.db import connection

def nettoyer_tout():
    """Supprime toutes les données de test en une seule fois"""
    
    print("🧹 NETTOYAGE COMPLET DE LA BASE DE DONNÉES")
    print("=" * 60)
    
    with connection.cursor() as cursor:
        print("\n🗄️ Suppression de toutes les données de test...")
        
        # Désactiver temporairement les contraintes de clés étrangères
        cursor.execute("PRAGMA foreign_keys=OFF")
        
        try:
            # Supprimer toutes les données de test en une seule fois
            cursor.execute("""
                DELETE FROM proprietes_propriete 
                WHERE adresse LIKE '%test%' OR adresse LIKE '%Test%'
            """)
            count_prop = cursor.rowcount
            print(f"   ✅ {count_prop} propriétés de test supprimées")
            
            cursor.execute("""
                DELETE FROM proprietes_bailleur 
                WHERE nom LIKE '%test%' OR nom LIKE '%Test%'
            """)
            count_bailleur = cursor.rowcount
            print(f"   ✅ {count_bailleur} bailleurs de test supprimés")
            
            cursor.execute("""
                DELETE FROM proprietes_locataire 
                WHERE nom LIKE '%test%' OR nom LIKE '%Test%'
            """)
            count_locataire = cursor.rowcount
            print(f"   ✅ {count_locataire} locataires de test supprimés")
            
            cursor.execute("""
                DELETE FROM utilisateurs_utilisateur 
                WHERE username LIKE 'test_%'
            """)
            count_user = cursor.rowcount
            print(f"   ✅ {count_user} utilisateurs de test supprimés")
            
        finally:
            # Réactiver les contraintes de clés étrangères
            cursor.execute("PRAGMA foreign_keys=ON")
        
        print("\n✅ Nettoyage terminé !")

def verifier_nettoyage():
    """Vérifie que le nettoyage a bien fonctionné"""
    
    print("\n🔍 VÉRIFICATION DU NETTOYAGE")
    print("=" * 60)
    
    with connection.cursor() as cursor:
        # Compter les données restantes
        cursor.execute("SELECT COUNT(*) FROM proprietes_propriete WHERE adresse LIKE '%test%'")
        prop_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM proprietes_bailleur WHERE nom LIKE '%test%'")
        bailleur_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM proprietes_locataire WHERE nom LIKE '%test%'")
        locataire_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM utilisateurs_utilisateur WHERE username LIKE 'test_%'")
        user_count = cursor.fetchone()[0]
        
        print(f"   Propriétés de test restantes: {prop_count}")
        print(f"   Bailleurs de test restants: {bailleur_count}")
        print(f"   Locataires de test restants: {locataire_count}")
        print(f"   Utilisateurs de test restants: {user_count}")
        
        if prop_count == 0 and bailleur_count == 0 and locataire_count == 0 and user_count == 0:
            print("\n✅ Toutes les données de test ont été supprimées !")
            return True
        else:
            print("\n⚠️  Il reste encore des données de test")
            return False

def main():
    """Fonction principale"""
    
    print("🧹 NETTOYAGE COMPLET DE LA BASE DE DONNÉES")
    print("=" * 80)
    
    try:
        # 1. Nettoyage
        nettoyer_tout()
        
        # 2. Vérification
        verifier_nettoyage()
        
        print("\n🎉 Nettoyage terminé avec succès !")
        
    except Exception as e:
        print(f"\n❌ ERREUR LORS DU NETTOYAGE: {e}")
        return False
    
    return True

if __name__ == "__main__":
    main()
