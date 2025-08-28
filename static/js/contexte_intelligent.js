/**
 * 🚀 SYSTÈME INTELLIGENT DE CONTEXTE AUTOMATIQUE
 * 
 * Ce script gère automatiquement l'affichage de toutes les informations contextuelles
 * dès qu'un contrat est sélectionné dans les formulaires de paiement.
 */

class ContexteIntelligent {
    constructor() {
        this.init();
    }
    
    init() {
        this.bindEvents();
        this.initializeSelect2();
        this.setupAutoComplete();
    }
    
    bindEvents() {
        // Écouteur pour la sélection de contrat
        $(document).on('change', '#contrat-select, #contrat-charge-select', (e) => {
            const contratId = $(e.target).val();
            if (contratId) {
                this.chargerContexteComplet(contratId);
            } else {
                this.effacerContexte();
            }
        });
        
        // Écouteur pour la recherche en temps réel
        $(document).on('input', '#terme-recherche', (e) => {
            const terme = $(e.target).val();
            if (terme.length >= 2) {
                this.rechercheEnTempsReel(terme);
            }
        });
        
        // Écouteur pour les suggestions de paiement
        $(document).on('click', '.btn-suggestion-paiement', (e) => {
            e.preventDefault();
            const suggestion = $(e.target).data('suggestion');
            this.appliquerSuggestion(suggestion);
        });
    }
    
    initializeSelect2() {
        // Initialisation de Select2 pour une meilleure UX
        $('[data-toggle="select2"]').select2({
            theme: 'bootstrap-5',
            width: '100%',
            placeholder: 'Recherchez un contrat...',
            allowClear: true,
            language: 'fr'
        });
    }
    
    setupAutoComplete() {
        // Configuration de l'autocomplétion pour la recherche
        $('#terme-recherche').autocomplete({
            source: (request, response) => {
                this.rechercheAutocomplete(request.term, response);
            },
            minLength: 2,
            delay: 300,
            autoFocus: true
        });
    }
    
    async chargerContexteComplet(contratId) {
        try {
            this.afficherChargement();
            
            const response = await fetch(`/paiements/api/contexte-intelligent/contrat/${contratId}/`);
            const data = await response.json();
            
            if (data.success) {
                this.afficherContexteComplet(data.data);
                this.chargerSuggestions(contratId);
            } else {
                this.afficherErreur(data.error);
            }
        } catch (error) {
            console.error('Erreur lors du chargement du contexte:', error);
            this.afficherErreur('Erreur de connexion au serveur');
        } finally {
            this.masquerChargement();
        }
    }
    
    afficherContexteComplet(contexte) {
        // Affichage des informations du contrat
        this.afficherInformationsContrat(contexte.contrat);
        
        // Affichage des informations de la propriété
        this.afficherInformationsPropriete(contexte.propriete);
        
        // Affichage des informations du locataire
        this.afficherInformationsLocataire(contexte.locataire);
        
        // Affichage des informations du bailleur
        this.afficherInformationsBailleur(contexte.bailleur);
        
        // Affichage de l'historique des paiements
        this.afficherHistoriquePaiements(contexte.historique_paiements);
        
        // Affichage des charges déductibles
        this.afficherChargesDeductibles(contexte.charges_deductibles);
        
        // Affichage des calculs automatiques
        this.afficherCalculsAutomatiques(contexte.calculs_automatiques);
        
        // Affichage des alertes
        this.afficherAlertes(contexte.alertes);
        
        // Mise à jour des champs suggérés
        this.mettreAJourChampsSuggeres(contexte);
        
        // Affichage du panneau de contexte
        $('#panneau-contexte').removeClass('d-none').addClass('show');
    }
    
    afficherInformationsContrat(contrat) {
        const html = `
            <div class="card border-primary">
                <div class="card-header bg-primary text-white">
                    <h6 class="mb-0"><i class="fas fa-file-contract"></i> Informations du contrat</h6>
                </div>
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-6">
                            <p><strong>Numéro:</strong> ${contrat.numero}</p>
                            <p><strong>Date début:</strong> ${this.formaterDate(contrat.date_debut)}</p>
                            <p><strong>Date fin:</strong> ${contrat.date_fin ? this.formaterDate(contrat.date_fin) : 'Non définie'}</p>
                        </div>
                        <div class="col-md-6">
                            <p><strong>Loyer mensuel:</strong> <span class="badge bg-success">${contrat.loyer_mensuel} FCfa</span></p>
                            <p><strong>Charges:</strong> <span class="badge bg-info">${contrat.charges_mensuelles} FCfa</span></p>
                            <p><strong>Jour paiement:</strong> ${contrat.jour_paiement}</p>
                        </div>
                    </div>
                </div>
            </div>
        `;
        $('#contexte-contrat').html(html);
    }
    
