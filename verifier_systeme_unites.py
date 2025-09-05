#!/usr/bin/env python
"""
Script de vérification du système d'unités locatives
"""
import os
import django
import sys

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from proprietes.models import Propriete, UniteLocative, ReservationUnite
from contrats.models import Contrat
from django.urls import reverse
from django.test import Client
from django.contrib.auth import get_user_model

User = get_user_model()

def verifier_modeles():
    """Vérifier que les modèles sont bien créés et fonctionnels."""
    print("🔍 Vérification des modèles...")
    
    # Vérifier les unités locatives
    total_unites = UniteLocative.objects.count()
    print(f"✅ {total_unites} unités locatives trouvées")
    
    if total_unites > 0:
        unite = UniteLocative.objects.first()
        print(f"   • Exemple: {unite.numero_unite} - {unite.nom}")
        print(f"   • Méthodes: est_disponible() = {unite.est_disponible()}")
        print(f"   • Loyer total: {unite.get_loyer_total()} F CFA")
        
        # Vérifier la propriété associée
        propriete = unite.propriete
        print(f"   • Propriété: {propriete.titre}")
        print(f"   • Est grande propriété: {propriete.est_grande_propriete()}")
        print(f"   • Nombre d'unités: {propriete.get_nombre_unites_locatives()}")
        print(f"   • Taux d'occupation: {propriete.get_taux_occupation_global()}%")
    
    # Vérifier les réservations
    total_reservations = ReservationUnite.objects.count()
    print(f"✅ {total_reservations} réservations trouvées")
    
    if total_reservations > 0:
        reservation = ReservationUnite.objects.first()
        print(f"   • Exemple: {reservation.unite_locative.numero_unite} pour {reservation.locataire_potentiel.get_nom_complet()}")
        print(f"   • Statut: {reservation.get_statut_display()}")
        print(f"   • Active: {reservation.est_active()}")

def verifier_urls():
    """Vérifier que les URLs sont bien configurées."""
    print("\n🔗 Vérification des URLs...")
    
    urls_to_check = [
        ('proprietes:unites_liste', 'Liste des unités'),
        ('proprietes:unite_create', 'Création d\'unité'),
        ('proprietes:api_unites_disponibles', 'API unités disponibles'),
    ]
    
    for url_name, description in urls_to_check:
        try:
            url = reverse(url_name)
            print(f"✅ {description}: {url}")
        except Exception as e:
            print(f"❌ {description}: Erreur - {e}")
    
    # Vérifier les URLs avec paramètres
    if UniteLocative.objects.exists():
        unite = UniteLocative.objects.first()
        propriete = unite.propriete
        
        try:
            url = reverse('proprietes:unite_detail', kwargs={'pk': unite.pk})
            print(f"✅ Détail unité: {url}")
        except Exception as e:
            print(f"❌ Détail unité: Erreur - {e}")
        
        try:
            url = reverse('proprietes:dashboard_propriete', kwargs={'propriete_id': propriete.pk})
            print(f"✅ Dashboard propriété: {url}")
        except Exception as e:
            print(f"❌ Dashboard propriété: Erreur - {e}")

def verifier_admin():
    """Vérifier l'interface d'administration."""
    print("\n🛠️  Vérification de l'interface admin...")
    
    from django.contrib import admin
    from proprietes.models import UniteLocative, ReservationUnite
    
    # Vérifier que les modèles sont enregistrés
    if UniteLocative in admin.site._registry:
        print("✅ UniteLocative enregistré dans l'admin")
    else:
        print("❌ UniteLocative non enregistré dans l'admin")
    
    if ReservationUnite in admin.site._registry:
        print("✅ ReservationUnite enregistré dans l'admin")
    else:
        print("❌ ReservationUnite non enregistré dans l'admin")

def verifier_templates():
    """Vérifier que les templates existent."""
    print("\n📄 Vérification des templates...")
    
    templates_to_check = [
        'templates/proprietes/unites/liste.html',
        'templates/proprietes/dashboard_propriete.html',
        'templates/core/dashboard.html',
    ]
    
    for template_path in templates_to_check:
        full_path = os.path.join(os.path.dirname(__file__), template_path)
        if os.path.exists(full_path):
            print(f"✅ Template trouvé: {template_path}")
        else:
            print(f"❌ Template manquant: {template_path}")

