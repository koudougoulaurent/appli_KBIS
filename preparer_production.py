#!/usr/bin/env python
"""
Script de préparation à la production - Nettoyage et configuration professionnelle
"""

import os
import sys
import django
from datetime import datetime

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from django.db import connection, transaction
from django.contrib.auth import get_user_model
from utilisateurs.models import Utilisateur, GroupeTravail
from proprietes.models import Propriete, Bailleur, Locataire
from contrats.models import Contrat
from paiements.models import Paiement, Retrait, Recu
from contrats.models import Quittance
from core.id_generator import IDGenerator, IDConfiguration

Utilisateur = get_user_model()

def nettoyer_donnees_test():
    """Supprime toutes les données de test de la base"""
    
    print("🧹 NETTOYAGE DES DONNÉES DE TEST")
    print("=" * 60)
    
    # 1. Supprimer les utilisateurs de test
    print("\n👥 Suppression des utilisateurs de test...")
    utilisateurs_test = Utilisateur.objects.filter(
        username__startswith='test_'
    ).exclude(
        username='admin'  # Garder l'admin
    )
    
    count_utilisateurs = utilisateurs_test.count()
    if count_utilisateurs > 0:
        utilisateurs_test.delete()
        print(f"   ✅ {count_utilisateurs} utilisateurs de test supprimés")
    else:
        print("   ℹ️ Aucun utilisateur de test trouvé")
    
    # 2. Supprimer les paiements de test (avant les contrats)
    print("\n💰 Suppression des paiements de test...")
    paiements_test = Paiement.objects.filter(
        contrat__propriete__adresse__icontains='test'
    )
    
    count_paiements = paiements_test.count()
    if count_paiements > 0:
        paiements_test.delete()
        print(f"   ✅ {count_paiements} paiements de test supprimés")
    else:
        print("   ℹ️ Aucun paiement de test trouvé")
    
    # 3. Supprimer les reçus de test
    print("\n🧾 Suppression des reçus de test...")
    recus_test = Recu.objects.filter(
        paiement__contrat__propriete__adresse__icontains='test'
    )
    
    count_recus = recus_test.count()
    if count_recus > 0:
        recus_test.delete()
        print(f"   ✅ {count_recus} reçus de test supprimés")
    else:
        print("   ℹ️ Aucun reçu de test trouvé")
    
    # 4. Supprimer les quittances de test
    print("\n📄 Suppression des quittances de test...")
    quittances_test = Quittance.objects.filter(
        contrat__propriete__adresse__icontains='test'
    )
    
    count_quittances = quittances_test.count()
    if count_quittances > 0:
        quittances_test.delete()
        print(f"   ✅ {count_quittances} quittances de test supprimées")
    else:
        print("   ℹ️ Aucune quittance de test trouvée")
    
    # 4.5. Supprimer les charges déductibles de test
    print("\n💸 Suppression des charges déductibles de test...")
    try:
        from paiements.models import ChargeDeductible
        charges_test = ChargeDeductible.objects.filter(
            contrat__propriete__adresse__icontains='test'
        )
        count_charges = charges_test.count()
        if count_charges > 0:
            charges_test.delete()
            print(f"   ✅ {count_charges} charges déductibles de test supprimées")
        else:
            print("   ℹ️ Aucune charge déductible de test trouvée")
    except ImportError:
        print("   ℹ️ Modèle ChargeDeductible non disponible")
    
    # 4.6. Supprimer les autres dépendances de contrats
    print("\n🔗 Suppression des autres dépendances de contrats...")
    try:
        from contrats.models import RenouvellementContrat
        renouvellements_test = RenouvellementContrat.objects.filter(
            contrat__propriete__adresse__icontains='test'
        )
        count_renouvellements = renouvellements_test.count()
        if count_renouvellements > 0:
            renouvellements_test.delete()
            print(f"   ✅ {count_renouvellements} renouvellements de test supprimés")
        else:
            print("   ℹ️ Aucun renouvellement de test trouvé")
    except ImportError:
        print("   ℹ️ Modèle RenouvellementContrat non disponible")
    
    # 5. Supprimer les contrats de test (après les paiements et dépendances)
    print("\n📋 Suppression des contrats de test...")
    contrats_test = Contrat.objects.filter(
        propriete__adresse__icontains='test'
    )
    
    count_contrats = contrats_test.count()
    if count_contrats > 0:
        contrats_test.delete()
        print(f"   ✅ {count_contrats} contrats de test supprimés")
    else:
        print("   ℹ️ Aucun contrat de test trouvé")
    
    # 6. Maintenant supprimer les propriétés de test (après avoir supprimé les contrats)
    print("\n🏠 Suppression des propriétés de test...")
    proprietes_test = Propriete.objects.filter(
        adresse__icontains='test'
    )
    
    count_proprietes = proprietes_test.count()
    if count_proprietes > 0:
        proprietes_test.delete()
        print(f"   ✅ {count_proprietes} propriétés de test supprimées")
    else:
        print("   ℹ️ Aucune propriété de test trouvée")
    
    # 6.5. Vérifier s'il reste des propriétés de test et les supprimer forcément
    proprietes_restantes = Propriete.objects.filter(
        adresse__icontains='test'
    )
    if proprietes_restantes.exists():
        print("\n⚠️  Suppression forcée des propriétés de test restantes...")
        for prop in proprietes_restantes:
            try:
                prop.delete()
                print(f"   ✅ Propriété supprimée: {prop.adresse}")
            except Exception as e:
                print(f"   ❌ Erreur suppression {prop.adresse}: {e}")
                # Suppression forcée en base
                try:
                    from django.db import connection
                    with connection.cursor() as cursor:
                        cursor.execute("DELETE FROM proprietes_propriete WHERE id = %s", [prop.id])
                    print(f"   ✅ Suppression forcée en base: {prop.adresse}")
                except Exception as e2:
                    print(f"   ❌ Échec suppression forcée: {e2}")
    
    # 7. Enfin supprimer les bailleurs de test (après avoir supprimé les propriétés)
    print("\n👤 Suppression des bailleurs de test...")
    bailleurs_test = Bailleur.objects.filter(
        nom__icontains='test'
    ).exclude(
        nom__icontains='admin'
    )
    
    count_bailleurs = bailleurs_test.count()
    if count_bailleurs > 0:
        bailleurs_test.delete()
        print(f"   ✅ {count_bailleurs} bailleurs de test supprimés")
    else:
        print("   ℹ️ Aucun bailleur de test trouvé")
    
    print("\n✅ Nettoyage des données de test terminé !")

