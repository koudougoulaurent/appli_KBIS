#!/usr/bin/env python
"""
Script simple pour convertir un paiement d'avance spécifique
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from paiements.models import Paiement
from paiements.models_avance import AvanceLoyer
from paiements.services_avance import ServiceGestionAvance
from decimal import Decimal

def convertir_avance_specifique():
    """Convertit l'avance de 300 000 F CFA du 30/09/2025"""
    
    print("Recherche du paiement d'avance de 300 000 F CFA...")
    
    # Trouver le paiement d'avance spécifique
    paiement_avance = Paiement.objects.filter(
        type_paiement__in=['avance_loyer', 'avance'],
        montant=300000,
        date_paiement__year=2025,
        date_paiement__month=9,
        date_paiement__day=30,
        statut='valide'
    ).first()
    
    if not paiement_avance:
        print("Paiement d'avance de 300 000 F CFA non trouve")
        return
    
    print(f"Paiement trouve: ID {paiement_avance.id}")
    print(f"Contrat: {paiement_avance.contrat.numero_contrat}")
    print(f"Montant: {paiement_avance.montant} F CFA")
    print(f"Date: {paiement_avance.date_paiement}")
    
    # Vérifier si un AvanceLoyer existe déjà
    avance_existant = AvanceLoyer.objects.filter(
        contrat=paiement_avance.contrat,
        montant_avance=paiement_avance.montant,
        date_avance=paiement_avance.date_paiement
    ).first()
    
    if avance_existant:
        print(f"AvanceLoyer deja existant: ID {avance_existant.id}")
        print(f"Statut: {avance_existant.statut}")
        print(f"Mois couverts: {avance_existant.nombre_mois_couverts}")
        return
    
    # Créer l'AvanceLoyer
    try:
        print("Creation de l'AvanceLoyer...")
        avance = ServiceGestionAvance.creer_avance_loyer(
            contrat=paiement_avance.contrat,
            montant_avance=Decimal(str(paiement_avance.montant)),
            date_avance=paiement_avance.date_paiement,
            notes="Converti depuis paiement existant"
        )
        
        print(f"AvanceLoyer cree avec succes!")
        print(f"ID: {avance.id}")
        print(f"Statut: {avance.statut}")
        print(f"Mois couverts: {avance.nombre_mois_couverts}")
        print(f"Montant restant: {avance.montant_restant}")
        
    except Exception as e:
        print(f"Erreur lors de la creation: {str(e)}")

if __name__ == "__main__":
    convertir_avance_specifique()
