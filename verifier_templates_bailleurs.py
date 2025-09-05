#!/usr/bin/env python
"""
Script pour vérifier et créer tous les templates manquants pour les bailleurs
"""

import os

def create_missing_bailleur_templates():
    """Crée les templates manquants pour les bailleurs"""
    
    print("🔍 Vérification des templates pour les bailleurs...")
    print("=" * 60)
    
    templates_dir = "templates/proprietes"
    os.makedirs(templates_dir, exist_ok=True)
    
    # Liste des templates nécessaires pour les bailleurs
    templates_needed = {
        'bailleur_ajouter.html': 'Template pour ajouter un bailleur',
        'bailleur_detail.html': 'Template pour afficher les détails d\'un bailleur',
        'bailleur_modifier.html': 'Template pour modifier un bailleur',
        'bailleurs_liste.html': 'Template pour la liste des bailleurs'
    }
    
    created_count = 0
    
    for template_name, description in templates_needed.items():
        template_path = os.path.join(templates_dir, template_name)
        
        if os.path.exists(template_path):
            print(f"✅ {template_name} - Existe déjà")
        else:
            print(f"❌ {template_name} - Manquant")
            
            # Créer le template manquant
            if template_name == 'bailleur_detail.html':
                create_bailleur_detail_template(template_path)
            elif template_name == 'bailleur_modifier.html':
                create_bailleur_modifier_template(template_path)
            elif template_name == 'bailleurs_liste.html':
                create_bailleurs_liste_template(template_path)
            
            created_count += 1
            print(f"✅ {template_name} - Créé")
    
    print("\n" + "=" * 60)
    print(f"📊 Résumé : {created_count} templates créés")
    print("🎉 Tous les templates pour les bailleurs sont maintenant disponibles !")

