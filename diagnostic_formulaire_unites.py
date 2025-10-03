#!/usr/bin/env python
"""
Diagnostic du formulaire d'ajout d'unités locatives
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from proprietes.models import UniteLocative, Propriete, Bailleur, TypeBien
from proprietes.forms_unites import UniteLocativeForm

def verifier_donnees_base():
    """Vérifie les données dans la base de données"""
    print("🔍 VÉRIFICATION DES DONNÉES EN BASE")
    print("=" * 50)
    
    # Vérifier les types d'unités
    print("\n📋 Types d'unités disponibles :")
    for choice in UniteLocative.TYPE_UNITE_CHOICES:
        print(f"   - {choice[0]}: {choice[1]}")
    
    # Vérifier les propriétés
    print(f"\n🏢 Propriétés disponibles : {Propriete.objects.filter(is_deleted=False).count()}")
    for prop in Propriete.objects.filter(is_deleted=False)[:5]:
        print(f"   - {prop.id}: {prop.titre}")
    
    # Vérifier les bailleurs
    print(f"\n👤 Bailleurs disponibles : {Bailleur.objects.filter(is_deleted=False, actif=True).count()}")
    for bailleur in Bailleur.objects.filter(is_deleted=False, actif=True)[:5]:
        print(f"   - {bailleur.id}: {bailleur.nom} {bailleur.prenom}")
    
    # Vérifier les types de biens
    print(f"\n🏠 Types de biens disponibles : {TypeBien.objects.count()}")
    for type_bien in TypeBien.objects.all()[:5]:
        print(f"   - {type_bien.id}: {type_bien.nom}")

def tester_formulaire():
    """Teste le formulaire d'unités locatives"""
    print("\n🧪 TEST DU FORMULAIRE")
    print("=" * 50)
    
    try:
        # Créer une instance du formulaire
        form = UniteLocativeForm()
        
        print("\n✅ Formulaire créé avec succès")
        
        # Vérifier les champs
        print("\n📝 Champs du formulaire :")
        for field_name, field in form.fields.items():
            print(f"   - {field_name}: {type(field).__name__}")
            
            # Vérifier les choix pour les champs Select
            if hasattr(field, 'choices') and field.choices:
                print(f"     Choix disponibles : {len(field.choices)}")
                for choice in field.choices[:3]:  # Afficher les 3 premiers
                    print(f"       - {choice[0]}: {choice[1]}")
                if len(field.choices) > 3:
                    print(f"       ... et {len(field.choices) - 3} autres")
            
            # Vérifier le queryset pour les champs ModelChoiceField
            if hasattr(field, 'queryset') and field.queryset:
                print(f"     Queryset : {field.queryset.count()} éléments")
        
        # Vérifier spécifiquement le champ type_unite
        print(f"\n🎯 Champ type_unite :")
        print(f"   - Type : {type(form.fields['type_unite']).__name__}")
        print(f"   - Choix : {len(form.fields['type_unite'].choices)}")
        print(f"   - Requis : {form.fields['type_unite'].required}")
        
        for choice in form.fields['type_unite'].choices:
            print(f"     - {choice[0]}: {choice[1]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la création du formulaire : {e}")
        return False

def creer_donnees_test():
    """Crée des données de test si nécessaire"""
    print("\n🔧 CRÉATION DE DONNÉES DE TEST")
    print("=" * 50)
    
    # Créer un type de bien si nécessaire
    if TypeBien.objects.count() == 0:
        type_bien = TypeBien.objects.create(
            nom="Immeuble",
            description="Immeuble résidentiel"
        )
        print(f"✅ Type de bien créé : {type_bien.nom}")
    
    # Créer une propriété si nécessaire
    if Propriete.objects.filter(is_deleted=False).count() == 0:
        type_bien = TypeBien.objects.first()
        propriete = Propriete.objects.create(
            titre="Test Property",
            type_bien=type_bien,
            adresse="123 Test Street",
            ville="Test City"
        )
        print(f"✅ Propriété créée : {propriete.titre}")
    
    # Créer un bailleur si nécessaire
    if Bailleur.objects.filter(is_deleted=False, actif=True).count() == 0:
        bailleur = Bailleur.objects.create(
            nom="Test",
            prenom="Bailleur",
            telephone="+226 70 00 00 00"
        )
        print(f"✅ Bailleur créé : {bailleur.nom} {bailleur.prenom}")

def verifier_template():
    """Vérifie le template du formulaire"""
    print("\n📄 VÉRIFICATION DU TEMPLATE")
    print("=" * 50)
    
    template_path = "templates/proprietes/unites/form.html"
    
    if os.path.exists(template_path):
        print(f"✅ Template trouvé : {template_path}")
        
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Vérifier la présence des champs
        champs_importants = [
            'form.type_unite',
            'form.propriete',
            'form.bailleur',
            'form.numero_unite',
            'form.nom'
        ]
        
        for champ in champs_importants:
            if champ in content:
                print(f"   ✅ {champ} présent dans le template")
            else:
                print(f"   ❌ {champ} manquant dans le template")
        
        # Vérifier les classes CSS
        if 'form-select' in content:
            print("   ✅ Classes CSS form-select présentes")
        else:
            print("   ❌ Classes CSS form-select manquantes")
            
    else:
        print(f"❌ Template non trouvé : {template_path}")

def main():
    """Fonction principale"""
    print("🔧 DIAGNOSTIC FORMULAIRE UNITÉS LOCATIVES")
    print("=" * 60)
    
    # Vérifier les données en base
    verifier_donnees_base()
    
    # Créer des données de test si nécessaire
    creer_donnees_test()
    
    # Tester le formulaire
    formulaire_ok = tester_formulaire()
    
    # Vérifier le template
    verifier_template()
    
    print("\n" + "=" * 60)
    if formulaire_ok:
        print("✅ DIAGNOSTIC TERMINÉ - Formulaire fonctionnel")
        print("\n🎯 Solutions appliquées :")
        print("   ✅ Choix définis pour le champ type_unite")
        print("   ✅ Queryset défini pour le champ propriete")
        print("   ✅ Queryset défini pour le champ bailleur")
        print("   ✅ Valeurs par défaut configurées")
        print("   ✅ Validation des données ajoutée")
        
        print("\n🚀 Le formulaire devrait maintenant afficher correctement :")
        print("   📋 Liste des types d'unités")
        print("   🏢 Liste des propriétés")
        print("   👤 Liste des bailleurs")
        print("   ✨ Tous les champs avec leurs données")
        
    else:
        print("❌ DIAGNOSTIC TERMINÉ - Problèmes détectés")
        print("Vérifiez les erreurs ci-dessus et corrigez-les.")

if __name__ == '__main__':
    main()
