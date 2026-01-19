# CORRECTION : Génération de Quittances KBIS A5 pour les Paiements de Reliquat

## 🎯 Problème Identifié

Le système de paiements partiels ne générait pas correctement les quittances KBIS A5 pour les paiements de complétion de reliquat avec les mentions appropriées :
- ❌ Pas de distinction entre paiement partiel initial et paiement de reliquat
- ❌ Titre de document générique "QUITTANCE DE PAIEMENT" pour tous les cas
- ❌ Informations insuffisantes sur le statut du reliquat (complet ou partiel)
- ❌ Pas de mention claire "PAIEMENT DE RELIQUAT" ou "COMPLETION DE RELIQUAT"

## ✅ Corrections Apportées

### 1. Détection Automatique des Paiements de Reliquat
**Fichier :** `paiements/services_document_unifie_complet.py`

**Modifications dans `_prepare_paiement_context()` :**

```python
# NOUVEAU : Détecter si c'est un paiement de complétion de reliquat
est_reliquat = False
date_paiement_initial = None
numero_paiement_dans_sequence = 1

# Méthode 1 : Vérifier les notes
notes_paiement = getattr(paiement, 'notes', '') or ''
if 'complétion' in notes_paiement.lower() or 'reliquat' in notes_paiement.lower():
    est_reliquat = True

# Méthode 2 : Si ce n'est pas le premier paiement du mois
if paiements_partiels_mois.count() > 1:
    # Trouver la position de ce paiement dans la séquence
    for index, p in enumerate(paiements_partiels_mois, start=1):
        if p.id == paiement.id:
            numero_paiement_dans_sequence = index
            if index > 1:
                est_reliquat = True
                # Récupérer le premier paiement de la séquence
                premier_paiement = paiements_partiels_mois.first()
                if premier_paiement:
                    date_paiement_initial = premier_paiement.date_paiement
            break

info_paiement_partiel = {
    # ... autres champs ...
    # NOUVEAU : Informations de reliquat
    'est_reliquat': est_reliquat,
    'date_paiement_initial': date_paiement_initial,
    'numero_paiement_dans_sequence': numero_paiement_dans_sequence,
}
```

### 2. Modification Automatique du Titre de Document
**Fichier :** `paiements/services_document_unifie_complet.py`

**Modifications dans `generer_document_unifie()` :**

```python
# NOUVEAU : Modifier le titre si c'est un paiement de reliquat ou de complétion
if document_type.startswith('paiement_') and context.get('info_paiement_partiel'):
    info_partiel = context.get('info_paiement_partiel')
    if info_partiel.get('est_reliquat'):
        # C'est un paiement de complétion/reliquat
        if info_partiel.get('est_complet'):
            document_title = 'QUITTANCE DE PAIEMENT - COMPLETION DE RELIQUAT'
        else:
            document_title = 'QUITTANCE DE PAIEMENT - RELIQUAT PARTIEL'
    elif info_partiel.get('est_partiel'):
        # C'est le premier paiement partiel
        document_title = 'QUITTANCE DE PAIEMENT PARTIEL'
```

**Résultat :**
- ✅ "QUITTANCE DE PAIEMENT PARTIEL" pour le 1er paiement partiel
- ✅ "QUITTANCE DE PAIEMENT - RELIQUAT PARTIEL" pour un paiement de reliquat qui ne solde pas tout
- ✅ "QUITTANCE DE PAIEMENT - COMPLETION DE RELIQUAT" pour le paiement qui solde le reliquat

### 3. Amélioration des Templates de Quittance
**Fichiers :** 
- `templates/paiements/recu_quittance_unifie_a5.html`
- `templates/paiements/document_unifie_a5_complet.html`

**Modifications dans la section "Note" :**

```django
{% if est_paiement_partiel and info_paiement_partiel and info_paiement_partiel.est_reliquat %}
    <strong style="color: #d9534f; font-size: 11px;">⚠️ PAIEMENT DE RELIQUAT / COMPLETION</strong><br>
    • Ce paiement constitue {% if info_paiement_partiel.est_complet %}la complétion finale{% else %}une complétion partielle{% endif %} du reliquat pour {{ paiement.mois_paye|default:"le mois courant" }}<br>
    {% if info_paiement_partiel.date_paiement_initial %}
    • Paiement initial du : {{ info_paiement_partiel.date_paiement_initial|date:'d/m/Y' }}<br>
    {% endif %}
    • Paiement n°{{ info_paiement_partiel.numero_paiement_dans_sequence }} sur {{ info_paiement_partiel.nombre_paiements }} pour ce mois<br>
    {% if info_paiement_partiel.est_complet %}
    • <strong style="color: #5cb85c;">✓ RELIQUAT ENTIÈREMENT SOLDÉ</strong>
    {% else %}
    • Reste à payer : <strong>{{ info_paiement_partiel.montant_restant|floatformat:0 }} F CFA</strong>
    {% endif %}
{% elif est_paiement_partiel and info_paiement_partiel %}
    <strong style="color: #f0ad4e;">⚠️ PAIEMENT PARTIEL</strong><br>
    • Paiement partiel reçu en bonne et due forme pour la période {{ paiement.mois_paye|default:"courante" }}<br>
    • Montant payé : {{ montant_total|floatformat:0 }} F CFA sur {{ info_paiement_partiel.montant_du_mois|floatformat:0 }} F CFA<br>
    • Reste à payer : <strong>{{ info_paiement_partiel.montant_restant|floatformat:0 }} F CFA</strong>
{% endif %}
```

