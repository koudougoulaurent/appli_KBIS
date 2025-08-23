# Génération Automatique de PDF pour Contrats et Résiliations

## 🎯 Vue d'ensemble

Ce système permet de générer automatiquement des documents PDF professionnels pour les contrats de bail et les résiliations, en remplaçant la gestion manuelle des documents signés par un processus automatisé et personnalisable.

## ✨ Avantages

- **Automatisation complète** : Plus besoin de télécharger et gérer des fichiers signés
- **Personnalisation dynamique** : Les informations de l'entreprise sont récupérées depuis la base de données
- **Cohérence** : Tous les documents suivent le même format et style
- **Flexibilité** : Possibilité de personnaliser les textes via l'interface d'administration
- **Professionnalisme** : Documents PDF de qualité professionnelle au format A4

## 🚀 Fonctionnalités

### Génération de Contrats
- **PDF automatique** : Génération immédiate après création/modification
- **Informations complètes** : Contrat, propriété, locataire, conditions financières
- **Obligations personnalisables** : Textes configurables via l'administration
- **Signatures** : Sections pour bailleur, locataire et agent immobilier

### Génération de Résiliations
- **Avis de résiliation** : Document officiel avec toutes les informations
- **Conditions de sortie** : Textes personnalisables pour les procédures
- **Suivi complet** : Intégration avec le système de gestion des résiliations

## 📋 Utilisation

### 1. Création d'un Contrat

1. Remplir le formulaire de contrat (plus de champs de documents à remplir)
2. Cocher "Générer le contrat en PDF" si souhaité
3. Valider le formulaire
4. Le PDF est généré automatiquement et proposé au téléchargement

### 2. Modification d'un Contrat

1. Modifier les informations du contrat
2. Cocher "Générer le contrat en PDF" si souhaité
3. Valider les modifications
4. Nouveau PDF généré avec les informations mises à jour

### 3. Génération depuis la Page de Détail

- **Contrat** : Bouton "Générer PDF" dans la page de détail
- **Résiliation** : Bouton "Générer PDF" dans la page de détail
- **Résiliation depuis contrat** : Bouton "Générer PDF de résiliation"

## ⚙️ Configuration

### Configuration de l'Entreprise

**IMPORTANT** : La configuration se fait maintenant via la base de données, pas via des fichiers statiques !

1. Aller dans **Core > Configuration de l'entreprise**
2. Configurer les informations de base :
   - Nom de l'entreprise
   - Adresse complète
   - Coordonnées (téléphone, email, site web)
   - Informations légales (SIRET, licence, etc.)
   - Logo et couleurs de marque

3. **Personnalisation des textes** (nouveau !) :
   - **Texte personnalisé pour les contrats** : Obligations et conditions personnalisées
   - **Texte personnalisé pour les résiliations** : Conditions de sortie personnalisées

### Exemple de Configuration

```python
# Ces textes sont maintenant configurables via l'interface d'administration
# et non plus dans le code !

# Texte personnalisé pour les contrats (exemple)
"""
Obligations du locataire :
• Payer le loyer et les charges dans les délais convenus
• Entretenir les lieux loués selon nos standards
• Respecter le règlement intérieur de l'immeuble
• Ne pas effectuer de travaux sans autorisation écrite
• Assurer le logement contre tous les risques locatifs
• Respecter la destination des lieux (habitation exclusive)

Obligations du bailleur :
• Livrer le logement en parfait état d'usage
• Effectuer toutes les réparations locatives
• Respecter les obligations de sécurité et d'accessibilité
• Garantir la jouissance paisible des lieux
"""

# Texte personnalisé pour les résiliations (exemple)
"""
Conditions de sortie spécifiques :
• Le locataire doit libérer les lieux dans l'état où il les a reçus
• Un état des lieux de sortie sera effectué dans les 8 jours
• La caution sera restituée après déduction des éventuels dommages
• Les clés doivent être remises le jour de la sortie
• Nettoyage complet obligatoire avant remise des clés
"""
```

## 🏗️ Architecture Technique

### Services PDF

- **`ContratPDFService`** : Génération des contrats de bail
- **`ResiliationPDFService`** : Génération des avis de résiliation
- **Configuration dynamique** : Récupération des données depuis `ConfigurationEntreprise`

### Intégration Base de Données

```python
# Récupération automatique de la configuration
from core.models import ConfigurationEntreprise
config = ConfigurationEntreprise.get_configuration_active()

# Utilisation des informations personnalisées
nom_entreprise = config.nom_entreprise
adresse_complete = config.get_adresse_complete()
texte_contrat = config.texte_contrat  # Texte personnalisé
texte_resiliation = config.texte_resiliation  # Texte personnalisé
```

