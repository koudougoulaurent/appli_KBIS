#!/usr/bin/env python3
"""
Script de restauration des données sauvegardées
Restaure les données depuis les fichiers de sauvegarde
"""

import os
import sys
import django
import json
from datetime import datetime

# Configuration de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from django.contrib.auth.hashers import make_password
from utilisateurs.models import GroupeTravail, Utilisateur
from proprietes.models import TypeBien, Propriete, Bailleur, Locataire

def restaurer_donnees(timestamp=None):
    """Restaure les données depuis les fichiers de sauvegarde"""
    try:
        print("🔄 RESTAURATION DES DONNÉES PERMANENTES")
        print("=" * 40)
        
        backup_dir = "backup_data"
        
        if not os.path.exists(backup_dir):
            print(f"❌ Dossier de sauvegarde {backup_dir} introuvable")
            return False
        
        # Trouver le fichier de sauvegarde le plus récent si timestamp non spécifié
        if not timestamp:
            fichiers = [f for f in os.listdir(backup_dir) if f.startswith('resume_') and f.endswith('.json')]
            if not fichiers:
                print("❌ Aucun fichier de sauvegarde trouvé")
                return False
            fichiers.sort(reverse=True)
            timestamp = fichiers[0].replace('resume_', '').replace('.json', '')
            print(f"📅 Utilisation de la sauvegarde la plus récente: {timestamp}")
        
        # 1. Restaurer les groupes de travail
        groupes_file = f"{backup_dir}/groupes_{timestamp}.json"
        if os.path.exists(groupes_file):
            with open(groupes_file, 'r', encoding='utf-8') as f:
                groupes_data = json.load(f)
            
            for groupe_data in groupes_data:
                groupe, created = GroupeTravail.objects.update_or_create(
                    nom=groupe_data['nom'],
                    defaults={
                        'description': groupe_data['description'],
                        'permissions': groupe_data['permissions'],
                        'actif': groupe_data['actif']
                    }
                )
                if created:
                    print(f"✅ Groupe restauré: {groupe.nom}")
                else:
                    print(f"ℹ️  Groupe existant: {groupe.nom}")
        
        # 2. Restaurer les types de biens
        types_file = f"{backup_dir}/types_biens_{timestamp}.json"
        if os.path.exists(types_file):
            with open(types_file, 'r', encoding='utf-8') as f:
                types_data = json.load(f)
            
            for type_data in types_data:
                type_bien, created = TypeBien.objects.update_or_create(
                    nom=type_data['nom'],
                    defaults={
                        'description': type_data['description'],
                        'est_actif': type_data.get('est_actif', True)
                    }
                )
                if created:
                    print(f"✅ Type restauré: {type_bien.nom}")
                else:
                    print(f"ℹ️  Type existant: {type_bien.nom}")
        
        # 3. Restaurer les utilisateurs
        utilisateurs_file = f"{backup_dir}/utilisateurs_{timestamp}.json"
        if os.path.exists(utilisateurs_file):
            with open(utilisateurs_file, 'r', encoding='utf-8') as f:
                utilisateurs_data = json.load(f)
            
            for user_data in utilisateurs_data:
                # Récupérer le groupe de travail
                groupe = None
                if user_data.get('groupe_travail'):
                    try:
                        groupe = GroupeTravail.objects.get(nom=user_data['groupe_travail'])
                    except GroupeTravail.DoesNotExist:
                        print(f"⚠️  Groupe {user_data['groupe_travail']} introuvable pour {user_data['username']}")
                
                user, created = Utilisateur.objects.update_or_create(
                    username=user_data['username'],
                    defaults={
                        'email': user_data['email'],
                        'first_name': user_data['first_name'],
                        'last_name': user_data['last_name'],
                        'groupe_travail': groupe,
                        'is_staff': user_data['is_staff'],
                        'is_superuser': user_data['is_superuser'],
                        'actif': user_data['actif'],
                        'poste': user_data.get('poste', ''),
                        'departement': user_data.get('departement', ''),
                        'telephone': user_data.get('telephone', ''),
                        'password': make_password('password123')  # Mot de passe par défaut
                    }
                )
                if created:
                    print(f"✅ Utilisateur restauré: {user.username}")
                else:
                    print(f"ℹ️  Utilisateur existant: {user.username}")
        
        print(f"\n✅ RESTAURATION TERMINÉE AVEC SUCCÈS !")
        print(f"📅 Timestamp utilisé: {timestamp}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la restauration: {e}")
        import traceback
        print(traceback.format_exc())
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        timestamp = sys.argv[1]
        restaurer_donnees(timestamp)
    else:
        restaurer_donnees()
