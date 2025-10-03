"""
Utilitaires pour la génération de documents avec en-tête et pied de page KBIS
"""
from django.conf import settings
from django.templatetags.static import static
from django.utils import timezone
import os


class KBISDocumentTemplate:
    """Classe pour gérer l'en-tête et le pied de page KBIS dans tous les documents."""
    
    # Informations de l'entreprise KBIS
    ENTREPRISE_INFO = {
        'nom': 'KBIS IMMOBILIER',
        'slogan': 'Votre Partenaire Immobilier de Confiance',
        'adresse_ligne1': 'Avenue de la République',
        'adresse_ligne2': 'Quartier Centre-Ville',
        'ville': 'Abidjan, Côte d\'Ivoire',
        'telephone': '+225 XX XX XX XX XX',
        'email': 'contact@kbis-immobilier.ci',
        'site_web': 'www.kbis-immobilier.ci',
        'rccm': 'CI-ABJ-XXXX-X-XXXXX',
        'ifu': 'XXXXXXXXXX',
    }
    
    @staticmethod
    def get_logo_path():
        """Retourne le chemin du logo KBIS."""
        # Chercher le logo dans différents emplacements possibles
        possible_paths = [
            'images/logo_kbis.png',
            'images/logo.png', 
            'img/logo_kbis.png',
            'img/logo.png',
        ]
        
        try:
            # Utiliser le répertoire static configuré
            static_dir = None
            if hasattr(settings, 'STATIC_ROOT') and settings.STATIC_ROOT:
                static_dir = settings.STATIC_ROOT
            elif hasattr(settings, 'STATICFILES_DIRS') and settings.STATICFILES_DIRS:
                static_dir = settings.STATICFILES_DIRS[0]
            
            if static_dir:
                for path in possible_paths:
                    full_path = os.path.join(static_dir, path)
                    if os.path.exists(full_path):
                        return static(path)
        except (IndexError, AttributeError):
            pass
        
        # Logo par défaut si aucun trouvé
        return None
    
    @staticmethod
    def get_entete_html():
        """Génère l'HTML de l'en-tête KBIS."""
        logo_url = KBISDocumentTemplate.get_logo_path()
        info = KBISDocumentTemplate.ENTREPRISE_INFO
        
        return f"""
        <div class="document-header" style="
            border-bottom: 3px solid #2c5aa0;
            padding: 20px 0;
            margin-bottom: 30px;
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        ">
            <table style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td style="width: 120px; vertical-align: top;">
                        {f'<img src="{logo_url}" alt="Logo KBIS" style="max-width: 100px; height: auto;">' if logo_url else ''}
                    </td>
                    <td style="vertical-align: top; padding-left: 20px;">
                        <h1 style="
                            margin: 0;
                            color: #2c5aa0;
                            font-size: 28px;
                            font-weight: bold;
                            font-family: 'Arial', sans-serif;
                        ">{info['nom']}</h1>
                        <p style="
                            margin: 5px 0;
                            color: #6c757d;
                            font-style: italic;
                            font-size: 14px;
                        ">{info['slogan']}</p>
                        <div style="
                            margin-top: 15px;
                            font-size: 12px;
                            color: #495057;
                            line-height: 1.4;
                        ">
                            <p style="margin: 2px 0;">{info['adresse_ligne1']}, {info['adresse_ligne2']}</p>
                            <p style="margin: 2px 0;">{info['ville']}</p>
                            <p style="margin: 2px 0;">
                                <strong>Tél:</strong> {info['telephone']} | 
                                <strong>Email:</strong> {info['email']}
                            </p>
                            <p style="margin: 2px 0;">
                                <strong>Site:</strong> {info['site_web']}
                            </p>
                        </div>
                    </td>
                    <td style="
                        width: 200px;
                        vertical-align: top;
                        text-align: right;
                        padding-left: 20px;
                        border-left: 1px solid #dee2e6;
                    ">
                        <div style="
                            background: #2c5aa0;
                            color: white;
                            padding: 10px;
                            border-radius: 8px;
                            font-size: 11px;
                            text-align: center;
                        ">
                            <p style="margin: 0; font-weight: bold;">INFORMATIONS LÉGALES</p>
                            <p style="margin: 5px 0 0 0;">
                                RCCM: {info['rccm']}<br>
                                IFU: {info['ifu']}
                            </p>
                        </div>
                        <div style="
                            margin-top: 15px;
                            font-size: 10px;
                            color: #6c757d;
                            text-align: center;
                        ">
                            Document généré le<br>
                            <strong>{timezone.now().strftime('%d/%m/%Y à %H:%M')}</strong>
                        </div>
                    </td>
                </tr>
            </table>
        </div>
        """
    
    @staticmethod
    def get_pied_page_html():
        """Génère l'HTML du pied de page KBIS."""
        info = KBISDocumentTemplate.ENTREPRISE_INFO
        
        return f"""
        <div class="document-footer" style="
            border-top: 2px solid #2c5aa0;
            margin-top: 40px;
            padding-top: 20px;
            background: #f8f9fa;
            font-size: 11px;
            color: #6c757d;
        ">
            <table style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td style="width: 33%; vertical-align: top;">
                        <p style="margin: 0; font-weight: bold; color: #2c5aa0;">CONTACT</p>
                        <p style="margin: 2px 0; line-height: 1.3;">
                            {info['telephone']}<br>
                            {info['email']}<br>
                            {info['site_web']}
                        </p>
                    </td>
                    <td style="width: 34%; text-align: center; vertical-align: top;">
                        <p style="margin: 0; font-weight: bold; color: #2c5aa0;">ADRESSE</p>
                        <p style="margin: 2px 0; line-height: 1.3;">
                            {info['adresse_ligne1']}<br>
                            {info['adresse_ligne2']}<br>
                            {info['ville']}
                        </p>
                    </td>
                    <td style="width: 33%; text-align: right; vertical-align: top;">
                        <p style="margin: 0; font-weight: bold; color: #2c5aa0;">MENTIONS LÉGALES</p>
                        <p style="margin: 2px 0; line-height: 1.3;">
                            RCCM: {info['rccm']}<br>
                            IFU: {info['ifu']}<br>
                            <em>Document confidentiel</em>
                        </p>
                    </td>
                </tr>
            </table>
            <div style="
                text-align: center;
                margin-top: 15px;
                padding-top: 10px;
                border-top: 1px solid #dee2e6;
                font-size: 10px;
                color: #adb5bd;
            ">
                © {timezone.now().year} {info['nom']} - Tous droits réservés | 
                Document généré automatiquement le {timezone.now().strftime('%d/%m/%Y à %H:%M')}
            </div>
        </div>
        """
    
    @staticmethod
    def get_document_complet(titre, contenu, type_document="Document"):
        """Génère un document HTML complet avec en-tête et pied de page KBIS."""
        return f"""
        <!DOCTYPE html>
        <html lang="fr">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{titre} - KBIS IMMOBILIER</title>
            <style>
                body {{
                    font-family: 'Arial', sans-serif;
                    margin: 0;
                    padding: 30px;
                    background: #ffffff;
                    color: #333;
                    line-height: 1.6;
                }}
                .container {{
                    max-width: 800px;
                    margin: 0 auto;
                    background: white;
                    box-shadow: 0 0 20px rgba(0,0,0,0.1);
                    padding: 40px;
                }}
                .document-title {{
                    text-align: center;
                    color: #2c5aa0;
                    font-size: 24px;
                    font-weight: bold;
                    margin: 30px 0;
                    padding: 15px;
                    background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
                    border: 2px solid #2c5aa0;
                    border-radius: 8px;
                }}
                .document-content {{
                    margin: 30px 0;
                    min-height: 400px;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 15px 0;
                }}
                th, td {{
                    padding: 10px;
                    text-align: left;
                    border-bottom: 1px solid #dee2e6;
                }}
                th {{
                    background: #f8f9fa;
                    font-weight: bold;
                    color: #2c5aa0;
                }}
                .montant {{
                    font-weight: bold;
                    color: #28a745;
                }}
                @media print {{
                    body {{ margin: 0; padding: 20px; }}
                    .container {{ box-shadow: none; }}
                }}
            </style>
        </head>
        <body>
            <div class="container">
                {KBISDocumentTemplate.get_entete_html()}
                
                <div class="document-title">
                    {titre}
                </div>
                
                <div class="document-content">
                    {contenu}
                </div>
                
                {KBISDocumentTemplate.get_pied_page_html()}
            </div>
        </body>
        </html>
        """
    
    @staticmethod
    def generer_recu_paiement(paiement):
        """Génère un reçu de paiement avec l'en-tête KBIS."""
        
        # Récupérer les informations avec gestion d'erreur
        # Récupérer les informations avec gestion d'erreur
        mode_paiement = getattr(paiement, 'get_mode_paiement_display', lambda: 'Non spécifié')()
        statut = getattr(paiement, 'get_statut_display', lambda: 'Payé')()
        nom_locataire = getattr(paiement, 'get_nom_complet_locataire', lambda: 'Non spécifié')()
        adresse_propriete = getattr(paiement, 'get_adresse_propriete', lambda: 'Non spécifié')()
        
        contenu = f"""
        <div style="margin: 20px 0;">
            <h3 style="color: #2c5aa0; border-bottom: 2px solid #2c5aa0; padding-bottom: 10px;">
                INFORMATIONS DU PAIEMENT
            </h3>
            <table style="background: #f8f9fa; border-radius: 8px;">
                <tr>
                    <td><strong>Référence:</strong></td>
                    <td>{getattr(paiement, 'reference_paiement', 'N/A')}</td>
                </tr>
                <tr>
                    <td><strong>Date de paiement:</strong></td>
                    <td>{getattr(paiement, 'date_paiement', timezone.now()).strftime('%d/%m/%Y')}</td>
                </tr>
                <tr>
                    <td><strong>Montant:</strong></td>
                    <td class="montant">{paiement.get_montant_formatted()}</td>
                </tr>
                <tr>
                    <td><strong>Mode de paiement:</strong></td>
                    <td>{mode_paiement}</td>
                </tr>
                <tr>
                    <td><strong>Statut:</strong></td>
                    <td><span style="background: #28a745; color: white; padding: 3px 8px; border-radius: 4px;">
                        {statut}
                    </span></td>
                </tr>
            </table>
        </div>
        
        <div style="margin: 20px 0;">
            <h3 style="color: #2c5aa0; border-bottom: 2px solid #2c5aa0; padding-bottom: 10px;">
                INFORMATIONS DU LOCATAIRE
            </h3>
            <table style="background: #f8f9fa; border-radius: 8px;">
                <tr>
                    <td><strong>Nom complet:</strong></td>
                    <td>{paiement.get_nom_complet_locataire()}</td>
                </tr>
                <tr>
                    <td><strong>Code locataire:</strong></td>
                    <td>{paiement.get_code_locataire()}</td>
                </tr>
                <tr>
                    <td><strong>Propriété:</strong></td>
                    <td>{paiement.get_adresse_propriete()}, {paiement.get_ville_propriete()}</td>
                </tr>
            </table>
        </div>
        
        <div style="
            margin: 30px 0;
            padding: 20px;
            background: linear-gradient(135deg, #28a745, #20c997);
            color: white;
            border-radius: 8px;
            text-align: center;
        ">
            <h2 style="margin: 0; font-size: 18px;">
                REÇU CERTIFIÉ CONFORME
            </h2>
            <p style="margin: 10px 0 0 0;">
                Ce document certifie le paiement effectué et fait foi de quittance.
            </p>
        </div>
        """
        
        titre = f"REÇU DE PAIEMENT N° {paiement.reference_paiement}"
        return KBISDocumentTemplate.get_document_complet(titre, contenu, "Reçu de Paiement")
    
    @staticmethod
    def generer_quittance(quittance):
        """Génère une quittance avec l'en-tête KBIS."""
        paiement = quittance.paiement
        
        contenu = f"""
        <div style="text-align: center; margin: 20px 0; padding: 15px; background: #e7f3ff; border-radius: 8px;">
            <h2 style="color: #2c5aa0; margin: 0;">QUITTANCE DE LOYER</h2>
            <p style="margin: 5px 0; font-size: 14px;">N° {quittance.numero_quittance}</p>
        </div>
        
        <div style="margin: 20px 0;">
            <p style="font-size: 16px; line-height: 1.8;">
                Je soussigné, représentant de <strong>KBIS IMMOBILIER</strong>, 
                certifie avoir reçu de <strong>{paiement.get_nom_complet_locataire()}</strong>
                la somme de <span class="montant">{paiement.get_montant_formatted()}</span>
                au titre du loyer pour la période du <strong>{paiement.mois_paye.strftime('%B %Y') if paiement.mois_paye else 'N/A'}</strong>
                concernant le logement situé <strong>{paiement.get_adresse_propriete()}</strong>.
            </p>
        </div>
        
        <div style="margin: 30px 0;">
            <table style="background: #f8f9fa; border-radius: 8px;">
                <tr>
                    <th colspan="2" style="background: #2c5aa0; color: white;">DÉTAILS DU PAIEMENT</th>
                </tr>
                <tr>
                    <td>Montant du loyer:</td>
                    <td class="montant">{paiement.get_montant_formatted()}</td>
                </tr>
                <tr>
                    <td>Date de paiement:</td>
                    <td>{paiement.date_paiement.strftime('%d/%m/%Y')}</td>
                </tr>
                <tr>
                    <td>Mode de paiement:</td>
                    <td>{paiement.get_mode_paiement_display()}</td>
                </tr>
                <tr>
                    <td>Référence:</td>
                    <td>{paiement.reference_paiement}</td>
                </tr>
            </table>
        </div>
        
        <div style="
            margin: 40px 0;
            text-align: right;
            padding: 20px;
            border: 2px dashed #2c5aa0;
            border-radius: 8px;
        ">
            <p style="margin: 0; font-size: 14px;">
                Fait à Abidjan, le {quittance.date_emission.strftime('%d/%m/%Y')}
            </p>
            <br><br>
            <p style="margin: 0; font-weight: bold;">
                Signature et Cachet<br>
                KBIS IMMOBILIER
            </p>
        </div>
        """
        
        titre = f"QUITTANCE DE LOYER N° {quittance.numero_quittance}"
        return KBISDocumentTemplate.get_document_complet(titre, contenu, "Quittance")
    
    @staticmethod
    def get_css_styles():
        """Retourne les styles CSS pour les documents KBIS."""
        return """
        body {
            font-family: 'Arial', sans-serif;
            margin: 0;
            padding: 30px;
            background: #ffffff;
            color: #333;
            line-height: 1.6;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            box-shadow: 0 0 20px rgba(0,0,0,0.1);
            border-radius: 12px;
            overflow: hidden;
        }
        .header-kbis {
            background: linear-gradient(135deg, #2c5aa0 0%, #3d6db0 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        .footer-kbis {
            background: #f8f9fa;
            color: #666;
            text-align: center;
            padding: 20px;
            font-size: 12px;
            border-top: 3px solid #2c5aa0;
        }
        .document-content {
            padding: 40px;
        }
        .montant {
            font-weight: bold;
            color: #2c5aa0;
            text-align: right;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th {
            background-color: #f8f9fa;
            font-weight: bold;
            color: #2c5aa0;
        }
        """