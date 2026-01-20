# 🔧 Configuration des Paramètres de Caution et Avance

## 🎯 Problème Résolu

**Avant :** Le système imposait des valeurs fixes :
- ❌ **3 mois de caution** (codé en dur)
- ❌ **1 mois d'avance** (codé en dur)

**Maintenant :** L'utilisateur peut configurer ces valeurs selon ses besoins !
- ✅ **Caution configurable** (1 à 12 mois)
- ✅ **Avance configurable** (0 à 12 mois)

---

## 📊 Où Configurer

### 🔗 Accès Direct

**URL :**
```
https://appli-kbis-3.onrender.com/core/configuration-entreprise/
```

**Ou via le menu :** Menu latéral → **⚙️ Configuration Entreprise**

---

## 🖼️ Interface de Configuration

### Nouvelle Section : "Paramètres de Caution et Avance"

La page de configuration affiche maintenant une nouvelle section avec :

#### 1️⃣ Nombre de mois de caution
- **Champ numérique** (1 à 12 mois)
- **Valeur par défaut :** 3 mois
- **Description :** La caution sera automatiquement calculée comme `Loyer × Nombre de mois`

**Exemple :**
```
Loyer mensuel : 100 000 F CFA
Nombre de mois de caution : 3
→ Caution = 100 000 × 3 = 300 000 F CFA
```

#### 2️⃣ Nombre de mois d'avance
- **Champ numérique** (0 à 12 mois)
- **Valeur par défaut :** 1 mois
- **Description :** L'avance sera automatiquement calculée comme `Loyer × Nombre de mois`

**Exemple :**
```
Loyer mensuel : 100 000 F CFA
Nombre de mois d'avance : 2
→ Avance = 100 000 × 2 = 200 000 F CFA
```

---

## 🎬 Comment Utiliser

### Étape 1 : Accéder à la Configuration

1. **Connectez-vous** à votre application KBIS
2. **Cliquez** sur **⚙️ Configuration Entreprise** dans le menu latéral
3. **Faites défiler** jusqu'à la section **"Paramètres de Caution et Avance"**

### Étape 2 : Modifier les Valeurs

1. **Modifiez** le **"Nombre de mois de caution"** (ex: 2, 3, 4, 6...)
2. **Modifiez** le **"Nombre de mois d'avance"** (ex: 0, 1, 2...)
3. **Cliquez** sur le bouton **"Enregistrer les modifications"** en bas de page

### Étape 3 : Vérification

Un message de succès s'affiche :
```
✅ Configuration mise à jour avec succès !
```

---

## 📋 Exemples de Configuration

### Cas 1 : Configuration Classique (Défaut)

```
Nombre de mois de caution : 3
Nombre de mois d'avance : 1
```

**Résultat pour un loyer de 150 000 F CFA :**
- Caution : 150 000 × 3 = **450 000 F CFA**
- Avance : 150 000 × 1 = **150 000 F CFA**
- **Total à l'entrée :** 600 000 F CFA

---

### Cas 2 : Configuration Flexible

```
Nombre de mois de caution : 2
Nombre de mois d'avance : 0
```

**Résultat pour un loyer de 150 000 F CFA :**
- Caution : 150 000 × 2 = **300 000 F CFA**
- Avance : 150 000 × 0 = **0 F CFA**
- **Total à l'entrée :** 300 000 F CFA

---

### Cas 3 : Configuration Stricte

```
Nombre de mois de caution : 6
Nombre de mois d'avance : 2
```

**Résultat pour un loyer de 150 000 F CFA :**
- Caution : 150 000 × 6 = **900 000 F CFA**
- Avance : 150 000 × 2 = **300 000 F CFA**
- **Total à l'entrée :** 1 200 000 F CFA

---

## ⚠️ Important à Savoir

### 1. S'applique uniquement aux NOUVEAUX contrats

Ces paramètres sont utilisés **uniquement lors de la création de nouveaux contrats**.

**Les contrats existants :**
- ✅ Conservent leurs valeurs actuelles de caution et d'avance
- ❌ Ne sont PAS modifiés automatiquement

Si vous voulez modifier un contrat existant, vous devez :
1. Ouvrir le contrat en modification
2. Changer manuellement les valeurs de caution/avance
3. Enregistrer

### 2. Calcul automatique

Lors de la **création d'un nouveau contrat** :
1. Vous saisissez le **loyer mensuel**
2. Le système calcule automatiquement :
   - **Caution** = Loyer × `nombre_mois_caution` (configuré)
   - **Avance** = Loyer × `nombre_mois_avance` (configuré)
3. Vous pouvez **modifier manuellement** ces valeurs calculées si nécessaire

### 3. Permissions requises

Seuls les utilisateurs du groupe **PRIVILEGE** peuvent modifier cette configuration.

---

## 🔍 Vérification Post-Configuration

### Test 1 : Vérifier les Valeurs Enregistrées

1. **Retournez** sur la page **Configuration Entreprise**
2. **Vérifiez** que les champs affichent les bonnes valeurs :
   - Nombre de mois de caution : **[Votre valeur]**
   - Nombre de mois d'avance : **[Votre valeur]**

### Test 2 : Créer un Nouveau Contrat

1. **Allez** sur **Contrats → Ajouter un Contrat**
2. **Remplissez** les champs obligatoires
3. **Saisissez** le **loyer mensuel** (ex: 100 000 F CFA)
4. **Observez** les champs calculés automatiquement :
   - Dépôt de garantie (caution) : devrait être **100 000 × [votre config]**
   - Avance loyer : devrait être **100 000 × [votre config]**

### Test 3 : Vérifier un Contrat Existant

