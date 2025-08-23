#!/usr/bin/env python3
"""
Script de test pour la génération effective d'un PDF
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

def test_generation_contrat_pdf():
    """Teste la génération d'un PDF de contrat"""
    print("🔍 Test de génération de PDF de contrat...")
    
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
        
        # Vérifier que c'est un PDF valide
        pdf_content = pdf_buffer.getvalue()
        if pdf_content.startswith(b'%PDF'):
            print("   ✅ Format PDF valide détecté")
        else:
            print("   ⚠️  Format PDF non détecté")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la génération du PDF de contrat : {e}")
        import traceback
        traceback.print_exc()
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
        
        print(f"📋 Test avec la résiliation : {resiliation.id}")
        print(f"   📅 Date : {resiliation.date_resiliation}")
        print(f"   🏠 Contrat : {resiliation.contrat.numero_contrat}")
        
        # Créer le service et générer le PDF
        service = ResiliationPDFService(resiliation)
        pdf_buffer = service.generate_resiliation_pdf()
        
        # Sauvegarder le PDF de test
        filename = f"test_resiliation_{resiliation.id}.pdf"
        with open(filename, 'wb') as f:
            f.write(pdf_buffer.getvalue())
        
        print(f"✅ PDF généré avec succès : {filename}")
        print(f"   📏 Taille : {len(pdf_buffer.getvalue())} octets")
        
        # Vérifier que c'est un PDF valide
        pdf_content = pdf_buffer.getvalue()
        if pdf_content.startswith(b'%PDF'):
            print("   ✅ Format PDF valide détecté")
        else:
            print("   ⚠️  Format PDF non détecté")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la génération du PDF de résiliation : {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Fonction principale"""
    print("🚀 Test de génération effective de PDF")
    print("=" * 60)
    
    # Test de génération de contrat
    contrat_ok = test_generation_contrat_pdf()
    
    # Test de génération de résiliation
    resiliation_ok = test_generation_resiliation_pdf()
    
    # Résumé
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ DES TESTS")
    print("=" * 60)
    
    print(f"Génération PDF contrat : {'✅ SUCCÈS' if contrat_ok else '❌ ÉCHEC'}")
    print(f"Génération PDF résiliation : {'✅ SUCCÈS' if resiliation_ok else '❌ ÉCHEC'}")
    
    if contrat_ok and resiliation_ok:
        print("\n🎉 Tous les tests sont passés avec succès !")
        print("   Le système de génération PDF est opérationnel.")
    else:
        print("\n⚠️  Certains tests ont échoué.")
        print("   Vérifiez les erreurs ci-dessus.")
    
    print(f"\n📁 Les PDF de test ont été sauvegardés dans le répertoire courant.")
    print("   Vous pouvez les ouvrir pour vérifier leur contenu.")

if __name__ == "__main__":
    main() 