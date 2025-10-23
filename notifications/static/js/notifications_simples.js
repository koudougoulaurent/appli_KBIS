/**
 * Système de Notifications Simples et Efficaces
 * Gestion simple des notifications sans complexité SMS
 */

class NotificationManagerSimple {
    constructor() {
        this.pollInterval = 15000; // 15 secondes (plus simple)
        this.retryInterval = 10000; // 10 secondes
        this.maxRetries = 2;
        this.retryCount = 0;
        this.isPolling = false;
        this.soundEnabled = true;
        this.toastEnabled = true;
        this.notifications = new Map();
        
        this.init();
    }
    
    init() {
        console.log('🔔 Initialisation du système de notifications simples');
        
        // Démarrer le polling
        this.startPolling();
        
        // Initialiser les event listeners
        this.setupEventListeners();
        
        // Charger les notifications existantes
        this.loadInitialNotifications();
        
        // Initialiser les sons
        this.initSounds();
        
        console.log('✅ Système de notifications simples initialisé');
    }
    
    startPolling() {
        if (this.isPolling) return;
        
        this.isPolling = true;
        console.log('🔄 Démarrage du polling simple des notifications');
        
        // Polling immédiat
        this.checkNewNotifications();
        
        // Polling périodique
        this.pollingInterval = setInterval(() => {
            this.checkNewNotifications();
        }, this.pollInterval);
    }
    
    stopPolling() {
        if (this.pollingInterval) {
            clearInterval(this.pollingInterval);
            this.pollingInterval = null;
        }
        this.isPolling = false;
        console.log('⏹️ Arrêt du polling des notifications');
    }
    
    async checkNewNotifications() {
        try {
            const response = await fetch('/notifications/api/simples/unread-count/');
            const data = await response.json();
            
            if (data.success) {
                this.updateNotificationBadge(data.unread_count);
                this.retryCount = 0; // Reset retry count on success
            }
        } catch (error) {
            console.error('Erreur vérification notifications:', error);
            this.handlePollingError();
        }
    }
    
    handlePollingError() {
        this.retryCount++;
        
        if (this.retryCount < this.maxRetries) {
            console.log(`🔄 Tentative ${this.retryCount}/${this.maxRetries} dans ${this.retryInterval/1000}s`);
            setTimeout(() => {
                this.checkNewNotifications();
            }, this.retryInterval);
        } else {
            console.error('❌ Échec du polling après', this.maxRetries, 'tentatives');
            this.stopPolling();
        }
    }
    
    updateNotificationBadge(count) {
        const badge = document.getElementById('notification-badge');
        if (!badge) return;
        
        if (count > 0) {
            badge.textContent = count > 99 ? '99+' : count;
            badge.style.display = 'inline';
            badge.classList.add('pulse');
            
            // Retirer l'animation après 2 secondes
            setTimeout(() => {
                badge.classList.remove('pulse');
            }, 2000);
        } else {
            badge.style.display = 'none';
        }
    }
    
    async loadInitialNotifications() {
        try {
            const response = await fetch('/notifications/api/simples/?limit=10');
            const data = await response.json();
            
            if (data.success) {
                this.displayNotifications(data.notifications);
            }
        } catch (error) {
            console.error('Erreur chargement notifications initiales:', error);
        }
    }
    
    displayNotifications(notifications) {
        const container = document.getElementById('notifications-list');
        if (!container) return;
        
        container.innerHTML = '';
        
        if (notifications.length === 0) {
            container.innerHTML = `
                <li class="dropdown-item text-center text-muted">
                    <i class="bi bi-bell-slash"></i> Aucune notification
                </li>
            `;
            return;
        }
        
        notifications.forEach(notification => {
            const notificationElement = this.createNotificationElement(notification);
            container.appendChild(notificationElement);
        });
    }
    
