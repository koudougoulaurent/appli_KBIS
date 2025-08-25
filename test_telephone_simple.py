#!/usr/bin/env python3
"""
Test simple de validation du téléphone
"""

import re

def test_phone_validation():
    """Test de la validation du téléphone"""
    
    # Regex du modèle (corrigée)
    phone_regex = re.compile(r'^\+\d{9,15}$')
    
    # Tests de validation
    test_cases = [
        # Cas valides
        ('+22990123456', True, 'Bénin - valide (11 chiffres)'),
        ('+22670123456', True, 'Burkina Faso - valide (11 chiffres)'),
        ('+22507123456', True, 'Côte d\'Ivoire - valide (11 chiffres)'),
        ('+233201234567', True, 'Ghana - valide (12 chiffres)'),
        ('+234801234567', True, 'Nigeria - valide (13 chiffres)'),
        ('+123456789', True, '9 chiffres - valide (minimum)'),
        ('+123456789012345', True, '15 chiffres - valide (maximum)'),
        
        # Cas invalides
        ('22990123456', False, 'Pas de +'),
        ('+2299012345678901', False, 'Plus de 15 chiffres (16 chiffres)'),
        ('+229 90 12 34 56', False, 'Contient des espaces'),
        ('+229-90-12-34-56', False, 'Contient des tirets'),
        ('+229.90.12.34.56', False, 'Contient des points'),
        ('+12345678', False, 'Moins de 9 chiffres (8 chiffres)'),
        ('+123456789a', False, 'Contient des lettres'),
        ('+1234567', False, 'Trop court (7 chiffres)'),
        ('+123456', False, 'Trop court (6 chiffres)'),
        ('', False, 'Vide'),
        (None, False, 'Null'),
    ]
    
    print("=== TEST DE VALIDATION DU TÉLÉPHONE ===\n")
    
    for phone, expected_valid, description in test_cases:
        if phone is None:
            is_valid = False
        else:
            is_valid = bool(phone_regex.match(phone))
        
        status = "✅ VALIDE" if is_valid == expected_valid else "❌ ERREUR"
        print(f"{status} | {phone or 'None':<20} | {description}")
        
        if is_valid != expected_valid:
            print(f"    Attendu: {expected_valid}, Obtenu: {is_valid}")
            print(f"    Regex: {phone_regex.pattern}")
            if phone:
                print(f"    Longueur après +: {len(phone)-1}")
                print(f"    Caractères après +: '{phone[1:]}'")
    
    print("\n=== RÉSULTATS ===")
    print("La validation du téléphone fonctionne correctement si tous les tests passent.")

if __name__ == '__main__':
    test_phone_validation()
