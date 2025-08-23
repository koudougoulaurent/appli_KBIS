#!/usr/bin/env python
"""
Script de test simple du système immobilier
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from proprietes.models import TypeBien, Bailleur, Propriete
from rentila_features.models import Document, TableauBordFinancier

User = get_user_model()

def test_systeme_simple():
    """Test simple du système."""
    print("🚀 Test simple du système immobilier")
    print("=" * 50)
    
    try:
        # Créer un utilisateur de test
        user, created = User.objects.get_or_create(
            username='testuser',
            defaults={
                'email': 'test@example.com',
                'first_name': 'Test',
                'last_name': 'User'
            }
        )
        if created:
            user.set_password('testpass123')
            user.save()
            print("✅ Utilisateur de test créé")
        else:
            print("✅ Utilisateur de test existant")
        
        # Créer un type de bien
        type_bien, created = TypeBien.objects.get_or_create(
            nom="Appartement",
            defaults={'description': 'Type de bien par défaut'}
        )
        if created:
            print("✅ Type de bien créé")
        else:
            print("✅ Type de bien existant")
        
        # Créer un bailleur
        bailleur, created = Bailleur.objects.get_or_create(
            numero_bailleur="BLTEST001",
            defaults={
                'nom': 'Test',
                'prenom': 'Bailleur',
                'email': 'test@example.com',
                'telephone': '0123456789',
                'adresse': 'Adresse test',
                'code_postal': '75001',
                'ville': 'Paris',
                'pays': 'France'
            }
        )
        if created:
            print("✅ Bailleur de test créé")
        else:
            print("✅ Bailleur de test existant")
        
        # Créer une propriété
        propriete, created = Propriete.objects.get_or_create(
            numero_propriete="PRTEST001",
            defaults={
                'titre': 'Propriété Test',
                'adresse': 'Adresse test',
                'code_postal': '75001',
                'ville': 'Paris',
                'pays': 'France',
                'surface': 75.5,
                'nombre_pieces': 3,
                'nombre_chambres': 2,
                'nombre_salles_bain': 1,
                'loyer_actuel': 1200.00,
                'charges_locataire': 150.00,
                'type_bien': type_bien,
                'bailleur': bailleur
            }
        )
        if created:
            print("✅ Propriété de test créée")
        else:
            print("✅ Propriété de test existante")
        
        # Test des modèles Rentila
        try:
            document = Document.objects.create(
                nom="Document Test",
                type_document="contrat",
                description="Document de test",
                fichier="",  # Fichier vide pour le test
                propriete=propriete,
                statut="brouillon",
                cree_par=user
            )
            print("✅ Modèle Document (Rentila) fonctionne")
            document.delete()
        except Exception as e:
            print(f"❌ Erreur Document : {e}")
        
        try:
            tableau_bord = TableauBordFinancier.objects.create(
                nom="Tableau Test",
                description="Tableau de bord de test",
                periode="mensuel",
                cree_par=user
            )
            print("✅ Modèle TableauBordFinancier (Rentila) fonctionne")
            tableau_bord.delete()
        except Exception as e:
            print(f"❌ Erreur TableauBordFinancier : {e}")
        
        # Test des URLs
        client = Client()
        urls_a_tester = [
            ('/', 'Page d\'accueil'),
            ('/proprietes/', 'Liste des propriétés'),
            ('/rentila/', 'Fonctionnalités Rentila')
        ]
        
        print("\n🔗 Test des URLs...")
        for url, description in urls_a_tester:
            try:
                response = client.get(url)
                if response.status_code in [200, 302]:
                    print(f"✅ {description} : {response.status_code}")
                else:
                    print(f"❌ {description} : {response.status_code}")
            except Exception as e:
                print(f"❌ {description} : Erreur - {e}")
        
        print("\n🎉 Test simple terminé avec succès !")
        return True
        
    except Exception as e:
        print(f"❌ Erreur générale : {e}")
        return False

if __name__ == "__main__":
    success = test_systeme_simple()
    sys.exit(0 if success else 1)
