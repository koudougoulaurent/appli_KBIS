# 🚨 CORRECTION MANUELLE URGENTE

## Problème
L'erreur `value too long for type character varying(20)` persiste car le champ `numero_locataire` est encore VARCHAR(20).

## Solution Manuelle

### 1. Connectez-vous au Shell Render
- Allez sur https://dashboard.render.com
- Sélectionnez votre service `appli-kbis-postgresql`
- Cliquez sur "Shell"

### 2. Exécutez cette commande SQL directement :

```sql
ALTER TABLE proprietes_locataire ALTER COLUMN numero_locataire TYPE VARCHAR(50);
```

### 3. Vérifiez la correction :

```sql
SELECT column_name, data_type, character_maximum_length 
FROM information_schema.columns 
WHERE table_name = 'proprietes_locataire' 
AND column_name = 'numero_locataire';
```

### 4. Résultat attendu :
```
column_name     | data_type        | character_maximum_length
numero_locataire| character varying| 50
```

## Alternative : Script Python

Si vous préférez, exécutez ce script Python dans le Shell :

```python
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'gestion_immobiliere.settings_postgresql'
import django
django.setup()
from django.db import connection

with connection.cursor() as cursor:
    cursor.execute("ALTER TABLE proprietes_locataire ALTER COLUMN numero_locataire TYPE VARCHAR(50);")
    print("✅ numero_locataire corrigé: VARCHAR(20) -> VARCHAR(50)")
```

## Test Final
Après la correction, testez l'ajout d'un locataire sur :
https://appli-kbis-3.onrender.com/proprietes/locataires/ajouter/

L'erreur 500 devrait disparaître !