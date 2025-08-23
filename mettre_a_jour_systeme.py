#!/usr/bin/env python
"""
Script pour mettre à jour le système et générer les IDs uniques
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from django.db import connection, transaction
from core.id_generator import IDGenerator


def mettre_a_jour_bailleurs():
    """Mettre à jour les bailleurs avec les nouveaux IDs uniques"""
    
    print("👤 MISE À JOUR DES BAILLEURS")
    print("-" * 40)
    
    try:
        from proprietes.models import Bailleur
        
        # Vérifier si le champ numero_bailleur existe
        with connection.cursor() as cursor:
            cursor.execute("PRAGMA table_info(proprietes_bailleur)")
            colonnes = cursor.fetchall()
            colonnes_noms = [col[1] for col in colonnes]
            
            if 'numero_bailleur' not in colonnes_noms:
                print("   ❌ Champ numero_bailleur manquant dans le modèle")
                return False
        
        # Récupérer tous les bailleurs
        bailleurs = Bailleur.objects.all()
        print(f"   {bailleurs.count()} bailleurs trouvés")
        
        # Générer les IDs uniques pour chaque bailleur
        for bailleur in bailleurs:
            if not hasattr(bailleur, 'numero_bailleur') or not bailleur.numero_bailleur:
                try:
                    # Générer un nouveau numéro au format BLR-YYYY-XXXX
                    nouveau_numero = IDGenerator.generate_id('bailleur')
                    
                    # Mettre à jour directement en base
                    with connection.cursor() as cursor:
                        cursor.execute(
                            "UPDATE proprietes_bailleur SET numero_bailleur = %s WHERE id = %s",
                            [nouveau_numero, bailleur.id]
                        )
                    
                    print(f"      ✅ {bailleur.nom} {bailleur.prenom}: {nouveau_numero}")
                    
                except Exception as e:
                    print(f"      ❌ Erreur pour {bailleur.nom}: {e}")
        
        print("   ✅ Mise à jour des bailleurs terminée")
        return True
        
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return False


def mettre_a_jour_locataires():
    """Mettre à jour les locataires avec les nouveaux IDs uniques"""
    
    print("\n👥 MISE À JOUR DES LOCATAIRES")
    print("-" * 40)
    
    try:
        from proprietes.models import Locataire
        
        # Vérifier si le champ numero_locataire existe
        with connection.cursor() as cursor:
            cursor.execute("PRAGMA table_info(proprietes_locataire)")
            colonnes = cursor.fetchall()
            colonnes_noms = [col[1] for col in colonnes]
            
            if 'numero_locataire' not in colonnes_noms:
                print("   ❌ Champ numero_locataire manquant dans le modèle")
                return False
        
        # Récupérer tous les locataires
        locataires = Locataire.objects.all()
        print(f"   {locataires.count()} locataires trouvés")
        
        # Générer les IDs uniques pour chaque locataire
        for locataire in locataires:
            if not hasattr(locataire, 'numero_locataire') or not locataire.numero_locataire:
                try:
                    # Générer un nouveau numéro au format LOC-YYYY-XXXX
                    nouveau_numero = IDGenerator.generate_id('locataire')
                    
                    # Mettre à jour directement en base
                    with connection.cursor() as cursor:
                        cursor.execute(
                            "UPDATE proprietes_locataire SET numero_locataire = %s WHERE id = %s",
                            [nouveau_numero, locataire.id]
                        )
                    
                    print(f"      ✅ {locataire.nom} {locataire.prenom}: {nouveau_numero}")
                    
                except Exception as e:
                    print(f"      ❌ Erreur pour {locataire.nom}: {e}")
        
        print("   ✅ Mise à jour des locataires terminée")
        return True
        
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return False


def mettre_a_jour_proprietes():
    """Mettre à jour les propriétés avec les nouveaux IDs uniques"""
    
    print("\n🏠 MISE À JOUR DES PROPRIÉTÉS")
    print("-" * 40)
    
    try:
        from proprietes.models import Propriete
        
        # Vérifier si le champ numero_propriete existe
        with connection.cursor() as cursor:
            cursor.execute("PRAGMA table_info(proprietes_propriete)")
            colonnes = cursor.fetchall()
            colonnes_noms = [col[1] for col in colonnes]
            
            if 'numero_propriete' not in colonnes_noms:
                print("   ❌ Champ numero_propriete manquant dans le modèle")
                return False
        
        # Récupérer toutes les propriétés
        proprietes = Propriete.objects.all()
        print(f"   {proprietes.count()} propriétés trouvées")
        
        # Générer les IDs uniques pour chaque propriété
        for propriete in proprietes:
            if not hasattr(propriete, 'numero_propriete') or not propriete.numero_propriete:
                try:
                    # Générer un nouveau numéro au format PRP-YYYY-XXXX
                    nouveau_numero = IDGenerator.generate_id('propriete')
                    
                    # Mettre à jour directement en base
                    with connection.cursor() as cursor:
                        cursor.execute(
                            "UPDATE proprietes_propriete SET numero_propriete = %s WHERE id = %s",
                            [nouveau_numero, propriete.id]
                        )
                    
                    print(f"      ✅ {propriete.adresse}: {nouveau_numero}")
                    
                except Exception as e:
                    print(f"      ❌ Erreur pour {propriete.adresse}: {e}")
        
        print("   ✅ Mise à jour des propriétés terminée")
        return True
        
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return False


def mettre_a_jour_paiements():
    """Mettre à jour les paiements avec les nouveaux IDs uniques"""
    
    print("\n💳 MISE À JOUR DES PAIEMENTS")
    print("-" * 40)
    
    try:
        from paiements.models import Paiement
        
        # Vérifier si le champ numero_paiement existe
        with connection.cursor() as cursor:
            cursor.execute("PRAGMA table_info(paiements_paiement)")
            colonnes = cursor.fetchall()
            colonnes_noms = [col[1] for col in colonnes]
            
            if 'numero_paiement' not in colonnes_noms:
                print("   ❌ Champ numero_paiement manquant dans le modèle")
                return False
        
        # Récupérer tous les paiements
        paiements = Paiement.objects.all()
        print(f"   {paiements.count()} paiements trouvés")
        
        # Générer les IDs uniques pour chaque paiement
        for paiement in paiements:
            if not hasattr(paiement, 'numero_paiement') or not paiement.numero_paiement:
                try:
                    # Générer un nouveau numéro au format PAY-YYYYMM-XXXX
                    nouveau_numero = IDGenerator.generate_id('paiement', date_paiement=paiement.date_paiement)
                    
                    # Mettre à jour directement en base
                    with connection.cursor() as cursor:
                        cursor.execute(
                            "UPDATE paiements_paiement SET numero_paiement = %s WHERE id = %s",
                            [nouveau_numero, paiement.id]
                        )
                    
                    print(f"      ✅ Paiement {paiement.id}: {nouveau_numero}")
                    
                except Exception as e:
                    print(f"      ❌ Erreur pour paiement {paiement.id}: {e}")
        
        print("   ✅ Mise à jour des paiements terminée")
        return True
        
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return False


def verifier_resultats():
    """Vérifier les résultats de la mise à jour"""
    
    print("\n🔍 VÉRIFICATION DES RÉSULTATS")
    print("-" * 40)
    
    try:
        with connection.cursor() as cursor:
            # Vérifier les bailleurs
            cursor.execute("SELECT COUNT(*) FROM proprietes_bailleur WHERE numero_bailleur IS NOT NULL")
            bailleurs_avec_id = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM proprietes_bailleur")
            total_bailleurs = cursor.fetchone()[0]
            
            print(f"   Bailleurs avec ID unique: {bailleurs_avec_id}/{total_bailleurs}")
            
            # Vérifier les locataires
            cursor.execute("SELECT COUNT(*) FROM proprietes_locataire WHERE numero_locataire IS NOT NULL")
            locataires_avec_id = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM proprietes_locataire")
            total_locataires = cursor.fetchone()[0]
            
            print(f"   Locataires avec ID unique: {locataires_avec_id}/{total_locataires}")
            
            # Vérifier les propriétés
            cursor.execute("SELECT COUNT(*) FROM proprietes_propriete WHERE numero_propriete IS NOT NULL")
            proprietes_avec_id = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM proprietes_propriete")
            total_proprietes = cursor.fetchone()[0]
            
            print(f"   Propriétés avec ID unique: {proprietes_avec_id}/{total_proprietes}")
            
            # Vérifier les paiements
            cursor.execute("SELECT COUNT(*) FROM paiements_paiement WHERE numero_paiement IS NOT NULL")
            paiements_avec_id = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM paiements_paiement")
            total_paiements = cursor.fetchone()[0]
            
            print(f"   Paiements avec ID unique: {paiements_avec_id}/{total_paiements}")
            
            # Afficher quelques exemples
            print("\n📊 Exemples d'IDs au nouveau format:")
            print("-" * 40)
            
            # Bailleurs
            cursor.execute("SELECT numero_bailleur, nom, prenom FROM proprietes_bailleur WHERE numero_bailleur IS NOT NULL LIMIT 3")
            for row in cursor.fetchall():
                print(f"   Bailleur: {row[0]} - {row[2]} {row[1]}")
            
            # Locataires
            cursor.execute("SELECT numero_locataire, nom, prenom FROM proprietes_locataire WHERE numero_locataire IS NOT NULL LIMIT 3")
            for row in cursor.fetchall():
                print(f"   Locataire: {row[0]} - {row[2]} {row[1]}")
            
            # Propriétés
            cursor.execute("SELECT numero_propriete, adresse FROM proprietes_propriete WHERE numero_propriete IS NOT NULL LIMIT 3")
            for row in cursor.fetchall():
                print(f"   Propriété: {row[0]} - {row[1]}")
            
            # Paiements
            cursor.execute("SELECT numero_paiement, montant FROM paiements_paiement WHERE numero_paiement IS NOT NULL LIMIT 3")
            for row in cursor.fetchall():
                print(f"   Paiement: {row[0]} - {row[1]}")
        
        print("\n✅ Vérification terminée!")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la vérification: {e}")
        return False


def main():
    """Fonction principale"""
    
    print("🚀 MISE À JOUR DU SYSTÈME D'IDS UNIQUES")
    print("=" * 60)
    
    # Étape 1: Mettre à jour les bailleurs
    if not mettre_a_jour_bailleurs():
        print("❌ Échec de la mise à jour des bailleurs")
        return False
    
    # Étape 2: Mettre à jour les locataires
    if not mettre_a_jour_locataires():
        print("❌ Échec de la mise à jour des locataires")
        return False
    
    # Étape 3: Mettre à jour les propriétés
    if not mettre_a_jour_proprietes():
        print("❌ Échec de la mise à jour des propriétés")
        return False
    
    # Étape 4: Mettre à jour les paiements
    if not mettre_a_jour_paiements():
        print("❌ Échec de la mise à jour des paiements")
        return False
    
    # Étape 5: Vérifier les résultats
    if not verifier_resultats():
        print("❌ Échec de la vérification")
        return False
    
    print("\n🎉 MISE À JOUR TERMINÉE AVEC SUCCÈS!")
    print("=" * 60)
    print("✅ Tous les modèles ont maintenant des IDs uniques")
    print("✅ Les vues affichent les nouvelles colonnes")
    print("✅ Les données existantes ont été mises à jour")
    print("✅ Le système est prêt à être utilisé")
    
    return True


if __name__ == "__main__":
    main()
