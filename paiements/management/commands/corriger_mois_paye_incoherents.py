"""
Commande pour corriger automatiquement les mois_paye incohérents
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from paiements.models import Paiement
from datetime import datetime


class Command(BaseCommand):
    help = 'Corrige les paiements avec mois_paye incoherent par rapport a la sequence des paiements'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Affiche les corrections sans les appliquer',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)

        self.stdout.write(self.style.SUCCESS('\n' + '='*80))
        self.stdout.write(self.style.SUCCESS('CORRECTION DES MOIS_PAYE INCOHERENTS'))
        self.stdout.write(self.style.SUCCESS('='*80 + '\n'))

        if dry_run:
            self.stdout.write(self.style.WARNING('MODE TEST (DRY-RUN) - Aucune modification ne sera sauvegardee\n'))

        # Récupérer tous les contrats actifs
        from contrats.models import Contrat
        contrats = Contrat.objects.filter(est_actif=True, is_deleted=False)

        total_contrats = contrats.count()
        total_corrections = 0
        stats = {
            'contrats_traites': 0,
            'paiements_corriges': 0,
            'erreurs': 0,
        }

        self.stdout.write(f"{total_contrats} contrat(s) a traiter\n")

        for contrat in contrats:
            try:
                self.stdout.write(f"\n{'-'*80}")
                self.stdout.write(f"Contrat: {contrat}")
                self.stdout.write(f"{'-'*80}")

                # Récupérer tous les paiements de loyer pour ce contrat, triés par date
                paiements = Paiement.objects.filter(
                    contrat=contrat,
                    type_paiement='loyer',
                    statut__in=['valide', 'confirme'],
                    is_deleted=False
                ).exclude(
                    mois_paye__isnull=True
                ).exclude(
                    mois_paye=''
                ).order_by('date_paiement', 'id')

                if not paiements.exists():
                    self.stdout.write("  Aucun paiement de loyer pour ce contrat")
                    continue

                stats['contrats_traites'] += 1

                # Pour chaque paiement, vérifier la cohérence
                dernier_mois_attendu = None

                for paiement in paiements:
                    # Parser le mois_paye actuel
                    try:
                        # Format attendu : "janvier 2026" ou "January 2026"
                        mois_paye_str = paiement.mois_paye
                        
                        # Conversion en date pour comparaison
                        from .services_paiement_partiel import ServicePaiementPartiel
                        
                        # Si c'est le premier paiement, on ne peut pas vérifier la cohérence
                        if dernier_mois_attendu is None:
                            # Utiliser le mois_paye tel quel
                            mois_francais = {
                                'janvier': 1, 'février': 2, 'fevrier': 2, 'mars': 3, 'avril': 4,
                                'mai': 5, 'juin': 6, 'juillet': 7, 'août': 8, 'aout': 8,
                                'septembre': 9, 'octobre': 10, 'novembre': 11, 'décembre': 12, 'decembre': 12,
                                'january': 1, 'february': 2, 'march': 3, 'april': 4, 'may': 5,
                                'june': 6, 'july': 7, 'august': 8, 'september': 9, 'october': 10,
                                'november': 11, 'december': 12
                            }
                            
                            parts = mois_paye_str.lower().split()
                            if len(parts) >= 2:
                                mois_nom = parts[0]
                                annee = int(parts[1])
                                mois_num = mois_francais.get(mois_nom, 1)
                                dernier_mois_attendu = datetime(annee, mois_num, 1).date()
                                
                                self.stdout.write(f"  Premier paiement: {paiement.id} - {mois_paye_str} - OK")
                                continue
                            else:
                                self.stdout.write(self.style.WARNING(f"  Paiement {paiement.id}: Format mois_paye invalide: {mois_paye_str}"))
                                continue
                        
                        # Pour les paiements suivants, vérifier qu'ils suivent la séquence
                        # Le mois attendu = dernier_mois_attendu + 1 mois
                        from dateutil.relativedelta import relativedelta
                        mois_attendu = dernier_mois_attendu + relativedelta(months=1)
                        
                        # Parser le mois_paye actuel du paiement
                        parts = mois_paye_str.lower().split()
                        if len(parts) >= 2:
                            mois_nom = parts[0]
                            annee_actuelle = int(parts[1])
                            mois_num_actuel = mois_francais.get(mois_nom, 1)
                            mois_actuel = datetime(annee_actuelle, mois_num_actuel, 1).date()
                            
                            # Comparer avec le mois attendu
                            if mois_actuel != mois_attendu:
                                # Incohérence détectée !
                                mois_attendu_str_fr = [
                                    'janvier', 'février', 'mars', 'avril', 'mai', 'juin',
                                    'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre'
                                ][mois_attendu.month - 1]
                                mois_attendu_str = f"{mois_attendu_str_fr} {mois_attendu.year}"
                                
                                self.stdout.write(self.style.ERROR(
                                    f"  INCOH ERENCE - Paiement {paiement.id}:"
                                ))
                                self.stdout.write(f"    Actuel: {mois_paye_str}")
                                self.stdout.write(f"    Attendu: {mois_attendu_str}")
                                self.stdout.write(f"    Date paiement: {paiement.date_paiement}")
                                
                                if not dry_run:
                                    # Corriger
                                    paiement.mois_paye = mois_attendu_str
                                    paiement.save(update_fields=['mois_paye'])
                                    self.stdout.write(self.style.SUCCESS(f"    CORRIGE: {mois_attendu_str}"))
                                    stats['paiements_corriges'] += 1
                                else:
                                    self.stdout.write(self.style.WARNING(f"    A CORRIGER (dry-run)"))
                                    stats['paiements_corriges'] += 1
                                
                                # Mettre à jour le dernier mois attendu
                                dernier_mois_attendu = mois_attendu
                            else:
                                # Cohérent
                                self.stdout.write(f"  Paiement {paiement.id}: {mois_paye_str} - OK")
                                dernier_mois_attendu = mois_actuel
                        else:
                            self.stdout.write(self.style.WARNING(f"  Paiement {paiement.id}: Format mois_paye invalide: {mois_paye_str}"))
                            
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"  Erreur paiement {paiement.id}: {str(e)}"))
                        stats['erreurs'] += 1
                        continue

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Erreur contrat {contrat.id}: {str(e)}"))
                stats['erreurs'] += 1
                continue

        # Résumé
        self.stdout.write(f"\n\n{'='*80}")
        self.stdout.write(self.style.SUCCESS('RESUME'))
        self.stdout.write(f"{'='*80}\n")
        self.stdout.write(f"Contrats traites: {stats['contrats_traites']}")
        self.stdout.write(self.style.SUCCESS(f"Paiements corriges: {stats['paiements_corriges']}"))
        
        if stats['erreurs'] > 0:
            self.stdout.write(self.style.ERROR(f"Erreurs: {stats['erreurs']}"))
        
        if dry_run and stats['paiements_corriges'] > 0:
            self.stdout.write(self.style.WARNING(f"\nPour appliquer les corrections, relancez sans --dry-run"))
        
        self.stdout.write(f"\n{'='*80}\n")
        
        if not dry_run and stats['paiements_corriges'] > 0:
            self.stdout.write(self.style.SUCCESS(f"Traitement termine avec succes !"))
        else:
            self.stdout.write(self.style.WARNING(f"Mode test - Aucune modification enregistree"))
