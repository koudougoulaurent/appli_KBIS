from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.urls import reverse
from decimal import Decimal
from datetime import date
from contrats.models import Contrat
from proprietes.managers import NonDeletedManager
from django.conf import settings
from proprietes.models import Bailleur, Propriete

# Les modèles de retraits sont définis dans models_retraits.py


class ChargeDeductible(models.Model):
    """Modèle pour les charges avancées par le locataire et déductibles du loyer."""
    
    # Informations de base
    contrat = models.ForeignKey(
        Contrat,
        on_delete=models.PROTECT,
        related_name='charges_deductibles',
        verbose_name=_("Contrat")
    )
    montant = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        verbose_name=_("Montant de la charge")
    )
    
    # Description de la charge
    libelle = models.CharField(
        max_length=200,
        verbose_name=_("Libellé de la charge")
    )
    description = models.TextField(
        blank=True,
        verbose_name=_("Description détaillée")
    )
    
    # Type de charge
    type_charge = models.CharField(
        max_length=30,
        choices=[
            ('reparation', 'Réparation'),
            ('travaux', 'Travaux'),
            ('entretien', 'Entretien'),
            ('urgence', 'Urgence'),
            ('fourniture', 'Fourniture'),
            ('service', 'Service'),
            ('autre', 'Autre'),
        ],
        default='reparation',
        verbose_name=_("Type de charge")
    )
    
    # Statut de la charge
    statut = models.CharField(
        max_length=20,
        choices=[
            ('en_attente', 'En attente de validation'),
            ('validee', 'Validée'),
            ('deduite', 'Déduite du loyer'),
            ('refusee', 'Refusée'),
            ('annulee', 'Annulée'),
        ],
        default='en_attente',
        verbose_name=_("Statut")
    )
    
    # Dates importantes
    date_charge = models.DateField(
        verbose_name=_("Date de la charge")
    )
    date_creation = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Date de création")
    )
    date_validation = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Date de validation")
    )
    date_deduction = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Date de déduction")
    )
    
    # Justificatifs
    justificatif_url = models.URLField(
        blank=True,
        verbose_name=_("URL du justificatif")
    )
    facture_numero = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Numéro de facture")
    )
    fournisseur = models.CharField(
        max_length=150,
        blank=True,
        verbose_name=_("Fournisseur")
    )
    
    # Métadonnées
    date_modification = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Date de modification")
    )
    cree_par = models.ForeignKey(
        'utilisateurs.Utilisateur',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='charges_crees',
        verbose_name=_("Créé par")
    )
    valide_par = models.ForeignKey(
        'utilisateurs.Utilisateur',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='charges_validees',
        verbose_name=_("Validée par")
    )
    
    # Gestion de la suppression logique
    is_deleted = models.BooleanField(
        default=False,
        verbose_name='Supprimé logiquement'
    )
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Date de suppression'
    )
    deleted_by = models.ForeignKey(
        'utilisateurs.Utilisateur',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='charges_deleted',
        verbose_name='Supprimé par'
    )
    
    objects = NonDeletedManager()
    all_objects = models.Manager()
    
    class Meta:
        verbose_name = _("Charge déductible")
        verbose_name_plural = _("Charges déductibles")
        ordering = ['-date_charge']
    
    def __str__(self):
        try:
            contrat_num = self.contrat.numero_contrat if self.contrat else f"Contrat ID {self.contrat_id}"
        except:
            contrat_num = f"Contrat ID {self.contrat_id}"
        return f"{self.libelle} - {contrat_num} - {self.montant} F CFA"
    
    def get_montant_formatted(self):
        """Retourne le montant formaté avec la devise."""
        return f"{self.montant} F CFA"
    
    def get_statut_display_color(self):
        """Retourne la couleur CSS pour le statut."""
        colors = {
            'en_attente': 'warning',
            'validee': 'success',
            'deduite': 'info',
            'refusee': 'danger',
            'annulee': 'secondary',
        }
        return colors.get(self.statut, 'secondary')
    
    def peut_etre_validee(self):
        """Vérifie si la charge peut être validée."""
        return self.statut == 'en_attente'
    
    def peut_etre_deduite(self):
        """Vérifie si la charge peut être déduite du loyer."""
        return self.statut == 'validee'
    
    def valider_charge(self, utilisateur):
        """Valide la charge."""
        if self.peut_etre_validee():
            self.statut = 'validee'
            self.date_validation = timezone.now()
            self.valide_par = utilisateur
            self.save()
            return True
        return False
    
    def deduire_du_loyer(self, utilisateur):
        """Marque la charge comme déduite du loyer."""
        if self.peut_etre_deduite():
            self.statut = 'deduite'
            self.date_deduction = timezone.now()
            self.save()
            return True
        return False


