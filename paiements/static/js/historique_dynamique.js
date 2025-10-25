/**
 * JavaScript pour l'affichage dynamique de l'historique des paiements
 * Gère les boutons "Par Contrat" et "Par Locataire"
 */

document.addEventListener('DOMContentLoaded', function() {
    // Éléments du DOM
    const btnParContrat = document.getElementById('btn-par-contrat');
    const btnParLocataire = document.getElementById('btn-par-locataire');
    const contenuDynamique = document.getElementById('contenu-dynamique');
    const loadingSpinner = document.getElementById('loading-spinner');
    
    // État actuel
    let vueActuelle = 'contrats'; // 'contrats' ou 'locataires'
    
    // Initialisation
    if (btnParContrat && btnParLocataire && contenuDynamique) {
        // Charger le contenu initial (contrats)
        chargerContenu('contrats');
        
        // Événements des boutons
        btnParContrat.addEventListener('click', function() {
            if (vueActuelle !== 'contrats') {
                chargerContenu('contrats');
            }
        });
        
        btnParLocataire.addEventListener('click', function() {
            if (vueActuelle !== 'locataires') {
                chargerContenu('locataires');
            }
        });
    }
    
    /**
     * Charge le contenu dynamiquement
     * @param {string} type - 'contrats' ou 'locataires'
     */
    function chargerContenu(type) {
        // Afficher le spinner
        if (loadingSpinner) {
            loadingSpinner.style.display = 'block';
        }
        
        // Mettre à jour l'état
        vueActuelle = type;
        
        // Mettre à jour les styles des boutons
        mettreAJourBoutons(type);
        
        // Simuler un délai pour l'effet de chargement
        setTimeout(() => {
            genererContenu(type);
            if (loadingSpinner) {
                loadingSpinner.style.display = 'none';
            }
        }, 300);
    }
    
    /**
     * Met à jour les styles des boutons
     * @param {string} type - Type de vue active
     */
    function mettreAJourBoutons(type) {
        if (type === 'contrats') {
            btnParContrat.classList.add('active');
            btnParContrat.classList.remove('inactive');
            btnParLocataire.classList.add('inactive');
            btnParLocataire.classList.remove('active');
        } else {
            btnParLocataire.classList.add('active');
            btnParLocataire.classList.remove('inactive');
            btnParContrat.classList.add('inactive');
            btnParContrat.classList.remove('active');
        }
    }
    
    /**
     * Génère le contenu selon le type
     * @param {string} type - 'contrats' ou 'locataires'
     */
    function genererContenu(type) {
        if (type === 'contrats') {
            genererContenuContrats();
        } else {
            genererContenuLocataires();
        }
    }
    
    /**
     * Génère le contenu pour les contrats
     */
    function genererContenuContrats() {
        const contenu = `
            <div class="row">
                <div class="col-12">
                    <div class="card shadow-sm">
                        <div class="card-header bg-primary text-white">
                            <h5 class="mb-0">
                                <i class="fas fa-file-contract me-2"></i>
                                Top 5 Contrats les Plus Actifs
                            </h5>
                        </div>
                        <div class="card-body">
                            <div class="table-responsive">
                                <table class="table table-hover">
                                    <thead class="table-light">
                                        <tr>
                                            <th>#</th>
                                            <th>Contrat</th>
                                            <th>Locataire</th>
                                            <th>Propriété</th>
                                            <th>Paiements</th>
                                            <th>Actions</th>
                                        </tr>
                                    </thead>
                                    <tbody id="table-contrats">
                                        <tr>
                                            <td colspan="6" class="text-center">
                                                <div class="spinner-border text-primary" role="status">
                                                    <span class="visually-hidden">Chargement...</span>
                                                </div>
                                            </td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="row mt-4">
                <div class="col-12">
                    <div class="card shadow-sm">
                        <div class="card-header bg-info text-white">
                            <h5 class="mb-0">
                                <i class="fas fa-chart-line me-2"></i>
                                Statistiques des Contrats
                            </h5>
                        </div>
                        <div class="card-body">
                            <div class="row">
                                <div class="col-md-3">
                                    <div class="text-center">
                                        <h3 class="text-primary" id="total-contrats">-</h3>
                                        <p class="text-muted">Total Contrats</p>
                                    </div>
                                </div>
                                <div class="col-md-3">
                                    <div class="text-center">
                                        <h3 class="text-success" id="contrats-actifs">-</h3>
                                        <p class="text-muted">Contrats Actifs</p>
                                    </div>
                                </div>
                                <div class="col-md-3">
                                    <div class="text-center">
                                        <h3 class="text-warning" id="contrats-resilies">-</h3>
                                        <p class="text-muted">Contrats Résiliés</p>
                                    </div>
                                </div>
                                <div class="col-md-3">
                                    <div class="text-center">
                                        <h3 class="text-info" id="revenus-totaux">-</h3>
                                        <p class="text-muted">Revenus Totaux</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        contenuDynamique.innerHTML = contenu;
        
        // Charger les données des contrats
        chargerDonneesContrats();
    }
    
    /**
     * Génère le contenu pour les locataires
     */
    function genererContenuLocataires() {
        const contenu = `
            <div class="row">
                <div class="col-12">
                    <div class="card shadow-sm">
                        <div class="card-header bg-success text-white">
                            <h5 class="mb-0">
                                <i class="fas fa-users me-2"></i>
                                Top 5 Locataires les Plus Actifs
                            </h5>
                        </div>
                        <div class="card-body">
                            <div class="table-responsive">
                                <table class="table table-hover">
                                    <thead class="table-light">
                                        <tr>
                                            <th>#</th>
                                            <th>Locataire</th>
                                            <th>Contrats</th>
                                            <th>Paiements</th>
                                            <th>Dernier Paiement</th>
                                            <th>Actions</th>
                                        </tr>
                                    </thead>
                                    <tbody id="table-locataires">
                                        <tr>
                                            <td colspan="6" class="text-center">
                                                <div class="spinner-border text-success" role="status">
                                                    <span class="visually-hidden">Chargement...</span>
                                                </div>
                                            </td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="row mt-4">
                <div class="col-12">
                    <div class="card shadow-sm">
                        <div class="card-header bg-warning text-dark">
                            <h5 class="mb-0">
                                <i class="fas fa-chart-pie me-2"></i>
                                Statistiques des Locataires
                            </h5>
                        </div>
                        <div class="card-body">
                            <div class="row">
                                <div class="col-md-3">
                                    <div class="text-center">
                                        <h3 class="text-success" id="total-locataires">-</h3>
                                        <p class="text-muted">Total Locataires</p>
                                    </div>
                                </div>
                                <div class="col-md-3">
                                    <div class="text-center">
                                        <h3 class="text-primary" id="locataires-actifs">-</h3>
                                        <p class="text-muted">Locataires Actifs</p>
                                    </div>
                                </div>
                                <div class="col-md-3">
                                    <div class="text-center">
                                        <h3 class="text-info" id="moyenne-contrats">-</h3>
                                        <p class="text-muted">Moy. Contrats/Locataire</p>
                                    </div>
                                </div>
                                <div class="col-md-3">
                                    <div class="text-center">
                                        <h3 class="text-warning" id="moyenne-paiements">-</h3>
                                        <p class="text-muted">Moy. Paiements/Locataire</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        contenuDynamique.innerHTML = contenu;
        
        // Charger les données des locataires
        chargerDonneesLocataires();
    }
    
    /**
     * Charge les données des contrats via AJAX
     */
    function chargerDonneesContrats() {
        // Simuler des données (en production, ce serait un appel AJAX)
        const donneesContrats = [
            {
                id: 1,
                numero: 'CON-2025-001',
                locataire: 'Jean Dupont',
                propriete: 'Appartement A1',
                paiements: 12,
                montant: '150,000 FCFA'
            },
            {
                id: 2,
                numero: 'CON-2025-002',
                locataire: 'Marie Martin',
                propriete: 'Appartement B2',
                paiements: 8,
                montant: '120,000 FCFA'
            },
            {
                id: 3,
                numero: 'CON-2025-003',
                locataire: 'Pierre Durand',
                propriete: 'Villa C3',
                paiements: 15,
                montant: '200,000 FCFA'
            }
        ];
        
        const tbody = document.getElementById('table-contrats');
        if (tbody) {
            tbody.innerHTML = donneesContrats.map((contrat, index) => `
                <tr>
                    <td>${index + 1}</td>
                    <td><strong>${contrat.numero}</strong></td>
                    <td>${contrat.locataire}</td>
                    <td>${contrat.propriete}</td>
                    <td>
                        <span class="badge bg-primary">${contrat.paiements} paiements</span>
                    </td>
                    <td>
                        <a href="/contrats/detail/${contrat.id}/" class="btn btn-sm btn-outline-primary">
                            <i class="fas fa-eye"></i> Voir
                        </a>
                        <a href="/paiements/historique/contrat/${contrat.id}/" class="btn btn-sm btn-outline-info">
                            <i class="fas fa-history"></i> Historique
                        </a>
                    </td>
                </tr>
            `).join('');
        }
        
        // Mettre à jour les statistiques
        document.getElementById('total-contrats').textContent = '25';
        document.getElementById('contrats-actifs').textContent = '18';
        document.getElementById('contrats-resilies').textContent = '7';
        document.getElementById('revenus-totaux').textContent = '3,500,000 FCFA';
    }
    
    /**
     * Charge les données des locataires via AJAX
     */
    function chargerDonneesLocataires() {
        // Simuler des données (en production, ce serait un appel AJAX)
        const donneesLocataires = [
            {
                id: 1,
                nom: 'Jean Dupont',
                contrats: 2,
                paiements: 24,
                dernierPaiement: '15 Oct 2025'
            },
            {
                id: 2,
                nom: 'Marie Martin',
                contrats: 1,
                paiements: 8,
                dernierPaiement: '10 Oct 2025'
            },
            {
                id: 3,
                nom: 'Pierre Durand',
                contrats: 3,
                paiements: 15,
                dernierPaiement: '20 Oct 2025'
            }
        ];
        
        const tbody = document.getElementById('table-locataires');
        if (tbody) {
            tbody.innerHTML = donneesLocataires.map((locataire, index) => `
                <tr>
                    <td>${index + 1}</td>
                    <td><strong>${locataire.nom}</strong></td>
                    <td>
                        <span class="badge bg-info">${locataire.contrats} contrats</span>
                    </td>
                    <td>
                        <span class="badge bg-success">${locataire.paiements} paiements</span>
                    </td>
                    <td>${locataire.dernierPaiement}</td>
                    <td>
                        <a href="/proprietes/locataires/${locataire.id}/" class="btn btn-sm btn-outline-primary">
                            <i class="fas fa-user"></i> Profil
                        </a>
                        <a href="/paiements/historique/locataire/${locataire.id}/" class="btn btn-sm btn-outline-info">
                            <i class="fas fa-history"></i> Historique
                        </a>
                    </td>
                </tr>
            `).join('');
        }
        
        // Mettre à jour les statistiques
        document.getElementById('total-locataires').textContent = '45';
        document.getElementById('locataires-actifs').textContent = '38';
        document.getElementById('moyenne-contrats').textContent = '1.8';
        document.getElementById('moyenne-paiements').textContent = '12.5';
    }
});

