#!/usr/bin/env python
"""
Script de débogage pour la vue dashboard
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth import authenticate
from utilisateurs.views import dashboard_groupe
from utilisateurs.models import Utilisateur

def debug_dashboard():
    """Déboguer la vue dashboard"""
    print("🔍 Débogage de la vue dashboard")
    print("-" * 40)
    
    # Créer une factory de requêtes
    factory = RequestFactory()
    
    # Authentifier un utilisateur
    user = authenticate(username='test_caisse', password='test123')
    if not user:
        print("❌ Impossible de s'authentifier")
        return
    
    print(f"✅ Utilisateur authentifié: {user.username}")
    print(f"   - Groupe: {user.groupe_travail}")
    
    # Créer une requête
    request = factory.get('/utilisateurs/dashboard/CAISSE/')
    request.user = user
    
    # Appeler la vue directement
    try:
        response = dashboard_groupe(request, 'CAISSE')
        print(f"✅ Vue exécutée avec succès")
        print(f"   - Status code: {response.status_code}")
        
        if hasattr(response, 'context'):
            print(f"   - Contexte présent: {response.context is not None}")
            if response.context:
                print(f"   - Clés du contexte: {list(response.context.keys())}")
                if 'stats' in response.context:
                    stats = response.context['stats']
                    print(f"   - Statistiques: {stats}")
                else:
                    print("   - ❌ Pas de statistiques dans le contexte")
            else:
                print("   - ❌ Contexte vide")
        else:
            print("   - ❌ Pas de contexte")
            
    except Exception as e:
        print(f"❌ Erreur lors de l'exécution: {e}")
        import traceback
        traceback.print_exc()

def test_direct_stats():
    """Test direct du calcul des statistiques"""
    print("\n📊 Test direct du calcul des statistiques")
    print("-" * 40)
    
    from django.db.models import Q, Count, Sum
    from datetime import datetime
    from paiements.models import Paiement, Retrait
    
    mois_courant = datetime.now().month
    annee_courante = datetime.now().year
    
    # Calculer les statistiques directement
    stats_paiements = Paiement.objects.filter(
        date_paiement__month=mois_courant,
        date_paiement__year=annee_courante
    ).aggregate(
        total_paiements=Sum('montant'),
        count_paiements=Count('id')
    )
    
    stats_retraits = Retrait.objects.filter(
        date_demande__month=mois_courant,
        date_demande__year=annee_courante
    ).aggregate(
        total_retraits=Sum('montant')
    )
    
    stats_cautions = Paiement.objects.filter(
        type_paiement='depot_garantie',
        statut='valide'
    ).aggregate(
        total_cautions=Sum('montant')
    )
    
    stats_attente = Paiement.objects.filter(statut='en_attente').count()
    
    stats = {
        'paiements_mois': stats_paiements['total_paiements'] or 0,
        'retraits_mois': stats_retraits['total_retraits'] or 0,
        'cautions_cours': stats_cautions['total_cautions'] or 0,
        'paiements_attente': stats_attente,
    }
    
    print(f"✅ Statistiques calculées:")
    for key, value in stats.items():
        print(f"   - {key}: {value}")

def main():
    """Fonction principale"""
    print("🔍 DÉBOGAGE DES DASHBOARDS")
    print("=" * 60)
    
    test_direct_stats()
    debug_dashboard()

if __name__ == '__main__':
    main() 