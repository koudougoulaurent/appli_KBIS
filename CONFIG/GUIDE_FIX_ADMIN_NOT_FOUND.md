# 🔧 Guide de Résolution - Admin Django "Not Found"

## 🚨 Problème
Après chaque redéploiement sur Render, l'admin Django retourne une erreur "Not Found" :
- URL : `https://appli-kbis-3.onrender.com/admin/`
- Erreur : "The requested resource was not found on this server"

## 🔍 Causes identifiées

### 1. **ALLOWED_HOSTS manquant**
- L'URL `appli-kbis-3.onrender.com` n'était pas dans `ALLOWED_HOSTS`
- Django rejette les requêtes pour les domaines non autorisés

### 2. **Configuration de production**
- Conflits entre les différents environnements
- Settings de production pas correctement appliqués

### 3. **Fichiers statiques**
- `collectstatic` pas exécuté après redéploiement
- CSS/JS de l'admin non disponibles

### 4. **Migrations**
- Migrations pas appliquées après redéploiement
- Tables de l'admin manquantes

## ✅ Solutions appliquées

### 1. **Correction ALLOWED_HOSTS**
```python
# Dans settings.py
ALLOWED_HOSTS = [
    'localhost', '127.0.0.1', 
    'appli-kbis.onrender.com', 
    'appli-kbis-3.onrender.com',  # ← Ajouté
    '.onrender.com', '*', '0.0.0.0'
]
```

### 2. **Script de correction automatique**
- `CONFIG/fix_admin_not_found.sh` - Script complet de correction
- `CONFIG/check_admin_status.py` - Script de diagnostic

## 🚀 Déploiement de la correction

### Option 1 : Déploiement automatique
Le commit a été poussé. Render devrait automatiquement :
1. Détecter le nouveau commit
2. Redémarrer l'application
3. Appliquer la correction

### Option 2 : Correction manuelle via Shell Render
```bash
cd /opt/render/project/src
source .venv/bin/activate
git pull origin master
python manage.py migrate --noinput
python manage.py collectstatic --noinput
sudo systemctl restart kbis-immobilier
```

### Option 3 : Script de correction automatique
```bash
cd /opt/render/project/src
chmod +x CONFIG/fix_admin_not_found.sh
./CONFIG/fix_admin_not_found.sh
```

## 🧪 Vérification

### Test rapide :
```bash
python CONFIG/check_admin_status.py
```

### Test via navigateur :
1. Aller sur `https://appli-kbis-3.onrender.com/admin/`
2. Vérifier que la page de connexion admin s'affiche
3. Se connecter avec les identifiants admin

## 🔄 Prévention future

### 1. **Script de post-déploiement**
Ajouter dans la configuration Render :
```bash
python manage.py migrate --noinput
python manage.py collectstatic --noinput
```

### 2. **Monitoring**
Utiliser le script `check_admin_status.py` régulièrement

### 3. **Configuration robuste**
- Toujours inclure `.onrender.com` dans ALLOWED_HOSTS
- Utiliser des variables d'environnement pour les domaines

## 📋 Checklist de résolution

- [ ] ✅ ALLOWED_HOSTS mis à jour
- [ ] ✅ Migrations appliquées
- [ ] ✅ Fichiers statiques collectés
- [ ] ✅ Application redémarrée
- [ ] ✅ Admin accessible via navigateur
- [ ] ✅ Superutilisateur créé si nécessaire

## 🆘 Dépannage avancé

### Si le problème persiste :

1. **Vérifier les logs** :
   ```bash
   sudo journalctl -u kbis-immobilier -f
   ```

2. **Vérifier la configuration** :
   ```bash
   python manage.py shell -c "from django.conf import settings; print(settings.ALLOWED_HOSTS)"
   ```

3. **Tester l'URL directement** :
   ```bash
   curl -I https://appli-kbis-3.onrender.com/admin/
   ```

4. **Recréer le superutilisateur** :
   ```bash
   python manage.py createsuperuser
   ```

---
**Statut** : ✅ Correction appliquée
**Prochaine étape** : Tester l'accès admin
**Prévention** : Scripts de post-déploiement en place