**Informations affichées sur la quittance :**
- ✅ Indication claire "PAIEMENT DE RELIQUAT / COMPLETION"
- ✅ Date du paiement initial
- ✅ Numéro du paiement dans la séquence (ex: Paiement n°2 sur 3)
- ✅ Statut du reliquat (ENTIÈREMENT SOLDÉ ou Reste à payer)
- ✅ Montant restant dû si applicable

### 4. Correction de la Méthode de Génération
**Fichier :** `paiements/models.py`

**Remplacement de `generer_quittance_kbis_dynamique()` :**

Ancien système utilisant `document_kbis_unifie` (introuvable) → Nouveau système utilisant `DocumentUnifieA5ServiceComplet`

```python
def generer_quittance_kbis_dynamique(self, user=None):
    """Génère une quittance KBIS dynamique avec le format correct."""
    try:
        # CORRECTION : Utiliser le nouveau système unifié DocumentUnifieA5ServiceComplet
        from .services_document_unifie_complet import DocumentUnifieA5ServiceComplet
        
        # Déterminer le type de document selon le type de paiement
        document_type_map = {
            'loyer': 'paiement_quittance',
            'caution': 'paiement_caution',
            'avance': 'paiement_avance',
            'charges': 'paiement_quittance',
            'autre': 'paiement_quittance',
            'paiement_partiel': 'paiement_quittance',
        }
        
        # Déterminer le type de document
        document_type = document_type_map.get(self.type_paiement, 'paiement_quittance')
        
        # Si c'est un paiement partiel, utiliser le type approprié
        if self.est_paiement_partiel or self.type_paiement == 'paiement_partiel':
            document_type = 'paiement_quittance'
        
        # Générer le document avec le nouveau système
        service = DocumentUnifieA5ServiceComplet()
        html_content = service.generer_document_unifie(
            document_type=document_type,
            user=user,
            paiement_id=self.id
        )
        
        return html_content
        
    except Exception as e:
        import traceback
        print(f"❌ Erreur génération quittance KBIS: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return None
```

## 📋 Guide de Test

### Scénario de Test 1 : Paiement Partiel Initial

1. **Créer un paiement partiel pour un contrat**
   - Montant dû : 100 000 F CFA
   - Montant payé : 60 000 F CFA (1er paiement)

2. **Générer la quittance KBIS A5**
   - Accéder au paiement créé
   - Cliquer sur le bouton de génération de quittance

3. **Vérifier la quittance**
   - ✅ Titre : "QUITTANCE DE PAIEMENT PARTIEL"
   - ✅ Section "Note" avec "⚠️ PAIEMENT PARTIEL"
   - ✅ Montant payé : 60 000 F CFA sur 100 000 F CFA
   - ✅ Reste à payer : 40 000 F CFA

### Scénario de Test 2 : Complétion Partielle de Reliquat

1. **Compléter partiellement le reliquat**
   - Utiliser la vue "Compléter le Reliquat"
   - Ajouter un 2ème paiement de 20 000 F CFA
   - Total payé : 80 000 F CFA / 100 000 F CFA

2. **Générer la quittance KBIS A5**

3. **Vérifier la quittance**
   - ✅ Titre : "QUITTANCE DE PAIEMENT - RELIQUAT PARTIEL"
   - ✅ Section "Note" avec "⚠️ PAIEMENT DE RELIQUAT / COMPLETION"
   - ✅ "Ce paiement constitue une complétion partielle du reliquat pour [mois]"
   - ✅ Date du paiement initial affichée
   - ✅ "Paiement n°2 sur 2 pour ce mois"
   - ✅ Reste à payer : 20 000 F CFA

### Scénario de Test 3 : Complétion Finale du Reliquat

1. **Solder le reliquat**
   - Utiliser la vue "Compléter le Reliquat"
   - Ajouter un 3ème paiement de 20 000 F CFA
   - Total payé : 100 000 F CFA / 100 000 F CFA

2. **Générer la quittance KBIS A5**

3. **Vérifier la quittance**
   - ✅ Titre : "QUITTANCE DE PAIEMENT - COMPLETION DE RELIQUAT"
   - ✅ Section "Note" avec "⚠️ PAIEMENT DE RELIQUAT / COMPLETION"
   - ✅ "Ce paiement constitue la complétion finale du reliquat pour [mois]"
   - ✅ Date du paiement initial affichée
   - ✅ "Paiement n°3 sur 3 pour ce mois"
   - ✅ "✓ RELIQUAT ENTIÈREMENT SOLDÉ" en vert

## 🔄 Flux de Travail

### Processus de Paiement Partiel avec Reliquat

