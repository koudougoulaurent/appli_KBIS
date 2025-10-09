#!/usr/bin/env python
"""
Script de test pour vérifier le système de contrats mis à jour
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'appli_KBIS.settings')
django.setup()

from contrats.models import Contrat
from contrats.services_contrat_pdf_updated import ContratPDFServiceUpdated
from core.models import ConfigurationEntreprise
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_contrat_updated():
    """Test du système de contrats mis à jour."""
    
    print("Test du systeme de contrats mis a jour")
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
        print(f"   - Loyer: {contrat.loyer_mensuel}")
        print(f"   - Depot: {contrat.depot_garantie}")
        
        # Créer le service
        service = ContratPDFServiceUpdated(contrat)
        
        # Remplir automatiquement les champs
        print("\nRemplissage automatique des champs...")
        contrat = service.auto_remplir_champs_contrat()
        
        print("Champs remplis automatiquement:")
        print(f"   - Loyer en lettres: {contrat.loyer_mensuel_texte}")
        print(f"   - Loyer en chiffres: {contrat.loyer_mensuel_numerique}")
        print(f"   - Depot en lettres: {contrat.depot_garantie_texte}")
        print(f"   - Depot en chiffres: {contrat.depot_garantie_numerique}")
        print(f"   - Nombre de mois: {contrat.nombre_mois_caution}")
        print(f"   - Montant garantie max: {contrat.montant_garantie_max}")
        print(f"   - Montant garantie max en lettres: {contrat.montant_garantie_max_texte}")
        print(f"   - Mois debut paiement: {contrat.mois_debut_paiement}")
        print(f"   - Numero maison: {contrat.numero_maison}")
        print(f"   - Secteur: {contrat.secteur}")
        
        # Tester la génération de PDF
        print("\nTest de generation de PDF...")
        
        # Test contrat PDF
        try:
            contrat_pdf = service.generate_contrat_pdf()
            print("PDF du contrat genere avec succes")
            print(f"   - Taille: {len(contrat_pdf.getvalue())} bytes")
        except Exception as e:
            print(f"Erreur generation PDF contrat: {str(e)}")
        
        # Test état des lieux PDF
        try:
            etat_lieux_pdf = service.generate_etat_lieux_pdf()
            print("PDF de l'etat des lieux genere avec succes")
            print(f"   - Taille: {len(etat_lieux_pdf.getvalue())} bytes")
        except Exception as e:
            print(f"Erreur generation PDF etat des lieux: {str(e)}")
        
        # Test garantie PDF
        try:
            garantie_pdf = service.generate_garantie_pdf()
            print("PDF de la garantie genere avec succes")
            print(f"   - Taille: {len(garantie_pdf.getvalue())} bytes")
        except Exception as e:
            print(f"Erreur generation PDF garantie: {str(e)}")
        
        # Afficher les URLs de test
        print("\nURLs de test disponibles:")
        print(f"   - Contrat PDF: /contrats/generer-pdf-updated/{contrat.id}/")
        print(f"   - Etat des lieux PDF: /contrats/generer-etat-lieux-pdf/{contrat.id}/")
        print(f"   - Garantie PDF: /contrats/generer-garantie-pdf/{contrat.id}/")
        print(f"   - Documents complets: /contrats/generer-documents-complets/{contrat.id}/")
        print(f"   - Auto-remplir: /contrats/auto-remplir/{contrat.id}/")
        
        print("\nTest termine avec succes!")
        
    except Exception as e:
        print(f"Erreur lors du test: {str(e)}")
        logger.error(f"Erreur test contrat updated: {str(e)}")

def test_migration_contrats():
    """Test de la migration des contrats existants."""
    
    print("\nTest de la migration des contrats existants")
    print("=" * 50)
    
    try:
        # Compter les contrats
        total_contrats = Contrat.objects.count()
        contrats_avec_champs = Contrat.objects.filter(
            loyer_mensuel_texte__isnull=False,
            depot_garantie_texte__isnull=False
        ).count()
        
        print(f"Statistiques des contrats:")
        print(f"   - Total: {total_contrats}")
        print(f"   - Avec champs remplis: {contrats_avec_champs}")
        print(f"   - A migrer: {total_contrats - contrats_avec_champs}")
        
        if total_contrats - contrats_avec_champs > 0:
            print("\nPour migrer les contrats existants, executez:")
            print("   python manage.py migrate_contracts_template")
            print("   python manage.py migrate_contracts_template --dry-run  # Pour voir ce qui sera fait")
        else:
            print("Tous les contrats sont deja migres!")
        
    except Exception as e:
        print(f"Erreur lors du test de migration: {str(e)}")

if __name__ == "__main__":
    test_contrat_updated()
    test_migration_contrats()
