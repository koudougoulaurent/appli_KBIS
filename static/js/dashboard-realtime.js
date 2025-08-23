// dashboard-realtime.js
// Script pour mettre à jour les dashboards en temps réel

// Fonction pour mettre à jour le dashboard principal
function updateMainDashboard() {
    fetch('/core/api/dashboard/')
        .then(response => response.json())
        .then(data => {
            // Mettre à jour les statistiques
            document.getElementById('total-paiements').textContent = data.stats.utilisateurs.total;
            document.getElementById('paiements-valides').textContent = data.stats.utilisateurs.actifs;
            document.getElementById('total-recus').textContent = data.stats.recus.total;
            document.getElementById('recus-valides').textContent = data.stats.recus.valides;
            document.getElementById('recus-imprimes').textContent = data.stats.recus.imprimes;
            document.getElementById('montant-total-recus').textContent = data.stats.recus.montant_total + ' XOF';
            document.getElementById('total-proprietes').textContent = data.stats.proprietes.total;
            document.getElementById('proprietes-louees').textContent = data.stats.proprietes.disponibles;
            document.getElementById('total-contrats').textContent = data.stats.contrats.total;
            document.getElementById('contrats-actifs').textContent = data.stats.contrats.actifs;
            
            // Mettre à jour les tendances
            document.getElementById('paiements-mois').textContent = data.tendances.paiements_mois;
            document.getElementById('recus-mois').textContent = data.tendances.recus_mois;
        })
        .catch(error => {
            console.error('Erreur lors de la mise à jour du dashboard principal:', error);
        });
}

// Fonction pour mettre à jour le dashboard de groupe
function updateGroupDashboard(groupeNom) {
    fetch(`/core/api/groupe-dashboard/${groupeNom}/`)
        .then(response => response.json())
        .then(data => {
            // Mettre à jour les statistiques selon le groupe
            if (groupeNom === 'CAISSE') {
                document.getElementById('paiements-mois').textContent = data.stats.paiements_mois;
                document.getElementById('retraits-mois').textContent = data.stats.retraits_mois;
                document.getElementById('cautions-cours').textContent = data.stats.cautions_cours;
                document.getElementById('paiements-attente').textContent = data.stats.paiements_attente;
            } else if (groupeNom === 'ADMINISTRATION') {
                document.getElementById('total-proprietes').textContent = data.stats.total_proprietes;
                document.getElementById('contrats-actifs').textContent = data.stats.contrats_actifs;
                document.getElementById('total-bailleurs').textContent = data.stats.total_bailleurs;
                document.getElementById('contrats-renouveler').textContent = data.stats.contrats_renouveler;
            } else if (groupeNom === 'CONTROLES') {
                document.getElementById('paiements-a-valider').textContent = data.stats.paiements_a_valider;
                document.getElementById('contrats-a-verifier').textContent = data.stats.contrats_a_verifier;
            } else if (groupeNom === 'PRIVILEGE') {
                document.getElementById('total-proprietes').textContent = data.stats.total_proprietes;
                document.getElementById('total-utilisateurs').textContent = data.stats.total_utilisateurs;
                document.getElementById('total-contrats').textContent = data.stats.total_contrats;
                document.getElementById('total-paiements').textContent = data.stats.total_paiements;
                document.getElementById('total-groupes').textContent = data.stats.total_groupes;
                document.getElementById('total-notifications').textContent = data.stats.total_notifications;
                document.getElementById('utilisateurs-actifs').textContent = data.stats.utilisateurs_actifs;
                document.getElementById('total-bailleurs').textContent = data.stats.total_bailleurs;
                document.getElementById('total-locataires').textContent = data.stats.total_locataires;
                document.getElementById('contrats-actifs').textContent = data.stats.contrats_actifs;
            }
        })
        .catch(error => {
            console.error('Erreur lors de la mise à jour du dashboard de groupe:', error);
        });
}

// Initialiser la mise à jour périodique
document.addEventListener('DOMContentLoaded', function() {
    // Vérifier si nous sommes sur le dashboard principal
    if (document.getElementById('main-dashboard')) {
        // Mettre à jour immédiatement
        updateMainDashboard();
        // Mettre à jour toutes les 30 secondes
        setInterval(updateMainDashboard, 30000);
    }
    
    // Vérifier si nous sommes sur un dashboard de groupe
    const groupDashboard = document.getElementById('group-dashboard');
    if (groupDashboard) {
        const groupeNom = groupDashboard.dataset.groupeNom;
        // Mettre à jour immédiatement
        updateGroupDashboard(groupeNom);
        // Mettre à jour toutes les 30 secondes
        setInterval(() => updateGroupDashboard(groupeNom), 30000);
    }
});