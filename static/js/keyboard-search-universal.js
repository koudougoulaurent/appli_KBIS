/**
 * Système de recherche clavier universel pour tous les éléments de sélection
 * Permet de taper directement au clavier pour filtrer les options
 */

class KeyboardSearchUniversal {
    constructor() {
        this.init();
    }

    init() {
        // Initialiser Select2 sur tous les éléments avec data-toggle="select2"
        this.initSelect2();
        
        // Initialiser la recherche clavier sur les selects normaux
        this.initKeyboardSearch();
        
        // Initialiser la recherche sur les inputs de recherche personnalisés
        this.initCustomSearch();
    }

    /**
     * Initialiser Select2 avec recherche clavier
     */
    initSelect2() {
        const self = this; // Sauvegarder la référence à la classe
        $('[data-toggle="select2"]').each(function() {
            const $element = $(this);
            
            // Configuration Select2 avec recherche clavier
            $element.select2({
                placeholder: $element.attr('data-placeholder') || 'Recherchez...',
                allowClear: true,
                width: '100%',
                language: {
                    noResults: function() {
                        return "Aucun résultat trouvé";
                    },
                    searching: function() {
                        return "Recherche en cours...";
                    },
                    inputTooShort: function() {
                        return "Tapez au moins 1 caractère";
                    }
                },
                // Configuration pour la recherche clavier
                matcher: function(params, data) {
                    // Si aucun terme de recherche, afficher tous les résultats
                    if ($.trim(params.term) === '') {
                        return data;
                    }

                    // Recherche insensible à la casse
                    const term = params.term.toLowerCase();
                    const text = data.text.toLowerCase();
                    
                    // Recherche dans le texte affiché
                    if (text.indexOf(term) > -1) {
                        return data;
                    }
                    
                    // Recherche dans les attributs data
                    const $option = $(data.element);
                    const dataAttributes = $option.data();
                    
                    for (const key in dataAttributes) {
                        if (typeof dataAttributes[key] === 'string' && 
                            dataAttributes[key].toLowerCase().indexOf(term) > -1) {
                            return data;
                        }
                    }
                    
                    return null;
                },
                // Configuration pour l'ouverture automatique
                dropdownParent: $element.parent(),
                // Améliorer l'accessibilité
                selectOnClose: false,
                closeOnSelect: true
            });

            // Ajouter des événements clavier personnalisés
            self.addKeyboardEvents($element);
        });
    }

    /**
     * Initialiser la recherche clavier sur les selects normaux
     */
    initKeyboardSearch() {
        $('select:not([data-toggle="select2"])').each(function() {
            const $select = $(this);
            
            // Créer un wrapper avec input de recherche
            if (!$select.parent().hasClass('keyboard-search-wrapper')) {
                $select.wrap('<div class="keyboard-search-wrapper position-relative"></div>');
                
                const $wrapper = $select.parent();
                const $searchInput = $(`
                    <input type="text" 
                           class="form-control keyboard-search-input" 
                           placeholder="Tapez pour rechercher..." 
                           autocomplete="off"
                           style="display: none;">
                `);
                
                $wrapper.prepend($searchInput);
                
                // Gérer l'ouverture/fermeture
                $select.on('focus click', function() {
                    $searchInput.show().focus();
                    $select.hide();
                });
                
                $searchInput.on('blur', function() {
                    setTimeout(() => {
                        $searchInput.hide();
                        $select.show();
                    }, 200);
                });
                
                // Gérer la recherche
                $searchInput.on('input', function() {
                    const searchTerm = $(this).val().toLowerCase();
                    $select.find('option').each(function() {
                        const $option = $(this);
                        const text = $option.text().toLowerCase();
                        
                        if (text.indexOf(searchTerm) > -1 || searchTerm === '') {
                            $option.show();
                        } else {
                            $option.hide();
                        }
                    });
                });
                
                // Gérer la sélection
                $searchInput.on('keydown', function(e) {
                    if (e.key === 'Enter') {
                        const $visibleOptions = $select.find('option:visible:not(:first)');
                        if ($visibleOptions.length > 0) {
                            $visibleOptions.first().prop('selected', true);
                            $select.trigger('change');
                            $searchInput.blur();
                        }
                    }
                });
            }
        });
    }

    /**
     * Initialiser la recherche sur les inputs personnalisés
     */
    initCustomSearch() {
        // Recherche de bailleurs
        this.initBailleurSearch();
        
        // Recherche de locataires
        this.initLocataireSearch();
        
        // Recherche de contrats
        this.initContratSearch();
        
        // Recherche de propriétés
        this.initProprieteSearch();
    }