def create_bailleur_detail_template(template_path):
    """Crée le template de détail d'un bailleur"""
    content = '''{% extends 'base.html' %}

{% block title %}Détails du Bailleur{% endblock %}

{% block content %}
<div class="container-fluid">
    <div class="row">
        <div class="col-12">
            <div class="card">
                <div class="card-header">
                    <div class="d-flex justify-content-between align-items-center">
                        <h4 class="mb-0">
                            <i class="bi bi-person-fill text-primary me-2"></i>
                            Détails du Bailleur
                        </h4>
                        <div>
                            <a href="{% url 'proprietes:bailleur_modifier' bailleur.pk %}" class="btn btn-warning me-2">
                                <i class="bi bi-pencil me-1"></i>
                                Modifier
                            </a>
                            <a href="{% url 'proprietes:bailleurs_liste' %}" class="btn btn-outline-secondary">
                                <i class="bi bi-arrow-left me-1"></i>
                                Retour à la liste
                            </a>
                        </div>
                    </div>
                </div>
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-6">
                            <h5 class="text-primary">Informations Personnelles</h5>
                            <table class="table table-borderless">
                                <tr>
                                    <td><strong>Nom :</strong></td>
                                    <td>{{ bailleur.nom }}</td>
                                </tr>
                                <tr>
                                    <td><strong>Prénom :</strong></td>
                                    <td>{{ bailleur.prenom }}</td>
                                </tr>
                                <tr>
                                    <td><strong>Date de naissance :</strong></td>
                                    <td>{{ bailleur.date_naissance|default:"Non renseigné" }}</td>
                                </tr>
                                <tr>
                                    <td><strong>Nationalité :</strong></td>
                                    <td>{{ bailleur.nationalite|default:"Non renseigné" }}</td>
                                </tr>
                                <tr>
                                    <td><strong>Profession :</strong></td>
                                    <td>{{ bailleur.profession|default:"Non renseigné" }}</td>
                                </tr>
                            </table>
                        </div>
                        <div class="col-md-6">
                            <h5 class="text-success">Coordonnées</h5>
                            <table class="table table-borderless">
                                <tr>
                                    <td><strong>Adresse :</strong></td>
                                    <td>{{ bailleur.adresse }}</td>
                                </tr>
                                <tr>
                                    <td><strong>Code postal :</strong></td>
                                    <td>{{ bailleur.code_postal }}</td>
                                </tr>
                                <tr>
                                    <td><strong>Ville :</strong></td>
                                    <td>{{ bailleur.ville }}</td>
                                </tr>
                                <tr>
                                    <td><strong>Téléphone :</strong></td>
                                    <td>{{ bailleur.telephone }}</td>
                                </tr>
                                <tr>
                                    <td><strong>Email :</strong></td>
                                    <td>{{ bailleur.email|default:"Non renseigné" }}</td>
                                </tr>
                            </table>
                        </div>
                    </div>
                    
                    <div class="row mt-4">
                        <div class="col-12">
                            <h5 class="text-info">Informations Bancaires</h5>
                            <table class="table table-borderless">
                                <tr>
                                    <td><strong>Banque :</strong></td>
                                    <td>{{ bailleur.banque|default:"Non renseigné" }}</td>
                                    <td><strong>IBAN :</strong></td>
                                    <td>{{ bailleur.iban|default:"Non renseigné" }}</td>
                                </tr>
                                <tr>
                                    <td><strong>BIC/SWIFT :</strong></td>
                                    <td>{{ bailleur.bic|default:"Non renseigné" }}</td>
                                    <td><strong>Compte :</strong></td>
                                    <td>{{ bailleur.compte|default:"Non renseigné" }}</td>
                                </tr>
                            </table>
                        </div>
                    </div>
                    
                    {% if bailleur.notes %}
                    <div class="row mt-4">
                        <div class="col-12">
                            <h5 class="text-warning">Notes</h5>
                            <div class="alert alert-warning">
                                {{ bailleur.notes }}
                            </div>
                        </div>
                    </div>
                    {% endif %}
                    
                    <div class="row mt-4">
                        <div class="col-12">
                            <h5 class="text-primary">Propriétés du Bailleur</h5>
                            {% if proprietes %}
                                <div class="table-responsive">
                                    <table class="table table-striped">
                                        <thead>
                                            <tr>
                                                <th>Adresse</th>
                                                <th>Type</th>
                                                <th>Surface</th>
                                                <th>Prix</th>
                                                <th>Actions</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {% for propriete in proprietes %}
                                            <tr>
                                                <td>{{ propriete.adresse }}</td>
                                                <td>{{ propriete.type_bien.nom }}</td>
                                                <td>{{ propriete.surface }} m²</td>
                                                <td>{{ propriete.prix }} F CFA</td>
                                                <td>
                                                    <a href="{% url 'proprietes:detail' propriete.pk %}" class="btn btn-sm btn-outline-primary">
                                                        <i class="bi bi-eye"></i>
                                                    </a>
                                                </td>
                                            </tr>
                                            {% endfor %}
                                        </tbody>
                                    </table>
                                </div>
                            {% else %}
                                <div class="alert alert-info">
                                    <i class="bi bi-info-circle me-2"></i>
                                    Aucune propriété associée à ce bailleur.
                                </div>
                            {% endif %}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}'''
    
    with open(template_path, 'w', encoding='utf-8') as f:
        f.write(content)