class Paiement(models.Model):
    """Modèle pour les paiements de loyer avec support des paiements partiels."""
    
    # Numéro unique professionnel
    numero_paiement = models.CharField(
        max_length=50,
        unique=True,
        null=True,
        blank=True,
        verbose_name=_("Numéro Paiement"),
        help_text=_("Numéro unique professionnel du paiement")
    )
    
    # Identifiant unique
    reference_paiement = models.CharField(
        max_length=30,
        unique=True,
        null=True,
        blank=True,
        verbose_name=_("Référence Paiement"),
        help_text=_("Référence unique pour identifier le paiement")
    )
    
    # Informations de base
    contrat = models.ForeignKey(
        Contrat,
        on_delete=models.PROTECT,
        related_name='paiements',
        verbose_name=_("Contrat")
    )
    montant = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        verbose_name=_("Montant")
    )
    
    # Informations sur les charges déductibles
    montant_charges_deduites = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_("Montant des charges déduites")
    )
    montant_net_paye = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Montant net payé (après déductions)")
    )
    
    # Gestion des paiements partiels
    est_paiement_partiel = models.BooleanField(
        default=False,
        verbose_name=_("Paiement partiel")
    )
    mois_paye = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name=_("Mois payé"),
        help_text=_("Mois pour lequel ce paiement est effectué (ex: octobre 2025)")
    )
    montant_du_mois = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Montant dû pour le mois"),
        help_text=_("Montant total dû pour le mois (loyer + charges)")
    )
    montant_restant_du = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_("Montant restant dû"),
        help_text=_("Montant restant à payer pour ce mois")
    )
    
    # Type et statut
    type_paiement = models.CharField(
        max_length=20,
        choices=[
            ('loyer', 'Loyer'),
            ('charges', 'Charges'),
            ('caution', 'Caution'),
            ('avance_loyer', 'Avance de loyer'),
            ('depot_garantie', 'Dépôt de garantie'),
            ('regularisation', 'Régularisation'),
            ('paiement_partiel', 'Paiement partiel'),
            ('autre', 'Autre'),
        ],
        default='loyer',
        verbose_name=_("Type de paiement")
    )
    statut = models.CharField(
        max_length=20,
        choices=[
            ('en_attente', 'En attente'),
            ('partiellement_payé', 'Partiellement payé'),
            ('valide', 'Validé'),
            ('refuse', 'Refusé'),
            ('annule', 'Annulé'),
        ],
        default='en_attente',
        verbose_name=_("Statut")
    )
    
    # Mode de paiement
    mode_paiement = models.CharField(
        max_length=20,
        choices=[
            ('virement', 'Virement bancaire'),
            ('cheque', 'Chèque'),
            ('especes', 'Espèces'),
            ('prelevement', 'Prélèvement automatique'),
            ('carte', 'Carte bancaire'),
        ],
        verbose_name=_("Mode de paiement")
    )
    
    # Dates
    date_paiement = models.DateField(verbose_name=_("Date de paiement"))
    date_encaissement = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Date d'encaissement")
    )
    
    # Informations bancaires
    numero_cheque = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_("Numéro de chèque")
    )
    reference_virement = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Référence virement")
    )
    
    # Métadonnées
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name=_("Date de création"))
    date_modification = models.DateTimeField(auto_now=True, verbose_name=_("Date de modification"))
    notes = models.TextField(blank=True, verbose_name=_("Notes"))
    
    # Libellé du paiement
    libelle = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_("Libellé du paiement"),
        help_text=_("Description ou motif du paiement")
    )
    
    # Relations
    cree_par = models.ForeignKey(
        'utilisateurs.Utilisateur',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='paiements_crees',
        verbose_name=_("Créé par")
    )
    valide_par = models.ForeignKey(
        'utilisateurs.Utilisateur',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='paiements_valides',
        verbose_name=_("Validé par")
    )
    date_validation = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Date de validation")
    )
    
    # Champs pour le refus
    refuse_par = models.ForeignKey(
        'utilisateurs.Utilisateur',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='paiements_refuses',
        verbose_name=_("Refusé par")
    )
    date_refus = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Date de refus")
    )
    raison_refus = models.TextField(
        blank=True,
        verbose_name=_("Raison du refus")
    )
    
    # Champs pour l'annulation
    annule_par = models.ForeignKey(
        'utilisateurs.Utilisateur',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='paiements_annules',
        verbose_name=_("Annulé par")
    )
    date_annulation = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Date d'annulation")
    )
    raison_annulation = models.TextField(
        blank=True,
        verbose_name=_("Raison de l'annulation")
    )
    
    is_deleted = models.BooleanField(default=False, verbose_name='Supprimé logiquement')
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name='Date de suppression')
    deleted_by = models.ForeignKey('utilisateurs.Utilisateur', null=True, blank=True, on_delete=models.SET_NULL, related_name='paiement_deleted', verbose_name='Supprimé par')
    
    objects = NonDeletedManager()
    all_objects = models.Manager()
    
    class Meta:
        verbose_name = _("Paiement")
        verbose_name_plural = _("Paiements")
        ordering = ['-date_paiement', '-date_creation']
    
    def __str__(self):
        try:
            contrat_num = self.contrat.numero_contrat if self.contrat else f"Contrat ID {self.contrat_id}"
        except:
            contrat_num = f"Contrat ID {self.contrat_id}"
        return f"Paiement {self.reference_paiement} - {contrat_num} - {self.montant} F CFA"
    
    def save(self, *args, **kwargs):
        if not self.reference_paiement:
            self.reference_paiement = self.generate_reference_paiement()

        # Calculer automatiquement le montant net payé
        if self.montant_net_paye is None:
            self.montant_net_paye = self.montant - self.montant_charges_deduites

        # Logique paiement partiel : cumul des paiements pour le contrat et le mois
        if self.contrat and self.mois_paye:
            paiements = Paiement.objects.filter(
                contrat=self.contrat,
                mois_paye=self.mois_paye,
                is_deleted=False
            )
            total_paye = sum([p.montant for p in paiements if p.pk != self.pk]) + self.montant
            # Convertir le loyer_mensuel (CharField) en Decimal
            try:
                loyer_mensuel_decimal = Decimal(self.contrat.loyer_mensuel) if self.contrat.loyer_mensuel else Decimal('0')
                montant_du_mois = self.montant_du_mois or loyer_mensuel_decimal
            except (ValueError, TypeError):
                montant_du_mois = self.montant_du_mois or Decimal('0')
            self.montant_restant_du = max(Decimal(montant_du_mois) - Decimal(total_paye), 0)
            if total_paye < Decimal(montant_du_mois):
                self.statut = 'partiellement_payé'
                self.est_paiement_partiel = True
            elif total_paye >= Decimal(montant_du_mois):
                self.statut = 'valide'
                self.est_paiement_partiel = False
            # Optionnel : empêcher la saisie de plus que le montant dû
            if total_paye > Decimal(montant_du_mois):
                raise ValueError("Le total des paiements dépasse le montant dû pour ce mois.")

        super().save(*args, **kwargs)
    
    def generate_reference_paiement(self):
        """Génère une référence unique pour le paiement."""
        from django.utils.crypto import get_random_string
        prefix = "PAY"
        while True:
            code = f"{prefix}-{get_random_string(8, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')}"
            if not Paiement.objects.filter(reference_paiement=code).exists():
                return code
    
    def get_locataire(self):
        """Retourne le locataire associé à ce paiement."""
        try:
            return self.contrat.locataire
        except:
            return None
    
    def get_bailleur(self):
        """Retourne le bailleur associé à ce paiement."""
        try:
            return self.contrat.propriete.bailleur
        except:
            return None
    
    def get_propriete(self):
        """Retourne la propriété associée à ce paiement."""
        try:
            return self.contrat.propriete
        except:
            return None
    
    def get_code_locataire(self):
        """Retourne le code unique du locataire."""
        return self.get_locataire().code_locataire
    
    def get_code_bailleur(self):
        """Retourne le code unique du bailleur."""
        return self.get_bailleur().code_bailleur
    
    def get_nom_complet_locataire(self):
        """Retourne le nom complet du locataire."""
        return self.get_locataire().get_nom_complet()
    
    def get_nom_complet_bailleur(self):
        """Retourne le nom complet du bailleur."""
        return self.get_bailleur().get_nom_complet()
    
    def get_adresse_propriete(self):
        """Retourne l'adresse de la propriété."""
        return self.get_propriete().adresse
    
    def get_ville_propriete(self):
        """Retourne la ville de la propriété."""
        return self.get_propriete().ville
    
    def get_montant_formatted(self):
        """Retourne le montant formaté avec la devise."""
        return f"{self.montant} F CFA"
    
    def get_montant_net_formatted(self):
        """Retourne le montant net formaté avec la devise."""
        return f"{self.montant_net_paye} F CFA"
    
    def get_montant_charges_formatted(self):
        """Retourne le montant des charges formaté avec la devise."""
        return f"{self.montant_charges_deduites} F CFA"
    
    def get_statut_display_color(self):
        """Retourne la couleur CSS pour le statut."""
        colors = {
            'en_attente': 'warning',
            'valide': 'success',
            'refuse': 'danger',
            'annule': 'secondary',
        }
        return colors.get(self.statut, 'secondary')
    
    def get_type_display_icon(self):
        """Retourne l'icône Bootstrap pour le type de paiement."""
        icons = {
            'loyer': 'bi-house',
            'charges': 'bi-lightning',
            'caution': 'bi-shield',
            'avance_loyer': 'bi-piggy-bank',
            'depot_garantie': 'bi-shield-check',
            'regularisation': 'bi-arrow-repeat',
            'paiement_partiel': 'bi-currency-exchange',
            'autre': 'bi-coin',
        }
        return icons.get(self.type_paiement, 'bi-coin')
    
    def get_mode_display_icon(self):
        """Retourne l'icône Bootstrap pour le mode de paiement."""
        icons = {
            'virement': 'bi-bank',
            'cheque': 'bi-receipt',
            'especes': 'bi-cash',
            'prelevement': 'bi-arrow-repeat',
            'carte': 'bi-credit-card',
        }
        return icons.get(self.mode_paiement, 'bi-coin')
    
    def peut_etre_valide(self):
        """Vérifie si le paiement peut être validé."""
        return self.statut == 'en_attente'
    
    def peut_generer_quittance(self):
        """Vérifie si le paiement peut générer une quittance."""
        # Un paiement peut générer une quittance s'il est validé
        # et qu'il n'est pas un paiement partiel
        return self.statut == 'valide' and not self.est_paiement_partiel
    
    def valider_paiement(self, utilisateur):
        """Valide le paiement et génère automatiquement une quittance et un reçu."""
        if self.peut_etre_valide():
            self.statut = 'valide'
            self.date_encaissement = timezone.now().date()
            self.valide_par = utilisateur
            self.save()
            
            # Générer automatiquement une quittance de paiement
            self.generer_quittance(utilisateur)
            
            # Générer automatiquement un reçu de paiement
            self.generer_recu_automatique(utilisateur)
            
            return True
        return False
    
    def generer_quittance(self, utilisateur):
        """Génère automatiquement une quittance de paiement avec nouveau système KBIS."""
        from .models import QuittancePaiement
        
        # Vérifier si une quittance existe déjà
        if not hasattr(self, 'quittance'):
            quittance = QuittancePaiement.objects.create(
                paiement=self,
                cree_par=utilisateur
            )
            # Générer le document KBIS dynamique
            quittance.contenu_html = self.generer_document_kbis('quittance')
            quittance.save()
            return quittance
        return self.quittance
    
    def generer_quittance_kbis_dynamique(self):
        """Génère une quittance KBIS dynamique avec le format correct."""
        import sys
        import os
        from datetime import datetime
        
        try:
            # Utiliser le système unifié
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from document_kbis_unifie import DocumentKBISUnifie
            
            # Déterminer le type de quittance selon le type de paiement
            type_quittance = self._determiner_type_quittance_paiement()
            
            # Récupérer les informations de base de manière sécurisée
            try:
                code_location = self.contrat.numero_contrat if self.contrat and self.contrat.numero_contrat else 'N/A'
            except:
                code_location = 'N/A'
                
            try:
                recu_de = self.contrat.locataire.get_nom_complet() if self.contrat and self.contrat.locataire else 'LOCATAIRE'
            except:
                recu_de = 'LOCATAIRE'
                
            try:
                quartier = self.contrat.propriete.adresse if self.contrat and self.contrat.propriete else 'Non spécifié'
            except:
                quartier = 'Non spécifié'
            
            # Générer un numéro de quittance unique au format KBIS
            numero_quittance = f"QUI-{datetime.now().strftime('%Y%m%d%H%M%S')}-{self.id if self.id else 'X1DZ'}"
            
            # Données de la quittance
            donnees_quittance = {
                'numero': numero_quittance,
                'date': self.date_paiement.strftime('%d-%b-%y') if self.date_paiement else datetime.now().strftime('%d-%b-%y'),
                'code_location': code_location,
                'recu_de': recu_de,
                'montant': int(self.montant) if self.montant else 0,
                'loyer_base': int(self.montant) if self.montant else 0,
                'mois_regle': self.mois_paye if self.mois_paye else datetime.now().strftime('%B %Y'),
                'restant_du': 0,
                'loyer_au_prorata': 0,
                'quartier': quartier,
                'timestamp': datetime.now().isoformat(),
                'type_document': type_quittance,
                'type_paiement': self.get_type_paiement_display() if hasattr(self, 'get_type_paiement_display') else 'Paiement',
                'mode_paiement': self.get_mode_paiement_display() if hasattr(self, 'get_mode_paiement_display') else 'Espèces'
            }
            
            # Ajouter des données spécialisées selon le type
            try:
                donnees_quittance.update(self._ajouter_donnees_specialisees_quittance(type_quittance))
            except:
                pass  # Ignorer les erreurs de données spécialisées
            
            return DocumentKBISUnifie.generer_document_unifie(donnees_quittance, type_quittance)
            
        except Exception as e:
            print(f"Erreur lors de la génération de la quittance KBIS: {e}")
            import traceback
            print(f"Détails: {traceback.format_exc()}")
            return None
    
    def generer_recu_automatique(self, utilisateur):
        """Génère automatiquement un reçu de paiement avec template KBIS."""
        try:
            # Vérifier si un reçu existe déjà
            if not hasattr(self, 'recu') or not self.recu:
                from .models import Recu
                import uuid
                
                # Générer un numéro de reçu unique
                numero_recu = f"RECU-{self.reference_paiement}-{uuid.uuid4().hex[:8].upper()}"
                
                Recu.objects.create(
                    paiement=self,
                    numero_recu=numero_recu,
                    template_utilise='kbis_standard',
                    format_impression='A4',
                    valide=True,
                    genere_automatiquement=True
                )
                return True
        except Exception as e:
            print(f"Erreur lors de la génération du reçu: {e}")
            return False
    
    def generer_document_kbis(self, type_document='recu'):
        """Génère un document avec le nouveau système KBIS IMMOBILIER dynamique."""
        try:
            # Utiliser le système unifié
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from document_kbis_unifie import DocumentKBISUnifie
            
            if type_document == 'recu':
                return self._generer_recu_kbis_dynamique()
            elif type_document == 'quittance':
                return self._generer_recu_kbis_dynamique()
            elif type_document == 'facture':
                return self._generer_facture_kbis_dynamique()
            else:
                return None
        except Exception as e:
            print(f"Erreur lors de la génération du document KBIS: {e}")
            return None
    
    def _generer_recu_kbis_dynamique(self):
        """Génère un récépissé avec le système unifié KBIS IMMOBILIER."""
        import sys
        import os
        from datetime import datetime
        
        try:
            # Utiliser le système unifié
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from document_kbis_unifie import DocumentKBISUnifie
            
            # Déterminer le type de récépissé selon le type de paiement
            type_recu = self._determiner_type_recu()
            
            # Récupérer les informations de base de manière sécurisée
            try:
                code_location = self.contrat.numero_contrat if self.contrat and self.contrat.numero_contrat else 'N/A'
            except:
                code_location = 'N/A'
                
            try:
                recu_de = self.contrat.locataire.get_nom_complet() if self.contrat and self.contrat.locataire else 'LOCATAIRE'
            except:
                recu_de = 'LOCATAIRE'
                
            try:
                quartier = self.contrat.propriete.adresse if self.contrat and self.contrat.propriete else 'Non spécifié'
            except:
                quartier = 'Non spécifié'
            
            # Données du récépissé
            donnees_recu = {
                'numero': f"REC-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                'date': self.date_paiement.strftime('%d-%b-%y') if self.date_paiement else datetime.now().strftime('%d-%b-%y'),
                'code_location': code_location,
                'recu_de': recu_de,
                'montant': int(self.montant) if self.montant else 0,
                'loyer_base': int(self.montant) if self.montant else 0,
                'mois_regle': self.mois_paye if self.mois_paye else datetime.now().strftime('%B %Y'),
                'restant_du': 0,
                'loyer_au_prorata': 0,
                'quartier': quartier,
                'timestamp': datetime.now().isoformat(),
                'type_document': type_recu,
                'type_paiement': self.get_type_paiement_display() if hasattr(self, 'get_type_paiement_display') else 'Paiement',
                'mode_paiement': self.get_mode_paiement_display() if hasattr(self, 'get_mode_paiement_display') else 'Espèces'
            }
            
            # Ajouter des données spécialisées selon le type
            try:
                donnees_recu.update(self._ajouter_donnees_specialisees_recu(type_recu))
            except:
                pass  # Ignorer les erreurs de données spécialisées
            
            return DocumentKBISUnifie.generer_document_unifie(donnees_recu, type_recu)
            
        except Exception as e:
            print(f"Erreur lors de la génération du récépissé KBIS: {e}")
            import traceback
            print(f"Détails: {traceback.format_exc()}")
            return None
    
    def _determiner_type_recu(self):
        """Détermine le type de récépissé selon le type de paiement"""
        # Mapping précis des types de paiement vers les types de récépissés
        type_mapping = {
            'loyer': 'recu_loyer',
            'charges': 'recu_charges', 
            'caution': 'recu_caution',
            'avance_loyer': 'recu_avance',
            'depot_garantie': 'recu_caution',
            'regularisation': 'recu_regularisation',
            'paiement_partiel': 'recu_partiel',
            'autre': 'recu_autre'
        }
        
        return type_mapping.get(self.type_paiement, 'recu')
    
    def _ajouter_donnees_specialisees_recu(self, type_recu):
        """Ajoute des données spécialisées selon le type de récépissé"""
        donnees_specialisees = {}
        
        # Données spécialisées selon le type de récépissé
        if type_recu in ['recu_caution', 'recu_caution_avance'] and self.contrat:
            # Calculer les montants pour caution et avance
            loyer_mensuel = float(self.contrat.loyer_mensuel) if self.contrat.loyer_mensuel else 0
            charges_mensuelles = float(self.contrat.charges_mensuelles) if self.contrat.charges_mensuelles else 0
            
            donnees_specialisees.update({
                'loyer_mensuel': int(loyer_mensuel),
                'charges_mensuelles': int(charges_mensuelles),
                'depot_garantie': int(loyer_mensuel * 2),  # 2 mois de loyer
                'avance_loyer': int(loyer_mensuel),  # 1 mois de loyer
                'montant_total': int(loyer_mensuel * 3)  # 3 mois au total
            })
            
        elif type_recu == 'recu_loyer' and self.contrat:
            # Données spécifiques au loyer
            loyer_mensuel = float(self.contrat.loyer_mensuel) if self.contrat.loyer_mensuel else 0
            charges_mensuelles = float(self.contrat.charges_mensuelles) if self.contrat.charges_mensuelles else 0
            
            donnees_specialisees.update({
                'loyer_mensuel': int(loyer_mensuel),
                'charges_mensuelles': int(charges_mensuelles),
                'total_mensuel': int(loyer_mensuel + charges_mensuelles)
            })
            
        elif type_recu == 'recu_charges' and self.contrat:
            # Données spécifiques aux charges
            charges_mensuelles = float(self.contrat.charges_mensuelles) if self.contrat.charges_mensuelles else 0
            
            donnees_specialisees.update({
                'charges_mensuelles': int(charges_mensuelles),
                'type_charges': 'Charges mensuelles'
            })
            
        elif type_recu == 'recu_avance' and self.contrat:
            # Données spécifiques à l'avance de loyer
            loyer_mensuel = float(self.contrat.loyer_mensuel) if self.contrat.loyer_mensuel else 0
            
            donnees_specialisees.update({
                'loyer_mensuel': int(loyer_mensuel),
                'type_avance': 'Avance de loyer'
            })
            
        elif type_recu == 'recu_partiel':
            # Données spécifiques au paiement partiel
            donnees_specialisees.update({
                'type_paiement': 'Paiement partiel',
                'note_speciale': 'Ce paiement ne couvre qu\'une partie du montant dû'
            })
            
        elif type_recu == 'recu_regularisation':
            # Données spécifiques à la régularisation
            donnees_specialisees.update({
                'type_paiement': 'Régularisation',
                'note_speciale': 'Paiement de régularisation'
            })
        
        return donnees_specialisees
    
    def _ajouter_donnees_specialisees_quittance(self, type_quittance):
        """Ajoute des données spécialisées selon le type de quittance"""
        donnees_specialisees = {}
        
        # Données spécialisées selon le type de quittance
        if type_quittance in ['quittance_caution', 'quittance_caution_avance'] and self.contrat:
            # Calculer les montants pour caution et avance
            loyer_mensuel = float(self.contrat.loyer_mensuel) if self.contrat.loyer_mensuel else 0
            charges_mensuelles = float(self.contrat.charges_mensuelles) if self.contrat.charges_mensuelles else 0
            
            donnees_specialisees.update({
                'loyer_mensuel': int(loyer_mensuel),
                'charges_mensuelles': int(charges_mensuelles),
                'depot_garantie': int(loyer_mensuel * 2),  # 2 mois de loyer
                'avance_loyer': int(loyer_mensuel),  # 1 mois de loyer
                'montant_total': int(loyer_mensuel * 3),  # 3 mois au total
                'note': 'Dépôt de garantie - Remboursable en fin de bail'
            })
            
        elif type_quittance == 'quittance_loyer' and self.contrat:
            # Données spécifiques au loyer
            loyer_mensuel = float(self.contrat.loyer_mensuel) if self.contrat.loyer_mensuel else 0
            charges_mensuelles = float(self.contrat.charges_mensuelles) if self.contrat.charges_mensuelles else 0
            
            donnees_specialisees.update({
                'loyer_mensuel': int(loyer_mensuel),
                'charges_mensuelles': int(charges_mensuelles),
                'total_mensuel': int(loyer_mensuel + charges_mensuelles),
                'note': 'Loyer mensuel'
            })
            
        elif type_quittance == 'quittance_charges' and self.contrat:
            # Données spécifiques aux charges
            charges_mensuelles = float(self.contrat.charges_mensuelles) if self.contrat.charges_mensuelles else 0
            
            donnees_specialisees.update({
                'charges_mensuelles': int(charges_mensuelles),
                'type_charges': 'Charges mensuelles',
                'note': 'Charges mensuelles'
            })
            
        elif type_quittance == 'quittance_avance' and self.contrat:
            # Données spécifiques à l'avance de loyer
            loyer_mensuel = float(self.contrat.loyer_mensuel) if self.contrat.loyer_mensuel else 0
            
            donnees_specialisees.update({
                'loyer_mensuel': int(loyer_mensuel),
                'type_avance': 'Avance de loyer',
                'note': 'Avance de loyer'
            })
            
        elif type_quittance == 'quittance_partiel':
            # Données spécifiques au paiement partiel
            donnees_specialisees.update({
                'type_paiement': 'Paiement partiel',
                'note': 'Paiement partiel'
            })
            
        else:
            # Quittance standard
            donnees_specialisees.update({
                'note': 'Paiement'
            })
            
        return donnees_specialisees
    
    def _generer_quittance_retrait_kbis(self):
        """Génère une quittance de retrait avec le système unifié KBIS IMMOBILIER."""
        import sys
        import os
        from datetime import datetime
        
        try:
            # Utiliser le système unifié
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from document_kbis_unifie import DocumentKBISUnifie
            
            # Déterminer le type de quittance selon le type de retrait
            type_quittance = self._determiner_type_quittance_retrait()
            
            # Données de la quittance de retrait
            donnees_quittance = {
                'numero': f"QUI-RET-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                'date': self.date_versement.strftime('%d-%b-%y') if self.date_versement else datetime.now().strftime('%d-%b-%y'),
                'code_location': f"RET-{self.bailleur.nom.upper()[:3]}-{self.mois_retrait.strftime('%Y%m')}",
                'recu_de': f"{self.bailleur.get_nom_complet()}",
                'montant': int(self.montant_net_a_payer),
                'loyer_base': int(self.montant_loyers_bruts),
                'mois_regle': self.mois_retrait.strftime('%B %Y'),
                'restant_du': 0,
                'loyer_au_prorata': 0,
                'quartier': f"Retrait {self.get_type_retrait_display().lower()}",
                'timestamp': datetime.now().isoformat(),
                'type_document': type_quittance,
                'type_retrait': self.get_type_retrait_display(),
                'mode_retrait': self.get_mode_retrait_display(),
                'montant_brut': int(self.montant_loyers_bruts),
                'charges_deduites': int(self.montant_charges_deductibles),
                'montant_net': int(self.montant_net_a_payer)
            }
            
            return DocumentKBISUnifie.generer_document_unifie(donnees_quittance, type_quittance)
            
        except Exception as e:
            print(f"Erreur lors de la génération de la quittance de retrait KBIS: {e}")
            return None
    
    def _determiner_type_quittance_retrait(self):
        """Détermine le type de quittance selon le type de retrait"""
        if self.type_retrait == 'mensuel':
            return 'quittance_retrait_mensuel'
        elif self.type_retrait == 'trimestriel':
            return 'quittance_retrait_trimestriel'
        elif self.type_retrait == 'annuel':
            return 'quittance_retrait_annuel'
        elif self.type_retrait == 'exceptionnel':
            return 'quittance_retrait_exceptionnel'
        else:
            return 'quittance_retrait'
    
    def generer_quittance_kbis_dynamique(self):
        """Génère une quittance avec le nouveau système KBIS IMMOBILIER dynamique - MÊME FORMAT QUE RÉCÉPISSÉ."""
        # Utiliser exactement la même méthode que les récépissés pour avoir le même format
        return self._generer_recu_kbis_dynamique()
    
    def _determiner_type_quittance_paiement(self):
        """Détermine le type de quittance selon le type de paiement"""
        if self.type_paiement == 'loyer':
            return 'quittance_loyer'
        elif self.type_paiement == 'avance':
            return 'quittance_avance'
        elif self.type_paiement == 'caution':
            return 'quittance_caution'
        elif self.type_paiement == 'caution_avance':
            return 'quittance_caution_avance'
        elif self.type_paiement == 'charges':
            return 'quittance_charges'
        elif self.type_paiement == 'frais_agence':
            return 'quittance_frais_agence'
        else:
            return 'quittance'
    
    def _generer_code_unique(self):
        """Génère un code unique pour la quittance"""
        from django.utils.crypto import get_random_string
        return get_random_string(4, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
    
    def _generer_facture_kbis_dynamique(self):
        """Génère une facture avec le système unifié KBIS IMMOBILIER."""
        import sys
        import os
        from datetime import datetime, timedelta
        
        try:
            # Utiliser le système unifié
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from document_kbis_unifie import DocumentKBISUnifie
            
            # Données de facture (à échoir)
            mois_suivant = datetime.now() + timedelta(days=30)
            
            donnees_facture = {
                'numero': f"FACT-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                'date': datetime.now().strftime('%d-%b-%y'),
                'code_location': f"{self.contrat.numero_contrat if self.contrat and self.contrat.numero_contrat else 'N/A'}",
                'recu_de': f"{self.contrat.locataire.get_nom_complet() if self.contrat and self.contrat.locataire else 'LOCATAIRE'}",
                'montant': int(float(self.contrat.loyer_mensuel) if self.contrat and self.contrat.loyer_mensuel else self.montant),
                'loyer_base': int(float(self.contrat.loyer_mensuel) if self.contrat and self.contrat.loyer_mensuel else self.montant),
                'mois_regle': mois_suivant.strftime('%B %Y'),
                'restant_du': 0,
                'loyer_au_prorata': 0,
                'quartier': f"{self.contrat.propriete.adresse}" if self.contrat and self.contrat.propriete else 'Non spécifié',
                'timestamp': datetime.now().isoformat(),
                'type_document': 'facture'
            }
            
            return DocumentKBISUnifie.generer_document_unifie(donnees_facture, 'facture')
            
        except Exception as e:
            print(f"Erreur lors de la génération de la facture KBIS: {e}")
            return None
    
    def _generer_facture_kbis_old(self):
        """Génère une facture avec template KBIS (ancienne version)."""
        from core.utils import KBISDocumentTemplate
        
        contenu = f"""
        <div style="margin: 20px 0;">
            <h3 style="color: #2c5aa0; border-bottom: 2px solid #2c5aa0; padding-bottom: 10px;">
                FACTURE DE LOYER
            </h3>
            <table style="width: 100%; background: #f8f9fa; border-radius: 8px;">
                <tr>
                    <th style="background: #2c5aa0; color: white;">Description</th>
                    <th style="background: #2c5aa0; color: white;">Montant</th>
                </tr>
                <tr>
                    <td>Loyer mensuel - {self.mois_paye.strftime('%B %Y') if self.mois_paye else 'N/A'}</td>
                    <td class="montant">{self.get_montant_formatted()}</td>
                </tr>
                <tr>
                    <td><strong>TOTAL À PAYER</strong></td>
                    <td class="montant"><strong>{self.get_montant_formatted()}</strong></td>
                </tr>
            </table>
        </div>
        
        <div style="margin: 20px 0; padding: 15px; background: #fff3cd; border-radius: 8px;">
            <h4 style="color: #856404; margin-top: 0;">INFORMATIONS DE PAIEMENT</h4>
            <p><strong>Échéance:</strong> {self.date_paiement.strftime('%d/%m/%Y')}</p>
            <p><strong>Référence:</strong> {self.reference_paiement}</p>
            <p><strong>Locataire:</strong> {self.get_nom_complet_locataire()}</p>
            <p><strong>Propriété:</strong> {self.get_adresse_propriete()}</p>
        </div>
        """
        
        titre = f"FACTURE N° {self.reference_paiement}"
        return KBISDocumentTemplate.get_document_complet(titre, contenu, "Facture")
    
    def peut_etre_annule(self):
        """Vérifie si le paiement peut être annulé."""
        return self.statut in ['en_attente', 'valide']
    
    def annuler_paiement(self, utilisateur, raison=""):
        """Annule le paiement."""
        if self.peut_etre_annule():
            self.statut = 'annule'
            self.notes = f"Annulé par {utilisateur.get_full_name()}. Raison: {raison}"
            self.save()
            return True
        return False
    
    def get_type_paiement_display(self):
        """Retourne le type de paiement avec une description complète."""
        if self.type_paiement == 'caution':
            return f"Caution - {self.get_montant_formatted()}"
        elif self.type_paiement == 'avance_loyer':
            return f"Avance de loyer - {self.get_montant_formatted()}"
        elif self.type_paiement == 'depot_garantie':
            return f"Dépôt de garantie - {self.get_montant_formatted()}"
        else:
            # Pour les autres types, utiliser le nom du type directement
            # ou retourner une description par défaut
            type_names = {
                'loyer': 'Loyer',
                'charges': 'Charges',
                'autres': 'Autres',
            }
            return type_names.get(self.type_paiement, self.type_paiement)
    
    def clean(self):
        """Validation personnalisée pour empêcher les doublons de paiement."""
        from django.core.exceptions import ValidationError
        from django.utils import timezone
        
        super().clean()
        
        # Vérifier les doublons seulement si c'est un nouveau paiement ou si le contrat/mois a changé
        if self.pk is None or hasattr(self, '_original_contrat') or hasattr(self, '_original_mois_paye'):
            # Utiliser contrat_id au lieu de self.contrat pour éviter l'erreur RelatedObjectDoesNotExist
            contrat_id = getattr(self, 'contrat_id', None)
            if contrat_id and self.mois_paye:
                # Vérifier s'il existe déjà un paiement pour ce contrat dans le même mois
                # mois_paye est un CharField, on compare directement les strings
                existing_payment = Paiement.objects.filter(
                    contrat_id=contrat_id,
                    mois_paye=self.mois_paye,
                    is_deleted=False
                ).exclude(pk=self.pk)
                
                if existing_payment.exists():
                    existing = existing_payment.first()
                    raise ValidationError({
                        'mois_paye': f"Un paiement existe déjà pour ce contrat au mois de {self.mois_paye}. "
                                    f"Paiement existant: {existing.reference_paiement} du {existing.date_paiement.strftime('%d/%m/%Y')} "
                                    f"pour un montant de {existing.montant} F CFA."
                    })
    
    def save(self, *args, **kwargs):
        """Override save pour stocker les valeurs originales et valider."""
        # Stocker les valeurs originales pour la validation
        if self.pk:
            try:
                original = Paiement.objects.get(pk=self.pk)
                self._original_contrat = original.contrat
                self._original_mois_paye = original.mois_paye
            except Paiement.DoesNotExist:
                pass
        
        # Valider avant de sauvegarder
        self.clean()
        super().save(*args, **kwargs)


class QuittancePaiement(models.Model):
    def get_unite_locative(self):
        """Retourne l'unité locative associée à cette quittance (via le contrat du paiement)."""
        contrat = getattr(self.paiement, 'contrat', None)
        if contrat and hasattr(contrat, 'unite_locative'):
            return contrat.unite_locative
        return None
    """Modèle pour les quittances de paiement générées automatiquement."""
    
    # Numéro unique de la quittance
    numero_quittance = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_("Numéro de quittance"),
        help_text=_("Numéro unique de la quittance")
    )
    
    # Paiement associé
    paiement = models.OneToOneField(
        Paiement,
        on_delete=models.CASCADE,
        related_name='quittance',
        verbose_name=_("Paiement")
    )
    
    # Informations de la quittance
    date_emission = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Date d'émission")
    )
    date_impression = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Date d'impression")
    )
    
    # Statut de la quittance
    statut = models.CharField(
        max_length=20,
        choices=[
            ('generee', 'Générée'),
            ('imprimee', 'Imprimée'),
            ('envoyee', 'Envoyée'),
            ('archivée', 'Archivée'),
        ],
        default='generee',
        verbose_name=_("Statut")
    )
    
    # Métadonnées
    cree_par = models.ForeignKey(
        'utilisateurs.Utilisateur',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='quittances_crees',
        verbose_name=_("Créé par")
    )
    
    # Gestion de la suppression logique
    is_deleted = models.BooleanField(
        default=False,
        verbose_name='Supprimé logiquement'
    )
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Date de suppression'
    )
    deleted_by = models.ForeignKey(
        'utilisateurs.Utilisateur',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='quittances_deleted',
        verbose_name='Supprimé par'
    )
    
    objects = NonDeletedManager()
    all_objects = models.Manager()
    
    class Meta:
        verbose_name = _("Quittance de paiement")
        verbose_name_plural = _("Quittances de paiement")
        ordering = ['-date_emission']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.numero_quittance:
            self.numero_quittance = self.generate_numero_quittance()
    
    def __str__(self):
        return f"Quittance {self.numero_quittance} - {self.paiement.reference_paiement}"
    
    def generate_numero_quittance(self):
        """Génère un numéro unique pour la quittance."""
        from django.utils.crypto import get_random_string
        from datetime import datetime
        
        # Utiliser un système basé sur timestamp + random pour garantir l'unicité
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        prefix = "REC"
        
        # Format: REC-YYYYMMDDHHMMSS-XXXX
        code = f"{prefix}-{timestamp}-{get_random_string(4, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')}"
        
        # Vérifier l'unicité et régénérer si nécessaire
        while QuittancePaiement.objects.filter(numero_quittance=code).exists():
            code = f"{prefix}-{timestamp}-{get_random_string(4, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')}"
        
        return code
    
    def get_locataire(self):
        """Retourne le locataire associé à cette quittance."""
        return self.paiement.get_locataire()
    
    def get_bailleur(self):
        """Retourne le bailleur associé à cette quittance."""
        return self.paiement.get_bailleur()
    
    def get_propriete(self):
        """Retourne la propriété associée à cette quittance."""
        return self.paiement.get_propriete()
    
    def get_contrat(self):
        """Retourne le contrat associé à cette quittance."""
        return self.paiement.contrat
    
    def marquer_imprimee(self):
        """Marque la quittance comme imprimée."""
        self.statut = 'imprimee'
        self.date_impression = timezone.now()
        self.save()
    
    def marquer_envoyee(self):
        """Marque la quittance comme envoyée."""
        self.statut = 'envoyee'
        self.save()
    
    def marquer_archivee(self):
        """Marque la quittance comme archivée."""
        self.statut = 'archivée'
        self.save()
    
    def get_statut_display_color(self):
        """Retourne la couleur CSS pour le statut."""
        colors = {
            'generee': 'info',
            'imprimee': 'success',
            'envoyee': 'primary',
            'archivée': 'secondary',
        }
        return colors.get(self.statut, 'secondary')


