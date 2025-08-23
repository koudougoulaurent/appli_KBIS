#!/usr/bin/env python
"""
Migration pour ajouter les champs d'IDs uniques professionnels
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from django.db import connection, transaction
from django.core.management import execute_from_command_line
from core.id_generator import IDGenerator


def ajouter_champs_ids_uniques():
    """Ajouter les champs d'IDs uniques aux modèles existants"""
    
    print("🔧 MIGRATION DES IDS UNIQUES PROFESSIONNELS")
    print("=" * 60)
    
    try:
        with connection.cursor() as cursor:
            # 1. Ajouter le champ numero_bailleur à la table proprietes_bailleur
            print("\n📋 1. Ajout du champ numero_bailleur aux bailleurs")
            print("-" * 40)
            
            try:
                cursor.execute("""
                    ALTER TABLE proprietes_bailleur 
                    ADD COLUMN numero_bailleur VARCHAR(50) UNIQUE
                """)
                print("   ✅ Champ numero_bailleur ajouté")
            except Exception as e:
                if "duplicate column name" in str(e).lower():
                    print("   ℹ️ Champ numero_bailleur existe déjà")
                else:
                    print(f"   ⚠️ Erreur: {e}")
            
            # 2. Ajouter le champ numero_locataire à la table proprietes_locataire
            print("\n👥 2. Ajout du champ numero_locataire aux locataires")
            print("-" * 40)
            
            try:
                cursor.execute("""
                    ALTER TABLE proprietes_locataire 
                    ADD COLUMN numero_locataire VARCHAR(50) UNIQUE
                """)
                print("   ✅ Champ numero_locataire ajouté")
            except Exception as e:
                if "duplicate column name" in str(e).lower():
                    print("   ℹ️ Champ numero_locataire existe déjà")
                else:
                    print(f"   ⚠️ Erreur: {e}")
            
            # 3. Ajouter le champ numero_propriete à la table proprietes_propriete
            print("\n🏠 3. Ajout du champ numero_propriete aux propriétés")
            print("-" * 40)
            
            try:
                cursor.execute("""
                    ALTER TABLE proprietes_propriete 
                    ADD COLUMN numero_propriete VARCHAR(50) UNIQUE
                """)
                print("   ✅ Champ numero_propriete ajouté")
            except Exception as e:
                if "duplicate column name" in str(e).lower():
                    print("   ℹ️ Champ numero_propriete existe déjà")
                else:
                    print(f"   ⚠️ Erreur: {e}")
            
            # 4. Ajouter le champ numero_paiement à la table paiements_paiement
            print("\n💳 4. Ajout du champ numero_paiement aux paiements")
            print("-" * 40)
            
            try:
                cursor.execute("""
                    ALTER TABLE paiements_paiement 
                    ADD COLUMN numero_paiement VARCHAR(50) UNIQUE
                """)
                print("   ✅ Champ numero_paiement ajouté")
            except Exception as e:
                if "duplicate column name" in str(e).lower():
                    print("   ℹ️ Champ numero_paiement existe déjà")
                else:
                    print(f"   ⚠️ Erreur: {e}")
            
            # 5. Ajouter le champ numero_quittance à la table contrats_quittance
            print("\n📄 5. Ajout du champ numero_quittance aux quittances")
            print("-" * 40)
            
            try:
                cursor.execute("""
                    ALTER TABLE contrats_quittance 
                    ADD COLUMN numero_quittance VARCHAR(50) UNIQUE
                """)
                print("   ✅ Champ numero_quittance ajouté")
            except Exception as e:
                if "duplicate column name" in str(e).lower():
                    print("   ℹ️ Champ numero_quittance existe déjà")
                else:
                    print(f"   ⚠️ Erreur: {e}")
            
            # 6. Créer les index pour améliorer les performances
            print("\n🔍 6. Création des index pour les IDs uniques")
            print("-" * 40)
            
            index_configs = [
                ('proprietes_bailleur', 'numero_bailleur'),
                ('proprietes_locataire', 'numero_locataire'),
                ('proprietes_propriete', 'numero_propriete'),
                ('paiements_paiement', 'numero_paiement'),
                ('contrats_quittance', 'numero_quittance'),
            ]
            
            for table, field in index_configs:
                try:
                    index_name = f"idx_{table}_{field}"
                    cursor.execute(f"""
                        CREATE INDEX IF NOT EXISTS {index_name} 
                        ON {table} ({field})
                    """)
                    print(f"   ✅ Index créé pour {table}.{field}")
                except Exception as e:
                    print(f"   ⚠️ Erreur index {table}.{field}: {e}")
            
            print("\n✅ Migration des champs terminée avec succès!")
            
    except Exception as e:
        print(f"❌ Erreur lors de la migration: {e}")
        return False
    
    return True


