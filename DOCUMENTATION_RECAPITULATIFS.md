# 📊 SYSTÈME DE RÉCAPITULATIFS MENSUELS - DOCUMENTATION COMPLÈTE

## 🎯 Vue d'ensemble

Le système de récapitulatifs mensuels permet de générer automatiquement des rapports financiers détaillés pour chaque bailleur, incluant les loyers, charges, paiements et totaux nets. Le système inclut la génération de PDF professionnels avec en-tête personnalisé et pied de page dynamique.

## 🏗️ Architecture du système

### Modèles de données

#### 1. RecapMensuel (paiements/models.py)
```python
class RecapMensuel(models.Model):
    bailleur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE)
    mois = models.IntegerField()
    annee = models.IntegerField()
    total_loyers = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_charges = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_paiements = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_net_a_payer = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='en_attente')
    date_creation = models.DateTimeField(auto_now_add=True)
    est_supprime = models.BooleanField(default=False)
```

### Méthodes principales

#### 1. Calcul des totaux
- `calculer_totaux_bailleur()` : Calcule les totaux pour un bailleur spécifique
- `calculer_totaux_globaux()` : Retourne un dictionnaire des totaux calculés
- `get_proprietes_details()` : Récupère les détails des propriétés et contrats

#### 2. Génération PDF
- `generer_pdf_recapitulatif()` : Génère le PDF avec en-tête Base64 et pied dynamique
- `get_nom_fichier_pdf()` : Génère un nom de fichier professionnel

## 🔧 Configuration technique

### 1. Settings Django
```python
# gestion_immobiliere/settings_simple.py
CONTEXT_PROCESSORS = [
    'core.context_processors.entreprise_config',
    'core.context_processors.dynamic_navigation',
]
```

### 2. URLs
```python
# paiements/urls.py
urlpatterns = [
    path('recaps/', views.liste_recaps_mensuels, name='liste_recaps_mensuels'),
    path('recap/<int:recap_id>/', views.detail_recap_mensuel, name='detail_recap_mensuel'),
    path('recap/creer/', views.creer_recap_mensuel, name='creer_recap_mensuel'),
    path('recap/<int:recap_id>/imprimer/', views.imprimer_recap_mensuel, name='imprimer_recap_mensuel'),
    path('recap/<int:recap_id>/supprimer/', views.supprimer_recap_mensuel, name='supprimer_recap_mensuel'),
    path('recap/<int:recap_id>/restaurer/', views.restaurer_recap_mensuel, name='restaurer_recap_mensuel'),
    path('recaps/supprimes/', views.liste_recaps_supprimes, name='liste_recaps_supprimes'),
]
```

## 🎨 Interface utilisateur

### 1. Templates principaux
- `liste_recaps_mensuels.html` : Liste des récapitulatifs avec actions
- `detail_recap_mensuel.html` : Détail d'un récapitulatif avec bouton suppression
- `recaps_supprimes.html` : Liste des récapitulatifs supprimés
- `confirmer_suppression_recap.html` : Confirmation de suppression

### 2. Templates PDF
- `recapitulatif_mensuel_pdf.html` : Template principal avec en-tête Base64
- `recapitulatif_mensuel_simple.html` : Template de fallback

### 3. Permissions
- **Superusers** : Accès complet (création, modification, suppression)
- **Groupe PRIVILEGE** : Accès complet (création, modification, suppression)
- **Autres groupes** : Lecture seule

## 📊 Structure de la base de données

### Tables impliquées
1. **paiements_recapmensuel** : Table principale des récapitulatifs
2. **contrats_contrat** : Contrats de location
3. **paiements_paiement** : Paiements effectués
4. **proprietes_propriete** : Propriétés immobilières
5. **auth_user** : Utilisateurs (bailleurs)
6. **auth_group** : Groupes d'utilisateurs

### Relations
- `RecapMensuel.bailleur` → `Utilisateur`
- `Contrat.propriete` → `Propriete`
- `Contrat.bailleur` → `Utilisateur`
- `Paiement.contrat` → `Contrat`

## 🔄 Flux de données

### 1. Création d'un récapitulatif
1. Sélection du bailleur et période
2. Calcul automatique des totaux
3. Sauvegarde en base de données
4. Génération du PDF

### 2. Calcul des totaux
1. Récupération des contrats actifs pour la période
2. Calcul des loyers et charges mensuels
3. Récupération des paiements confirmés
4. Calcul du net à payer

### 3. Génération PDF
1. Conversion de l'image d'en-tête en Base64
2. Récupération des données d'entreprise
3. Rendu du template HTML
4. Conversion en PDF avec xhtml2pdf

## 🛠️ Dépendances techniques

### Python packages
- `Django` : Framework web
- `xhtml2pdf` : Génération de PDF
- `Pillow` : Traitement d'images
- `decimal` : Calculs financiers précis

### Fichiers statiques
- `static/images/enteteEnImage.png` : Image d'en-tête des PDF
- Templates HTML dans `templates/paiements/`

## 🚀 Utilisation

### 1. Accès au système
- URL : `/paiements/recaps/`
- Permissions : Tous les utilisateurs authentifiés

### 2. Création d'un récapitulatif
1. Cliquer sur "Nouveau"
2. Sélectionner le bailleur
3. Choisir le mois et l'année
4. Cliquer sur "Générer"

### 3. Actions disponibles
- **Voir** : Consulter les détails
- **Imprimer** : Générer le PDF
- **Supprimer** : Suppression logique (superusers/PRIVILEGE)
- **Restaurer** : Restaurer un récapitulatif supprimé

## 🔒 Sécurité

### 1. Permissions
- Contrôle d'accès basé sur les groupes
- Suppression logique (pas de suppression physique)
- Validation des données d'entrée

### 2. Données sensibles
- Calculs financiers avec précision décimale
- Gestion des erreurs robuste
- Logs de débogage pour le diagnostic

## 📈 Performance

### 1. Optimisations
- Requêtes optimisées avec select_related
- Calculs en mémoire pour éviter les requêtes multiples
- Cache des données d'entreprise

### 2. Limitations
- Génération PDF synchrone
- Taille des images Base64 en mémoire

## 🐛 Dépannage

### Problèmes courants
1. **Récapitulatifs vides** : Vérifier les contrats actifs et paiements
2. **Bouton suppression invisible** : Vérifier les permissions utilisateur
3. **Erreur PDF** : Vérifier l'installation de xhtml2pdf
4. **Image d'en-tête** : Vérifier le chemin vers enteteEnImage.png

### Logs de débogage
- Utiliser `python manage.py shell` pour tester
- Vérifier les permissions avec les scripts de test
- Contrôler les données avec l'interface d'administration

## 📝 Changelog

### Version 1.0 (Octobre 2025)
- ✅ Système de récapitulatifs mensuels complet
- ✅ Génération PDF avec en-tête personnalisé
- ✅ Pied de page dynamique avec données d'entreprise
- ✅ Gestion des permissions et suppression logique
- ✅ Interface utilisateur responsive
- ✅ Calculs financiers précis
- ✅ Documentation complète

---

**Développé pour GESTIMMOB - Système de gestion immobilière**
