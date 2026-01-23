"""
Commande pour appliquer la logique unique des avances partout
=============================================================

Cette commande :
1. Resynchronise toutes les avances avec la logique unique
2. Corrige les incohérences entre les différents systèmes
3. S'assure que toutes les avances suivent la même logique métier
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from paiements.models_avance import AvanceLoyer
from paiements.models import Paiement
from paiements.services_logique_avance_unique import ServiceLogiqueAvanceUnique
from datetime import datetime


class Command(BaseCommand):
    help = "Applique la logique unique des avances partout et resynchronise"

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Affiche les modifications sans les appliquer',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Affiche tous les détails',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        verbose = options['verbose']
        
        if dry_run:
            self.stdout.write(self.style.WARNING("\n" + "="*80))
            self.stdout.write(self.style.WARNING("MODE DRY-RUN - Aucune modification ne sera appliquée"))
            self.stdout.write(self.style.WARNING("="*80 + "\n"))
        
        self.stdout.write("\n" + "="*80)
        self.stdout.write("APPLICATION DE LA LOGIQUE UNIQUE DES AVANCES")
        self.stdout.write("="*80 + "\n")
        
        # Étape 1 : Vérifier les paiements d'avance sans AvanceLoyer
        self.stdout.write("\n1. Vérification des paiements d'avance sans objet AvanceLoyer...")
        
        paiements_sans_avance = Paiement.objects.filter(
            type_paiement='avance',
            statut='valide',
            is_deleted=False
        ).select_related('contrat', 'contrat__locataire')
        
        paiements_manquants = []
        for paiement in paiements_sans_avance:
            if not AvanceLoyer.objects.filter(paiement=paiement).exists():
                paiements_manquants.append(paiement)
        
        if paiements_manquants:
            self.stdout.write(f"   Trouvé {len(paiements_manquants)} paiement(s) sans AvanceLoyer")
            
            if not dry_run:
                for paiement in paiements_manquants:
                    try:
                        avance = ServiceLogiqueAvanceUnique.creer_avance_avec_logique_unique(
                            contrat=paiement.contrat,
                            montant_avance=paiement.montant,
                            date_avance=paiement.date_paiement,
                            notes=f"Créé automatiquement par resynchronisation - Paiement #{paiement.id}",
                            paiement=paiement
                        )
                        self.stdout.write(self.style.SUCCESS(
                            f"   ✓ Avance créée pour paiement #{paiement.id} "
                            f"(Contrat: {paiement.contrat.locataire.get_nom_complet()})"
                        ))
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(
                            f"   ✗ Erreur paiement #{paiement.id}: {str(e)}"
                        ))
            else:
                for paiement in paiements_manquants:
                    self.stdout.write(
                        f"   [DRY-RUN] Créerait avance pour paiement #{paiement.id} "
                        f"({paiement.montant} F CFA, contrat {paiement.contrat.locataire.get_nom_complet()})"
                    )
        else:
            self.stdout.write("   Aucun paiement sans AvanceLoyer")
        
        # Étape 2 : Resynchroniser toutes les avances existantes
        self.stdout.write("\n2. Resynchronisation de toutes les avances avec logique unique...")
        
        avances = AvanceLoyer.objects.select_related(
            'contrat',
            'contrat__locataire',
            'paiement'
        ).order_by('contrat__id', 'date_avance')
        
        total_avances = avances.count()
        self.stdout.write(f"   Trouvé {total_avances} avance(s) à resynchroniser")
        
        avances_modifiees = 0
        avances_ok = 0
        avances_erreurs = 0
        
        for avance in avances:
            try:
                # Sauvegarder les valeurs actuelles
                ancien_mois_debut = avance.mois_debut_couverture
                ancien_mois_fin = avance.mois_fin_couverture
                ancien_nombre_mois = avance.nombre_mois_couverts
                
                # Calculer la nouvelle logique
                # NOTE: On ne modifie PAS le mois de début pour les avances existantes
                # On recalcule seulement le nombre de mois et le mois de fin
                from decimal import Decimal
                
                loyer_mensuel = Decimal(str(avance.contrat.loyer_mensuel)) if avance.contrat.loyer_mensuel else Decimal('0')
                montant_avance = Decimal(str(avance.montant_avance))
                
                if loyer_mensuel <= 0:
                    if verbose:
                        self.stdout.write(f"   ⚠️  Avance #{avance.id}: Loyer mensuel invalide, skip")
                    continue
                
                # Recalculer avec la logique unique
                nombre_mois, reste = ServiceLogiqueAvanceUnique.calculer_nombre_mois_couverts(
                    montant_avance, loyer_mensuel
                )
                
                mois_fin = ServiceLogiqueAvanceUnique.calculer_mois_fin_couverture(
                    avance.mois_debut_couverture, nombre_mois
                )
                
                # Vérifier si quelque chose a changé
                a_change = (
                    avance.mois_fin_couverture != mois_fin or
                    avance.nombre_mois_couverts != nombre_mois or
                    abs(avance.loyer_mensuel - loyer_mensuel) > Decimal('0.01')
                )
                
                if a_change:
                    avances_modifiees += 1
                    
                    if verbose or dry_run:
                        self.stdout.write(f"\n   Avance #{avance.id} ({avance.contrat.locataire.get_nom_complet()}):")
                        self.stdout.write(f"     Date avance: {avance.date_avance}")
                        self.stdout.write(f"     Montant: {montant_avance} F CFA")
                        
                        if avance.mois_debut_couverture != ancien_mois_debut:
                            self.stdout.write(self.style.WARNING(
                                f"     Début: {ancien_mois_debut} → {avance.mois_debut_couverture}"
                            ))
                        
                        if avance.mois_fin_couverture != mois_fin:
                            self.stdout.write(self.style.WARNING(
                                f"     Fin: {ancien_mois_fin} → {mois_fin}"
                            ))
                        
                        if avance.nombre_mois_couverts != nombre_mois:
                            self.stdout.write(self.style.WARNING(
                                f"     Mois couverts: {ancien_nombre_mois} → {nombre_mois}"
                            ))
                    
                    if not dry_run:
                        avance.loyer_mensuel = loyer_mensuel
                        avance.nombre_mois_couverts = nombre_mois
                        avance.montant_reste = reste
                        avance.mois_fin_couverture = mois_fin
                        avance.save()
                        
                        if verbose:
                            self.stdout.write(self.style.SUCCESS("     ✓ Modifiée"))
                else:
                    avances_ok += 1
                    if verbose:
                        self.stdout.write(f"   ✓ Avance #{avance.id}: Déjà cohérente")
                    
            except Exception as e:
                avances_erreurs += 1
                self.stdout.write(self.style.ERROR(
                    f"   ✗ Erreur avance #{avance.id}: {str(e)}"
                ))
        
        # Étape 3 : Vérifier les cohérences
        self.stdout.write("\n3. Vérification des cohérences finales...")
        
        # Vérifier que toutes les avances ont un paiement
        avances_sans_paiement = AvanceLoyer.objects.filter(paiement__isnull=True).count()
        if avances_sans_paiement > 0:
            self.stdout.write(self.style.WARNING(
                f"   ⚠️  {avances_sans_paiement} avance(s) sans paiement associé"
            ))
        
        # Vérifier que tous les paiements d'avance ont une AvanceLoyer
        paiements_avance_total = Paiement.objects.filter(
            type_paiement='avance',
            statut='valide',
            is_deleted=False
        ).count()
        
        avances_total = AvanceLoyer.objects.count()
        
        if paiements_avance_total != avances_total:
            self.stdout.write(self.style.WARNING(
                f"   ⚠️  Incohérence: {paiements_avance_total} paiements d'avance "
                f"mais {avances_total} objets AvanceLoyer"
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                f"   ✓ Cohérence OK: {paiements_avance_total} paiements = {avances_total} avances"
            ))
        
        # Résumé
        self.stdout.write("\n" + "="*80)
        self.stdout.write("RÉSUMÉ")
        self.stdout.write("="*80)
        self.stdout.write(f"\nPaiements sans AvanceLoyer:")
        self.stdout.write(f"  - Trouvés: {len(paiements_manquants)}")
        if not dry_run and len(paiements_manquants) > 0:
            self.stdout.write(f"  - Créés: {len(paiements_manquants)}")
        
        self.stdout.write(f"\nAvances resynchronisées:")
        self.stdout.write(f"  - Total traité: {total_avances}")
        self.stdout.write(f"  - Modifiées: {avances_modifiees}")
        self.stdout.write(f"  - Déjà OK: {avances_ok}")
        self.stdout.write(f"  - Erreurs: {avances_erreurs}")
        
        if dry_run:
            self.stdout.write(self.style.WARNING("\nDRY-RUN : Aucune modification appliquée"))
            self.stdout.write("Relancez sans --dry-run pour appliquer les modifications")
        else:
            self.stdout.write(self.style.SUCCESS("\n✓ Logique unique appliquée avec succès !"))
        
        self.stdout.write("\n" + "="*80 + "\n")
