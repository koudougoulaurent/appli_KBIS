"""
Script pour créer un logo PNG simple pour KBIS IMMOBILIER
"""
from PIL import Image, ImageDraw, ImageFont
import os

def create_kbis_logo():
    """Crée un logo PNG simple pour KBIS IMMOBILIER."""
    
    # Dimensions du logo
    width, height = 200, 100
    
    # Créer une nouvelle image avec fond blanc
    image = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(image)
    
    # Couleurs
    couleur_principale = '#2c5aa0'
    couleur_secondaire = '#3d6db0'
    blanc = '#ffffff'
    
    # Dessiner le rectangle principal avec bordure
    draw.rectangle([10, 10, 190, 90], fill=couleur_principale, outline=couleur_secondaire, width=2)
    
    # Essayer d'utiliser une police par défaut
    try:
        font_title = ImageFont.truetype("arial.ttf", 22)
        font_subtitle = ImageFont.truetype("arial.ttf", 12)
    except:
        # Police par défaut si Arial n'est pas disponible
        font_title = ImageFont.load_default()
        font_subtitle = ImageFont.load_default()
    
    # Texte KBIS (centré)
    text_kbis = "KBIS"
    bbox = draw.textbbox((0, 0), text_kbis, font=font_title)
    text_width = bbox[2] - bbox[0]
    x = (width - text_width) // 2
    draw.text((x, 25), text_kbis, fill=blanc, font=font_title)
    
    # Texte IMMOBILIER (centré)
    text_immobilier = "IMMOBILIER"
    bbox = draw.textbbox((0, 0), text_immobilier, font=font_subtitle)
    text_width = bbox[2] - bbox[0]
    x = (width - text_width) // 2
    draw.text((x, 55), text_immobilier, fill=blanc, font=font_subtitle)
    
    # Dessiner une petite maison à gauche (simple)
    # Base de la maison
    draw.rectangle([25, 45, 40, 65], fill=blanc)
    # Toit
    draw.polygon([(30, 35), (35, 30), (40, 35), (25, 35)], fill=blanc)
    # Porte
    draw.rectangle([30, 55, 35, 65], fill=couleur_principale)
    
    # Dessiner une clé à droite (simple)
    # Tête de la clé (cercle)
    draw.ellipse([160, 40, 170, 50], fill=blanc)
    # Corps de la clé
    draw.rectangle([170, 43, 180, 47], fill=blanc)
    # Dents de la clé
    draw.rectangle([180, 41, 182, 43], fill=blanc)
    draw.rectangle([180, 47, 182, 49], fill=blanc)
    
    # Sauvegarder l'image
    logo_path = os.path.join(os.path.dirname(__file__), 'static', 'images', 'logo_kbis.png')
    os.makedirs(os.path.dirname(logo_path), exist_ok=True)
    image.save(logo_path, 'PNG')
    
    print(f"Logo KBIS créé: {logo_path}")
    return logo_path

if __name__ == "__main__":
    create_kbis_logo()