# 🖥️ Guide Déploiement VPS LWS

## 🎯 **OUI ! Votre application peut être hébergée sur un VPS LWS**

LWS propose **2 options** pour votre application Django :

### 1️⃣ **Hébergement Partagé cPanel** (Recommandé pour débuter)
- **Prix** : 3-5€/mois
- **Facilité** : Très simple, gestion automatique
- **Contrôle** : Limité
- **Idéal pour** : Débuter, petits projets

### 2️⃣ **VPS (Serveur Virtuel Privé)** (Recommandé pour production)
- **Prix** : 15-50€/mois selon la configuration
- **Facilité** : Plus complexe, contrôle total
- **Contrôle** : Complet (root access)
- **Idéal pour** : Production, applications complexes

---

## 🚀 **VPS LWS - Avantages pour votre application**

### ✅ **Pourquoi choisir un VPS ?**
- **Performance** : Ressources dédiées
- **Contrôle total** : Configuration personnalisée
- **Sécurité** : Isolation complète
- **Évolutivité** : Facilement extensible
- **Base de données** : MySQL/PostgreSQL dédiés
- **SSL** : Certificats personnalisés
- **Domaine** : Nombre illimité de domaines

### 💰 **Prix VPS LWS**
- **VPS Starter** : ~15€/mois (1 vCPU, 1GB RAM)
- **VPS Standard** : ~25€/mois (2 vCPU, 2GB RAM)
- **VPS Pro** : ~40€/mois (4 vCPU, 4GB RAM)

---

## 🛠️ **Configuration VPS pour Django**

### **Système d'exploitation recommandé**
- **Ubuntu 22.04 LTS** (gratuit, stable)
- **CentOS 8** (gratuit, entreprise)
- **Debian 11** (gratuit, léger)

### **Stack technique recommandé**
- **Web Server** : Nginx + Gunicorn
- **Base de données** : PostgreSQL ou MySQL
- **Cache** : Redis (optionnel)
- **SSL** : Let's Encrypt (gratuit)

---

## 📋 **Étapes de déploiement VPS**

### **Phase 1 : Configuration du serveur**
1. **Commander le VPS** sur LWS
2. **Accéder au serveur** via SSH
3. **Mettre à jour le système**
4. **Installer Python 3.9+**
5. **Installer PostgreSQL/MySQL**
6. **Installer Nginx**

### **Phase 2 : Déploiement de l'application**
1. **Cloner votre code** depuis Git
2. **Installer les dépendances**
3. **Configurer la base de données**
4. **Configurer Nginx + Gunicorn**
5. **Configurer SSL**
6. **Tester l'application**

---

## 🔧 **Scripts de déploiement VPS**

### **Script de configuration serveur**
```bash
#!/bin/bash
# configure_vps.sh

# Mise à jour du système
sudo apt update && sudo apt upgrade -y

# Installation des dépendances
sudo apt install -y python3 python3-pip python3-venv postgresql postgresql-contrib nginx git

# Installation de Node.js (pour les assets)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Configuration de PostgreSQL
sudo -u postgres createuser --interactive
sudo -u postgres createdb gestimmob_db

# Installation de Gunicorn
pip3 install gunicorn

echo "✅ Serveur configuré !"
```

### **Script de déploiement application**
```bash
#!/bin/bash
# deploy_vps.sh

# Cloner le code
git clone https://github.com/koudougoulaurent/appli_KBIS.git
cd appli_KBIS

# Créer l'environnement virtuel
python3 -m venv venv
source venv/bin/activate

# Installer les dépendances
pip install -r requirements_production.txt

# Configuration de la base de données
python manage.py makemigrations
python manage.py migrate

# Collecte des fichiers statiques
python manage.py collectstatic --noinput

# Création du superutilisateur
python manage.py createsuperuser

# Configuration de Gunicorn
echo "[Unit]
Description=Gunicorn instance to serve gestimmob
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/home/ubuntu/appli_KBIS
Environment="PATH=/home/ubuntu/appli_KBIS/venv/bin"
ExecStart=/home/ubuntu/appli_KBIS/venv/bin/gunicorn --workers 3 --bind unix:/home/ubuntu/appli_KBIS/gestimmob.sock gestion_immobiliere.wsgi:application

[Install]
WantedBy=multi-user.target" | sudo tee /etc/systemd/system/gestimmob.service

# Démarrer le service
sudo systemctl start gestimmob
sudo systemctl enable gestimmob

echo "✅ Application déployée !"
```

