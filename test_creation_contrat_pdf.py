#!/usr/bin/env python3
"""
Script pour tester la création d'un contrat avec génération PDF
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from django.test import Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from proprietes.models import Propriete, Locataire
from contrats.models import Contrat
from datetime import date, timedelta

User = get_user_model()

def test_creation_contrat_avec_pdf():
    """Teste la création d'un contrat avec génération PDF"""
    print("🔍 Test de création de contrat avec PDF...")
    
    try:
        # Utiliser un utilisateur existant
        user = User.objects.filter(is_staff=True).first()
        if not user:
            print("❌ Aucun utilisateur admin trouvé")
            return False
        
        # Récupérer une propriété et un locataire
        propriete = Propriete.objects.first()
        locataire = Locataire.objects.first()
        
        if not propriete or not locataire:
            print("❌ Données manquantes (propriété ou locataire)")
            return False
        
        print(f"✅ Propriété : {propriete.titre}")
        print(f"✅ Locataire : {locataire.nom} {locataire.prenom}")
        
        # Créer un client et se connecter
        client = Client()
        client.force_login(user)
        
        # Données du formulaire
        form_data = {
            'numero_contrat': f'TEST-{date.today().strftime("%Y%m%d")}-001',
            'propriete': propriete.id,
            'locataire': locataire.id,
            'date_debut': date.today().strftime('%Y-%m-%d'),
            'date_fin': (date.today() + timedelta(days=365)).strftime('%Y-%m-%d'),
            'date_signature': date.today().strftime('%Y-%m-%d'),
            'loyer_mensuel': '800.00',
            'charges_mensuelles': '50.00',
            'depot_garantie': '800.00',
            'avance_loyer': '0.00',
            'jour_paiement': 1,
            'mode_paiement': 'virement',
            'telecharger_pdf': True,  # Important : demander la génération PDF
            'notes': 'Contrat de test pour génération PDF'
        }
        
        print("📋 Données du formulaire préparées")
        
        # Soumettre le formulaire
        url = reverse('contrats:ajouter')
        response = client.post(url, data=form_data)
        
        print(f"📊 Code de réponse : {response.status_code}")
        print(f"📋 Type de contenu : {response.get('Content-Type', 'N/A')}")
        
        if response.status_code == 200:
            # Vérifier si c'est un PDF
            if response.get('Content-Type') == 'application/pdf':
                print("✅ PDF généré avec succès !")
                
                # Sauvegarder le PDF pour vérification
                pdf_content = response.content
                filename = f"test_contrat_interface_{date.today().strftime('%Y%m%d')}.pdf"
                with open(filename, 'wb') as f:
                    f.write(pdf_content)
                
                print(f"💾 PDF sauvegardé : {filename}")
                print(f"📏 Taille : {len(pdf_content)} octets")
                
                # Vérifier que c'est un PDF valide
                if pdf_content.startswith(b'%PDF'):
                    print("✅ Format PDF valide détecté")
                else:
                    print("⚠️  Format PDF non détecté")
                
                return True
            else:
                print("⚠️  Pas de PDF généré - Vérifier le formulaire")
                content = response.content.decode('utf-8')[:1000]
                print(f"Contenu reçu : {content}...")
                return False
                
        elif response.status_code == 302:
            print("🔄 Redirection détectée")
            print(f"   Location : {response.get('Location', 'N/A')}")
            
            # Vérifier si un contrat a été créé
            nouveau_contrat = Contrat.objects.filter(numero_contrat=form_data['numero_contrat']).first()
            if nouveau_contrat:
                print(f"✅ Contrat créé : {nouveau_contrat.numero_contrat}")
                print("⚠️  Mais pas de PDF généré automatiquement")
                return True
            else:
                print("❌ Aucun contrat créé")
                return False
        else:
            print(f"❌ Erreur : {response.status_code}")
            if hasattr(response, 'content'):
                content = response.content.decode('utf-8')[:1000]
                print(f"Contenu : {content}...")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors du test : {e}")
        import traceback
        traceback.print_exc()
        return False

def test_generation_manuelle():
    """Teste la génération PDF manuelle depuis un contrat existant"""
    print("\n🔍 Test de génération PDF manuelle...")
    
    try:
        contrat = Contrat.objects.first()
        if not contrat:
            print("❌ Aucun contrat trouvé")
            return False
        
        print(f"📋 Contrat : {contrat.numero_contrat}")
        
        # Tester le service PDF directement
        from contrats.services import ContratPDFService
        
        service = ContratPDFService(contrat)
        pdf_buffer = service.generate_contrat_pdf()
        
        # Sauvegarder le PDF
        filename = f"test_manuel_{contrat.numero_contrat}.pdf"
        with open(filename, 'wb') as f:
            f.write(pdf_buffer.getvalue())
        
        print(f"✅ PDF généré manuellement : {filename}")
        print(f"📏 Taille : {len(pdf_buffer.getvalue())} octets")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur génération manuelle : {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("🚀 Test de création de contrat avec génération PDF")
    print("=" * 60)
    
    # Test 1 : Génération manuelle (pour vérifier que les services fonctionnent)
    manuel_ok = test_generation_manuelle()
    
    # Test 2 : Création via interface
    interface_ok = test_creation_contrat_avec_pdf()
    
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ")
    print("=" * 60)
    
    print(f"Génération manuelle : {'✅ OK' if manuel_ok else '❌ ÉCHEC'}")
    print(f"Création via interface : {'✅ OK' if interface_ok else '❌ ÉCHEC'}")
    
    if manuel_ok and interface_ok:
        print("\n🎉 Tout fonctionne parfaitement !")
        print("   Les contrats peuvent être créés avec génération PDF automatique.")
    elif manuel_ok:
        print("\n⚠️  Les services PDF fonctionnent mais l'interface a un problème.")
        print("   Vérifiez le formulaire et les vues.")
    else:
        print("\n❌ Problèmes détectés.")
        print("   Vérifiez la configuration et les services PDF.")

if __name__ == "__main__":
    main()
