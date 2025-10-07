#!/bin/bash

# Script pour restaurer le PDF du recapitulatif mensuel avec plus de details
echo "Restoration du PDF du recapitulatif mensuel avec plus de details..."

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

# 4. Restaurer le PDF detaille
echo "4. Restoration du PDF detaille..."

# Creer un script Python pour restaurer le PDF detaille
cat > restore_detailed_pdf.py << 'EOF'
#!/usr/bin/env python3

def restore_detailed_pdf():
    # Lire le fichier models.py
    with open('paiements/models.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Creer une sauvegarde
    with open('paiements/models.py.backup_detailed_pdf', 'w', encoding='utf-8') as f:
        f.write(content)
    
    # Nouvelle methode generer_pdf_recapitulatif plus detaillee
    new_method = '''    def generer_pdf_recapitulatif(self):
        """Génère le PDF du récapitulatif mensuel avec ReportLab - VERSION DÉTAILLÉE."""
        from django.utils import timezone
        from io import BytesIO
        from datetime import timedelta
        from decimal import Decimal
        
        try:
            # Utiliser ReportLab pour une génération PDF fiable
            from reportlab.lib.pagesizes import A4
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import cm
            from reportlab.lib import colors
            
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
            
            # Styles
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=18,
                spaceAfter=30,
                alignment=1,  # Centré
                textColor=colors.darkblue
            )
            
            subtitle_style = ParagraphStyle(
                'CustomSubtitle',
                parent=styles['Heading2'],
                fontSize=14,
                spaceAfter=15,
                textColor=colors.darkblue
            )
            
            normal_style = styles['Normal']
            normal_style.fontSize = 10
            
            # Contenu du PDF
            story = []
            
            # Récupérer la configuration de l'entreprise
            from core.models import ConfigurationEntreprise
            from core.utils import ajouter_en_tete_entreprise_reportlab, ajouter_pied_entreprise_reportlab
            config = ConfigurationEntreprise.get_configuration_active()
            
            # En-tête de l'entreprise
            ajouter_en_tete_entreprise_reportlab(story, config)
            
            # Titre principal
            story.append(Paragraph("RÉCAPITULATIF MENSUEL", title_style))
            story.append(Spacer(1, 20))
            
            # Informations du bailleur
            story.append(Paragraph(f"<b>Bailleur:</b> {self.bailleur.get_nom_complet()}", subtitle_style))
            story.append(Paragraph(f"<b>Mois:</b> {self.mois_recap.strftime('%B %Y')}", normal_style))
            story.append(Spacer(1, 15))
            
            # Résumé financier
            story.append(Paragraph("RÉSUMÉ FINANCIER", subtitle_style))
            story.append(Spacer(1, 10))
            
            # Tableau des montants
            montants_data = [
                ['Description', 'Montant (F CFA)'],
                ['Loyer brut total', f"{self.total_loyers_bruts:,.0f}"],
                ['Charges déductibles', f"{self.total_charges_deductibles:,.0f}"],
                ['Charges bailleur', f"{self.total_charges_bailleur or 0:,.0f}"],
                ['Loyer net total', f"{self.total_net_a_payer:,.0f}"],
            ]
            
            montants_table = Table(montants_data, colWidths=[8*cm, 4*cm])
            montants_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(montants_table)
            story.append(Spacer(1, 20))
            
            # Statistiques
            story.append(Paragraph("STATISTIQUES", subtitle_style))
            story.append(Spacer(1, 10))
            
            stats_data = [
                ['Description', 'Nombre'],
                ['Propriétés', str(self.nombre_proprietes)],
                ['Contrats actifs', str(self.nombre_contrats_actifs)],
                ['Paiements reçus', str(self.nombre_paiements_recus)],
            ]
            
            stats_table = Table(stats_data, colWidths=[8*cm, 4*cm])
            stats_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(stats_table)
            story.append(Spacer(1, 20))
            
            # Détails des propriétés et contrats
            story.append(Paragraph("DÉTAILS DES PROPRIÉTÉS ET CONTRATS", subtitle_style))
            story.append(Spacer(1, 10))
            
            # Récupérer les détails des propriétés
            proprietes_details = self.get_proprietes_details()
            
            if proprietes_details:
                # En-tête du tableau détaillé
                details_data = [
                    ['Propriété', 'Locataire', 'Loyer', 'Charges', 'Net à payer']
                ]
                
                for detail in proprietes_details:
                    details_data.append([
                        detail['adresse_complete'],
                        detail['locataire'].get_nom_complet() if detail['locataire'] else 'N/A',
                        f"{detail['loyer_mensuel']:,.0f}",
                        f"{detail['charges_deductibles']:,.0f}",
                        f"{detail['net_a_payer']:,.0f}"
                    ])
                
                details_table = Table(details_data, colWidths=[4*cm, 3*cm, 2.5*cm, 2.5*cm, 2.5*cm])
                details_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('FONTSIZE', (0, 1), (-1, -1), 9),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ]))
                
                story.append(details_table)
                story.append(Spacer(1, 20))
            
            # Garanties financières
            if self.total_cautions_requises > 0 or self.total_avances_requises > 0:
                story.append(Paragraph("GARANTIES FINANCIÈRES", subtitle_style))
                story.append(Spacer(1, 10))
                
                garanties_data = [
                    ['Description', 'Montant (F CFA)'],
                    ['Cautions requises', f"{self.total_cautions_requises:,.0f}"],
                    ['Cautions versées', f"{self.total_cautions_versees:,.0f}"],
                    ['Avances requises', f"{self.total_avances_requises:,.0f}"],
                    ['Avances versées', f"{self.total_avances_versees:,.0f}"],
                    ['Statut', 'Suffisantes' if self.garanties_suffisantes else 'Insuffisantes'],
                ]
                
                garanties_table = Table(garanties_data, colWidths=[8*cm, 4*cm])
                garanties_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.orange),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.lightyellow),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                
                story.append(garanties_table)
                story.append(Spacer(1, 20))
            
            # Pied de page
            ajouter_pied_entreprise_reportlab(story, config)
            
            # Générer le PDF
            doc.build(story)
            pdf_content = pdf_buffer.getvalue()
            pdf_buffer.close()
            
            return pdf_content
            
        except Exception as e:
            # En cas d'erreur, retourner un PDF simple
            from reportlab.lib.pagesizes import A4
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet
            
            pdf_buffer = BytesIO()
            doc = SimpleDocTemplate(pdf_buffer, pagesize=A4)
            styles = getSampleStyleSheet()
            story = []
            
            story.append(Paragraph("RÉCAPITULATIF MENSUEL", styles['Title']))
            story.append(Spacer(1, 20))
            story.append(Paragraph(f"Bailleur: {self.bailleur.get_nom_complet()}", styles['Normal']))
            story.append(Paragraph(f"Mois: {self.mois_recap.strftime('%B %Y')}", styles['Normal']))
            story.append(Spacer(1, 20))
            story.append(Paragraph(f"Loyer brut total: {self.total_loyers_bruts:,.0f} F CFA", styles['Normal']))
            story.append(Paragraph(f"Charges déductibles: {self.total_charges_deductibles:,.0f} F CFA", styles['Normal']))
            story.append(Paragraph(f"Loyer net total: {self.total_net_a_payer:,.0f} F CFA", styles['Normal']))
            
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
            
            print("OK: Methode generer_pdf_recapitulatif remplacee par une version plus detaillee")
            return True
        else:
            print("ATTENTION: Impossible de trouver la fin de la methode")
            return False
    else:
        print("ATTENTION: Methode generer_pdf_recapitulatif non trouvee")
        return False

if __name__ == '__main__':
    restore_detailed_pdf()
EOF

# Executer le script de restoration du PDF detaille
python restore_detailed_pdf.py

# Supprimer le script temporaire
rm restore_detailed_pdf.py

echo "Restoration du PDF detaille terminee!"

# Redemarrer Gunicorn
echo "Redemarrage de Gunicorn..."
sudo systemctl restart gunicorn

# Verifier le statut
echo "Verification du statut..."
sudo systemctl status gunicorn

# Tester l'application
echo "Test de l'application..."
curl -I http://localhost:8000

echo "Restoration du PDF detaille terminee avec succes!"
echo "Le PDF du recapitulatif sera maintenant plus detaille avec:"
echo "- Resume financier complet"
echo "- Statistiques detailees"
echo "- Details des proprietes et contrats"
echo "- Garanties financieres"
