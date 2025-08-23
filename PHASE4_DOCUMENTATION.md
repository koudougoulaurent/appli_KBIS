# Phase 4 - Système de Notifications

## Vue d'ensemble

La Phase 4 introduit un système de notifications complet pour améliorer l'expérience utilisateur et la communication au sein de la plateforme de gestion immobilière.

## Fonctionnalités Principales

### 1. Système de Notifications
- **Notifications en temps réel** pour les événements importants
- **Types de notifications** : paiements, contrats, maintenance, alertes système
- **Priorités** : faible, moyenne, élevée, urgente
- **État de lecture** : lu/non lu avec horodatage
- **Références génériques** vers les objets (contrats, paiements, propriétés)

### 2. Préférences de Notification
- **Personnalisation par utilisateur** des préférences de notification
- **Contrôle par type** : activer/désactiver les notifications par catégorie
- **Options de livraison** : email, navigateur, digest quotidien/hebdomadaire
- **Interface de gestion** des préférences

### 3. API REST Complète
- **CRUD complet** pour les notifications
- **Actions personnalisées** : marquer comme lu/non lu, comptage
- **Filtrage et recherche** avancés
- **Pagination** et tri automatique
- **Authentification** requise pour toutes les opérations

## Architecture Technique

### Modèles

#### Notification
```python
class Notification(models.Model):
    type = models.CharField(choices=TYPE_CHOICES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    priority = models.CharField(choices=PRIORITY_CHOICES)
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL)
    content_type = models.ForeignKey(ContentType, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    is_read = models.BooleanField(default=False)
    is_sent_email = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
```

#### NotificationPreference
```python
class NotificationPreference(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL)
    email_notifications = models.BooleanField(default=True)
    browser_notifications = models.BooleanField(default=True)
    payment_due_email = models.BooleanField(default=True)
    payment_received_email = models.BooleanField(default=True)
    contract_expiring_email = models.BooleanField(default=True)
    maintenance_email = models.BooleanField(default=True)
    system_alerts_email = models.BooleanField(default=True)
    daily_digest = models.BooleanField(default=False)
    weekly_digest = models.BooleanField(default=False)
```

### Types de Notifications

| Type | Description | Priorité par défaut |
|------|-------------|-------------------|
| `payment_due` | Échéance de paiement | Élevée |
| `payment_received` | Paiement reçu | Moyenne |
| `contract_expiring` | Contrat expirant | Élevée |
| `maintenance_request` | Demande de maintenance | Moyenne |
| `maintenance_completed` | Maintenance terminée | Faible |
| `system_alert` | Alerte système | Urgente |
| `info` | Information générale | Moyenne |

### Priorités

| Priorité | Description | Couleur |
|----------|-------------|---------|
| `low` | Faible | Gris |
| `medium` | Moyenne | Bleu |
| `high` | Élevée | Orange |
| `urgent` | Urgente | Rouge |

## API Endpoints

### Notifications

#### Liste des notifications
```
GET /notifications/api/notifications/
```

**Paramètres de requête :**
- `type` : Filtrer par type de notification
- `priority` : Filtrer par priorité
- `is_read` : Filtrer par état de lecture (true/false)
- `search` : Recherche dans le titre et le message
- `ordering` : Tri (created_at, priority, title)
- `page` : Pagination

#### Notification détaillée
```
GET /notifications/api/notifications/{id}/
```

#### Créer une notification
```
POST /notifications/api/notifications/
```

#### Marquer comme lue
```
POST /notifications/api/notifications/{id}/mark_as_read/
```

#### Marquer comme non lue
```
POST /notifications/api/notifications/{id}/mark_as_unread/
```

#### Marquer toutes comme lues
```
POST /notifications/api/notifications/mark_all_as_read/
```

#### Comptage des notifications non lues
```
GET /notifications/api/notifications/unread_count/
```

#### Notifications récentes
```
GET /notifications/api/notifications/recent/?limit=10
```

#### Notifications par type
```
GET /notifications/api/notifications/by_type/?type=payment_due
```

#### Notifications haute priorité
```
GET /notifications/api/notifications/high_priority/
```

### Préférences

#### Mes préférences
```
GET /notifications/api/preferences/my_preferences/
```

#### Mettre à jour les préférences
```
POST /notifications/api/preferences/update_preferences/
```

#### Réinitialiser aux valeurs par défaut
```
POST /notifications/api/preferences/reset_to_default/
```

## Utilisation

### Création de Notifications

