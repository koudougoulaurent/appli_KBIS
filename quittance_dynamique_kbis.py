#!/usr/bin/env python
"""
Système de Quittances Dynamiques KBIS IMMOBILIER
Génération avec données réelles et format A5
"""

from datetime import datetime, timedelta
import random
import json
import os

class GestionnaireQuittancesDynamiques:
    """Gestionnaire de quittances avec données dynamiques réelles"""
    
    # Fichier de stockage des données
    FICHIER_DONNEES = 'donnees_quittances.json'
    
    # Informations entreprise actualisées
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
    
    # Base de données de locataires réels (exemples africains)
    LOCATAIRES_REELS = [
        {'nom': 'M. OUEDRAOGO ISSOUF', 'code': '6001', 'loyer': 45000, 'quartier': 'Pissy'},
        {'nom': 'Mme SAWADOGO FATIMA', 'code': '6002', 'loyer': 35000, 'quartier': 'Ouaga 2000'},
        {'nom': 'M. KONE IBRAHIM', 'code': '6003', 'loyer': 60000, 'quartier': 'Zone du Bois'},
        {'nom': 'Mme TRAORE AMINATA', 'code': '6004', 'loyer': 40000, 'quartier': 'Secteur 15'},
        {'nom': 'M. COMPAORE MOUSSA', 'code': '6005', 'loyer': 55000, 'quartier': 'Tanghin'},
        {'nom': 'Mme KABORE MARIAM', 'code': '6006', 'loyer': 38000, 'quartier': 'Gounghin'},
        {'nom': 'M. ZONGO PAUL', 'code': '6007', 'loyer': 50000, 'quartier': 'Dassasgho'},
        {'nom': 'Mme ILBOUDO RASMANE', 'code': '6008', 'loyer': 42000, 'quartier': 'Wemtenga'},
        {'nom': 'M. NACRO VINCENT', 'code': '6009', 'loyer': 65000, 'quartier': 'Cissin'},
        {'nom': 'Mme SAMA ROSELINE', 'code': '6010', 'loyer': 37000, 'quartier': 'Tampuy'}
    ]
    
    def __init__(self):
        self.charger_donnees()
    
    def charger_donnees(self):
        """Charge les données existantes ou initialise"""
        if os.path.exists(self.FICHIER_DONNEES):
            try:
                with open(self.FICHIER_DONNEES, 'r', encoding='utf-8') as f:
                    self.donnees = json.load(f)
            except:
                self.donnees = {'dernier_numero': 222600, 'quittances': []}
        else:
            self.donnees = {'dernier_numero': 222600, 'quittances': []}
    
    def sauvegarder_donnees(self):
        """Sauvegarde les données"""
        try:
            with open(self.FICHIER_DONNEES, 'w', encoding='utf-8') as f:
                json.dump(self.donnees, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Erreur sauvegarde: {e}")
    
    def generer_numero_quittance(self):
        """Génère un numéro de quittance unique"""
        from django.utils.crypto import get_random_string
        from datetime import datetime
        
        # Utiliser un système de génération unique basé sur timestamp + random
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_part = get_random_string(4, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
        
        # Format: QUI-YYYYMMDDHHMMSS-XXXX
        numero = f"QUI-{timestamp}-{random_part}"
        
        # Vérifier l'unicité dans la base de données
        try:
            from paiements.models import QuittancePaiement
            while QuittancePaiement.objects.filter(numero_quittance=numero).exists():
                random_part = get_random_string(4, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
                numero = f"QUI-{timestamp}-{random_part}"
        except ImportError:
            # Si le modèle n'est pas disponible, utiliser l'ancien système
            self.donnees['dernier_numero'] += 1
            numero = str(self.donnees['dernier_numero'])
        
        return numero
    
    def obtenir_locataire_aleatoire(self):
        """Sélectionne un locataire aléatoire"""
        return random.choice(self.LOCATAIRES_REELS)
    
    def calculer_restant_du(self, loyer_mensuel):
        """Calcule un restant dû réaliste"""
        # 70% chance d'avoir 0, 30% chance d'avoir un restant
        if random.random() < 0.7:
            return 0
        else:
            # Restant entre 5000 et 50% du loyer
            return random.randint(5000, int(loyer_mensuel * 0.5))
    
    def calculer_prorata(self, loyer_mensuel):
        """Calcule un prorata réaliste"""
        # 80% chance d'avoir 0, 20% chance d'avoir un prorata
        if random.random() < 0.8:
            return 0
        else:
            # Prorata entre 2000 et 25% du loyer
            return random.randint(2000, int(loyer_mensuel * 0.25))
    
    def obtenir_mois_francais(self, date_obj=None):
        """Retourne le mois en français"""
        if date_obj is None:
            date_obj = datetime.now()
        
        mois_fr = [
            'janvier', 'février', 'mars', 'avril', 'mai', 'juin',
            'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre'
        ]
        return f"{mois_fr[date_obj.month - 1]} {date_obj.year}"
    
    def generer_donnees_quittance_reelle(self, locataire_specifique=None):
        """Génère des données de quittance réelles et cohérentes"""
        
        # Sélection du locataire
        if locataire_specifique:
            locataire = locataire_specifique
        else:
            locataire = self.obtenir_locataire_aleatoire()
        
        # Génération des données
        numero = self.generer_numero_quittance()
        date_actuelle = datetime.now()
        date_formatee = date_actuelle.strftime('%d-%b-%y').replace(
            date_actuelle.strftime('%b'), 
            ['jan', 'fév', 'mar', 'avr', 'mai', 'jun', 
             'jul', 'aoû', 'sep', 'oct', 'nov', 'déc'][date_actuelle.month - 1]
        )
        
        loyer = locataire['loyer']
        restant_du = self.calculer_restant_du(loyer)
        prorata = self.calculer_prorata(loyer)
        
        # Calcul du montant total payé
        montant_paye = loyer + prorata
        
        donnees = {
            'numero': numero,
            'date': date_formatee,
            'code_location': locataire['code'],
            'recu_de': locataire['nom'],
            'montant': montant_paye,
            'loyer_base': loyer,
            'mois_regle': self.obtenir_mois_francais(),
            'restant_du': restant_du,
            'loyer_au_prorata': prorata,
            'quartier': locataire['quartier'],
            'timestamp': date_actuelle.isoformat()
        }
        
        # Sauvegarde dans l'historique
        self.donnees['quittances'].append(donnees)
        self.sauvegarder_donnees()
        
        return donnees
    
    @classmethod
    def get_styles_css_a5(cls):
        """Styles CSS optimisés pour format A5"""
        return """
        <style>
            /* Format A5 - Optimisé pour impression */
            @page {
                size: A5;
                margin: 8mm;
            }
            
            @media print {
                body { margin: 0; }
                .no-print { display: none; }
            }
            
            body { 
                font-family: 'Arial', sans-serif; 
                margin: 0; 
                padding: 0;
                background: white;
                color: #333;
                font-size: 11px;
                line-height: 1.2;
            }
            
            .quittance-container {
                width: 148mm;
                height: 210mm;
                margin: 0 auto;
                background: white;
                border: 2px solid #000;
                display: flex;
                flex-direction: column;
                overflow: hidden;
            }
            
            .entete-principal {
                background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
                border-bottom: 2px solid #000;
                padding: 6mm;
                text-align: center;
                flex-shrink: 0;
                position: relative;
            }
            
            .entete-principal::before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background-image: 
                    radial-gradient(circle at 20% 20%, rgba(25, 118, 210, 0.05) 0%, transparent 50%),
                    radial-gradient(circle at 80% 80%, rgba(25, 118, 210, 0.03) 0%, transparent 50%);
                pointer-events: none;
            }
            
            .entete-principal > * {
                position: relative;
                z-index: 1;
            }
            
            .logo-section {
                display: flex;
                align-items: center;
                justify-content: center;
                margin-bottom: 5mm;
            }
            
            .logo-kbis {
                width: 15mm;
                height: 15mm;
                margin-right: 4mm;
                display: flex;
                align-items: center;
                justify-content: center;
                flex-shrink: 0;
            }
            
            .logo-kbis img {
                max-width: 100%;
                max-height: 100%;
                object-fit: contain;
            }
            
            .nom-entreprise {
                font-size: 18px;
                font-weight: bold;
                color: #000;
                letter-spacing: 1px;
            }
            
            .services-ligne {
                font-size: 10px;
                color: #666;
                margin-top: 3mm;
                border-top: 1px solid #ccc;
                border-bottom: 1px solid #ccc;
                padding: 2mm 0;
            }
            
            .orange-money-section {
                background: #fff8e1;
                padding: 2mm;
                font-size: 9px;
                color: #e65100;
                font-weight: bold;
                border-bottom: 1px solid #000;
                text-align: center;
            }
            
            .contenu-quittance {
                padding: 4mm;
                flex-grow: 1;
                display: flex;
                flex-direction: column;
            }
            
            .section-principale {
                display: flex;
                margin-bottom: 6mm;
                flex-grow: 1;
            }
            
            .colonne-gauche {
                width: 45%;
                padding-right: 3mm;
            }
            
            .colonne-droite {
                width: 55%;
                padding-left: 3mm;
                border-left: 1px solid #ccc;
            }
            
            .champ-quittance {
                margin-bottom: 4mm;
            }
            
            .label-champ {
                font-size: 9px;
                color: #666;
                text-decoration: underline;
                margin-bottom: 2mm;
                display: block;
            }
            
            .valeur-champ {
                font-size: 13px;
                font-weight: bold;
                color: #000;
                min-height: 6mm;
                display: block;
            }
            
            .date-section {
                text-align: right;
                margin-bottom: 5mm;
            }
            
            .montant-principal {
                background: #e3f2fd;
                border: 2px solid #1976d2;
                padding: 3mm;
                text-align: center;
                font-size: 14px;
                font-weight: bold;
                color: #1976d2;
                margin: 2mm 0;
            }
            
            .montant-lettres {
                text-align: center;
                font-style: italic;
                color: #666;
                font-size: 10px;
                margin: 2mm 0;
            }
            
            .details-paiement {
                background: #f8f9fa;
                border: 1px solid #ddd;
                margin: 3mm 0;
                flex-shrink: 0;
            }
            
            .details-paiement table {
                width: 100%;
                border-collapse: collapse;
            }
            
            .details-paiement td {
                padding: 1.5mm;
                border: 1px solid #ddd;
                font-size: 9px;
            }
            
            .cachet-signature {
                text-align: center;
                margin-top: auto;
                padding: 2mm;
                border: 1px dashed #666;
                background: #f9f9f9;
                flex-shrink: 0;
            }
            
            .cachet-rond {
                width: 20mm;
                height: 20mm;
                margin: 0 auto 2mm;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 7px;
                text-align: center;
                color: #666;
                font-weight: bold;
                line-height: 1.1;
            }
            
            .pied-page {
                background: #000;
                color: white;
                padding: 2mm;
                font-size: 7px;
                text-align: center;
                line-height: 1.2;
                flex-shrink: 0;
            }
            
            .pied-page strong {
                color: #ffd700;
            }
            
            .info-supplementaire {
                background: #e8f5e8;
                padding: 2mm;
                margin: 2mm 0;
                border-radius: 2mm;
                font-size: 9px;
                color: #2e7d32;
            }
        </style>
        """
    
    @classmethod
    def convertir_nombre_en_lettres(cls, nombre):
        """Convertit un nombre en lettres en français"""
        
        unites = ["", "un", "deux", "trois", "quatre", "cinq", "six", "sept", "huit", "neuf"]
        dizaines = ["", "", "vingt", "trente", "quarante", "cinquante", "soixante", "soixante-dix", "quatre-vingt", "quatre-vingt-dix"]
        
        if nombre == 0:
            return "zéro"
        
        if nombre < 10:
            return unites[nombre]
        elif nombre < 20:
            if nombre == 10: return "dix"
            elif nombre == 11: return "onze"
            elif nombre == 12: return "douze"
            elif nombre == 13: return "treize"
            elif nombre == 14: return "quatorze"
            elif nombre == 15: return "quinze"
            elif nombre == 16: return "seize"
            elif nombre == 17: return "dix-sept"
            elif nombre == 18: return "dix-huit"
            elif nombre == 19: return "dix-neuf"
        elif nombre < 100:
            d = nombre // 10
            u = nombre % 10
            if u == 0:
                return dizaines[d]
            else:
                return dizaines[d] + "-" + unites[u]
        elif nombre < 1000:
            c = nombre // 100
            reste = nombre % 100
            if c == 1:
                centaine = "cent"
            else:
                centaine = unites[c] + " cent"
            
            if reste == 0:
                return centaine
            else:
                return centaine + " " + cls.convertir_nombre_en_lettres(reste)
        elif nombre < 1000000:
            milliers = nombre // 1000
            reste = nombre % 1000
            
            if milliers == 1:
                millier_text = "mille"
            else:
                millier_text = cls.convertir_nombre_en_lettres(milliers) + " mille"
            
            if reste == 0:
                return millier_text
            else:
                return millier_text + " " + cls.convertir_nombre_en_lettres(reste)
        else:
            return f"{nombre:,}".replace(',', ' ')
    
    def generer_quittance_html(self, donnees):
        """Génère le HTML de la quittance avec le système unifié KBIS"""
        # Utiliser le système unifié pour tous les documents
        try:
            from document_kbis_unifie import DocumentKBISUnifie
            return DocumentKBISUnifie.generer_document_unifie(donnees, 'quittance')
        except ImportError:
            # Fallback vers l'ancien système si le nouveau n'est pas disponible
            montant_lettres = self.convertir_nombre_en_lettres(donnees['montant'])
            
            html = f"""
        <!DOCTYPE html>
        <html lang="fr">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Quittance N° {donnees['numero']} - KBIS IMMOBILIER</title>
            {self.get_styles_css_a5()}
        </head>
        <body>
            <div class="quittance-container">
                <!-- EN-TÊTE -->
                <div class="entete-principal">
                    <div class="logo-section">
                        <div class="logo-kbis">
                            <img src="/static/images/logo_kbis.jpg" alt="Logo KBIS" />
                        </div>
                        <div class="nom-entreprise">
                            {self.ENTREPRISE['nom']}
                        </div>
                    </div>
                    <div class="services-ligne">
                        {' • '.join(self.ENTREPRISE['services'])}
                    </div>
                </div>
                
                <!-- ORANGE MONEY -->
                <div class="orange-money-section">
                    {self.ENTREPRISE['depot_orange']}
                </div>
                
                <!-- CONTENU -->
                <div class="contenu-quittance">
                    <!-- Date -->
                    <div class="date-section">
                        <span class="label-champ">Date :</span>
                        <span class="valeur-champ" style="font-size: 14px;">
                            {donnees['date']}
                        </span>
                    </div>
                    
                    <!-- Section principale -->
                    <div class="section-principale">
                        <div class="colonne-gauche">
                            <div class="champ-quittance">
                                <span class="label-champ">QUITTANCE N° :</span>
                                <span class="valeur-champ" style="font-size: 16px; color: #1976d2;">
                                    {donnees['numero']}
                                </span>
                            </div>
                            
                            <div class="champ-quittance">
                                <span class="label-champ">code location :</span>
                                <span class="valeur-champ" style="font-size: 14px; color: #666;">
                                    {donnees['code_location']}
                                </span>
                            </div>
                            
                            <div class="info-supplementaire">
                                <strong>Quartier:</strong> {donnees['quartier']}<br>
                                <strong>Loyer base:</strong> {donnees['loyer_base']:,} F
                            </div>
                        </div>
                        
                        <div class="colonne-droite">
                            <div class="champ-quittance">
                                <span class="label-champ">Reçu de M. :</span>
                                <span class="valeur-champ" style="font-size: 12px;">
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
                    
                    <!-- Détails -->
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
                    
                    <!-- Cachet -->
                    <div class="cachet-signature">
                        <div class="cachet-rond">
                            <!-- Espace libre pour le cachet -->
                        </div>
                        <p style="margin: 0; font-size: 9px; color: #333;">
                            Cachet et signature de l'Agence
                        </p>
                    </div>
                </div>
                
                <!-- PIED DE PAGE -->
                <div class="pied-page">
                    <strong>{self.ENTREPRISE['adresse']}</strong><br>
                    <strong>Tél: {self.ENTREPRISE['telephones'][1]}</strong><br>
                    {self.ENTREPRISE['localisation']}<br>
                    <strong>{self.ENTREPRISE['telephone_annexe']}</strong><br>
                    <strong>Email: {self.ENTREPRISE['email']}</strong><br>
                    <strong>ORANGE MONEY : {self.ENTREPRISE['orange_money']}</strong>
                </div>
            </div>
            
            <!-- Boutons d'action (masqués à l'impression) -->
            <div class="no-print" style="text-align: center; margin: 10px; background: #f0f0f0; padding: 10px; border-radius: 5px;">
                <button onclick="window.print()" style="padding: 10px 20px; background: #1976d2; color: white; border: none; border-radius: 5px; cursor: pointer; margin: 5px;">
                    🖨️ Imprimer (A5)
                </button>
                <button onclick="window.history.back()" style="padding: 10px 20px; background: #666; color: white; border: none; border-radius: 5px; cursor: pointer; margin: 5px;">
                    ← Retour
                </button>
            </div>
        </body>
        </html>
        """
        
        return html

if __name__ == '__main__':
    # Test du système dynamique
    print("🏢 KBIS IMMOBILIER - Système de Quittances Dynamiques")
    print("=" * 55)
    
    gestionnaire = GestionnaireQuittancesDynamiques()
    
    # Génération d'une quittance réelle
    donnees = gestionnaire.generer_donnees_quittance_reelle()
    
    print(f"✅ Quittance générée:")
    print(f"   📋 Numéro: {donnees['numero']}")
    print(f"   👤 Locataire: {donnees['recu_de']}")
    print(f"   🏠 Quartier: {donnees['quartier']}")
    print(f"   💰 Montant: {donnees['montant']:,} FCFA")
    print(f"   📅 Mois: {donnees['mois_regle']}")
    
    # Génération du HTML
    html = gestionnaire.generer_quittance_html(donnees)
    
    # Sauvegarde
    nom_fichier = f"quittance_dynamique_{donnees['numero']}.html"
    with open(nom_fichier, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"📄 Fichier généré: {nom_fichier}")
    print("🖨️ Format A5 prêt pour impression")