#!/usr/bin/env python
"""
Script pour créer des données de test pour le système d'unités locatives
"""
import os
import django
import sys

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from proprietes.models import Propriete, UniteLocative, Bailleur, TypeBien, Locataire, ReservationUnite
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

def create_test_data():
    """Créer des données de test pour les unités locatives."""
    
    print("🚀 Création des données de test pour les unités locatives...")
    
    # Vérifier s'il y a déjà des unités
    if UniteLocative.objects.exists():
        print("⚠️  Des unités locatives existent déjà.")
        response = input("Voulez-vous continuer et en créer d'autres ? (y/N): ")
        if response.lower() != 'y':
            print("❌ Annulé par l'utilisateur.")
            return
    
    # Récupérer ou créer un bailleur
    bailleur, created = Bailleur.objects.get_or_create(
        nom="IMMOBILIER",
        prenom="TEST",
        defaults={
            'email': 'test@immobilier.com',
            'telephone': '0123456789',
            'actif': True
        }
    )
    if created:
        print(f"✅ Bailleur créé: {bailleur.get_nom_complet()}")
    
    # Récupérer ou créer un type de bien
    type_bien, created = TypeBien.objects.get_or_create(
        nom="Immeuble résidentiel",
        defaults={'description': 'Immeuble avec plusieurs appartements'}
    )
    if created:
        print(f"✅ Type de bien créé: {type_bien.nom}")
    
    # Créer une grande propriété de test
    propriete, created = Propriete.objects.get_or_create(
        numero_propriete="TEST001",
        defaults={
            'titre': 'Résidence Les Palmiers - TEST',
            'description': 'Immeuble de 20 appartements sur 5 étages',
            'adresse': '123 Avenue des Palmiers',
            'code_postal': '75001',
            'ville': 'Paris',
            'pays': 'France',
            'type_bien': type_bien,
            'surface': Decimal('1500.00'),
            'nombre_pieces': 80,  # Total de toutes les pièces
            'nombre_chambres': 40,
            'nombre_salles_bain': 20,
            'prix_achat': Decimal('2500000.00'),
            'loyer_actuel': Decimal('15000.00'),  # Loyer total de l'immeuble
            'charges_locataire': Decimal('2000.00'),
            'bailleur': bailleur,
            'disponible': False  # Pas entièrement disponible
        }
    )
    if created:
        print(f"✅ Propriété créée: {propriete.titre}")
    else:
        print(f"ℹ️  Propriété existante utilisée: {propriete.titre}")
    
    # Créer des unités locatives
    unites_data = [
        # Rez-de-chaussée - Locaux commerciaux
        {'numero': 'Local-A', 'nom': 'Local Commercial A', 'type': 'local_commercial', 'etage': 0, 'pieces': 2, 'chambres': 0, 'sdb': 1, 'surface': 80, 'loyer': 1200, 'charges': 150, 'statut': 'occupee'},
        {'numero': 'Local-B', 'nom': 'Local Commercial B', 'type': 'local_commercial', 'etage': 0, 'pieces': 3, 'chambres': 0, 'sdb': 1, 'surface': 120, 'loyer': 1800, 'charges': 200, 'statut': 'disponible'},
        
        # 1er étage - Appartements
        {'numero': 'Apt-101', 'nom': 'Appartement 2 pièces Sud', 'type': 'appartement', 'etage': 1, 'pieces': 2, 'chambres': 1, 'sdb': 1, 'surface': 45, 'loyer': 750, 'charges': 80, 'statut': 'occupee', 'meuble': False},
        {'numero': 'Apt-102', 'nom': 'Appartement 3 pièces Nord', 'type': 'appartement', 'etage': 1, 'pieces': 3, 'chambres': 2, 'sdb': 1, 'surface': 65, 'loyer': 950, 'charges': 100, 'statut': 'reservee'},
        {'numero': 'Apt-103', 'nom': 'Studio meublé', 'type': 'studio', 'etage': 1, 'pieces': 1, 'chambres': 0, 'sdb': 1, 'surface': 25, 'loyer': 600, 'charges': 70, 'statut': 'disponible', 'meuble': True},
        {'numero': 'Apt-104', 'nom': 'Appartement 4 pièces', 'type': 'appartement', 'etage': 1, 'pieces': 4, 'chambres': 3, 'sdb': 2, 'surface': 85, 'loyer': 1200, 'charges': 120, 'statut': 'occupee'},
        
        # 2ème étage - Mix appartements et bureaux
        {'numero': 'Apt-201', 'nom': 'Appartement 2 pièces balcon', 'type': 'appartement', 'etage': 2, 'pieces': 2, 'chambres': 1, 'sdb': 1, 'surface': 50, 'loyer': 800, 'charges': 85, 'statut': 'occupee', 'balcon': True},
        {'numero': 'Apt-202', 'nom': 'Appartement 3 pièces terrasse', 'type': 'appartement', 'etage': 2, 'pieces': 3, 'chambres': 2, 'sdb': 1, 'surface': 70, 'loyer': 1000, 'charges': 110, 'statut': 'disponible', 'balcon': True},
        {'numero': 'Bureau-203', 'nom': 'Bureau professionnel', 'type': 'bureau', 'etage': 2, 'pieces': 3, 'chambres': 0, 'sdb': 1, 'surface': 60, 'loyer': 900, 'charges': 120, 'statut': 'en_renovation'},
        {'numero': 'Bureau-204', 'nom': 'Open Space', 'type': 'bureau', 'etage': 2, 'pieces': 2, 'chambres': 0, 'sdb': 1, 'surface': 80, 'loyer': 1100, 'charges': 150, 'statut': 'disponible'},
        
        # 3ème étage - Chambres meublées
        {'numero': 'Ch-301', 'nom': 'Chambre meublée A', 'type': 'chambre', 'etage': 3, 'pieces': 1, 'chambres': 1, 'sdb': 1, 'surface': 20, 'loyer': 450, 'charges': 60, 'statut': 'occupee', 'meuble': True, 'internet': True},
        {'numero': 'Ch-302', 'nom': 'Chambre meublée B', 'type': 'chambre', 'etage': 3, 'pieces': 1, 'chambres': 1, 'sdb': 1, 'surface': 22, 'loyer': 480, 'charges': 60, 'statut': 'disponible', 'meuble': True, 'internet': True},
        {'numero': 'Ch-303', 'nom': 'Chambre meublée C', 'type': 'chambre', 'etage': 3, 'pieces': 1, 'chambres': 1, 'sdb': 1, 'surface': 18, 'loyer': 420, 'charges': 55, 'statut': 'reservee', 'meuble': True, 'internet': True},
        {'numero': 'Ch-304', 'nom': 'Chambre meublée D', 'type': 'chambre', 'etage': 3, 'pieces': 1, 'chambres': 1, 'sdb': 1, 'surface': 25, 'loyer': 500, 'charges': 65, 'statut': 'disponible', 'meuble': True, 'internet': True, 'balcon': True},
        
        # 4ème étage - Appartements haut de gamme
        {'numero': 'Apt-401', 'nom': 'Penthouse 5 pièces', 'type': 'appartement', 'etage': 4, 'pieces': 5, 'chambres': 3, 'sdb': 2, 'surface': 120, 'loyer': 1800, 'charges': 200, 'statut': 'occupee', 'balcon': True, 'climatisation': True},
        {'numero': 'Apt-402', 'nom': 'Appartement 4 pièces vue', 'type': 'appartement', 'etage': 4, 'pieces': 4, 'chambres': 2, 'sdb': 2, 'surface': 95, 'loyer': 1400, 'charges': 160, 'statut': 'disponible', 'balcon': True},
        
        # Sous-sol - Parkings et caves
        {'numero': 'Park-01', 'nom': 'Place de parking A', 'type': 'parking', 'etage': -1, 'pieces': 1, 'chambres': 0, 'sdb': 0, 'surface': 15, 'loyer': 80, 'charges': 10, 'statut': 'occupee'},
        {'numero': 'Park-02', 'nom': 'Place de parking B', 'type': 'parking', 'etage': -1, 'pieces': 1, 'chambres': 0, 'sdb': 0, 'surface': 15, 'loyer': 80, 'charges': 10, 'statut': 'disponible'},
        {'numero': 'Cave-01', 'nom': 'Cave de stockage', 'type': 'cave', 'etage': -1, 'pieces': 1, 'chambres': 0, 'sdb': 0, 'surface': 10, 'loyer': 50, 'charges': 5, 'statut': 'disponible'},
    ]
    
    created_unites = 0
    for unite_info in unites_data:
        unite, created = UniteLocative.objects.get_or_create(
            propriete=propriete,
            numero_unite=unite_info['numero'],
            defaults={
                'nom': unite_info['nom'],
                'type_unite': unite_info['type'],
                'etage': unite_info['etage'],
                'surface': Decimal(str(unite_info['surface'])),
                'nombre_pieces': unite_info['pieces'],
                'nombre_chambres': unite_info['chambres'],
                'nombre_salles_bain': unite_info['sdb'],
                'loyer_mensuel': Decimal(str(unite_info['loyer'])),
                'charges_mensuelles': Decimal(str(unite_info['charges'])),
                'caution_demandee': Decimal(str(unite_info['loyer'] * 2)),  # 2 mois de caution
                'statut': unite_info['statut'],
                'meuble': unite_info.get('meuble', False),
                'balcon': unite_info.get('balcon', False),
                'climatisation': unite_info.get('climatisation', False),
                'internet_inclus': unite_info.get('internet', False),
                'description': f"Unité {unite_info['nom']} située au {unite_info['etage']}ème étage",
            }
        )
        if created:
            created_unites += 1
            print(f"✅ Unité créée: {unite.numero_unite} - {unite.nom}")
    
    print(f"\n🎉 {created_unites} unités locatives créées avec succès!")
    
    # Créer quelques locataires de test
    locataires_data = [
        {'nom': 'MARTIN', 'prenom': 'Jean', 'email': 'jean.martin@email.com', 'numero': 'LOC001'},
        {'nom': 'DUPONT', 'prenom': 'Marie', 'email': 'marie.dupont@email.com', 'numero': 'LOC002'},
        {'nom': 'BERNARD', 'prenom': 'Pierre', 'email': 'pierre.bernard@email.com', 'numero': 'LOC003'},
    ]
    
    created_locataires = 0
    for loc_info in locataires_data:
        locataire, created = Locataire.objects.get_or_create(
            numero_locataire=loc_info['numero'],
            defaults={
                'nom': loc_info['nom'],
                'prenom': loc_info['prenom'],
                'email': loc_info['email'],
                'telephone': '0123456789',
                'statut': 'actif'
            }
        )
        if created:
            created_locataires += 1
            print(f"✅ Locataire créé: {locataire.get_nom_complet()}")
    
    # Créer quelques réservations de test
    unites_disponibles = UniteLocative.objects.filter(statut='disponible')[:2]
    locataires = Locataire.objects.all()[:2]
    
    created_reservations = 0
    for i, unite in enumerate(unites_disponibles):
        if i < len(locataires):
            reservation, created = ReservationUnite.objects.get_or_create(
                unite_locative=unite,
                locataire_potentiel=locataires[i],
                defaults={
                    'date_debut_souhaitee': timezone.now().date() + timedelta(days=7),
                    'date_expiration': timezone.now() + timedelta(days=7),
                    'montant_reservation': unite.loyer_mensuel * Decimal('0.1'),  # 10% du loyer
                    'statut': 'en_attente',
                    'notes': f'Réservation de test pour {unite.numero_unite}'
                }
            )
            if created:
                created_reservations += 1
                print(f"✅ Réservation créée: {unite.numero_unite} pour {locataires[i].get_nom_complet()}")
    
    print(f"\n📊 RÉSUMÉ DE LA CRÉATION:")
    print(f"   • {created_unites} unités locatives")
    print(f"   • {created_locataires} locataires")
    print(f"   • {created_reservations} réservations")
    
    # Afficher les statistiques
    total_unites = UniteLocative.objects.filter(propriete=propriete).count()
    stats = {
        'total': total_unites,
        'disponibles': UniteLocative.objects.filter(propriete=propriete, statut='disponible').count(),
        'occupees': UniteLocative.objects.filter(propriete=propriete, statut='occupee').count(),
        'reservees': UniteLocative.objects.filter(propriete=propriete, statut='reservee').count(),
        'renovation': UniteLocative.objects.filter(propriete=propriete, statut='en_renovation').count(),
    }
    
    print(f"\n📈 STATISTIQUES DE LA PROPRIÉTÉ '{propriete.titre}':")
    print(f"   • Total unités: {stats['total']}")
    print(f"   • Disponibles: {stats['disponibles']}")
    print(f"   • Occupées: {stats['occupees']}")
    print(f"   • Réservées: {stats['reservees']}")
    print(f"   • En rénovation: {stats['renovation']}")
    print(f"   • Taux d'occupation: {propriete.get_taux_occupation_global()}%")
    print(f"   • Revenus potentiels: {propriete.get_revenus_mensuels_potentiels()} F CFA/mois")
    print(f"   • Revenus actuels: {propriete.get_revenus_mensuels_actuels()} F CFA/mois")
    
    print(f"\n🔗 LIENS UTILES:")
    print(f"   • Liste des unités: /proprietes/unites/")
    print(f"   • Dashboard propriété: /proprietes/{propriete.pk}/dashboard/")
    print(f"   • Admin Django: /admin/proprietes/unitelocative/")
    
    print(f"\n✨ Système d'unités locatives prêt à être testé!")

if __name__ == "__main__":
    create_test_data()
