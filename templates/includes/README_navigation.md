# Composants de Navigation pour le Module Propriétés

Ce dossier contient des composants de navigation réutilisables pour assurer une expérience utilisateur cohérente et professionnelle dans le module propriétés.

## Composants Disponibles

### 1. `navigation_buttons.html` - Navigation Complète
Composant principal pour les pages avec titre, sous-titre et boutons d'action.

**Utilisation :**
```html
{% include 'includes/navigation_buttons.html' with 
    page_title="Titre de la page"
    page_subtitle="Sous-titre descriptif"
    back_url='proprietes:liste'
    back_text="Retour à la liste"
    show_dashboard_button=True
    show_list_button=True %}
```

**Paramètres disponibles :**
- `page_title` : Titre principal de la page
- `page_subtitle` : Sous-titre descriptif
- `back_url` : URL de retour (obligatoire)
- `back_text` : Texte du bouton retour (défaut: "Retour")
- `show_dashboard_button` : Afficher le bouton Dashboard
- `show_list_button` : Afficher le bouton Liste
- `action_buttons` : Liste de boutons d'action personnalisés
- `breadcrumbs` : Fil d'Ariane personnalisé

### 2. `back_button.html` - Boutons de Retour Rapides
Composant simple pour les boutons de retour avec options supplémentaires.

**Utilisation :**
```html
{% include 'includes/back_button.html' with 
    back_url='proprietes:dashboard' 
    back_text="Retour au dashboard"
    show_list=True
    show_bailleurs=True
    show_locataires=True %}
```

**Paramètres disponibles :**
- `back_url` : URL de retour (obligatoire)
- `back_text` : Texte du bouton retour
- `button_style` : Style du bouton (secondary, primary, success, warning, info, danger)
- `show_dashboard` : Afficher le bouton Dashboard
- `show_list` : Afficher le bouton Liste des propriétés
- `show_bailleurs` : Afficher le bouton Bailleurs
- `show_locataires` : Afficher le bouton Locataires
- `show_charges` : Afficher le bouton Charges bailleur
- `custom_buttons` : Boutons personnalisés

## Exemples d'Utilisation

### Page de détail d'une propriété
```html
{% include 'includes/navigation_buttons.html' with 
    page_title=propriete.titre
    page_subtitle=propriete.get_adresse_complete
    back_url='proprietes:liste'
    back_text="Retour à la liste"
    show_dashboard_button=True %}
```

### Formulaire d'ajout/modification
```html
{% include 'includes/navigation_buttons.html' with 
    page_title="Ajouter une propriété"
    page_subtitle="Remplissez les informations de la propriété"
    back_url='proprietes:liste'
    back_text="Retour à la liste"
    show_dashboard_button=True
    show_list_button=True %}
```

### Page avec boutons de retour multiples
```html
{% include 'includes/back_button.html' with 
    back_url='proprietes:detail'
    back_text="Retour à la propriété"
    show_dashboard=True
    show_list=True
    show_bailleurs=True %}
```

## Styles et Personnalisation

### Couleurs des boutons
- `secondary` : Gris (défaut)
- `primary` : Bleu
- `success` : Vert
- `warning` : Jaune
- `info` : Bleu clair
- `danger` : Rouge
- `outline` : Contour avec fond transparent

### Responsive Design
Les composants s'adaptent automatiquement aux écrans mobiles :
- Boutons empilés verticalement sur mobile
- Taille de police réduite
- Espacement optimisé

### Animations
- Effet de survol avec élévation
- Transition fluide des couleurs
- Effet de brillance au survol

## Intégration avec Bootstrap

Les composants utilisent les classes Bootstrap 5 et sont compatibles avec :
- Grille responsive
- Composants Bootstrap (cards, buttons, etc.)
- Icônes Bootstrap Icons
- Utilitaires de couleur et d'espacement

## Bonnes Pratiques

1. **Cohérence** : Utilisez toujours le même composant pour des pages similaires
2. **Accessibilité** : Les boutons incluent des icônes et des textes descriptifs
3. **Responsive** : Testez sur différents écrans
4. **Performance** : Les composants sont légers et optimisés
5. **Maintenance** : Centralisez les modifications dans ces composants

## Personnalisation Avancée

### Ajout de boutons d'action personnalisés
```html
{% include 'includes/navigation_buttons.html' with 
    page_title="Gestion des photos"
    action_buttons=action_buttons_list %}
```

Dans votre vue Django :
```python
context['action_buttons_list'] = [
    {
        'url': 'proprietes:photo_create',
        'text': 'Ajouter Photo',
        'style': 'success',
        'icon': 'plus-circle'
    },
    {
        'url': 'proprietes:photo_gallery',
        'text': 'Voir Galerie',
        'style': 'info',
        'icon': 'images'
    }
]
```

### Fil d'Ariane personnalisé
```python
context['breadcrumbs_example'] = [
    {'url': 'proprietes:dashboard', 'text': 'Dashboard'},
    {'url': 'proprietes:liste', 'text': 'Propriétés'},
    {'url': 'proprietes:detail', 'text': 'Détail Propriété'},
    {'text': 'Modifier'}  # Page courante
]
```

## Support et Maintenance

Pour toute question ou modification :
1. Vérifiez la compatibilité avec Bootstrap 5
2. Testez sur différents navigateurs
3. Maintenez la cohérence visuelle
4. Documentez les nouvelles fonctionnalités