class RetraitBailleur(models.Model):
    """Modèle pour les retraits des bailleurs avec gestion des charges déductibles."""
    
    # Informations de base
    bailleur = models.ForeignKey(
        'proprietes.Bailleur',
        on_delete=models.PROTECT,
        related_name='retraits_bailleur',
        verbose_name=_("Bailleur")
    )
    
    # Période concernée
    mois_retrait = models.DateField(
        verbose_name=_("Mois de retrait"),
        help_text=_("Mois pour lequel le retrait est effectué")
    )
    
    # Montants
    montant_loyers_bruts = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        verbose_name=_("Montant total des loyers bruts")
    )
    montant_charges_deductibles = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name=_("Montant total des charges déductibles")
    )
    montant_net_a_payer = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name=_("Montant net à payer (après déduction des charges)")
    )
    
    # Type et statut
    type_retrait = models.CharField(
        max_length=20,
        choices=[
            ('mensuel', 'Retrait mensuel'),
            ('trimestriel', 'Retrait trimestriel'),
            ('annuel', 'Retrait annuel'),
            ('exceptionnel', 'Retrait exceptionnel'),
        ],
        default='mensuel',
        verbose_name=_("Type de retrait")
    )
    statut = models.CharField(
        max_length=20,
        choices=[
            ('en_attente', 'En attente'),
            ('valide', 'Validé'),
            ('paye', 'Payé'),
            ('annule', 'Annulé'),
        ],
        default='en_attente',
        verbose_name=_("Statut")
    )
    
    # Mode de retrait
    mode_retrait = models.CharField(
        max_length=20,
        choices=[
            ('virement', 'Virement bancaire'),
            ('cheque', 'Chèque'),
            ('especes', 'Espèces'),
        ],
        verbose_name=_("Mode de retrait")
    )
    
    # Dates
    date_demande = models.DateField(verbose_name=_("Date de demande"))
    date_versement = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Date de versement")
    )
    
    # Informations bancaires
    numero_cheque = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_("Numéro de chèque")
    )
    reference_virement = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Référence virement")
    )
    
    # Métadonnées
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name=_("Date de création"))
    date_modification = models.DateTimeField(auto_now=True, verbose_name=_("Date de modification"))
    notes = models.TextField(blank=True, verbose_name=_("Notes"))
    
    # Liaison avec le récapitulatif
    recap_lie = models.ForeignKey(
        'RecapMensuel',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='retraits_lies',
        verbose_name=_("Récapitulatif lié"),
        help_text=_("Récapitulatif mensuel à l'origine de ce retrait")
    )
    
    # Relations
    cree_par = models.ForeignKey(
        'utilisateurs.Utilisateur',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='retraits_crees',
        verbose_name=_("Créé par")
    )
    valide_par = models.ForeignKey(
        'utilisateurs.Utilisateur',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='retraits_valides',
        verbose_name=_("Validé par")
    )
    paye_par = models.ForeignKey(
        'utilisateurs.Utilisateur',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='retraits_payes',
        verbose_name=_("Payé par")
    )
    
    # SÉCURITÉ ET AUDIT - NOUVEAU
    # Horodatage des actions critiques
    date_validation = models.DateTimeField(
        null=True, 
        blank=True, 
        verbose_name=_("Date de validation")
    )
    date_paiement = models.DateTimeField(
        null=True, 
        blank=True, 
        verbose_name=_("Date de paiement")
    )
    date_annulation = models.DateTimeField(
        null=True, 
        blank=True, 
        verbose_name=_("Date d'annulation")
    )
    
    # Motif des actions critiques
    motif_annulation = models.TextField(
        blank=True, 
        null=True, 
        verbose_name=_("Motif de l'annulation")
    )
    motif_modification = models.TextField(
        blank=True, 
        null=True, 
        verbose_name=_("Motif de la modification")
    )
    
    # Contrôles de sécurité
    peut_etre_modifie = models.BooleanField(
        default=True, 
        verbose_name=_("Peut être modifié"),
        help_text=_("Désactivé une fois validé")
    )
    peut_etre_annule = models.BooleanField(
        default=True, 
        verbose_name=_("Peut être annulé"),
        help_text=_("Désactivé une fois payé")
    )
    
    # Hash de sécurité pour vérifier l'intégrité
    hash_securite = models.CharField(
        max_length=64, 
        blank=True, 
        null=True, 
        verbose_name=_("Hash de sécurité")
    )
    
    # Niveau d'autorisation requis pour les modifications
    NIVEAU_AUTORISATION_CHOICES = [
        ('standard', 'Standard'),
        ('superviseur', 'Superviseur'),
        ('manager', 'Manager'),
        ('admin', 'Administrateur'),
        ('system', 'Système uniquement'),
    ]
    niveau_autorisation_modification = models.CharField(
        max_length=20,
        choices=NIVEAU_AUTORISATION_CHOICES,
        default='standard',
        verbose_name=_("Niveau d'autorisation requis pour modification")
    )
    
    # Lien avec les charges déductibles
    charges_deductibles = models.ManyToManyField(
        'ChargeDeductible',
        through='RetraitChargeDeductible',
        related_name='retraits_bailleur',
        verbose_name=_("Charges déductibles")
    )
    
    # Lien avec les paiements concernés
    paiements_concernes = models.ManyToManyField(
        'Paiement',
        related_name='retraits_bailleur',
        verbose_name=_("Paiements concernés")
    )
    
    is_deleted = models.BooleanField(default=False, verbose_name='Supprimé logiquement')
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name='Date de suppression')
    deleted_by = models.ForeignKey(
        'utilisateurs.Utilisateur',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='retraits_bailleur_supprimes',
        verbose_name='Supprimé par'
    )
    
    objects = NonDeletedManager()
    all_objects = models.Manager()
    
    class Meta:
        verbose_name = _("Retrait bailleur")
        verbose_name_plural = _("Retraits bailleur")
        ordering = ['-mois_retrait']
        # Temporairement commenté pour permettre les retraits supprimés
        # unique_together = ['bailleur', 'mois_retrait']
        constraints = [
            models.UniqueConstraint(
                fields=['bailleur', 'mois_retrait'],
                condition=models.Q(is_deleted=False),
                name='unique_retrait_actif_per_bailleur_month'
            )
        ]
        indexes = [
            models.Index(fields=['bailleur', 'mois_retrait']),
            models.Index(fields=['statut']),
            models.Index(fields=['date_demande']),
        ]
    
    def __str__(self):
        return f"Retrait {self.bailleur} - {self.mois_retrait.strftime('%B %Y')} - {self.montant_net_a_payer} F CFA"
    
    def save(self, *args, **kwargs):
        """Override save pour calculer automatiquement le montant net et générer le hash de sécurité."""
        # S'assurer que les montants sont des Decimal
        from decimal import Decimal
        if isinstance(self.montant_loyers_bruts, str):
            self.montant_loyers_bruts = Decimal(self.montant_loyers_bruts)
        if isinstance(self.montant_charges_deductibles, str):
            self.montant_charges_deductibles = Decimal(self.montant_charges_deductibles)
        
        # Calculer le montant net
        if self.montant_loyers_bruts > 0:
            self.montant_net_a_payer = self.montant_loyers_bruts - self.montant_charges_deductibles
        
        # Générer le hash de sécurité
        self.generer_hash_securite()
        
        super().save(*args, **kwargs)
    
    def generer_hash_securite(self):
        """Génère un hash de sécurité pour vérifier l'intégrité des données."""
        import hashlib
        data_string = f"{self.id}{self.montant_loyers_bruts}{self.montant_charges_deductibles}{self.statut}{self.date_creation}"
        self.hash_securite = hashlib.sha256(data_string.encode()).hexdigest()
    
    def verifier_integrite(self):
        """Vérifie l'intégrité des données en comparant avec le hash de sécurité."""
        if not self.hash_securite:
            return False
        import hashlib
        data_string = f"{self.id}{self.montant_loyers_bruts}{self.montant_charges_deductibles}{self.statut}{self.date_creation}"
        current_hash = hashlib.sha256(data_string.encode()).hexdigest()
        return current_hash == self.hash_securite
    
    def valider_retrait(self, utilisateur, force=False):
        """
        Valide un retrait avec contrôles de sécurité.
        Une fois validé, le retrait ne peut plus être modifié sauf par un administrateur.
        """
        from django.utils import timezone
        
        # Vérifier que l'utilisateur a les droits
        if not force and not self.peut_etre_valide(utilisateur):
            raise PermissionError("Vous n'avez pas les droits pour valider ce retrait")
        
        # Vérifier l'intégrité des données
        if not self.verifier_integrite():
            raise ValueError("L'intégrité des données du retrait est compromise")
        
        # Mettre à jour le statut
        self.statut = 'valide'
        self.valide_par = utilisateur
        self.date_validation = timezone.now()
        
        # Désactiver la modification (sauf pour les administrateurs)
        self.peut_etre_modifie = False
        self.niveau_autorisation_modification = 'admin'
        
        # Sauvegarder
        self.save()
    
        # Créer un log d'audit
        self.creer_log_audit('validation', utilisateur, f"Retrait validé par {utilisateur.get_nom_complet()}")
    
    def marquer_paye(self, utilisateur, force=False):
        """
        Marque un retrait comme payé avec contrôles de sécurité.
        Une fois payé, le retrait ne peut plus être annulé sauf par le système.
        """
        from django.utils import timezone
        
        # Vérifier que l'utilisateur a les droits
        if not force and not self.peut_etre_paye(utilisateur):
            raise PermissionError("Vous n'avez pas les droits pour marquer ce retrait comme payé")
        
        # Vérifier que le retrait est validé
        if self.statut != 'valide':
            raise ValueError("Seuls les retraits validés peuvent être marqués comme payés")
        
        # Mettre à jour le statut
        self.statut = 'paye'
        self.paye_par = utilisateur
        self.date_paiement = timezone.now()
        self.date_versement = timezone.now().date()
        
        # Désactiver l'annulation (sauf pour le système)
        self.peut_etre_annule = False
        self.niveau_autorisation_modification = 'system'
        
        # Sauvegarder
        self.save()
    
        # Créer un log d'audit
        self.creer_log_audit('paiement', utilisateur, f"Retrait marqué comme payé par {utilisateur.get_nom_complet()}")
    
    def annuler_retrait(self, utilisateur, motif, force=False):
        """
        Annule un retrait avec contrôles de sécurité stricts.
        Seuls les administrateurs peuvent annuler un retrait validé.
        """
        from django.utils import timezone
        
        # Vérifier que l'utilisateur a les droits
        if not force and not self.peut_etre_annule(utilisateur):
            raise PermissionError("Vous n'avez pas les droits pour annuler ce retrait")
        
        # Vérifier que le retrait peut être annulé
        if not self.peut_etre_annule:
            raise ValueError("Ce retrait ne peut plus être annulé")
        
        # Si le retrait est validé, seuls les administrateurs peuvent l'annuler
        if self.statut == 'valide' and not self.utilisateur_est_admin(utilisateur):
            raise PermissionError("Seuls les administrateurs peuvent annuler un retrait validé")
        
        # Mettre à jour le statut
        self.statut = 'annule'
        self.date_annulation = timezone.now()
        self.motif_annulation = motif
        
        # Désactiver toutes les modifications
        self.peut_etre_modifie = False
        self.peut_etre_annule = False
        self.niveau_autorisation_modification = 'system'
        
        # Sauvegarder
        self.save()
        
        # Créer un log d'audit
        self.creer_log_audit('annulation', utilisateur, f"Retrait annulé par {utilisateur.get_nom_complet()}. Motif: {motif}")
    
    def peut_etre_valide(self, utilisateur):
        """Vérifie si l'utilisateur peut valider ce retrait."""
        if self.statut != 'en_attente':
            return False
        return self.utilisateur_est_autorise(utilisateur, 'standard')
    
    def peut_etre_paye(self, utilisateur):
        """Vérifie si l'utilisateur peut marquer ce retrait comme payé."""
        if self.statut != 'valide':
            return False
        return self.utilisateur_est_autorise(utilisateur, 'superviseur')
    
    def peut_etre_annule(self, utilisateur):
        """Vérifie si l'utilisateur peut annuler ce retrait."""
        if not self.peut_etre_annule:
            return False
        if self.statut == 'paye':
            return False
        return self.utilisateur_est_autorise(utilisateur, 'standard')
    
    def get_mode_display_icon(self):
        """Retourne l'icône Bootstrap pour le mode de retrait."""
        icons = {
            'virement': 'bi-bank',
            'cheque': 'bi-receipt',
            'especes': 'bi-cash-coin',
        }
        return icons.get(self.mode_retrait, 'bi-currency-exchange')
    
    def get_mode_retrait_display(self):
        """Retourne le nom d'affichage du mode de retrait."""
        modes = {
            'virement': 'Virement bancaire',
            'cheque': 'Chèque',
            'especes': 'Espèces',
        }
        return modes.get(self.mode_retrait, self.mode_retrait)
    
    def get_type_retrait_display(self):
        """Retourne le nom d'affichage du type de retrait."""
        types = {
            'mensuel': 'Retrait mensuel',
            'trimestriel': 'Retrait trimestriel',
            'annuel': 'Retrait annuel',
            'exceptionnel': 'Retrait exceptionnel',
        }
        return types.get(self.type_retrait, self.type_retrait)
    
    def get_statut_display(self):
        """Retourne le nom d'affichage du statut."""
        statuts = {
            'en_attente': 'En attente',
            'valide': 'Validé',
            'paye': 'Payé',
            'annule': 'Annulé',
        }
        return statuts.get(self.statut, self.statut)
    
    def get_statut_display_color(self):
        """Retourne la couleur CSS pour le statut."""
        colors = {
            'en_attente': 'warning',
            'valide': 'success',
            'paye': 'info',
            'annule': 'danger',
        }
        return colors.get(self.statut, 'secondary')
    
    def peut_etre_edite(self):
        """Vérifie si le retrait peut être édité."""
        return self.peut_etre_modifie and self.statut == 'en_attente'
    
    def ajouter_charge_bailleur(self, charge_bailleur, montant_deduction, notes=""):
        """
        Ajoute une charge de bailleur au retrait pour déduction automatique.
        
        Args:
            charge_bailleur: Instance de ChargesBailleur
            montant_deduction: Montant à déduire
            notes: Notes sur la déduction
            
        Returns:
            bool: True si la charge a été ajoutée avec succès
        """
        try:
            from proprietes.models import ChargesBailleurRetrait
            
            # Vérifier que le retrait peut être modifié
            if not self.peut_etre_edite():
                raise ValueError("Ce retrait ne peut plus être modifié")
            
            # Vérifier que la charge peut être déduite
            if not charge_bailleur.peut_etre_deduit():
                raise ValueError("Cette charge ne peut pas être déduite")
            
            # Vérifier le montant
            montant_deductible = charge_bailleur.get_montant_deductible()
            if montant_deduction > montant_deductible:
                raise ValueError(f"Le montant de déduction ({montant_deduction}) dépasse le montant déductible ({montant_deductible})")
            
            # Créer la liaison
            liaison = ChargesBailleurRetrait.objects.create(
                charge_bailleur=charge_bailleur,
                retrait_bailleur=self,
                montant_deduit=montant_deduction,
                notes=notes
            )
            
            # Marquer la charge comme déduite
            montant_effectivement_deduit = charge_bailleur.marquer_comme_deduit(montant_deduction)
            
            # Mettre à jour le montant des charges déductibles du retrait
            self.montant_charges_deductibles += montant_effectivement_deduit
            self.save()
            
            # Créer un log d'audit
            self.creer_log_audit('ajout_charge', self.cree_par, 
                                f"Charge '{charge_bailleur.titre}' ajoutée pour {montant_effectivement_deduit} F CFA")
            
            return True
            
        except Exception as e:
            # Log l'erreur
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Erreur lors de l'ajout de la charge bailleur: {e}")
            return False
    
    def retirer_charge_bailleur(self, charge_bailleur, notes=""):
        """
        Retire une charge de bailleur du retrait.
        
        Args:
            charge_bailleur: Instance de ChargesBailleur
            notes: Notes sur le retrait
            
        Returns:
            bool: True si la charge a été retirée avec succès
        """
        try:
            from proprietes.models import ChargesBailleurRetrait
            
            # Vérifier que le retrait peut être modifié
            if not self.peut_etre_edite():
                raise ValueError("Ce retrait ne peut plus être modifié")
            
            # Trouver la liaison
            liaison = ChargesBailleurRetrait.objects.filter(
                charge_bailleur=charge_bailleur,
                retrait_bailleur=self
            ).first()
            
            if not liaison:
                raise ValueError("Cette charge n'est pas liée à ce retrait")
            
            # Récupérer le montant déduit
            montant_deduit = liaison.montant_deduit
            
            # Supprimer la liaison
            liaison.delete()
            
            # Remettre la charge en attente
            charge_bailleur.montant_deja_deduit -= montant_deduit
            charge_bailleur.statut = 'en_attente'
            charge_bailleur.save()
            
            # Mettre à jour le montant des charges déductibles du retrait
            self.montant_charges_deductibles -= montant_deduit
            self.save()
            
            # Créer un log d'audit
            self.creer_log_audit('retrait_charge', self.cree_par, 
                                f"Charge '{charge_bailleur.titre}' retirée ({montant_deduit} F CFA)")
            
            return True
            
        except Exception as e:
            # Log l'erreur
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Erreur lors du retrait de la charge bailleur: {e}")
            return False
    
    def get_charges_bailleur_liees(self):
        """Récupère toutes les charges de bailleur liées à ce retrait."""
        try:
            from proprietes.models import ChargesBailleurRetrait
            return ChargesBailleurRetrait.objects.filter(retrait_bailleur=self).select_related('charge_bailleur')
        except Exception:
            return []
    
    def calculer_charges_automatiquement(self, mois_retrait=None):
        """
        Calcule automatiquement les charges de bailleur à déduire pour le mois donné.
        
        Args:
            mois_retrait: Mois de retrait (par défaut: mois du retrait)
            
        Returns:
            dict: Résumé des charges calculées
        """
        try:
            from proprietes.models import ChargesBailleur
            from django.db.models import Sum
            from django.utils import timezone
            
            if mois_retrait is None:
                mois_retrait = self.mois_retrait
            
            # Récupérer toutes les charges de bailleur du bailleur pour le mois
            charges = ChargesBailleur.objects.filter(
                propriete__bailleur=self.bailleur,
                date_charge__year=mois_retrait.year,
                date_charge__month=mois_retrait.month,
                statut__in=['en_attente', 'deduite_retrait']
            ).select_related('propriete')
            
            from decimal import Decimal
            total_charges = Decimal('0')
            charges_details = []
            
            for charge in charges:
                montant_deductible = charge.get_montant_deductible()
                if montant_deductible > 0:
                    total_charges += montant_deductible
                    charges_details.append({
                        'charge': charge,
                        'montant_deductible': montant_deductible,
                        'propriete': charge.propriete
                    })
            
            return {
                'total_charges': total_charges,
                'charges_details': charges_details,
                'nombre_charges': len(charges_details)
            }
            
        except Exception as e:
            # Log l'erreur
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Erreur lors du calcul automatique des charges: {e}")
            return {'total_charges': 0, 'charges_details': [], 'nombre_charges': 0}
    
    def appliquer_charges_automatiquement(self, mois_retrait=None):
        """
        Applique automatiquement toutes les charges de bailleur calculées.
        
        Args:
            mois_retrait: Mois de retrait (par défaut: mois du retrait)
            
        Returns:
            dict: Résumé de l'application des charges
        """
        try:
            # Calculer les charges
            calcul = self.calculer_charges_automatiquement(mois_retrait)
            
            if calcul['total_charges'] == 0:
                return {'success': True, 'message': 'Aucune charge à appliquer', 'charges_appliquees': 0}
            
            charges_appliquees = 0
            
            # Appliquer chaque charge
            for detail in calcul['charges_details']:
                charge = detail['charge']
                montant = detail['montant_deductible']
                
                if self.ajouter_charge_bailleur(charge, montant, "Application automatique"):
                    charges_appliquees += 1
            
            # Mettre à jour le retrait
            self.save()
            
            return {
                'success': True,
                'message': f'{charges_appliquees} charges appliquées pour un total de {calcul["total_charges"]} F CFA',
                'charges_appliquees': charges_appliquees,
                'total_applique': calcul['total_charges']
            }
            
        except Exception as e:
            # Log l'erreur
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Erreur lors de l'application automatique des charges: {e}")
            return {'success': False, 'message': f'Erreur: {str(e)}', 'charges_appliquees': 0}
    
    def utilisateur_est_autorise(self, utilisateur, niveau_requis):
        """Vérifie si l'utilisateur a le niveau d'autorisation requis."""
        niveaux = {
            'standard': 1,
            'superviseur': 2,
            'manager': 3,
            'admin': 4,
            'system': 5
        }
        
        # Vérifier le niveau de l'utilisateur
        niveau_utilisateur = self.get_niveau_utilisateur(utilisateur)
        return niveaux.get(niveau_utilisateur, 0) >= niveaux.get(niveau_requis, 0)
    
    def utilisateur_est_admin(self, utilisateur):
        """Vérifie si l'utilisateur est un administrateur."""
        return self.utilisateur_est_autorise(utilisateur, 'admin')
    
    def get_niveau_utilisateur(self, utilisateur):
        """Détermine le niveau d'autorisation de l'utilisateur."""
        # Logique pour déterminer le niveau de l'utilisateur
        # À adapter selon votre système de permissions
        if utilisateur.is_superuser:
            return 'admin'
        elif hasattr(utilisateur, 'groupe') and utilisateur.groupe:
            if 'admin' in utilisateur.groupe.nom.lower():
                return 'admin'
            elif 'manager' in utilisateur.groupe.nom.lower():
                return 'manager'
            elif 'superviseur' in utilisateur.groupe.nom.lower():
                return 'superviseur'
        return 'standard'
    
    def creer_log_audit(self, action, utilisateur, description):
        """Crée un log d'audit pour tracer toutes les actions critiques."""
        try:
            from core.models import LogAudit
            LogAudit.objects.create(
                modele='RetraitBailleur',
                instance_id=self.id,
                action=action,
                utilisateur=utilisateur,
                description=description,
                donnees_avant={},
                donnees_apres=self.to_dict()
            )
        except Exception as e:
            # En cas d'erreur, on log mais on ne bloque pas l'opération
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Erreur lors de la création du log d'audit: {e}")
    
    def to_dict(self):
        """Convertit le retrait en dictionnaire pour l'audit."""
        return {
            'id': self.id,
            'statut': self.statut,
            'montant_loyers_bruts': str(self.montant_loyers_bruts),
            'montant_charges_deductibles': str(self.montant_charges_deductibles),
            'montant_net_a_payer': str(self.montant_net_a_payer),
            'date_validation': self.date_validation.isoformat() if self.date_validation else None,
            'date_paiement': self.date_paiement.isoformat() if self.date_paiement else None,
            'hash_securite': self.hash_securite
        }


