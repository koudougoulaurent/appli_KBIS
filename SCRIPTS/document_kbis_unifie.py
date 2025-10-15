#!/usr/bin/env python
"""
Système unifié de génération de documents KBIS Immobilier
Génère les quittances, récépissés et autres documents avec un format cohérent
"""

import os
import sys
from datetime import datetime
from decimal import Decimal


class DocumentKBISUnifie:
    """Classe unifiée pour la génération de tous les documents KBIS"""
    
    @staticmethod
    def generer_document_unifie(donnees, type_document):
        """
        Génère un document unifié selon le type spécifié
        
        Args:
            donnees (dict): Données du document
            type_document (str): Type de document (quittance_loyer, quittance_caution, etc.)
        
        Returns:
            str: HTML du document généré
        """
        try:
            # Déterminer le template selon le type
            template_html = DocumentKBISUnifie._get_template_document(type_document)
            
            # Remplacer les variables dans le template
            html_final = DocumentKBISUnifie._remplacer_variables(template_html, donnees)
            
            return html_final
            
        except Exception as e:
            print(f"Erreur génération document unifié: {e}")
            return None
    
    @staticmethod
    def _get_template_document(type_document):
        """Retourne le template HTML selon le type de document"""
        
        # Template de base pour les quittances
        if 'quittance' in type_document:
            return DocumentKBISUnifie._get_template_quittance(type_document)
        
        # Template de base pour les récépissés
        elif 'recu' in type_document:
            return DocumentKBISUnifie._get_template_recu(type_document)
        
        # Template par défaut
        else:
            return DocumentKBISUnifie._get_template_quittance('quittance')
    
    @staticmethod
    def _get_template_quittance(type_quittance):
        """Template pour les quittances"""
        return """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>QUITTANCE KBIS IMMOBILIER</title>
    <style>
        body {
            font-family: 'Arial', sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f8f9fa;
            color: #333;
        }
        .document-container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            padding: 20px; /* Reduced padding */
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .header {
            text-align: center;
            margin: 0 auto 20px auto; /* Centered with auto margins */
            border-bottom: 2px solid #2c3e50;
            padding: 5px 0; /* Reduced padding */
            width: 100%;
            max-width: 100%; /* Ensure full width usage */
        }
        .header-image {
            width: 100%;
            height: auto;
            max-height: 100px;
            display: block;
            margin: 0 auto 10px auto; /* Centered */
            object-fit: contain; /* Keep aspect ratio without cropping */
        }
        .document-title {
            background: linear-gradient(135deg, #007bff, #0056b3);
            color: white;
            padding: 15px;
            text-align: center;
            font-size: 18px;
            font-weight: bold;
            margin: 20px 0;
            border-radius: 5px;
        }
        .document-info {
            display: flex;
            justify-content: space-between;
            margin-bottom: 30px;
        }
        .info-left, .info-right {
            flex: 1;
        }
        .info-item {
            margin-bottom: 10px;
        }
        .info-label {
            font-weight: bold;
            color: #555;
        }
        .amount-box {
            background: #e3f2fd;
            border: 2px solid #2196f3;
            padding: 20px;
            text-align: center;
            border-radius: 8px;
            margin: 20px 0;
        }
        .amount-value {
            font-size: 28px;
            font-weight: bold;
            color: #1976d2;
            margin-bottom: 10px;
        }
        .amount-words {
            font-size: 16px;
            color: #555;
        }
        .payment-details {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }
        .detail-row {
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid #dee2e6;
        }
        .detail-row:last-child {
            border-bottom: none;
        }
        .detail-label {
            font-weight: bold;
            color: #495057;
        }
        .detail-value {
            color: #6c757d;
        }
        .highlight {
            background: #d4edda;
            color: #155724;
            padding: 2px 6px;
            border-radius: 3px;
            font-weight: bold;
        }
        .signature-area {
            margin-top: 40px;
            text-align: center;
        }
        .signature-box {
            border: 2px dashed #ccc;
            height: 80px;
            margin: 20px 0;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #666;
        }
        .footer {
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #dee2e6;
            font-size: 12px;
            color: #6c757d;
            text-align: center;
        }
        .contact-info {
            display: flex;
            justify-content: space-around;
            margin-top: 15px;
        }
        .contact-item {
            text-align: center;
        }
        .contact-label {
            font-weight: bold;
            color: #495057;
        }
    </style>
</head>
<body>
    <div class="document-container">
        <!-- En-tête -->
        <div class="header">
            {image_header}
        </div>
        
        <!-- Titre du document -->
        <div class="document-title">
            {document_title} N° {numero}
        </div>
        
        <!-- Informations du document -->
        <div class="document-info">
            <div class="info-left">
                <div class="info-item">
                    <span class="info-label">Date :</span> {date}
                </div>
                <div class="info-item">
                    <span class="info-label">Code location :</span> {code_location}
                </div>
                <div class="info-item">
                    <span class="info-label">Reçu de :</span> {recu_de}
                </div>
            </div>
            <div class="info-right">
                <div class="info-item">
                    <span class="info-label">Mois réglé :</span> {mois_regle}
                </div>
                <div class="info-item">
                    <span class="info-label">Type :</span> {type_paiement}
                </div>
                <div class="info-item">
                    <span class="info-label">Mode :</span> {mode_paiement}
                </div>
            </div>
        </div>
        
        <!-- Montant principal -->
        <div class="amount-box">
            <div class="amount-value">{montant} F CFA</div>
            <div class="amount-words">{montant_words}</div>
        </div>
        
        <!-- Détails du paiement -->
        <div class="payment-details">
            {payment_details}
        </div>
        
        <!-- Zone de signature -->
        <div class="signature-area">
            <div class="signature-box">
                Cachet et signature de l'Agence
            </div>
        </div>
        
        <!-- Pied de page -->
        <div class="footer">
            <div><strong>KBIS Immobilier & Construction</strong></div>
            <div class="contact-info">
                <div class="contact-item">
                    <div class="contact-label">Adresse</div>
                    <div>Pissy 10050 Ouagadougou, Burkina Faso</div>
                    <div>Quartier Centre-Ville, BP 440 Ouagadougou</div>
                </div>
                <div class="contact-item">
                    <div class="contact-label">Téléphone</div>
                    <div>+226 70 20 54 91</div>
                    <div>79183939</div>
                </div>
                <div class="contact-item">
                    <div class="contact-label">Email</div>
                    <div>kbissarl2022@gmail.com</div>
                    <div>Web: https://omnicom-bf.com/</div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
        """
    
    @staticmethod
    def _get_template_recu(type_recu):
        """Template pour les récépissés"""
        return """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RÉCÉPISSÉ KBIS IMMOBILIER</title>
    <style>
        body {
            font-family: 'Arial', sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f8f9fa;
            color: #333;
        }
        .document-container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            padding: 20px; /* Reduced padding */
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
            border-bottom: 3px solid #28a745;
            padding-bottom: 20px;
        }
        .logo {
            font-size: 24px;
            font-weight: bold;
            color: #28a745;
            margin-bottom: 10px;
        }
        .company-name {
            font-size: 20px;
            color: #333;
            margin-bottom: 5px;
        }
        .company-tagline {
            font-size: 14px;
            color: #666;
        }
        .document-title {
            background: linear-gradient(135deg, #28a745, #1e7e34);
            color: white;
            padding: 15px;
            text-align: center;
            font-size: 18px;
            font-weight: bold;
            margin: 20px 0;
            border-radius: 5px;
        }
        .document-info {
            display: flex;
            justify-content: space-between;
            margin-bottom: 30px;
        }
        .info-left, .info-right {
            flex: 1;
        }
        .info-item {
            margin-bottom: 10px;
        }
        .info-label {
            font-weight: bold;
            color: #555;
        }
        .amount-box {
            background: #e8f5e8;
            border: 2px solid #28a745;
            padding: 20px;
            text-align: center;
            border-radius: 8px;
            margin: 20px 0;
        }
        .amount-value {
            font-size: 28px;
            font-weight: bold;
            color: #155724;
            margin-bottom: 10px;
        }
        .amount-words {
            font-size: 16px;
            color: #555;
        }
        .payment-details {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }
        .detail-row {
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid #dee2e6;
        }
        .detail-row:last-child {
            border-bottom: none;
        }
        .detail-label {
            font-weight: bold;
            color: #495057;
        }
        .detail-value {
            color: #6c757d;
        }
        .highlight {
            background: #d4edda;
            color: #155724;
            padding: 2px 6px;
            border-radius: 3px;
            font-weight: bold;
        }
        .signature-area {
            margin-top: 40px;
            text-align: center;
        }
        .signature-box {
            border: 2px dashed #ccc;
            height: 80px;
            margin: 20px 0;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #666;
        }
        .footer {
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #dee2e6;
            font-size: 12px;
            color: #6c757d;
            text-align: center;
        }
        .contact-info {
            display: flex;
            justify-content: space-around;
            margin-top: 15px;
        }
        .contact-item {
            text-align: center;
        }
        .contact-label {
            font-weight: bold;
            color: #495057;
        }
    </style>
</head>
<body>
    <div class="document-container">
        <!-- En-tête -->
        <div class="header">
            {image_header}
        </div>
        
        <!-- Titre du document -->
        <div class="document-title">
            {document_title} N° {numero}
        </div>
        
        <!-- Informations du document -->
        <div class="document-info">
            <div class="info-left">
                <div class="info-item">
                    <span class="info-label">Date :</span> {date}
                </div>
                <div class="info-item">
                    <span class="info-label">Code location :</span> {code_location}
                </div>
                <div class="info-item">
                    <span class="info-label">Reçu de :</span> {recu_de}
                </div>
            </div>
            <div class="info-right">
                <div class="info-item">
                    <span class="info-label">Mois réglé :</span> {mois_regle}
                </div>
                <div class="info-item">
                    <span class="info-label">Type :</span> {type_paiement}
                </div>
                <div class="info-item">
                    <span class="info-label">Mode :</span> {mode_paiement}
                </div>
            </div>
        </div>
        
        <!-- Montant principal -->
        <div class="amount-box">
            <div class="amount-value">{montant} F CFA</div>
            <div class="amount-words">{montant_words}</div>
        </div>
        
        <!-- Détails du paiement -->
        <div class="payment-details">
            {payment_details}
        </div>
        
        <!-- Zone de signature -->
        <div class="signature-area">
            <div class="signature-box">
                Cachet et signature de l'Agence
            </div>
        </div>
        
        <!-- Pied de page -->
        <div class="footer">
            <div><strong>KBIS Immobilier & Construction</strong></div>
            <div class="contact-info">
                <div class="contact-item">
                    <div class="contact-label">Adresse</div>
                    <div>Pissy 10050 Ouagadougou, Burkina Faso</div>
                    <div>Quartier Centre-Ville, BP 440 Ouagadougou</div>
                </div>
                <div class="contact-item">
                    <div class="contact-label">Téléphone</div>
                    <div>+226 70 20 54 91</div>
                    <div>79183939</div>
                </div>
                <div class="contact-item">
                    <div class="contact-label">Email</div>
                    <div>kbissarl2022@gmail.com</div>
                    <div>Web: https://omnicom-bf.com/</div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
        """
    
    @staticmethod
    def _remplacer_variables(template, donnees):
        """Remplace les variables dans le template avec les données fournies"""
        try:
            # Convertir l'image en base64
            image_base64 = DocumentKBISUnifie._get_image_base64()
            
            # Générer l'en-tête avec ou sans image
            if image_base64:
                image_header = f'''
                <div style="width: 100%; text-align: center; margin-bottom: 10px;">
                    <img src="{image_base64}" alt="KBIS Immobilier & Construction" class="header-image" style="width: 100%; max-width: 100%; height: auto; max-height: 100px; object-fit: contain;">
                </div>
                '''
            else:
                image_header = '''
                <div class="logo">🏠 KBIS</div>
                <div class="company-name">KBIS Immobilier & Construction</div>
                <div class="company-tagline">Achat & Vente • Location • Gestion • Nettoyage</div>
                '''
            
            # Variables de base
            variables = {
                'document_title': DocumentKBISUnifie._get_document_title(donnees.get('type_paiement', '')),
                'numero': donnees.get('numero', 'N/A'),
                'date': donnees.get('date', datetime.now().strftime('%d-%b-%y')),
                'code_location': donnees.get('code_location', 'N/A'),
                'recu_de': donnees.get('recu_de', 'N/A'),
                'mois_regle': donnees.get('mois_regle', 'N/A'),
                'type_paiement': donnees.get('type_paiement', 'N/A'),
                'mode_paiement': donnees.get('mode_paiement', 'N/A'),
                'montant': f"{donnees.get('montant', 0):,.2f}".replace(',', ' '),
                'montant_words': DocumentKBISUnifie._convertir_montant_en_mots(donnees.get('montant', 0)),
                'payment_details': DocumentKBISUnifie._generer_details_paiement(donnees),
                'image_header': image_header,
            }
            
            # Remplacer les variables dans le template
            html_final = template
            for key, value in variables.items():
                html_final = html_final.replace(f'{{{key}}}', str(value))
            
            return html_final
            
        except Exception as e:
            print(f"Erreur remplacement variables: {e}")
            return template
    
    @staticmethod
    def _get_document_title(type_paiement):
        """Retourne le titre du document selon le type de paiement"""
        titles = {
            'loyer': 'QUITTANCE DE LOYER',
            'caution': 'QUITTANCE DE CAUTION',
            'avance': 'QUITTANCE D\'AVANCE',
            'charges': 'QUITTANCE DE CHARGES',
            'depot_garantie': 'QUITTANCE DE DÉPÔT DE GARANTIE',
            'avance_loyer': 'QUITTANCE D\'AVANCE DE LOYER',
        }
        return titles.get(type_paiement, 'QUITTANCE DE PAIEMENT')
    
    @staticmethod
    def _convertir_montant_en_mots(montant):
        """Convertit un montant en mots (version simplifiée)"""
        try:
            montant_int = int(float(montant))
            return f"{montant_int} francs CFA"
        except:
            return "Montant en francs CFA"
    
    @staticmethod
    def _generer_details_paiement(donnees):
        """Génère les détails du paiement selon le type"""
        details = []
        
        # Détails de base
        details.append(f'<div class="detail-row"><span class="detail-label">Type de paiement :</span> <span class="detail-value highlight">{donnees.get("type_paiement", "N/A")} - {donnees.get("montant", 0):,.2f} F CFA</span></div>')
        details.append(f'<div class="detail-row"><span class="detail-label">Mode de paiement :</span> <span class="detail-value">{donnees.get("mode_paiement", "N/A")}</span></div>')
        
        # Détails spécialisés selon le type
        type_paiement = donnees.get('type_paiement', '')
        
        if 'caution' in type_paiement or 'depot_garantie' in type_paiement:
            details.append(f'<div class="detail-row"><span class="detail-label">Montant de la caution :</span> <span class="detail-value">{donnees.get("montant", 0):,.2f} F CFA</span></div>')
            details.append(f'<div class="detail-row"><span class="detail-label">Note :</span> <span class="detail-value highlight">Dépôt de garantie - Remboursable en fin de bail</span></div>')
        
        elif 'avance' in type_paiement:
            details.append(f'<div class="detail-row"><span class="detail-label">Montant de l\'avance :</span> <span class="detail-value">{donnees.get("montant", 0):,.2f} F CFA</span></div>')
            if donnees.get('mois_couverts', 0) > 0:
                details.append(f'<div class="detail-row"><span class="detail-label">Mois couverts :</span> <span class="detail-value">{donnees.get("mois_couverts", 0)} mois</span></div>')
            if donnees.get('note_speciale'):
                details.append(f'<div class="detail-row"><span class="detail-label">Note :</span> <span class="detail-value highlight">{donnees.get("note_speciale", "")}</span></div>')
        
        elif 'loyer' in type_paiement:
            details.append(f'<div class="detail-row"><span class="detail-label">Loyer mensuel :</span> <span class="detail-value">{donnees.get("loyer_base", donnees.get("montant", 0)):,.2f} F CFA</span></div>')
            if donnees.get('charges_mensuelles', 0) > 0:
                details.append(f'<div class="detail-row"><span class="detail-label">Charges mensuelles :</span> <span class="detail-value">{donnees.get("charges_mensuelles", 0):,.2f} F CFA</span></div>')
            details.append(f'<div class="detail-row"><span class="detail-label">Total mensuel :</span> <span class="detail-value">{donnees.get("total_mensuel", donnees.get("montant", 0)):,.2f} F CFA</span></div>')
        
        return ''.join(details)
    
    @staticmethod
    def _get_image_base64():
        """Convertit l'image d'en-tête en base64"""
        try:
            import os
            import base64
            
            # Chercher l'image dans différents emplacements
            image_paths = [
                'static/images/enteteEnImage.png',
                'staticfiles/images/enteteEnImage.png',
                os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'static', 'images', 'enteteEnImage.png'),
                os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'staticfiles', 'images', 'enteteEnImage.png'),
            ]
            
            for image_path in image_paths:
                if os.path.exists(image_path):
                    with open(image_path, 'rb') as img_file:
                        image_data = base64.b64encode(img_file.read()).decode('utf-8')
                        return f"data:image/png;base64,{image_data}"
            
            # Si aucune image trouvée, retourner None
            return None
            
        except Exception as e:
            print(f"Erreur conversion image base64: {e}")
            return None


# Test de la classe
if __name__ == "__main__":
    # Test avec des données d'exemple
    donnees_test = {
        'numero': 'QUI-20250101120000-TEST',
        'date': '01-Jan-25',
        'code_location': 'CTN012',
        'recu_de': 'Test Locataire',
        'mois_regle': 'janvier 2025',
        'type_paiement': 'caution',
        'mode_paiement': 'Espèces',
        'montant': 300000.00,
    }
    
    html = DocumentKBISUnifie.generer_document_unifie(donnees_test, 'quittance_caution')
    if html:
        print("Document généré avec succès!")
        # Sauvegarder pour test
        with open('test_document.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print("Document sauvegardé dans test_document.html")
    else:
        print("Erreur lors de la génération du document")
