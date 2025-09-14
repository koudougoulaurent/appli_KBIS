#!/usr/bin/env python3
"""
Script de sauvegarde des données pour garantir la permanence
Sauvegarde toutes les données importantes avant redéploiement
"""

import os
import sys
import django
import json
from datetime import datetime

# Configuration de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from utilisateurs.models import GroupeTravail, Utilisateur
from proprietes.models import TypeBien, Propriete, Bailleur, Locataire
from contrats.models import Contrat
from paiements.models import Paiement

def sauvegarder_donnees():
    """Sauvegarde toutes les données importantes"""
    try:
        print("💾 SAUVEGARDE DES DONNÉES PERMANENTES")
        print("=" * 40)
        
        # Créer le dossier de sauvegarde
        backup_dir = "backup_data"
        os.makedirs(backup_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 1. Sauvegarder les groupes de travail
        groupes_data = []
        for groupe in GroupeTravail.objects.all():
            groupes_data.append({
                'nom': groupe.nom,
                'description': groupe.description,
                'permissions': groupe.permissions,
                'actif': groupe.actif,
                'date_creation': groupe.date_creation.isoformat() if groupe.date_creation else None,
                'date_modification': groupe.date_modification.isoformat() if groupe.date_modification else None
            })
        
        with open(f"{backup_dir}/groupes_{timestamp}.json", 'w', encoding='utf-8') as f:
            json.dump(groupes_data, f, ensure_ascii=False, indent=2)
        print(f"✅ Groupes sauvegardés: {len(groupes_data)}")
        
        # 2. Sauvegarder les types de biens
        types_data = []
        for type_bien in TypeBien.objects.all():
            types_data.append({
                'nom': type_bien.nom,
                'description': type_bien.description,
                'est_actif': getattr(type_bien, 'est_actif', True)
            })
        
        with open(f"{backup_dir}/types_biens_{timestamp}.json", 'w', encoding='utf-8') as f:
            json.dump(types_data, f, ensure_ascii=False, indent=2)
        print(f"✅ Types de biens sauvegardés: {len(types_data)}")
        
        # 3. Sauvegarder les utilisateurs (sans les mots de passe)
        utilisateurs_data = []
        for user in Utilisateur.objects.all():
            utilisateurs_data.append({
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'groupe_travail': user.groupe_travail.nom if user.groupe_travail else None,
                'is_staff': user.is_staff,
                'is_superuser': user.is_superuser,
                'actif': user.actif,
                'poste': getattr(user, 'poste', ''),
                'departement': getattr(user, 'departement', ''),
                'telephone': getattr(user, 'telephone', ''),
                'date_joined': user.date_joined.isoformat() if user.date_joined else None
            })
        
        with open(f"{backup_dir}/utilisateurs_{timestamp}.json", 'w', encoding='utf-8') as f:
            json.dump(utilisateurs_data, f, ensure_ascii=False, indent=2)
        print(f"✅ Utilisateurs sauvegardés: {len(utilisateurs_data)}")
        
        # 4. Sauvegarder les propriétés
        proprietes_data = []
        for prop in Propriete.objects.all():
            proprietes_data.append({
                'adresse': prop.adresse,
                'ville': prop.ville,
                'code_postal': prop.code_postal,
                'surface': str(prop.surface) if prop.surface else None,
                'nombre_pieces': prop.nombre_pieces,
                'loyer_actuel': str(prop.loyer_actuel) if hasattr(prop, 'loyer_actuel') and prop.loyer_actuel else None,
                'charges_mensuelles': str(prop.charges_mensuelles) if hasattr(prop, 'charges_mensuelles') and prop.charges_mensuelles else None,
                'type_bien': prop.type_bien.nom if prop.type_bien else None,
                'bailleur': prop.bailleur.nom if prop.bailleur else None,
                'est_actif': getattr(prop, 'est_actif', True)
            })
        
        with open(f"{backup_dir}/proprietes_{timestamp}.json", 'w', encoding='utf-8') as f:
            json.dump(proprietes_data, f, ensure_ascii=False, indent=2)
        print(f"✅ Propriétés sauvegardées: {len(proprietes_data)}")
        
        # 5. Sauvegarder les bailleurs
        bailleurs_data = []
        for bailleur in Bailleur.objects.all():
            bailleurs_data.append({
                'nom': bailleur.nom,
                'prenom': bailleur.prenom,
                'email': bailleur.email,
                'telephone': bailleur.telephone,
                'adresse': bailleur.adresse,
                'ville': bailleur.ville,
                'code_postal': bailleur.code_postal,
                'est_actif': getattr(bailleur, 'est_actif', True)
            })
        
        with open(f"{backup_dir}/bailleurs_{timestamp}.json", 'w', encoding='utf-8') as f:
            json.dump(bailleurs_data, f, ensure_ascii=False, indent=2)
        print(f"✅ Bailleurs sauvegardés: {len(bailleurs_data)}")
        
        # 6. Sauvegarder les locataires
        locataires_data = []
        for locataire in Locataire.objects.all():
            locataires_data.append({
                'nom': locataire.nom,
                'prenom': locataire.prenom,
                'email': locataire.email,
                'telephone': locataire.telephone,
                'adresse': locataire.adresse,
                'ville': locataire.ville,
                'code_postal': locataire.code_postal,
                'est_actif': getattr(locataire, 'est_actif', True)
            })
        
        with open(f"{backup_dir}/locataires_{timestamp}.json", 'w', encoding='utf-8') as f:
            json.dump(locataires_data, f, ensure_ascii=False, indent=2)
        print(f"✅ Locataires sauvegardés: {len(locataires_data)}")
        
        # 7. Créer un fichier de résumé
        resume = {
            'timestamp': timestamp,
            'date_sauvegarde': datetime.now().isoformat(),
            'statistiques': {
                'groupes': len(groupes_data),
                'types_biens': len(types_data),
                'utilisateurs': len(utilisateurs_data),
                'proprietes': len(proprietes_data),
                'bailleurs': len(bailleurs_data),
                'locataires': len(locataires_data)
            }
        }
        
        with open(f"{backup_dir}/resume_{timestamp}.json", 'w', encoding='utf-8') as f:
            json.dump(resume, f, ensure_ascii=False, indent=2)
        
        print(f"\n📊 RÉSUMÉ DE LA SAUVEGARDE")
        print("=" * 30)
        print(f"📁 Dossier: {backup_dir}/")
        print(f"⏰ Timestamp: {timestamp}")
        print(f"👥 Utilisateurs: {len(utilisateurs_data)}")
        print(f"🏠 Propriétés: {len(proprietes_data)}")
        print(f"👤 Bailleurs: {len(bailleurs_data)}")
        print(f"👤 Locataires: {len(locataires_data)}")
        print(f"📋 Groupes: {len(groupes_data)}")
        print(f"🏠 Types de biens: {len(types_data)}")
        
        print(f"\n✅ SAUVEGARDE TERMINÉE AVEC SUCCÈS !")
        print(f"📁 Tous les fichiers sont dans le dossier: {backup_dir}/")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la sauvegarde: {e}")
        import traceback
        print(traceback.format_exc())
        return False

if __name__ == "__main__":
    sauvegarder_donnees()
