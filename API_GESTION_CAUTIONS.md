# API Gestion des Cautions et Avances

## Vue d'ensemble

Cette documentation décrit les endpoints API pour la gestion des cautions et avances de loyer dans l'application immobilière. Ces endpoints permettent de :

- Consulter l'état des cautions et avances
- Marquer les cautions et avances comme payées
- Obtenir des statistiques détaillées
- Gérer les paiements de caution et avance

## Endpoints disponibles

### 1. Gestion des Cautions (Module Contrats)

#### Base URL : `/contrats/api/cautions/`

**GET** `/contrats/api/cautions/`
- **Description** : Liste des contrats avec leurs cautions et avances
- **Paramètres de filtrage** :
  - `statut_caution` : `payee`, `non_payee`
  - `statut_avance` : `payee`, `non_payee`
  - `propriete__ville` : Ville de la propriété
  - `propriete__bailleur` : ID du bailleur
- **Réponse** : Liste paginée des contrats avec détails des cautions

**GET** `/contrats/api/cautions/statistiques/`
- **Description** : Statistiques globales des cautions et avances
- **Réponse** : Totaux, montants, compteurs par statut

**POST** `/contrats/api/cautions/{id}/marquer_caution_payee/`
- **Description** : Marquer la caution d'un contrat comme payée
- **Réponse** : Confirmation et détails du contrat mis à jour

**POST** `/contrats/api/cautions/{id}/marquer_avance_payee/`
- **Description** : Marquer l'avance de loyer d'un contrat comme payée
- **Réponse** : Confirmation et détails du contrat mis à jour

**GET** `/contrats/api/cautions/{id}/recu_caution/`
- **Description** : Obtenir les informations du reçu de caution
- **Réponse** : Détails du reçu de caution

### 2. Paiements de Caution et Avance (Module Paiements)

#### Base URL : `/paiements/api/cautions-avances/`

**GET** `/paiements/api/cautions-avances/`
- **Description** : Liste des paiements de caution et avance
- **Paramètres de filtrage** :
  - `type_paiement` : `caution`, `avance_loyer`, `depot_garantie`, `caution_avance`
  - `statut` : `en_attente`, `valide`, `refuse`
  - `date_paiement` : Filtres de date
  - `contrat` : ID du contrat
- **Réponse** : Liste paginée des paiements

**GET** `/paiements/api/cautions-avances/statistiques/`
- **Description** : Statistiques des paiements de caution et avance
- **Réponse** : Statistiques par type, statut, mois et propriétaire

**GET** `/paiements/api/cautions-avances/cautions_en_attente/`
- **Description** : Contrats avec cautions en attente de paiement
- **Réponse** : Liste des contrats et montants en attente

**GET** `/paiements/api/cautions-avances/avances_en_attente/`
- **Description** : Contrats avec avances de loyer en attente
- **Réponse** : Liste des contrats et montants en attente

**POST** `/paiements/api/cautions-avances/{id}/valider_caution_avance/`
- **Description** : Valider un paiement de caution ou avance
- **Réponse** : Confirmation et mise à jour du contrat

### 3. API Unifiée (Module Core)

#### Base URL : `/core/api/cautions/`

**GET** `/core/api/cautions/`
- **Description** : Endpoint unifié pour la gestion des cautions
- **Paramètres de filtrage** :
  - `statut_caution` : `payee`, `non_payee`
  - `statut_avance` : `payee`, `non_payee`
  - `proprietaire` : Nom du propriétaire (recherche partielle)
  - `ville` : Ville de la propriété (recherche partielle)
- **Réponse** : Données complètes avec statistiques et contrats

**POST** `/core/api/cautions/{contrat_id}/marquer-caution/`
- **Description** : Marquer la caution comme payée (API unifiée)
- **Réponse** : Confirmation et détails du contrat

**POST** `/core/api/cautions/{contrat_id}/marquer-avance/`
- **Description** : Marquer l'avance comme payée (API unifiée)
- **Réponse** : Confirmation et détails du contrat

