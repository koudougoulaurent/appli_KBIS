#!/usr/bin/env python
"""
Nettoyage complet de tous les décorateurs de sécurité
- Suppression de tous les décorateurs qui bloquent l'accès
- Permet l'accès libre à toutes les pages
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

def nettoyer_tous_les_decorateurs():
    """Nettoie tous les décorateurs de sécurité"""
    
    print("🧹 NETTOYAGE COMPLET DE TOUS LES DÉCORATEURS DE SÉCURITÉ")
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
    
    # Étape 2: Identifier tous les décorateurs de sécurité
    print("\n🔍 Étape 2: Identification des décorateurs de sécurité")
    print("-" * 60)
    
    decorateurs_securite = [
        '@login_required',
        '@user_passes_test',
        '@permission_required',
        '@groupe_required',
        '@method_decorator',
        '@csrf_exempt',
        '@require_http_methods',
        '@require_GET',
        '@require_POST',
        '@require_safe',
    ]
    
    counts_before = {}
    for decorateur in decorateurs_securite:
        count = content.count(decorateur)
        counts_before[decorateur] = count
        if count > 0:
            print(f"📊 {decorateur}: {count} occurrences")
    
    # Étape 3: Supprimer tous les décorateurs de sécurité
    print("\n🔧 Étape 3: Suppression de tous les décorateurs de sécurité")
    print("-" * 60)
    
    try:
        lines = content.split('\n')
        lines_filtered = []
        removed_count = 0
        
        for line in lines:
            line_stripped = line.strip()
            should_remove = False
            
            # Vérifier si la ligne contient un décorateur de sécurité
            for decorateur in decorateurs_securite:
                if line_stripped.startswith(decorateur):
                    should_remove = True
                    print(f"   ❌ Supprimé: {line_stripped}")
                    break
            
            if should_remove:
                removed_count += 1
            else:
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
        backup_path = 'paiements/views_backup_before_complete_cleanup.py'
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
        
        print("📊 Décorateurs restants après nettoyage:")
        for decorateur in decorateurs_securite:
            count_after = content_after.count(decorateur)
            if count_after > 0:
                print(f"   ⚠️ {decorateur}: {count_after} (encore présent)")
            else:
                print(f"   ✅ {decorateur}: 0 (supprimé)")
        
        total_restants = sum(content_after.count(d) for d in decorateurs_securite)
        if total_restants == 0:
            print("\n🎉 SUCCÈS ! Tous les décorateurs de sécurité ont été supprimés")
        else:
            print(f"\n⚠️ Il reste {total_restants} décorateurs de sécurité")
            
    except Exception as e:
        print(f"❌ Erreur lors de la vérification: {e}")
        return False
    
    print("\n✅ NETTOYAGE TERMINÉ !")
    print("🎯 Tous les décorateurs de sécurité ont été supprimés")
    print("🔓 Toutes les pages sont maintenant accessibles sans restriction")
    
    return True

if __name__ == "__main__":
    nettoyer_tous_les_decorateurs()
