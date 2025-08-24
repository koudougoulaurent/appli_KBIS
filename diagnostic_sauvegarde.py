#!/usr/bin/env python
"""
Diagnostic complet du problème de sauvegarde
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from django.test import Client
from django.contrib.auth import authenticate
from utilisateurs.models import Utilisateur, GroupeTravail
from core.models import ConfigurationTableauBord
from core.utils import check_group_permissions

def diagnostic_complet():
    """Diagnostic complet du problème de sauvegarde"""
    print("🔍 Diagnostic complet du problème de sauvegarde")
    print("=" * 60)
    
    try:
        # 1. Vérifier la base de données
        print("\n📊 1. Vérification de la base de données:")
        print("-" * 40)
        
        # Vérifier les modèles
        try:
            config_count = ConfigurationTableauBord.objects.count()
            print(f"✅ ConfigurationTableauBord: {config_count} enregistrements")
        except Exception as e:
            print(f"❌ Erreur ConfigurationTableauBord: {str(e)}")
            return False
        
        try:
            user_count = Utilisateur.objects.count()
            print(f"✅ Utilisateur: {user_count} enregistrements")
        except Exception as e:
            print(f"❌ Erreur Utilisateur: {str(e)}")
            return False
        
        try:
            groupe_count = GroupeTravail.objects.count()
            print(f"✅ GroupeTravail: {groupe_count} enregistrements")
        except Exception as e:
            print(f"❌ Erreur GroupeTravail: {str(e)}")
            return False
        
        # 2. Vérifier le groupe PRIVILEGE
        print("\n👥 2. Vérification du groupe PRIVILEGE:")
        print("-" * 40)
        
        try:
            groupe_privilege = GroupeTravail.objects.get(nom='PRIVILEGE')
            print(f"✅ Groupe PRIVILEGE trouvé: {groupe_privilege.nom}")
            print(f"   - Description: {groupe_privilege.description}")
            print(f"   - Actif: {groupe_privilege.actif}")
            print(f"   - Permissions: {groupe_privilege.permissions}")
        except GroupeTravail.DoesNotExist:
            print("❌ Groupe PRIVILEGE non trouvé - Création...")
            groupe_privilege = GroupeTravail.objects.create(
                nom='PRIVILEGE',
                description='Groupe avec privilèges spéciaux',
                permissions={'modules': ['all']},
                actif=True
            )
            print(f"✅ Groupe PRIVILEGE créé: {groupe_privilege.nom}")
        except Exception as e:
            print(f"❌ Erreur avec le groupe PRIVILEGE: {str(e)}")
            return False
        
        # 3. Créer un utilisateur de test
        print("\n👤 3. Création d'un utilisateur de test:")
        print("-" * 40)
        
        try:
            # Supprimer l'utilisateur de test s'il existe
            Utilisateur.objects.filter(username='test_privilege').delete()
            
            utilisateur_test = Utilisateur.objects.create(
                username='test_privilege',
                email='test@example.com',
                first_name='Test',
                last_name='Privilege',
                is_active=True
            )
            
            # Définir un mot de passe
            utilisateur_test.set_password('test123')
            utilisateur_test.save()
            
            print(f"✅ Utilisateur de test créé: {utilisateur_test.username}")
            print(f"   - ID: {utilisateur_test.id}")
            print(f"   - Email: {utilisateur_test.email}")
            print(f"   - Actif: {utilisateur_test.is_active}")
            
        except Exception as e:
            print(f"❌ Erreur création utilisateur: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
        
        # 4. Assigner l'utilisateur au groupe PRIVILEGE
        print("\n🔗 4. Assignment au groupe PRIVILEGE:")
        print("-" * 40)
        
        try:
            utilisateur_test.groupe_travail = groupe_privilege
            utilisateur_test.save()
            print(f"✅ Utilisateur assigné au groupe: {utilisateur_test.groupe_travail.nom}")
            
            # Vérifier la relation
            utilisateur_refresh = Utilisateur.objects.get(id=utilisateur_test.id)
            print(f"✅ Vérification relation: {utilisateur_refresh.groupe_travail.nom}")
            
        except Exception as e:
            print(f"❌ Erreur assignment groupe: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
        
        # 5. Tester les permissions
        print("\n🔐 5. Test des permissions:")
        print("-" * 40)
        
        try:
            permissions = check_group_permissions(utilisateur_test, ['PRIVILEGE'], 'modify')
            print(f"✅ Test permissions: {permissions}")
            
            if permissions['allowed']:
                print("✅ Permissions OK - L'utilisateur peut modifier")
            else:
                print(f"❌ Permissions KO: {permissions['message']}")
                return False
                
        except Exception as e:
            print(f"❌ Erreur test permissions: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
        
        # 6. Test de création de configuration
        print("\n📝 6. Test de création de configuration:")
        print("-" * 40)
        
        try:
            # Supprimer l'ancienne configuration si elle existe
            ConfigurationTableauBord.objects.filter(
                utilisateur=utilisateur_test,
                par_defaut=True
            ).delete()
            
            config = ConfigurationTableauBord.objects.create(
                utilisateur=utilisateur_test,
                nom_tableau="Tableau Test",
                par_defaut=True,
                widgets_actifs=['statistiques_generales'],
                masquer_montants_sensibles=True,
                affichage_anonymise=False,
                limite_donnees_recentes=30
            )
            
            print(f"✅ Configuration créée: {config.id}")
            print(f"   - Nom: {config.nom_tableau}")
            print(f"   - Utilisateur: {config.utilisateur.username}")
            print(f"   - Widgets: {config.widgets_actifs}")
            
        except Exception as e:
            print(f"❌ Erreur création configuration: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
        
        # 7. Test de modification de configuration
        print("\n✏️ 7. Test de modification de configuration:")
        print("-" * 40)
        
        try:
            ancien_nom = config.nom_tableau
            config.nom_tableau = 'Tableau Modifié'
            config.save()
            
            print(f"✅ Configuration modifiée: {ancien_nom} -> {config.nom_tableau}")
            
            # Vérifier en base
            config_refresh = ConfigurationTableauBord.objects.get(id=config.id)
            print(f"✅ Vérification en base: {config_refresh.nom_tableau}")
            
        except Exception as e:
            print(f"❌ Erreur modification configuration: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
        
        # 8. Test via l'interface web
        print("\n🌐 8. Test via l'interface web:")
        print("-" * 40)
        
        try:
            client = Client()
            
            # Test de connexion
            login_success = client.login(username='test_privilege', password='test123')
            if login_success:
                print("✅ Connexion réussie")
            else:
                print("❌ Échec de la connexion")
                return False
            
            # Test GET de la page de configuration
            response_get = client.get('/configuration-tableau/')
            print(f"✅ GET /configuration-tableau/: {response_get.status_code}")
            
            if response_get.status_code != 200:
                print(f"❌ Erreur GET: {response_get.status_code}")
                print(f"   Contenu: {response_get.content[:500]}...")
                return False
            
            # Test POST de sauvegarde
            data_post = {
                'nom_tableau': 'Test Web POST',
                'widgets_actifs': ['statistiques_generales', 'activite_recente'],
                'masquer_montants': 'on',
                'affichage_anonymise': 'off',
                'limite_jours': '45'
            }
            
            response_post = client.post('/configuration-tableau/', data_post)
            print(f"✅ POST /configuration-tableau/: {response_post.status_code}")
            
            if response_post.status_code == 302:  # Redirection après sauvegarde
                print("✅ Sauvegarde réussie (redirection)")
                
                # Vérifier que la configuration a été sauvegardée
                config_sauvegardee = ConfigurationTableauBord.objects.filter(
                    utilisateur=utilisateur_test,
                    nom_tableau='Test Web POST'
                ).first()
                
                if config_sauvegardee:
                    print("✅ Configuration trouvée en base après sauvegarde")
                    print(f"   - Nom: {config_sauvegardee.nom_tableau}")
                    print(f"   - Widgets: {config_sauvegardee.widgets_actifs}")
                    print(f"   - Limite jours: {config_sauvegardee.limite_donnees_recentes}")
                else:
                    print("❌ Configuration non trouvée après sauvegarde")
                    return False
                    
            else:
                print(f"❌ Erreur lors de la sauvegarde: {response_post.status_code}")
                if hasattr(response_post, 'content'):
                    print(f"   Contenu: {response_post.content[:500]}...")
                return False
                
        except Exception as e:
            print(f"❌ Erreur test web: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
        
        # 9. Nettoyage
        print("\n🧹 9. Nettoyage:")
        print("-" * 40)
        
        try:
            # Supprimer les configurations de test
            ConfigurationTableauBord.objects.filter(
                utilisateur=utilisateur_test
            ).delete()
            print("✅ Configurations de test supprimées")
            
            # Supprimer l'utilisateur de test
            utilisateur_test.delete()
            print("✅ Utilisateur de test supprimé")
            
        except Exception as e:
            print(f"⚠️ Erreur lors du nettoyage: {str(e)}")
        
        print("\n🎉 Diagnostic terminé avec succès !")
        return True
        
    except Exception as e:
        print(f"❌ Erreur générale lors du diagnostic: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = diagnostic_complet()
    if success:
        print("\n✅ Tous les tests ont réussi !")
    else:
        print("\n❌ Certains tests ont échoué")
