#!/usr/bin/env python3
"""
Test de la correction du formulaire de téléphone
"""

import re

def test_phone_cleaning():
    """Test du nettoyage et de la validation du téléphone"""
    
    def clean_telephone(telephone):
        """Fonction de nettoyage du formulaire"""
        if telephone:
            # Nettoyer le numéro (supprimer espaces, tirets, points)
            clean_number = re.sub(r'[\s\-\.]', '', telephone)
            
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
    
    # Tests
    test_cases = [
        # Cas valides
        ('+22990123456', True, 'Bénin - valide'),
        ('22990123456', True, 'Bénin sans + (ajouté automatiquement)'),
        ('+229 90 12 34 56', True, 'Bénin avec espaces (nettoyés)'),
        ('+229-90-12-34-56', True, 'Bénin avec tirets (nettoyés)'),
        ('+229.90.12.34.56', True, 'Bénin avec points (nettoyés)'),
        
        # Cas invalides
        ('+12345678', False, 'Trop court (8 chiffres)'),
        ('+1234567890123456', False, 'Trop long (16 chiffres)'),
        ('+123456789a', False, 'Contient des lettres'),
        ('', False, 'Vide'),
        (None, False, 'Null'),
    ]
    
    print("=== TEST DE LA CORRECTION DU FORMULAIRE ===\n")
    
    for phone, expected_valid, description in test_cases:
        cleaned_phone, error = clean_telephone(phone)
        
        if expected_valid:
            if cleaned_phone and not error:
                print(f"✅ VALIDE | {phone or 'None':<20} -> {cleaned_phone}")
            else:
                print(f"❌ ERREUR | {phone or 'None':<20} -> Erreur: {error}")
        else:
            if not cleaned_phone and error:
                print(f"✅ REJETÉ | {phone or 'None':<20} -> {error}")
            else:
                print(f"❌ ERREUR | {phone or 'None':<20} -> Devrait être rejeté mais a passé")
    
    print("\n=== RÉSULTATS ===")
    print("La correction fonctionne si:")
    print("- Les numéros valides sont nettoyés et acceptés")
    print("- Les numéros invalides sont rejetés avec un message d'erreur clair")

if __name__ == '__main__':
    test_phone_cleaning()
