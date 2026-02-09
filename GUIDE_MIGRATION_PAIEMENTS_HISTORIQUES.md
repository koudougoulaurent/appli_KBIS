# 📦 GUIDE DE MIGRATION DES PAIEMENTS HISTORIQUES

## 🎯 Objectif

Ce guide explique comment importer les paiements de l'ancienne plateforme vers la nouvelle, en prenant en compte les retards de paiement existants.

## 🔧 Fonctionnalités Ajoutées

### 1. **Champ "Saisie Manuelle Historique"**
- Nouveau champ booléen dans le modèle `Paiement`
- Permet d'identifier les paiements importés de l'ancienne plateforme
- Badge orange "📦 HISTORIQUE" visible dans l'admin

### 2. **Synchronisation Automatique**
- Signal Django qui se déclenche après chaque sauvegarde de paiement
- Recalcule automatiquement le prochain paiement dû pour le contrat
- Fonctionne pour tous les types de paiements : loyer, avance, etc.

### 3. **Action Admin de Synchronisation Batch**
- Action "🔄 Synchroniser les contrats après import historique"
- Permet de recalculer tous les contrats sélectionnés en une seule fois
- Utile après un import massif de paiements

---

## 📝 Procédure d'Import

### Étape 1 : Préparation de la Migration

Avant de commencer, assurez-vous d'avoir :
- ✅ La liste complète des contrats à migrer
- ✅ L'historique des paiements pour chaque contrat
- ✅ Les dates et montants exacts de chaque paiement
- ✅ Les informations sur les retards éventuels

### Étape 2 : Appliquer la Migration

```bash
# Appliquer la migration pour ajouter le nouveau champ
python manage.py migrate paiements
```

### Étape 3 : Import Manuel via l'Admin Django

#### Option A : Saisie Individuelle

1. **Accédez à l'admin Django**
   - URL : `http://127.0.0.1:8000/admin/paiements/paiement/add/`

2. **Cochez la case "Saisie manuelle historique"**
   - 🔴 **IMPORTANT** : Cocher cette case en premier
   - Cela désactive toutes les validations automatiques
   - Permet la saisie libre du mois payé

3. **Remplissez les champs**
   ```
   Contrat : [Sélectionner le contrat concerné]
   Montant : [Montant exact du paiement]
   Type de paiement : [Loyer / Avance / Caution / etc.]
   Mois payé : [Format libre, ex: "Janvier 2024" ou "01/2024"]
   Mode de paiement : [Virement / Chèque / Espèces / Mobile Money]
   Date de paiement : [Date réelle du paiement]
   Statut : Validé
   ```

4. **Sauvegardez**
   - Le signal se déclenche automatiquement
   - Le prochain paiement est recalculé immédiatement
   - Un message apparaît dans la console : 
     ```
     📦 HISTORIQUE Contrat CT-2024-001 synchronisé - Prochain paiement: MARS 2026
     ```

#### Option B : Import Massif via Script Python

Créez un script `import_paiements_historiques.py` :

```python
import os
import django
from datetime import datetime

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings')
django.setup()

from paiements.models import Paiement
from contrats.models import Contrat

# Données d'exemple à adapter selon votre format
paiements_ancienne_plateforme = [
    {
        'numero_contrat': 'CT-2024-001',
        'montant': 250000,
        'type_paiement': 'loyer',
        'mois_paye': 'Janvier 2024',
        'date_paiement': '2024-01-15',
        'mode_paiement': 'virement',
        'notes': 'Import depuis ancienne plateforme'
    },
    {
        'numero_contrat': 'CT-2024-001',
        'montant': 250000,
        'type_paiement': 'loyer',
        'mois_paye': 'Février 2024',
        'date_paiement': '2024-02-20',
        'mode_paiement': 'virement',
        'notes': 'Import depuis ancienne plateforme'
    },
    # ... autres paiements
]

# Import des paiements
for data in paiements_ancienne_plateforme:
    try:
        # Récupérer le contrat
        contrat = Contrat.objects.get(numero_contrat=data['numero_contrat'])
        
        # Créer le paiement historique
        paiement = Paiement.objects.create(
            contrat=contrat,
            montant=data['montant'],
            type_paiement=data['type_paiement'],
            mois_paye=data['mois_paye'],
            date_paiement=datetime.strptime(data['date_paiement'], '%Y-%m-%d').date(),
            mode_paiement=data['mode_paiement'],
            statut='valide',
            notes=data.get('notes', ''),
            est_saisie_manuelle_historique=True,  # IMPORTANT
            montant_net_paye=data['montant']
        )
        
        print(f"✅ Paiement importé : {contrat.numero_contrat} - {data['mois_paye']}")
        
    except Exception as e:
        print(f"❌ Erreur pour {data.get('numero_contrat')}: {str(e)}")

print("\n🎉 Import terminé !")
```

