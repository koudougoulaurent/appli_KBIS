/**
 * 🚀 SYSTÈME INTELLIGENT POUR LES RETRAITS DES BAILLEURS
 * 
 * Ce fichier JavaScript gère l'interface intelligente des retraits
 * avec chargement automatique du contexte et suggestions intelligentes.
 */

class ContexteIntelligentRetraits {
    constructor() {
        this.currentBailleurId = null;
        this.currentContexte = null;
        this.isLoading = false;
        
        this.init();
    }
    
    init() {
        this.bindEvents();
        this.initializeSelect2();
        this.initializeTooltips();
    }
    
    bindEvents() {
        // Écouter la sélection d'un bailleur
        const bailleurSelect = document.getElementById('bailleur-select');
        if (bailleurSelect) {
            bailleurSelect.addEventListener('change', (e) => {
                this.onBailleurChange(e.target.value);
            });
        }
        
        // Écouter les suggestions
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('suggestion-item')) {
                this.applySuggestion(e.target.dataset);
            }
        });
        
        // Écouter les changements de montants
        const montantLoyersInput = document.getElementById('montant-loyers-bruts');
        const montantChargesInput = document.getElementById('montant-charges-deductibles');
        
        if (montantLoyersInput) {
            montantLoyersInput.addEventListener('input', () => this.calculateMontantNet());
        }
        
        if (montantChargesInput) {
            montantChargesInput.addEventListener('input', () => this.calculateMontantNet());
        }
    }
    
    initializeSelect2() {
        // Initialiser Select2 pour une meilleure UX
        if (typeof $ !== 'undefined' && $.fn.select2) {
            $('#bailleur-select').select2({
                placeholder: 'Recherchez un bailleur...',
                allowClear: true,
                width: '100%'
            });
        }
    }
    
    initializeTooltips() {
        // Initialiser les tooltips Bootstrap
        if (typeof bootstrap !== 'undefined') {
            const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
            tooltipTriggerList.map(function (tooltipTriggerEl) {
                return new bootstrap.Tooltip(tooltipTriggerEl);
            });
        }
    }
    
    async onBailleurChange(bailleurId) {
        if (!bailleurId) {
            this.clearContexte();
            return;
        }
        
        this.currentBailleurId = bailleurId;
        this.showLoading();
        
        try {
            const contexte = await this.fetchContexteBailleur(bailleurId);
            if (contexte.success) {
                this.currentContexte = contexte.data;
                this.displayContexte(contexte.data);
                this.displaySuggestions(contexte.data.suggestions);
                this.updateFormWithContexte(contexte.data);
            } else {
                this.showError(`Erreur: ${contexte.error}`);
            }
        } catch (error) {
            console.error('Erreur lors du chargement du contexte:', error);
            this.showError('Erreur lors du chargement du contexte');
        } finally {
            this.hideLoading();
        }
    }
    
    async fetchContexteBailleur(bailleurId) {
        const response = await fetch(`/paiements/api/contexte-bailleur/${bailleurId}/`);
        return await response.json();
    }
    
    displayContexte(contexte) {
        this.displayBailleurInfo(contexte.bailleur);
        this.displayProprietes(contexte.proprietes);
        this.displayContrats(contexte.contrats_actifs);
        this.displayPaiementsRecents(contexte.paiements_recents);
        this.displayCharges(contexte.charges_deductibles, contexte.charges_bailleur);
        this.displayRetraitsRecents(contexte.retraits_recents);
        this.displayCalculs(contexte.calculs_automatiques);
        this.displayAlertes(contexte.alertes);
    }
    
    displayBailleurInfo(bailleur) {
        const container = document.getElementById('bailleur-info');
        if (!container) return;
        
        container.innerHTML = `
            <div class="card border-primary">
                <div class="card-header bg-primary text-white">
                    <h6 class="mb-0">
                        <i class="bi bi-person-circle me-2"></i>
                        Informations du Bailleur
                    </h6>
                </div>
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-6">
                            <p><strong>Nom:</strong> ${bailleur.nom} ${bailleur.prenom}</p>
                            <p><strong>Code:</strong> ${bailleur.code_bailleur}</p>
                            <p><strong>Email:</strong> ${bailleur.email || 'Non renseigné'}</p>
                        </div>
                        <div class="col-md-6">
                            <p><strong>Téléphone:</strong> ${bailleur.telephone || 'Non renseigné'}</p>
                            <p><strong>Statut:</strong> 
                                <span class="badge ${bailleur.est_actif ? 'bg-success' : 'bg-danger'}">
                                    ${bailleur.est_actif ? 'Actif' : 'Inactif'}
                                </span>
                            </p>
                            <p><strong>Membre depuis:</strong> ${this.formatDate(bailleur.date_creation)}</p>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
    
    displayProprietes(proprietes) {
        const container = document.getElementById('proprietes-info');
        if (!container) return;
        
        let proprietesHtml = `
            <div class="card border-info">
                <div class="card-header bg-info text-white">
                    <h6 class="mb-0">
                        <i class="bi bi-building me-2"></i>
                        Propriétés (${proprietes.total_proprietes})
                    </h6>
                </div>
                <div class="card-body">
                    <div class="row mb-3">
                        <div class="col-md-3">
                            <div class="text-center">
                                <h4 class="text-info">${proprietes.total_proprietes}</h4>
                                <small>Propriétés</small>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="text-center">
                                <h4 class="text-info">${proprietes.total_surface || 0}</h4>
                                <small>m² Total</small>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="text-center">
                                <h4 class="text-info">${proprietes.total_pieces || 0}</h4>
                                <small>Pièces</small>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="text-center">
                                <h4 class="text-info">${this.formatCurrency(proprietes.total_loyer_mensuel)}</h4>
                                <small>Loyer mensuel</small>
                            </div>
                        </div>
                    </div>
        `;
        
        if (proprietes.proprietes.length > 0) {
            proprietesHtml += '<div class="table-responsive"><table class="table table-sm">';
            proprietesHtml += '<thead><tr><th>Adresse</th><th>Type</th><th>Surface</th><th>Loyer</th></tr></thead><tbody>';
            
            proprietes.proprietes.forEach(propriete => {
                proprietesHtml += `
                    <tr>
                        <td>${propriete.adresse}</td>
                        <td><span class="badge bg-secondary">${propriete.type_propriete}</span></td>
                        <td>${propriete.surface || 0} m²</td>
                        <td>${this.formatCurrency(propriete.loyer_mensuel)}</td>
                    </tr>
                `;
            });
            
            proprietesHtml += '</tbody></table></div>';
        }
        
        proprietesHtml += '</div></div>';
        container.innerHTML = proprietesHtml;
    }
    
    displayContrats(contrats) {
        const container = document.getElementById('contrats-info');
        if (!container) return;
        
        let contratsHtml = `
            <div class="card border-success">
                <div class="card-header bg-success text-white">
                    <h6 class="mb-0">
                        <i class="bi bi-file-earmark-text me-2"></i>
                        Contrats Actifs (${contrats.total_contrats})
                    </h6>
                </div>
                <div class="card-body">
                    <div class="row mb-3">
                        <div class="col-md-6">
                            <div class="text-center">
                                <h4 class="text-success">${contrats.total_contrats}</h4>
                                <small>Contrats actifs</small>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="text-center">
                                <h4 class="text-success">${this.formatCurrency(contrats.total_loyer_mensuel)}</h4>
                                <small>Loyer mensuel total</small>
                            </div>
                        </div>
                    </div>
        `;
        
        if (contrats.contrats.length > 0) {
            contratsHtml += '<div class="table-responsive"><table class="table table-sm">';
            contratsHtml += '<thead><tr><th>Contrat</th><th>Propriété</th><th>Locataire</th><th>Loyer</th></tr></thead><tbody>';
            
            contrats.contrats.forEach(contrat => {
                contratsHtml += `
                    <tr>
                        <td><strong>${contrat.numero_contrat}</strong></td>
                        <td>${contrat.propriete_adresse}</td>
                        <td>${contrat.locataire_nom}</td>
                        <td>${this.formatCurrency(contrat.loyer_mensuel)}</td>
                    </tr>
                `;
            });
            
            contratsHtml += '</tbody></table></div>';
        }
        
        contratsHtml += '</div></div>';
        container.innerHTML = contratsHtml;
    }
    
    displayPaiementsRecents(paiements) {
        const container = document.getElementById('paiements-info');
        if (!container) return;
        
        let paiementsHtml = `
            <div class="card border-warning">
                <div class="card-header bg-warning text-dark">
                    <h6 class="mb-0">
                        <i class="bi bi-cash-coin me-2"></i>
                        Paiements Récents (5 derniers mois)
                    </h6>
                </div>
                <div class="card-body">
                    <div class="row mb-3">
                        <div class="col-md-4">
                            <div class="text-center">
                                <h4 class="text-warning">${this.formatCurrency(paiements.total_general)}</h4>
                                <small>Total général</small>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="text-center">
                                <h4 class="text-warning">${this.formatCurrency(paiements.moyenne_mensuelle)}</h4>
                                <small>Moyenne mensuelle</small>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="text-center">
                                <h4 class="text-warning">${paiements.paiements_par_mois.length}</h4>
                                <small>Mois avec paiements</small>
                            </div>
                        </div>
                    </div>
        `;
        
        if (paiements.paiements_par_mois.length > 0) {
            paiementsHtml += '<div class="table-responsive"><table class="table table-sm">';
            paiementsHtml += '<thead><tr><th>Mois</th><th>Paiements</th><th>Total</th></tr></thead><tbody>';
            
            paiements.paiements_par_mois.forEach(mois => {
                paiementsHtml += `
                    <tr>
                        <td><strong>${this.formatMonth(mois.mois)}</strong></td>
                        <td>${mois.nombre_paiements}</td>
                        <td>${this.formatCurrency(mois.total_mois)}</td>
                    </tr>
                `;
            });
            
            paiementsHtml += '</tbody></table></div>';
        }
        
        paiementsHtml += '</div></div>';
        container.innerHTML = paiementsHtml;
    }
    
    displayCharges(chargesDeductibles, chargesBailleur) {
        const container = document.getElementById('charges-info');
        if (!container) return;
        
        const totalCharges = chargesDeductibles.total_charges + chargesBailleur.total_charges;
        const totalChargesEnAttente = chargesDeductibles.charges_en_attente + chargesBailleur.charges_en_attente;
        
        let chargesHtml = `
            <div class="card border-danger">
                <div class="card-header bg-danger text-white">
                    <h6 class="mb-0">
                        <i class="bi bi-exclamation-triangle me-2"></i>
                        Charges Déductibles
                    </h6>
                </div>
                <div class="card-body">
                    <div class="row mb-3">
                        <div class="col-md-3">
                            <div class="text-center">
                                <h4 class="text-danger">${this.formatCurrency(totalCharges)}</h4>
                                <small>Total charges</small>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="text-center">
                                <h4 class="text-danger">${this.formatCurrency(totalChargesEnAttente)}</h4>
                                <small>En attente</small>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="text-center">
                                <h4 class="text-danger">${chargesDeductibles.nombre_charges}</h4>
                                <small>Charges locataire</small>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="text-center">
                                <h4 class="text-danger">${chargesBailleur.nombre_charges}</h4>
                                <small>Charges bailleur</small>
                            </div>
                        </div>
                    </div>
        `;
        
        if (chargesDeductibles.charges.length > 0 || chargesBailleur.charges.length > 0) {
            chargesHtml += '<div class="table-responsive"><table class="table table-sm">';
            chargesHtml += '<thead><tr><th>Type</th><th>Titre</th><th>Montant</th><th>Statut</th></tr></thead><tbody>';
            
            // Charges déductibles
            chargesDeductibles.charges.forEach(charge => {
                chargesHtml += `
                    <tr>
                        <td><span class="badge bg-info">Locataire</span></td>
                        <td>${charge.titre}</td>
                        <td>${this.formatCurrency(charge.montant)}</td>
                        <td><span class="badge ${this.getStatutBadgeClass(charge.statut)}">${charge.statut}</span></td>
                    </tr>
                `;
            });
            
            // Charges bailleur
            chargesBailleur.charges.forEach(charge => {
                chargesHtml += `
                    <tr>
                        <td><span class="badge bg-warning">Bailleur</span></td>
                        <td>${charge.titre}</td>
                        <td>${this.formatCurrency(charge.montant_restant)}</td>
                        <td><span class="badge ${this.getStatutBadgeClass(charge.statut)}">${charge.statut}</span></td>
                    </tr>
                `;
            });
            
            chargesHtml += '</tbody></table></div>';
        }
        
        chargesHtml += '</div></div>';
        container.innerHTML = chargesHtml;
    }
    
    displayRetraitsRecents(retraits) {
        const container = document.getElementById('retraits-info');
        if (!container) return;
        
        let retraitsHtml = `
            <div class="card border-secondary">
                <div class="card-header bg-secondary text-white">
                    <h6 class="mb-0">
                        <i class="bi bi-arrow-up-circle me-2"></i>
                        Retraits Récents (5 derniers)
                    </h6>
                </div>
                <div class="card-body">
                    <div class="row mb-3">
                        <div class="col-md-4">
                            <div class="text-center">
                                <h4 class="text-secondary">${retraits.nombre_retraits}</h4>
                                <small>Retraits</small>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="text-center">
                                <h4 class="text-secondary">${this.formatCurrency(retraits.total_retraits)}</h4>
                                <small>Total versé</small>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="text-center">
                                <h4 class="text-secondary">${this.formatCurrency(retraits.total_retraits / Math.max(retraits.nombre_retraits, 1))}</h4>
                                <small>Moyenne</small>
                            </div>
                        </div>
                    </div>
        `;
        
        if (retraits.retraits.length > 0) {
            retraitsHtml += '<div class="table-responsive"><table class="table table-sm">';
            retraitsHtml += '<thead><tr><th>Mois</th><th>Type</th><th>Montant net</th><th>Statut</th></tr></thead><tbody>';
            
            retraits.retraits.forEach(retrait => {
                retraitsHtml += `
                    <tr>
                        <td><strong>${this.formatDate(retrait.mois_retrait)}</strong></td>
                        <td><span class="badge bg-secondary">${retrait.type_retrait}</span></td>
                        <td>${this.formatCurrency(retrait.montant_net_a_payer)}</td>
                        <td><span class="badge ${this.getStatutRetraitBadgeClass(retrait.statut)}">${retrait.statut}</span></td>
                    </tr>
                `;
            });
            
            retraitsHtml += '</tbody></table></div>';
        }
        
        retraitsHtml += '</div></div>';
        container.innerHTML = retraitsHtml;
    }
    
    displayCalculs(calculs) {
        const container = document.getElementById('calculs-info');
        if (!container) return;
        
        let calculsHtml = `
            <div class="card border-primary">
                <div class="card-header bg-primary text-white">
                    <h6 class="mb-0">
                        <i class="bi bi-calculator me-2"></i>
                        Calculs Automatiques - ${calculs.mois_courant}
                    </h6>
                </div>
                <div class="card-body">
                    <div class="row mb-3">
                        <div class="col-md-3">
                            <div class="text-center">
                                <h4 class="text-primary">${this.formatCurrency(calculs.loyers_ce_mois)}</h4>
                                <small>Loyers perçus</small>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="text-center">
                                <h4 class="text-danger">${this.formatCurrency(calculs.total_charges)}</h4>
                                <small>Total charges</small>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="text-center">
                                <h4 class="text-success">${this.formatCurrency(calculs.montant_net_a_payer)}</h4>
                                <small>Montant net</small>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="text-center">
                                <h4 class="text-${calculs.peut_creer_retrait ? 'success' : 'warning'}">
                                    ${calculs.peut_creer_retrait ? 'OUI' : 'NON'}
                                </h4>
                                <small>Peut créer retrait</small>
                            </div>
                        </div>
                    </div>
                    
                    <div class="alert alert-${calculs.peut_creer_retrait ? 'success' : 'warning'}">
                        <i class="bi bi-info-circle me-2"></i>
                        ${calculs.peut_creer_retrait ? 
                            `Un retrait de ${this.formatCurrency(calculs.montant_net_a_payer)} peut être créé pour ${calculs.mois_courant}` :
                            `Aucun retrait ne peut être créé pour ${calculs.mois_courant} (montant net: ${this.formatCurrency(calculs.montant_net_a_payer)})`
                        }
                    </div>
                </div>
            </div>
        `;
        
        container.innerHTML = calculsHtml;
    }
    
    displayAlertes(alertes) {
        const container = document.getElementById('alertes-info');
        if (!container) return;
        
        if (alertes.length === 0) {
            container.innerHTML = `
                <div class="card border-success">
                    <div class="card-header bg-success text-white">
                        <h6 class="mb-0">
                            <i class="bi bi-check-circle me-2"></i>
                            Aucune alerte
                        </h6>
                    </div>
                    <div class="card-body">
                        <p class="text-success mb-0">
                            <i class="bi bi-emoji-smile me-2"></i>
                            Tout va bien ! Aucune alerte pour ce bailleur.
                        </p>
                    </div>
                </div>
            `;
            return;
        }
        
        let alertesHtml = `
            <div class="card border-warning">
                <div class="card-header bg-warning text-dark">
                    <h6 class="mb-0">
                        <i class="bi bi-exclamation-triangle me-2"></i>
                        Alertes (${alertes.length})
                    </h6>
                </div>
                <div class="card-body">
        `;
        
        alertes.forEach(alerte => {
            const badgeClass = alerte.severite === 'haute' ? 'bg-danger' : 'bg-warning';
            alertesHtml += `
                <div class="alert alert-${alerte.severite === 'haute' ? 'danger' : 'warning'} alert-dismissible fade show">
                    <span class="badge ${badgeClass} me-2">${alerte.severite.toUpperCase()}</span>
                    ${alerte.message}
                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                </div>
            `;
        });
        
        alertesHtml += '</div></div>';
        container.innerHTML = alertesHtml;
    }
    
    displaySuggestions(suggestions) {
        const container = document.getElementById('suggestions-info');
        if (!container) return;
        
        if (suggestions.length === 0) {
            container.innerHTML = `
                <div class="card border-secondary">
                    <div class="card-header bg-secondary text-white">
                        <h6 class="mb-0">
                            <i class="bi bi-lightbulb me-2"></i>
                            Aucune suggestion
                        </h6>
                    </div>
                    <div class="card-body">
                        <p class="text-muted mb-0">
                            Aucune suggestion de retrait disponible pour le moment.
                        </p>
                    </div>
                </div>
            `;
            return;
        }
        
        let suggestionsHtml = `
            <div class="card border-info">
                <div class="card-header bg-info text-white">
                    <h6 class="mb-0">
                        <i class="bi bi-lightbulb me-2"></i>
                        Suggestions Intelligentes (${suggestions.length})
                    </h6>
                </div>
                <div class="card-body">
        `;
        
        suggestions.forEach((suggestion, index) => {
            const badgeClass = suggestion.priorite === 'haute' ? 'bg-danger' : 'bg-info';
            suggestionsHtml += `
                <div class="suggestion-item card mb-2" 
                     data-type="${suggestion.type}" 
                     data-montant-loyers="${suggestion.montant_loyers || suggestion.montant}"
                     data-montant-charges="${suggestion.montant_charges || 0}"
                     data-montant-net="${suggestion.montant_net || suggestion.montant}"
                     style="cursor: pointer;">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-center">
                            <div>
                                <h6 class="mb-1">
                                    <span class="badge ${badgeClass} me-2">${suggestion.priorite.toUpperCase()}</span>
                                    ${suggestion.libelle}
                                </h6>
                                <small class="text-muted">
                                    ${suggestion.type === 'retrait_mensuel' ? 
                                        `Loyers: ${this.formatCurrency(suggestion.montant_loyers)} | Charges: ${this.formatCurrency(suggestion.montant_charges)} | Net: ${this.formatCurrency(suggestion.montant_net)}` :
                                        `Montant: ${this.formatCurrency(suggestion.montant)}`
                                    }
                                </small>
                            </div>
                            <button class="btn btn-sm btn-outline-primary" onclick="contexteIntelligentRetraits.applySuggestion(this.parentElement.parentElement.dataset)">
                                <i class="bi bi-check-lg me-1"></i>
                                Appliquer
                            </button>
                        </div>
                    </div>
                </div>
            `;
        });
        
        suggestionsHtml += '</div></div>';
        container.innerHTML = suggestionsHtml;
    }
    
    applySuggestion(data) {
        if (!data) return;
        
        // Appliquer les montants suggérés
        if (data.montantLoyers) {
            const loyersInput = document.getElementById('montant-loyers-bruts');
            if (loyersInput) loyersInput.value = data.montantLoyers;
        }
        
        if (data.montantCharges) {
            const chargesInput = document.getElementById('montant-charges-deductibles');
            if (chargesInput) chargesInput.value = data.montantCharges;
        }
        
        if (data.montantNet) {
            const netInput = document.getElementById('montant-net-a-payer');
            if (netInput) netInput.value = data.montantNet;
        }
        
        // Recalculer le montant net
        this.calculateMontantNet();
        
        // Afficher un message de confirmation
        this.showSuccess('Suggestion appliquée avec succès !');
        
        // Mettre à jour les champs suggérés
        this.updateSuggestedFields(data);
    }
    
    updateSuggestedFields(data) {
        if (data.montantLoyers) {
            const loyersSuggere = document.getElementById('montant-loyers-suggere');
            if (loyersSuggere) loyersSuggere.value = data.montantLoyers;
        }
        
        if (data.montantCharges) {
            const chargesSuggere = document.getElementById('montant-charges-suggere');
            if (chargesSuggere) chargesSuggere.value = data.montantCharges;
        }
        
        if (data.montantNet) {
            const netSuggere = document.getElementById('montant-net-suggere');
            if (netSuggere) netSuggere.value = data.montantNet;
        }
    }
    
    updateFormWithContexte(contexte) {
        // Mettre à jour les champs suggérés
        const calculs = contexte.calculs_automatiques;
        
        const loyersSuggere = document.getElementById('montant-loyers-suggere');
        const chargesSuggere = document.getElementById('montant-charges-suggere');
        const netSuggere = document.getElementById('montant-net-suggere');
        
        if (loyersSuggere) loyersSuggere.value = calculs.loyers_ce_mois;
        if (chargesSuggere) chargesSuggere.value = calculs.total_charges;
        if (netSuggere) netSuggere.value = calculs.montant_net_a_payer;
        
        // Mettre à jour le champ caché du contexte
        const contexteField = document.getElementById('contexte-bailleur');
        if (contexteField) {
            contexteField.value = JSON.stringify(contexte);
        }
    }
    
    calculateMontantNet() {
        const loyersInput = document.getElementById('montant-loyers-bruts');
        const chargesInput = document.getElementById('montant-charges-deductibles');
        const netInput = document.getElementById('montant-net-a-payer');
        
        if (!loyersInput || !chargesInput || !netInput) return;
        
        const loyers = parseFloat(loyersInput.value) || 0;
        const charges = parseFloat(chargesInput.value) || 0;
        const net = loyers - charges;
        
        netInput.value = net.toFixed(2);
        
        // Mettre à jour les champs suggérés
        const netSuggere = document.getElementById('montant-net-suggere');
        if (netSuggere) netSuggere.value = net.toFixed(2);
    }
    
    clearContexte() {
        this.currentBailleurId = null;
        this.currentContexte = null;
        
        // Vider tous les conteneurs
        const containers = [
            'bailleur-info', 'proprietes-info', 'contrats-info', 
            'paiements-info', 'charges-info', 'retraits-info', 
            'calculs-info', 'alertes-info', 'suggestions-info'
        ];
        
        containers.forEach(id => {
            const container = document.getElementById(id);
            if (container) {
                container.innerHTML = `
                    <div class="card border-secondary">
                        <div class="card-header bg-secondary text-white">
                            <h6 class="mb-0">
                                <i class="bi bi-info-circle me-2"></i>
                                Informations
                            </h6>
                        </div>
                        <div class="card-body">
                            <p class="text-muted mb-0">
                                Sélectionnez un bailleur pour voir les informations contextuelles.
                            </p>
                        </div>
                    </div>
                `;
            }
        });
        
        // Vider les champs suggérés
        const suggestedFields = [
            'montant-loyers-suggere', 'montant-charges-suggere', 'montant-net-suggere'
        ];
        
        suggestedFields.forEach(id => {
            const field = document.getElementById(id);
            if (field) field.value = '';
        });
        
        // Vider le champ caché du contexte
        const contexteField = document.getElementById('contexte-bailleur');
        if (contexteField) contexteField.value = '';
    }
    
    showLoading() {
        this.isLoading = true;
        
        // Afficher un indicateur de chargement
        const containers = [
            'bailleur-info', 'proprietes-info', 'contrats-info', 
            'paiements-info', 'charges-info', 'retraits-info', 
            'calculs-info', 'alertes-info', 'suggestions-info'
        ];
        
        containers.forEach(id => {
            const container = document.getElementById(id);
            if (container) {
                container.innerHTML = `
                    <div class="card border-secondary">
                        <div class="card-body text-center">
                            <div class="spinner-border text-primary" role="status">
                                <span class="visually-hidden">Chargement...</span>
                            </div>
                            <p class="mt-2 text-muted">Chargement du contexte...</p>
                        </div>
                    </div>
                `;
            }
        });
    }
    
    hideLoading() {
        this.isLoading = false;
    }
    
    showSuccess(message) {
        // Créer une notification de succès
        const notification = document.createElement('div');
        notification.className = 'alert alert-success alert-dismissible fade show position-fixed';
        notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        notification.innerHTML = `
            <i class="bi bi-check-circle me-2"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(notification);
        
        // Supprimer automatiquement après 3 secondes
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 3000);
    }
    
    showError(message) {
        // Créer une notification d'erreur
        const notification = document.createElement('div');
        notification.className = 'alert alert-danger alert-dismissible fade show position-fixed';
        notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        notification.innerHTML = `
            <i class="bi bi-exclamation-triangle me-2"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(notification);
        
        // Supprimer automatiquement après 5 secondes
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 5000);
    }
    
    // Méthodes utilitaires
    formatCurrency(amount) {
        if (amount === null || amount === undefined) return '0 F CFA';
        return new Intl.NumberFormat('fr-FR', {
            style: 'currency',
            currency: 'F CFA',
            minimumFractionDigits: 0
        }).format(amount);
    }
    
    formatDate(dateString) {
        if (!dateString) return 'Non renseigné';
        const date = new Date(dateString);
        return date.toLocaleDateString('fr-FR', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
    }
    
    formatMonth(monthString) {
        if (!monthString) return 'Non renseigné';
        const [year, month] = monthString.split('-');
        const date = new Date(parseInt(year), parseInt(month) - 1);
        return date.toLocaleDateString('fr-FR', {
            year: 'numeric',
            month: 'long'
        });
    }
    
    getStatutBadgeClass(statut) {
        const classes = {
            'en_attente': 'bg-warning',
            'validee': 'bg-success',
            'deduite_retrait': 'bg-info',
            'annulee': 'bg-danger'
        };
        return classes[statut] || 'bg-secondary';
    }
    
    getStatutRetraitBadgeClass(statut) {
        const classes = {
            'en_attente': 'bg-warning',
            'valide': 'bg-success',
            'paye': 'bg-info',
            'annule': 'bg-danger'
        };
        return classes[statut] || 'bg-secondary';
    }
}

// Initialisation automatique quand le DOM est prêt
document.addEventListener('DOMContentLoaded', function() {
    // Vérifier si nous sommes sur une page de retrait intelligent
    if (document.getElementById('bailleur-select')) {
        window.contexteIntelligentRetraits = new ContexteIntelligentRetraits();
    }
});

// Export pour utilisation dans d'autres modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ContexteIntelligentRetraits;
}

