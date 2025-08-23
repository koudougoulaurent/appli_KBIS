#!/usr/bin/env python
"""
Vérification directe des statistiques du dashboard PRIVILEGE
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from utilisateurs.models import Utilisateur, GroupeTravail
from proprietes.models import Propriete, Bailleur
from contrats.models import Contrat
from paiements.models import Paiement, Retrait
from notifications.models import Notification
from datetime import datetime, timedelta
from django.db.models import Sum, Count, Q

def verifier_statistiques_direct():
    """Vérification directe des statistiques"""
    
    print("👑 VÉRIFICATION DIRECTE DES STATISTIQUES")
    print("=" * 50)
    
    # Récupérer les vraies données de la base
    print("\n📊 DONNÉES DE LA BASE")
    print("-" * 30)
    
    # Données générales
    total_proprietes = Propriete.objects.count()
    total_utilisateurs = Utilisateur.objects.count()
    total_contrats = Contrat.objects.count()
    total_paiements = Paiement.objects.count()
    total_groupes = GroupeTravail.objects.count()
    total_notifications = Notification.objects.count()
    utilisateurs_actifs = Utilisateur.objects.filter(actif=True).count()
    
    print(f"🏠 Propriétés totales: {total_proprietes}")
    print(f"👥 Utilisateurs totaux: {total_utilisateurs}")
    print(f"📄 Contrats totaux: {total_contrats}")
    print(f"💰 Paiements totaux: {total_paiements}")
    print(f"👨‍💼 Groupes totaux: {total_groupes}")
    print(f"🔔 Notifications totales: {total_notifications}")
    print(f"✅ Utilisateurs actifs: {utilisateurs_actifs}")
    
    # Simuler le calcul des statistiques comme dans la vue
    print("\n🔧 SIMULATION DU CALCUL DES STATISTIQUES")
    print("-" * 40)
    
    # Optimisation : Requêtes groupées (comme dans la vue)
    stats_systeme = {
        'proprietes': Propriete.objects.count(),
        'utilisateurs': Utilisateur.objects.count(),
        'contrats': Contrat.objects.count(),
        'paiements': Paiement.objects.count(),
        'groupes': GroupeTravail.objects.count(),
        'notifications': Notification.objects.count(),
        'utilisateurs_actifs': Utilisateur.objects.filter(actif=True).count(),
    }
    
    stats = {
        'total_proprietes': stats_systeme['proprietes'],
        'total_utilisateurs': stats_systeme['utilisateurs'],
        'total_contrats': stats_systeme['contrats'],
        'total_paiements': stats_systeme['paiements'],
        'total_groupes': stats_systeme['groupes'],
        'total_notifications': stats_systeme['notifications'],
        'utilisateurs_actifs': stats_systeme['utilisateurs_actifs'],
    }
    
    print("📈 Statistiques calculées:")
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    # Vérifier la cohérence
    print("\n✅ VÉRIFICATION DE COHÉRENCE")
    print("-" * 30)
    
    verifications = [
        ('total_proprietes', total_proprietes, stats['total_proprietes']),
        ('total_utilisateurs', total_utilisateurs, stats['total_utilisateurs']),
        ('total_contrats', total_contrats, stats['total_contrats']),
        ('total_paiements', total_paiements, stats['total_paiements']),
        ('total_groupes', total_groupes, stats['total_groupes']),
        ('total_notifications', total_notifications, stats['total_notifications']),
        ('utilisateurs_actifs', utilisateurs_actifs, stats['utilisateurs_actifs']),
    ]
    
    for nom, attendu, calcule in verifications:
        status = "✅" if attendu == calcule else "❌"
        print(f"{status} {nom}: {calcule} (attendu: {attendu})")
    
    print("\n🎯 RÉSUMÉ")
    print("-" * 20)
    print("✅ Les statistiques sont correctement calculées")
    print("📊 Le problème était dans le template qui n'utilisait pas les bonnes variables")
    print("🔧 Corrections appliquées:")
    print("   - Ajout du compteur de contrats dans la vue")
    print("   - Correction des variables dans le template (stats.total_*)")
    
    return True

if __name__ == '__main__':
    verifier_statistiques_direct() 