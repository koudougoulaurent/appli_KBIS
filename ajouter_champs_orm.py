#!/usr/bin/env python
"""
Script pour ajouter dynamiquement les nouveaux champs numero_* aux modèles Django
"""

import os
import sys
import django
from django.conf import settings
from django.db import connection

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

def ajouter_champs_orm():
    """Ajoute dynamiquement les nouveaux champs numero_* aux modèles Django"""
    
    print("🔧 AJOUT DYNAMIQUE DES CHAMPS NUMERO_* AUX MODÈLES")
    print("=" * 60)
    
    # 1. Ajouter le champ numero_bailleur au modèle Bailleur
    print("\n👤 AJOUT DU CHAMP NUMERO_BAİLLEUR")
    print("-" * 40)
    
    try:
        from proprietes.models import Bailleur
        
        # Vérifier si le champ existe déjà
        if hasattr(Bailleur, 'numero_bailleur'):
            print("✅ Le champ numero_bailleur existe déjà dans le modèle")
        else:
            print("❌ Le champ numero_bailleur n'existe pas - ajout en cours...")
            
            # Ajouter le champ dynamiquement
            numero_bailleur_field = django.db.models.CharField(
                max_length=50,
                unique=True,
                null=True,
                blank=True,
                verbose_name='Numéro Bailleur',
                help_text='Numéro unique professionnel du bailleur'
            )
            
            # Ajouter le champ au modèle
            numero_bailleur_field.contribute_to_class(Bailleur, 'numero_bailleur')
            
            # Mettre à jour la base de données
            with connection.cursor() as cursor:
                cursor.execute("""
                    ALTER TABLE proprietes_bailleur 
                    ADD COLUMN numero_bailleur VARCHAR(50) UNIQUE
                """)
            
            print("✅ Champ numero_bailleur ajouté avec succès")
            
    except Exception as e:
        print(f"❌ Erreur lors de l'ajout du champ numero_bailleur: {e}")
    
    # 2. Ajouter le champ numero_locataire au modèle Locataire
    print("\n🏠 AJOUT DU CHAMP NUMERO_LOCATAIRE")
    print("-" * 40)
    
    try:
        from proprietes.models import Locataire
        
        # Vérifier si le champ existe déjà
        if hasattr(Locataire, 'numero_locataire'):
            print("✅ Le champ numero_locataire existe déjà dans le modèle")
        else:
            print("❌ Le champ numero_locataire n'existe pas - ajout en cours...")
            
            # Ajouter le champ dynamiquement
            numero_locataire_field = django.db.models.CharField(
                max_length=50,
                unique=True,
                null=True,
                blank=True,
                verbose_name='Numéro Locataire',
                help_text='Numéro unique professionnel du locataire'
            )
            
            # Ajouter le champ au modèle
            numero_locataire_field.contribute_to_class(Locataire, 'numero_locataire')
            
            # Mettre à jour la base de données
            with connection.cursor() as cursor:
                cursor.execute("""
                    ALTER TABLE proprietes_locataire 
                    ADD COLUMN numero_locataire VARCHAR(50) UNIQUE
                """)
            
            print("✅ Champ numero_locataire ajouté avec succès")
            
    except Exception as e:
        print(f"❌ Erreur lors de l'ajout du champ numero_locataire: {e}")
    
    # 3. Ajouter le champ numero_propriete au modèle Propriete
    print("\n🏘️ AJOUT DU CHAMP NUMERO_PROPRIETE")
    print("-" * 40)
    
    try:
        from proprietes.models import Propriete
        
        # Vérifier si le champ existe déjà
        if hasattr(Propriete, 'numero_propriete'):
            print("✅ Le champ numero_propriete existe déjà dans le modèle")
        else:
            print("❌ Le champ numero_propriete n'existe pas - ajout en cours...")
            
            # Ajouter le champ dynamiquement
            numero_propriete_field = django.db.models.CharField(
                max_length=50,
                unique=True,
                null=True,
                blank=True,
                verbose_name='Numéro Propriété',
                help_text='Numéro unique professionnel de la propriété'
            )
            
            # Ajouter le champ au modèle
            numero_propriete_field.contribute_to_class(Propriete, 'numero_propriete')
            
            # Mettre à jour la base de données
            with connection.cursor() as cursor:
                cursor.execute("""
                    ALTER TABLE proprietes_propriete 
                    ADD COLUMN numero_propriete VARCHAR(50) UNIQUE
                """)
            
            print("✅ Champ numero_propriete ajouté avec succès")
            
    except Exception as e:
        print(f"❌ Erreur lors de l'ajout du champ numero_propriete: {e}")
    
    # 4. Ajouter le champ numero_paiement au modèle Paiement
    print("\n💳 AJOUT DU CHAMP NUMERO_PAIEMENT")
    print("-" * 40)
    
    try:
        from paiements.models import Paiement
        
        # Vérifier si le champ existe déjà
        if hasattr(Paiement, 'numero_paiement'):
            print("✅ Le champ numero_paiement existe déjà dans le modèle")
        else:
            print("❌ Le champ numero_paiement n'existe pas - ajout en cours...")
            
            # Ajouter le champ dynamiquement
            numero_paiement_field = django.db.models.CharField(
                max_length=50,
                unique=True,
                null=True,
                blank=True,
                verbose_name='Numéro Paiement',
                help_text='Numéro unique professionnel du paiement'
            )
            
            # Ajouter le champ au modèle
            numero_paiement_field.contribute_to_class(Paiement, 'numero_paiement')
            
            # Mettre à jour la base de données
            with connection.cursor() as cursor:
                cursor.execute("""
                    ALTER TABLE paiements_paiement 
                    ADD COLUMN numero_paiement VARCHAR(50) UNIQUE
                """)
            
            print("✅ Champ numero_paiement ajouté avec succès")
            
    except Exception as e:
        print(f"❌ Erreur lors de l'ajout du champ numero_paiement: {e}")
    
    # 5. Vérification finale
    print("\n🔍 VÉRIFICATION FINALE")
    print("-" * 40)
    
    try:
        # Vérifier que tous les champs sont maintenant accessibles
        from proprietes.models import Bailleur, Locataire, Propriete
        from paiements.models import Paiement
        
        # Test d'accès aux champs
        bailleur_test = Bailleur.objects.first()
        if bailleur_test:
            try:
                numero = getattr(bailleur_test, 'numero_bailleur', None)
                print(f"✅ Accès au champ numero_bailleur: {numero}")
            except:
                print("❌ Impossible d'accéder au champ numero_bailleur")
        
        locataire_test = Locataire.objects.first()
        if locataire_test:
            try:
                numero = getattr(locataire_test, 'numero_locataire', None)
                print(f"✅ Accès au champ numero_locataire: {numero}")
            except:
                print("❌ Impossible d'accéder au champ numero_locataire")
        
        propriete_test = Propriete.objects.first()
        if propriete_test:
            try:
                numero = getattr(propriete_test, 'numero_propriete', None)
                print(f"✅ Accès au champ numero_propriete: {numero}")
            except:
                print("❌ Impossible d'accéder au champ numero_propriete")
        
        paiement_test = Paiement.objects.first()
        if paiement_test:
            try:
                numero = getattr(paiement_test, 'numero_paiement', None)
                print(f"✅ Accès au champ numero_paiement: {numero}")
            except:
                print("❌ Impossible d'accéder au champ numero_paiement")
                
    except Exception as e:
        print(f"❌ Erreur lors de la vérification finale: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Ajout des champs terminé!")

if __name__ == '__main__':
    ajouter_champs_orm()
