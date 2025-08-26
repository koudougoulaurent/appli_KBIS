from core.models import Devise, ConfigurationEntreprise
from django.conf import settings

def convertir_montant(montant, devise_source, devise_cible):
    if not devise_source or not devise_cible:
        return montant
    if devise_source.code == devise_cible.code:
        return montant
    # Conversion via EUR comme pivot
    montant_eur = montant / devise_source.taux_par_rapport_a_eur
    montant_cible = montant_eur * devise_cible.taux_par_rapport_a_eur
    return round(montant_cible, 2)

def format_currency_fcfa(value, show_decimals=True, short_format=False):
    """
    Formate un montant en F CFA selon les standards du Franc CFA
    
    Args:
        value: Le montant à formater
        show_decimals: Afficher les décimales (défaut: True)
        short_format: Utiliser les abréviations K/M (défaut: False)
    
    Returns:
        str: Le montant formaté avec F CFA
    """
    try:
        if value is None or value == '':
            return "0 F CFA"
        
        amount = float(value)
        
        # Format court avec abréviations
        if short_format:
            if amount >= 1000000:
                return f"{amount/1000000:,.1f}M F CFA".replace(',', ' ').replace('.', ',')
            elif amount >= 1000:
                return f"{amount/1000:,.0f}K F CFA".replace(',', ' ')
        
        # Format standard
        if show_decimals and amount != int(amount):
            # Afficher avec 2 décimales si nécessaire
            formatted = f"{amount:,.2f}".replace(',', ' ').replace('.', ',')
        else:
            # Format entier
            formatted = f"{int(amount):,}".replace(',', ' ')
        
        return f"{formatted} F CFA"
        
    except (ValueError, TypeError):
        return f"{value} F CFA"

def get_currency_settings():
    """Récupère les paramètres de devise depuis les settings"""
    return getattr(settings, 'CURRENCY_SETTINGS', {
        'DEFAULT_CURRENCY': 'F CFA',
        'CURRENCY_SYMBOL': 'F CFA',
        'CURRENCY_NAME': 'Franc CFA',
        'CURRENCY_CODE': 'F CFA',
        'DECIMAL_PLACES': 2,
        'USE_THOUSAND_SEPARATOR': True,
        'THOUSAND_SEPARATOR': ' ',
        'DECIMAL_SEPARATOR': ',',
    })

def inserer_devises_principales():
    from core.models import Devise
    devises = [
        {'code': 'F CFA', 'nom': 'Franc CFA', 'symbole': 'F CFA', 'taux_par_rapport_a_eur': 655.957},
        {'code': 'USD', 'nom': 'Dollar US', 'symbole': '$', 'taux_par_rapport_a_eur': 1.08},
        {'code': 'F CFA', 'nom': 'Franc CFA BCEAO', 'symbole': 'F CFA', 'taux_par_rapport_a_eur': 655.957},
    ]
    for d in devises:
        Devise.objects.update_or_create(
            code=d['code'],
            defaults={
                'nom': d['nom'],
                'symbole': d['symbole'],
                'taux_par_rapport_a_eur': d['taux_par_rapport_a_eur'],
                'actif': True
            }
        ) 

