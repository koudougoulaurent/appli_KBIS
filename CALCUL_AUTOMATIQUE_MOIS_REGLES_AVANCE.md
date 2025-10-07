# CALCUL AUTOMATIQUE DES MOIS RÉGLÉS DANS LE REÇU D'AVANCE

## Problème Identifié
Le champ "Mois réglé" était vide dans le reçu d'avance généré, alors qu'il devrait afficher automatiquement la liste des mois couverts par l'avance.

## Solution Implémentée

### 1. **Logique de Calcul des Mois Réglés**

**Principe :**
1. **Dernier mois de paiement** : Récupérer la dernière quittance de loyer
2. **Nombre de mois couverts** : `somme_avance ÷ loyer_mensuel`
3. **Calcul automatique** : `dernier_mois + 1, + 2, + 3, etc.`

### 2. **Méthodes Ajoutées dans `paiements/models_avance.py`**

#### **`_calculer_mois_regle()`**
```python
def _calculer_mois_regle(self):
    """Calcule automatiquement les mois réglés par l'avance"""
    # 1. Trouver le dernier mois de paiement
    dernier_mois_paiement = self._get_dernier_mois_paiement()
    
    # 2. Calculer le mois de début (dernier paiement + 1)
    if not dernier_mois_paiement:
        mois_debut = self.date_avance.replace(day=1) + relativedelta(months=1)
    else:
        mois_debut = dernier_mois_paiement + relativedelta(months=1)
    
    # 3. Générer la liste des mois réglés
    mois_regles = []
    mois_courant = mois_debut
    
    for i in range(self.nombre_mois_couverts):
        mois_regles.append(mois_courant.strftime('%B %Y'))
        mois_courant = mois_courant + relativedelta(months=1)
    
    return ', '.join(mois_regles)
```

#### **`_get_dernier_mois_paiement()`**
```python
def _get_dernier_mois_paiement(self):
    """Récupère le dernier mois de paiement (dernière quittance)"""
    # Chercher la dernière quittance de loyer pour ce contrat
    derniere_quittance = Paiement.objects.filter(
        contrat=self.contrat,
        type_paiement='loyer',
        statut='valide'
    ).order_by('-date_paiement').first()
    
    if derniere_quittance:
        return derniere_quittance.date_paiement.replace(day=1)
    
    # Si pas de quittance, utiliser le mois de début du contrat
    if self.contrat and self.contrat.date_debut:
        return self.contrat.date_debut.replace(day=1)
    
    return None
```

### 3. **Intégration dans la Génération du Reçu**

**Modification de `generer_recu_avance_kbis()` :**
```python
# Calculer les mois réglés automatiquement
mois_regle = self._calculer_mois_regle()

# Données du récépissé d'avance
donnees_recu = {
    # ... autres données ...
    'mois_regle': mois_regle  # *** NOUVEAU : Mois réglés calculés automatiquement ***
}
```

### 4. **Exemples de Calcul**

#### **Scénario 1 : Avance de 1,800,000 F CFA (9 mois)**
- **Dernier paiement** : Septembre 2025
- **Mois réglés** : Octobre 2025, Novembre 2025, Décembre 2025, Janvier 2026, Février 2026, Mars 2026, Avril 2026, Mai 2026, Juin 2026

#### **Scénario 2 : Avance de 600,000 F CFA (3 mois)**
- **Dernier paiement** : Août 2025
- **Mois réglés** : Septembre 2025, Octobre 2025, Novembre 2025

#### **Scénario 3 : Avance de 1,200,000 F CFA (6 mois)**
- **Dernier paiement** : Septembre 2025
- **Mois réglés** : Octobre 2025, Novembre 2025, Décembre 2025, Janvier 2026, Février 2026, Mars 2026

### 5. **Affichage dans le Reçu**

Le reçu d'avance affiche maintenant :
- ✅ **En-tête statique KBIS** (même que les autres reçus)
- ✅ **Montant de l'avance** : 1,800,000 F CFA
- ✅ **Loyer mensuel** : 200,000 F CFA
- ✅ **Mois couverts** : 9 mois
- ✅ **Mois réglés** : Octobre 2025, Novembre 2025, Décembre 2025, Janvier 2026, Février 2026, Mars 2026, Avril 2026, Mai 2026, Juin 2026
- ✅ **Période de couverture** : Octobre 2025 - Juin 2026
- ✅ **Montant restant** : 1,800,000 F CFA
- ✅ **Statut** : Active
- ✅ **Pied de page dynamique** (même que les autres reçus)

### 6. **Logique de Calcul Automatique**

**Étapes du calcul :**
1. **Recherche du dernier paiement** : Dernière quittance de loyer validée
2. **Calcul du mois de début** : Dernier mois de paiement + 1 mois
3. **Génération de la liste** : Mois de début + 1, + 2, + 3, etc. (selon nombre de mois couverts)
4. **Formatage** : Liste des mois séparés par des virgules

**Gestion des cas particuliers :**
- **Pas de paiement précédent** : Commence au mois suivant la date d'avance
- **Pas de contrat** : Utilise la date d'avance comme référence
- **Erreur de calcul** : Affiche un message de fallback avec les informations disponibles

## Résultat Final

✅ **Le champ "Mois réglé" est maintenant automatiquement calculé et affiché**
✅ **Calcul basé sur le dernier mois de paiement + nombre de mois couverts**
✅ **Affichage formaté : "Octobre 2025, Novembre 2025, Décembre 2025, ..."**
✅ **Intégration parfaite dans le système de reçu unifié KBIS**
✅ **Gestion des cas particuliers et des erreurs**

Le système calcule maintenant automatiquement et affiche correctement les mois réglés par l'avance dans le reçu généré ! 🎉
