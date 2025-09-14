#!/usr/bin/env python
"""
Script de correction rapide pour les templates
"""

import os
import re
from pathlib import Path

def corriger_template(chemin_fichier):
    """Corrige un template avec les nouvelles permissions"""
    
    if not os.path.exists(chemin_fichier):
        return False
    
    with open(chemin_fichier, 'r', encoding='utf-8') as f:
        contenu = f.read()
    
    modifications = 0
    
    # 1. Ajouter le load des template tags
    if '{% load utilisateurs_extras %}' not in contenu:
        contenu = '{% load utilisateurs_extras %}\n' + contenu
        modifications += 1
    
    # 2. Masquer les boutons de modification
    pattern_modifier = r'(<a[^>]*href="[^"]*modifier[^"]*"[^>]*>.*?</a>)'
    def masquer_modifier(match):
        bouton = match.group(1)
        return f'{% if user.groupe_travail.nom == "PRIVILEGE" %}\n    {bouton}\n{% endif %}'
    
    if re.search(pattern_modifier, contenu):
        contenu = re.sub(pattern_modifier, masquer_modifier, contenu)
        modifications += 1
    
    # 3. Masquer les boutons de suppression
    pattern_supprimer = r'(<a[^>]*href="[^"]*supprimer[^"]*"[^>]*>.*?</a>)'
    def masquer_supprimer(match):
        bouton = match.group(1)
        return f'{% if user.groupe_travail.nom == "PRIVILEGE" %}\n    {bouton}\n{% endif %}'
    
    if re.search(pattern_supprimer, contenu):
        contenu = re.sub(pattern_supprimer, masquer_supprimer, contenu)
        modifications += 1
    
    # 4. Ajouter un message informatif
    if 'permission-info' not in contenu and 'alert-info' in contenu:
        message = '''
{% if user.groupe_travail.nom != "PRIVILEGE" %}
<div class="alert alert-info mt-3">
    <i class="bi bi-info-circle me-2"></i>
    <strong>Information :</strong> Vous pouvez ajouter des éléments, mais seuls les utilisateurs du groupe PRIVILEGE peuvent les modifier ou les supprimer.
</div>
{% endif %}'''
        contenu = contenu.replace('</div>', message + '\n</div>', 1)
        modifications += 1
    
    if modifications > 0:
        with open(chemin_fichier, 'w', encoding='utf-8') as f:
            f.write(contenu)
        return True
    
    return False

def main():
    """Fonction principale"""
    print("🔧 CORRECTION RAPIDE DES TEMPLATES")
    print("=" * 40)
    
    # Templates principaux à corriger
    templates_principaux = [
        'templates/proprietes/liste.html',
        'templates/proprietes/detail.html',
        'templates/contrats/liste.html',
        'templates/contrats/detail.html',
        'templates/paiements/liste.html',
        'templates/paiements/detail.html',
        'templates/utilisateurs/liste_utilisateurs.html',
        'templates/utilisateurs/detail_utilisateur.html'
    ]
    
    fichiers_corriges = 0
    
    for template in templates_principaux:
        if os.path.exists(template):
            print(f"📝 Correction de {template}...")
            if corriger_template(template):
                print(f"✅ {template} corrigé")
                fichiers_corriges += 1
            else:
                print(f"ℹ️  {template} - Aucune correction nécessaire")
        else:
            print(f"❌ {template} - Fichier non trouvé")
    
    print(f"\n" + "=" * 40)
    print(f"📊 RÉSULTAT:")
    print(f"   - Templates traités: {len(templates_principaux)}")
    print(f"   - Templates corrigés: {fichiers_corriges}")
    
    print(f"\n✅ Correction terminée !")
    print(f"🎨 Les templates affichent maintenant les permissions correctement")

if __name__ == '__main__':
    main()
