# 🎨 PERSONNALISATION DES REÇUS - CONFIGURATION ENTREPRISE

## 📋 Vue d'ensemble

Le système de gestion immobilière a été enrichi d'un module complet de personnalisation des reçus permettant aux entreprises de :

- ✅ **Personnaliser leur identité visuelle** sur tous les reçus
- ✅ **Ajouter leur logo** et informations de contact
- ✅ **Choisir leurs couleurs** et polices préférées
- ✅ **Gérer leurs informations légales** (SIRET, TVA, RCS)
- ✅ **Créer des templates personnalisés** pour différents usages
- ✅ **Modifier et adapter** les reçus selon leurs besoins

## 🏢 Configuration de l'entreprise

### **Modèle ConfigurationEntreprise**

Le nouveau modèle `ConfigurationEntreprise` permet de stocker toutes les informations de l'entreprise :

```python
class ConfigurationEntreprise(models.Model):
    # Informations de base
    nom_entreprise = models.CharField(max_length=200)
    nom_commercial = models.CharField(max_length=200, blank=True)
    logo = models.ImageField(upload_to='logos/', null=True, blank=True)
    
    # Informations de contact
    adresse = models.TextField()
    telephone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    site_web = models.URLField(blank=True)
    
    # Informations légales
    siret = models.CharField(max_length=14, blank=True)
    tva_intra = models.CharField(max_length=20, blank=True)
    rcs = models.CharField(max_length=50, blank=True)
    
    # Informations bancaires
    banque = models.CharField(max_length=100, blank=True)
    iban = models.CharField(max_length=34, blank=True)
    bic = models.CharField(max_length=11, blank=True)
    
    # Personnalisation visuelle
    couleur_principale = models.CharField(max_length=7, default='#2c3e50')
    couleur_secondaire = models.CharField(max_length=7, default='#3498db')
    police_principale = models.CharField(max_length=50, default='Arial')
    police_titre = models.CharField(max_length=50, default='Arial')
    
    # Options d'affichage
    afficher_logo = models.BooleanField(default=True)
    afficher_siret = models.BooleanField(default=True)
    afficher_tva = models.BooleanField(default=True)
    afficher_iban = models.BooleanField(default=False)
    
    # Textes personnalisés
    pied_page = models.TextField(blank=True)
    conditions_generales = models.TextField(blank=True)
```

### **Fonctionnalités de configuration**

- **Gestion automatique** : Une configuration par défaut est créée automatiquement
- **Validation des couleurs** : Vérification du format hexadécimal
- **Méthodes utilitaires** : `get_nom_display()`, `get_logo_url()`, etc.
- **Informations formatées** : Contact, légales, bancaires

## 📄 Templates de reçus

### **Modèle TemplateRecu**

Le modèle `TemplateRecu` permet de créer des modèles personnalisés :

```python
class TemplateRecu(models.Model):
    nom = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    fichier_template = models.FileField(upload_to='templates_recus/')
    
    # Personnalisation
    couleur_principale = models.CharField(max_length=7, default='#2c3e50')
    couleur_secondaire = models.CharField(max_length=7, default='#3498db')
    police_principale = models.CharField(max_length=50, default='Arial')
    
    # Options d'affichage
    afficher_logo = models.BooleanField(default=True)
    afficher_siret = models.BooleanField(default=True)
    afficher_tva = models.BooleanField(default=True)
    afficher_iban = models.BooleanField(default=False)
    
    # Gestion
    actif = models.BooleanField(default=True)
    par_defaut = models.BooleanField(default=False)
```

### **Templates par défaut créés**

1. **Standard** - Template professionnel avec toutes les informations
2. **Professionnel** - Design élégant avec couleurs modernes
3. **Simplifié** - Version épurée avec informations essentielles
4. **Luxe** - Template premium avec design sophistiqué

## 🎨 Interface de configuration

### **Page de configuration** (`/core/configuration/`)

Interface complète pour gérer la configuration de l'entreprise :

- **Informations de base** : Nom, adresse, contact
- **Logo** : Upload et prévisualisation
- **Informations légales** : SIRET, TVA, RCS
- **Informations bancaires** : Banque, IBAN, BIC
- **Personnalisation** : Couleurs, polices
- **Options d'affichage** : Choix des éléments à afficher
- **Textes personnalisés** : Pied de page, conditions générales

### **Gestion des templates** (`/core/templates/`)

Interface pour gérer les templates de reçus :

- **Liste des templates** avec aperçu
- **Création de nouveaux templates**
- **Modification des templates existants**
- **Test des templates** avec génération PDF
- **Définition du template par défaut**

## 🖨️ Génération PDF personnalisée

### **Fonction `generer_pdf_reportlab()` améliorée**

La fonction de génération PDF a été complètement refactorisée pour utiliser la configuration :

```python
def generer_pdf_reportlab(recu, config=None, template=None):
    # Récupération de la configuration
    if config is None:
        config = ConfigurationEntreprise.get_configuration_active()
    
    # Styles personnalisés
    title_style = ParagraphStyle(
        'CustomTitle',
        fontSize=18,
        textColor=colors.HexColor(config.couleur_principale),
        fontName=get_reportlab_font(config.police_titre)
    )
    
    # En-tête avec logo
    if config.afficher_logo and config.logo:
        logo = Image(config.logo.path, width=2*inch, height=1*inch)
        story.append(logo)
    
    # Informations de l'entreprise
    story.append(Paragraph(config.get_nom_display(), title_style))
    
    # Informations légales conditionnelles
    if config.afficher_siret and config.siret:
        legal_info.append(f"SIRET: {config.siret}")
    
    # Couleurs personnalisées dans les tableaux
    paiement_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 0), colors.HexColor(config.couleur_principale)),
        ('FONTNAME', (0, 0), (-1, -1), get_reportlab_font(config.police_principale)),
    ]))
```

