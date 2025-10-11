# Guide de Nettoyage VPS - Application KBIS Immobilier

## 🧹 Objectif
Nettoyer complètement le VPS de l'ancienne installation problématique pour repartir sur une base propre.

## ⚠️ Attention
Ce script va supprimer **TOUTES** les données de l'ancienne installation. Assurez-vous d'avoir sauvegardé vos données importantes avant de continuer.

## 🚀 Nettoyage Automatique (Recommandé)

### 1. Connexion au VPS
```bash
ssh root@votre-ip-vps
```

### 2. Téléchargement et exécution du script de nettoyage
```bash
# Télécharger le script de nettoyage
wget https://raw.githubusercontent.com/koudougoulaurent/appli_KBIS/modifications-octobre-2025/clean_vps_complete.sh

# Rendre le script exécutable
chmod +x clean_vps_complete.sh

# Exécuter le nettoyage
./clean_vps_complete.sh
```

## 🔧 Nettoyage Manuel (Si nécessaire)

### 1. Arrêter tous les services
```bash
# Arrêter les services
systemctl stop kbis-immobilier
systemctl stop nginx
systemctl stop mysql

# Vérifier qu'ils sont arrêtés
systemctl status kbis-immobilier
systemctl status nginx
systemctl status mysql
```

### 2. Supprimer les services systemd
```bash
# Supprimer les services
rm -f /etc/systemd/system/kbis-immobilier.service
rm -f /etc/systemd/system/kbis-*.service
systemctl daemon-reload
```

### 3. Supprimer les configurations Nginx
```bash
# Supprimer les configurations
rm -f /etc/nginx/sites-available/kbis-immobilier
rm -f /etc/nginx/sites-enabled/kbis-immobilier
rm -f /etc/nginx/sites-available/kbis-*
rm -f /etc/nginx/sites-enabled/kbis-*

# Restaurer la configuration par défaut
cat > /etc/nginx/sites-available/default <<EOF
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    
    root /var/www/html;
    index index.html index.htm index.nginx-debian.html;
    
    server_name _;
    
    location / {
        try_files \$uri \$uri/ =404;
    }
}
EOF

ln -sf /etc/nginx/sites-available/default /etc/nginx/sites-enabled/
```

### 4. Supprimer l'application
```bash
# Supprimer les répertoires de l'application
rm -rf /var/www/kbis-immobilier
rm -rf /var/www/appli_KBIS
rm -rf /home/*/appli_KBIS
rm -rf /root/appli_KBIS
```

### 5. Nettoyer la base de données
```bash
# Démarrer MySQL
systemctl start mysql

# Supprimer la base de données
mysql -u root -p
```

```sql
DROP DATABASE IF EXISTS kbis_immobilier;
DROP USER IF EXISTS 'kbis_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### 6. Tuer les processus
```bash
# Tuer tous les processus liés à l'application
pkill -f "gunicorn.*kbis"
pkill -f "python.*manage.py"
pkill -f "appli_KBIS"
```

### 7. Nettoyer les logs et caches
```bash
# Supprimer les logs
rm -rf /var/log/kbis-*
rm -rf /var/log/appli_KBIS*
rm -rf /var/www/*/logs

# Vider les logs systemd
journalctl --vacuum-time=1d

# Nettoyer les caches
rm -rf /var/cache/nginx/*
rm -rf /tmp/kbis-*
rm -rf /tmp/appli_KBIS*
```

### 8. Supprimer les packages Python
```bash
# Supprimer les packages Python inutiles
pip3 uninstall -y django gunicorn whitenoise mysqlclient
```

### 9. Nettoyage final
```bash
# Nettoyage du système
apt autoremove -y
apt autoclean
updatedb
```

## 🔍 Vérification du Nettoyage

### 1. Vérifier que les services sont arrêtés
```bash
systemctl status kbis-immobilier
systemctl status nginx
systemctl status mysql
```

### 2. Vérifier que les répertoires sont supprimés
```bash
ls -la /var/www/
ls -la /etc/nginx/sites-enabled/
ls -la /etc/systemd/system/ | grep kbis
```

### 3. Vérifier qu'aucun processus n'est actif
```bash
ps aux | grep gunicorn
ps aux | grep python
ps aux | grep kbis
```

### 4. Vérifier la base de données
```bash
mysql -u root -p -e "SHOW DATABASES;"
```

## ✅ Checklist de Nettoyage

- [ ] Services arrêtés
- [ ] Services systemd supprimés
- [ ] Configuration Nginx nettoyée
- [ ] Application supprimée
- [ ] Base de données nettoyée
- [ ] Processus terminés
- [ ] Logs vidés
- [ ] Caches nettoyés
- [ ] Packages Python supprimés
- [ ] Système nettoyé

## 🚀 Après le Nettoyage

Une fois le nettoyage terminé, vous pouvez :

1. **Déployer la nouvelle version propre** :
   ```bash
   wget https://raw.githubusercontent.com/koudougoulaurent/appli_KBIS/modifications-octobre-2025/deploy_vps_clean.sh
   chmod +x deploy_vps_clean.sh
   ./deploy_vps_clean.sh
   ```

2. **Vérifier que tout fonctionne** :
   - Accéder à l'application via HTTP
   - Tester la connexion à la base de données
   - Vérifier les logs

## 🚨 Dépannage

### Si des services ne s'arrêtent pas
```bash
# Forcer l'arrêt
systemctl kill kbis-immobilier
pkill -9 -f "gunicorn.*kbis"
```

### Si des fichiers ne se suppriment pas
```bash
# Vérifier les permissions
ls -la /var/www/
chown -R root:root /var/www/kbis-immobilier
rm -rf /var/www/kbis-immobilier
```

### Si la base de données ne se supprime pas
```bash
# Se connecter en tant que root
mysql -u root -p
# Puis exécuter les commandes SQL manuellement
```

## 📞 Support

En cas de problème lors du nettoyage :
1. Vérifiez les logs : `journalctl -f`
2. Vérifiez les processus : `ps aux | grep kbis`
3. Vérifiez les services : `systemctl list-units | grep kbis`
4. Consultez ce guide ou contactez le support

---

**🧹 Le VPS sera complètement nettoyé et prêt pour un nouveau déploiement propre !**