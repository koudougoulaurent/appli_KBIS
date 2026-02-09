"""
Script d'exemple pour tester l'import de paiements historiques

Ce script crée des paiements de test pour démontrer le système.
À adapter selon vos besoins réels.
"""
import os
import django
from datetime import datetime

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from paiements.models import Paiement
from contrats.models import Contrat

def test_import_avec_retard():
    """
    Test avec un contrat ayant un retard de paiement
    """
    print("\n" + "="*80)
    print("📦 TEST : Import de paiements avec retard")
    print("="*80 + "\n")
    
    # Remplacez par un vrai numéro de contrat de votre base
    numero_contrat = 'CT-2024-001'  # ← MODIFIER ICI
    
    try:
        contrat = Contrat.objects.get(numero_contrat=numero_contrat)
        print(f"✅ Contrat trouvé : {contrat.numero_contrat}")
        print(f"   Locataire : {contrat.locataire.get_nom_complet()}")
        print(f"   Loyer : {contrat.loyer_mensuel} FCFA\n")
        
    except Contrat.DoesNotExist:
        print(f"❌ Contrat {numero_contrat} non trouvé !")
        print(f"ℹ️  Modifiez la variable 'numero_contrat' avec un contrat existant.\n")
        return
    
    # Paiements à importer (exemple avec retard)
    paiements_a_importer = [
        {
            'montant': 250000,
            'type_paiement': 'loyer',
            'mois_paye': 'Janvier 2024',
            'date_paiement': '2024-01-15',
            'mode_paiement': 'virement',
            'notes': '📦 Import test - Paiement à jour'
        },
        {
            'montant': 250000,
            'type_paiement': 'loyer',
            'mois_paye': 'Février 2024',
            'date_paiement': '2024-02-20',
            'mode_paiement': 'virement',
            'notes': '📦 Import test - Paiement à jour'
        },
        # MARS 2024 MANQUANT = RETARD !
        {
            'montant': 250000,
            'type_paiement': 'loyer',
            'mois_paye': 'Avril 2024',
            'date_paiement': '2024-04-10',
            'mode_paiement': 'virement',
            'notes': '📦 Import test - Paiement malgré retard mars'
        },
    ]
    
    print("📋 Paiements à importer :")
    for i, p in enumerate(paiements_a_importer, 1):
        print(f"   {i}. {p['mois_paye']} - {p['montant']:,} FCFA")
    print()
    
    # Import des paiements
    for data in paiements_a_importer:
        try:
            paiement = Paiement.objects.create(
                contrat=contrat,
                montant=data['montant'],
                type_paiement=data['type_paiement'],
                mois_paye=data['mois_paye'],
                date_paiement=datetime.strptime(data['date_paiement'], '%Y-%m-%d').date(),
                mode_paiement=data['mode_paiement'],
                statut='valide',
                notes=data['notes'],
                est_saisie_manuelle_historique=True,  # ← FLAG IMPORTANT !
                montant_net_paye=data['montant']
            )
            
            print(f"✅ Importé : {data['mois_paye']} - {data['montant']:,} FCFA")
            print(f"   ID: {paiement.id} | Badge: 📦 HISTORIQUE")
            
        except Exception as e:
            print(f"❌ Erreur pour {data['mois_paye']}: {str(e)}")
    
    print("\n" + "="*80)
    print("🎉 Import terminé !")
    print("="*80 + "\n")
    
    print("📊 Résultat attendu :")
    print("   - Janvier 2024 : ✅ Payé")
    print("   - Février 2024 : ✅ Payé")
    print("   - Mars 2024    : ❌ RETARD (à saisir)")
    print("   - Avril 2024   : ✅ Payé")
    print("\n   → Le système devrait calculer : Prochain paiement = MARS 2024\n")
    
    print("🔍 Vérifications à faire :")
    print("   1. Allez dans l'admin : /admin/paiements/paiement/")
    print("   2. Filtrez par 'Saisie manuelle historique = Oui'")
    print("   3. Vérifiez le badge '📦 HISTORIQUE' sur les 3 paiements")
    print("   4. Regardez les logs de la console Django")
    print(f"   5. Créez un nouveau paiement pour {contrat.numero_contrat}")
    print("      → Le mois suggéré devrait être MARS 2024 (le retard)\n")