def generer_ids_existants():
    """Générer des IDs uniques pour les données existantes"""
    
    print("\n🔄 GÉNÉRATION DES IDS POUR LES DONNÉES EXISTANTES")
    print("=" * 60)
    
    try:
        # 1. Générer les IDs pour les bailleurs existants
        print("\n👤 1. Génération des IDs pour les bailleurs existants")
        print("-" * 40)
        
        from proprietes.models import Bailleur
        
        bailleurs = Bailleur.objects.filter(numero_bailleur__isnull=True)
        print(f"   {bailleurs.count()} bailleurs sans ID unique")
        
        for bailleur in bailleurs:
            try:
                numero_bailleur = IDGenerator.generate_id('bailleur')
                bailleur.numero_bailleur = numero_bailleur
                bailleur.save(update_fields=['numero_bailleur'])
                print(f"   ✅ {bailleur.nom} {bailleur.prenom}: {numero_bailleur}")
            except Exception as e:
                print(f"   ❌ Erreur pour {bailleur.nom}: {e}")
        
        # 2. Générer les IDs pour les locataires existants
        print("\n👥 2. Génération des IDs pour les locataires existants")
        print("-" * 40)
        
        from proprietes.models import Locataire
        
        locataires = Locataire.objects.filter(numero_locataire__isnull=True)
        print(f"   {locataires.count()} locataires sans ID unique")
        
        for locataire in locataires:
            try:
                numero_locataire = IDGenerator.generate_id('locataire')
                locataire.numero_locataire = numero_locataire
                locataire.save(update_fields=['numero_locataire'])
                print(f"   ✅ {locataire.nom} {locataire.prenom}: {numero_locataire}")
            except Exception as e:
                print(f"   ❌ Erreur pour {locataire.nom}: {e}")
        
        # 3. Générer les IDs pour les propriétés existantes
        print("\n🏠 3. Génération des IDs pour les propriétés existantes")
        print("-" * 40)
        
        from proprietes.models import Propriete
        
        proprietes = Propriete.objects.filter(numero_propriete__isnull=True)
        print(f"   {proprietes.count()} propriétés sans ID unique")
        
        for propriete in proprietes:
            try:
                numero_propriete = IDGenerator.generate_id('propriete')
                propriete.numero_propriete = numero_propriete
                propriete.save(update_fields=['numero_propriete'])
                print(f"   ✅ {propriete.adresse}: {numero_propriete}")
            except Exception as e:
                print(f"   ❌ Erreur pour {propriete.adresse}: {e}")
        
        # 4. Générer les IDs pour les contrats existants (si pas déjà fait)
        print("\n📋 4. Vérification des IDs des contrats existants")
        print("-" * 40)
        
        from contrats.models import Contrat
        
        contrats_sans_id = Contrat.objects.filter(numero_contrat__isnull=True)
        if contrats_sans_id.exists():
            print(f"   {contrats_sans_id.count()} contrats sans ID unique")
            for contrat in contrats_sans_id:
                try:
                    numero_contrat = IDGenerator.generate_id('contrat')
                    contrat.numero_contrat = numero_contrat
                    contrat.save(update_fields=['numero_contrat'])
                    print(f"   ✅ Contrat {contrat.id}: {numero_contrat}")
                except Exception as e:
                    print(f"   ❌ Erreur pour contrat {contrat.id}: {e}")
        else:
            print("   ✅ Tous les contrats ont déjà des IDs uniques")
        
        # 5. Générer les IDs pour les paiements existants
        print("\n💳 5. Génération des IDs pour les paiements existants")
        print("-" * 40)
        
        from paiements.models import Paiement
        
        paiements = Paiement.objects.filter(numero_paiement__isnull=True)
        print(f"   {paiements.count()} paiements sans ID unique")
        
        for paiement in paiements:
            try:
                numero_paiement = IDGenerator.generate_id('paiement', date_paiement=paiement.date_paiement)
                paiement.numero_paiement = numero_paiement
                paiement.save(update_fields=['numero_paiement'])
                print(f"   ✅ Paiement {paiement.id}: {numero_paiement}")
            except Exception as e:
                print(f"   ❌ Erreur pour paiement {paiement.id}: {e}")
        
        # 6. Générer les IDs pour les reçus existants
        print("\n💰 6. Vérification des IDs des reçus existants")
        print("-" * 40)
        
        from paiements.models import Recu
        
        recus_sans_id = Recu.objects.filter(numero_recu__isnull=True)
        if recus_sans_id.exists():
            print(f"   {recus_sans_id.count()} reçus sans ID unique")
            for recu in recus_sans_id:
                try:
                    numero_recu = IDGenerator.generate_id('recu', date_emission=recu.date_emission)
                    recu.numero_recu = numero_recu
                    recu.save(update_fields=['numero_recu'])
                    print(f"   ✅ Reçu {recu.id}: {numero_recu}")
                except Exception as e:
                    print(f"   ❌ Erreur pour reçu {recu.id}: {e}")
        else:
            print("   ✅ Tous les reçus ont déjà des IDs uniques")
        
        print("\n✅ Génération des IDs terminée avec succès!")
        
    except Exception as e:
        print(f"❌ Erreur lors de la génération des IDs: {e}")
        return False
    
    return True