def ajouter_en_tete_entreprise(canvas, config, y_position=800):
    """
    Ajoute l'en-tête de l'entreprise sur un document PDF avec support de l'en-tête personnalisé.
    
    Args:
        canvas: Le canvas ReportLab
        config: L'objet ConfigurationEntreprise
        y_position: Position Y de départ (défaut: 800)
    """
    
    # Vérifier d'abord si un en-tête personnalisé existe
    if config.a_un_entete_personnalise():
        try:
            from reportlab.lib.utils import ImageReader
            import os
            
            entete_path = config.get_entete_prioritaire()
            if entete_path and os.path.exists(entete_path):
                # Utiliser l'en-tête personnalisé
                img = ImageReader(entete_path)
                img_width, img_height = img.getSize()
                
                # Calculer les dimensions optimales pour l'en-tête
                max_width = 500  # Largeur maximale de la page
                max_height = 150  # Hauteur maximale pour l'en-tête
                
                # Redimensionner proportionnellement
                aspect_ratio = img_width / img_height
                if aspect_ratio > 3.33:  # Très large
                    entete_width = max_width
                    entete_height = max_width / aspect_ratio
                elif aspect_ratio < 2:  # Très haut
                    entete_height = max_height
                    entete_width = max_height * aspect_ratio
                else:
                    # Ratio normal
                    entete_width = max_width
                    entete_height = max_height
                
                # Centrer l'en-tête
                entete_x = (600 - entete_width) / 2  # Centrer sur la page
                entete_y = y_position - entete_height + 20
                
                canvas.drawImage(entete_path, entete_x, entete_y, entete_width, entete_height)
                
                # Retourner la position Y après l'en-tête
                return y_position - entete_height - 20
                
        except Exception as e:
            print(f"Erreur lors de l'ajout de l'en-tête personnalisé: {e}")
            # Fallback vers le logo + texte
    
    # Si pas d'en-tête personnalisé, utiliser le logo + texte classique
    # Dimensions du logo (à ajuster selon vos besoins)
    logo_width = 120
    logo_height = 60
    
    # Position du logo (à droite de l'en-tête)
    logo_x = 400
    logo_y = y_position - 20
    
    # Ajouter le logo si disponible (priorité à l'upload)
    logo_source = config.get_logo_prioritaire()
    if logo_source:
        try:
            from reportlab.lib.utils import ImageReader
            from urllib.parse import urlparse
            import os
            
            # Gérer les différents types de logos
            if isinstance(logo_source, str):
                if logo_source.startswith('http'):
                    # URL externe - télécharger temporairement
                    import requests
                    import tempfile
                    
                    response = requests.get(logo_source, timeout=10)
                    if response.status_code == 200:
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
                            tmp_file.write(response.content)
                            logo_path = tmp_file.name
                            temp_file_created = True
                    else:
                        logo_path = None
                else:
                    # Chemin local (upload)
                    logo_path = logo_source
                    temp_file_created = False
            else:
                logo_path = None
            
            # Ajouter le logo au PDF
            if logo_path and os.path.exists(logo_path):
                try:
                    img = ImageReader(logo_path)
                    # Redimensionner le logo pour qu'il tienne dans l'espace
                    img_width, img_height = img.getSize()
                    aspect_ratio = img_width / img_height
                    
                    if aspect_ratio > 2:  # Logo très large
                        logo_width = 120
                        logo_height = logo_width / aspect_ratio
                    elif aspect_ratio < 0.5:  # Logo très haut
                        logo_height = 60
                        logo_width = logo_height * aspect_ratio
                    else:
                        # Logo carré ou normal
                        logo_width = 120
                        logo_height = 60
                    
                    canvas.drawImage(logo_path, logo_x, logo_y, logo_width, logo_height)
                    
                    # Nettoyer le fichier temporaire si créé
                    if 'temp_file_created' in locals() and temp_file_created:
                        os.unlink(logo_path)
                        
                except Exception as e:
                    print(f"Erreur lors de l'ajout du logo: {e}")
                    # Fallback vers le texte
                    canvas.setFont("Helvetica-Bold", 12)
                    canvas.drawString(logo_x, logo_y + 30, "LOGO")
                    
        except Exception as e:
            print(f"Erreur lors du traitement du logo: {e}")
            # Fallback vers le texte
            canvas.setFont("Helvetica-Bold", 12)
            canvas.drawString(logo_x, logo_y + 30, "LOGO")
    
    # Informations textuelles de l'entreprise (à gauche du logo)
    text_x = 50
    text_y = y_position
    
    canvas.setFont("Helvetica-Bold", 14)
    canvas.drawString(text_x, text_y, config.nom_entreprise)
    canvas.setFont("Helvetica", 10)
    canvas.drawString(text_x, text_y - 20, config.get_adresse_complete())
    canvas.drawString(text_x, text_y - 40, config.get_contact_complet())
    
    # Retourner la position Y après l'en-tête (pour la compatibilité)
    return y_position - 60