class RetraitChargeDeductible(models.Model):
    """Modèle de liaison entre RetraitBailleur et ChargeDeductible."""
    
    retrait_bailleur = models.ForeignKey(
        RetraitBailleur,
        on_delete=models.CASCADE,
        verbose_name=_("Retrait bailleur")
    )
    charge_deductible = models.ForeignKey(
        ChargeDeductible,
        on_delete=models.CASCADE,
        verbose_name=_("Charge déductible")
    )
    date_ajout = models.DateTimeField(auto_now_add=True, verbose_name=_("Date d'ajout"))
    
    class Meta:
        verbose_name = _("Charge déductible du retrait")
        verbose_name_plural = _("Charges déductibles du retrait")
        unique_together = ['retrait_bailleur', 'charge_deductible']
    
    def __str__(self):
        return f"{self.retrait_bailleur} - {self.charge_deductible}"


class RecuRetrait(models.Model):
    """Modèle pour les reçus de retrait des bailleurs."""
    
    retrait_bailleur = models.OneToOneField(
        RetraitBailleur,
        on_delete=models.CASCADE,
        related_name='recu_retrait',
        verbose_name=_("Retrait bailleur")
    )
    numero_recu = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_("Numéro de reçu")
    )
    date_emission = models.DateTimeField(auto_now_add=True, verbose_name=_("Date d'émission"))
    
    # Informations d'impression
    imprime = models.BooleanField(default=False, verbose_name=_("Imprimé"))
    date_impression = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Date d'impression")
    )
    imprime_par = models.ForeignKey(
        'utilisateurs.Utilisateur',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recus_retrait_imprimes',
        verbose_name=_("Imprimé par")
    )
    
    # Informations de génération
    genere_automatiquement = models.BooleanField(
        default=True,
        verbose_name=_("Généré automatiquement")
    )
    
    # Options d'impression
    format_impression = models.CharField(
        max_length=20,
        choices=[
            ('a5', 'A5'),
            ('a4', 'A4'),
        ],
        default='a5',
        verbose_name=_("Format d'impression")
    )
    
    # Métadonnées
    notes_internes = models.TextField(blank=True, verbose_name=_("Notes internes"))
    
    class Meta:
        verbose_name = _("Reçu de retrait")
        verbose_name_plural = _("Reçus de retrait")
        ordering = ['-date_emission']
    
    def __str__(self):
        return f"Reçu retrait {self.numero_recu} - {self.retrait_bailleur.bailleur}"
    
    def save(self, *args, **kwargs):
        if not self.numero_recu:
            self.numero_recu = self._generer_numero_recu()
        super().save(*args, **kwargs)
    
    def _generer_numero_recu(self):
        """Génère un numéro de reçu unique."""
        from datetime import datetime
        from django.utils.crypto import get_random_string
        
        prefix = "RET"
        date_str = datetime.now().strftime("%Y%m")
        random_str = get_random_string(6, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
        
        numero = f"{prefix}-{date_str}-{random_str}"
        
        # Vérifier l'unicité
        while RecuRetrait.objects.filter(numero_recu=numero).exists():
            random_str = get_random_string(6, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
            numero = f"{prefix}-{date_str}-{random_str}"
        
        return numero
    
    def marquer_imprime(self, utilisateur):
        """Marque le reçu comme imprimé."""
        self.imprime = True
        self.date_impression = timezone.now()
        self.imprime_par = utilisateur
        self.save()
    
    def get_bailleur(self):
        """Retourne le bailleur associé à ce reçu."""
        return self.retrait_bailleur.bailleur
    
    def get_montant_total(self):
        """Retourne le montant total du retrait."""
        return self.retrait_bailleur.montant_net_a_payer
    
    def get_montant_formatted(self):
        """Retourne le montant formaté."""
        return f"{self.get_montant_total()} F CFA"
    
    def get_date_retrait(self):
        """Retourne la date du retrait."""
        return self.retrait_bailleur.mois_retrait
    
    def get_statut_retrait(self):
        """Retourne le statut du retrait."""
        return self.retrait_bailleur.get_statut_display()


class TableauBordFinancier(models.Model):
    """Modèle pour le tableau de bord financier professionnel - Intégré dans le module paiements."""
    
    # Informations de base
    nom = models.CharField(
        max_length=100, 
        verbose_name=_("Nom du tableau de bord"),
        help_text=_("Nom descriptif du tableau de bord")
    )
    description = models.TextField(
        blank=True, 
        verbose_name=_("Description"),
        help_text=_("Description détaillée du tableau de bord")
    )
    
    # Relations
    proprietes = models.ManyToManyField(
        'proprietes.Propriete',
        verbose_name=_("Propriétés incluses"),
        help_text=_("Propriétés à inclure dans ce tableau de bord"),
        blank=True
    )
    bailleurs = models.ManyToManyField(
        'proprietes.Bailleur',
        blank=True,
        verbose_name=_("Bailleurs inclus"),
        help_text=_("Bailleurs à inclure dans ce tableau de bord")
    )
    
    # Paramètres d'affichage
    afficher_revenus = models.BooleanField(
        default=True,
        verbose_name=_("Afficher les revenus"),
        help_text=_("Inclure les revenus dans le tableau de bord")
    )
    afficher_charges = models.BooleanField(
        default=True,
        verbose_name=_("Afficher les charges"),
        help_text=_("Inclure les charges dans le tableau de bord")
    )
    afficher_benefices = models.BooleanField(
        default=True,
        verbose_name=_("Afficher les bénéfices"),
        help_text=_("Inclure les bénéfices dans le tableau de bord")
    )
    afficher_taux_occupation = models.BooleanField(
        default=True,
        verbose_name=_("Afficher le taux d'occupation"),
        help_text=_("Inclure le taux d'occupation dans le tableau de bord")
    )
    
    # Période d'analyse
    PERIODE_CHOICES = [
        ('mensuel', 'Mensuel'),
        ('trimestriel', 'Trimestriel'),
        ('annuel', 'Annuel'),
        ('personnalise', 'Personnalisé'),
    ]
    periode = models.CharField(
        max_length=20,
        choices=PERIODE_CHOICES,
        default='mensuel',
        verbose_name=_("Période d'analyse")
    )
    date_debut_personnalisee = models.DateField(
        blank=True,
        null=True,
        verbose_name=_("Date de début (période personnalisée)")
    )
    date_fin_personnalisee = models.DateField(
        blank=True,
        null=True,
        verbose_name=_("Date de fin (période personnalisée)")
    )
    
    # Configuration avancée
    seuil_alerte = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name=_("Seuil d'alerte"),
        help_text=_("Montant seuil pour déclencher des alertes")
    )
    devise = models.CharField(
        max_length=10,
        default='F CFA',
        verbose_name=_("Devise"),
        help_text=_("Devise utilisée pour les montants")
    )
    couleur_theme = models.CharField(
        max_length=7,
        default='#007bff',
        verbose_name=_("Couleur du thème"),
        help_text=_("Couleur principale du tableau de bord (format hexadécimal)")
    )
    
    # Métadonnées
    date_creation = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Date de création")
    )
    date_modification = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Date de modification")
    )
    cree_par = models.ForeignKey(
        'utilisateurs.Utilisateur',
        on_delete=models.CASCADE,
        verbose_name=_("Créé par"),
        related_name='tableaux_bord_crees'
    )
    actif = models.BooleanField(
        default=True,
        verbose_name=_("Tableau actif"),
        help_text=_("Désactiver pour masquer ce tableau de bord")
    )
    
    class Meta:
        verbose_name = _("Tableau de bord financier")
        verbose_name_plural = _("Tableaux de bord financiers")
        ordering = ['-date_creation']
        permissions = [
            ("view_tableau_bord_financier", "Peut voir les tableaux de bord financiers"),
            ("add_tableau_bord_financier", "Peut créer des tableaux de bord financiers"),
            ("change_tableau_bord_financier", "Peut modifier les tableaux de bord financiers"),
            ("delete_tableau_bord_financier", "Peut supprimer les tableaux de bord financiers"),
        ]
    
    def __str__(self):
        return f"{self.nom} ({self.get_periode_display()})"
    
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('paiements:tableau_bord_detail', kwargs={'pk': self.pk})
    
    def get_periode_analyse(self):
        """Retourne la période d'analyse pour le calcul."""
        from django.utils import timezone
        now = timezone.now()
        
        if self.periode == 'mensuel':
            return {
                'debut': now.replace(day=1),
                'fin': now
            }
        elif self.periode == 'trimestriel':
            # Calculer le trimestre actuel
            quarter = (now.month - 1) // 3
            start_month = quarter * 3 + 1
            return {
                'debut': now.replace(month=start_month, day=1),
                'fin': now
            }
        elif self.periode == 'annuel':
            return {
                'debut': now.replace(month=1, day=1),
                'fin': now
            }
        elif self.periode == 'personnalise' and self.date_debut_personnalisee and self.date_fin_personnalisee:
            return {
                'debut': self.date_debut_personnalisee,
                'fin': self.date_fin_personnalisee
            }
        
        # Par défaut, mois en cours
        return {
            'debut': now.replace(day=1),
            'fin': now
        }
    
    def get_statistiques_financieres(self):
        """Retourne les statistiques financières pour la période."""
        periode = self.get_periode_analyse()
        
        # Calculer les revenus (loyers reçus)
        revenus = self._calculer_revenus(periode)
        
        # Calculer les charges
        charges = self._calculer_charges(periode)
        
        # Calculer le taux d'occupation
        taux_occupation = self._calculer_taux_occupation(periode)
        
        return {
            'revenus': revenus,
            'charges': charges,
            'benefices': revenus - charges,
            'taux_occupation': taux_occupation,
            'periode': periode
        }
    
    def _calculer_revenus(self, periode):
        """Calcule les revenus pour la période donnée."""
        from .models import Paiement
        from decimal import Decimal
        
        paiements = Paiement.objects.filter(
            contrat__propriete__in=self.proprietes.all(),
            date_paiement__gte=periode['debut'],
            date_paiement__lte=periode['fin'],
            statut='valide'
        )
        
        total = paiements.aggregate(
            total=models.Sum('montant')
        )['total'] or Decimal('0')
        
        if not isinstance(total, Decimal):
            total = Decimal(str(total))
        
        return total
    
    def _calculer_charges(self, periode):
        """Calcule les charges pour la période donnée."""
        from proprietes.models import ChargeBailleur
        from decimal import Decimal
        
        charges = ChargeBailleur.objects.filter(
            propriete__in=self.proprietes.all(),
            date_charge__gte=periode['debut'],
            date_charge__lte=periode['fin']
        )
        
        total = charges.aggregate(
            total=models.Sum('montant')
        )['total'] or Decimal('0')
        
        if not isinstance(total, Decimal):
            total = Decimal(str(total))
        
        return total
    
    def _calculer_taux_occupation(self, periode):
        """Calcule le taux d'occupation pour la période donnée."""
        from contrats.models import Contrat
        
        contrats_actifs = Contrat.objects.filter(
            propriete__in=self.proprietes.all(),
            est_actif=True,
            est_resilie=False
        )
        
        total_proprietes = self.proprietes.count()
        if total_proprietes == 0:
            return 0
        
        return (contrats_actifs.count() / total_proprietes) * 100
    
    def get_nombre_proprietes(self):
        """Retourne le nombre de propriétés incluses."""
        return self.proprietes.count()
    
    def get_nombre_bailleurs(self):
        """Retourne le nombre de bailleurs inclus."""
        return self.bailleurs.count()
    
    def is_alerte_active(self):
        """Vérifie si le seuil d'alerte est dépassé."""
        if not self.seuil_alerte:
            return False
        
        stats = self.get_statistiques_financieres()
        return stats['benefices'] < self.seuil_alerte
    
    def get_statut_display(self):
        """Retourne le statut d'affichage du tableau de bord."""
        if not self.actif:
            return "Inactif"
        elif self.is_alerte_active():
            return "Alerte"
        else:
            return "Actif"
    
    @property
    def montant(self):
        """Propriété pour maintenir la compatibilité avec l'ancien modèle Retrait."""
        return self.montant_net_a_payer

