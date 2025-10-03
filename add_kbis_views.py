#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Script pour ajouter les vues KBIS à views.py

code_to_add = '''

# ============================================================================
# VUES KBIS IMMOBILIER - SYSTÈME DE QUITTANCES DYNAMIQUES  
# ============================================================================

@login_required
def generer_quittance_kbis_dynamique(request, paiement_pk):
    """Génère une quittance avec le nouveau système KBIS IMMOBILIER dynamique."""
    # Vérification des permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE'], 'add')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:detail', pk=paiement_pk)
    
    try:
        paiement = get_object_or_404(Paiement, pk=paiement_pk)
        
        # Génération directe avec le système KBIS dynamique
        html_quittance = paiement.generer_quittance_kbis_dynamique()
        
        if html_quittance:
            # Retourner directement le HTML (format A5 prêt pour impression)
            return HttpResponse(html_quittance, content_type='text/html')
        else:
            messages.error(request, 'Erreur lors de la génération de la quittance KBIS')
            return redirect('paiements:detail', pk=paiement_pk)
            
    except Exception as e:
        messages.error(request, f'Erreur lors de la génération: {str(e)}')
        return redirect('paiements:detail', pk=paiement_pk)

@login_required
def generer_quittance_kbis_tous_paiements(request):
    """Interface pour générer des quittances KBIS pour plusieurs paiements."""
    # Vérification des permissions
    permissions = check_group_permissions(request.user, ['PRIVILEGE', 'ADMINISTRATION', 'COMPTABILITE'], 'add')
    if not permissions['allowed']:
        messages.error(request, permissions['message'])
        return redirect('paiements:liste')
    
    if request.method == 'POST':
        paiements_ids = request.POST.getlist('paiements')
        format_sortie = request.POST.get('format', 'html')
        
        if not paiements_ids:
            messages.error(request, 'Aucun paiement sélectionné')
            return redirect('paiements:liste')
        
        try:
            paiements = Paiement.objects.filter(id__in=paiements_ids, is_deleted=False)
            
            if format_sortie == 'html':
                # Génération HTML combinée pour affichage direct
                html_content = f"""
                <!DOCTYPE html>
                <html lang="fr">
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>Quittances KBIS IMMOBILIER</title>
                    <style>
                        body {{ margin: 0; padding: 20px; font-family: Arial, sans-serif; background: #f5f5f5; }}
                        .container {{ max-width: 1200px; margin: 0 auto; }}
                        .header {{ text-align: center; margin-bottom: 30px; }}
                        .header h1 {{ color: #2c5aa0; margin-bottom: 10px; }}
                        .stats {{ background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                        .quittance-container {{ margin-bottom: 40px; page-break-after: always; }}
                        @media print {{
                            body {{ background: white; }}
                            .header, .stats {{ display: none; }}
                            .quittance-container {{ margin-bottom: 0; page-break-after: always; }}
                        }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <h1>📋 Quittances KBIS IMMOBILIER - Format A5</h1>
                            <p>Génération automatique de {len(paiements)} quittance(s)</p>
                        </div>
                        <div class="stats">
                            <h3>Statistiques</h3>
                            <p><strong>Nombre de quittances:</strong> {len(paiements)}</p>
                            <p><strong>Format:</strong> A5 (148mm × 210mm)</p>
                            <button onclick="window.print()" style="background: #007bff; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer;">🖨️ Imprimer tout</button>
                        </div>
                """
                
                for paiement in paiements:
                    quittance_html = paiement.generer_quittance_kbis_dynamique()
                    if quittance_html:
                        html_content += f'<div class="quittance-container">{quittance_html}</div>'
                
                html_content += """
                    </div>
                </body>
                </html>
                """
                
                return HttpResponse(html_content, content_type='text/html')
            
        except Exception as e:
            messages.error(request, f'Erreur lors de la génération: {str(e)}')
            return redirect('paiements:liste')
    
    # Affichage du formulaire
    paiements = Paiement.objects.filter(is_deleted=False).order_by('-date_paiement')[:50]
    
    context = {
        'paiements': paiements,
        'titre': 'Génération Quittances KBIS IMMOBILIER'
    }
    
    return render(request, 'paiements/generer_quittances_kbis.html', context)
'''

# Ajouter le code à la fin du fichier views.py
with open('paiements/views.py', 'a', encoding='utf-8') as f:
    f.write(code_to_add)

print("✅ Fonctions KBIS ajoutées avec succès au fichier views.py")