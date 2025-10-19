/**
 * Script de nettoyage final pour supprimer tous les effets de grisage
 */
(function() {
    'use strict';
    
    console.log('Nettoyage final des effets de grisage...');
    
    // Fonction de nettoyage complète
    function finalCleanup() {
        // 1. Supprimer tous les éléments de chargement
        const loadingElements = document.querySelectorAll('[id*="loading"], [class*="loading"], [id*="overlay"], [class*="overlay"]');
        loadingElements.forEach(element => {
            element.style.display = 'none';
            element.style.opacity = '0';
            element.style.visibility = 'hidden';
            element.style.pointerEvents = 'auto';
            element.remove();
        });
        
        // 2. Nettoyer le body
        document.body.style.opacity = '1';
        document.body.style.pointerEvents = 'auto';
        document.body.style.filter = 'none';
        document.body.classList.remove('loading', 'loading-page', 'page-loading', 'grayed-out', 'disabled');
        
        // 3. Supprimer tous les spinners
        const spinners = document.querySelectorAll('.spinner, .spinner-border, .spinner-grow, .loading-spinner, .spinner-border-sm');
        spinners.forEach(spinner => {
            spinner.style.display = 'none';
            spinner.style.animation = 'none';
            spinner.remove();
        });
        
        // 4. Nettoyer tous les éléments avec pointer-events: none
        const allElements = document.querySelectorAll('*');
        allElements.forEach(element => {
            if (element.style.pointerEvents === 'none') {
                element.style.pointerEvents = 'auto';
            }
            if (element.style.opacity && parseFloat(element.style.opacity) < 1) {
                element.style.opacity = '1';
            }
        });
        
        // 5. Supprimer les z-index élevés
        allElements.forEach(element => {
            if (element.style.zIndex && parseInt(element.style.zIndex) > 9990) {
                element.style.zIndex = '1';
            }
        });
        
        // 6. Nettoyer les backgrounds de grisage
        allElements.forEach(element => {
            if (element.style.background && 
                (element.style.background.includes('rgba(255, 255, 255, 0.8)') ||
                 element.style.background.includes('rgba(0, 0, 0, 0.8)') ||
                 element.style.background.includes('rgba(0, 0, 0, 0.5)'))) {
                element.style.background = 'transparent';
            }
        });
        
        // 7. Supprimer les classes show des éléments de chargement
        const showElements = document.querySelectorAll('.show');
        showElements.forEach(element => {
            if (element.id.includes('loading') || element.classList.contains('loading')) {
                element.classList.remove('show');
                element.style.display = 'none';
            }
        });
        
        console.log('Nettoyage final terminé');
    }
    
    // Fonction pour intercepter les tentatives de grisage
    function interceptGrayingAttempts() {
        // Intercepter les modifications de style
        const originalSetProperty = CSSStyleDeclaration.prototype.setProperty;
        CSSStyleDeclaration.prototype.setProperty = function(property, value, priority) {
            // Bloquer les propriétés qui causent le grisage
            if (property === 'opacity' && value < '1') {
                console.log('Tentative de grisage bloquée (opacity)');
                return originalSetProperty.call(this, 'opacity', '1', priority);
            }
            if (property === 'pointer-events' && value === 'none') {
                console.log('Tentative de grisage bloquée (pointer-events)');
                return originalSetProperty.call(this, 'pointer-events', 'auto', priority);
            }
            if (property === 'filter' && value.includes('grayscale')) {
                console.log('Tentative de grisage bloquée (filter)');
                return originalSetProperty.call(this, 'filter', 'none', priority);
            }
            return originalSetProperty.call(this, property, value, priority);
        };
        
        // Intercepter les ajouts de classes
        const originalClassListAdd = DOMTokenList.prototype.add;
        DOMTokenList.prototype.add = function(...tokens) {
            const filteredTokens = tokens.filter(token => 
                !token.includes('loading') && 
                !token.includes('grayed') && 
                !token.includes('disabled') &&
                !token.includes('overlay')
            );
            return originalClassListAdd.apply(this, filteredTokens);
        };
    }
    
    // Fonction pour gérer les événements de navigation
    function handleNavigationEvents() {
        // Gérer le bouton retour du navigateur
        window.addEventListener('popstate', function(event) {
            console.log('Bouton retour détecté - nettoyage immédiat');
            finalCleanup();
        });
        
        // Gérer les changements de page
        window.addEventListener('beforeunload', function(event) {
            finalCleanup();
        });
        
        // Gérer le chargement de la page
        window.addEventListener('load', function(event) {
            finalCleanup();
        });
        
        // Gérer les clics sur les liens
        document.addEventListener('click', function(event) {
            if (event.target.tagName === 'A' || event.target.closest('a')) {
                console.log('Clic sur lien détecté - protection activée');
                finalCleanup();
            }
        });
        
        // Gérer les soumissions de formulaires
        document.addEventListener('submit', function(event) {
            console.log('Soumission de formulaire détectée - protection activée');
            finalCleanup();
        });
    }
    
    // Initialisation
    function init() {
        console.log('Initialisation du nettoyage final...');
        
        // Nettoyer immédiatement
        finalCleanup();
        
        // Intercepter les tentatives de grisage
        interceptGrayingAttempts();
        
        // Gérer les événements de navigation
        handleNavigationEvents();
        
        // Nettoyer périodiquement
        setInterval(finalCleanup, 2000);
        
        console.log('Nettoyage final initialisé');
    }
    
    // Démarrer immédiatement
    init();
    
    // Exposer les fonctions globalement
    window.finalCleanup = finalCleanup;
    window.interceptGrayingAttempts = interceptGrayingAttempts;
    
})();
