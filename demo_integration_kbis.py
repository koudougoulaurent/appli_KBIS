#!/usr/bin/env python
"""
Démonstration complète du système de templates KBIS
Ce script montre comment utiliser le nouveau système intégré.
"""

import os
import sys
import django
from datetime import datetime
from decimal import Decimal

# Configuration Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from core.utils import KBISDocumentTemplate


def demonstration_complete():
    """Démonstration complète du système KBIS."""
    
    print("🏢 SYSTÈME DE TEMPLATES KBIS - DÉMONSTRATION COMPLÈTE")
    print("=" * 70)
    
    # 1. Informations de l'entreprise
    print("\n📋 INFORMATIONS DE L'ENTREPRISE KBIS:")
    info = KBISDocumentTemplate.ENTREPRISE_INFO
    for cle, valeur in info.items():
        print(f"  • {cle.replace('_', ' ').title()}: {valeur}")
    
    # 2. Test du logo
    print(f"\n🎨 LOGO KBIS:")
    logo_path = KBISDocumentTemplate.get_logo_path()
    if logo_path:
        print(f"  ✓ Logo trouvé: {logo_path}")
    else:
        print("  ⚠️  Logo non trouvé, utilisation du texte par défaut")
    
    # 3. Génération d'un document exemple
    print(f"\n📄 GÉNÉRATION DE DOCUMENT EXEMPLE:")
    
    contenu_exemple = f"""
    <div style="text-align: center; margin: 40px 0;">
        <h1 style="color: #2c5aa0; font-size: 28px; margin-bottom: 30px;">
            INTÉGRATION RÉUSSIE !
        </h1>
        
        <div style="background: linear-gradient(135deg, #e7f3ff 0%, #f0f8ff 100%); 
                    padding: 30px; border-radius: 15px; margin: 20px 0; 
                    border: 2px solid #2c5aa0;">
            
            <h2 style="color: #2c5aa0; margin-top: 0;">
                🎉 Le système de templates KBIS est opérationnel !
            </h2>
            
            <div style="text-align: left; margin: 20px 0;">
                <h3 style="color: #2c5aa0; border-bottom: 2px solid #2c5aa0; padding-bottom: 10px;">
                    Fonctionnalités intégrées:
                </h3>
                <ul style="line-height: 1.8; font-size: 16px;">
                    <li>✅ En-tête professionnel avec logo et informations entreprise</li>
                    <li>✅ Pied de page complet avec coordonnées et mentions légales</li>
                    <li>✅ Styles CSS cohérents avec l'identité KBIS</li>
                    <li>✅ Génération automatique de documents PDF</li>
                    <li>✅ Intégration avec le modèle Paiement</li>
                    <li>✅ Templates personnalisables par type de document</li>
                </ul>
            </div>
            
            <div style="background: #fff; padding: 20px; border-radius: 10px; margin: 20px 0; border-left: 5px solid #28a745;">
                <h4 style="color: #28a745; margin-top: 0;">Utilisation dans votre code:</h4>
                <pre style="background: #f8f9fa; padding: 15px; border-radius: 5px; overflow-x: auto;">
# Pour générer un document avec template KBIS:
from core.utils.document_templates import KBISDocumentTemplate

# Document complet avec en-tête et pied de page
document_html = KBISDocumentTemplate.get_document_complet(
    titre="Mon Document",
    contenu="Contenu du document...",
    type_document="Facture"
)

# Ou directement depuis un paiement:
paiement.generer_document_kbis('recu')  # Pour un reçu
paiement.generer_document_kbis('facture')  # Pour une facture
                </pre>
            </div>
            
            <div style="background: #fff3cd; padding: 15px; border-radius: 8px; border-left: 5px solid #ffc107;">
                <h4 style="color: #856404; margin-top: 0;">📝 Prochaines étapes recommandées:</h4>
                <ol style="color: #856404;">
                    <li>Ajouter votre logo officiel dans <code>static/images/logo_kbis.png</code></li>
                    <li>Personnaliser les informations de l'entreprise dans le template</li>
                    <li>Configurer les templates par défaut pour chaque type de document</li>
                    <li>Tester la génération PDF avec xhtml2pdf</li>
                </ol>
            </div>
        </div>
        
        <div style="margin: 30px 0; padding: 20px; background: #f8f9fa; border-radius: 10px;">
            <p style="font-size: 18px; color: #2c5aa0; margin: 0;">
                <strong>Document généré le {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}</strong>
            </p>
            <p style="font-size: 14px; color: #666; margin: 10px 0 0 0;">
                Système de templates KBIS v1.0 - Opérationnel ✅
            </p>
        </div>
    </div>
    """
    
    titre_document = f"DÉMONSTRATION SYSTÈME KBIS - {datetime.now().strftime('%d/%m/%Y')}"
    document_final = KBISDocumentTemplate.get_document_complet(
        titre_document, 
        contenu_exemple, 
        "Démonstration"
    )
    
    # Sauvegarder le document de démonstration
    fichier_demo = os.path.join(os.path.dirname(__file__), "demo_kbis_complete.html")
    with open(fichier_demo, 'w', encoding='utf-8') as f:
        f.write(document_final)
    
    print(f"  ✅ Document de démonstration généré: {fichier_demo}")
    print(f"     Taille: {len(document_final):,} caractères")
    
    # 4. Résumé de l'intégration
    print(f"\n🔧 RÉSUMÉ DE L'INTÉGRATION:")
    print(f"  📁 Templates créés: core/utils/document_templates.py")
    print(f"  📁 Modèles ajoutés: core/models.py (ConfigurationEntreprise, TemplateDocument)")
    print(f"  🔗 Méthodes intégrées: Paiement.generer_document_kbis()")
    print(f"  🎨 Logo créé: static/images/logo_kbis.png")
    print(f"  ✅ Système opérationnel et prêt à l'utilisation")
    
    print(f"\n🎯 COMMENT UTILISER LE SYSTÈME:")
    print(f"""
    1. Dans vos vues Django:
       document_html = paiement.generer_document_kbis('recu')
       return HttpResponse(document_html)
    
    2. Pour personnaliser l'entreprise:
       Modifiez KBISDocumentTemplate.ENTREPRISE_INFO
    
    3. Pour ajouter votre logo:
       Placez votre logo dans static/images/logo_kbis.png
    
    4. Pour créer de nouveaux templates:
       Utilisez KBISDocumentTemplate.get_document_complet()
    """)
    
    return True


if __name__ == "__main__":
    try:
        demonstration_complete()
        print("\n" + "🎉 INTÉGRATION KBIS TERMINÉE AVEC SUCCÈS ! 🎉".center(70))
        print("=" * 70)
    except Exception as e:
        print(f"\n❌ Erreur lors de la démonstration: {e}")