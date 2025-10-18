/**
 * 🔍 SCRIPT DE DÉBOGAGE POUR LES BOUTONS
 * Ce script aide à identifier pourquoi les boutons ne répondent plus
 */

(function() {
    'use strict';
    
    // Fonction de débogage sécurisée
    function safeLog(message, data) {
        if (typeof console !== 'undefined' && console.log) {
            console.log('🔍 DEBUG BUTTONS:', message, data || '');
        }
    }
    
    // Vérifier les dépendances
    function checkDependencies() {
        const deps = {
            jQuery: typeof $ !== 'undefined',
            Bootstrap: typeof bootstrap !== 'undefined',
            Select2: typeof $ !== 'undefined' && $.fn && $.fn.select2
        };
        
        safeLog('Dépendances chargées:', deps);
        return deps;
    }
    
    // Vérifier les boutons
    function checkButtons() {
        const buttons = document.querySelectorAll('button, .btn, input[type="submit"]');
        safeLog('Nombre de boutons trouvés:', buttons.length);
        
        buttons.forEach((btn, index) => {
            const info = {
                index: index,
                id: btn.id || 'sans-id',
                classes: btn.className || 'sans-classes',
                type: btn.type || btn.tagName,
                disabled: btn.disabled,
                hasClickListener: btn.onclick !== null
            };
            
            if (index < 5) { // Afficher seulement les 5 premiers pour éviter le spam
                safeLog(`Bouton ${index + 1}:`, info);
            }
        });
        
        return buttons;
    }
    
    // Ajouter des event listeners de débogage
    function addDebugListeners() {
        document.addEventListener('click', function(e) {
            if (e.target.matches('button, .btn, input[type="submit"]')) {
                safeLog('Clic sur bouton détecté:', {
                    element: e.target.tagName,
                    id: e.target.id || 'sans-id',
                    classes: e.target.className || 'sans-classes',
                    disabled: e.target.disabled
                });
            }
        });
        
        document.addEventListener('submit', function(e) {
            safeLog('Soumission de formulaire détectée:', {
                form: e.target.id || 'sans-id',
                action: e.target.action || 'sans-action'
            });
        });
    }
    
    // Initialisation du débogage
    function initDebug() {
        safeLog('=== DÉBUT DU DÉBOGAGE DES BOUTONS ===');
        
        const deps = checkDependencies();
        const buttons = checkButtons();
        
        // Vérifier si des erreurs JavaScript existent
        window.addEventListener('error', function(e) {
            safeLog('ERREUR JavaScript détectée:', {
                message: e.message,
                filename: e.filename,
                line: e.lineno,
                column: e.colno
            });
        });
        
        addDebugListeners();
        
        safeLog('=== DÉBOGAGE INITIALISÉ ===');
        
        return {
            dependencies: deps,
            buttonCount: buttons.length,
            timestamp: new Date().toISOString()
        };
    }
    
    // Démarrer le débogage quand le DOM est prêt
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initDebug);
    } else {
        initDebug();
    }
    
    // Exposer les fonctions de débogage globalement
    window.debugButtons = {
        check: checkButtons,
        dependencies: checkDependencies,
        init: initDebug
    };
    
})();
