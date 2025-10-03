# 🖼️ Guide d'intégration de l'image d'en-tête/pied de page

## 📁 Structure créée

```
static/
└── images/
    └── header_footer/
        ├── entetepieddepage.png  ← Votre image ici
        └── README.md

templates/
└── includes/
    ├── header_footer.html        ← En-tête + pied de page
    ├── header_only.html          ← En-tête uniquement
    └── footer_only.html          ← Pied de page uniquement
```

## 🔧 Comment utiliser

### 1. **Placer votre image**
- Copiez votre fichier `entetepieddepage.png` dans le dossier `static/images/header_footer/`
- L'image sera automatiquement utilisée dans tous les templates

### 2. **Utilisation automatique**
L'image est déjà intégrée dans `templates/base.html` :
- ✅ **En-tête** : Affiché en haut de chaque page
- ✅ **Pied de page** : Affiché en bas de chaque page

### 3. **Utilisation manuelle dans d'autres templates**

#### En-tête uniquement :
```html
{% include 'includes/header_only.html' %}
```

#### Pied de page uniquement :
```html
{% include 'includes/footer_only.html' %}
```

#### En-tête + pied de page :
```html
{% include 'includes/header_footer.html' %}
```

## 🎨 Personnalisation

### Modifier la taille de l'image
Éditez les fichiers dans `templates/includes/` et modifiez :
```css
.header-image, .footer-image {
    max-height: 150px;  /* Ajustez cette valeur */
}
```

### Modifier le style
Les images ont les classes CSS suivantes :
- `.kbis-header-only` - Conteneur de l'en-tête
- `.kbis-footer-only` - Conteneur du pied de page
- `.header-image` - Image d'en-tête
- `.footer-image` - Image de pied de page

## 📱 Responsive
L'image s'adapte automatiquement :
- **Desktop** : Hauteur max 150px
- **Mobile** : Hauteur max 100px

## ✅ Vérification
1. Placez votre image `entetepieddepage.png` dans `static/images/header_footer/`
2. Redémarrez le serveur Django
3. Visitez n'importe quelle page de l'application
4. L'image devrait apparaître en haut et en bas de la page

## 🔄 Mise à jour de l'image
Pour changer l'image :
1. Remplacez le fichier `entetepieddepage.png`
2. Rafraîchissez la page (Ctrl+F5)
3. L'image sera automatiquement mise à jour

## 🎯 Résultat attendu
- **En-tête** : Image centrée en haut de chaque page
- **Pied de page** : Image centrée en bas de chaque page
- **Responsive** : Adaptation automatique sur mobile
- **Performance** : Chargement optimisé avec `img-fluid`
