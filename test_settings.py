#!/usr/bin/env python
"""
Test direct du fichier settings
"""
import os
from pathlib import Path

# Simuler __file__
__file__ = 'gestion_immobiliere/settings_postgresql.py'

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Configuration de base
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-change-me-in-production')
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
ALLOWED_HOSTS = ['*']

# Database PostgreSQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'kbis_immobilier',
        'USER': 'kbis_user',
        'PASSWORD': 'qN64K1DDSffwfTPThqEPgtsH5sVwwKGP',
        'HOST': 'dpg-d3og40k9c44c73cvh1h0-a.oregon-postgres.render.com',
        'PORT': '5432',
        'OPTIONS': {
            'sslmode': 'require',
        },
    }
}

print("Configuration chargee")
print(f"DATABASES: {DATABASES}")
print(f"ENGINE: {DATABASES['default']['ENGINE']}")
print(f"NAME: {DATABASES['default']['NAME']}")
print(f"HOST: {DATABASES['default']['HOST']}")
print("Test reussi!")
