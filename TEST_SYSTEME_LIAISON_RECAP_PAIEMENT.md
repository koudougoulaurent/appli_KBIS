# Guide de Test - Système de Liaison Récapitulatif → Paiement

## 🧪 **Comment Tester le Système**

### **Prérequis**
1. **Migration** : Exécuter la migration pour ajouter le champ `recap_lie`
2. **Données** : Avoir au moins un récapitulatif mensuel validé
3. **Permissions** : Être connecté avec un utilisateur ayant les droits PRIVILEGE, ADMINISTRATION ou COMPTABILITE

### **Étapes de Test**

#### **1. Vérifier la Migration**
```bash
# Dans le terminal, depuis le dossier appli_KBIS
python manage.py migrate paiements
```

#### **2. Accéder aux Récapitulatifs**
1. **Aller sur** : `/paiements/recaps-mensuels-automatiques/bailleurs/`
2. **Vérifier** : La liste des bailleurs s'affiche
3. **Chercher** : Un bailleur avec un récapitulatif existant et validé

#### **3. Tester le Bouton "Payer le Bailleur"**

##### **Dans la Liste des Bailleurs**
1. **Localiser** : Un bailleur avec récapitulatif validé
2. **Vérifier** : Le bouton vert "Payer le Bailleur" (icône cash-coin) est visible
3. **Cliquer** : Sur le bouton

##### **Dans le Détail du Récapitulatif**
1. **Aller sur** : `/paiements/recaps-mensuels-automatiques/{recap_id}/`
2. **Vérifier** : Le bouton vert "Payer le Bailleur" est visible
3. **Cliquer** : Sur le bouton

#### **4. Tester le Formulaire de Création de Retrait**

##### **Vérifications Visuelles**
- ✅ **En-tête** : Informations du récapitulatif affichées
- ✅ **Formulaire** : Champs pré-remplis (bailleur, mois, montants)
- ✅ **Mode de retrait** : Dropdown avec options (Virement, Chèque, Espèces)
- ✅ **Référence** : Champ vide, auto-généré pour virement
- ✅ **Observations** : Texte pré-rempli avec référence au récapitulatif
- ✅ **Résumé** : Montants et détails du retrait
- ✅ **Boutons** : "Créer le Retrait" et "Annuler"

##### **Test de Validation**
1. **Sélectionner** : Mode de retrait (ex: Virement)
2. **Vérifier** : Référence auto-générée (format: VIR-YYYYMMDD-XXXXXX)
3. **Modifier** : Les observations si nécessaire
4. **Cliquer** : "Créer le Retrait"
5. **Confirmer** : Dans la popup de confirmation

#### **5. Vérifier la Création du Retrait**

##### **Redirection**
- ✅ **Après création** : Redirection vers le détail du retrait
- ✅ **Message** : "Retrait créé avec succès pour [Bailleur] - Montant: [Montant] €"

##### **Dans le Détail du Retrait**
- ✅ **Informations** : Bailleur, mois, montants corrects
- ✅ **Lien** : "Voir le Récapitulatif" vers le récapitulatif lié
- ✅ **Statut** : "En attente"

##### **Dans le Détail du Récapitulatif**
- ✅ **Statut** : Changé à "Payé"
- ✅ **Date de paiement** : Date actuelle
- ✅ **Lien** : "Voir le Retrait" vers le retrait créé

### **6. Tests de Validation et Sécurité**

#### **Test 1 : Récapitulatif Non Validé**
1. **Créer** : Un récapitulatif en statut "Brouillon"
2. **Vérifier** : Le bouton "Payer le Bailleur" n'apparaît PAS
3. **Tenter** : Accès direct à l'URL → Erreur attendue

#### **Test 2 : Retrait Existant**
1. **Créer** : Un retrait pour un mois/bailleur
2. **Tenter** : Créer un autre retrait pour le même mois/bailleur
3. **Vérifier** : Message "Un retrait existe déjà" + redirection

#### **Test 3 : Permissions**
1. **Se connecter** : Avec un utilisateur sans droits
2. **Tenter** : Accéder au formulaire de création
3. **Vérifier** : Message d'erreur de permissions

