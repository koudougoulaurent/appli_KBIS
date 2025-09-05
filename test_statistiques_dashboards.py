#!/usr/bin/env python
"""
Script de test pour vérifier les statistiques des dashboards
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from django.db.models import Q, Count, Sum
from datetime import datetime, timedelta
from proprietes.models import Propriete, Bailleur
from contrats.models import Contrat
from paiements.models import Paiement, Retrait
from utilisateurs.models import Utilisateur, GroupeTravail
from notifications.models import Notification

def test_statistiques_caisse():
    """Test des statistiques du dashboard CAISSE"""
    print("💰 Test des statistiques CAISSE")
    print("-" * 40)
    
    mois_courant = datetime.now().month
    annee_courante = datetime.now().year
    
    # Statistiques des paiements
    stats_paiements = Paiement.objects.filter(
        date_paiement__month=mois_courant,
        date_paiement__year=annee_courante
    ).aggregate(
        total_paiements=Sum('montant'),
        count_paiements=Count('id')
    )
    
    # Statistiques des retraits
    stats_retraits = Retrait.objects.filter(
        date_demande__month=mois_courant,
        date_demande__year=annee_courante
    ).aggregate(
        total_retraits=Sum('montant')
    )
    
    # Statistiques des cautions
    stats_cautions = Paiement.objects.filter(
        type_paiement='depot_garantie',
        statut='valide'
    ).aggregate(
        total_cautions=Sum('montant')
    )
    
    # Paiements en attente
    stats_attente = Paiement.objects.filter(statut='en_attente').count()
    
    print(f"✅ Paiements du mois ({mois_courant}/{annee_courante}): {stats_paiements['total_paiements'] or 0} F CFA")
    print(f"✅ Retraits du mois: {stats_retraits['total_retraits'] or 0} F CFA")
    print(f"✅ Cautions en cours: {stats_cautions['total_cautions'] or 0} F CFA")
    print(f"✅ Paiements en attente: {stats_attente}")
    
    return {
        'paiements_mois': stats_paiements['total_paiements'] or 0,
        'retraits_mois': stats_retraits['total_retraits'] or 0,
        'cautions_cours': stats_cautions['total_cautions'] or 0,
        'paiements_attente': stats_attente,
    }

def test_statistiques_administration():
    """Test des statistiques du dashboard ADMINISTRATION"""
    print("\n🏠 Test des statistiques ADMINISTRATION")
    print("-" * 40)
    
    # Statistiques des propriétés
    stats_proprietes = Propriete.objects.aggregate(
        total=Count('id')
    )
    
    # Statistiques des contrats
    stats_contrats = Contrat.objects.aggregate(
        actifs=Count('id', filter=Q(est_actif=True)),
        renouveler=Count('id', filter=Q(
            date_fin__lte=datetime.now() + timedelta(days=30),
            est_actif=True
        ))
    )
    
    # Statistiques des bailleurs
    stats_bailleurs = Bailleur.objects.aggregate(
        total=Count('id')
    )
    
    print(f"✅ Total propriétés: {stats_proprietes['total']}")
    print(f"✅ Contrats actifs: {stats_contrats['actifs']}")
    print(f"✅ Total bailleurs: {stats_bailleurs['total']}")
    print(f"✅ Contrats à renouveler (30j): {stats_contrats['renouveler']}")
    
    return {
        'total_proprietes': stats_proprietes['total'],
        'contrats_actifs': stats_contrats['actifs'],
        'total_bailleurs': stats_bailleurs['total'],
        'contrats_renouveler': stats_contrats['renouveler'],
    }

def test_statistiques_controles():
    """Test des statistiques du dashboard CONTROLES"""
    print("\n🔍 Test des statistiques CONTROLES")
    print("-" * 40)
    
    # Statistiques des contrôles
    stats_controles = Paiement.objects.aggregate(
        a_valider=Count('id', filter=Q(statut='en_attente'))
    )
    
    stats_contrats = Contrat.objects.aggregate(
        a_verifier=Count('id', filter=Q(est_actif=True))
    )
    
    print(f"✅ Paiements à valider: {stats_controles['a_valider']}")
    print(f"✅ Contrats à vérifier: {stats_contrats['a_verifier']}")
    print(f"✅ Anomalies: 0 (à implémenter)")
    print(f"✅ Rapports générés: 0 (à implémenter)")
    
    return {
        'paiements_a_valider': stats_controles['a_valider'],
        'contrats_a_verifier': stats_contrats['a_verifier'],
        'anomalies': 0,
        'rapports_generes': 0,
    }

def test_statistiques_privilege():
    """Test des statistiques du dashboard PRIVILEGE"""
    print("\n👑 Test des statistiques PRIVILEGE")
    print("-" * 40)
    
    # Statistiques système
    stats_systeme = {
        'proprietes': Propriete.objects.count(),
        'utilisateurs': Utilisateur.objects.count(),
        'contrats': Contrat.objects.count(),
        'paiements': Paiement.objects.count(),
        'groupes': GroupeTravail.objects.count(),
        'notifications': Notification.objects.count(),
        'utilisateurs_actifs': Utilisateur.objects.filter(actif=True).count(),
    }
    
    print(f"✅ Total propriétés: {stats_systeme['proprietes']}")
    print(f"✅ Total utilisateurs: {stats_systeme['utilisateurs']}")
    print(f"✅ Total contrats: {stats_systeme['contrats']}")
    print(f"✅ Total paiements: {stats_systeme['paiements']}")
    print(f"✅ Total groupes: {stats_systeme['groupes']}")
    print(f"✅ Total notifications: {stats_systeme['notifications']}")
    print(f"✅ Utilisateurs actifs: {stats_systeme['utilisateurs_actifs']}")
    
    return {
        'total_proprietes': stats_systeme['proprietes'],
        'total_utilisateurs': stats_systeme['utilisateurs'],
        'total_contrats': stats_systeme['contrats'],
        'total_paiements': stats_systeme['paiements'],
        'total_groupes': stats_systeme['groupes'],
        'total_notifications': stats_systeme['notifications'],
        'utilisateurs_actifs': stats_systeme['utilisateurs_actifs'],
    }

def test_donnees_reelles():
    """Test des données réelles dans la base"""
    print("\n📊 Données réelles dans la base")
    print("-" * 40)
    
    print(f"📈 Propriétés: {Propriete.objects.count()}")
    print(f"📈 Utilisateurs: {Utilisateur.objects.count()}")
    print(f"📈 Contrats: {Contrat.objects.count()}")
    print(f"📈 Paiements: {Paiement.objects.count()}")
    print(f"📈 Retraits: {Retrait.objects.count()}")
    print(f"📈 Notifications: {Notification.objects.count()}")
    print(f"📈 Groupes: {GroupeTravail.objects.count()}")
    
    # Détails des paiements
    paiements_par_statut = Paiement.objects.values('statut').annotate(count=Count('id'))
    print(f"\n📈 Paiements par statut:")
    for statut in paiements_par_statut:
        print(f"   - {statut['statut']}: {statut['count']}")
    
    # Détails des contrats
    contrats_actifs = Contrat.objects.filter(est_actif=True).count()
    print(f"📈 Contrats actifs: {contrats_actifs}")

def main():
    """Fonction principale"""
    print("🔍 VÉRIFICATION DES STATISTIQUES DES DASHBOARDS")
    print("=" * 60)
    
    # Tests des statistiques par groupe
    stats_caisse = test_statistiques_caisse()
    stats_admin = test_statistiques_administration()
    stats_controles = test_statistiques_controles()
    stats_privilege = test_statistiques_privilege()
    
    # Test des données réelles
    test_donnees_reelles()
    
    print("\n" + "=" * 60)
    print("📋 RÉSUMÉ DES STATISTIQUES")
    print("=" * 60)
    
    print(f"💰 CAISSE:")
    print(f"   - Paiements du mois: {stats_caisse['paiements_mois']} F CFA")
    print(f"   - Retraits du mois: {stats_caisse['retraits_mois']} F CFA")
    print(f"   - Cautions en cours: {stats_caisse['cautions_cours']} F CFA")
    print(f"   - Paiements en attente: {stats_caisse['paiements_attente']}")
    
    print(f"\n🏠 ADMINISTRATION:")
    print(f"   - Total propriétés: {stats_admin['total_proprietes']}")
    print(f"   - Contrats actifs: {stats_admin['contrats_actifs']}")
    print(f"   - Total bailleurs: {stats_admin['total_bailleurs']}")
    print(f"   - Contrats à renouveler: {stats_admin['contrats_renouveler']}")
    
    print(f"\n🔍 CONTROLES:")
    print(f"   - Paiements à valider: {stats_controles['paiements_a_valider']}")
    print(f"   - Contrats à vérifier: {stats_controles['contrats_a_verifier']}")
    
    print(f"\n👑 PRIVILEGE:")
    print(f"   - Total propriétés: {stats_privilege['total_proprietes']}")
    print(f"   - Total utilisateurs: {stats_privilege['total_utilisateurs']}")
    print(f"   - Total contrats: {stats_privilege['total_contrats']}")
    print(f"   - Total paiements: {stats_privilege['total_paiements']}")
    print(f"   - Total groupes: {stats_privilege['total_groupes']}")
    print(f"   - Total notifications: {stats_privilege['total_notifications']}")
    print(f"   - Utilisateurs actifs: {stats_privilege['utilisateurs_actifs']}")

if __name__ == '__main__':
    main() 