def ajouter_pied_entreprise(canvas, config, y_position=100):
    """
    Ajoute le pied de page avec les informations de l'entreprise.
    
    Args:
        canvas: Le canvas ReportLab
        config: L'objet ConfigurationEntreprise
        y_position: Position Y de départ (défaut: 100)
    """
    canvas.setFont("Helvetica", 8)
    
    # Informations de base toujours affichées
    canvas.drawString(50, y_position, f"{config.nom_entreprise} - {config.get_adresse_complete()}")
    
    # Informations de contact
    contact_info = []
    if config.telephone:
        contact_info.append(f"Tél: {config.telephone}")
    if config.email:
        contact_info.append(f"Email: {config.email}")
    
    if contact_info:
        canvas.drawString(50, y_position - 15, " | ".join(contact_info))
    
    # Informations optionnelles (SIRET et Licence)
    info_legales = []
    if config.siret and config.siret.strip():
        info_legales.append(f"SIRET: {config.siret}")
    if config.numero_licence and config.numero_licence.strip():
        info_legales.append(f"Licence: {config.numero_licence}")
    
    if info_legales:
        canvas.drawString(50, y_position - 30, " | ".join(info_legales))

def ajouter_en_tete_entreprise_reportlab(story, config):
    """
    Ajoute l'en-tête de l'entreprise pour les documents ReportLab avec Platypus.
    
    Args:
        story: La liste des éléments du document
        config: L'objet ConfigurationEntreprise
    """
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib import colors
    from reportlab.platypus import Paragraph, Spacer, Image, Table, TableStyle
    from reportlab.lib.units import cm
    
    # Vérifier d'abord si un en-tête personnalisé existe
    if config.a_un_entete_personnalise():
        try:
            import os
            
            entete_path = config.get_entete_prioritaire()
            if entete_path and os.path.exists(entete_path):
                # Utiliser l'en-tête personnalisé
                entete_img = Image(entete_path, width=16*cm, height=4*cm)
                story.append(entete_img)
                story.append(Spacer(1, 20))
                return  # L'en-tête personnalisé remplace tout
                
        except Exception as e:
            print(f"Erreur lors de l'ajout de l'en-tête personnalisé: {e}")
            # Fallback vers le logo + texte
    
    # Style pour l'en-tête
    header_style = ParagraphStyle(
        'HeaderStyle',
        fontSize=14,
        spaceAfter=10,
        alignment=1,  # Centré
        textColor=colors.darkblue
    )
    
    # Style pour les informations de contact
    contact_style = ParagraphStyle(
        'ContactStyle',
        fontSize=10,
        spaceAfter=5,
        alignment=1,  # Centré
        textColor=colors.darkgrey
    )
    
    # Créer un tableau pour l'en-tête avec logo et texte
    logo_source = config.get_logo_prioritaire()
    if logo_source:
        try:
            # Essayer d'ajouter le logo
            if isinstance(logo_source, str):
                if logo_source.startswith('http'):
                    # URL externe - télécharger temporairement
                    import requests
                    import tempfile
                    import os
                    
                    response = requests.get(logo_source, timeout=10)
                    if response.status_code == 200:
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
                            tmp_file.write(response.content)
                            logo_path = tmp_file.name
                            temp_file_created = True
                    else:
                        logo_path = None
                else:
                    # Chemin local (upload)
                    logo_path = logo_source
                    temp_file_created = False
            else:
                logo_path = None
            
            # Créer l'en-tête avec logo
            if logo_path and os.path.exists(logo_path):
                try:
                    # Tableau avec logo à gauche et texte à droite
                    logo_img = Image(logo_path, width=3*cm, height=1.5*cm)
                    
                    # Informations de l'entreprise
                    entreprise_info = [
                        [Paragraph(f"<b>{config.nom_entreprise}</b>", header_style)],
                        [Paragraph(config.get_adresse_complete(), contact_style)],
                    ]
                    
                    contact_info = []
                    if config.telephone:
                        contact_info.append(f"Tél: {config.telephone}")
                    if config.email:
                        contact_info.append(f"Email: {config.email}")
                    if config.site_web:
                        contact_info.append(f"Web: {config.site_web}")
                    
                    if contact_info:
                        entreprise_info.append([Paragraph(" | ".join(contact_info), contact_style)])
                    
                    # Tableau avec logo et informations
                    header_data = [[logo_img, entreprise_info]]
                    header_table = Table(header_data, colWidths=[4*cm, 12*cm])
                    header_table.setStyle(TableStyle([
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                        ('ALIGN', (0, 0), (0, 0), 'CENTER'),
                        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                        ('LEFTPADDING', (1, 0), (1, -1), 20),
                    ]))
                    
                    story.append(header_table)
                    
                    # Nettoyer le fichier temporaire si créé
                    if 'temp_file_created' in locals() and temp_file_created:
                        os.unlink(logo_path)
                        
                except Exception as e:
                    print(f"Erreur lors de l'ajout du logo: {e}")
                    # Fallback vers le texte seulement
                    story.append(Paragraph(f"<b>{config.nom_entreprise}</b>", header_style))
                    if config.get_adresse_complete():
                        story.append(Paragraph(config.get_adresse_complete(), contact_style))
                    
                    contact_info = []
                    if config.telephone:
                        contact_info.append(f"Tél: {config.telephone}")
                    if config.email:
                        contact_info.append(f"Email: {config.email}")
                    if config.site_web:
                        contact_info.append(f"Web: {config.site_web}")
                    
                    if contact_info:
                        story.append(Paragraph(" | ".join(contact_info), contact_style))
            else:
                # Pas de logo - afficher le texte seulement
                story.append(Paragraph(f"<b>{config.nom_entreprise}</b>", header_style))
                if config.get_adresse_complete():
                    story.append(Paragraph(config.get_adresse_complete(), contact_style))
                
                contact_info = []
                if config.telephone:
                    contact_info.append(f"Tél: {config.telephone}")
                if config.email:
                    contact_info.append(f"Email: {config.email}")
                if config.site_web:
                    contact_info.append(f"Web: {config.site_web}")
                
                if contact_info:
                    story.append(Paragraph(" | ".join(contact_info), contact_style))
                    
        except Exception as e:
            print(f"Erreur lors du traitement du logo: {e}")
            # Fallback vers le texte seulement
            story.append(Paragraph(f"<b>{config.nom_entreprise}</b>", header_style))
            if config.get_adresse_complete():
                story.append(Paragraph(config.get_adresse_complete(), contact_style))
            
            contact_info = []
            if config.telephone:
                contact_info.append(f"Tél: {config.telephone}")
            if config.email:
                contact_info.append(f"Email: {config.email}")
            if config.site_web:
                contact_info.append(f"Web: {config.site_web}")
            
            if contact_info:
                story.append(Paragraph(" | ".join(contact_info), contact_style))
    else:
        # Pas de logo configuré - afficher le texte seulement
        story.append(Paragraph(f"<b>{config.nom_entreprise}</b>", header_style))
        if config.get_adresse_complete():
            story.append(Paragraph(config.get_adresse_complete(), contact_style))
        
        contact_info = []
        if config.telephone:
            contact_info.append(f"Tél: {config.telephone}")
        if config.email:
            contact_info.append(f"Email: {config.email}")
        if config.site_web:
            contact_info.append(f"Web: {config.site_web}")
        
        if contact_info:
            story.append(Paragraph(" | ".join(contact_info), contact_style))
    
    story.append(Spacer(1, 20))

