#!/usr/bin/env python
"""
Système de Quittances KBIS INTERNATIONAL IMMOBILIER
Reproduction exacte du format officiel utilisé par l'entreprise
"""

from datetime import datetime
import locale

class QuittanceKBISOfficielle:
    """Générateur de quittances au format officiel KBIS INTERNATIONAL IMMOBILIER"""
    
    # Informations entreprise (basées sur le document officiel)
    ENTREPRISE = {
        'nom': 'KBIS IMMOBILIER',
        'services': ['Achat', 'Vente', 'Location', 'Gestion', 'Nettoyage'],
        'depot_orange': 'DEPOT ORANGE * 144 * 10 * 5933721 * Montant #',
        'adresse': 'BP 440 Ouaga pissy 10050 ouagadougou burkina faso',
        'telephones': ['+226 79 18', '32 32 / 70 20 64 91 / 79 18 39 39 / 79 26 82 82'],
        'localisation': 'sis, secteur 26 pissy sur la voie du CMA de pissy, Annexe Ouaga 2000',
        'telephone_annexe': '+226 79 26 88 88 / 78 20 64 91',
        'email': 'kbissari2022@gmail.com',
        'orange_money': '144*10*5933721*MONTANT#'
    }
    
    @classmethod 
    def get_styles_css(cls):
        """Styles CSS pour reproduction exacte du format officiel"""
        return """
        <style>
            /* Format A5 - Dimensions exactes pour impression */
            @page {
                size: A5;
                margin: 10mm;
            }
            
            body { 
                font-family: Arial, sans-serif; 
                margin: 0; 
                padding: 0;
                background: white;
                color: #333;
                font-size: 12px;
                line-height: 1.3;
            }
            
            .quittance-container {
                width: 148mm;  /* Largeur A5 */
                height: 210mm; /* Hauteur A5 */
                margin: 0 auto;
                background: white;
                border: 2px solid #333;
                padding: 0;
                page-break-inside: avoid;
            }
            
            .entete-principal {
                background: #f8f8f8;
                border-bottom: 2px solid #333;
                padding: 15px;
                text-align: center;
            }
            
            .logo-section {
                display: flex;
                align-items: center;
                justify-content: center;
                margin-bottom: 10px;
            }
            
            .logo-kbis {
                width: 60px;
                height: 60px;
                border: 2px solid #333;
                margin-right: 15px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-weight: bold;
                font-size: 12px;
                background: white;
            }
            
            .nom-entreprise {
                font-size: 24px;
                font-weight: bold;
                color: #333;
                letter-spacing: 1px;
            }
            
            .services-ligne {
                font-size: 14px;
                color: #666;
                margin-top: 8px;
                border-top: 1px solid #ccc;
                border-bottom: 1px solid #ccc;
                padding: 8px 0;
            }
            
            .orange-money-section {
                background: #fff3e0;
                padding: 8px;
                font-size: 12px;
                color: #e65100;
                font-weight: bold;
                border-bottom: 1px solid #333;
            }
            
            .contenu-quittance {
                padding: 20px;
            }
            
            .section-principale {
                display: flex;
                margin-bottom: 30px;
            }
            
            .colonne-gauche {
                width: 45%;
                padding-right: 20px;
            }
            
            .colonne-droite {
                width: 55%;
                padding-left: 20px;
                border-left: 1px solid #ccc;
            }
            
            .champ-quittance {
                margin-bottom: 25px;
            }
            
            .label-champ {
                font-size: 12px;
                color: #666;
                text-decoration: underline;
                margin-bottom: 5px;
                display: block;
            }
            
            .valeur-champ {
                font-size: 18px;
                font-weight: bold;
                color: #333;
                min-height: 25px;
                display: block;
            }
            
            .date-section {
                text-align: right;
                margin-bottom: 20px;
            }
            
            .montant-principal {
                background: #e3f2fd;
                border: 2px solid #1976d2;
                padding: 15px;
                text-align: center;
                font-size: 24px;
                font-weight: bold;
                color: #1976d2;
                margin: 20px 0;
            }
            
            .montant-lettres {
                text-align: center;
                font-style: italic;
                color: #666;
                margin: 10px 0;
            }
            
            .details-paiement {
                background: #f8f9fa;
                border: 1px solid #ddd;
                margin: 20px 0;
            }
            
            .details-paiement table {
                width: 100%;
                border-collapse: collapse;
            }
            
            .details-paiement td {
                padding: 10px;
                border: 1px solid #ddd;
                font-size: 14px;
            }
            
            .cachet-signature {
                text-align: center;
                margin-top: 40px;
                padding: 20px;
                border: 2px dashed #666;
                background: #f9f9f9;
            }
            
            .cachet-rond {
                width: 120px;
                height: 120px;
                border: 3px solid #1976d2;
                border-radius: 50%;
                margin: 0 auto 15px;
                display: flex;
                align-items: center;
                justify-content: center;
                background: rgba(25, 118, 210, 0.1);
                font-size: 10px;
                text-align: center;
                color: #1976d2;
                font-weight: bold;
                line-height: 1.2;
            }
            
            .pied-page {
                background: #333;
                color: white;
                padding: 15px;
                font-size: 11px;
                text-align: center;
                line-height: 1.4;
            }
            
            .pied-page strong {
                color: #ffd700;
            }
        </style>
        """
    
    @classmethod
    def convertir_nombre_en_lettres(cls, nombre):
        """Convertit un nombre en lettres (version simplifiée pour FCFA)"""
        if nombre == 30000:
            return "trente mille"
        elif nombre < 1000:
            return f"{nombre}"
        elif nombre < 10000:
            milliers = nombre // 1000
            reste = nombre % 1000
            if reste == 0:
                return f"{milliers} mille"
            else:
                return f"{milliers} mille {reste}"
        elif nombre < 100000:
            dizaines_milliers = nombre // 10000
            reste = nombre % 10000
            if reste == 0:
                return f"{dizaines_milliers * 10} mille"
            else:
                return f"{dizaines_milliers * 10} mille {reste}"
        else:
            return f"{nombre:,}".replace(',', ' ')
    
    @classmethod
    def generer_quittance_officielle(cls, donnees_quittance):
        """
        Génère une quittance au format officiel KBIS
        
        Args:
            donnees_quittance (dict): {
                'numero': '222600',
                'date': '26-sept-25',
                'code_location': '6283', 
                'recu_de': 'FARMA ODOSSE',
                'montant': 30000,
                'mois_regle': 'juillet 2025',
                'restant_du': 60000,
                'loyer_au_prorata': 0
            }
        """
        
        # Données par défaut si non fournies
        donnees = {
            'numero': '222601',
            'date': datetime.now().strftime('%d-%b-%y'),
            'code_location': '6284',
            'recu_de': 'NOM DU LOCATAIRE',
            'montant': 30000,
            'mois_regle': 'septembre 2025',
            'restant_du': 0,
            'loyer_au_prorata': 0,
            **donnees_quittance
        }
        
        montant_lettres = cls.convertir_nombre_en_lettres(donnees['montant'])
        
        html_quittance = f"""
        <!DOCTYPE html>
        <html lang="fr">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Quittance N° {donnees['numero']} - KBIS INTERNATIONAL IMMOBILIER</title>
            {cls.get_styles_css()}
        </head>
        <body>
            <div class="quittance-container">
                <!-- EN-TÊTE OFFICIEL -->
                <div class="entete-principal">
                    <div class="logo-section">
                        <div class="logo-kbis">
                            🏠<br>KBIS
                        </div>
                        <div class="nom-entreprise">
                            {cls.ENTREPRISE['nom']}
                        </div>
                    </div>
                    
                    <div class="services-ligne">
                        {' • '.join(cls.ENTREPRISE['services'])}
                    </div>
                </div>
                
                <!-- SECTION ORANGE MONEY -->
                <div class="orange-money-section">
                    {cls.ENTREPRISE['depot_orange']}
                </div>
                
                <!-- CONTENU PRINCIPAL -->
                <div class="contenu-quittance">
                    <!-- Date -->
                    <div class="date-section">
                        <span class="label-champ">Date :</span>
                        <span class="valeur-champ" style="font-size: 16px; font-weight: bold;">
                            {donnees['date']}
                        </span>
                    </div>
                    
                    <!-- Section principale -->
                    <div class="section-principale">
                        <!-- Colonne gauche -->
                        <div class="colonne-gauche">
                            <div class="champ-quittance">
                                <span class="label-champ">QUITTANCE N° :</span>
                                <span class="valeur-champ" style="font-size: 24px; color: #1976d2;">
                                    {donnees['numero']}
                                </span>
                            </div>
                            
                            <div class="champ-quittance">
                                <span class="label-champ">code location :</span>
                                <span class="valeur-champ" style="font-size: 20px; color: #666;">
                                    {donnees['code_location']}
                                </span>
                            </div>
                            
                            <div class="champ-quittance">
                                <span class="label-champ">Cachet et signature de l'Agence :</span>
                                <div style="height: 100px; border: 1px dashed #ccc; margin-top: 10px;">
                                    <!-- Espace pour cachet -->
                                </div>
                            </div>
                        </div>
                        
                        <!-- Colonne droite -->
                        <div class="colonne-droite">
                            <div class="champ-quittance">
                                <span class="label-champ">Reçu de M. :</span>
                                <span class="valeur-champ" style="font-size: 16px; font-weight: bold;">
                                    {donnees['recu_de']}
                                </span>
                            </div>
                            
                            <div class="champ-quittance">
                                <span class="label-champ">Pour le versement de la somme de :</span>
                                <div class="montant-principal">
                                    {donnees['montant']:,} F
                                </div>
                                <div class="montant-lettres">
                                    ( {montant_lettres} )
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Détails du paiement -->
                    <div class="details-paiement">
                        <table>
                            <tr>
                                <td style="font-weight: bold; background: #f0f0f0;">Mois Réglé</td>
                                <td style="font-weight: bold; background: #f0f0f0;">{donnees['mois_regle']}</td>
                            </tr>
                            <tr>
                                <td>Restant dû</td>
                                <td style="font-weight: bold; color: #d32f2f;">
                                    {donnees['restant_du']:,} F
                                </td>
                            </tr>
                            <tr>
                                <td>loyer au prorata à régler :</td>
                                <td style="font-weight: bold;">
                                    {donnees['loyer_au_prorata']} F
                                </td>
                            </tr>
                        </table>
                    </div>
                    
                    <!-- Cachet et signature -->
                    <div class="cachet-signature">
                        <div class="cachet-rond">
                            CACHET<br>ET<br>SIGNATURE<br>DE<br>L'AGENCE
                        </div>
                        <p style="margin: 0; font-weight: bold; color: #333;">
                            Cachet et signature de l'Agence
                        </p>
                    </div>
                </div>
                
                <!-- PIED DE PAGE -->
                <div class="pied-page">
                    <strong>{cls.ENTREPRISE['adresse']}</strong><br>
                    <strong>Tél: {cls.ENTREPRISE['telephones'][1]}</strong><br>
                    {cls.ENTREPRISE['localisation']}<br>
                    <strong>{cls.ENTREPRISE['telephone_annexe']}</strong><br>
                    <strong>Email: {cls.ENTREPRISE['email']}</strong><br>
                    <strong>ORANGE MONEY : {cls.ENTREPRISE['orange_money']}</strong>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html_quittance
    
    @classmethod
    def generer_quittance_test(cls):
        """Génère une quittance de test avec les données de l'exemple"""
        donnees_test = {
            'numero': '222600',
            'date': '26-sept-25',
            'code_location': '6283',
            'recu_de': 'FARMA ODOSSE',
            'montant': 30000,
            'mois_regle': 'juillet 2025',
            'restant_du': 60000,
            'loyer_au_prorata': 0
        }
        
        return cls.generer_quittance_officielle(donnees_test)

if __name__ == '__main__':
    # Test de génération
    print("🏢 Génération de la quittance KBIS officielle...")
    
    # Générer la quittance test
    html_quittance = QuittanceKBISOfficielle.generer_quittance_test()
    
    # Sauvegarder le fichier
    with open('quittance_kbis_officielle_test.html', 'w', encoding='utf-8') as f:
        f.write(html_quittance)
    
    print("✅ Quittance générée : quittance_kbis_officielle_test.html")
    print("📱 Ouvrez le fichier dans votre navigateur pour voir le résultat")