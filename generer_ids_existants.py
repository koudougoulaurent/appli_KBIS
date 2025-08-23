#!/usr/bin/env python
"""
Script pour générer et assigner les nouveaux IDs uniques à toutes les données existantes
"""

import os
import sys
import django
from django.conf import settings

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from proprietes.models import Bailleur, Locataire, Propriete
from paiements.models import Paiement
from core.id_generator import IDGenerator

def generer_ids_existants():
    """Génère et assigne les nouveaux IDs uniques à toutes les données existantes"""
    
    print("🆔 GÉNÉRATION DES IDS UNIQUES POUR LES DONNÉES EXISTANTES")
    print("=" * 70)
    
    generator = IDGenerator()
    
    # 1. Générer les IDs pour les bailleurs
    print("\n👤 GÉNÉRATION DES IDS POUR LES BAİLLEURS")
    print("-" * 50)
    
    bailleurs = Bailleur.objects.all()
    print(f"   {bailleurs.count()} bailleurs trouvés")
    
    for bailleur in bailleurs:
        try:
            if not bailleur.numero_bailleur:
                numero = generator.generate_id('bailleur')
                bailleur.numero_bailleur = numero
                bailleur.save(update_fields=['numero_bailleur'])
                print(f"   ✅ {bailleur.nom} {bailleur.prenom}: {numero}")
            else:
                print(f"   ℹ️  {bailleur.nom} {bailleur.prenom}: {bailleur.numero_bailleur} (déjà présent)")
        except Exception as e:
            print(f"   ❌ Erreur pour {bailleur.nom} {bailleur.prenom}: {e}")
    
    # 2. Générer les IDs pour les locataires
    print("\n🏠 GÉNÉRATION DES IDS POUR LES LOCATAIRES")
    print("-" * 50)
    
    locataires = Locataire.objects.all()
    print(f"   {locataires.count()} locataires trouvés")
    
    for locataire in locataires:
        try:
            if not locataire.numero_locataire:
                numero = generator.generate_id('locataire')
                locataire.numero_locataire = numero
                locataire.save(update_fields=['numero_locataire'])
                print(f"   ✅ {locataire.nom} {locataire.prenom}: {numero}")
            else:
                print(f"   ℹ️  {locataire.nom} {locataire.prenom}: {locataire.numero_locataire} (déjà présent)")
        except Exception as e:
            print(f"   ❌ Erreur pour {locataire.nom} {locataire.prenom}: {e}")
    
    # 3. Générer les IDs pour les propriétés
    print("\n🏘️ GÉNÉRATION DES IDS POUR LES PROPRIÉTÉS")
    print("-" * 50)
    
    proprietes = Propriete.objects.all()
    print(f"   {proprietes.count()} propriétés trouvées")
    
    for propriete in proprietes:
        try:
            if not propriete.numero_propriete:
                numero = generator.generate_id('propriete')
                propriete.numero_propriete = numero
                propriete.save(update_fields=['numero_propriete'])
                print(f"   ✅ {propriete.titre}: {numero}")
            else:
                print(f"   ℹ️  {propriete.titre}: {propriete.numero_propriete} (déjà présent)")
        except Exception as e:
            print(f"   ❌ Erreur pour {propriete.titre}: {e}")
    
    # 4. Générer les IDs pour les paiements
    print("\n💳 GÉNÉRATION DES IDS POUR LES PAIEMENTS")
    print("-" * 50)
    
    paiements = Paiement.objects.all()
    print(f"   {paiements.count()} paiements trouvés")
    
    for paiement in paiements:
        try:
            if not paiement.numero_paiement:
                numero = generator.generate_id('paiement')
                paiement.numero_paiement = numero
                paiement.save(update_fields=['numero_paiement'])
                print(f"   ✅ Paiement {paiement.id}: {numero}")
            else:
                print(f"   ℹ️  Paiement {paiement.id}: {paiement.numero_paiement} (déjà présent)")
        except Exception as e:
            print(f"   ❌ Erreur pour paiement {paiement.id}: {e}")
    
    # 5. Vérification finale
    print("\n🔍 VÉRIFICATION FINALE")
    print("-" * 50)
    
    try:
        # Compter les enregistrements avec des IDs uniques
        bailleurs_avec_id = Bailleur.objects.filter(numero_bailleur__isnull=False).count()
        locataires_avec_id = Locataire.objects.filter(numero_locataire__isnull=False).count()
        proprietes_avec_id = Propriete.objects.filter(numero_propriete__isnull=False).count()
        paiements_avec_id = Paiement.objects.filter(numero_paiement__isnull=False).count()
        
        total_bailleurs = Bailleur.objects.count()
        total_locataires = Locataire.objects.count()
        total_proprietes = Propriete.objects.count()
        total_paiements = Paiement.objects.count()
        
        print(f"   Bailleurs: {bailleurs_avec_id}/{total_bailleurs} avec ID unique")
        print(f"   Locataires: {locataires_avec_id}/{total_locataires} avec ID unique")
        print(f"   Propriétés: {proprietes_avec_id}/{total_proprietes} avec ID unique")
        print(f"   Paiements: {paiements_avec_id}/{total_paiements} avec ID unique")
        
        # Afficher quelques exemples
        print("\n📋 EXEMPLES D'IDS GÉNÉRÉS:")
        print("-" * 30)
        
        bailleur_exemple = Bailleur.objects.filter(numero_bailleur__isnull=False).first()
        if bailleur_exemple:
            print(f"   Bailleur: {bailleur_exemple.numero_bailleur}")
            
        locataire_exemple = Locataire.objects.filter(numero_locataire__isnull=False).first()
        if locataire_exemple:
            print(f"   Locataire: {locataire_exemple.numero_locataire}")
            
        propriete_exemple = Propriete.objects.filter(numero_propriete__isnull=False).first()
        if propriete_exemple:
            print(f"   Propriété: {propriete_exemple.numero_propriete}")
            
        paiement_exemple = Paiement.objects.filter(numero_paiement__isnull=False).first()
        if paiement_exemple:
            print(f"   Paiement: {paiement_exemple.numero_paiement}")
            
    except Exception as e:
        print(f"   ❌ Erreur lors de la vérification finale: {e}")
    
    print("\n" + "=" * 70)
    print("✅ Génération des IDs uniques terminée!")
    print("\n🎯 PROCHAINES ÉTAPES:")
    print("   1. Redémarrer le serveur Django")
    print("   2. Tester l'application dans le navigateur")
    print("   3. Vérifier que les nouveaux IDs sont visibles dans les listes")
    print("   4. Tester la création de nouveaux enregistrements")

if __name__ == '__main__':
    generer_ids_existants()