    /**
     * Recherche de bailleurs avec clavier
     */
    initBailleurSearch() {
        $('#bailleur_search, #bailleur-search-input').on('input', function() {
            const searchTerm = $(this).val().toLowerCase();
            const $dropdown = $('#bailleur_dropdown, .bailleur-dropdown');
            const $options = $dropdown.find('.dropdown-item');
            
            $options.each(function() {
                const $item = $(this);
                const text = $item.text().toLowerCase();
                
                if (text.indexOf(searchTerm) > -1 || searchTerm === '') {
                    $item.show();
                } else {
                    $item.hide();
                }
            });
            
            // Afficher/masquer le dropdown
            if (searchTerm.length > 0) {
                $dropdown.show();
            } else {
                $dropdown.hide();
            }
        });
    }

    /**
     * Recherche de locataires avec clavier
     */
    initLocataireSearch() {
        $('#locataire_search, #locataire-search-input').on('input', function() {
            const searchTerm = $(this).val().toLowerCase();
            const $dropdown = $('#locataire_dropdown, .locataire-dropdown');
            const $options = $dropdown.find('.dropdown-item');
            
            $options.each(function() {
                const $item = $(this);
                const text = $item.text().toLowerCase();
                
                if (text.indexOf(searchTerm) > -1 || searchTerm === '') {
                    $item.show();
                } else {
                    $item.hide();
                }
            });
            
            if (searchTerm.length > 0) {
                $dropdown.show();
            } else {
                $dropdown.hide();
            }
        });
    }

    /**
     * Recherche de contrats avec clavier
     */
    initContratSearch() {
        $('#contrat_search, #contrat-search-input').on('input', function() {
            const searchTerm = $(this).val().toLowerCase();
            const $dropdown = $('#contrat_dropdown, .contrat-dropdown');
            const $options = $dropdown.find('.dropdown-item');
            
            $options.each(function() {
                const $item = $(this);
                const text = $item.text().toLowerCase();
                
                if (text.indexOf(searchTerm) > -1 || searchTerm === '') {
                    $item.show();
                } else {
                    $item.hide();
                }
            });
            
            if (searchTerm.length > 0) {
                $dropdown.show();
            } else {
                $dropdown.hide();
            }
        });
    }

    /**
     * Recherche de propriétés avec clavier
     */
    initProprieteSearch() {
        $('#propriete_search, #propriete-search-input').on('input', function() {
            const searchTerm = $(this).val().toLowerCase();
            const $dropdown = $('#propriete_dropdown, .propriete-dropdown');
            const $options = $dropdown.find('.dropdown-item');
            
            $options.each(function() {
                const $item = $(this);
                const text = $item.text().toLowerCase();
                
                if (text.indexOf(searchTerm) > -1 || searchTerm === '') {
                    $item.show();
                } else {
                    $item.hide();
                }
            });
            
            if (searchTerm.length > 0) {
                $dropdown.show();
            } else {
                $dropdown.hide();
            }
        });
    }

    /**
     * Ajouter des événements clavier personnalisés
     */
    addKeyboardEvents($element) {
        $element.on('select2:open', function() {
            // Focus automatique sur le champ de recherche
            setTimeout(() => {
                $('.select2-search__field').focus();
            }, 100);
        });
        
        // Navigation au clavier
        $element.on('select2:select', function(e) {
            // Optionnel : actions après sélection
            console.log('Élément sélectionné:', e.params.data);
        });
    }

    /**
     * Méthode pour réinitialiser la recherche
     */
    resetSearch(elementId) {
        const $element = $(`#${elementId}`);
        if ($element.length) {
            if ($element.hasClass('select2-hidden-accessible')) {
                $element.val(null).trigger('change');
            } else {
                $element.val('');
                $element.find('option').show();
            }
        }
    }

    /**
     * Méthode pour activer/désactiver la recherche
     */
    toggleSearch(elementId, enabled) {
        const $element = $(`#${elementId}`);
        if ($element.length) {
            if (enabled) {
                $element.prop('disabled', false);
            } else {
                $element.prop('disabled', true);
            }
        }
    }
}

// Initialiser automatiquement quand le DOM est prêt
$(document).ready(function() {
    // Initialiser le système de recherche clavier
    window.keyboardSearch = new KeyboardSearchUniversal();
    
    // Réinitialiser la recherche quand on change de page
    $(document).on('page:load', function() {
        if (window.keyboardSearch) {
            window.keyboardSearch.init();
        }
    });
});

// Exporter pour utilisation globale
window.KeyboardSearchUniversal = KeyboardSearchUniversal;
