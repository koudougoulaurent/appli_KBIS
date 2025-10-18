// dashboard-dynamic.js
// Script pour la mise à jour dynamique des statistiques du dashboard

document.addEventListener('DOMContentLoaded', function() {
    // Configuration
    const REFRESH_INTERVAL = 60000; // 1 minute
    const API_ENDPOINT = '/api/dashboard-stats/';
    
    // Éléments du DOM
    const elements = {
        'total-proprietes': 'total-proprietes',
        'contrats-actifs': 'contrats-actifs',
        'total-paiements': 'total-paiements',
        'total-bailleurs': 'total-bailleurs',
        'proprietes-louees': 'proprietes-louees',
        'proprietes-disponibles': 'proprietes-disponibles',
        'contrats-actifs-module': 'contrats-actifs-module',
        'total-contrats-module': 'total-contrats-module',
        'total-paiements-module': 'total-paiements-module',
        'paiements-attente': 'paiements-attente',
        'total-bailleurs-module': 'total-bailleurs-module',
        'total-locataires': 'total-locataires'
    };
    
    // Fonction pour mettre à jour les statistiques
    function updateStats() {
        fetch(API_ENDPOINT)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                console.log('Statistiques mises à jour:', data);
                
                // Mettre à jour chaque élément
                Object.keys(elements).forEach(key => {
                    const elementId = elements[key];
                    const element = document.getElementById(elementId);
                    if (element && data[key] !== undefined) {
                        // Animation de mise à jour
                        element.style.transition = 'all 0.3s ease';
                        element.style.transform = 'scale(1.1)';
                        element.style.color = '#10b981';
                        
                        // Mettre à jour la valeur
                        element.textContent = data[key];
                        
                        // Retour à la normale
                        setTimeout(() => {
                            element.style.transform = 'scale(1)';
                            element.style.color = '';
                        }, 300);
                    }
                });
                
                // Mettre à jour l'horodatage
                const timestampElement = document.querySelector('.alert-info small');
                if (timestampElement && data.derniere_maj) {
                    timestampElement.textContent = `Dernière mise à jour: ${data.derniere_maj}`;
                }
                
                // Indicateur de statut
                const statusElement = document.querySelector('.alert-info strong');
                if (statusElement) {
                    statusElement.innerHTML = '<i class="bi bi-check-circle me-2 text-success"></i>Statistiques dynamiques';
                }
                
            })
            .catch(error => {
                console.error('Erreur lors de la mise à jour des statistiques:', error);
                
                // Indicateur d'erreur
                const statusElement = document.querySelector('.alert-info strong');
                if (statusElement) {
                    statusElement.innerHTML = '<i class="bi bi-exclamation-triangle me-2 text-warning"></i>Erreur de mise à jour';
                }
            });
    }
    
    // Fonction pour forcer la mise à jour
    function forceUpdate() {
        const refreshButton = document.querySelector('a[href*="refresh=1"]');
        if (refreshButton) {
            refreshButton.addEventListener('click', function(e) {
                e.preventDefault();
                
                // Afficher un indicateur de chargement
                const originalText = this.innerHTML;
                this.innerHTML = '<i class="bi bi-arrow-clockwise me-1 spin"></i>Actualisation...';
                this.classList.add('disabled');
                
                // Rediriger vers la page avec refresh
                window.location.href = this.href;
            });
        }
    }
    
    // Fonction pour ajouter des styles d'animation
    function addAnimationStyles() {
        const style = document.createElement('style');
        style.textContent = `
            .spin {
                animation: spin 1s linear infinite;
            }
            
            @keyframes spin {
                from { transform: rotate(0deg); }
                to { transform: rotate(360deg); }
            }
            
            .stat-number {
                transition: all 0.3s ease;
            }
            
            .stat-number.updating {
                transform: scale(1.1);
                color: #10b981 !important;
            }
        `;
        document.head.appendChild(style);
    }
    
    // Fonction pour afficher les notifications de mise à jour
    function showUpdateNotification() {
        const notification = document.createElement('div');
        notification.className = 'alert alert-success alert-dismissible fade show position-fixed';
        notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        notification.innerHTML = `
            <i class="bi bi-check-circle me-2"></i>
            <strong>Statistiques mises à jour</strong>
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(notification);
        
        // Supprimer automatiquement après 3 secondes
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 3000);
    }
    
    // Initialisation
    function init() {
        console.log('Initialisation du dashboard dynamique...');
        
        // Ajouter les styles d'animation
        addAnimationStyles();
        
        // Configurer le bouton de rafraîchissement
        forceUpdate();
        
        // Mise à jour automatique
        setInterval(updateStats, REFRESH_INTERVAL);
        
        // Mise à jour initiale
        updateStats();
        
        console.log('Dashboard dynamique initialisé avec succès');
    }
    
    // Démarrer l'initialisation
    init();
});

// Fonction globale pour forcer la mise à jour (peut être appelée depuis la console)
window.refreshDashboardStats = function() {
    const event = new CustomEvent('refreshDashboard');
    document.dispatchEvent(event);
};
