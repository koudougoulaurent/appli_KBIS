/**
 * Script pour empêcher les effets de grisage lors de la navigation
 */
(function() {
    'use strict';
    
    console.log('Protection contre les effets de grisage activée...');
    
    // Fonction pour supprimer tous les effets de grisage
    function removeGrayingEffects() {
        // Supprimer tous les overlays de chargement
        const overlays = document.querySelectorAll('[id*="loading"], [class*="loading"], [id*="overlay"], [class*="overlay"]');
        overlays.forEach(overlay => {
            overlay.style.display = 'none';
            overlay.style.opacity = '0';
            overlay.style.visibility = 'hidden';
            overlay.style.pointerEvents = 'none';
            overlay.classList.remove('show', 'active', 'visible');
        });
        
        // Supprimer les classes de grisage du body
        document.body.classList.remove('loading', 'loading-page', 'page-loading', 'grayed-out', 'disabled');
        
        // Supprimer les styles de grisage
        document.body.style.opacity = '1';
        document.body.style.pointerEvents = 'auto';
        document.body.style.filter = 'none';
        
        // Supprimer les éléments de chargement globaux
        const globalElements = document.querySelectorAll('#global-loading, .global-loading, .page-loader');
        globalElements.forEach(element => {
            element.style.display = 'none';
            element.remove();
        });
        
        // Supprimer les spinners
        const spinners = document.querySelectorAll('.spinner, .spinner-border, .spinner-grow, .loading-spinner');
        spinners.forEach(spinner => {
            spinner.style.display = 'none';
            spinner.remove();
        });
        
        console.log('Effets de grisage supprimés');
    }
    
    // Fonction pour empêcher l'activation des effets de grisage
    function preventGrayingActivation() {
        // Intercepter les événements qui pourraient déclencher le grisage
        const originalAddEventListener = Element.prototype.addEventListener;
        Element.prototype.addEventListener = function(type, listener, options) {
            // Empêcher l'ajout de classes de chargement
            if (type === 'click' && listener.toString().includes('loading')) {
                console.log('Événement de chargement intercepté et bloqué');
                return;
            }
            return originalAddEventListener.call(this, type, listener, options);
        };
        
        // Intercepter les modifications de classes
        const originalClassListAdd = DOMTokenList.prototype.add;
        DOMTokenList.prototype.add = function(...tokens) {
            // Bloquer l'ajout de classes de chargement
            const filteredTokens = tokens.filter(token => 
                !token.includes('loading') && 
                !token.includes('grayed') && 
                !token.includes('disabled')
            );
            return originalClassListAdd.apply(this, filteredTokens);
        };
        
        // Intercepter les modifications de style
        const originalStyleSetProperty = CSSStyleDeclaration.prototype.setProperty;
        CSSStyleDeclaration.prototype.setProperty = function(property, value, priority) {
            // Bloquer les propriétés qui causent le grisage
            if (property === 'opacity' && value < '1') {
                console.log('Tentative de grisage bloquée');
                return;
            }
            if (property === 'pointer-events' && value === 'none') {
                console.log('Désactivation des pointeurs bloquée');
                return;
            }
            return originalStyleSetProperty.call(this, property, value, priority);
        };
    }
    
    // Fonction pour gérer les événements de navigation
    function handleNavigationEvents() {
        // Gérer le bouton retour du navigateur
        window.addEventListener('popstate', function(event) {
            console.log('Bouton retour détecté - suppression des effets de grisage');
            removeGrayingEffects();
        });
        
        // Gérer les changements de page
        window.addEventListener('beforeunload', function(event) {
            removeGrayingEffects();
        });
        
        // Gérer le chargement de la page
        window.addEventListener('load', function(event) {
            removeGrayingEffects();
        });
        
        // Gérer les clics sur les liens
        document.addEventListener('click', function(event) {
            if (event.target.tagName === 'A' || event.target.closest('a')) {
                console.log('Clic sur lien détecté - protection contre le grisage');
                removeGrayingEffects();
            }
        });
    }
    
    // Initialisation
    function init() {
        console.log('Initialisation de la protection anti-grisage...');
        
        // Supprimer immédiatement tous les effets de grisage
        removeGrayingEffects();
        
        // Empêcher l'activation de nouveaux effets
        preventGrayingActivation();
        
        // Gérer les événements de navigation
        handleNavigationEvents();
        
        // Nettoyer périodiquement
        setInterval(removeGrayingEffects, 1000);
        
        console.log('Protection anti-grisage activée');
    }
    
    // Démarrer immédiatement
    init();
    
    // Exposer les fonctions globalement
    window.removeGrayingEffects = removeGrayingEffects;
    window.preventGrayingActivation = preventGrayingActivation;
    
})();
