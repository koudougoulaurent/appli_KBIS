#!/usr/bin/env python3
"""
Test simple du formulaire sans validation du modèle
"""

import re

def test_form_validation():
    """Test de la validation du formulaire"""
    
    def clean_telephone(telephone, country_code=None):
        """Fonction de nettoyage du formulaire"""
        if telephone:
            # Nettoyer le numéro (supprimer espaces, tirets, points)
            clean_number = re.sub(r'[\s\-\.]', '', telephone)
            
            # Si on a un code pays et que le numéro ne commence pas par +
            if country_code and not clean_number.startswith('+'):
                # L'utilisateur a saisi seulement le numéro local, ajouter le code pays
                clean_number = f"+{country_code}{clean_number}"
            
            # Vérifier que le numéro commence par +
            if not clean_number.startswith('+'):
                clean_number = '+' + clean_number
            
            # Vérifier la longueur (9 à 15 chiffres après le +)
            digits_only = clean_number[1:]  # Tout sauf le +
            if len(digits_only) < 9 or len(digits_only) > 15:
                return None, "Le numéro de téléphone doit être au format : '+999999999'. Jusqu'à 15 chiffres autorisés."
            
            # Vérifier que ce sont bien des chiffres
            if not digits_only.isdigit():
                return None, "Le numéro de téléphone ne doit contenir que des chiffres après le +."
            
            return clean_number, None
        
        return telephone, None
    
    print("=== TEST DU FORMULAIRE SANS VALIDATION DU MODÈLE ===\n")
    
    # Test 1: Utilisateur sélectionne Bénin et saisit seulement le numéro local
    print("Test 1: Bénin (+229) - numéro local seulement")
    result, error = clean_telephone("90123456", "229")
    if result:
        print(f"✅ Succès: 90123456 → {result}")
    else:
        print(f"❌ Erreur: {error}")
    
    # Test 2: Utilisateur saisit déjà le code pays complet
    print("\nTest 2: Code pays déjà saisi")
    result, error = clean_telephone("+22990123456", "229")
    if result:
        print(f"✅ Succès: +22990123456 → {result}")
    else:
        print(f"❌ Erreur: {error}")
    
    # Test 3: Numéro avec espaces
    print("\nTest 3: Numéro avec espaces")
    result, error = clean_telephone("+229 90 12 34 56", "229")
    if result:
        print(f"✅ Succès: +229 90 12 34 56 → {result}")
    else:
        print(f"❌ Erreur: {error}")
    
    # Test 4: Numéro trop court
    print("\nTest 4: Numéro trop court")
    result, error = clean_telephone("12345678", "229")
    if result:
        print(f"✅ Succès: 12345678 → {result}")
    else:
        print(f"❌ Erreur: {error}")
    
    print("\n=== RÉSULTATS ===")
    print("Le formulaire fonctionne si tous les tests passent ✅")

if __name__ == '__main__':
    test_form_validation()
