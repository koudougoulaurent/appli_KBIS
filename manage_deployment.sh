#!/bin/bash

# Script de gestion des déploiements
# Menu principal pour gérer les mises à jour et déploiements

set -e

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Variables
APP_DIR="/var/www/kbis_immobilier"
BACKUP_DIR="/var/backups/kbis_immobilier"

# Fonction pour afficher le menu
show_menu() {
    echo -e "${BLUE}🚀 GESTIONNAIRE DE DÉPLOIEMENT KBIS${NC}"
    echo "=================================="
    echo ""
    echo "1. Mise à jour sécurisée (dernière version)"
    echo "2. Déploiement depuis un commit spécifique"
    echo "3. Retour en arrière (rollback)"
    echo "4. Vérifier l'état de l'application"
    echo "5. Lister les sauvegardes disponibles"
    echo "6. Nettoyer les anciennes sauvegardes"
    echo "7. Quitter"
    echo ""
    echo -e "${YELLOW}Choisissez une option (1-7):${NC}"
}

# Fonction pour vérifier l'état de l'application
check_app_status() {
    echo -e "\n${YELLOW}📊 ÉTAT DE L'APPLICATION${NC}"
    echo "========================"
    
    # Vérifier gunicorn
    if pgrep -f gunicorn > /dev/null; then
        echo -e "${GREEN}✅ Gunicorn: ACTIF${NC}"
        echo "   PID: $(pgrep -f gunicorn)"
    else
        echo -e "${RED}❌ Gunicorn: INACTIF${NC}"
    fi
    
    # Vérifier nginx
    if sudo systemctl is-active --quiet nginx; then
        echo -e "${GREEN}✅ Nginx: ACTIF${NC}"
    else
        echo -e "${RED}❌ Nginx: INACTIF${NC}"
    fi
    
    # Vérifier les ports
    echo -e "\n${YELLOW}Ports ouverts:${NC}"
    netstat -tlnp | grep -E ":(80|443|8000) " || echo "Aucun port ouvert"
    
    # Test de connectivité
    echo -e "\n${YELLOW}Test de connectivité:${NC}"
    if curl -s -I https://78.138.58.185 >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Application accessible via HTTPS${NC}"
    else
        echo -e "${RED}❌ Application non accessible${NC}"
    fi
    
    # Informations Git
    echo -e "\n${YELLOW}Informations Git:${NC}"
    cd $APP_DIR
    echo "Branche actuelle: $(git branch --show-current)"
    echo "Dernier commit: $(git log -1 --oneline)"
    echo "État du dépôt: $(git status --porcelain | wc -l) fichiers modifiés"
}

# Fonction pour lister les sauvegardes
list_backups() {
    echo -e "\n${YELLOW}📁 SAUVEGARDES DISPONIBLES${NC}"
    echo "========================"
    
    if [ ! -d "$BACKUP_DIR" ]; then
        echo -e "${RED}❌ Aucune sauvegarde trouvée${NC}"
        return
    fi
    
    echo "Sauvegardes de configuration:"
    ls -la $BACKUP_DIR/settings_*.py 2>/dev/null | tail -10 || echo "Aucune sauvegarde de configuration"
    
    echo -e "\nSauvegardes de base de données:"
    ls -la $BACKUP_DIR/database_*.json 2>/dev/null | tail -10 || echo "Aucune sauvegarde de base de données"
    
    echo -e "\nSauvegardes Nginx:"
    ls -la $BACKUP_DIR/nginx_*.conf 2>/dev/null | tail -10 || echo "Aucune sauvegarde Nginx"
}

# Fonction pour nettoyer les anciennes sauvegardes
cleanup_backups() {
    echo -e "\n${YELLOW}🧹 NETTOYAGE DES ANCIENNES SAUVEGARDES${NC}"
    echo "====================================="
    
    if [ ! -d "$BACKUP_DIR" ]; then
        echo -e "${RED}❌ Aucune sauvegarde trouvée${NC}"
        return
    fi
    
    # Compter les sauvegardes
    backup_count=$(ls $BACKUP_DIR/*.py $BACKUP_DIR/*.json $BACKUP_DIR/*.conf 2>/dev/null | wc -l)
    echo "Nombre de sauvegardes: $backup_count"
    
    if [ $backup_count -gt 20 ]; then
        echo "Suppression des sauvegardes de plus de 30 jours..."
        find $BACKUP_DIR -name "*.py" -mtime +30 -delete
        find $BACKUP_DIR -name "*.json" -mtime +30 -delete
        find $BACKUP_DIR -name "*.conf" -mtime +30 -delete
        echo -e "${GREEN}✅ Nettoyage terminé${NC}"
    else
        echo -e "${YELLOW}⚠️  Pas assez de sauvegardes pour le nettoyage${NC}"
    fi
}

# Boucle principale
while true; do
    show_menu
    read -r choice
    
    case $choice in
        1)
            echo -e "\n${YELLOW}🔄 Mise à jour sécurisée...${NC}"
            bash update_app_safe.sh
            ;;
        2)
            echo -e "\n${YELLOW}🚀 Déploiement depuis un commit...${NC}"
            bash deploy_from_commit.sh
            ;;
        3)
            echo -e "\n${YELLOW}⏪ Retour en arrière...${NC}"
            bash rollback_app.sh
            ;;
        4)
            check_app_status
            ;;
        5)
            list_backups
            ;;
        6)
            cleanup_backups
            ;;
        7)
            echo -e "\n${GREEN}👋 Au revoir !${NC}"
            exit 0
            ;;
        *)
            echo -e "\n${RED}❌ Option invalide. Veuillez choisir entre 1 et 7.${NC}"
            ;;
    esac
    
    echo -e "\n${YELLOW}Appuyez sur Entrée pour continuer...${NC}"
    read -r
done

