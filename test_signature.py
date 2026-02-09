#!/usr/bin/env python
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'packages.hotspot.settings_dev')
django.setup()

from contrats.services_contrat_pdf_updated import ContratPDFServiceUpdated
import inspect

# Vérifier la signature
sig = inspect.signature(ContratPDFServiceUpdated.generate_contrat_pdf)
print(f"✅ Paramètres trouvés: {list(sig.parameters.keys())}")

# Vérifier le fichier source
source_file = inspect.getfile(ContratPDFServiceUpdated)
print(f"📁 Fichier source: {source_file}")

# Tester l'appel
from contrats.models import Contrat
try:
    contrat = Contrat.objects.get(pk=16)
    service = ContratPDFServiceUpdated(contrat)
    
    # Essayer avec use_cache
    print("\n🧪 Test 1: service.generate_contrat_pdf(use_cache=False)")
    try:
        result = service.generate_contrat_pdf(use_cache=False)
        print("✅ Succès avec use_cache!")
    except TypeError as e:
        print(f"❌ Erreur: {e}")
    
    # Essayer sans use_cache
    print("\n🧪 Test 2: service.generate_contrat_pdf()")
    try:
        result = service.generate_contrat_pdf()
        print("✅ Succès sans use_cache!")
    except Exception as e:
        print(f"❌ Erreur: {e}")
        
except Exception as e:
    print(f"❌ Erreur générale: {e}")
