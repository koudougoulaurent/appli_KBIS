#!/usr/bin/env python
"""
Script d'initialisation des données de base
Utilisateurs, propriétés, bailleurs, locataires
"""
import os
import django
import random
from datetime import date

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from django.contrib.auth import get_user_model
from proprietes.models import Propriete, Bailleur, Locataire, TypeBien

Utilisateur = get_user_model()


def create_superuser():
    """Crée un superutilisateur."""
    print("👤 Création du superutilisateur...")
    
    if Utilisateur.objects.filter(username='admin').exists():
        print("⚠️ L'utilisateur admin existe déjà")
        return Utilisateur.objects.get(username='admin')
    
    user = Utilisateur.objects.create_superuser(
        username='admin',
        email='admin@example.com',
        password='admin123'
    )
    print("✅ Superutilisateur créé: admin/admin123")
    return user


def create_users():
    """Crée des utilisateurs de test."""
    print("👥 Création des utilisateurs...")
    
    users_data = [
        {'username': 'manager', 'email': 'manager@example.com', 'first_name': 'Jean', 'last_name': 'Dupont'},
        {'username': 'agent', 'email': 'agent@example.com', 'first_name': 'Marie', 'last_name': 'Martin'},
        {'username': 'assistant', 'email': 'assistant@example.com', 'first_name': 'Pierre', 'last_name': 'Durand'},
    ]
    
    users_crees = []
    
    for user_data in users_data:
        if not Utilisateur.objects.filter(username=user_data['username']).exists():
            user = Utilisateur.objects.create_user(
                username=user_data['username'],
                email=user_data['email'],
                password='password123',
                first_name=user_data['first_name'],
                last_name=user_data['last_name'],
                is_staff=True
            )
            users_crees.append(user)
            print(f"✅ Utilisateur créé: {user.username}")
    
    print(f"🎉 {len(users_crees)} utilisateurs créés")
    return users_crees


def create_types_bien():
    """Crée les types de biens."""
    print("🏠 Création des types de biens...")
    
    types_data = [
        {'nom': 'Appartement', 'description': 'Appartement en immeuble'},
        {'nom': 'Maison', 'description': 'Maison individuelle'},
        {'nom': 'Studio', 'description': 'Studio meublé'},
        {'nom': 'Loft', 'description': 'Loft industriel'},
        {'nom': 'Villa', 'description': 'Villa avec jardin'},
    ]
    
    types_crees = []
    
    for type_data in types_data:
        type_bien, created = TypeBien.objects.get_or_create(
            nom=type_data['nom'],
            defaults=type_data
        )
        if created:
            types_crees.append(type_bien)
            print(f"✅ Type créé: {type_bien.nom}")
    
    print(f"🎉 {len(types_crees)} types de biens créés")
    return TypeBien.objects.all()


def create_bailleurs():
    """Crée des bailleurs de test."""
    print("👨‍💼 Création des bailleurs...")
    
    bailleurs_data = [
        {
            'nom': 'Dupont', 'prenom': 'Michel', 'email': 'michel.dupont@email.com', 
            'telephone': '0123456789', 'adresse': '123 Rue de la Paix, 75001 Paris'
        },
        {
            'nom': 'Martin', 'prenom': 'Sophie', 'email': 'sophie.martin@email.com', 
            'telephone': '0123456790', 'adresse': '456 Avenue des Champs, 69001 Lyon'
        },
        {
            'nom': 'Durand', 'prenom': 'François', 'email': 'francois.durand@email.com', 
            'telephone': '0123456791', 'adresse': '789 Boulevard Central, 13001 Marseille'
        },
        {
            'nom': 'Leroy', 'prenom': 'Isabelle', 'email': 'isabelle.leroy@email.com', 
            'telephone': '0123456792', 'adresse': '321 Rue du Commerce, 31000 Toulouse'
        },
        {
            'nom': 'Moreau', 'prenom': 'Philippe', 'email': 'philippe.moreau@email.com', 
            'telephone': '0123456793', 'adresse': '654 Avenue Victor Hugo, 33000 Bordeaux'
        },
    ]
    
    bailleurs_crees = []
    
    for bailleur_data in bailleurs_data:
        bailleur, created = Bailleur.objects.get_or_create(
            email=bailleur_data['email'],
            defaults=bailleur_data
        )
        if created:
            bailleurs_crees.append(bailleur)
            print(f"✅ Bailleur créé: {bailleur.nom} {bailleur.prenom}")
    
    print(f"🎉 {len(bailleurs_crees)} bailleurs créés")
    return Bailleur.objects.all()