def verifier_migrations():
    """Vérifier que les migrations sont appliquées."""
    print("\n🗄️  Vérification des migrations...")
    
    from django.db import connection
    
    # Vérifier que les tables existent
    with connection.cursor() as cursor:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        
        tables_to_check = [
            'proprietes_unitelocative',
            'proprietes_reservationunite',
        ]
        
        for table in tables_to_check:
            if table in tables:
                print(f"✅ Table {table} existe")
            else:
                print(f"❌ Table {table} manquante")

def verifier_statistiques():
    """Vérifier les statistiques du système."""
    print("\n📊 Statistiques du système...")
    
    # Statistiques générales
    total_proprietes = Propriete.objects.filter(is_deleted=False).count()
    grandes_proprietes = sum(1 for p in Propriete.objects.filter(is_deleted=False) if p.est_grande_propriete())
    
    print(f"   • Total propriétés: {total_proprietes}")
    print(f"   • Grandes propriétés: {grandes_proprietes}")
    
    # Statistiques des unités
    unites_stats = {
        'total': UniteLocative.objects.filter(is_deleted=False).count(),
        'disponibles': UniteLocative.objects.filter(is_deleted=False, statut='disponible').count(),
        'occupees': UniteLocative.objects.filter(is_deleted=False, statut='occupee').count(),
        'reservees': UniteLocative.objects.filter(is_deleted=False, statut='reservee').count(),
    }
    
    print(f"   • Unités locatives:")
    for statut, count in unites_stats.items():
        print(f"     - {statut.capitalize()}: {count}")
    
    # Statistiques des réservations
    reservations_stats = {
        'total': ReservationUnite.objects.filter(is_deleted=False).count(),
        'actives': sum(1 for r in ReservationUnite.objects.filter(is_deleted=False) if r.est_active()),
        'expirees': sum(1 for r in ReservationUnite.objects.filter(is_deleted=False) if r.est_expiree()),
    }
    
    print(f"   • Réservations:")
    for statut, count in reservations_stats.items():
        print(f"     - {statut.capitalize()}: {count}")

def verifier_integration_contrats():
    """Vérifier l'intégration avec les contrats."""
    print("\n🤝 Vérification de l'intégration avec les contrats...")
    
    # Vérifier que le modèle Contrat a bien le champ unite_locative
    from contrats.models import Contrat
    
    try:
        # Essayer d'accéder au champ
        contrat = Contrat.objects.first()
        if contrat:
            unite = contrat.unite_locative
            print(f"✅ Champ unite_locative accessible dans Contrat")
            if unite:
                print(f"   • Contrat lié à l'unité: {unite.numero_unite}")
            else:
                print(f"   • Contrat sans unité locative (normal pour anciens contrats)")
        else:
            print(f"ℹ️  Aucun contrat existant pour tester l'intégration")
    except AttributeError as e:
        print(f"❌ Erreur d'intégration avec les contrats: {e}")

def main():
    """Fonction principale de vérification."""
    print("🚀 VÉRIFICATION DU SYSTÈME D'UNITÉS LOCATIVES")
    print("=" * 60)
    
    try:
        verifier_modeles()
        verifier_urls()
        verifier_admin()
        verifier_templates()
        verifier_migrations()
        verifier_statistiques()
        verifier_integration_contrats()
        
        print("\n" + "=" * 60)
        print("✅ VÉRIFICATION TERMINÉE AVEC SUCCÈS!")
        print("\n🎯 PROCHAINES ÉTAPES:")
        print("   1. Lancez le serveur: python manage.py runserver")
        print("   2. Accédez au dashboard: http://localhost:8000/")
        print("   3. Testez les unités locatives: http://localhost:8000/proprietes/unites/")
        print("   4. Explorez l'admin: http://localhost:8000/admin/")
        
    except Exception as e:
        print(f"\n❌ ERREUR LORS DE LA VÉRIFICATION: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
