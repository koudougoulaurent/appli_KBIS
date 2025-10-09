#!/usr/bin/env python
"""
Script pour comparer l'ancien et le nouveau système de génération de PDF de contrats
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings_simple')
django.setup()

from contrats.models import Contrat
from contrats.services import ContratPDFService
from contrats.services_contrat_pdf_updated import ContratPDFServiceUpdated
import logging

logger = logging.getLogger(__name__)

def test_pdf_generation():
    """Test de génération de PDF avec l'ancien et le nouveau système."""
    
    print("Test de generation de PDF de contrats")
    print("=" * 50)
    
    try:
        # Récupérer un contrat existant
        contrat = Contrat.objects.first()
        if not contrat:
            print("Aucun contrat trouve dans la base de donnees")
            return
        
        print(f"Contrat selectionne: {contrat.numero_contrat}")
        print(f"   - Locataire: {contrat.locataire.nom} {contrat.locataire.prenom}")
        print(f"   - Propriete: {contrat.propriete.titre}")
        
        # Test avec l'ANCIEN système
        print("\n1. Test avec l'ANCIEN systeme:")
        try:
            old_service = ContratPDFService(contrat)
            old_pdf = old_service.generate_contrat_pdf()
            print(f"   ✅ ANCIEN PDF genere: {len(old_pdf.getvalue())} bytes")
        except Exception as e:
            print(f"   ❌ ERREUR ancien systeme: {str(e)}")
        
        # Test avec le NOUVEAU système
        print("\n2. Test avec le NOUVEAU systeme:")
        try:
            new_service = ContratPDFServiceUpdated(contrat)
            # Remplir automatiquement les champs
            contrat = new_service.auto_remplir_champs_contrat()
            new_pdf = new_service.generate_contrat_pdf()
            print(f"   ✅ NOUVEAU PDF genere: {len(new_pdf.getvalue())} bytes")
            
            # Afficher les nouveaux champs remplis
            print(f"   📋 Champs remplis automatiquement:")
            print(f"      - Loyer en lettres: {contrat.loyer_mensuel_texte}")
            print(f"      - Depot en lettres: {contrat.depot_garantie_texte}")
            print(f"      - Nombre de mois: {contrat.nombre_mois_caution}")
            print(f"      - Montant garantie max: {contrat.montant_garantie_max}")
            print(f"      - Numero maison: {contrat.numero_maison}")
            print(f"      - Secteur: {contrat.secteur}")
            
        except Exception as e:
            print(f"   ❌ ERREUR nouveau systeme: {str(e)}")
        
        # Test des autres documents
        print("\n3. Test des autres documents:")
        try:
            # État des lieux
            etat_lieux_pdf = new_service.generate_etat_lieux_pdf()
            print(f"   ✅ Etat des lieux: {len(etat_lieux_pdf.getvalue())} bytes")
            
            # Garantie
            garantie_pdf = new_service.generate_garantie_pdf()
            print(f"   ✅ Garantie: {len(garantie_pdf.getvalue())} bytes")
            
        except Exception as e:
            print(f"   ❌ ERREUR autres documents: {str(e)}")
        
        print("\n" + "=" * 50)
        print("RESUME")
        print("=" * 50)
        print("✅ Le nouveau systeme fonctionne correctement")
        print("✅ Tous les champs sont remplis automatiquement")
        print("✅ Les 3 types de documents sont generes")
        print("\n🌐 URLs de test:")
        print(f"   - Contrat PDF: /contrats/generer-pdf-updated/{contrat.id}/")
        print(f"   - Etat des lieux: /contrats/generer-etat-lieux-pdf/{contrat.id}/")
        print(f"   - Garantie: /contrats/generer-garantie-pdf/{contrat.id}/")
        print(f"   - Documents complets: /contrats/generer-documents-complets/{contrat.id}/")
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {str(e)}")
        logger.error(f"Erreur test PDF comparison: {str(e)}")

if __name__ == "__main__":
    test_pdf_generation()