**Exécution du script :**
```bash
python import_paiements_historiques.py
```

### Étape 4 : Vérification et Synchronisation

1. **Vérifiez l'import dans l'admin**
   - Allez dans `/admin/paiements/paiement/`
   - Filtrez par "Saisie manuelle historique = Oui"
   - Vérifiez que tous les paiements ont le badge "📦 HISTORIQUE"

2. **Synchronisez les contrats (si nécessaire)**
   - Sélectionnez tous les paiements importés
   - Dans "Actions", choisissez "🔄 Synchroniser les contrats après import historique"
   - Cliquez sur "Exécuter"
   - Un message de confirmation apparaît : "✅ X contrat(s) synchronisé(s)"

3. **Testez le calcul du prochain paiement**
   - Allez dans la vue de détail d'un contrat
   - Cliquez sur "📅 Ajouter un paiement"
   - Le système doit suggérer le bon mois suivant (tenant compte de l'historique)

---

## 🔍 Cas d'Usage Concrets

### Cas 1 : Contrat avec Retard

**Situation :**
- Contrat démarré en janvier 2024
- Loyer mensuel : 250,000 FCFA
- Paiements effectués : janvier, février, avril (mars manquant = RETARD)

**Import :**
```python
# Paiement Janvier 2024
Paiement.objects.create(
    contrat=contrat,
    montant=250000,
    type_paiement='loyer',
    mois_paye='Janvier 2024',
    date_paiement=datetime(2024, 1, 15),
    statut='valide',
    est_saisie_manuelle_historique=True
)

# Paiement Février 2024
Paiement.objects.create(
    contrat=contrat,
    montant=250000,
    type_paiement='loyer',
    mois_paye='Février 2024',
    date_paiement=datetime(2024, 2, 20),
    statut='valide',
    est_saisie_manuelle_historique=True
)

# Paiement Avril 2024 (Mars manquant)
Paiement.objects.create(
    contrat=contrat,
    montant=250000,
    type_paiement='loyer',
    mois_paye='Avril 2024',
    date_paiement=datetime(2024, 4, 10),
    statut='valide',
    est_saisie_manuelle_historique=True
)

# Le système calculera automatiquement :
# - Prochain paiement dû : MARS 2024 (le retard)
# - Puis MAI 2024 après paiement de mars
```

### Cas 2 : Contrat avec Avance

**Situation :**
- Contrat démarré en février 2026
- Avance de 3 mois versée (février, mars, avril couverts)
- Loyer de mai déjà payé

**Import :**
```python
# Avance (février-avril 2026)
Paiement.objects.create(
    contrat=contrat,
    montant=750000,  # 3 mois
    type_paiement='avance_loyer',
    mois_paye='Février-Avril 2026',
    date_paiement=datetime(2026, 2, 9),
    statut='valide',
    est_saisie_manuelle_historique=True
)

# Loyer Mai 2026
Paiement.objects.create(
    contrat=contrat,
    montant=250000,
    type_paiement='loyer',
    mois_paye='Mai 2026',
    date_paiement=datetime(2026, 5, 5),
    statut='valide',
    est_saisie_manuelle_historique=True
)

# Le système calculera :
# - Prochain paiement : JUIN 2026
```

---

## ⚙️ Paramètres Techniques

### Champs du Modèle Paiement

| Champ | Type | Obligatoire | Description |
|-------|------|-------------|-------------|
| `contrat` | ForeignKey | ✅ Oui | Lien vers le contrat concerné |
| `montant` | Decimal | ✅ Oui | Montant du paiement |
| `type_paiement` | CharField | ✅ Oui | Type : loyer, avance, caution, etc. |
| `mois_paye` | CharField | ⚠️ Recommandé | Format libre (ex: "Janvier 2024") |
| `date_paiement` | DateField | ✅ Oui | Date réelle du paiement |
| `mode_paiement` | CharField | ✅ Oui | virement, cheque, especes, mobile_money |
| `statut` | CharField | ✅ Oui | en_attente, valide, refuse, annule |
| `est_saisie_manuelle_historique` | Boolean | ✅ **OUI** | **Toujours cocher à True** |

### Signal de Synchronisation

**Fichier :** `paiements/signals_paiement_historique.py`

**Conditions de déclenchement :**
- ✅ Paiement non supprimé (`is_deleted=False`)
- ✅ Paiement validé (`statut='valide'`)
- ✅ Type de paiement concerné (`loyer`, `avance`, `avance_loyer`)

**Comportement :**
- Recalcule automatiquement le prochain paiement via `ServiceGestionAvance`
- Affiche un log dans la console avec le préfixe "📦 HISTORIQUE"
- Ne bloque jamais la sauvegarde (gestion d'erreur silencieuse)

---

## 🐛 Dépannage

### Problème : Le signal ne se déclenche pas

**Solution :**
```bash
# Vérifiez que le signal est chargé
python manage.py shell
>>> from paiements import signals_paiement_historique
>>> print("Signal chargé !")
```

### Problème : Le prochain paiement n'est pas correct

**Solution :**
1. Vérifiez que tous les paiements historiques sont marqués `est_saisie_manuelle_historique=True`
2. Utilisez l'action admin "🔄 Synchroniser les contrats"
3. Si le problème persiste, recalculez manuellement :
   ```python
   from paiements.services_avance import ServiceGestionAvance
   from contrats.models import Contrat
   
   contrat = Contrat.objects.get(numero_contrat='CT-2024-001')
   prochain = ServiceGestionAvance.calculer_prochain_mois_paiement(contrat)
   print(f"Prochain paiement : {prochain.strftime('%B %Y')}")
   ```

### Problème : Erreur lors de l'import massif

**Solution :**
- Vérifiez que le contrat existe (`Contrat.objects.get(numero_contrat=...)`)
- Vérifiez le format de la date (YYYY-MM-DD)
- Vérifiez que le montant est un nombre valide
- Activez le mode debug pour voir les erreurs détaillées

---

## 📊 Logs et Monitoring

### Messages dans la Console

**Succès :**
```
📦 HISTORIQUE Contrat CT-2024-001 synchronisé - Prochain paiement: MARS 2026
```

**Paiement normal (non historique) :**
```
🔄 Contrat CT-2024-002 synchronisé - Prochain paiement: AVRIL 2026
```

**Erreur :**
```
⚠️ Erreur lors de la synchronisation du contrat CT-2024-003: [message d'erreur]
```

### Filtres Admin

Dans l'admin Django (`/admin/paiements/paiement/`), utilisez :
- **Filtre "Saisie manuelle historique"** : Affiche uniquement les paiements importés
- **Badge "📦 HISTORIQUE"** : Visible dans la colonne "Type"
- **Recherche par "mois_paye"** : Trouvez rapidement un paiement par mois

---

## ✅ Checklist de Migration

- [ ] Migration appliquée (`python manage.py migrate paiements`)
- [ ] Signal chargé (vérifier dans apps.py)
- [ ] Paiements historiques importés
- [ ] Case "Saisie manuelle historique" cochée pour tous les imports
- [ ] Statut "Validé" pour tous les paiements historiques
- [ ] Synchronisation effectuée (action admin ou automatique)
- [ ] Tests sur quelques contrats pour vérifier le calcul
- [ ] Documentation des retards existants
- [ ] Backup de la base de données avant import massif

---

## 🎓 Bonnes Pratiques

1. **Toujours cocher "Saisie manuelle historique"** pour les imports
2. **Importer les paiements dans l'ordre chronologique** (du plus ancien au plus récent)
3. **Valider les paiements immédiatement** (`statut='valide'`)
4. **Renseigner le champ "mois_paye"** pour faciliter les recherches
5. **Ajouter une note** pour tracer l'origine du paiement
6. **Faire un backup** avant l'import massif
7. **Tester sur quelques contrats** avant l'import complet
8. **Synchroniser après import** si nécessaire

---

## 📞 Support

En cas de problème, vérifiez :
1. Les logs de la console Django
2. Les messages d'erreur dans l'admin
3. La base de données (table `paiements_paiement`)
4. Le fichier `signals_paiement_historique.py`

**Fichiers modifiés :**
- `paiements/models.py` (ajout du champ)
- `paiements/admin.py` (interface admin)
- `paiements/signals_paiement_historique.py` (signal de synchronisation)
- `paiements/apps.py` (activation du signal)
- `paiements/migrations/0099_paiement_est_saisie_manuelle_historique.py` (migration)

---

🎉 **Bonne migration !**
