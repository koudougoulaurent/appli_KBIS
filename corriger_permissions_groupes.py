#!/usr/bin/env python3
"""
Script pour corriger les permissions des groupes.
Tous les groupes peuvent modifier/supprimer sauf les données dédiées au groupe PRIVILEGE.
"""

import os
import re
from pathlib import Path

def corriger_permissions_groupes():
    """Corrige les permissions pour que tous les groupes puissent modifier/supprimer sauf les données PRIVILEGE."""
    
    # Données spécifiquement dédiées au groupe PRIVILEGE
    donnees_privilege_only = [
        'utilisateur',  # Gestion des utilisateurs
        'groupe_travail',  # Gestion des groupes de travail
        'audit_log',  # Journal d'audit
        'notification_preference',  # Préférences de notification
        'niveau_acces',  # Niveaux d'accès
        'permission_tableau_bord',  # Permissions tableau de bord
    ]
    
    # Fichiers à modifier
    fichiers_a_modifier = [
        'core/utils.py',
        'utilisateurs/views.py',
        'utilisateurs/privilege_views.py',
        'proprietes/views.py',
        'contrats/views.py',
        'paiements/views.py',
        'notifications/views.py',
    ]
    
    # Patterns de permissions à corriger
    patterns_permissions = [
        # Ancien pattern restrictif
        (r"check_group_permissions\([^,]+,\s*\[['\"]PRIVILEGE['\"]\]", 
         r"check_group_permissions(\1, ['PRIVILEGE', 'ADMINISTRATION', 'CAISSE', 'CONTROLES', 'COMPTABILITE', 'GESTIONNAIRE']"),
        
        # Pattern pour les actions en lot
        (r"check_group_permissions\([^,]+,\s*\[['\"]PRIVILEGE['\"],\s*['\"]ADMINISTRATION['\"]\]", 
         r"check_group_permissions(\1, ['PRIVILEGE', 'ADMINISTRATION', 'CAISSE', 'CONTROLES', 'COMPTABILITE', 'GESTIONNAIRE']"),
        
        # Pattern pour les vues de suppression
        (r"@privilege_required", r"@login_required"),
        
        # Pattern pour les vérifications de groupe
        (r"if not request\.user\.is_privilege_user\(\):", 
         r"if not request.user.is_authenticated:"),
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
            
            # Corrections spécifiques pour les données PRIVILEGE
            if 'utilisateurs' in fichier_path:
                # Garder les restrictions pour les données utilisateurs
                content = re.sub(
                    r"check_group_permissions\([^,]+,\s*\[['\"]PRIVILEGE['\"]\]",
                    r"check_group_permissions(\1, ['PRIVILEGE']",
                    content
                )
            
            # Si le contenu a changé, sauvegarder
            if content != original_content:
                with open(fichier_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                fichiers_modifies.append(fichier_path)
                print(f"[OK] Permissions corrigées: {fichier_path}")
            
        except Exception as e:
            print(f"[ERROR] Erreur avec {fichier_path}: {e}")
    
    # Créer une fonction utilitaire pour vérifier les permissions
    fonction_utilitaire = '''
def check_data_permissions(user, model_name, action='modify'):
    """
    Vérifie si l'utilisateur peut effectuer une action sur un type de données.
    
    Args:
        user: L'utilisateur connecté
        model_name: Nom du modèle (ex: 'bailleur', 'locataire', 'utilisateur')
        action: Type d'action ('view', 'add', 'modify', 'delete')
    
    Returns:
        dict: {'allowed': bool, 'message': str}
    """
    if not user.is_authenticated:
        return {'allowed': False, 'message': 'Utilisateur non authentifié.'}
    
    # Données spécifiquement dédiées au groupe PRIVILEGE
    donnees_privilege_only = [
        'utilisateur', 'groupe_travail', 'audit_log', 
        'notification_preference', 'niveau_acces', 'permission_tableau_bord'
    ]
    
    groupe_nom = getattr(user.groupe_travail, 'nom', '').upper() if hasattr(user, 'groupe_travail') and user.groupe_travail else ''
    
    # Si c'est une donnée PRIVILEGE, seul le groupe PRIVILEGE peut y accéder
    if model_name.lower() in donnees_privilege_only:
        if groupe_nom == 'PRIVILEGE':
            return {'allowed': True, 'message': 'Accès autorisé (données PRIVILEGE).'}
        else:
            return {'allowed': False, 'message': f'Accès refusé. Les données {model_name} sont réservées au groupe PRIVILEGE.'}
    
    # Pour toutes les autres données, tous les groupes peuvent y accéder
    groupes_autorises = ['PRIVILEGE', 'ADMINISTRATION', 'CAISSE', 'CONTROLES', 'COMPTABILITE', 'GESTIONNAIRE']
    
    if groupe_nom in groupes_autorises:
        return {'allowed': True, 'message': f'Accès autorisé (groupe {groupe_nom}).'}
    else:
        return {'allowed': False, 'message': f'Accès refusé. Groupe non autorisé: {groupe_nom}.'}
'''
    
    # Ajouter la fonction utilitaire à core/utils.py
    try:
        with open('core/utils.py', 'r', encoding='utf-8') as f:
            utils_content = f.read()
        
        if 'def check_data_permissions(' not in utils_content:
            utils_content += fonction_utilitaire
            with open('core/utils.py', 'w', encoding='utf-8') as f:
                f.write(utils_content)
            print("[OK] Fonction utilitaire ajoutée à core/utils.py")
            fichiers_modifies.append('core/utils.py')
    
    except Exception as e:
        print(f"[ERROR] Erreur lors de l'ajout de la fonction utilitaire: {e}")
    
    print(f"\\n=== RÉSUMÉ ===")
    print(f"Fichiers modifiés: {len(fichiers_modifies)}")
    for fichier in fichiers_modifies:
        print(f"  - {fichier}")
    
    print(f"\\n=== DONNÉES PRIVILEGE ONLY ===")
    for donnee in donnees_privilege_only:
        print(f"  - {donnee}")

if __name__ == "__main__":
    corriger_permissions_groupes()