def test_import_avec_avance():
    """
    Test avec un contrat ayant une avance de loyer
    """
    print("\n" + "="*80)
    print("📦 TEST : Import de paiements avec avance")
    print("="*80 + "\n")
    
    # Remplacez par un vrai numéro de contrat de votre base
    numero_contrat = 'CT-2026-016'  # ← MODIFIER ICI
    
    try:
        contrat = Contrat.objects.get(numero_contrat=numero_contrat)
        print(f"✅ Contrat trouvé : {contrat.numero_contrat}")
        print(f"   Locataire : {contrat.locataire.get_nom_complet()}")
        print(f"   Loyer : {contrat.loyer_mensuel} FCFA\n")
        
    except Contrat.DoesNotExist:
        print(f"❌ Contrat {numero_contrat} non trouvé !")
        print(f"ℹ️  Modifiez la variable 'numero_contrat' avec un contrat existant.\n")
        return
    
    # Paiements à importer (exemple avec avance)
    paiements_a_importer = [
        {
            'montant': 750000,  # 3 mois d'avance
            'type_paiement': 'avance_loyer',
            'mois_paye': 'Février-Avril 2026',
            'date_paiement': '2026-02-09',
            'mode_paiement': 'virement',
            'notes': '📦 Import test - Avance 3 mois'
        },
        {
            'montant': 250000,
            'type_paiement': 'loyer',
            'mois_paye': 'Mai 2026',
            'date_paiement': '2026-05-05',
            'mode_paiement': 'virement',
            'notes': '📦 Import test - Premier loyer après avance'
        },
    ]
    
    print("📋 Paiements à importer :")
    for i, p in enumerate(paiements_a_importer, 1):
        print(f"   {i}. {p['mois_paye']} - {p['montant']:,} FCFA")
    print()
    
    # Import des paiements
    for data in paiements_a_importer:
        try:
            paiement = Paiement.objects.create(
                contrat=contrat,
                montant=data['montant'],
                type_paiement=data['type_paiement'],
                mois_paye=data['mois_paye'],
                date_paiement=datetime.strptime(data['date_paiement'], '%Y-%m-%d').date(),
                mode_paiement=data['mode_paiement'],
                statut='valide',
                notes=data['notes'],
                est_saisie_manuelle_historique=True,  # ← FLAG IMPORTANT !
                montant_net_paye=data['montant']
            )
            
            print(f"✅ Importé : {data['mois_paye']} - {data['montant']:,} FCFA")
            print(f"   ID: {paiement.id} | Badge: 📦 HISTORIQUE")
            
        except Exception as e:
            print(f"❌ Erreur pour {data['mois_paye']}: {str(e)}")
    
    print("\n" + "="*80)
    print("🎉 Import terminé !")
    print("="*80 + "\n")
    
    print("📊 Résultat attendu :")
    print("   - Février 2026 : ✅ Couvert par avance")
    print("   - Mars 2026    : ✅ Couvert par avance")
    print("   - Avril 2026   : ✅ Couvert par avance")
    print("   - Mai 2026     : ✅ Payé")
    print("\n   → Le système devrait calculer : Prochain paiement = JUIN 2026\n")


if __name__ == '__main__':
    print("\n")
    print("🚀 " + "="*76 + " 🚀")
    print("   SCRIPT DE TEST : Import de Paiements Historiques")
    print("🚀 " + "="*76 + " 🚀")
    
    print("\n⚠️  ATTENTION :")
    print("   - Modifiez les numéros de contrat avant d'exécuter")
    print("   - Assurez-vous que le serveur Django tourne")
    print("   - Surveillez les logs dans la console serveur\n")
    
    choix = input("Quel test voulez-vous exécuter ?\n"
                  "1. Test avec retard de paiement\n"
                  "2. Test avec avance de loyer\n"
                  "3. Les deux\n"
                  "Choix (1/2/3) : ")
    
    if choix == '1':
        test_import_avec_retard()
    elif choix == '2':
        test_import_avec_avance()
    elif choix == '3':
        test_import_avec_retard()
        test_import_avec_avance()
    else:
        print("❌ Choix invalide !")
    
    print("\n✅ Terminé ! Consultez l'admin Django et les logs.\n")
