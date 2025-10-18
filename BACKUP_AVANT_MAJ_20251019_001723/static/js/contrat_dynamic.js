/**
 * JavaScript pour les fonctionnalités dynamiques des contrats
 * Récupération automatique du loyer et autres données
 */

class ContratDynamic {
    constructor() {
        this.init();
    }

    init() {
        this.bindEvents();
        this.initializeForm();
    }

    bindEvents() {
        // Événement sur le changement de propriété
        const proprieteSelect = document.getElementById('propriete');
        if (proprieteSelect) {
            proprieteSelect.addEventListener('change', (e) => {
                this.handleProprieteChange(e.target.value);
            });
        }

        // Événement sur le changement de locataire
        const locataireSelect = document.getElementById('locataire');
        if (locataireSelect) {
            locataireSelect.addEventListener('change', (e) => {
                this.handleLocataireChange(e.target.value);
            });
        }

        // Événements sur les dates pour calculer la durée
        const dateDebutInput = document.getElementById('date_debut');
        const dateFinInput = document.getElementById('date_fin');
        
        if (dateDebutInput) {
            dateDebutInput.addEventListener('change', () => {
                this.calculateDuration();
            });
        }
        
        if (dateFinInput) {
            dateFinInput.addEventListener('change', () => {
                this.calculateDuration();
            });
        }
    }

    initializeForm() {
        // Initialiser le formulaire avec les données existantes
        const proprieteSelect = document.getElementById('propriete');
        if (proprieteSelect && proprieteSelect.value) {
            this.handleProprieteChange(proprieteSelect.value);
        }
    }

    async handleProprieteChange(proprieteId) {
        if (!proprieteId) {
            this.clearProprieteData();
            return;
        }

        try {
            this.showLoading('propriete');
            
            const response = await fetch(`/contrats/ajax/propriete/${proprieteId}/`);
            const data = await response.json();

            if (data.success) {
                this.updateProprieteData(data.propriete);
                this.showSuccess('Propriété chargée avec succès');
            } else {
                this.showError('Erreur lors du chargement de la propriété: ' + data.error);
            }
        } catch (error) {
            console.error('Erreur AJAX:', error);
            this.showError('Erreur de connexion lors du chargement de la propriété');
        } finally {
            this.hideLoading('propriete');
        }
    }

    async handleLocataireChange(locataireId) {
        if (!locataireId) {
            this.clearLocataireData();
            return;
        }

        try {
            this.showLoading('locataire');
            
            const response = await fetch(`/contrats/ajax/locataire/${locataireId}/`);
            const data = await response.json();

            if (data.success) {
                this.updateLocataireData(data.locataire);
                this.showSuccess('Locataire chargé avec succès');
            } else {
                this.showError('Erreur lors du chargement du locataire: ' + data.error);
            }
        } catch (error) {
            console.error('Erreur AJAX:', error);
            this.showError('Erreur de connexion lors du chargement du locataire');
        } finally {
            this.hideLoading('locataire');
        }
    }

    updateProprieteData(propriete) {
        // Mettre à jour le loyer mensuel
        const loyerInput = document.getElementById('loyer_mensuel');
        if (loyerInput && propriete.loyer_actuel) {
            loyerInput.value = propriete.loyer_actuel;
            loyerInput.classList.add('is-valid');
        }

        // Mettre à jour les informations de la propriété
        this.updateProprieteInfo(propriete);

        // Mettre à jour les unités disponibles
        this.updateUnitesDisponibles(propriete.unites);

        // Vérifier la disponibilité
        if (!propriete.disponible) {
            this.showWarning('Cette propriété n\'est pas disponible');
        }

        if (propriete.contrats_actifs > 0) {
            this.showWarning(`Cette propriété a ${propriete.contrats_actifs} contrat(s) actif(s)`);
        }
    }

