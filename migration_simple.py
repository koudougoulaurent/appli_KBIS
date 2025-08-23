#!/usr/bin/env python
"""
Script de migration simple pour l'état 21
Ajoute uniquement les références uniques aux paiements
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from paiements.models import Paiement
from django.utils.crypto import get_random_string


def generate_reference_paiement():
    """Génère une référence unique pour le paiement."""
    prefix = "PAY"
    while True:
        code = f"{prefix}-{get_random_string(8, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')}"
        if not Paiement.objects.filter(reference_paiement=code).exists():
            return code


def migrer_paiements_simple():
    """Migration simple des paiements - ajoute seulement les références."""
    print("🔧 Migration simple des paiements...")
    
    paiements_sans_reference = Paiement.objects.filter(reference_paiement__isnull=True)
    total = paiements_sans_reference.count()
    
    if total == 0:
        print("✅ Tous les paiements ont déjà une référence unique")
        return
    
    print(f"📝 Ajout de références uniques à {total} paiements...")
    
    for i, paiement in enumerate(paiements_sans_reference, 1):
        try:
            reference = generate_reference_paiement()
            # Sauvegarder seulement la référence
            Paiement.objects.filter(id=paiement.id).update(reference_paiement=reference)
            print(f"  {i}/{total}: Paiement {paiement.id} -> {reference}")
        except Exception as e:
            print(f"  ❌ Erreur sur le paiement {paiement.id}: {e}")
            continue
    
    print("✅ Migration simple des paiements terminée")


def verifier_migration():
    """Vérifie que la migration s'est bien passée."""
    print("🔍 Vérification de la migration...")
    
    # Vérifier les paiements
    paiements_sans_reference = Paiement.objects.filter(reference_paiement__isnull=True).count()
    total_paiements = Paiement.objects.count()
    
    print(f"📊 Paiements: {total_paiements - paiements_sans_reference}/{total_paiements} avec référence unique")
    
    if paiements_sans_reference == 0:
        print("✅ Migration complète et réussie!")
        return True
    else:
        print("❌ Migration incomplète")
        return False


def main():
    """Fonction principale de migration."""
    print("🚀 Début de la migration simple vers l'état 21")
    print("=" * 50)
    
    try:
        # Migration simple des paiements
        migrer_paiements_simple()
        print()
        
        # Vérification
        verifier_migration()
        print()
        
        print("🎉 Migration simple terminée!")
        
    except Exception as e:
        print(f"❌ Erreur lors de la migration: {e}")
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