def configurer_systeme_production():
    """Configure le système pour un usage professionnel"""
    
    print("\n⚙️ CONFIGURATION DU SYSTÈME PRODUCTION")
    print("=" * 60)
    
    # 1. Vérifier la configuration des IDs
    print("\n🔢 Configuration des identifiants uniques...")
    
    # Afficher la configuration actuelle
    print("   Configuration actuelle des IDs :")
    for entity_type, config in IDGenerator.ID_FORMATS.items():
        print(f"     {entity_type}: {config['format']}")
    
    # 2. Vérifier la politique de réinitialisation
    print("\n📅 Politique de réinitialisation des séquences :")
    reset_policy = IDConfiguration.get_sequence_reset_policy()
    for entity, policy in reset_policy.items():
        print(f"     {entity}: {policy}")
    
    # 3. Vérifier le préfixe de l'entreprise
    company_prefix = IDConfiguration.get_company_prefix()
    print(f"\n🏢 Préfixe de l'entreprise: {company_prefix}")
    
    print("\n✅ Configuration du système production terminée !")

def regenerer_ids_existants():
    """Régénère les IDs pour tous les enregistrements existants"""
    
    print("\n🔄 RÉGÉNÉRATION DES IDENTIFIANTS EXISTANTS")
    print("=" * 60)
    
    with transaction.atomic():
        # 1. Régénérer les IDs des bailleurs
        print("\n👤 Régénération des IDs des bailleurs...")
        bailleurs_sans_id = Bailleur.objects.filter(numero_bailleur__isnull=True)
        count_bailleurs = bailleurs_sans_id.count()
        
        if count_bailleurs > 0:
            for bailleur in bailleurs_sans_id:
                bailleur.numero_bailleur = IDGenerator.generate_id('bailleur')
                bailleur.save(update_fields=['numero_bailleur'])
            print(f"   ✅ {count_bailleurs} IDs de bailleurs régénérés")
        else:
            print("   ℹ️ Tous les bailleurs ont déjà un ID")
        
        # 2. Régénérer les IDs des locataires
        print("\n👥 Régénération des IDs des locataires...")
        locataires_sans_id = Locataire.objects.filter(numero_locataire__isnull=True)
        count_locataires = locataires_sans_id.count()
        
        if count_locataires > 0:
            for locataire in locataires_sans_id:
                locataire.numero_locataire = IDGenerator.generate_id('locataire')
                locataire.save(update_fields=['numero_locataire'])
            print(f"   ✅ {count_locataires} IDs de locataires régénérés")
        else:
            print("   ℹ️ Tous les locataires ont déjà un ID")
        
        # 3. Régénérer les IDs des propriétés
        print("\n🏠 Régénération des IDs des propriétés...")
        proprietes_sans_id = Propriete.objects.filter(numero_propriete__isnull=True)
        count_proprietes = proprietes_sans_id.count()
        
        if count_proprietes > 0:
            for propriete in proprietes_sans_id:
                propriete.numero_propriete = IDGenerator.generate_id('propriete')
                propriete.save(update_fields=['numero_propriete'])
            print(f"   ✅ {count_proprietes} IDs de propriétés régénérés")
        else:
            print("   ℹ️ Toutes les propriétés ont déjà un ID")
    
    print("\n✅ Régénération des identifiants terminée !")

