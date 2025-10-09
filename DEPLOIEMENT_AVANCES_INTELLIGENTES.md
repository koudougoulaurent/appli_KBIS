# 🚀 GUIDE DE DÉPLOIEMENT - SYSTÈME AVANCES INTELLIGENTES

## 📋 RÉSUMÉ DES MODIFICATIONS

### ✨ Nouvelles fonctionnalités
- **Intégration automatique** des avances dans le système de paiement
- **Détection intelligente** des avances existantes avec prolongation
- **Sélection manuelle** des mois couverts avec suggestions dynamiques
- **Interface utilisateur** améliorée avec messages d'erreur clairs

### 🔧 Corrections critiques
- **Logique temporelle** corrigée (mois actuel = en cours)
- **Format des années** corrigé (2025 au lieu de 0225)
- **Statuts cohérents** (active par défaut)
- **Compteurs réalistes** (suppression des valeurs négatives)

## 🗄️ MODIFICATIONS BASE DE DONNÉES

### Nouvelles migrations
```bash
# Migrations à appliquer dans l'ordre
python manage.py migrate paiements 0011  # Champs sélection manuelle
python manage.py migrate paiements 0012  # Champ paiement
```

### Nouveaux champs ajoutés
- `paiements_avanceloyer.paiement_id` (ForeignKey vers paiements_paiement)
- `paiements_avanceloyer.mode_selection_mois` (VARCHAR, défaut: 'automatique')
- `paiements_avanceloyer.mois_couverts_manuels` (JSON, défaut: '[]')

## 🚀 PROCÉDURE DE DÉPLOIEMENT

### 1. Préparation de l'environnement
```bash
# Sauvegarder la base de données
python manage.py dumpdata > backup_avant_avances_intelligentes.json

# Vérifier l'état actuel
python manage.py showmigrations paiements
```

### 2. Mise à jour du code
```bash
# Récupérer les dernières modifications
git pull origin modifications-octobre-2025

# Installer les nouvelles dépendances (si nécessaire)
pip install -r requirements.txt
```

### 3. Application des migrations
```bash
# Appliquer les migrations dans l'ordre
python manage.py migrate paiements 0011
python manage.py migrate paiements 0012

# Vérifier que les migrations sont appliquées
python manage.py showmigrations paiements
```

### 4. Correction des données existantes
```bash
# Script de correction des données
python manage.py shell << EOF
from paiements.models_avance import AvanceLoyer, ConsommationAvance
from datetime import date

# Corriger les avances avec des dates incorrectes
for avance in AvanceLoyer.objects.all():
    if avance.mois_debut_couverture and avance.mois_debut_couverture.year < 2000:
        avance.mois_debut_couverture = avance.mois_debut_couverture.replace(year=avance.mois_debut_couverture.year + 2000)
    if avance.mois_fin_couverture and avance.mois_fin_couverture.year < 2000:
        avance.mois_fin_couverture = avance.mois_fin_couverture.replace(year=avance.mois_fin_couverture.year + 2000)
    avance.save()

# Supprimer les consommations avec des dates incorrectes
ConsommationAvance.objects.filter(mois_consomme__year__lt=2000).delete()

print("Correction des données terminée")
EOF
```

### 5. Vérification de l'intégrité
```bash
# Vérifier l'intégrité des données
python manage.py shell << EOF
from paiements.models_avance import AvanceLoyer

# Vérifier les avances
avances = AvanceLoyer.objects.all()
print(f"Total avances: {avances.count()}")

# Vérifier les avances avec des problèmes
problemes = avances.filter(montant_restant__lt=0)
print(f"Avances avec montant restant négatif: {problemes.count()}")

# Vérifier les dates
dates_incorrectes = avances.filter(mois_debut_couverture__year__lt=2000)
print(f"Avances avec dates incorrectes: {dates_incorrectes.count()}")

print("Vérification terminée")
EOF
```