### **7. Tests de Navigation**

#### **Liens Bidirectionnels**
- ✅ **Récapitulatif → Retrait** : Lien "Voir le Retrait"
- ✅ **Retrait → Récapitulatif** : Lien "Voir le Récapitulatif"
- ✅ **Navigation** : Retour aux listes et détails

#### **Boutons PDF**
- ✅ **PDF Standard** : Génération du PDF classique
- ✅ **PDF Détaillé** : Génération du PDF paysage avec détails

### **8. Tests de Données**

#### **Vérification des Montants**
- ✅ **Loyers bruts** : Montant correct du récapitulatif
- ✅ **Charges déductibles** : Montant correct du récapitulatif
- ✅ **Net à payer** : Calcul correct (loyers - charges)

#### **Vérification des Informations**
- ✅ **Bailleur** : Nom complet correct
- ✅ **Mois** : Mois du récapitulatif
- ✅ **Type** : "Mensuel" par défaut
- ✅ **Statut** : "En attente" pour le retrait

### **9. Tests d'Interface**

#### **Responsive Design**
- ✅ **Mobile** : Formulaire adapté aux petits écrans
- ✅ **Tablet** : Mise en page correcte
- ✅ **Desktop** : Interface complète

#### **Accessibilité**
- ✅ **Labels** : Tous les champs ont des labels
- ✅ **Icônes** : Icônes Bootstrap Icons visibles
- ✅ **Couleurs** : Contraste suffisant

### **10. Tests de Performance**

#### **Temps de Chargement**
- ✅ **Liste des bailleurs** : Chargement rapide
- ✅ **Détail récapitulatif** : Affichage immédiat
- ✅ **Formulaire de retrait** : Ouverture rapide

#### **Gestion des Erreurs**
- ✅ **Erreurs réseau** : Messages d'erreur appropriés
- ✅ **Données manquantes** : Gestion des cas vides
- ✅ **Validation** : Messages d'erreur clairs

## 🐛 **Problèmes Potentiels et Solutions**

### **Problème 1 : Bouton Non Visible**
**Cause** : Récapitulatif non validé ou montant net = 0
**Solution** : Valider le récapitulatif et vérifier les montants

### **Problème 2 : Erreur de Migration**
**Cause** : Migration non appliquée
**Solution** : Exécuter `python manage.py migrate paiements`

### **Problème 3 : Erreur de Permissions**
**Cause** : Utilisateur sans droits
**Solution** : Vérifier les groupes d'utilisateur

### **Problème 4 : Lien Cassé**
**Cause** : URL incorrecte ou vue manquante
**Solution** : Vérifier les URLs et les vues

## ✅ **Checklist de Validation**

- [ ] Migration appliquée
- [ ] Boutons visibles dans la liste des bailleurs
- [ ] Boutons visibles dans le détail du récapitulatif
- [ ] Formulaire de création fonctionnel
- [ ] Validation des champs
- [ ] Création du retrait réussie
- [ ] Liaison bidirectionnelle
- [ ] Mise à jour du statut du récapitulatif
- [ ] Messages de succès/erreur
- [ ] Navigation entre les pages
- [ ] Tests de sécurité
- [ ] Tests de permissions

## 📝 **Rapport de Test**

### **Date de Test** : [Date]
### **Testeur** : [Nom]
### **Version** : [Version du système]

#### **Tests Réussis**
- [ ] Test 1 : [Description]
- [ ] Test 2 : [Description]
- [ ] Test 3 : [Description]

#### **Tests Échoués**
- [ ] Test 1 : [Description] - [Cause]
- [ ] Test 2 : [Description] - [Cause]

#### **Bugs Découverts**
- [ ] Bug 1 : [Description] - [Priorité]
- [ ] Bug 2 : [Description] - [Priorité]

#### **Recommandations**
- [ ] Amélioration 1 : [Description]
- [ ] Amélioration 2 : [Description]

## 🎯 **Conclusion**

Le système de liaison récapitulatif → paiement bailleur est maintenant fonctionnel et prêt pour les tests. Suivez ce guide pour valider toutes les fonctionnalités et signaler tout problème rencontré.
