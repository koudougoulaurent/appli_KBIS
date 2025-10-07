#!/usr/bin/env python
"""
Script de test pour vérifier que toutes les URLs utilisées dans les actions rapides existent
"""

import os
import django
from django.urls import reverse, NoReverseMatch

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'packages.hotspot.settings_dev')
django.setup()

def test_urls_actions_rapides():
    """Teste toutes les URLs utilisées dans les actions rapides"""
    
    print("TEST DES URLs DANS LES ACTIONS RAPIDES")
    print("=" * 50)
    
    # URLs à tester
    urls_to_test = [
        # Propriétés
        ('proprietes:proprietes_dashboard', 'Dashboard Propriétés'),
        ('proprietes:ajouter', 'Ajouter Propriété'),
        ('proprietes:liste', 'Liste Propriétés'),
        ('proprietes:recherche_unites', 'Recherche Unités'),
        ('proprietes:bailleurs_liste', 'Liste Bailleurs'),
        ('proprietes:locataires_liste', 'Liste Locataires'),
        ('proprietes:ajouter_bailleur', 'Ajouter Bailleur'),
        ('proprietes:ajouter_locataire', 'Ajouter Locataire'),
        ('proprietes:document_list', 'Liste Documents'),
        
        # Contrats
        ('contrats:dashboard', 'Dashboard Contrats'),
        ('contrats:ajouter', 'Créer Contrat'),
        ('contrats:liste', 'Liste Contrats'),
        ('contrats:orphelins', 'Contrats Orphelins'),
        
        # Paiements
        ('paiements:dashboard', 'Dashboard Paiements'),
        ('paiements:ajouter', 'Ajouter Paiement'),
        ('paiements:liste', 'Liste Paiements'),
        ('paiements:recherche_intelligente', 'Recherche Intelligente Paiements'),
        ('paiements:tableau_bord_list', 'Tableaux de Bord'),
        
        # Core
        ('core:tableau_bord_principal', 'Tableau de Bord Principal'),
        ('core:configuration_entreprise', 'Configuration Entreprise'),
        ('core:rapports_audit', 'Rapports Audit'),
        ('core:intelligent_search', 'Recherche Intelligente'),
        
        # Utilisateurs (redirigés vers core)
        ('core:tableau_bord_principal', 'Profil Utilisateur'),
        ('core:tableau_bord_principal', 'Déconnexion'),
    ]
    
    success_count = 0
    error_count = 0
    errors = []
    
    for url_name, description in urls_to_test:
        try:
            url = reverse(url_name)
            print(f"OK {description}: {url}")
            success_count += 1
        except NoReverseMatch as e:
            print(f"ERREUR {description}: ERREUR - {e}")
            error_count += 1
            errors.append((url_name, description, str(e)))
        except Exception as e:
            print(f"ATTENTION {description}: ERREUR INATTENDUE - {e}")
            error_count += 1
            errors.append((url_name, description, str(e)))
    
    print("\n" + "=" * 50)
    print(f"RESULTATS DU TEST")
    print(f"URLs valides: {success_count}")
    print(f"URLs invalides: {error_count}")
    print(f"Taux de reussite: {(success_count / (success_count + error_count) * 100):.1f}%")
    
    if errors:
        print(f"\nERREURS DETECTEES:")
        for url_name, description, error in errors:
            print(f"   - {description} ({url_name}): {error}")
    
    return error_count == 0

def test_urls_objects_rapides():
    """Teste les URLs pour les actions d'objets spécifiques"""
    
    print("\nTEST DES URLs D'OBJETS SPECIFIQUES")
    print("=" * 50)
    
    # URLs d'objets (avec paramètres)
    object_urls = [
        # Propriétés
        ('proprietes:detail', 'Détail Propriété', {'object_id': 1}),
        ('proprietes:modifier', 'Modifier Propriété', {'object_id': 1}),
        ('proprietes:contrats_propriete', 'Contrats Propriété', {'object_id': 1}),
        ('proprietes:paiements_propriete', 'Paiements Propriété', {'object_id': 1}),
        
        # Contrats
        ('contrats:detail', 'Détail Contrat', {'object_id': 1}),
        ('contrats:modifier', 'Modifier Contrat', {'object_id': 1}),
        ('contrats:generer_pdf', 'PDF Contrat', {'object_id': 1}),
        ('contrats:paiements_contrat', 'Paiements Contrat', {'object_id': 1}),
        
        # Paiements
        ('paiements:detail', 'Détail Paiement', {'object_id': 1}),
        ('paiements:modifier', 'Modifier Paiement', {'object_id': 1}),
        ('paiements:generer_quittance', 'Quittance Paiement', {'object_id': 1}),
        ('paiements:historique_contrat', 'Historique Contrat', {'object_id': 1}),
        
        # Avances
        ('paiements:avances:detail_avance', 'Détail Avance', {'object_id': 1}),
        ('paiements:avances:detail_progression_avance', 'Progression Avance', {'object_id': 1}),
        ('paiements:avances:generer_recu_avance', 'Reçu Avance', {'object_id': 1}),
        ('paiements:avances:historique_contrat', 'Historique Contrat Avance', {'object_id': 1}),
    ]
    
    success_count = 0
    error_count = 0
    errors = []
    
    for url_name, description, kwargs in object_urls:
        try:
            url = reverse(url_name, kwargs=kwargs)
            print(f"OK {description}: {url}")
            success_count += 1
        except NoReverseMatch as e:
            print(f"ERREUR {description}: ERREUR - {e}")
            error_count += 1
            errors.append((url_name, description, str(e)))
        except Exception as e:
            print(f"ATTENTION {description}: ERREUR INATTENDUE - {e}")
            error_count += 1
            errors.append((url_name, description, str(e)))
    
    print("\n" + "=" * 50)
    print(f"RESULTATS DU TEST D'OBJETS")
    print(f"URLs valides: {success_count}")
    print(f"URLs invalides: {error_count}")
    print(f"Taux de reussite: {(success_count / (success_count + error_count) * 100):.1f}%")
    
    if errors:
        print(f"\nERREURS DETECTEES:")
        for url_name, description, error in errors:
            print(f"   - {description} ({url_name}): {error}")
    
    return error_count == 0

if __name__ == "__main__":
    print("DEMARRAGE DES TESTS D'URLS")
    print("=" * 60)
    
    # Test des URLs principales
    main_test_passed = test_urls_actions_rapides()
    
    # Test des URLs d'objets
    objects_test_passed = test_urls_objects_rapides()
    
    print("\n" + "=" * 60)
    print("RESULTAT FINAL")
    print("=" * 60)
    
    if main_test_passed and objects_test_passed:
        print("TOUS LES TESTS SONT PASSES !")
        print("Les actions rapides devraient fonctionner correctement.")
    else:
        print("CERTAINS TESTS ONT ECHOUE !")
        print("Verifiez les erreurs ci-dessus et corrigez les URLs manquantes.")
    
    print("\nCONSEILS:")
    print("- Verifiez que toutes les applications sont bien installees")
    print("- Assurez-vous que les URLs sont correctement definies")
    print("- Testez l'application dans le navigateur apres correction")
