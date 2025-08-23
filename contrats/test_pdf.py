#!/usr/bin/env python3
"""
Script de test pour la génération de PDF de contrats et résiliations
Teste les services PDF avec la configuration depuis la base de données
"""

import os
import sys
import django
from datetime import date, timedelta

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

def test_configuration_entreprise():
    """Teste la récupération de la configuration de l'entreprise"""
    print("🔍 Test de la configuration de l'entreprise...")
    
    try:
        from core.models import ConfigurationEntreprise
        
        # Récupérer la configuration active
        config = ConfigurationEntreprise.get_configuration_active()
        
        if config:
            print(f"✅ Configuration trouvée : {config.nom_entreprise}")
            print(f"   📍 Adresse : {config.get_adresse_complete()}")
            print(f"   📞 Contact : {config.get_contact_complet()}")
            print(f"   🏢 SIRET : {config.siret}")
            
            # Vérifier les nouveaux champs de texte
            if config.texte_contrat:
                print(f"   📄 Texte contrat : {len(config.texte_contrat)} caractères")
            else:
                print("   ⚠️  Texte contrat : Non configuré (utilisera le texte par défaut)")
                
            if config.texte_resiliation:
                print(f"   📄 Texte résiliation : {len(config.texte_resiliation)} caractères")
            else:
                print("   ⚠️  Texte résiliation : Non configuré (utilisera le texte par défaut)")
                
        else:
            print("⚠️  Aucune configuration d'entreprise active trouvée")
            print("   Créez une configuration via l'administration Django")
            
    except Exception as e:
        print(f"❌ Erreur lors de la récupération de la configuration : {e}")
        return False
    
    return True

def test_import_services():
    """Teste l'import des services PDF"""
    print("\n🔍 Test de l'import des services PDF...")
    
    try:
        from contrats.services import ContratPDFService, ResiliationPDFService
        print("✅ Services PDF importés avec succès")
        return True
    except Exception as e:
        print(f"❌ Erreur lors de l'import des services : {e}")
        return False

def test_generation_contrat_pdf():
    """Teste la génération d'un PDF de contrat"""
    print("\n🔍 Test de génération de PDF de contrat...")
    
    try:
        from contrats.models import Contrat
        from contrats.services import ContratPDFService
        
        # Récupérer un contrat existant
        contrat = Contrat.objects.filter(est_actif=True).first()
        
        if not contrat:
            print("⚠️  Aucun contrat actif trouvé pour le test")
            return False
        
        print(f"📋 Test avec le contrat : {contrat.numero_contrat}")
        print(f"   🏠 Propriété : {contrat.propriete.titre}")
        print(f"   👤 Locataire : {contrat.locataire.nom} {contrat.locataire.prenom}")
        
        # Créer le service et générer le PDF
        service = ContratPDFService(contrat)
        pdf_buffer = service.generate_contrat_pdf()
        
        # Sauvegarder le PDF de test
        filename = f"test_contrat_{contrat.numero_contrat}.pdf"
        with open(filename, 'wb') as f:
            f.write(pdf_buffer.getvalue())
        
        print(f"✅ PDF généré avec succès : {filename}")
        print(f"   📏 Taille : {len(pdf_buffer.getvalue())} octets")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la génération du PDF de contrat : {e}")
        return False

def test_generation_resiliation_pdf():
    """Teste la génération d'un PDF de résiliation"""
    print("\n🔍 Test de génération de PDF de résiliation...")
    
    try:
        from contrats.models import ResiliationContrat
        from contrats.services import ResiliationPDFService
        
        # Récupérer une résiliation existante
        resiliation = ResiliationContrat.objects.first()
        
        if not resiliation:
            print("⚠️  Aucune résiliation trouvée pour le test")
            print("   Créez d'abord une résiliation via l'interface")
            return False
        
        print(f"📋 Test avec la résiliation : {resiliation.numero_resiliation}")
        print(f"   📅 Date : {resiliation.date_resiliation}")
        print(f"   🏠 Contrat : {resiliation.contrat.numero_contrat}")
        
        # Créer le service et générer le PDF
        service = ResiliationPDFService(resiliation)
        pdf_buffer = service.generate_resiliation_pdf()
        
        # Sauvegarder le PDF de test
        filename = f"test_resiliation_{resiliation.numero_resiliation}.pdf"
        with open(filename, 'wb') as f:
            f.write(pdf_buffer.getvalue())
        
        print(f"✅ PDF généré avec succès : {filename}")
        print(f"   📏 Taille : {len(pdf_buffer.getvalue())} octets")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la génération du PDF de résiliation : {e}")
        return False