```
1. PAIEMENT PARTIEL INITIAL (60 000 / 100 000)
   ↓
   Génération quittance → "QUITTANCE DE PAIEMENT PARTIEL"
   ↓
   
2. COMPLÉTION PARTIELLE (+ 20 000 → 80 000 / 100 000)
   ↓
   Génération quittance → "QUITTANCE DE PAIEMENT - RELIQUAT PARTIEL"
   • Détection automatique : paiement n°2 pour ce mois
   • Affichage : "Reste à payer : 20 000 F CFA"
   ↓
   
3. COMPLÉTION FINALE (+ 20 000 → 100 000 / 100 000)
   ↓
   Génération quittance → "QUITTANCE DE PAIEMENT - COMPLETION DE RELIQUAT"
   • Détection automatique : paiement n°3 pour ce mois
   • Affichage : "✓ RELIQUAT ENTIÈREMENT SOLDÉ"
   • Mise à jour automatique : tous les paiements marqués comme complétés
```

## 🎨 Présentation Visuelle des Quittances

### Paiement Partiel Initial
```
┌────────────────────────────────────────────┐
│  QUITTANCE DE PAIEMENT PARTIEL             │
├────────────────────────────────────────────┤
│  Montant payé: 60 000 F CFA               │
│                                            │
│  Note:                                     │
│  ⚠️ PAIEMENT PARTIEL                       │
│  • Montant payé : 60 000 sur 100 000      │
│  • Reste à payer : 40 000 F CFA           │
└────────────────────────────────────────────┘
```

### Reliquat Partiel
```
┌────────────────────────────────────────────┐
│  QUITTANCE DE PAIEMENT - RELIQUAT PARTIEL  │
├────────────────────────────────────────────┤
│  Montant payé: 20 000 F CFA               │
│                                            │
│  Note:                                     │
│  ⚠️ PAIEMENT DE RELIQUAT / COMPLETION      │
│  • Complétion partielle pour janvier 2026 │
│  • Paiement initial du : 15/01/2026       │
│  • Paiement n°2 sur 2                     │
│  • Reste à payer : 20 000 F CFA           │
└────────────────────────────────────────────┘
```

### Complétion Finale
```
┌────────────────────────────────────────────┐
│  QUITTANCE - COMPLETION DE RELIQUAT        │
├────────────────────────────────────────────┤
│  Montant payé: 20 000 F CFA               │
│                                            │
│  Note:                                     │
│  ⚠️ PAIEMENT DE RELIQUAT / COMPLETION      │
│  • Complétion finale pour janvier 2026    │
│  • Paiement initial du : 15/01/2026       │
│  • Paiement n°3 sur 3                     │
│  • ✓ RELIQUAT ENTIÈREMENT SOLDÉ           │
└────────────────────────────────────────────┘
```

## 📊 Points Techniques

### Détection Automatique des Reliquats

La détection se fait par **deux méthodes complémentaires** :

1. **Analyse des notes** : Si les notes contiennent "complétion" ou "reliquat"
2. **Position dans la séquence** : Si le paiement n'est pas le premier pour ce mois

### Calculs Dynamiques

Le système recalcule automatiquement :
- Total payé pour le mois
- Montant restant dû
- Pourcentage de progression
- Nombre de paiements dans la séquence
- Statut de complétion du reliquat

### Synchronisation Automatique

Lors de chaque génération de quittance :
1. Synchronisation du paiement partiel (`synchroniser_paiement_partiel`)
2. Recalcul des montants restants (`calculer_montant_restant`)
3. Vérification de la complétion (`verifier_et_completer_reliquat`)
4. Rafraîchissement des données depuis la base (`refresh_from_db`)

## ✅ Avantages de la Solution

1. **Détection Automatique** : Pas besoin de marquage manuel
2. **Titres Explicites** : Identification immédiate du type de paiement
3. **Informations Complètes** : Historique et statut du reliquat
4. **Format Professionnel** : Quittance conforme aux standards KBIS
5. **Mise à jour Dynamique** : Calculs automatiques et précis
6. **Traçabilité** : Date du paiement initial et numéro de séquence

## 🔧 Maintenance Future

### Ajout de Nouvelles Fonctionnalités

Pour ajouter de nouvelles informations sur les quittances de reliquat :

1. **Modifier le contexte** dans `services_document_unifie_complet.py`
2. **Mettre à jour les templates** HTML
3. **Tester** avec les 3 scénarios de base

### Personnalisation des Titres

Les titres peuvent être facilement modifiés dans :
```python
# paiements/services_document_unifie_complet.py - ligne ~66
if info_partiel.get('est_reliquat'):
    if info_partiel.get('est_complet'):
        document_title = 'VOTRE_TITRE_PERSONNALISÉ'
    else:
        document_title = 'VOTRE_AUTRE_TITRE'
```

## 📞 Support

En cas de problème :
1. Vérifier les logs dans la console
2. Vérifier que `est_paiement_partiel = True` sur le paiement
3. Vérifier que `mois_paye` est correctement défini
4. Vérifier que plusieurs paiements existent pour le même mois

---

**Date de correction :** 19 janvier 2026
**Version :** 2.0
**Statut :** ✅ Opérationnel