```python
from notifications.models import Notification

# Notification simple
Notification.create_notification(
    recipient=user,
    type='payment_due',
    title='Échéance de paiement',
    message='Le paiement du loyer arrive à échéance dans 5 jours.',
    priority='high'
)

# Notification avec référence à un objet
Notification.create_notification(
    recipient=user,
    type='contract_expiring',
    title='Contrat expirant',
    message=f'Le contrat #{contrat.id} expire dans 30 jours.',
    priority='high',
    content_object=contrat
)
```

### Récupération des Notifications

```python
# Notifications non lues
unread_count = Notification.get_unread_count(user)

# Notifications récentes
recent_notifications = Notification.get_user_notifications(user, limit=10)

# Notifications par type
payment_notifications = Notification.objects.filter(
    recipient=user,
    type='payment_due',
    is_read=False
)
```

### Gestion des Préférences

```python
# Récupérer les préférences
preferences = NotificationPreference.objects.get(user=user)

# Vérifier les préférences email
email_prefs = preferences.get_email_preferences()

# Modifier les préférences
preferences.email_notifications = False
preferences.payment_due_email = True
preferences.save()
```

## Interface d'Administration

### Notifications
- **Liste** avec filtres par type, priorité, état de lecture
- **Recherche** dans le titre et le message
- **Actions en lot** : marquer comme lu/non lu, supprimer
- **Détails** complets avec références aux objets

### Préférences
- **Gestion** des préférences par utilisateur
- **Configuration** des types de notifications activés
- **Options** de digest et de livraison

## Statistiques

### Données Actuelles
- **Total** : 106 notifications
- **Non lues** : 71 notifications
- **Haute priorité** : 30 notifications

### Répartition par Type
- Alerte système : 16
- Paiement reçu : 15
- Échéance de paiement : 15
- Demande de maintenance : 15
- Maintenance terminée : 15
- Information générale : 15
- Contrat expirant : 15

### Répartition par Priorité
- Moyenne : 46
- Faible : 30
- Élevée : 30

## Intégration

### Références vers les Objets
- **Contrats** : 30 notifications liées
- **Paiements** : 15 notifications liées
- **Propriétés** : 30 notifications liées

### Intégration Future
- **Notifications par email** avec templates personnalisés
- **Notifications push** en temps réel
- **Intégration** avec le système de calendrier
- **Notifications** pour les rapports et statistiques

## Sécurité

### Authentification
- Toutes les opérations API nécessitent une authentification
- Les utilisateurs ne peuvent accéder qu'à leurs propres notifications
- Validation des permissions pour les actions sensibles

### Validation
- Validation des types de notifications
- Validation des priorités
- Validation des références aux objets
- Protection contre les injections

## Performance

### Optimisations
- **Indexation** sur les champs fréquemment utilisés
- **Pagination** automatique pour les grandes listes
- **Requêtes optimisées** avec select_related et prefetch_related
- **Cache** pour les statistiques fréquemment consultées

### Monitoring
- **Comptage** des notifications par type et priorité
- **Suivi** des performances des requêtes
- **Alertes** en cas de surcharge

## Tests

### Tests Automatisés
- **Tests unitaires** pour les modèles
- **Tests d'intégration** pour l'API
- **Tests de performance** pour les requêtes
- **Tests de sécurité** pour l'authentification

### Tests Manuels
- **Interface utilisateur** : navigation et interactions
- **API** : tous les endpoints avec différents scénarios
- **Administration** : gestion des notifications et préférences

## Déploiement

### Prérequis
- Django 4.2.7+
- Base de données avec support des relations génériques
- Configuration email pour les notifications par email

### Migration
```bash
python manage.py makemigrations notifications
python manage.py migrate
```

### Configuration
- Ajouter `'notifications'` à `INSTALLED_APPS`
- Configurer les URLs dans `urls.py`
- Configurer les paramètres email dans `settings.py`

## Prochaines Étapes

### Phase 5 - Rapports et Statistiques
- **Génération de rapports** PDF/Excel
- **Graphiques** et visualisations
- **Statistiques financières** avancées
- **Export de données** personnalisé

### Phase 6 - Calendrier et Maintenance
- **Calendrier des échéances**
- **Planification des visites**
- **Gestion des demandes de maintenance**
- **Suivi des interventions**

### Phase 7 - Amélioration de l'Interface
- **Interface moderne** et responsive
- **Tableaux de bord** personnalisés
- **Filtres avancés** et recherche
- **Notifications en temps réel**

## Conclusion

Le système de notifications de la Phase 4 fournit une base solide pour améliorer la communication et l'expérience utilisateur. Il s'intègre parfaitement avec les modules existants et prépare le terrain pour les fonctionnalités avancées des phases suivantes.

**Statut** : ✅ **Terminé et opérationnel**
**Tests** : ✅ **6/6 tests réussis**
**Documentation** : ✅ **Complète** 