# Configuration Git pour ProjetImo

Ce guide explique comment configurer Git et pousser le projet sur une plateforme de gestion de versions comme GitHub, GitLab ou Bitbucket.

## Configuration initiale Git

### 1. Configuration de l'utilisateur
```bash
# Configurer votre nom et email
git config --global user.name "Votre Nom"
git config --global user.email "votre.email@example.com"

# Vérifier la configuration
git config --list
```

### 2. Configuration des fins de ligne (Windows)
```bash
# Configurer Git pour gérer automatiquement les fins de ligne
git config --global core.autocrlf true

# Ou pour forcer LF sur tous les fichiers
git config --global core.eol lf
```

## Configuration du remote

### Option 1 : GitHub

#### Créer un repository sur GitHub
1. Aller sur [GitHub](https://github.com)
2. Cliquer sur "New repository"
3. Nommer le repository : `projetimo`
4. Description : "Application Django de gestion immobilière"
5. Choisir "Public" ou "Private"
6. **NE PAS** initialiser avec README, .gitignore ou licence
7. Cliquer sur "Create repository"

#### Ajouter le remote
```bash
# Ajouter le remote origin
git remote add origin https://github.com/votre-username/projetimo.git

# Vérifier le remote
git remote -v

# Pousser le code
git push -u origin master
```

### Option 2 : GitLab

#### Créer un projet sur GitLab
1. Aller sur [GitLab](https://gitlab.com)
2. Cliquer sur "New project"
3. Choisir "Create blank project"
4. Nommer le projet : `projetimo`
5. Choisir la visibilité
6. Cliquer sur "Create project"

#### Ajouter le remote
```bash
# Ajouter le remote origin
git remote add origin https://gitlab.com/votre-username/projetimo.git

# Vérifier le remote
git remote -v

# Pousser le code
git push -u origin master
```

### Option 3 : Bitbucket

#### Créer un repository sur Bitbucket
1. Aller sur [Bitbucket](https://bitbucket.org)
2. Cliquer sur "Create repository"
3. Nommer le repository : `projetimo`
4. Choisir la visibilité
5. Cliquer sur "Create repository"

#### Ajouter le remote
```bash
# Ajouter le remote origin
git remote add origin https://bitbucket.org/votre-username/projetimo.git

# Vérifier le remote
git remote -v

# Pousser le code
git push -u origin master
```

## Authentification

### Option 1 : Token d'accès personnel (recommandé)

#### GitHub
1. Aller dans Settings > Developer settings > Personal access tokens
2. Cliquer sur "Generate new token"
3. Sélectionner les scopes : `repo`, `workflow`
4. Copier le token généré
5. Utiliser le token comme mot de passe

#### GitLab
1. Aller dans User Settings > Access Tokens
2. Créer un token avec les scopes : `read_repository`, `write_repository`
3. Copier le token généré

#### Bitbucket
1. Aller dans Personal settings > App passwords
2. Créer un mot de passe d'application
3. Sélectionner les permissions : `Repositories: Read, Write`

### Option 2 : Clé SSH

#### Générer une clé SSH
```bash
# Générer une nouvelle clé SSH
ssh-keygen -t ed25519 -C "votre.email@example.com"

# Démarrer l'agent SSH
eval "$(ssh-agent -s)"

# Ajouter la clé à l'agent
ssh-add ~/.ssh/id_ed25519

# Afficher la clé publique
cat ~/.ssh/id_ed25519.pub
```

#### Ajouter la clé sur la plateforme
1. Copier le contenu de la clé publique
2. L'ajouter dans les paramètres SSH de votre plateforme
3. Tester la connexion SSH

## Première poussée

### Pousser le code initial
```bash
# Vérifier le statut
git status

# Vérifier les remotes
git remote -v

# Pousser vers le remote
git push -u origin master

# Vérifier que tout est bien poussé
git log --oneline --all --graph
```

### Vérification
1. Aller sur votre plateforme (GitHub/GitLab/Bitbucket)
2. Vérifier que tous les fichiers sont présents
3. Vérifier que l'historique des commits est visible

## Workflow de développement

### Branches de développement
```bash
# Créer une branche pour une nouvelle fonctionnalité
git checkout -b feature/nouvelle-fonctionnalite

# Travailler sur la fonctionnalité
# ... faire des modifications ...

# Commiter les changements
git add .
git commit -m "Ajout de la nouvelle fonctionnalité"

# Pousser la branche
git push origin feature/nouvelle-fonctionnalite

# Créer une Pull Request/Merge Request
```

### Branches de correction
```bash
# Créer une branche pour corriger un bug
git checkout -b hotfix/correction-bug

# Corriger le bug
# ... faire des corrections ...

# Commiter les corrections
git add .
git commit -m "Correction du bug critique"

# Pousser la branche
git push origin hotfix/correction-bug
```

## Commandes Git utiles

### Vérification
```bash
# Statut du repository
git status

# Historique des commits
git log --oneline

# Branches
git branch -a

# Remotes
git remote -v
```

### Gestion des branches
```bash
# Créer et changer de branche
git checkout -b nom-de-la-branche

# Changer de branche
git checkout nom-de-la-branche

# Supprimer une branche locale
git branch -d nom-de-la-branche

# Supprimer une branche distante
git push origin --delete nom-de-la-branche
```

### Synchronisation
```bash
# Récupérer les dernières modifications
git fetch origin

# Mettre à jour la branche locale
git pull origin master

# Pousser les modifications
git push origin master
```

## Gestion des conflits

### Résolution de conflits
```bash
# En cas de conflit lors d'un merge
git status

# Éditer les fichiers en conflit
# ... résoudre les conflits ...

# Ajouter les fichiers résolus
git add .

# Finaliser le merge
git commit -m "Résolution des conflits de merge"
```

## Sauvegarde et restauration

### Sauvegarde locale
```bash
# Créer une archive du projet
git archive --format=zip --output=projetimo-backup.zip master

# Ou avec tar
git archive --format=tar --output=projetimo-backup.tar master
```

### Restauration
```bash
# Cloner depuis le remote
git clone https://github.com/votre-username/projetimo.git

# Ou restaurer depuis une archive
tar -xf projetimo-backup.tar
cd projetimo
git init
git add .
git commit -m "Restauration depuis sauvegarde"
```

## Bonnes pratiques

### Messages de commit
- Utiliser des messages clairs et descriptifs
- Commencer par un verbe à l'impératif
- Limiter la première ligne à 50 caractères
- Ajouter des détails si nécessaire

### Exemples de messages
```
feat: Ajout de la gestion des cautions
fix: Correction du bug d'affichage des montants
docs: Mise à jour de la documentation
style: Amélioration du formatage du code
refactor: Refactorisation du système de permissions
test: Ajout de tests pour la validation des formulaires
```

### Fréquence des commits
- Commiter régulièrement (après chaque fonctionnalité)
- Éviter les commits trop volumineux
- Tester avant de commiter
- Utiliser des branches pour les fonctionnalités

## Dépannage

### Problèmes courants
1. **Erreur d'authentification** : Vérifier le token ou la clé SSH
2. **Conflit de merge** : Résoudre manuellement les conflits
3. **Push rejeté** : Faire un pull avant de pousser
4. **Fichiers non trackés** : Vérifier le .gitignore

### Commandes de récupération
```bash
# Annuler le dernier commit
git reset --soft HEAD~1

# Annuler les modifications non commitées
git checkout -- .

# Voir l'historique des actions
git reflog

# Restaurer un commit spécifique
git checkout <hash-du-commit>
```

## Conclusion

Ce guide couvre la configuration complète de Git pour ProjetImo. Une fois configuré, vous pourrez :

- Collaborer avec d'autres développeurs
- Suivre l'historique des modifications
- Gérer les versions de votre application
- Déployer facilement sur d'autres machines
- Maintenir un code source organisé et sécurisé

Pour toute question sur Git, consultez la [documentation officielle](https://git-scm.com/doc) ou les ressources de votre plateforme de gestion de versions.
