#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Système de Documents Unifiés KBIS IMMOBILIER
Utilise la même en-tête et pied de page pour tous les documents
"""

from datetime import datetime
import os

class DocumentKBISUnifie:
    """Gestionnaire unifié pour tous les documents KBIS avec en-tête et pied de page cohérents"""
    
    # Informations entreprise unifiées
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
    def get_styles_css_unifie(cls):
        """Styles CSS unifiés pour tous les documents KBIS"""
        return """
        <style>
            /* Format A5 - Unifié pour tous les documents */
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
            
            .document-container {
                width: 148mm;
                height: 210mm;
                margin: 0 auto;
                background: white;
                border: 2px solid #000;
                display: flex;
                flex-direction: column;
                overflow: hidden;
            }
            
            /* EN-TÊTE UNIFIÉ */
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
            
            /* CONTENU DOCUMENT */
            .contenu-document {
                padding: 4mm;
                flex-grow: 1;
                display: flex;
                flex-direction: column;
            }
            
            .titre-document {
                text-align: center;
                font-size: 16px;
                font-weight: bold;
                color: #1976d2;
                margin-bottom: 4mm;
                padding: 2mm;
                background: #e3f2fd;
                border: 1px solid #1976d2;
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
            
            .champ-document {
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
            
            .details-document {
                background: #f8f9fa;
                border: 1px solid #ddd;
                margin: 3mm 0;
                flex-shrink: 0;
            }
            
            .details-document table {
                width: 100%;
                border-collapse: collapse;
            }
            
            .details-document td {
                padding: 1.5mm;
                border: 1px solid #ddd;
                font-size: 9px;
            }
            
            /* CACHET ET SIGNATURE UNIFIÉ */
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
            
            /* PIED DE PAGE UNIFIÉ */
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
        </style>
        """
    
    @classmethod
    def generer_document_unifie(cls, donnees, type_document='quittance'):
        """Génère un document unifié avec en-tête et pied de page KBIS"""
        
        # S'assurer que le numéro est unique si pas fourni
        if 'numero' not in donnees or not donnees['numero']:
            donnees['numero'] = cls.generer_numero_unique(type_document)
        
        # Titre selon le type de document avec précisions
        titres = {
            'quittance': 'QUITTANCE N°',
            'quittance_loyer': 'QUITTANCE DE LOYER N°',
            'quittance_avance': 'QUITTANCE D\'AVANCE N°',
            'quittance_caution': 'QUITTANCE DE CAUTION N°',
            'quittance_caution_avance': 'QUITTANCE DE CAUTION ET AVANCE N°',
            'quittance_charges': 'QUITTANCE DE CHARGES N°',
            'quittance_frais_agence': 'QUITTANCE DE FRAIS D\'AGENCE N°',
            'quittance_retrait': 'QUITTANCE DE RETRAIT N°',
            'quittance_retrait_mensuel': 'QUITTANCE DE RETRAIT MENSUEL N°',
            'quittance_retrait_trimestriel': 'QUITTANCE DE RETRAIT TRIMESTRIEL N°',
            'quittance_retrait_annuel': 'QUITTANCE DE RETRAIT ANNUEL N°',
            'quittance_retrait_exceptionnel': 'QUITTANCE DE RETRAIT EXCEPTIONNEL N°',
            'facture': 'FACTURE N°',
            'recu': 'RÉCÉPISSÉ N°',
            'recu_loyer': 'RÉCÉPISSÉ DE LOYER N°',
            'recu_charges': 'RÉCÉPISSÉ DE CHARGES N°',
            'recu_caution': 'RÉCÉPISSÉ DE CAUTION N°',
            'recu_avance': 'RÉCÉPISSÉ D\'AVANCE DE LOYER N°',
            'recu_caution_avance': 'RÉCÉPISSÉ DE CAUTION ET AVANCE N°',
            'recu_regularisation': 'RÉCÉPISSÉ DE RÉGULARISATION N°',
            'recu_partiel': 'RÉCÉPISSÉ DE PAIEMENT PARTIEL N°',
            'recu_autre': 'RÉCÉPISSÉ DE PAIEMENT N°',
            'recu_retrait': 'RÉCÉPISSÉ DE RETRAIT N°',
            'recu_recapitulatif': 'RÉCÉPISSÉ DE RÉCAPITULATIF N°',
            'attestation': 'ATTESTATION N°'
        }
        
        titre_document = titres.get(type_document, 'DOCUMENT N°')
        
        html_document = f"""
        <!DOCTYPE html>
        <html lang="fr">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{titre_document} {donnees.get('numero', '')} - {cls._get_nom_entreprise_dynamique()}</title>
            {cls.get_styles_css_unifie()}
        </head>
        <body>
            <div class="document-container">
                <!-- EN-TÊTE UNIFIÉ -->
                {cls._generer_entete_dynamique()}
                
                <!-- CONTENU DOCUMENT -->
                <div class="contenu-document">
                    <div class="titre-document">
                        {titre_document} {donnees.get('numero', '')}
                    </div>
                    
                    <div class="section-principale">
                        <div class="colonne-gauche">
                            <div class="champ-document">
                                <span class="label-champ">Date</span>
                                <span class="valeur-champ">{donnees.get('date', '')}</span>
                            </div>
                            
                            <div class="champ-document">
                                <span class="label-champ">Code location</span>
                                <span class="valeur-champ">{donnees.get('code_location', '')}</span>
                            </div>
                            
                            <div class="champ-document">
                                <span class="label-champ">Reçu de</span>
                                <span class="valeur-champ">{donnees.get('recu_de', '')}</span>
                            </div>
                        </div>
                        
                        <div class="colonne-droite">
                            <div class="montant-principal">
                                {donnees.get('montant', 0):,} F CFA
                            </div>
                            <div class="montant-lettres">
                                {cls.convertir_nombre_en_lettres(donnees.get('montant', 0))} francs CFA
                            </div>
                            
                            <div class="champ-document">
                                <span class="label-champ">Mois réglé</span>
                                <span class="valeur-champ">{donnees.get('mois_regle', '')}</span>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Détails du document -->
                    <div class="details-document">
                        {cls._generer_details_specialises(donnees, type_document)}
                    </div>
                    
                    <!-- Cachet et signature -->
                    <div class="cachet-signature">
                        <div class="cachet-rond">
                            <!-- Espace libre pour le cachet -->
                        </div>
                        <p style="margin: 0; font-size: 9px; color: #333;">
                            Cachet et signature de l'Agence
                        </p>
                    </div>
                </div>
                
                <!-- PIED DE PAGE UNIFIÉ -->
                {cls._generer_pied_page_dynamique()}
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
        
        return html_document
    
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
            if d == 7:
                return f"soixante-{unites[u + 10] if u < 10 else unites[u]}"
            elif d == 9:
                return f"quatre-vingt-{unites[u] if u > 0 else ''}"
            else:
                return f"{dizaines[d]}{'-' + unites[u] if u > 0 else ''}"
        else:
            return f"{nombre}"
    
    @classmethod
    def generer_numero_unique(cls, type_document='quittance'):
        """Génère un numéro unique pour le document"""
        from django.utils.crypto import get_random_string
        from datetime import datetime
        
        # Préfixes selon le type de document
        prefixes = {
            'quittance': 'QUI',
            'facture': 'FAC',
            'recu': 'REC',
            'attestation': 'ATT'
        }
        
        prefix = prefixes.get(type_document, 'DOC')
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_part = get_random_string(4, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
        
        # Format: PREFIX-YYYYMMDDHHMMSS-XXXX
        numero = f"{prefix}-{timestamp}-{random_part}"
        
        # Vérifier l'unicité dans la base de données
        try:
            from paiements.models import QuittancePaiement
            while QuittancePaiement.objects.filter(numero_quittance=numero).exists():
                random_part = get_random_string(4, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
                numero = f"{prefix}-{timestamp}-{random_part}"
        except ImportError:
            # Si le modèle n'est pas disponible, utiliser un système simple
            import time
            numero = f"{prefix}-{int(time.time())}-{random_part}"
        
        return numero
    
    @classmethod
    def _generer_entete_dynamique(cls):
        """Génère l'en-tête dynamique avec l'image personnalisée KBIS"""
        try:
            from core.models import ConfigurationEntreprise
            config = ConfigurationEntreprise.get_configuration_active()
            
            # Utiliser l'image d'en-tête personnalisée KBIS
            entete_image_path = config.get_entete_prioritaire()
            if entete_image_path:
                # Utiliser l'image d'en-tête personnalisée
                return f"""
                <div class="entete-principal">
                    <div class="logo-section">
                        <img src="/static/images/enteteEnImage.png" 
                             alt="KBIS IMMOBILIER" 
                             style="width: 100%; max-width: 100%; height: auto; display: block;">
                    </div>
                </div>
                """
            else:
                # Fallback vers l'ancien système si l'image n'existe pas
                logo_html = ""
                if config.logo:
                    logo_html = f'<img src="{config.logo.url}" alt="Logo {config.nom_entreprise}" />'
                elif config.logo_url:
                    logo_html = f'<img src="{config.logo_url}" alt="Logo {config.nom_entreprise}" />'
                else:
                    logo_html = '<img src="/static/images/logo_kbis.jpg" alt="Logo KBIS" />'
                
                # Slogan ou services par défaut
                slogan = config.slogan if config.slogan else 'Achat • Vente • Location • Gestion • Nettoyage'
                
                # Code de référence (IFU ou Orange Money)
                reference_code = config.ifu if config.ifu else '144*10*5933721*MONTANT#'
                
                return f"""
                <div class="entete-principal">
                    <div class="logo-section">
                        <div class="logo-kbis">
                            {logo_html}
                        </div>
                        <div class="nom-entreprise">
                            {config.nom_entreprise}
                        </div>
                    </div>
                    <div class="services-ligne">
                        {slogan}
                    </div>
                    <div class="orange-money-section">
                        {reference_code}
                    </div>
                </div>
                """
        except Exception as e:
            # Fallback vers les valeurs par défaut en cas d'erreur
            return f"""
            <div class="entete-principal">
                <div class="logo-section">
                    <div class="logo-kbis">
                        <img src="/static/images/logo_kbis.jpg" alt="Logo KBIS" />
                    </div>
                    <div class="nom-entreprise">
                        {cls.ENTREPRISE['nom']}
                    </div>
                </div>
                <div class="services-ligne">
                    {' • '.join(cls.ENTREPRISE['services'])}
                </div>
                <div class="orange-money-section">
                    {cls.ENTREPRISE['orange_money']}
                </div>
            </div>
            """
    
    @classmethod
    def _generer_pied_page_dynamique(cls):
        """Génère le pied de page dynamique avec les informations de configuration entreprise"""
        try:
            from core.models import ConfigurationEntreprise
            config = ConfigurationEntreprise.get_configuration_active()
            
            # Construire l'adresse complète
            adresse_parts = []
            if config.adresse_ligne1:
                adresse_parts.append(config.adresse_ligne1)
            if config.adresse_ligne2:
                adresse_parts.append(config.adresse_ligne2)
            if config.code_postal and config.ville:
                adresse_parts.append(f"{config.code_postal} {config.ville}")
            elif config.ville:
                adresse_parts.append(config.ville)
            if config.pays:
                adresse_parts.append(config.pays)
            
            adresse_complete = ", ".join(adresse_parts) if adresse_parts else "Adresse non configurée"
            
            # Construire les informations de contact
            contact_parts = []
            if config.telephone:
                contact_parts.append(f"Tél: {config.telephone}")
            if config.telephone_2:
                contact_parts.append(f"Tél 2: {config.telephone_2}")
            if config.email:
                contact_parts.append(f"Email: {config.email}")
            if config.site_web:
                contact_parts.append(f"Web: {config.site_web}")
            
            contact_complet = " | ".join(contact_parts) if contact_parts else "Contact non configuré"
            
            # Orange Money ou IFU
            orange_money = config.ifu if config.ifu else "ORANGE MONEY: 144*10*5933721*MONTANT#"
            
            return f"""
            <div class="pied-page">
                <strong>{adresse_complete}</strong><br>
                <strong>{contact_complet}</strong><br>
                <strong>{orange_money}</strong>
            </div>
            """
        except Exception as e:
            # Fallback vers les valeurs par défaut en cas d'erreur
            return f"""
            <div class="pied-page">
                <strong>{cls.ENTREPRISE['adresse']}</strong><br>
                <strong>Tél: {cls.ENTREPRISE['telephones'][1]}</strong><br>
                {cls.ENTREPRISE['localisation']}<br>
                <strong>{cls.ENTREPRISE['telephone_annexe']}</strong><br>
                <strong>Email: {cls.ENTREPRISE['email']}</strong><br>
                <strong>ORANGE MONEY: {cls.ENTREPRISE['orange_money']}</strong>
            </div>
            """
    
    @classmethod
    def _get_nom_entreprise_dynamique(cls):
        """Récupère le nom de l'entreprise depuis la configuration"""
        try:
            from core.models import ConfigurationEntreprise
            config = ConfigurationEntreprise.get_configuration_active()
            return config.nom_entreprise
        except Exception:
            return cls.ENTREPRISE['nom']
    
    @classmethod
    def _generer_details_specialises(cls, donnees, type_document):
        """Génère les détails spécialisés selon le type de document"""
        
        if type_document.startswith('recu_'):
            return cls._generer_details_recu(donnees, type_document)
        elif type_document.startswith('quittance_retrait'):
            return cls._generer_details_quittance_retrait(donnees, type_document)
        elif type_document.startswith('quittance_'):
            return cls._generer_details_quittance_paiement(donnees, type_document)
        else:
            # Détails standard pour quittances de loyer et factures
            return f"""
            <table>
                <tr>
                    <td>Loyer de base</td>
                    <td style="font-weight: bold;">
                        {donnees.get('loyer_base', 0):,} F
                    </td>
                </tr>
                <tr>
                    <td>Restant dû</td>
                    <td style="font-weight: bold; color: #d32f2f;">
                        {donnees.get('restant_du', 0):,} F
                    </td>
                </tr>
                <tr>
                    <td>Loyer au prorata à régler</td>
                    <td style="font-weight: bold;">
                        {donnees.get('loyer_au_prorata', 0)} F
                    </td>
                </tr>
            </table>
            """
    
    @classmethod
    def _generer_details_recu(cls, donnees, type_document):
        """Génère les détails spécialisés pour les récépissés"""
        
        if type_document == 'recu_loyer':
            return f"""
            <table>
                <tr>
                    <td>Loyer de base</td>
                    <td style="font-weight: bold;">
                        {donnees.get('loyer_mensuel', donnees.get('loyer_base', 0)):,} F CFA
                    </td>
                </tr>
                <tr>
                    <td>Charges mensuelles</td>
                    <td style="font-weight: bold;">
                        {donnees.get('charges_mensuelles', 0):,} F CFA
                    </td>
                </tr>
                <tr style="background-color: #e3f2fd; font-weight: bold;">
                    <td>TOTAL LOYER</td>
                    <td style="font-weight: bold; color: #1976d2;">
                        {donnees.get('total_mensuel', donnees.get('montant', 0)):,} F CFA
                    </td>
                </tr>
            </table>
            """
            
        elif type_document == 'recu_charges':
            return f"""
            <table>
                <tr>
                    <td>Type de charges</td>
                    <td style="font-weight: bold;">
                        {donnees.get('type_charges', 'Charges mensuelles')}
                    </td>
                </tr>
                <tr>
                    <td>Montant des charges</td>
                    <td style="font-weight: bold;">
                        {donnees.get('charges_mensuelles', donnees.get('montant', 0)):,} F CFA
                    </td>
                </tr>
            </table>
            """
            
        elif type_document == 'recu_avance':
            return f"""
            <table>
                <tr>
                    <td>Type d'avance</td>
                    <td style="font-weight: bold;">
                        {donnees.get('type_avance', 'Avance de loyer')}
                    </td>
                </tr>
                <tr>
                    <td>Loyer mensuel</td>
                    <td style="font-weight: bold;">
                        {donnees.get('loyer_mensuel', 0):,} F CFA
                    </td>
                </tr>
                <tr>
                    <td>Montant de l'avance</td>
                    <td style="font-weight: bold; color: #1976d2;">
                        {donnees.get('montant', 0):,} F CFA
                    </td>
                </tr>
            </table>
            """
            
        elif type_document == 'recu_caution':
            return f"""
            <table>
                <tr>
                    <td>Type de paiement</td>
                    <td style="font-weight: bold;">
                        Caution - {donnees.get('montant', 0):,} F CFA
                    </td>
                </tr>
                <tr>
                    <td>Mode de paiement</td>
                    <td style="font-weight: bold;">
                        {donnees.get('mode_paiement', 'Espèces')}
                    </td>
                </tr>
                <tr>
                    <td>Note</td>
                    <td style="font-weight: bold; color: #1976d2;">
                        Dépôt de garantie - Remboursable en fin de bail
                    </td>
                </tr>
            </table>
            """
            
        elif type_document == 'recu_partiel':
            return f"""
            <table>
                <tr>
                    <td>Type de paiement</td>
                    <td style="font-weight: bold;">
                        {donnees.get('type_paiement', 'Paiement partiel')}
                    </td>
                </tr>
                <tr>
                    <td>Montant payé</td>
                    <td style="font-weight: bold;">
                        {donnees.get('montant', 0):,} F CFA
                    </td>
                </tr>
                <tr>
                    <td>Note spéciale</td>
                    <td style="font-weight: bold; color: #ff9800;">
                        {donnees.get('note_speciale', 'Ce paiement ne couvre qu\'une partie du montant dû')}
                    </td>
                </tr>
            </table>
            """
            
        elif type_document == 'recu_regularisation':
            return f"""
            <table>
                <tr>
                    <td>Type de paiement</td>
                    <td style="font-weight: bold;">
                        {donnees.get('type_paiement', 'Régularisation')}
                    </td>
                </tr>
                <tr>
                    <td>Montant de régularisation</td>
                    <td style="font-weight: bold;">
                        {donnees.get('montant', 0):,} F CFA
                    </td>
                </tr>
                <tr>
                    <td>Note spéciale</td>
                    <td style="font-weight: bold; color: #1976d2;">
                        {donnees.get('note_speciale', 'Paiement de régularisation')}
                    </td>
                </tr>
            </table>
            """
            
        elif type_document == 'recu_autre':
            return f"""
            <table>
                <tr>
                    <td>Type de paiement</td>
                    <td style="font-weight: bold;">
                        {donnees.get('type_paiement', 'Paiement')}
                    </td>
                </tr>
                <tr>
                    <td>Montant</td>
                    <td style="font-weight: bold;">
                        {donnees.get('montant', 0):,} F CFA
                    </td>
                </tr>
                <tr>
                    <td>Mode de paiement</td>
                    <td style="font-weight: bold;">
                        {donnees.get('mode_paiement', 'Espèces')}
                    </td>
                </tr>
            </table>
            """
            
        elif type_document == 'recu_caution_avance':
            return f"""
            <table>
                <tr>
                    <td>Loyer mensuel</td>
                    <td style="font-weight: bold;">
                        {donnees.get('loyer_mensuel', 0):,} F CFA
                    </td>
                </tr>
                <tr>
                    <td>Charges mensuelles</td>
                    <td style="font-weight: bold;">
                        {donnees.get('charges_mensuelles', 0):,} F CFA
                    </td>
                </tr>
                <tr>
                    <td>Dépôt de garantie</td>
                    <td style="font-weight: bold;">
                        {donnees.get('depot_garantie', 0):,} F CFA
                    </td>
                </tr>
                <tr>
                    <td>Avance de loyer</td>
                    <td style="font-weight: bold;">
                        {donnees.get('avance_loyer', 0):,} F CFA
                    </td>
                </tr>
                <tr style="background-color: #e3f2fd; font-weight: bold;">
                    <td>TOTAL</td>
                    <td style="font-weight: bold; color: #1976d2;">
                        {donnees.get('montant_total', 0):,} F CFA
                    </td>
                </tr>
            </table>
            
            <div style="margin-top: 10px;">
                <h4 style="color: #1976d2; font-size: 12px; margin-bottom: 5px;">STATUT DES PAIEMENTS</h4>
                <table>
                    <tr>
                        <td>Caution</td>
                        <td style="font-weight: bold; color: #4caf50;">✓ Payée</td>
                    </tr>
                    <tr>
                        <td>Avance</td>
                        <td style="font-weight: bold; color: #4caf50;">✓ Payée</td>
                    </tr>
                </table>
            </div>
            """
        
        elif type_document == 'recu_retrait':
            return f"""
            <table>
                <tr>
                    <td>Montant brut</td>
                    <td style="font-weight: bold;">
                        {donnees.get('montant_brut', 0):,} F CFA
                    </td>
                </tr>
                <tr>
                    <td>Charges déduites</td>
                    <td style="font-weight: bold; color: #d32f2f;">
                        -{donnees.get('charges_deduites', 0):,} F CFA
                    </td>
                </tr>
                <tr style="background-color: #e3f2fd; font-weight: bold;">
                    <td>Montant net à payer</td>
                    <td style="font-weight: bold; color: #1976d2;">
                        {donnees.get('montant_net', 0):,} F CFA
                    </td>
                </tr>
            </table>
            """
        
        elif type_document == 'recu_recapitulatif':
            return f"""
            <table>
                <tr>
                    <td>Période</td>
                    <td style="font-weight: bold;">
                        {donnees.get('periode', '')}
                    </td>
                </tr>
                <tr>
                    <td>Nombre de propriétés</td>
                    <td style="font-weight: bold;">
                        {donnees.get('nombre_proprietes', 0)}
                    </td>
                </tr>
                <tr>
                    <td>Total loyers</td>
                    <td style="font-weight: bold;">
                        {donnees.get('total_loyers', 0):,} F CFA
                    </td>
                </tr>
                <tr style="background-color: #e3f2fd; font-weight: bold;">
                    <td>Montant net</td>
                    <td style="font-weight: bold; color: #1976d2;">
                        {donnees.get('montant_net', 0):,} F CFA
                    </td>
                </tr>
            </table>
            """
        
        else:
            # Récépissé standard
            return f"""
            <table>
                <tr>
                    <td>Type de paiement</td>
                    <td style="font-weight: bold;">
                        {donnees.get('type_paiement', 'Paiement')}
                    </td>
                </tr>
                <tr>
                    <td>Montant reçu</td>
                    <td style="font-weight: bold;">
                        {donnees.get('montant', 0):,} F CFA
                    </td>
                </tr>
                <tr>
                    <td>Mode de paiement</td>
                    <td style="font-weight: bold;">
                        {donnees.get('mode_paiement', 'Non spécifié')}
                    </td>
                </tr>
            </table>
            """
    
    @classmethod
    def _generer_details_quittance_retrait(cls, donnees, type_document):
        """Génère les détails spécialisés pour les quittances de retrait"""
        
        # Informations sur le type de retrait
        type_retrait = donnees.get('type_retrait', 'Retrait')
        mode_retrait = donnees.get('mode_retrait', 'Non spécifié')
        
        return f"""
        <table>
            <tr>
                <td>Type de retrait</td>
                <td style="font-weight: bold;">
                    {type_retrait}
                </td>
            </tr>
            <tr>
                <td>Mode de retrait</td>
                <td style="font-weight: bold;">
                    {mode_retrait}
                </td>
            </tr>
            <tr>
                <td>Montant brut des loyers</td>
                <td style="font-weight: bold;">
                    {donnees.get('montant_brut', 0):,} F CFA
                </td>
            </tr>
            <tr>
                <td>Charges déductibles</td>
                <td style="font-weight: bold; color: #d32f2f;">
                    -{donnees.get('charges_deduites', 0):,} F CFA
                </td>
            </tr>
            <tr style="background-color: #e3f2fd; font-weight: bold;">
                <td>Montant net à payer</td>
                <td style="font-weight: bold; color: #1976d2;">
                    {donnees.get('montant_net', 0):,} F CFA
                </td>
            </tr>
        </table>
        
        <div style="margin-top: 10px;">
            <h4 style="color: #1976d2; font-size: 12px; margin-bottom: 5px;">DÉTAILS DU RETRAIT</h4>
            <table>
                <tr>
                    <td>Période concernée</td>
                    <td style="font-weight: bold;">
                        {donnees.get('mois_regle', '')}
                    </td>
                </tr>
                <tr>
                    <td>Code de retrait</td>
                    <td style="font-weight: bold;">
                        {donnees.get('code_location', '')}
                    </td>
                </tr>
            </table>
        </div>
        """
    
    @classmethod
    def _generer_details_quittance_paiement(cls, donnees, type_document):
        """Génère les détails spécialisés pour les quittances de paiement"""
        
        type_paiement = donnees.get('type_paiement', 'Paiement')
        mode_paiement = donnees.get('mode_paiement', 'Non spécifié')
        
        if type_document == 'quittance_loyer':
            return f"""
            <table>
                <tr>
                    <td>Type de paiement</td>
                    <td style="font-weight: bold; color: #1976d2;">
                        {type_paiement}
                    </td>
                </tr>
                <tr>
                    <td>Mode de paiement</td>
                    <td style="font-weight: bold;">
                        {mode_paiement}
                    </td>
                </tr>
                <tr>
                    <td>Loyer de base</td>
                    <td style="font-weight: bold;">
                        {donnees.get('loyer_base', 0):,} F CFA
                    </td>
                </tr>
                <tr>
                    <td>Restant dû</td>
                    <td style="font-weight: bold; color: #d32f2f;">
                        {donnees.get('restant_du', 0):,} F CFA
                    </td>
                </tr>
                <tr>
                    <td>Loyer au prorata à régler</td>
                    <td style="font-weight: bold;">
                        {donnees.get('loyer_au_prorata', 0):,} F CFA
                    </td>
                </tr>
            </table>
            """
        
        elif type_document == 'quittance_avance':
            return f"""
            <table>
                <tr>
                    <td>Type de paiement</td>
                    <td style="font-weight: bold; color: #ff9800;">
                        {type_paiement}
                    </td>
                </tr>
                <tr>
                    <td>Mode de paiement</td>
                    <td style="font-weight: bold;">
                        {mode_paiement}
                    </td>
                </tr>
                <tr>
                    <td>Montant de l'avance</td>
                    <td style="font-weight: bold;">
                        {donnees.get('montant', 0):,} F CFA
                    </td>
                </tr>
                <tr style="background-color: #fff3e0;">
                    <td><strong>Note</strong></td>
                    <td style="font-weight: bold; color: #f57c00;">
                        Cette avance sera déduite du prochain loyer
                    </td>
                </tr>
            </table>
            """
        
        elif type_document == 'quittance_caution':
            return f"""
            <table>
                <tr>
                    <td>Type de paiement</td>
                    <td style="font-weight: bold; color: #4caf50;">
                        {type_paiement}
                    </td>
                </tr>
                <tr>
                    <td>Mode de paiement</td>
                    <td style="font-weight: bold;">
                        {mode_paiement}
                    </td>
                </tr>
                <tr>
                    <td>Montant de la caution</td>
                    <td style="font-weight: bold;">
                        {donnees.get('montant', 0):,} F CFA
                    </td>
                </tr>
                <tr style="background-color: #e8f5e8;">
                    <td><strong>Note</strong></td>
                    <td style="font-weight: bold; color: #2e7d32;">
                        Dépôt de garantie - Remboursable en fin de bail
                    </td>
                </tr>
            </table>
            """
        
        elif type_document == 'quittance_caution_avance':
            return f"""
            <table>
                <tr>
                    <td>Type de paiement</td>
                    <td style="font-weight: bold; color: #9c27b0;">
                        {type_paiement}
                    </td>
                </tr>
                <tr>
                    <td>Mode de paiement</td>
                    <td style="font-weight: bold;">
                        {mode_paiement}
                    </td>
                </tr>
                <tr>
                    <td>Montant total</td>
                    <td style="font-weight: bold;">
                        {donnees.get('montant', 0):,} F CFA
                    </td>
                </tr>
                <tr style="background-color: #f3e5f5;">
                    <td><strong>Composition</strong></td>
                    <td style="font-weight: bold; color: #7b1fa2;">
                        Caution + Avance de loyer
                    </td>
                </tr>
            </table>
            """
        
        elif type_document == 'quittance_charges':
            return f"""
            <table>
                <tr>
                    <td>Type de paiement</td>
                    <td style="font-weight: bold; color: #2196f3;">
                        {type_paiement}
                    </td>
                </tr>
                <tr>
                    <td>Mode de paiement</td>
                    <td style="font-weight: bold;">
                        {mode_paiement}
                    </td>
                </tr>
                <tr>
                    <td>Montant des charges</td>
                    <td style="font-weight: bold;">
                        {donnees.get('montant', 0):,} F CFA
                    </td>
                </tr>
                <tr style="background-color: #e3f2fd;">
                    <td><strong>Note</strong></td>
                    <td style="font-weight: bold; color: #1976d2;">
                        Charges communes et services
                    </td>
                </tr>
            </table>
            """
        
        elif type_document == 'quittance_frais_agence':
            return f"""
            <table>
                <tr>
                    <td>Type de paiement</td>
                    <td style="font-weight: bold; color: #ff5722;">
                        {type_paiement}
                    </td>
                </tr>
                <tr>
                    <td>Mode de paiement</td>
                    <td style="font-weight: bold;">
                        {mode_paiement}
                    </td>
                </tr>
                <tr>
                    <td>Montant des frais d'agence</td>
                    <td style="font-weight: bold;">
                        {donnees.get('montant', 0):,} F CFA
                    </td>
                </tr>
                <tr style="background-color: #fce4ec;">
                    <td><strong>Note</strong></td>
                    <td style="font-weight: bold; color: #c2185b;">
                        Frais de gestion et administration
                    </td>
                </tr>
            </table>
            """
        
        else:
            # Quittance standard
            return f"""
            <table>
                <tr>
                    <td>Type de paiement</td>
                    <td style="font-weight: bold;">
                        {type_paiement}
                    </td>
                </tr>
                <tr>
                    <td>Mode de paiement</td>
                    <td style="font-weight: bold;">
                        {mode_paiement}
                    </td>
                </tr>
                <tr>
                    <td>Montant payé</td>
                    <td style="font-weight: bold;">
                        {donnees.get('montant', 0):,} F CFA
                    </td>
                </tr>
            </table>
            """

if __name__ == "__main__":
    # Test de génération
    donnees_test = {
        'numero': '222600',
        'date': '26-sept-25',
        'code_location': '6283',
        'recu_de': 'FARMA ODOSSE',
        'montant': 30000,
        'loyer_base': 30000,
        'mois_regle': 'juillet 2025',
        'restant_du': 60000,
        'loyer_au_prorata': 0
    }
    
    # Test quittance
    quittance = DocumentKBISUnifie.generer_document_unifie(donnees_test, 'quittance')
    print("Quittance générée avec succès")
    
    # Test facture
    facture = DocumentKBISUnifie.generer_document_unifie(donnees_test, 'facture')
    print("Facture générée avec succès")