    createNotificationElement(notification) {
        const li = document.createElement('li');
        li.className = `dropdown-item notification-item ${notification.is_read ? 'read' : 'unread'}`;
        li.dataset.notificationId = notification.id;
        
        const config = this.getNotificationConfig(notification.type);
        
        li.innerHTML = `
            <div class="d-flex align-items-start">
                <div class="notification-icon me-2">
                    <i class="bi ${config.icon} text-${config.color}"></i>
                </div>
                <div class="flex-grow-1">
                    <div class="notification-title">${notification.title}</div>
                    <div class="notification-message">${notification.message}</div>
                    <div class="notification-meta">
                        <small class="text-muted">${notification.time_ago}</small>
                        ${!notification.is_read ? '<span class="badge bg-primary ms-2">Nouveau</span>' : ''}
                    </div>
                </div>
                <div class="notification-actions">
                    ${!notification.is_read ? 
                        `<button class="btn btn-sm btn-outline-primary" onclick="notificationManagerSimple.markAsRead(${notification.id})" title="Marquer comme lu">
                            <i class="bi bi-check"></i>
                        </button>` : ''
                    }
                    <button class="btn btn-sm btn-outline-danger" onclick="notificationManagerSimple.deleteNotification(${notification.id})" title="Supprimer">
                        <i class="bi bi-trash"></i>
                    </button>
                </div>
            </div>
        `;
        
        // Ajouter un event listener pour marquer comme lu au clic
        li.addEventListener('click', (e) => {
            if (!e.target.closest('.notification-actions')) {
                this.markAsRead(notification.id);
            }
        });
        
        return li;
    }
    
    getNotificationConfig(type) {
        const configs = {
            'payment_received': { icon: 'bi-cash-stack', color: 'success' },
            'payment_partial': { icon: 'bi-cash-coin', color: 'warning' },
            'payment_overdue': { icon: 'bi-exclamation-triangle', color: 'danger' },
            'advance_consumed': { icon: 'bi-arrow-down-circle', color: 'info' },
            'contract_expiring': { icon: 'bi-calendar-x', color: 'warning' },
            'retrait_created': { icon: 'bi-bank', color: 'primary' },
            'system_alert': { icon: 'bi-gear', color: 'secondary' },
            'info': { icon: 'bi-info-circle', color: 'info' }
        };
        
        return configs[type] || { icon: 'bi-bell', color: 'secondary' };
    }
    
