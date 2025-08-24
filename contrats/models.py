from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth import get_user_model
from django.utils import timezone
from proprietes.models import Propriete, Locataire
from proprietes.managers import NonDeletedManager

Utilisateur = get_user_model()


class Contrat(models.Model):
    """Modèle pour les contrats de location."""
    
    # Informations de base
    numero_contrat = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_("Numéro de contrat")
    )
    propriete = models.ForeignKey(
        Propriete,
        on_delete=models.PROTECT,
        related_name='contrats',
        verbose_name=_("Propriété")
    )
    locataire = models.ForeignKey(
        Locataire,
        on_delete=models.PROTECT,
        related_name='contrats',
        verbose_name=_("Locataire")
    )
    
    # Dates importantes
    date_debut = models.DateField(verbose_name=_("Date de début"))
    date_fin = models.DateField(blank=True, null=True, verbose_name=_("Date de fin"))
    date_signature = models.DateField(verbose_name=_("Date de signature"))
    
    # Informations financières
    loyer_mensuel = models.CharField(
        max_length=20,
        verbose_name=_("Loyer mensuel")
    )
    charges_mensuelles = models.CharField(
        max_length=20,
        default="0.00",
        verbose_name=_("Charges mensuelles")
    )
    
    # Gestion des cautions et avances
    depot_garantie = models.CharField(
        max_length=20,
        default="0.00",
        verbose_name=_("Dépôt de garantie")
    )
    avance_loyer = models.CharField(
        max_length=20,
        default="0.00",
        verbose_name=_("Avance de loyer")
    )
    
    # Statut des paiements de caution et avance
    caution_payee = models.BooleanField(
        default=False,
        verbose_name=_("Caution payée")
    )
    avance_loyer_payee = models.BooleanField(
        default=False,
        verbose_name=_("Avance de loyer payée")
    )
    date_paiement_caution = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Date de paiement de la caution")
    )
    date_paiement_avance = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Date de paiement de l'avance")
    )
    
    # Conditions de paiement
    jour_paiement = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(31)],
        verbose_name=_("Jour de paiement")
    )
    mode_paiement = models.CharField(
        max_length=20,
        choices=[
            ('virement', 'Virement bancaire'),
            ('cheque', 'Chèque'),
            ('especes', 'Espèces'),
            ('prelevement', 'Prélèvement automatique'),
        ],
        default='virement',
        verbose_name=_("Mode de paiement")
    )
    
    # État du contrat
    est_actif = models.BooleanField(default=True, verbose_name=_("Contrat actif"))
    est_resilie = models.BooleanField(default=False, verbose_name=_("Contrat résilié"))
    date_resiliation = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Date de résiliation")
    )
    motif_resiliation = models.TextField(
        blank=True,
        verbose_name=_("Motif de résiliation")
    )
    
    # Métadonnées
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name=_("Date de création"))
    date_modification = models.DateTimeField(auto_now=True, verbose_name=_("Date de modification"))
    notes = models.TextField(blank=True, verbose_name=_("Notes"))
    
    # Relations
    pieces = models.ManyToManyField(
        'proprietes.Piece',
        through='proprietes.PieceContrat',
        related_name='contrats',
        verbose_name=_("Pièces louées"),
        help_text=_("Pièces spécifiques louées dans ce contrat")
    )
    cree_par = models.ForeignKey(
        Utilisateur,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='contrats_crees',
        verbose_name=_("Créé par")
    )
    
    is_deleted = models.BooleanField(default=False, verbose_name='Supprimé logiquement')
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name='Date de suppression')
    deleted_by = models.ForeignKey(Utilisateur, null=True, blank=True, on_delete=models.SET_NULL, related_name='contrat_deleted', verbose_name='Supprimé par')
    
    objects = NonDeletedManager()
    all_objects = models.Manager()
    
    class Meta:
        verbose_name = _("Contrat")
        verbose_name_plural = _("Contrats")
        ordering = ['-date_debut']
    
    def __str__(self):
        return f"Contrat {self.numero_contrat} - {self.propriete.titre}"
    
    def get_loyer_total(self):
        """Retourne le loyer total (loyer + charges)."""
        return self.loyer_mensuel + self.charges_mensuelles
    
    def get_loyer_mensuel_formatted(self):
        """Retourne le loyer mensuel formaté en XOF"""
        from core.utils import format_currency_xof
        return format_currency_xof(self.loyer_mensuel)
    
    def get_charges_mensuelles_formatted(self):
        """Retourne les charges mensuelles formatées en XOF"""
        from core.utils import format_currency_xof
        return format_currency_xof(self.charges_mensuelles)
    
    def get_loyer_total_formatted(self):
        """Retourne le loyer total formaté en XOF"""
        from core.utils import format_currency_xof
        return format_currency_xof(self.get_loyer_total())
    
    def get_depot_garantie_formatted(self):
        """Retourne le dépôt de garantie formaté en XOF"""
        from core.utils import format_currency_xof
        return format_currency_xof(self.depot_garantie)
    
    def get_avance_loyer_formatted(self):
        """Retourne l'avance de loyer formatée en XOF"""
        from core.utils import format_currency_xof
        return format_currency_xof(self.avance_loyer)
    
    def get_total_caution_avance(self):
        """Retourne le total caution + avance."""
        return self.depot_garantie + self.avance_loyer
    
    def get_total_caution_avance_formatted(self):
        """Retourne le total caution + avance formaté en XOF"""
        from core.utils import format_currency_xof
        return format_currency_xof(self.get_total_caution_avance())
    
    def get_duree_mois(self):
        """Retourne la durée du contrat en mois."""
        try:
            from dateutil.relativedelta import relativedelta
            delta = relativedelta(self.date_fin, self.date_debut)
            return delta.years * 12 + delta.months
        except ImportError:
            # Fallback si dateutil n'est pas disponible
            return (self.date_fin - self.date_debut).days // 30
        except Exception:
            # Fallback en cas d'erreur
            return 0
    
    def est_expire(self):
        """Vérifie si le contrat est expiré."""
        from django.utils import timezone
        return self.date_fin < timezone.now().date()
    
    def get_statut(self):
        """Retourne le statut du contrat."""
        if self.est_resilie:
            return "Résilié"
        elif not self.est_actif:
            return "Inactif"
        elif self.est_expire():
            return "Expiré"
        else:
            return "Actif"
    
    def verifier_disponibilite_pieces(self, pieces_ids, date_debut, date_fin):
        """Vérifie si les pièces sont disponibles pour la période donnée."""
        from proprietes.models import Piece
        
        if not pieces_ids:
            return True, []
        
        pieces = Piece.objects.filter(id__in=pieces_ids)
        conflits = []
        
        for piece in pieces:
            if not piece.est_disponible(date_debut, date_fin):
                # Vérifier les contrats conflictuels
                contrats_conflictuels = piece.contrats.filter(
                    est_actif=True,
                    est_resilie=False,
                    date_debut__lt=date_fin,
                    date_fin__gt=date_debut
                )
                
                for contrat in contrats_conflictuels:
                    conflits.append({
                        'piece': piece.nom,
                        'contrat_existant': contrat.numero_contrat,
                        'locataire_existant': contrat.locataire.get_nom_complet(),
                        'periode': f"{contrat.date_debut} à {contrat.date_fin}"
                    })
        
        return len(conflits) == 0, conflits
    
    def assigner_pieces(self, pieces_data):
        """Assigne des pièces au contrat avec gestion des conflits."""
        from proprietes.models import PieceContrat
        
        # Supprimer les anciennes assignations
        self.pieces_contrat.all().delete()
        
        # Créer les nouvelles assignations
        for piece_data in pieces_data:
            piece_id = piece_data.get('piece_id')
            loyer_piece = piece_data.get('loyer_piece')
            charges_piece = piece_data.get('charges_piece', 0)
            date_debut_occupation = piece_data.get('date_debut_occupation', self.date_debut)
            date_fin_occupation = piece_data.get('date_fin_occupation', self.date_fin)
            
            PieceContrat.objects.create(
                piece_id=piece_id,
                contrat=self,
                loyer_piece=loyer_piece,
                charges_piece=charges_piece,
                date_debut_occupation=date_debut_occupation,
                date_fin_occupation=date_fin_occupation
            )
    
    def get_pieces_louees(self):
        """Retourne les pièces louées dans ce contrat."""
        return self.pieces_contrat.filter(actif=True)
    
    def get_total_surface_louee(self):
        """Retourne la surface totale des pièces louées."""
        pieces = self.get_pieces_louees()
        return sum(piece.piece.surface or 0 for piece in pieces)
    
    def get_loyer_total_pieces(self):
        """Retourne le loyer total des pièces louées."""
        pieces = self.get_pieces_louees()
        return sum(piece.get_loyer_total() for piece in pieces)
    
    def save(self, *args, **kwargs):
        """Override save pour générer automatiquement le numéro de contrat et calculer les montants par défaut."""
        if not self.numero_contrat:
            # Générer un numéro de contrat unique
            import uuid
            self.numero_contrat = f"CTR-{uuid.uuid4().hex[:8].upper()}"
        
        # Calculer automatiquement le dépôt de garantie et l'avance si non spécifiés
        if self.depot_garantie == 0:
            self.depot_garantie = self.loyer_mensuel * 3  # 3 mois de caution
        
        if self.avance_loyer == 0:
            self.avance_loyer = self.loyer_mensuel  # 1 mois d'avance
        
        # Gérer la disponibilité de la propriété
        self._gestion_disponibilite_propriete()
        
        super().save(*args, **kwargs)
    
    def _gestion_disponibilite_propriete(self):
        """Gère automatiquement la disponibilité de la propriété associée."""
        if self.pk:  # Si c'est une modification
            old_instance = Contrat.objects.get(pk=self.pk)
            old_actif = old_instance.est_actif
            old_resilie = old_instance.est_resilie
            
            # Si le statut a changé, mettre à jour la disponibilité
            if (old_actif != self.est_actif) or (old_resilie != self.est_resilie):
                self._update_disponibilite_propriete()
        else:  # Si c'est une création
            if self.est_actif and not self.est_resilie:
                # Nouveau contrat actif = propriété non disponible
                self.propriete.disponible = False
                self.propriete.save(update_fields=['disponible'])
    
    def _update_disponibilite_propriete(self):
        """Met à jour la disponibilité de la propriété en fonction des contrats actifs."""
        # Vérifier s'il y a d'autres contrats actifs pour cette propriété
        contrats_actifs = Contrat.objects.filter(
            propriete=self.propriete,
            est_actif=True,
            est_resilie=False
        ).exclude(pk=self.pk)
        
        # Si ce contrat devient actif et qu'il n'y a pas d'autres contrats actifs
        if self.est_actif and not self.est_resilie:
            if not contrats_actifs.exists():
                self.propriete.disponible = False
                self.propriete.save(update_fields=['disponible'])
        # Si ce contrat devient inactif ou résilié
        elif not self.est_actif or self.est_resilie:
            if not contrats_actifs.exists():
                self.propriete.disponible = True
                self.propriete.save(update_fields=['disponible'])
    
    def delete(self, *args, **kwargs):
        """Override delete pour gérer la disponibilité de la propriété."""
        # Marquer la propriété comme disponible si c'était le seul contrat actif
        if self.est_actif and not self.est_resilie:
            contrats_actifs = Contrat.objects.filter(
                propriete=self.propriete,
                est_actif=True,
                est_resilie=False
            ).exclude(pk=self.pk)
            
            if not contrats_actifs.exists():
                self.propriete.disponible = True
                self.propriete.save(update_fields=['disponible'])
        
        super().delete(*args, **kwargs)
    
    def marquer_caution_payee(self, date_paiement=None):
        """Marque la caution comme payée."""
        self.caution_payee = True
        if date_paiement:
            self.date_paiement_caution = date_paiement
        else:
            from django.utils import timezone
            self.date_paiement_caution = timezone.now().date()
        self.save()
    
    def marquer_avance_payee(self, date_paiement=None):
        """Marque l'avance de loyer comme payée."""
        self.avance_loyer_payee = True
        if date_paiement:
            self.date_paiement_avance = date_paiement
        else:
            from django.utils import timezone
            self.date_paiement_avance = timezone.now().date()
        self.save()
    
    def peut_commencer_location(self):
        """Vérifie si le locataire peut commencer la location (caution + avance payées)."""
        return self.caution_payee and self.avance_loyer_payee
    
    def get_statut_paiements(self):
        """Retourne le statut des paiements de caution et avance."""
        if self.caution_payee and self.avance_loyer_payee:
            return "Complet"
        elif self.caution_payee:
            return "Caution payée, avance en attente"
        elif self.avance_loyer_payee:
            return "Avance payée, caution en attente"
        else:
            return "En attente de paiement"


