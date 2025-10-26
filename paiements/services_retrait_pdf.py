#!/usr/bin/env python
"""
Service de génération PDF pour les retraits avec templates
"""

import logging
from datetime import datetime
from decimal import Decimal
from django.utils import timezone
from django.template.loader import render_to_string
from django.http import HttpResponse
from django.db.models import Sum
from io import BytesIO

from core.models import TemplateDocument, ConfigurationEntreprise
from .models import ChargeDeductible, ChargeBailleur
from proprietes.models import Propriete

logger = logging.getLogger(__name__)


class ServiceGenerationRetraitPDF:
    """Service pour la génération de PDF de retraits avec templates."""
    
    def __init__(self):
        self.logger = logger
    
    def generer_pdf_retrait(self, retrait, template_type='retrait_standard', user=None):
        """
        Génère un PDF de retrait avec template.
        
        Args:
            retrait: Instance de RetraitBailleur
            template_type: Type de template à utiliser
            user: Utilisateur qui génère le document
        
        Returns:
            HttpResponse: PDF généré
        """
        try:
            # Récupérer le template
            template = self._get_template_retrait(template_type)
            
            # Récupérer la configuration de l'entreprise
            config = ConfigurationEntreprise.get_configuration_active()
            
            # Préparer les données pour le template
            donnees_retrait = self._preparer_donnees_retrait(retrait)
            
            # Générer le HTML avec le template
            html_content = render_to_string(
                'paiements/templates_retrait/retrait_pdf.html',
                {
                    'retrait': retrait,
                    'donnees': donnees_retrait,
                    'template': template,
                    'config': config,
                    'date_generation': timezone.now(),
                    'user': user,  # Ajouter l'utilisateur au contexte
                }
            )
            
            # Générer le PDF avec xhtml2pdf
            from xhtml2pdf import pisa
            pdf_buffer = BytesIO()
            pisa_status = pisa.CreatePDF(html_content, dest=pdf_buffer)
            
            if pisa_status.err:
                self.logger.error("Erreur lors de la génération PDF: %s", pisa_status.err)
                raise Exception(f"Erreur lors de la génération PDF: {pisa_status.err}")
            
            # Préparer la réponse
            pdf_content = pdf_buffer.getvalue()
            pdf_buffer.close()
            
            response = HttpResponse(pdf_content, content_type='application/pdf')
            filename = f"retrait_{retrait.bailleur.get_nom_complet().replace(' ', '_')}_{retrait.mois_retrait.strftime('%Y_%m')}.pdf"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            # Enregistrer dans l'historique
            self._enregistrer_historique(template, retrait, filename, len(pdf_content))
            
            return response
            
        except Exception as e:
            self.logger.error("Erreur lors de la génération PDF du retrait: %s", str(e))
            raise
    
    def _get_template_retrait(self, template_type=None):
        """Récupère le template de retrait."""
        try:
            # Chercher un template spécifique pour les retraits
            template = TemplateDocument.objects.filter(
                type_document='retrait',
                actif=True
            ).first()
            
            if not template:
                # Créer un template par défaut pour les retraits
                template = self._creer_template_retrait_defaut()
            
            return template
            
        except Exception as e:
            self.logger.error("Erreur lors de la récupération du template: %s", str(e))
            raise
    
    def _creer_template_retrait_defaut(self):
        """Crée un template par défaut pour les retraits."""
        template_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Retrait Bailleur - {{ config.nom_entreprise }}</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 0; padding: 20px; }
                .header { text-align: center; margin-bottom: 30px; }
                .logo { max-width: 150px; height: auto; }
                .title { font-size: 24px; font-weight: bold; color: #2c3e50; margin: 20px 0; }
                .subtitle { font-size: 18px; color: #7f8c8d; margin-bottom: 30px; }
                .info-section { margin: 20px 0; }
                .info-title { font-size: 16px; font-weight: bold; color: #34495e; margin-bottom: 10px; }
                .info-content { background: #f8f9fa; padding: 15px; border-radius: 5px; }
                .table { width: 100%; border-collapse: collapse; margin: 20px 0; }
                .table th, .table td { border: 1px solid #ddd; padding: 12px; text-align: left; }
                .table th { background: #3498db; color: white; font-weight: bold; }
                .table tr:nth-child(even) { background: #f2f2f2; }
                .total-section { margin-top: 30px; padding: 20px; background: #ecf0f1; border-radius: 5px; }
                .total-line { display: flex; justify-content: space-between; margin: 10px 0; }
                .total-final { font-size: 18px; font-weight: bold; color: #27ae60; border-top: 2px solid #27ae60; padding-top: 10px; }
                .footer { margin-top: 50px; text-align: center; font-size: 12px; color: #7f8c8d; }
            </style>
        </head>
        <body>
            <div class="header">
                {% if config.logo %}
                <img src="{{ config.logo.url }}" alt="Logo" class="logo">
                {% endif %}
                <h1 class="title">{{ config.nom_entreprise }}</h1>
                <p class="subtitle">RETRAIT BAILLEUR - {{ retrait.mois_retrait|date:"F Y"|upper }}</p>
            </div>
            
            <div class="info-section">
                <h3 class="info-title">Informations du Bailleur</h3>
                <div class="info-content">
                    <p><strong>Nom:</strong> {{ retrait.bailleur.get_nom_complet }}</p>
                    <p><strong>Email:</strong> {{ retrait.bailleur.email|default:"Non renseigné" }}</p>
                    <p><strong>Téléphone:</strong> {{ retrait.bailleur.telephone|default:"Non renseigné" }}</p>
                </div>
            </div>
            
            <div class="info-section">
                <h3 class="info-title">Détail des Propriétés</h3>
                <table class="table">
                    <thead>
                        <tr>
                            <th>Propriété</th>
                            <th>Loyer Brut</th>
                            <th>Charges Déductibles</th>
                            <th>Charges Bailleur</th>
                            <th>Net à Payer</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for propriete in donnees.proprietes %}
                        <tr>
                            <td>{{ propriete.titre }}</td>
                            <td>{{ propriete.loyer_brut|floatformat:0 }} F CFA</td>
                            <td>{{ propriete.charges_deductibles|floatformat:0 }} F CFA</td>
                            <td>{{ propriete.charges_bailleur|floatformat:0 }} F CFA</td>
                            <td>{{ propriete.montant_net|floatformat:0 }} F CFA</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
            
            <div class="total-section">
                <div class="total-line">
                    <span>Total Loyers Bruts:</span>
                    <span>{{ donnees.total_loyers_bruts|floatformat:0 }} F CFA</span>
                </div>
                <div class="total-line">
                    <span>Total Charges Déductibles:</span>
                    <span>- {{ donnees.total_charges_deductibles|floatformat:0 }} F CFA</span>
                </div>
                <div class="total-line">
                    <span>Total Charges Bailleur:</span>
                    <span>- {{ donnees.total_charges_bailleur|floatformat:0 }} F CFA</span>
                </div>
                <div class="total-line total-final">
                    <span>MONTANT NET À PAYER:</span>
                    <span>{{ donnees.montant_net_total|floatformat:0 }} F CFA</span>
                </div>
            </div>
            
            <div class="footer">
                <p>Document généré le {{ date_generation|date:"d/m/Y à H:i" }}</p>
                {% if user %}
                <p><strong>Généré par :</strong> {{ user.get_full_name|default:user.username }}</p>
                {% endif %}
                <p>{{ config.nom_entreprise }} - {{ config.adresse|default:"" }}</p>
            </div>
        </body>
        </html>
        """
        
        template = TemplateDocument.objects.create(
            nom='Template Retrait Standard',
            type_document='retrait',
            description='Template par défaut pour les retraits de bailleurs',
            template_html=template_html,
            format_page='A4',
            par_defaut=True,
            actif=True
        )
        
        return template
    
    def _preparer_donnees_retrait(self, retrait):
        """Prépare les données détaillées du retrait."""
        # Récupérer les propriétés du bailleur avec leurs détails
        proprietes = Propriete.objects.filter(
            bailleur=retrait.bailleur,
            is_deleted=False
        ).select_related('type_bien')
        
        proprietes_details = []
        total_loyers_bruts = Decimal('0')
        total_charges_deductibles = Decimal('0')
        total_charges_bailleur = Decimal('0')
        
        for propriete in proprietes:
            # Calculer les loyers pour cette propriété
            loyer_brut = propriete.get_loyer_actuel_calcule()
            
            # Calculer les charges déductibles
            charges_deductibles = ChargeDeductible.objects.filter(
                contrat__propriete=propriete,
                date_charge__year=retrait.mois_retrait.year,
                date_charge__month=retrait.mois_retrait.month,
                est_valide=True
            ).aggregate(total=Sum('montant'))['total'] or Decimal('0')
            
            # Calculer les charges bailleur (via le bailleur)
            charges_bailleur = ChargeBailleur.objects.filter(
                bailleur=retrait.bailleur,
                date_charge__year=retrait.mois_retrait.year,
                date_charge__month=retrait.mois_retrait.month,
                statut__in=['en_attente', 'valide']
            ).aggregate(total=Sum('montant'))['total'] or Decimal('0')
            
            # Montant net pour cette propriété
            montant_net = loyer_brut - charges_deductibles - charges_bailleur
            
            proprietes_details.append({
                'propriete': propriete,
                'loyer_brut': loyer_brut,
                'charges_deductibles': charges_deductibles,
                'charges_bailleur': charges_bailleur,
                'montant_net': montant_net,
            })
            
            # Cumuler les totaux
            total_loyers_bruts += loyer_brut
            total_charges_deductibles += charges_deductibles
            total_charges_bailleur += charges_bailleur
        
        montant_net_total = total_loyers_bruts - total_charges_deductibles - total_charges_bailleur
        
        return {
            'proprietes': proprietes_details,
            'total_loyers_bruts': total_loyers_bruts,
            'total_charges_deductibles': total_charges_deductibles,
            'total_charges_bailleur': total_charges_bailleur,
            'montant_net_total': montant_net_total,
        }
    
    def _enregistrer_historique(self, template, retrait, nom_fichier, taille_fichier):
        """Enregistre l'historique de génération."""
        from core.models import HistoriqueGeneration
        
        HistoriqueGeneration.objects.create(
            template=template,
            type_document='retrait',
            nom_fichier=nom_fichier,
            taille_fichier=taille_fichier,
            reference_objet=str(retrait.id),
            type_objet='RetraitBailleur',
            succes=True
        )
    
    def generer_pdf_retrait_multiple(self, retraits, template_type='retrait_standard', user=None):
        """
        Génère un PDF consolidé pour plusieurs retraits.
        
        Args:
            retraits: Liste d'instances de RetraitBailleur
            template_type: Type de template à utiliser
        
        Returns:
            HttpResponse: PDF généré
        """
        try:
            # Récupérer le template
            template = self._get_template_retrait(template_type)
            
            # Récupérer la configuration de l'entreprise
            config = ConfigurationEntreprise.get_configuration_active()
            
            # Préparer les données consolidées
            donnees_consolidees = self._preparer_donnees_retraits_multiple(retraits)
            
            # Générer le HTML avec le template
            html_content = render_to_string(
                'paiements/templates_retrait/retraits_multiple_pdf.html',
                {
                    'retraits': retraits,
                    'donnees': donnees_consolidees,
                    'template': template,
                    'config': config,
                    'date_generation': timezone.now(),
                    'user': user,  # Ajouter l'utilisateur au contexte
                }
            )
            
            # Générer le PDF avec xhtml2pdf
            from xhtml2pdf import pisa
            pdf_buffer = BytesIO()
            pisa_status = pisa.CreatePDF(html_content, dest=pdf_buffer)
            
            if pisa_status.err:
                self.logger.error("Erreur lors de la génération PDF: %s", pisa_status.err)
                raise Exception(f"Erreur lors de la génération PDF: {pisa_status.err}")
            
            # Préparer la réponse
            pdf_content = pdf_buffer.getvalue()
            pdf_buffer.close()
            
            response = HttpResponse(pdf_content, content_type='application/pdf')
            filename = f"retraits_consolides_{datetime.now().strftime('%Y_%m_%d')}.pdf"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            return response
            
        except Exception as e:
            self.logger.error("Erreur lors de la génération PDF des retraits multiples: %s", str(e))
            raise
    
    def _preparer_donnees_retraits_multiple(self, retraits):
        """Prépare les données consolidées pour plusieurs retraits."""
        total_loyers_bruts = Decimal('0')
        total_charges_deductibles = Decimal('0')
        total_charges_bailleur = Decimal('0')
        total_net = Decimal('0')
        
        retraits_details = []
        
        for retrait in retraits:
            donnees_retrait = self._preparer_donnees_retrait(retrait)
            
            retraits_details.append({
                'retrait': retrait,
                'donnees': donnees_retrait,
            })
            
            # Cumuler les totaux
            total_loyers_bruts += donnees_retrait['total_loyers_bruts']
            total_charges_deductibles += donnees_retrait['total_charges_deductibles']
            total_charges_bailleur += donnees_retrait['total_charges_bailleur']
            total_net += donnees_retrait['montant_net_total']
        
        return {
            'retraits_details': retraits_details,
            'total_loyers_bruts': total_loyers_bruts,
            'total_charges_deductibles': total_charges_deductibles,
            'total_charges_bailleur': total_charges_bailleur,
            'total_net': total_net,
            'nombre_retraits': len(retraits),
        }
