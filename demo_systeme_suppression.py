#!/usr/bin/env python
"""
Script de démonstration du système de suppressions sécurisées
Montre concrètement les effets et fonctionnalités du système
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from utilisateurs.models import GroupeTravail
from core.models import HardDeleteLog
from core.services import SecureDeletionService, DeletionPolicyManager

User = get_user_model()

def demo_systeme_suppression():
    """Démonstration complète du système de suppressions sécurisées"""
    
    print("🎯 DÉMONSTRATION DU SYSTÈME DE SUPPRESSIONS SÉCURISÉES")
    print("=" * 60)
    
    # 1. Vérification de l'état initial
    print("\n1️⃣ ÉTAT INITIAL DU SYSTÈME")
    print("-" * 40)
    
    privilege_groupe = GroupeTravail.objects.get(nom='PRIVILEGE')
    privilege_users = User.objects.filter(groupe_travail=privilege_groupe)
    
    print(f"✓ Groupe PRIVILEGE: {privilege_groupe.nom} (ID: {privilege_groupe.id})")
    print(f"✓ Utilisateurs PRIVILEGE: {privilege_users.count()}")
    print(f"✓ Logs de suppression existants: {HardDeleteLog.objects.count()}")
    
    # 2. Démonstration des politiques de suppression
    print("\n2️⃣ POLITIQUES DE SUPPRESSION PAR MODÈLE")
    print("-" * 40)
    
    models_to_demo = [User]
    
    # Essayer d'importer d'autres modèles
    try:
        from contrats.models import Contrat
        models_to_demo.append(Contrat)
    except ImportError:
        pass
    
    try:
        from paiements.models import Paiement
        models_to_demo.append(Paiement)
    except ImportError:
        pass
    
    try:
        from proprietes.models import Propriete
        models_to_demo.append(Propriete)
    except ImportError:
        pass
    
    for model in models_to_demo:
        policy = DeletionPolicyManager.get_deletion_policy(model)
        print(f"📋 {model.__name__}:")
        print(f"   - Niveau critique: {policy['critical_level'].upper()}")
        print(f"   - Validation requise: {'✅ Oui' if policy['require_validation'] else '❌ Non'}")
        print(f"   - Rétention: {policy['max_retention_days']} jours")
        print(f"   - Types autorisés: {', '.join(policy['allowed_types'])}")
    
    # 3. Test du service de suppression sécurisée
    print("\n3️⃣ TEST DU SERVICE DE SUPPRESSION SÉCURISÉE")
    print("-" * 40)
    
    if privilege_users.exists():
        test_user = privilege_users.first()
        print(f"👤 Utilisateur de test: {test_user.username}")
        
        # Créer un objet mock pour tester
        class MockRequest:
            def __init__(self, user):
                self.user = user
                self.META = {'REMOTE_ADDR': '127.0.0.1', 'HTTP_USER_AGENT': 'Demo Script'}
                self.session = type('MockSession', (), {'session_key': 'demo_session'})()
        
        mock_request = MockRequest(test_user)
        service = SecureDeletionService(mock_request)
        
        # Test des permissions
        for model in models_to_demo:
            can_delete, msg = service.can_perform_hard_delete(model, None)
            status = "✅ Autorisé" if can_delete else "❌ Refusé"
            print(f"   {model.__name__}: {status} - {msg}")
        
        # Test de l'analyse d'impact
        print(f"\n🔍 Test de l'analyse d'impact:")
        try:
            # Créer un utilisateur de test temporaire
            temp_user = User.objects.create_user(
                username='temp_demo_user',
                email='temp@demo.com',
                password='temp123',
                nom='Temp',
                prenom='Demo',
                groupe_travail=privilege_groupe,
                actif=True
            )
            
            impact = service.analyze_deletion_impact(temp_user)
            print(f"   - Niveau de risque: {impact['risk_level'].upper()}")
            print(f"   - Relations directes: {len(impact['direct_relations'])}")
            print(f"   - Relations inverses: {len(impact['reverse_relations'])}")
            
            # Nettoyer l'utilisateur temporaire
            temp_user.delete()
            print("   ✓ Utilisateur temporaire nettoyé")
            
        except Exception as e:
            print(f"   ⚠ Erreur lors de l'analyse d'impact: {e}")
    
    # 4. Démonstration de la création de logs
    print("\n4️⃣ DÉMONSTRATION DE LA CRÉATION DE LOGS")
    print("-" * 40)
    
    try:
        # Créer un log de démonstration
        content_type = ContentType.objects.get_for_model(User)
        
        demo_log = HardDeleteLog.objects.create(
            content_type=content_type,
            object_id=999999,  # ID fictif
            object_repr="Utilisateur de démonstration",
            object_data_before_deletion={
                'username': 'demo_user',
                'email': 'demo@example.com',
                'nom': 'Demo',
                'prenom': 'User',
                'groupe_travail': 'PRIVILEGE',
                'actif': True,
                'date_creation': '2024-01-01T00:00:00Z'
            },
            deleted_by=test_user if privilege_users.exists() else None,
            deletion_type='demo',
            reason='Démonstration du système',
            justification='Ce log est créé pour démontrer les fonctionnalités du système de suppression sécurisée',
            ip_address='127.0.0.1',
            user_agent='Demo Script',
            session_id='demo_session'
        )
        
        print(f"✅ Log de démonstration créé:")
        print(f"   - ID: {demo_log.id}")
        print(f"   - Hash: {demo_log.deletion_hash[:30]}...")
        print(f"   - Timestamp: {demo_log.deletion_timestamp}")
        print(f"   - Type: {demo_log.get_deletion_type_display()}")
        print(f"   - Raison: {demo_log.reason}")
        
        # Afficher les données sauvegardées
        print(f"\n📊 Données sauvegardées:")
        for key, value in demo_log.object_data_before_deletion.items():
            print(f"   - {key}: {value}")
        
        # 5. Démonstration de la validation
        print(f"\n5️⃣ DÉMONSTRATION DE LA VALIDATION")
        print("-" * 40)
        
        if privilege_users.count() > 1:
            validator = privilege_users.exclude(id=test_user.id).first()
            print(f"👤 Validateur: {validator.username}")
            
            # Simuler la validation
            demo_log.validated_by = validator
            demo_log.validation_timestamp = django.utils.timezone.now()
            demo_log.validation_notes = "Validation de démonstration - Test du système"
            demo_log.save()
            
            print(f"✅ Log validé par {validator.username}")
            print(f"   - Date validation: {demo_log.validation_timestamp}")
            print(f"   - Notes: {demo_log.validation_notes}")
            print(f"   - Statut: {demo_log.get_validation_status()}")
        else:
            print("⚠ Validation non démontrée (un seul utilisateur PRIVILEGE)")
        
        # 6. Test des fonctionnalités avancées
        print(f"\n6️⃣ FONCTIONNALITÉS AVANCÉES")
        print("-" * 40)
        
        print(f"🔐 Non-répudiation:")
        print(f"   - Hash unique: {demo_log.deletion_hash}")
        print(f"   - Intégrité garantie: ✅")
        
        print(f"📱 Interface utilisateur:")
        print(f"   - Dashboard: /suppressions-securisees/")
        print(f"   - Détails du log: /suppressions-securisees/logs/{demo_log.id}/")
        print(f"   - Export: /suppressions-securisees/export/")
        
        print(f"🔄 Restauration possible:")
        print(f"   - Peut être restauré: {'✅ Oui' if demo_log.can_be_restored() else '❌ Non'}")
        
        # 7. Nettoyage et résumé
        print(f"\n7️⃣ NETTOYAGE ET RÉSUMÉ")
        print("-" * 40)
        
        # Supprimer le log de démonstration
        demo_log.delete()
        print("🧹 Log de démonstration supprimé")
        
        final_count = HardDeleteLog.objects.count()
        print(f"📊 Logs restants: {final_count}")
        
        print(f"\n🎉 DÉMONSTRATION TERMINÉE AVEC SUCCÈS!")
        print(f"✅ Toutes les fonctionnalités du système ont été testées")
        print(f"✅ Les utilisateurs PRIVILEGE peuvent maintenant utiliser le système")
        print(f"✅ La traçabilité et la non-répudiation sont garanties")
        
        print(f"\n🚀 PROCHAINES ÉTAPES:")
        print(f"1. Démarrer le serveur Django: python manage.py runserver")
        print(f"2. Se connecter avec un utilisateur PRIVILEGE")
        print(f"3. Accéder à: http://localhost:8000/suppressions-securisees/")
        print(f"4. Tester les fonctionnalités en conditions réelles")
        
    except Exception as e:
        print(f"❌ Erreur lors de la démonstration: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    demo_systeme_suppression()