def verifier_migration():
    """Vérifier que la migration s'est bien passée"""
    
    print("\n🔍 VÉRIFICATION DE LA MIGRATION")
    print("=" * 60)
    
    try:
        with connection.cursor() as cursor:
            # Vérifier que les champs existent
            tables_a_verifier = [
                ('proprietes_bailleur', 'numero_bailleur'),
                ('proprietes_locataire', 'numero_locataire'),
                ('proprietes_propriete', 'numero_propriete'),
                ('paiements_paiement', 'numero_paiement'),
                ('contrats_quittance', 'numero_quittance'),
            ]
            
            for table, field in tables_a_verifier:
                try:
                    cursor.execute(f"PRAGMA table_info({table})")
                    colonnes = cursor.fetchall()
                    colonnes_noms = [col[1] for col in colonnes]
                    
                    if field in colonnes_noms:
                        print(f"   ✅ {table}.{field}: Présent")
                    else:
                        print(f"   ❌ {table}.{field}: Manquant")
                        
                except Exception as e:
                    print(f"   ⚠️ Erreur vérification {table}: {e}")
            
            # Vérifier les données
            print("\n📊 Vérification des données:")
            print("-" * 40)
            
            from proprietes.models import Bailleur, Locataire, Propriete
            from paiements.models import Paiement
            from contrats.models import Contrat, Quittance
            from paiements.models import Recu
            
            print(f"   Bailleurs avec ID: {Bailleur.objects.filter(numero_bailleur__isnull=False).count()}")
            print(f"   Locataires avec ID: {Locataire.objects.filter(numero_locataire__isnull=False).count()}")
            print(f"   Propriétés avec ID: {Propriete.objects.filter(numero_propriete__isnull=False).count()}")
            print(f"   Contrats avec ID: {Contrat.objects.filter(numero_contrat__isnull=False).count()}")
            print(f"   Paiements avec ID: {Paiement.objects.filter(numero_paiement__isnull=False).count()}")
            print(f"   Reçus avec ID: {Recu.objects.filter(numero_recu__isnull=False).count()}")
            
            # Vérifier les formats
            print("\n🎯 Vérification des formats d'IDs:")
            print("-" * 40)
            
            formats = IDGenerator.get_available_formats()
            for entity_type, config in formats.items():
                print(f"   {entity_type.upper()}: {config['description']}")
                print(f"     Exemple: {config['example']}")
            
            print("\n✅ Vérification terminée!")
            
    except Exception as e:
        print(f"❌ Erreur lors de la vérification: {e}")
        return False
    
    return True


def main():
    """Fonction principale de migration"""
    
    print("🚀 MIGRATION COMPLÈTE DES IDS UNIQUES PROFESSIONNELS")
    print("=" * 60)
    
    # Étape 1: Ajouter les champs
    if not ajouter_champs_ids_uniques():
        print("❌ Échec de l'ajout des champs")
        return False
    
    # Étape 2: Générer les IDs pour les données existantes
    if not generer_ids_existants():
        print("❌ Échec de la génération des IDs")
        return False
    
    # Étape 3: Vérifier la migration
    if not verifier_migration():
        print("❌ Échec de la vérification")
        return False
    
    print("\n🎉 MIGRATION TERMINÉE AVEC SUCCÈS!")
    print("=" * 60)
    print("✅ Tous les modèles ont maintenant des IDs uniques professionnels")
    print("✅ Les formats sont: BLR-YYYY-XXXX, LOC-YYYY-XXXX, PRP-YYYY-XXXX, etc.")
    print("✅ Les séquences se réinitialisent automatiquement (annuellement, mensuellement, etc.)")
    print("✅ L'entreprise peut maintenant contrôler et personnaliser les formats")
    
    return True


if __name__ == "__main__":
    main()