    afficherInformationsPropriete(propriete) {
        const html = `
            <div class="card border-info">
                <div class="card-header bg-info text-white">
                    <h6 class="mb-0"><i class="fas fa-home"></i> Propriété</h6>
                </div>
                <div class="card-body">
                    <h6 class="card-title">${propriete.titre}</h6>
                    <p><strong>Adresse:</strong> ${propriete.adresse}</p>
                    <p><strong>Ville:</strong> ${propriete.ville} ${propriete.code_postal}</p>
                    <p><strong>Type:</strong> ${propriete.type_propriete}</p>
                    <p><strong>Surface:</strong> ${propriete.surface} m² - ${propriete.nombre_pieces} pièces</p>
                </div>
            </div>
        `;
        $('#contexte-propriete').html(html);
    }
    
    afficherInformationsLocataire(locataire) {
        const html = `
            <div class="card border-warning">
                <div class="card-header bg-warning text-dark">
                    <h6 class="mb-0"><i class="fas fa-user"></i> Locataire</h6>
                </div>
                <div class="card-body">
                    <h6 class="card-title">${locataire.prenom} ${locataire.nom}</h6>
                    <p><strong>Téléphone:</strong> <a href="tel:${locataire.telephone}">${locataire.telephone}</a></p>
                    <p><strong>Email:</strong> <a href="mailto:${locataire.email}">${locataire.email}</a></p>
                    <p><strong>Profession:</strong> ${locataire.profession || 'Non renseignée'}</p>
                </div>
            </div>
        `;
        $('#contexte-locataire').html(html);
    }
    
    afficherInformationsBailleur(bailleur) {
        const html = `
            <div class="card border-secondary">
                <div class="card-header bg-secondary text-white">
                    <h6 class="mb-0"><i class="fas fa-user-tie"></i> Bailleur</h6>
                </div>
                <div class="card-body">
                    <h6 class="card-title">${bailleur.prenom} ${bailleur.nom}</h6>
                    <p><strong>Téléphone:</strong> <a href="tel:${bailleur.telephone}">${bailleur.telephone}</a></p>
                    <p><strong>Email:</strong> <a href="mailto:${bailleur.email}">${bailleur.email}</a></p>
                </div>
            </div>
        `;
        $('#contexte-bailleur').html(html);
    }
    
    afficherHistoriquePaiements(historique) {
        let html = `
            <div class="card border-success">
                <div class="card-header bg-success text-white">
                    <h6 class="mb-0"><i class="fas fa-history"></i> Historique des paiements (5 derniers mois)</h6>
                </div>
                <div class="card-body">
                    <div class="table-responsive">
                        <table class="table table-sm">
                            <thead>
                                <tr>
                                    <th>Mois</th>
                                    <th>Total</th>
                                    <th>Nombre</th>
                                    <th>Statut</th>
                                </tr>
                            </thead>
                            <tbody>
        `;
        
        historique.forEach(mois => {
            const statutClass = mois.statut_mois === 'Complet' ? 'success' : 'warning';
            html += `
                <tr>
                    <td>${mois.mois}</td>
                    <td><span class="badge bg-primary">${mois.total_paiements} FCfa</span></td>
                    <td>${mois.nombre_paiements}</td>
                    <td><span class="badge bg-${statutClass}">${mois.statut_mois}</span></td>
                </tr>
            `;
        });
        
        html += `
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        `;
        
        $('#contexte-historique').html(html);
    }
    
    afficherChargesDeductibles(charges) {
        const html = `
            <div class="card border-warning">
                <div class="card-header bg-warning text-dark">
                    <h6 class="mb-0"><i class="fas fa-tools"></i> Charges déductibles</h6>
                </div>
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-4">
                            <div class="text-center">
                                <h4 class="text-primary">${charges.total_charges} FCfa</h4>
                                <small class="text-muted">Total des charges</small>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="text-center">
                                <h4 class="text-warning">${charges.charges_en_attente} FCfa</h4>
                                <small class="text-muted">En attente</small>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="text-center">
                                <h4 class="text-success">${charges.charges_validees} FCfa</h4>
                                <small class="text-muted">Validées</small>
                            </div>
                        </div>
                    </div>
                    ${charges.nombre_charges > 0 ? `
                        <hr>
                        <h6>Charges récentes:</h6>
                        <ul class="list-unstyled">
                            ${charges.charges_recentes.map(charge => `
                                <li><i class="fas fa-circle text-${this.getStatutColor(charge.statut)}"></i> 
                                    ${charge.libelle} - ${charge.montant} FCfa (${charge.statut})
                                </li>
                            `).join('')}
                        </ul>
                    ` : ''}
                </div>
            </div>
        `;
        
        $('#contexte-charges').html(html);
    }
    