def create_locataires():
    """Crée des locataires de test."""
    print("👤 Création des locataires...")
    
    locataires_data = [
        {
            'nom': 'Bernard', 'prenom': 'Thomas', 'email': 'thomas.bernard@email.com', 
            'telephone': '0123456794', 'adresse_actuelle': '123 Rue de la Paix, 75001 Paris'
        },
        {
            'nom': 'Petit', 'prenom': 'Julie', 'email': 'julie.petit@email.com', 
            'telephone': '0123456795', 'adresse_actuelle': '456 Avenue des Champs, 69001 Lyon'
        },
        {
            'nom': 'Robert', 'prenom': 'Nicolas', 'email': 'nicolas.robert@email.com', 
            'telephone': '0123456796', 'adresse_actuelle': '789 Boulevard Central, 13001 Marseille'
        },
        {
            'nom': 'Richard', 'prenom': 'Céline', 'email': 'celine.richard@email.com', 
            'telephone': '0123456797', 'adresse_actuelle': '321 Rue du Commerce, 31000 Toulouse'
        },
        {
            'nom': 'Durand', 'prenom': 'Laurent', 'email': 'laurent.durand@email.com', 
            'telephone': '0123456798', 'adresse_actuelle': '654 Avenue Victor Hugo, 33000 Bordeaux'
        },
        {
            'nom': 'Leroy', 'prenom': 'Amélie', 'email': 'amelie.leroy@email.com', 
            'telephone': '0123456799', 'adresse_actuelle': '987 Boulevard Saint-Germain, 44000 Nantes'
        },
        {
            'nom': 'Moreau', 'prenom': 'David', 'email': 'david.moreau@email.com', 
            'telephone': '0123456800', 'adresse_actuelle': '147 Rue de Rivoli, 67000 Strasbourg'
        },
        {
            'nom': 'Simon', 'prenom': 'Caroline', 'email': 'caroline.simon@email.com', 
            'telephone': '0123456801', 'adresse_actuelle': '258 Avenue des Ternes, 34000 Montpellier'
        },
    ]
    
    locataires_crees = []
    
    for locataire_data in locataires_data:
        locataire, created = Locataire.objects.get_or_create(
            email=locataire_data['email'],
            defaults=locataire_data
        )
        if created:
            locataires_crees.append(locataire)
            print(f"✅ Locataire créé: {locataire.nom} {locataire.prenom}")
    
    print(f"🎉 {len(locataires_crees)} locataires créés")
    return Locataire.objects.all()


def create_proprietes(bailleurs, types_bien):
    """Crée des propriétés de test."""
    print("🏠 Création des propriétés...")
    
    villes = ['Paris', 'Lyon', 'Marseille', 'Toulouse', 'Bordeaux', 'Nantes', 'Strasbourg', 'Montpellier']
    adresses = [
        '123 Rue de la Paix', '456 Avenue des Champs', '789 Boulevard Central',
        '321 Rue du Commerce', '654 Avenue Victor Hugo', '987 Boulevard Saint-Germain',
        '147 Rue de Rivoli', '258 Avenue des Ternes', '369 Boulevard Haussmann',
        '741 Rue de la Pompe', '852 Avenue Foch', '963 Boulevard Malesherbes'
    ]
    
    proprietes_crees = []
    
    for i in range(15):
        ville = random.choice(villes)
        adresse = random.choice(adresses)
        type_bien = random.choice(types_bien)
        bailleur = random.choice(bailleurs)
        
        # Générer des données réalistes
        superficie = random.randint(25, 150)
        nb_pieces = random.randint(1, 5)
        loyer_actuel = random.randint(500, 2000)
        
        propriete = Propriete.objects.create(
            titre=f"{type_bien.nom} à {ville}",
            adresse=adresse,
            ville=ville,
            code_postal=str(random.randint(10000, 99999)),
            surface=superficie,
            nombre_pieces=nb_pieces,
            nombre_chambres=random.randint(1, nb_pieces),
            nombre_salles_bain=random.randint(1, 2),
            loyer_actuel=loyer_actuel,
            charges=random.randint(50, 200),
            ascenseur=random.choice([True, False]),
            parking=random.choice([True, False]),
            balcon=random.choice([True, False]),
            jardin=random.choice([True, False]),
            etat=random.choice(['excellent', 'bon', 'moyen']),
            disponible=random.choice([True, True, True, False]),  # 75% disponibles
            type_bien=type_bien,
            bailleur=bailleur,
            notes=f"Propriété de test {i+1}"
        )
        
        proprietes_crees.append(propriete)
        print(f"✅ Propriété créée: {propriete.titre}")
    
    print(f"🎉 {len(proprietes_crees)} propriétés créées")
    return proprietes_crees


def main():
    """Fonction principale."""
    print("🚀 INITIALISATION DES DONNÉES DE BASE")
    print("=" * 50)
    
    try:
        # 1. Créer le superutilisateur
        admin_user = create_superuser()
        
        # 2. Créer les utilisateurs
        users = create_users()
        
        # 3. Créer les types de biens
        types_bien = create_types_bien()
        
        # 4. Créer les bailleurs
        bailleurs = create_bailleurs()
        
        # 5. Créer les locataires
        locataires = create_locataires()
        
        # 6. Créer les propriétés
        proprietes = create_proprietes(bailleurs, types_bien)
        
        print("\n🎉 INITIALISATION TERMINÉE AVEC SUCCÈS !")
        print("\n📊 Statistiques créées:")
        print(f"   - Utilisateurs: {Utilisateur.objects.count()}")
        print(f"   - Types de biens: {TypeBien.objects.count()}")
        print(f"   - Bailleurs: {Bailleur.objects.count()}")
        print(f"   - Locataires: {Locataire.objects.count()}")
        print(f"   - Propriétés: {Propriete.objects.count()}")
        
        print("\n🔑 Identifiants de connexion:")
        print("   - Admin: admin/admin123")
        print("   - Manager: manager/password123")
        print("   - Agent: agent/password123")
        print("   - Assistant: assistant/password123")
        
        print("\n🌐 Accès:")
        print("   - Dashboard: http://127.0.0.1:8000/")
        print("   - Admin: http://127.0.0.1:8000/admin/")
        
    except Exception as e:
        print(f"❌ Erreur lors de l'initialisation: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main() 