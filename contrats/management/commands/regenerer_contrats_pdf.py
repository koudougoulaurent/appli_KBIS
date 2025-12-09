#!/usr/bin/env python
"""
Commande de management pour régénérer tous les PDFs des contrats existants
avec la nouvelle logique corrigée pour l'affichage des champs remplis.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from contrats.models import Contrat
from contrats.services import ContratPDFService
from core.pdf_cache import PDFCacheManager
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Régénère tous les PDFs des contrats existants avec la logique corrigée'

    def add_arguments(self, parser):
        parser.add_argument(
            '--contrat-id',
            type=int,
            help='ID d\'un contrat spécifique à régénérer (optionnel)',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force la régénération même si le cache existe',
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=10,
            help='Nombre de contrats à traiter par batch (défaut: 10)',
        )

    def handle(self, *args, **options):
        contrat_id = options.get('contrat_id')
        force = options.get('force', False)
        batch_size = options.get('batch_size', 10)

        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('Régénération des PDFs des contrats'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write('')

        # Récupérer les contrats à traiter
        if contrat_id:
            try:
                contrats = [Contrat.objects.get(id=contrat_id)]
                self.stdout.write(f'Traitement du contrat ID: {contrat_id}')
            except Contrat.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Contrat avec ID {contrat_id} non trouvé')
                )
                return
        else:
            contrats = Contrat.objects.all().order_by('id')
            total = contrats.count()
            self.stdout.write(f'Nombre total de contrats à traiter: {total}')
            self.stdout.write('')

        # Statistiques
        success_count = 0
        error_count = 0
        skipped_count = 0

        # Traiter les contrats par batch
        for i in range(0, len(contrats), batch_size):
            batch = contrats[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (len(contrats) + batch_size - 1) // batch_size

            self.stdout.write(
                f'Batch {batch_num}/{total_batches} - Traitement de {len(batch)} contrat(s)...'
            )

            for contrat in batch:
                try:
                    # Invalider le cache si demandé ou si force est activé
                    if force:
                        PDFCacheManager.invalidate_cache('contrat', contrat.id)

                    # Générer le PDF avec use_cache=False pour forcer la régénération
                    service = ContratPDFService(contrat)
                    pdf_buffer = service.generate_contrat_pdf(use_cache=False)

                    if pdf_buffer:
                        success_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'  [OK] Contrat {contrat.numero_contrat} (ID: {contrat.id}) - PDF regenere'
                            )
                        )
                    else:
                        error_count += 1
                        self.stdout.write(
                            self.style.ERROR(
                                f'  [ERREUR] Contrat {contrat.numero_contrat} (ID: {contrat.id}) - Erreur lors de la generation'
                            )
                        )

                except Exception as e:
                    error_count += 1
                    logger.error(
                        f'Erreur lors de la regeneration du PDF pour le contrat {contrat.id}: {str(e)}',
                        exc_info=True
                    )
                    self.stdout.write(
                        self.style.ERROR(
                            f'  [ERREUR] Contrat {contrat.numero_contrat} (ID: {contrat.id}) - Erreur: {str(e)}'
                        )
                    )

            # Afficher la progression
            processed = min(i + batch_size, len(contrats))
            self.stdout.write(
                f'Progression: {processed}/{len(contrats)} contrats traités'
            )
            self.stdout.write('')

        # Résumé final
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('Résumé de la régénération'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(f'Total de contrats traites: {len(contrats)}')
        self.stdout.write(
            self.style.SUCCESS(f'[OK] PDFs regeneres avec succes: {success_count}')
        )
        if error_count > 0:
            self.stdout.write(
                self.style.ERROR(f'[ERREUR] Erreurs: {error_count}')
            )
        if skipped_count > 0:
            self.stdout.write(
                self.style.WARNING(f'[IGNORE] Contrats ignores: {skipped_count}')
            )
        self.stdout.write('')
        self.stdout.write(
            self.style.SUCCESS(
                'Tous les PDFs ont ete regeneres avec la nouvelle logique corrigee!'
            )
        )

