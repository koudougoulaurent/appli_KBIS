/**
 * Fix pour l'affichage des champs select - Priorité aux options visibles
 * Ce script s'assure que les champs select affichent d'abord les options, puis permettent la recherche
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log('🔧 Fix des champs select chargé');
    
    // Fonction pour corriger l'affichage des champs select
    function fixSelectDisplay() {
        const selects = document.querySelectorAll('select.form-select, select.form-control, .form-select');
        
        selects.forEach(select => {
            // S'assurer que le champ est visible
            select.style.display = 'block';
            select.style.visibility = 'visible';
            select.style.opacity = '1';
            select.style.overflow = 'visible';
            select.style.zIndex = '999';
            select.style.backgroundColor = 'white';
            select.style.color = '#212529';
            
            // S'assurer que les options sont visibles
            const options = select.querySelectorAll('option');
            options.forEach(option => {
                option.style.display = 'block';
                option.style.visibility = 'visible';
                option.style.opacity = '1';
                option.style.backgroundColor = 'white';
                option.style.color = '#212529';
            });
            
            // Désactiver Select2 si présent
            if (select.classList.contains('select2-hidden-accessible')) {
                select.classList.remove('select2-hidden-accessible');
                select.style.display = 'block';
                select.style.visibility = 'visible';
                select.style.opacity = '1';
            }
            
            // S'assurer que le champ n'est pas masqué par d'autres éléments
            select.style.position = 'relative';
            select.style.zIndex = '1';
        });
        
        console.log(`✅ ${selects.length} champs select corrigés`);
    }
    
    // Corriger immédiatement
    fixSelectDisplay();
    
    // Corriger après un délai pour s'assurer que tous les scripts sont chargés
    setTimeout(fixSelectDisplay, 1000);
    
    // Corriger lors des changements de contenu (pour les formulaires dynamiques)
    const observer = new MutationObserver(function(mutations) {
        let shouldFix = false;
        mutations.forEach(function(mutation) {
            if (mutation.type === 'childList') {
                mutation.addedNodes.forEach(function(node) {
                    if (node.nodeType === 1) { // Element node
                        if (node.tagName === 'SELECT' || node.querySelector('select')) {
                            shouldFix = true;
                        }
                    }
                });
            }
        });
        
        if (shouldFix) {
            setTimeout(fixSelectDisplay, 100);
        }
    });
    
    // Observer les changements dans le body
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
    
    // Fonction pour forcer l'affichage des options
    function forceOptionsDisplay() {
        const selects = document.querySelectorAll('select');
        
        selects.forEach(select => {
            // Désactiver tous les styles qui pourraient masquer les options
            select.style.setProperty('display', 'block', 'important');
            select.style.setProperty('visibility', 'visible', 'important');
            select.style.setProperty('opacity', '1', 'important');
            select.style.setProperty('overflow', 'visible', 'important');
            select.style.setProperty('z-index', '999', 'important');
            
            // S'assurer que les options sont visibles
            const options = select.querySelectorAll('option');
            options.forEach(option => {
                option.style.setProperty('display', 'block', 'important');
                option.style.setProperty('visibility', 'visible', 'important');
                option.style.setProperty('opacity', '1', 'important');
                option.style.setProperty('background-color', 'white', 'important');
                option.style.setProperty('color', '#212529', 'important');
            });
        });
    }
    
    // Exposer la fonction globalement pour un usage manuel
    window.fixSelectDisplay = fixSelectDisplay;
    window.forceOptionsDisplay = forceOptionsDisplay;
    
    // Corriger lors du clic sur les champs select
    document.addEventListener('click', function(e) {
        if (e.target.tagName === 'SELECT' || e.target.closest('select')) {
            setTimeout(fixSelectDisplay, 50);
        }
    });
    
    // Corriger lors du focus sur les champs select
    document.addEventListener('focus', function(e) {
        if (e.target.tagName === 'SELECT') {
            setTimeout(fixSelectDisplay, 50);
        }
    }, true);
    
    console.log('✅ Fix des champs select initialisé avec succès');
});
