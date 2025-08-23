#!/usr/bin/env python
"""
Script de migration pour l'état 21
Ajoute les codes uniques aux bailleurs et locataires existants
"""

import os
import sys
import django
from django.utils.crypto import get_random_string

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from proprietes.models import Bailleur, Locataire
from paiements.models import Paiement


def generate_code_bailleur():
    """Génère un code unique pour le bailleur."""
    prefix = "BL"
    while True:
        code = f"{prefix}-{get_random_string(8, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')}"
        if not Bailleur.objects.filter(code_bailleur=code).exists():
            return code


def generate_code_locataire():
    """Génère un code unique pour le locataire."""
    prefix = "LT"
    while True:
        code = f"{prefix}-{get_random_string(8, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')}"
        if not Locataire.objects.filter(code_locataire=code).exists():
            return code


def generate_reference_paiement():
    """Génère une référence unique pour le paiement."""
    prefix = "PAY"
    while True:
        code = f"{prefix}-{get_random_string(8, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')}"
        if not Paiement.objects.filter(reference_paiement=code).exists():
            return code


def migrer_bailleurs():
    """Ajoute les codes uniques aux bailleurs existants."""
    print("🔧 Migration des bailleurs...")
    
    bailleurs_sans_code = Bailleur.objects.filter(code_bailleur__isnull=True)
    total = bailleurs_sans_code.count()
    
    if total == 0:
        print("✅ Tous les bailleurs ont déjà un code unique")
        return
    
    print(f"📝 Ajout de codes uniques à {total} bailleurs...")
    
    for i, bailleur in enumerate(bailleurs_sans_code, 1):
        code = generate_code_bailleur()
        bailleur.code_bailleur = code
        bailleur.save()
        print(f"  {i}/{total}: {bailleur.get_nom_complet()} -> {code}")
    
    print("✅ Migration des bailleurs terminée")


def migrer_locataires():
    """Ajoute les codes uniques aux locataires existants."""
    print("🔧 Migration des locataires...")
    
    locataires_sans_code = Locataire.objects.filter(code_locataire__isnull=True)
    total = locataires_sans_code.count()
    
    if total == 0:
        print("✅ Tous les locataires ont déjà un code unique")
        return
    
    print(f"📝 Ajout de codes uniques à {total} locataires...")
    
    for i, locataire in enumerate(locataires_sans_code, 1):
        code = generate_code_locataire()
        locataire.code_locataire = code
        locataire.save()
        print(f"  {i}/{total}: {locataire.get_nom_complet()} -> {code}")
    
    print("✅ Migration des locataires terminée")


def migrer_paiements():
    """Ajoute les références uniques aux paiements existants."""
    print("🔧 Migration des paiements...")
    
    paiements_sans_reference = Paiement.objects.filter(reference_paiement__isnull=True)
    total = paiements_sans_reference.count()
    
    if total == 0:
        print("✅ Tous les paiements ont déjà une référence unique")
        return
    
    print(f"📝 Ajout de références uniques à {total} paiements...")
    
    for i, paiement in enumerate(paiements_sans_reference, 1):
        try:
            reference = generate_reference_paiement()
            paiement.reference_paiement = reference
            
            # Calculer le montant net si nécessaire
            if paiement.montant_net_paye is None:
                charges = paiement.montant_charges_deduites or 0
                paiement.montant_net_paye = paiement.montant - charges
            
            paiement.save()
            print(f"  {i}/{total}: Paiement {paiement.id} -> {reference}")
        except Exception as e:
            print(f"  ❌ Erreur sur le paiement {paiement.id}: {e}")
            # Essayer de sauvegarder juste la référence
            try:
                paiement.reference_paiement = generate_reference_paiement()
                paiement.save(update_fields=['reference_paiement'])
                print(f"  ✅ Référence ajoutée au paiement {paiement.id}")
            except Exception as e2:
                print(f"  ❌ Impossible de sauvegarder le paiement {paiement.id}: {e2}")
            continue
    
    print("✅ Migration des paiements terminée")


def verifier_migration():
    """Vérifie que la migration s'est bien passée."""
    print("🔍 Vérification de la migration...")
    
    # Vérifier les bailleurs
    bailleurs_sans_code = Bailleur.objects.filter(code_bailleur__isnull=True).count()
    total_bailleurs = Bailleur.objects.count()
    
    # Vérifier les locataires
    locataires_sans_code = Locataire.objects.filter(code_locataire__isnull=True).count()
    total_locataires = Locataire.objects.count()
    
    # Vérifier les paiements
    paiements_sans_reference = Paiement.objects.filter(reference_paiement__isnull=True).count()
    total_paiements = Paiement.objects.count()
    
    print(f"📊 Bailleurs: {total_bailleurs - bailleurs_sans_code}/{total_bailleurs} avec code unique")
    print(f"📊 Locataires: {total_locataires - locataires_sans_code}/{total_locataires} avec code unique")
    print(f"📊 Paiements: {total_paiements - paiements_sans_reference}/{total_paiements} avec référence unique")
    
    if bailleurs_sans_code == 0 and locataires_sans_code == 0 and paiements_sans_reference == 0:
        print("✅ Migration complète et réussie!")
        return True
    else:
        print("❌ Migration incomplète")
        return False


def main():
    """Fonction principale de migration."""
    print("🚀 Début de la migration vers l'état 21")
    print("=" * 50)
    
    try:
        # Migration des bailleurs
        migrer_bailleurs()
        print()
        
        # Migration des locataires
        migrer_locataires()
        print()
        
        # Migration des paiements
        migrer_paiements()
        print()
        
        # Vérification
        verifier_migration()
        print()
        
        print("🎉 Migration terminée avec succès!")
        
    except Exception as e:
        print(f"❌ Erreur lors de la migration: {e}")
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
