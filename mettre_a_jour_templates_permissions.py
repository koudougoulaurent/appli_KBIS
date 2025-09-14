#!/usr/bin/env python
"""
Script pour mettre à jour les templates avec les nouvelles permissions
- Masquer les boutons de modification/suppression pour les non-PRIVILEGE
- Afficher les boutons d'ajout pour tous les utilisateurs
"""

import os
import re
from pathlib import Path

def mettre_a_jour_template(chemin_fichier):
    """Met à jour un template avec les nouvelles permissions"""
    
    if not os.path.exists(chemin_fichier):
        return False
    
    with open(chemin_fichier, 'r', encoding='utf-8') as f:
        contenu = f.read()
    
    # Sauvegarder l'original
    with open(chemin_fichier + '.backup', 'w', encoding='utf-8') as f:
        f.write(contenu)
    
    modifications = []
    
    # 1. Ajouter la vérification des permissions au début du template
    if '{% load utilisateurs_extras %}' not in contenu:
        # Ajouter après les autres load
        pattern_load = r'({% load [^%]+ %}\n)'
        if re.search(pattern_load, contenu):
            contenu = re.sub(pattern_load, r'\1{% load utilisateurs_extras %}\n', contenu)
        else:
            # Ajouter au début du fichier
            contenu = '{% load utilisateurs_extras %}\n' + contenu
        modifications.append("✅ Load utilisateurs_extras ajouté")
    
    # 2. Masquer les boutons de modification pour les non-PRIVILEGE
    pattern_modifier = r'(<a[^>]*href="[^"]*modifier[^"]*"[^>]*>.*?</a>)'
    def masquer_modifier(match):
        bouton = match.group(1)
        return f'{{% if user.groupe_travail.nom == "PRIVILEGE" %}}\n    {bouton}\n{{% endif %}}'
    
    contenu = re.sub(pattern_modifier, masquer_modifier, contenu)
    
    # 3. Masquer les boutons de suppression pour les non-PRIVILEGE
    pattern_supprimer = r'(<a[^>]*href="[^"]*supprimer[^"]*"[^>]*>.*?</a>)'
    def masquer_supprimer(match):
        bouton = match.group(1)
        return f'{{% if user.groupe_travail.nom == "PRIVILEGE" %}}\n    {bouton}\n{{% endif %}}'
    
    contenu = re.sub(pattern_supprimer, masquer_supprimer, contenu)
    
    # 4. Masquer les boutons de suppression dans les formulaires
    pattern_form_supprimer = r'(<button[^>]*type="submit"[^>]*name="supprimer"[^>]*>.*?</button>)'
    def masquer_form_supprimer(match):
        bouton = match.group(1)
        return f'{{% if user.groupe_travail.nom == "PRIVILEGE" %}}\n    {bouton}\n{{% endif %}}'
    
    contenu = re.sub(pattern_form_supprimer, masquer_form_supprimer, contenu)
    
    # 5. Masquer les liens de modification dans les listes
    pattern_liste_modifier = r'(<a[^>]*href="[^"]*modifier[^"]*"[^>]*class="[^"]*btn[^"]*"[^>]*>.*?</a>)'
    def masquer_liste_modifier(match):
        bouton = match.group(1)
        return f'{{% if user.groupe_travail.nom == "PRIVILEGE" %}}\n    {bouton}\n{{% endif %}}'
    
    contenu = re.sub(pattern_liste_modifier, masquer_liste_modifier, contenu)
    
    # 6. Masquer les liens de suppression dans les listes
    pattern_liste_supprimer = r'(<a[^>]*href="[^"]*supprimer[^"]*"[^>]*class="[^"]*btn[^"]*"[^>]*>.*?</a>)'
    def masquer_liste_supprimer(match):
        bouton = match.group(1)
        return f'{{% if user.groupe_travail.nom == "PRIVILEGE" %}}\n    {bouton}\n{{% endif %}}'
    
    contenu = re.sub(pattern_liste_supprimer, masquer_liste_supprimer, contenu)
    
    # 7. Masquer les actions de modification/suppression dans les tableaux
    pattern_action_modifier = r'(<td[^>]*>.*?<a[^>]*href="[^"]*modifier[^"]*"[^>]*>.*?</a>.*?</td>)'
    def masquer_action_modifier(match):
        cellule = match.group(1)
        return f'<td>{{% if user.groupe_travail.nom == "PRIVILEGE" %}}{cellule}{{% else %}}-{{% endif %}}</td>'
    
    contenu = re.sub(pattern_action_modifier, masquer_action_modifier, contenu)
    
    pattern_action_supprimer = r'(<td[^>]*>.*?<a[^>]*href="[^"]*supprimer[^"]*"[^>]*>.*?</a>.*?</td>)'
    def masquer_action_supprimer(match):
        cellule = match.group(1)
        return f'<td>{{% if user.groupe_travail.nom == "PRIVILEGE" %}}{cellule}{{% else %}}-{{% endif %}}</td>'
    
    contenu = re.sub(pattern_action_supprimer, masquer_action_supprimer, contenu)
    
    # 8. Ajouter des messages informatifs pour les non-PRIVILEGE
    pattern_messages = r'(<div class="alert[^>]*>.*?</div>)'
    def ajouter_message_permissions(match):
        message_existant = match.group(1)
        message_permissions = '''
{{% if user.groupe_travail.nom != "PRIVILEGE" %}}
<div class="alert alert-info">
    <i class="bi bi-info-circle me-2"></i>
    <strong>Information :</strong> Vous pouvez ajouter des éléments, mais seuls les utilisateurs du groupe PRIVILEGE peuvent les modifier ou les supprimer.
</div>
{{% endif %}}'''
        return message_existant + message_permissions
    
    # Ajouter le message après le premier alert
    contenu = re.sub(pattern_messages, ajouter_message_permissions, contenu, count=1)
    
    # Écrire le fichier modifié
    with open(chemin_fichier, 'w', encoding='utf-8') as f:
        f.write(contenu)
    
    return len(modifications) > 0

def main():
    """Fonction principale"""
    print("🔄 MISE À JOUR DES TEMPLATES AVEC LES NOUVELLES PERMISSIONS")
    print("=" * 60)
    
    # Dossier des templates
    dossier_templates = 'templates'
    
    if not os.path.exists(dossier_templates):
        print(f"❌ Dossier {dossier_templates} non trouvé")
        return
    
    # Trouver tous les fichiers HTML
    fichiers_html = []
    for root, dirs, files in os.walk(dossier_templates):
        for file in files:
            if file.endswith('.html'):
                fichiers_html.append(os.path.join(root, file))
    
    fichiers_modifies = 0
    
    for fichier in fichiers_html:
        print(f"📝 Traitement de {fichier}...")
        if mettre_a_jour_template(fichier):
            print(f"✅ {fichier} modifié avec succès")
            fichiers_modifies += 1
        else:
            print(f"ℹ️  {fichier} - Aucune modification nécessaire")
    
    print("\n" + "=" * 60)
    print(f"📊 RÉSULTAT:")
    print(f"   - Fichiers HTML trouvés: {len(fichiers_html)}")
    print(f"   - Fichiers modifiés: {fichiers_modifies}")
    
    print(f"\n✅ Mise à jour des templates terminée !")
    print(f"🎨 Les templates affichent maintenant :")
    print(f"   - Boutons d'ajout pour tous les utilisateurs")
    print(f"   - Boutons de modification/suppression uniquement pour PRIVILEGE")
    print(f"   - Messages informatifs pour les non-PRIVILEGE")

if __name__ == '__main__':
    main()
