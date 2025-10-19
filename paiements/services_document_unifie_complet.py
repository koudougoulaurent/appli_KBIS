"""
Service unifié pour la génération de TOUS les documents A5
- Paiements (récépissés, quittances, avances, cautions)
- Retraits bailleurs (quittances de retrait)
- Récapitulatifs (quittances de récapitulatif)
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


class DocumentUnifieA5ServiceComplet:
    """Service unifié pour générer TOUS les documents A5."""
    
    def __init__(self):
        self.config_entreprise = ConfigurationEntreprise.get_configuration_active()
    
    def generer_document_unifie(self, document_type, **kwargs):
        """
        Génère un document unifié au format A5.
        
        Args:
            document_type (str): Type de document
                - 'paiement_recu': Récépissé de paiement
                - 'paiement_quittance': Quittance de paiement
                - 'paiement_avance': Récépissé d'avance
                - 'paiement_caution': Récépissé de caution
                - 'retrait_quittance': Quittance de retrait
                - 'recap_quittance': Quittance de récapitulatif
        
        Returns:
            str: HTML du document généré
        """
        try:
            # Déterminer le type de document et le titre
            document_titles = {
                'paiement_recu': 'RÉCÉPISSÉ DE PAIEMENT',
                'paiement_quittance': 'QUITTANCE DE PAIEMENT',
                'paiement_avance': 'RÉCÉPISSÉ DE PAIEMENT D\'AVANCE',
                'paiement_caution': 'RÉCÉPISSÉ DE PAIEMENT DE CAUTION',
                'retrait_quittance': 'RÉCÉPISSÉ DE RETRAIT',
                'retrait_recu': 'RÉCÉPISSÉ DE RETRAIT',
                'recap_quittance': 'QUITTANCE DE RÉCAPITULATIF'
            }
            
            document_title = document_titles.get(document_type, 'DOCUMENT')
            
            # Préparer le contexte selon le type de document
            if document_type.startswith('paiement_'):
                context = self._prepare_paiement_context(document_type, **kwargs)
            elif document_type in ['retrait_quittance', 'retrait_recu']:
                context = self._prepare_retrait_context(**kwargs)
            elif document_type == 'recap_quittance':
                context = self._prepare_recap_context(**kwargs)
            else:
                raise ValueError(f"Type de document non supporté: {document_type}")
            
            # Ajouter les données communes
            context.update({
                'document_title': document_title,
                'document_type': document_type,
                'generation_date': timezone.now(),
                'config_entreprise': self.config_entreprise,
            })
            
            # Rendre le template
            html_content = render_to_string(
                'paiements/document_unifie_a5_complet.html',
                context
            )
            
            return html_content
            
        except Exception as e:
            raise Exception(f"Erreur lors de la génération du document: {str(e)}")
    
    def _prepare_paiement_context(self, document_type, paiement_id):
        """Prépare le contexte pour un document de paiement."""
        paiement = Paiement.objects.select_related(
            'contrat__locataire',
            'contrat__propriete__type_bien',
            'contrat__propriete__bailleur'
        ).get(id=paiement_id)
        
        # CORRECTION CRITIQUE : Récupérer l'avance correspondante pour les avances
        avance_loyer = None
        if document_type == 'paiement_avance' or paiement.type_paiement == 'avance':
            try:
                from .models_avance import AvanceLoyer
                avance_loyer = AvanceLoyer.objects.filter(
                    paiement=paiement,
                    statut='active'
                ).first()
            except Exception:
                pass
        
        # CORRECTION CRITIQUE : Calculer le bon montant selon le type de document
        montant_a_afficher = paiement.montant
        
        if document_type == 'paiement_avance' or paiement.type_paiement == 'avance':
            # Pour un récépissé d'avance, utiliser le montant de l'avance récupérée
            if avance_loyer:
                montant_a_afficher = float(avance_loyer.montant_avance)
            else:
                # Fallback : utiliser le montant de l'avance du contrat
                try:
                    montant_avance_contrat = float(paiement.contrat.avance_loyer) if paiement.contrat.avance_loyer else 0
                    if montant_avance_contrat > 0:
                        montant_a_afficher = montant_avance_contrat
                except (ValueError, TypeError, AttributeError):
                    pass
        
        # Calculer les mois couverts par l'avance (UNIQUEMENT pour les avances, PAS pour les cautions)
        mois_couverts = None
        if (document_type == 'paiement_avance' or paiement.type_paiement == 'avance') and montant_a_afficher and paiement.contrat.loyer_mensuel:
            try:
                # CORRECTION CRITIQUE : Utiliser l'avance récupérée si disponible
                if avance_loyer and hasattr(avance_loyer, 'get_mois_couverts_liste'):
                    # Utiliser les mois couverts calculés par l'avance
                    mois_liste = avance_loyer.get_mois_couverts_liste()
                    if mois_liste:
                        # Convertir les dates en noms de mois français
                        mois_noms = []
                        mois_francais = {
                            1: 'Janvier', 2: 'Février', 3: 'Mars', 4: 'Avril',
                            5: 'Mai', 6: 'Juin', 7: 'Juillet', 8: 'Août',
                            9: 'Septembre', 10: 'Octobre', 11: 'Novembre', 12: 'Décembre'
                        }
                        for mois_date in mois_liste:
                            mois_nom = mois_francais.get(mois_date.month, mois_date.strftime("%B"))
                            mois_noms.append(f"{mois_nom} {mois_date.year}")
                        
                        mois_couverts = {
                            'nombre': avance_loyer.nombre_mois_couverts,
                            'mois_liste': mois_noms,
                            'mois_texte': ', '.join(mois_noms)
                        }
                else:
                    # Fallback : calculer manuellement
                    montant_float = float(montant_a_afficher)
                    loyer_float = float(paiement.contrat.loyer_mensuel)
                    if montant_float > 0 and loyer_float > 0:
                        # Utiliser le montant correct pour le calcul
                        paiement_temp = paiement
                        paiement_temp.montant = montant_a_afficher
                        mois_couverts = self._calculer_mois_couverts_avance(paiement_temp)
            except (ValueError, TypeError, AttributeError):
                pass
        
        return {
            'document_number': paiement.numero_paiement or f"PAI-{paiement.id}",
            'type_paiement': paiement.get_type_paiement_display(),
            'mode_paiement': paiement.get_mode_paiement_display(),
            'date_paiement': paiement.date_paiement,
            'numero_cheque': paiement.numero_cheque,
            'reference_virement': paiement.reference_virement,
            'montant_total': montant_a_afficher,  # CORRECTION : Utiliser le bon montant
            'montant_lettres': self._convertir_en_lettres(montant_a_afficher),
            'montant_loyer': paiement.contrat.loyer_mensuel,
            'montant_charges_deduites': getattr(paiement, 'montant_charges_deduites', 0),
            'montant_net_paye': getattr(paiement, 'montant_net_paye', montant_a_afficher),
            'montant_net_lettres': self._convertir_en_lettres(getattr(paiement, 'montant_net_paye', montant_a_afficher)),
            'mois_couverts': mois_couverts,
            'mois_couverts_lettres': self._convertir_mois_couverts_en_lettres(mois_couverts) if mois_couverts else None,
            'locataire': paiement.contrat.locataire,
            'propriete': paiement.contrat.propriete,
            'bailleur': paiement.contrat.propriete.bailleur,
            'contrat': paiement.contrat,
            'paiement': paiement,
            'avance_loyer': avance_loyer,  # NOUVEAU : Ajouter l'avance au contexte
            'charges_deduites': getattr(paiement, 'charges_deduites', []),
        }
    
    def _prepare_retrait_context(self, retrait_id):
        """Prépare le contexte pour un document de retrait."""
        # Import ici pour éviter les imports circulaires
        from paiements.models import RetraitBailleur
        
        retrait = RetraitBailleur.objects.select_related(
            'bailleur'
        ).get(id=retrait_id)
        
        return {
            'document_number': f"RET-{retrait.id}",
            'type_paiement': retrait.get_type_retrait_display(),
            'mode_paiement': retrait.get_mode_retrait_display(),
            'date_paiement': retrait.mois_retrait,
            'montant_total': retrait.montant_net_a_payer,
            'montant_lettres': self._convertir_en_lettres(retrait.montant_net_a_payer),
            'montant_brut': retrait.montant_loyers_bruts,
            'charges_deduites': retrait.montant_charges_deductibles,
            'charges_bailleur': retrait.montant_charges_bailleur,
            'montant_net': retrait.montant_net_a_payer,
            'bailleur': retrait.bailleur,
            'contrat': None,  # Pas de contrat direct pour les retraits
            'locataire': None,  # Pas de locataire direct pour les retraits
            'propriete': None,  # Pas de propriété directe pour les retraits
            'retrait': retrait,
            'periode_retrait': retrait.mois_retrait.strftime('%B %Y'),
        }
    
    def _prepare_recap_context(self, recapitulatif_id):
        """Prépare le contexte pour un document de récapitulatif."""
        # Import ici pour éviter les imports circulaires
        from paiements.models import RecapitulatifMensuel
        
        recap = RecapitulatifMensuel.objects.select_related(
            'bailleur'
        ).get(id=recapitulatif_id)
        
        return {
            'document_number': recap.numero_recapitulatif,
            'type_paiement': 'Récapitulatif',
            'mode_paiement': 'Virement',
            'date_paiement': recap.date_generation,
            'montant_total': recap.montant_total,
            'montant_lettres': self._convertir_en_lettres(recap.montant_total),
            'bailleur': recap.bailleur,
            'recapitulatif': recap,
        }
    
    def _calculer_mois_couverts_avance(self, paiement):
        """Calcule le nombre de mois couverts par l'avance."""
        try:
            # Conversion sécurisée des valeurs
            montant_avance = float(paiement.montant) if paiement.montant else 0
            loyer_mensuel = float(paiement.contrat.loyer_mensuel) if paiement.contrat.loyer_mensuel else 0
            
            if loyer_mensuel <= 0 or montant_avance <= 0:
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
            
        except (ValueError, TypeError, ZeroDivisionError, ImportError, AttributeError):
            return None
    
    def _convertir_mois_couverts_en_lettres(self, mois_couverts):
        """Convertit le nombre de mois couverts en lettres."""
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
    
    def _convertir_en_lettres(self, montant):
        """Convertit un montant en lettres."""
        if not montant or montant == 0:
            return "Zéro"
        
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