### 6. Test des nouvelles fonctionnalités
```bash
# Tester la création d'avance
python manage.py shell << EOF
from paiements.services_avance import ServiceGestionAvance
from contrats.models import Contrat
from decimal import Decimal
from datetime import date

# Récupérer un contrat
contrat = Contrat.objects.first()
if contrat:
    # Créer une avance de test
    avance = ServiceGestionAvance.creer_avance_loyer(
        contrat=contrat,
        montant_avance=Decimal('100000'),
        date_avance=date.today(),
        notes="Test déploiement"
    )
    print(f"Avance créée: {avance.id}, Statut: {avance.statut}")
    print(f"Paiement associé: {avance.paiement}")
    # Supprimer l'avance de test
    avance.delete()
    print("Test terminé avec succès")
else:
    print("Aucun contrat trouvé pour le test")
EOF
```

## 🔧 CONFIGURATION POST-DÉPLOIEMENT

### 1. Vérifier les URLs
```bash
# Tester les nouvelles URLs
curl -I http://localhost:8000/paiements/avances/ajouter/
curl -I http://localhost:8000/paiements/avances/detail/1/
```

### 2. Vérifier les permissions
```bash
# Vérifier que les utilisateurs peuvent accéder aux nouvelles fonctionnalités
python manage.py shell << EOF
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

# Vérifier les permissions pour les avances
ct = ContentType.objects.get(app_label='paiements', model='avanceloyer')
perms = Permission.objects.filter(content_type=ct)
print("Permissions avances disponibles:")
for perm in perms:
    print(f"  - {perm.codename}: {perm.name}")
EOF
```

### 3. Nettoyer le cache
```bash
# Nettoyer le cache Django
python manage.py clear_cache

# Redémarrer le serveur
sudo systemctl restart gunicorn  # ou votre service web
```

## 📊 MONITORING POST-DÉPLOIEMENT

### 1. Logs à surveiller
```bash
# Surveiller les logs d'erreur
tail -f /var/log/nginx/error.log
tail -f /var/log/gunicorn/error.log

# Surveiller les logs Django
tail -f logs/django.log
```

### 2. Métriques importantes
- Nombre d'avances créées par jour
- Taux d'erreur sur la création d'avances
- Temps de réponse des pages d'avances
- Utilisation de la mémoire

### 3. Tests de régression
```bash
# Tester les fonctionnalités existantes
python manage.py test paiements.tests.test_avances
python manage.py test paiements.tests.test_paiements
```

## 🚨 ROLLBACK EN CAS DE PROBLÈME

### 1. Restaurer la base de données
```bash
# Restaurer la sauvegarde
python manage.py loaddata backup_avant_avances_intelligentes.json
```

### 2. Revenir à l'ancien code
```bash
# Revenir au commit précédent
git checkout HEAD~1
```

### 3. Annuler les migrations
```bash
# Annuler les migrations (ATTENTION: perte de données)
python manage.py migrate paiements 0010
```

## 📞 SUPPORT ET DÉPANNAGE

### Problèmes courants
1. **Erreur de migration** : Vérifier que la base de données est accessible
2. **Permissions insuffisantes** : Vérifier les permissions des utilisateurs
3. **Erreur 500** : Vérifier les logs et la configuration
4. **Données incohérentes** : Exécuter les scripts de correction

### Contacts
- **Développeur** : Assistant IA
- **Documentation** : Ce fichier et les commentaires dans le code
- **Logs** : `/var/log/` et `logs/`

## ✅ CHECKLIST DE DÉPLOIEMENT

- [ ] Sauvegarde de la base de données
- [ ] Mise à jour du code
- [ ] Application des migrations
- [ ] Correction des données existantes
- [ ] Vérification de l'intégrité
- [ ] Test des nouvelles fonctionnalités
- [ ] Vérification des URLs
- [ ] Vérification des permissions
- [ ] Nettoyage du cache
- [ ] Redémarrage du serveur
- [ ] Monitoring post-déploiement
- [ ] Tests de régression

## 🎯 RÉSULTATS ATTENDUS

Après le déploiement, vous devriez avoir :
- ✅ **Intégration automatique** des avances dans le système de paiement
- ✅ **Interface utilisateur** améliorée avec messages clairs
- ✅ **Logique temporelle** correcte (mois actuel = en cours)
- ✅ **Format des dates** correct (2025 au lieu de 0225)
- ✅ **Statuts cohérents** (active par défaut)
- ✅ **Compteurs réalistes** (pas de valeurs négatives)

---

**Date de création** : 09/10/2025  
**Version** : 2.0  
**Statut** : Prêt pour la production