class Quittance(models.Model):
    """Modèle pour les quittances de loyer."""
    
    contrat = models.ForeignKey(
        Contrat,
        on_delete=models.CASCADE,
        related_name='quittances',
        verbose_name=_("Contrat")
    )
    mois = models.DateField(verbose_name=_("Mois concerné"))
    montant_loyer = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        verbose_name=_("Montant loyer")
    )
    montant_charges = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0,
        verbose_name=_("Montant charges")
    )
    montant_total = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        verbose_name=_("Montant total")
    )
    
    # Métadonnées
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name=_("Date de création"))
    date_emission = models.DateTimeField(auto_now_add=True, verbose_name=_("Date d'émission"))
    numero_quittance = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_("Numéro de quittance")
    )
    
    class Meta:
        verbose_name = _("Quittance")
        verbose_name_plural = _("Quittances")
        ordering = ['-mois']
        unique_together = ['contrat', 'mois']
    
    def __str__(self):
        return f"Quittance {self.numero_quittance} - {self.contrat.numero_contrat}"
    
    def save(self, *args, **kwargs):
        """Override save pour calculer le montant total et générer le numéro."""
        if not self.montant_total:
            self.montant_total = self.montant_loyer + self.montant_charges
        
        if not self.numero_quittance:
            # Générer un numéro de quittance unique
            import uuid
            self.numero_quittance = f"QUI-{uuid.uuid4().hex[:8].upper()}"
        
        super().save(*args, **kwargs)


