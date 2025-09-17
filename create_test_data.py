#!/usr/bin/env python
"""
Script pour créer des données de test minimales
"""
import os
import django
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from utilisateurs.models import Utilisateur, GroupeTravail
from contrats.models import Contrat
from proprietes.models import Propriete, Locataire, Bailleur, TypeBien
from decimal import Decimal
from datetime import date, timedelta

def create_test_data():
    """Créer des données de test minimales"""
    print("🚀 Création des données de test...")
    
    try:
        # 1. Créer un type de bien
        type_bien, created = TypeBien.objects.get_or_create(
            nom='Appartement',
            defaults={'description': 'Type de bien pour test'}
        )
        print(f"✅ Type de bien: {type_bien}")
        
        # 2. Créer un bailleur
        bailleur, created = Bailleur.objects.get_or_create(
            nom='Dupont',
            defaults={
                'prenom': 'Jean',
                'email': 'jean.dupont@example.com',
                'telephone': '0123456789'
            }
        )
        print(f"✅ Bailleur: {bailleur}")
        
        # 3. Créer une propriété
        propriete, created = Propriete.objects.get_or_create(
            numero_propriete='PR001',
            defaults={
                'titre': 'Appartement Test',
                'description': 'Appartement pour test',
                'type_bien': type_bien,
                'bailleur': bailleur,
                'adresse': '123 Rue Test',
                'ville': 'Paris',
                'code_postal': '75001',
                'etat': 'excellent'
            }
        )
        print(f"✅ Propriété: {propriete}")
        
        # 4. Créer un locataire
        locataire, created = Locataire.objects.get_or_create(
            nom='Martin',
            defaults={
                'prenom': 'Pierre',
                'email': 'pierre.martin@example.com',
                'telephone': '0987654321'
            }
        )
        print(f"✅ Locataire: {locataire}")
        
        # 5. Créer un contrat
        contrat, created = Contrat.objects.get_or_create(
            propriete=propriete,
            locataire=locataire,
            defaults={
                'date_debut': date.today(),
                'date_fin': date.today() + timedelta(days=365),
                'loyer_mensuel': Decimal('500.00'),
                'charges_mensuelles': Decimal('50.00'),
                'caution': Decimal('1000.00'),
                'statut': 'actif'
            }
        )
        print(f"✅ Contrat: {contrat}")
        
        print("\n🎉 Données de test créées avec succès!")
        
    except Exception as e:
        print(f"❌ Erreur lors de la création des données: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_test_data()
