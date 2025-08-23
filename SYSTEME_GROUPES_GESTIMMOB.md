# SYSTÈME DE GROUPES DE TRAVAIL - GESTIMMOB

## 📋 Vue d'ensemble

Le système GESTIMMOB version 5.0.1 implémente un système de groupes de travail avec des permissions spécifiques pour chaque groupe. La première page que les utilisateurs voient est la page de sélection des groupes de travail, similaire à l'interface Microsoft Access montrée dans l'image de référence.

## 🏢 Groupes de Travail Disponibles

### 1. **CAISSE** 🏦
- **Description :** Gestion des paiements et retraits
- **Couleur :** Vert (#28a745)
- **Permissions :**
  - Modules : `paiements`, `retraits`
  - Actions : `read`, `write`, `validate`
  - Restrictions : `no_delete`

**Comptes de test :**
- `caisse1` / `caisse123` (Marie Dubois)
- `caisse2` / `caisse123` (Pierre Martin)

### 2. **CONTROLES** 🔍
- **Description :** Contrôle et audit des opérations
- **Couleur :** Jaune (#ffc107)
- **Permissions :**
  - Modules : `paiements`, `contrats`, `proprietes`, `utilisateurs`
  - Actions : `read`, `validate`
  - Restrictions : `no_write`, `no_delete`

**Comptes de test :**
- `controle1` / `controle123` (Sophie Bernard)
- `controle2` / `controle123` (Jean Petit)

### 3. **ADMINISTRATION** 📋
- **Description :** Gestion administrative complète
- **Couleur :** Bleu (#17a2b8)
- **Permissions :**
  - Modules : `proprietes`, `contrats`, `bailleurs`, `locataires`
  - Actions : `read`, `write`, `create`
  - Restrictions : `no_delete`

**Comptes de test :**
- `admin1` / `admin123` (Claire Moreau)
- `admin2` / `admin123` (Thomas Leroy)

### 4. **PRIVILEGE** 👑
- **Description :** Accès complet au système
- **Couleur :** Rouge (#dc3545)
- **Permissions :**
  - Modules : `paiements`, `retraits`, `proprietes`, `contrats`, `bailleurs`, `locataires`, `utilisateurs`, `groupes`
  - Actions : `read`, `write`, `create`, `delete`, `admin`
  - Restrictions : Aucune

**Comptes de test :**
- `privilege1` / `privilege123` (Marc Durand) - Superuser
- `privilege2` / `privilege123` (Isabelle Roux) - Staff

## 🎨 Interface Utilisateur

### Page de Connexion des Groupes
- **URL :** `http://127.0.0.1:8000/`
- **Design :** Interface moderne avec gradient de fond
- **Fonctionnalités :**
  - Sélection visuelle des groupes avec boutons colorés
  - Descriptions pour chaque groupe
  - Animation d'entrée fluide
  - Design responsive

### Page de Connexion par Groupe
- **URL :** `http://127.0.0.1:8000/utilisateurs/login/<groupe>/`
- **Design :** Interface spécifique à chaque groupe
- **Fonctionnalités :**
  - En-tête coloré selon le groupe
  - Formulaire de connexion sécurisé
  - Validation en temps réel
  - Bouton de retour aux groupes

### Dashboard de Groupe
- **URL :** `http://127.0.0.1:8000/utilisateurs/dashboard/<groupe>/`
- **Design :** Dashboard personnalisé par groupe
- **Fonctionnalités :**
  - Statistiques spécifiques au groupe
  - Modules accessibles
  - Actions rapides
  - Navigation intuitive

## 🔐 Système de Sécurité

### Authentification
- **Vérification du groupe :** L'utilisateur doit appartenir au groupe sélectionné
- **Statut actif :** Seuls les utilisateurs actifs peuvent se connecter
- **Sessions sécurisées :** Gestion des sessions avec groupe

### Permissions
- **Vérification des modules :** Chaque vue vérifie les permissions du groupe
- **Actions autorisées :** Contrôle des actions selon le groupe
- **Restrictions :** Limitations spécifiques par groupe

### Décorateurs de Sécurité
```python
@groupe_required  # Vérifie que l'utilisateur a un groupe
@module_required('paiements')  # Vérifie l'accès au module
@groupe_specific('CAISSE', 'PRIVILEGE')  # Vérifie le groupe spécifique
```

## 📁 Structure des Fichiers

### Modèles
```
utilisateurs/
├── models.py          # GroupeTravail, Utilisateur
├── forms.py           # Formulaires de connexion et gestion
├── views.py           # Vues de connexion et dashboard
├── urls.py            # URLs des groupes
├── admin.py           # Interface d'administration
└── decorators.py      # Décorateurs de sécurité
```

### Templates
```
templates/utilisateurs/
├── connexion_groupes.html    # Page de sélection des groupes
├── login_groupe.html         # Page de connexion par groupe
└── dashboard_groupe.html     # Dashboard de groupe
```

## 🚀 Utilisation

### 1. Démarrage
```bash
python manage.py runserver
```

### 2. Accès à l'application
- Aller sur : `http://127.0.0.1:8000/`
- Sélectionner un groupe de travail
- Se connecter avec un compte de test

### 3. Navigation
- **CAISSE :** Accès aux paiements et retraits
- **CONTROLES :** Accès en lecture seule pour audit
- **ADMINISTRATION :** Gestion des propriétés et contrats
- **PRIVILEGE :** Accès complet à tous les modules

## 🔧 Configuration

### Création de Nouveaux Groupes
```python
# Dans le shell Django
from utilisateurs.models import GroupeTravail

groupe = GroupeTravail.objects.create(
    nom='NOUVEAU_GROUPE',
    description='Description du nouveau groupe',
    permissions={
        'modules': ['module1', 'module2'],
        'actions': ['read', 'write'],
        'restrictions': []
    }
)
```

### Ajout d'Utilisateurs
```python
# Via l'admin Django ou le shell
from utilisateurs.models import Utilisateur, GroupeTravail

groupe = GroupeTravail.objects.get(nom='CAISSE')
utilisateur = Utilisateur.objects.create_user(
    username='nouveau_user',
    password='mot_de_passe',
    groupe_travail=groupe,
    first_name='Prénom',
    last_name='Nom'
)
```

## 📊 Statistiques par Groupe

### CAISSE
- Total des paiements
- Paiements du mois en cours
- Total des retraits
- Retraits en attente

### ADMINISTRATION
- Total des propriétés
- Total des bailleurs
- Total des contrats
- Contrats actifs

### CONTROLES
- Paiements à contrôler
- Contrats à vérifier
- Utilisateurs actifs

### PRIVILEGE
- Total des propriétés
- Total des utilisateurs
- Total des paiements
- Utilisateurs actifs

## 🎯 Fonctionnalités Avancées

### Actions Rapides
Chaque groupe a des actions rapides spécifiques :
- **CAISSE :** Nouveau paiement, nouveau retrait, paiements en attente
- **ADMINISTRATION :** Nouvelle propriété, nouveau contrat, nouveau bailleur
- **CONTROLES :** Contrôler paiements, vérifier contrats
- **PRIVILEGE :** Nouvel utilisateur, nouveau groupe, sauvegarde

### Modules Accessibles
- **CAISSE :** Paiements, Retraits
- **ADMINISTRATION :** Propriétés, Contrats
- **CONTROLES :** Lecture seule sur tous les modules
- **PRIVILEGE :** Tous les modules avec accès complet

## 🔄 Workflow Utilisateur

1. **Accès initial :** `http://127.0.0.1:8000/`
2. **Sélection du groupe :** Interface visuelle avec 4 boutons
3. **Connexion :** Formulaire spécifique au groupe
4. **Validation :** Vérification du groupe et des permissions
5. **Dashboard :** Interface personnalisée selon le groupe
6. **Navigation :** Accès aux modules autorisés uniquement

## 🛠️ Maintenance

### Sauvegarde des Groupes
```bash
python manage.py dumpdata utilisateurs.GroupeTravail > groupes_backup.json
```

### Restauration des Groupes
```bash
python manage.py loaddata groupes_backup.json
```

### Réinitialisation des Comptes
```bash
python init_groupes_et_comptes.py
```

## 📝 Notes Importantes

1. **Sécurité :** Chaque utilisateur ne peut accéder qu'à son groupe assigné
2. **Permissions :** Les permissions sont stockées en JSON pour la flexibilité
3. **Interface :** Design cohérent avec l'image de référence GESTIMMOB
4. **Responsive :** Interface adaptée aux différents écrans
5. **Audit :** Traçabilité complète des connexions et actions

## 🎉 Conclusion

Le système de groupes de travail GESTIMMOB offre :
- ✅ **Sécurité renforcée** avec permissions par groupe
- ✅ **Interface intuitive** similaire à l'image de référence
- ✅ **Flexibilité** pour ajouter de nouveaux groupes
- ✅ **Traçabilité** complète des actions
- ✅ **Design moderne** et responsive

L'application est maintenant prête pour la production avec un système de groupes fonctionnel et sécurisé ! 