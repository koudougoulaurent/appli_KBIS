#!/usr/bin/env python
"""
Vérifier l'état actuel du contrat
"""
import subprocess
import sys

# Commande à exécuter dans le shell Django
commands = """
from contrats.models import Contrat
from core.utils import check_active_contracts_before_force_delete
from proprietes.models import Propriete

print("Verification de l'etat actuel du contrat")
print("=" * 50)

# Vérifier tous les contrats
contrats = Contrat.objects.all()
print(f"Total contrats: {contrats.count()}")

for contrat in contrats:
    print(f"Contrat {contrat.id}: {contrat}")
    print(f"  - Est actif: {contrat.est_actif}")
    print(f"  - Est resilie: {contrat.est_resilie}")
    print(f"  - Propriete: {contrat.propriete}")
    print(f"  - Locataire: {contrat.locataire}")
    print()

# Vérifier les contrats actifs
contrats_actifs = Contrat.objects.filter(est_actif=True, est_resilie=False)
print(f"Contrats actifs: {contrats_actifs.count()}")

# Tester la suppression forcée sur la propriété
propriete = Propriete.objects.first()
if propriete:
    print(f"\\nTest suppression forcee pour: {propriete}")
    result = check_active_contracts_before_force_delete(propriete)
    print(f"can_force_delete: {result['can_force_delete']}")
    print(f"contracts_count: {result['contracts_count']}")
    print(f"message: {result['message'][:200]}...")

print("\\n" + "=" * 50)
print("Verification terminee")
"""

# Exécuter les commandes dans le shell Django
try:
    result = subprocess.run([
        'python', 'manage.py', 'shell', '--settings=gestion_immobiliere.settings'
    ], input=commands, text=True, capture_output=True, encoding='utf-8', errors='ignore')
    
    print("STDOUT:")
    print(result.stdout)
    
    if result.stderr:
        print("STDERR:")
        print(result.stderr)
        
except Exception as e:
    print(f"Erreur: {e}")

