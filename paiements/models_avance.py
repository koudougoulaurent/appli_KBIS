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
    
    # Relations
    contrat = models.ForeignKey(
        Contrat,
        on_delete=models.CASCADE,
        related_name='avances_loyer',
        verbose_name=_("Contrat")
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
        
        # Calculer le nombre de mois complets
        mois_complets = int(self.montant_avance // self.loyer_mensuel)
        
        # Calculer le reste
        reste = self.montant_avance % self.loyer_mensuel
        
        self.nombre_mois_couverts = mois_complets
        
        # Définir les dates de couverture
        self.mois_debut_couverture = self.date_avance.replace(day=1)
        if mois_complets > 0:
            self.mois_fin_couverture = self.mois_debut_couverture + relativedelta(months=mois_complets - 1)
        else:
            self.mois_fin_couverture = self.mois_debut_couverture
        
        # Mettre à jour le statut et le montant restant
        # *** CORRECTION : Une avance est toujours active au début, même si elle couvre exactement des mois complets ***
        self.statut = 'active'  # Toutes les avances commencent comme actives
        self.montant_restant = self.montant_avance  # Le montant restant commence avec le montant total
    
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
            # *** NOUVELLE LOGIQUE : Calculer les mois couverts par l'avance ***
            # 1. Calculer le nombre de mois couverts par l'avance
            nombre_mois = self.nombre_mois_couverts
            
            if nombre_mois <= 0:
                return "Aucun mois couvert"
            
            # 2. Commencer au mois suivant la date d'avance
            mois_debut = self.date_avance.replace(day=1) + relativedelta(months=1)
            
            # 3. Générer la liste des mois couverts par l'avance
            mois_regles = []
            mois_courant = mois_debut
            
            for i in range(nombre_mois):
                mois_regles.append(mois_courant.strftime('%B %Y'))
                mois_courant = mois_courant + relativedelta(months=1)
            
            # 4. Convertir les mois en français
            mois_regles_fr = [self._convertir_mois_francais(mois) for mois in mois_regles]
            
            # 5. Retourner la liste formatée des mois couverts
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
        """Convertit un mois anglais en français"""
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
        
        return resultat

    def consommer_mois(self, mois_consomme):
        """Consomme un mois d'avance"""
        if self.statut != 'active':
            return False
        
        # Vérifier si le mois est dans la période de couverture
        if not self.est_mois_couvert(mois_consomme):
            return False
        
        # Consommer le loyer mensuel
        self.montant_restant -= self.loyer_mensuel
        
        # Mettre à jour le statut
        if self.montant_restant <= 0:
            self.statut = 'epuisee'
        
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
