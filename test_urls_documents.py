#!/usr/bin/env python
"""
Script de test pour vérifier que toutes les URLs des documents fonctionnent correctement
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from django.urls import reverse
from django.test import Client
from django.contrib.auth import get_user_model
from proprietes.models import Document, Propriete, Bailleur, Locataire

def test_urls():
    """Teste toutes les URLs importantes des documents"""
    print("🔍 Test des URLs des documents")
    print("=" * 50)
    
    # URLs à tester
    urls_to_test = [
        # URLs de base
        ('proprietes:document_list', [], 'Liste des documents'),
        ('proprietes:document_create', [], 'Création de document'),
        
        # URLs avec paramètres (si des documents existent)
        # Ces URLs seront testées dynamiquement
    ]
    
    # Test des URLs de base
    for url_name, args, description in urls_to_test:
        try:
            url = reverse(url_name, args=args)
            print(f"✅ {description}: {url}")
        except Exception as e:
            print(f"❌ {description}: ERREUR - {e}")
    
    # Test des URLs avec des objets existants
    print("\n🔍 Test des URLs avec objets existants")
    print("-" * 30)
    
    # Vérifier s'il y a des documents
    if Document.objects.exists():
        document = Document.objects.first()
        try:
            url = reverse('proprietes:document_detail', args=[document.pk])
            print(f"✅ Détail document: {url}")
        except Exception as e:
            print(f"❌ Détail document: ERREUR - {e}")
            
        try:
            url = reverse('proprietes:document_update', args=[document.pk])
            print(f"✅ Modification document: {url}")
        except Exception as e:
            print(f"❌ Modification document: ERREUR - {e}")
    else:
        print("⚠️ Aucun document en base pour tester les URLs avec paramètres")
    
    # Test des URLs des entités liées
    print("\n🔍 Test des URLs des entités liées")
    print("-" * 30)
    
    # Propriétés
    if Propriete.objects.exists():
        propriete = Propriete.objects.first()
        try:
            url = reverse('proprietes:detail', args=[propriete.pk])
            print(f"✅ Détail propriété: {url}")
        except Exception as e:
            print(f"❌ Détail propriété: ERREUR - {e}")
    
    # Bailleurs
    if Bailleur.objects.exists():
        bailleur = Bailleur.objects.first()
        try:
            url = reverse('proprietes:detail_bailleur', args=[bailleur.pk])
            print(f"✅ Détail bailleur: {url}")
        except Exception as e:
            print(f"❌ Détail bailleur: ERREUR - {e}")
    
    # Locataires
    if Locataire.objects.exists():
        locataire = Locataire.objects.first()
        try:
            url = reverse('proprietes:detail_locataire', args=[locataire.pk])
            print(f"✅ Détail locataire: {url}")
        except Exception as e:
            print(f"❌ Détail locataire: ERREUR - {e}")

def test_template_rendering():
    """Teste le rendu des templates avec un utilisateur privilégié"""
    print("\n🎨 Test du rendu des templates")
    print("=" * 50)
    
    User = get_user_model()
    client = Client()
    
    # Créer ou récupérer un utilisateur privilégié
    try:
        user = User.objects.filter(username='privilege1').first()
        if not user:
            print("⚠️ Aucun utilisateur privilégié trouvé pour tester les templates")
            return
        
        # Se connecter
        client.force_login(user)
        
        # Tester la page de liste des documents
        response = client.get(reverse('proprietes:document_list'))
        if response.status_code == 200:
            print("✅ Page liste des documents: OK")
        else:
            print(f"❌ Page liste des documents: Status {response.status_code}")
        
        # Tester la page de détail si un document existe
        if Document.objects.exists():
            document = Document.objects.first()
            response = client.get(reverse('proprietes:document_detail', args=[document.pk]))
            if response.status_code == 200:
                print("✅ Page détail document: OK")
            else:
                print(f"❌ Page détail document: Status {response.status_code}")
        
    except Exception as e:
        print(f"❌ Erreur lors du test des templates: {e}")

def main():
    """Fonction principale"""
    print("🚀 Test des URLs et Templates des Documents")
    print("=" * 60)
    
    test_urls()
    test_template_rendering()
    
    print("\n🎉 Tests terminés!")
    print("=" * 60)

if __name__ == "__main__":
    main()
