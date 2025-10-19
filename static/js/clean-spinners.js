/**
 * Script pour nettoyer tous les spinners et indicateurs de chargement
 */
(function() {
    'use strict';
    
    console.log('Nettoyage des spinners et indicateurs de chargement...');
    
    // Fonction pour nettoyer les spinners et effets de grisage
    function cleanSpinners() {
        // Supprimer tous les spinners visibles
        const spinners = document.querySelectorAll('.spinner, .loading, .loading-indicator, .spinner-border, .spinner-grow');
        spinners.forEach(spinner => {
            spinner.style.display = 'none';
            spinner.remove();
        });
        
        // Supprimer les animations de rotation
        const rotatingElements = document.querySelectorAll('[class*="spin"], [class*="rotate"]');
        rotatingElements.forEach(element => {
            element.style.animation = 'none';
            element.classList.remove('spin', 'rotate');
        });
        
        // Nettoyer les indicateurs de chargement globaux
        const globalLoading = document.getElementById('global-loading');
        if (globalLoading) {
            globalLoading.style.display = 'none';
            globalLoading.remove();
        }
        
        // Nettoyer les overlays de grisage
        const overlays = document.querySelectorAll('[id*="loading"], [class*="loading"], [id*="overlay"], [class*="overlay"]');
        overlays.forEach(overlay => {
            if (overlay.style.position === 'fixed' || overlay.style.position === 'absolute') {
                overlay.style.display = 'none';
                overlay.style.opacity = '0';
                overlay.style.pointerEvents = 'none';
            }
        });
        
        // Supprimer les classes de chargement et grisage
        document.body.classList.remove('loading', 'loading-page', 'page-loading');
        
        // Supprimer les classes show des éléments de chargement
        const showElements = document.querySelectorAll('.show');
        showElements.forEach(element => {
            if (element.id.includes('loading') || element.classList.contains('loading')) {
                element.classList.remove('show');
                element.style.display = 'none';
            }
        });
        
        // Nettoyer les alertes d'erreur de mise à jour
        const errorAlerts = document.querySelectorAll('.alert-info strong');
        errorAlerts.forEach(alert => {
            if (alert.innerHTML.includes('Erreur de mise à jour')) {
                alert.innerHTML = '<i class="bi bi-info-circle me-2 text-info"></i>Statistiques statiques';
            }
        });
        
        console.log('Spinners et effets de grisage nettoyés avec succès');
    }
    
    // Nettoyer immédiatement
    cleanSpinners();
    
    // Nettoyer périodiquement (toutes les 5 secondes)
    setInterval(cleanSpinners, 5000);
    
    // Nettoyer lors des changements de page
    window.addEventListener('beforeunload', cleanSpinners);
    
    // Nettoyer lors du retour en arrière
    window.addEventListener('popstate', cleanSpinners);
    
    // Exposer la fonction globalement
    window.cleanSpinners = cleanSpinners;
    
    console.log('Script de nettoyage des spinners initialisé');
})();
