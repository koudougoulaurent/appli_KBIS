#!/usr/bin/env python
"""
Commande de management pour régénérer tous les récapitulatifs mensuels existants
avec le nouveau format groupé par propriété.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from paiements.models import RecapMensuel
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Regenere tous les recapitulatifs mensuels existants avec le nouveau format groupe par propriete'

    def add_arguments(self, parser):
        parser.add_argument(
            '--recap-id',
            type=int,
            help='ID d\'un recapitulatif specifique a regenerer (optionnel)',
        )
        parser.add_argument(
            '--bailleur-id',
            type=int,
            help='ID d\'un bailleur specifique (regenerer tous ses recaps)',
        )
        parser.add_argument(
            '--mois',
            type=str,
            help='Mois specifique (format: YYYY-MM)',
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=10,
            help='Nombre de recapitulatifs a traiter par batch (defaut: 10)',
        )

    def handle(self, *args, **options):
        recap_id = options.get('recap_id')
        bailleur_id = options.get('bailleur_id')
        mois = options.get('mois')
        batch_size = options.get('batch_size', 10)

        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS('Regeneration des recapitulatifs mensuels avec nouveau format'))
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write('')

        # Récupérer les récapitulatifs à traiter
        recapitulatifs = RecapMensuel.objects.filter(is_deleted=False)
        
        if recap_id:
            try:
                recapitulatifs = RecapMensuel.objects.filter(id=recap_id, is_deleted=False)
                if not recapitulatifs.exists():
                    self.stdout.write(
                        self.style.ERROR(f'Recapitulatif avec ID {recap_id} non trouve')
                    )
                    return
                self.stdout.write(f'Traitement du recapitulatif ID: {recap_id}')
            except RecapMensuel.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Recapitulatif avec ID {recap_id} non trouve')
                )
                return
        elif bailleur_id:
            recapitulatifs = recapitulatifs.filter(bailleur_id=bailleur_id)
            self.stdout.write(f'Traitement des recapitulatifs du bailleur ID: {bailleur_id}')
        elif mois:
            try:
                from datetime import datetime
                date_mois = datetime.strptime(mois, '%Y-%m')
                recapitulatifs = recapitulatifs.filter(
                    mois_recap__year=date_mois.year,
                    mois_recap__month=date_mois.month
                )
                self.stdout.write(f'Traitement des recapitulatifs du mois: {mois}')
            except ValueError:
                self.stdout.write(
                    self.style.ERROR('Format de mois invalide. Utilisez YYYY-MM (ex: 2025-01)')
                )
                return
        
        recapitulatifs = recapitulatifs.select_related('bailleur').order_by('id')
        total = recapitulatifs.count()
        
        if total == 0:
            self.stdout.write(self.style.WARNING('Aucun recapitulatif a traiter'))
            return
            
        self.stdout.write(f'Nombre total de recapitulatifs a traiter: {total}')
        self.stdout.write('')

        # Statistiques
        success_count = 0
        error_count = 0
        skipped_count = 0

        # Traiter les récapitulatifs par batch
        recaps_list = list(recapitulatifs)
        for i in range(0, len(recaps_list), batch_size):
            batch = recaps_list[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (len(recaps_list) + batch_size - 1) // batch_size

            self.stdout.write(
                f'Batch {batch_num}/{total_batches} - Traitement de {len(batch)} recapitulatif(s)...'
            )

            for recap in batch:
                try:
                    # Vérifier que le bailleur existe
                    if not recap.bailleur:
                        skipped_count += 1
                        self.stdout.write(
                            self.style.WARNING(
                                f'  [IGNORE] Recap ID {recap.id} - Pas de bailleur associe'
                            )
                        )
                        continue
                    
                    # Recalculer les totaux pour mettre à jour avec les dernières données
                    recap.calculer_totaux_bailleur()
                    
                    success_count += 1
                    bailleur_nom = recap.bailleur.get_nom_complet()
                    mois_nom = recap.mois_recap.strftime('%B %Y')
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'  [OK] Recap ID {recap.id} - {bailleur_nom} - {mois_nom}'
                        )
                    )

                except Exception as e:
                    error_count += 1
                    logger.error(
                        f'Erreur lors de la regeneration du recapitulatif {recap.id}: {str(e)}',
                        exc_info=True
                    )
                    self.stdout.write(
                        self.style.ERROR(
                            f'  [ERREUR] Recap ID {recap.id} - Erreur: {str(e)}'
                        )
                    )

            # Afficher la progression
            processed = min(i + batch_size, len(recaps_list))
            self.stdout.write(
                f'Progression: {processed}/{len(recaps_list)} recapitulatifs traites'
            )
            self.stdout.write('')

        # Résumé final
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS('Resume de la regeneration'))
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(f'Total de recapitulatifs traites: {len(recaps_list)}')
        self.stdout.write(
            self.style.SUCCESS(f'[OK] Recapitulatifs recalcules avec succes: {success_count}')
        )
        if error_count > 0:
            self.stdout.write(
                self.style.ERROR(f'[ERREUR] Erreurs: {error_count}')
            )
        if skipped_count > 0:
            self.stdout.write(
                self.style.WARNING(f'[IGNORE] Recapitulatifs ignores: {skipped_count}')
            )
        self.stdout.write('')
        self.stdout.write(
            self.style.SUCCESS(
                'Les recapitulatifs ont ete recalcules et utiliseront le nouveau format lors de la generation PDF!'
            )
        )
        self.stdout.write('')
        self.stdout.write(
            self.style.SUCCESS(
                'NOTE: Le nouveau format sera applique automatiquement lors de la prochaine generation PDF'
            )
        )

