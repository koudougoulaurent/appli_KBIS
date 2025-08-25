#!/usr/bin/env python3
"""
Debug de la regex du téléphone
"""

import re

def debug_regex():
    """Debug de la regex du téléphone"""
    
    # Test de différentes regex
    regexes = [
        (r'^\+\d{9,15}$', 'Regex actuelle'),
        (r'^\+\d{9,15}$', 'Regex avec raw string'),
        (r'^\+[0-9]{9,15}$', 'Regex avec [0-9]'),
        (r'^\+[0-9]{9,15}$', 'Regex avec [0-9] et raw string'),
    ]
    
    test_cases = [
        '+123456789',           # 9 chiffres - devrait être valide
        '+12345678',            # 8 chiffres - devrait être invalide
        '+123456789012345',     # 15 chiffres - devrait être valide
        '+1234567890123456',    # 16 chiffres - devrait être invalide
        '+123 456 789',         # Avec espaces - devrait être invalide
        '+123-456-789',         # Avec tirets - devrait être invalide
        '+123.456.789',         # Avec points - devrait être invalide
        '+123456789a',          # Avec lettre - devrait être invalide
        '123456789',            # Sans + - devrait être invalide
    ]
    
    print("=== DEBUG DE LA REGEX DU TÉLÉPHONE ===\n")
    
    for pattern, description in regexes:
        print(f"Pattern: {pattern} ({description})")
        regex = re.compile(pattern)
        
        for test_case in test_cases:
            match = regex.match(test_case)
            is_valid = bool(match)
            print(f"  {test_case:<20} -> {'✅' if is_valid else '❌'} ({len(test_case)-1} caractères après +)")
        
        print()
    
    # Test spécifique du problème
    print("=== TEST SPÉCIFIQUE ===")
    problem_case = '+123 456 789'
    print(f"Test du cas problématique: {problem_case}")
    
    # Analyser caractère par caractère
    print("Analyse caractère par caractère:")
    for i, char in enumerate(problem_case):
        if char == '+':
            print(f"  Position {i}: {char} (début)")
        elif char.isdigit():
            print(f"  Position {i}: {char} (chiffre)")
        else:
            print(f"  Position {i}: {char} (autre: {ord(char)})")
    
    # Test avec la regex
    regex = re.compile(r'^\+\d{9,15}$')
    match = regex.match(problem_case)
    print(f"\nRegex match: {bool(match)}")
    
    if match:
        print(f"Match groups: {match.groups()}")
        print(f"Match span: {match.span()}")

if __name__ == '__main__':
    debug_regex()
