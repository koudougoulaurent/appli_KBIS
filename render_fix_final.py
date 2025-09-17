#!/usr/bin/env python
"""
Script de correction finale pour Render - Solution définitive
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')

try:
    django.setup()
    print("✅ Django configuré")
    
    from django.contrib.auth import get_user_model
    from django.contrib.auth.models import Group
    from utilisateurs.models import GroupeTravail
    from proprietes.models import TypeBien
    from core.models import ConfigurationEntreprise
    
    User = get_user_model()
    
    def fix_everything():
        """Corriger tout définitivement"""
        print("🔧 CORRECTION FINALE - SOLUTION DÉFINITIVE")
        
        # 1. Créer les GroupeTravail
        print("📋 Création des GroupeTravail...")
        groupes_data = [
            ('PRIVILEGE', 'Groupe avec tous les privilèges', {'modules': ['all'], 'actions': ['create', 'read', 'update', 'delete']}),
            ('ADMINISTRATION', 'Groupe d\'administration', {'modules': ['utilisateurs', 'proprietes', 'contrats', 'paiements'], 'actions': ['create', 'read', 'update']}),
            ('CAISSE', 'Groupe de gestion de la caisse', {'modules': ['paiements', 'contrats'], 'actions': ['create', 'read', 'update']}),
            ('CONTROLES', 'Groupe de contrôles', {'modules': ['proprietes', 'contrats'], 'actions': ['read', 'update']})
        ]
        
        groupes = {}
        for nom, desc, perms in groupes_data:
            groupe, created = GroupeTravail.objects.get_or_create(
                nom=nom,
                defaults={
                    'description': desc,
                    'permissions': perms,
                    'actif': True
                }
            )
            groupes[nom] = groupe
            print(f"  ✅ {nom}")
        
        # 2. Supprimer tous les utilisateurs existants
        print("🗑️ Suppression des anciens utilisateurs...")
        User.objects.all().delete()
        print("  ✅ Tous les utilisateurs supprimés")
        
        # 3. Créer les utilisateurs de test
        print("👥 Création des utilisateurs de test...")
        users_data = [
            ('admin', 'admin@example.com', 'admin123', 'ADMINISTRATION', True, True),
            ('caisse1', 'caisse1@example.com', 'caisse123', 'CAISSE', True, False),
            ('controle1', 'controle1@example.com', 'controle123', 'CONTROLES', True, False),
            ('admin1', 'admin1@example.com', 'admin123', 'ADMINISTRATION', True, False),
            ('privilege1', 'privilege1@example.com', 'privilege123', 'PRIVILEGE', True, False),
        ]
        
        for username, email, password, groupe_nom, is_staff, is_superuser in users_data:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password
            )
            user.is_staff = is_staff
            user.is_superuser = is_superuser
            user.groupe_travail = groupes[groupe_nom]
            user.save()
            print(f"  ✅ {username} ({groupe_nom})")
        
        # 4. Créer les types de biens
        print("🏠 Création des types de biens...")
        types_bien = [
            'Appartement', 'Maison', 'Studio', 'Loft', 'Villa', 'Duplex',
            'Penthouse', 'Château', 'Ferme', 'Bureau', 'Commerce',
            'Entrepôt', 'Garage', 'Terrain', 'Autre'
        ]
        
        for type_name in types_bien:
            TypeBien.objects.get_or_create(nom=type_name)
            print(f"  ✅ {type_name}")
        
        # 5. Configuration entreprise
        print("🏢 Configuration entreprise...")
        ConfigurationEntreprise.objects.get_or_create(
            nom_entreprise="Gestion Immobilière KBIS",
            defaults={
                'adresse': "123 Rue de l'Immobilier",
                'ville': "Ouagadougou",
                'code_postal': "01 BP 1234",
                'telephone': "+226 25 12 34 56",
                'email': "contact@kbis.bf"
            }
        )
        print("  ✅ Configuration créée")
        
        # 6. Test des connexions
        print("🔍 Test des connexions...")
        from django.contrib.auth import authenticate
        
        for username, _, password, groupe_nom, _, _ in users_data:
            user = authenticate(username=username, password=password)
            if user and user.groupe_travail and user.groupe_travail.nom == groupe_nom:
                print(f"  ✅ {username}: Connexion OK - Groupe: {groupe_nom}")
            else:
                print(f"  ❌ {username}: Échec de connexion")
        
        print("\n🎉 CORRECTION FINALE TERMINÉE !")
        print("=" * 50)
        print("🔐 UTILISATEURS DE TEST:")
        print("=" * 50)
        for username, _, password, groupe_nom, _, _ in users_data:
            print(f"👤 {username} / {password} (Groupe: {groupe_nom})")
        print("=" * 50)
        print("🌐 URL: https://appli-kbis.onrender.com")
        print("🎯 Sélectionnez un groupe et connectez-vous !")
        
    if __name__ == "__main__":
        fix_everything()
        
except Exception as e:
    print(f"❌ ERREUR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
