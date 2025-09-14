#!/usr/bin/env python3
"""
Script de vérification automatique des données essentielles
S'exécute au démarrage sur Render pour s'assurer que les données de base existent
"""

import os
import sys
import django

# Configuration de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from django.contrib.auth.hashers import make_password
from utilisateurs.models import GroupeTravail, Utilisateur
from proprietes.models import TypeBien
import logging

logger = logging.getLogger(__name__)

def verifier_et_creer_donnees():
    """Vérifie et crée les données essentielles si elles n'existent pas"""
    try:
        print("🔍 Vérification des données essentielles...")
        
        # 1. Créer les groupes de travail
        groupes_data = [
            {'nom': 'CAISSE', 'description': 'Gestion des paiements et retraits'},
            {'nom': 'CONTROLES', 'description': 'Contrôle et audit'},
            {'nom': 'ADMINISTRATION', 'description': 'Gestion administrative'},
            {'nom': 'PRIVILEGE', 'description': 'Accès complet'},
        ]
        
        for groupe_data in groupes_data:
            groupe, created = GroupeTravail.objects.update_or_create(
                nom=groupe_data['nom'],
                defaults={
                    'description': groupe_data['description'],
                    'actif': True,
                    'permissions': {}
                }
            )
            if created:
                print(f"✅ Groupe créé: {groupe.nom}")
            else:
                print(f"ℹ️  Groupe existant: {groupe.nom}")
        
        # 2. Créer les types de biens
        types_data = [
            {'nom': 'Appartement', 'description': 'Appartement en immeuble'},
            {'nom': 'Maison', 'description': 'Maison individuelle'},
            {'nom': 'Studio', 'description': 'Studio meublé'},
            {'nom': 'Loft', 'description': 'Loft industriel'},
            {'nom': 'Villa', 'description': 'Villa avec jardin'},
            {'nom': 'Duplex', 'description': 'Duplex sur deux niveaux'},
            {'nom': 'Penthouse', 'description': 'Penthouse de luxe'},
            {'nom': 'Château', 'description': 'Château ou manoir'},
            {'nom': 'Ferme', 'description': 'Ferme ou propriété rurale'},
            {'nom': 'Bureau', 'description': 'Local commercial ou bureau'},
            {'nom': 'Commerce', 'description': 'Local commercial'},
            {'nom': 'Entrepôt', 'description': 'Entrepôt ou local industriel'},
            {'nom': 'Garage', 'description': 'Garage ou parking'},
            {'nom': 'Terrain', 'description': 'Terrain constructible'},
            {'nom': 'Autre', 'description': 'Autre type de bien'},
        ]
        
        for type_data in types_data:
            type_bien, created = TypeBien.objects.update_or_create(
                nom=type_data['nom'],
                defaults=type_data
            )
            if created:
                print(f"✅ Type créé: {type_bien.nom}")
            else:
                print(f"ℹ️  Type existant: {type_bien.nom}")
        
        # 3. Créer l'utilisateur admin s'il n'existe pas
        if not Utilisateur.objects.filter(username='admin').exists():
            groupe_privilege = GroupeTravail.objects.get(nom='PRIVILEGE')
            Utilisateur.objects.create(
                username='admin',
                email='admin@gestimmob.com',
                first_name='Super',
                last_name='Administrateur',
                groupe_travail=groupe_privilege,
                is_staff=True,
                is_superuser=True,
                actif=True,
                password=make_password('password123')
            )
            print("✅ Utilisateur admin créé")
        else:
            print("ℹ️  Utilisateur admin existant")
        
        print("🎉 Vérification des données terminée avec succès !")
        
    except Exception as e:
        print(f"❌ Erreur lors de la vérification des données: {e}")
        import traceback
        print(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    verifier_et_creer_donnees()