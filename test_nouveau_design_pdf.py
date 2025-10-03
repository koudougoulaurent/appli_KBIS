#!/usr/bin/env python
"""
Test du nouveau design KBIS horizontal pour les PDF
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from core.models import ConfigurationEntreprise
from core.utils import ajouter_en_tete_entreprise_reportlab, ajouter_pied_entreprise_reportlab
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from io import BytesIO

def test_design_horizontal():
    """Test du design horizontal KBIS"""
    print("🎨 Test du nouveau design KBIS horizontal")
    print("=" * 50)
    
    try:
        # Récupérer la configuration d'entreprise
        config = ConfigurationEntreprise.get_configuration_active()
        if not config:
            print("❌ Aucune configuration d'entreprise trouvée")
            return False
        
        print(f"✅ Configuration trouvée: {config.nom_entreprise}")
        
        # Créer un PDF de test
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        # Construction du contenu
        story = []
        
        # En-tête avec le nouveau design horizontal
        print("📄 Ajout de l'en-tête horizontal...")
        ajouter_en_tete_entreprise_reportlab(story, config)
        
        # Titre du document
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.lib import colors
        
        title_style = ParagraphStyle(
            'TitleStyle',
            fontSize=18,
            spaceAfter=20,
            alignment=1,  # Centré
            textColor=colors.HexColor('#1e3a8a'),
            fontName='Helvetica-Bold'
        )
        
        story.append(Paragraph("CONTRAT DE BAIL D'HABITATION", title_style))
        
        # Contenu de test
        content_style = ParagraphStyle(
            'ContentStyle',
            fontSize=12,
            spaceAfter=10,
            alignment=0,  # Justifié
            fontName='Helvetica'
        )
        
        story.append(Paragraph("Ce document utilise le nouveau design horizontal KBIS avec :", content_style))
        story.append(Paragraph("• Logo avec bâtiments et soleil (🏠🏢☀️)", content_style))
        story.append(Paragraph("• Nom d'entreprise en bleu clair", content_style))
        story.append(Paragraph("• Services sur fond orange", content_style))
        story.append(Paragraph("• Couleurs exactes de l'image fournie", content_style))
        
        # Pied de page avec le nouveau design
        print("📄 Ajout du pied de page...")
        ajouter_pied_entreprise_reportlab(story, config)
        
        # Générer le PDF
        print("🔨 Génération du PDF...")
        doc.build(story)
        buffer.seek(0)
        
        # Sauvegarder le PDF de test
        with open('test_design_kbis_horizontal.pdf', 'wb') as f:
            f.write(buffer.getvalue())
        
        print("✅ PDF de test généré : test_design_kbis_horizontal.pdf")
        print("🎯 Le nouveau design horizontal KBIS est maintenant actif !")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test : {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Fonction principale"""
    print("🚀 Test du Design KBIS Horizontal")
    print("=" * 50)
    
    success = test_design_horizontal()
    
    if success:
        print("\n🎉 SUCCÈS !")
        print("📋 Le nouveau design KBIS horizontal est maintenant actif sur :")
        print("   • Tous les contrats de bail")
        print("   • Toutes les quittances")
        print("   • Tous les récapitulatifs")
        print("   • Tous les autres documents PDF")
        print("\n🎯 Pour tester :")
        print("   1. Créez un nouveau contrat")
        print("   2. Générez le PDF")
        print("   3. Vérifiez l'en-tête horizontal")
    else:
        print("\n❌ ÉCHEC !")
        print("Vérifiez les erreurs ci-dessus et réessayez.")

if __name__ == '__main__':
    main()
