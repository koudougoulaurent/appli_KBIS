# Gestion des Types de Propriétés - Architecture Améliorée

## Problème Résolu

Le système précédent ne distinguait pas les deux types de gestion de propriétés :
1. **Propriété louable en une seule fois** (maison entière, appartement complet)
2. **Propriété avec unités locatives multiples** (colocation, appartement partagé, immeuble)

Cela causait le problème où les pièces apparaissaient comme "disponibles" individuellement même quand la propriété entière était louée.

## Solution Implémentée

### 1. Nouveau Champ `type_gestion` dans le Modèle Propriete

```python
TYPE_GESTION_CHOICES = [
    ('propriete_entiere', 'Propriété entière (louable en une seule fois)'),
    ('unites_multiples', 'Propriété avec unités locatives multiples'),
]

type_gestion = models.CharField(
    max_length=20,
    choices=TYPE_GESTION_CHOICES,
    default='propriete_entiere',
    verbose_name=_("Type de gestion"),
    help_text=_("Définit si la propriété est louable entièrement ou par unités multiples")
)
```

### 2. Méthodes Utilitaires Ajoutées au Modèle Propriete

```python
def est_propriete_entiere(self):
    """Vérifie si c'est une propriété louable entièrement."""
    return self.type_gestion == 'propriete_entiere'

def est_avec_unites_multiples(self):
    """Vérifie si c'est une propriété avec unités locatives multiples."""
    return self.type_gestion == 'unites_multiples'

def get_pieces_louables_individuellement(self):
    """Retourne les pièces qui peuvent être louées individuellement."""
    if not self.est_avec_unites_multiples():
        return self.pieces.none()
    return self.pieces.filter(
        unite_locative__isnull=True,
        is_deleted=False
    )

def get_unites_locatives(self):
    """Retourne les unités locatives de cette propriété."""
    if not self.est_avec_unites_multiples():
        return self.unites_locatives.none()
    return self.unites_locatives.filter(is_deleted=False)
```

### 3. Logique de Disponibilité Améliorée

La méthode `est_disponible_pour_location()` a été modifiée pour tenir compte du type de gestion :

```python
def est_disponible_pour_location(self):
    if self.est_propriete_entiere():
        # Pour une propriété entière, vérifier s'il n'y a pas de contrat actif
        contrats_actifs = Contrat.objects.filter(
            propriete=self,
            est_actif=True,
            est_resilie=False,
            date_debut__lte=timezone.now().date(),
            date_fin__gte=timezone.now().date(),
            is_deleted=False,
            unite_locative__isnull=True  # Pas d'unité locative = propriété complète
        ).exists()
        
        return self.disponible and not contrats_actifs
        
    elif self.est_avec_unites_multiples():
        # Pour les propriétés avec unités multiples, vérifier les unités et pièces disponibles
        unites_disponibles = self.get_unites_locatives().filter(
            statut='disponible'
        ).exclude(
            contrats__est_actif=True,
            contrats__est_resilie=False,
            contrats__date_debut__lte=timezone.now().date(),
            contrats__date_fin__gte=timezone.now().date(),
            contrats__is_deleted=False
        ).exists()
        
        pieces_disponibles = self.get_pieces_louables_individuellement().filter(
            statut='disponible'
        ).exclude(
            contrats__est_actif=True,
            contrats__est_resilie=False,
            contrats__date_debut__lte=timezone.now().date(),
            contrats__date_fin__gte=timezone.now().date(),
            contrats__is_deleted=False
        ).exists()
        
        return unites_disponibles or pieces_disponibles
    
    return False
```

### 4. Méthodes Ajoutées au Modèle Piece