def valider_logo_entreprise(logo_file):
    """
    Valide et traite un fichier logo uploadé.
    
    Args:
        logo_file: Le fichier uploadé (django.core.files.uploadedfile.UploadedFile)
    
    Returns:
        dict: Résultat de la validation avec 'valid' (bool) et 'message' (str)
    """
    import os
    from django.conf import settings
    
    # Vérifier le type de fichier
    allowed_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp']
    file_extension = os.path.splitext(logo_file.name)[1].lower()
    
    if file_extension not in allowed_extensions:
        return {
            'valid': False,
            'message': f"Format de fichier non supporté. Formats autorisés: {', '.join(allowed_extensions)}"
        }
    
    # Vérifier la taille du fichier (max 5MB)
    max_size = 5 * 1024 * 1024  # 5MB
    if logo_file.size > max_size:
        return {
            'valid': False,
            'message': f"Fichier trop volumineux. Taille maximale: 5MB"
        }
    
    # Vérifier les dimensions de l'image
    try:
        from PIL import Image
        from io import BytesIO
        
        # Ouvrir l'image pour vérifier ses dimensions
        img = Image.open(BytesIO(logo_file.read()))
        logo_file.seek(0)  # Remettre le curseur au début
        
        width, height = img.size
        
        # Recommandations pour un bon logo
        if width < 100 or height < 50:
            return {
                'valid': False,
                'message': f"Image trop petite. Dimensions minimales recommandées: 200x100 pixels"
            }
        
        if width > 2000 or height > 1000:
            return {
                'valid': False,
                'message': f"Image trop grande. Dimensions maximales recommandées: 2000x1000 pixels"
            }
        
        # Vérifier le ratio d'aspect (pas trop large ni trop haut)
        aspect_ratio = width / height
        if aspect_ratio > 4 or aspect_ratio < 0.25:
            return {
                'valid': False,
                'message': f"Ratio d'aspect non recommandé. Ratio optimal: entre 0.5 et 3"
            }
        
        return {
            'valid': True,
            'message': f"Logo valide ({width}x{height} pixels)"
        }
        
    except Exception as e:
        return {
            'valid': False,
            'message': f"Erreur lors de la validation de l'image: {str(e)}"
        }