class EtatLieux(models.Model):
    """Modèle pour les états des lieux."""
    
    TYPE_CHOICES = [
        ('entree', 'Entrée'),
        ('sortie', 'Sortie'),
    ]
    
    contrat = models.ForeignKey(
        Contrat,
        on_delete=models.CASCADE,
        related_name='etats_lieux',
        verbose_name=_("Contrat")
    )
    type_etat = models.CharField(
        max_length=10,
        choices=TYPE_CHOICES,
        verbose_name=_("Type d'état des lieux")
    )
    date_etat = models.DateField(verbose_name=_("Date de l'état des lieux"))
    
    # Observations
    observations_generales = models.TextField(blank=True, verbose_name=_("Observations générales"))
    etat_murs = models.CharField(
        max_length=20,
        choices=[
            ('excellent', 'Excellent'),
            ('bon', 'Bon'),
            ('moyen', 'Moyen'),
            ('mauvais', 'Mauvais'),
        ],
        default='bon',
        verbose_name=_("État des murs")
    )
    etat_sol = models.CharField(
        max_length=20,
        choices=[
            ('excellent', 'Excellent'),
            ('bon', 'Bon'),
            ('moyen', 'Moyen'),
            ('mauvais', 'Mauvais'),
        ],
        default='bon',
        verbose_name=_("État du sol")
    )
    etat_plomberie = models.CharField(
        max_length=20,
        choices=[
            ('excellent', 'Excellent'),
            ('bon', 'Bon'),
            ('moyen', 'Moyen'),
            ('mauvais', 'Mauvais'),
        ],
        default='bon',
        verbose_name=_("État de la plomberie")
    )
    etat_electricite = models.CharField(
        max_length=20,
        choices=[
            ('excellent', 'Excellent'),
            ('bon', 'Bon'),
            ('moyen', 'Moyen'),
            ('mauvais', 'Mauvais'),
        ],
        default='bon',
        verbose_name=_("État de l'électricité")
    )
    
    # Métadonnées
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name=_("Date de création"))
    notes = models.TextField(blank=True, verbose_name=_("Notes"))
    
    # Relations
    cree_par = models.ForeignKey(
        Utilisateur,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='etats_lieux_crees',
        verbose_name=_("Créé par")
    )
    
    class Meta:
        verbose_name = _("État des lieux")
        verbose_name_plural = _("États des lieux")
        ordering = ['-date_etat']
        unique_together = ['contrat', 'type_etat']
    
    def __str__(self):
        return f"État des lieux {self.get_type_etat_display()} - {self.contrat.numero_contrat}"


