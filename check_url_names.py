#!/usr/bin/env python
"""
Script de vérification des noms d'URLs dans les templates
Vérifie que tous les noms d'URLs utilisés dans les templates existent
"""

import os
import re
import sys
from django.conf import settings
from django.urls import get_resolver

def get_all_url_names():
    """Récupère tous les noms d'URLs définis dans l'application"""
    resolver = get_resolver()
    url_names = set()
    
    def collect_urls(url_patterns, namespace=''):
        for pattern in url_patterns:
            if hasattr(pattern, 'url_patterns'):
                # Namespace
                new_namespace = f"{namespace}:{pattern.namespace}" if namespace else pattern.namespace
                collect_urls(pattern.url_patterns, new_namespace)
            elif hasattr(pattern, 'name') and pattern.name:
                # URL avec nom
                full_name = f"{namespace}:{pattern.name}" if namespace else pattern.name
                url_names.add(full_name)
    
    collect_urls(resolver.url_patterns)
    return url_names

def find_url_references_in_templates():
    """Trouve toutes les références d'URLs dans les templates"""
    template_dir = 'templates'
    url_references = []
    
    for root, dirs, files in os.walk(template_dir):
        for file in files:
            if file.endswith('.html'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    # Recherche des patterns {% url 'namespace:name' %}
                    pattern = r"{%\s*url\s+['\"]([^'\"]+)['\"]"
                    matches = re.findall(pattern, content)
                    
                    for match in matches:
                        url_references.append({
                            'file': file_path,
                            'url_name': match
                        })
                        
                except Exception as e:
                    print(f"Erreur lors de la lecture de {file_path}: {e}")
    
    return url_references

def check_url_names():
    """Vérifie que tous les noms d'URLs utilisés existent"""
    print("🔍 Vérification des noms d'URLs dans les templates...")
    
    # Configuration Django minimale
    if not settings.configured:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
        import django
        django.setup()
    
    # Récupération des noms d'URLs définis
    defined_urls = get_all_url_names()
    print(f"✅ {len(defined_urls)} noms d'URLs définis")
    
    # Récupération des références dans les templates
    url_references = find_url_references_in_templates()
    print(f"📄 {len(url_references)} références d'URLs trouvées dans les templates")
    
    # Vérification
    errors = []
    for ref in url_references:
        if ref['url_name'] not in defined_urls:
            errors.append({
                'file': ref['file'],
                'url_name': ref['url_name']
            })
    
    # Affichage des résultats
    if errors:
        print(f"\n❌ {len(errors)} erreurs trouvées :")
        for error in errors:
            print(f"  - {error['file']} : '{error['url_name']}'")
    else:
        print("\n✅ Aucune erreur trouvée ! Tous les noms d'URLs sont valides.")
    
    return len(errors) == 0

if __name__ == '__main__':
    success = check_url_names()
    sys.exit(0 if success else 1)

