"""
Commande Django pour corriger les paiements existants et ajouter les informations détaillées
dans les notes des paiements pour améliorer l'affichage des récépissés.
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from paiements.models import Paiement
from datetime import datetime
from dateutil.relativedelta import relativedelta


class Command(BaseCommand):
    help = 'Corrige les paiements existants en ajoutant des informations détaillées'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Affiche ce qui serait fait sans effectuer les modifications',
        )

    def calculer_mois_couverts_avance(self, paiement):
        """Calcule les mois couverts par une avance de loyer."""
        try:
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
            date_paiement = paiement.date_paiement
            mois_couverts = []
            
            # Dictionnaire de traduction des mois en français
            mois_francais = {
                1: 'Janvier', 2: 'Février', 3: 'Mars', 4: 'Avril',
                5: 'Mai', 6: 'Juin', 7: 'Juillet', 8: 'Août',
                9: 'Septembre', 10: 'Octobre', 11: 'Novembre', 12: 'Décembre'
            }
            
            for i in range(nombre_mois):
                mois_date = date_paiement + relativedelta(months=i)
                mois_nom = mois_francais.get(mois_date.month, mois_date.strftime("%B"))
                mois_couverts.append(f"{mois_nom} {mois_date.year}")
            
            return {
                'nombre': nombre_mois,
                'mois_liste': mois_couverts,
                'mois_texte': ', '.join(mois_couverts)
            }
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Erreur lors du calcul des mois couverts pour le paiement {paiement.id}: {e}"))
            return None

    def afficher_statistiques(self):
        """Affiche les statistiques des paiements par type."""
        self.stdout.write("\n=== STATISTIQUES DES PAIEMENTS ===")
        
        from django.db import models
        
        stats = Paiement.objects.values('type_paiement').annotate(
            count=models.Count('id'),
            total_montant=models.Sum('montant')
        ).order_by('type_paiement')
        
        for stat in stats:
            type_paiement = stat['type_paiement']
            count = stat['count']
            total = stat['total_montant'] or 0
            self.stdout.write(f"{type_paiement}: {count} paiements, Total: {total:,.0f} F CFA")

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        self.stdout.write("=== CORRECTION DES PAIEMENTS EXISTANTS ===")
        self.stdout.write(f"Début: {datetime.now()}")
        
        if dry_run:
            self.stdout.write(self.style.WARNING('MODE DRY-RUN - Aucune modification ne sera effectuée'))
        
        # Afficher les statistiques avant correction
        self.afficher_statistiques()
        
        # Récupérer tous les paiements
        paiements = Paiement.objects.select_related('contrat', 'contrat__locataire').all()
        
        self.stdout.write(f"\nNombre total de paiements trouvés: {paiements.count()}")
        
        corrections_effectuees = 0
        erreurs = 0
        
        if not dry_run:
            with transaction.atomic():
                for paiement in paiements:
                    try:
                        nouvelle_note = None
                        
                        if paiement.type_paiement == 'avance':
                            # Pour les avances, calculer les mois couverts
                            mois_couverts = self.calculer_mois_couverts_avance(paiement)
                            if mois_couverts:
                                nouvelle_note = f"Avance de loyer - Couvre {mois_couverts['nombre']} mois de loyer ({mois_couverts['mois_texte']}) - Loyer mensuel: {paiement.contrat.loyer_mensuel} F CFA"
                            else:
                                nouvelle_note = f"Avance de loyer - Montant: {paiement.montant} F CFA - Loyer mensuel: {paiement.contrat.loyer_mensuel} F CFA"
                        
                        elif paiement.type_paiement == 'caution':
                            # Pour les cautions
                            nouvelle_note = f"Dépôt de garantie - Montant: {paiement.montant} F CFA - Remboursable en fin de contrat"
                        
                        elif paiement.type_paiement == 'loyer':
                            # Pour les loyers
                            periode = paiement.date_paiement.strftime("%B %Y")
                            nouvelle_note = f"Paiement de loyer - Période: {periode} - Montant: {paiement.montant} F CFA"
                        
                        elif paiement.type_paiement == 'charges':
                            # Pour les charges
                            nouvelle_note = f"Paiement de charges - Montant: {paiement.montant} F CFA"
                        
                        elif paiement.type_paiement == 'regularisation':
                            # Pour les régularisations
                            nouvelle_note = f"Régularisation - Montant: {paiement.montant} F CFA"
                        
                        elif paiement.type_paiement == 'paiement_partiel':
                            # Pour les paiements partiels
                            nouvelle_note = f"Paiement partiel - Montant: {paiement.montant} F CFA"
                        
                        else:
                            # Pour les autres types
                            nouvelle_note = f"Paiement reçu - Montant: {paiement.montant} F CFA - Type: {paiement.get_type_paiement_display()}"
                        
                        # Mettre à jour la note du paiement
                        if nouvelle_note:
                            ancienne_note = paiement.notes or ""
                            if "Document généré en bonne et due forme" in ancienne_note or not ancienne_note.strip():
                                paiement.notes = nouvelle_note
                                paiement.save()
                                corrections_effectuees += 1
                                self.stdout.write(f"✓ Paiement {paiement.id} ({paiement.type_paiement}): {nouvelle_note[:80]}...")
                            else:
                                self.stdout.write(f"- Paiement {paiement.id} ({paiement.type_paiement}): Note déjà personnalisée, ignoré")
                        
                    except Exception as e:
                        erreurs += 1
                        self.stdout.write(self.style.ERROR(f"✗ Erreur pour le paiement {paiement.id}: {e}"))
        else:
            # Mode dry-run : afficher ce qui serait fait
            for paiement in paiements:
                try:
                    nouvelle_note = None
                    
                    if paiement.type_paiement == 'avance':
                        mois_couverts = self.calculer_mois_couverts_avance(paiement)
                        if mois_couverts:
                            nouvelle_note = f"Avance de loyer - Couvre {mois_couverts['nombre']} mois de loyer ({mois_couverts['mois_texte']}) - Loyer mensuel: {paiement.contrat.loyer_mensuel} F CFA"
                        else:
                            nouvelle_note = f"Avance de loyer - Montant: {paiement.montant} F CFA - Loyer mensuel: {paiement.contrat.loyer_mensuel} F CFA"
                    
                    elif paiement.type_paiement == 'caution':
                        nouvelle_note = f"Dépôt de garantie - Montant: {paiement.montant} F CFA - Remboursable en fin de contrat"
                    
                    elif paiement.type_paiement == 'loyer':
                        periode = paiement.date_paiement.strftime("%B %Y")
                        nouvelle_note = f"Paiement de loyer - Période: {periode} - Montant: {paiement.montant} F CFA"
                    
                    else:
                        nouvelle_note = f"Paiement reçu - Montant: {paiement.montant} F CFA - Type: {paiement.get_type_paiement_display()}"
                    
                    if nouvelle_note:
                        ancienne_note = paiement.notes or ""
                        if "Document généré en bonne et due forme" in ancienne_note or not ancienne_note.strip():
                            self.stdout.write(f"[DRY-RUN] ✓ Paiement {paiement.id} ({paiement.type_paiement}): {nouvelle_note[:80]}...")
                        else:
                            self.stdout.write(f"[DRY-RUN] - Paiement {paiement.id} ({paiement.type_paiement}): Note déjà personnalisée, ignoré")
                
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"[DRY-RUN] ✗ Erreur pour le paiement {paiement.id}: {e}"))
        
        self.stdout.write(f"\n=== RÉSULTATS ===")
        self.stdout.write(f"Corrections effectuées: {corrections_effectuees}")
        self.stdout.write(f"Erreurs: {erreurs}")
        self.stdout.write(f"Fin: {datetime.now()}")
        
        if not dry_run:
            self.stdout.write("\n=== STATISTIQUES APRÈS CORRECTION ===")
            self.afficher_statistiques()
