#!/usr/bin/env python
"""
Script pour corriger directement la propriété avec ID 24 qui a un bailleur invalide.
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from django.db import connection

def corriger_propriete_24():
    """Corrige la propriété avec ID 24"""
    print("🔧 Correction de la propriété ID 24...")
    
    with connection.cursor() as cursor:
        # Vérifier d'abord l'état actuel
        cursor.execute("SELECT id, adresse, bailleur_id FROM proprietes_propriete WHERE id = 24")
        result = cursor.fetchone()
        
        if result:
            print(f"Propriété trouvée: ID {result[0]}, Adresse: {result[1]}, Bailleur ID: {result[2]}")
            
            # Vérifier si le bailleur existe
            cursor.execute("SELECT id FROM proprietes_bailleur WHERE id = %s", [result[2]])
            bailleur_exists = cursor.fetchone()
            
            if not bailleur_exists:
                print("Bailleur invalide détecté. Suppression de la propriété...")
                
                # Supprimer d'abord les objets dépendants
                print("Suppression des contrats...")
                cursor.execute("DELETE FROM contrats_contrat WHERE propriete_id = 24")
                
                print("Suppression des paiements...")
                cursor.execute("DELETE FROM paiements_paiement WHERE contrat_id IN (SELECT id FROM contrats_contrat WHERE propriete_id = 24)")
                
                print("Suppression des reçus...")
                cursor.execute("DELETE FROM paiements_recu WHERE paiement_id IN (SELECT id FROM paiements_paiement WHERE contrat_id IN (SELECT id FROM contrats_contrat WHERE propriete_id = 24))")
                
                print("Suppression des quittances...")
                cursor.execute("DELETE FROM contrats_quittance WHERE contrat_id IN (SELECT id FROM contrats_contrat WHERE propriete_id = 24)")
                
                print("Suppression des charges déductibles...")
                cursor.execute("DELETE FROM paiements_chargedeductible WHERE contrat_id IN (SELECT id FROM contrats_contrat WHERE propriete_id = 24)")
                
                # Maintenant supprimer la propriété
                print("Suppression de la propriété...")
                cursor.execute("DELETE FROM proprietes_propriete WHERE id = 24")
                
                print("✅ Propriété ID 24 supprimée avec succès")
            else:
                print("Bailleur valide, aucune action nécessaire")
        else:
            print("Propriété ID 24 non trouvée")
    
    # Vérifier l'état final
    with connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM proprietes_propriete")
        total_proprietes = cursor.fetchone()[0]
        print(f"Total des propriétés après correction: {total_proprietes}")

if __name__ == "__main__":
    corriger_propriete_24()