class RecuCaution(models.Model):
    """Modèle pour les reçus de caution et d'avance de loyer."""
    
    contrat = models.OneToOneField(
        Contrat,
        on_delete=models.CASCADE,
        related_name='recu_caution',
        verbose_name=_("Contrat")
    )
    numero_recu = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_("Numéro de reçu")
    )
    date_emission = models.DateTimeField(auto_now_add=True, verbose_name=_("Date d'émission"))
    
    # Type de reçu
    type_recu = models.CharField(
        max_length=20,
        choices=[
            ('caution', 'Caution'),
            ('avance', 'Avance de loyer'),
            ('complet', 'Caution + Avance'),
        ],
        default='complet',
        verbose_name=_("Type de reçu")
    )
    
    # Informations d'impression
    imprime = models.BooleanField(default=False, verbose_name=_("Imprimé"))
    date_impression = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Date d'impression")
    )
    imprime_par = models.ForeignKey(
        Utilisateur,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recus_caution_imprimes',
        verbose_name=_("Imprimé par")
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
        verbose_name = _("Reçu de caution")
        verbose_name_plural = _("Reçus de caution")
        ordering = ['-date_emission']
    
    def __str__(self):
        return f"Reçu caution {self.numero_recu} - {self.contrat.numero_contrat}"
    
    def save(self, *args, **kwargs):
        if not self.numero_recu:
            self.numero_recu = self._generer_numero_recu()
        super().save(*args, **kwargs)
    
    def _generer_numero_recu(self):
        """Génère un numéro de reçu unique."""
        from datetime import datetime
        from django.utils import timezone
        
        # Format: CAU-YYYYMMDD-XXXXX
        date_str = datetime.now().strftime('%Y%m%d')
        timestamp_part = str(int(datetime.now().timestamp() * 1000))[-5:]
        numero_recu = f'CAU-{date_str}-{timestamp_part}'
        
        return numero_recu
    
    def marquer_imprime(self, utilisateur):
        """Marque le reçu comme imprimé."""
        self.imprime = True
        self.date_impression = timezone.now()
        self.imprime_par = utilisateur
        self.save()
    
    def get_informations_caution(self):
        """Retourne les informations détaillées de la caution et avance."""
        contrat = self.contrat
        propriete = contrat.propriete
        locataire = contrat.locataire
        bailleur = propriete.bailleur
        
        return {
            'contrat': contrat,
            'propriete': propriete,
            'locataire': locataire,
            'bailleur': bailleur,
            'depot_garantie': contrat.depot_garantie,
            'avance_loyer': contrat.avance_loyer,
            'total_caution_avance': contrat.get_total_caution_avance(),
            'loyer_mensuel': contrat.loyer_mensuel,
            'charges_mensuelles': contrat.charges_mensuelles,
            'date_debut': contrat.date_debut,
            'date_fin': contrat.date_fin,
            'caution_payee': contrat.caution_payee,
            'avance_loyer_payee': contrat.avance_loyer_payee,
            'date_paiement_caution': contrat.date_paiement_caution,
            'date_paiement_avance': contrat.date_paiement_avance,
        }
    
    def get_template_context(self):
        """Retourne le contexte pour le template de reçu."""
        context = self.get_informations_caution()
        context.update({
            'recu': self,
            'date_emission': self.date_emission,
            'numero_recu': self.numero_recu,
        })
        return context


class DocumentContrat(models.Model):
    """Modèle pour la documentation PDF des contrats."""
    
    contrat = models.OneToOneField(
        Contrat,
        on_delete=models.CASCADE,
        related_name='document_contrat',
        verbose_name=_("Contrat")
    )
    numero_document = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_("Numéro de document")
    )
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name=_("Date de création"))
    
    # Type de document
    type_document = models.CharField(
        max_length=25,
        choices=[
            ('contrat_complet', 'Contrat complet'),
            ('contrat_simplifie', 'Contrat simplifié'),
            ('contrat_professionnel', 'Contrat professionnel'),
        ],
        default='contrat_complet',
        verbose_name=_("Type de document")
    )
    
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
        related_name='documents_contrat_imprimes',
        verbose_name=_("Imprimé par")
    )
    
    # Options d'impression
    format_impression = models.CharField(
        max_length=20,
        choices=[
            ('a4', 'A4'),
            ('a3', 'A3'),
        ],
        default='a4',
        verbose_name=_("Format d'impression")
    )
    
    # Métadonnées
    version_template = models.CharField(
        max_length=10,
        default='1.0',
        verbose_name=_("Version du template")
    )
    notes_internes = models.TextField(blank=True, verbose_name=_("Notes internes"))
    
    class Meta:
        verbose_name = _("Document de contrat")
        verbose_name_plural = _("Documents de contrat")
        ordering = ['-date_creation']
    
    def __str__(self):
        return f"Document contrat {self.numero_document} - {self.contrat.numero_contrat}"
    
    def save(self, *args, **kwargs):
        if not self.numero_document:
            self.numero_document = self._generer_numero_document()
        super().save(*args, **kwargs)
    
    def _generer_numero_document(self):
        """Génère un numéro de document unique."""
        from datetime import datetime
        
        # Format: DOC-YYYYMMDD-XXXXX
        date_str = datetime.now().strftime('%Y%m%d')
        timestamp_part = str(int(datetime.now().timestamp() * 1000))[-5:]
        numero_document = f'DOC-{date_str}-{timestamp_part}'
        
        return numero_document
    
    def marquer_imprime(self, utilisateur):
        """Marque le document comme imprimé."""
        self.imprime = True
        self.date_impression = timezone.now()
        self.imprime_par = utilisateur
        self.save()
    
    def get_informations_contrat(self):
        """Retourne les informations détaillées du contrat pour la documentation."""
        contrat = self.contrat
        propriete = contrat.propriete
        locataire = contrat.locataire
        bailleur = propriete.bailleur
        
        return {
            'contrat': contrat,
            'propriete': propriete,
            'locataire': locataire,
            'bailleur': bailleur,
            'numero_contrat': contrat.numero_contrat,
            'date_debut': contrat.date_debut,
            'date_fin': contrat.date_fin,
            'date_signature': contrat.date_signature,
            'loyer_mensuel': contrat.loyer_mensuel,
            'charges_mensuelles': contrat.charges_mensuelles,
            'depot_garantie': contrat.depot_garantie,
            'avance_loyer': contrat.avance_loyer,
            'jour_paiement': contrat.jour_paiement,
            'mode_paiement': contrat.get_mode_paiement_display(),
            'duree_mois': contrat.get_duree_mois(),
            'statut': contrat.get_statut(),
            'statut_paiements': contrat.get_statut_paiements(),
        }
    
    def get_template_context(self):
        """Retourne le contexte pour le template de document."""
        context = self.get_informations_contrat()
        context.update({
            'document': self,
            'date_creation': self.date_creation,
            'numero_document': self.numero_document,
            'type_document': self.get_type_document_display(),
        })
        return context


