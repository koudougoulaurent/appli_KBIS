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
    
    # Garanties financières
    total_cautions_requises = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name=_("Total des cautions requises"))
    total_avances_requises = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name=_("Total des avances requises"))
    total_cautions_versees = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name=_("Total des cautions versées"))
    total_avances_versees = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name=_("Total des avances versées"))
    garanties_suffisantes = models.BooleanField(default=True, verbose_name=_("Garanties financières suffisantes"))
    
    # Statut et workflow
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='brouillon', verbose_name=_("Statut"))
    
    # Métadonnées
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name=_("Date de création"))
    cree_par = models.ForeignKey('utilisateurs.Utilisateur', on_delete=models.SET_NULL, null=True, blank=True, related_name='recaps_mensuels_crees', verbose_name=_("Créé par"))
    date_modification = models.DateTimeField(auto_now=True, verbose_name=_("Date de modification"))
    modifie_par = models.ForeignKey('utilisateurs.Utilisateur', on_delete=models.SET_NULL, null=True, blank=True, related_name='recaps_mensuels_modifies', verbose_name=_("Modifié par"))
    
    # Relations
    paiements_concernes = models.ManyToManyField('Paiement', related_name='recaps_mensuels', verbose_name=_("Paiements concernés"), blank=True)
    charges_deductibles = models.ManyToManyField('ChargeDeductible', related_name='recaps_mensuels', verbose_name=_("Charges déductibles"), blank=True)
    
    # Suppression logique
    is_deleted = models.BooleanField(default=False, verbose_name=_("Supprimé logiquement"))
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Date de suppression"))
    deleted_by = models.ForeignKey('utilisateurs.Utilisateur', on_delete=models.SET_NULL, null=True, blank=True, related_name='recaps_mensuels_supprimes', verbose_name=_("Supprimé par"))
    
    class Meta:
        app_label = 'paiements'
        verbose_name = _("Récapitulatif mensuel")
        verbose_name_plural = _("Récapitulatifs mensuels")
        ordering = ['-mois_recap', 'bailleur__nom']
        unique_together = ['bailleur', 'mois_recap']
        indexes = [
            models.Index(fields=['mois_recap', 'bailleur']),
            models.Index(fields=['statut', 'mois_recap']),
        ]
    
    def __str__(self):
        return f"Récapitulatif {self.bailleur.get_nom_complet()} - {self.mois_recap.strftime('%B %Y')}"
    
    def get_absolute_url(self):
        return reverse('paiements:detail_recap_mensuel_auto', kwargs={'recap_id': self.pk})
    
    @staticmethod
    def get_mois_recap_suggere_pour_bailleur(bailleur):
        """Retourne le mois suggéré pour le prochain récapitulatif."""
        from datetime import date
        from dateutil.relativedelta import relativedelta
        
        # Récupérer le dernier récapitulatif du bailleur
        dernier_recap = RecapMensuel.objects.filter(
            bailleur=bailleur,
            is_deleted=False
        ).order_by('-mois_recap').first()
        
        if dernier_recap:
            # Retourner le mois suivant le dernier récapitulatif
            return dernier_recap.mois_recap + relativedelta(months=1)
        else:
            # Retourner le mois précédent si aucun récapitulatif n'existe
            return date.today().replace(day=1) - relativedelta(months=1)
    
    def calculer_totaux_bailleur(self):
        """Calcule les totaux pour le bailleur avec les charges dynamiques."""
        from decimal import Decimal
        from django.db.models import Sum
        from proprietes.models import ChargesBailleur
        
        try:
            # Initialiser les totaux
            total_loyers = Decimal('0')
            total_charges_deductibles = Decimal('0')
            total_charges_bailleur = Decimal('0')
            nombre_proprietes = 0
            nombre_contrats_actifs = 0
            nombre_paiements_recus = 0
            
            # Récupérer les propriétés du bailleur
            proprietes = self.bailleur.proprietes.filter(is_deleted=False)
            nombre_proprietes = proprietes.count()
            
            # Calculer les loyers bruts pour le mois
            for propriete in proprietes:
                # Récupérer les contrats actifs pour cette propriété
                contrats_actifs = propriete.contrats.filter(
                    est_actif=True,
                    date_debut__lte=self.mois_recap,
                    date_fin__gte=self.mois_recap
                )
                
                for contrat in contrats_actifs:
                    nombre_contrats_actifs += 1
                    # Loyer mensuel
                    loyer_mensuel = contrat.loyer_mensuel or Decimal('0')
                    total_loyers += loyer_mensuel
                    
                    # Charges déductibles du contrat
                    charges_mensuelles = contrat.charges_mensuelles or Decimal('0')
                    total_charges_deductibles += charges_mensuelles
            
            # Calculer les charges bailleur pour le mois
            charges_bailleur_mois = ChargesBailleur.objects.filter(
                propriete__bailleur=self.bailleur,
                date_charge__year=self.mois_recap.year,
                date_charge__month=self.mois_recap.month,
                statut__in=['en_attente', 'deduite_retrait']
            )
            
            for charge in charges_bailleur_mois:
                total_charges_bailleur += charge.montant_restant or charge.montant
            
            # Calculer le total net
            total_net = total_loyers - total_charges_deductibles - total_charges_bailleur
            
            # Mettre à jour les champs
            self.total_loyers_bruts = total_loyers
            self.total_charges_deductibles = total_charges_deductibles
            self.total_charges_bailleur = total_charges_bailleur
            self.total_net_a_payer = max(total_net, Decimal('0'))
            self.nombre_proprietes = nombre_proprietes
            self.nombre_contrats_actifs = nombre_contrats_actifs
            self.nombre_paiements_recus = nombre_paiements_recus
            
            # Sauvegarder les modifications
            self.save()
            
        except Exception as e:
            # En cas d'erreur, utiliser les valeurs par défaut
            total_loyers = Decimal('0')
            total_charges_deductibles = Decimal('0')
            total_charges_bailleur = Decimal('0')
            nombre_proprietes = 0
            nombre_contrats_actifs = 0
            nombre_paiements_recus = 0
            total_net = Decimal('0')
        
        return {
            'total_loyers_bruts': total_loyers,
            'total_charges_deductibles': total_charges_deductibles,
            'total_charges_bailleur': total_charges_bailleur,
            'total_net_a_payer': max(total_net, Decimal('0')),
            'nombre_proprietes': nombre_proprietes,
            'nombre_contrats_actifs': nombre_contrats_actifs,
            'nombre_paiements_recus': nombre_paiements_recus,
        }
    
    def calculer_charges_bailleur_disponibles(self):
        """Calcule les charges bailleur disponibles pour ce mois."""
        from django.db.models import Sum
        from decimal import Decimal
        
        # Récupérer les charges validées et non utilisées pour ce mois
        charges_disponibles = ChargeBailleur.objects.filter(
            bailleur=self.bailleur,
            mois_charge__year=self.mois_recap.year,
            mois_charge__month=self.mois_recap.month,
            statut='valide'
        ).aggregate(total=Sum('montant'))['total'] or Decimal('0')
        
        return charges_disponibles


