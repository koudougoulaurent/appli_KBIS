# DIAGRAMME DE CAS D'UTILISATION - KBIS IMMOBILIER

## Acteurs

- **👑 Administrateur:** Gestion complète du système
- **💰 Caissier:** Gestion des paiements et reçus
- **🔍 Contrôleur:** Gestion des propriétés et contrats
- **⭐ Utilisateur Privilégié:** Accès étendu

## Modules et fonctionnalités

### 👥 Gestion des Utilisateurs
- Créer utilisateur
- Modifier utilisateur
- Supprimer utilisateur
- Gérer groupes de travail
- Assigner permissions
- Gérer niveaux d'accès

### 🏢 Gestion Immobilière
- Créer propriété
- Modifier propriété
- Supprimer propriété
- Gérer bailleurs
- Gérer locataires
- Gérer unités locatives
- Gérer types de biens
- Gérer documents
- Archivage des documents

### 📄 Gestion des Contrats
- Créer contrat
- Modifier contrat
- Résilier contrat
- Gérer quittances
- Gérer états des lieux
- Gérer cautions
- Gérer avances de loyer

### 💰 Gestion des Paiements
- Enregistrer paiement
- Générer reçu
- Gérer retraits
- Paiements partiels
- Plans de paiement
- Gérer comptes bancaires
- Charges déductibles
- Rapports financiers
- Récapitulatifs mensuels

### 🔒 Sécurité
- Surveiller sécurité
- Gérer alertes
- Audit des actions
- Monitoring en temps réel
- Contrôle d'accès
- Logs de sécurité

### 📱 Notifications
- Envoyer notifications
- Gérer alertes
- Notifications automatiques
- Historique des notifications

## Matrice des permissions

| Fonctionnalité | Admin | Caissier | Contrôleur | Privilégié |
|----------------|-------|----------|------------|------------|
| **Utilisateurs** | | | | |
| Créer utilisateur | ✅ | ❌ | ❌ | ✅ |
| Modifier utilisateur | ✅ | ❌ | ❌ | ✅ |
| Supprimer utilisateur | ✅ | ❌ | ❌ | ✅ |
| Gérer groupes | ✅ | ❌ | ❌ | ✅ |
| **Immobilier** | | | | |
| Créer propriété | ✅ | ❌ | ✅ | ✅ |
| Modifier propriété | ✅ | ❌ | ✅ | ✅ |
| Supprimer propriété | ✅ | ❌ | ❌ | ✅ |
| Gérer bailleurs | ✅ | ❌ | ✅ | ✅ |
| Gérer locataires | ✅ | ❌ | ✅ | ✅ |
| **Contrats** | | | | |
| Créer contrat | ✅ | ❌ | ✅ | ✅ |
| Modifier contrat | ✅ | ❌ | ✅ | ✅ |
| Résilier contrat | ✅ | ❌ | ❌ | ✅ |
| Gérer quittances | ✅ | ❌ | ✅ | ✅ |
| **Paiements** | | | | |
| Enregistrer paiement | ✅ | ✅ | ❌ | ✅ |
| Générer reçu | ✅ | ✅ | ❌ | ✅ |
| Gérer retraits | ✅ | ✅ | ❌ | ✅ |
| Paiements partiels | ✅ | ✅ | ❌ | ✅ |
| **Sécurité** | | | | |
| Surveiller sécurité | ✅ | ❌ | ❌ | ✅ |
| Gérer alertes | ✅ | ❌ | ❌ | ✅ |
| Audit des actions | ✅ | ❌ | ❌ | ✅ |

## Flux de travail principal

### 1. Gestion d'une propriété
1. **Création de la propriété** (Contrôleur/Privilégié)
2. **Ajout du bailleur** (Contrôleur/Privilégié)
3. **Création d'unités locatives** (si nécessaire)
4. **Ajout de locataires** (Contrôleur/Privilégié)
5. **Création de contrats** (Contrôleur/Privilégié)

### 2. Gestion des paiements
1. **Enregistrement du paiement** (Caissier/Privilégié)
2. **Génération du reçu** (automatique)
3. **Mise à jour du statut** (automatique)
4. **Notification** (automatique)

### 3. Gestion des paiements partiels
1. **Création du plan** (Caissier/Privilégié)
2. **Définition des échéances** (Caissier/Privilégié)
3. **Enregistrement des paiements** (Caissier/Privilégié)
4. **Suivi du statut** (tous les utilisateurs autorisés)

## Règles métier

### Contrats
- Un contrat ne peut être créé que pour une propriété disponible
- Un locataire ne peut avoir qu'un seul contrat actif par propriété
- Les dates de début et fin doivent être cohérentes

### Paiements
- Un paiement doit être associé à un contrat valide
- Le montant ne peut pas être négatif
- Les reçus sont générés automatiquement

### Sécurité
- Toutes les actions sont loggées
- Les tentatives d'accès non autorisé sont bloquées
- Les alertes sont envoyées en temps réel

### Notifications
- Les notifications importantes sont envoyées immédiatement
- Les utilisateurs peuvent marquer les notifications comme lues
- L'historique est conservé pour audit
