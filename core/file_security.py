"""
Module de sécurité pour les uploads de fichiers
"""
import os
import mimetypes
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.conf import settings
import logging

# Import optionnel de python-magic
try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False

logger = logging.getLogger(__name__)

class FileSecurityValidator:
    """Validateur de sécurité pour les fichiers uploadés"""
    
    # Types MIME autorisés par catégorie
    ALLOWED_MIME_TYPES = {
        'images': [
            'image/jpeg',
            'image/png',
            'image/gif',
            'image/webp',
            'image/bmp',
            'image/tiff'
        ],
        'documents': [
            'application/pdf',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/vnd.ms-excel',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'application/vnd.ms-powerpoint',
            'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            'text/plain',
            'text/csv'
        ],
        'archives': [
            'application/zip',
            'application/x-rar-compressed',
            'application/x-7z-compressed'
        ]
    }
    
    # Extensions autorisées
    ALLOWED_EXTENSIONS = {
        'images': ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.tiff'],
        'documents': ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt', '.csv'],
        'archives': ['.zip', '.rar', '.7z']
    }
    
    # Tailles maximales (en bytes)
    MAX_FILE_SIZES = {
        'images': 5 * 1024 * 1024,  # 5MB
        'documents': 10 * 1024 * 1024,  # 10MB
        'archives': 50 * 1024 * 1024,  # 50MB
        'default': 5 * 1024 * 1024  # 5MB par défaut
    }
    
    # Noms de fichiers interdits
    FORBIDDEN_FILENAMES = [
        '..', '.', 'CON', 'PRN', 'AUX', 'NUL',
        'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
        'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
    ]
    
    @classmethod
    def validate_file_security(cls, file, category='default', user=None):
        """
        Valide la sécurité d'un fichier uploadé
        
        Args:
            file: Fichier Django uploadé
            category: Catégorie du fichier (images, documents, archives, default)
            user: Utilisateur qui upload le fichier (pour logging)
        
        Returns:
            dict: Résultat de la validation avec détails
        """
        result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'file_info': {}
        }
        
        try:
            # 1. Validation du nom de fichier
            filename = file.name
            result['file_info']['filename'] = filename
            
            # Vérifier les noms interdits
            if filename.upper() in cls.FORBIDDEN_FILENAMES:
                result['valid'] = False
                result['errors'].append("Nom de fichier interdit")
            
            # Vérifier les caractères dangereux
            dangerous_chars = ['<', '>', ':', '"', '|', '?', '*', '\\', '/']
            if any(char in filename for char in dangerous_chars):
                result['valid'] = False
                result['errors'].append("Nom de fichier contient des caractères interdits")
            
            # Vérifier la longueur du nom
            if len(filename) > 255:
                result['valid'] = False
                result['errors'].append("Nom de fichier trop long (max 255 caractères)")
            
            # 2. Validation de la taille
            file_size = file.size
            result['file_info']['size'] = file_size
            
            max_size = cls.MAX_FILE_SIZES.get(category, cls.MAX_FILE_SIZES['default'])
            if file_size > max_size:
                result['valid'] = False
                result['errors'].append(f"Fichier trop volumineux (max {max_size // (1024*1024)}MB)")
            
            # 3. Validation de l'extension
            file_ext = os.path.splitext(filename)[1].lower()
            result['file_info']['extension'] = file_ext
            
            allowed_extensions = cls.ALLOWED_EXTENSIONS.get(category, [])
            if allowed_extensions and file_ext not in allowed_extensions:
                result['valid'] = False
                result['errors'].append(f"Extension non autorisée. Extensions autorisées: {', '.join(allowed_extensions)}")
            
            # 4. Validation du type MIME
            mime_type = cls._get_mime_type(file)
            result['file_info']['mime_type'] = mime_type
            
            allowed_mime_types = cls.ALLOWED_MIME_TYPES.get(category, [])
            if allowed_mime_types and mime_type not in allowed_mime_types:
                result['valid'] = False
                result['errors'].append(f"Type de fichier non autorisé. Types autorisés: {', '.join(allowed_mime_types)}")
            
            # 5. Vérification de cohérence extension/MIME
            if not cls._is_extension_mime_consistent(file_ext, mime_type):
                result['warnings'].append("Incohérence entre l'extension et le type MIME du fichier")
            
            # 6. Scan de contenu (basique)
            if not cls._scan_file_content(file):
                result['valid'] = False
                result['errors'].append("Contenu de fichier suspect détecté")
            
            # 7. Logging de sécurité
            if user:
                logger.info(f"Upload de fichier par {user.username}: {filename} ({mime_type}, {file_size} bytes)")
            
            if not result['valid']:
                logger.warning(f"Tentative d'upload de fichier non sécurisé par {user.username if user else 'anonyme'}: {filename}")
            
        except Exception as e:
            result['valid'] = False
            result['errors'].append(f"Erreur lors de la validation: {str(e)}")
            logger.error(f"Erreur de validation de fichier: {e}")
        
        return result
    
    @classmethod
    def _get_mime_type(cls, file):
        """Détermine le type MIME d'un fichier"""
        try:
            # Essayer d'abord avec python-magic si disponible
            if MAGIC_AVAILABLE and hasattr(magic, 'from_buffer'):
                file.seek(0)
                mime = magic.from_buffer(file.read(1024), mime=True)
                file.seek(0)
                return mime
        except:
            pass
        
        # Fallback avec mimetypes
        mime_type, _ = mimetypes.guess_type(file.name)
        return mime_type or 'application/octet-stream'
    
    @classmethod
    def _is_extension_mime_consistent(cls, extension, mime_type):
        """Vérifie la cohérence entre extension et type MIME"""
        if not mime_type:
            return True
        
        # Mapping des extensions vers types MIME
        extension_mime_map = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.pdf': 'application/pdf',
            '.doc': 'application/msword',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.txt': 'text/plain',
            '.zip': 'application/zip',
        }
        
        expected_mime = extension_mime_map.get(extension.lower())
        if expected_mime:
            return mime_type == expected_mime
        
        return True
    
    @classmethod
    def _scan_file_content(cls, file):
        """Scan basique du contenu du fichier"""
        try:
            file.seek(0)
            content = file.read(1024)  # Lire les premiers 1024 bytes
            
            # Vérifier les signatures de fichiers dangereux
            dangerous_signatures = [
                b'<script',
                b'javascript:',
                b'vbscript:',
                b'<?php',
                b'<iframe',
                b'<object',
                b'<embed',
            ]
            
            for signature in dangerous_signatures:
                if signature in content.lower():
                    return False
            
            # Vérifier les headers de fichiers valides
            valid_headers = [
                b'\x89PNG',  # PNG
                b'\xFF\xD8\xFF',  # JPEG
                b'GIF8',  # GIF
                b'%PDF',  # PDF
                b'PK\x03\x04',  # ZIP
                b'\x50\x4B',  # ZIP/DOCX
            ]
            
            # Si c'est un fichier binaire, vérifier qu'il a un header valide
            if any(header in content for header in valid_headers):
                return True
            
            # Pour les fichiers texte, vérifier qu'ils ne contiennent pas de code exécutable
            if b'\x00' not in content:  # Fichier texte
                text_content = content.decode('utf-8', errors='ignore').lower()
                if any(keyword in text_content for keyword in ['<script', 'javascript:', 'eval(', 'function(']):
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors du scan de contenu: {e}")
            return False
        finally:
            file.seek(0)
    
    @classmethod
    def get_safe_filename(cls, filename):
        """Génère un nom de fichier sécurisé"""
        import re
        import uuid
        
        # Supprimer les caractères dangereux
        safe_name = re.sub(r'[<>:"/\\|?*]', '_', filename)
        
        # Limiter la longueur
        name, ext = os.path.splitext(safe_name)
        if len(name) > 200:
            name = name[:200]
        
        # Ajouter un UUID pour éviter les collisions
        unique_id = str(uuid.uuid4())[:8]
        safe_name = f"{name}_{unique_id}{ext}"
        
        return safe_name

class SecureFileField:
    """Champ de fichier sécurisé pour les formulaires Django"""
    
    def __init__(self, category='default', max_size=None, allowed_types=None):
        self.category = category
        self.max_size = max_size or FileSecurityValidator.MAX_FILE_SIZES.get(category, 5*1024*1024)
        self.allowed_types = allowed_types or FileSecurityValidator.ALLOWED_EXTENSIONS.get(category, [])
    
    def clean(self, value):
        """Nettoie et valide un fichier uploadé"""
        if not value:
            return value
        
        # Validation de sécurité
        result = FileSecurityValidator.validate_file_security(
            value, 
            category=self.category
        )
        
        if not result['valid']:
            raise ValidationError(result['errors'])
        
        # Générer un nom de fichier sécurisé
        if hasattr(value, 'name'):
            value.name = FileSecurityValidator.get_safe_filename(value.name)
        
        return value
