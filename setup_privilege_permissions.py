#!/usr/bin/env python
"""
Script pour configurer les permissions nécessaires pour les utilisateurs PRIVILEGE
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission, Group
from django.contrib.contenttypes.models import ContentType
from utilisateurs.models import GroupeTravail
from core.models import HardDeleteLog

User = get_user_model()

def setup_privilege_permissions():
    """Configure les permissions nécessaires pour les utilisateurs PRIVILEGE"""
    
    print("=== CONFIGURATION DES PERMISSIONS PRIVILEGE ===\n")
    
    # 1. Vérifier le groupe PRIVILEGE
    try:
        privilege_groupe = GroupeTravail.objects.get(nom='PRIVILEGE')
        print(f"✓ Groupe PRIVILEGE trouvé (ID: {privilege_groupe.id})")
    except GroupeTravail.DoesNotExist:
        print("✗ Groupe PRIVILEGE non trouvé")
        return
    
    # 2. Créer un groupe Django pour les permissions
    django_group, created = Group.objects.get_or_create(name='PRIVILEGE_USERS')
    if created:
        print(f"✓ Groupe Django PRIVILEGE_USERS créé")
    else:
        print(f"✓ Groupe Django PRIVILEGE_USERS existe déjà")
    
    # 3. Définir les modèles pour lesquels nous voulons des permissions
    models_to_configure = [
        (User, 'utilisateurs'),
        (HardDeleteLog, 'core'),
    ]
    
    # Essayer d'importer d'autres modèles si disponibles
    try:
        from contrats.models import Contrat
        models_to_configure.append((Contrat, 'contrats'))
        print("✓ Modèle Contrat disponible")
    except ImportError:
        print("⚠ Modèle Contrat non disponible")
    
    try:
        from paiements.models import Paiement
        models_to_configure.append((Paiement, 'paiements'))
        print("✓ Modèle Paiement disponible")
    except ImportError:
        print("⚠ Modèle Paiement non disponible")
    
    try:
        from proprietes.models import Propriete
        models_to_configure.append((Propriete, 'proprietes'))
        print("✓ Modèle Propriete disponible")
    except ImportError:
        print("⚠ Modèle Propriete non disponible")
    
    print(f"\nModèles à configurer: {len(models_to_configure)}")
    
    # 4. Créer et assigner les permissions
    permissions_created = []
    
    for model_class, app_label in models_to_configure:
        try:
            content_type = ContentType.objects.get_for_model(model_class)
            
            # Permissions de base
            permissions = [
                f'add_{model_class._meta.model_name}',
                f'change_{model_class._meta.model_name}',
                f'delete_{model_class._meta.model_name}',
                f'view_{model_class._meta.model_name}',
            ]
            
            # Permissions spéciales pour la suppression sécurisée
            if hasattr(model_class, '_meta') and model_class._meta.model_name != 'harddeletelog':
                permissions.append(f'secure_delete_{model_class._meta.model_name}')
            
            for perm_name in permissions:
                try:
                    permission, created = Permission.objects.get_or_create(
                        codename=perm_name,
                        content_type=content_type,
                        defaults={'name': f'Can {perm_name.replace("_", " ")}'}
                    )
                    
                    if created:
                        permissions_created.append(f"{app_label}.{perm_name}")
                        print(f"  ✓ Permission créée: {perm_name}")
                    
                    # Assigner au groupe Django
                    django_group.permissions.add(permission)
                    
                except Exception as e:
                    print(f"  ⚠ Erreur avec permission {perm_name}: {e}")
            
            print(f"✓ Modèle {model_class.__name__} configuré")
            
        except Exception as e:
            print(f"✗ Erreur avec modèle {model_class.__name__}: {e}")
    
    # 5. Assigner le groupe Django aux utilisateurs PRIVILEGE
    privilege_users = User.objects.filter(groupe_travail=privilege_groupe)
    users_updated = 0
    
    for user in privilege_users:
        try:
            user.groups.add(django_group)
            users_updated += 1
            print(f"✓ Utilisateur {user.username} ajouté au groupe Django")
        except Exception as e:
            print(f"✗ Erreur avec utilisateur {user.username}: {e}")
    
    # 6. Créer des permissions personnalisées si nécessaire
    print("\n6. Création de permissions personnalisées:")
    
    # Permission pour la suppression sécurisée
    try:
        secure_delete_permission, created = Permission.objects.get_or_create(
            codename='can_perform_secure_deletion',
            content_type=ContentType.objects.get_for_model(HardDeleteLog),
            defaults={'name': 'Can perform secure deletion'}
        )
        
        if created:
            print(f"✓ Permission personnalisée créée: can_perform_secure_deletion")
            django_group.permissions.add(secure_delete_permission)
        else:
            print(f"✓ Permission personnalisée existe déjà: can_perform_secure_deletion")
            
    except Exception as e:
        print(f"✗ Erreur création permission personnalisée: {e}")
    
    # 7. Résumé
    print(f"\n=== RÉSUMÉ ===")
    print(f"Permissions créées: {len(permissions_created)}")
    print(f"Utilisateurs mis à jour: {users_updated}")
    print(f"Groupe Django: {django_group.name}")
    
    print(f"\nPermissions disponibles dans le groupe:")
    for perm in django_group.permissions.all():
        print(f"  - {perm.codename} ({perm.content_type.app_label}.{perm.content_type.model})")
    
    print(f"\nUtilisateurs PRIVILEGE configurés:")
    for user in privilege_users:
        django_groups = [g.name for g in user.groups.all()]
        print(f"  - {user.username}: {', '.join(django_groups)}")
    
    print(f"\n✅ Configuration terminée!")
    print(f"Les utilisateurs PRIVILEGE peuvent maintenant accéder au système de suppressions sécurisées.")

if __name__ == '__main__':
    setup_privilege_permissions()






