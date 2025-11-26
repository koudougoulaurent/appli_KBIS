# Migration des Contrats de Gestion

## Description

Cette commande de management Django permet de migrer tous les bailleurs existants vers le système de contrat de gestion unique.

**Règle importante :** Un bailleur ne peut avoir qu'UN SEUL contrat de gestion qui inclut TOUTES ses propriétés.

## Utilisation

### En local (développement)

```bash
# Mode test (affiche ce qui sera fait sans modifier)
python manage.py migrer_contrats_gestion --dry-run

# Exécution réelle
python manage.py migrer_contrats_gestion
```

### En production (Render)

1. **Via le terminal Render** :
   ```bash
   python manage.py migrer_contrats_gestion
   ```

2. **Via SSH** :
   ```bash
   # Se connecter au service Render
   render ssh <service-name>
   
   # Exécuter la commande
   python manage.py migrer_contrats_gestion
   ```

3. **Via le shell Django** :
   ```bash
   python manage.py shell
   # Puis exécuter le code de migration manuellement
   ```

## Options

- `--dry-run` : Mode test, affiche ce qui sera fait sans effectuer les modifications
- `--force` : Force la mise à jour même si des contrats existent déjà

## Ce que fait la commande

1. **Pour chaque bailleur avec propriétés** :
   - Si aucun contrat n'existe → Crée un nouveau contrat de gestion
   - Si un contrat existe → Vérifie qu'il inclut toutes les propriétés
   - Si plusieurs contrats existent → Fusionne en un seul contrat unique

2. **Garantit** :
   - Un bailleur = Un seul contrat de gestion
   - Toutes les propriétés du bailleur sont incluses dans le contrat
   - Les contrats en double sont supprimés logiquement

## Résultat attendu

Après exécution, tous les bailleurs avec propriétés auront :
- ✅ Un seul contrat de gestion
- ✅ Toutes leurs propriétés incluses dans le contrat
- ✅ Le contrat visible dans la page de détail du bailleur
- ✅ Le bouton "Contrat de Gestion PDF" disponible

## Notes importantes

- La commande est **idempotente** : peut être exécutée plusieurs fois sans problème
- Les modifications sont effectuées dans une **transaction atomique**
- Les erreurs sont loggées mais n'arrêtent pas le processus
- La commande fonctionne avec SQLite (local) et PostgreSQL (production)

