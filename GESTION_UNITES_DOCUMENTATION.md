# 🏢 Documentation - Système de Gestion des Unités et Charges Communes

**Date de création :** 19 janvier 2025  
**Version :** 1.0  
**Statut :** ✅ Implémenté et fonctionnel

---

## 🎯 **Vue d'ensemble**

Le système de gestion des unités permet de gérer efficacement :
- **Unités locatives complètes** (appartements, maisons)
- **Pièces individuelles** (chambres en colocation)
- **Espaces partagés** (cuisine commune, salon, salle de bain)
- **Charges communes** avec répartition automatique
- **Validations intelligentes** pour éviter les conflits

---

## 🏗️ **Architecture des Modèles**

### **1. Modèles Existants Étendus**

#### **`Piece` (Étendu)**
```python
class Piece(models.Model):
    # Champs existants...
    
    # Nouveaux champs pour espaces partagés
    est_espace_partage = models.BooleanField(default=False)
    cout_acces_mensuel = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    acces_inclus_dans_pieces = models.ManyToManyField('self', through='AccesEspacePartage')
```

#### **`Contrat` (Étendu)**
```python
class Contrat(models.Model):
    # Champs existants...
    
    # Nouvelles méthodes
    def get_type_location(self):
        # Retourne: 'unite_complete', 'pieces_individuelles', 'propriete_complete'
    
    def get_description_location(self):
        # Description lisible du type de location
    
    def _valider_coherence_unite_pieces(self):
        # Validation automatique unité OU pièces (pas les deux)
```

### **2. Nouveaux Modèles**

#### **`ChargeCommune`**
Gestion des charges partagées d'une propriété.

```python
class ChargeCommune(models.Model):
    propriete = models.ForeignKey(Propriete)
    nom = models.CharField(max_length=100)
    type_charge = models.CharField(choices=TYPE_CHARGE_CHOICES)
    montant_mensuel = models.DecimalField(max_digits=10, decimal_places=2)
    type_repartition = models.CharField(choices=TYPE_REPARTITION_CHOICES)
    date_debut = models.DateField()
    date_fin = models.DateField(blank=True, null=True)
    active = models.BooleanField(default=True)
```

**Types de charges :**
- Électricité, Eau, Gaz
- Internet, Entretien, Assurance
- Taxes, Gardiennage, Nettoyage

**Types de répartition :**
- `equipartition` : Répartition équitable
- `surface` : Répartition par surface des pièces
- `nb_occupants` : Répartition par nombre d'occupants
- `personnalisee` : Répartition personnalisée

#### **`RepartitionChargeCommune`**
Stockage des calculs de répartition.

```python
class RepartitionChargeCommune(models.Model):
    charge_commune = models.ForeignKey(ChargeCommune)
    piece_contrat = models.ForeignKey(PieceContrat)
    montant_calcule = models.DecimalField(max_digits=10, decimal_places=2)
    montant_ajuste = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    mois = models.PositiveIntegerField()
    annee = models.PositiveIntegerField()
    base_calcul = models.CharField(max_length=100)
    applique = models.BooleanField(default=False)
```

#### **`AccesEspacePartage`**
Gestion des accès aux espaces partagés.

```python
class AccesEspacePartage(models.Model):
    piece_privee = models.ForeignKey(Piece, related_name='acces_espaces_partages')
    espace_partage = models.ForeignKey(Piece, related_name='acces_depuis_pieces')
    acces_inclus = models.BooleanField(default=True)
    cout_supplementaire = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    heures_acces_debut = models.TimeField(blank=True, null=True)
    heures_acces_fin = models.TimeField(blank=True, null=True)
    jours_acces = models.CharField(max_length=50, blank=True)
    date_debut_acces = models.DateField()
    date_fin_acces = models.DateField(blank=True, null=True)
    actif = models.BooleanField(default=True)
```

---

## 🔧 **Services et Logique Métier**

### **`GestionChargesCommunesService`**

