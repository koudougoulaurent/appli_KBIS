# 👥 Utilisateurs de Test pour Render

## 🔑 Informations de Connexion

**Mot de passe pour tous les utilisateurs :** `password123`

## 📋 Groupes de Travail

### 1. CAISSE
- **Description :** Gestion des paiements et retraits
- **Permissions :** Voir, créer, modifier, valider les paiements et retraits
- **Restrictions :** Pas de suppression

### 2. CONTROLES  
- **Description :** Contrôle et audit des opérations
- **Permissions :** Voir, auditer, rapporter sur tous les modules
- **Restrictions :** Lecture seule

### 3. ADMINISTRATION
- **Description :** Gestion administrative complète
- **Permissions :** Voir, créer, modifier, supprimer (sauf superuser)
- **Restrictions :** Pas d'accès superuser

### 4. PRIVILEGE
- **Description :** Accès complet à toutes les fonctionnalités
- **Permissions :** Tous les modules et actions
- **Restrictions :** Aucune

## 👤 Utilisateurs Créés

### 🔴 Super Administrateurs
| Utilisateur | Nom | Poste | Groupe | Email |
|-------------|-----|-------|--------|-------|
| `admin` | Super Administrateur | Super Administrateur | PRIVILEGE | admin@gestimmob.com |
| `directeur` | Directeur Général | Directeur Général | PRIVILEGE | directeur@gestimmob.com |

### 🟡 Managers et Privilégiés
| Utilisateur | Nom | Poste | Groupe | Email |
|-------------|-----|-------|--------|-------|
| `privilege1` | Alice Manager | Manager | PRIVILEGE | privilege1@gestimmob.com |
| `demo` | Démo Utilisateur | Utilisateur Démo | PRIVILEGE | demo@gestimmob.com |

### 🟢 Administration
| Utilisateur | Nom | Poste | Groupe | Email |
|-------------|-----|-------|--------|-------|
| `admin1` | Claire Administratrice | Administratrice | ADMINISTRATION | admin1@gestimmob.com |
| `gestion1` | Paul Gestionnaire | Gestionnaire | ADMINISTRATION | gestion1@gestimmob.com |

### 🔵 Caisse
| Utilisateur | Nom | Poste | Groupe | Email |
|-------------|-----|-------|--------|-------|
| `caisse1` | Marie Caissière | Caissière | CAISSE | caisse1@gestimmob.com |
| `caisse2` | Fatou Traoré | Agent de caisse | CAISSE | caisse2@gestimmob.com |

### 🟠 Contrôles
| Utilisateur | Nom | Poste | Groupe | Email |
|-------------|-----|-------|--------|-------|
| `controle1` | Sophie Contrôleuse | Contrôleuse | CONTROLES | controle1@gestimmob.com |
| `audit1` | Jean Auditeur | Auditeur | CONTROLES | audit1@gestimmob.com |

## 🏠 Types de Biens Disponibles

### Résidentiel
- Appartement, Maison, Studio, Duplex, Penthouse
- Villa, Château, Ferme, Loft
- T3, T4, T5+, Chambre, Colocation
- Résidence, Hôtel

### Commercial
- Bureau, Commerce, Entrepôt, Garage
- Cave, Terrain, Parking, Box

### Spécialisé
- Restaurant, Autre

## 🚀 Utilisation sur Render

1. **Accédez à l'application** via l'URL Render
2. **Connectez-vous** avec n'importe quel utilisateur ci-dessus
3. **Mot de passe :** `password123`
4. **Testez les différentes fonctionnalités** selon le groupe de l'utilisateur

## 📞 Contacts de Test

Tous les utilisateurs ont des numéros de téléphone de test :
- Format : `+225 07 00 00 00 XX`
- Où XX est un numéro unique pour chaque utilisateur

## 🔧 Maintenance

Les données sont créées automatiquement au démarrage de l'application sur Render via le script `verifier_donnees_automatique.py`.

Pour recréer les données, redéployez l'application ou exécutez le script manuellement.