# Alias pour maintenir la compatibilité avec le code existant
Retrait = RetraitBailleur


class DetailRetraitUnite(models.Model):
    """Détails d'un retrait par unité locative."""
    
    retrait = models.ForeignKey(
        RetraitBailleur,
        on_delete=models.CASCADE,
        related_name='details_unites',
        verbose_name=_("Retrait")
    )
    unite_locative = models.ForeignKey(
        'proprietes.UniteLocative',
        on_delete=models.PROTECT,
        related_name='details_retraits',
        verbose_name=_("Unité locative")
    )
    contrat = models.ForeignKey(
        'contrats.Contrat',
        on_delete=models.PROTECT,
        related_name='details_retraits',
        verbose_name=_("Contrat")
    )
    
    # Montants spécifiques à cette unité
    loyer_theorique = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Loyer théorique de l'unité")
    )
    charges_theoriques = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_("Charges théoriques de l'unité")
    )
    paiements_recus = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Paiements effectivement reçus")
    )
    charges_deductibles = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_("Charges déductibles de l'unité")
    )
    revenus_nets_unite = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Revenus nets de l'unité")
    )
    
    # Informations de performance
    taux_paiement = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name=_("Taux de paiement (%)")
    )
    statut_paiement = models.CharField(
        max_length=20,
        choices=[
            ('complet', 'Complet'),
            ('partiel', 'Partiel'),
            ('impaye', 'Impayé'),
            ('avance', 'Avance'),
        ],
        default='complet',
        verbose_name=_("Statut de paiement")
    )
    
    # Métadonnées
    date_creation = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(
        blank=True,
        verbose_name=_("Notes spécifiques à cette unité")
    )
    
    class Meta:
        verbose_name = _("Détail retrait par unité")
        verbose_name_plural = _("Détails retraits par unités")
        unique_together = ['retrait', 'unite_locative']
        ordering = ['unite_locative__numero_unite']
    
    def __str__(self):
        return f"Détail {self.retrait} - Unité {self.unite_locative.numero_unite}"
    
    def get_rentabilite_unite(self):
        """Calcule la rentabilité de l'unité pour cette période."""
        if self.loyer_theorique > 0:
            return (self.revenus_nets_unite / self.loyer_theorique) * 100
        return 0
    
    def is_unite_rentable(self):
        """Vérifie si l'unité est rentable."""
        return self.revenus_nets_unite > 0
    
    def get_statut_color(self):
        """Retourne la couleur associée au statut de paiement."""
        colors = {
            'complet': 'success',
            'partiel': 'warning',
            'impaye': 'danger',
            'avance': 'info'
        }
        return colors.get(self.statut_paiement, 'secondary')