    afficherCalculsAutomatiques(calculs) {
        const soldeClass = calculs.solde_actuel >= 0 ? 'success' : 'danger';
        const html = `
            <div class="card border-${soldeClass}">
                <div class="card-header bg-${soldeClass} text-white">
                    <h6 class="mb-0"><i class="fas fa-calculator"></i> Calculs automatiques</h6>
                </div>
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-6">
                            <div class="text-center mb-3">
                                <h3 class="text-${soldeClass}">${calculs.solde_actuel} FCfa</h3>
                                <small class="text-muted">Solde actuel</small>
                            </div>
                            <div class="text-center">
                                <h5 class="text-primary">${calculs.loyer_net} FCfa</h5>
                                <small class="text-muted">Loyer net</small>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="text-center mb-3">
                                <h5 class="text-info">${calculs.prochaine_echeance}</h5>
                                <small class="text-muted">Prochaine échéance</small>
                            </div>
                            <div class="text-center">
                                <h5 class="text-warning">${calculs.jours_avant_echeance} jours</h5>
                                <small class="text-muted">Jours restants</small>
                            </div>
                        </div>
                    </div>
                    ${calculs.montant_du > 0 ? `
                        <div class="alert alert-danger mt-3">
                            <i class="fas fa-exclamation-triangle"></i>
                            <strong>Montant dû:</strong> ${calculs.montant_du} FCfa
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
        
        $('#contexte-calculs').html(html);
    }
    
    afficherAlertes(alertes) {
        if (alertes.length === 0) {
            $('#contexte-alertes').html(`
                <div class="alert alert-success">
                    <i class="fas fa-check-circle"></i> Aucune alerte pour ce contrat
                </div>
            `);
            return;
        }
        
        let html = `
            <div class="card border-danger">
                <div class="card-header bg-danger text-white">
                    <h6 class="mb-0"><i class="fas fa-exclamation-triangle"></i> Alertes (${alertes.length})</h6>
                </div>
                <div class="card-body">
        `;
        
        alertes.forEach(alerte => {
            html += `
                <div class="alert alert-${alerte.niveau} alert-dismissible fade show">
                    <i class="fas fa-${this.getAlerteIcon(alerte.type)}"></i>
                    ${alerte.message}
                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                </div>
            `;
        });
        
        html += `
                </div>
            </div>
        `;
        
        $('#contexte-alertes').html(html);
    }
    
    async chargerSuggestions(contratId) {
        try {
            const response = await fetch(`/paiements/api/suggestions-paiement/contrat/${contratId}/`);
            const data = await response.json();
            
            if (data.success) {
                this.afficherSuggestions(data.suggestions);
            }
        } catch (error) {
            console.error('Erreur lors du chargement des suggestions:', error);
        }
    }
    
    afficherSuggestions(suggestions) {
        let html = `
            <div class="card border-info">
                <div class="card-header bg-info text-white">
                    <h6 class="mb-0"><i class="fas fa-lightbulb"></i> Suggestions de paiement</h6>
                </div>
                <div class="card-body">
        `;
        
        suggestions.forEach(suggestion => {
            const prioriteClass = suggestion.priorite === 'haute' ? 'danger' : 'primary';
            html += `
                <div class="d-flex justify-content-between align-items-center mb-2">
                    <div>
                        <strong>${suggestion.libelle}</strong>
                        <br><small class="text-muted">${suggestion.montant} FCfa</small>
                    </div>
                    <button class="btn btn-${prioriteClass} btn-sm btn-suggestion-paiement" 
                            data-suggestion='${JSON.stringify(suggestion)}'>
                        <i class="fas fa-check"></i> Appliquer
                    </button>
                </div>
            `;
        });
        
        html += `
                </div>
            </div>
        `;
        
        $('#contexte-suggestions').html(html);
    }
    
