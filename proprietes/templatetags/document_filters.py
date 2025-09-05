from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter
def split_tags(value, delimiter=","):
    """
    Sépare une chaîne de tags par le délimiteur spécifié.
    Usage: {{ document.tags|split_tags:"," }}
    """
    if not value:
        return []
    return [tag.strip() for tag in value.split(delimiter) if tag.strip()]

@register.filter
def format_tags(value, delimiter=","):
    """
    Formate les tags en badges HTML.
    Usage: {{ document.tags|format_tags|safe }}
    """
    if not value:
        return ""
    
    tags = [tag.strip() for tag in value.split(delimiter) if tag.strip()]
    badges = []
    
    for tag in tags:
        badges.append(f'<span class="badge bg-secondary me-1">{tag}</span>')
    
    return mark_safe(''.join(badges))

@register.filter
def file_extension(value):
    """
    Retourne l'extension d'un fichier.
    Usage: {{ document.fichier.name|file_extension }}
    """
    if not value:
        return ""
    
    import os
    return os.path.splitext(str(value))[1].lower()

@register.filter
def file_type_class(value):
    """
    Retourne la classe CSS appropriée selon le type de fichier.
    Usage: {{ document.fichier.name|file_type_class }}
    """
    if not value:
        return "file-other"
    
    extension = file_extension(value)
    
    if extension == '.pdf':
        return 'file-pdf'
    elif extension in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
        return 'file-image'
    elif extension in ['.doc', '.docx']:
        return 'file-doc'
    elif extension in ['.xls', '.xlsx']:
        return 'file-excel'
    elif extension in ['.ppt', '.pptx']:
        return 'file-powerpoint'
    else:
        return 'file-other'

@register.filter
def file_icon(value):
    """
    Retourne l'icône Bootstrap appropriée selon le type de fichier.
    Usage: {{ document.fichier.name|file_icon }}
    """
    if not value:
        return "bi-file-earmark"
    
    extension = file_extension(value)
    
    if extension == '.pdf':
        return 'bi-file-earmark-pdf-fill'
    elif extension in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
        return 'bi-file-earmark-image-fill'
    elif extension in ['.doc', '.docx']:
        return 'bi-file-earmark-word-fill'
    elif extension in ['.xls', '.xlsx']:
        return 'bi-file-earmark-excel-fill'
    elif extension in ['.ppt', '.pptx']:
        return 'bi-file-earmark-ppt-fill'
    elif extension in ['.txt']:
        return 'bi-file-earmark-text-fill'
    elif extension in ['.zip', '.rar', '.7z']:
        return 'bi-file-earmark-zip-fill'
    else:
        return 'bi-file-earmark-fill'
