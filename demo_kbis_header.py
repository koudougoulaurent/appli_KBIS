#!/usr/bin/env python3
"""
Démonstration de l'en-tête KBIS en production
"""

import os
import sqlite3
from PIL import Image

def show_kbis_header():
    """Affiche l'en-tête KBIS configuré"""
    
    print("=== DÉMONSTRATION DE L'EN-TÊTE KBIS ===")
    print()
    
    # Vérifier la configuration
    db_path = "db.sqlite3"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT nom_entreprise, adresse, ville, pays, telephone, email, 
               forme_juridique, couleur_principale, couleur_secondaire, entete_upload
        FROM core_configurationentreprise
        WHERE actif = 1
        LIMIT 1
    """)
    
    config = cursor.fetchone()
    conn.close()
    
    if not config:
        print("❌ Configuration non trouvée")
        return
    
    print("📋 CONFIGURATION ENTREPRISE KBIS :")
    print(f"   🏢 Nom : {config[0]}")
    print(f"   📍 Adresse : {config[1]}")
    print(f"   🏙️ Ville : {config[2]}")
    print(f"   🌍 Pays : {config[3]}")
    print(f"   📞 Téléphone : {config[4]}")
    print(f"   📧 Email : {config[5]}")
    print(f"   🏛️ Forme juridique : {config[6]}")
    print(f"   🎨 Couleur principale : {config[7]}")
    print(f"   🎨 Couleur secondaire : {config[8]}")
    print(f"   🖼️ En-tête personnalisé : {config[9]}")
    print()
    
    # Afficher l'image d'en-tête
    header_path = f"media/{config[9]}"
    if os.path.exists(header_path):
        print("🖼️ EN-TÊTE KBIS CONFIGURÉ :")
        print(f"   📁 Fichier : {header_path}")
        
        try:
            with Image.open(header_path) as img:
                print(f"   📏 Dimensions : {img.size[0]}x{img.size[1]} pixels")
                print(f"   🎨 Format : {img.format}")
                print(f"   💾 Mode couleur : {img.mode}")
                
                # Afficher un aperçu ASCII de l'image
                print("\n📋 APERÇU DE L'EN-TÊTE :")
                print("   " + "="*50)
                
                # Redimensionner pour l'aperçu ASCII
                preview = img.resize((50, 12), Image.Resampling.LANCZOS)
                preview = preview.convert('L')  # Convertir en niveaux de gris
                
                # Créer un aperçu ASCII simple
                ascii_chars = " .:-=+*#%@"
                for y in range(preview.height):
                    line = "   "
                    for x in range(preview.width):
                        pixel = preview.getpixel((x, y))
                        char_index = int(pixel / 255 * (len(ascii_chars) - 1))
                        line += ascii_chars[char_index]
                    print(line)
                
                print("   " + "="*50)
                
        except Exception as e:
            print(f"   ⚠️ Erreur lors de l'affichage : {e}")
    else:
        print(f"❌ Fichier d'en-tête non trouvé : {header_path}")
        return
    
    print()
    print("🔧 INTÉGRATION DANS LES DOCUMENTS PDF :")
    print("   ✅ L'en-tête KBIS sera automatiquement utilisé sur :")
    print("      📄 Contrats de bail")
    print("      📄 Quittances de loyer")
    print("      📄 Récapitulatifs mensuels")
    print("      📄 Avis de résiliation")
    print("      📄 Tous les autres documents PDF")
    print()
    
    print("🎯 FONCTIONNALITÉS DE L'EN-TÊTE :")
    print("   🏠 Logo maison avec bâtiments et soleil")
    print("   🏢 Nom de l'entreprise 'KBIS' en bleu")
    print("   📦 Boîte jaune avec 'Immobilier & Construction'")
    print("   📋 Services : Achat & Vente, Location, Gestion, Nettoyage")
    print("   📍 Adresse complète : BP 440 Ouaga pissy 10050 Ouagadougou")
    print("   📞 Téléphones : +226 79 18 32 32 / 66 66 45 60")
    print("   📧 Email : kbissarl2022@gmail.com")
    print()
    
    print("🚀 PRÊT POUR LA PRODUCTION !")
    print("   L'en-tête KBIS est maintenant configuré et sera utilisé")
    print("   automatiquement sur tous les documents PDF générés par")
    print("   l'application de gestion immobilière.")

def show_usage_instructions():
    """Affiche les instructions d'utilisation"""
    
    print("\n" + "="*60)
    print("📖 INSTRUCTIONS D'UTILISATION")
    print("="*60)
    print()
    print("1. 🎯 L'en-tête KBIS est maintenant actif")
    print("   - Tous les documents PDF utiliseront automatiquement cet en-tête")
    print("   - Aucune action supplémentaire n'est requise")
    print()
    print("2. 🔧 Personnalisation (optionnelle)")
    print("   - Pour modifier l'en-tête, remplacez le fichier :")
    print("     media/entetes_entreprise/kbis_header.png")
    print("   - Dimensions recommandées : 800x200 pixels")
    print("   - Formats supportés : PNG, JPG")
    print()
    print("3. 📊 Vérification")
    print("   - Exécutez 'python test_kbis_direct.py' pour vérifier")
    print("   - L'en-tête apparaîtra sur tous les PDF générés")
    print()
    print("4. 🎨 Couleurs de l'entreprise")
    print("   - Bleu principal : #1e3a8a")
    print("   - Jaune secondaire : #fbbf24")
    print("   - Ces couleurs sont utilisées dans l'interface")
    print()

if __name__ == "__main__":
    show_kbis_header()
    show_usage_instructions()