    mettreAJourChampsSuggeres(contexte) {
        // Mise à jour du montant suggéré
        if ($('#montant-suggere').length) {
            $('#montant-suggere').val(contexte.contrat.loyer_mensuel);
        }
        
        // Mise à jour du libellé suggéré
        if ($('#libelle-suggere').length) {
            $('#libelle-suggere').val(`Paiement loyer - ${contexte.contrat.numero}`);
        }
        
        // Mise à jour du montant maximum suggéré pour les charges
        if ($('#montant-max-suggere').length) {
            $('#montant-max-suggere').val(contexte.calculs_automatiques.montant_du || contexte.contrat.loyer_mensuel);
        }
    }
    
    appliquerSuggestion(suggestion) {
        // Application automatique de la suggestion
        if ($('#montant-paiement').length) {
            $('#montant-paiement').val(suggestion.montant);
        }
        
        if ($('#libelle-paiement').length) {
            $('#libelle-paiement').val(suggestion.libelle);
        }
        
        // Notification de succès
        this.afficherNotification('Suggestion appliquée avec succès', 'success');
    }
    
    async rechercheEnTempsReel(terme) {
        try {
            const response = await fetch(`/paiements/api/recherche-contrats/?terme=${encodeURIComponent(terme)}`);
            const data = await response.json();
            
            if (data.success) {
                this.afficherResultatsRecherche(data.contrats);
            }
        } catch (error) {
            console.error('Erreur lors de la recherche:', error);
        }
    }
    
    afficherResultatsRecherche(contrats) {
        // Affichage des résultats de recherche en temps réel
        // Cette fonction peut être personnalisée selon vos besoins
    }
    
    async rechercheAutocomplete(terme, response) {
        try {
            const result = await fetch(`/paiements/api/recherche-contrats/?terme=${encodeURIComponent(terme)}`);
            const data = await result.json();
            
            if (data.success) {
                const suggestions = data.contrats.map(contrat => ({
                    label: `${contrat.numero_contrat} - ${contrat.locataire.nom} ${contrat.locataire.prenom}`,
                    value: contrat.numero_contrat,
                    contrat: contrat
                }));
                response(suggestions);
            }
        } catch (error) {
            console.error('Erreur lors de l\'autocomplétion:', error);
            response([]);
        }
    }
    
    effacerContexte() {
        // Effacement de tous les panneaux de contexte
        $('#panneau-contexte').addClass('d-none').removeClass('show');
        $('#contexte-contrat, #contexte-propriete, #contexte-locataire, #contexte-bailleur, #contexte-historique, #contexte-charges, #contexte-calculs, #contexte-alertes, #contexte-suggestions').empty();
        
        // Réinitialisation des champs suggérés
        $('#montant-suggere, #libelle-suggere, #montant-max-suggere').val('');
    }
    
    afficherChargement() {
        // Affichage d'un indicateur de chargement
        $('#panneau-contexte').html(`
            <div class="text-center p-4">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Chargement...</span>
                </div>
                <p class="mt-2">Chargement du contexte...</p>
            </div>
        `).removeClass('d-none').addClass('show');
    }
    
    masquerChargement() {
        // Masquage de l'indicateur de chargement
        // Le contenu sera affiché par afficherContexteComplet
    }
    
    afficherErreur(message) {
        $('#panneau-contexte').html(`
            <div class="alert alert-danger">
                <i class="fas fa-exclamation-triangle"></i> ${message}
            </div>
        `).removeClass('d-none').addClass('show');
    }
    
    afficherNotification(message, type = 'info') {
        // Affichage d'une notification toast ou alert
        const alertClass = `alert-${type}`;
        const html = `
            <div class="alert ${alertClass} alert-dismissible fade show" role="alert">
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        // Insertion de la notification
        $('body').prepend(html);
        
        // Auto-suppression après 5 secondes
        setTimeout(() => {
            $(`.alert-${type}`).fadeOut();
        }, 5000);
    }
    
    // Fonctions utilitaires
    formaterDate(dateString) {
        if (!dateString) return 'Non définie';
        const date = new Date(dateString);
        return date.toLocaleDateString('fr-FR');
    }
    
    getStatutColor(statut) {
        const colors = {
            'en_attente': 'warning',
            'validee': 'success',
            'deduite': 'info',
            'refusee': 'danger',
            'annulee': 'secondary'
        };
        return colors[statut] || 'secondary';
    }
    
    getAlerteIcon(type) {
        const icons = {
            'echeance': 'clock',
            'solde': 'exclamation-triangle',
            'charges': 'tools',
            'expiration': 'calendar-times'
        };
        return icons[type] || 'exclamation-triangle';
    }
}

// Initialisation du système intelligent
$(document).ready(() => {
    window.contexteIntelligent = new ContexteIntelligent();
});
