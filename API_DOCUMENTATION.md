# 📚 Documentation API REST - Gestion Immobilière

## 🎯 Vue d'ensemble

L'API REST de gestion immobilière fournit un accès programmatique à toutes les fonctionnalités de l'application. Elle est construite avec Django REST Framework et offre des endpoints complets pour la gestion des utilisateurs, propriétés, bailleurs, locataires, contrats et paiements.

## 🔐 Authentification

L'API utilise l'authentification Django standard. Tous les endpoints (sauf l'authentification) nécessitent que l'utilisateur soit connecté.

### Endpoints d'authentification

#### POST /utilisateurs/auth/login/
Authentification d'un utilisateur.

**Corps de la requête :**
```json
{
    "username": "laurenzo",
    "password": "motdepasse123"
}
```

**Réponse :**
```json
{
    "user": {
        "id": 1,
        "username": "laurenzo",
        "email": "laurenzo@example.com",
        "first_name": "Laurenzo",
        "last_name": "Admin",
        "groupe": "privilege",
        "groupe_display": "Privilège",
        "telephone": "+1234567890",
        "is_active": true
    },
    "message": "Connexion réussie"
}
```

#### POST /utilisateurs/auth/change_password/
Changer le mot de passe de l'utilisateur connecté.

**Corps de la requête :**
```json
{
    "old_password": "ancienmotdepasse",
    "new_password": "nouveaumotdepasse"
}
```

---

## 👥 API Utilisateurs

### Base URL : `/utilisateurs/api/`

#### GET /utilisateurs/api/
Récupérer la liste des utilisateurs.

**Paramètres de requête :**
- `groupe` : Filtrer par groupe (privilege, administration, caisse, controle)
- `is_active` : Filtrer par statut actif (true/false)
- `search` : Recherche dans username, email, first_name, last_name, telephone
- `ordering` : Tri (username, first_name, last_name, date_joined, last_login)

**Réponse :**
```json
{
    "count": 5,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": 1,
            "username": "laurenzo",
            "email": "laurenzo@example.com",
            "nom_complet": "Laurenzo Admin",
            "groupe": "privilege",
            "groupe_display": "Privilège",
            "telephone": "+1234567890",
            "is_active": true
        }
    ]
}
```

#### GET /utilisateurs/api/stats/
Statistiques des utilisateurs.

**Réponse :**
```json
{
    "total_users": 5,
    "active_users": 4,
    "inactive_users": 1,
    "groupe_stats": {
        "privilege": 1,
        "administration": 2,
        "caisse": 1,
        "controle": 1
    }
}
```

#### GET /utilisateurs/api/me/
Récupérer les informations de l'utilisateur connecté.

#### POST /utilisateurs/api/
Créer un nouvel utilisateur.

**Corps de la requête :**
```json
{
    "username": "nouveau_user",
    "email": "nouveau@example.com",
    "password": "motdepasse123",
    "password_confirm": "motdepasse123",
    "first_name": "Nouveau",
    "last_name": "Utilisateur",
    "groupe": "administration",
    "telephone": "+1234567890",
    "adresse": "123 Rue Example",
    "date_naissance": "1990-01-01",
    "date_embauche": "2024-01-01",
    "salaire": 3000.00
}
```

#### PUT /utilisateurs/api/{id}/
Mettre à jour un utilisateur.

#### DELETE /utilisateurs/api/{id}/
Supprimer un utilisateur.

#### POST /utilisateurs/api/{id}/activate/
Activer un utilisateur.

#### POST /utilisateurs/api/{id}/deactivate/
Désactiver un utilisateur.

#### POST /utilisateurs/api/{id}/reset_password/
Réinitialiser le mot de passe d'un utilisateur.

**Corps de la requête :**
```json
{
    "new_password": "nouveaumotdepasse"
}
```

#### GET /utilisateurs/api/search/
Recherche avancée d'utilisateurs.

**Paramètres de requête :**
- `q` : Terme de recherche

---

## 🏠 API Propriétés

### Base URL : `/proprietes/api/`

#### GET /proprietes/api/proprietes/
Récupérer la liste des propriétés.

**Paramètres de requête :**
- `statut` : Filtrer par statut (disponible, loue, construction)
- `ville` : Filtrer par ville
- `type_bien` : Filtrer par type de bien
- `bailleur` : Filtrer par bailleur
- `locataire` : Filtrer par locataire
- `prix_min` : Prix minimum
- `prix_max` : Prix maximum
- `surface_min` : Surface minimum
- `surface_max` : Surface maximum
- `search` : Recherche dans reference, titre, adresse, ville, description
- `ordering` : Tri (reference, titre, prix_location, surface, date_creation)

**Réponse :**
```json
{
    "count": 10,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": 1,
            "reference": "PROP-2024-001",
            "titre": "Appartement moderne",
            "adresse": "123 Rue de la Paix",
            "ville": "Paris",
            "surface": 75.5,
            "nombre_pieces": 3,
            "prix_location": 1200.00,
            "statut": "loue",
            "statut_display": "Loué",
            "bailleur_nom": "Jean Dupont",
            "locataire_nom": "Marie Martin",
            "type_bien_nom": "Appartement"
        }
    ]
}
```

#### GET /proprietes/api/proprietes/stats/
Statistiques des propriétés.

**Réponse :**
```json
{
    "total_proprietes": 10,
    "proprietes_louees": 7,
    "proprietes_disponibles": 2,
    "proprietes_en_construction": 1,
    "valeur_totale": 2500000.00,
    "revenus_mensuels": 8400.00,
    "prix_moyen_m2": 1120.50
}
```

#### GET /proprietes/api/proprietes/disponibles/
Récupérer les propriétés disponibles.

#### GET /proprietes/api/proprietes/louees/
Récupérer les propriétés louées.

#### POST /proprietes/api/proprietes/{id}/louer/
Louer une propriété.

**Corps de la requête :**
```json
{
    "locataire_id": 1
}
```

#### POST /proprietes/api/proprietes/{id}/liberer/
Libérer une propriété.

#### GET /proprietes/api/proprietes/search/
Recherche avancée de propriétés.

#### GET /proprietes/api/proprietes/par_ville/
Propriétés groupées par ville.

**Paramètres de requête :**
- `ville` : Nom de la ville

#### GET /proprietes/api/proprietes/par_prix/
Propriétés dans une fourchette de prix.

**Paramètres de requête :**
- `prix_min` : Prix minimum
- `prix_max` : Prix maximum

---

## 👤 API Bailleurs

### Base URL : `/proprietes/api/bailleurs/`

#### GET /proprietes/api/bailleurs/
Récupérer la liste des bailleurs.

**Paramètres de requête :**
- `ville` : Filtrer par ville
- `pays` : Filtrer par pays
- `search` : Recherche dans nom, prenom, email, telephone, ville
- `ordering` : Tri (nom, prenom, date_creation)

**Réponse :**
```json
{
    "count": 5,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": 1,
            "nom": "Dupont",
            "prenom": "Jean",
            "nom_complet": "Jean Dupont",
            "email": "jean.dupont@example.com",
            "telephone": "+1234567890",
            "ville": "Paris",
            "proprietes_count": 3
        }
    ]
}
```

#### GET /proprietes/api/bailleurs/stats/
Statistiques des bailleurs.

**Réponse :**
```json
{
    "total_bailleurs": 5,
    "bailleurs_avec_proprietes": 4,
    "top_bailleurs": [
        {
            "id": 1,
            "nom": "Dupont",
            "prenom": "Jean",
            "nom_complet": "Jean Dupont",
            "email": "jean.dupont@example.com",
            "telephone": "+1234567890",
            "ville": "Paris",
            "proprietes_count": 3
        }
    ]
}
```

#### GET /proprietes/api/bailleurs/{id}/proprietes/
Récupérer les propriétés d'un bailleur.

#### GET /proprietes/api/bailleurs/search/
Recherche avancée de bailleurs.

---

## 🏠 API Locataires

### Base URL : `/proprietes/api/locataires/`

#### GET /proprietes/api/locataires/
Récupérer la liste des locataires.

**Paramètres de requête :**
- `ville` : Filtrer par ville
- `pays` : Filtrer par pays
- `search` : Recherche dans nom, prenom, email, telephone, ville
- `ordering` : Tri (nom, prenom, date_creation)

#### GET /proprietes/api/locataires/stats/
Statistiques des locataires.

#### GET /proprietes/api/locataires/{id}/proprietes/
Récupérer les propriétés d'un locataire.

#### GET /proprietes/api/locataires/search/
Recherche avancée de locataires.

---

## 🏢 API Types de Biens

### Base URL : `/proprietes/api/types/`

#### GET /proprietes/api/types/
Récupérer la liste des types de biens.

**Paramètres de requête :**
- `search` : Recherche dans nom, description
- `ordering` : Tri (nom, prix_moyen_m2)

#### GET /proprietes/api/types/stats/
Statistiques des types de biens.

---

## 🔧 Utilisation

### Exemple avec JavaScript

```javascript
// Récupérer la liste des propriétés
async function getProperties() {
    try {
        const response = await fetch('/proprietes/api/proprietes/');
        const data = await response.json();
        console.log('Propriétés:', data.results);
    } catch (error) {
        console.error('Erreur:', error);
    }
}

// Créer une nouvelle propriété
async function createProperty(propertyData) {
    try {
        const response = await fetch('/proprietes/api/proprietes/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify(propertyData)
        });
        const data = await response.json();
        console.log('Propriété créée:', data);
    } catch (error) {
        console.error('Erreur:', error);
    }
}

// Fonction utilitaire pour récupérer le token CSRF
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
```

### Exemple avec Python (requests)

```python
import requests

# Configuration
BASE_URL = 'http://localhost:8000'
session = requests.Session()

# Authentification
login_data = {
    'username': 'laurenzo',
    'password': 'motdepasse123'
}
response = session.post(f'{BASE_URL}/utilisateurs/auth/login/', json=login_data)
print('Authentification:', response.json())

# Récupérer les propriétés
response = session.get(f'{BASE_URL}/proprietes/api/proprietes/')
properties = response.json()
print('Propriétés:', properties['results'])

# Créer une nouvelle propriété
new_property = {
    'titre': 'Nouvel appartement',
    'adresse': '456 Rue Nouvelle',
    'ville': 'Lyon',
    'surface': 85.0,
    'nombre_pieces': 4,
    'prix_location': 1500.00,
    'statut': 'disponible',
    'bailleur': 1,
    'type_bien': 1
}
response = session.post(f'{BASE_URL}/proprietes/api/proprietes/', json=new_property)
print('Propriété créée:', response.json())
```

---

## 📊 Codes de statut HTTP

- `200 OK` : Requête réussie
- `201 Created` : Ressource créée avec succès
- `400 Bad Request` : Données de requête invalides
- `401 Unauthorized` : Authentification requise
- `403 Forbidden` : Permissions insuffisantes
- `404 Not Found` : Ressource non trouvée
- `500 Internal Server Error` : Erreur serveur

---

## 🛡️ Sécurité

- Tous les endpoints nécessitent une authentification (sauf login)
- Les permissions sont vérifiées selon le groupe de l'utilisateur
- Protection CSRF activée pour les requêtes POST/PUT/DELETE
- Validation des données côté serveur
- Limitation de débit (rate limiting) configurable

---

## 📝 Notes importantes

- L'API retourne les données au format JSON
- Les dates sont au format ISO 8601 (YYYY-MM-DD)
- Les montants sont en euros (EUR)
- La pagination est automatique pour les listes
- Les erreurs sont retournées avec des messages explicites

---

**API REST v1.0 - Gestion Immobilière** 🚀 