#!/usr/bin/env python3
"""
Script de gestion des données permanentes
Permet de sauvegarder, restaurer et gérer les données
"""

import os
import sys
import django
from datetime import datetime

# Configuration de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from utilisateurs.models import GroupeTravail, Utilisateur
from proprietes.models import TypeBien, Propriete, Bailleur, Locataire

def afficher_menu():
    """Affiche le menu de gestion des données"""
    print("\n" + "="*50)
    print("🗄️  GESTION DES DONNÉES PERMANENTES")
    print("="*50)
    print("1. 💾 Sauvegarder les données")
    print("2. 🔄 Restaurer les données")
    print("3. 📊 Afficher les statistiques")
    print("4. 🔍 Lister les sauvegardes")
    print("5. 🗑️  Supprimer les données de test")
    print("6. ❌ Quitter")
    print("="*50)

def afficher_statistiques():
    """Affiche les statistiques des données"""
    print("\n📊 STATISTIQUES DES DONNÉES")
    print("-" * 30)
    print(f"👥 Utilisateurs: {Utilisateur.objects.count()}")
    print(f"   • Actifs: {Utilisateur.objects.filter(actif=True).count()}")
    print(f"   • Staff: {Utilisateur.objects.filter(is_staff=True).count()}")
    print(f"   • Superusers: {Utilisateur.objects.filter(is_superuser=True).count()}")
    
    print(f"\n📋 Groupes de travail: {GroupeTravail.objects.count()}")
    for groupe in GroupeTravail.objects.all():
        print(f"   • {groupe.nom}: {groupe.description}")
    
    print(f"\n🏠 Types de biens: {TypeBien.objects.count()}")
    for type_bien in TypeBien.objects.all()[:10]:
        print(f"   • {type_bien.nom}")
    if TypeBien.objects.count() > 10:
        print(f"   ... et {TypeBien.objects.count() - 10} autres")
    
    print(f"\n🏢 Propriétés: {Propriete.objects.count()}")
    print(f"👤 Bailleurs: {Bailleur.objects.count()}")
    print(f"👤 Locataires: {Locataire.objects.count()}")

def lister_sauvegardes():
    """Liste les sauvegardes disponibles"""
    backup_dir = "backup_data"
    if not os.path.exists(backup_dir):
        print("❌ Aucune sauvegarde trouvée")
        return
    
    print("\n📁 SAUVEGARDES DISPONIBLES")
    print("-" * 30)
    
    fichiers = [f for f in os.listdir(backup_dir) if f.startswith('resume_') and f.endswith('.json')]
    if not fichiers:
        print("❌ Aucune sauvegarde trouvée")
        return
    
    fichiers.sort(reverse=True)
    for i, fichier in enumerate(fichiers, 1):
        timestamp = fichier.replace('resume_', '').replace('.json', '')
        try:
            date_obj = datetime.strptime(timestamp, "%Y%m%d_%H%M%S")
            date_str = date_obj.strftime("%d/%m/%Y %H:%M:%S")
            print(f"{i}. {date_str} ({timestamp})")
        except:
            print(f"{i}. {timestamp}")

def supprimer_donnees_test():
    """Supprime les données de test (demande confirmation)"""
    print("\n⚠️  ATTENTION: SUPPRESSION DES DONNÉES DE TEST")
    print("=" * 50)
    print("Cette action va supprimer TOUTES les données de test.")
    print("Les données réelles ne seront PAS affectées.")
    print("=" * 50)
    
    confirmation = input("Êtes-vous sûr de vouloir continuer ? (tapez 'SUPPRIMER'): ")
    
    if confirmation != "SUPPRIMER":
        print("❌ Suppression annulée")
        return
    
    print("\n🗑️  Suppression des données de test...")
    
    # Supprimer les utilisateurs de test (garder admin et directeur)
    utilisateurs_test = Utilisateur.objects.exclude(username__in=['admin', 'directeur'])
    count_users = utilisateurs_test.count()
    utilisateurs_test.delete()
    print(f"✅ {count_users} utilisateurs de test supprimés")
    
    # Supprimer les propriétés de test
    count_proprietes = Propriete.objects.count()
    Propriete.objects.all().delete()
    print(f"✅ {count_proprietes} propriétés supprimées")
    
    # Supprimer les bailleurs de test
    count_bailleurs = Bailleur.objects.count()
    Bailleur.objects.all().delete()
    print(f"✅ {count_bailleurs} bailleurs supprimés")
    
    # Supprimer les locataires de test
    count_locataires = Locataire.objects.count()
    Locataire.objects.all().delete()
    print(f"✅ {count_locataires} locataires supprimés")
    
    print("\n✅ Suppression des données de test terminée")
    print("ℹ️  Les groupes de travail et types de biens sont conservés")

def main():
    """Fonction principale"""
    while True:
        afficher_menu()
        choix = input("\nVotre choix (1-6): ").strip()
        
        if choix == "1":
            print("\n💾 Sauvegarde en cours...")
            os.system("python sauvegarder_donnees.py")
            
        elif choix == "2":
            print("\n🔄 Restauration en cours...")
            os.system("python restaurer_donnees.py")
            
        elif choix == "3":
            afficher_statistiques()
            
        elif choix == "4":
            lister_sauvegardes()
            
        elif choix == "5":
            supprimer_donnees_test()
            
        elif choix == "6":
            print("\n👋 Au revoir !")
            break
            
        else:
            print("❌ Choix invalide")
        
        input("\nAppuyez sur Entrée pour continuer...")

if __name__ == "__main__":
    main()