class ChargeDeductible(models.Model):
    """Modèle pour les charges avancées par le locataire et déductibles du loyer."""
    
    # Informations de base
    contrat = models.ForeignKey(
        Contrat,
        on_delete=models.CASCADE,
        related_name='charges_deductibles',
        verbose_name=_("Contrat")
    )
    
    # Détails de la charge
    description = models.CharField(
        max_length=200,
        verbose_name=_("Description de la charge")
    )
    montant = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        verbose_name=_("Montant de la charge")
    )
    date_charge = models.DateField(
        verbose_name=_("Date de la charge")
    )
    
    # Statut
    est_deductible_loyer = models.BooleanField(
        default=True,
        verbose_name=_("Déductible du loyer")
    )
    est_valide = models.BooleanField(
        default=False,
        verbose_name=_("Validé")
    )
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)
    
    objects = NonDeletedManager()
    all_objects = models.Manager()
    
    class Meta:
        app_label = 'paiements'
        verbose_name = _("Charge déductible")
        verbose_name_plural = _("Charges déductibles")
        ordering = ['-date_charge']
    
    def __str__(self):
        return f"{self.description} - {self.montant} F CFA"


class Paiement(models.Model):
    """Modèle pour les paiements de loyer avec support des paiements partiels."""
    
    # Relations
    contrat = models.ForeignKey(
        Contrat,
        on_delete=models.CASCADE,
        related_name='paiements',
        verbose_name=_("Contrat")
    )
    
    # Montants
    montant = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        verbose_name=_("Montant payé")
    )
    montant_charges_deduites = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_("Montant des charges déduites")
    )
    montant_net_paye = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Montant net payé")
    )
    
    # Type et mode de paiement
    type_paiement = models.CharField(
        max_length=20,
        choices=[
            ('loyer', 'Loyer'),
            ('caution', 'Caution'),
            ('avance', 'Avance'),
            ('charges', 'Charges'),
        ],
        default='loyer',
        verbose_name=_("Type de paiement")
    )
    mode_paiement = models.CharField(
        max_length=20,
        choices=[
            ('especes', 'Espèces'),
            ('cheque', 'Chèque'),
            ('virement', 'Virement'),
            ('mobile_money', 'Mobile Money'),
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
    
    # Statut
    statut = models.CharField(
        max_length=20,
        choices=[
            ('en_attente', 'En attente'),
            ('valide', 'Validé'),
            ('refuse', 'Refusé'),
            ('annule', 'Annulé'),
        ],
        default='en_attente',
        verbose_name=_("Statut")
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
        verbose_name=_("Référence du virement")
    )
    
    # Notes
    notes = models.TextField(
        blank=True,
        verbose_name=_("Notes"),
        help_text=_("Notes ou commentaires sur le paiement")
    )
    
    # Validation
    valide_par = models.ForeignKey(
        'utilisateurs.Utilisateur',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='paiements_valides',
        verbose_name=_("Validé par")
    )
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(
        'utilisateurs.Utilisateur',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='paiement_deleted',
        verbose_name=_("Supprimé par")
    )
    
    objects = NonDeletedManager()
    all_objects = models.Manager()
    
    class Meta:
        app_label = 'paiements'
        verbose_name = _("Paiement")
        verbose_name_plural = _("Paiements")
        ordering = ['-date_paiement']
    
    def __str__(self):
        return f"Paiement {self.montant} F CFA - {self.contrat.locataire.get_nom_complet()}"
    
    def get_statut_color(self):
        """Retourne la couleur Bootstrap pour le statut"""
        colors = {
            'en_attente': 'warning',
            'valide': 'success',
            'refuse': 'danger',
            'annule': 'secondary',
        }
        return colors.get(self.statut, 'secondary')
    
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
                'montant': float(self.montant),
                'mois_regle': self._obtenir_mois_regle(),
                'type_paiement': self.get_type_paiement_display(),
                'mode_paiement': self.get_mode_paiement_display(),
                'quartier': quartier,
            }
            
            # Ajouter des données spécialisées selon le type
            donnees_quittance.update(self._ajouter_donnees_specialisees_quittance(type_quittance))
            
            # Générer le document unifié
            return DocumentKBISUnifie.generer_document_unifie(donnees_quittance, type_quittance)
            
        except Exception as e:
            print(f"Erreur génération quittance KBIS: {e}")
            return None
    
    def _determiner_type_quittance_paiement(self):
        """Détermine le type de quittance selon le type de paiement"""
        mapping = {
            'loyer': 'quittance_loyer',
            'caution': 'quittance_caution',
            'avance': 'quittance_avance',
            'charges': 'quittance_charges',
            'autre': 'quittance',
        }
        return mapping.get(self.type_paiement, 'quittance')
    
    def _obtenir_mois_regle(self):
        """Obtient le mois réglé formaté"""
        if self.date_paiement:
            mois_francais = [
                'janvier', 'février', 'mars', 'avril', 'mai', 'juin',
                'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre'
            ]
            return f"{mois_francais[self.date_paiement.month - 1]} {self.date_paiement.year}"
        return datetime.now().strftime('%B %Y')
    
    def _ajouter_donnees_specialisees_quittance(self, type_quittance):
        """Ajoute des données spécialisées selon le type de quittance"""
        donnees_speciales = {}
        
        if type_quittance == 'quittance_loyer':
            try:
                donnees_speciales.update({
                    'loyer_base': float(self.contrat.loyer_mensuel) if self.contrat else 0,
                    'charges_mensuelles': float(self.contrat.charges_mensuelles) if self.contrat else 0,
                    'total_mensuel': float(self.montant),
                    'restant_du': 0,  # À calculer selon la logique métier
                    'loyer_au_prorata': 0,  # À calculer selon la logique métier
                })
            except:
                donnees_speciales.update({
                    'loyer_base': float(self.montant),
                    'charges_mensuelles': 0,
                    'total_mensuel': float(self.montant),
                    'restant_du': 0,
                    'loyer_au_prorata': 0,
                })
        
        elif type_quittance == 'quittance_caution':
            try:
                donnees_speciales.update({
                    'montant_caution': float(self.montant),
                    'note_speciale': 'Dépôt de garantie - Remboursable en fin de bail',
                })
            except:
                donnees_speciales.update({
                    'montant_caution': float(self.montant),
                    'note_speciale': 'Dépôt de garantie',
                })
        
        elif type_quittance == 'quittance_avance':
            try:
                donnees_speciales.update({
                    'montant_avance': float(self.montant),
                    'loyer_mensuel': float(self.contrat.loyer_mensuel) if self.contrat else 0,
                    'note_speciale': 'Cette avance sera déduite du prochain loyer',
                })
            except:
                donnees_speciales.update({
                    'montant_avance': float(self.montant),
                    'loyer_mensuel': 0,
                    'note_speciale': 'Avance de loyer',
                })
        
        elif type_quittance == 'quittance_charges':
            donnees_speciales.update({
                'type_charges': 'Charges mensuelles',
                'montant_charges': float(self.montant),
                'note_speciale': 'Charges communes et services',
            })
        
        return donnees_speciales
    
    def _generer_recu_kbis_dynamique(self):
        """Génère un récépissé KBIS dynamique avec le format correct."""
        import sys
        import os
        from datetime import datetime
        
        try:
            # Utiliser le système unifié
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from document_kbis_unifie import DocumentKBISUnifie
            
            # Déterminer le type de récépissé selon le type de paiement
            type_recu = self._determiner_type_recu_paiement()
            
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
            
            # Générer un numéro de récépissé unique au format KBIS
            numero_recu = f"REC-{datetime.now().strftime('%Y%m%d%H%M%S')}-{self.id if self.id else 'X1DZ'}"
            
            # Données du récépissé
            donnees_recu = {
                'numero': numero_recu,
                'date': self.date_paiement.strftime('%d-%b-%y') if self.date_paiement else datetime.now().strftime('%d-%b-%y'),
                'code_location': code_location,
                'recu_de': recu_de,
                'montant': float(self.montant),
                'mois_regle': self._obtenir_mois_regle(),
                'type_paiement': self.get_type_paiement_display(),
                'mode_paiement': self.get_mode_paiement_display(),
                'quartier': quartier,
            }
            
            # Ajouter des données spécialisées selon le type
            donnees_recu.update(self._ajouter_donnees_specialisees_recu(type_recu))
            
            # Générer le document unifié
            return DocumentKBISUnifie.generer_document_unifie(donnees_recu, type_recu)
            
        except Exception as e:
            print(f"Erreur génération récépissé KBIS: {e}")
            return None
    
    def _determiner_type_recu_paiement(self):
        """Détermine le type de récépissé selon le type de paiement"""
        mapping = {
            'loyer': 'recu_loyer',
            'caution': 'recu_caution',
            'avance': 'recu_avance',
            'charges': 'recu_charges',
            'autre': 'recu',
        }
        return mapping.get(self.type_paiement, 'recu')
    
    def _ajouter_donnees_specialisees_recu(self, type_recu):
        """Ajoute des données spécialisées selon le type de récépissé"""
        donnees_speciales = {}
        
        if type_recu == 'recu_loyer':
            try:
                donnees_speciales.update({
                    'loyer_mensuel': float(self.contrat.loyer_mensuel) if self.contrat else 0,
                    'charges_mensuelles': float(self.contrat.charges_mensuelles) if self.contrat else 0,
                    'total_mensuel': float(self.montant),
                })
            except:
                donnees_speciales.update({
                    'loyer_mensuel': float(self.montant),
                    'charges_mensuelles': 0,
                    'total_mensuel': float(self.montant),
                })
        
        elif type_recu == 'recu_caution':
            try:
                donnees_speciales.update({
                    'montant_caution': float(self.montant),
                    'note_speciale': 'Dépôt de garantie - Remboursable en fin de bail',
                })
            except:
                donnees_speciales.update({
                    'montant_caution': float(self.montant),
                    'note_speciale': 'Dépôt de garantie',
                })
        
        elif type_recu == 'recu_avance':
            try:
                donnees_speciales.update({
                    'montant_avance': float(self.montant),
                    'loyer_mensuel': float(self.contrat.loyer_mensuel) if self.contrat else 0,
                    'note_speciale': 'Cette avance sera déduite du prochain loyer',
                })
            except:
                donnees_speciales.update({
                    'montant_avance': float(self.montant),
                    'loyer_mensuel': 0,
                    'note_speciale': 'Avance de loyer',
                })
        
        elif type_recu == 'recu_charges':
            donnees_speciales.update({
                'type_charges': 'Charges mensuelles',
                'montant_charges': float(self.montant),
                'note_speciale': 'Charges communes et services',
            })
        
        return donnees_speciales


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
        null=True,
        blank=True,
        verbose_name=_("Date de création")
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Date de modification")
    )
    
    class Meta:
        app_label = 'paiements'
        verbose_name = _("Retrait bailleur")
        verbose_name_plural = _("Retraits bailleur")
        ordering = ['-mois_retrait', '-date_demande']
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
    
    def calculer_charges_bailleur_disponibles(self):
        """Calcule les charges bailleur disponibles pour ce mois"""
        from django.db.models import Sum
        
        # Récupérer les charges validées et non utilisées pour ce mois
        charges_disponibles = ChargeBailleur.objects.filter(
            bailleur=self.bailleur,
            mois_charge__year=self.mois_retrait.year,
            mois_charge__month=self.mois_retrait.month,
            statut='valide'
        ).aggregate(total=Sum('montant'))['total'] or Decimal('0')
        
        return charges_disponibles
    
    def calculer_montant_net(self):
        """Calcule le montant net à payer avec les charges bailleur dynamiques"""
        # Calculer les charges bailleur disponibles
        self.montant_charges_bailleur = self.calculer_charges_bailleur_disponibles()
        
        # Calculer le montant net
        net = self.montant_loyers_bruts - self.montant_charges_deductibles - self.montant_charges_bailleur
        self.montant_net_a_payer = max(net, Decimal('0'))
        return self.montant_net_a_payer
    
    def valider(self, user):
        """Valide le retrait"""
        from django.utils import timezone
        
        self.statut = 'valide'
        self.date_validation = date.today()
        self.valide_par = user
        self.updated_at = timezone.now()
        
        # Sauvegarder seulement les champs modifiés
        self.save(update_fields=['statut', 'date_validation', 'valide_par', 'updated_at'])
    
    def marquer_paye(self, user):
        """Marque le retrait comme payé et marque les charges comme utilisées"""
        from django.utils import timezone
        
        self.statut = 'paye'
        self.date_paiement = date.today()
        self.updated_at = timezone.now()
        
        # Marquer les charges bailleur comme utilisées
        charges_utilisees = ChargeBailleur.objects.filter(
            bailleur=self.bailleur,
            mois_charge__year=self.mois_retrait.year,
            mois_charge__month=self.mois_retrait.month,
            statut='valide'
        )
        
        for charge in charges_utilisees:
            charge.marquer_utilise(self)
        
        # Sauvegarder seulement les champs modifiés
        self.save(update_fields=['statut', 'date_paiement', 'updated_at'])
    
    def annuler(self, user):
        """Annule le retrait"""
        from django.utils import timezone
        
        self.statut = 'annule'
        self.updated_at = timezone.now()
        
        # Sauvegarder seulement les champs modifiés
        self.save(update_fields=['statut', 'updated_at'])
    
    def _generer_quittance_retrait_kbis(self):
        """Génère une quittance de retrait KBIS dynamique avec le format correct."""
        import sys
        import os
        from datetime import datetime
        
        try:
            # Utiliser le système unifié
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from document_kbis_unifie import DocumentKBISUnifie
            
            # Récupérer les informations de base de manière sécurisée
            try:
                code_location = f"RET-{self.id}" if self.id else 'RET-N/A'
            except:
                code_location = 'RET-N/A'
                
            try:
                recu_de = self.bailleur.get_nom_complet() if self.bailleur else 'BAILLEUR'
            except:
                recu_de = 'BAILLEUR'
                
            try:
                quartier = f"Retrait {self.mois_retrait.strftime('%B %Y')}" if self.mois_retrait else 'Retrait mensuel'
            except:
                quartier = 'Retrait mensuel'
            
            # Générer un numéro de quittance unique au format KBIS
            numero_quittance = f"QUI-RET-{datetime.now().strftime('%Y%m%d%H%M%S')}-{self.id if self.id else 'X1DZ'}"
            
            # Données de la quittance
            donnees_quittance = {
                'numero': numero_quittance,
                'date': datetime.now().strftime('%d-%b-%y'),
                'code_location': code_location,
                'recu_de': recu_de,
                'montant': float(self.montant_net_a_payer),
                'mois_regle': self.mois_retrait.strftime('%B %Y') if self.mois_retrait else 'N/A',
                'type_retrait': 'Retrait Mensuel',
                'mode_retrait': 'Virement bancaire',
                'quartier': quartier,
                'montant_brut': float(self.montant_loyers_bruts),
                'charges_deduites': float(self.montant_charges_deductibles),
                'charges_bailleur': float(self.montant_charges_bailleur),
                'montant_net': float(self.montant_net_a_payer),
            }
            
            # Générer le document unifié
            html_quittance = DocumentKBISUnifie.generer_document_unifie(donnees_quittance, 'quittance_retrait_mensuel')
            
            return html_quittance
            
        except Exception as e:
            print(f"Erreur lors de la génération de la quittance de retrait KBIS: {str(e)}")
            return None


