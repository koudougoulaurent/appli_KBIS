import re

# Test de la regex
regex = re.compile(r'^\+\d{9,15}$')

print("=== TEST SIMPLE DE LA REGEX ===")

# Test 1: Numéro valide
phone1 = "+22990123456"
match1 = regex.match(phone1)
print(f"Test 1: {phone1} -> {'✅ Valide' if match1 else '❌ Invalide'}")

# Test 2: Numéro trop court
phone2 = "+12345678"
match2 = regex.match(phone2)
print(f"Test 2: {phone2} -> {'✅ Valide' if match2 else '❌ Invalide'}")

# Test 3: Numéro avec espaces
phone3 = "+123 456 789"
match3 = regex.match(phone3)
print(f"Test 3: {phone3} -> {'✅ Valide' if match3 else '❌ Invalide'}")

# Test 4: Numéro trop long
phone4 = "+1234567890123456"
match4 = regex.match(phone4)
print(f"Test 4: {phone4} -> {'✅ Valide' if match4 else '❌ Invalide'}")

print("\nRegex utilisée:", regex.pattern)
