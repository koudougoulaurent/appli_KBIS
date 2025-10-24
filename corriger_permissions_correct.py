#!/usr/bin/env python3
"""
Script pour corriger les permissions des groupes.
- Tous les groupes peuvent CRÉER/AJOUTER de nouvelles données
- Seul le groupe PRIVILEGE peut MODIFIER/SUPPRIMER les données existantes
"""

import os
import re
from pathlib import Path

def corriger_permissions_groupes():
    """Corrige les permissions selon la règle : tous peuvent créer, seul PRIVILEGE peut modifier/supprimer."""
    
    # Fichiers à modifier
    fichiers_a_modifier = [
        'core/utils.py',
        'utilisateurs/views.py',
        'proprietes/views.py',
        'contrats/views.py',
        'paiements/views.py',
        'notifications/views.py',
    ]
    
    # Patterns de permissions à corriger
    patterns_permissions = [
        # Pour les actions de CRÉATION/AJOUT - tous les groupes autorisés
        (r"check_group_permissions\([^,]+,\s*\[['\"]PRIVILEGE['\"]\]\s*,\s*['\"]add['\"]", 
         r"check_group_permissions(\1, ['PRIVILEGE', 'ADMINISTRATION', 'CAISSE', 'CONTROLES', 'COMPTABILITE', 'GESTIONNAIRE'], 'add'"),
        
        # Pour les actions de CRÉATION/AJOUT - tous les groupes autorisés (sans action spécifiée)
        (r"check_group_permissions\([^,]+,\s*\[['\"]PRIVILEGE['\"]\]\s*,\s*['\"]view['\"]", 
         r"check_group_permissions(\1, ['PRIVILEGE', 'ADMINISTRATION', 'CAISSE', 'CONTROLES', 'COMPTABILITE', 'GESTIONNAIRE'], 'view'"),
        
        # Pour les actions de MODIFICATION/SUPPRESSION - seul PRIVILEGE
        (r"check_group_permissions\([^,]+,\s*\[['\"]PRIVILEGE['\"]\]\s*,\s*['\"]modify['\"]", 
         r"check_group_permissions(\1, ['PRIVILEGE'], 'modify'"),
        
        (r"check_group_permissions\([^,]+,\s*\[['\"]PRIVILEGE['\"]\]\s*,\s*['\"]delete['\"]", 
         r"check_group_permissions(\1, ['PRIVILEGE'], 'delete'"),
        
        # Pour les actions de MODIFICATION/SUPPRESSION - seul PRIVILEGE (sans action spécifiée)
        (r"check_group_permissions\([^,]+,\s*\[['\"]PRIVILEGE['\"]\]\s*\)(?!\s*,\s*['\"](?:add|view)['\"])", 
         r"check_group_permissions(\1, ['PRIVILEGE']"),
    ]
    
    fichiers_modifies = []
    
    for fichier_path in fichiers_a_modifier:
        if not os.path.exists(fichier_path):
            continue
            
        try:
            with open(fichier_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Appliquer les corrections de permissions
            for pattern, replacement in patterns_permissions:
                content = re.sub(pattern, replacement, content)
            
            # Si le contenu a changé, sauvegarder
            if content != original_content:
                with open(fichier_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                fichiers_modifies.append(fichier_path)
                print(f"[OK] Permissions corrigées: {fichier_path}")
            
        except Exception as e:
            print(f"[ERROR] Erreur avec {fichier_path}: {e}")
    
    # Créer une fonction utilitaire pour vérifier les permissions selon le type d'action
    fonction_utilitaire = '''
def check_action_permissions(user, action_type='view'):
    """
    Vérifie si l'utilisateur peut effectuer une action selon son type.
    
    Args:
        user: L'utilisateur connecté
        action_type: Type d'action ('view', 'add', 'modify', 'delete')
    
    Returns:
        dict: {'allowed': bool, 'message': str}
    """
    if not user.is_authenticated:
        return {'allowed': False, 'message': 'Utilisateur non authentifié.'}
    
    groupe_nom = getattr(user.groupe_travail, 'nom', '').upper() if hasattr(user, 'groupe_travail') and user.groupe_travail else ''
    
    # Actions que tous les groupes peuvent faire
    actions_tous_groupes = ['view', 'add']
    
    # Actions que seul PRIVILEGE peut faire
    actions_privilege_only = ['modify', 'delete']
    
    if action_type in actions_tous_groupes:
        # Tous les groupes peuvent voir et ajouter
        groupes_autorises = ['PRIVILEGE', 'ADMINISTRATION', 'CAISSE', 'CONTROLES', 'COMPTABILITE', 'GESTIONNAIRE']
        if groupe_nom in groupes_autorises:
            return {'allowed': True, 'message': f'Accès autorisé pour {action_type} (groupe {groupe_nom}).'}
        else:
            return {'allowed': False, 'message': f'Accès refusé. Groupe non autorisé: {groupe_nom}.'}
    
    elif action_type in actions_privilege_only:
        # Seul PRIVILEGE peut modifier et supprimer
        if groupe_nom == 'PRIVILEGE':
            return {'allowed': True, 'message': f'Accès autorisé pour {action_type} (groupe PRIVILEGE).'}
        else:
            return {'allowed': False, 'message': f'Accès refusé. Seul le groupe PRIVILEGE peut {action_type}.'}
    
    else:
        return {'allowed': False, 'message': f'Type d\'action non reconnu: {action_type}.'}
'''
    
    # Ajouter la fonction utilitaire à core/utils.py
    try:
        with open('core/utils.py', 'r', encoding='utf-8') as f:
            utils_content = f.read()
        
        if 'def check_action_permissions(' not in utils_content:
            utils_content += fonction_utilitaire
            with open('core/utils.py', 'w', encoding='utf-8') as f:
                f.write(utils_content)
            print("[OK] Fonction utilitaire ajoutée à core/utils.py")
            fichiers_modifies.append('core/utils.py')
    
    except Exception as e:
        print(f"[ERROR] Erreur lors de l'ajout de la fonction utilitaire: {e}")
    
    print(f"\\n=== RÈGLES DE PERMISSIONS ===")
    print(f"✅ TOUS LES GROUPES peuvent :")
    print(f"  - Voir les données (view)")
    print(f"  - Créer/Ajouter de nouvelles données (add)")
    print(f"")
    print(f"🔒 SEUL PRIVILEGE peut :")
    print(f"  - Modifier les données existantes (modify)")
    print(f"  - Supprimer les données existantes (delete)")
    
    print(f"\\n=== RÉSUMÉ ===")
    print(f"Fichiers modifiés: {len(fichiers_modifies)}")
    for fichier in fichiers_modifies:
        print(f"  - {fichier}")

if __name__ == "__main__":
    corriger_permissions_groupes()