### Modèles de Données

- **`ConfigurationEntreprise`** : Informations de l'entreprise + textes personnalisés
- **`Contrat`** : Données du contrat de bail
- **`ResiliationContrat`** : Données de la résiliation

## 📁 Structure des Fichiers

```
contrats/
├── services.py          # Services de génération PDF
├── views.py            # Vues avec intégration PDF
├── forms.py            # Formulaires simplifiés (sans upload)
├── urls.py             # Routes pour génération PDF
└── config.py           # Configuration de référence (plus utilisée)

core/
├── models.py           # Modèle ConfigurationEntreprise avec nouveaux champs
└── admin.py            # Interface d'administration

templates/contrats/
└── contrat_form.html   # Formulaire simplifié avec option PDF
```

## 🔧 Installation

### 1. Dépendances

```bash
pip install -r requirements_pdf.txt
```

### 2. Migrations

```bash
python manage.py makemigrations core
python manage.py migrate
```

### 3. Configuration

1. Créer une configuration d'entreprise via l'administration
2. Personnaliser les textes des contrats et résiliations
3. Tester la génération PDF

## 🧪 Tests

### Test Automatique

```bash
python contrats/test_pdf.py
```

### Test Manuel

1. Créer un contrat via l'interface
2. Vérifier la génération du PDF
3. Modifier la configuration de l'entreprise
4. Régénérer le PDF pour vérifier les changements

## 🎨 Personnalisation Avancée

### Styles PDF

Les styles sont définis dans les services et peuvent être modifiés :

```python
# Dans ContratPDFService._setup_custom_styles()
self.styles.add(ParagraphStyle(
    name='CustomTitle',
    parent=self.styles['Title'],
    fontSize=18,
    spaceAfter=20,
    alignment=TA_CENTER,
    textColor=colors.darkblue  # Couleur personnalisable
))
```

### Mise en Page

- **Format** : A4 standard
- **Marges** : 2cm sur tous les côtés
- **Polices** : Helvetica (standard PDF)
- **Couleurs** : Configurables via la base de données

## 🔒 Sécurité et Permissions

### Contrôle d'Accès

- **Génération PDF** : Utilisateurs avec permissions PRIVILEGE, ADMINISTRATION, CONTROLES
- **Configuration** : Administrateurs uniquement
- **Consultation** : Selon les permissions existantes

### Validation des Données

- Vérification de l'existence des objets (contrat, propriété, locataire)
- Gestion des erreurs avec messages utilisateur
- Fallback sur valeurs par défaut si configuration manquante

## 📊 Statistiques et Monitoring

### Métriques Disponibles

- Nombre de PDF générés par type
- Taille des fichiers générés
- Temps de génération
- Erreurs de génération

### Logs

- Génération PDF dans les logs Django
- Erreurs et exceptions capturées
- Traçabilité des actions utilisateur

## 🚀 Évolutions Futures

### Fonctionnalités Prévues

- **Templates multiples** : Choix entre différents styles de documents
- **Signature électronique** : Intégration de signatures numériques
- **Archivage automatique** : Stockage des PDF générés
- **Notifications** : Alertes lors de la génération de documents
- **Export batch** : Génération en lot de plusieurs documents

### Améliorations Techniques

- **Cache** : Mise en cache des configurations pour améliorer les performances
- **Async** : Génération PDF en arrière-plan pour les gros volumes
- **Compression** : Optimisation de la taille des fichiers
- **Watermark** : Ajout de filigranes de sécurité

## 🆘 Dépannage

### Problèmes Courants

1. **PDF non généré** : Vérifier les permissions utilisateur
2. **Erreur de configuration** : Vérifier la configuration de l'entreprise
3. **Problème de police** : Utiliser les polices standard PDF
4. **Erreur de mémoire** : Vérifier la taille des données

### Solutions

- Vérifier les logs Django
- Tester avec `test_pdf.py`
- Réinitialiser la configuration de l'entreprise
- Vérifier les permissions utilisateur

## 📞 Support

Pour toute question ou problème :

1. Consulter les logs Django
2. Vérifier la configuration de l'entreprise
3. Tester avec le script de test
4. Consulter la documentation technique

---

**Note** : Ce système remplace complètement l'ancienne gestion manuelle des documents. Tous les PDF sont maintenant générés automatiquement avec les informations de l'entreprise configurées dans la base de données.
