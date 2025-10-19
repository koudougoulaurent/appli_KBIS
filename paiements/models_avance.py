from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from decimal import Decimal
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from contrats.models import Contrat


class AvanceLoyer(models.Model):
    """
    Modèle pour gérer les avances de loyer avec calcul automatique des mois
    """
    STATUT_CHOICES = [
        ('active', 'Active'),
        ('epuisee', 'Épuisée'),
        ('annulee', 'Annulée'),
    ]
    
    MODE_SELECTION_CHOICES = [
        ('automatique', 'Calcul automatique'),
        ('manuel', 'Sélection manuelle'),
    ]
    
    # Relations
    contrat = models.ForeignKey(
        Contrat,
        on_delete=models.CASCADE,
        related_name='avances_loyer',
        verbose_name=_("Contrat")
    )
    
    paiement = models.ForeignKey(
        'paiements.Paiement',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='avance_loyer',
        verbose_name=_("Paiement associé")
    )
    
    # Montants
    montant_avance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        verbose_name=_("Montant de l'avance")
    )
    
    loyer_mensuel = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        verbose_name=_("Loyer mensuel")
    )
    
    # Calculs automatiques
    nombre_mois_couverts = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Nombre de mois couverts")
    )
    
    montant_restant = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name=_("Montant restant")
    )
    
    # Dates
    date_avance = models.DateField(
        verbose_name=_("Date de l'avance")
    )
    
    # *** NOUVEAU : Mois d'effet personnalisé ***
    mois_effet_personnalise = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Mois d'effet personnalisé"),
        help_text=_("Laissez vide pour utiliser la logique automatique (15+ du mois)")
    )
    
    # *** NOUVEAU : Sélection manuelle des mois couverts ***
    mois_couverts_manuels = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_("Mois couverts sélectionnés manuellement"),
        help_text=_("Liste des mois sélectionnés manuellement pour cette avance")
    )
    
    # *** NOUVEAU : Mode de sélection des mois ***
    MODE_SELECTION_CHOICES = [
        ('automatique', 'Calcul automatique'),
        ('manuel', 'Sélection manuelle'),
    ]
    
    mode_selection_mois = models.CharField(
        max_length=20,
        choices=MODE_SELECTION_CHOICES,
        default='automatique',
        verbose_name=_("Mode de sélection des mois"),
        help_text=_("Choisissez comment déterminer les mois couverts par cette avance")
    )
    
    mois_debut_couverture = models.DateField(
        verbose_name=_("Mois de début de couverture")
    )
    
    mois_fin_couverture = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Mois de fin de couverture")
    )
    
    # Statut
    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='active',
        verbose_name=_("Statut")
    )
    
    # *** NOUVEAU : Lien avec le paiement ***
    paiement = models.ForeignKey(
        'Paiement',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='avance_loyer',
        verbose_name=_("Paiement associé")
    )
    
    # Métadonnées
    notes = models.TextField(
        blank=True,
        verbose_name=_("Notes")
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        app_label = 'paiements'
        verbose_name = _("Avance de loyer")
        verbose_name_plural = _("Avances de loyer")
        ordering = ['-date_avance']
    
    def get_mois_couverts_liste_original(self):
        """Retourne la liste des mois couverts par l'avance (version originale)"""
        if not self.mois_debut_couverture or not self.nombre_mois_couverts:
            return []
        
        mois_liste = []
        for i in range(self.nombre_mois_couverts):
            mois = self.mois_debut_couverture + relativedelta(months=i)
            mois_liste.append(mois)
        
        return mois_liste

    def __str__(self):
        return f"Avance {self.montant_avance} F CFA - {self.contrat.locataire.get_nom_complet()}"
    
    def save(self, *args, **kwargs):
        """Sauvegarde personnalisée avec calcul automatique des mois"""
        if not self.pk:  # Nouvelle avance
            self.calculer_mois_couverts()
            # Le montant_restant est déjà géré par calculer_mois_couverts()
        super().save(*args, **kwargs)
    
    def calculer_mois_couverts(self):
        """Calcule le nombre de mois couverts par l'avance"""
        # Vérifier que le loyer mensuel est valide
        if not self.loyer_mensuel or self.loyer_mensuel <= 0:
            self.nombre_mois_couverts = 0
            self.mois_debut_couverture = self.date_avance.replace(day=1)
            self.mois_fin_couverture = self.mois_debut_couverture
            self.statut = 'annulee'
            return
        
        # *** NOUVELLE LOGIQUE : Gestion de la sélection manuelle vs automatique ***
        if self.mode_selection_mois == 'manuel' and self.mois_couverts_manuels:
            # Mode manuel : utiliser les mois sélectionnés
            self._calculer_mois_manuels()
        else:
            # Mode automatique : calculer normalement
            self._calculer_mois_automatiques()
        
        # Mettre à jour le statut et le montant restant
        self.statut = 'active'  # Toutes les avances commencent comme actives
        self.montant_restant = self.montant_avance  # Le montant restant commence avec le montant total
    
    def _calculer_mois_automatiques(self):
        """Calcule les mois couverts en mode automatique"""
        # Calculer le nombre de mois complets
        mois_complets = int(self.montant_avance // self.loyer_mensuel)
        
        self.nombre_mois_couverts = mois_complets
        
        # *** LOGIQUE INTELLIGENTE : Mois d'effet personnalisé ou automatique ***
        if self.mois_effet_personnalise:
            # Utiliser le mois d'effet personnalisé
            self.mois_debut_couverture = self.mois_effet_personnalise.replace(day=1)
        else:
            # Logique automatique basée sur le jour du mois
            # Si l'avance est versée après le 15 du mois, elle prend effet le mois suivant
            # Sinon, elle prend effet le mois courant
            mois_avance = self.date_avance.replace(day=1)
            jour_avance = self.date_avance.day
            
            # Règle du 15+ : après le 15 = mois suivant, sinon mois courant
            if jour_avance > 15:
                self.mois_debut_couverture = mois_avance + relativedelta(months=1)
            else:
                self.mois_debut_couverture = mois_avance
        
        # Calculer la fin de couverture
        if mois_complets > 0:
            self.mois_fin_couverture = self.mois_debut_couverture + relativedelta(months=mois_complets - 1)
        else:
            self.mois_fin_couverture = self.mois_debut_couverture
    
    def _calculer_mois_manuels(self):
        """Calcule les mois couverts en mode manuel"""
        if not self.mois_couverts_manuels:
            # Si pas de mois sélectionnés, revenir au mode automatique
            self.mode_selection_mois = 'automatique'
            self._calculer_mois_automatiques()
            return
        
        # Trier les mois sélectionnés
        mois_dates = []
        for mois_str in self.mois_couverts_manuels:
            try:
                # Convertir la chaîne en date (format YYYY-MM-DD)
                mois_date = datetime.strptime(mois_str, '%Y-%m-%d').date()
                mois_dates.append(mois_date)
            except ValueError:
                continue
        
        if not mois_dates:
            # Si aucun mois valide, revenir au mode automatique
            self.mode_selection_mois = 'automatique'
            self._calculer_mois_automatiques()
            return
        
        mois_dates.sort()
        
        # Définir les mois de début et fin
        self.mois_debut_couverture = mois_dates[0]
        self.mois_fin_couverture = mois_dates[-1]
        self.nombre_mois_couverts = len(mois_dates)
        
        # Vérifier que le montant de l'avance est suffisant
        montant_requis = self.loyer_mensuel * self.nombre_mois_couverts
        if self.montant_avance < montant_requis:
            # Ajuster le nombre de mois si le montant est insuffisant
            mois_possibles = int(self.montant_avance // self.loyer_mensuel)
            if mois_possibles > 0:
                self.nombre_mois_couverts = mois_possibles
                self.mois_fin_couverture = self.mois_debut_couverture + relativedelta(months=mois_possibles - 1)
                # Mettre à jour la liste des mois sélectionnés
                self.mois_couverts_manuels = [mois.strftime('%Y-%m-%d') for mois in mois_dates[:mois_possibles]]
    
    def get_mois_couverts_liste(self):
        """Retourne la liste des mois couverts par l'avance"""
        if self.mode_selection_mois == 'manuel' and self.mois_couverts_manuels:
            # Mode manuel : retourner les mois sélectionnés
            mois_liste = []
            for mois_str in self.mois_couverts_manuels:
                try:
                    mois_date = datetime.strptime(mois_str, '%Y-%m-%d').date()
                    mois_liste.append(mois_date)
                except ValueError:
                    continue
            return sorted(mois_liste)
        else:
            # Mode automatique : calculer normalement
            if not self.mois_debut_couverture or not self.nombre_mois_couverts:
                return []
            
            mois_liste = []
            for i in range(self.nombre_mois_couverts):
                mois = self.mois_debut_couverture + relativedelta(months=i)
                mois_liste.append(mois)
            
            return mois_liste
    
    def generer_recu_avance_kbis(self):
        """Génère un reçu d'avance avec le système KBIS unifié"""
        import os
        import sys
        from datetime import datetime
        
        try:
            # *** CORRECTION : Recalculer les mois couverts pour s'assurer qu'ils sont corrects ***
            self.calculer_mois_couverts()
            self.save()
            
            # Utiliser le système unifié
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from document_kbis_unifie import DocumentKBISUnifie
            
            # Récupérer les informations de base
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
            numero_recu = f"AVC-{datetime.now().strftime('%Y%m%d%H%M%S')}-{self.id if self.id else 'X1DZ'}"
            
            # Calculer les mois réglés automatiquement
            mois_regle = self._calculer_mois_regle()
            
            # Données du récépissé d'avance
            donnees_recu = {
                'numero': numero_recu,
                'date': self.date_avance.strftime('%d-%b-%y') if self.date_avance else datetime.now().strftime('%d-%b-%y'),
                'code_location': code_location,
                'recu_de': recu_de,
                'montant': float(self.montant_avance),
                'type_paiement': 'Avance de Loyer',
                'mode_paiement': 'Espèces',
                'quartier': quartier,
                'loyer_mensuel': float(self.loyer_mensuel),
                'mois_couverts': self.nombre_mois_couverts,
                'montant_restant': float(self.montant_restant),
                'date_debut_couverture': self.mois_debut_couverture.strftime('%B %Y') if self.mois_debut_couverture else '',
                'date_fin_couverture': self.mois_fin_couverture.strftime('%B %Y') if self.mois_fin_couverture else '',
                'statut': self.get_statut_display(),
                'notes': self.notes or '',
                'mois_regle': mois_regle  # *** NOUVEAU : Mois réglés calculés automatiquement ***
            }
            
            # Générer le document unifié
            return DocumentKBISUnifie.generer_recu_avance(donnees_recu)
            
        except Exception as e:
            print(f"Erreur lors de la génération du reçu d'avance: {str(e)}")
            return None

    def _calculer_mois_regle(self):
        """Calcule automatiquement les mois couverts par l'avance basé sur le loyer mensuel"""
        from dateutil.relativedelta import relativedelta
        from datetime import datetime
        
        try:
            # *** CORRECTION : Utiliser la même logique que calculer_mois_couverts() ***
            # Utiliser directement les mois de couverture calculés
            if not self.mois_debut_couverture or self.nombre_mois_couverts <= 0:
                return "Aucun mois couvert"
            
            # Générer la liste des mois couverts par l'avance
            mois_regles = []
            mois_courant = self.mois_debut_couverture
            
            for i in range(self.nombre_mois_couverts):
                mois_regles.append(mois_courant.strftime('%B %Y'))
                mois_courant = mois_courant + relativedelta(months=1)
            
            # Convertir les mois en français
            mois_regles_fr = [self._convertir_mois_francais(mois) for mois in mois_regles]
            
            # Retourner la liste formatée des mois couverts
            return ', '.join(mois_regles_fr)
            
        except Exception as e:
            print(f"Erreur lors du calcul des mois couverts: {str(e)}")
            return f"{self.nombre_mois_couverts} mois couverts par l'avance"


    def _get_dernier_mois_paiement(self):
        """Récupère le dernier mois de paiement (dernière quittance)"""
        try:
            from paiements.models import Paiement
            from dateutil.relativedelta import relativedelta
            
            # Chercher la dernière quittance de loyer pour ce contrat
            derniere_quittance = Paiement.objects.filter(
                contrat=self.contrat,
                type_paiement='loyer',
                statut='valide'
            ).order_by('-date_paiement').first()
            
            if derniere_quittance:
                # Retourner le mois de la dernière quittance
                return derniere_quittance.date_paiement.replace(day=1)
            
            # Si pas de quittance, utiliser le mois de début du contrat
            if self.contrat and self.contrat.date_debut:
                return self.contrat.date_debut.replace(day=1)
            
            return None
            
        except Exception as e:
            print(f"Erreur lors de la récupération du dernier mois de paiement: {str(e)}")
            return None

    def _convertir_mois_francais(self, mois_anglais):
        """Convertit un mois anglais en français et corrige le format des années"""
        mois_francais = {
            'January': 'Janvier',
            'February': 'Février', 
            'March': 'Mars',
            'April': 'Avril',
            'May': 'Mai',
            'June': 'Juin',
            'July': 'Juillet',
            'August': 'Août',
            'September': 'Septembre',
            'October': 'Octobre',
            'November': 'Novembre',
            'December': 'Décembre'
        }
        
        # Remplacer le mois anglais par le mois français
        resultat = mois_anglais
        for mois_en, mois_fr in mois_francais.items():
            resultat = resultat.replace(mois_en, mois_fr)
        
        # Corriger le format des années (0225 -> 2025, 0226 -> 2026, etc.)
        import re
        # Chercher les années au format 0XXX et les convertir en 20XX
        # Pattern plus simple et plus robuste
        resultat = re.sub(r'\b0(\d{2})\b', r'20\1', resultat)
        
        return resultat

    def consommer_mois(self, mois_consomme):
        """Consomme un mois d'avance"""
        if self.statut != 'active':
            return False
        
        # Vérifier si le mois est dans la période de couverture
        if not self.est_mois_couvert(mois_consomme):
            return False
        
        # Consommer le loyer mensuel (conversion en Decimal)
        loyer_decimal = Decimal(str(self.loyer_mensuel))
        montant_restant_decimal = Decimal(str(self.montant_restant))
        self.montant_restant = montant_restant_decimal - loyer_decimal
        
        # Mettre à jour le statut
        if self.montant_restant <= 0:
            self.statut = 'epuisee'
            self.montant_restant = Decimal('0')
        
        self.save()
        return True
    
    def est_mois_couvert(self, mois):
        """Vérifie si un mois est couvert par cette avance"""
        if not self.mois_debut_couverture or not self.mois_fin_couverture:
            return False
        
        mois_debut = self.mois_debut_couverture.replace(day=1)
        mois_fin = self.mois_fin_couverture.replace(day=1)
        mois_test = mois.replace(day=1)
        
        return mois_debut <= mois_test <= mois_fin
    
    def get_mois_couverts_liste(self):
        """Retourne la liste des mois couverts"""
        if not self.mois_debut_couverture or not self.mois_fin_couverture:
            return []
        
        mois_liste = []
        mois_courant = self.mois_debut_couverture.replace(day=1)
        mois_fin = self.mois_fin_couverture.replace(day=1)
        
        while mois_courant <= mois_fin:
            mois_liste.append(mois_courant)
            mois_courant = mois_courant + relativedelta(months=1)
        
        return mois_liste
    
    def get_montant_par_mois(self):
        """Retourne le montant par mois (loyer mensuel)"""
        return self.loyer_mensuel
    
    def get_montant_restant_apres_mois(self, mois):
        """Calcule le montant restant après avoir consommé jusqu'à un mois donné"""
        if not self.est_mois_couvert(mois):
            return self.montant_restant
        
        # Calculer le nombre de mois consommés depuis le début
        mois_debut = self.mois_debut_couverture.replace(day=1)
        mois_test = mois.replace(day=1)
        
        # Calculer la différence en mois
        diff_mois = (mois_test.year - mois_debut.year) * 12 + (mois_test.month - mois_debut.month)
        
        # Calculer le montant consommé
        montant_consomme = diff_mois * self.loyer_mensuel
        
        # Retourner le montant restant
        return max(self.montant_avance - montant_consomme, Decimal('0'))
    
    def est_mois_consomme(self, mois):
        """Vérifie si un mois spécifique a été consommé"""
        from .models_avance import ConsommationAvance
        return ConsommationAvance.objects.filter(
            avance=self,
            mois_consomme__year=mois.year,
            mois_consomme__month=mois.month
        ).exists()


class ConsommationAvance(models.Model):
    """
    Modèle pour tracer la consommation des avances mois par mois
    """
    # Relations
    avance = models.ForeignKey(
        AvanceLoyer,
        on_delete=models.CASCADE,
        related_name='consommations',
        verbose_name=_("Avance")
    )
    
    paiement = models.ForeignKey(
        'Paiement',
        on_delete=models.CASCADE,
        related_name='consommations_avance',
        null=True,
        blank=True,
        verbose_name=_("Paiement")
    )
    
    # Mois consommé
    mois_consomme = models.DateField(
        verbose_name=_("Mois consommé")
    )
    
    # Montant consommé
    montant_consomme = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Montant consommé")
    )
    
    # Montant restant après consommation
    montant_restant_apres = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name=_("Montant restant après")
    )
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        app_label = 'paiements'
        verbose_name = _("Consommation d'avance")
        verbose_name_plural = _("Consommations d'avance")
        ordering = ['-mois_consomme']
        unique_together = ['avance', 'mois_consomme']
    
    def __str__(self):
        return f"Consommation {self.mois_consomme.strftime('%B %Y')} - {self.montant_consomme} F CFA"


class HistoriquePaiement(models.Model):
    """
    Modèle pour l'historique détaillé des paiements
    """
    # Relations
    contrat = models.ForeignKey(
        Contrat,
        on_delete=models.CASCADE,
        related_name='historique_paiements',
        verbose_name=_("Contrat")
    )
    
    # Paiement original
    paiement = models.ForeignKey(
        'Paiement',
        on_delete=models.CASCADE,
        related_name='historique',
        verbose_name=_("Paiement")
    )
    
    # Mois concerné
    mois_paiement = models.DateField(
        verbose_name=_("Mois du paiement")
    )
    
    # Montants
    montant_paye = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Montant payé")
    )
    
    montant_du = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Montant dû")
    )
    
    montant_avance_utilisee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_("Montant d'avance utilisée")
    )
    
    montant_restant_du = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_("Montant restant dû")
    )
    
    # Statut du mois
    mois_regle = models.BooleanField(
        default=False,
        verbose_name=_("Mois réglé")
    )
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        app_label = 'paiements'
        verbose_name = _("Historique de paiement")
        verbose_name_plural = _("Historiques de paiement")
        ordering = ['-mois_paiement']
        unique_together = ['contrat', 'mois_paiement']
    
    def __str__(self):
        return f"Historique {self.mois_paiement.strftime('%B %Y')} - {self.contrat.locataire.get_nom_complet()}"
