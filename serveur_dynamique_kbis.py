#!/usr/bin/env python
"""
Serveur Flask - KBIS IMMOBILIER
Système de Quittances Dynamiques avec Format A5
"""

from flask import Flask, Response, request
from datetime import datetime
import sys
import os

# Ajouter le répertoire courant au PATH
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import du système dynamique
from quittance_dynamique_kbis import GestionnaireQuittancesDynamiques

app = Flask(__name__)

# Instance globale du gestionnaire
gestionnaire = GestionnaireQuittancesDynamiques()

@app.route('/')
def accueil():
    """Page d'accueil système KBIS IMMOBILIER"""
    return f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>🏢 KBIS IMMOBILIER - Système de Quittances Dynamiques</title>
        <style>
            body {{ 
                font-family: 'Segoe UI', Arial, sans-serif; 
                margin: 0; 
                padding: 20px; 
                background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
                min-height: 100vh;
                color: #333;
            }}
            .container {{ 
                max-width: 1200px; 
                margin: 0 auto; 
                background: white; 
                padding: 40px; 
                border-radius: 20px; 
                box-shadow: 0 15px 35px rgba(0,0,0,0.3); 
            }}
            .header {{
                text-align: center;
                border-bottom: 3px solid #1976d2;
                padding-bottom: 30px;
                margin-bottom: 40px;
            }}
            .logo-entreprise {{
                font-size: 32px;
                font-weight: bold;
                color: #1976d2;
                margin-bottom: 10px;
                letter-spacing: 2px;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
            }}
            .services {{
                color: #666;
                font-size: 16px;
                margin-top: 15px;
                font-weight: 500;
            }}
            .status-dynamique {{
                background: linear-gradient(45deg, #4caf50, #45a049);
                color: white;
                padding: 25px;
                border-radius: 15px;
                margin: 30px 0;
                text-align: center;
                box-shadow: 0 8px 20px rgba(76, 175, 80, 0.4);
                animation: pulse 2s infinite;
            }}
            @keyframes pulse {{
                0% {{ transform: scale(1); }}
                50% {{ transform: scale(1.02); }}
                100% {{ transform: scale(1); }}
            }}
            .fonctionnalites {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
                gap: 25px;
                margin: 40px 0;
            }}
            .btn-fonctionnalite {{
                display: block;
                padding: 20px;
                background: linear-gradient(45deg, #1976d2, #1565c0);
                color: white;
                text-decoration: none;
                border-radius: 12px;
                text-align: center;
                font-weight: bold;
                font-size: 16px;
                transition: all 0.3s ease;
                box-shadow: 0 8px 20px rgba(25, 118, 210, 0.3);
                position: relative;
                overflow: hidden;
            }}
            .btn-fonctionnalite:hover {{
                transform: translateY(-3px);
                box-shadow: 0 12px 25px rgba(25, 118, 210, 0.5);
            }}
            .btn-fonctionnalite:before {{
                content: '';
                position: absolute;
                top: 0;
                left: -100%;
                width: 100%;
                height: 100%;
                background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
                transition: left 0.5s;
            }}
            .btn-fonctionnalite:hover:before {{
                left: 100%;
            }}
            .btn-generer {{ background: linear-gradient(45deg, #4caf50, #45a049); }}
            .btn-formulaire {{ background: linear-gradient(45deg, #ff9800, #f57c00); }}
            .btn-historique {{ background: linear-gradient(45deg, #9c27b0, #7b1fa2); }}
            .btn-demo {{ background: linear-gradient(45deg, #00bcd4, #0097a7); }}
            .stats-dynamiques {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin: 40px 0;
            }}
            .stat-card {{
                background: #f8f9fa;
                padding: 25px;
                border-radius: 15px;
                text-align: center;
                border-left: 5px solid #1976d2;
                transition: transform 0.3s ease;
            }}
            .stat-card:hover {{
                transform: translateY(-5px);
                box-shadow: 0 10px 25px rgba(0,0,0,0.1);
            }}
            .stat-icon {{
                font-size: 32px;
                margin-bottom: 15px;
                display: block;
            }}
            .stat-title {{
                font-weight: bold;
                color: #1976d2;
                margin-bottom: 8px;
            }}
            .stat-value {{
                font-size: 18px;
                color: #333;
            }}
            .info-systeme {{
                background: linear-gradient(135deg, #e3f2fd, #bbdefb);
                padding: 25px;
                border-radius: 15px;
                margin-top: 40px;
                border: 1px solid #1976d2;
            }}
            .footer-timestamp {{
                text-align: center;
                margin-top: 40px;
                padding: 20px;
                background: #1976d2;
                color: white;
                border-radius: 12px;
                font-weight: bold;
                font-size: 16px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div style="display: flex; align-items: center; justify-content: center; margin-bottom: 20px;">
                    <div style="width: 100px; height: 100px; border: 4px solid #1976d2; border-radius: 15px; display: flex; align-items: center; justify-content: center; margin-right: 25px; font-size: 18px; font-weight: bold; color: #1976d2; background: #e3f2fd;">
                        🏠<br>KBIS
                    </div>
                    <div>
                        <div class="logo-entreprise">KBIS IMMOBILIER</div>
                        <div class="services">Achat • Vente • Location • Gestion • Nettoyage</div>
                    </div>
                </div>
            </div>
            
            <div class="status-dynamique">
                <h2 style="margin: 0; font-size: 28px;">🚀 SYSTÈME DYNAMIQUE OPÉRATIONNEL</h2>
                <p style="margin: 15px 0 0 0; font-size: 18px; opacity: 0.95;">
                    Données réelles • Format A5 • Génération automatique • Numérotation séquentielle
                </p>
            </div>
            
            <div class="stats-dynamiques">
                <div class="stat-card">
                    <span class="stat-icon">📋</span>
                    <div class="stat-title">Format Quittance</div>
                    <div class="stat-value">A5 Officiel</div>
                </div>
                <div class="stat-card">
                    <span class="stat-icon">🏠</span>
                    <div class="stat-title">Locataires</div>
                    <div class="stat-value">{len(gestionnaire.LOCATAIRES_REELS)} Actifs</div>
                </div>
                <div class="stat-card">
                    <span class="stat-icon">💰</span>
                    <div class="stat-title">Dernier N°</div>
                    <div class="stat-value">{gestionnaire.donnees['dernier_numero']}</div>
                </div>
                <div class="stat-card">
                    <span class="stat-icon">📅</span>
                    <div class="stat-title">Système</div>
                    <div class="stat-value">100% Dynamique</div>
                </div>
            </div>
            
            <div class="fonctionnalites">
                <a href="/generer-quittance-dynamique" class="btn-fonctionnalite btn-generer">
                    ✨ Générer Quittance Dynamique
                    <br><small style="font-weight: normal; opacity: 0.9;">Données réelles • Locataire aléatoire</small>
                </a>
                
                <a href="/formulaire-personnalise" class="btn-fonctionnalite btn-formulaire">
                    📝 Créateur Personnalisé
                    <br><small style="font-weight: normal; opacity: 0.9;">Saisie manuelle • Format A5</small>
                </a>
                
                <a href="/demo-locataires" class="btn-fonctionnalite btn-demo">
                    👥 Démonstration Locataires
                    <br><small style="font-weight: normal; opacity: 0.9;">Tous les locataires disponibles</small>
                </a>
                
                <a href="/historique-quittances" class="btn-fonctionnalite btn-historique">
                    📚 Historique des Quittances
                    <br><small style="font-weight: normal; opacity: 0.9;">Toutes les quittances générées</small>
                </a>
            </div>
            
            <div class="info-systeme">
                <h3 style="color: #1976d2; margin-top: 0; font-size: 24px;">ℹ️ Informations Système Dynamique</h3>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px;">
                    <div>
                        <h4 style="color: #1976d2;">✅ Fonctionnalités Actives</h4>
                        <ul style="color: #333; line-height: 1.8;">
                            <li><strong>Données dynamiques:</strong> Locataires réels</li>
                            <li><strong>Format A5:</strong> Optimisé impression</li>
                            <li><strong>Numérotation:</strong> Séquentielle automatique</li>
                            <li><strong>Calculs:</strong> Montants réalistes</li>
                        </ul>
                    </div>
                    <div>
                        <h4 style="color: #1976d2;">🎯 Nouvelles Capacités</h4>
                        <ul style="color: #333; line-height: 1.8;">
                            <li><strong>KBIS IMMOBILIER:</strong> Nom mis à jour</li>
                            <li><strong>Quartiers:</strong> Localisations réelles</li>
                            <li><strong>Historique:</strong> Sauvegarde automatique</li>
                            <li><strong>Impression:</strong> Bouton intégré</li>
                        </ul>
                    </div>
                </div>
            </div>
            
            <div class="footer-timestamp">
                🚀 SYSTÈME KBIS IMMOBILIER OPÉRATIONNEL<br>
                📅 {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}
            </div>
        </div>
    </body>
    </html>
    """

@app.route('/generer-quittance-dynamique')
def generer_quittance_dynamique():
    """Génère une quittance avec données dynamiques"""
    donnees = gestionnaire.generer_donnees_quittance_reelle()
    html = gestionnaire.generer_quittance_html(donnees)
    return Response(html, mimetype='text/html')

@app.route('/demo-locataires')
def demo_locataires():
    """Page de démonstration avec tous les locataires"""
    
    locataires_html = ""
    for i, locataire in enumerate(gestionnaire.LOCATAIRES_REELS):
        locataires_html += f"""
        <div class="locataire-card">
            <h3>👤 {locataire['nom']}</h3>
            <div class="info-locataire">
                <span><strong>Code:</strong> {locataire['code']}</span>
                <span><strong>Loyer:</strong> {locataire['loyer']:,} FCFA</span>
                <span><strong>Quartier:</strong> {locataire['quartier']}</span>
            </div>
            <a href="/quittance-locataire/{i}" class="btn-mini">Générer Quittance</a>
        </div>
        """
    
    return f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <title>👥 Démonstration Locataires - KBIS IMMOBILIER</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f0f2f5; }}
            .container {{ max-width: 1200px; margin: 0 auto; }}
            .header {{ text-align: center; margin-bottom: 40px; background: white; padding: 30px; border-radius: 15px; box-shadow: 0 5px 15px rgba(0,0,0,0.1); }}
            .locataires-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); gap: 25px; }}
            .locataire-card {{ 
                background: white; 
                padding: 25px; 
                border-radius: 12px; 
                box-shadow: 0 5px 15px rgba(0,0,0,0.1);
                transition: transform 0.3s ease;
                border-left: 4px solid #1976d2;
            }}
            .locataire-card:hover {{ transform: translateY(-5px); box-shadow: 0 8px 25px rgba(0,0,0,0.15); }}
            .locataire-card h3 {{ color: #1976d2; margin: 0 0 15px 0; font-size: 18px; }}
            .info-locataire {{ display: grid; gap: 8px; margin-bottom: 20px; }}
            .info-locataire span {{ background: #f8f9fa; padding: 8px 12px; border-radius: 6px; font-size: 14px; }}
            .btn-mini {{ 
                display: inline-block; 
                padding: 10px 20px; 
                background: #1976d2; 
                color: white; 
                text-decoration: none; 
                border-radius: 6px; 
                font-weight: bold;
                transition: background 0.3s ease;
            }}
            .btn-mini:hover {{ background: #1565c0; }}
            .retour-btn {{ 
                display: inline-block; 
                margin: 20px 0; 
                padding: 12px 25px; 
                background: #666; 
                color: white; 
                text-decoration: none; 
                border-radius: 8px; 
                font-weight: bold;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1 style="color: #1976d2; margin: 0;">👥 LOCATAIRES KBIS IMMOBILIER</h1>
                <p style="color: #666; margin: 15px 0 0 0; font-size: 16px;">
                    Cliquez sur un locataire pour générer sa quittance • Format A5 • Données réelles
                </p>
            </div>
            
            <div class="locataires-grid">
                {locataires_html}
            </div>
            
            <div style="text-align: center; margin-top: 40px;">
                <a href="/" class="retour-btn">← Retour à l'accueil</a>
                <a href="/generer-quittance-dynamique" class="retour-btn" style="background: #4caf50;">✨ Quittance Aléatoire</a>
            </div>
        </div>
    </body>
    </html>
    """

@app.route('/quittance-locataire/<int:index>')
def quittance_locataire(index):
    """Génère une quittance pour un locataire spécifique"""
    if 0 <= index < len(gestionnaire.LOCATAIRES_REELS):
        locataire = gestionnaire.LOCATAIRES_REELS[index]
        donnees = gestionnaire.generer_donnees_quittance_reelle(locataire)
        html = gestionnaire.generer_quittance_html(donnees)
        return Response(html, mimetype='text/html')
    else:
        return "Locataire non trouvé", 404

@app.route('/formulaire-personnalise', methods=['GET', 'POST'])
def formulaire_personnalise():
    """Formulaire pour créer une quittance personnalisée"""
    
    if request.method == 'POST':
        # Récupération des données du formulaire
        donnees_personnalisees = {
            'numero': gestionnaire.generer_numero_quittance(),
            'date': request.form.get('date', datetime.now().strftime('%d-%b-%y')),
            'code_location': request.form.get('code_location'),
            'recu_de': request.form.get('recu_de'),
            'montant': int(request.form.get('montant', 0)),
            'loyer_base': int(request.form.get('loyer_base', 0)),
            'mois_regle': request.form.get('mois_regle'),
            'restant_du': int(request.form.get('restant_du', 0)),
            'loyer_au_prorata': int(request.form.get('loyer_au_prorata', 0)),
            'quartier': request.form.get('quartier', 'Non spécifié'),
            'timestamp': datetime.now().isoformat()
        }
        
        # Sauvegarde dans l'historique
        gestionnaire.donnees['quittances'].append(donnees_personnalisees)
        gestionnaire.sauvegarder_donnees()
        
        html = gestionnaire.generer_quittance_html(donnees_personnalisees)
        return Response(html, mimetype='text/html')
    
    # Affichage du formulaire
    return f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <title>📝 Créateur Personnalisé - KBIS IMMOBILIER</title>
        <style>
            body {{ 
                font-family: Arial, sans-serif; 
                margin: 0; 
                padding: 20px; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                min-height: 100vh; 
            }}
            .container {{ 
                max-width: 800px; 
                margin: 0 auto; 
                background: white; 
                padding: 40px; 
                border-radius: 20px; 
                box-shadow: 0 15px 35px rgba(0,0,0,0.3); 
            }}
            .header {{ 
                text-align: center; 
                margin-bottom: 40px; 
                padding-bottom: 25px; 
                border-bottom: 3px solid #1976d2; 
            }}
            .form-grid {{ 
                display: grid; 
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); 
                gap: 25px; 
                margin-bottom: 30px; 
            }}
            .form-group {{ 
                margin-bottom: 20px; 
            }}
            label {{ 
                display: block; 
                margin-bottom: 8px; 
                font-weight: bold; 
                color: #1976d2; 
                font-size: 14px;
            }}
            input, select {{ 
                width: 100%; 
                padding: 12px 15px; 
                border: 2px solid #ddd; 
                border-radius: 8px; 
                font-size: 14px; 
                box-sizing: border-box;
                transition: border-color 0.3s ease;
            }}
            input:focus {{ 
                border-color: #1976d2; 
                outline: none; 
                box-shadow: 0 0 0 3px rgba(25, 118, 210, 0.1);
            }}
            .btn-generer {{ 
                background: linear-gradient(45deg, #1976d2, #1565c0); 
                color: white; 
                padding: 15px 40px; 
                border: none; 
                border-radius: 10px; 
                font-size: 16px; 
                font-weight: bold; 
                cursor: pointer;
                width: 100%;
                margin-top: 20px;
                transition: transform 0.3s ease;
            }}
            .btn-generer:hover {{ 
                transform: translateY(-2px); 
                box-shadow: 0 8px 25px rgba(25, 118, 210, 0.4); 
            }}
            .info-note {{ 
                background: #e8f5e8; 
                padding: 20px; 
                border-radius: 10px; 
                margin-top: 30px; 
                border-left: 4px solid #4caf50;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1 style="color: #1976d2; margin: 0; font-size: 28px;">📝 Créateur de Quittance</h1>
                <p style="color: #666; margin: 15px 0 0 0; font-size: 16px;">KBIS IMMOBILIER • Format A5 • Données personnalisées</p>
            </div>
            
            <form method="POST">
                <div class="form-grid">
                    <div>
                        <div class="form-group">
                            <label for="recu_de">👤 Nom du Locataire:</label>
                            <input type="text" id="recu_de" name="recu_de" placeholder="Ex: M. OUEDRAOGO ISSOUF" required>
                        </div>
                        
                        <div class="form-group">
                            <label for="code_location">🏠 Code Location:</label>
                            <input type="text" id="code_location" name="code_location" placeholder="Ex: 6001" required>
                        </div>
                        
                        <div class="form-group">
                            <label for="quartier">📍 Quartier:</label>
                            <input type="text" id="quartier" name="quartier" placeholder="Ex: Pissy, Ouaga 2000" required>
                        </div>
                        
                        <div class="form-group">
                            <label for="date">📅 Date:</label>
                            <input type="text" id="date" name="date" value="{datetime.now().strftime('%d-%b-%y')}" required>
                        </div>
                    </div>
                    
                    <div>
                        <div class="form-group">
                            <label for="loyer_base">💰 Loyer de Base (FCFA):</label>
                            <input type="number" id="loyer_base" name="loyer_base" placeholder="Ex: 35000" min="0" required>
                        </div>
                        
                        <div class="form-group">
                            <label for="loyer_au_prorata">📊 Prorata (FCFA):</label>
                            <input type="number" id="loyer_au_prorata" name="loyer_au_prorata" value="0" min="0">
                        </div>
                        
                        <div class="form-group">
                            <label for="montant">💵 Montant Total Payé (FCFA):</label>
                            <input type="number" id="montant" name="montant" placeholder="Sera calculé automatiquement" min="0" required>
                        </div>
                        
                        <div class="form-group">
                            <label for="restant_du">⚠️ Restant Dû (FCFA):</label>
                            <input type="number" id="restant_du" name="restant_du" value="0" min="0">
                        </div>
                    </div>
                </div>
                
                <div class="form-group">
                    <label for="mois_regle">📅 Mois Réglé:</label>
                    <input type="text" id="mois_regle" name="mois_regle" value="{gestionnaire.obtenir_mois_francais()}" required>
                </div>
                
                <button type="submit" class="btn-generer">🚀 Générer la Quittance (Format A5)</button>
            </form>
            
            <div class="info-note">
                <h4 style="color: #2e7d32; margin-top: 0;">ℹ️ Informations</h4>
                <ul style="color: #2e7d32; margin: 0; line-height: 1.6;">
                    <li><strong>Numérotation:</strong> Automatique et séquentielle</li>
                    <li><strong>Format:</strong> A5 optimisé pour l'impression</li>
                    <li><strong>Sauvegarde:</strong> Automatique dans l'historique</li>
                    <li><strong>Bouton impression:</strong> Intégré dans la quittance</li>
                </ul>
            </div>
            
            <div style="text-align: center; margin-top: 30px;">
                <a href="/" style="color: #1976d2; text-decoration: none; font-weight: bold;">← Retour à l'accueil</a>
            </div>
        </div>
        
        <script>
            // Calcul automatique du montant total
            document.getElementById('loyer_base').addEventListener('input', calculerTotal);
            document.getElementById('loyer_au_prorata').addEventListener('input', calculerTotal);
            
            function calculerTotal() {{
                const loyerBase = parseInt(document.getElementById('loyer_base').value) || 0;
                const prorata = parseInt(document.getElementById('loyer_au_prorata').value) || 0;
                const total = loyerBase + prorata;
                document.getElementById('montant').value = total;
            }}
        </script>
    </body>
    </html>
    """

@app.route('/historique-quittances')
def historique_quittances():
    """Affiche l'historique des quittances générées"""
    
    quittances = gestionnaire.donnees.get('quittances', [])
    
    if not quittances:
        historique_html = "<p style='text-align: center; color: #666; font-style: italic;'>Aucune quittance générée pour le moment.</p>"
    else:
        historique_html = ""
        for i, quittance in enumerate(reversed(quittances[-20:])):  # 20 dernières quittances
            date_obj = datetime.fromisoformat(quittance.get('timestamp', datetime.now().isoformat()))
            historique_html += f"""
            <div class="quittance-historique">
                <div class="quittance-info">
                    <h4>📋 Quittance N° {quittance['numero']}</h4>
                    <div class="details-grid">
                        <span><strong>👤 Locataire:</strong> {quittance['recu_de']}</span>
                        <span><strong>💰 Montant:</strong> {quittance['montant']:,} F</span>
                        <span><strong>📅 Date:</strong> {quittance['date']}</span>
                        <span><strong>🏠 Code:</strong> {quittance['code_location']}</span>
                        <span><strong>📍 Quartier:</strong> {quittance.get('quartier', 'N/A')}</span>
                        <span><strong>🕒 Généré:</strong> {date_obj.strftime('%d/%m/%Y %H:%M')}</span>
                    </div>
                </div>
                <div class="actions">
                    <a href="/regenerer-quittance/{len(quittances) - i - 1}" class="btn-action">🔄 Régénérer</a>
                </div>
            </div>
            """
    
    return f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <title>📚 Historique - KBIS IMMOBILIER</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f7fa; }}
            .container {{ max-width: 1200px; margin: 0 auto; }}
            .header {{ 
                text-align: center; 
                margin-bottom: 40px; 
                background: white; 
                padding: 30px; 
                border-radius: 15px; 
                box-shadow: 0 5px 15px rgba(0,0,0,0.1); 
            }}
            .stats-rapides {{ 
                display: grid; 
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
                gap: 20px; 
                margin-bottom: 40px; 
            }}
            .stat-rapide {{ 
                background: white; 
                padding: 20px; 
                border-radius: 10px; 
                text-align: center; 
                box-shadow: 0 3px 10px rgba(0,0,0,0.1);
                border-left: 4px solid #1976d2;
            }}
            .quittances-liste {{ display: grid; gap: 20px; }}
            .quittance-historique {{ 
                background: white; 
                padding: 25px; 
                border-radius: 12px; 
                box-shadow: 0 5px 15px rgba(0,0,0,0.1);
                display: flex;
                justify-content: space-between;
                align-items: center;
                transition: transform 0.3s ease;
            }}
            .quittance-historique:hover {{ transform: translateX(5px); }}
            .quittance-info h4 {{ color: #1976d2; margin: 0 0 15px 0; }}
            .details-grid {{ 
                display: grid; 
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
                gap: 10px; 
                font-size: 14px;
            }}
            .btn-action {{ 
                display: inline-block; 
                padding: 8px 16px; 
                background: #1976d2; 
                color: white; 
                text-decoration: none; 
                border-radius: 6px; 
                font-size: 14px;
                margin: 2px;
            }}
            .retour-btn {{ 
                display: inline-block; 
                margin: 20px 0; 
                padding: 12px 25px; 
                background: #666; 
                color: white; 
                text-decoration: none; 
                border-radius: 8px; 
                font-weight: bold;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1 style="color: #1976d2; margin: 0;">📚 HISTORIQUE DES QUITTANCES</h1>
                <p style="color: #666; margin: 15px 0 0 0;">KBIS IMMOBILIER • Toutes les quittances générées</p>
            </div>
            
            <div class="stats-rapides">
                <div class="stat-rapide">
                    <h3 style="color: #1976d2; margin: 0;">📋 Total Quittances</h3>
                    <p style="font-size: 24px; font-weight: bold; margin: 10px 0 0 0;">{len(quittances)}</p>
                </div>
                <div class="stat-rapide">
                    <h3 style="color: #1976d2; margin: 0;">🔢 Dernier N°</h3>
                    <p style="font-size: 24px; font-weight: bold; margin: 10px 0 0 0;">{gestionnaire.donnees['dernier_numero']}</p>
                </div>
                <div class="stat-rapide">
                    <h3 style="color: #1976d2; margin: 0;">👥 Locataires</h3>
                    <p style="font-size: 24px; font-weight: bold; margin: 10px 0 0 0;">{len(set(q['recu_de'] for q in quittances))}</p>
                </div>
                <div class="stat-rapide">
                    <h3 style="color: #1976d2; margin: 0;">📅 Aujourd'hui</h3>
                    <p style="font-size: 24px; font-weight: bold; margin: 10px 0 0 0;">{datetime.now().strftime('%d/%m')}</p>
                </div>
            </div>
            
            <div class="quittances-liste">
                {historique_html}
            </div>
            
            <div style="text-align: center; margin-top: 40px;">
                <a href="/" class="retour-btn">← Retour à l'accueil</a>
                <a href="/generer-quittance-dynamique" class="retour-btn" style="background: #4caf50;">✨ Nouvelle Quittance</a>
            </div>
        </div>
    </body>
    </html>
    """

@app.route('/regenerer-quittance/<int:index>')
def regenerer_quittance(index):
    """Régénère une quittance depuis l'historique"""
    quittances = gestionnaire.donnees.get('quittances', [])
    
    if 0 <= index < len(quittances):
        donnees = quittances[index]
        html = gestionnaire.generer_quittance_html(donnees)
        return Response(html, mimetype='text/html')
    else:
        return "Quittance non trouvée", 404

if __name__ == '__main__':
    print("🏢 KBIS IMMOBILIER - Système de Quittances Dynamiques")
    print("=" * 60)
    print("🚀 Serveur opérationnel sur: http://localhost:5000")
    print("✨ Génération dynamique: http://localhost:5000/generer-quittance-dynamique")
    print("👥 Démonstration locataires: http://localhost:5000/demo-locataires")
    print("📝 Formulaire personnalisé: http://localhost:5000/formulaire-personnalise")
    print("📚 Historique: http://localhost:5000/historique-quittances")
    print("=" * 60)
    print(f"📋 Dernier numéro de quittance: {gestionnaire.donnees['dernier_numero']}")
    print(f"👥 Nombre de locataires: {len(gestionnaire.LOCATAIRES_REELS)}")
    print("🖨️ Format A5 prêt pour impression")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=5000)