```python
def peut_etre_louee_individuellement(self):
    """Détermine si cette pièce peut être louée individuellement."""
    return (
        self.propriete.est_avec_unites_multiples() and
        self.unite_locative is None and
        not self.est_espace_partage
    )

def est_dans_propriete_entiere(self):
    """Détermine si cette pièce fait partie d'une propriété louable entièrement."""
    return self.propriete.est_propriete_entiere()

def get_statut_affichage(self):
    """Retourne le statut d'affichage de la pièce selon le type de propriété."""
    if self.est_dans_propriete_entiere():
        return "incluse dans la propriété"
    else:
        return self.get_statut_display()

def est_vraiment_disponible(self):
    """Vérifie si la pièce est vraiment disponible pour location."""
    if self.est_dans_propriete_entiere():
        return False
    
    if not self.peut_etre_louee_individuellement():
        return False
        
    # Vérifier s'il n'y a pas de contrat actif sur cette pièce
    contrats_actifs = Contrat.objects.filter(
        pieces=self,
        est_actif=True,
        est_resilie=False,
        date_debut__lte=timezone.now().date(),
        date_fin__gte=timezone.now().date(),
        is_deleted=False
    ).exists()
    
    return self.statut == 'disponible' and not contrats_actifs
```

### 5. Formulaire Mis à Jour

Le formulaire `ProprieteForm` a été mis à jour pour inclure le champ `type_gestion` :

```python
fields = [
    'numero_propriete', 'titre', 'adresse', 'code_postal', 'ville', 'pays',
    'type_bien', 'type_gestion', 'bailleur', 'surface', 'nombre_pieces', 
    'nombre_chambres', 'nombre_salles_bain',
    'ascenseur', 'parking', 'balcon', 'jardin',
    'prix_achat', 'loyer_actuel', 'charges_locataire',
    'etat', 'disponible', 'notes'
]
```

## Cas d'Usage

### Cas 1 : Propriété Entière (type_gestion = 'propriete_entiere')
- **Exemple** : Maison familiale, appartement T3 complet
- **Comportement** : 
  - La propriété se loue en une seule fois
  - Les pièces ne sont pas louables individuellement
  - Le statut des pièces affiche "incluse dans la propriété"
  - La disponibilité se base sur l'absence de contrat actif sur la propriété complète

### Cas 2 : Propriété avec Unités Multiples (type_gestion = 'unites_multiples')
- **Exemple** : Colocation, appartement partagé, immeuble avec plusieurs unités
- **Comportement** :
  - Les unités locatives peuvent être louées individuellement
  - Les pièces non liées à une unité peuvent être louées individuellement
  - Les espaces partagés (cuisine, salon) ne sont pas louables individuellement
  - La disponibilité se base sur les unités et pièces disponibles

## Migration

Une migration a été créée pour ajouter le champ `type_gestion` :

```python
# proprietes/migrations/0022_add_type_gestion_to_propriete.py
operations = [
    migrations.AddField(
        model_name='propriete',
        name='type_gestion',
        field=models.CharField(
            choices=[
                ('propriete_entiere', 'Propriété entière (louable en une seule fois)'),
                ('unites_multiples', 'Propriété avec unités locatives multiples'),
            ],
            default='propriete_entiere',
            help_text='Définit si la propriété est louable entièrement ou par unités multiples',
            max_length=20,
            verbose_name='Type de gestion'
        ),
    ),
]
```

## Avantages

1. **Clarté** : Distinction claire entre les deux types de gestion
2. **Logique métier** : Respect des règles de location selon le type de propriété
3. **Interface utilisateur** : Affichage approprié du statut des pièces
4. **Évolutivité** : Architecture extensible pour de futurs types de gestion
5. **Rétrocompatibilité** : Valeur par défaut 'propriete_entiere' pour les propriétés existantes

## Utilisation

Lors de la création d'une propriété, l'utilisateur doit maintenant choisir :
- **"Propriété entière"** : Pour les maisons, appartements complets
- **"Propriété avec unités multiples"** : Pour les colocations, appartements partagés

Cette distinction permet au système de gérer correctement la disponibilité et l'affichage des pièces selon le contexte d'usage.
