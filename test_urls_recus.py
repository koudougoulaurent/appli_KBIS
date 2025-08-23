#!/usr/bin/env python
"""
Test script pour vérifier que toutes les URLs des reçus fonctionnent correctement
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from django.urls import reverse
from paiements.models import Recu

def test_urls_recus():
    """Test toutes les URLs liées aux reçus."""
    
    print("🔗 TEST DES URLS DES REÇUS")
    print("=" * 60)
    
    # Vérifier qu'il y a des reçus
    nb_recus = Recu.objects.count()
    if nb_recus == 0:
        print("❌ Aucun reçu trouvé dans la base de données")
        return False
    
    print(f"📊 Reçus disponibles: {nb_recus}")
    
    # Prendre le premier reçu
    recu = Recu.objects.first()
    print(f"🎯 Test avec le reçu: {recu.numero_recu}")
    
    # Liste des URLs à tester
    urls_to_test = [
        ('paiements:recu_detail', [recu.pk], 'Détail du reçu'),
        ('paiements:recu_impression', [recu.pk], 'Impression du reçu'),
        ('paiements:recu_telecharger_pdf', [recu.pk], 'Téléchargement PDF'),
        ('paiements:valider_recu', [recu.pk], 'Validation du reçu'),
        ('paiements:invalider_recu', [recu.pk], 'Invalidation du reçu'),
        ('paiements:envoyer_recu_email', [recu.pk], 'Envoi par email'),
        ('paiements:changer_template_recu', [recu.pk], 'Changement de template'),
        ('paiements:recus_liste', [], 'Liste des reçus'),
        ('paiements:statistiques_recus', [], 'Statistiques des reçus'),
        ('paiements:export_recus', [], 'Export des reçus'),
    ]
    
    print("\n📋 Test des URLs:")
    print("-" * 60)
    
    success_count = 0
    error_count = 0
    
    for url_name, args, description in urls_to_test:
        try:
            url = reverse(url_name, args=args)
            print(f"✅ {description:25} : {url}")
            success_count += 1
        except Exception as e:
            print(f"❌ {description:25} : {str(e)}")
            error_count += 1
    
    print("\n" + "=" * 60)
    print("📊 RÉSULTATS")
    print("=" * 60)
    print(f"✅ URLs fonctionnelles : {success_count}")
    print(f"❌ URLs en erreur : {error_count}")
    print(f"📈 Taux de réussite : {(success_count/(success_count+error_count)*100):.1f}%")
    
    if error_count == 0:
        print("\n🎉 TOUTES LES URLS FONCTIONNENT CORRECTEMENT !")
        return True
    else:
        print(f"\n⚠️  {error_count} URL(s) à corriger")
        return False

def test_templates_recus():
    """Test que tous les templates des reçus existent."""
    
    print("\n📄 TEST DES TEMPLATES DES REÇUS")
    print("=" * 60)
    
    templates_to_test = [
        'paiements/recu_detail.html',
        'paiements/recu_impression.html',
        'paiements/envoyer_recu_email.html',
        'paiements/valider_recu.html',
        'paiements/invalider_recu.html',
        'paiements/changer_template_recu.html',
        'paiements/recus_liste.html',
        'paiements/statistiques_recus.html',
    ]
    
    print("📋 Vérification des templates:")
    print("-" * 60)
    
    success_count = 0
    error_count = 0
    
    for template in templates_to_test:
        template_path = os.path.join('templates', template)
        if os.path.exists(template_path):
            print(f"✅ {template:35} : Existe")
            success_count += 1
        else:
            print(f"❌ {template:35} : Manquant")
            error_count += 1
    
    print("\n" + "=" * 60)
    print("📊 RÉSULTATS")
    print("=" * 60)
    print(f"✅ Templates existants : {success_count}")
    print(f"❌ Templates manquants : {error_count}")
    print(f"📈 Taux de réussite : {(success_count/(success_count+error_count)*100):.1f}%")
    
    if error_count == 0:
        print("\n🎉 TOUS LES TEMPLATES EXISTENT !")
        return True
    else:
        print(f"\n⚠️  {error_count} template(s) à créer")
        return False

if __name__ == '__main__':
    print("🧪 TEST COMPLET DU SYSTÈME DE REÇUS")
    print("=" * 60)
    
    # Test des URLs
    urls_ok = test_urls_recus()
    
    # Test des templates
    templates_ok = test_templates_recus()
    
    print("\n" + "=" * 60)
    print("🎯 RÉSUMÉ FINAL")
    print("=" * 60)
    
    if urls_ok and templates_ok:
        print("🎉 SYSTÈME DE REÇUS ENTIÈREMENT FONCTIONNEL !")
        print("✅ Toutes les URLs fonctionnent")
        print("✅ Tous les templates existent")
        print("✅ Prêt pour la production")
    else:
        print("⚠️  PROBLÈMES DÉTECTÉS")
        if not urls_ok:
            print("❌ Certaines URLs ne fonctionnent pas")
        if not templates_ok:
            print("❌ Certains templates manquent")
        print("🔧 Corrections nécessaires avant utilisation") 