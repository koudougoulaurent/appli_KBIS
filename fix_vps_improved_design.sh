#!/bin/bash

# Script pour ameliorer le design et la presentation du PDF du recapitulatif mensuel
echo "Amelioration du design et de la presentation du PDF du recapitulatif mensuel..."

cd /var/www/kbis_immobilier

# 1. Corriger les references RecapitulatifMensuelBailleur
echo "1. Correction des references RecapitulatifMensuelBailleur..."

files=(
    "paiements/views_recus.py"
    "paiements/views_kbis_recus.py"
    "paiements/forms.py"
    "paiements/services_recus.py"
    "paiements/views_charges_avancees.py"
)

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "Correction de $file..."
        cp "$file" "$file.backup"
        sed -i 's/RecapitulatifMensuelBailleur/RecapMensuel/g' "$file"
        echo "  OK: $file corrige"
    else
        echo "  ATTENTION: $file introuvable"
    fi
done

# 2. Corriger les imports manquants
echo "2. Correction des imports manquants..."

# Corriger views_recus.py
if [ -f "paiements/views_recus.py" ]; then
    echo "Correction des imports dans views_recus.py..."
    sed -i 's/# from .models import RecuRecapitulatif, RecapMensuel  # Modeles supprimes/from .models import RecapMensuel, RecuRecapitulatif/' "paiements/views_recus.py"
    sed -i 's/from .models import RecuRecapitulatif, RecapMensuel/from .models import RecapMensuel, RecuRecapitulatif/' "paiements/views_recus.py"
    sed -i 's/from .models import RecapMensuel$/from .models import RecapMensuel, RecuRecapitulatif/' "paiements/views_recus.py"
    echo "  OK: views_recus.py corrige"
fi

# Corriger views_charges_avancees.py
if [ -f "paiements/views_charges_avancees.py" ]; then
    echo "Correction des imports dans views_charges_avancees.py..."
    sed -i 's/# from .models import RecapMensuel  # Modele supprime/from .models import RecapMensuel/' "paiements/views_charges_avancees.py"
    echo "  OK: views_charges_avancees.py corrige"
fi

# Corriger views_kbis_recus.py
if [ -f "paiements/views_kbis_recus.py" ]; then
    echo "Correction des imports dans views_kbis_recus.py..."
    sed -i 's/# from .models import RecapMensuel  # Modele supprime/from .models import RecapMensuel/' "paiements/views_kbis_recus.py"
    echo "  OK: views_kbis_recus.py corrige"
fi

# 3. Corriger UNIQUEMENT la relation ForeignKey
echo "3. Correction UNIQUEMENT de la relation ForeignKey..."

# Creer un script Python pour corriger UNIQUEMENT la relation
cat > fix_foreign_key_only.py << 'EOF'
#!/usr/bin/env python3

