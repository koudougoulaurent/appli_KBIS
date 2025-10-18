"""
Système de protection contre les injections SQL
"""
import re
import logging
from django.db import connection
from django.core.exceptions import ValidationError, SuspiciousOperation
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from typing import List, Dict, Any, Union
import json

logger = logging.getLogger(__name__)


class SQLInjectionProtection:
    """Classe principale pour la protection contre les injections SQL"""
    
    # Patterns dangereux à détecter
    DANGEROUS_PATTERNS = [
        # Injection SQL classique
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE|UNION|SCRIPT)\b)",
        r"(\b(OR|AND)\s+\d+\s*=\s*\d+)",
        r"(\b(OR|AND)\s+'.*'\s*=\s*'.*')",
        r"(\b(OR|AND)\s+\".*\"\s*=\s*\".*\")",
        
        # Commentaires SQL
        r"(--|#|\/\*|\*\/)",
        
        # Caractères spéciaux dangereux
        r"([;'\"\\])",
        
        # Tentatives de contournement
        r"(\b(OR|AND)\s+1\s*=\s*1)",
        r"(\b(OR|AND)\s+true)",
        r"(\b(OR|AND)\s+false)",
        
        # Fonctions système
        r"(\b(LOAD_FILE|INTO\s+OUTFILE|INTO\s+DUMPFILE)\b)",
        r"(\b(CHAR|ASCII|ORD|HEX|UNHEX)\s*\()",
        r"(\b(SLEEP|BENCHMARK|WAITFOR)\s*\()",
        
        # Tentatives d'échappement
        r"(\\(x[0-9a-fA-F]{2}|[0-7]{3}))",
        r"(\b(CHAR|CHR)\s*\(\s*\d+\s*\))",
        
        # Injection de commandes
        r"(\b(SYSTEM|SHELL|CMD|POWERSHELL|BASH)\b)",
        r"(\b(COPY|MOVE|DEL|RM|RMDIR|MKDIR)\b)",
    ]
    
    # Patterns de validation pour les identifiants
    SAFE_IDENTIFIER_PATTERN = r'^[a-zA-Z_][a-zA-Z0-9_]*$'
    
    # Patterns de validation pour les valeurs
    SAFE_VALUE_PATTERNS = {
        'integer': r'^\d+$',
        'decimal': r'^\d+(\.\d+)?$',
        'string': r'^[a-zA-Z0-9\s\-_.,!?@#$%^&*()+=\[\]{}|\\:";\'<>?/~`]*$',
        'email': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
        'phone': r'^[\+]?[0-9\s\-\(\)]{8,20}$',
        'date': r'^\d{4}-\d{2}-\d{2}$',
        'datetime': r'^\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}$',
    }
    
    @classmethod
    def detect_sql_injection(cls, input_string: str) -> bool:
        """
        Détecte une tentative d'injection SQL dans une chaîne
        
        Args:
            input_string: La chaîne à analyser
            
        Returns:
            bool: True si une injection est détectée, False sinon
        """
        if not input_string or not isinstance(input_string, str):
            return False
        
        input_upper = input_string.upper()
        
        # Vérifier les patterns dangereux
        for pattern in cls.DANGEROUS_PATTERNS:
            if re.search(pattern, input_upper, re.IGNORECASE):
                logger.warning(f"SQL Injection détectée: {pattern} dans '{input_string}'")
                return True
        
        # Vérifier les tentatives d'échappement de guillemets
        if cls._has_quote_escaping(input_string):
            logger.warning(f"Tentative d'echappement de guillemets detectee: '{input_string}'")
            return True
        
        # Vérifier les tentatives de commentaires
        if cls._has_sql_comments(input_string):
            logger.warning(f"Commentaires SQL détectés: '{input_string}'")
            return True
        
        return False
    
    @classmethod
    def _has_quote_escaping(cls, input_string: str) -> bool:
        """Vérifie les tentatives d'échappement de guillemets"""
        dangerous_quotes = ["'", '"', '`']
        for quote in dangerous_quotes:
            if quote in input_string:
                # Vérifier les patterns d'échappement
                if f"\\{quote}" in input_string or f"'{quote}" in input_string:
                    return True
        return False
    
    @classmethod
    def _has_sql_comments(cls, input_string: str) -> bool:
        """Vérifie la présence de commentaires SQL"""
        comment_patterns = ['--', '#', '/*', '*/']
        for pattern in comment_patterns:
            if pattern in input_string:
                return True
        return False
    
    @classmethod
    def sanitize_input(cls, input_value: Any, input_type: str = 'string') -> Any:
        """
        Nettoie une entrée utilisateur
        
        Args:
            input_value: La valeur à nettoyer
            input_type: Le type attendu ('string', 'integer', 'decimal', 'email', 'phone', 'date', 'datetime')
            
        Returns:
            La valeur nettoyée
            
        Raises:
            ValidationError: Si la valeur est dangereuse ou invalide
        """
        if input_value is None:
            return None
        
        # Convertir en chaîne pour l'analyse
        str_value = str(input_value).strip()
        
        # Détecter les injections SQL
        if cls.detect_sql_injection(str_value):
            raise ValidationError(
                _("Entrée suspecte détectée. Caractères non autorisés.")
            )
        
        # Valider selon le type
        if input_type in cls.SAFE_VALUE_PATTERNS:
            pattern = cls.SAFE_VALUE_PATTERNS[input_type]
            if not re.match(pattern, str_value):
                raise ValidationError(
                    _(f"Format invalide pour le type {input_type}")
                )
        
        # Nettoyer selon le type
        if input_type == 'integer':
            return int(str_value)
        elif input_type == 'decimal':
            return float(str_value)
        elif input_type == 'string':
            return cls._clean_string(str_value)
        else:
            return str_value
    
    @classmethod
    def _clean_string(cls, input_string: str) -> str:
        """Nettoie une chaîne de caractères"""
        # Supprimer les caractères de contrôle
        cleaned = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', input_string)
        
        # Limiter la longueur
        max_length = getattr(settings, 'MAX_INPUT_LENGTH', 1000)
        if len(cleaned) > max_length:
            cleaned = cleaned[:max_length]
        
        return cleaned
    
    @classmethod
    def validate_identifier(cls, identifier: str) -> bool:
        """
        Valide un identifiant de base de données (nom de table, colonne, etc.)
        
        Args:
            identifier: L'identifiant à valider
            
        Returns:
            bool: True si l'identifiant est valide, False sinon
        """
        if not identifier or not isinstance(identifier, str):
            return False
        
        # Vérifier le pattern de base
        if not re.match(cls.SAFE_IDENTIFIER_PATTERN, identifier):
            return False
        
        # Vérifier qu'il n'y a pas d'injection
        if cls.detect_sql_injection(identifier):
            return False
        
        return True
    
    @classmethod
    def safe_raw_query(cls, query: str, params: List[Any] = None) -> Dict[str, Any]:
        """
        Exécute une requête SQL brute de manière sécurisée
        
        Args:
            query: La requête SQL
            params: Les paramètres de la requête
            
        Returns:
            Dict contenant les résultats et métadonnées
            
        Raises:
            ValidationError: Si la requête est dangereuse
        """
        # Valider la requête
        if cls.detect_sql_injection(query):
            raise ValidationError(_("Requête SQL suspecte détectée"))
        
        # Valider les paramètres
        if params:
            for param in params:
                if isinstance(param, str) and cls.detect_sql_injection(param):
                    raise ValidationError(_("Paramètre suspect détecté"))
        
        # Exécuter la requête
        try:
            with connection.cursor() as cursor:
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                # Récupérer les résultats
                if query.strip().upper().startswith('SELECT'):
                    results = cursor.fetchall()
                    columns = [desc[0] for desc in cursor.description] if cursor.description else []
                    
                    return {
                        'success': True,
                        'results': results,
                        'columns': columns,
                        'row_count': len(results)
                    }
                else:
                    return {
                        'success': True,
                        'row_count': cursor.rowcount
                    }
        
        except Exception as e:
            logger.error(f"Erreur lors de l'exécution de la requête SQL: {e}")
            raise ValidationError(_("Erreur lors de l'exécution de la requête"))
    
    @classmethod
    def log_suspicious_activity(cls, user_id: int, activity: str, details: Dict[str, Any]):
        """
        Enregistre une activité suspecte
        
        Args:
            user_id: ID de l'utilisateur
            activity: Type d'activité
            details: Détails de l'activité
        """
        logger.warning(
            f"Activité suspecte détectée - "
            f"Utilisateur: {user_id}, "
            f"Activité: {activity}, "
            f"Détails: {json.dumps(details)}"
        )