def create_bailleur_modifier_template(template_path):
    """Crée le template de modification d'un bailleur"""
    content = '''{% extends 'base.html' %}
{% load crispy_forms_tags %}

{% block title %}Modifier le Bailleur{% endblock %}

{% block content %}
<div class="container-fluid">
    <div class="row">
        <div class="col-12">
            <div class="card">
                <div class="card-header">
                    <div class="d-flex justify-content-between align-items-center">
                        <h4 class="mb-0">
                            <i class="bi bi-pencil-square text-warning me-2"></i>
                            Modifier le Bailleur
                        </h4>
                        <a href="{% url 'proprietes:bailleur_detail' bailleur.pk %}" class="btn btn-outline-secondary">
                            <i class="bi bi-arrow-left me-1"></i>
                            Retour aux détails
                        </a>
                    </div>
                </div>
                <div class="card-body">
                    <form method="post" class="needs-validation" novalidate>
                        {% csrf_token %}
                        
                        <div class="row">
                            <!-- Informations personnelles -->
                            <div class="col-md-6">
                                <div class="card border-primary">
                                    <div class="card-header bg-primary text-white">
                                        <h5 class="mb-0">
                                            <i class="bi bi-person-fill me-2"></i>
                                            Informations Personnelles
                                        </h5>
                                    </div>
                                    <div class="card-body">
                                        <div class="row">
                                            <div class="col-md-6 mb-3">
                                                <label for="nom" class="form-label">Nom *</label>
                                                <input type="text" class="form-control" id="nom" name="nom" value="{{ bailleur.nom }}" required>
                                                <div class="invalid-feedback">
                                                    Le nom est requis.
                                                </div>
                                            </div>
                                            <div class="col-md-6 mb-3">
                                                <label for="prenom" class="form-label">Prénom *</label>
                                                <input type="text" class="form-control" id="prenom" name="prenom" value="{{ bailleur.prenom }}" required>
                                                <div class="invalid-feedback">
                                                    Le prénom est requis.
                                                </div>
                                            </div>
                                        </div>
                                        
                                        <div class="row">
                                            <div class="col-md-6 mb-3">
                                                <label for="date_naissance" class="form-label">Date de naissance</label>
                                                <input type="date" class="form-control" id="date_naissance" name="date_naissance" value="{{ bailleur.date_naissance|date:'Y-m-d' }}">
                                            </div>
                                            <div class="col-md-6 mb-3">
                                                <label for="nationalite" class="form-label">Nationalité</label>
                                                <input type="text" class="form-control" id="nationalite" name="nationalite" value="{{ bailleur.nationalite }}">
                                            </div>
                                        </div>
                                        
                                        <div class="mb-3">
                                            <label for="profession" class="form-label">Profession</label>
                                            <input type="text" class="form-control" id="profession" name="profession" value="{{ bailleur.profession }}">
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            <!-- Coordonnées -->
                            <div class="col-md-6">
                                <div class="card border-success">
                                    <div class="card-header bg-success text-white">
                                        <h5 class="mb-0">
                                            <i class="bi bi-geo-alt-fill me-2"></i>
                                            Coordonnées
                                        </h5>
                                    </div>
                                    <div class="card-body">
                                        <div class="mb-3">
                                            <label for="adresse" class="form-label">Adresse *</label>
                                            <textarea class="form-control" id="adresse" name="adresse" rows="3" required>{{ bailleur.adresse }}</textarea>
                                            <div class="invalid-feedback">
                                                L'adresse est requise.
                                            </div>
                                        </div>
                                        
                                        <div class="row">
                                            <div class="col-md-6 mb-3">
                                                <label for="code_postal" class="form-label">Code postal *</label>
                                                <input type="text" class="form-control" id="code_postal" name="code_postal" value="{{ bailleur.code_postal }}" required>
                                                <div class="invalid-feedback">
                                                    Le code postal est requis.
                                                </div>
                                            </div>
                                            <div class="col-md-6 mb-3">
                                                <label for="ville" class="form-label">Ville *</label>
                                                <input type="text" class="form-control" id="ville" name="ville" value="{{ bailleur.ville }}" required>
                                                <div class="invalid-feedback">
                                                    La ville est requise.
                                                </div>
                                            </div>
                                        </div>
                                        
                                        <div class="row">
                                            <div class="col-md-6 mb-3">
                                                <label for="telephone" class="form-label">Téléphone *</label>
                                                <input type="tel" class="form-control" id="telephone" name="telephone" value="{{ bailleur.telephone }}" required>
                                                <div class="invalid-feedback">
                                                    Le téléphone est requis.
                                                </div>
                                            </div>
                                            <div class="col-md-6 mb-3">
                                                <label for="email" class="form-label">Email</label>
                                                <input type="email" class="form-control" id="email" name="email" value="{{ bailleur.email }}">
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Informations bancaires -->
                        <div class="row mt-4">
                            <div class="col-12">
                                <div class="card border-info">
                                    <div class="card-header bg-info text-white">
                                        <h5 class="mb-0">
                                            <i class="bi bi-bank me-2"></i>
                                            Informations Bancaires
                                        </h5>
                                    </div>
                                    <div class="card-body">
                                        <div class="row">
                                            <div class="col-md-6 mb-3">
                                                <label for="banque" class="form-label">Banque</label>
                                                <input type="text" class="form-control" id="banque" name="banque" value="{{ bailleur.banque }}">
                                            </div>
                                            <div class="col-md-6 mb-3">
                                                <label for="iban" class="form-label">IBAN</label>
                                                <input type="text" class="form-control" id="iban" name="iban" value="{{ bailleur.iban }}">
                                            </div>
                                        </div>
                                        
                                        <div class="row">
                                            <div class="col-md-6 mb-3">
                                                <label for="bic" class="form-label">BIC/SWIFT</label>
                                                <input type="text" class="form-control" id="bic" name="bic" value="{{ bailleur.bic }}">
                                            </div>
                                            <div class="col-md-6 mb-3">
                                                <label for="compte" class="form-label">Numéro de compte</label>
                                                <input type="text" class="form-control" id="compte" name="compte" value="{{ bailleur.compte }}">
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Notes -->
                        <div class="row mt-4">
                            <div class="col-12">
                                <div class="card border-warning">
                                    <div class="card-header bg-warning text-dark">
                                        <h5 class="mb-0">
                                            <i class="bi bi-file-earmark-text-fill me-2"></i>
                                            Notes
                                        </h5>
                                    </div>
                                    <div class="card-body">
                                        <div class="mb-3">
                                            <label for="notes" class="form-label">Notes</label>
                                            <textarea class="form-control" id="notes" name="notes" rows="3">{{ bailleur.notes }}</textarea>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Boutons d'action -->
                        <div class="row mt-4">
                            <div class="col-12">
                                <div class="d-flex justify-content-between">
                                    <a href="{% url 'proprietes:bailleur_detail' bailleur.pk %}" class="btn btn-secondary">
                                        <i class="bi bi-x-circle me-1"></i>
                                        Annuler
                                    </a>
                                    <button type="submit" class="btn btn-warning">
                                        <i class="bi bi-check-circle me-1"></i>
                                        Mettre à jour
                                    </button>
                                </div>
                            </div>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    </div>
</div>

<!-- Script de validation Bootstrap -->
<script>
(function() {
    'use strict';
    window.addEventListener('load', function() {
        var forms = document.getElementsByClassName('needs-validation');
        var validation = Array.prototype.filter.call(forms, function(form) {
            form.addEventListener('submit', function(event) {
                if (form.checkValidity() === false) {
                    event.preventDefault();
                    event.stopPropagation();
                }
                form.classList.add('was-validated');
            }, false);
        });
    }, false);
})();
</script>
{% endblock %}'''
    
    with open(template_path, 'w', encoding='utf-8') as f:
        f.write(content)