class ResiliationContrat(models.Model):
    """Modèle pour gérer les résiliations de contrat avec possibilité de suppression totale."""
    
    contrat = models.OneToOneField(
        Contrat,
        on_delete=models.CASCADE,
        related_name='resiliation',
        verbose_name=_("Contrat")
    )
    
    # Informations de résiliation
    date_resiliation = models.DateField(verbose_name=_("Date de résiliation"))
    motif_resiliation = models.TextField(verbose_name=_("Motif de résiliation"))
    type_resiliation = models.CharField(
        max_length=20,
        choices=[
            ('locataire', 'Résiliation par le locataire'),
            ('bailleur', 'Résiliation par le bailleur'),
            ('accord_mutuel', 'Résiliation d\'accord mutuel'),
            ('expiration', 'Expiration naturelle'),
            ('judiciaire', 'Résiliation judiciaire'),
        ],
        verbose_name=_("Type de résiliation")
    )
    
    # Statut de la résiliation
    statut = models.CharField(
        max_length=20,
        choices=[
            ('en_cours', 'En cours de traitement'),
            ('validee', 'Validée'),
            ('annulee', 'Annulée'),
            ('supprimee', 'Supprimée définitivement'),
        ],
        default='en_cours',
        verbose_name=_("Statut")
    )
    
    # Gestion des biens et cautions
    etat_lieux_sortie = models.TextField(
        blank=True,
        verbose_name=_("État des lieux de sortie")
    )
    caution_remboursee = models.BooleanField(
        default=False,
        verbose_name=_("Caution remboursée")
    )
    montant_remboursement = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0,
        verbose_name=_("Montant du remboursement")
    )
    date_remboursement = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Date de remboursement")
    )
    
    # Métadonnées
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name=_("Date de création"))
    date_modification = models.DateTimeField(auto_now=True, verbose_name=_("Date de modification"))
    notes = models.TextField(blank=True, verbose_name=_("Notes"))
    
    # Relations
    cree_par = models.ForeignKey(
        'utilisateurs.Utilisateur',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resiliations_crees',
        verbose_name=_("Créé par")
    )
    validee_par = models.ForeignKey(
        'utilisateurs.Utilisateur',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resiliations_validees',
        verbose_name=_("Validée par")
    )
    
    class Meta:
        verbose_name = _("Résiliation de contrat")
        verbose_name_plural = _("Résiliations de contrat")
        ordering = ['-date_resiliation']
    
    def __str__(self):
        return f"Résiliation {self.contrat.numero_contrat} - {self.date_resiliation}"
    
    def save(self, *args, **kwargs):
        """Override save pour mettre à jour le contrat."""
        super().save(*args, **kwargs)
        
        # Mettre à jour le contrat
        if self.statut == 'validee':
            self.contrat.est_resilie = True
            self.contrat.date_resiliation = self.date_resiliation
            self.contrat.motif_resiliation = self.motif_resiliation
            self.contrat.save()
    
    def valider_resiliation(self, utilisateur):
        """Valide la résiliation."""
        self.statut = 'validee'
        self.validee_par = utilisateur
        self.save()
    
    def annuler_resiliation(self, utilisateur, motif=""):
        """Annule la résiliation."""
        self.statut = 'annulee'
        self.validee_par = utilisateur
        if motif:
            self.notes += f"\nMotif d'annulation: {motif}"
        self.save()
        
        # Réactiver le contrat
        self.contrat.est_resilie = False
        self.contrat.date_resiliation = None
        self.contrat.motif_resiliation = ""
        self.contrat.save()
    
    def supprimer_definitivement(self, utilisateur, motif=""):
        """Supprime définitivement la résiliation et le contrat."""
        if self.statut == 'validee':
            self.statut = 'supprimee'
            self.validee_par = utilisateur
            if motif:
                self.notes += f"\nMotif de suppression: {motif}"
            self.save()
            
            # Supprimer définitivement le contrat
            self.contrat.delete()
            return True
        return False
    
    def peut_etre_supprimee(self):
        """Vérifie si la résiliation peut être supprimée définitivement."""
        return self.statut == 'validee'
    
    def get_montant_remboursement_formatted(self):
        """Retourne le montant de remboursement formaté en XOF"""
        from core.utils import format_currency_xof
        return format_currency_xof(self.montant_remboursement)
