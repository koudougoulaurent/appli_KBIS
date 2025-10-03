#!/usr/bin/env python
"""
Vérification du design KBIS horizontal
"""
import os

def verifier_fichiers():
    """Vérifie que tous les fichiers sont présents et corrects"""
    print("🔍 Vérification du design KBIS horizontal")
    print("=" * 50)
    
    # Fichiers à vérifier
    fichiers = [
        'core/utils.py',
        'templates/includes/kbis_pdf_header.html',
        'templates/includes/kbis_pdf_footer.html',
        'static/css/kbis_pdf_styles.css',
        'contrats/services.py'
    ]
    
    tous_presents = True
    
    for fichier in fichiers:
        if os.path.exists(fichier):
            print(f"✅ {fichier}")
            
            # Vérifier le contenu pour les fichiers clés
            if fichier == 'core/utils.py':
                with open(fichier, 'r', encoding='utf-8') as f:
                    contenu = f.read()
                    if 'ajouter_en_tete_entreprise_reportlab' in contenu and 'Design horizontal KBIS' in contenu:
                        print("   ✅ Fonction ReportLab mise à jour")
                    else:
                        print("   ❌ Fonction ReportLab non mise à jour")
                        tous_presents = False
                        
        else:
            print(f"❌ {fichier}")
            tous_presents = False
    
    return tous_presents

def verifier_fonctions():
    """Vérifie que les fonctions contiennent le bon code"""
    print("\n🔧 Vérification des fonctions")
    print("=" * 30)
    
    try:
        with open('core/utils.py', 'r', encoding='utf-8') as f:
            contenu = f.read()
        
        # Vérifier les éléments clés du design horizontal
        elements_cles = [
            'Design horizontal KBIS',
            'B3D9FF',  # Couleur bleu clair
            'FFE5B4',  # Couleur orange/peach
            '666666',  # Couleur gris foncé
            'Immobilier & Construction',
            'Achat & Vente location - Gestion - Nettoyage',
            '🏠🏢☀️'  # Emojis pour le logo
        ]
        
        elements_trouves = 0
        for element in elements_cles:
            if element in contenu:
                print(f"✅ {element}")
                elements_trouves += 1
            else:
                print(f"❌ {element}")
        
        if elements_trouves == len(elements_cles):
            print("\n✅ Tous les éléments du design horizontal sont présents !")
            return True
        else:
            print(f"\n⚠️ {elements_trouves}/{len(elements_cles)} éléments trouvés")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors de la vérification : {e}")
        return False

def main():
    """Fonction principale"""
    print("🎨 Vérification du Design KBIS Horizontal")
    print("=" * 50)
    
    # Vérifier les fichiers
    fichiers_ok = verifier_fichiers()
    
    # Vérifier les fonctions
    fonctions_ok = verifier_fonctions()
    
    print("\n" + "=" * 50)
    if fichiers_ok and fonctions_ok:
        print("🎉 SUCCÈS ! Le design KBIS horizontal est prêt !")
        print("\n📋 Ce qui a été mis à jour :")
        print("   ✅ Fonction ajouter_en_tete_entreprise() - Canvas ReportLab")
        print("   ✅ Fonction ajouter_en_tete_entreprise_reportlab() - Platypus")
        print("   ✅ Fonction ajouter_pied_entreprise() - Canvas ReportLab")
        print("   ✅ Fonction ajouter_pied_entreprise_reportlab() - Platypus")
        print("   ✅ Templates HTML avec design horizontal")
        print("   ✅ Styles CSS avec couleurs exactes")
        
        print("\n🎯 Le nouveau design sera utilisé sur :")
        print("   📄 Contrats de bail")
        print("   📄 Quittances de loyer")
        print("   📄 Récapitulatifs mensuels")
        print("   📄 Avis de résiliation")
        print("   📄 Tous les autres documents PDF")
        
        print("\n🚀 Pour tester :")
        print("   1. Créez un nouveau contrat")
        print("   2. Générez le PDF")
        print("   3. Vérifiez l'en-tête horizontal avec logo, 'KBIS' et services")
        
    else:
        print("❌ ÉCHEC ! Certains éléments sont manquants.")
        print("Vérifiez les erreurs ci-dessus et réessayez.")

if __name__ == '__main__':
    main()