class SecureQueryBuilder:
    """Constructeur de requêtes sécurisé"""
    
    @staticmethod
    def build_select_query(
        table: str,
        columns: List[str] = None,
        where_clause: str = None,
        where_params: List[Any] = None,
        order_by: str = None,
        limit: int = None
    ) -> Dict[str, Any]:
        """
        Construit une requête SELECT sécurisée
        
        Args:
            table: Nom de la table
            columns: Liste des colonnes à sélectionner
            where_clause: Clause WHERE
            where_params: Paramètres de la clause WHERE
            order_by: Clause ORDER BY
            limit: Limite du nombre de résultats
            
        Returns:
            Dict contenant la requête et les paramètres
        """
        # Valider le nom de la table
        if not SQLInjectionProtection.validate_identifier(table):
            raise ValidationError(_("Nom de table invalide"))
        
        # Construire la requête
        if columns:
            # Valider les noms de colonnes
            for col in columns:
                if not SQLInjectionProtection.validate_identifier(col):
                    raise ValidationError(_("Nom de colonne invalide"))
            columns_str = ', '.join(columns)
        else:
            columns_str = '*'
        
        query = f"SELECT {columns_str} FROM {table}"
        params = []
        
        # Ajouter la clause WHERE
        if where_clause:
            if SQLInjectionProtection.detect_sql_injection(where_clause):
                raise ValidationError(_("Clause WHERE suspecte"))
            query += f" WHERE {where_clause}"
            if where_params:
                params.extend(where_params)
        
        # Ajouter ORDER BY
        if order_by:
            if SQLInjectionProtection.detect_sql_injection(order_by):
                raise ValidationError(_("Clause ORDER BY suspecte"))
            query += f" ORDER BY {order_by}"
        
        # Ajouter LIMIT
        if limit:
            if not isinstance(limit, int) or limit <= 0:
                raise ValidationError(_("Limite invalide"))
            query += f" LIMIT {limit}"
        
        return {
            'query': query,
            'params': params
        }


