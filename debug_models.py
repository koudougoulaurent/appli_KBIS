#!/usr/bin/env python
"""Script de debug pour tester les modèles individuellement"""

import os
import sys

# Ajouter le répertoire du projet au PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("🔍 Test des modèles individuellement...")

try:
    print("1. Test import django.db.models...")
    from django.db import models
    print("   ✅ django.db.models importé")
except Exception as e:
    print(f"   ❌ Erreur django.db.models: {e}")

try:
    print("2. Test import django.contrib.auth.models...")
    from django.contrib.auth.models import Group
    print("   ✅ Group importé")
except Exception as e:
    print(f"   ❌ Erreur Group: {e}")

try:
    print("3. Test import django.utils.translation...")
    from django.utils.translation import gettext_lazy as _
    print("   ✅ gettext_lazy importé")
except Exception as e:
    print(f"   ❌ Erreur gettext_lazy: {e}")

try:
    print("4. Test import django.core.validators...")
    from django.core.validators import MinValueValidator, MaxValueValidator
    print("   ✅ Validators importés")
except Exception as e:
    print(f"   ❌ Erreur validators: {e}")

try:
    print("5. Test import django.contrib.contenttypes...")
    from django.contrib.contenttypes.models import ContentType
    from django.contrib.contenttypes.fields import GenericForeignKey
    print("   ✅ ContentType importés")
except Exception as e:
    print(f"   ❌ Erreur ContentType: {e}")

try:
    print("6. Test import django.utils...")
    from django.utils import timezone
    print("   ✅ timezone importé")
except Exception as e:
    print(f"   ❌ Erreur timezone: {e}")

print("✅ Tests terminés")
