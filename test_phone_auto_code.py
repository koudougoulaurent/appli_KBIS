#!/usr/bin/env python3
"""
Test de la logique automatique d'ajout du code pays
"""

import re

def test_phone_with_country_code():
    """Test de la logique avec code pays automatique"""
    
    def clean_telephone(telephone, country_code=None):
        """Fonction de nettoyage du formulaire avec code pays"""
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
    
    # Tests avec différents scénarios
    test_cases = [
        # Scénario 1: Utilisateur sélectionne Bénin (+229) et saisit seulement le numéro local
        {
            'country_code': '229',
            'telephone': '90123456',
            'expected': '+22990123456',
            'description': 'Bénin - numéro local seulement'
        },
        # Scénario 2: Utilisateur sélectionne Burkina Faso (+226) et saisit seulement le numéro local
        {
            'country_code': '226',
            'telephone': '70123456',
            'expected': '+22670123456',
            'description': 'Burkina Faso - numéro local seulement'
        },
        # Scénario 3: Utilisateur saisit déjà le code pays complet
        {
            'country_code': '225',
            'telephone': '+22507123456',
            'expected': '+22507123456',
            'description': 'Côte d\'Ivoire - code pays déjà saisi'
        },
        # Scénario 4: Pas de code pays, utilisateur saisit tout
        {
            'country_code': None,
            'telephone': '+123456789',
            'expected': '+123456789',
            'description': 'Pas de pays - numéro complet saisi'
        },
        # Scénario 5: Numéro avec espaces (nettoyage automatique)
        {
            'country_code': '233',
            'telephone': '20 123 4567',
            'expected': '+233201234567',
            'description': 'Ghana - numéro avec espaces (nettoyés)'
        },
    ]
    
    print("=== TEST DE LA LOGIQUE AUTOMATIQUE DU CODE PAYS ===\n")
    
    for i, test_case in enumerate(test_cases, 1):
        country_code = test_case['country_code']
        telephone = test_case['telephone']
        expected = test_case['expected']
        description = test_case['description']
        
        cleaned_phone, error = clean_telephone(telephone, country_code)
        
        if cleaned_phone == expected:
            print(f"✅ Test {i} | {description}")
            print(f"    Entrée: {telephone} (pays: {country_code or 'Aucun'})")
            print(f"    Sortie: {cleaned_phone}")
        else:
            print(f"❌ Test {i} | {description}")
            print(f"    Entrée: {telephone} (pays: {country_code or 'Aucun'})")
            print(f"    Attendu: {expected}")
            print(f"    Obtenu: {cleaned_phone}")
            if error:
                print(f"    Erreur: {error}")
        
        print()
    
    print("=== RÉSULTATS ===")
    print("La logique automatique fonctionne si tous les tests passent ✅")

if __name__ == '__main__':
    test_phone_with_country_code()