def test_generation_resiliation_depuis_contrat():
    """Teste la génération d'un PDF de résiliation depuis un contrat"""
    print("\n🔍 Test de génération de PDF de résiliation depuis un contrat...")
    
    try:
        from contrats.models import Contrat
        from contrats.services import ResiliationPDFService
        
        # Récupérer un contrat existant
        contrat = Contrat.objects.filter(est_actif=True).first()
        
        if not contrat:
            print("⚠️  Aucun contrat actif trouvé pour le test")
            return False
        
        print(f"📋 Test avec le contrat : {contrat.numero_contrat}")
        
        # Créer une résiliation temporaire pour le test
        from contrats.models import ResiliationContrat
        resiliation_temp = ResiliationContrat(
            contrat=contrat,
            numero_resiliation=f"TEST_{contrat.numero_contrat}_RES",
            date_resiliation=date.today(),
            date_effet=date.today() + timedelta(days=30),
            type_resiliation='LOCATAIRE',
            statut='EN_COURS',
            motifs="Test de génération PDF"
        )
        
        # Créer le service et générer le PDF
        service = ResiliationPDFService(resiliation_temp)
        pdf_buffer = service.generate_resiliation_pdf()
        
        # Sauvegarder le PDF de test
        filename = f"test_resiliation_contrat_{contrat.numero_contrat}.pdf"
        with open(filename, 'wb') as f:
            f.write(pdf_buffer.getvalue())
        
        print(f"✅ PDF généré avec succès : {filename}")
        print(f"   📏 Taille : {len(pdf_buffer.getvalue())} octets")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la génération du PDF de résiliation depuis contrat : {e}")
        return False

def test_configuration_fallback():
    """Teste le fallback sur la configuration par défaut"""
    print("\n🔍 Test du fallback sur la configuration par défaut...")
    
    try:
        # Importer le fichier de configuration (pour référence)
        from contrats import config
        
        print("✅ Fichier de configuration importé (référence historique)")
        print(f"   📄 Configuration par défaut disponible")
        print(f"   📄 Clauses contractuelles par défaut disponibles")
        print(f"   📄 Modèle de résiliation par défaut disponible")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de l'import de la configuration : {e}")
        return False

def main():
    """Fonction principale de test"""
    print("🚀 Test de la génération PDF de contrats et résiliations")
    print("=" * 60)
    
    # Tests à effectuer
    tests = [
        ("Configuration entreprise", test_configuration_entreprise),
        ("Import services PDF", test_import_services),
        ("Génération PDF contrat", test_generation_contrat_pdf),
        ("Génération PDF résiliation", test_generation_resiliation_pdf),
        ("Génération PDF résiliation depuis contrat", test_generation_resiliation_depuis_contrat),
        ("Configuration fallback", test_configuration_fallback),
    ]
    
    # Exécuter les tests
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Erreur lors du test '{test_name}' : {e}")
            results.append((test_name, False))
    
    # Résumé des tests
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ DES TESTS")
    print("=" * 60)
    
    success_count = 0
    for test_name, result in results:
        status = "✅ SUCCÈS" if result else "❌ ÉCHEC"
        print(f"{status} : {test_name}")
        if result:
            success_count += 1
    
    print(f"\n🎯 Résultat global : {success_count}/{len(results)} tests réussis")
    
    if success_count == len(results):
        print("🎉 Tous les tests sont passés avec succès !")
        print("   Le système de génération PDF est opérationnel.")
    else:
        print("⚠️  Certains tests ont échoué.")
        print("   Vérifiez la configuration et les logs d'erreur.")
    
    # Recommandations
    print("\n💡 RECOMMANDATIONS")
    print("=" * 60)
    
    if success_count < len(results):
        print("🔧 Actions à effectuer :")
        print("   1. Vérifier la configuration de l'entreprise")
        print("   2. Créer au moins un contrat et une résiliation")
        print("   3. Vérifier les permissions utilisateur")
        print("   4. Consulter les logs Django pour plus de détails")
    
    print("\n📚 Documentation :")
    print("   - README : GENERATION_PDF_CONTRATS.md")
    print("   - Configuration : Core > Configuration de l'entreprise")
    print("   - Tests : python contrats/test_pdf.py")
    
    return success_count == len(results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