def fix_foreign_key_only():
    # Lire le fichier models.py
    with open('paiements/models.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Creer une sauvegarde
    with open('paiements/models.py.backup_fk_only', 'w', encoding='utf-8') as f:
        f.write(content)
    
    # UNIQUEMENT : Remplacer OneToOneField par ForeignKey avec null=True, blank=True
    old_relation = """recapitulatif = models.OneToOneField(
        RecapMensuel,
        on_delete=models.CASCADE,
        related_name='recu',
        verbose_name=_("Récapitulatif")
    )"""
    
    new_relation = """recapitulatif = models.ForeignKey(
        RecapMensuel,
        on_delete=models.CASCADE,
        related_name='recus',
        verbose_name=_("Récapitulatif"),
        null=True,
        blank=True
    )"""
    
    if old_relation in content:
        content = content.replace(old_relation, new_relation)
        print("OK: Relation OneToOneField remplacee par ForeignKey avec null=True, blank=True")
    else:
        print("ATTENTION: Relation OneToOneField non trouvee")
    
    # Sauvegarder le fichier modifie
    with open('paiements/models.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("OK: Correction UNIQUEMENT de la FOREIGN KEY terminee")

if __name__ == '__main__':
    fix_foreign_key_only()
EOF

# Executer le script de correction UNIQUEMENT de la FOREIGN KEY
python fix_foreign_key_only.py

# Supprimer le script temporaire
rm fix_foreign_key_only.py

# 4. Ameliorer le design du PDF
echo "4. Amelioration du design du PDF..."

# Creer un script Python pour ameliorer le design du PDF
cat > improve_pdf_design.py << 'EOF'
#!/usr/bin/env python3

def improve_pdf_design():
    # Lire le fichier models.py
    with open('paiements/models.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Creer une sauvegarde
    with open('paiements/models.py.backup_improved_design', 'w', encoding='utf-8') as f:
        f.write(content)
    
    # Nouvelle methode generer_pdf_recapitulatif avec design ameliore
    new_method = '''    def generer_pdf_recapitulatif(self):
        """Génère le PDF du récapitulatif mensuel avec ReportLab - DESIGN AMÉLIORÉ ET DÉTAILLÉ."""
        from django.utils import timezone
        from io import BytesIO
        from datetime import timedelta
        from decimal import Decimal
        
        try:
            # Utiliser ReportLab pour une génération PDF fiable
            from reportlab.lib.pagesizes import A4
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import cm
            from reportlab.lib import colors
            from reportlab.graphics.shapes import Drawing, Rect
            from reportlab.graphics import renderPDF
            
            # Créer le buffer pour le PDF
            pdf_buffer = BytesIO()
            doc = SimpleDocTemplate(
                pdf_buffer,
                pagesize=A4,
                rightMargin=1.5*cm,
                leftMargin=1.5*cm,
                topMargin=2*cm,
                bottomMargin=2*cm
            )
            
            # Styles améliorés
            styles = getSampleStyleSheet()
            
            # Style pour le titre principal
            title_style = ParagraphStyle(
                'MainTitle',
                parent=styles['Heading1'],
                fontSize=20,
                spaceAfter=25,
                alignment=1,  # Centré
                textColor=colors.darkblue,
                fontName='Helvetica-Bold'
            )
            
            # Style pour les sous-titres
            subtitle_style = ParagraphStyle(
                'Subtitle',
                parent=styles['Heading2'],
                fontSize=14,
                spaceAfter=12,
                textColor=colors.darkblue,
                fontName='Helvetica-Bold',
                borderWidth=1,
                borderColor=colors.lightblue,
                borderPadding=8,
                backColor=colors.lightgrey
            )
            
            # Style pour les informations importantes
            info_style = ParagraphStyle(
                'Info',
                parent=styles['Normal'],
                fontSize=11,
                spaceAfter=8,
                textColor=colors.darkgreen,
                fontName='Helvetica-Bold'
            )
            
            # Style normal amélioré
            normal_style = ParagraphStyle(
                'Normal',
                parent=styles['Normal'],
                fontSize=10,
                spaceAfter=6,
                fontName='Helvetica'
            )
            
            # Style pour les totaux
            total_style = ParagraphStyle(
                'Total',
                parent=styles['Normal'],
                fontSize=12,
                spaceAfter=8,
                textColor=colors.darkred,
                fontName='Helvetica-Bold',
                alignment=1
            )
            
            # Contenu du PDF
            story = []
            
            # Récupérer la configuration de l'entreprise
            from core.models import ConfigurationEntreprise
            from core.utils import ajouter_en_tete_entreprise_reportlab, ajouter_pied_entreprise_reportlab
            config = ConfigurationEntreprise.get_configuration_active()
            
            # En-tête de l'entreprise
            ajouter_en_tete_entreprise_reportlab(story, config)
            
            # Titre principal avec style amélioré
            story.append(Paragraph("RÉCAPITULATIF MENSUEL", title_style))
            story.append(Spacer(1, 15))
            
            # Informations du bailleur avec style amélioré
            story.append(Paragraph(f"<b>Bailleur:</b> {self.bailleur.get_nom_complet()}", info_style))
            story.append(Paragraph(f"<b>Mois:</b> {self.mois_recap.strftime('%B %Y')}", info_style))
            story.append(Paragraph(f"<b>Date de génération:</b> {timezone.now().strftime('%d/%m/%Y à %H:%M')}", normal_style))
            story.append(Spacer(1, 20))
            
            # Résumé financier avec design amélioré
            story.append(Paragraph("RÉSUMÉ FINANCIER", subtitle_style))
            story.append(Spacer(1, 10))
            
            # Tableau des montants avec design amélioré
            montants_data = [
                ['Description', 'Montant (F CFA)', 'Pourcentage'],
                ['Loyer brut total', f"{self.total_loyers_bruts:,.0f}", "100%"],
                ['Charges déductibles', f"{self.total_charges_deductibles:,.0f}", f"{(self.total_charges_deductibles/self.total_loyers_bruts*100):.1f}%" if self.total_loyers_bruts > 0 else "0%"],
                ['Charges bailleur', f"{self.total_charges_bailleur or 0:,.0f}", f"{(self.total_charges_bailleur/self.total_loyers_bruts*100):.1f}%" if self.total_loyers_bruts > 0 else "0%"],
                ['', '', ''],
                ['TOTAL NET À PAYER', f"{self.total_net_a_payer:,.0f}", f"{(self.total_net_a_payer/self.total_loyers_bruts*100):.1f}%" if self.total_loyers_bruts > 0 else "0%"],
            ]
            
            montants_table = Table(montants_data, colWidths=[6*cm, 3*cm, 2*cm])
            montants_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (2, 4), colors.lightgrey),
                ('BACKGROUND', (0, 5), (-1, 5), colors.lightblue),
                ('FONTNAME', (0, 5), (-1, 5), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 5), (-1, 5), 12),
                ('TEXTCOLOR', (0, 5), (-1, 5), colors.darkred),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            
            story.append(montants_table)
            story.append(Spacer(1, 20))
            
            # Statistiques détaillées avec design amélioré
            story.append(Paragraph("STATISTIQUES DÉTAILLÉES", subtitle_style))
            story.append(Spacer(1, 10))
            
            # Calculer des statistiques supplémentaires
            taux_occupation = (self.nombre_contrats_actifs / self.nombre_proprietes * 100) if self.nombre_proprietes > 0 else 0
            taux_paiement = (self.nombre_paiements_recus / self.nombre_contrats_actifs * 100) if self.nombre_contrats_actifs > 0 else 0
            
            stats_data = [
                ['Description', 'Nombre', 'Pourcentage', 'Observations'],
                ['Propriétés totales', str(self.nombre_proprietes), "100%", "Toutes les propriétés"],
                ['Contrats actifs', str(self.nombre_contrats_actifs), f"{taux_occupation:.1f}%", "Taux d'occupation"],
                ['Paiements reçus', str(self.nombre_paiements_recus), f"{taux_paiement:.1f}%", "Taux de paiement"],
                ['', '', '', ''],
                ['RÉCAPITULATIF', '', '', ''],
                ['Loyer moyen par contrat', f"{self.total_loyers_bruts/self.nombre_contrats_actifs:,.0f}" if self.nombre_contrats_actifs > 0 else "0", "F CFA", "Par mois"],
                ['Charges moyennes', f"{(self.total_charges_deductibles + (self.total_charges_bailleur or 0))/self.nombre_contrats_actifs:,.0f}" if self.nombre_contrats_actifs > 0 else "0", "F CFA", "Par mois"],
            ]
            
            stats_table = Table(stats_data, colWidths=[4*cm, 2*cm, 2*cm, 4*cm])
            stats_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkgreen),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, 3), colors.lightgreen),
                ('BACKGROUND', (0, 5), (-1, -1), colors.lightyellow),
                ('FONTNAME', (0, 5), (-1, -1), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            
            story.append(stats_table)
            story.append(Spacer(1, 20))
            
            # Détails des propriétés et contrats avec design amélioré
            story.append(Paragraph("DÉTAILS DES PROPRIÉTÉS ET CONTRATS", subtitle_style))
            story.append(Spacer(1, 10))
            
            # Récupérer les détails des propriétés
            proprietes_details = self.get_proprietes_details()
            
            if proprietes_details:
                # En-tête du tableau détaillé avec plus de colonnes
                details_data = [
                    ['Propriété', 'Locataire', 'Loyer', 'Charges', 'Net à payer', 'Statut']
                ]
                
                for detail in proprietes_details:
                    # Déterminer le statut du contrat
                    statut_contrat = "Actif"
                    if detail['contrat'].est_resilie:
                        statut_contrat = "Résilié"
                    elif not detail['contrat'].est_actif:
                        statut_contrat = "Inactif"
                    
                    details_data.append([
                        detail['adresse_complete'][:30] + "..." if len(detail['adresse_complete']) > 30 else detail['adresse_complete'],
                        detail['locataire'].get_nom_complet() if detail['locataire'] else 'N/A',
                        f"{detail['loyer_mensuel']:,.0f}",
                        f"{detail['charges_deductibles']:,.0f}",
                        f"{detail['net_a_payer']:,.0f}",
                        statut_contrat
                    ])
                
                details_table = Table(details_data, colWidths=[3*cm, 3*cm, 2*cm, 2*cm, 2*cm, 2*cm])
                details_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('FONTSIZE', (0, 1), (-1, -1), 8),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
                ]))
                
                story.append(details_table)
                story.append(Spacer(1, 20))
            
            # Garanties financières avec design amélioré
            if self.total_cautions_requises > 0 or self.total_avances_requises > 0:
                story.append(Paragraph("GARANTIES FINANCIÈRES", subtitle_style))
                story.append(Spacer(1, 10))
                
                # Calculer les pourcentages de garanties
                taux_cautions = (self.total_cautions_versees / self.total_cautions_requises * 100) if self.total_cautions_requises > 0 else 0
                taux_avances = (self.total_avances_versees / self.total_avances_requises * 100) if self.total_avances_requises > 0 else 0
                
                garanties_data = [
                    ['Description', 'Montant requis', 'Montant versé', 'Pourcentage', 'Statut'],
                    ['Cautions', f"{self.total_cautions_requises:,.0f}", f"{self.total_cautions_versees:,.0f}", f"{taux_cautions:.1f}%", "✓" if taux_cautions >= 100 else "✗"],
                    ['Avances', f"{self.total_avances_requises:,.0f}", f"{self.total_avances_versees:,.0f}", f"{taux_avances:.1f}%", "✓" if taux_avances >= 100 else "✗"],
                    ['', '', '', '', ''],
                    ['TOTAL GARANTIES', f"{self.total_cautions_requises + self.total_avances_requises:,.0f}", f"{self.total_cautions_versees + self.total_avances_versees:,.0f}", f"{((self.total_cautions_versees + self.total_avances_versees)/(self.total_cautions_requises + self.total_avances_requises)*100):.1f}%" if (self.total_cautions_requises + self.total_avances_requises) > 0 else "0%", "✓" if self.garanties_suffisantes else "✗"],
                ]
                
                garanties_table = Table(garanties_data, colWidths=[3*cm, 2.5*cm, 2.5*cm, 2*cm, 2*cm])
                garanties_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.orange),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, 2), colors.lightyellow),
                    ('BACKGROUND', (0, 4), (-1, 4), colors.lightblue),
                    ('FONTNAME', (0, 4), (-1, 4), 'Helvetica-Bold'),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ]))
                
                story.append(garanties_table)
                story.append(Spacer(1, 20))
            
            # Analyse et recommandations
            story.append(Paragraph("ANALYSE ET RECOMMANDATIONS", subtitle_style))
            story.append(Spacer(1, 10))
            
            # Générer des recommandations basées sur les données
            recommandations = []
            
            if taux_occupation < 100:
                recommandations.append(f"• Taux d'occupation de {taux_occupation:.1f}% - Améliorer la commercialisation des propriétés vacantes")
            
            if taux_paiement < 100:
                recommandations.append(f"• Taux de paiement de {taux_paiement:.1f}% - Suivre les impayés et relancer les locataires")
            
            if not self.garanties_suffisantes:
                recommandations.append("• Garanties insuffisantes - Exiger le complément des cautions et avances")
            
            if self.total_charges_deductibles > 0:
                recommandations.append(f"• Charges déductibles de {self.total_charges_deductibles:,.0f} F CFA - Vérifier la régularité des charges")
            
            if not recommandations:
                recommandations.append("• Situation financière satisfaisante - Continuer le suivi régulier")
            
            for rec in recommandations:
                story.append(Paragraph(rec, normal_style))
            
            story.append(Spacer(1, 20))
            
            # Pied de page
            ajouter_pied_entreprise_reportlab(story, config)
            
            # Générer le PDF
            doc.build(story)
            pdf_content = pdf_buffer.getvalue()
            pdf_buffer.close()
            
            return pdf_content
            
        except Exception as e:
            # En cas d'erreur, retourner un PDF simple mais avec un meilleur design
            from reportlab.lib.pagesizes import A4
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.lib import colors
            
            pdf_buffer = BytesIO()
            doc = SimpleDocTemplate(pdf_buffer, pagesize=A4)
            styles = getSampleStyleSheet()
            story = []
            
            # Style amélioré même pour le fallback
            title_style = ParagraphStyle(
                'Title',
                parent=styles['Title'],
                fontSize=18,
                textColor=colors.darkblue,
                alignment=1
            )
            
            story.append(Paragraph("RÉCAPITULATIF MENSUEL", title_style))
            story.append(Spacer(1, 20))
            story.append(Paragraph(f"<b>Bailleur:</b> {self.bailleur.get_nom_complet()}", styles['Normal']))
            story.append(Paragraph(f"<b>Mois:</b> {self.mois_recap.strftime('%B %Y')}", styles['Normal']))
            story.append(Spacer(1, 20))
            
            # Tableau simple mais avec style
            data = [
                ['Description', 'Montant (F CFA)'],
                ['Loyer brut total', f"{self.total_loyers_bruts:,.0f}"],
                ['Charges déductibles', f"{self.total_charges_deductibles:,.0f}"],
                ['Loyer net total', f"{self.total_net_a_payer:,.0f}"],
            ]
            
            table = Table(data, colWidths=[8*cm, 4*cm])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(table)
            
            doc.build(story)
            pdf_content = pdf_buffer.getvalue()
            pdf_buffer.close()
            
            return pdf_content'''
    
    # Remplacer l'ancienne methode par la nouvelle
    old_method_start = content.find('    def generer_pdf_recapitulatif(self):')
    if old_method_start != -1:
        # Trouver la fin de la methode
        lines = content.split('\n')
        method_start_line = -1
        method_end_line = -1
        
        for i, line in enumerate(lines):
            if 'def generer_pdf_recapitulatif(self):' in line and method_start_line == -1:
                method_start_line = i
            elif method_start_line != -1 and line.strip().startswith('def ') and not line.strip().startswith('def generer_pdf_recapitulatif'):
                method_end_line = i
                break
        
        if method_start_line != -1 and method_end_line != -1:
            # Remplacer la methode
            new_lines = lines[:method_start_line] + new_method.split('\n') + lines[method_end_line:]
            new_content = '\n'.join(new_lines)
            
            # Sauvegarder le fichier modifie
            with open('paiements/models.py', 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            print("OK: Methode generer_pdf_recapitulatif remplacee par une version avec design ameliore")
            return True
        else:
            print("ATTENTION: Impossible de trouver la fin de la methode")
            return False
    else:
        print("ATTENTION: Methode generer_pdf_recapitulatif non trouvee")
        return False

if __name__ == '__main__':
    improve_pdf_design()
EOF

# Executer le script d'amelioration du design du PDF
python improve_pdf_design.py

# Supprimer le script temporaire
rm improve_pdf_design.py

echo "Amelioration du design du PDF terminee!"

# Redemarrer Gunicorn
echo "Redemarrage de Gunicorn..."
sudo systemctl restart gunicorn

# Verifier le statut
echo "Verification du statut..."
sudo systemctl status gunicorn

# Tester l'application
echo "Test de l'application..."
curl -I http://localhost:8000

echo "Amelioration du design du PDF terminee avec succes!"
echo "Le PDF du recapitulatif aura maintenant:"
echo "- Design professionnel avec couleurs et styles"
echo "- Statistiques detaillees avec pourcentages"
echo "- Tableaux avec alternance de couleurs"
echo "- Analyse et recommandations automatiques"
echo "- Mise en forme amelioree"
echo "- Informations plus detailees et presentables"
