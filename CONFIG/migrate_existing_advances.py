#!/usr/bin/env python
"""
Script de migration pour créer les avances manquantes pour les contrats existants
Usage: python CONFIG/migrate_existing_advances.py
"""
import os
import sys
import django
from pathlib import Path

# Ajouter le répertoire parent au path Python
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from contrats.models import Contrat
from paiements.models_avance import AvanceLoyer
from decimal import Decimal

def migrate_existing_advances():
    """Migre les avances manquantes pour les contrats existants"""
    print("🔄 Migration des avances existantes...")
    
    # Trouver tous les contrats avec des avances payées mais sans AvanceLoyer
    contrats_avec_avances = Contrat.objects.filter(
        avance_loyer_payee=True,
        avance_loyer__gt='0'
    ).exclude(
        avances_loyer__isnull=False
    )
    
    print(f"📊 {contrats_avec_avances.count()} contrats trouvés avec des avances payées")
    
    avances_creees = 0
    erreurs = 0
    
    for contrat in contrats_avec_avances:
        try:
            print(f"🔄 Traitement du contrat {contrat.numero_contrat}...")
            
            # Créer l'avance automatiquement
            contrat._creer_avance_loyer_automatique()
            
            # Vérifier que l'avance a été créée
            if AvanceLoyer.objects.filter(contrat=contrat).exists():
                avances_creees += 1
                print(f"✅ Avance créée pour le contrat {contrat.numero_contrat}")
            else:
                print(f"⚠️ Aucune avance créée pour le contrat {contrat.numero_contrat}")
                
        except Exception as e:
            erreurs += 1
            print(f"❌ Erreur pour le contrat {contrat.numero_contrat}: {str(e)}")
    
    print(f"\n📈 Résumé de la migration:")
    print(f"✅ Avances créées: {avances_creees}")
    print(f"❌ Erreurs: {erreurs}")
    print(f"📊 Total contrats traités: {contrats_avec_avances.count()}")
    
    return avances_creees, erreurs

def main():
    """Fonction principale"""
    print("🚀 Migration des avances de loyer existantes")
    print("=" * 50)
    
    try:
        avances_creees, erreurs = migrate_existing_advances()
        
        if erreurs == 0:
            print("🎉 Migration terminée avec succès!")
        else:
            print(f"⚠️ Migration terminée avec {erreurs} erreurs")
            
    except Exception as e:
        print(f"❌ Erreur lors de la migration: {str(e)}")
        return False
    
    return True

if __name__ == '__main__':
    main()
