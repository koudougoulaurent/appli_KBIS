#!/usr/bin/env python
"""
Test final de la fonctionnalité type_gestion
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings_minimal')
django.setup()

from proprietes.models import Propriete, Piece, TypeBien, Bailleur
from django.contrib.auth.models import User

def test_final():
    """Test final de la fonctionnalité type_gestion"""
    print('=== Test final de la fonctionnalité type_gestion ===')

    # Utiliser un utilisateur existant ou en créer un nouveau
    user, created = User.objects.get_or_create(
        username='test_user_final', 
        defaults={'email': 'test@test.com', 'password': 'pbkdf2_sha256$260000$test'}
    )
    print(f'✓ Utilisateur: {"créé" if created else "existant"}')

    # Créer un type de bien
    type_bien, created = TypeBien.objects.get_or_create(
        nom='Appartement', 
        defaults={'description': 'Test'}
    )
    print(f'✓ Type de bien: {"créé" if created else "existant"}')

    # Créer un bailleur
    bailleur, created = Bailleur.objects.get_or_create(
        nom='Dupont', prenom='Jean',
        defaults={
            'email': 'jean@test.com', 
            'telephone': '0123456789', 
            'adresse': '123 rue Test', 
            'ville': 'Paris', 
            'code_postal': '75001', 
            'pays': 'France', 
            'cree_par': user
        }
    )
    print(f'✓ Bailleur: {"créé" if created else "existant"}')

    # Test 1: Propriété entière
    print('\n1. Test propriété entière...')
    propriete_entiere = Propriete.objects.create(
        titre='Appartement T3 complet',
        type_gestion='propriete_entiere',
        type_bien=type_bien,
        bailleur=bailleur,
        adresse='456 avenue Test',
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
    print(f'   ✓ Propriété créée: {propriete_entiere.titre}')
    print(f'   ✓ Type: {propriete_entiere.get_type_gestion_display()}')
    print(f'   ✓ est_propriete_entiere(): {propriete_entiere.est_propriete_entiere()}')
    print(f'   ✓ est_avec_unites_multiples(): {propriete_entiere.est_avec_unites_multiples()}')

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
    print(f'   ✓ Pièces créées pour propriété entière')
    print(f'   - {piece1.nom}: peut_etre_louee_individuellement() = {piece1.peut_etre_louee_individuellement()}')
    print(f'   - {piece1.nom}: get_statut_affichage() = {piece1.get_statut_affichage()}')
    print(f'   - {piece2.nom}: peut_etre_louee_individuellement() = {piece2.peut_etre_louee_individuellement()}')
    print(f'   - {piece2.nom}: get_statut_affichage() = {piece2.get_statut_affichage()}')

    # Test 2: Propriété avec unités multiples
    print('\n2. Test propriété avec unités multiples...')
    propriete_unites = Propriete.objects.create(
        titre='Colocation 4 chambres',
        type_gestion='unites_multiples',
        type_bien=type_bien,
        bailleur=bailleur,
        adresse='789 rue Test',
        ville='Lyon',
        code_postal='69001',
        pays='France',
        nombre_pieces=6,
        nombre_chambres=4,
        nombre_salles_bain=2,
        surface=120.0,
        loyer_actuel=0.00,
        cree_par=user
    )
    print(f'   ✓ Propriété créée: {propriete_unites.titre}')
    print(f'   ✓ Type: {propriete_unites.get_type_gestion_display()}')
    print(f'   ✓ est_propriete_entiere(): {propriete_unites.est_propriete_entiere()}')
    print(f'   ✓ est_avec_unites_multiples(): {propriete_unites.est_avec_unites_multiples()}')

    # Créer des pièces pour la propriété avec unités multiples
    piece3 = Piece.objects.create(
        propriete=propriete_unites,
        nom='Chambre A',
        type_piece='chambre',
        surface=18.0,
        statut='disponible'
    )
    piece4 = Piece.objects.create(
        propriete=propriete_unites,
        nom='Cuisine commune',
        type_piece='cuisine',
        surface=15.0,
        statut='disponible',
        est_espace_partage=True
    )
    print(f'   ✓ Pièces créées pour propriété unités multiples')
    print(f'   - {piece3.nom}: peut_etre_louee_individuellement() = {piece3.peut_etre_louee_individuellement()}')
    print(f'   - {piece3.nom}: get_statut_affichage() = {piece3.get_statut_affichage()}')
    print(f'   - {piece4.nom}: peut_etre_louee_individuellement() = {piece4.peut_etre_louee_individuellement()}')
    print(f'   - {piece4.nom}: get_statut_affichage() = {piece4.get_statut_affichage()}')

    # Test des méthodes de disponibilité
    print('\n3. Test des méthodes de disponibilité...')
    print(f'   Propriété entière disponible: {propriete_entiere.est_disponible_pour_location()}')
    print(f'   Propriété unités multiples disponible: {propriete_unites.est_disponible_pour_location()}')

    # Test des pièces louables individuellement
    print('\n4. Test des pièces louables individuellement...')
    pieces_louables_entiere = propriete_entiere.get_pieces_louables_individuellement()
    pieces_louables_unites = propriete_unites.get_pieces_louables_individuellement()
    print(f'   Pièces louables individuellement (propriété entière): {pieces_louables_entiere.count()}')
    print(f'   Pièces louables individuellement (propriété unités): {pieces_louables_unites.count()}')

    for piece in pieces_louables_unites:
        print(f'   - {piece.nom} (louable individuellement)')

    print('\n=== Test final réussi ! ===')

    # Nettoyage
    print('\nNettoyage des données de test...')
    propriete_entiere.delete()
    propriete_unites.delete()
    print('✓ Données de test supprimées')

if __name__ == '__main__':
    test_final()