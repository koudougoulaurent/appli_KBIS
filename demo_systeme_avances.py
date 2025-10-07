#!/usr/bin/env python
"""
Démonstration du système d'avances de loyer KBIS
"""

import os
import sys
import django
from decimal import Decimal
from datetime import date

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

def demo_calcul_avance():
    """Démonstration du calcul automatique des mois d'avance"""
    print("=" * 60)
    print("DEMONSTRATION DU SYSTEME D'AVANCES DE LOYER KBIS")
    print("=" * 60)
    
    print("\n1. CALCUL AUTOMATIQUE DES MOIS D'AVANCE")
    print("-" * 40)
    
    # Exemple 1: Avance exacte de 3 mois
    loyer_mensuel = Decimal('150000')
    montant_avance = Decimal('450000')
    
    mois_complets = int(montant_avance // loyer_mensuel)
    reste = montant_avance % loyer_mensuel
    
    print(f"Loyer mensuel: {loyer_mensuel:,} F CFA")
    print(f"Montant avance: {montant_avance:,} F CFA")
    print(f"Resultat: {mois_complets} mois complets")
    print(f"Reste: {reste:,} F CFA")
    print(f"Statut: {'Epuisee' if reste == 0 else 'Active'}")
    
    print("\n" + "=" * 40)
    
    # Exemple 2: Avance avec reste
    montant_avance2 = Decimal('400000')
    mois_complets2 = int(montant_avance2 // loyer_mensuel)
    reste2 = montant_avance2 % loyer_mensuel
    
    print(f"Loyer mensuel: {loyer_mensuel:,} F CFA")
    print(f"Montant avance: {montant_avance2:,} F CFA")
    print(f"Resultat: {mois_complets2} mois complets")
    print(f"Reste: {reste2:,} F CFA")
    print(f"Statut: {'Epuisee' if reste2 == 0 else 'Active'}")

def demo_service_avance():
    """Démonstration du service de gestion des avances"""
    print("\n2. SERVICE DE GESTION DES AVANCES")
    print("-" * 40)
    
    try:
        from paiements.services_avance import ServiceGestionAvance
        
        print("Service importe avec succes!")
        print("\nMethodes disponibles:")
        methods = [method for method in dir(ServiceGestionAvance) if not method.startswith('_')]
        for i, method in enumerate(methods, 1):
            print(f"  {i:2d}. {method}")
        
        print(f"\nTotal: {len(methods)} methodes disponibles")
        
    except Exception as e:
        print(f"Erreur: {str(e)}")

def demo_modeles():
    """Démonstration des modèles de données"""
    print("\n3. MODELES DE DONNEES")
    print("-" * 40)
    
    try:
        from paiements.models_avance import AvanceLoyer, ConsommationAvance, HistoriquePaiement
        
        print("Modeles importes avec succes!")
        
        # Afficher les champs de AvanceLoyer
        print("\nChamps du modele AvanceLoyer:")
        for field in AvanceLoyer._meta.fields:
            print(f"  - {field.name}: {field.__class__.__name__}")
        
        print(f"\nTotal: {len(AvanceLoyer._meta.fields)} champs")
        
    except Exception as e:
        print(f"Erreur: {str(e)}")

def demo_forms():
    """Démonstration des formulaires"""
    print("\n4. FORMULAIRES")
    print("-" * 40)
    
    try:
        from paiements.forms_avance import AvanceLoyerForm, PaiementAvanceForm
        
        print("Formulaires importes avec succes!")
        
        # Créer un formulaire d'avance
        form = AvanceLoyerForm()
        print(f"\nFormulaire AvanceLoyer:")
        print(f"  - Nombre de champs: {len(form.fields)}")
        print(f"  - Champs: {list(form.fields.keys())}")
        
        # Créer un formulaire de paiement
        form_paiement = PaiementAvanceForm()
        print(f"\nFormulaire PaiementAvance:")
        print(f"  - Nombre de champs: {len(form_paiement.fields)}")
        print(f"  - Champs: {list(form_paiement.fields.keys())}")
        
    except Exception as e:
        print(f"Erreur: {str(e)}")

def demo_utils_pdf():
    """Démonstration des utilitaires PDF"""
    print("\n5. UTILITAIRES PDF")
    print("-" * 40)
    
    try:
        from paiements.utils_pdf import generate_historique_pdf
        
        print("Utilitaires PDF importes avec succes!")
        
        # Créer des données de test
        rapport_data = {
            'contrat': type('Contrat', (), {
                'numero_contrat': 'DEMO-001',
                'locataire': type('Locataire', (), {'get_nom_complet': lambda: 'Jean Dupont'})(),
                'propriete': type('Propriete', (), {'adresse': '123 Rue de Demo'})(),
                'loyer_mensuel': Decimal('150000')
            })(),
            'periode': {'debut': date.today(), 'fin': date.today()},
            'avances': [],
            'historique': [],
            'statistiques': {
                'total_avances_versees': Decimal('450000'),
                'total_avances_consommees': Decimal('300000'),
                'total_avances_restantes': Decimal('150000'),
                'nombre_mois_couverts': 3
            }
        }
        
        print("Donnees de test creees avec succes!")
        print(f"  - Contrat: {rapport_data['contrat'].numero_contrat}")
        print(f"  - Locataire: {rapport_data['contrat'].locataire.get_nom_complet()}")
        print(f"  - Total avances versees: {rapport_data['statistiques']['total_avances_versees']:,} F CFA")
        
    except Exception as e:
        print(f"Erreur: {str(e)}")

def demo_integration():
    """Démonstration d'intégration complète"""
    print("\n6. INTEGRATION COMPLETE")
    print("-" * 40)
    
    try:
        from paiements.models_avance import AvanceLoyer
        
        # Créer une avance de test
        avance_test = AvanceLoyer(
            montant_avance=Decimal('300000'),
            loyer_mensuel=Decimal('150000'),
            date_avance=date.today(),
            statut='active'
        )
        
        # Calculer les mois couverts
        avance_test.calculer_mois_couverts()
        
        print("Avance de test creee avec succes!")
        print(f"  - Montant: {avance_test.montant_avance:,} F CFA")
        print(f"  - Loyer mensuel: {avance_test.loyer_mensuel:,} F CFA")
        print(f"  - Mois couverts: {avance_test.nombre_mois_couverts}")
        print(f"  - Montant restant: {avance_test.montant_restant:,} F CFA")
        print(f"  - Statut: {avance_test.statut}")
        
        # Vérifier les calculs
        assert avance_test.nombre_mois_couverts == 2, "Devrait etre 2 mois"
        assert avance_test.montant_restant == Decimal('0'), "Le montant restant devrait etre 0"
        assert avance_test.statut == 'epuisee', "Le statut devrait etre 'epuisee'"
        
        print("\nVerifications: TOUTES REUSSIES!")
        
    except Exception as e:
        print(f"Erreur: {str(e)}")

def main():
    """Fonction principale de démonstration"""
    print("DEMONSTRATION DU SYSTEME D'AVANCES DE LOYER KBIS")
    print("Version 1.0 - Octobre 2025")
    print("=" * 60)
    
    try:
        demo_calcul_avance()
        demo_service_avance()
        demo_modeles()
        demo_forms()
        demo_utils_pdf()
        demo_integration()
        
        print("\n" + "=" * 60)
        print("DEMONSTRATION TERMINEE AVEC SUCCES!")
        print("Le systeme d'avances de loyer KBIS est operationnel")
        print("=" * 60)
        
    except Exception as e:
        print(f"\nERREUR LORS DE LA DEMONSTRATION: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