    updateProprieteInfo(propriete) {
        // Créer ou mettre à jour la section d'informations de la propriété
        let infoSection = document.getElementById('propriete-info');
        if (!infoSection) {
            infoSection = document.createElement('div');
            infoSection.id = 'propriete-info';
            infoSection.className = 'alert alert-info mt-3';
            
            const proprieteSelect = document.getElementById('propriete');
            proprieteSelect.parentNode.appendChild(infoSection);
        }

        infoSection.innerHTML = `
            <div class="row">
                <div class="col-md-6">
                    <h6><i class="bi bi-house"></i> ${propriete.titre}</h6>
                    <p class="mb-1"><strong>Adresse:</strong> ${propriete.adresse}</p>
                    <p class="mb-1"><strong>Ville:</strong> ${propriete.ville}</p>
                    <p class="mb-1"><strong>Type:</strong> ${propriete.type_propriete}</p>
                </div>
                <div class="col-md-6">
                    <p class="mb-1"><strong>Loyer actuel:</strong> <span class="text-primary fw-bold">${propriete.loyer_actuel.toLocaleString()} F CFA</span></p>
                    <p class="mb-1"><strong>Disponibilité:</strong> 
                        <span class="badge ${propriete.disponible ? 'bg-success' : 'bg-danger'}">
                            ${propriete.disponible ? 'Disponible' : 'Non disponible'}
                        </span>
                    </p>
                    <p class="mb-0"><strong>Contrats actifs:</strong> ${propriete.contrats_actifs}</p>
                </div>
            </div>
        `;
    }

    updateUnitesDisponibles(unites) {
        // Mettre à jour la liste des unités disponibles
        let unitesSection = document.getElementById('unites-disponibles');
        if (!unitesSection) {
            unitesSection = document.createElement('div');
            unitesSection.id = 'unites-disponibles';
            unitesSection.className = 'mt-3';
            
            const proprieteInfo = document.getElementById('propriete-info');
            if (proprieteInfo) {
                proprieteInfo.appendChild(unitesSection);
            }
        }

        if (unites && unites.length > 0) {
            unitesSection.innerHTML = `
                <h6><i class="bi bi-building"></i> Unités disponibles:</h6>
                <div class="row">
                    ${unites.map(unite => `
                        <div class="col-md-6 mb-2">
                            <div class="card card-body py-2">
                                <div class="d-flex justify-content-between">
                                    <span>${unite.nom}</span>
                                    <span class="text-primary fw-bold">${unite.loyer_mensuel.toLocaleString()} F CFA</span>
                                </div>
                            </div>
                        </div>
                    `).join('')}
                </div>
            `;
        } else {
            unitesSection.innerHTML = '<p class="text-muted">Aucune unité disponible</p>';
        }
    }

    updateLocataireData(locataire) {
        // Mettre à jour les informations du locataire
        let infoSection = document.getElementById('locataire-info');
        if (!infoSection) {
            infoSection = document.createElement('div');
            infoSection.id = 'locataire-info';
            infoSection.className = 'alert alert-info mt-3';
            
            const locataireSelect = document.getElementById('locataire');
            locataireSelect.parentNode.appendChild(infoSection);
        }

        infoSection.innerHTML = `
            <div class="row">
                <div class="col-md-6">
                    <h6><i class="bi bi-person"></i> ${locataire.prenom} ${locataire.nom}</h6>
                    <p class="mb-1"><strong>Email:</strong> ${locataire.email || 'Non renseigné'}</p>
                    <p class="mb-1"><strong>Téléphone:</strong> ${locataire.telephone || 'Non renseigné'}</p>
                </div>
                <div class="col-md-6">
                    <p class="mb-1"><strong>Contrats actifs:</strong> ${locataire.contrats_actifs.length}</p>
                    ${locataire.contrats_actifs.length > 0 ? `
                        <div class="mt-2">
                            <small class="text-muted">Contrats en cours:</small>
                            ${locataire.contrats_actifs.map(contrat => `
                                <div class="small">${contrat.numero_contrat} - ${contrat.propriete}</div>
                            `).join('')}
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
    }

