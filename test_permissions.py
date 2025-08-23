#!/usr/bin/env python
import os
import sys
import django
from datetime import datetime

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from utilisateurs.models import Utilisateur
from paiements.models import RecapMensuel

def test_permissions():
    """Test des permissions et groupes dans le système."""
    print("=== Test des permissions et groupes ===")
    
    try:
        # Test 1: Vérifier les groupes existants
        print("1. Groupes existants:")
        groupes = Group.objects.all()
        for groupe in groupes:
            print(f"   - {groupe.name}")
            permissions = groupe.permissions.all()
            if permissions:
                print(f"     Permissions: {', '.join([p.name for p in permissions])}")
            else:
                print("     Aucune permission")
        
        # Test 2: Vérifier l'utilisateur de test
        print("\n2. Utilisateur de test:")
        try:
            utilisateur = Utilisateur.objects.get(username='test_pdf_direct')
            print(f"   - Username: {utilisateur.username}")
            print(f"   - Email: {utilisateur.email}")
            print(f"   - Prénom: {utilisateur.first_name}")
            print(f"   - Nom: {utilisateur.last_name}")
            print(f"   - Actif: {utilisateur.is_active}")
            print(f"   - Staff: {utilisateur.is_staff}")
            print(f"   - Superuser: {utilisateur.is_superuser}")
            
            # Vérifier les groupes
            groupes_utilisateur = utilisateur.groups.all()
            print(f"   - Groupes: {', '.join([g.name for g in groupes_utilisateur])}")
            
            # Vérifier les permissions
            permissions_utilisateur = utilisateur.user_permissions.all()
            print(f"   - Permissions directes: {', '.join([p.name for p in permissions_utilisateur])}")
            
            # Vérifier les permissions via les groupes
            permissions_groupes = Permission.objects.filter(group__user=utilisateur)
            print(f"   - Permissions via groupes: {', '.join([p.name for p in permissions_groupes])}")
            
        except Utilisateur.DoesNotExist:
            print("   ✗ Utilisateur de test non trouvé")
        
        # Test 3: Vérifier les permissions sur RecapMensuel
        print("\n3. Permissions sur RecapMensuel:")
        content_type = ContentType.objects.get_for_model(RecapMensuel)
        permissions_recap = Permission.objects.filter(content_type=content_type)
        print(f"   - ContentType: {content_type}")
        for perm in permissions_recap:
            print(f"   - {perm.name} ({perm.codename})")
        
        # Test 4: Créer un superuser pour test
        print("\n4. Création d'un superuser pour test:")
        try:
            superuser = Utilisateur.objects.create_user(
                username='admin_pdf_test',
                email='admin@pdftest.com',
                password='admin123',
                first_name='Admin',
                last_name='PDFTest',
                is_staff=True,
                is_superuser=True
            )
            print("   ✓ Superuser créé avec succès")
            print(f"   - Username: {superuser.username}")
            print(f"   - Superuser: {superuser.is_superuser}")
            
        except Exception as e:
            print(f"   ⚠️  Erreur création superuser: {e}")
            try:
                superuser = Utilisateur.objects.get(username='admin_pdf_test')
                print("   ✓ Superuser existant")
            except Utilisateur.DoesNotExist:
                print("   ✗ Impossible de créer ou récupérer le superuser")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test des permissions: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("Démarrage des tests de permissions...")
    success = test_permissions()
    
    if success:
        print("\n✅ Tests de permissions terminés avec succès.")
    else:
        print("\n❌ Certains tests de permissions ont échoué.")
        print("Vérifiez les erreurs ci-dessus pour identifier le problème.")
