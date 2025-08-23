#!/usr/bin/env python
"""
Script pour mettre à jour les permissions des groupes de travail
selon la distribution des pages par fonction
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from utilisateurs.models import GroupeTravail
from django.core.management import execute_from_command_line

def mettre_a_jour_permissions_groupes():
    """Met à jour les permissions des groupes selon leur fonction"""
    
    print("🔄 Mise à jour des permissions des groupes...")
    
    # Définition des permissions par groupe
    permissions_groupes = {
        'CAISSE': {
            'modules': ['paiements', 'retraits', 'cautions', 'rapports_financiers'],
            'actions': ['read', 'write', 'create'],
            'restrictions': ['pas_acces_utilisateurs', 'pas_acces_groupes'],
            'description': 'Gestion des paiements, retraits et finances'
        },
        'ADMINISTRATION': {
            'modules': ['proprietes', 'bailleurs', 'locataires', 'contrats', 'notifications'],
            'actions': ['read', 'write', 'create', 'delete'],
            'restrictions': ['pas_acces_utilisateurs', 'pas_acces_groupes'],
            'description': 'Gestion administrative des propriétés et contrats'
        },
        'CONTROLES': {
            'modules': ['paiements', 'contrats', 'proprietes', 'audit', 'rapports_controle'],
            'actions': ['read', 'validate', 'audit'],
            'restrictions': ['pas_modification_directe', 'pas_acces_utilisateurs'],
            'description': 'Contrôle et audit des données'
        },
        'PRIVILEGE': {
            'modules': ['paiements', 'proprietes', 'contrats', 'utilisateurs', 'groupes', 'systeme'],
            'actions': ['read', 'write', 'create', 'delete', 'admin'],
            'restrictions': [],
            'description': 'Accès complet à toutes les fonctionnalités'
        }
    }
    
    # Mise à jour des groupes
    for nom_groupe, permissions in permissions_groupes.items():
        try:
            groupe = GroupeTravail.objects.get(nom=nom_groupe)
            groupe.permissions = permissions
            groupe.description = permissions['description']
            groupe.save()
            print(f"✅ Groupe {nom_groupe} mis à jour avec succès")
            print(f"   Modules: {', '.join(permissions['modules'])}")
            print(f"   Actions: {', '.join(permissions['actions'])}")
            print()
        except GroupeTravail.DoesNotExist:
            print(f"❌ Groupe {nom_groupe} non trouvé")
        except Exception as e:
            print(f"❌ Erreur lors de la mise à jour du groupe {nom_groupe}: {e}")
    
    print("🎯 Distribution des pages par groupe:")
    print()
    print("📊 CAISSE:")
    print("   • Paiements (création, validation, suivi)")
    print("   • Retraits vers les bailleurs")
    print("   • Suivi des cautions")
    print("   • Rapports financiers")
    print()
    print("📋 ADMINISTRATION:")
    print("   • Propriétés (création, modification, suivi)")
    print("   • Bailleurs (gestion complète)")
    print("   • Locataires (gestion complète)")
    print("   • Contrats (création, modification, renouvellement)")
    print("   • Notifications")
    print()
    print("🔍 CONTROLES:")
    print("   • Contrôle des paiements")
    print("   • Validation des contrats")
    print("   • Audit des données")
    print("   • Rapports de contrôle")
    print()
    print("👑 PRIVILEGE:")
    print("   • Toutes les pages")
    print("   • Gestion des utilisateurs")
    print("   • Gestion des groupes")
    print("   • Configuration système")
    print()
    
    print("✅ Mise à jour des permissions terminée!")

if __name__ == '__main__':
    mettre_a_jour_permissions_groupes() 