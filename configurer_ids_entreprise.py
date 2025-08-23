#!/usr/bin/env python
"""
Configuration des identifiants uniques pour l'entreprise
Personnalisation des formats selon les besoins professionnels
"""

import os
import sys
import django
from datetime import datetime

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from core.id_generator import IDGenerator, IDConfiguration

def afficher_configuration_actuelle():
    """Affiche la configuration actuelle des IDs"""
    
    print("🔢 CONFIGURATION ACTUELLE DES IDENTIFIANTS")
    print("=" * 60)
    
    print("\n📋 Formats actuels :")
    for entity_type, config in IDGenerator.ID_FORMATS.items():
        print(f"   {entity_type.upper()}: {config['format']}")
        print(f"     Préfixe: {config['prefix']}")
        print(f"     Description: {config['description']}")
        print()
    
    print("🏢 Préfixe entreprise actuel:", IDConfiguration.get_company_prefix())
    
    print("\n📅 Politique de réinitialisation :")
    reset_policy = IDConfiguration.get_sequence_reset_policy()
    for entity, policy in reset_policy.items():
        print(f"   {entity}: {policy}")

def proposer_formats_alternatifs():
    """Propose des formats alternatifs pour l'entreprise"""
    
    print("\n💡 FORMATS ALTERNATIFS PROPOSÉS")
    print("=" * 60)
    
    formats_alternatifs = {
        'bailleur': {
            'format_simple': 'BLR-{year}-{sequence:04d}',
            'format_entreprise': 'GESTIMMOB-BLR-{year}-{sequence:04d}',
            'format_region': 'BLR-{region}-{year}-{sequence:04d}',
            'description': 'Bailleur avec options de formatage'
        },
        'locataire': {
            'format_simple': 'LOC-{year}-{sequence:04d}',
            'format_entreprise': 'GESTIMMOB-LOC-{year}-{sequence:04d}',
            'format_region': 'LOC-{region}-{year}-{sequence:04d}',
            'description': 'Locataire avec options de formatage'
        },
        'propriete': {
            'format_simple': 'PRP-{year}-{sequence:04d}',
            'format_entreprise': 'GESTIMMOB-PRP-{year}-{sequence:04d}',
            'format_region': 'PRP-{region}-{year}-{sequence:04d}',
            'description': 'Propriété avec options de formatage'
        },
        'contrat': {
            'format_simple': 'CTR-{year}-{sequence:04d}',
            'format_entreprise': 'GESTIMMOB-CTR-{year}-{sequence:04d}',
            'format_region': 'CTR-{region}-{year}-{sequence:04d}',
            'description': 'Contrat avec options de formatage'
        },
        'paiement': {
            'format_simple': 'PAY-{yearmonth}-{sequence:04d}',
            'format_entreprise': 'GESTIMMOB-PAY-{yearmonth}-{sequence:04d}',
            'format_detaille': 'PAY-{year}-{month:02d}-{day:02d}-{sequence:04d}',
            'description': 'Paiement avec options de formatage'
        }
    }
    
    for entity, formats in formats_alternatifs.items():
        print(f"\n{entity.upper()}:")
        for format_name, format_value in formats.items():
            if format_name != 'description':
                print(f"   {format_name}: {format_value}")
        print(f"   Description: {formats['description']}")

def configurer_prefixe_entreprise():
    """Configure le préfixe de l'entreprise"""
    
    print("\n🏢 CONFIGURATION DU PRÉFIXE ENTREPRISE")
    print("=" * 60)
    
    print("Le préfixe de l'entreprise est actuellement configuré dans core/id_generator.py")
    print("Pour le modifier, éditez la classe IDConfiguration:")
    print()
    print("class IDConfiguration:")
    print("    @classmethod")
    print("    def get_company_prefix(cls):")
    print("        return \"VOTRE_PREFIXE\"  # Remplacez par votre préfixe")
    print()
    
    # Afficher le préfixe actuel
    current_prefix = IDConfiguration.get_company_prefix()
    print(f"Préfixe actuel: {current_prefix}")
    
    # Proposer des alternatives
    print("\n💡 Préfixes suggérés :")
    prefixes_suggérés = [
        "GESTIMMOB",      # Gestion Immobilière
        "IMMOBPRO",       # Immobilier Professionnel
        "PROPIMMO",       # Propriété Immobilière
        "GESTPROP",       # Gestion Propriété
        "IMMOGEST",       # Immobilier Gestion
        "PROPGEST",       # Propriété Gestion
        "VOTRE_NOM",      # Nom de votre entreprise
        "VOTRE_VILLE",    # Ville de votre entreprise
    ]
    
    for i, prefix in enumerate(prefixes_suggérés, 1):
        print(f"   {i}. {prefix}")
    
    print("\n⚠️  Pour appliquer un nouveau préfixe :")
    print("   1. Modifiez core/id_generator.py")
    print("   2. Redémarrez l'application")
    print("   3. Régénérez les IDs existants si nécessaire")