#### **Calcul des charges mensuelles**
```python
resultats = GestionChargesCommunesService.calculer_charges_mensuelles(
    propriete_id=1,
    mois=1,
    annee=2025
)
```

**Retourne :**
```python
{
    'charges_calculees': [
        {
            'charge': 'Électricité commune',
            'locataire': 'Dupont Jean',
            'piece': 'Chambre 1',
            'montant': 37.50,
            'base_calcul': 'équipartition',
            'nouveau': True
        }
    ],
    'total_charges': 150.00,
    'nb_locataires': 4,
    'erreurs': []
}
```

#### **Application des charges aux contrats**
```python
resultats = GestionChargesCommunesService.appliquer_charges_aux_contrats(
    propriete_id=1,
    mois=1,
    annee=2025
)
```

**Retourne :**
```python
{
    'applications': [
        {
            'locataire': 'Dupont Jean',
            'piece': 'Chambre 1',
            'charges_avant': 50.00,
            'charges_ajoutees': 87.50,
            'charges_apres': 137.50,
            'details': [
                {'charge': 'Électricité commune', 'montant': 37.50},
                {'charge': 'Internet haut débit', 'montant': 12.50},
                {'charge': 'Entretien ménage', 'montant': 25.00},
                {'charge': 'Eau commune', 'montant': 12.50}
            ]
        }
    ],
    'total_applique': 350.00,
    'erreurs': []
}
```

---

## 🌐 **API REST**

### **Endpoints des Charges Communes**

#### **CRUD de base**
```
GET    /proprietes/api/charges-communes/          # Liste des charges
POST   /proprietes/api/charges-communes/          # Créer une charge
GET    /proprietes/api/charges-communes/{id}/     # Détail d'une charge
PUT    /proprietes/api/charges-communes/{id}/     # Modifier une charge
DELETE /proprietes/api/charges-communes/{id}/     # Supprimer une charge
```

#### **Actions spécialisées**
```
POST /proprietes/api/charges-communes/{id}/calculer_repartition/
POST /proprietes/api/charges-communes/calculer_charges_propriete/
POST /proprietes/api/charges-communes/appliquer_charges_propriete/
```

**Exemple d'appel API :**
```javascript
// Calcul des charges pour janvier 2025
fetch('/proprietes/api/charges-communes/calculer_charges_propriete/', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        propriete_id: 1,
        mois: 1,
        annee: 2025
    })
})
```

### **Endpoints des Pièces**

```
GET /proprietes/api/pieces/                    # Liste des pièces
GET /proprietes/api/pieces/{id}/espaces_partages/     # Espaces partagés accessibles
GET /proprietes/api/pieces/{id}/cout_acces_espaces/   # Coût d'accès aux espaces
GET /proprietes/api/pieces/{id}/peut_etre_louee/      # Vérification de location individuelle
```

---

## 🖥️ **Interface Utilisateur**

### **Vue d'Occupation Unifiée**
**URL :** `/contrats/occupation-propriete/{propriete_id}/`

**Fonctionnalités :**
- 📊 **Statistiques en temps réel** : Taux d'occupation, revenus mensuels
- 🏠 **Onglet Unités Locatives** : Vue des appartements/maisons complètes
- 🚪 **Onglet Pièces Individuelles** : Vue des chambres en colocation
- 🎯 **Actions rapides** : Création de contrats, gestion des pièces
- 📈 **Barres de progression** : Visualisation des taux d'occupation

**Exemple de données affichées :**
```
Statistiques Générales:
├── 3 Unités totales (66.7% occupées)
├── 12 Pièces totales (83.3% occupées) 
├── 2 Unités occupées
└── 2,850€ Revenus mensuels

Unités Locatives:
├── Appartement A - OCCUPÉ (Jean Dupont, 1,200€/mois)
├── Appartement B - OCCUPÉ (Marie Martin, 1,000€/mois)
└── Appartement C - LIBRE

Pièces Individuelles:
├── Chambre 1 - OCCUPÉE (Paul Durand, 400€ + 50€ charges)
├── Chambre 2 - OCCUPÉE (Sophie Leroy, 450€ + 60€ charges)
├── Chambre 3 - LIBRE
└── Cuisine commune - ESPACE PARTAGÉ (30€/mois d'accès)
```

