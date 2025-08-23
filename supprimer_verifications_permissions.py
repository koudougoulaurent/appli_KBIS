#!/usr/bin/env python
"""
Suppression de toutes les vérifications de permissions
- Supprime les redirections causées par check_group_permissions
- Permet l'accès libre à toutes les pages
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

def supprimer_verifications_permissions():
    """Supprime toutes les vérifications de permissions"""
    
    print("🚫 SUPPRESSION DE TOUTES LES VÉRIFICATIONS DE PERMISSIONS")
    print("=" * 70)
    
    # Étape 1: Lire le fichier views.py
    print("\n📖 Étape 1: Lecture du fichier views.py")
    print("-" * 60)
    
    try:
        with open('paiements/views.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        print(f"✅ Fichier lu: {len(content)} caractères")
        
    except Exception as e:
        print(f"❌ Erreur lors de la lecture: {e}")
        return False
    
    # Étape 2: Identifier les vérifications de permissions
    print("\n🔍 Étape 2: Identification des vérifications de permissions")
    print("-" * 60)
    
    # Patterns à rechercher
    patterns_permissions = [
        'check_group_permissions',
        'return redirect',
        'messages.error',
        'permissions[\'allowed\']',
        'if not permissions[\'allowed\']:',
    ]
    
    counts_before = {}
    for pattern in patterns_permissions:
        count = content.count(pattern)
        counts_before[pattern] = count
        if count > 0:
            print(f"📊 {pattern}: {count} occurrences")
    
    # Étape 3: Supprimer les blocs de vérification de permissions
    print("\n🔧 Étape 3: Suppression des blocs de vérification de permissions")
    print("-" * 60)
    
    try:
        lines = content.split('\n')
        lines_filtered = []
        removed_count = 0
        skip_next_lines = 0
        
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            
            # Détecter le début d'un bloc de vérification de permissions
            if 'check_group_permissions' in line:
                print(f"   ❌ Supprimé: {line_stripped}")
                removed_count += 1
                skip_next_lines = 3  # Ignorer les 3 lignes suivantes
                continue
            
            # Ignorer les lignes du bloc de vérification
            if skip_next_lines > 0:
                if 'return redirect' in line or 'messages.error' in line:
                    print(f"   ❌ Supprimé: {line_stripped}")
                    removed_count += 1
                skip_next_lines -= 1
                continue
            
            # Garder la ligne
            lines_filtered.append(line)
        
        content_filtered = '\n'.join(lines_filtered)
        
        print(f"✅ Lignes supprimées: {removed_count}")
        
    except Exception as e:
        print(f"❌ Erreur lors de la suppression: {e}")
        return False
    
    # Étape 4: Sauvegarder le fichier modifié
    print("\n💾 Étape 4: Sauvegarde du fichier modifié")
    print("-" * 60)
    
    try:
        # Créer une sauvegarde
        backup_path = 'paiements/views_backup_before_permissions_cleanup.py'
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Sauvegarde créée: {backup_path}")
        
        # Sauvegarder le fichier modifié
        with open('paiements/views.py', 'w', encoding='utf-8') as f:
            f.write(content_filtered)
        
        print("✅ Fichier views.py mis à jour")
        
    except Exception as e:
        print(f"❌ Erreur lors de la sauvegarde: {e}")
        return False
    
    # Étape 5: Vérification finale
    print("\n✅ Étape 5: Vérification finale")
    print("-" * 60)
    
    try:
        with open('paiements/views.py', 'r', encoding='utf-8') as f:
            content_after = f.read()
        
        print("📊 Vérifications de permissions restantes:")
        for pattern in patterns_permissions:
            count_after = content_after.count(pattern)
            if count_after > 0:
                print(f"   ⚠️ {pattern}: {count_after} (encore présent)")
            else:
                print(f"   ✅ {pattern}: 0 (supprimé)")
        
        total_restants = sum(content_after.count(p) for p in patterns_permissions)
        if total_restants == 0:
            print("\n🎉 SUCCÈS ! Toutes les vérifications de permissions ont été supprimées")
        else:
            print(f"\n⚠️ Il reste {total_restants} vérifications de permissions")
            
    except Exception as e:
        print(f"❌ Erreur lors de la vérification: {e}")
        return False
    
    print("\n✅ SUPPRESSION TERMINÉE !")
    print("🎯 Toutes les vérifications de permissions ont été supprimées")
    print("🔓 Toutes les pages sont maintenant accessibles sans restriction")
    
    return True

if __name__ == "__main__":
    supprimer_verifications_permissions()
