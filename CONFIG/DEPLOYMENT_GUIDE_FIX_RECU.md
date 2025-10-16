# 🚀 Guide de Déploiement - Correction Génération Récépissés

## 📋 Résumé de la correction
- **Problème** : Erreur "Erreur lors de la génération du récépissé"
- **Cause** : Import incorrect du module `DocumentKBISUnifie`
- **Solution** : Correction du chemin d'import vers le répertoire `SCRIPTS`

## 🔧 Modifications apportées
- **Fichier modifié** : `paiements/models.py`
- **Méthodes corrigées** :
  - `_generer_recu_kbis_dynamique()`
  - `_generer_quittance_kbis_dynamique()`
  - `_generer_recu_retrait_kbis()`

## 📦 Déploiement sur Render

### Option 1 : Déploiement automatique (Recommandé)
Le commit a été poussé sur la branche `master`. Render devrait automatiquement :
1. Détecter le nouveau commit
2. Redémarrer l'application
3. Appliquer les modifications

### Option 2 : Déploiement manuel via Shell Render
Si le déploiement automatique ne fonctionne pas, exécutez ces commandes dans le Shell Render :

```bash
# 1. Aller dans le répertoire du projet
cd /opt/render/project/src

# 2. Activer l'environnement virtuel
source .venv/bin/activate

# 3. Récupérer les dernières modifications
git pull origin master

# 4. Redémarrer l'application
sudo systemctl restart kbis-immobilier

# 5. Vérifier le statut
sudo systemctl status kbis-immobilier
```

### Option 3 : Test de la correction
Pour vérifier que la correction fonctionne, exécutez ce test dans le Shell Render :

```bash
cd /opt/render/project/src
source .venv/bin/activate

python manage.py shell -c "
import sys
import os
from paiements.models import Paiement

# Test de l'import
try:
    project_root = os.path.dirname(os.path.dirname(os.path.abspath('paiements/models.py')))
    scripts_path = os.path.join(project_root, 'SCRIPTS')
    if scripts_path not in sys.path:
        sys.path.append(scripts_path)
    from document_kbis_unifie import DocumentKBISUnifie
    print('✅ Import DocumentKBISUnifie: SUCCÈS')
except Exception as e:
    print(f'❌ Import DocumentKBISUnifie: ÉCHEC - {e}')

# Test de génération
try:
    paiement = Paiement.objects.first()
    if paiement:
        html_recu = paiement._generer_recu_kbis_dynamique()
        if html_recu:
            print('✅ Génération récépissé: SUCCÈS')
            print(f'📄 Taille HTML: {len(html_recu)} caractères')
        else:
            print('❌ Génération récépissé: ÉCHEC')
    else:
        print('⚠️ Aucun paiement trouvé pour le test')
except Exception as e:
    print(f'❌ Test génération: ÉCHEC - {e}')
"
```

## ✅ Vérification post-déploiement

1. **Accéder à l'application** : https://votre-app.onrender.com
2. **Se connecter** avec vos identifiants
3. **Aller dans la section Paiements**
4. **Essayer de générer un récépissé** pour un paiement existant
5. **Vérifier** que le récépissé s'affiche correctement

## 🔍 Dépannage

Si le problème persiste :

1. **Vérifier les logs** :
   ```bash
   sudo journalctl -u kbis-immobilier -f
   ```

2. **Vérifier le statut de l'application** :
   ```bash
   sudo systemctl status kbis-immobilier
   ```

3. **Redémarrer manuellement** :
   ```bash
   sudo systemctl restart kbis-immobilier
   ```

## 📞 Support

Si vous rencontrez des problèmes :
1. Vérifiez les logs d'erreur
2. Testez la génération via le shell
3. Contactez le support technique si nécessaire

---
**Date de déploiement** : $(date)
**Version** : Fix génération récépissés v1.0
**Statut** : ✅ Prêt pour la production
