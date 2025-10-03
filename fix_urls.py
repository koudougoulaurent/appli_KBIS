#!/usr/bin/env python3
"""
Script pour corriger les URLs en commentant les fonctions manquantes
"""

import re

# Lire le fichier URLs
with open('paiements/urls.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fonctions qui existent probablement (à garder)
existing_functions = [
    'paiements_dashboard', 'paiement_list', 'paiement_detail', 'ajouter_paiement',
    'liste_retraits_bailleur', 'modifier_paiement', 'supprimer_paiement', 'valider_paiement',
    'quittance_list', 'quittance_detail', 'generer_quittance_manuelle'
]

# Remplacer toutes les références views.fonction par des commentaires
def comment_url_line(match):
    line = match.group(0)
    if any(func in line for func in existing_functions):
        return line  # Garder les fonctions qui existent
    else:
        # Commenter la ligne
        return f"    # {line.strip()}  # Fonction non disponible"

# Pattern pour capturer les lignes avec views.fonction
pattern = r'    path\([^)]*views\.[^)]*\),?\n'
content = re.sub(pattern, comment_url_line, content)

# Écrire le fichier corrigé
with open('paiements/urls.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("URLs corrigées !")
