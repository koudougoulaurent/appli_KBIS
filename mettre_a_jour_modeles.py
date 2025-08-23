#!/usr/bin/env python
"""
Script pour mettre à jour les modèles Django avec les nouveaux champs numero_*
"""

import os
import sys
import django
from django.conf import settings

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

def mettre_a_jour_modeles():
    """Met à jour les modèles Django avec les nouveaux champs numero_*"""
    
    print("🔧 MISE À JOUR DES MODÈLES DJANGO")
    print("=" * 60)
    
    # 1. Mettre à jour le modèle Bailleur
    print("\n👤 MISE À JOUR DU MODÈLE BAİLLEUR")
    print("-" * 40)
    
    try:
        from proprietes.models import Bailleur
        
        # Vérifier si le champ numero_bailleur existe déjà
        if hasattr(Bailleur, 'numero_bailleur'):
            print("✅ Le champ numero_bailleur existe déjà")
        else:
            print("❌ Le champ numero_bailleur n'existe pas - ajout en cours...")
            
            # Ajouter le champ via une migration personnalisée
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("""
                    ALTER TABLE proprietes_bailleur 
                    ADD COLUMN numero_bailleur VARCHAR(50) UNIQUE
                """)
            print("✅ Champ numero_bailleur ajouté à la base de données")
            
    except Exception as e:
        print(f"❌ Erreur lors de la mise à jour du modèle Bailleur: {e}")
    
    # 2. Mettre à jour le modèle Locataire
    print("\n🏠 MISE À JOUR DU MODÈLE LOCATAIRE")
    print("-" * 40)
    
    try:
        from proprietes.models import Locataire
        
        # Vérifier si le champ numero_locataire existe déjà
        if hasattr(Locataire, 'numero_locataire'):
            print("✅ Le champ numero_locataire existe déjà")
        else:
            print("❌ Le champ numero_locataire n'existe pas - ajout en cours...")
            
            # Ajouter le champ via une migration personnalisée
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("""
                    ALTER TABLE proprietes_locataire 
                    ADD COLUMN numero_locataire VARCHAR(50) UNIQUE
                """)
            print("✅ Champ numero_locataire ajouté à la base de données")
            
    except Exception as e:
        print(f"❌ Erreur lors de la mise à jour du modèle Locataire: {e}")
    
    # 3. Mettre à jour le modèle Propriete
    print("\n🏘️ MISE À JOUR DU MODÈLE PROPRIÉTÉ")
    print("-" * 40)
    
    try:
        from proprietes.models import Propriete
        
        # Vérifier si le champ numero_propriete existe déjà
        if hasattr(Propriete, 'numero_propriete'):
            print("✅ Le champ numero_propriete existe déjà")
        else:
            print("❌ Le champ numero_propriete n'existe pas - ajout en cours...")
            
            # Ajouter le champ via une migration personnalisée
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("""
                    ALTER TABLE proprietes_propriete 
                    ADD COLUMN numero_propriete VARCHAR(50) UNIQUE
                """)
            print("✅ Champ numero_propriete ajouté à la base de données")
            
    except Exception as e:
        print(f"❌ Erreur lors de la mise à jour du modèle Propriete: {e}")
    
    # 4. Mettre à jour le modèle Paiement
    print("\n💳 MISE À JOUR DU MODÈLE PAIEMENT")
    print("-" * 40)
    
    try:
        from paiements.models import Paiement
        
        # Vérifier si le champ numero_paiement existe déjà
        if hasattr(Paiement, 'numero_paiement'):
            print("✅ Le champ numero_paiement existe déjà")
        else:
            print("❌ Le champ numero_paiement n'existe pas - ajout en cours...")
            
            # Ajouter le champ via une migration personnalisée
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("""
                    ALTER TABLE paiements_paiement 
                    ADD COLUMN numero_paiement VARCHAR(50) UNIQUE
                """)
            print("✅ Champ numero_paiement ajouté à la base de données")
            
    except Exception as e:
        print(f"❌ Erreur lors de la mise à jour du modèle Paiement: {e}")
    
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
    print("✅ Mise à jour des modèles terminée!")

if __name__ == '__main__':
    mettre_a_jour_modeles()