def optimiser_logo_pour_pdf(logo_path, max_width=120, max_height=60):
    """
    Optimise un logo pour l'utilisation dans les PDF.
    
    Args:
        logo_path: Chemin vers le fichier logo
        max_width: Largeur maximale en pixels
        max_height: Hauteur maximale en pixels
    
    Returns:
        str: Chemin vers le logo optimisé ou le logo original
    """
    try:
        from PIL import Image
        import os
        
        # Ouvrir l'image
        img = Image.open(logo_path)
        
        # Convertir en RGB si nécessaire (pour la compatibilité PDF)
        if img.mode in ('RGBA', 'LA', 'P'):
            # Créer un fond blanc
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = background
        
        # Redimensionner si nécessaire
        if img.width > max_width or img.height > max_height:
            img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
        
        # Créer un fichier temporaire optimisé
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
            img.save(tmp_file.name, 'PNG', optimize=True, quality=95)
            return tmp_file.name
            
    except Exception as e:
        print(f"Erreur lors de l'optimisation du logo: {e}")
        return logo_path

def ajouter_pied_entreprise_reportlab(story, config):
    """
    Ajoute le pied de page avec les informations de l'entreprise pour ReportLab.
    
    Args:
        story: La liste des éléments du document
        config: L'objet ConfigurationEntreprise
    """
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib import colors
    from reportlab.platypus import Paragraph, Spacer
    
    # Style pour le pied de page
    footer_style = ParagraphStyle(
        'FooterStyle',
        fontSize=8,
        spaceAfter=5,
        alignment=1,  # Centré
        textColor=colors.grey
    )
    
    story.append(Spacer(1, 30))
    
    # Ligne de séparation
    story.append(Paragraph("<hr/>", footer_style))
    
    # Informations de l'entreprise
    story.append(Paragraph(f"{config.nom_entreprise} - {config.get_adresse_complete()}", footer_style))
    
    # Informations de contact
    contact_info = []
    if config.telephone:
        contact_info.append(f"Tél: {config.telephone}")
    if config.email:
        contact_info.append(f"Email: {config.email}")
    
    if contact_info:
        story.append(Paragraph(" | ".join(contact_info), footer_style))
    
    # Informations légales optionnelles
    info_legales = []
    if config.siret and config.siret.strip():
        info_legales.append(f"SIRET: {config.siret}")
    if config.numero_licence and config.numero_licence.strip():
        info_legales.append(f"Licence: {config.numero_licence}")
    
    if info_legales:
        story.append(Paragraph(" | ".join(info_legales), footer_style))

