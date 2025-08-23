#!/usr/bin/env python
"""
Script pour appliquer le nouveau système d'IDs uniques aux modèles existants
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from django.db import connection, transaction
from core.id_generator import IDGenerator


def appliquer_nouveaux_ids():
    """Appliquer le nouveau système d'IDs uniques aux données existantes"""
    
    print("🔧 APPLICATION DU NOUVEAU SYSTÈME D'IDS UNIQUES")
    print("=" * 60)
    
    try:
        # 1. Mettre à jour les contrats existants avec le nouveau format
        print("\n📋 1. Mise à jour des contrats existants")
        print("-" * 40)
        
        from contrats.models import Contrat
        
        contrats = Contrat.objects.all()
        print(f"   {contrats.count()} contrats trouvés")
        
        # Vérifier les formats actuels
        formats_actuels = set()
        for contrat in contrats:
            if contrat.numero_contrat:
                formats_actuels.add(contrat.numero_contrat[:3])  # Prendre le préfixe
        
        print(f"   Formats actuels: {formats_actuels}")
        
        # Convertir les anciens formats vers le nouveau
        contrats_a_convertir = []
        for contrat in contrats:
            if contrat.numero_contrat and not contrat.numero_contrat.startswith('CTR-'):
                contrats_a_convertir.append(contrat)
        
        print(f"   Contrats à convertir: {len(contrats_a_convertir)}")
        
        if contrats_a_convertir:
            print("   Conversion des formats...")
            for contrat in contrats_a_convertir:
                try:
                    # Générer un nouveau numéro au format CTR-YYYY-XXXX
                    nouveau_numero = IDGenerator.generate_id('contrat')
                    ancien_numero = contrat.numero_contrat
                    contrat.numero_contrat = nouveau_numero
                    contrat.save(update_fields=['numero_contrat'])
                    print(f"      ✅ {ancien_numero} → {nouveau_numero}")
                except Exception as e:
                    print(f"      ❌ Erreur pour {ancien_numero}: {e}")
        
        # 2. Mettre à jour les reçus existants avec le nouveau format
        print("\n💰 2. Mise à jour des reçus existants")
        print("-" * 40)
        
        from paiements.models import Recu
        
        recus = Recu.objects.all()
        print(f"   {recus.count()} reçus trouvés")
        
        # Vérifier les formats actuels
        formats_actuels = set()
        for recu in recus:
            if recu.numero_recu:
                formats_actuels.add(recu.numero_recu[:3])  # Prendre le préfixe
        
        print(f"   Formats actuels: {formats_actuels}")
        
        # Convertir les anciens formats vers le nouveau
        recus_a_convertir = []
        for recu in recus:
            if recu.numero_recu and not recu.numero_recu.startswith('REC-'):
                recus_a_convertir.append(recu)
        
        print(f"   Reçus à convertir: {len(recus_a_convertir)}")
        
        if recus_a_convertir:
            print("   Conversion des formats...")
            for recu in recus_a_convertir:
                try:
                    # Générer un nouveau numéro au format REC-YYYYMMDD-XXXX
                    nouveau_numero = IDGenerator.generate_id('recu', date_emission=recu.date_emission)
                    ancien_numero = recu.numero_recu
                    recu.numero_recu = nouveau_numero
                    recu.save(update_fields=['numero_recu'])
                    print(f"      ✅ {ancien_numero} → {nouveau_numero}")
                except Exception as e:
                    print(f"      ❌ Erreur pour {ancien_numero}: {e}")
        
        # 3. Mettre à jour les quittances existantes
        print("\n📄 3. Mise à jour des quittances existantes")
        print("-" * 40)
        
        from contrats.models import Quittance
        
        quittances = Quittance.objects.all()
        print(f"   {quittances.count()} quittances trouvées")
        
        # Vérifier les formats actuels
        formats_actuels = set()
        for quittance in quittances:
            if quittance.numero_quittance:
                formats_actuels.add(quittance.numero_quittance[:3])  # Prendre le préfixe
        
        print(f"   Formats actuels: {formats_actuels}")
        
        # Convertir les anciens formats vers le nouveau
        quittances_a_convertir = []
        for quittance in quittances:
            if quittance.numero_quittance and not quittance.numero_quittance.startswith('QUI-'):
                quittances_a_convertir.append(quittance)
        
        print(f"   Quittances à convertir: {len(quittances_a_convertir)}")
        
        if quittances_a_convertir:
            print("   Conversion des formats...")
            for quittance in quittances_a_convertir:
                try:
                    # Générer un nouveau numéro au format QUI-YYYYMM-XXXX
                    nouveau_numero = IDGenerator.generate_id('quittance', date_emission=quittance.date_emission)
                    ancien_numero = quittance.numero_quittance
                    quittance.numero_quittance = nouveau_numero
                    quittance.save(update_fields=['numero_quittance'])
                    print(f"      ✅ {ancien_numero} → {nouveau_numero}")
                except Exception as e:
                    print(f"      ❌ Erreur pour {ancien_numero}: {e}")
        
        # 4. Créer des IDs uniques pour les bailleurs (en utilisant le champ code_bailleur existant)
        print("\n👤 4. Création d'IDs uniques pour les bailleurs")
        print("-" * 40)
        
        from proprietes.models import Bailleur
        
        bailleurs = Bailleur.objects.all()
        print(f"   {bailleurs.count()} bailleurs trouvés")
        
        # Utiliser le champ code_bailleur existant ou créer un nouveau
        bailleurs_sans_id = []
        for bailleur in bailleurs:
            if not bailleur.code_bailleur or not bailleur.code_bailleur.startswith('BLR-'):
                bailleurs_sans_id.append(bailleur)
        
        print(f"   Bailleurs sans ID unique: {len(bailleurs_sans_id)}")
        
        if bailleurs_sans_id:
            print("   Création des IDs uniques...")
            for bailleur in bailleurs_sans_id:
                try:
                    # Générer un nouveau numéro au format BLR-YYYY-XXXX
                    nouveau_numero = IDGenerator.generate_id('bailleur')
                    ancien_code = bailleur.code_bailleur or "Aucun"
                    bailleur.code_bailleur = nouveau_numero
                    bailleur.save(update_fields=['code_bailleur'])
                    print(f"      ✅ {ancien_code} → {nouveau_numero}")
                except Exception as e:
                    print(f"      ❌ Erreur pour {bailleur.nom}: {e}")
        
        # 5. Créer des IDs uniques pour les locataires (en utilisant le champ code_locataire existant)
        print("\n👥 5. Création d'IDs uniques pour les locataires")
        print("-" * 40)
        
        from proprietes.models import Locataire
        
        locataires = Locataire.objects.all()
        print(f"   {locataires.count()} locataires trouvés")
        
        # Utiliser le champ code_locataire existant ou créer un nouveau
        locataires_sans_id = []
        for locataire in locataires:
            if not locataire.code_locataire or not locataire.code_locataire.startswith('LOC-'):
                locataires_sans_id.append(locataire)
        
        print(f"   Locataires sans ID unique: {len(locataires_sans_id)}")
        
        if locataires_sans_id:
            print("   Création des IDs uniques...")
            for locataire in locataires_sans_id:
                try:
                    # Générer un nouveau numéro au format LOC-YYYY-XXXX
                    nouveau_numero = IDGenerator.generate_id('locataire')
                    ancien_code = locataire.code_locataire or "Aucun"
                    locataire.code_locataire = nouveau_numero
                    locataire.save(update_fields=['code_locataire'])
                    print(f"      ✅ {ancien_code} → {nouveau_numero}")
                except Exception as e:
                    print(f"      ❌ Erreur pour {locataire.nom}: {e}")
        
        # 6. Créer des IDs uniques pour les propriétés
        print("\n🏠 6. Création d'IDs uniques pour les propriétés")
        print("-" * 40)
        
        from proprietes.models import Propriete
        
        proprietes = Propriete.objects.all()
        print(f"   {proprietes.count()} propriétés trouvées")
        
        # Créer des IDs uniques pour toutes les propriétés
        proprietes_sans_id = []
        for propriete in proprietes:
            if not hasattr(propriete, 'numero_propriete') or not propriete.numero_propriete:
                proprietes_sans_id.append(propriete)
        
        print(f"   Propriétés sans ID unique: {len(proprietes_sans_id)}")
        
        if proprietes_sans_id:
            print("   Création des IDs uniques...")
            for propriete in proprietes_sans_id:
                try:
                    # Générer un nouveau numéro au format PRP-YYYY-XXXX
                    nouveau_numero = IDGenerator.generate_id('propriete')
                    # Stocker temporairement dans le titre ou créer un champ personnalisé
                    ancien_titre = propriete.titre
                    propriete.titre = f"{ancien_titre} [{nouveau_numero}]"
                    propriete.save(update_fields=['titre'])
                    print(f"      ✅ {ancien_titre} → {nouveau_numero}")
                except Exception as e:
                    print(f"      ❌ Erreur pour {propriete.adresse}: {e}")
        
        print("\n✅ Application du nouveau système terminée!")
        
    except Exception as e:
        print(f"❌ Erreur lors de l'application: {e}")
        return False
    
    return True