### **Éléments personnalisables**

- **Logo de l'entreprise** : Affiché en haut du reçu
- **Couleurs** : Principale et secondaire pour les titres et tableaux
- **Polices** : Principale et titres (mappées vers les polices ReportLab)
- **Informations légales** : SIRET, TVA, RCS (affichage conditionnel)
- **Informations bancaires** : IBAN, BIC (affichage conditionnel)
- **Pied de page** : Texte personnalisé
- **Conditions générales** : Texte personnalisé

## 🔧 Fonctionnalités avancées

### **API de configuration**

```python
# Récupération de la configuration
GET /core/api/configuration/

# Sauvegarde de la configuration
POST /core/api/configuration/sauvegarder/
```

### **Gestion des polices**

Mapping automatique des polices personnalisées vers les polices ReportLab :

```python
def get_reportlab_font(font_name):
    font_mapping = {
        'Arial': 'Helvetica',
        'Helvetica': 'Helvetica',
        'Times New Roman': 'Times-Roman',
        'Georgia': 'Times-Roman',
        'Verdana': 'Helvetica'
    }
    return font_mapping.get(font_name, 'Helvetica')
```

### **Validation et sécurité**

- **Validation des couleurs** : Format hexadécimal requis
- **Validation des fichiers** : Types d'images autorisés
- **Gestion des erreurs** : Fallback vers la configuration par défaut
- **Permissions** : Accès administrateur requis

## 📊 Tests et validation

### **Script de test complet**

Le script `test_personnalisation_recus.py` valide toutes les fonctionnalités :

- ✅ Configuration de l'entreprise
- ✅ Templates de reçus
- ✅ Génération PDF personnalisée
- ✅ Modification de configuration
- ✅ Templates personnalisés

### **Résultats des tests**

```
🎯 TEST COMPLET DE LA PERSONNALISATION DES REÇUS
================================================================================
✅ Configuration entreprise : OK
✅ Templates : OK
✅ Génération PDF : OK
✅ Modification config : OK
✅ Templates personnalisés : OK

🎉 PERSONNALISATION DES REÇUS OPÉRATIONNELLE !
```

## 🚀 Utilisation

### **Configuration initiale**

1. **Exécuter le script d'initialisation** :
   ```bash
   python initialiser_configuration_entreprise.py
   ```

2. **Accéder à la configuration** :
   ```
   http://localhost:8000/core/configuration/
   ```

3. **Personnaliser les informations** :
   - Logo de l'entreprise
   - Couleurs et polices
   - Informations légales
   - Textes personnalisés

### **Gestion des templates**

1. **Accéder à la gestion des templates** :
   ```
   http://localhost:8000/core/templates/
   ```

2. **Créer un nouveau template** :
   - Nom et description
   - Fichier HTML du template
   - Couleurs et polices
   - Options d'affichage

3. **Tester les templates** :
   - Aperçu en temps réel
   - Génération PDF de test
   - Définition comme template par défaut

### **Génération de reçus personnalisés**

Les reçus générés automatiquement utilisent maintenant :

- La configuration active de l'entreprise
- Le template par défaut (ou spécifié)
- Les couleurs et polices personnalisées
- Le logo et informations de l'entreprise

## 📈 Avantages

### **Pour l'entreprise**

- **Identité visuelle cohérente** sur tous les documents
- **Professionnalisme** avec logo et informations complètes
- **Flexibilité** pour adapter les reçus selon les besoins
- **Conformité légale** avec informations SIRET/TVA
- **Personnalisation** des couleurs et polices

### **Pour les utilisateurs**

- **Interface intuitive** de configuration
- **Aperçu en temps réel** des modifications
- **Gestion des templates** simple et efficace
- **Tests automatiques** de la personnalisation
- **Génération PDF** fiable et rapide

### **Pour le système**

- **Architecture modulaire** et extensible
- **Validation robuste** des données
- **Gestion d'erreurs** complète
- **Performance optimisée** avec cache
- **Sécurité** avec permissions appropriées

## 🔮 Évolutions futures

### **Fonctionnalités prévues**

- **Templates HTML avancés** avec variables dynamiques
- **Prévisualisation en temps réel** des modifications
- **Import/Export** de configurations
- **Historique des modifications** de configuration
- **Templates par type de paiement** (loyer, charges, etc.)
- **Signature électronique** sur les reçus
- **Archivage automatique** des reçus générés

### **Améliorations techniques**

- **Cache Redis** pour les configurations
- **Génération asynchrone** des PDF
- **API REST complète** pour l'intégration
- **Webhooks** pour notifications
- **Monitoring** des performances

---

*Document généré le 20 juillet 2025 - Version 1.0*

**🎉 Le système de personnalisation des reçus est maintenant opérationnel et permet aux entreprises de créer des reçus professionnels et personnalisés selon leurs besoins !** 