## Exemples d'utilisation

### 1. Consulter toutes les cautions en attente

```bash
GET /contrats/api/cautions/?statut_caution=non_payee
```

**Réponse :**
```json
{
  "count": 5,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "numero_contrat": "CON-2024-001",
      "locataire": {
        "nom": "Dupont",
        "prenom": "Jean"
      },
      "propriete": {
        "titre": "Appartement T3",
        "ville": "Paris"
      },
      "caution_montant": 1500.00,
      "avance_montant": 800.00,
      "caution_payee": false,
      "avance_payee": false
    }
  ]
}
```

### 2. Obtenir les statistiques des cautions

```bash
GET /contrats/api/cautions/statistiques/
```

**Réponse :**
```json
{
  "cautions": {
    "total_requises": 25,
    "total_payees": 20,
    "total_en_attente": 5,
    "montant_paye": 30000.00,
    "montant_en_attente": 7500.00
  },
  "avances": {
    "total_requises": 15,
    "total_payees": 12,
    "total_en_attente": 3,
    "montant_paye": 12000.00,
    "montant_en_attente": 2400.00
  },
  "total_contrats": 25
}
```

### 3. Marquer une caution comme payée

```bash
POST /contrats/api/cautions/1/marquer_caution_payee/
```

**Réponse :**
```json
{
  "message": "Caution marquée comme payée avec succès.",
  "contrat": {
    "id": 1,
    "numero_contrat": "CON-2024-001",
    "caution_payee": true,
    "date_paiement_caution": "2024-01-15"
  }
}
```

### 4. Consulter les paiements de caution

```bash
GET /paiements/api/cautions-avances/?type_paiement=caution
```

**Réponse :**
```json
{
  "count": 8,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "reference_paiement": "PAY-20240115-ABC123",
      "montant": 1500.00,
      "type_paiement": "caution",
      "statut": "valide",
      "date_paiement": "2024-01-15",
      "contrat": {
        "numero_contrat": "CON-2024-001",
        "locataire": "Jean Dupont",
        "propriete": "Appartement T3"
      }
    }
  ]
}
```

## Authentification

Tous les endpoints nécessitent une authentification. Utilisez l'en-tête d'autorisation :

```
Authorization: Token <votre_token>
```

ou

```
Authorization: Basic <base64_username_password>
```

## Codes de statut HTTP

- **200** : Succès
- **201** : Créé avec succès
- **400** : Erreur de validation
- **401** : Non authentifié
- **403** : Non autorisé
- **404** : Ressource non trouvée
- **500** : Erreur serveur

## Filtres et recherche

### Filtres de base
- `statut_caution` : Statut de la caution
- `statut_avance` : Statut de l'avance
- `type_paiement` : Type de paiement
- `date_paiement` : Date de paiement
- `montant` : Montant du paiement

### Recherche textuelle
- Numéro de contrat
- Nom et prénom du locataire
- Titre de la propriété
- Ville de la propriété
- Nom du propriétaire

### Tri
- `ordering` : Champs de tri disponibles
- Tri par défaut : Date de création décroissante

## Pagination

Tous les endpoints de liste supportent la pagination avec les paramètres :
- `page` : Numéro de page
- `page_size` : Taille de page (défaut : 20)

## Gestion des erreurs

Les erreurs sont retournées au format JSON avec :
- `error` : Message d'erreur
- `detail` : Détails supplémentaires (si applicable)
- `code` : Code d'erreur (si applicable)

## Notes importantes

1. **Synchronisation** : Les actions sur les cautions mettent automatiquement à jour les contrats correspondants
2. **Validation** : Seuls les paiements validés sont pris en compte dans les statistiques
3. **Sécurité** : Toutes les opérations sont tracées dans les logs d'audit
4. **Performance** : Les requêtes utilisent des optimisations (select_related, prefetch_related)

## Support

Pour toute question ou problème avec ces endpoints API, consultez la documentation technique ou contactez l'équipe de développement.