### **Administration Django**

**Nouveaux modèles dans l'admin :**
- 🏢 **Charges Communes** : Création et gestion des charges
- 📊 **Répartitions** : Visualisation des calculs
- 🚪 **Pièces** : Gestion des pièces et espaces partagés
- 🔗 **Accès Espaces** : Configuration des accès aux espaces communs

---

## ⚡ **Commandes de Gestion**

### **Commande d'initialisation**
```bash
# Créer des charges de test pour une propriété
python manage.py init_charges_communes --propriete_id=1

# Créer des charges pour toutes les propriétés
python manage.py init_charges_communes --all

# Calculer les charges du mois courant
python manage.py init_charges_communes --propriete_id=1 --calculer

# Appliquer les charges calculées
python manage.py init_charges_communes --propriete_id=1 --appliquer

# Processus complet
python manage.py init_charges_communes --propriete_id=1 --calculer --appliquer
```

**Sortie exemple :**
```
🏢 Initialisation du système de charges communes

📍 Traitement de la propriété: Résidence Les Jardins
  ✅ Charge créée: Électricité commune (150€, Répartition équitable)
  ✅ Charge créée: Internet haut débit (50€, Répartition équitable)
  ✅ Charge créée: Entretien ménage (100€, Répartition par surface)
  ✅ Charge créée: Eau commune (80€, Répartition par nombre d'occupants)
📊 4 charges communes créées

🔢 Calcul des charges pour 1/2025...
✅ 16 répartitions calculées
💰 Total charges: 380.00€
👥 Nombre de locataires: 4

📝 Application des charges pour 1/2025...
✅ Charges appliquées à 4 contrats
💰 Total appliqué: 380.00€
```

---

## 🔒 **Validations et Sécurité**

### **Validations Automatiques**

#### **1. Validation Unité OU Pièces**
```python
# Dans le modèle Contrat
def _valider_coherence_unite_pieces(self):
    if self.unite_locative and self.pieces_contrat.filter(actif=True).exists():
        raise ValidationError(
            "Un contrat ne peut pas avoir simultanément une unité locative "
            "ET des pièces spécifiques."
        )
```

#### **2. Validation Espaces Essentiels**
```python
# Dans le modèle Piece
def peut_etre_louee_individuellement(self):
    espaces_accessibles = self.get_espaces_partages_accessibles()
    types_espaces = set(espaces_accessibles.values_list('type_piece', flat=True))
    espaces_essentiels = {'cuisine', 'salle_bain'}
    return espaces_essentiels.issubset(types_espaces)
```

#### **3. Validation Accès Cohérents**
```python
# Dans le modèle AccesEspacePartage
def clean(self):
    if self.piece_privee == self.espace_partage:
        raise ValidationError("Une pièce ne peut pas avoir accès à elle-même.")
    
    if not self.espace_partage.est_espace_partage:
        raise ValidationError("L'espace de destination doit être marqué comme espace partagé.")
```

---

## 📊 **Exemples d'Usage**

### **Cas 1 : Immeuble avec Appartements**
```python
# Propriété : Résidence Le Parc (3 appartements)
propriete = Propriete.objects.create(
    titre="Résidence Le Parc",
    type_propriete="immeuble"
)

# Unités locatives
apt_a = UniteLocative.objects.create(
    propriete=propriete,
    nom="Appartement A",
    surface=60,
    nombre_pieces=3
)

# Contrat pour appartement complet
contrat = Contrat.objects.create(
    propriete=propriete,
    unite_locative=apt_a,  # Unité complète
    locataire=locataire,
    loyer_mensuel=1200
)
```