def configurer_formats_personnalises():
    """Configure des formats personnalisés pour l'entreprise"""
    
    print("\n⚙️ CONFIGURATION DES FORMATS PERSONNALISÉS")
    print("=" * 60)
    
    print("Pour personnaliser les formats d'IDs, modifiez la classe IDGenerator")
    print("dans core/id_generator.py :")
    print()
    print("class IDGenerator:")
    print("    ID_FORMATS = {")
    print("        'bailleur': {")
    print("            'prefix': 'BLR',")
    print("            'format': 'VOTRE_FORMAT',  # Votre format personnalisé")
    print("            'description': 'Description personnalisée',")
    print("            'sequence_field': 'numero_bailleur',")
    print("            'model': 'proprietes.Bailleur'")
    print("        },")
    print("        # ... autres entités")
    print("    }")
    print()
    
    print("💡 Exemples de formats personnalisés :")
    print()
    print("1. Format avec région :")
    print("   'format': 'BLR-{region}-{year}-{sequence:04d}'")
    print()
    print("2. Format avec département :")
    print("   'format': 'BLR-{dept:02d}-{year}-{sequence:04d}'")
    print()
    print("3. Format avec mois :")
    print("   'format': 'BLR-{year}-{month:02d}-{sequence:04d}'")
    print()
    print("4. Format avec préfixe entreprise :")
    print("   'format': '{company}-BLR-{year}-{sequence:04d}'")
    print()
    print("⚠️  Variables disponibles :")
    print("   - {year}: Année courante")
    print("   - {month}: Mois courant (01-12)")
    print("   - {day}: Jour courant (01-31)")
    print("   - {sequence}: Numéro de séquence")
    print("   - {company}: Préfixe de l'entreprise")
    print("   - {region}: Région (à implémenter)")
    print("   - {dept}: Département (à implémenter)")

def configurer_politique_sequences():
    """Configure la politique de réinitialisation des séquences"""
    
    print("\n📅 CONFIGURATION DE LA POLITIQUE DES SÉQUENCES")
    print("=" * 60)
    
    print("La politique de réinitialisation des séquences définit quand les")
    print("numéros de séquence sont remis à zéro :")
    print()
    
    current_policy = IDConfiguration.get_sequence_reset_policy()
    print("Politique actuelle :")
    for entity, policy in current_policy.items():
        print(f"   {entity}: {policy}")
    
    print("\n💡 Options disponibles :")
    print("   - 'yearly': Réinitialisation annuelle (recommandé pour la plupart)")
    print("   - 'monthly': Réinitialisation mensuelle (pour paiements, reçus)")
    print("   - 'daily': Réinitialisation quotidienne (pour reçus)")
    print("   - 'never': Jamais de réinitialisation")
    print("   - 'custom': Réinitialisation personnalisée")
    
    print("\n⚠️  Pour modifier la politique :")
    print("   1. Modifiez la méthode get_sequence_reset_policy()")
    print("   2. Dans core/id_generator.py")
    print("   3. Redémarrez l'application")

def afficher_instructions_implementation():
    """Affiche les instructions pour implémenter les modifications"""
    
    print("\n📋 INSTRUCTIONS D'IMPLÉMENTATION")
    print("=" * 60)
    
    print("""
🔧 POUR MODIFIER LA CONFIGURATION DES IDs :

1. 📁 Éditez le fichier core/id_generator.py :
   - Modifiez IDGenerator.ID_FORMATS pour changer les formats
   - Modifiez IDConfiguration.get_company_prefix() pour le préfixe
   - Modifiez IDConfiguration.get_sequence_reset_policy() pour les séquences

2. 🚀 Redémarrez l'application Django

3. 🔄 Régénérez les IDs existants si nécessaire :
   python preparer_production.py

4. ✅ Testez les nouveaux formats

⚠️  ATTENTION :
   - Sauvegardez votre base de données avant modification
   - Testez en environnement de développement d'abord
   - Les modifications affectent tous les nouveaux enregistrements
   - Les anciens IDs ne sont pas modifiés automatiquement

💡 RECOMMANDATIONS :
   - Gardez les formats simples et lisibles
   - Utilisez des préfixes courts (3-4 caractères)
   - Évitez les caractères spéciaux dans les formats
   - Documentez vos choix de formatage
   - Testez avec vos données réelles
""")

def main():
    """Fonction principale"""
    
    print("🏢 CONFIGURATION DES IDENTIFIANTS ENTREPRISE")
    print("=" * 80)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    try:
        # 1. Afficher la configuration actuelle
        afficher_configuration_actuelle()
        
        # 2. Proposer des formats alternatifs
        proposer_formats_alternatifs()
        
        # 3. Configuration du préfixe entreprise
        configurer_prefixe_entreprise()
        
        # 4. Configuration des formats personnalisés
        configurer_formats_personnalises()
        
        # 5. Configuration de la politique des séquences
        configurer_politique_sequences()
        
        # 6. Instructions d'implémentation
        afficher_instructions_implementation()
        
        print("\n🎯 CONFIGURATION TERMINÉE !")
        print("Vous pouvez maintenant personnaliser les formats selon vos besoins.")
        
    except Exception as e:
        print(f"\n❌ ERREUR LORS DE LA CONFIGURATION: {e}")
        print("Veuillez vérifier les logs et réessayer.")
        return False
    
    return True

if __name__ == "__main__":
    main()