def check_group_permissions(user, allowed_groups, operation_type='modify'):
    """
    Vérifie les permissions d'un utilisateur selon son groupe et le type d'opération
    
    Args:
        user: L'utilisateur connecté
        allowed_groups: Liste des groupes autorisés (ex: ['PRIVILEGE', 'ADMINISTRATION'])
        operation_type: Type d'opération ('add', 'modify', 'delete', 'view', 'validate', 'resilier')
    
    Returns:
        dict: Dictionnaire avec 'allowed' (bool) et 'message' (str)
    """
    if not user.is_authenticated:
        return {'allowed': False, 'message': 'Utilisateur non authentifié.'}
    
    groupe = getattr(user, 'groupe_travail', None)
    if not groupe:
        return {'allowed': False, 'message': 'Aucun groupe de travail assigné.'}
    
    groupe_nom = groupe.nom.upper()
    
    # PRIVILEGE a TOUS les droits sur TOUTES les fonctionnalités sensibles
    if groupe_nom == 'PRIVILEGE':
        return {'allowed': True, 'message': 'Accès autorisé (groupe PRIVILEGE).'}
    
    # SÉCURITÉ STRICTE : Seul PRIVILEGE a accès aux fonctionnalités sensibles
    operations_sensibles = ['modify', 'delete', 'validate', 'resilier']
    if operation_type in operations_sensibles:
        return {'allowed': False, 'message': f'Accès refusé. Seul le groupe PRIVILEGE peut effectuer des {operation_type}.'}
    
    # CAISSE : Lecture uniquement, pas de modification/suppression
    if groupe_nom == 'CAISSE':
        if operation_type == 'view':
            return {'allowed': True, 'message': 'Accès autorisé (groupe CAISSE - consultation uniquement).'}
        elif operation_type == 'add':
            # CAISSE peut ajouter des paiements mais pas d'autres éléments sensibles
            return {'allowed': True, 'message': 'Accès autorisé (groupe CAISSE - ajout de paiements).'}
        else:
            return {'allowed': False, 'message': 'Le groupe CAISSE ne peut que consulter et ajouter des paiements.'}
    
    # CONTROLES : Lecture et audit uniquement
    if groupe_nom == 'CONTROLES':
        if operation_type == 'view':
            return {'allowed': True, 'message': 'Accès autorisé (groupe CONTROLES - audit et vérification).'}
        else:
            return {'allowed': False, 'message': 'Le groupe CONTROLES peut consulter et vérifier mais pas modifier, supprimer ou valider.'}
    
    # ADMINISTRATION : Lecture et ajout limité uniquement
    if groupe_nom == 'ADMINISTRATION':
        if operation_type == 'view':
            return {'allowed': True, 'message': 'Accès autorisé (groupe ADMINISTRATION - consultation).'}
        elif operation_type == 'add':
            # ADMINISTRATION peut ajouter des éléments de base mais pas de fonctionnalités sensibles
            return {'allowed': True, 'message': 'Accès autorisé (groupe ADMINISTRATION - ajout d\'éléments de base).'}
        else:
            return {'allowed': False, 'message': 'Le groupe ADMINISTRATION peut consulter et ajouter des éléments de base mais pas modifier, supprimer ou valider.'}
    
    # Autres groupes : Vérifier la liste allowed_groups pour les opérations non sensibles
    if groupe_nom in allowed_groups and operation_type not in operations_sensibles:
        return {'allowed': True, 'message': f'Accès autorisé (groupe {groupe_nom}).'}
    
    return {'allowed': False, 'message': f'Accès refusé. Groupe requis: {", ".join(allowed_groups)}.'} 

def log_audit_action(request, action, content_type=None, object_id=None, object_repr=None, details=None):
    """
    Enregistre une action dans les logs d'audit
    
    Args:
        request: La requête HTTP
        action: L'action effectuée (create, update, delete, view, etc.)
        content_type: Le type de contenu (optionnel)
        object_id: L'ID de l'objet (optionnel)
        object_repr: La représentation textuelle de l'objet (optionnel)
        details: Détails supplémentaires en JSON (optionnel)
    """
    try:
        from .models import AuditLog
        from django.contrib.contenttypes.models import ContentType
        
        # Récupérer l'adresse IP et le user agent
        ip_address = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Créer le log d'audit
        AuditLog.objects.create(
            user=request.user,
            action=action,
            content_type=content_type,
            object_id=object_id,
            object_repr=object_repr,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent
        )
    except Exception as e:
        # En cas d'erreur, on log mais on ne fait pas échouer l'opération principale
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Erreur lors de l'enregistrement du log d'audit: {e}")

