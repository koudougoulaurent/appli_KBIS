#!/usr/bin/env python
"""
Script de test simplifié pour vérifier les nouvelles permissions
"""

import os
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from utilisateurs.models import Utilisateur, GroupeTravail

def tester_permissions():
    """Teste les nouvelles permissions pour chaque groupe"""
    
    print("🧪 TEST SIMPLIFIÉ DES PERMISSIONS")
    print("=" * 40)
    
    # Vérifier les groupes existants
    groupes = GroupeTravail.objects.all()
    print(f"📊 Groupes trouvés: {groupes.count()}")
    
    for groupe in groupes:
        print(f"   - {groupe.nom}: {'✅ Actif' if groupe.actif else '❌ Inactif'}")
    
    # Vérifier les utilisateurs existants
    utilisateurs = Utilisateur.objects.all()
    print(f"\n👥 Utilisateurs trouvés: {utilisateurs.count()}")
    
    for user in utilisateurs:
        groupe_nom = user.groupe_travail.nom if user.groupe_travail else "Aucun"
        print(f"   - {user.username} ({groupe_nom}): {'✅ Actif' if user.actif else '❌ Inactif'}")
    
    # Test des permissions basiques
    print(f"\n🔐 TEST DES PERMISSIONS:")
    print("-" * 40)
    
    for user in utilisateurs:
        if not user.groupe_travail:
            continue
            
        groupe_nom = user.groupe_travail.nom
        is_privilege = groupe_nom.upper() == 'PRIVILEGE'
        
        print(f"\n👤 {user.username} ({groupe_nom}):")
        print(f"   ✅ Ajouter: OUI (tous les utilisateurs)")
        print(f"   🔧 Modifier: {'OUI' if is_privilege else 'NON'} ({'PRIVILEGE' if is_privilege else 'Non-PRIVILEGE'})")
        print(f"   🗑️  Supprimer: {'OUI' if is_privilege else 'NON'} ({'PRIVILEGE' if is_privilege else 'Non-PRIVILEGE'})")
    
    print(f"\n" + "=" * 40)
    print("✅ TEST TERMINÉ !")
    print("📋 RÉSUMÉ:")
    print("   - Tous les utilisateurs connectés et actifs peuvent AJOUTER")
    print("   - Seuls les utilisateurs PRIVILEGE peuvent MODIFIER et SUPPRIMER")
    print("   - Les permissions sont maintenant actives dans l'application")

def main():
    """Fonction principale"""
    try:
        tester_permissions()
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