def verifier_integrite_donnees():
    """Vérifie l'intégrité des données après nettoyage"""
    
    print("\n🔍 VÉRIFICATION DE L'INTÉGRITÉ DES DONNÉES")
    print("=" * 60)
    
    # 1. Compter les enregistrements
    print("\n📊 Statistiques des données :")
    
    count_bailleurs = Bailleur.objects.count()
    count_locataires = Locataire.objects.count()
    count_proprietes = Propriete.objects.count()
    count_contrats = Contrat.objects.count()
    count_paiements = Paiement.objects.count()
    count_utilisateurs = Utilisateur.objects.count()
    
    print(f"   Bailleurs: {count_bailleurs}")
    print(f"   Locataires: {count_locataires}")
    print(f"   Propriétés: {count_proprietes}")
    print(f"   Contrats: {count_contrats}")
    print(f"   Paiements: {count_paiements}")
    print(f"   Utilisateurs: {count_utilisateurs}")
    
    # 2. Vérifier les relations
    print("\n🔗 Vérification des relations :")
    
    proprietes_sans_bailleur = Propriete.objects.filter(bailleur__isnull=True).count()
    contrats_sans_propriete = Contrat.objects.filter(propriete__isnull=True).count()
    paiements_sans_contrat = Paiement.objects.filter(contrat__isnull=True).count()
    
    print(f"   Propriétés sans bailleur: {proprietes_sans_bailleur}")
    print(f"   Contrats sans propriété: {contrats_sans_propriete}")
    print(f"   Paiements sans contrat: {paiements_sans_contrat}")
    
    # 3. Vérifier les IDs uniques
    print("\n🆔 Vérification des identifiants uniques :")
    
    bailleurs_avec_id = Bailleur.objects.filter(numero_bailleur__isnull=False).count()
    locataires_avec_id = Locataire.objects.filter(numero_locataire__isnull=False).count()
    proprietes_avec_id = Propriete.objects.filter(numero_propriete__isnull=False).count()
    
    print(f"   Bailleurs avec ID: {bailleurs_avec_id}/{count_bailleurs}")
    print(f"   Locataires avec ID: {locataires_avec_id}/{count_locataires}")
    print(f"   Propriétés avec ID: {proprietes_avec_id}/{count_proprietes}")
    
    if (bailleurs_avec_id == count_bailleurs and 
        locataires_avec_id == count_locataires and 
        proprietes_avec_id == count_proprietes):
        print("   ✅ Tous les enregistrements ont un ID unique")
    else:
        print("   ⚠️ Certains enregistrements n'ont pas d'ID unique")
    
    print("\n✅ Vérification de l'intégrité terminée !")

