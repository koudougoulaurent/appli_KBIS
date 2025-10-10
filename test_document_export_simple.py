#!/usr/bin/env python
"""
Script de test simple pour le module d'export des documents
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

def test_imports():
    """Test des imports"""
    print("Test des imports...")
    
    try:
        from proprietes.document_export_views import document_export
        print("OK - Import des vues d'export reussi")
        
        from proprietes.services.export_documents import DocumentExportService
        print("OK - Import du service d'export reussi")
        
        from proprietes.forms import DocumentSearchForm
        print("OK - Import du formulaire de recherche reussi")
        
        return True
        
    except Exception as e:
        print(f"ERREUR d'import: {str(e)}")
        return False

def test_export_service():
    """Test du service d'export des documents"""
    print("Test du service d'export des documents...")
    
    try:
        from proprietes.services.export_documents import DocumentExportService
        from proprietes.models import Document
        
        # Récupérer quelques documents pour le test
        documents = Document.objects.all()[:5]
        print(f"{documents.count()} documents trouves pour le test")
        
        # Créer le service d'export
        export_service = DocumentExportService()
        print("Service d'export cree avec succes")
        
        # Test des statistiques
        stats = export_service.get_export_statistics(documents)
        print(f"Statistiques calculees: {stats['total_documents']} documents")
        
        print("Tous les tests sont passes avec succes !")
        return True
        
    except Exception as e:
        print(f"ERREUR lors du test: {str(e)}")
        return False

if __name__ == "__main__":
    print("Demarrage des tests du module d'export des documents")
    print("=" * 60)
    
    # Test des imports
    if not test_imports():
        print("ECHEC des tests d'import")
        sys.exit(1)
    
    print()
    
    # Test du service d'export
    if not test_export_service():
        print("ECHEC des tests du service")
        sys.exit(1)
    
    print()
    print("Tous les tests sont passes avec succes !")
    print("Le module d'export des documents est pret a etre utilise")