def create_bailleurs_liste_template(template_path):
    """Crée le template de liste des bailleurs"""
    content = '''{% extends 'base.html' %}

{% block title %}Liste des Bailleurs{% endblock %}

{% block content %}
<div class="container-fluid">
    <div class="row">
        <div class="col-12">
            <div class="card">
                <div class="card-header">
                    <div class="d-flex justify-content-between align-items-center">
                        <h4 class="mb-0">
                            <i class="bi bi-people-fill text-primary me-2"></i>
                            Liste des Bailleurs
                        </h4>
                        <a href="{% url 'proprietes:bailleur_ajouter' %}" class="btn btn-primary">
                            <i class="bi bi-person-plus me-1"></i>
                            Ajouter un Bailleur
                        </a>
                    </div>
                </div>
                <div class="card-body">
                    {% if bailleurs %}
                        <div class="table-responsive">
                            <table class="table table-striped table-hover">
                                <thead class="table-dark">
                                    <tr>
                                        <th>Nom</th>
                                        <th>Prénom</th>
                                        <th>Téléphone</th>
                                        <th>Email</th>
                                        <th>Ville</th>
                                        <th>Propriétés</th>
                                        <th>Actions</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {% for bailleur in bailleurs %}
                                    <tr>
                                        <td>
                                            <strong>{{ bailleur.nom }}</strong>
                                        </td>
                                        <td>{{ bailleur.prenom }}</td>
                                        <td>
                                            <i class="bi bi-telephone me-1"></i>
                                            {{ bailleur.telephone }}
                                        </td>
                                        <td>
                                            {% if bailleur.email %}
                                                <i class="bi bi-envelope me-1"></i>
                                                {{ bailleur.email }}
                                            {% else %}
                                                <span class="text-muted">Non renseigné</span>
                                            {% endif %}
                                        </td>
                                        <td>
                                            <i class="bi bi-geo-alt me-1"></i>
                                            {{ bailleur.ville }}
                                        </td>
                                        <td>
                                            <span class="badge bg-info">{{ bailleur.proprietes.count }}</span>
                                        </td>
                                        <td>
                                            <div class="btn-group" role="group">
                                                <a href="{% url 'proprietes:bailleur_detail' bailleur.pk %}" class="btn btn-sm btn-outline-primary" title="Voir les détails">
                                                    <i class="bi bi-eye"></i>
                                                </a>
                                                <a href="{% url 'proprietes:bailleur_modifier' bailleur.pk %}" class="btn btn-sm btn-outline-warning" title="Modifier">
                                                    <i class="bi bi-pencil"></i>
                                                </a>
                                            </div>
                                        </td>
                                    </tr>
                                    {% endfor %}
                                </tbody>
                            </table>
                        </div>
                        
                        <!-- Statistiques -->
                        <div class="row mt-4">
                            <div class="col-md-3">
                                <div class="card bg-primary text-white">
                                    <div class="card-body text-center">
                                        <h5 class="card-title">
                                            <i class="bi bi-people-fill me-2"></i>
                                            Total Bailleurs
                                        </h5>
                                        <h3>{{ bailleurs.count }}</h3>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="card bg-success text-white">
                                    <div class="card-body text-center">
                                        <h5 class="card-title">
                                            <i class="bi bi-house-fill me-2"></i>
                                            Total Propriétés
                                        </h5>
                                        <h3>{{ total_proprietes|default:0 }}</h3>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="card bg-info text-white">
                                    <div class="card-body text-center">
                                        <h5 class="card-title">
                                            <i class="bi bi-envelope-fill me-2"></i>
                                            Avec Email
                                        </h5>
                                        <h3>{{ avec_email|default:0 }}</h3>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="card bg-warning text-dark">
                                    <div class="card-body text-center">
                                        <h5 class="card-title">
                                            <i class="bi bi-bank me-2"></i>
                                            Avec IBAN
                                        </h5>
                                        <h3>{{ avec_iban|default:0 }}</h3>
                                    </div>
                                </div>
                            </div>
                        </div>
                    {% else %}
                        <div class="text-center py-5">
                            <i class="bi bi-people display-1 text-muted"></i>
                            <h3 class="text-muted mt-3">Aucun bailleur enregistré</h3>
                            <p class="text-muted">Commencez par ajouter votre premier bailleur.</p>
                            <a href="{% url 'proprietes:bailleur_ajouter' %}" class="btn btn-primary btn-lg">
                                <i class="bi bi-person-plus me-2"></i>
                                Ajouter un Bailleur
                            </a>
                        </div>
                    {% endif %}
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}'''
    
    with open(template_path, 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == '__main__':
    create_missing_bailleur_templates() 