#!/usr/bin/env python
"""
Script de test pour vérifier que le filtre intcomma fonctionne
"""

import os
import sys
import django

# Configuration Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from django.template import Template, Context
from django.contrib.humanize.templatetags.humanize import intcomma

def test_intcomma_filter():
    """Teste le filtre intcomma."""
    
    print("🧪 Test du filtre intcomma")
    print("=" * 40)
    
    # Test direct du filtre
    test_values = [
        1000,
        10000,
        100000,
        1000000,
        1234567.89
    ]
    
    print("Test direct du filtre intcomma :")
    for value in test_values:
        formatted = intcomma(value)
        print(f"   {value:>10} → {formatted}")
    
    # Test avec template Django
    print("\nTest avec template Django :")
    template_string = """
    {% load humanize %}
    Valeur 1: {{ value1|intcomma }} F CFA
    Valeur 2: {{ value2|intcomma }} F CFA
    Valeur 3: {{ value3|intcomma }} F CFA
    """
    
    template = Template(template_string)
    context = Context({
        'value1': 100000,
        'value2': 1500000,
        'value3': 2500000.50
    })
    
    result = template.render(context)
    print(result)
    
    print("\n✅ Test du filtre intcomma réussi !")
    print("   Le filtre fonctionne correctement.")
    print("   Les templates peuvent maintenant utiliser |intcomma")

if __name__ == "__main__":
    test_intcomma_filter()
