"""
Système unifié de génération de documents KBIS IMMOBILIER
Génère des récépissés, quittances et autres documents avec en-tête image statique et pied de page dynamique
"""

import os
from datetime import datetime


class DocumentKBISUnifie:
    """Classe unifiée pour la génération de documents KBIS"""
    
    @staticmethod
    def generer_document_unifie(donnees, type_document='recu'):
        """
        Génère un document unifié avec en-tête image statique et pied de page dynamique
        
        Args:
            donnees (dict): Données du document
            type_document (str): Type de document ('recu', 'quittance', etc.)
        
        Returns:
            str: HTML du document généré
        """
        try:
            # Template HTML avec en-tête image statique et pied de page dynamique
            html_template = """
            <!DOCTYPE html>
            <html lang="fr">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>{{ titre_document }} - {{ numero }}</title>
                <style>
                    @page {
                        size: A5;
                        margin: 0.5cm;
                    }
                    
                    body {
                        font-family: 'Arial', sans-serif;
                        margin: 0;
                        padding: 0;
                        font-size: 12px;
                        line-height: 1.4;
                        color: #333;
                    }
                    
                    .document-container {
                        width: 100%;
                        max-width: 100%;
                        margin: 0 auto;
                        background: white;
                    }
                    
                    /* EN-TÊTE AVEC IMAGE STATIQUE */
                    .header {
                        width: 100%;
                        text-align: center;
                        margin-bottom: 15px;
                        border-bottom: 2px solid #007bff;
                        padding-bottom: 10px;
                    }
                    
                    .header-image {
                        width: 100%;
                        max-width: 200px;
                        height: auto;
                        margin-bottom: 10px;
                    }
                    
                    .header-title {
                        font-size: 18px;
                        font-weight: bold;
                        color: #007bff;
                        margin: 5px 0;
                    }
                    
                    .header-subtitle {
                        font-size: 14px;
                        color: #666;
                        margin: 0;
                    }
                    
                    /* CONTENU PRINCIPAL */
                    .content {
                        padding: 10px 0;
                    }
                    
                    .info-section {
                        margin-bottom: 15px;
                    }
                    
                    .info-section h3 {
                        font-size: 14px;
                        color: #333;
                        border-bottom: 1px solid #007bff;
                        padding-bottom: 3px;
                        margin-bottom: 8px;
                    }
                    
                    .info-grid {
                        display: table;
                        width: 100%;
                    }
                    
                    .info-row {
                        display: table-row;
                    }
                    
                    .info-label {
                        display: table-cell;
                        font-weight: bold;
                        padding: 2px 10px 2px 0;
                        width: 40%;
                        vertical-align: top;
                    }
                    
                    .info-value {
                        display: table-cell;
                        padding: 2px 0;
                        width: 60%;
                    }
                    
                    .amount-section {
                        background: #f8f9fa;
                        border: 2px solid #28a745;
                        border-radius: 5px;
                        padding: 15px;
                        text-align: center;
                        margin: 15px 0;
                    }
                    
                    .amount-label {
                        font-size: 14px;
                        font-weight: bold;
                        color: #333;
                        margin-bottom: 5px;
                    }
                    
                    .amount-value {
                        font-size: 24px;
                        font-weight: bold;
                        color: #28a745;
                        margin: 0;
                    }
                    
                    /* PIED DE PAGE DYNAMIQUE */
                    .footer {
                        margin-top: 20px;
                        padding-top: 10px;
                        border-top: 2px solid #007bff;
                        text-align: center;
                        font-size: 10px;
                        color: #666;
                    }
                    
                    .signature-section {
                        display: table;
                        width: 100%;
                        margin-top: 20px;
                    }
                    
                    .signature-left, .signature-right {
                        display: table-cell;
                        width: 50%;
                        text-align: center;
                        padding: 20px 10px 0 10px;
                    }
                    
                    .signature-line {
                        border-top: 1px solid #333;
                        margin-top: 30px;
                        padding-top: 5px;
                    }
                    
                    .signature-label {
                        font-weight: bold;
                        font-size: 11px;
                    }
                    
                    /* RESPONSIVE */
                    @media print {
                        body { margin: 0; }
                        .document-container { box-shadow: none; }
                    }
                </style>
            </head>
            <body>
                <div class="document-container">
                    <!-- EN-TÊTE AVEC IMAGE STATIQUE -->
                    <div class="header">
                        <img src="{{ image_entete }}" alt="GESTIMMOB" class="header-image" onerror="this.style.display='none'">
                        <h1 class="header-title">{{ titre_document }}</h1>
                        <p class="header-subtitle">GESTIMMOB - Gestion Immobilière Professionnelle</p>
                    </div>
                    
                    <!-- CONTENU PRINCIPAL -->
                    <div class="content">
                        <!-- Informations du document -->
                        <div class="info-section">
                            <h3>Informations du Document</h3>
                            <div class="info-grid">
                                <div class="info-row">
                                    <span class="info-label">Numéro:</span>
                                    <span class="info-value">{{ numero }}</span>
                                </div>
                                <div class="info-row">
                                    <span class="info-label">Date:</span>
                                    <span class="info-value">{{ date }}</span>
                                </div>
                                <div class="info-row">
                                    <span class="info-label">Type:</span>
                                    <span class="info-value">{{ type_paiement }}</span>
                                </div>
                                <div class="info-row">
                                    <span class="info-label">Mode:</span>
                                    <span class="info-value">{{ mode_paiement }}</span>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Informations du contrat -->
                        <div class="info-section">
                            <h3>Informations du Contrat</h3>
                            <div class="info-grid">
                                <div class="info-row">
                                    <span class="info-label">Contrat:</span>
                                    <span class="info-value">{{ code_location }}</span>
                                </div>
                                <div class="info-row">
                                    <span class="info-label">Locataire:</span>
                                    <span class="info-value">{{ recu_de }}</span>
                                </div>
                                <div class="info-row">
                                    <span class="info-label">Adresse:</span>
                                    <span class="info-value">{{ quartier }}</span>
                                </div>
                                <div class="info-row">
                                    <span class="info-label">Période:</span>
                                    <span class="info-value">{{ mois_regle }}</span>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Montant -->
                        <div class="amount-section">
                            <div class="amount-label">Montant Reçu</div>
                            <div class="amount-value">{{ montant|floatformat:0 }} F CFA</div>
                        </div>
                        
                        <!-- Données spécialisées selon le type -->
                        {% if donnees_speciales %}
                        <div class="info-section">
                            <h3>Détails Spécifiques</h3>
                            <div class="info-grid">
                                {% for key, value in donnees_speciales.items %}
                                <div class="info-row">
                                    <span class="info-label">{{ key|title }}:</span>
                                    <span class="info-value">{{ value }}</span>
                                </div>
                                {% endfor %}
                            </div>
                        </div>
                        {% endif %}
                    </div>
                    
                    <!-- SIGNATURES -->
                    <div class="signature-section">
                        <div class="signature-left">
                            <div class="signature-line">
                                <div class="signature-label">Reçu par</div>
                            </div>
                        </div>
                        <div class="signature-right">
                            <div class="signature-line">
                                <div class="signature-label">Payé par</div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- PIED DE PAGE DYNAMIQUE -->
                    <div class="footer">
                        <p><strong>GESTIMMOB</strong> - Gestion Immobilière Professionnelle</p>
                        <p>Ce document certifie que le paiement ci-dessus a été reçu en bonne et due forme.</p>
                        <p>Généré le {{ date_generation }} - Document {{ numero }}</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Préparer les données pour le template
            donnees_template = {
                'titre_document': DocumentKBISUnifie._get_titre_document(type_document),
                'image_entete': DocumentKBISUnifie._get_image_entete(),
                'numero': donnees.get('numero', 'N/A'),
                'date': donnees.get('date', datetime.now().strftime('%d/%m/%Y')),
                'code_location': donnees.get('code_location', 'N/A'),
                'recu_de': donnees.get('recu_de', 'LOCATAIRE'),
                'montant': donnees.get('montant', 0),
                'mois_regle': donnees.get('mois_regle', 'N/A'),
                'type_paiement': donnees.get('type_paiement', 'N/A'),
                'mode_paiement': donnees.get('mode_paiement', 'N/A'),
                'quartier': donnees.get('quartier', 'Non spécifié'),
                'donnees_speciales': DocumentKBISUnifie._extraire_donnees_speciales(donnees),
                'date_generation': datetime.now().strftime('%d/%m/%Y à %H:%M'),
            }
            
            # Remplacer les variables dans le template
            html_final = html_template
            for key, value in donnees_template.items():
                if key == 'donnees_speciales':
                    # Gérer les données spéciales
                    if value:
                        speciales_html = ""
                        for k, v in value.items():
                            speciales_html += f'<div class="info-row"><span class="info-label">{k.replace("_", " ").title()}:</span><span class="info-value">{v}</span></div>'
                        # Remplacer la section conditionnelle des données spéciales
                        html_final = html_final.replace('{% if donnees_speciales %}\n                        <div class="info-section">\n                            <h3>Détails Spécifiques</h3>\n                            <div class="info-grid">\n                                {% for key, value in donnees_speciales.items %}\n                                <div class="info-row">\n                                    <span class="info-label">{{ key|title }}:</span>\n                                    <span class="info-value">{{ value }}</span>\n                                </div>\n                                {% endfor %}\n                            </div>\n                        </div>\n                        {% endif %}', 
                        f'<div class="info-section"><h3>Détails Spécifiques</h3><div class="info-grid">{speciales_html}</div></div>' if speciales_html else '')
                    else:
                        # Supprimer la section si pas de données spéciales
                        html_final = html_final.replace('{% if donnees_speciales %}\n                        <div class="info-section">\n                            <h3>Détails Spécifiques</h3>\n                            <div class="info-grid">\n                                {% for key, value in donnees_speciales.items %}\n                                <div class="info-row">\n                                    <span class="info-label">{{ key|title }}:</span>\n                                    <span class="info-value">{{ value }}</span>\n                                </div>\n                                {% endfor %}\n                            </div>\n                        </div>\n                        {% endif %}', '')
                else:
                    # Remplacer les variables simples
                    html_final = html_final.replace('{{ ' + key + ' }}', str(value))
                    # Gérer les filtres Django
                    if '|floatformat:0' in html_final:
                        html_final = html_final.replace('{{ ' + key + '|floatformat:0 }}', f"{float(value):.0f}")
                    if '|title' in html_final:
                        html_final = html_final.replace('{{ ' + key + '|title }}', str(value).title())
            
            return html_final
            
        except Exception as e:
            print(f"Erreur génération document KBIS: {e}")
            return None
    
    @staticmethod
    def _get_titre_document(type_document):
        """Retourne le titre selon le type de document"""
        titres = {
            'recu': 'RÉCÉPISSÉ DE PAIEMENT',
            'recu_loyer': 'RÉCÉPISSÉ DE LOYER',
            'recu_caution': 'RÉCÉPISSÉ DE CAUTION',
            'recu_avance': 'RÉCÉPISSÉ D\'AVANCE',
            'recu_charges': 'RÉCÉPISSÉ DE CHARGES',
            'quittance': 'QUITTANCE DE PAIEMENT',
            'quittance_loyer': 'QUITTANCE DE LOYER',
        }
        return titres.get(type_document, 'RÉCÉPISSÉ DE PAIEMENT')
    
    @staticmethod
    def _get_image_entete():
        """Retourne le chemin vers l'image d'en-tête statique"""
        # Chemin vers l'image d'en-tête statique
        return "/static/images/logo_gestimmob.png"
    
    @staticmethod
    def _extraire_donnees_speciales(donnees):
        """Extrait les données spéciales du dictionnaire principal"""
        speciales = {}
        for key, value in donnees.items():
            if key not in ['numero', 'date', 'code_location', 'recu_de', 'montant', 
                          'mois_regle', 'type_paiement', 'mode_paiement', 'quartier']:
                speciales[key] = value
        return speciales
