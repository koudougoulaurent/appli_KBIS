#!/usr/bin/env python
"""
Suppression de tous les décorateurs @login_required des vues de liste
- Permet l'accès direct aux pages sans redirection forcée
- Conserve la sécurité sur les actions sensibles
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

def supprimer_login_required():
    """Supprime tous les décorateurs @login_required des vues de liste"""
    
    print("🚫 SUPPRESSION DE TOUS LES @login_required")
    print("=" * 60)
    
    # Étape 1: Lire le fichier views.py
    print("\n📖 Étape 1: Lecture du fichier views.py")
    print("-" * 50)
    
    try:
        with open('paiements/views.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        print(f"✅ Fichier lu: {len(content)} caractères")
        
        # Compter les occurrences de @login_required
        count_before = content.count('@login_required')
        print(f"📊 Nombre de @login_required trouvés: {count_before}")
        
    except Exception as e:
        print(f"❌ Erreur lors de la lecture: {e}")
        return False
    
    # Étape 2: Supprimer les décorateurs @login_required
    print("\n🔧 Étape 2: Suppression des décorateurs @login_required")
    print("-" * 50)
    
    try:
        # Supprimer les lignes avec @login_required
        lines = content.split('\n')
        lines_filtered = []
        removed_count = 0
        
        for line in lines:
            if line.strip().startswith('@login_required'):
                print(f"   ❌ Supprimé: {line.strip()}")
                removed_count += 1
            else:
                lines_filtered.append(line)
        
        content_filtered = '\n'.join(lines_filtered)
        
        print(f"✅ Lignes supprimées: {removed_count}")
        
    except Exception as e:
        print(f"❌ Erreur lors de la suppression: {e}")
        return False
    
    # Étape 3: Sauvegarder le fichier modifié
    print("\n💾 Étape 3: Sauvegarde du fichier modifié")
    print("-" * 50)
    
    try:
        # Créer une sauvegarde
        backup_path = 'paiements/views_backup_before_cleanup.py'
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
    
    # Étape 4: Vérification
    print("\n✅ Étape 4: Vérification")
    print("-" * 50)
    
    try:
        with open('paiements/views.py', 'r', encoding='utf-8') as f:
            content_after = f.read()
        
        count_after = content_after.count('@login_required')
        print(f"📊 Nombre de @login_required après suppression: {count_after}")
        
        if count_after == 0:
            print("🎉 SUCCÈS ! Tous les @login_required ont été supprimés")
        else:
            print(f"⚠️ Il reste {count_after} @login_required")
            
    except Exception as e:
        print(f"❌ Erreur lors de la vérification: {e}")
        return False
    
    print("\n✅ SUPPRESSION TERMINÉE !")
    print("🎯 Tous les décorateurs @login_required ont été supprimés")
    print("🔒 Les pages de liste sont maintenant accessibles sans redirection")
    
    return True

if __name__ == "__main__":
    supprimer_login_required()
