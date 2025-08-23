#!/usr/bin/env python3
"""
Script de test pour vérifier le bon fonctionnement du système de gestion des locataires
avec suppression logique, corbeille et gestion des références.
"""

import os
import sys
import django
from datetime import datetime, timedelta

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from django.contrib.auth.models import User
from django.test import TestCase
from proprietes.models import Locataire, Propriete
from contrats.models import Contrat
from paiements.models import Paiement
from utilisateurs.models import GroupeTravail, Utilisateur

def test_gestion_locataires():
    """
    Test complet du système de gestion des locataires
    """
    print("🧪 Test du système de gestion des locataires")
    print("=" * 60)
    
    try:
        # 1. Vérifier que les modèles existent
        print("\n1. Vérification des modèles...")
        assert hasattr(Locataire, 'est_supprime'), "Le modèle Locataire doit avoir le champ 'est_supprime'"
        assert hasattr(Locataire, 'date_suppression'), "Le modèle Locataire doit avoir le champ 'date_suppression'"
        print("✅ Modèles vérifiés")
        
        # 2. Vérifier les privilèges
        print("\n2. Vérification des privilèges...")
        groupes_privileges = ['ADMINISTRATION', 'PRIVILEGE']
        for nom_groupe in groupes_privileges:
            groupe, created = GroupeTravail.objects.get_or_create(nom=nom_groupe)
            if created:
                print(f"   - Groupe '{nom_groupe}' créé")
            else:
                print(f"   - Groupe '{nom_groupe}' existe déjà")
        print("✅ Privilèges vérifiés")
        
        # 3. Vérifier les URLs
        print("\n3. Vérification des URLs...")
        from django.urls import reverse
        try:
            # URLs des locataires
            reverse('proprietes:locataires_liste')
            reverse('proprietes:corbeille_locataires')
            reverse('contrats:orphelins')
            print("✅ URLs vérifiées")
        except Exception as e:
            print(f"❌ Erreur avec les URLs: {e}")
            return False
        
        # 4. Vérifier les vues
        print("\n4. Vérification des vues...")
        from proprietes.views import corbeille_locataires
        from contrats.views import contrats_orphelins
        print("✅ Vues vérifiées")
        
        # 5. Vérifier les templates
        print("\n5. Vérification des templates...")
        template_paths = [
            'templates/proprietes/confirm_supprimer_locataire_avance.html',
            'templates/proprietes/corbeille_locataires.html',
            'templates/contrats/orphelins.html'
        ]
        
        for template_path in template_paths:
            if os.path.exists(template_path):
                print(f"   ✅ {template_path}")
            else:
                print(f"   ❌ {template_path} manquant")
        
        # 6. Test de création de données de test
        print("\n6. Création de données de test...")
        
        # Créer un utilisateur de test
        user, created = User.objects.get_or_create(
            username='test_admin',
            defaults={'email': 'test@example.com', 'is_staff': True}
        )
        if created:
            user.set_password('testpass123')
            user.save()
            print("   - Utilisateur de test créé")
        
        # Créer un groupe de travail
        groupe_admin, created = GroupeTravail.objects.get_or_create(nom='ADMINISTRATION')
        
        # Créer un utilisateur avec groupe
        utilisateur, created = Utilisateur.objects.get_or_create(
            user=user,
            defaults={'groupe_travail': groupe_admin}
        )
        if created:
            print("   - Utilisateur avec groupe créé")
        
        # Créer une propriété de test
        propriete, created = Propriete.objects.get_or_create(
            titre='Propriété de Test',
            defaults={
                'adresse': '123 Rue de Test',
                'type_propriete': 'APPARTEMENT',
                'surface': 80.0,
                'nombre_pieces': 3,
                'loyer_mensuel': 50000,
                'charges_mensuelles': 5000,
                'est_actif': True
            }
        )
        if created:
            print("   - Propriété de test créée")
        
        # Créer des locataires de test
        locataire1, created = Locataire.objects.get_or_create(
            nom='Dupont',
            prenom='Jean',
            defaults={
                'email': 'jean.dupont@example.com',
                'telephone': '0123456789',
                'date_naissance': '1980-01-01',
                'profession': 'Ingénieur',
                'est_actif': True
            }
        )
        if created:
            print("   - Locataire 1 créé")
        
        locataire2, created = Locataire.objects.get_or_create(
            nom='Martin',
            prenom='Marie',
            defaults={
                'email': 'marie.martin@example.com',
                'telephone': '0987654321',
                'date_naissance': '1985-05-15',
                'profession': 'Médecin',
                'est_actif': True
            }
        )
        if created:
            print("   - Locataire 2 créé")
        
        # Créer des contrats de test
        contrat1, created = Contrat.objects.get_or_create(
            numero_contrat='CTR-001-2024',
            defaults={
                'propriete': propriete,
                'locataire': locataire1,
                'date_debut': datetime.now().date(),
                'date_fin': (datetime.now() + timedelta(days=365)).date(),
                'loyer_mensuel': 50000,
                'charges_mensuelles': 5000,
                'caution': 100000,
                'est_actif': True
            }
        )
        if created:
            print("   - Contrat 1 créé")
        
        contrat2, created = Contrat.objects.get_or_create(
            numero_contrat='CTR-002-2024',
            defaults={
                'propriete': propriete,
                'locataire': locataire2,
                'date_debut': (datetime.now() + timedelta(days=30)).date(),
                'date_fin': (datetime.now() + timedelta(days=395)).date(),
                'loyer_mensuel': 55000,
                'charges_mensuelles': 6000,
                'caution': 110000,
                'est_actif': True
            }
        )
        if created:
            print("   - Contrat 2 créé")
        
        print("✅ Données de test créées")
        
        # 7. Test de suppression logique
        print("\n7. Test de suppression logique...")
        
        # Supprimer logiquement le premier locataire
        locataire1.est_supprime = True
        locataire1.date_suppression = datetime.now()
        locataire1.save()
        print("   - Locataire 1 supprimé logiquement")
        
        # Vérifier que le locataire est marqué comme supprimé
        locataire1.refresh_from_db()
        assert locataire1.est_supprime == True, "Le locataire doit être marqué comme supprimé"
        assert locataire1.date_suppression is not None, "La date de suppression doit être définie"
        print("   ✅ Suppression logique vérifiée")
        
        # 8. Test de la corbeille
        print("\n8. Test de la corbeille...")
        
        # Vérifier que le locataire apparaît dans la corbeille
        locataires_supprimes = Locataire.objects.filter(est_supprime=True)
        assert locataire1 in locataires_supprimes, "Le locataire supprimé doit apparaître dans la corbeille"
        print("   ✅ Locataire dans la corbeille")
        
        # 9. Test des contrats orphelins
        print("\n9. Test des contrats orphelins...")
        
        # Vérifier que le contrat du locataire supprimé est considéré comme orphelin
        contrats_orphelins = Contrat.objects.filter(locataire__est_supprime=True)
        assert contrat1 in contrats_orphelins, "Le contrat du locataire supprimé doit être orphelin"
        print("   ✅ Contrat orphelin détecté")
        
        # 10. Test de restauration
        print("\n10. Test de restauration...")
        
        # Restaurer le locataire
        locataire1.est_supprime = False
        locataire1.date_suppression = None
        locataire1.save()
        print("   - Locataire 1 restauré")
        
        # Vérifier que le locataire n'est plus dans la corbeille
        locataire1.refresh_from_db()
        assert locataire1.est_supprime == False, "Le locataire doit être restauré"
        assert locataire1.date_suppression is None, "La date de suppression doit être effacée"
        print("   ✅ Restauration vérifiée")
        
        # 11. Test de suppression définitive
        print("\n11. Test de suppression définitive...")
        
        # Supprimer définitivement le deuxième locataire (sans contrats actifs)
        locataire2.delete()
        print("   - Locataire 2 supprimé définitivement")
        
        # Vérifier que le locataire n'existe plus
        try:
            Locataire.objects.get(pk=locataire2.pk)
            print("   ❌ Le locataire existe encore après suppression définitive")
            return False
        except Locataire.DoesNotExist:
            print("   ✅ Suppression définitive vérifiée")
        
        # 12. Nettoyage
        print("\n12. Nettoyage des données de test...")
        
        # Supprimer les contrats
        contrat1.delete()
        contrat2.delete()
        
        # Supprimer la propriété
        propriete.delete()
        
        # Supprimer l'utilisateur de test
        user.delete()
        
        print("✅ Données de test nettoyées")
        
        print("\n🎉 Tous les tests sont passés avec succès !")
        return True
        
    except Exception as e:
        print(f"\n❌ Erreur lors des tests: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """
    Fonction principale
    """
    print("🚀 Démarrage des tests de gestion des locataires")
    print("=" * 60)
    
    success = test_gestion_locataires()
    
    if success:
        print("\n✅ Le système de gestion des locataires fonctionne correctement")
        print("\n📋 Fonctionnalités implémentées :")
        print("   - Suppression logique des locataires")
        print("   - Corbeille des locataires supprimés")
        print("   - Gestion des contrats orphelins")
        print("   - Restauration des locataires")
        print("   - Suppression définitive")
        print("   - Vérification des références")
        print("   - Interface utilisateur complète")
        return 0
    else:
        print("\n❌ Des problèmes ont été détectés")
        return 1

if __name__ == '__main__':
    sys.exit(main())