### **Cas 2 : Grande Maison en Colocation**
```python
# Propriété : Maison de Colocation (6 chambres + espaces communs)
maison = Propriete.objects.create(
    titre="Maison de Colocation",
    type_propriete="maison"
)

# Pièces privées
chambre1 = Piece.objects.create(
    propriete=maison,
    nom="Chambre 1",
    type_piece="chambre",
    surface=15
)

# Espaces partagés
cuisine_commune = Piece.objects.create(
    propriete=maison,
    nom="Cuisine commune",
    type_piece="cuisine",
    est_espace_partage=True,
    cout_acces_mensuel=30
)

# Accès aux espaces partagés
AccesEspacePartage.objects.create(
    piece_privee=chambre1,
    espace_partage=cuisine_commune,
    acces_inclus=True,
    date_debut_acces=date.today()
)

# Contrat pour chambre individuelle
contrat = Contrat.objects.create(
    propriete=maison,
    # unite_locative reste null
    locataire=locataire
)

# Assignation de la pièce
PieceContrat.objects.create(
    contrat=contrat,
    piece=chambre1,
    loyer_piece=400,
    charges_piece=50,
    date_debut_occupation=contrat.date_debut
)
```

### **Cas 3 : Charges Communes Automatiques**
```python
# Création des charges communes
charges = [
    ChargeCommune.objects.create(
        propriete=maison,
        nom="Électricité commune",
        type_charge="electricite",
        montant_mensuel=150,
        type_repartition="equipartition",
        date_debut=date.today()
    ),
    ChargeCommune.objects.create(
        propriete=maison,
        nom="Entretien ménage",
        type_charge="nettoyage",
        montant_mensuel=100,
        type_repartition="surface",
        date_debut=date.today()
    )
]

# Calcul automatique pour janvier 2025
resultats = GestionChargesCommunesService.calculer_charges_mensuelles(
    maison.id, 1, 2025
)

# Application aux contrats
GestionChargesCommunesService.appliquer_charges_aux_contrats(
    maison.id, 1, 2025
)
```

---

## 🚀 **Avantages du Système**

### **1. Flexibilité Maximale**
- Gère tous types de locations (unités, pièces, mixte)
- Espaces partagés configurables
- Charges communes intelligentes

### **2. Automatisation**
- Calculs automatiques des répartitions
- Validation des configurations
- Mise à jour des statuts

### **3. Transparence**
- Vue d'occupation en temps réel
- Détail des calculs de charges
- Historique des modifications

### **4. Évolutivité**
- Architecture modulaire
- API REST complète
- Extensible pour nouveaux besoins

---

## 🔧 **Installation et Configuration**

### **1. Migrations**
```bash
python manage.py makemigrations proprietes
python manage.py migrate
```

### **2. Permissions**
Les nouvelles fonctionnalités respectent le système de permissions existant :
- `PRIVILEGE` : Accès complet
- `ADMINISTRATION` : Gestion des charges
- `CONTROLES` : Visualisation

### **3. Tests**
```bash
# Tester la commande d'initialisation
python manage.py init_charges_communes --propriete_id=1

# Tester l'API
curl -X GET http://localhost:8000/proprietes/api/charges-communes/

# Tester la vue d'occupation
http://localhost:8000/contrats/occupation-propriete/1/
```

---

## 📝 **Notes de Développement**

### **Considérations Techniques**
- Utilisation de `select_related` et `prefetch_related` pour optimiser les requêtes
- Gestion des transactions pour les calculs de charges
- Validation côté modèle ET côté formulaire
- Gestion des erreurs avec messages utilisateur

### **Points d'Extension Futurs**
- Notifications automatiques pour charges calculées
- Intégration avec système de paiement
- Rapports PDF des répartitions
- Planning de maintenance des espaces partagés

---

**🎉 Le système est maintenant pleinement opérationnel et prêt à gérer tous vos besoins de location d'unités et de gestion des charges communes !**





