#!/bin/bash
# Script d'initialisation des données pour Render

echo "🚀 INITIALISATION DES DONNÉES RENDER"
echo "===================================="

# Aller dans le bon répertoire
cd /opt/render/project/src

# Activer l'environnement virtuel
source .venv/bin/activate

echo "📁 Répertoire: $(pwd)"
echo "🐍 Python: $(which python)"

# 1. Créer les groupes de travail
echo "👥 Création des groupes de travail..."
python manage.py shell -c "
from utilisateurs.models import GroupeTravail
groupes = [
    {'nom': 'ADMINISTRATION', 'description': 'Gestion administrative et comptable complète'},
    {'nom': 'CAISSE', 'description': 'Gestion des paiements et encaissements'},
    {'nom': 'CONTROLES', 'description': 'Contrôles et vérifications des données'},
    {'nom': 'PRIVILEGE', 'description': 'Accès privilégié aux fonctionnalités avancées'}
]
for g in groupes:
    groupe, created = GroupeTravail.objects.get_or_create(nom=g['nom'], defaults={'description': g['description']})
    print(f'Groupe: {groupe.nom} - {\"Créé\" if created else \"Existe déjà\"}')
"

# 2. Créer les types de biens
echo "🏠 Création des types de biens..."
python manage.py shell -c "
from proprietes.models import TypeBien
types = [
    'Appartement', 'Maison', 'Studio', 'T1', 'T2', 'T3', 'T4', 'T5+',
    'Bureau', 'Local commercial', 'Entrepôt', 'Parking', 'Cave', 'Grenier',
    'Terrain', 'Immeuble', 'Résidence', 'Villa', 'Duplex', 'Loft'
]
for t in types:
    type_bien, created = TypeBien.objects.get_or_create(nom=t)
    print(f'Type: {type_bien.nom} - {\"Créé\" if created else \"Existe déjà\"}')
"

# 3. Créer les devises
echo "💰 Création des devises..."
python manage.py shell -c "
from core.models import Devise
devises = [
    {'code': 'XOF', 'nom': 'Franc CFA', 'symbole': 'FCFA', 'actif': True},
    {'code': 'EUR', 'nom': 'Euro', 'symbole': '€', 'actif': True},
    {'code': 'USD', 'nom': 'Dollar US', 'symbole': '$', 'actif': True}
]
for d in devises:
    devise, created = Devise.objects.get_or_create(code=d['code'], defaults=d)
    print(f'Devise: {devise.code} - {\"Créé\" if created else \"Existe déjà\"}')
"

# 4. Créer la configuration entreprise
echo "🏢 Création de la configuration entreprise..."
python manage.py shell -c "
from core.models import ConfigurationEntreprise, Devise
devise_principale = Devise.objects.filter(code='XOF').first()
config, created = ConfigurationEntreprise.objects.get_or_create(
    nom_entreprise='KBIS Immobilier',
    defaults={
        'adresse': 'Adresse de l\'entreprise',
        'telephone': '+226 XX XX XX XX',
        'email': 'contact@kbis-immobilier.com',
        'devise_principale': devise_principale,
        'actif': True
    }
)
print(f'Configuration: {\"Créée\" if created else \"Existe déjà\"}')
"

# 5. Vérification finale
echo "🔍 Vérification des données créées..."
python manage.py shell -c "
from utilisateurs.models import GroupeTravail
from proprietes.models import TypeBien
from core.models import Devise, ConfigurationEntreprise
print(f'Groupes: {GroupeTravail.objects.count()}')
print(f'Types biens: {TypeBien.objects.count()}')
print(f'Devises: {Devise.objects.count()}')
print(f'Configurations: {ConfigurationEntreprise.objects.count()}')
print('✅ Initialisation terminée avec succès!')
"

echo ""
echo "🎉 INITIALISATION TERMINÉE!"
echo "🌐 Votre application est prête avec toutes les données!"
