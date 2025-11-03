"""
Service pour la génération de documents unifiés A5 (récépissés et quittances)
"""
from django.template.loader import render_to_string
from django.template import Context, Template
from django.utils import timezone
from core.models import ConfigurationEntreprise
from paiements.models import Paiement
from contrats.models import Contrat
from proprietes.models import Propriete
from utilisateurs.models import Utilisateur
import os
from django.conf import settings


class DocumentUnifieA5Service:
    """Service pour générer des documents A5 unifiés."""
    
    def __init__(self):
        self.config_entreprise = ConfigurationEntreprise.get_configuration_active()
    
    def generer_recu_unifie(self, paiement_id, document_type='recu', user=None):
        """
        Génère une quittance unifiée au format A5.
        
        Args:
            paiement_id (int): ID du paiement
            document_type (str): Type de document ('recu', 'quittance', 'avance', 'caution')
            user: Utilisateur qui génère le document
        
        Returns:
            str: HTML du document généré
        """
        try:
            paiement = Paiement.objects.select_related(
                'contrat__locataire',
                'contrat__propriete__type_bien',
                'contrat__propriete__bailleur'
            ).get(id=paiement_id)
            
            # Déterminer le type de document et le titre
            document_titles = {
                'recu': 'QUITTANCE DE PAIEMENT',
                'quittance': 'QUITTANCE DE LOYER',
                'avance': 'QUITTANCE DE PAIEMENT D\'AVANCE',
                'caution': 'QUITTANCE DE PAIEMENT DE CAUTION'
            }
            
            document_title = document_titles.get(document_type, 'QUITTANCE DE PAIEMENT')
            
            # Calculer les mois couverts par l'avance si c'est une avance
            mois_couverts = None
            if document_type == 'avance' and paiement.montant > 0 and paiement.contrat.loyer_mensuel > 0:
                mois_couverts = self._calculer_mois_couverts_avance(paiement)
                print(f"DEBUG: mois_couverts calculés: {mois_couverts}")  # Debug
            elif document_type == 'avance':
                print(f"DEBUG: Avance détectée mais conditions non remplies - montant: {paiement.montant}, loyer: {paiement.contrat.loyer_mensuel}")  # Debug
            
            # Préparer les données du document
            context = {
                'document_title': document_title,
                'document_type': document_type,
                'document_number': paiement.numero_paiement,
                'generation_date': timezone.now(),
                'config_entreprise': self.config_entreprise,
                'user': user,  # Ajouter l'utilisateur au contexte
                
                # Informations du paiement
                'type_paiement': paiement.get_type_paiement_display(),
                'mode_paiement': paiement.get_mode_paiement_display(),
                'date_paiement': paiement.date_paiement,
                'numero_cheque': paiement.numero_cheque,
                'reference_virement': paiement.reference_virement,
                
                # Montants
                'montant_total': paiement.montant,
                'montant_lettres': self._convertir_en_lettres(paiement.montant),
                'montant_loyer': paiement.contrat.loyer_mensuel,
                'montant_charges_deduites': getattr(paiement, 'montant_charges_deduites', 0),
                'montant_net_paye': getattr(paiement, 'montant_net_paye', paiement.montant),
                'montant_net_lettres': self._convertir_en_lettres(getattr(paiement, 'montant_net_paye', paiement.montant)),
                
                # Logique avance dynamique
                'mois_couverts': mois_couverts,
                'mois_couverts_lettres': self._convertir_mois_couverts_en_lettres(mois_couverts) if mois_couverts else None,
                
                # Informations des entités
                'locataire': paiement.contrat.locataire,
                'propriete': paiement.contrat.propriete,
                'bailleur': paiement.contrat.propriete.bailleur,
                'contrat': paiement.contrat,
                'paiement': paiement,  # IMPORTANT: Passer le paiement pour accéder à mois_paye
                
                # Charges déductibles (si applicable)
                'charges_deduites': getattr(paiement, 'charges_deduites', []),
            }
            
            # Rendre le template
            html_content = render_to_string(
                'paiements/recu_quittance_unifie_a5.html',
                context
            )
            
            return html_content
            
        except Paiement.DoesNotExist:
            raise ValueError(f"Paiement avec l'ID {paiement_id} introuvable")
        except Exception as e:
            raise Exception(f"Erreur lors de la génération du document: {str(e)}")
    
    def generer_quittance_unifie(self, paiement_id):
        """Génère une quittance unifiée au format A5."""
        return self.generer_recu_unifie(paiement_id, 'quittance')
    
    def generer_avance_unifie(self, paiement_id):
        """Génère un récépissé d'avance unifié au format A5."""
        return self.generer_recu_unifie(paiement_id, 'avance')
    
    def generer_caution_unifie(self, paiement_id):
        """Génère un récépissé de caution unifié au format A5."""
        return self.generer_recu_unifie(paiement_id, 'caution')
    
    def _convertir_en_lettres(self, montant):
        """
        Convertit un montant en lettres (version simplifiée).
        Pour une version complète, utiliser une bibliothèque comme num2words.
        """
        if not montant or montant == 0:
            return "Zéro"
        
        # Version simplifiée - à améliorer avec une vraie conversion
        try:
            montant_int = int(montant)
            if montant_int < 1000:
                return f"{montant_int} francs CFA"
            elif montant_int < 1000000:
                milliers = montant_int // 1000
                reste = montant_int % 1000
                if reste == 0:
                    return f"{milliers} mille francs CFA"
                else:
                    return f"{milliers} mille {reste} francs CFA"
            else:
                millions = montant_int // 1000000
                reste = montant_int % 1000000
                if reste == 0:
                    return f"{millions} million(s) francs CFA"
                else:
                    milliers_reste = reste // 1000
                    if milliers_reste > 0:
                        return f"{millions} million(s) {milliers_reste} mille francs CFA"
                    else:
                        return f"{millions} million(s) {reste} francs CFA"
        except (ValueError, TypeError):
            return f"{montant} francs CFA"
    
    def verifier_image_entete(self):
        """Vérifie que l'image d'en-tête existe."""
        image_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'enteteEnImage.png')
        return os.path.exists(image_path)
    
    def get_chemin_image_entete(self):
        """Retourne le chemin de l'image d'en-tête."""
        return os.path.join(settings.STATIC_URL, 'images', 'enteteEnImage.png')
    
    def _calculer_mois_couverts_avance(self, paiement):
        """
        Calcule le nombre de mois couverts par l'avance basé sur le montant et le loyer mensuel.
        Retourne un dictionnaire avec le nombre de mois et la liste des mois.
        """
        try:
            montant_avance = float(paiement.montant)
            loyer_mensuel = float(paiement.contrat.loyer_mensuel)
            
            if loyer_mensuel <= 0:
                return None
                
            # Calculer le nombre de mois complets
            mois_entiers = int(montant_avance // loyer_mensuel)
            
            # Calculer le reste
            reste = montant_avance % loyer_mensuel
            
            # Si le reste est significatif (plus de 50% du loyer), compter un mois partiel
            if reste > (loyer_mensuel * 0.5):
                mois_entiers += 1
            
            nombre_mois = max(1, mois_entiers)  # Au minimum 1 mois
            
            # Calculer les mois couverts à partir de la date du paiement
            from datetime import datetime, timedelta
            from dateutil.relativedelta import relativedelta
            import locale
            
            # Définir la locale française pour les mois
            try:
                locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')
            except:
                try:
                    locale.setlocale(locale.LC_TIME, 'French_France.1252')
                except:
                    pass  # Utiliser les noms par défaut si la locale française n'est pas disponible
            
            date_paiement = paiement.date_paiement
            mois_couverts = []
            
            # Dictionnaire de traduction des mois en français
            mois_francais = {
                1: 'Janvier', 2: 'Février', 3: 'Mars', 4: 'Avril',
                5: 'Mai', 6: 'Juin', 7: 'Juillet', 8: 'Août',
                9: 'Septembre', 10: 'Octobre', 11: 'Novembre', 12: 'Décembre'
            }
            
            for i in range(nombre_mois):
                mois_couvert = date_paiement + relativedelta(months=i)
                mois_nom = mois_francais.get(mois_couvert.month, mois_couvert.strftime("%B"))
                mois_couverts.append(f"{mois_nom} {mois_couvert.year}")
            
            return {
                'nombre': nombre_mois,
                'mois_liste': mois_couverts,
                'mois_texte': ', '.join(mois_couverts)
            }
            
        except (ValueError, TypeError, ZeroDivisionError, ImportError):
            return None
    
    def _convertir_mois_couverts_en_lettres(self, mois_couverts):
        """
        Convertit le nombre de mois couverts en lettres.
        """
        if not mois_couverts or not isinstance(mois_couverts, dict):
            return None
            
        try:
            mois = mois_couverts.get('nombre', 0)
            if mois == 1:
                return "un mois"
            elif mois == 2:
                return "deux mois"
            elif mois == 3:
                return "trois mois"
            elif mois == 4:
                return "quatre mois"
            elif mois == 5:
                return "cinq mois"
            elif mois == 6:
                return "six mois"
            elif mois == 7:
                return "sept mois"
            elif mois == 8:
                return "huit mois"
            elif mois == 9:
                return "neuf mois"
            elif mois == 10:
                return "dix mois"
            elif mois == 11:
                return "onze mois"
            elif mois == 12:
                return "douze mois"
            else:
                return f"{mois} mois"
        except (ValueError, TypeError):
            return f"{mois_couverts} mois"


class DocumentUnifieA5ViewMixin:
    """Mixin pour les vues utilisant le service de documents unifiés A5."""
    
    def __init__(self):
        self.document_service = DocumentUnifieA5Service()
    
    def generer_document_html(self, paiement_id, document_type='recu'):
        """Génère le HTML du document."""
        return self.document_service.generer_recu_unifie(paiement_id, document_type)
    
    def get_context_data_for_document(self, paiement_id, document_type='recu'):
        """Prépare les données de contexte pour le document."""
        try:
            paiement = Paiement.objects.select_related(
                'contrat__locataire',
                'contrat__propriete__type_bien',
                'contrat__propriete__bailleur'
            ).get(id=paiement_id)
            
            return {
                'paiement': paiement,
                'document_type': document_type,
                'config_entreprise': self.document_service.config_entreprise,
                'image_entete_exists': self.document_service.verifier_image_entete(),
            }
        except Paiement.DoesNotExist:
            return None


