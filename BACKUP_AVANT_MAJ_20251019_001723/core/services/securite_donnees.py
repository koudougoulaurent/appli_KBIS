"""
Services de sécurité pour la protection des données sensibles
dans les tableaux de bord d'entreprise.
"""

from typing import Dict, List, Any, Optional, Union
from django.contrib.auth.models import User, Group
from django.db.models import QuerySet
from django.utils import timezone
from datetime import timedelta
import hashlib
import logging
from dataclasses import dataclass
from decimal import Decimal

from ..models import NiveauAcces, PermissionTableauBord, LogAccesDonnees
from utilisateurs.models import Utilisateur


logger = logging.getLogger(__name__)


@dataclass
class NiveauSecurite:
    """Classe pour représenter un niveau de sécurité utilisateur."""
    niveau: str
    priorite: int
    permissions: List[str]
    peut_voir_montants: bool
    peut_voir_details: bool
    peut_exporter: bool


class ServiceSecuriteDonnees:
    """Service principal pour gérer la sécurité des données."""
    
    def __init__(self):
        self.cache_permissions = {}
        self.cache_niveaux = {}
    
    def obtenir_niveau_securite_utilisateur(self, utilisateur: Utilisateur) -> NiveauSecurite:
        """Détermine le niveau de sécurité d'un utilisateur."""
        if utilisateur.id in self.cache_niveaux:
            return self.cache_niveaux[utilisateur.id]
        
        # Vérifier les groupes de l'utilisateur
        groupes_utilisateur = utilisateur.groups.all()
        niveau_max = None
        priorite_max = 0
        
        for groupe in groupes_utilisateur:
            niveaux = NiveauAcces.objects.filter(
                groupes_autorises=groupe,
                actif=True
            )
            
            for niveau in niveaux:
                if niveau.priorite > priorite_max:
                    niveau_max = niveau
                    priorite_max = niveau.priorite
        
        if not niveau_max:
            # Niveau par défaut pour utilisateurs sans permissions spéciales
            niveau_securite = NiveauSecurite(
                niveau='public',
                priorite=1,
                permissions=['consultation_basique'],
                peut_voir_montants=False,
                peut_voir_details=False,
                peut_exporter=False
            )
        else:
            # Construire le niveau basé sur les permissions
            permissions_tableau = PermissionTableauBord.objects.filter(
                niveau_acces_requis__priorite__lte=priorite_max,
                actif=True
            )
            
            niveau_securite = NiveauSecurite(
                niveau=niveau_max.niveau,
                priorite=priorite_max,
                permissions=[p.nom for p in permissions_tableau],
                peut_voir_montants=any(p.peut_voir_montants for p in permissions_tableau),
                peut_voir_details=any(p.peut_voir_details_personnels for p in permissions_tableau),
                peut_exporter=any(p.peut_exporter for p in permissions_tableau)
            )
        
        # Mise en cache
        self.cache_niveaux[utilisateur.id] = niveau_securite
        return niveau_securite
    
    def filtrer_donnees_selon_niveau(
        self, 
        donnees: Union[QuerySet, List[Dict]], 
        utilisateur: Utilisateur,
        type_donnees: str
    ) -> Union[QuerySet, List[Dict]]:
        """Filtre les données selon le niveau de sécurité de l'utilisateur."""
        niveau = self.obtenir_niveau_securite_utilisateur(utilisateur)
        
        # Journaliser l'accès
        self.journaliser_acces(
            utilisateur=utilisateur,
            type_action='consultation',
            type_donnees=type_donnees,
            niveau_acces=niveau
        )
        
        if isinstance(donnees, QuerySet):
            return self._filtrer_queryset(donnees, niveau, type_donnees)
        else:
            return self._filtrer_liste_dict(donnees, niveau, type_donnees)
    
    def _filtrer_queryset(self, queryset: QuerySet, niveau: NiveauSecurite, type_donnees: str) -> QuerySet:
        """Filtre un QuerySet selon le niveau de sécurité."""
        # Limitation temporelle pour les données sensibles
        if niveau.priorite < 7:  # Niveaux inférieurs à "secret"
            date_limite = timezone.now() - timedelta(days=90)
            if hasattr(queryset.model, 'date_creation'):
                queryset = queryset.filter(date_creation__gte=date_limite)
            elif hasattr(queryset.model, 'date_modification'):
                queryset = queryset.filter(date_modification__gte=date_limite)
        
        # Limitation du nombre de résultats
        if niveau.priorite < 5:  # Niveaux basiques
            queryset = queryset[:100]
        elif niveau.priorite < 8:  # Niveaux intermédiaires
            queryset = queryset[:500]
        
        return queryset
    
    def _filtrer_liste_dict(self, donnees: List[Dict], niveau: NiveauSecurite, type_donnees: str) -> List[Dict]:
        """Filtre une liste de dictionnaires selon le niveau de sécurité."""
        donnees_filtrees = []
        
        for item in donnees:
            item_filtre = self._filtrer_item_dict(item, niveau, type_donnees)
            if item_filtre:
                donnees_filtrees.append(item_filtre)
        
        return donnees_filtrees
    
    def _filtrer_item_dict(self, item: Dict, niveau: NiveauSecurite, type_donnees: str) -> Optional[Dict]:
        """Filtre un élément dictionnaire selon le niveau de sécurité."""
        item_filtre = item.copy()
        
        # Masquer les montants si pas autorisé
        if not niveau.peut_voir_montants:
            for cle in item_filtre.keys():
                if any(mot in cle.lower() for mot in ['montant', 'prix', 'loyer', 'charge', 'cout']):
                    if isinstance(item_filtre[cle], (int, float, Decimal)):
                        item_filtre[cle] = "***"
        
        # Masquer les détails personnels si pas autorisé
        if not niveau.peut_voir_details:
            champs_sensibles = [
                'nom', 'prenom', 'email', 'telephone', 'adresse',
                'numero_compte', 'iban', 'numero_piece_identite'
            ]
            for champ in champs_sensibles:
                if champ in item_filtre:
                    if isinstance(item_filtre[champ], str) and len(item_filtre[champ]) > 2:
                        # Anonymiser : garder les 2 premiers caractères
                        item_filtre[champ] = item_filtre[champ][:2] + "*" * (len(item_filtre[champ]) - 2)
        
        # Anonymisation complète pour les niveaux très bas
        if niveau.priorite < 3:
            # Remplacer les identifiants par des hashes
            if 'id' in item_filtre:
                item_filtre['id_anonyme'] = self._generer_hash_anonyme(str(item_filtre['id']))
                del item_filtre['id']
        
        return item_filtre
    
    def _generer_hash_anonyme(self, valeur: str) -> str:
        """Génère un hash anonyme pour masquer les identifiants."""
        return hashlib.md5(f"anon_{valeur}".encode()).hexdigest()[:8]
    
    def masquer_donnees_sensibles(self, donnees: Dict, niveau: NiveauSecurite) -> Dict:
        """Masque les données sensibles selon le niveau d'accès."""
        donnees_masquees = donnees.copy()
        
        if niveau.priorite < 6:  # Niveaux confidentiels et inférieurs
            # Masquer les informations financières détaillées
            if 'details_financiers' in donnees_masquees:
                donnees_masquees['details_financiers'] = {
                    'resume_disponible': True,
                    'acces_complet_requis': 'Niveau Secret ou supérieur'
                }
            
            # Masquer les informations personnelles complètes
            if 'informations_personnelles' in donnees_masquees:
                donnees_masquees['informations_personnelles'] = {
                    'nombre_personnes': len(donnees_masquees['informations_personnelles']),
                    'details_masques': True
                }
        
        return donnees_masquees
    
    def journaliser_acces(
        self, 
        utilisateur: Utilisateur, 
        type_action: str, 
        type_donnees: str,
        niveau_acces: NiveauSecurite,
        identifiant_objet: Optional[str] = None,
        adresse_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
        succes: bool = True,
        message_erreur: Optional[str] = None
    ):
        """Journalise un accès aux données."""
        try:
            # Obtenir le niveau d'accès correspondant
            niveau_obj = NiveauAcces.objects.filter(
                niveau=niveau_acces.niveau,
                priorite=niveau_acces.priorite
            ).first()
            
            if not niveau_obj:
                # Créer un niveau temporaire si nécessaire
                niveau_obj = NiveauAcces.objects.create(
                    nom=f"Niveau {niveau_acces.niveau}",
                    niveau=niveau_acces.niveau,
                    description=f"Niveau automatiquement créé",
                    priorite=niveau_acces.priorite
                )
            
            LogAccesDonnees.objects.create(
                utilisateur=utilisateur,
                type_action=type_action,
                type_donnees=type_donnees,
                identifiant_objet=identifiant_objet,
                niveau_acces_utilise=niveau_obj,
                adresse_ip=adresse_ip,
                user_agent=user_agent,
                succes=succes,
                message_erreur=message_erreur
            )
            
        except Exception as e:
            logger.error(f"Erreur lors de la journalisation d'accès: {e}")
    
    def verifier_autorisation_export(self, utilisateur: Utilisateur, type_donnees: str) -> bool:
        """Vérifie si un utilisateur peut exporter des données."""
        niveau = self.obtenir_niveau_securite_utilisateur(utilisateur)
        
        # Journaliser la tentative d'export
        self.journaliser_acces(
            utilisateur=utilisateur,
            type_action='export',
            type_donnees=type_donnees,
            niveau_acces=niveau
        )
        
        return niveau.peut_exporter and niveau.priorite >= 5
    
    def obtenir_statistiques_securite(self, utilisateur: Utilisateur) -> Dict[str, Any]:
        """Obtient les statistiques de sécurité pour un utilisateur."""
        niveau = self.obtenir_niveau_securite_utilisateur(utilisateur)
        
        if niveau.priorite < 8:  # Seuls les niveaux très élevés peuvent voir les stats
            return {
                'acces_refuse': True,
                'message': 'Niveau d\'autorisation insuffisant'
            }
        
        # Statistiques des accès récents
        logs_recents = LogAccesDonnees.objects.filter(
            timestamp__gte=timezone.now() - timedelta(days=30)
        )
        
        return {
            'niveau_utilisateur': niveau.niveau,
            'priorite': niveau.priorite,
            'acces_recents': logs_recents.count(),
            'types_donnees_accedees': list(
                logs_recents.values_list('type_donnees', flat=True).distinct()
            ),
            'utilisateurs_actifs': logs_recents.values('utilisateur').distinct().count()
        }
    
    def nettoyer_cache_permissions(self):
        """Nettoie le cache des permissions (à appeler périodiquement)."""
        self.cache_permissions.clear()
        self.cache_niveaux.clear()
        logger.info("Cache des permissions nettoyé")


# Instance globale du service
service_securite = ServiceSecuriteDonnees()
