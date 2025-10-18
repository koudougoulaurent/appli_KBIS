/**
 * Optimiseur de performances côté client pour l'application de gestion immobilière
 * Améliore le chargement, la navigation et l'expérience utilisateur
 */

class PerformanceOptimizer {
    constructor() {
        this.initialized = false;
        this.lazyImages = [];
        this.intersectionObserver = null;
        this.debounceTimers = {};
        this.init();
    }

    init() {
        if (this.initialized) return;
        
        this.setupLazyLoading();
        this.setupIntersectionObserver();
        this.setupPerformanceMonitoring();
        this.setupNavigationOptimization();
        this.setupFormOptimization();
        this.setupTableOptimization();
        this.setupSearchOptimization();
        
        this.initialized = true;
        console.log('PerformanceOptimizer initialisé');
    }

    /**
     * Configuration du chargement différé des images
     */
    setupLazyLoading() {
        this.lazyImages = document.querySelectorAll('img[data-src], img[loading="lazy"]');
        
        if ('IntersectionObserver' in window) {
            this.intersectionObserver = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        this.loadImage(entry.target);
                        this.intersectionObserver.unobserve(entry.target);
                    }
                });
            }, {
                rootMargin: '50px 0px',
                threshold: 0.01
            });

            this.lazyImages.forEach(img => {
                this.intersectionObserver.observe(img);
            });
        } else {
            // Fallback pour les navigateurs plus anciens
            this.lazyImages.forEach(img => {
                this.loadImage(img);
            });
        }
    }

    /**
     * Charger une image de manière optimisée
     */
    loadImage(img) {
        const src = img.dataset.src || img.src;
        if (!src) return;

        // Créer une nouvelle image pour précharger
        const tempImage = new Image();
        tempImage.onload = () => {
            img.src = src;
            img.classList.remove('lazy');
            img.classList.add('loaded');
        };
        tempImage.onerror = () => {
            img.classList.add('error');
            console.warn(`Impossible de charger l'image: ${src}`);
        };
        tempImage.src = src;
    }

    /**
     * Configuration de l'observateur d'intersection
     */
    setupIntersectionObserver() {
        if (!('IntersectionObserver' in window)) return;

        // Observer pour les éléments qui apparaissent dans le viewport
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('in-viewport');
                    
                    // Charger les données si nécessaire
                    if (entry.target.dataset.loadData) {
                        this.loadDataForElement(entry.target);
                    }
                }
            });
        }, {
            threshold: 0.1,
            rootMargin: '100px'
        });

        // Observer tous les éléments avec data-observe
        document.querySelectorAll('[data-observe]').forEach(el => {
            observer.observe(el);
        });
    }

    /**
     * Charger des données pour un élément
     */
    loadDataForElement(element) {
        const dataUrl = element.dataset.loadData;
        if (!dataUrl || element.dataset.loaded) return;

        fetch(dataUrl)
            .then(response => response.json())
            .then(data => {
                this.updateElementWithData(element, data);
                element.dataset.loaded = 'true';
            })
            .catch(error => {
                console.error('Erreur lors du chargement des données:', error);
            });
    }

    /**
     * Mettre à jour un élément avec des données
     */
    updateElementWithData(element, data) {
        // Implémentation spécifique selon le type d'élément
        if (element.classList.contains('table-row')) {
            this.updateTableRow(element, data);
        } else if (element.classList.contains('card')) {
            this.updateCard(element, data);
        }
    }

    /**
     * Configuration du monitoring des performances
     */
    setupPerformanceMonitoring() {
        // Mesurer le temps de chargement de la page
        window.addEventListener('load', () => {
            const loadTime = performance.now();
            this.sendPerformanceMetric('page_load_time', loadTime);
            
            // Mesurer les métriques Web Vitals
            if ('PerformanceObserver' in window) {
                this.observeWebVitals();
            }
        });

        // Mesurer le temps de navigation
        let navigationStart = performance.now();
        document.addEventListener('DOMContentLoaded', () => {
            const domLoadTime = performance.now() - navigationStart;
            this.sendPerformanceMetric('dom_load_time', domLoadTime);
        });
    }

    /**
     * Observer les métriques Web Vitals
     */
    observeWebVitals() {
        // LCP (Largest Contentful Paint)
        const lcpObserver = new PerformanceObserver((list) => {
            const entries = list.getEntries();
            const lastEntry = entries[entries.length - 1];
            this.sendPerformanceMetric('lcp', lastEntry.startTime);
        });
        lcpObserver.observe({ entryTypes: ['largest-contentful-paint'] });

        // FID (First Input Delay)
        const fidObserver = new PerformanceObserver((list) => {
            const entries = list.getEntries();
            entries.forEach(entry => {
                this.sendPerformanceMetric('fid', entry.processingStart - entry.startTime);
            });
        });
        fidObserver.observe({ entryTypes: ['first-input'] });

        // CLS (Cumulative Layout Shift)
        const clsObserver = new PerformanceObserver((list) => {
            let clsValue = 0;
            list.getEntries().forEach(entry => {
                if (!entry.hadRecentInput) {
                    clsValue += entry.value;
                }
            });
            this.sendPerformanceMetric('cls', clsValue);
        });
        clsObserver.observe({ entryTypes: ['layout-shift'] });
    }

    /**
     * Envoyer une métrique de performance
     */
    sendPerformanceMetric(name, value) {
        // Envoyer au serveur ou à un service d'analytics
        if (navigator.sendBeacon) {
            const data = new FormData();
            data.append('metric', name);
            data.append('value', value.toString());
            data.append('timestamp', Date.now().toString());
            data.append('url', window.location.pathname);
            
            navigator.sendBeacon('/api/performance-metrics/', data);
        }
        
        // Stocker localement pour analyse
        this.storePerformanceMetric(name, value);
    }

    /**
     * Stocker une métrique de performance localement
     */
    storePerformanceMetric(name, value) {
        const metrics = JSON.parse(localStorage.getItem('performance_metrics') || '{}');
        if (!metrics[name]) {
            metrics[name] = [];
        }
        metrics[name].push({
            value: value,
            timestamp: Date.now(),
            url: window.location.pathname
        });
        
        // Garder seulement les 100 dernières métriques
        if (metrics[name].length > 100) {
            metrics[name] = metrics[name].slice(-100);
        }
        
        localStorage.setItem('performance_metrics', JSON.stringify(metrics));
    }

    /**
     * Configuration de l'optimisation de navigation
     */
    setupNavigationOptimization() {
        // Précharger les liens dans le viewport
        document.addEventListener('mouseover', (e) => {
            if (e.target.tagName === 'A') {
                this.preloadPage(e.target.href);
            }
        });

        // Précharger les pages suivantes dans les listes
        this.preloadNextPages();
    }

    /**
     * Précharger une page
     */
    preloadPage(url) {
        if (!url || url === window.location.href) return;
        
        const link = document.createElement('link');
        link.rel = 'prefetch';
        link.href = url;
        document.head.appendChild(link);
    }

    /**
     * Précharger les pages suivantes
     */
    preloadNextPages() {
        const paginationLinks = document.querySelectorAll('.pagination .page-link');
        paginationLinks.forEach(link => {
            if (link.textContent.trim() === 'Suivant' || link.textContent.trim() === 'Next') {
                this.preloadPage(link.href);
            }
        });
    }

    /**
     * Configuration de l'optimisation des formulaires
     */
    setupFormOptimization() {
        // Validation en temps réel avec debounce
        document.querySelectorAll('form').forEach(form => {
            const inputs = form.querySelectorAll('input, select, textarea');
            inputs.forEach(input => {
                input.addEventListener('input', this.debounce(() => {
                    this.validateField(input);
                }, 300));
            });
        });

        // Soumission optimisée des formulaires
        document.querySelectorAll('form').forEach(form => {
            form.addEventListener('submit', (e) => {
                this.optimizeFormSubmission(e);
            });
        });
    }

    /**
     * Validation d'un champ
     */
    validateField(field) {
        // Implémentation de la validation en temps réel
        const value = field.value.trim();
        const fieldName = field.name;
        
        // Supprimer les anciens messages d'erreur
        const existingError = field.parentNode.querySelector('.field-error');
        if (existingError) {
            existingError.remove();
        }

        // Validation spécifique selon le type de champ
        let isValid = true;
        let errorMessage = '';

        if (field.hasAttribute('required') && !value) {
            isValid = false;
            errorMessage = 'Ce champ est requis';
        } else if (field.type === 'email' && value && !this.isValidEmail(value)) {
            isValid = false;
            errorMessage = 'Email invalide';
        }

        if (!isValid) {
            this.showFieldError(field, errorMessage);
        }
    }

    /**
     * Afficher une erreur de champ
     */
    showFieldError(field, message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'field-error text-danger small mt-1';
        errorDiv.textContent = message;
        field.parentNode.appendChild(errorDiv);
    }

    /**
     * Validation d'email
     */
    isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }

    /**
     * Optimisation de la soumission de formulaire
     */
    optimizeFormSubmission(event) {
        const form = event.target;
        const submitButton = form.querySelector('button[type="submit"]');
        
        if (submitButton) {
            submitButton.disabled = true;
            submitButton.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Envoi en cours...';
        }

        // Validation finale avant envoi
        if (!this.validateForm(form)) {
            event.preventDefault();
            if (submitButton) {
                submitButton.disabled = false;
                submitButton.innerHTML = 'Envoyer';
            }
            return;
        }
    }

    /**
     * Validation complète d'un formulaire
     */
    validateForm(form) {
        const requiredFields = form.querySelectorAll('[required]');
        let isValid = true;

        requiredFields.forEach(field => {
            if (!field.value.trim()) {
                this.showFieldError(field, 'Ce champ est requis');
                isValid = false;
            }
        });

        return isValid;
    }

    /**
     * Configuration de l'optimisation des tableaux
     */
    setupTableOptimization() {
        // Pagination virtuelle pour les gros tableaux
        document.querySelectorAll('table[data-virtual-pagination]').forEach(table => {
            this.setupVirtualPagination(table);
        });

        // Tri optimisé des colonnes
        document.querySelectorAll('th[data-sortable]').forEach(header => {
            header.addEventListener('click', (e) => {
                this.sortTableColumn(e.target);
            });
        });
    }

    /**
     * Configuration de la pagination virtuelle
     */
    setupVirtualPagination(table) {
        const rows = table.querySelectorAll('tbody tr');
        const pageSize = parseInt(table.dataset.pageSize) || 50;
        let currentPage = 0;

        const showPage = (page) => {
            const start = page * pageSize;
            const end = start + pageSize;

            rows.forEach((row, index) => {
                if (index >= start && index < end) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        };

        // Afficher la première page
        showPage(0);

        // Ajouter les contrôles de pagination
        this.addPaginationControls(table, Math.ceil(rows.length / pageSize), showPage);
    }

    /**
     * Ajouter les contrôles de pagination
     */
    addPaginationControls(table, totalPages, showPageCallback) {
        const paginationContainer = document.createElement('div');
        paginationContainer.className = 'pagination-controls d-flex justify-content-center mt-3';
        
        let currentPage = 0;

        const updatePagination = () => {
            paginationContainer.innerHTML = '';
            
            // Bouton précédent
            if (currentPage > 0) {
                const prevButton = document.createElement('button');
                prevButton.className = 'btn btn-outline-primary me-2';
                prevButton.textContent = 'Précédent';
                prevButton.onclick = () => {
                    currentPage--;
                    showPageCallback(currentPage);
                    updatePagination();
                };
                paginationContainer.appendChild(prevButton);
            }

            // Numéros de page
            for (let i = 0; i < totalPages; i++) {
                const pageButton = document.createElement('button');
                pageButton.className = `btn ${i === currentPage ? 'btn-primary' : 'btn-outline-primary'} me-1`;
                pageButton.textContent = i + 1;
                pageButton.onclick = () => {
                    currentPage = i;
                    showPageCallback(currentPage);
                    updatePagination();
                };
                paginationContainer.appendChild(pageButton);
            }

            // Bouton suivant
            if (currentPage < totalPages - 1) {
                const nextButton = document.createElement('button');
                nextButton.className = 'btn btn-outline-primary ms-2';
                nextButton.textContent = 'Suivant';
                nextButton.onclick = () => {
                    currentPage++;
                    showPageCallback(currentPage);
                    updatePagination();
                };
                paginationContainer.appendChild(nextButton);
            }
        };

        updatePagination();
        table.parentNode.appendChild(paginationContainer);
    }

    /**
     * Configuration de l'optimisation de recherche
     */
    setupSearchOptimization() {
        // Recherche en temps réel avec debounce
        document.querySelectorAll('input[data-search]').forEach(searchInput => {
            searchInput.addEventListener('input', this.debounce(() => {
                this.performSearch(searchInput);
            }, 300));
        });
    }

    /**
     * Effectuer une recherche
     */
    performSearch(searchInput) {
        const query = searchInput.value.trim();
        const searchTarget = searchInput.dataset.search;
        const targetElement = document.querySelector(searchTarget);

        if (!targetElement) return;

        if (query.length < 2) {
            // Afficher tous les éléments si la recherche est trop courte
            this.showAllElements(targetElement);
            return;
        }

        // Recherche dans les éléments
        this.filterElements(targetElement, query);
    }

    /**
     * Filtrer les éléments selon la recherche
     */
    filterElements(container, query) {
        const elements = container.querySelectorAll('[data-searchable]');
        const queryLower = query.toLowerCase();

        elements.forEach(element => {
            const searchableText = element.dataset.searchable.toLowerCase();
            if (searchableText.includes(queryLower)) {
                element.style.display = '';
                element.classList.add('search-highlight');
            } else {
                element.style.display = 'none';
                element.classList.remove('search-highlight');
            }
        });
    }

    /**
     * Afficher tous les éléments
     */
    showAllElements(container) {
        const elements = container.querySelectorAll('[data-searchable]');
        elements.forEach(element => {
            element.style.display = '';
            element.classList.remove('search-highlight');
        });
    }

    /**
     * Fonction utilitaire debounce
     */
    debounce(func, wait) {
        return (...args) => {
            clearTimeout(this.debounceTimers[func]);
            this.debounceTimers[func] = setTimeout(() => func.apply(this, args), wait);
        };
    }

    /**
     * Nettoyer les ressources
     */
    destroy() {
        if (this.intersectionObserver) {
            this.intersectionObserver.disconnect();
        }
        
        // Nettoyer les timers
        Object.values(this.debounceTimers).forEach(timer => {
            clearTimeout(timer);
        });
        
        this.initialized = false;
    }
}

// Initialisation automatique
document.addEventListener('DOMContentLoaded', () => {
    window.performanceOptimizer = new PerformanceOptimizer();
});

// Export pour utilisation dans d'autres modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PerformanceOptimizer;
}
