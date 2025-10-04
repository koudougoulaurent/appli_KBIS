"""
Test simple de vérification des propriétés.
"""

import sqlite3
import os

def test_proprietes_database():
    """Test direct de la base de données."""
    print("Test direct de la base de données...")
    
    try:
        # Connexion à la base de données
        db_path = os.path.join(os.getcwd(), 'db.sqlite3')
        if not os.path.exists(db_path):
            print(f"ERREUR - Base de données non trouvée: {db_path}")
            return False
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Test 1: Vérifier les propriétés
        print("1. Vérification des propriétés:")
        cursor.execute("SELECT COUNT(*) FROM proprietes_propriete WHERE is_deleted = 0")
        count_proprietes = cursor.fetchone()[0]
        print(f"   Nombre de propriétés: {count_proprietes}")
        
        if count_proprietes > 0:
            cursor.execute("""
                SELECT p.id, p.adresse, b.nom, b.prenom, b.civilite 
                FROM proprietes_propriete p 
                LEFT JOIN proprietes_bailleur b ON p.bailleur_id = b.id 
                WHERE p.is_deleted = 0 
                LIMIT 5
            """)
            
            proprietes = cursor.fetchall()
            for i, (id_prop, adresse, nom, prenom, civilite) in enumerate(proprietes):
                bailleur_nom = f"{civilite} {prenom} {nom}" if nom else "Aucun bailleur"
                print(f"   {i+1}. ID:{id_prop} - {adresse} - {bailleur_nom}")
        
        # Test 2: Vérifier les bailleurs
        print("\n2. Vérification des bailleurs:")
        cursor.execute("SELECT COUNT(*) FROM proprietes_bailleur")
        count_bailleurs = cursor.fetchone()[0]
        print(f"   Nombre de bailleurs: {count_bailleurs}")
        
        if count_bailleurs > 0:
            cursor.execute("SELECT nom, prenom, civilite FROM proprietes_bailleur LIMIT 5")
            bailleurs = cursor.fetchall()
            for i, (nom, prenom, civilite) in enumerate(bailleurs):
                print(f"   {i+1}. {civilite} {prenom} {nom}")
        
        # Test 3: Vérifier la relation propriété-bailleur
        print("\n3. Vérification de la relation propriété-bailleur:")
        cursor.execute("""
            SELECT COUNT(*) FROM proprietes_propriete p 
            WHERE p.is_deleted = 0 AND p.bailleur_id IS NOT NULL
        """)
        count_avec_bailleur = cursor.fetchone()[0]
        print(f"   Propriétés avec bailleur: {count_avec_bailleur}")
        
        cursor.execute("""
            SELECT COUNT(*) FROM proprietes_propriete p 
            WHERE p.is_deleted = 0 AND p.bailleur_id IS NULL
        """)
        count_sans_bailleur = cursor.fetchone()[0]
        print(f"   Propriétés sans bailleur: {count_sans_bailleur}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"ERREUR - Test base de données: {e}")
        return False

def main():
    """Fonction principale de test."""
    print("TEST SIMPLE DE VERIFICATION DES PROPRIETES")
    print("=" * 50)
    
    success = test_proprietes_database()
    
    print("\n" + "=" * 50)
    print("RESUME DU TEST")
    print("=" * 50)
    
    if success:
        print("SUCCES - Les proprietes sont disponibles dans la base de données!")
        print("Le probleme peut venir de:")
        print("1. La requete dans la vue")
        print("2. Le template")
        print("3. La configuration Django")
    else:
        print("ERREUR - Probleme avec la base de données.")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
