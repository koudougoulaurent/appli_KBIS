#!/usr/bin/env python
"""
Script de test pour la création de contrat
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from proprietes.models import Propriete, Locataire

def test_contrat_creation():
    """Test de création de contrat"""
    print("=== Test de création de contrat ===")
    
    # Créer un client de test
    client = Client()
    
    # Vérifier s'il y a des propriétés et locataires
    proprietes = Propriete.objects.filter(is_deleted=False)
    locataires = Locataire.objects.filter(is_deleted=False)
    
    print(f"Propriétés disponibles: {proprietes.count()}")
    print(f"Locataires disponibles: {locataires.count()}")
    
    if proprietes.count() == 0:
        print("❌ Aucune propriété disponible pour le test")
        return False
    
    if locataires.count() == 0:
        print("❌ Aucun locataire disponible pour le test")
        return False
    
    # Prendre la première propriété et le premier locataire
    propriete = proprietes.first()
    locataire = locataires.first()
    
    print(f"Propriété de test: {propriete.titre} (ID: {propriete.id})")
    print(f"Locataire de test: {locataire.get_nom_complet()} (ID: {locataire.id})")
    
    # Données du formulaire
    form_data = {
        'propriete': propriete.id,
        'locataire': locataire.id,
        'date_debut': '2025-01-01',
        'date_fin': '2025-12-31',
        'date_signature': '2024-12-15',
        'loyer_mensuel': '150000',
        'charges_mensuelles': '15000',
        'depot_garantie': '300000',
        'avance_loyer': '150000',
        'telecharger_pdf': True,
        'creer_paiement_caution': True,
        'creer_paiement_avance': True,
        'mode_paiement_caution': 'especes',
        'mode_paiement_avance': 'especes',
    }
    
    print("\n=== Test de soumission du formulaire ===")
    
    # Tenter de se connecter (nécessaire pour les permissions)
    User = get_user_model()
    user = User.objects.first()
    if not user:
        print("❌ Aucun utilisateur trouvé")
        return False
    
    client.force_login(user)
    print(f"Utilisateur connecté: {user.username}")
    
    # Tenter de soumettre le formulaire
    response = client.post('/contrats/ajouter/', form_data)
    
    print(f"Code de réponse: {response.status_code}")
    print(f"Redirection: {response.get('Location', 'Aucune')}")
    
    if response.status_code == 302:
        print("✅ Redirection détectée (succès probable)")
        return True
    elif response.status_code == 200:
        print("⚠️ Page de retour (erreur probable)")
        # Vérifier s'il y a des messages d'erreur
        if hasattr(response, 'context') and 'form' in response.context:
            form = response.context['form']
            if hasattr(form, 'errors') and form.errors:
                print(f"Erreurs du formulaire: {form.errors}")
        return False
    else:
        print(f"❌ Erreur inattendue: {response.status_code}")
        return False

if __name__ == '__main__':
    success = test_contrat_creation()
    if success:
        print("\n✅ Test réussi!")
    else:
        print("\n❌ Test échoué!")
