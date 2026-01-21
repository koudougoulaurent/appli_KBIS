"""
Commande pour resynchroniser complètement toutes les avances
Garantit la cohérence parfaite entre Paiement(type='avance') et AvanceLoyer
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from paiements.models_avance import AvanceLoyer
from paiements.models import Paiement
from paiements.services_synchronisation_avances import ServiceSynchronisationAvances
from datetime import datetime


class Command(BaseCommand):
    help = "Resynchronise complètement toutes les avances pour garantir la cohérence"

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Affiche les modifications sans les appliquer',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING("MODE DRY-RUN - Aucune modification"))
        
        self.stdout.write("\n" + "=" * 80)
        self.stdout.write("RESYNCHRONISATION COMPLÈTE DES AVANCES")
        self.stdout.write("=" * 80 + "\n")
        
        # Étape 1 : Supprimer les avances orphelines (sans paiement correspondant)
        self.stdout.write("\n1. Nettoyage des avances orphelines...")
        
        avances_orphelines = AvanceLoyer.objects.filter(paiement__isnull=True)
        count_orphelines = avances_orphelines.count()
        
        if count_orphelines > 0:
            self.stdout.write(f"   Trouvé {count_orphelines} avance(s) orpheline(s)")
            if not dry_run:
                avances_orphelines.delete()
                self.stdout.write(self.style.SUCCESS(f"   ✓ {count_orphelines} avance(s) supprimée(s)"))
        else:
            self.stdout.write("   Aucune avance orpheline")
        
        # Étape 2 : Vérifier tous les paiements d'avance
        self.stdout.write("\n2. Vérification des paiements d'avance...")
        
        paiements_avance = Paiement.objects.filter(
            type_paiement='avance',
            statut='valide',
            is_deleted=False
        ).select_related('contrat', 'contrat__locataire')
        
        total_paiements = paiements_avance.count()
        self.stdout.write(f"   Trouvé {total_paiements} paiement(s) d'avance validé(s)")
        
        # Étape 3 : Synchroniser chaque paiement
        self.stdout.write("\n3. Synchronisation des paiements...")
        
        sync_ok = 0
        sync_créés = 0
        sync_mis_à_jour = 0
        sync_erreurs = 0
        
        for paiement in paiements_avance:
            try:
                # Vérifier si une avance existe déjà
                avance_existe = AvanceLoyer.objects.filter(paiement=paiement).exists()
                
                if not dry_run:
                    # Synchroniser (créer ou mettre à jour)
                    avance = ServiceSynchronisationAvances.synchroniser_avance_avec_paiement(paiement)
                    
                    if avance:
                        sync_ok += 1
                        if avance_existe:
                            sync_mis_à_jour += 1
                        else:
                            sync_créés += 1
                            self.stdout.write(
                                f"   ✓ Avance créée pour paiement {paiement.id} "
                                f"(Contrat: {paiement.contrat.locataire.get_nom_complet()}, "
                                f"{paiement.montant} F CFA)"
                            )
                    else:
                        sync_erreurs += 1
                        self.stdout.write(self.style.ERROR(
                            f"   ✗ Erreur pour paiement {paiement.id}"
                        ))
                else:
                    # Dry-run : juste compter
                    if avance_existe:
                        sync_mis_à_jour += 1
                    else:
                        sync_créés += 1
                        self.stdout.write(
                            f"   [DRY-RUN] Avance serait créée pour paiement {paiement.id}"
                        )
                    sync_ok += 1
                    
            except Exception as e:
                sync_erreurs += 1
                self.stdout.write(self.style.ERROR(
                    f"   ✗ Erreur paiement {paiement.id}: {str(e)}"
                ))
        
        # Étape 4 : Corriger les statuts d'avances
        self.stdout.write("\n4. Correction des statuts d'avances...")
        
        today = datetime.now().date().replace(day=1)
        
        # 4a. Avances actives avec montant_restant = 0
        avances_vides = AvanceLoyer.objects.filter(
            statut='active',
            montant_restant__lte=0
        )
        count_vides = avances_vides.count()
        
        if count_vides > 0:
            self.stdout.write(f"   Trouvé {count_vides} avance(s) active(s) avec montant_restant = 0")
            if not dry_run:
                avances_vides.update(statut='epuisee')
                self.stdout.write(self.style.SUCCESS(f"   ✓ {count_vides} avance(s) marquée(s) comme 'epuisee'"))
        
        # 4b. Avances épuisées avec montant_restant > 0 ET date non expirée
        avances_incorrectes = AvanceLoyer.objects.filter(
            statut='epuisee',
            montant_restant__gt=0,
            mois_fin_couverture__gte=today
        )
        count_incorrectes = avances_incorrectes.count()
        
        if count_incorrectes > 0:
            self.stdout.write(f"   Trouvé {count_incorrectes} avance(s) incorrectement marquée(s) 'epuisee'")
            if not dry_run:
                avances_incorrectes.update(statut='active')
                self.stdout.write(self.style.SUCCESS(f"   ✓ {count_incorrectes} avance(s) réactivée(s)"))
        
        # Résumé
        self.stdout.write("\n" + "=" * 80)
        self.stdout.write("RÉSUMÉ DE LA SYNCHRONISATION")
        self.stdout.write("=" * 80)
        self.stdout.write(f"\nPaiements d'avance traités : {total_paiements}")
        self.stdout.write(f"  - Synchronisations OK : {sync_ok}")
        self.stdout.write(f"  - Avances créées : {sync_créés}")
        self.stdout.write(f"  - Avances mises à jour : {sync_mis_à_jour}")
        self.stdout.write(f"  - Erreurs : {sync_erreurs}")
        
        self.stdout.write(f"\nCorrections de statuts :")
        self.stdout.write(f"  - Avances épuisées (montant = 0) : {count_vides}")
        self.stdout.write(f"  - Avances réactivées (montant > 0) : {count_incorrectes}")
        
        self.stdout.write(f"\nAvances orphelines supprimées : {count_orphelines}")
        
        if dry_run:
            self.stdout.write(self.style.WARNING("\nDRY-RUN : Aucune modification appliquée"))
            self.stdout.write("Relancez sans --dry-run pour appliquer les modifications")
        else:
            self.stdout.write(self.style.SUCCESS("\n✓ Resynchronisation terminée avec succès !"))
        
        self.stdout.write("\n" + "=" * 80 + "\n")
