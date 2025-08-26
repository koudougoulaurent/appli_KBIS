#!/usr/bin/env python
"""
Script pour créer tous les templates manquants
"""

import os

def create_template_directory(path):
    """Crée un répertoire de templates s'il n'existe pas"""
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"✅ Répertoire créé: {path}")

def create_template_file(file_path, content):
    """Crée un fichier template s'il n'existe pas"""
    if not os.path.exists(file_path):
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Template créé: {file_path}")
    else:
        print(f"⚠️ Template existe déjà: {file_path}")

def main():
    """Fonction principale"""
    print("🔧 Création des templates manquants")
    print("=" * 50)
    
    # Créer les répertoires de templates
    template_dirs = [
        'templates/proprietes',
        'templates/contrats', 
        'templates/paiements',
        'templates/utilisateurs',
        'templates/notifications'
    ]
    
    for dir_path in template_dirs:
        create_template_directory(dir_path)
    
    # Templates pour les propriétés
    proprietes_templates = {
        'templates/proprietes/liste.html': '''{% extends 'base.html' %}

{% block title %}Liste des Propriétés{% endblock %}

{% block content %}
<div class="container-fluid">
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h1 class="h3 mb-0">
            <i class="bi bi-house"></i> Liste des Propriétés
        </h1>
        <a href="{% url 'proprietes:ajouter' %}" class="btn btn-primary">
            <i class="bi bi-plus-circle"></i> Ajouter une Propriété
        </a>
    </div>

    <div class="card">
        <div class="card-header">
            <h5 class="mb-0">Propriétés ({{ proprietes.count }})</h5>
        </div>
        <div class="card-body">
            {% if proprietes %}
                <div class="table-responsive">
                    <table class="table table-hover">
                        <thead>
                            <tr>
                                <th>Adresse</th>
                                <th>Type</th>
                                <th>Loyer</th>
                                <th>Statut</th>
                                <th>Bailleur</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for propriete in proprietes %}
                            <tr>
                                <td>{{ propriete.adresse }}</td>
                                <td>{{ propriete.type_bien.nom }}</td>
                                <td>{{ propriete.loyer_actuel }} F CFA</td>
                                <td>
                                    {% if propriete.disponible %}
                                        <span class="badge bg-success">Disponible</span>
                                    {% else %}
                                        <span class="badge bg-warning">Louée</span>
                                    {% endif %}
                                </td>
                                <td>{{ propriete.bailleur.nom }} {{ propriete.bailleur.prenom }}</td>
                                <td>
                                    <div class="btn-group" role="group">
                                        <a href="{% url 'proprietes:detail' propriete.pk %}" 
                                           class="btn btn-sm btn-outline-primary">
                                            <i class="bi bi-eye"></i>
                                        </a>
                                        <a href="{% url 'proprietes:modifier' propriete.pk %}" 
                                           class="btn btn-sm btn-outline-warning">
                                            <i class="bi bi-pencil"></i>
                                        </a>
                                    </div>
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            {% else %}
                <div class="text-center py-4">
                    <i class="bi bi-house display-1 text-muted"></i>
                    <h4 class="mt-3">Aucune propriété trouvée</h4>
                    <p class="text-muted">Commencez par ajouter votre première propriété.</p>
                    <a href="{% url 'proprietes:ajouter' %}" class="btn btn-primary">
                        <i class="bi bi-plus-circle"></i> Ajouter une Propriété
                    </a>
                </div>
            {% endif %}
        </div>
    </div>
</div>
{% endblock %}''',

        'templates/proprietes/detail.html': '''{% extends 'base.html' %}

{% block title %}Détail de la Propriété{% endblock %}

{% block content %}
<div class="container-fluid">
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h1 class="h3 mb-0">
            <i class="bi bi-house"></i> Détail de la Propriété
        </h1>
        <a href="{% url 'proprietes:liste' %}" class="btn btn-secondary">
            <i class="bi bi-arrow-left"></i> Retour à la liste
        </a>
    </div>

    <div class="card">
        <div class="card-header">
            <h5 class="mb-0">{{ propriete.adresse }}</h5>
        </div>
        <div class="card-body">
            <div class="row">
                <div class="col-md-6">
                    <h6>Informations générales</h6>
                    <p><strong>Adresse:</strong> {{ propriete.adresse }}</p>
                    <p><strong>Type:</strong> {{ propriete.type_bien.nom }}</p>
                    <p><strong>Loyer actuel:</strong> {{ propriete.loyer_actuel }} F CFA</p>
                    <p><strong>Statut:</strong> 
                        {% if propriete.disponible %}
                            <span class="badge bg-success">Disponible</span>
                        {% else %}
                            <span class="badge bg-warning">Louée</span>
                        {% endif %}
                    </p>
                </div>
                <div class="col-md-6">
                    <h6>Bailleur</h6>
                    <p><strong>Nom:</strong> {{ propriete.bailleur.nom }} {{ propriete.bailleur.prenom }}</p>
                    <p><strong>Email:</strong> {{ propriete.bailleur.email }}</p>
                    <p><strong>Téléphone:</strong> {{ propriete.bailleur.telephone }}</p>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}''',

        'templates/proprietes/ajouter.html': '''{% extends 'base.html' %}

{% block title %}Ajouter une Propriété{% endblock %}

{% block content %}
<div class="container-fluid">
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h1 class="h3 mb-0">
            <i class="bi bi-plus-circle"></i> Ajouter une Propriété
        </h1>
        <a href="{% url 'proprietes:liste' %}" class="btn btn-secondary">
            <i class="bi bi-arrow-left"></i> Retour à la liste
        </a>
    </div>

    <div class="card">
        <div class="card-header">
            <h5 class="mb-0">Nouvelle Propriété</h5>
        </div>
        <div class="card-body">
            <form method="post">
                {% csrf_token %}
                <div class="row">
                    <div class="col-md-6">
                        <div class="mb-3">
                            <label for="adresse" class="form-label">Adresse</label>
                            <input type="text" class="form-control" id="adresse" name="adresse" required>
                        </div>
                        <div class="mb-3">
                            <label for="type_bien" class="form-label">Type de bien</label>
                            <select class="form-select" id="type_bien" name="type_bien" required>
                                <option value="">Sélectionner un type</option>
                                {% for type in types_bien %}
                                    <option value="{{ type.id }}">{{ type.nom }}</option>
                                {% endfor %}
                            </select>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="mb-3">
                            <label for="loyer_actuel" class="form-label">Loyer mensuel (F CFA)</label>
                            <input type="number" class="form-control" id="loyer_actuel" name="loyer_actuel" required>
                        </div>
                        <div class="mb-3">
                            <label for="bailleur" class="form-label">Bailleur</label>
                            <select class="form-select" id="bailleur" name="bailleur" required>
                                <option value="">Sélectionner un bailleur</option>
                                {% for bailleur in bailleurs %}
                                    <option value="{{ bailleur.id }}">{{ bailleur.nom }} {{ bailleur.prenom }}</option>
                                {% endfor %}
                            </select>
                        </div>
                    </div>
                </div>
                <div class="text-end">
                    <button type="submit" class="btn btn-primary">
                        <i class="bi bi-check-circle"></i> Ajouter
                    </button>
                </div>
            </form>
        </div>
    </div>
</div>
{% endblock %}''',

        'templates/proprietes/modifier.html': '''{% extends 'base.html' %}

{% block title %}Modifier la Propriété{% endblock %}

{% block content %}
<div class="container-fluid">
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h1 class="h3 mb-0">
            <i class="bi bi-pencil"></i> Modifier la Propriété
        </h1>
        <a href="{% url 'proprietes:detail' propriete.pk %}" class="btn btn-secondary">
            <i class="bi bi-arrow-left"></i> Retour au détail
        </a>
    </div>

    <div class="card">
        <div class="card-header">
            <h5 class="mb-0">{{ propriete.adresse }}</h5>
        </div>
        <div class="card-body">
            <form method="post">
                {% csrf_token %}
                <div class="row">
                    <div class="col-md-6">
                        <div class="mb-3">
                            <label for="adresse" class="form-label">Adresse</label>
                            <input type="text" class="form-control" id="adresse" name="adresse" 
                                   value="{{ propriete.adresse }}" required>
                        </div>
                        <div class="mb-3">
                            <label for="type_bien" class="form-label">Type de bien</label>
                            <select class="form-select" id="type_bien" name="type_bien" required>
                                {% for type in types_bien %}
                                    <option value="{{ type.id }}" {% if type.id == propriete.type_bien.id %}selected{% endif %}>
                                        {{ type.nom }}
                                    </option>
                                {% endfor %}
                            </select>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="mb-3">
                            <label for="loyer_actuel" class="form-label">Loyer mensuel (F CFA)</label>
                            <input type="number" class="form-control" id="loyer_actuel" name="loyer_actuel" 
                                   value="{{ propriete.loyer_actuel }}" required>
                        </div>
                        <div class="mb-3">
                            <label for="bailleur" class="form-label">Bailleur</label>
                            <select class="form-select" id="bailleur" name="bailleur" required>
                                {% for bailleur in bailleurs %}
                                    <option value="{{ bailleur.id }}" {% if bailleur.id == propriete.bailleur.id %}selected{% endif %}>
                                        {{ bailleur.nom }} {{ bailleur.prenom }}
                                    </option>
                                {% endfor %}
                            </select>
                        </div>
                    </div>
                </div>
                <div class="text-end">
                    <button type="submit" class="btn btn-primary">
                        <i class="bi bi-check-circle"></i> Modifier
                    </button>
                </div>
            </form>
        </div>
    </div>
</div>
{% endblock %}'''
    }
    
    # Créer les templates des propriétés
    for file_path, content in proprietes_templates.items():
        create_template_file(file_path, content)
    
    # Templates pour les contrats
    contrats_templates = {
        'templates/contrats/detail.html': '''{% extends 'base.html' %}

{% block title %}Détail du Contrat{% endblock %}

{% block content %}
<div class="container-fluid">
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h1 class="h3 mb-0">
            <i class="bi bi-file-earmark-text"></i> Détail du Contrat
        </h1>
        <a href="{% url 'contrats:liste' %}" class="btn btn-secondary">
            <i class="bi bi-arrow-left"></i> Retour à la liste
        </a>
    </div>

    <div class="card">
        <div class="card-header">
            <h5 class="mb-0">{{ contrat.reference }}</h5>
        </div>
        <div class="card-body">
            <div class="row">
                <div class="col-md-6">
                    <h6>Informations du contrat</h6>
                    <p><strong>Référence:</strong> {{ contrat.reference }}</p>
                    <p><strong>Date de début:</strong> {{ contrat.date_debut|date:"d/m/Y" }}</p>
                    <p><strong>Date de fin:</strong> {{ contrat.date_fin|date:"d/m/Y" }}</p>
                    <p><strong>Loyer mensuel:</strong> {{ contrat.loyer_mensuel }} F CFA</p>
                    <p><strong>Statut:</strong> 
                        {% if contrat.est_actif and not contrat.est_resilie %}
                            <span class="badge bg-success">Actif</span>
                        {% elif contrat.est_resilie %}
                            <span class="badge bg-danger">Résilié</span>
                        {% else %}
                            <span class="badge bg-secondary">Expiré</span>
                        {% endif %}
                    </p>
                </div>
                <div class="col-md-6">
                    <h6>Propriété et Locataire</h6>
                    <p><strong>Propriété:</strong> {{ contrat.propriete.adresse }}</p>
                    <p><strong>Locataire:</strong> {{ contrat.locataire.nom }} {{ contrat.locataire.prenom }}</p>
                    <p><strong>Email:</strong> {{ contrat.locataire.email }}</p>
                    <p><strong>Téléphone:</strong> {{ contrat.locataire.telephone }}</p>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}''',

        'templates/contrats/ajouter.html': '''{% extends 'base.html' %}

{% block title %}Ajouter un Contrat{% endblock %}

{% block content %}
<div class="container-fluid">
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h1 class="h3 mb-0">
            <i class="bi bi-plus-circle"></i> Ajouter un Contrat
        </h1>
        <a href="{% url 'contrats:liste' %}" class="btn btn-secondary">
            <i class="bi bi-arrow-left"></i> Retour à la liste
        </a>
    </div>

    <div class="card">
        <div class="card-header">
            <h5 class="mb-0">Nouveau Contrat</h5>
        </div>
        <div class="card-body">
            <form method="post">
                {% csrf_token %}
                <div class="row">
                    <div class="col-md-6">
                        <div class="mb-3">
                            <label for="propriete" class="form-label">Propriété</label>
                            <select class="form-select" id="propriete" name="propriete" required>
                                <option value="">Sélectionner une propriété</option>
                                {% for propriete in proprietes %}
                                    <option value="{{ propriete.id }}">{{ propriete.adresse }}</option>
                                {% endfor %}
                            </select>
                        </div>
                        <div class="mb-3">
                            <label for="locataire" class="form-label">Locataire</label>
                            <select class="form-select" id="locataire" name="locataire" required>
                                <option value="">Sélectionner un locataire</option>
                                {% for locataire in locataires %}
                                    <option value="{{ locataire.id }}">{{ locataire.nom }} {{ locataire.prenom }}</option>
                                {% endfor %}
                            </select>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="mb-3">
                            <label for="date_debut" class="form-label">Date de début</label>
                            <input type="date" class="form-control" id="date_debut" name="date_debut" required>
                        </div>
                        <div class="mb-3">
                            <label for="date_fin" class="form-label">Date de fin</label>
                            <input type="date" class="form-control" id="date_fin" name="date_fin" required>
                        </div>
                        <div class="mb-3">
                            <label for="loyer_mensuel" class="form-label">Loyer mensuel (F CFA)</label>
                            <input type="number" class="form-control" id="loyer_mensuel" name="loyer_mensuel" required>
                        </div>
                    </div>
                </div>
                <div class="text-end">
                    <button type="submit" class="btn btn-primary">
                        <i class="bi bi-check-circle"></i> Ajouter
                    </button>
                </div>
            </form>
        </div>
    </div>
</div>
{% endblock %}''',

        'templates/contrats/modifier.html': '''{% extends 'base.html' %}

{% block title %}Modifier le Contrat{% endblock %}

{% block content %}
<div class="container-fluid">
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h1 class="h3 mb-0">
            <i class="bi bi-pencil"></i> Modifier le Contrat
        </h1>
        <a href="{% url 'contrats:detail' contrat.pk %}" class="btn btn-secondary">
            <i class="bi bi-arrow-left"></i> Retour au détail
        </a>
    </div>

    <div class="card">
        <div class="card-header">
            <h5 class="mb-0">{{ contrat.reference }}</h5>
        </div>
        <div class="card-body">
            <form method="post">
                {% csrf_token %}
                <div class="row">
                    <div class="col-md-6">
                        <div class="mb-3">
                            <label for="propriete" class="form-label">Propriété</label>
                            <select class="form-select" id="propriete" name="propriete" required>
                                {% for propriete in proprietes %}
                                    <option value="{{ propriete.id }}" {% if propriete.id == contrat.propriete.id %}selected{% endif %}>
                                        {{ propriete.adresse }}
                                    </option>
                                {% endfor %}
                            </select>
                        </div>
                        <div class="mb-3">
                            <label for="locataire" class="form-label">Locataire</label>
                            <select class="form-select" id="locataire" name="locataire" required>
                                {% for locataire in locataires %}
                                    <option value="{{ locataire.id }}" {% if locataire.id == contrat.locataire.id %}selected{% endif %}>
                                        {{ locataire.nom }} {{ locataire.prenom }}
                                    </option>
                                {% endfor %}
                            </select>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="mb-3">
                            <label for="date_debut" class="form-label">Date de début</label>
                            <input type="date" class="form-control" id="date_debut" name="date_debut" 
                                   value="{{ contrat.date_debut|date:'Y-m-d' }}" required>
                        </div>
                        <div class="mb-3">
                            <label for="date_fin" class="form-label">Date de fin</label>
                            <input type="date" class="form-control" id="date_fin" name="date_fin" 
                                   value="{{ contrat.date_fin|date:'Y-m-d' }}" required>
                        </div>
                        <div class="mb-3">
                            <label for="loyer_mensuel" class="form-label">Loyer mensuel (F CFA)</label>
                            <input type="number" class="form-control" id="loyer_mensuel" name="loyer_mensuel" 
                                   value="{{ contrat.loyer_mensuel }}" required>
                        </div>
                    </div>
                </div>
                <div class="text-end">
                    <button type="submit" class="btn btn-primary">
                        <i class="bi bi-check-circle"></i> Modifier
                    </button>
                </div>
            </form>
        </div>
    </div>
</div>
{% endblock %}'''
    }
    
    # Créer les templates des contrats
    for file_path, content in contrats_templates.items():
        create_template_file(file_path, content)
    
    # Templates pour les paiements
    paiements_templates = {
        'templates/paiements/detail.html': '''{% extends 'base.html' %}

{% block title %}Détail du Paiement{% endblock %}

{% block content %}
<div class="container-fluid">
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h1 class="h3 mb-0">
            <i class="bi bi-cash-coin"></i> Détail du Paiement
        </h1>
        <a href="{% url 'paiements:liste' %}" class="btn btn-secondary">
            <i class="bi bi-arrow-left"></i> Retour à la liste
        </a>
    </div>

    <div class="card">
        <div class="card-header">
            <h5 class="mb-0">{{ paiement.reference }}</h5>
        </div>
        <div class="card-body">
            <div class="row">
                <div class="col-md-6">
                    <h6>Informations du paiement</h6>
                    <p><strong>Référence:</strong> {{ paiement.reference }}</p>
                    <p><strong>Montant:</strong> {{ paiement.montant }} F CFA</p>
                    <p><strong>Date de paiement:</strong> {{ paiement.date_paiement|date:"d/m/Y" }}</p>
                    <p><strong>Méthode:</strong> {{ paiement.get_methode_paiement_display }}</p>
                    <p><strong>Statut:</strong> 
                        {% if paiement.statut == 'valide' %}
                            <span class="badge bg-success">Validé</span>
                        {% elif paiement.statut == 'en_attente' %}
                            <span class="badge bg-warning">En attente</span>
                        {% else %}
                            <span class="badge bg-danger">Rejeté</span>
                        {% endif %}
                    </p>
                </div>
                <div class="col-md-6">
                    <h6>Contrat associé</h6>
                    <p><strong>Référence:</strong> {{ paiement.contrat.reference }}</p>
                    <p><strong>Propriété:</strong> {{ paiement.contrat.propriete.adresse }}</p>
                    <p><strong>Locataire:</strong> {{ paiement.contrat.locataire.nom }} {{ paiement.contrat.locataire.prenom }}</p>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}''',

        'templates/paiements/ajouter.html': '''{% extends 'base.html' %}

{% block title %}Ajouter un Paiement{% endblock %}

{% block content %}
<div class="container-fluid">
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h1 class="h3 mb-0">
            <i class="bi bi-plus-circle"></i> Ajouter un Paiement
        </h1>
        <a href="{% url 'paiements:liste' %}" class="btn btn-secondary">
            <i class="bi bi-arrow-left"></i> Retour à la liste
        </a>
    </div>

    <div class="card">
        <div class="card-header">
            <h5 class="mb-0">Nouveau Paiement</h5>
        </div>
        <div class="card-body">
            <form method="post">
                {% csrf_token %}
                <div class="row">
                    <div class="col-md-6">
                        <div class="mb-3">
                            <label for="contrat" class="form-label">Contrat</label>
                            <select class="form-select" id="contrat" name="contrat" required>
                                <option value="">Sélectionner un contrat</option>
                                {% for contrat in contrats %}
                                    <option value="{{ contrat.id }}">{{ contrat.reference }} - {{ contrat.propriete.adresse }}</option>
                                {% endfor %}
                            </select>
                        </div>
                        <div class="mb-3">
                            <label for="montant" class="form-label">Montant (F CFA)</label>
                            <input type="number" step="0.01" class="form-control" id="montant" name="montant" required>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="mb-3">
                            <label for="date_paiement" class="form-label">Date de paiement</label>
                            <input type="date" class="form-control" id="date_paiement" name="date_paiement" required>
                        </div>
                        <div class="mb-3">
                            <label for="methode_paiement" class="form-label">Méthode de paiement</label>
                            <select class="form-select" id="methode_paiement" name="methode_paiement" required>
                                <option value="">Sélectionner une méthode</option>
                                <option value="virement">Virement</option>
                                <option value="cheque">Chèque</option>
                                <option value="especes">Espèces</option>
                                <option value="carte">Carte bancaire</option>
                            </select>
                        </div>
                    </div>
                </div>
                <div class="text-end">
                    <button type="submit" class="btn btn-primary">
                        <i class="bi bi-check-circle"></i> Ajouter
                    </button>
                </div>
            </form>
        </div>
    </div>
</div>
{% endblock %}''',

        'templates/paiements/modifier.html': '''{% extends 'base.html' %}

{% block title %}Modifier le Paiement{% endblock %}

{% block content %}
<div class="container-fluid">
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h1 class="h3 mb-0">
            <i class="bi bi-pencil"></i> Modifier le Paiement
        </h1>
        <a href="{% url 'paiements:detail' paiement.pk %}" class="btn btn-secondary">
            <i class="bi bi-arrow-left"></i> Retour au détail
        </a>
    </div>

    <div class="card">
        <div class="card-header">
            <h5 class="mb-0">{{ paiement.reference }}</h5>
        </div>
        <div class="card-body">
            <form method="post">
                {% csrf_token %}
                <div class="row">
                    <div class="col-md-6">
                        <div class="mb-3">
                            <label for="contrat" class="form-label">Contrat</label>
                            <select class="form-select" id="contrat" name="contrat" required>
                                {% for contrat in contrats %}
                                    <option value="{{ contrat.id }}" {% if contrat.id == paiement.contrat.id %}selected{% endif %}>
                                        {{ contrat.reference }} - {{ contrat.propriete.adresse }}
                                    </option>
                                {% endfor %}
                            </select>
                        </div>
                        <div class="mb-3">
                            <label for="montant" class="form-label">Montant (F CFA)</label>
                            <input type="number" step="0.01" class="form-control" id="montant" name="montant" 
                                   value="{{ paiement.montant }}" required>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="mb-3">
                            <label for="date_paiement" class="form-label">Date de paiement</label>
                            <input type="date" class="form-control" id="date_paiement" name="date_paiement" 
                                   value="{{ paiement.date_paiement|date:'Y-m-d' }}" required>
                        </div>
                        <div class="mb-3">
                            <label for="methode_paiement" class="form-label">Méthode de paiement</label>
                            <select class="form-select" id="methode_paiement" name="methode_paiement" required>
                                <option value="virement" {% if paiement.methode_paiement == 'virement' %}selected{% endif %}>Virement</option>
                                <option value="cheque" {% if paiement.methode_paiement == 'cheque' %}selected{% endif %}>Chèque</option>
                                <option value="especes" {% if paiement.methode_paiement == 'especes' %}selected{% endif %}>Espèces</option>
                                <option value="carte" {% if paiement.methode_paiement == 'carte' %}selected{% endif %}>Carte bancaire</option>
                            </select>
                        </div>
                    </div>
                </div>
                <div class="text-end">
                    <button type="submit" class="btn btn-primary">
                        <i class="bi bi-check-circle"></i> Modifier
                    </button>
                </div>
            </form>
        </div>
    </div>
</div>
{% endblock %}'''
    }
    
    # Créer les templates des paiements
    for file_path, content in paiements_templates.items():
        create_template_file(file_path, content)
    
    # Templates pour les utilisateurs
    utilisateurs_templates = {
        'templates/utilisateurs/detail.html': '''{% extends 'base.html' %}

{% block title %}Détail de l'Utilisateur{% endblock %}

{% block content %}
<div class="container-fluid">
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h1 class="h3 mb-0">
            <i class="bi bi-person"></i> Détail de l'Utilisateur
        </h1>
        <a href="{% url 'utilisateurs:liste' %}" class="btn btn-secondary">
            <i class="bi bi-arrow-left"></i> Retour à la liste
        </a>
    </div>

    <div class="card">
        <div class="card-header">
            <h5 class="mb-0">{{ utilisateur.username }}</h5>
        </div>
        <div class="card-body">
            <div class="row">
                <div class="col-md-6">
                    <h6>Informations personnelles</h6>
                    <p><strong>Nom d'utilisateur:</strong> {{ utilisateur.username }}</p>
                    <p><strong>Nom:</strong> {{ utilisateur.nom }}</p>
                    <p><strong>Prénom:</strong> {{ utilisateur.prenom }}</p>
                    <p><strong>Email:</strong> {{ utilisateur.email }}</p>
                    <p><strong>Téléphone:</strong> {{ utilisateur.telephone }}</p>
                </div>
                <div class="col-md-6">
                    <h6>Statut et permissions</h6>
                    <p><strong>Statut:</strong> 
                        {% if utilisateur.is_active %}
                            <span class="badge bg-success">Actif</span>
                        {% else %}
                            <span class="badge bg-secondary">Inactif</span>
                        {% endif %}
                    </p>
                    <p><strong>Rôle:</strong> 
                        {% if utilisateur.is_superuser %}
                            <span class="badge bg-danger">Administrateur</span>
                        {% elif utilisateur.is_staff %}
                            <span class="badge bg-warning">Staff</span>
                        {% else %}
                            <span class="badge bg-info">Utilisateur</span>
                        {% endif %}
                    </p>
                    <p><strong>Date d'inscription:</strong> {{ utilisateur.date_joined|date:"d/m/Y" }}</p>
                    <p><strong>Dernière connexion:</strong> {{ utilisateur.last_login|date:"d/m/Y H:i" }}</p>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}''',

        'templates/utilisateurs/ajouter.html': '''{% extends 'base.html' %}

{% block title %}Ajouter un Utilisateur{% endblock %}

{% block content %}
<div class="container-fluid">
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h1 class="h3 mb-0">
            <i class="bi bi-plus-circle"></i> Ajouter un Utilisateur
        </h1>
        <a href="{% url 'utilisateurs:liste' %}" class="btn btn-secondary">
            <i class="bi bi-arrow-left"></i> Retour à la liste
        </a>
    </div>

    <div class="card">
        <div class="card-header">
            <h5 class="mb-0">Nouvel Utilisateur</h5>
        </div>
        <div class="card-body">
            <form method="post">
                {% csrf_token %}
                <div class="row">
                    <div class="col-md-6">
                        <div class="mb-3">
                            <label for="username" class="form-label">Nom d'utilisateur</label>
                            <input type="text" class="form-control" id="username" name="username" required>
                        </div>
                        <div class="mb-3">
                            <label for="email" class="form-label">Email</label>
                            <input type="email" class="form-control" id="email" name="email" required>
                        </div>
                        <div class="mb-3">
                            <label for="nom" class="form-label">Nom</label>
                            <input type="text" class="form-control" id="nom" name="nom" required>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="mb-3">
                            <label for="prenom" class="form-label">Prénom</label>
                            <input type="text" class="form-control" id="prenom" name="prenom" required>
                        </div>
                        <div class="mb-3">
                            <label for="telephone" class="form-label">Téléphone</label>
                            <input type="tel" class="form-control" id="telephone" name="telephone">
                        </div>
                        <div class="mb-3">
                            <label for="password" class="form-label">Mot de passe</label>
                            <input type="password" class="form-control" id="password" name="password" required>
                        </div>
                    </div>
                </div>
                <div class="text-end">
                    <button type="submit" class="btn btn-primary">
                        <i class="bi bi-check-circle"></i> Ajouter
                    </button>
                </div>
            </form>
        </div>
    </div>
</div>
{% endblock %}''',

        'templates/utilisateurs/modifier.html': '''{% extends 'base.html' %}

{% block title %}Modifier l'Utilisateur{% endblock %}

{% block content %}
<div class="container-fluid">
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h1 class="h3 mb-0">
            <i class="bi bi-pencil"></i> Modifier l'Utilisateur
        </h1>
        <a href="{% url 'utilisateurs:detail' utilisateur.pk %}" class="btn btn-secondary">
            <i class="bi bi-arrow-left"></i> Retour au détail
        </a>
    </div>

    <div class="card">
        <div class="card-header">
            <h5 class="mb-0">{{ utilisateur.username }}</h5>
        </div>
        <div class="card-body">
            <form method="post">
                {% csrf_token %}
                <div class="row">
                    <div class="col-md-6">
                        <div class="mb-3">
                            <label for="username" class="form-label">Nom d'utilisateur</label>
                            <input type="text" class="form-control" id="username" name="username" 
                                   value="{{ utilisateur.username }}" required>
                        </div>
                        <div class="mb-3">
                            <label for="email" class="form-label">Email</label>
                            <input type="email" class="form-control" id="email" name="email" 
                                   value="{{ utilisateur.email }}" required>
                        </div>
                        <div class="mb-3">
                            <label for="nom" class="form-label">Nom</label>
                            <input type="text" class="form-control" id="nom" name="nom" 
                                   value="{{ utilisateur.nom }}" required>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="mb-3">
                            <label for="prenom" class="form-label">Prénom</label>
                            <input type="text" class="form-control" id="prenom" name="prenom" 
                                   value="{{ utilisateur.prenom }}" required>
                        </div>
                        <div class="mb-3">
                            <label for="telephone" class="form-label">Téléphone</label>
                            <input type="tel" class="form-control" id="telephone" name="telephone" 
                                   value="{{ utilisateur.telephone }}">
                        </div>
                        <div class="mb-3">
                            <label for="is_active" class="form-label">Statut</label>
                            <select class="form-select" id="is_active" name="is_active">
                                <option value="True" {% if utilisateur.is_active %}selected{% endif %}>Actif</option>
                                <option value="False" {% if not utilisateur.is_active %}selected{% endif %}>Inactif</option>
                            </select>
                        </div>
                    </div>
                </div>
                <div class="text-end">
                    <button type="submit" class="btn btn-primary">
                        <i class="bi bi-check-circle"></i> Modifier
                    </button>
                </div>
            </form>
        </div>
    </div>
</div>
{% endblock %}''',

        'templates/utilisateurs/profile.html': '''{% extends 'base.html' %}

{% block title %}Mon Profil{% endblock %}

{% block content %}
<div class="container-fluid">
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h1 class="h3 mb-0">
            <i class="bi bi-person"></i> Mon Profil
        </h1>
    </div>

    <div class="card">
        <div class="card-header">
            <h5 class="mb-0">Informations personnelles</h5>
        </div>
        <div class="card-body">
            <div class="row">
                <div class="col-md-6">
                    <p><strong>Nom d'utilisateur:</strong> {{ user.username }}</p>
                    <p><strong>Nom:</strong> {{ user.nom }}</p>
                    <p><strong>Prénom:</strong> {{ user.prenom }}</p>
                    <p><strong>Email:</strong> {{ user.email }}</p>
                    <p><strong>Téléphone:</strong> {{ user.telephone }}</p>
                </div>
                <div class="col-md-6">
                    <p><strong>Date d'inscription:</strong> {{ user.date_joined|date:"d/m/Y" }}</p>
                    <p><strong>Dernière connexion:</strong> {{ user.last_login|date:"d/m/Y H:i" }}</p>
                    <p><strong>Statut:</strong> 
                        {% if user.is_active %}
                            <span class="badge bg-success">Actif</span>
                        {% else %}
                            <span class="badge bg-secondary">Inactif</span>
                        {% endif %}
                    </p>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}''',

        'templates/utilisateurs/settings.html': '''{% extends 'base.html' %}

{% block title %}Paramètres{% endblock %}

{% block content %}
<div class="container-fluid">
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h1 class="h3 mb-0">
            <i class="bi bi-gear"></i> Paramètres
        </h1>
    </div>

    <div class="card">
        <div class="card-header">
            <h5 class="mb-0">Configuration</h5>
        </div>
        <div class="card-body">
            <p>Page des paramètres en cours de développement...</p>
        </div>
    </div>
</div>
{% endblock %}'''
    }
    
    # Créer les templates des utilisateurs
    for file_path, content in utilisateurs_templates.items():
        create_template_file(file_path, content)
    
    print("\n🎉 Création des templates terminée !")
    print("=" * 50)
    print("✅ Tous les templates manquants ont été créés")
    print("🚀 Vous pouvez maintenant accéder à toutes les pages web")

if __name__ == '__main__':
    main() 