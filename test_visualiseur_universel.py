#!/usr/bin/env python
"""
Script de test pour le visualiseur universel de documents
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from django.urls import reverse
from proprietes.models import Document
from proprietes.document_settings import get_viewer_config, is_format_viewable

def test_viewer_urls():
    """Teste les URLs du visualiseur"""
    print("🔍 Test des URLs du Visualiseur Universel")
    print("=" * 60)
    
    if not Document.objects.exists():
        print("⚠️ Aucun document en base pour tester")
        return
    
    document = Document.objects.first()
    
    urls_to_test = [
        ('document_viewer', 'Visualiseur principal'),
        ('document_content_view', 'Contenu textuel'),
        ('document_pdf_viewer', 'Visualiseur PDF'),
        ('document_secure_proxy', 'Proxy sécurisé'),
    ]
    
    for url_name, description in urls_to_test:
        try:
            url = reverse(f'proprietes:{url_name}', args=[document.pk])
            print(f"✅ {description}: {url}")
        except Exception as e:
            print(f"❌ {description}: ERREUR - {e}")

def test_format_support():
    """Teste le support des différents formats"""
    print("\n🎨 Test du Support des Formats")
    print("=" * 60)
    
    test_files = [
        'document.pdf',
        'image.jpg',
        'presentation.pptx',
        'spreadsheet.xlsx',
        'text.txt',
        'code.py',
        'archive.zip',
        'unknown.xyz'
    ]
    
    for filename in test_files:
        ext = os.path.splitext(filename)[1]
        is_viewable, format_type = is_format_viewable(ext)
        
        status = "✅ Supporté" if is_viewable else "⚠️ Téléchargement uniquement"
        type_info = f"({format_type})" if format_type else ""
        
        print(f"{status} {filename} {type_info}")

def test_configuration():
    """Teste la configuration du visualiseur"""
    print("\n⚙️ Test de la Configuration")
    print("=" * 60)
    
    config = get_viewer_config()
    
    print(f"✅ Taille max en ligne: {config['MAX_INLINE_SIZE'] / (1024*1024):.1f}MB")
    print(f"✅ Taille max texte: {config['MAX_TEXT_SIZE'] / (1024*1024):.1f}MB")
    print(f"✅ Cache activé: {config['SECURITY']['ENABLE_CACHE']}")
    print(f"✅ Log des accès: {config['SECURITY']['LOG_ACCESS']}")
    
    print(f"\n📁 Formats supportés:")
    for format_type, extensions in config['VIEWABLE_FORMATS'].items():
        print(f"  {format_type}: {', '.join(extensions)}")

def test_document_examples():
    """Teste avec des documents existants"""
    print("\n📄 Test avec Documents Existants")
    print("=" * 60)
    
    documents = Document.objects.all()[:5]
    
    if not documents:
        print("⚠️ Aucun document en base")
        return
    
    for doc in documents:
        print(f"\n📋 Document: {doc.nom}")
        print(f"   Type: {doc.get_type_document_display()}")
        print(f"   Confidentiel: {'Oui' if doc.confidentiel else 'Non'}")
        
        if doc.fichier:
            ext = os.path.splitext(doc.fichier.name)[1]
            is_viewable, format_type = is_format_viewable(ext)
            print(f"   Fichier: {doc.fichier.name}")
            print(f"   Extension: {ext}")
            print(f"   Visualisable: {'✅ Oui' if is_viewable else '⚠️ Non'} {f'({format_type})' if format_type else ''}")
        else:
            print(f"   ❌ Aucun fichier attaché")

def main():
    """Fonction principale"""
    print("🚀 Test du Visualiseur Universel de Documents")
    print("=" * 80)
    
    test_viewer_urls()
    test_format_support()
    test_configuration()
    test_document_examples()
    
    print("\n🎉 Tests du Visualiseur Terminés!")
    print("=" * 80)
    print("\n💡 Pour tester en live:")
    print("   1. Démarrez le serveur: python manage.py runserver")
    print("   2. Allez sur: http://127.0.0.1:8000/proprietes/documents/")
    print("   3. Cliquez sur 'Visualiser' pour un document")
    print("   4. Testez les différents formats et visualiseurs")

if __name__ == "__main__":
    main()