    async markAsRead(notificationId) {
        try {
            const response = await fetch(`/notifications/api/simples/mark-read/${notificationId}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCSRFToken(),
                    'Content-Type': 'application/json'
                }
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Mettre à jour l'interface
                const element = document.querySelector(`[data-notification-id="${notificationId}"]`);
                if (element) {
                    element.classList.remove('unread');
                    element.classList.add('read');
                    
                    // Supprimer le badge "Nouveau"
                    const badge = element.querySelector('.badge');
                    if (badge) badge.remove();
                    
                    // Mettre à jour le bouton
                    const button = element.querySelector('.notification-actions button');
                    if (button) button.remove();
                }
                
                // Actualiser le compteur
                this.checkNewNotifications();
                
                this.showToast('Notification marquée comme lue', 'success');
            }
        } catch (error) {
            console.error('Erreur marquage notification:', error);
            this.showToast('Erreur lors du marquage', 'error');
        }
    }
    
    async deleteNotification(notificationId) {
        if (!confirm('Supprimer cette notification ?')) return;
        
        try {
            const response = await fetch(`/notifications/api/simples/delete/${notificationId}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCSRFToken(),
                    'Content-Type': 'application/json'
                }
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Supprimer l'élément de l'interface
                const element = document.querySelector(`[data-notification-id="${notificationId}"]`);
                if (element) {
                    element.remove();
                }
                
                // Actualiser le compteur
                this.checkNewNotifications();
                
                this.showToast('Notification supprimée', 'success');
            }
        } catch (error) {
            console.error('Erreur suppression notification:', error);
            this.showToast('Erreur lors de la suppression', 'error');
        }
    }
    
    async markAllAsRead() {
        try {
            const response = await fetch('/notifications/api/simples/mark-all-read/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCSRFToken(),
                    'Content-Type': 'application/json'
                }
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Mettre à jour toutes les notifications visibles
                document.querySelectorAll('.notification-item.unread').forEach(element => {
                    element.classList.remove('unread');
                    element.classList.add('read');
                    
                    const badge = element.querySelector('.badge');
                    if (badge) badge.remove();
                    
                    const button = element.querySelector('.notification-actions button');
                    if (button) button.remove();
                });
                
                // Actualiser le compteur
                this.checkNewNotifications();
                
                this.showToast(data.message, 'success');
            }
        } catch (error) {
            console.error('Erreur marquage toutes notifications:', error);
            this.showToast('Erreur lors du marquage', 'error');
        }
    }
    
    showToast(message, type = 'info') {
        if (!this.toastEnabled) return;
        
        const toast = document.createElement('div');
        toast.className = `toast-notification toast-${type}`;
        toast.innerHTML = `
            <div class="toast-content">
                <i class="bi ${this.getToastIcon(type)}"></i>
                <span>${message}</span>
                <button class="btn-close" onclick="this.parentElement.parentElement.remove()"></button>
            </div>
        `;
        
        // Ajouter au DOM
        let container = document.getElementById('toast-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toast-container';
            container.className = 'toast-container';
            document.body.appendChild(container);
        }
        
        container.appendChild(toast);
        
        // Animation d'entrée
        setTimeout(() => {
            toast.classList.add('show');
        }, 100);
        
        // Auto-suppression
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.parentNode.removeChild(toast);
                }
            }, 300);
        }, 5000);
        
        // Son
        if (this.soundEnabled) {
            this.playSound(type);
        }
    }
    
    getToastIcon(type) {
        const icons = {
            'success': 'bi-check-circle',
            'error': 'bi-exclamation-triangle',
            'warning': 'bi-exclamation-circle',
            'info': 'bi-info-circle'
        };
        return icons[type] || 'bi-info-circle';
    }
    
    initSounds() {
        // Sons simples
        this.sounds = {
            success: this.createSound(800, 0.1),
            error: this.createSound(400, 0.2),
            warning: this.createSound(600, 0.15),
            info: this.createSound(1000, 0.1),
            alert: this.createSound(300, 0.3)
        };
    }
    
    createSound(frequency, duration) {
        return () => {
            if (!this.soundEnabled) return;
            
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();
            
            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);
            
            oscillator.frequency.value = frequency;
            oscillator.type = 'sine';
            
            gainNode.gain.setValueAtTime(0.1, audioContext.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + duration);
            
            oscillator.start(audioContext.currentTime);
            oscillator.stop(audioContext.currentTime + duration);
        };
    }
    
    playSound(type) {
        if (this.sounds && this.sounds[type]) {
            this.sounds[type]();
        }
    }
    
    setupEventListeners() {
        // Event listener pour les clics sur la cloche
        const bell = document.querySelector('[data-bs-toggle="dropdown"]');
        if (bell) {
            bell.addEventListener('click', () => {
                this.loadInitialNotifications();
            });
        }
        
        // Event listener pour la visibilité de la page
        document.addEventListener('visibilitychange', () => {
            if (document.visibilityState === 'visible') {
                this.checkNewNotifications();
            }
        });
    }
    
    getCSRFToken() {
        const token = document.querySelector('[name=csrfmiddlewaretoken]');
        return token ? token.value : '';
    }
    
    // Méthodes publiques pour l'interface
    refresh() {
        this.loadInitialNotifications();
        this.checkNewNotifications();
    }
    
    toggleSound() {
        this.soundEnabled = !this.soundEnabled;
        this.showToast(`Son ${this.soundEnabled ? 'activé' : 'désactivé'}`, 'info');
    }
    
    toggleToast() {
        this.toastEnabled = !this.toastEnabled;
        this.showToast(`Notifications ${this.toastEnabled ? 'activées' : 'désactivées'}`, 'info');
    }
}

// Initialiser le gestionnaire de notifications simples
const notificationManagerSimple = new NotificationManagerSimple();

// Fonctions globales pour l'interface
window.markAllAsReadSimple = () => notificationManagerSimple.markAllAsRead();
window.refreshNotificationsSimple = () => notificationManagerSimple.refresh();
window.toggleNotificationSoundSimple = () => notificationManagerSimple.toggleSound();
window.toggleNotificationToastSimple = () => notificationManagerSimple.toggleToast();