def get_client_ip(request):
    """
    Récupère l'adresse IP réelle du client
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def detecter_anomalies():
    """
    Détecte les anomalies dans le système
    
    Returns:
        dict: Dictionnaire contenant les anomalies détectées
    """
    from django.utils import timezone
    from datetime import timedelta
    from django.db.models import Q
    from django.contrib.auth import get_user_model
    
    User = get_user_model()
    anomalies = []
    stats = {'danger': 0, 'warning': 0, 'info': 0, 'total': 0}
    
    try:
        # 1. Paiements en retard (plus de 30 jours)
        from paiements.models import Paiement
        date_limite = timezone.now().date() - timedelta(days=30)
        paiements_retard = Paiement.objects.filter(
            date_echeance__lt=date_limite,
            statut='en_attente'
        ).select_related('contrat__locataire')
        
        if paiements_retard.exists():
            anomalies.append({
                'type': 'paiement_retard',
                'titre': f'{paiements_retard.count()} paiement(s) en retard',
                'description': f'Paiements en retard de plus de 30 jours',
                'severite': 'danger',
                'date': timezone.now(),
                'url': '/paiements/liste/'
            })
            stats['danger'] += 1
        
        # 2. Contrats expirant dans les 30 jours
        from contrats.models import Contrat
        date_expiration = timezone.now().date() + timedelta(days=30)
        contrats_expirant = Contrat.objects.filter(
            date_fin__lte=date_expiration,
            statut='actif'
        ).select_related('locataire')
        
        if contrats_expirant.exists():
            anomalies.append({
                'type': 'contrat_expirant',
                'titre': f'{contrats_expirant.count()} contrat(s) expirant bientôt',
                'description': f'Contrats expirant dans les 30 prochains jours',
                'severite': 'warning',
                'date': timezone.now(),
                'url': '/contrats/liste/'
            })
            stats['warning'] += 1
        
        # 3. Propriétés vides depuis plus de 6 mois
        from proprietes.models import Propriete
        date_limite_vide = timezone.now().date() - timedelta(days=180)
        proprietes_vides = Propriete.objects.filter(
            statut='disponible',
            date_disponibilite__lt=date_limite_vide
        )
        
        if proprietes_vides.exists():
            anomalies.append({
                'type': 'propriete_vide',
                'titre': f'{proprietes_vides.count()} propriété(s) vide(s) depuis longtemps',
                'description': f'Propriétés disponibles depuis plus de 6 mois',
                'severite': 'info',
                'date': timezone.now(),
                'url': '/proprietes/liste/'
            })
            stats['info'] += 1
        
        # 4. Utilisateurs inactifs depuis plus de 90 jours
        date_limite_inactif = timezone.now() - timedelta(days=90)
        utilisateurs_inactifs = User.objects.filter(
            last_login__lt=date_limite_inactif,
            is_active=True
        ).exclude(is_superuser=True)
        
        if utilisateurs_inactifs.exists():
            anomalies.append({
                'type': 'utilisateur_inactif',
                'titre': f'{utilisateurs_inactifs.count()} utilisateur(s) inactif(s)',
                'description': f'Utilisateurs qui ne se sont pas connectés depuis 90 jours',
                'severite': 'warning',
                'date': timezone.now(),
                'url': '/utilisateurs/liste/'
            })
            stats['warning'] += 1
        
        # Calculer le total
        stats['total'] = len(anomalies)
        
    except Exception as e:
        # En cas d'erreur, on retourne une anomalie système
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Erreur lors de la détection d'anomalies: {e}")
        
        anomalies.append({
            'type': 'erreur_systeme',
            'titre': 'Erreur de détection d\'anomalies',
            'description': f'Erreur technique: {str(e)}',
            'severite': 'danger',
            'date': timezone.now(),
            'url': None
        })
        stats['danger'] += 1
        stats['total'] = 1
    
    return {
        'anomalies': anomalies,
        'stats_anomalies': stats,
        'paiements_retard': paiements_retard if 'paiements_retard' in locals() else [],
        'contrats_expirant': contrats_expirant if 'contrats_expirant' in locals() else [],
        'proprietes_vides': proprietes_vides if 'proprietes_vides' in locals() else [],
        'utilisateurs_inactifs': utilisateurs_inactifs if 'utilisateurs_inactifs' in locals() else []
    }


def get_context_with_entreprise_config(base_context=None):
    """
    Fonction utilitaire pour ajouter la configuration d'entreprise au contexte des templates.
    Utilisée pour tous les documents générés (quittances, reçus, contrats, etc.)
    
    Args:
        base_context (dict): Contexte de base existant
        
    Returns:
        dict: Contexte enrichi avec la configuration d'entreprise
    """
    if base_context is None:
        base_context = {}
    
    # Récupérer la configuration active de l'entreprise
    config_entreprise = ConfigurationEntreprise.get_configuration_active()
    
    # Ajouter au contexte
    base_context['config_entreprise'] = config_entreprise
    
    return base_context 