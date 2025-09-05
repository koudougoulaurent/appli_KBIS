# 🔧 Guide de Test - Boutons Menu Utilisateur

## 🎯 **Boutons Concernés**

Les boutons dans le menu déroulant utilisateur (en haut à droite) :
- **Mon Profil** → `{% url 'utilisateurs:profile' %}`
- **Configuration** → `{% url 'core:configuration_entreprise' %}`  
- **Déconnexion** → `{% url 'logout' %}`

## ✅ **Corrections Appliquées**

### **1. Ordre de Chargement JavaScript**
- ✅ Bootstrap chargé en premier
- ✅ jQuery chargé après Bootstrap (évite les conflits)
- ✅ Select2 chargé après jQuery

### **2. Initialisation Bootstrap Dropdown**
- ✅ Script ajouté pour réinitialiser tous les dropdowns
- ✅ Event listeners de debug pour tracer les clics
- ✅ Réinitialisation automatique au chargement de la page

### **3. URL du Bouton "Mon Profil"**
- ✅ Corrigé : `core:dashboard` → `utilisateurs:profile`
- ✅ Pointe maintenant vers la vraie page de profil

## 🧪 **Tests à Effectuer**

### **1. Test du Dropdown**
1. **Ouvrir la page** dans le navigateur
2. **Cliquer sur le nom d'utilisateur** en haut à droite
3. **Vérifier que le menu se déploie** avec les 3 options
4. **Vérifier dans la console** (F12) les messages de debug

### **2. Test des Boutons Individuels**

#### **Mon Profil**
- [ ] Cliquer sur "Mon Profil"
- [ ] Vérifier la redirection vers `/utilisateurs/profile/`
- [ ] Page de profil s'affiche correctement

#### **Configuration**
- [ ] Cliquer sur "Configuration" 
- [ ] Vérifier la redirection vers `/configuration-entreprise/`
- [ ] Page de configuration s'affiche correctement

#### **Déconnexion**
- [ ] Cliquer sur "Déconnexion"
- [ ] Vérifier la déconnexion effective
- [ ] Redirection vers la page de connexion

### **3. Test de Debug**
1. **Ouvrir la console** du navigateur (F12)
2. **Chercher les messages** :
   - `🔍 Dropdowns initialisés: X`
   - `🖱️ Clic sur: Mon Profil` (quand on clique)

## 🚀 **Démarrage pour Test**

```powershell
# 1. Aller dans le dossier du projet
cd C:\Users\GAMER\Desktop\gestionImo

# 2. Activer l'environnement virtuel
.\venv\Scripts\Activate.ps1

# 3. Aller dans Django
cd appli_KBIS

# 4. Démarrer le serveur
python manage.py runserver 127.0.0.1:8000
```

## 🔍 **Diagnostic en Cas de Problème**

### **Menu ne s'ouvre pas**
```javascript
// Dans la console du navigateur
console.log('Bootstrap version:', bootstrap);
console.log('Dropdowns:', document.querySelectorAll('.dropdown-toggle'));
```

### **Boutons ne redirigent pas**
1. **Vérifier les URLs** dans la console réseau (F12 > Network)
2. **Chercher les erreurs 404** ou 500
3. **Vérifier que les vues existent**

### **Erreurs JavaScript**
1. **Console du navigateur** (F12 > Console)
2. **Chercher les erreurs rouges**
3. **Vérifier l'ordre de chargement des scripts**

## 📋 **Checklist Final**

- [ ] Serveur Django démarré
- [ ] Page accessible sur http://127.0.0.1:8000/
- [ ] Menu utilisateur cliquable
- [ ] Dropdown s'ouvre au clic
- [ ] "Mon Profil" fonctionne
- [ ] "Configuration" fonctionne  
- [ ] "Déconnexion" fonctionne
- [ ] Console sans erreurs rouges

## 🎉 **Résultat Attendu**

Après ces corrections, les 3 boutons du menu utilisateur devraient fonctionner parfaitement :
- **Dropdown s'ouvre** au clic sur le nom d'utilisateur
- **Navigation fonctionnelle** vers chaque page
- **Déconnexion opérationnelle**

---
*Guide créé pour résoudre spécifiquement le problème des boutons du menu utilisateur*