class RecapMensuel(models.Model):
    """Récapitulatif mensuel pour un bailleur."""
    
    STATUT_CHOICES = [
        ('brouillon', _('Brouillon')),
        ('valide', _('Validé')),
        ('envoye', _('Envoyé au bailleur')),
        ('paye', _('Payé au bailleur')),
    ]
    
    # Informations de base
    bailleur = models.ForeignKey(
        'proprietes.Bailleur', on_delete=models.PROTECT, related_name='recaps_mensuels', verbose_name=_("Bailleur")
    )
    mois_recap = models.DateField(verbose_name=_("Mois du récapitulatif"))
    
    # Montants calculés automatiquement
    total_loyers_bruts = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name=_("Total des loyers bruts"))
    total_charges_deductibles = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name=_("Total des charges déductibles"))
    total_charges_bailleur = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name=_("Total des charges bailleur"), null=True, blank=True)
    total_net_a_payer = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name=_("Total net à payer"))
    
    # Compteurs automatiques
    nombre_proprietes = models.PositiveIntegerField(default=0, verbose_name=_("Nombre de propriétés"))
    nombre_contrats_actifs = models.PositiveIntegerField(default=0, verbose_name=_("Nombre de contrats actifs"))
    nombre_paiements_recus = models.PositiveIntegerField(default=0, verbose_name=_("Nombre de paiements reçus"))
    
    # NOUVEAU : Vérification des garanties financières
    total_cautions_requises = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name=_("Total des cautions requises"))
    total_avances_requises = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name=_("Total des avances requises"))
    total_cautions_versees = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name=_("Total des cautions versées"))
    total_avances_versees = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name=_("Total des avances versées"))
    garanties_suffisantes = models.BooleanField(default=False, verbose_name=_("Garanties financières suffisantes"))
    
    # Statut et workflow
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='brouillon', verbose_name=_("Statut"))
    
    # Métadonnées
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name=_("Date de création"))
    cree_par = models.ForeignKey('utilisateurs.Utilisateur', on_delete=models.SET_NULL, null=True, blank=True, related_name='recaps_mensuels_crees', verbose_name=_("Créé par"))
    date_modification = models.DateTimeField(auto_now=True, verbose_name=_("Date de modification"))
    modifie_par = models.ForeignKey('utilisateurs.Utilisateur', on_delete=models.SET_NULL, null=True, blank=True, related_name='recaps_mensuels_modifies', verbose_name=_("Modifié par"))
    
    # Relations
    # retraits_associes = models.ManyToManyField('RetraitBailleur', related_name='recaps_mensuels', verbose_name=_("Retraits associés"), blank=True)  # Temporairement commenté
    paiements_concernes = models.ManyToManyField('Paiement', related_name='recaps_mensuels', verbose_name=_("Paiements concernés"), blank=True)
    charges_deductibles = models.ManyToManyField('ChargeDeductible', related_name='recaps_mensuels', verbose_name=_("Charges déductibles"), blank=True)
    
    # Suppression logique
    is_deleted = models.BooleanField(default=False, verbose_name=_("Supprimé logiquement"))
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Date de suppression"))
    deleted_by = models.ForeignKey('utilisateurs.Utilisateur', on_delete=models.SET_NULL, null=True, blank=True, related_name='recaps_mensuels_supprimes', verbose_name=_("Supprimé par"))
    
    class Meta:
        verbose_name = _("Récapitulatif mensuel")
        verbose_name_plural = _("Récapitulatifs mensuels")
        ordering = ['-mois_recap', 'bailleur__nom']
        unique_together = ['bailleur', 'mois_recap']
        indexes = [
            models.Index(fields=['mois_recap', 'bailleur']),
            models.Index(fields=['statut', 'mois_recap']),
            models.Index(fields=['garanties_suffisantes', 'mois_recap']),
        ]
    
    def __str__(self):
        return f"Récapitulatif {self.bailleur.get_nom_complet()} - {self.mois_recap.strftime('%B %Y')}"
    
    def get_total_charges_bailleur(self):
        """Retourne le total des charges bailleur, calculé dynamiquement si nécessaire."""
        if self.total_charges_bailleur is not None:
            return self.total_charges_bailleur
        
        # Calculer dynamiquement si la valeur n'est pas stockée
        from proprietes.models import ChargesBailleur
        from django.db.models import Sum
        from decimal import Decimal
        
        if not self.bailleur:
            return Decimal('0')
        
        charges_bailleur = ChargesBailleur.objects.filter(
            propriete__bailleur=self.bailleur,
            date_charge__year=self.mois_recap.year,
            date_charge__month=self.mois_recap.month,
            statut__in=['en_attente', 'deduite_retrait']
        ).aggregate(total=Sum('montant_restant'))['total'] or Decimal('0')
        
        return charges_bailleur
    
    def get_absolute_url(self):
        return reverse('paiements:detail_recap_mensuel_auto', kwargs={'recap_id': self.pk})
    
    def calculer_totaux(self):
        """Calcule automatiquement tous les totaux et vérifie les garanties financières."""
        from django.db.models import Sum, Count
        from decimal import Decimal
        
        # Calculer les totaux des loyers (basés sur les contrats actifs, pas les paiements reçus)
        total_loyers = Decimal('0')
        total_charges = Decimal('0')
        nombre_proprietes = 0
        nombre_contrats = 0
        
        # Récupérer toutes les propriétés du bailleur avec contrats actifs
        proprietes_actives = self.bailleur.proprietes.filter(
            contrats__est_actif=True,
            contrats__est_resilie=False
        ).distinct()
        
        nombre_proprietes = proprietes_actives.count()
        
        for propriete in proprietes_actives:
            contrat_actif = propriete.contrats.filter(est_actif=True).first()
            if contrat_actif:
                nombre_contrats += 1
                # Loyer mensuel du contrat (pas besoin d'attendre le paiement)
                # Conversion sécurisée en Decimal
                loyer_mensuel = contrat_actif.loyer_mensuel
                if isinstance(loyer_mensuel, str):
                    try:
                        loyer_mensuel = Decimal(loyer_mensuel)
                    except (ValueError, TypeError):
                        loyer_mensuel = Decimal('0')
                elif loyer_mensuel is None:
                    loyer_mensuel = Decimal('0')
                total_loyers += loyer_mensuel
                
                # Charges mensuelles du contrat
                # Conversion sécurisée en Decimal
                charges_mensuelles = contrat_actif.charges_mensuelles
                if isinstance(charges_mensuelles, str):
                    try:
                        charges_mensuelles = Decimal(charges_mensuelles)
                    except (ValueError, TypeError):
                        charges_mensuelles = Decimal('0')
                elif charges_mensuelles is None:
                    charges_mensuelles = Decimal('0')
                total_charges += charges_mensuelles
        
        # NOUVEAU : Calculer les charges bailleur pour le mois
        total_charges_bailleur = self._calculer_charges_bailleur_mois()
        
        # Mettre à jour les totaux
        self.total_loyers_bruts = total_loyers
        self.total_charges_deductibles = total_charges
        self.total_charges_bailleur = total_charges_bailleur  # NOUVEAU
        self.total_net_a_payer = total_loyers - total_charges - total_charges_bailleur  # MODIFIÉ
        self.nombre_proprietes = nombre_proprietes
        self.nombre_contrats_actifs = nombre_contrats
        
        # NOUVEAU : Calculer et vérifier les garanties financières
        self.calculer_garanties_financieres()
        
        self.save()
    
    def _calculer_charges_bailleur_mois(self):
        """
        Calcule les charges bailleur pour le mois du récapitulatif.
        Utilise le service intelligent des charges bailleur.
        """
        try:
            from paiements.services_charges_bailleur import ServiceChargesBailleurIntelligent
            
            # Utiliser le service intelligent pour calculer les charges
            charges_data = ServiceChargesBailleurIntelligent.calculer_charges_bailleur_pour_mois(
                self.bailleur, self.mois_recap
            )
            
            return charges_data.get('total_charges', Decimal('0'))
            
        except Exception as e:
            # En cas d'erreur, utiliser la méthode de base
            from proprietes.models import ChargesBailleur
            from django.db.models import Sum
            
            return ChargesBailleur.objects.filter(
                propriete__bailleur=self.bailleur,
                date_charge__year=self.mois_recap.year,
                date_charge__month=self.mois_recap.month,
                statut__in=['en_attente', 'deduite_retrait']
            ).aggregate(total=Sum('montant_restant'))['total'] or Decimal('0')
    
    def calculer_garanties_financieres(self):
        """Calcule et vérifie si les garanties financières sont suffisantes."""
        from django.db.models import Sum
        from decimal import Decimal
        
        total_cautions_requises = Decimal('0')
        total_avances_requises = Decimal('0')
        total_cautions_versees = Decimal('0')
        total_avances_versees = Decimal('0')
        
        # Récupérer toutes les propriétés du bailleur avec contrats actifs
        proprietes_actives = self.bailleur.proprietes.filter(
            contrats__est_actif=True,
            contrats__est_resilie=False
        ).distinct()
        
        for propriete in proprietes_actives:
            contrat_actif = propriete.contrats.filter(est_actif=True).first()
            if contrat_actif:
                # Calculer les garanties requises (caution + avance)
                # Conversion sécurisée en Decimal
                caution_requise = contrat_actif.loyer_mensuel
                if isinstance(caution_requise, str):
                    try:
                        caution_requise = Decimal(caution_requise)
                    except (ValueError, TypeError):
                        caution_requise = Decimal('0')
                elif caution_requise is None:
                    caution_requise = Decimal('0')
                else:
                    caution_requise = Decimal(str(caution_requise))
                
                avance_requise = caution_requise  # Généralement 1 mois de loyer
                
                total_cautions_requises += caution_requise
                total_avances_requises += avance_requise
                
                # Récupérer les paiements de caution et d'avance déjà reçus
                paiements_caution = contrat_actif.paiements.filter(
                    type_paiement='caution',
                    statut='valide'
                ).aggregate(total=Sum('montant'))['total'] or 0
                
                paiements_avance = contrat_actif.paiements.filter(
                    type_paiement__in=['avance_loyer', 'avance'],
                    statut='valide'
                ).aggregate(total=Sum('montant'))['total'] or 0
                
                # Conversion sécurisée des paiements
                if paiements_caution is None:
                    paiements_caution = Decimal('0')
                else:
                    paiements_caution = Decimal(str(paiements_caution))
                
                if paiements_avance is None:
                    paiements_avance = Decimal('0')
                else:
                    paiements_avance = Decimal(str(paiements_avance))
                
                total_cautions_versees += paiements_caution
                total_avances_versees += paiements_avance
        
        # Mettre à jour les totaux des garanties
        self.total_cautions_requises = total_cautions_requises
        self.total_avances_requises = total_avances_requises
        self.total_cautions_versees = total_cautions_versees
        self.total_avances_versees = total_avances_versees
        
        # Vérifier si les garanties sont suffisantes
        self.garanties_suffisantes = (
            total_cautions_versees >= total_cautions_requises and
            total_avances_versees >= total_avances_requises
        )
    
    def peut_etre_paye(self):
        """Vérifie si le récapitulatif peut être payé au bailleur."""
        return (
            self.statut in ['brouillon', 'valide'] and
            self.garanties_suffisantes and
            self.total_net_a_payer > 0
        )
    
    def get_statut_display(self):
        """Retourne le statut affiché avec indication des garanties."""
        statut_base = dict(self.STATUT_CHOICES).get(self.statut, self.statut)
        
        if self.statut in ['brouillon', 'valide']:
            if not self.garanties_suffisantes:
                return f"{statut_base} - Garanties insuffisantes"
            elif self.peut_etre_paye():
                return f"{statut_base} - Prêt pour paiement"
        
        return statut_base
    
    @classmethod
    def get_prochain_mois_recap_pour_bailleur(cls, bailleur):
        """
        Détermine automatiquement le prochain mois de récapitulatif pour un bailleur
        basé sur le dernier récapitulatif existant.
        
        Args:
            bailleur: Instance du modèle Bailleur
            
        Returns:
            date: Date du prochain mois de récapitulatif (1er du mois)
        """
        from datetime import date, timedelta
        from dateutil.relativedelta import relativedelta
        
        # Récupérer le dernier récapitulatif pour ce bailleur
        dernier_recap = cls.objects.filter(
            bailleur=bailleur,
            is_deleted=False
        ).order_by('-mois_recap').first()
        
        if dernier_recap:
            # Si un récapitulatif existe, prendre le mois suivant
            prochain_mois = dernier_recap.mois_recap + relativedelta(months=1)
        else:
            # Si aucun récapitulatif n'existe, commencer par le mois actuel
            prochain_mois = date.today().replace(day=1)
        
        return prochain_mois
    
    @classmethod
    def get_dernier_mois_recap_pour_bailleur(cls, bailleur):
        """
        Récupère le dernier mois de récapitulatif pour un bailleur.
        
        Args:
            bailleur: Instance du modèle Bailleur
            
        Returns:
            date or None: Date du dernier mois de récapitulatif ou None si aucun
        """
        dernier_recap = cls.objects.filter(
            bailleur=bailleur,
            is_deleted=False
        ).order_by('-mois_recap').first()
        
        return dernier_recap.mois_recap if dernier_recap else None
    
    @classmethod
    def get_mois_recap_suggere_pour_bailleur(cls, bailleur):
        """
        Suggère le mois de récapitulatif pour un bailleur en fonction de différents critères :
        1. Le mois suivant le dernier récapitulatif
        2. Le mois actuel si aucun récapitulatif n'existe
        3. Le mois actuel si le dernier récapitulatif est antérieur au mois actuel
        
        Args:
            bailleur: Instance du modèle Bailleur
            
        Returns:
            dict: Dictionnaire contenant le mois suggéré et des informations contextuelles
        """
        from datetime import date
        from dateutil.relativedelta import relativedelta
        
        mois_actuel = date.today().replace(day=1)
        dernier_mois = cls.get_dernier_mois_recap_pour_bailleur(bailleur)
        
        if dernier_mois is None:
            # Aucun récapitulatif existant
            mois_suggere = mois_actuel
            raison = "Aucun récapitulatif existant - suggestion du mois actuel"
        elif dernier_mois < mois_actuel:
            # Le dernier récapitulatif est antérieur au mois actuel
            mois_suggere = mois_actuel
            raison = f"Dernier récapitulatif ({dernier_mois.strftime('%B %Y')}) antérieur au mois actuel"
        else:
            # Le dernier récapitulatif est récent, suggérer le mois suivant
            mois_suggere = dernier_mois + relativedelta(months=1)
            raison = f"Mois suivant le dernier récapitulatif ({dernier_mois.strftime('%B %Y')})"
        
        # Vérifier si un récapitulatif existe déjà pour le mois suggéré
        recap_existant = cls.objects.filter(
            bailleur=bailleur,
            mois_recap=mois_suggere,
            is_deleted=False
        ).exists()
        
        return {
            'mois_suggere': mois_suggere,
            'raison': raison,
            'dernier_mois': dernier_mois,
            'mois_actuel': mois_actuel,
            'recap_existant': recap_existant,
            'mois_suggere_formate': mois_suggere.strftime('%B %Y')
        }