class ChargeBailleur(models.Model):
    """
    Modèle pour les charges avancées par le bailleur
    """
    STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('valide', 'Validé'),
        ('utilise', 'Utilisé'),
        ('annule', 'Annulé'),
    ]
    
    # Relations
    bailleur = models.ForeignKey(
        'proprietes.Bailleur',
        on_delete=models.CASCADE,
        related_name='charges_bailleur',
        verbose_name=_("Bailleur")
    )
    
    # Informations de base
    description = models.CharField(
        max_length=200,
        verbose_name=_("Description de la charge")
    )
    
    montant = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        verbose_name=_("Montant de la charge")
    )
    
    date_charge = models.DateField(
        verbose_name=_("Date de la charge")
    )
    
    mois_charge = models.DateField(
        verbose_name=_("Mois de la charge"),
        help_text=_("Mois pour lequel cette charge s'applique")
    )
    
    # Statut et utilisation
    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='en_attente',
        verbose_name=_("Statut")
    )
    
    retrait_utilise = models.ForeignKey(
        'RetraitBailleur',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='charges_utilisees',
        verbose_name=_("Retrait qui a utilisé cette charge")
    )
    
    # Métadonnées
    cree_par = models.ForeignKey(
        'utilisateurs.Utilisateur',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='charges_bailleur_crees',
        verbose_name=_("Créé par")
    )
    
    notes = models.TextField(
        blank=True,
        verbose_name=_("Notes")
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
        app_label = 'paiements'
        verbose_name = _("Charge Bailleur")
        verbose_name_plural = _("Charges Bailleur")
        ordering = ['-date_charge', '-created_at']
    
    def __str__(self):
        return f"{self.bailleur.get_nom_complet()} - {self.description} - {self.montant} F CFA"
    
    def marquer_utilise(self, retrait):
        """Marque cette charge comme utilisée dans un retrait"""
        self.statut = 'utilise'
        self.retrait_utilise = retrait
        self.save()
    
    def marquer_valide(self, user):
        """Valide cette charge"""
        self.statut = 'valide'
        self.save()
    
    def annuler(self, user):
        """Annule cette charge"""
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
        app_label = 'paiements'
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


class QuittancePaiement(models.Model):
    """
    Modèle pour les quittances de paiement
    """
    STATUT_CHOICES = [
        ('generee', 'Générée'),
        ('imprimee', 'Imprimée'),
        ('envoyee', 'Envoyée'),
        ('archivee', 'Archivée'),
    ]
    
    # Relations
    paiement = models.OneToOneField(
        Paiement,
        on_delete=models.CASCADE,
        related_name='quittance',
        verbose_name=_("Paiement")
    )
    
    # Informations de base
    numero_quittance = models.CharField(
        max_length=50,
        unique=True,
        help_text=_('Numéro unique de la quittance'),
        verbose_name=_("Numéro de quittance")
    )
    
    # Dates
    date_emission = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Date d'émission")
    )
    date_impression = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Date d'impression")
    )
    
    # Statut
    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='generee',
        verbose_name=_("Statut")
    )
    
    # Utilisateurs
    cree_par = models.ForeignKey(
        'utilisateurs.Utilisateur',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='quittances_crees',
        verbose_name=_("Créé par")
    )
    
    # Suppression logique
    is_deleted = models.BooleanField(
        default=False,
        verbose_name=_("Supprimé logiquement")
    )
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Date de suppression")
    )
    deleted_by = models.ForeignKey(
        'utilisateurs.Utilisateur',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='quittances_deleted',
        verbose_name=_("Supprimé par")
    )
    
    class Meta:
        app_label = 'paiements'
        verbose_name = _("Quittance de paiement")
        verbose_name_plural = _("Quittances de paiement")
        ordering = ['-date_emission']
    
    def __str__(self):
        return f"Quittance {self.numero_quittance} - {self.paiement.contrat.locataire.get_nom_complet()}"
    
    def generer_numero(self):
        """Génère un numéro de quittance unique"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"QUI-{timestamp}-{self.paiement.id}"
    
    def marquer_imprimee(self):
        """Marque la quittance comme imprimée"""
        from django.utils import timezone
        self.statut = 'imprimee'
        self.date_impression = timezone.now()
        self.save()
    
    def marquer_envoyee(self):
        """Marque la quittance comme envoyée"""
        self.statut = 'envoyee'
        self.save()
    
    def marquer_archivee(self):
        """Marque la quittance comme archivée"""
        self.statut = 'archivee'
        self.save()
    
    def save(self, *args, **kwargs):
        if not self.numero_quittance:
            self.numero_quittance = self.generer_numero()
        super().save(*args, **kwargs)