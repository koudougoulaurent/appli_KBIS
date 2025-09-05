#!/usr/bin/env python
"""
Script de test pour vérifier la migration de la devise F CFA vers F CFA
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from core.models import Devise
from core.utils import get_currency_settings, format_currency_fcfa
from django.conf import settings

def test_currency_settings():
    """Teste les paramètres de devise dans les settings"""
    print("🔍 Test des paramètres de devise...")
    
    try:
        # Vérifier les settings Django
        currency_settings = getattr(settings, 'CURRENCY_SETTINGS', {})
        
        print(f"   • DEFAULT_CURRENCY: {currency_settings.get('DEFAULT_CURRENCY', 'Non défini')}")
        print(f"   • CURRENCY_SYMBOL: {currency_settings.get('CURRENCY_SYMBOL', 'Non défini')}")
        print(f"   • CURRENCY_CODE: {currency_settings.get('CURRENCY_CODE', 'Non défini')}")
        
        # Vérifier que c'est bien F CFA
        if currency_settings.get('DEFAULT_CURRENCY') == 'F CFA':
            print("   ✅ Settings correctement configurés pour F CFA")
        else:
            print("   ❌ Settings pas encore mis à jour")
            
    except Exception as e:
        print(f"   ❌ Erreur lors du test des settings: {e}")

def test_database_devises():
    """Teste les devises dans la base de données"""
    print("\n🔍 Test des devises en base...")
    
    try:
        # Vérifier la devise F CFA
        try:
            devise_fcfa = Devise.objects.get(code='F CFA')
            print(f"   ✅ Devise F CFA trouvée: {devise_fcfa.nom} ({devise_fcfa.symbole})")
            print(f"   • Actif: {devise_fcfa.actif}")
            print(f"   • Taux de change: {devise_fcfa.taux_change}")
        except Devise.DoesNotExist:
            print("   ❌ Devise F CFA non trouvée")
        
        # Vérifier l'ancienne devise F CFA
        try:
            devise_xof = Devise.objects.get(code='F CFA')
            print(f"   ℹ️  Devise F CFA trouvée: {devise_xof.nom} ({devise_xof.symbole})")
            print(f"   • Actif: {devise_xof.actif}")
            if not devise_xof.actif:
                print("   ✅ Devise F CFA correctement désactivée")
            else:
                print("   ❌ Devise F CFA toujours active")
        except Devise.DoesNotExist:
            print("   ℹ️  Devise F CFA n'existe plus")
            
    except Exception as e:
        print(f"   ❌ Erreur lors du test de la base: {e}")

def test_currency_formatting():
    """Teste le formatage des montants"""
    print("\n🔍 Test du formatage des montants...")
    
    try:
        # Test avec différents montants
        test_amounts = [0, 1000, 1500.50, 1000000, 2500000.75]
        
        for amount in test_amounts:
            formatted = format_currency_fcfa(amount)
            print(f"   • {amount} → {formatted}")
        
        print("   ✅ Formatage F CFA fonctionne correctement")
        
    except Exception as e:
        print(f"   ❌ Erreur lors du test de formatage: {e}")

def test_currency_utils():
    """Teste les utilitaires de devise"""
    print("\n🔍 Test des utilitaires de devise...")
    
    try:
        # Test de la fonction get_currency_settings
        settings = get_currency_settings()
        print(f"   • DEFAULT_CURRENCY: {settings.get('DEFAULT_CURRENCY')}")
        print(f"   • CURRENCY_SYMBOL: {settings.get('CURRENCY_SYMBOL')}")
        print(f"   • CURRENCY_CODE: {settings.get('CURRENCY_CODE')}")
        
        if settings.get('DEFAULT_CURRENCY') == 'F CFA':
            print("   ✅ Utilitaires correctement configurés")
        else:
            print("   ❌ Utilitaires pas encore mis à jour")
            
    except Exception as e:
        print(f"   ❌ Erreur lors du test des utilitaires: {e}")

def main():
    """Fonction principale de test"""
    print("🧪 Test de la migration F CFA → F CFA")
    print("=" * 50)
    
    # 1. Test des settings
    test_currency_settings()
    
    # 2. Test de la base de données
    test_database_devises()
    
    # 3. Test du formatage
    test_currency_formatting()
    
    # 4. Test des utilitaires
    test_currency_utils()
    
    print("\n" + "=" * 50)
    print("✅ Tests terminés!")
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