class SQLSecurityMiddleware:
    """Middleware pour la protection contre les injections SQL"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Analyser les paramètres de la requête
        self._analyze_request(request)
        
        response = self.get_response(request)
        return response
    
    def _analyze_request(self, request):
        """Analyse la requête pour détecter les injections SQL"""
        # Analyser les paramètres GET
        for key, value in request.GET.items():
            if SQLInjectionProtection.detect_sql_injection(str(value)):
                SQLInjectionProtection.log_suspicious_activity(
                    getattr(request.user, 'id', None),
                    'SQL_INJECTION_GET',
                    {'parameter': key, 'value': str(value)}
                )
                raise SuspiciousOperation("Tentative d'injection SQL détectée")
        
        # Analyser les paramètres POST
        if request.method == 'POST':
            for key, value in request.POST.items():
                if SQLInjectionProtection.detect_sql_injection(str(value)):
                    SQLInjectionProtection.log_suspicious_activity(
                        getattr(request.user, 'id', None),
                        'SQL_INJECTION_POST',
                        {'parameter': key, 'value': str(value)}
                    )
                    raise SuspiciousOperation("Tentative d'injection SQL détectée")


# Décorateur pour sécuriser les vues
def secure_sql_view(view_func):
    """
    Décorateur pour sécuriser les vues contre les injections SQL
    """
    def wrapper(request, *args, **kwargs):
        # Analyser tous les paramètres
        all_params = {}
        all_params.update(request.GET)
        if request.method == 'POST':
            all_params.update(request.POST)
        
        for key, value in all_params.items():
            if SQLInjectionProtection.detect_sql_injection(str(value)):
                raise SuspiciousOperation("Tentative d'injection SQL détectée")
        
        return view_func(request, *args, **kwargs)
    
    return wrapper