    async calculateDuration() {
        const dateDebut = document.getElementById('date_debut')?.value;
        const dateFin = document.getElementById('date_fin')?.value;

        if (!dateDebut) return;

        try {
            const response = await fetch('/contrats/ajax/calculate-duration/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    date_debut: dateDebut,
                    date_fin: dateFin
                })
            });

            const data = await response.json();

            if (data.success) {
                this.updateDurationInfo(data.calculations);
            }
        } catch (error) {
            console.error('Erreur lors du calcul de la durée:', error);
        }
    }

    updateDurationInfo(calculations) {
        let durationSection = document.getElementById('duration-info');
        if (!durationSection) {
            durationSection = document.createElement('div');
            durationSection.id = 'duration-info';
            durationSection.className = 'alert alert-secondary mt-3';
            
            const dateFinInput = document.getElementById('date_fin');
            if (dateFinInput) {
                dateFinInput.parentNode.appendChild(durationSection);
            }
        }

        durationSection.innerHTML = `
            <h6><i class="bi bi-calendar"></i> Informations de durée</h6>
            <div class="row">
                <div class="col-md-4">
                    <strong>Durée:</strong> ${calculations.duree_annees} an(s), ${calculations.duree_mois} mois
                </div>
                <div class="col-md-4">
                    <strong>Jours:</strong> ${calculations.duree_jours} jours
                </div>
                <div class="col-md-4">
                    <strong>Date de fin:</strong> ${new Date(calculations.date_fin_auto).toLocaleDateString('fr-FR')}
                </div>
            </div>
            <div class="row mt-2">
                <div class="col-md-6">
                    <small class="text-muted">Préavis: ${new Date(calculations.date_preavis).toLocaleDateString('fr-FR')}</small>
                </div>
                <div class="col-md-6">
                    <small class="text-muted">Renouvellement: ${new Date(calculations.date_renouvellement).toLocaleDateString('fr-FR')}</small>
                </div>
            </div>
        `;

        // Mettre à jour automatiquement la date de fin si elle n'est pas définie
        const dateFinInput = document.getElementById('date_fin');
        if (dateFinInput && !dateFinInput.value) {
            dateFinInput.value = calculations.date_fin_auto;
        }
    }

    clearProprieteData() {
        const loyerInput = document.getElementById('loyer_mensuel');
        if (loyerInput) {
            loyerInput.value = '';
            loyerInput.classList.remove('is-valid');
        }

        const infoSection = document.getElementById('propriete-info');
        if (infoSection) {
            infoSection.remove();
        }

        const unitesSection = document.getElementById('unites-disponibles');
        if (unitesSection) {
            unitesSection.remove();
        }
    }

    clearLocataireData() {
        const infoSection = document.getElementById('locataire-info');
        if (infoSection) {
            infoSection.remove();
        }
    }

    showLoading(element) {
        const selectElement = document.getElementById(element);
        if (selectElement) {
            selectElement.disabled = true;
            selectElement.classList.add('loading');
        }
    }

    hideLoading(element) {
        const selectElement = document.getElementById(element);
        if (selectElement) {
            selectElement.disabled = false;
            selectElement.classList.remove('loading');
        }
    }

    showSuccess(message) {
        this.showAlert(message, 'success');
    }

    showError(message) {
        this.showAlert(message, 'danger');
    }

    showWarning(message) {
        this.showAlert(message, 'warning');
    }

    showAlert(message, type) {
        // Supprimer les alertes existantes
        const existingAlerts = document.querySelectorAll('.alert-dynamic');
        existingAlerts.forEach(alert => alert.remove());

        const alert = document.createElement('div');
        alert.className = `alert alert-${type} alert-dismissible fade show alert-dynamic`;
        alert.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        // Insérer l'alerte en haut du formulaire
        const form = document.querySelector('form');
        if (form) {
            form.insertBefore(alert, form.firstChild);
        }

        // Auto-supprimer après 5 secondes
        setTimeout(() => {
            if (alert.parentNode) {
                alert.remove();
            }
        }, 5000);
    }

    getCSRFToken() {
        const token = document.querySelector('[name=csrfmiddlewaretoken]');
        return token ? token.value : '';
    }
}

// Initialiser quand le DOM est chargé
document.addEventListener('DOMContentLoaded', () => {
    new ContratDynamic();
});
