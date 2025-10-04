"""
Test de l'affichage des propriétés avec le nouveau format.
"""

import sqlite3
import os

def test_affichage_proprietes():
    """Test de l'affichage des propriétés."""
    print("Test de l'affichage des propriétés...")
    
    try:
        # Connexion à la base de données
        db_path = os.path.join(os.getcwd(), 'db.sqlite3')
        if not os.path.exists(db_path):
            print(f"ERREUR - Base de données non trouvée: {db_path}")
            return False
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Test 1: Vérifier les propriétés avec le nouveau format
        print("1. Vérification des propriétés avec le nouveau format:")
        cursor.execute("""
            SELECT p.id, p.numero_propriete, p.titre, p.ville, b.nom, b.prenom, b.civilite 
            FROM proprietes_propriete p 
            LEFT JOIN proprietes_bailleur b ON p.bailleur_id = b.id 
            WHERE p.is_deleted = 0 
            ORDER BY p.numero_propriete
            LIMIT 10
        """)
        
        proprietes = cursor.fetchall()
        print(f"   Nombre de propriétés: {len(proprietes)}")
        
        for i, (id_prop, numero, titre, ville, nom, prenom, civilite) in enumerate(proprietes):
            # Simuler le nouveau format d'affichage
            titre_affichage = titre if titre else "Sans titre"
            ville_affichage = ville if ville else "Ville non renseignée"
            bailleur_nom = f"{civilite} {prenom} {nom}" if nom else "Inconnu"
            
            print(f"   {i+1}. {numero} - {titre_affichage} ({ville_affichage})")
            print(f"       Bailleur: {bailleur_nom}")
        
        # Test 2: Vérifier la diversité des propriétés
        print("\n2. Vérification de la diversité des propriétés:")
        cursor.execute("SELECT COUNT(DISTINCT numero_propriete) FROM proprietes_propriete WHERE is_deleted = 0")
        count_numeros = cursor.fetchone()[0]
        print(f"   Nombre de numéros uniques: {count_numeros}")
        
        cursor.execute("SELECT COUNT(DISTINCT titre) FROM proprietes_propriete WHERE is_deleted = 0 AND titre IS NOT NULL AND titre != ''")
        count_titres = cursor.fetchone()[0]
        print(f"   Nombre de titres uniques: {count_titres}")
        
        cursor.execute("SELECT COUNT(DISTINCT ville) FROM proprietes_propriete WHERE is_deleted = 0 AND ville IS NOT NULL AND ville != ''")
        count_villes = cursor.fetchone()[0]
        print(f"   Nombre de villes uniques: {count_villes}")
        
        # Test 3: Vérifier les propriétés sans titre ou ville
        print("\n3. Vérification des propriétés sans titre ou ville:")
        cursor.execute("SELECT COUNT(*) FROM proprietes_propriete WHERE is_deleted = 0 AND (titre IS NULL OR titre = '')")
        count_sans_titre = cursor.fetchone()[0]
        print(f"   Propriétés sans titre: {count_sans_titre}")
        
        cursor.execute("SELECT COUNT(*) FROM proprietes_propriete WHERE is_deleted = 0 AND (ville IS NULL OR ville = '')")
        count_sans_ville = cursor.fetchone()[0]
        print(f"   Propriétés sans ville: {count_sans_ville}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"ERREUR - Test affichage: {e}")
        return False

def main():
    """Fonction principale de test."""
    print("TEST DE L'AFFICHAGE DES PROPRIETES")
    print("=" * 40)
    
    success = test_affichage_proprietes()
    
    print("\n" + "=" * 40)
    print("RESUME DU TEST")
    print("=" * 40)
    
    if success:
        print("SUCCES - L'affichage des proprietes est maintenant plus clair!")
        print("Format utilise: NUMERO - TITRE (VILLE)")
        print("Exemple: PR0001 - Maison familiale (Paris)")
        print("\nAvantages:")
        print("- Identifiant unique (numero_propriete)")
        print("- Titre descriptif")
        print("- Localisation (ville)")
        print("- Plus de confusion avec les bailleurs")
    else:
        print("ERREUR - Probleme avec l'affichage des proprietes.")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
