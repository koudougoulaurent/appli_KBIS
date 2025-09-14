#!/usr/bin/env python
"""
Script pour mettre à jour les permissions des vues selon la nouvelle logique :
- Tous les utilisateurs peuvent AJOUTER
- Seuls les utilisateurs PRIVILEGE peuvent MODIFIER et SUPPRIMER
"""

import os
import re
from pathlib import Path

def mettre_a_jour_fichier_vues(chemin_fichier):
    """Met à jour un fichier de vues avec les nouvelles permissions"""
    
    if not os.path.exists(chemin_fichier):
        return False
    
    with open(chemin_fichier, 'r', encoding='utf-8') as f:
        contenu = f.read()
    
    # Sauvegarder l'original
    with open(chemin_fichier + '.backup', 'w', encoding='utf-8') as f:
        f.write(contenu)
    
    modifications = []
    
    # 1. Ajouter les imports des nouveaux mixins
    if 'from utilisateurs.mixins_permissions import' not in contenu:
        # Trouver la ligne d'import des mixins existants
        pattern_import = r'(from utilisateurs\.mixins import.*?\n)'
        match = re.search(pattern_import, contenu)
        if match:
            nouveau_import = match.group(1) + 'from utilisateurs.mixins_permissions import AddPermissionMixin, ModifyPermissionMixin, DeletePermissionMixin, ViewPermissionMixin, check_add_permission, check_modify_permission, check_delete_permission\n'
            contenu = contenu.replace(match.group(1), nouveau_import)
            modifications.append("✅ Imports des nouveaux mixins ajoutés")
    
    # 2. Remplacer les vues d'ajout pour utiliser AddPermissionMixin
    # Pattern pour les vues d'ajout
    pattern_ajout = r'class (\w+Ajouter\w*).*?PrivilegeRequiredMixin.*?:\n'
    def remplacer_ajout(match):
        nom_classe = match.group(1)
        return f'class {nom_classe}(AddPermissionMixin, '
    
    contenu = re.sub(pattern_ajout, remplacer_ajout, contenu)
    
    # 3. Remplacer les vues de modification pour utiliser ModifyPermissionMixin
    pattern_modif = r'class (\w+Modifier\w*).*?PrivilegeRequiredMixin.*?:\n'
    def remplacer_modif(match):
        nom_classe = match.group(1)
        return f'class {nom_classe}(ModifyPermissionMixin, '
    
    contenu = re.sub(pattern_modif, remplacer_modif, contenu)
    
    # 4. Remplacer les vues de suppression pour utiliser DeletePermissionMixin
    pattern_suppr = r'class (\w+Supprimer\w*).*?PrivilegeRequiredMixin.*?:\n'
    def remplacer_suppr(match):
        nom_classe = match.group(1)
        return f'class {nom_classe}(DeletePermissionMixin, '
    
    contenu = re.sub(pattern_suppr, remplacer_suppr, contenu)
    
    # 5. Remplacer les vues de liste pour utiliser ViewPermissionMixin
    pattern_liste = r'class (\w+Liste\w*).*?PrivilegeRequiredMixin.*?:\n'
    def remplacer_liste(match):
        nom_classe = match.group(1)
        return f'class {nom_classe}(ViewPermissionMixin, '
    
    contenu = re.sub(pattern_liste, remplacer_liste, contenu)
    
    # 6. Mettre à jour les décorateurs de fonctions
    # Remplacer @privilege_required par des vérifications conditionnelles
    pattern_decorator = r'@privilege_required\s*\n'
    contenu = re.sub(pattern_decorator, '', contenu)
    
    # 7. Ajouter des vérifications de permissions dans les fonctions
    # Pattern pour les fonctions d'ajout
    pattern_fonction_ajout = r'def (\w*ajouter\w*)\(request.*?\):'
    def ajouter_check_ajout(match):
        nom_fonction = match.group(1)
        return f'''def {nom_fonction}(request, *args, **kwargs):
    # Vérification des permissions d'ajout
    allowed, message = check_add_permission(request.user)
    if not allowed:
        from django.contrib import messages
        from django.shortcuts import redirect
        messages.error(request, message)
        return redirect('utilisateurs:dashboard_groupe', groupe_nom=request.user.groupe_travail.nom)
    
    # Code original de la fonction'''
    
    contenu = re.sub(pattern_fonction_ajout, ajouter_check_ajout, contenu)
    
    # Pattern pour les fonctions de modification
    pattern_fonction_modif = r'def (\w*modifier\w*)\(request.*?\):'
    def ajouter_check_modif(match):
        nom_fonction = match.group(1)
        return f'''def {nom_fonction}(request, *args, **kwargs):
    # Vérification des permissions de modification
    allowed, message = check_modify_permission(request.user)
    if not allowed:
        from django.contrib import messages
        from django.shortcuts import redirect
        messages.error(request, message)
        return redirect('utilisateurs:dashboard_groupe', groupe_nom=request.user.groupe_travail.nom)
    
    # Code original de la fonction'''
    
    contenu = re.sub(pattern_fonction_modif, ajouter_check_modif, contenu)
    
    # Pattern pour les fonctions de suppression
    pattern_fonction_suppr = r'def (\w*supprimer\w*)\(request.*?\):'
    def ajouter_check_suppr(match):
        nom_fonction = match.group(1)
        return f'''def {nom_fonction}(request, *args, **kwargs):
    # Vérification des permissions de suppression
    allowed, message = check_delete_permission(request.user)
    if not allowed:
        from django.contrib import messages
        from django.shortcuts import redirect
        messages.error(request, message)
        return redirect('utilisateurs:dashboard_groupe', groupe_nom=request.user.groupe_travail.nom)
    
    # Code original de la fonction'''
    
    contenu = re.sub(pattern_fonction_suppr, ajouter_check_suppr, contenu)
    
    # Écrire le fichier modifié
    with open(chemin_fichier, 'w', encoding='utf-8') as f:
        f.write(contenu)
    
    return len(modifications) > 0

def main():
    """Fonction principale"""
    print("🔄 MISE À JOUR DES PERMISSIONS DES VUES")
    print("=" * 50)
    
    # Fichiers à traiter
    fichiers_vues = [
        'proprietes/views.py',
        'contrats/views.py',
        'paiements/views.py',
        'utilisateurs/views.py',
        'core/main_views.py'
    ]
    
    fichiers_modifies = 0
    
    for fichier in fichiers_vues:
        if os.path.exists(fichier):
            print(f"📝 Traitement de {fichier}...")
            if mettre_a_jour_fichier_vues(fichier):
                print(f"✅ {fichier} modifié avec succès")
                fichiers_modifies += 1
            else:
                print(f"ℹ️  {fichier} - Aucune modification nécessaire")
        else:
            print(f"❌ {fichier} - Fichier non trouvé")
    
    print("\n" + "=" * 50)
    print(f"📊 RÉSULTAT:")
    print(f"   - Fichiers traités: {len(fichiers_vues)}")
    print(f"   - Fichiers modifiés: {fichiers_modifies}")
    print(f"   - Fichiers non trouvés: {len(fichiers_vues) - fichiers_modifies}")
    
    print(f"\n✅ Mise à jour terminée !")
    print(f"🔧 Les nouvelles permissions sont maintenant actives :")
    print(f"   - Tous les utilisateurs peuvent AJOUTER")
    print(f"   - Seuls les utilisateurs PRIVILEGE peuvent MODIFIER et SUPPRIMER")

if __name__ == '__main__':
    main()
