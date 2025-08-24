#!/usr/bin/env python
"""
Test réel de la sauvegarde de configuration
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

def test_sauvegarde_reel():
    """Test réel de la sauvegarde"""
    print("🔧 Test réel de la sauvegarde")
    print("=" * 40)
    
    # 1. Créer le groupe PRIVILEGE s'il n'existe pas
    groupe_privilege, created = GroupeTravail.objects.get_or_create(
        nom='PRIVILEGE',
        defaults={
            'description': 'Groupe avec privilèges spéciaux',
            'permissions': {'modules': ['all']},
            'actif': True
        }
    )
    
    if created:
        print(f"✅ Groupe PRIVILEGE créé: {groupe_privilege.nom}")
    else:
        print(f"✅ Groupe PRIVILEGE existant: {groupe_privilege.nom}")
    
    # 2. Créer un utilisateur de test avec mot de passe
    utilisateur_test, created = Utilisateur.objects.get_or_create(
        username='test_privilege',
        defaults={
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'Privilege',
            'is_active': True
        }
    )
    
    if created:
        # Définir un mot de passe
        utilisateur_test.set_password('test123')
        utilisateur_test.save()
        print(f"✅ Utilisateur de test créé: {utilisateur_test.username}")
    else:
        print(f"✅ Utilisateur de test existant: {utilisateur_test.username}")
    
    # 3. Ajouter l'utilisateur au groupe PRIVILEGE
    utilisateur_test.groups.add(groupe_privilege)
    print(f"✅ Utilisateur ajouté au groupe PRIVILEGE")
    
    # 4. Tester la création d'une configuration
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
        
        print(f"✅ Configuration créée: {config.nom_tableau}")
        
        # 5. Tester la modification
        ancien_nom = config.nom_tableau
        config.nom_tableau = 'Tableau Modifié'
        config.save()
        print(f"✅ Configuration modifiée: {ancien_nom} -> {config.nom_tableau}")
        
        # 6. Tester la modification des widgets
        anciens_widgets = config.widgets_actifs.copy()
        config.widgets_actifs = ['statistiques_generales', 'activite_recente']
        config.save()
        print(f"✅ Widgets modifiés: {anciens_widgets} -> {config.widgets_actifs}")
        
        # 7. Tester la modification des paramètres de sécurité
        config.masquer_montants_sensibles = False
        config.affichage_anonymise = True
        config.limite_donnees_recentes = 60
        config.save()
        print(f"✅ Paramètres de sécurité modifiés")
        print(f"   - Masquer montants: {config.masquer_montants_sensibles}")
        print(f"   - Affichage anonymisé: {config.affichage_anonymise}")
        print(f"   - Limite jours: {config.limite_donnees_recentes}")
        
        # 8. Tester la récupération depuis la base
        config_recuperee = ConfigurationTableauBord.objects.get(
            utilisateur=utilisateur_test,
            par_defaut=True
        )
        print(f"✅ Configuration récupérée depuis la base: {config_recuperee.nom_tableau}")
        print(f"   - Widgets: {config_recuperee.widgets_actifs}")
        print(f"   - Masquer montants: {config_recuperee.masquer_montants_sensibles}")
        
        print("\n🎉 Test de sauvegarde réussi !")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    test_sauvegarde_reel()
