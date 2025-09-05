# Guide de Test - Modal de Paiement

## 🎯 **URLs à Tester**

### **1. Liste des Bailleurs avec Récapitulatifs**
```
/paiements/recaps-mensuels-automatiques/bailleurs/
```

### **2. Détail d'un Récapitulatif**
```
/paiements/recaps-mensuels-automatiques/{recap_id}/
```

## 🔧 **Étapes de Test**

### **Étape 1 : Vérifier l'URL**
1. **Ouvrir** votre navigateur
2. **Aller sur** : `http://votre-domaine/paiements/recaps-mensuels-automatiques/bailleurs/`
3. **Vérifier** : La page se charge sans erreur

### **Étape 2 : Chercher le Bouton "Payer le Bailleur"**
1. **Chercher** : Un bailleur avec un récapitulatif validé
2. **Vérifier** : Le bouton vert avec icône cash-coin est visible
3. **Condition** : Le bouton n'apparaît que si :
   - Le récapitulatif est validé (`statut == 'valide'`)
   - Le montant net > 0 (`total_net_a_payer > 0`)

### **Étape 3 : Tester le Modal**
1. **Cliquer** sur le bouton vert "Payer le Bailleur"
2. **Vérifier** : Le modal s'ouvre
3. **Vérifier** : Les informations du récapitulatif sont pré-remplies
4. **Vérifier** : Le formulaire est fonctionnel

## 🐛 **Problèmes Possibles et Solutions**

### **Problème 1 : Page 404 (Not Found)**
**Cause** : URL incorrecte ou vue manquante
**Solution** : 
1. Vérifier que l'URL est exactement : `/paiements/recaps-mensuels-automatiques/bailleurs/`
2. Vérifier que la vue `liste_bailleurs_recaps` existe dans `views.py`

### **Problème 2 : Bouton Non Visible**
**Cause** : Aucun récapitulatif validé avec montant > 0
**Solution** :
1. Créer un récapitulatif mensuel
2. Le valider (statut = 'valide')
3. Vérifier que le montant net > 0

### **Problème 3 : Erreur de Migration**
**Cause** : Le champ `recap_lie` n'a pas été ajouté
**Solution** :
```bash
cd appli_KBIS
python manage.py migrate paiements
```

### **Problème 4 : Erreur de Permissions**
**Cause** : Utilisateur sans droits
**Solution** :
1. Vérifier que l'utilisateur est connecté
2. Vérifier que l'utilisateur a les droits PRIVILEGE, ADMINISTRATION ou COMPTABILITE

## 📋 **Checklist de Test**

- [ ] URL accessible : `/paiements/recaps-mensuels-automatiques/bailleurs/`
- [ ] Page se charge sans erreur
- [ ] Liste des bailleurs s'affiche
- [ ] Bouton "Payer le Bailleur" visible pour les récapitulatifs validés
- [ ] Modal s'ouvre au clic
- [ ] Informations pré-remplies dans le modal
- [ ] Formulaire fonctionnel
- [ ] Validation JavaScript
- [ ] Soumission du formulaire

## 🎯 **Test Rapide**

### **Si vous ne voyez pas la page :**
1. **Vérifier l'URL** : `/paiements/recaps-mensuels-automatiques/bailleurs/`
2. **Vérifier les permissions** : Être connecté avec les bons droits
3. **Vérifier la migration** : `python manage.py migrate paiements`

### **Si vous voyez la page mais pas de boutons :**
1. **Créer un récapitulatif** mensuel
2. **Le valider** (statut = 'valide')
3. **Vérifier le montant** net > 0

### **Si le modal ne s'ouvre pas :**
1. **Vérifier Bootstrap** : Le modal nécessite Bootstrap 5
2. **Vérifier JavaScript** : Pas d'erreurs dans la console
3. **Vérifier les IDs** : Les IDs des modals doivent être uniques

## 🚀 **URLs Alternatives à Tester**

Si l'URL principale ne fonctionne pas, essayez ces alternatives :

### **1. Tableau de Bord des Récapitulatifs**
```
/paiements/recaps-mensuels-automatiques/tableau-bord/
```

### **2. Liste des Récapitulatifs**
```
/paiements/recaps-mensuels-automatiques/
```

### **3. Ancien Système (pour comparaison)**
```
/paiements/recaps-mensuels/
```

## 📞 **Support**

Si vous rencontrez encore des problèmes :

1. **Vérifier les logs** Django pour les erreurs
2. **Vérifier la console** du navigateur pour les erreurs JavaScript
3. **Vérifier les permissions** utilisateur
4. **Vérifier la migration** de la base de données

## ✅ **Résultat Attendu**

Après avoir suivi ce guide, vous devriez voir :

- ✅ **Page de liste** des bailleurs avec récapitulatifs
- ✅ **Boutons verts** "Payer le Bailleur" pour les récapitulatifs validés
- ✅ **Modals fonctionnels** avec formulaire pré-rempli
- ✅ **Processus de paiement** complet et fluide