class RecapitulatifMensuelBailleur(models.Model):
    """Modèle pour le récapitulatif mensuel d'un bailleur individuel."""
    
    TYPE_RECAPITULATIF_CHOICES = [
        ('mensuel', 'Mensuel'),
        ('trimestriel', 'Trimestriel'),
        ('annuel', 'Annuel'),
        ('exceptionnel', 'Exceptionnel'),
    ]
    
    STATUT_CHOICES = [
        ('en_preparation', 'En préparation'),
        ('valide', 'Validé'),
        ('envoye', 'Envoyé au bailleur'),
        ('paye', 'Payé'),
        ('annule', 'Annulé'),
    ]
    
    # BAILLEUR INDIVIDUEL - C'EST ICI LA DIFFÉRENCE !
    bailleur = models.ForeignKey(
        'proprietes.Bailleur',
        on_delete=models.CASCADE,
        verbose_name=_("Bailleur"),
        related_name='recapitulatifs_mensuels_bailleur',
        help_text=_("Bailleur concerné par ce récapitulatif")
    )
    
    # Informations générales
    mois_recapitulatif = models.DateField(
        verbose_name=_("Mois du récapitulatif"),
        help_text=_("Mois de référence pour le récapitulatif")
    )
    type_recapitulatif = models.CharField(
        max_length=20,
        choices=TYPE_RECAPITULATIF_CHOICES,
        default='mensuel',
        verbose_name=_("Type de récapitulatif")
    )
    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='en_preparation',
        verbose_name=_("Statut")
    )
    
    # Dates importantes
    date_creation = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Date de création")
    )
    date_validation = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Date de validation")
    )
    date_envoi = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Date d'envoi au bailleur")
    )
    date_paiement = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Date de paiement")
    )
    
    # Informations de gestion
    gestionnaire = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Gestionnaire responsable"),
        related_name='recapitulatifs_crees'
    )
    notes = models.TextField(
        blank=True,
        verbose_name=_("Notes et observations")
    )
    
    # Métadonnées
    hash_securite = models.CharField(
        max_length=64,
        blank=True,
        verbose_name=_("Hash de sécurité")
    )
    version = models.CharField(
        max_length=10,
        default='1.0',
        verbose_name=_("Version du récapitulatif")
    )
    
    class Meta:
        verbose_name = _("Récapitulatif mensuel")
        verbose_name_plural = _("Récapitulatifs mensuels")
        ordering = ['-mois_recapitulatif', '-date_creation']
        unique_together = ['bailleur', 'mois_recapitulatif', 'type_recapitulatif']
        indexes = [
            models.Index(fields=['mois_recapitulatif', 'statut']),
            models.Index(fields=['gestionnaire', 'date_creation']),
        ]
    
    def __str__(self):
        return f"Récapitulatif {self.get_type_recapitulatif_display()} - {self.bailleur.nom} - {self.mois_recapitulatif.strftime('%B %Y')}"
    
    def get_nom_fichier_pdf(self):
        """Génère le nom du fichier PDF du récapitulatif."""
        return f"recapitulatif_{self.mois_recapitulatif.strftime('%Y_%m')}_{self.type_recapitulatif}.pdf"
    
    def calculer_totaux_bailleur(self):
        """Calcule les totaux pour le bailleur spécifique de ce récapitulatif."""
        from proprietes.models import ChargesBailleur
        from django.db.models import Sum
        
        # Calculer les totaux pour le bailleur spécifique
        details_bailleur = self.calculer_details_bailleur(self.bailleur)
        
        totaux = {
            'bailleur': self.bailleur,
            'nombre_proprietes': details_bailleur['nombre_proprietes'],
            'total_loyers_bruts': details_bailleur['total_loyers_bruts'],
            'total_charges_deductibles': details_bailleur['total_charges_deductibles'],
            'total_charges_bailleur': details_bailleur['total_charges_bailleur'],
            'total_net_a_payer': details_bailleur['montant_net_a_payer'],
            'details_proprietes': details_bailleur['proprietes_details']
        }
        
        return totaux
    
    def calculer_totaux_globaux(self):
        """Calcule les totaux globaux de tous les bailleurs."""
        from proprietes.models import ChargesBailleur
        from django.db.models import Sum
        
        # Calculer les totaux pour le bailleur spécifique
        details_bailleur = self.calculer_details_bailleur(self.bailleur)
        
        totaux = {
            'bailleur': self.bailleur,
            'nombre_proprietes': details_bailleur['nombre_proprietes'],
            'total_loyers_bruts': details_bailleur['total_loyers_bruts'],
            'total_charges_deductibles': details_bailleur['total_charges_deductibles'],
            'total_charges_bailleur': details_bailleur['total_charges_bailleur'],
            'total_net_a_payer': details_bailleur['montant_net_a_payer'],
            'details_proprietes': details_bailleur['proprietes_details']
        }
        
        return totaux
    
    def get_periode_calcul(self):
        """Retourne les dates de début et fin selon le type de récapitulatif."""
        from datetime import datetime, timedelta
        from dateutil.relativedelta import relativedelta
        
        date_debut = self.mois_recapitulatif.replace(day=1)
        
        if self.type_recapitulatif == 'mensuel':
            date_fin = date_debut + relativedelta(months=1) - timedelta(days=1)
        elif self.type_recapitulatif == 'trimestriel':
            # Calculer le trimestre
            trimestre = (date_debut.month - 1) // 3 + 1
            mois_debut_trimestre = (trimestre - 1) * 3 + 1
            date_debut = date_debut.replace(month=mois_debut_trimestre)
            date_fin = date_debut + relativedelta(months=3) - timedelta(days=1)
        elif self.type_recapitulatif == 'annuel':
            date_debut = date_debut.replace(month=1)
            date_fin = date_debut.replace(month=12, day=31)
        else:  # exceptionnel - utiliser le mois sélectionné
            date_fin = date_debut + relativedelta(months=1) - timedelta(days=1)
        
        return date_debut, date_fin
    
    def get_multiplicateur_periode(self):
        """Retourne le multiplicateur selon la période pour les loyers."""
        if self.type_recapitulatif == 'mensuel':
            return 1
        elif self.type_recapitulatif == 'trimestriel':
            return 3
        elif self.type_recapitulatif == 'annuel':
            return 12
        else:  # exceptionnel
            return 1
    
    def get_libelle_periode(self):
        """Retourne le libellé de la période selon le type."""
        if self.type_recapitulatif == 'mensuel':
            return f"Mensuel - {self.mois_recapitulatif.strftime('%B %Y')}"
        elif self.type_recapitulatif == 'trimestriel':
            trimestre = (self.mois_recapitulatif.month - 1) // 3 + 1
            return f"Trimestriel T{trimestre} - {self.mois_recapitulatif.year}"
        elif self.type_recapitulatif == 'annuel':
            return f"Annuel - {self.mois_recapitulatif.year}"
        else:  # exceptionnel
            return f"Exceptionnel - {self.mois_recapitulatif.strftime('%B %Y')}"


class QuittancePaiementBailleur(models.Model):
    """Quittance de paiement pour un retrait de bailleur."""
    
    STATUT_CHOICES = [
        ('en_attente', _('En attente')),
        ('generee', _('Générée')),
        ('envoyee', _('Envoyée')),
        ('imprimee', _('Imprimée')),
    ]
    
    # Informations de base
    retrait = models.OneToOneField(
        'RetraitBailleur', 
        on_delete=models.CASCADE, 
        related_name='quittance_paiement',
        verbose_name=_("Retrait lié")
    )
    numero_quittance = models.CharField(
        max_length=20, 
        unique=True, 
        verbose_name=_("Numéro de quittance")
    )
    
    # Informations du paiement
    montant_paye = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        verbose_name=_("Montant payé")
    )
    montant_en_lettres = models.CharField(
        max_length=500, 
        verbose_name=_("Montant en lettres")
    )
    mode_paiement = models.CharField(
        max_length=50, 
        verbose_name=_("Mode de paiement")
    )
    reference_paiement = models.CharField(
        max_length=100, 
        blank=True, 
        null=True, 
        verbose_name=_("Référence du paiement")
    )
    
    # Informations de la période
    mois_paye = models.CharField(
        max_length=50, 
        verbose_name=_("Mois payé")
    )
    montant_restant_due = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0, 
        verbose_name=_("Montant restant dû")
    )
    
    # Statut et dates
    statut = models.CharField(
        max_length=20, 
        choices=STATUT_CHOICES, 
        default='en_attente',
        verbose_name=_("Statut")
    )
    date_generation = models.DateTimeField(
        auto_now_add=True, 
        verbose_name=_("Date de génération")
    )
    date_envoi = models.DateTimeField(
        blank=True, 
        null=True, 
        verbose_name=_("Date d'envoi")
    )
    
    # Gestion
    cree_par = models.ForeignKey(
        'utilisateurs.Utilisateur', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='quittances_bailleur_creees',
        verbose_name=_("Créé par")
    )
    
    class Meta:
        verbose_name = _("Quittance de paiement bailleur")
        verbose_name_plural = _("Quittances de paiement bailleur")
        ordering = ['-date_generation']
        indexes = [
            models.Index(fields=['numero_quittance']),
            models.Index(fields=['statut', 'date_generation']),
        ]
    
    def __str__(self):
        return f"Quittance {self.numero_quittance} - {self.retrait.bailleur.get_nom_complet()}"
    
    def get_absolute_url(self):
        return reverse('paiements:quittance_bailleur_detail', kwargs={'pk': self.pk})
    
    def save(self, *args, **kwargs):
        if not self.numero_quittance:
            self.numero_quittance = self.generate_numero_quittance()
        super().save(*args, **kwargs)
    
    def generate_numero_quittance(self):
        """Génère un numéro de quittance unique."""
        from datetime import datetime
        now = datetime.now()
        # Format: Q + année + mois + jour + 3 chiffres aléatoires
        base = f"Q{now.year}{now.month:02d}{now.day:02d}"
        
        # Chercher le dernier numéro du jour
        last_quittance = QuittancePaiementBailleur.objects.filter(
            numero_quittance__startswith=base
        ).order_by('-numero_quittance').first()
        
        if last_quittance:
            try:
                last_number = int(last_quittance.numero_quittance[-3:])
                new_number = last_number + 1
            except (ValueError, IndexError):
                new_number = 1
        else:
            new_number = 1
        
        return f"{base}{new_number:03d}"
    
    def get_montant_formatted(self):
        """Retourne le montant formaté avec séparateurs."""
        return f"{self.montant_paye:,.0f} F CFA"
    
    def get_statut_color(self):
        """Retourne la couleur du statut."""
        colors = {
            'en_attente': 'secondary',
            'generee': 'info',
            'envoyee': 'success',
            'imprimee': 'primary',
        }
        return colors.get(self.statut, 'secondary')
    
    def get_statut_display_color(self):
        """Retourne le statut avec couleur Bootstrap."""
        color = self.get_statut_color()
        return f'<span class="badge bg-{color}">{self.get_statut_display()}</span>'

    def calculer_details_bailleur(self, bailleur):
        """Calcule les détails complets pour un bailleur spécifique selon la période."""
        from proprietes.models import ChargesBailleur
        from django.db.models import Sum
        
        # Propriétés louées du bailleur
        proprietes_louees = Propriete.objects.filter(
            bailleur=bailleur,
            contrats__est_actif=True
        ).distinct()
        
        from decimal import Decimal
        details = {
            'bailleur': bailleur,
            'nombre_proprietes': proprietes_louees.count(),
            'proprietes_details': [],
            'total_loyers_bruts': Decimal('0'),
            'total_charges_deductibles': Decimal('0'),
            'total_charges_bailleur': Decimal('0'),
            'montant_net_a_payer': Decimal('0'),
            'periode': self.get_libelle_periode(),
            'type_periode': self.type_recapitulatif,
            'multiplicateur': self.get_multiplicateur_periode()
        }
        
        # Obtenir les dates de la période
        date_debut, date_fin = self.get_periode_calcul()
        multiplicateur = Decimal(str(self.get_multiplicateur_periode()))
        
        for propriete in proprietes_louees:
            # Contrat actif de la propriété
            contrat_actif = propriete.contrats.filter(est_actif=True).first()
            if not contrat_actif:
                continue
            
            # CORRECTION : Utiliser le loyer mensuel du contrat au lieu des paiements reçus
            # Conversion sécurisée en Decimal
            loyer_mensuel_contrat = contrat_actif.loyer_mensuel
            if isinstance(loyer_mensuel_contrat, str):
                try:
                    loyer_mensuel_contrat = Decimal(loyer_mensuel_contrat)
                except (ValueError, TypeError):
                    loyer_mensuel_contrat = Decimal('0')
            elif isinstance(loyer_mensuel_contrat, (int, float)):
                loyer_mensuel_contrat = Decimal(str(loyer_mensuel_contrat))
            elif loyer_mensuel_contrat is None:
                loyer_mensuel_contrat = Decimal('0')
            
            # Calculer les loyers selon la période
            loyers_bruts = loyer_mensuel_contrat * multiplicateur
            
            # Loyers perçus pour la période (pour information)
            loyers_percus_periode = Paiement.objects.filter(
                contrat=contrat_actif,
                date_paiement__range=[date_debut, date_fin],
                statut='valide'
            ).aggregate(total=Sum('montant'))['total'] or Decimal('0')
            if not isinstance(loyers_percus_periode, Decimal):
                loyers_percus_periode = Decimal(str(loyers_percus_periode))
            
            # Charges déductibles (locataire) - basées sur le contrat
            charges_mensuelles_contrat = contrat_actif.charges_mensuelles
            if isinstance(charges_mensuelles_contrat, str):
                try:
                    charges_mensuelles_contrat = Decimal(charges_mensuelles_contrat)
                except (ValueError, TypeError):
                    charges_mensuelles_contrat = Decimal('0')
            elif isinstance(charges_mensuelles_contrat, (int, float)):
                charges_mensuelles_contrat = Decimal(str(charges_mensuelles_contrat))
            elif charges_mensuelles_contrat is None:
                charges_mensuelles_contrat = Decimal('0')
            
            # Calculer les charges selon la période
            charges_contrat_periode = charges_mensuelles_contrat * multiplicateur
            
            # Charges déductibles supplémentaires pour la période
            charges_deductibles_supplementaires = ChargeDeductible.objects.filter(
                contrat__propriete=propriete,
                date_charge__range=[date_debut, date_fin],
                statut='validee'
            ).aggregate(total=Sum('montant'))['total'] or Decimal('0')
            if not isinstance(charges_deductibles_supplementaires, Decimal):
                charges_deductibles_supplementaires = Decimal(str(charges_deductibles_supplementaires))
            
            # Total des charges déductibles
            charges_deductibles = charges_contrat_periode + charges_deductibles_supplementaires
            
            # Charges bailleur pour la période
            charges_bailleur = ChargesBailleur.objects.filter(
                propriete=propriete,
                date_charge__range=[date_debut, date_fin],
                statut__in=['en_attente', 'deduite_retrait']
            ).aggregate(total=Sum('montant_restant'))['total'] or Decimal('0')
            if not isinstance(charges_bailleur, Decimal):
                charges_bailleur = Decimal(str(charges_bailleur))
            
            # Calcul du montant net pour cette propriété
            montant_net_propriete = loyers_bruts - charges_deductibles - charges_bailleur
            
            propriete_detail = {
                'propriete': propriete,
                'contrat': contrat_actif,
                'loyers_bruts': loyers_bruts,
                'loyers_percus': loyers_percus_periode,  # Pour information
                'charges_deductibles': charges_deductibles,
                'charges_bailleur': charges_bailleur,
                'montant_net': montant_net_propriete,
                'locataire': contrat_actif.locataire,
                'loyer_mensuel_base': loyer_mensuel_contrat,
                'charges_mensuelles_base': charges_mensuelles_contrat,
                'multiplicateur': multiplicateur
            }
            
            details['proprietes_details'].append(propriete_detail)
            details['total_loyers_bruts'] += loyers_bruts
            details['total_charges_deductibles'] += charges_deductibles
            details['total_charges_bailleur'] += charges_bailleur
            details['montant_net_a_payer'] += montant_net_propriete
        
        return details
    
    def generer_pdf_recapitulatif(self):
        """Génère le PDF du récapitulatif mensuel."""
        from django.template.loader import render_to_string
        from xhtml2pdf import pisa
        import tempfile
        import os
        from io import BytesIO
        
        # Récupérer les totaux globaux
        totaux = self.calculer_totaux_globaux()
        
        # Rendre le template HTML
        html_content = render_to_string(
            'paiements/recapitulatifs/recapitulatif_mensuel_pdf.html',
            {
                'recapitulatif': self,
                'totaux': totaux,
                'date_generation': timezone.now(),
            }
        )
        
        # Créer le PDF avec xhtml2pdf
        pdf_buffer = BytesIO()
        pisa_status = pisa.CreatePDF(html_content, dest=pdf_buffer)
        
        if pisa_status.err:
            raise Exception(f"Erreur lors de la génération du PDF: {pisa_status.err}")
        
        pdf_content = pdf_buffer.getvalue()
        pdf_buffer.close()
        
        return pdf_content
    
    def valider(self, gestionnaire):
        """Valide le récapitulatif mensuel."""
        if self.statut != 'en_preparation':
            raise ValueError("Seul un récapitulatif en préparation peut être validé")
        
        self.statut = 'valide'
        self.date_validation = timezone.now()
        self.gestionnaire = gestionnaire
        self.save()
        
        # Générer le hash de sécurité
        self.generer_hash_securite()
        
        return True
    
    def envoyer_au_bailleur(self):
        """Marque le récapitulatif comme envoyé au bailleur."""
        if self.statut != 'valide':
            raise ValueError("Seul un récapitulatif validé peut être envoyé")
        
        self.statut = 'envoye'
        self.date_envoi = timezone.now()
        self.save()
        
        return True
    
    def marquer_comme_paye(self):
        """Marque le récapitulatif comme payé."""
        if self.statut not in ['envoye', 'valide']:
            raise ValueError("Seul un récapitulatif envoyé ou validé peut être marqué comme payé")
        
        self.statut = 'paye'
        self.date_paiement = timezone.now()
        self.save()
        
        return True
    
    def generer_hash_securite(self):
        """Génère un hash de sécurité pour vérifier l'intégrité."""
        import hashlib
        
        # Créer une chaîne de données pour le hash
        data_string = f"{self.id}_{self.mois_recapitulatif}_{self.type_recapitulatif}_{self.date_creation}"
        
        # Générer le hash SHA-256
        hash_object = hashlib.sha256(data_string.encode())
        self.hash_securite = hash_object.hexdigest()
        self.save()
    
    def verifier_integrite(self):
        """Vérifie l'intégrité du récapitulatif avec le hash de sécurité."""
        if not self.hash_securite:
            return False
        
        # Régénérer le hash pour comparaison
        import hashlib
        data_string = f"{self.id}_{self.mois_recapitulatif}_{self.type_recapitulatif}_{self.date_creation}"
        hash_object = hashlib.sha256(data_string.encode())
        hash_calcule = hash_object.hexdigest()
        
        return self.hash_securite == hash_calcule
    
    def get_statut_display_color(self):
        """Retourne la couleur CSS pour le statut."""
        colors = {
            'en_preparation': 'warning',
            'valide': 'success',
            'envoye': 'info',
            'paye': 'success',
            'annule': 'danger',
        }
        return colors.get(self.statut, 'secondary')
    
    def peut_etre_modifie(self):
        """Vérifie si le récapitulatif peut être modifié."""
        return self.statut in ['en_preparation']
    
    def peut_etre_valide(self):
        """Vérifie si le récapitulatif peut être validé."""
        return self.statut == 'en_preparation'
    
    def peut_etre_envoye(self):
        """Vérifie si le récapitulatif peut être envoyé."""
        return self.statut == 'valide'
    
    def peut_etre_paye(self):
        """Vérifie si le récapitulatif peut être marqué comme payé."""
        return self.statut in ['envoye', 'valide']


