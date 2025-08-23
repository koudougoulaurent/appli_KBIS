# 🎨 GUIDE COMPLET - PERSONNALISATION DES REÇUS

## 📋 Vue d'ensemble

Le système de personnalisation des reçus est **entièrement opérationnel** et permet de modifier et personnaliser les reçus avec les informations et le logo de votre entreprise.

## ✅ Fonctionnalités disponibles

### 🏢 **Configuration de l'entreprise**
- **Nom et identité** : Nom officiel et commercial
- **Logo** : Upload et affichage sur les reçus
- **Informations de contact** : Adresse, téléphone, email, site web
- **Informations légales** : SIRET, TVA, RCS
- **Informations bancaires** : Banque, IBAN, BIC
- **Personnalisation visuelle** : Couleurs, polices
- **Options d'affichage** : Choix des éléments à afficher

### 📄 **Templates de reçus**
- **4 templates prêts** : Standard, Professionnel, Simplifié, Luxe
- **Création de nouveaux templates** : Interface intuitive
- **Modification des templates** : Couleurs, polices, options
- **Test des templates** : Aperçu et génération PDF
- **Template par défaut** : Définition automatique

### 🖨️ **Génération PDF personnalisée**
- **Logo de l'entreprise** : Affiché en haut du reçu
- **Couleurs personnalisées** : Principale et secondaire
- **Polices personnalisées** : Mappées vers ReportLab
- **Informations conditionnelles** : SIRET, TVA, IBAN selon configuration
- **Pied de page personnalisé** : Texte libre
- **Conditions générales** : Texte personnalisable

## 🚀 Comment utiliser le système

### 1. **Accéder à la configuration**
```
URL : http://localhost:8000/core/configuration/
```
- Connectez-vous en tant qu'administrateur
- Accédez à la page de configuration
- Modifiez les informations de votre entreprise

### 2. **Personnaliser l'identité visuelle**
- **Logo** : Uploadez votre logo (PNG, JPG, SVG recommandé)
- **Couleurs** : Choisissez vos couleurs principales et secondaires
- **Polices** : Sélectionnez vos polices préférées
- **Options d'affichage** : Activez/désactivez les éléments

### 3. **Gérer les templates**
```
URL : http://localhost:8000/core/templates/
```
- **Voir les templates existants**
- **Créer un nouveau template**
- **Modifier un template existant**
- **Tester un template** avec génération PDF
- **Définir un template par défaut**

### 4. **Générer des reçus personnalisés**
- Les reçus existants utilisent automatiquement la configuration
- Nouveaux reçus générés avec la personnalisation
- PDF téléchargeables avec l'identité visuelle

## 🎯 Exemples de personnalisation

### **Configuration actuelle**
- **Entreprise** : GESTIMMOB - Gestion Immobilière
- **Couleurs** : #2c3e50 (principal) / #f39c12 (secondaire)
- **Police** : Helvetica
- **Logo** : Affiché ✅
- **SIRET** : Affiché ✅
- **TVA** : Affichée ✅
- **IBAN** : Masqué ❌

### **Templates disponibles**
1. **Standard** ⭐ (par défaut) - Professionnel complet
2. **Professionnel** - Design élégant moderne
3. **Simplifié** - Version épurée essentielle
4. **Luxe** - Template premium sophistiqué

## 📊 Tests effectués

### ✅ **Tests de validation**
- Configuration entreprise : **OK**
- Templates de reçus : **OK**
- Génération PDF : **OK**
- Modification de configuration : **OK**
- Templates personnalisés : **OK**

### 📁 **Fichiers PDF générés**
- `test_recu_personnalise_REC-20250720-47424.pdf`
- `test_recu_modifie_REC-20250720-47424.pdf`
- `test_template_Standard_REC-20250720-47424.pdf`
- `test_template_Luxe_REC-20250720-47424.pdf`
- `test_template_Professionnel_REC-20250720-47424.pdf`
- `test_template_Simplifié_REC-20250720-47424.pdf`

## 🔧 Fonctionnalités avancées

### **Modification en temps réel**
- Changement de configuration immédiat
- Aperçu des modifications
- Test des templates
- Génération PDF de test

### **Gestion des templates**
- Upload de fichiers HTML personnalisés
- Personnalisation des couleurs par template
- Options d'affichage spécifiques
- Versioning des templates

### **Intégration complète**
- Utilisation automatique de la configuration
- Génération PDF avec ReportLab
- Fallback vers WeasyPrint si nécessaire
- Validation des données

## 🌐 URLs importantes

### **Configuration**
- **Configuration entreprise** : `/core/configuration/`
- **Gestion templates** : `/core/templates/`
- **Aperçu template** : `/core/templates/<id>/apercu/`
- **Test template** : `/core/templates/<id>/test/`

### **API**
- **Configuration** : `/core/api/configuration/`
- **Sauvegarde** : `/core/api/configuration/sauvegarder/`

## 📈 Avantages

### **Pour l'entreprise**
- **Identité visuelle cohérente** sur tous les reçus
- **Professionnalisme** avec logo et informations complètes
- **Conformité légale** avec SIRET/TVA
- **Flexibilité** pour adapter selon les besoins

### **Pour les utilisateurs**
- **Interface intuitive** de configuration
- **Aperçu en temps réel** des modifications
- **Gestion simple** des templates
- **Tests automatiques** de la personnalisation

## 🎉 Conclusion

Le système de personnalisation des reçus est **entièrement fonctionnel** et permet de :

✅ **Modifier les informations de l'entreprise**  
✅ **Ajouter et personnaliser le logo**  
✅ **Choisir les couleurs et polices**  
✅ **Gérer les informations légales**  
✅ **Créer des templates personnalisés**  
✅ **Générer des PDF personnalisés**  

**Le système est prêt à être utilisé !** 🚀 