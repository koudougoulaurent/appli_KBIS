#!/bin/bash

# =============================================================================
# SYSTÈME DE NOTIFICATION AVANCÉ POUR KBIS IMMOBILIER
# =============================================================================

# Configuration
APP_NAME="kbis_immobilier"
NOTIFICATION_EMAIL="admin@votre-domaine.com"  # Changez cette adresse
SLACK_WEBHOOK_URL=""  # Optionnel: URL du webhook Slack
DISCORD_WEBHOOK_URL=""  # Optionnel: URL du webhook Discord
TELEGRAM_BOT_TOKEN=""  # Optionnel: Token du bot Telegram
TELEGRAM_CHAT_ID=""  # Optionnel: ID du chat Telegram

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Fonction de notification par email
send_email() {
    local subject="$1"
    local message="$2"
    local priority="$3"  # high, normal, low
    
    if command -v mail &> /dev/null; then
        local mail_options=""
        case "$priority" in
            "high") mail_options="-s 'URGENT: $subject'" ;;
            "low") mail_options="-s 'INFO: $subject'" ;;
            *) mail_options="-s '$subject'" ;;
        esac
        
        echo "$message" | mail $mail_options "$NOTIFICATION_EMAIL" 2>/dev/null || true
    fi
}

# Fonction de notification Slack
send_slack() {
    local message="$1"
    local color="$2"  # good, warning, danger
    
    if [ -n "$SLACK_WEBHOOK_URL" ]; then
        local payload=$(cat <<EOF
{
    "attachments": [
        {
            "color": "$color",
            "title": "KBIS Immobilier - Notification",
            "text": "$message",
            "footer": "KBIS System",
            "ts": $(date +%s)
        }
    ]
}
EOF
        )
        
        curl -X POST -H 'Content-type: application/json' \
             --data "$payload" \
             "$SLACK_WEBHOOK_URL" 2>/dev/null || true
    fi
}

# Fonction de notification Discord
send_discord() {
    local message="$1"
    local color="$2"  # hex color code
    
    if [ -n "$DISCORD_WEBHOOK_URL" ]; then
        local payload=$(cat <<EOF
{
    "embeds": [
        {
            "title": "KBIS Immobilier - Notification",
            "description": "$message",
            "color": $color,
            "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%S.000Z)",
            "footer": {
                "text": "KBIS System"
            }
        }
    ]
}
EOF
        )
        
        curl -X POST -H 'Content-type: application/json' \
             --data "$payload" \
             "$DISCORD_WEBHOOK_URL" 2>/dev/null || true
    fi
}

# Fonction de notification Telegram
send_telegram() {
    local message="$1"
    
    if [ -n "$TELEGRAM_BOT_TOKEN" ] && [ -n "$TELEGRAM_CHAT_ID" ]; then
        local url="https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/sendMessage"
        
        curl -s -X POST "$url" \
             -d "chat_id=$TELEGRAM_CHAT_ID" \
             -d "text=🚨 KBIS Immobilier%0A%0A$message" \
             -d "parse_mode=HTML" 2>/dev/null || true
    fi
}

# Fonction de notification système (wall)
send_system() {
    local message="$1"
    echo "🚨 KBIS Immobilier - $message" | wall 2>/dev/null || true
}

# Fonction de notification dans les logs système
send_system_log() {
    local level="$1"  # info, warning, error
    local message="$2"
    
    case "$level" in
        "error") logger -t "$APP_NAME" -p user.err "$message" ;;
        "warning") logger -t "$APP_NAME" -p user.warning "$message" ;;
        *) logger -t "$APP_NAME" -p user.info "$message" ;;
    esac
}

# Fonction de notification complète
send_notification() {
    local level="$1"  # info, warning, error, success
    local subject="$2"
    local message="$3"
    local details="$4"  # Détails supplémentaires optionnels
    
    # Préparer le message complet
    local full_message="$message"
    if [ -n "$details" ]; then
        full_message="$message\n\nDétails:\n$details"
    fi
    
    # Ajouter des informations système
    local system_info="\n\nSystème: $(hostname)\nDate: $(date)\nUtilisateur: $(whoami)"
    full_message="$full_message$system_info"
    
    # Déterminer les couleurs et priorités
    local color="good"
    local priority="normal"
    local log_level="info"
    
    case "$level" in
        "error")
            color="danger"
            priority="high"
            log_level="error"
            ;;
        "warning")
            color="warning"
            priority="normal"
            log_level="warning"
            ;;
        "success")
            color="good"
            priority="low"
            log_level="info"
            ;;
    esac
    
    # Envoyer toutes les notifications
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')] 📧 Envoi des notifications...${NC}"
    
    # Email
    send_email "$subject" "$full_message" "$priority"
    
    # Slack
    send_slack "$full_message" "$color"
    
    # Discord
    send_discord "$full_message" "0x${color:0:6}"
    
    # Telegram
    send_telegram "$full_message"
    
    # Système
    send_system "$subject: $message"
    
    # Logs système
    send_system_log "$log_level" "$subject: $message"
    
    echo -e "${GREEN}✅ Notifications envoyées${NC}"
}

# Fonction de test des notifications
test_notifications() {
    echo -e "${CYAN}🧪 Test du système de notifications...${NC}"
    
    # Test info
    send_notification "info" "Test Info" "Ceci est un test de notification de niveau info"
    
    sleep 2
    
    # Test warning
    send_notification "warning" "Test Warning" "Ceci est un test de notification de niveau warning"
    
    sleep 2
    
    # Test error
    send_notification "error" "Test Error" "Ceci est un test de notification de niveau error"
    
    sleep 2
    
    # Test success
    send_notification "success" "Test Success" "Ceci est un test de notification de niveau success"
    
    echo -e "${GREEN}✅ Tests de notifications terminés${NC}"
}