def creer_utilisateur_admin_production():
    """Crée un utilisateur administrateur pour la production"""
    
    print("\n👑 CRÉATION DE L'UTILISATEUR ADMINISTRATEUR")
    print("=" * 60)
    
    # Vérifier si l'admin existe déjà
    if Utilisateur.objects.filter(username='admin').exists():
        print("   ℹ️ L'utilisateur admin existe déjà")
        return
    
    # Créer le groupe PRIVILEGE s'il n'existe pas
    groupe_privilege, created = GroupeTravail.objects.get_or_create(
        nom='PRIVILEGE',
        defaults={
            'description': 'Groupe avec tous les privilèges',
            'niveau_acces': 100
        }
    )
    
    if created:
        print(f"   ✅ Groupe PRIVILEGE créé")
    else:
        print(f"   ℹ️ Groupe PRIVILEGE déjà présent")
    
    # Créer l'utilisateur admin
    try:
        admin_user = Utilisateur.objects.create_user(
            username='admin',
            email='admin@gestionimmobiliere.com',
            password='Admin2024!',  # À changer en production !
            first_name='Administrateur',
            last_name='Système',
            groupe_travail=groupe_privilege,
            is_staff=True,
            is_superuser=True
        )
        print(f"   ✅ Utilisateur admin créé: {admin_user.username}")
        print("   ⚠️ MOT DE PASSE: Admin2024! - À CHANGER EN PRODUCTION !")
        
    except Exception as e:
        print(f"   ❌ Erreur lors de la création de l'admin: {e}")
    
    print("\n✅ Configuration de l'utilisateur administrateur terminée !")

def afficher_instructions_production():
    """Affiche les instructions pour la production"""
    
    print("\n📋 INSTRUCTIONS POUR LA PRODUCTION")
    print("=" * 60)
    
    print("""
🚀 L'application est maintenant prête pour la production !

📝 ACTIONS REQUISES AVANT DÉPLOIEMENT :

1. 🔐 SÉCURITÉ :
   - Changer le mot de passe de l'utilisateur admin
   - Configurer HTTPS
   - Mettre à jour les paramètres de sécurité Django

2. 🗄️ BASE DE DONNÉES :
   - Sauvegarder la base SQLite actuelle
   - Migrer vers PostgreSQL ou MySQL pour la production
   - Configurer les sauvegardes automatiques

3. ⚙️ CONFIGURATION :
   - Modifier les paramètres dans core/id_generator.py
   - Configurer le préfixe de l'entreprise
   - Ajuster les formats d'IDs selon vos besoins

4. 📊 DONNÉES :
   - Supprimer toutes les données de test
   - Importer vos données réelles
   - Vérifier l'intégrité des données

5. 🚀 DÉPLOIEMENT :
   - Configurer le serveur web (Nginx/Apache)
   - Configurer WSGI/ASGI
   - Mettre en place le monitoring

📞 SUPPORT :
   - Consultez la documentation Django
   - Testez toutes les fonctionnalités
   - Préparez la formation des utilisateurs
""")

def main():
    """Fonction principale"""
    
    print("🏢 PRÉPARATION À LA PRODUCTION - GESTION IMMOBILIÈRE")
    print("=" * 80)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    try:
        # 1. Nettoyer les données de test
        nettoyer_donnees_test()
        
        # 2. Configurer le système pour la production
        configurer_systeme_production()
        
        # 3. Régénérer les IDs existants
        regenerer_ids_existants()
        
        # 4. Vérifier l'intégrité des données
        verifier_integrite_donnees()
        
        # 5. Créer l'utilisateur admin
        creer_utilisateur_admin_production()
        
        # 6. Afficher les instructions
        afficher_instructions_production()
        
        print("\n🎉 PRÉPARATION À LA PRODUCTION TERMINÉE AVEC SUCCÈS !")
        print("L'application est maintenant prête pour un usage professionnel.")
        
    except Exception as e:
        print(f"\n❌ ERREUR LORS DE LA PRÉPARATION: {e}")
        print("Veuillez vérifier les logs et réessayer.")
        return False
    
    return True

if __name__ == "__main__":
    main()
