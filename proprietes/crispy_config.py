"""
Configuration personnalisée pour Crispy Forms
Améliore l'affichage des champs obligatoires avec des étoiles rouges vives
"""

from crispy_forms.bootstrap import PrependedText, AppendedText
from crispy_forms.layout import Layout, Row, Column, HTML

# Configuration pour les champs obligatoires
REQUIRED_FIELD_TEMPLATE = """
<div class="form-group">
    <label for="{{ field.id_for_label }}" class="form-label {% if field.field.required %}required{% endif %}">
        {{ field.label }}
        {% if field.field.required %}
            <span class="asteriskField" style="color: #dc3545; font-weight: bold; font-size: 1.2em;">*</span>
        {% endif %}
    </label>
    {{ field }}
    {% if field.help_text %}
        <div class="form-text {% if field.field.required %}required{% endif %}">
            {{ field.help_text }}
        </div>
    {% endif %}
    {% if field.errors %}
        <div class="invalid-feedback d-block">
            {% for error in field.errors %}
                {{ error }}
            {% endfor %}
        </div>
    {% endif %}
</div>
"""

# Configuration pour les champs optionnels
OPTIONAL_FIELD_TEMPLATE = """
<div class="form-group">
    <label for="{{ field.id_for_label }}" class="form-label">
        {{ field.label }}
        <small class="text-muted">(Optionnel)</small>
    </label>
    {{ field }}
    {% if field.help_text %}
        <div class="form-text">
            {{ field.help_text }}
        </div>
    {% endif %}
    {% if field.errors %}
        <div class="invalid-feedback d-block">
            {% for error in field.errors %}
                {{ error }}
            {% endfor %}
        </div>
    {% endif %}
</div>
"""

# Layout personnalisé pour le formulaire de propriété
PROPRIETE_FORM_LAYOUT = Layout(
    Row(
        Column('numero_propriete', css_class='col-md-6'),
        Column('titre', css_class='col-md-6'),
        css_class='form-row'
    ),
    Row(
        Column('type_bien', css_class='col-md-6'),
        Column('bailleur', css_class='col-md-6'),
        css_class='form-row'
    ),
    Row(
        Column('etat', css_class='col-md-6'),
        css_class='form-row'
    ),
    HTML('<hr class="my-4">'),
    Row(
        Column('adresse', css_class='col-12'),
        css_class='form-row'
    ),
    Row(
        Column('code_postal', css_class='col-md-4'),
        Column('ville', css_class='col-md-4'),
        Column('pays', css_class='col-md-4'),
        css_class='form-row'
    ),
    HTML('<hr class="my-4">'),
    Row(
        Column('surface', css_class='col-md-6'),
        Column('nombre_pieces', css_class='col-md-6'),
        css_class='form-row'
    ),
    Row(
        Column('nombre_chambres', css_class='col-md-6'),
        Column('nombre_salles_bain', css_class='col-md-6'),
        css_class='form-row'
    ),
    HTML('<hr class="my-4">'),
    Row(
        Column('ascenseur', css_class='col-md-3'),
        Column('parking', css_class='col-md-3'),
        Column('balcon', css_class='col-md-3'),
        Column('jardin', css_class='col-md-3'),
        css_class='form-row'
    ),
    HTML('<hr class="my-4">'),
    Row(
        Column('prix_achat', css_class='col-md-6'),
        Column('loyer_actuel', css_class='col-md-6'),
        css_class='form-row'
    ),
    Row(
        Column('charges_locataire', css_class='col-md-6'),
        Column('disponible', css_class='col-md-6'),
        css_class='form-row'
    ),
    HTML('<hr class="my-4">'),
    Row(
        Column('notes', css_class='col-12'),
        css_class='form-row'
    ),
)
