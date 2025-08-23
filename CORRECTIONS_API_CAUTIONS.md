# Corrections Apportées - API Gestion des Cautions

## 🚨 Problème identifié

Lors du démarrage du serveur Django, une erreur se produisait :

```
django.core.exceptions.ImproperlyConfigured: Router with basename "contrat" is already registered. Please provide a unique basename for viewset "<class 'contrats.api_views.CautionViewSet'>"
```

## 🔍 Cause du problème

Le problème était causé par des **conflits de basename** dans les routers Django REST Framework :

1. **Module Contrats** : 
   - `ContratViewSet` (modèle: `Contrat`) → basename automatique: `"contrat"`
   - `CautionViewSet` (modèle: `Contrat`) → basename automatique: `"contrat"` ⚠️ **CONFLIT**

2. **Module Paiements** :
   - `PaiementViewSet` (modèle: `Paiement`) → basename automatique: `"paiement"`
   - `PaiementCautionAvanceViewSet` (modèle: `Paiement`) → basename automatique: `"paiement"` ⚠️ **CONFLIT**

## ✅ Solution appliquée

### 1. Correction du module Contrats

**Fichier** : `contrats/urls.py`

**Avant** :
```python
router.register(r'api/cautions', api_views.CautionViewSet)
```

**Après** :
```python
router.register(r'api/cautions', api_views.CautionViewSet, basename='caution')
```

### 2. Correction du module Paiements

**Fichier** : `paiements/urls.py`

**Avant** :
```python
router.register(r'api/cautions-avances', api_views.PaiementCautionAvanceViewSet)
```

**Après** :
```python
router.register(r'api/cautions-avances', api_views.PaiementCautionAvanceViewSet, basename='paiement-caution-avance')
```

## 🔧 Explication technique

### Pourquoi ce problème se produit ?

Django REST Framework génère automatiquement le `basename` à partir du modèle associé au ViewSet :

- Si le ViewSet utilise `queryset = Contrat.objects.all()`, le basename sera `"contrat"`
- Si le ViewSet utilise `queryset = Paiement.objects.all()`, le basename sera `"paiement"`

### Pourquoi spécifier un basename manuel ?

En spécifiant un `basename` manuel, nous évitons le conflit :

```python
# Basename automatique : "contrat" (conflit)
router.register(r'api/contrats', ContratViewSet)

# Basename manuel : "caution" (pas de conflit)
router.register(r'api/cautions', CautionViewSet, basename='caution')
```

## 📋 Endpoints maintenant disponibles

### Module Contrats
- `GET /contrats/api/cautions/` - Liste des contrats avec cautions
- `GET /contrats/api/cautions/statistiques/` - Statistiques des cautions
- `POST /contrats/api/cautions/{id}/marquer_caution_payee/` - Marquer caution payée
- `POST /contrats/api/cautions/{id}/marquer_avance_payee/` - Marquer avance payée

### Module Paiements
- `GET /paiements/api/cautions-avances/` - Liste des paiements de caution/avance
- `GET /paiements/api/cautions-avances/statistiques/` - Statistiques des paiements
- `GET /paiements/api/cautions-avances/cautions_en_attente/` - Cautions en attente
- `GET /paiements/api/cautions-avances/avances_en_attente/` - Avances en attente

### Module Core (API unifiée)
- `GET /core/api/cautions/` - Endpoint unifié pour la gestion des cautions
- `POST /core/api/cautions/{id}/marquer-caution/` - Marquer caution payée
- `POST /core/api/cautions/{id}/marquer-avance/` - Marquer avance payée

## 🧪 Vérification

### 1. Test de configuration
```bash
python manage.py check
# ✅ System check identified no issues (0 silenced).
```

### 2. Démarrage du serveur
```bash
python manage.py runserver
# ✅ Serveur démarre sans erreur
```

### 3. Test des endpoints
Utilisez le script `test_api_cautions.py` pour vérifier que tous les endpoints sont accessibles.

## 🎯 Résultat final

✅ **Problème résolu** : Le serveur Django démarre maintenant sans erreur  
✅ **Endpoints disponibles** : Tous les endpoints de gestion des cautions sont maintenant accessibles  
✅ **Pas de conflits** : Chaque ViewSet a un basename unique  
✅ **Fonctionnalité complète** : La gestion des cautions via API est maintenant opérationnelle  

## 💡 Bonnes pratiques pour l'avenir

1. **Toujours spécifier un basename unique** quand plusieurs ViewSets utilisent le même modèle
2. **Utiliser des noms descriptifs** pour les basenames (ex: `'caution'`, `'paiement-caution-avance'`)
3. **Tester la configuration** avec `python manage.py check` avant de démarrer le serveur
4. **Documenter les basenames** dans les commentaires du code

## 🔗 Liens utiles

- [Documentation Django REST Framework - Routers](https://www.django-rest-framework.org/api-guide/routers/)
- [API_GESTION_CAUTIONS.md](API_GESTION_CAUTIONS.md) - Documentation complète des endpoints
- [test_api_cautions.py](test_api_cautions.py) - Script de test des endpoints
