#!/usr/bin/env python
"""
Script de test pour vérifier la nouvelle fonctionnalité de type de gestion des propriétés
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings_minimal')
django.setup()

from proprietes.models import Propriete, TypeBien, Bailleur, Piece
from django.contrib.auth.models import User

def test_type_gestion():
    """Test de la nouvelle fonctionnalité type_gestion"""
    print("=== Test de la fonctionnalité type_gestion ===\n")
    
    # Créer un utilisateur de test
    user, created = User.objects.get_or_create(
        username='test_user',
        defaults={'email': 'test@example.com'}
    )
    
    # Créer un type de bien
    type_bien, created = TypeBien.objects.get_or_create(
        nom='Appartement',
        defaults={'description': 'Appartement de test'}
    )
    
    # Créer un bailleur
    bailleur, created = Bailleur.objects.get_or_create(
        nom='Dupont',
        prenom='Jean',
        defaults={
            'email': 'jean.dupont@example.com',
            'telephone': '01 23 45 67 89',
            'adresse': '123 rue de la Paix',
            'ville': 'Paris',
            'code_postal': '75001',
            'pays': 'France',
            'cree_par': user
        }
    )
    
    print("1. Test création propriété entière...")
    # Créer une propriété entière
    propriete_entiere = Propriete.objects.create(
        titre='Appartement T3 complet',
        type_bien=type_bien,
        type_gestion='propriete_entiere',  # Nouveau champ
        bailleur=bailleur,
        adresse='456 avenue des Champs',
        ville='Paris',
        code_postal='75008',
        pays='France',
        nombre_pieces=3,
        nombre_chambres=2,
        nombre_salles_bain=1,
        surface=75.5,
        loyer_actuel=1200.00,
        cree_par=user
    )
    
    print(f"   ✓ Propriété créée: {propriete_entiere.titre}")
    print(f"   ✓ Type de gestion: {propriete_entiere.get_type_gestion_display()}")
    print(f"   ✓ Est propriété entière: {propriete_entiere.est_propriete_entiere()}")
    print(f"   ✓ Est avec unités multiples: {propriete_entiere.est_avec_unites_multiples()}")
    
    # Créer des pièces pour la propriété entière
    piece1 = Piece.objects.create(
        propriete=propriete_entiere,
        nom='Salon',
        type_piece='salon',
        surface=25.0,
        statut='disponible'
    )
    
    piece2 = Piece.objects.create(
        propriete=propriete_entiere,
        nom='Chambre 1',
        type_piece='chambre',
        surface=15.0,
        statut='disponible'
    )
    
    piece3 = Piece.objects.create(
        propriete=propriete_entiere,
        nom='Cuisine',
        type_piece='cuisine',
        surface=12.0,
        statut='disponible'
    )
    
    print(f"\n   Pièces créées pour la propriété entière:")
    for piece in [piece1, piece2, piece3]:
        print(f"   - {piece.nom}: {piece.get_statut_affichage()}")
        print(f"     Peut être louée individuellement: {piece.peut_etre_louee_individuellement()}")
        print(f"     Est vraiment disponible: {piece.est_vraiment_disponible()}")
    
    print("\n2. Test création propriété avec unités multiples...")
    # Créer une propriété avec unités multiples
    propriete_unites = Propriete.objects.create(
        titre='Colocation 4 chambres',
        type_bien=type_bien,
        type_gestion='unites_multiples',  # Nouveau champ
        bailleur=bailleur,
        adresse='789 rue de la République',
        ville='Lyon',
        code_postal='69001',
        pays='France',
        nombre_pieces=6,
        nombre_chambres=4,
        nombre_salles_bain=2,
        surface=120.0,
        loyer_actuel=0.00,  # Pas de loyer global
        cree_par=user
    )
    
    print(f"   ✓ Propriété créée: {propriete_unites.titre}")
    print(f"   ✓ Type de gestion: {propriete_unites.get_type_gestion_display()}")
    print(f"   ✓ Est propriété entière: {propriete_unites.est_propriete_entiere()}")
    print(f"   ✓ Est avec unités multiples: {propriete_unites.est_avec_unites_multiples()}")
    
    # Créer des pièces pour la propriété avec unités multiples
    piece4 = Piece.objects.create(
        propriete=propriete_unites,
        nom='Chambre A',
        type_piece='chambre',
        surface=18.0,
        statut='disponible'
    )
    
    piece5 = Piece.objects.create(
        propriete=propriete_unites,
        nom='Chambre B',
        type_piece='chambre',
        surface=16.0,
        statut='disponible'
    )
    
    piece6 = Piece.objects.create(
        propriete=propriete_unites,
        nom='Cuisine commune',
        type_piece='cuisine',
        surface=15.0,
        statut='disponible',
        est_espace_partage=True  # Espace partagé
    )
    
    print(f"\n   Pièces créées pour la propriété avec unités multiples:")
    for piece in [piece4, piece5, piece6]:
        print(f"   - {piece.nom}: {piece.get_statut_affichage()}")
        print(f"     Peut être louée individuellement: {piece.peut_etre_louee_individuellement()}")
        print(f"     Est vraiment disponible: {piece.est_vraiment_disponible()}")
        if piece.est_espace_partage:
            print(f"     Espace partagé: Oui")
    
    print("\n3. Test des méthodes de disponibilité...")
    print(f"   Propriété entière disponible: {propriete_entiere.est_disponible_pour_location()}")
    print(f"   Propriété unités multiples disponible: {propriete_unites.est_disponible_pour_location()}")
    
    print("\n4. Test des pièces louables individuellement...")
    pieces_louables_entiere = propriete_entiere.get_pieces_louables_individuellement()
    pieces_louables_unites = propriete_unites.get_pieces_louables_individuellement()
    
    print(f"   Pièces louables individuellement (propriété entière): {pieces_louables_entiere.count()}")
    print(f"   Pièces louables individuellement (propriété unités): {pieces_louables_unites.count()}")
    
    for piece in pieces_louables_unites:
        print(f"   - {piece.nom} (louable individuellement)")
    
    print("\n=== Test terminé avec succès ! ===")
    
    # Nettoyage
    print("\nNettoyage des données de test...")
    propriete_entiere.delete()
    propriete_unites.delete()
    print("✓ Données de test supprimées")

if __name__ == '__main__':
    test_type_gestion()
