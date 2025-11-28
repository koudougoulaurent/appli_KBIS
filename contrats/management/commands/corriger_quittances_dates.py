"""
Commande de management pour corriger les dates des quittances
Corrige les quittances avec des dates incorrectes (ex: janvier 2025 après décembre 2025)
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from dateutil.relativedelta import relativedelta
from datetime import date
from contrats.models import Quittance
from paiements.models import Paiement


class Command(BaseCommand):
    help = 'Corrige les dates des quittances avec des années incorrectes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Affiche les corrections sans les appliquer',
        )
        parser.add_argument(
            '--contrat-id',
            type=int,
            help='Corriger uniquement les quittances d\'un contrat spécifique',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        contrat_id = options.get('contrat_id')
        
        self.stdout.write(self.style.SUCCESS('=== Correction des dates de quittances ===\n'))
        
        # Récupérer toutes les quittances
        queryset = Quittance.objects.all().select_related('contrat')
        if contrat_id:
            queryset = queryset.filter(contrat_id=contrat_id)
        
        quittances = queryset.order_by('contrat', 'mois')
        
        corrections = []
        total_quittances = quittances.count()
        
        self.stdout.write(f'Nombre de quittances à vérifier: {total_quittances}\n')
        
        # Grouper par contrat pour vérifier la cohérence
        quittances_par_contrat = {}
        for quittance in quittances:
            contrat_id = quittance.contrat.id
            if contrat_id not in quittances_par_contrat:
                quittances_par_contrat[contrat_id] = []
            quittances_par_contrat[contrat_id].append(quittance)
        
        for contrat_id, quittances_contrat in quittances_par_contrat.items():
            # Trier par mois
            quittances_contrat.sort(key=lambda q: q.mois)
            
            for i, quittance in enumerate(quittances_contrat):
                mois_quittance = quittance.mois
                
                # Vérifier si c'est janvier et si la quittance précédente était décembre
                if mois_quittance.month == 1 and i > 0:
                    quittance_precedente = quittances_contrat[i - 1]
                    mois_precedent = quittance_precedente.mois
                    
                    # Si la quittance précédente était décembre de l'année précédente
                    # et que la quittance actuelle est janvier de la même année que décembre
                    # alors il faut corriger l'année
                    if mois_precedent.month == 12:
                        annee_attendue = mois_precedent.year + 1
                        annee_actuelle = mois_quittance.year
                        
                        if annee_actuelle < annee_attendue:
                            # Vérifier aussi les paiements pour confirmer
                            paiements_decembre = Paiement.objects.filter(
                                contrat=quittance.contrat,
                                date_paiement__year=mois_precedent.year,
                                date_paiement__month=12,
                                statut='valide'
                            ).exists()
                            
                            if paiements_decembre or mois_precedent.year >= 2024:
                                # Correction nécessaire
                                nouvelle_date = date(annee_attendue, 1, 1)
                                corrections.append({
                                    'quittance': quittance,
                                    'ancienne_date': mois_quittance,
                                    'nouvelle_date': nouvelle_date,
                                    'raison': f'Janvier après décembre {mois_precedent.year}'
                                })
                
                # Vérifier aussi les incohérences générales (mois qui ne suit pas logiquement)
                if i > 0:
                    quittance_precedente = quittances_contrat[i - 1]
                    mois_precedent = quittance_precedente.mois
                    mois_attendu = mois_precedent + relativedelta(months=1)
                    
                    # Normaliser au premier jour du mois
                    mois_attendu = mois_attendu.replace(day=1)
                    mois_quittance_normalise = mois_quittance.replace(day=1)
                    
                    # Si le mois ne suit pas logiquement
                    if mois_quittance_normalise != mois_attendu:
                        # Vérifier si c'est juste une différence d'année (ex: janvier 2025 au lieu de janvier 2026)
                        if (mois_quittance_normalise.month == mois_attendu.month and 
                            mois_quittance_normalise.year < mois_attendu.year):
                            # Correction nécessaire
                            corrections.append({
                                'quittance': quittance,
                                'ancienne_date': mois_quittance,
                                'nouvelle_date': mois_attendu,
                                'raison': f'Mois ne suit pas logiquement après {mois_precedent.strftime("%B %Y")}'
                            })
        
        # Afficher les corrections
        if corrections:
            self.stdout.write(self.style.WARNING(f'\n{len(corrections)} correction(s) nécessaire(s):\n'))
            for corr in corrections:
                self.stdout.write(
                    f"  - Quittance {corr['quittance'].numero_quittance} "
                    f"(Contrat: {corr['quittance'].contrat.numero_contrat}):\n"
                    f"    {corr['ancienne_date'].strftime('%B %Y')} -> {corr['nouvelle_date'].strftime('%B %Y')}\n"
                    f"    Raison: {corr['raison']}\n"
                )
            
            if not dry_run:
                # Appliquer les corrections
                self.stdout.write(self.style.SUCCESS('\nApplication des corrections...\n'))
                with transaction.atomic():
                    for corr in corrections:
                        corr['quittance'].mois = corr['nouvelle_date']
                        corr['quittance'].save()
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"[OK] Corrige: {corr['quittance'].numero_quittance} "
                                f"-> {corr['nouvelle_date'].strftime('%B %Y')}"
                            )
                        )
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'\n[OK] {len(corrections)} quittance(s) corrigee(s) avec succes!'
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        '\n[DRY-RUN] Mode dry-run: aucune modification appliquee. '
                        'Utilisez sans --dry-run pour appliquer les corrections.'
                    )
                )
        else:
            self.stdout.write(self.style.SUCCESS('\n[OK] Aucune correction necessaire!'))