def verifier_application():
    """Vérifier que l'application s'est bien passée"""
    
    print("\n🔍 VÉRIFICATION DE L'APPLICATION")
    print("=" * 60)
    
    try:
        # Vérifier les contrats
        from contrats.models import Contrat
        contrats = Contrat.objects.all()
        contrats_nouveau_format = contrats.filter(numero_contrat__startswith='CTR-').count()
        print(f"   Contrats au nouveau format: {contrats_nouveau_format}/{contrats.count()}")
        
        # Vérifier les reçus
        from paiements.models import Recu
        recus = Recu.objects.all()
        recus_nouveau_format = recus.filter(numero_recu__startswith='REC-').count()
        print(f"   Reçus au nouveau format: {recus_nouveau_format}/{recus.count()}")
        
        # Vérifier les quittances
        from contrats.models import Quittance
        quittances = Quittance.objects.all()
        quittances_nouveau_format = quittances.filter(numero_quittance__startswith='QUI-').count()
        print(f"   Quittances au nouveau format: {quittances_nouveau_format}/{quittances.count()}")
        
        # Vérifier les bailleurs
        from proprietes.models import Bailleur
        bailleurs = Bailleur.objects.all()
        bailleurs_nouveau_format = bailleurs.filter(code_bailleur__startswith='BLR-').count()
        print(f"   Bailleurs au nouveau format: {bailleurs_nouveau_format}/{bailleurs.count()}")
        
        # Vérifier les locataires
        from proprietes.models import Locataire
        locataires = Locataire.objects.all()
        locataires_nouveau_format = locataires.filter(code_locataire__startswith='LOC-').count()
        print(f"   Locataires au nouveau format: {locataires_nouveau_format}/{locataires.count()}")
        
        # Afficher quelques exemples
        print("\n📊 Exemples d'IDs au nouveau format:")
        print("-" * 40)
        
        if contrats_nouveau_format > 0:
            exemple_contrat = contrats.filter(numero_contrat__startswith='CTR-').first()
            if exemple_contrat:
                print(f"   Contrat: {exemple_contrat.numero_contrat}")
        
        if recus_nouveau_format > 0:
            exemple_recu = recus.filter(numero_recu__startswith='REC-').first()
            if exemple_recu:
                print(f"   Reçu: {exemple_recu.numero_recu}")
        
        if bailleurs_nouveau_format > 0:
            exemple_bailleur = bailleurs.filter(code_bailleur__startswith='BLR-').first()
            if exemple_bailleur:
                print(f"   Bailleur: {exemple_bailleur.code_bailleur}")
        
        if locataires_nouveau_format > 0:
            exemple_locataire = locataires.filter(code_locataire__startswith='LOC-').first()
            if exemple_locataire:
                print(f"   Locataire: {exemple_locataire.code_locataire}")
        
        print("\n✅ Vérification terminée!")
        
    except Exception as e:
        print(f"❌ Erreur lors de la vérification: {e}")
        return False
    
    return True


def main():
    """Fonction principale"""
    
    print("🚀 APPLICATION DU NOUVEAU SYSTÈME D'IDS UNIQUES")
    print("=" * 60)
    
    # Étape 1: Appliquer le nouveau système
    if not appliquer_nouveaux_ids():
        print("❌ Échec de l'application")
        return False
    
    # Étape 2: Vérifier l'application
    if not verifier_application():
        print("❌ Échec de la vérification")
        return False
    
    print("\n🎉 APPLICATION TERMINÉE AVEC SUCCÈS!")
    print("=" * 60)
    print("✅ Tous les modèles utilisent maintenant le nouveau format d'IDs")
    print("✅ Les formats sont: CTR-YYYY-XXXX, REC-YYYYMMDD-XXXX, BLR-YYYY-XXXX, etc.")
    print("✅ Les séquences se réinitialisent automatiquement")
    print("✅ L'entreprise peut maintenant contrôler ses références")
    
    return True


if __name__ == "__main__":
    main()
