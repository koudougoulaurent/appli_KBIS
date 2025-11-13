"""
Commande de management pour corriger les statuts de disponibilité
des unités locatives et des propriétés en fonction des contrats actifs.
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from proprietes.models import Propriete, UniteLocative
from contrats.models import Contrat


class Command(BaseCommand):
    help = 'Corrige les statuts de disponibilité des unités locatives et propriétés en fonction des contrats actifs.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--unites',
            action='store_true',
            help='Corriger uniquement les statuts des unités locatives.',
        )
        parser.add_argument(
            '--proprietes',
            action='store_true',
            help='Corriger uniquement les statuts des propriétés.',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Afficher les détails de la correction.',
        )

    def handle(self, *args, **options):
        corriger_unites = options['unites']
        corriger_proprietes = options['proprietes']
        verbose = options['verbose']

        # Si aucune option n'est spécifiée, corriger les deux
        if not corriger_unites and not corriger_proprietes:
            corriger_unites = True
            corriger_proprietes = True

        self.stdout.write(
            self.style.SUCCESS('Début de la correction des statuts de disponibilité...')
        )

        try:
            with transaction.atomic():
                if corriger_unites:
                    self.corriger_unites_locatives(verbose)

                if corriger_proprietes:
                    self.corriger_proprietes(verbose)

                self.stdout.write(
                    self.style.SUCCESS('[OK] Correction des statuts terminée avec succès!')
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'[ERREUR] Erreur lors de la correction: {str(e)}')
            )
            import traceback
            traceback.print_exc()
            raise

    def corriger_unites_locatives(self, verbose=False):
        """Corrige les statuts des unités locatives en fonction des contrats actifs."""
        self.stdout.write(
            self.style.WARNING('Correction des statuts des unités locatives...')
        )

        unites = UniteLocative.objects.all()
        total = unites.count()
        corrigees = 0
        deja_correctes = 0

        for unite in unites:
            # Vérifier s'il y a des contrats actifs pour cette unité
            # CORRIGÉ : Utiliser all_objects pour inclure les contrats supprimés logiquement
            contrats_actifs = Contrat.all_objects.filter(
                unite_locative=unite,
                est_actif=True,
                est_resilie=False
            )

            a_contrats_actifs = contrats_actifs.exists()
            statut_attendu = 'occupee' if a_contrats_actifs else 'disponible'

            # Si le statut est incorrect, le corriger
            if unite.statut != statut_attendu:
                ancien_statut = unite.statut
                unite.statut = statut_attendu
                unite.save(update_fields=['statut'])
                corrigees += 1
                if verbose:
                    self.stdout.write(
                        f"  [OK] Unité {unite.nom} ({unite.numero_unite}): "
                        f"passée de '{ancien_statut}' à '{statut_attendu}'"
                    )
            else:
                deja_correctes += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'  Unités locatives: {corrigees} corrigées, {deja_correctes} déjà correctes sur {total}'
            )
        )

    def corriger_proprietes(self, verbose=False):
        """Corrige les statuts de disponibilité des propriétés en fonction des contrats actifs."""
        self.stdout.write(
            self.style.WARNING('Correction des statuts de disponibilité des propriétés...')
        )

        proprietes = Propriete.objects.all()
        total = proprietes.count()
        corrigees = 0
        deja_correctes = 0

        for propriete in proprietes:
            # Vérifier s'il y a des contrats actifs pour cette propriété
            # CORRIGÉ : Utiliser all_objects pour inclure les contrats supprimés logiquement
            contrats_actifs = Contrat.all_objects.filter(
                propriete=propriete,
                est_actif=True,
                est_resilie=False
            )

            a_contrats_actifs = contrats_actifs.exists()
            disponibilite_attendue = not a_contrats_actifs

            # Si la disponibilité est incorrecte, la corriger
            if propriete.disponible != disponibilite_attendue:
                ancienne_disponibilite = propriete.disponible
                propriete.disponible = disponibilite_attendue
                propriete.save(update_fields=['disponible'])
                corrigees += 1
                if verbose:
                    self.stdout.write(
                        f"  [OK] Propriété {propriete.titre} ({propriete.numero_propriete}): "
                        f"passée de 'disponible={ancienne_disponibilite}' à 'disponible={disponibilite_attendue}'"
                    )
            else:
                deja_correctes += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'  Propriétés: {corrigees} corrigées, {deja_correctes} déjà correctes sur {total}'
            )
        )

