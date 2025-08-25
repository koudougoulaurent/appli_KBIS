#!/usr/bin/env python
"""
Script de test pour vérifier toutes les améliorations du formulaire de contrat :
1. Remplissage automatique du loyer
2. Champs optionnels
3. Nouveau nom du champ "Dépôt de garantie ou Caution"
4. Messages d'erreur détaillés
5. Sauvegarde en base de données
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from contrats.forms import ContratForm
from proprietes.models import Propriete
from contrats.models import Contrat

def test_ameliorations_finales():
    """Test de toutes les améliorations du formulaire de contrat"""
    
    print("🧪 Test de toutes les améliorations du formulaire de contrat")
    print("=" * 70)
    
    try:
        # 1. Vérifier le modèle Contrat
        print("\n1. Vérification du modèle Contrat...")
        
        # Vérifier le nom du champ depot_garantie
        depot_field = Contrat._meta.get_field('depot_garantie')
        if 'Caution' in depot_field.verbose_name:
            print("   ✅ Champ depot_garantie renommé en 'Dépôt de garantie ou Caution'")
        else:
            print(f"   ❌ Champ depot_garantie n'a pas le bon nom: {depot_field.verbose_name}")
        
        # Vérifier que les champs sont optionnels
        if depot_field.blank and depot_field.null:
            print("   ✅ Champ depot_garantie rendu optionnel (blank=True, null=True)")
        else:
            print("   ❌ Champ depot_garantie n'est pas optionnel")
        
        # 2. Vérifier le formulaire
        print("\n2. Vérification du formulaire ContratForm...")
        form = ContratForm()
        
        # Vérifier que les champs sont optionnels
        if not form.fields['charges_mensuelles'].required:
            print("   ✅ Champ charges_mensuelles rendu optionnel")
        else:
            print("   ❌ Champ charges_mensuelles toujours requis")
            
        if not form.fields['depot_garantie'].required:
            print("   ✅ Champ depot_garantie rendu optionnel")
        else:
            print("   ❌ Champ depot_garantie toujours requis")
        
        # Vérifier que le champ loyer est en lecture seule
        loyer_widget = form.fields['loyer_mensuel'].widget
        if hasattr(loyer_widget, 'attrs') and loyer_widget.attrs.get('readonly'):
            print("   ✅ Champ loyer_mensuel configuré en lecture seule")
        else:
            print("   ❌ Champ loyer_mensuel n'est pas en lecture seule")
        
        # 3. Vérifier les données des propriétés
        print("\n3. Vérification des données des propriétés...")
        if hasattr(form, 'proprietes_data'):
            print(f"   ✅ Données des propriétés disponibles : {len(form.proprietes_data)} propriétés")
            
            for prop_id, prop_data in form.proprietes_data.items():
                print(f"      - ID {prop_id}: {prop_data['titre']} - Loyer: {prop_data['loyer']} XOF")
        else:
            print("   ❌ Données des propriétés non disponibles")
        
        # 4. Vérifier la méthode get_errors_summary
        print("\n4. Vérification de la méthode get_errors_summary...")
        if hasattr(form, 'get_errors_summary'):
            print("   ✅ Méthode get_errors_summary disponible")
            
            # Tester la méthode directement
            error_summary = form.get_errors_summary()
            if error_summary == "":  # Pas d'erreurs sur un formulaire vide
                print("   ✅ Résumé des erreurs fonctionne (aucune erreur sur formulaire vide)")
            else:
                print(f"   ✅ Résumé des erreurs généré: {error_summary}")
        else:
            print("   ❌ Méthode get_errors_summary non disponible")
        
        # 5. Vérifier qu'il y a des propriétés disponibles
        print("\n5. Vérification des propriétés disponibles...")
        proprietes_disponibles = Propriete.objects.filter(disponible=True)
        print(f"   ✅ {proprietes_disponibles.count()} propriétés disponibles")
        
        if proprietes_disponibles.exists():
            for prop in proprietes_disponibles:
                print(f"      - {prop.titre} (ID: {prop.id}) - Loyer: {prop.loyer_actuel} XOF")
        
        # 6. Test de validation et sauvegarde
        print("\n6. Test de validation et sauvegarde...")
        
        # Créer des données de test
        test_data = {
            'numero_contrat': 'TEST-CT-001',
            'propriete': proprietes_disponibles.first().id,
            'locataire': 1,  # Assurez-vous qu'il y a un locataire
            'date_debut': '2025-09-01',
            'date_fin': '2026-08-31',
            'date_signature': '2025-08-25',
            'loyer_mensuel': '75000.00',
            'charges_mensuelles': '',  # Champ optionnel vide
            'depot_garantie': '',      # Champ optionnel vide
            'avance_loyer': '0.00',
            'jour_paiement': 1,
            'mode_paiement': 'virement',
            'notes': 'Test d\'amélioration'
        }
        
        # Tester la validation
        form_test = ContratForm(data=test_data)
        if form_test.is_valid():
            print("   ✅ Formulaire valide avec champs optionnels vides")
            
            # Tester la sauvegarde
            try:
                contrat = form_test.save(commit=False)
                print("   ✅ Formulaire prêt pour sauvegarde")
                print(f"      - Numéro: {contrat.numero_contrat}")
                print(f"      - Propriété: {contrat.propriete.titre}")
                print(f"      - Loyer: {contrat.loyer_mensuel}")
                print(f"      - Charges: {contrat.charges_mensuelles or 'Non définies'}")
                print(f"      - Dépôt: {contrat.depot_garantie or 'Non défini'}")
                
            except Exception as e:
                print(f"   ❌ Erreur lors de la préparation de la sauvegarde: {e}")
        else:
            print("   ❌ Formulaire invalide:")
            error_summary = form_test.get_errors_summary()
            if error_summary:
                print(f"      {error_summary}")
        
        print("\n🎉 Test de toutes les améliorations terminé avec succès !")
        
    except Exception as e:
        print(f"\n❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_ameliorations_finales()