# Temporairement commenté pour résoudre le problème de migration
# class Recu(models.Model):
#     """Modèle pour les reçus de paiement générés automatiquement."""
#     
#     # Numéro unique du reçu
#     numero_recu = models.CharField(
#         max_length=50,
#         unique=True,
#         verbose_name=_("Numéro de reçu"),
#         help_text=_("Numéro unique du reçu")
#     )
#     
#     # Paiement associé
#     paiement = models.OneToOneField(
#         Paiement,
#         on_delete=models.CASCADE,
#         related_name='recu',
#         verbose_name=_("Paiement")
#     )
#     
#     # Template utilisé
#     template_utilise = models.CharField(
#         max_length=20,
#         choices=[
#             ('standard', 'Standard'),
#             ('simplified', 'Simplifié'),
#             ('detailed', 'Détaillé'),
#             ('professionnel', 'Professionnel'),
#             ('luxe', 'Luxe'),
#             ('entreprise', 'Entreprise'),
#         ],
#         default='standard',
#         verbose_name=_("Template utilisé")
#     )
#     
#     # Format d'impression
#     format_impression = models.CharField(
#         max_length=20,
#         choices=[
#             ('A4', 'A4'),
#             ('A5', 'A5'),
#             ('lettre', 'Lettre'),
#             ('personnalise', 'Personnalisé'),
#         ],
#         default='A4',
#         verbose_name=_("Format d'impression")
#     )
#     
#     # Statut du reçu
#     valide = models.BooleanField(
#         default=True,
#         verbose_name=_("Reçu validé")
#     )
#     
#     # Informations d'impression
#     imprime = models.BooleanField(
#         default=False,
#         verbose_name=_("Reçu imprimé")
#     )
#     date_impression = models.DateTimeField(
#         null=True,
#         blank=True,
#         verbose_name=_("Date d'impression")
#     )
#     imprime_par = models.ForeignKey(
#         'utilisateurs.Utilisateur',
#         on_delete=models.SET_NULL,
#         null=True,
#         blank=True,
#         related_name='recus_imprimes',
#         verbose_name=_("Imprimé par")
#     )
#     nombre_impressions = models.PositiveIntegerField(
#         default=0,
#         verbose_name=_("Nombre d'impressions")
#     )
#     
#     # Métadonnées
#     date_creation = models.DateTimeField(
#         auto_now_add=True,
#         verbose_name=_("Date de création")
#     )
#     cree_par = models.ForeignKey(
#         'utilisateurs.Utilisateur',
#         on_delete=models.SET_NULL,
#         null=True,
#         blank=True,
#         related_name='recus_crees',
#         verbose_name=_("Créé par")
#     )
#     
#     class Meta:
#         verbose_name = _("Reçu de paiement")
#         verbose_name_plural = _("Reçus de paiement")
#         ordering = ['-date_creation']
#     
#     def __str__(self):
#         return f"Reçu {self.numero_recu} - {self.paiement.contrat.locataire.get_nom_complet()}"
#     
#     def marquer_imprime(self, utilisateur):
#         """Marque le reçu comme imprimé."""
#         self.imprime = True
#         self.date_impression = timezone.now()
#         self.imprime_par = utilisateur
#         self.nombre_impressions += 1
#         self.save()


class RecuRecapitulatif(models.Model):
    """Modèle pour les reçus de récapitulatifs mensuels - PROFESSIONNEL."""
    
    # Numéro unique du reçu
    numero_recu = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_("Numéro de reçu"),
        help_text=_("Numéro unique du reçu de récapitulatif")
    )
    
    # Récapitulatif associé
    recapitulatif = models.OneToOneField(
        RecapitulatifMensuelBailleur,
        on_delete=models.CASCADE,
        related_name='recu',
        verbose_name=_("Récapitulatif")
    )
    
    # Type de reçu
    type_recu = models.CharField(
        max_length=20,
        choices=[
            ('recapitulatif', 'Récapitulatif'),
            ('quittance', 'Quittance'),
            ('attestation', 'Attestation'),
            ('releve', 'Relevé'),
            ('facture', 'Facture'),
        ],
        default='recapitulatif',
        verbose_name=_("Type de reçu")
    )
    
    # Template utilisé
    template_utilise = models.CharField(
        max_length=20,
        choices=[
            ('professionnel', 'Professionnel'),
            ('entreprise', 'Entreprise'),
            ('luxe', 'Luxe'),
            ('standard', 'Standard'),
            ('gestimmob', 'GESTIMMOB'),
        ],
        default='professionnel',
        verbose_name=_("Template utilisé")
    )
    
    # Format d'impression
    format_impression = models.CharField(
        max_length=20,
        choices=[
            ('A4_paysage', 'A4 Paysage'),
            ('A4_portrait', 'A4 Portrait'),
            ('A3_paysage', 'A3 Paysage'),
            ('lettre_paysage', 'Lettre Paysage'),
        ],
        default='A4_paysage',
        verbose_name=_("Format d'impression")
    )
    
    # Statut du reçu
    statut = models.CharField(
        max_length=20,
        choices=[
            ('brouillon', 'Brouillon'),
            ('valide', 'Validé'),
            ('imprime', 'Imprimé'),
            ('envoye', 'Envoyé'),
            ('archive', 'Archivé'),
        ],
        default='brouillon',
        verbose_name=_("Statut du reçu")
    )
    
    # Informations d'impression
    imprime = models.BooleanField(
        default=False,
        verbose_name=_("Reçu imprimé")
    )
    date_impression = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Date d'impression")
    )
    imprime_par = models.ForeignKey(
        'utilisateurs.Utilisateur',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recus_recapitulatifs_imprimes',
        verbose_name=_("Imprimé par")
    )
    nombre_impressions = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Nombre d'impressions")
    )
    
    # Informations d'envoi
    envoye = models.BooleanField(
        default=False,
        verbose_name=_("Reçu envoyé")
    )
    date_envoi = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Date d'envoi")
    )
    mode_envoi = models.CharField(
        max_length=20,
        choices=[
            ('email', 'Email'),
            ('courrier', 'Courrier'),
            ('remise_main', 'Remise en main propre'),
            ('fax', 'Fax'),
        ],
        blank=True,
        verbose_name=_("Mode d'envoi")
    )
    
    # Métadonnées
    date_creation = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Date de création")
    )
    cree_par = models.ForeignKey(
        'utilisateurs.Utilisateur',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recus_recapitulatifs_crees',
        verbose_name=_("Créé par")
    )
    
    # Hash de sécurité
    hash_securite = models.CharField(
        max_length=64,
        blank=True,
        verbose_name=_("Hash de sécurité")
    )
    
    # Notes
    notes = models.TextField(
        blank=True,
        verbose_name=_("Notes")
    )
    
    class Meta:
        verbose_name = _("Reçu de récapitulatif")
        verbose_name_plural = _("Reçus de récapitulatifs")
        ordering = ['-date_creation']
        indexes = [
            models.Index(fields=['numero_recu']),
            models.Index(fields=['statut', 'date_creation']),
            models.Index(fields=['recapitulatif', 'type_recu']),
        ]
    
    def __str__(self):
        return f"Reçu {self.numero_recu} - {self.recapitulatif.bailleur.get_nom_complet()}"
    
    def save(self, *args, **kwargs):
        if not self.numero_recu:
            self.numero_recu = self.generer_numero_recu()
        super().save(*args, **kwargs)
    
    def generer_numero_recu(self):
        """Génère un numéro de reçu unique."""
        from datetime import datetime
        import random
        
        # Format: REC-YYYYMMDD-XXXX
        date_str = datetime.now().strftime('%Y%m%d')
        random_num = random.randint(1000, 9999)
        numero = f"REC-{date_str}-{random_num}"
        
        # Vérifier l'unicité
        while RecuRecapitulatif.objects.filter(numero_recu=numero).exists():
            random_num = random.randint(1000, 9999)
            numero = f"REC-{date_str}-{random_num}"
        
        return numero
    
    def marquer_imprime(self, utilisateur):
        """Marque le reçu comme imprimé."""
        self.imprime = True
        self.date_impression = timezone.now()
        self.imprime_par = utilisateur
        self.nombre_impressions += 1
        self.statut = 'imprime'
        self.save()
    
    def marquer_envoye(self, mode_envoi):
        """Marque le reçu comme envoyé."""
        self.envoye = True
        self.date_envoi = timezone.now()
        self.mode_envoi = mode_envoi
        self.statut = 'envoye'
        self.save()
    
    def generer_hash_securite(self):
        """Génère un hash de sécurité pour le reçu."""
        import hashlib
        
        data = f"{self.numero_recu}{self.recapitulatif.pk}{self.date_creation.isoformat()}"
        self.hash_securite = hashlib.sha256(data.encode()).hexdigest()
        self.save()
    
    def get_absolute_url(self):
        return reverse('paiements:detail_recu_recapitulatif', kwargs={'pk': self.pk})


# =============================================================================
# MODÈLES POUR LES RETRAITS AUX BAILLEURS
# =============================================================================

class RetraitBailleur(models.Model):
    """
    Modèle pour les retraits aux bailleurs
    """
    STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('valide', 'Validé'),
        ('paye', 'Payé'),
        ('annule', 'Annulé'),
    ]
    
    TYPE_RETRAIT_CHOICES = [
        ('mensuel', 'Retrait mensuel'),
        ('trimestriel', 'Retrait trimestriel'),
        ('annuel', 'Retrait annuel'),
        ('exceptionnel', 'Retrait exceptionnel'),
    ]
    
    MODE_RETRAIT_CHOICES = [
        ('virement', 'Virement bancaire'),
        ('cheque', 'Chèque'),
        ('especes', 'Espèces'),
    ]
    
    # Relations
    bailleur = models.ForeignKey(
        'proprietes.Bailleur',
        on_delete=models.CASCADE,
        verbose_name=_("Bailleur"),
        related_name='retraits'
    )
    
    # Informations de base
    mois_retrait = models.DateField(
        verbose_name=_("Mois de retrait"),
        help_text=_("Mois pour lequel le retrait est effectué")
    )
    
    # Montants
    montant_loyers_bruts = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name=_("Montant des loyers bruts")
    )
    
    montant_charges_deductibles = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name=_("Montant des charges déductibles")
    )
    
    montant_charges_bailleur = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name=_("Montant des charges bailleur")
    )
    
    montant_net_a_payer = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name=_("Montant net à payer")
    )
    
    # Configuration
    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='en_attente',
        verbose_name=_("Statut")
    )
    
    type_retrait = models.CharField(
        max_length=20,
        choices=TYPE_RETRAIT_CHOICES,
        default='mensuel',
        verbose_name=_("Type de retrait")
    )
    
    mode_retrait = models.CharField(
        max_length=20,
        choices=MODE_RETRAIT_CHOICES,
        default='virement',
        verbose_name=_("Mode de retrait")
    )
    
    # Dates
    date_demande = models.DateField(
        auto_now_add=True,
        verbose_name=_("Date de demande")
    )
    
    date_validation = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Date de validation")
    )
    
    date_paiement = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Date de paiement")
    )
    
    # Utilisateurs
    cree_par = models.ForeignKey(
        'utilisateurs.Utilisateur',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='retraits_crees',
        verbose_name=_("Créé par")
    )
    
    valide_par = models.ForeignKey(
        'utilisateurs.Utilisateur',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='retraits_valides',
        verbose_name=_("Validé par")
    )
    
    # Métadonnées
    notes = models.TextField(
        blank=True,
        verbose_name=_("Notes")
    )
    
    is_deleted = models.BooleanField(
        default=False,
        verbose_name=_("Supprimé")
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Date de création")
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Date de modification")
    )
    
    class Meta:
        verbose_name = _("Retrait bailleur")
        verbose_name_plural = _("Retraits bailleur")
        ordering = ['-mois_retrait', '-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['bailleur', 'mois_retrait'],
                condition=models.Q(is_deleted=False),
                name='unique_retrait_actif_per_bailleur_month'
            )
        ]
        indexes = [
            models.Index(fields=['bailleur', 'mois_retrait']),
            models.Index(fields=['statut']),
            models.Index(fields=['date_demande']),
        ]
    
    def __str__(self):
        return f"Retrait {self.mois_retrait.strftime('%B %Y')} - {self.bailleur.get_nom_complet()}"
    
    def get_nom_complet(self):
        """Retourne le nom complet du bailleur"""
        return self.bailleur.get_nom_complet()
    
    def calculer_montant_net(self):
        """Calcule le montant net à payer"""
        net = self.montant_loyers_bruts - self.montant_charges_deductibles - self.montant_charges_bailleur
        self.montant_net_a_payer = max(net, Decimal('0'))
        return self.montant_net_a_payer
    
    def valider(self, user):
        """Valide le retrait"""
        self.statut = 'valide'
        self.date_validation = date.today()
        self.valide_par = user
        self.save()
    
    def marquer_paye(self, user):
        """Marque le retrait comme payé"""
        self.statut = 'paye'
        self.date_paiement = date.today()
        self.save()
    
    def annuler(self, user):
        """Annule le retrait"""
        self.statut = 'annule'
        self.save()


class RetraitQuittance(models.Model):
    """
    Modèle pour les quittances de retrait
    """
    retrait = models.OneToOneField(
        RetraitBailleur,
        on_delete=models.CASCADE,
        related_name='quittance',
        verbose_name=_("Retrait")
    )
    
    numero_quittance = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_("Numéro de quittance")
    )
    
    date_emission = models.DateField(
        auto_now_add=True,
        verbose_name=_("Date d'émission")
    )
    
    cree_par = models.ForeignKey(
        'utilisateurs.Utilisateur',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Créé par")
    )
    
    # Métadonnées
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Date de création")
    )
    
    class Meta:
        verbose_name = _("Quittance de retrait")
        verbose_name_plural = _("Quittances de retrait")
        ordering = ['-date_emission']
    
    def __str__(self):
        return f"Quittance {self.numero_quittance} - {self.retrait.get_nom_complet()}"
    
    def generer_numero(self):
        """Génère un numéro de quittance unique"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"QUI-{timestamp}-{self.retrait.id}"
    
    def save(self, *args, **kwargs):
        if not self.numero_quittance:
            self.numero_quittance = self.generer_numero()
        super().save(*args, **kwargs)
