#!/usr/bin/env python
"""
Script pour initialiser la configuration de l'entreprise par défaut
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from core.models import ConfigurationEntreprise, TemplateRecu

def initialiser_configuration():
    """Initialise la configuration de l'entreprise par défaut."""
    
    print("🏢 INITIALISATION DE LA CONFIGURATION ENTREPRISE")
    print("=" * 60)
    
    # Vérifier si une configuration existe déjà
    config_existante = ConfigurationEntreprise.objects.filter(active=True).first()
    
    if config_existante:
        print(f"✅ Configuration existante trouvée : {config_existante.nom_entreprise}")
        print(f"   📅 Dernière modification : {config_existante.date_modification}")
        return config_existante
    
    # Créer une configuration par défaut
    print("📝 Création de la configuration par défaut...")
    
    config = ConfigurationEntreprise.objects.create(
        nom_entreprise="GESTIMMOB",
        nom_commercial="GESTIMMOB - Gestion Immobilière",
        adresse="123 Rue de la Gestion\n75001 Paris, France",
        telephone="01 23 45 67 89",
        email="contact@gestimmob.fr",
        site_web="https://www.gestimmob.fr",
        siret="12345678901234",
        tva_intra="FR12345678901",
        rcs="Paris B 123 456 789",
        banque="Banque Populaire",
        iban="FR7630001007941234567890185",
        bic="BPPBFRPPXXX",
        couleur_principale="#2c3e50",
        couleur_secondaire="#3498db",
        police_principale="Arial",
        police_titre="Arial",
        afficher_logo=True,
        afficher_siret=True,
        afficher_tva=True,
        afficher_iban=False,
        pied_page="Merci de votre confiance.\nGESTIMMOB - Votre partenaire immobilier de confiance.",
        conditions_generales="Ce reçu est établi conformément aux dispositions légales en vigueur.\nToute contestation doit être formulée par écrit dans un délai de 30 jours.",
        actif=True
    )
    
    print(f"✅ Configuration créée : {config.nom_entreprise}")
    print(f"   📧 Email : {config.email}")
    print(f"   📞 Téléphone : {config.telephone}")
    print(f"   🎨 Couleurs : {config.couleur_principale} / {config.couleur_secondaire}")
    
    return config

def creer_templates_defaut():
    """Crée des templates de reçus par défaut."""
    
    print("\n📄 CRÉATION DES TEMPLATES PAR DÉFAUT")
    print("=" * 60)
    
    # Vérifier si des templates existent déjà
    templates_existants = TemplateRecu.objects.filter(actif=True).count()
    
    if templates_existants > 0:
        print(f"✅ {templates_existants} template(s) existant(s) trouvé(s)")
        return
    
    # Créer des templates par défaut
    templates_defaut = [
        {
            'nom': 'Standard',
            'description': 'Template standard professionnel avec toutes les informations',
            'couleur_principale': '#2c3e50',
            'couleur_secondaire': '#3498db',
            'police_principale': 'Arial',
            'afficher_logo': True,
            'afficher_siret': True,
            'afficher_tva': True,
            'afficher_iban': False,
            'par_defaut': True
        },
        {
            'nom': 'Professionnel',
            'description': 'Template élégant avec design moderne',
            'couleur_principale': '#34495e',
            'couleur_secondaire': '#e74c3c',
            'police_principale': 'Helvetica',
            'afficher_logo': True,
            'afficher_siret': True,
            'afficher_tva': True,
            'afficher_iban': True,
            'par_defaut': False
        },
        {
            'nom': 'Simplifié',
            'description': 'Template épuré avec informations essentielles',
            'couleur_principale': '#2c3e50',
            'couleur_secondaire': '#95a5a6',
            'police_principale': 'Arial',
            'afficher_logo': False,
            'afficher_siret': True,
            'afficher_tva': False,
            'afficher_iban': False,
            'par_defaut': False
        },
        {
            'nom': 'Luxe',
            'description': 'Template premium avec design sophistiqué',
            'couleur_principale': '#1a1a1a',
            'couleur_secondaire': '#d4af37',
            'police_principale': 'Georgia',
            'afficher_logo': True,
            'afficher_siret': True,
            'afficher_tva': True,
            'afficher_iban': True,
            'par_defaut': False
        }
    ]
    
    for template_data in templates_defaut:
        template = TemplateRecu.objects.create(**template_data)
        print(f"✅ Template créé : {template.nom}")
        print(f"   📝 Description : {template.description}")
        print(f"   🎨 Couleurs : {template.couleur_principale} / {template.couleur_secondaire}")
        if template.par_defaut:
            print(f"   ⭐ Template par défaut")
        print()

def afficher_statistiques():
    """Affiche les statistiques de la configuration."""
    
    print("📊 STATISTIQUES DE LA CONFIGURATION")
    print("=" * 60)
    
    config = ConfigurationEntreprise.get_configuration_active()
    templates = TemplateRecu.get_templates_actifs()
    
    print(f"🏢 Entreprise : {config.nom_entreprise}")
    print(f"📧 Contact : {config.email}")
    print(f"📞 Téléphone : {config.telephone}")
    print(f"🌐 Site web : {config.site_web}")
    print(f"🏛️ SIRET : {config.siret}")
    print(f"🏦 Banque : {config.banque}")
    print(f"🎨 Couleurs : {config.couleur_principale} / {config.couleur_secondaire}")
    print(f"📝 Police : {config.police_principale}")
    
    print(f"\n📄 Templates disponibles : {templates.count()}")
    for template in templates:
        statut = "⭐ Par défaut" if template.par_defaut else "✅ Actif"
        print(f"   • {template.nom} - {statut}")
    
    print(f"\n🔧 Options d'affichage :")
    print(f"   • Logo : {'✅' if config.afficher_logo else '❌'}")
    print(f"   • SIRET : {'✅' if config.afficher_siret else '❌'}")
    print(f"   • TVA : {'✅' if config.afficher_tva else '❌'}")
    print(f"   • IBAN : {'✅' if config.afficher_iban else '❌'}")

def main():
    """Fonction principale."""
    
    try:
        # Initialiser la configuration
        config = initialiser_configuration()
        
        # Créer les templates par défaut
        creer_templates_defaut()
        
        # Afficher les statistiques
        afficher_statistiques()
        
        print("\n" + "=" * 60)
        print("🎉 INITIALISATION TERMINÉE AVEC SUCCÈS")
        print("=" * 60)
        print("✅ Configuration de l'entreprise créée")
        print("✅ Templates par défaut créés")
        print("✅ Système de personnalisation opérationnel")
        print("\n🚀 Vous pouvez maintenant :")
        print("   • Accéder à la configuration : /core/configuration/")
        print("   • Gérer les templates : /core/templates/")
        print("   • Personnaliser les reçus selon vos besoins")
        
    except Exception as e:
        print(f"❌ ERREUR LORS DE L'INITIALISATION : {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 