1. **Ouvrez** un contrat créé **avant** la modification de la configuration
2. **Vérifiez** que ses valeurs de caution/avance **n'ont PAS changé** ✅
3. C'est normal ! Les contrats existants ne sont pas impactés.

---

## 📝 Modifications Techniques

### Fichiers Modifiés

| Fichier | Type de Modification |
|---------|---------------------|
| `core/models.py` | Ajout de 2 champs au modèle `ConfigurationEntreprise` |
| `core/forms.py` | Ajout des widgets pour les nouveaux champs |
| `core/migrations/0025_add_caution_avance_fields.py` | Migration de base de données |
| `templates/core/configuration_entreprise.html` | Ajout de la section dans l'interface |
| `contrats/models.py` | Utilisation des valeurs configurables au lieu de 3 et 1 en dur |
| `contrats/services_contrat_pdf_updated.py` | Utilisation des valeurs configurables pour les PDFs |

### Nouveaux Champs du Modèle

```python
class ConfigurationEntreprise(models.Model):
    # ... autres champs ...
    
    nombre_mois_caution = models.PositiveIntegerField(
        default=3,
        verbose_name="Nombre de mois de caution",
        help_text="Nombre de mois de loyer pour la caution (généralement 3)"
    )
    
    nombre_mois_avance = models.PositiveIntegerField(
        default=1,
        verbose_name="Nombre de mois d'avance",
        help_text="Nombre de mois de loyer à payer en avance (généralement 1)"
    )
```

### Logique de Calcul

**Dans `contrats/models.py` (méthode `save`) :**

```python
# Récupérer la configuration entreprise
config = ConfigurationEntreprise.get_configuration_active()
nombre_mois_caution = config.nombre_mois_caution if config else 3
nombre_mois_avance = config.nombre_mois_avance if config else 1

# Calcul automatique
if self.depot_garantie == "0.00" or not self.depot_garantie:
    self.depot_garantie = str(loyer_decimal * nombre_mois_caution)

if self.avance_loyer == "0.00" or not self.avance_loyer:
    self.avance_loyer = str(loyer_decimal * nombre_mois_avance)
```

---

## 🚨 Résolution de Problèmes

### Problème 1 : Je ne vois pas la nouvelle section

**Cause :** Cache navigateur ou déploiement non terminé

**Solution :**
1. Actualisez avec vidage du cache : **Ctrl + F5** (Windows) ou **Cmd + Shift + R** (Mac)
2. Vérifiez que le déploiement Render est terminé
3. Vérifiez que vous êtes sur la page **Configuration Entreprise** et non **Admin Django**

---

### Problème 2 : Les valeurs ne se sauvegardent pas

**Cause :** Permissions insuffisantes ou erreur formulaire

**Solution :**
1. Vérifiez que vous êtes dans le groupe **PRIVILEGE**
2. Vérifiez qu'il n'y a pas de message d'erreur rouge sous les champs
3. Les valeurs doivent être entre **1 et 12** pour la caution, **0 et 12** pour l'avance

---

### Problème 3 : Les nouveaux contrats n'utilisent pas les bonnes valeurs

**Cause :** Configuration non enregistrée ou erreur de calcul

**Solution :**
1. **Vérifiez** que la configuration a bien été sauvegardée (message de succès vert)
2. **Actualisez** la page de création de contrat (F5)
3. **Saisissez** le loyer mensuel (les champs caution/avance se calculent après saisie du loyer)
4. Si le problème persiste, contactez l'administrateur

---

### Problème 4 : Un contrat existant a été modifié

**Cause :** Impossible ! Les contrats existants ne sont jamais modifiés automatiquement

**Solution :**
1. Si un contrat a été modifié, c'est qu'un utilisateur l'a fait **manuellement**
2. Consultez l'historique du contrat pour voir qui l'a modifié et quand
3. Vous pouvez restaurer les anciennes valeurs en modifiant à nouveau le contrat

---

## 🎓 Cas d'Usage Réels

### Cas 1 : Propriétés Haut Standing

**Situation :** Propriétés de luxe, locataires solvables, faible rotation

**Configuration recommandée :**
```
Nombre de mois de caution : 2
Nombre de mois d'avance : 1
```

**Avantage :** Facilite l'accès aux locataires premium

---

### Cas 2 : Propriétés Standard

**Situation :** Marché classique, gestion courante

**Configuration recommandée :**
```
Nombre de mois de caution : 3
Nombre de mois d'avance : 1
```

**Avantage :** Configuration standard, équilibrée

---

### Cas 3 : Propriétés à Risque

**Situation :** Zone difficile, historique d'impayés

**Configuration recommandée :**
```
Nombre de mois de caution : 6
Nombre de mois d'avance : 2
```

**Avantage :** Protection maximale contre les impayés

---

### Cas 4 : Colocation ou Location Sociale

**Situation :** Locataires avec revenus modestes, besoin social

**Configuration recommandée :**
```
Nombre de mois de caution : 1
Nombre de mois d'avance : 0
```

**Avantage :** Facilite l'accès au logement

---

## 📞 Support

En cas de question :
1. Consultez ce document en premier
2. Testez sur un **nouveau contrat de test** avant d'appliquer en production
3. Contactez l'équipe de développement si problème persistant

---

## 🎉 Avantages de cette Fonctionnalité

✅ **Flexibilité totale** - Adaptez selon vos besoins
✅ **Facilité d'utilisation** - Interface simple et claire
✅ **Sécurisé** - Les contrats existants ne sont jamais modifiés
✅ **Calcul automatique** - Moins d'erreurs de saisie
✅ **Multi-scénarios** - Différentes politiques selon les propriétés
✅ **Réversible** - Vous pouvez changer à tout moment

---

**Date de création :** 20/01/2026  
**Version :** 1.0  
**Auteur :** Système KBIS Immobilier
