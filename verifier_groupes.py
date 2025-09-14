#!/usr/bin/env python
"""
Script pour vérifier et corriger les groupes de travail sur Render
"""

import os
import django

# Configuration Django pour Render
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from utilisateurs.models import GroupeTravail

def verifier_et_corriger_groupes():
    """Vérifie et corrige les groupes de travail"""
    print("🔍 Vérification des groupes de travail...")
    print("=" * 50)
    
    # Vérifier l'état actuel
    groupes_existants = GroupeTravail.objects.all()
    print(f"📊 Groupes existants: {groupes_existants.count()}")
    
    for groupe in groupes_existants:
        print(f"   - {groupe.nom}: {'✅ Actif' if groupe.actif else '❌ Inactif'}")
    
    # Groupes requis
    groupes_requis = [
        {'nom': 'CAISSE', 'description': 'Gestion des paiements et retraits'},
        {'nom': 'CONTROLES', 'description': 'Contrôle et audit'},
        {'nom': 'ADMINISTRATION', 'description': 'Gestion administrative'},
        {'nom': 'PRIVILEGE', 'description': 'Accès complet'},
    ]
    
    print(f"\n🔧 Correction des groupes...")
    groupes_corriges = 0
    
    for groupe_data in groupes_requis:
        groupe, created = GroupeTravail.objects.get_or_create(
            nom=groupe_data['nom'],
            defaults={
                'description': groupe_data['description'],
                'actif': True,
                'permissions': {}
            }
        )
        
        if created:
            print(f"✅ Créé: {groupe.nom}")
            groupes_corriges += 1
        else:
            # Réactiver le groupe s'il était inactif
            if not groupe.actif:
                groupe.actif = True
                groupe.save()
                print(f"🔄 Réactivé: {groupe.nom}")
                groupes_corriges += 1
            else:
                print(f"ℹ️  OK: {groupe.nom}")
    
    print("=" * 50)
    print(f"📊 Résultat final:")
    print(f"   - Groupes corrigés: {groupes_corriges}")
    print(f"   - Total actifs: {GroupeTravail.objects.filter(actif=True).count()}")
    
    # Afficher tous les groupes actifs
    print(f"\n📋 Groupes actifs disponibles:")
    for groupe in GroupeTravail.objects.filter(actif=True).order_by('nom'):
        print(f"   - {groupe.nom}: {groupe.description}")
    
    return groupes_corriges > 0

if __name__ == '__main__':
    try:
        success = verifier_et_corriger_groupes()
        if success:
            print(f"\n🎉 SUCCÈS ! Les groupes de travail sont maintenant disponibles.")
        else:
            print(f"\n✅ Les groupes de travail étaient déjà corrects.")
        print(f"\n🌐 Rechargez votre page de connexion pour voir les groupes !")
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
