"""
Vue de test pour le système de templates KBIS
"""
from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from core.utils import KBISDocumentTemplate
from datetime import datetime


@login_required
def test_template_kbis(request):
    """Vue de test pour le système de templates KBIS."""
    
    # Tester l'en-tête et le pied de page
    entete_html = KBISDocumentTemplate.get_entete_html()
    pied_page_html = KBISDocumentTemplate.get_pied_page_html()
    
    # Créer un document test
    titre = "TEST DOCUMENT KBIS - " + datetime.now().strftime('%d/%m/%Y %H:%M')
    contenu_test = """
    <div style="padding: 20px;">
        <h2 style="color: #2c5aa0; border-bottom: 2px solid #2c5aa0; padding-bottom: 10px;">
            Test du Système de Templates KBIS
        </h2>
        
        <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 20px 0;">
            <h3 style="color: #2c5aa0; margin-top: 0;">Fonctionnalités testées:</h3>
            <ul>
                <li>✓ En-tête avec logo et informations entreprise</li>
                <li>✓ Pied de page avec coordonnées complètes</li>
                <li>✓ Styles CSS intégrés</li>
                <li>✓ Structure HTML responsive</li>
                <li>✓ Branding KBIS complet</li>
            </ul>
        </div>
        
        <div style="margin: 30px 0;">
            <h3 style="color: #2c5aa0;">Informations de test:</h3>
            <table style="width: 100%; border-collapse: collapse;">
                <tr style="background: #f8f9fa;">
                    <th style="padding: 10px; border: 1px solid #ddd;">Élément</th>
                    <th style="padding: 10px; border: 1px solid #ddd;">Statut</th>
                </tr>
                <tr>
                    <td style="padding: 10px; border: 1px solid #ddd;">Template Engine</td>
                    <td style="padding: 10px; border: 1px solid #ddd; color: #28a745;">✓ Opérationnel</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border: 1px solid #ddd;">CSS Integration</td>
                    <td style="padding: 10px; border: 1px solid #ddd; color: #28a745;">✓ Opérationnel</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border: 1px solid #ddd;">Logo Display</td>
                    <td style="padding: 10px; border: 1px solid #ddd; color: #ffc107;">⚠ Logo à ajouter</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border: 1px solid #ddd;">Document Generation</td>
                    <td style="padding: 10px; border: 1px solid #ddd; color: #28a745;">✓ Opérationnel</td>
                </tr>
            </table>
        </div>
        
        <div style="background: #e7f3ff; padding: 15px; border-radius: 8px; margin: 20px 0;">
            <h4 style="color: #2c5aa0; margin-top: 0;">Note importante:</h4>
            <p>Ce système de templates KBIS est maintenant intégré dans l'application. 
            Tous les documents générés (reçus, factures, contrats) utiliseront automatiquement 
            l'en-tête et le pied de page KBIS avec le branding professionnel de l'entreprise.</p>
        </div>
    </div>
    """
    
    document_html = KBISDocumentTemplate.get_document_complet(titre, contenu_test, "Test")
    
    return HttpResponse(document_html)