# Fonction de configuration
configure_notifications() {
    echo -e "${CYAN}⚙️  Configuration du système de notifications${NC}"
    
    # Configuration email
    if ! command -v mail &> /dev/null; then
        echo -e "${YELLOW}⚠️  mailutils n'est pas installé. Installation...${NC}"
        sudo apt update && sudo apt install -y mailutils
    fi
    
    # Configuration des webhooks (optionnel)
    echo ""
    echo "Configuration des webhooks (optionnel):"
    echo "1. Slack: Ajoutez votre webhook URL dans SLACK_WEBHOOK_URL"
    echo "2. Discord: Ajoutez votre webhook URL dans DISCORD_WEBHOOK_URL"
    echo "3. Telegram: Ajoutez votre bot token et chat ID"
    
    # Créer un fichier de configuration
    cat > /etc/kbis/notifications.conf <<EOF
# Configuration des notifications KBIS Immobilier
NOTIFICATION_EMAIL="$NOTIFICATION_EMAIL"
SLACK_WEBHOOK_URL="$SLACK_WEBHOOK_URL"
DISCORD_WEBHOOK_URL="$DISCORD_WEBHOOK_URL"
TELEGRAM_BOT_TOKEN="$TELEGRAM_BOT_TOKEN"
TELEGRAM_CHAT_ID="$TELEGRAM_CHAT_ID"
EOF
    
    echo -e "${GREEN}✅ Configuration sauvegardée dans /etc/kbis/notifications.conf${NC}"
}

# Fonction de monitoring automatique
start_monitoring() {
    echo -e "${CYAN}🔍 Démarrage du monitoring automatique...${NC}"
    
    # Créer un script de monitoring
    cat > /usr/local/bin/kbis_monitor.sh <<'EOF'
#!/bin/bash

# Monitoring automatique de KBIS Immobilier
APP_NAME="kbis_immobilier"
LOG_FILE="/var/log/$APP_NAME/monitor.log"

# Fonction de vérification des services
check_services() {
    if ! systemctl is-active --quiet kbis_immobilier; then
        /usr/local/bin/notification_system.sh error "Service Down" "Le service kbis_immobilier est arrêté"
        return 1
    fi
    
    if ! systemctl is-active --quiet nginx; then
        /usr/local/bin/notification_system.sh error "Service Down" "Le service nginx est arrêté"
        return 1
    fi
    
    return 0
}

# Fonction de vérification de la connectivité
check_connectivity() {
    if ! curl -f -s http://localhost > /dev/null; then
        /usr/local/bin/notification_system.sh error "Connectivity Issue" "L'application n'est pas accessible"
        return 1
    fi
    
    return 0
}

# Fonction de vérification de l'espace disque
check_disk_space() {
    local usage=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
    
    if [ "$usage" -gt 90 ]; then
        /usr/local/bin/notification_system.sh error "Disk Space" "Espace disque critique: ${usage}% utilisé"
        return 1
    elif [ "$usage" -gt 80 ]; then
        /usr/local/bin/notification_system.sh warning "Disk Space" "Espace disque élevé: ${usage}% utilisé"
    fi
    
    return 0
}

# Fonction de vérification de la mémoire
check_memory() {
    local usage=$(free | awk 'NR==2{printf "%.0f", $3*100/$2}')
    
    if [ "$usage" -gt 90 ]; then
        /usr/local/bin/notification_system.sh error "Memory Usage" "Utilisation mémoire critique: ${usage}%"
        return 1
    elif [ "$usage" -gt 80 ]; then
        /usr/local/bin/notification_system.sh warning "Memory Usage" "Utilisation mémoire élevée: ${usage}%"
    fi
    
    return 0
}

# Exécution des vérifications
check_services
check_connectivity
check_disk_space
check_memory
EOF
    
    chmod +x /usr/local/bin/kbis_monitor.sh
    
    # Ajouter au crontab pour exécution toutes les 5 minutes
    (crontab -l 2>/dev/null; echo "*/5 * * * * /usr/local/bin/kbis_monitor.sh") | crontab -
    
    echo -e "${GREEN}✅ Monitoring automatique configuré${NC}"
}

# Fonction d'aide
show_help() {
    echo -e "${CYAN}Usage: $0 [COMMAND] [OPTIONS]${NC}"
    echo ""
    echo "Commands:"
    echo "  send LEVEL SUBJECT MESSAGE [DETAILS]  Envoyer une notification"
    echo "  test                                  Tester toutes les notifications"
    echo "  configure                             Configurer le système"
    echo "  monitor                               Démarrer le monitoring automatique"
    echo "  help                                  Afficher cette aide"
    echo ""
    echo "Levels: info, warning, error, success"
    echo ""
    echo "Exemples:"
    echo "  $0 send error 'Service Down' 'Le service est arrêté'"
    echo "  $0 test"
    echo "  $0 configure"
}

# Fonction principale
main() {
    case "$1" in
        "send")
            if [ $# -lt 4 ]; then
                echo "Usage: $0 send LEVEL SUBJECT MESSAGE [DETAILS]"
                exit 1
            fi
            send_notification "$2" "$3" "$4" "$5"
            ;;
        "test")
            test_notifications
            ;;
        "configure")
            configure_notifications
            ;;
        "monitor")
            start_monitoring
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            echo "Commande inconnue: $1"
            show_help
            exit 1
            ;;
    esac
}

# Exécution
main "$@"