---

## ⚙️ **Configuration Nginx**

### **Fichier de configuration**
```nginx
# /etc/nginx/sites-available/gestimmob

server {
    listen 80;
    server_name votre-domaine.com www.votre-domaine.com;

    location = /favicon.ico { access_log off; log_not_found off; }
    location /static/ {
        root /home/ubuntu/appli_KBIS;
    }

    location /media/ {
        root /home/ubuntu/appli_KBIS;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/home/ubuntu/appli_KBIS/gestimmob.sock;
    }
}
```

---

## 🔒 **Sécurité VPS**

### **Configuration de base**
```bash
# Configuration du firewall
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable

# Configuration SSH
sudo nano /etc/ssh/sshd_config
# Désactiver l'authentification par mot de passe
# Changer le port SSH (optionnel)

# Redémarrage SSH
sudo systemctl restart ssh
```

---

## 📊 **Monitoring et maintenance**

### **Surveillance des performances**
```bash
# Installation de htop
sudo apt install htop

# Surveillance des logs
sudo journalctl -u gestimmob -f

# Surveillance de l'espace disque
df -h

# Surveillance de la mémoire
free -h
```

### **Sauvegardes automatiques**
```bash
#!/bin/bash
# backup.sh

# Sauvegarde de la base de données
pg_dump gestimmob_db > backup_$(date +%Y%m%d).sql

# Sauvegarde des fichiers
tar -czf backup_files_$(date +%Y%m%d).tar.gz /home/ubuntu/appli_KBIS

# Nettoyage des anciennes sauvegardes
find /home/ubuntu/backups -name "backup_*" -mtime +7 -delete
```

---

## 🎯 **Recommandation pour votre projet**

### **Pour commencer : Hébergement Partagé**
- **Prix** : 3-5€/mois
- **Facilité** : Maximum
- **Temps** : 10 minutes
- **Idéal pour** : Test, démonstration

### **Pour la production : VPS**
- **Prix** : 15-25€/mois
- **Facilité** : Moyenne
- **Temps** : 1-2 heures
- **Idéal pour** : Production, clients

---

## 🚀 **Démarrage rapide VPS**

### **Option 1 : Script automatique**
```bash
# Télécharger et exécuter
wget https://raw.githubusercontent.com/votre-repo/setup-vps.sh
chmod +x setup-vps.sh
./setup-vps.sh
```

### **Option 2 : Docker (avancé)**
```dockerfile
# Dockerfile pour VPS
FROM python:3.9-slim

WORKDIR /app
COPY requirements_production.txt .
RUN pip install -r requirements_production.txt

COPY . .
EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "gestion_immobiliere.wsgi:application"]
```

---

## 💡 **Conseils Pro VPS**

### **Performance**
- Utilisez Redis pour le cache
- Configurez la compression Nginx
- Optimisez les requêtes Django

### **Sécurité**
- Mettez à jour régulièrement
- Configurez les sauvegardes
- Surveillez les logs

### **Monitoring**
- Installez un outil de monitoring
- Configurez les alertes
- Surveillez les performances

---

## 🎉 **Conclusion**

**Votre application Django peut parfaitement fonctionner sur un VPS LWS !**

**Recommandation :**
1. **Commencez** par l'hébergement partagé (3-5€/mois)
2. **Testez** votre application
3. **Migrez** vers VPS si nécessaire (15-25€/mois)

**Avantages VPS :**
- Performance supérieure
- Contrôle total
- Évolutivité
- Sécurité renforcée

**Voulez-vous que je vous aide à configurer le VPS ou préférez-vous commencer par l'hébergement partagé ?**





