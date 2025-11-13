"""
Commande Django pour mettre à jour les statuts actifs des bailleurs et locataires
en fonction de leurs contrats actifs.
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from proprietes.models import Bailleur, Locataire
from contrats.models import Contrat


class Command(BaseCommand):
    help = 'Met à jour les statuts actifs des bailleurs et locataires en fonction de leurs contrats actifs'

    def add_arguments(self, parser):
        parser.add_argument(
            '--bailleurs',
            action='store_true',
            help='Mettre à jour uniquement les bailleurs',
        )
        parser.add_argument(
            '--locataires',
            action='store_true',
            help='Mettre à jour uniquement les locataires',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Affiche les détails de la mise à jour',
        )

    def handle(self, *args, **options):
        update_bailleurs = options.get('bailleurs', False)
        update_locataires = options.get('locataires', False)
        verbose = options.get('verbose', False)
        
        # Si aucune option spécifiée, mettre à jour les deux
        if not update_bailleurs and not update_locataires:
            update_bailleurs = True
            update_locataires = True
        
        try:
            with transaction.atomic():
                if update_bailleurs:
                    self.mettre_a_jour_bailleurs(verbose)
                
                if update_locataires:
                    self.mettre_a_jour_locataires(verbose)
                
                self.stdout.write(
                    self.style.SUCCESS('[OK] Mise a jour des statuts terminee avec succes!')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'[ERREUR] Erreur lors de la mise a jour: {str(e)}')
            )
            import traceback
            traceback.print_exc()
            raise

    def mettre_a_jour_bailleurs(self, verbose=False):
        """Met à jour le statut actif des bailleurs en fonction de leurs contrats actifs"""
        self.stdout.write(
            self.style.WARNING('Mise a jour des statuts des bailleurs...')
        )
        
        bailleurs = Bailleur.objects.all()
        total = bailleurs.count()
        mis_a_jour = 0
        deja_correct = 0
        
        for bailleur in bailleurs:
            # Vérifier si le bailleur a des contrats actifs
            a_contrats_actifs = bailleur.a_des_proprietes_louees()
            
            # Mettre à jour le champ actif si nécessaire
            if a_contrats_actifs and not bailleur.actif:
                # Le bailleur a des contrats actifs mais est marqué inactif → corriger
                bailleur.actif = True
                bailleur.save(update_fields=['actif'])
                mis_a_jour += 1
                if verbose:
                    self.stdout.write(
                        f"  [OK] Bailleur {bailleur.get_nom_complet()} ({bailleur.numero_bailleur}): "
                        f"passe de Inactif a Actif (contrats actifs detectes)"
                    )
            elif not a_contrats_actifs and bailleur.actif:
                # Le bailleur n'a pas de contrats actifs mais est marqué actif
                # On peut le laisser actif ou le passer en inactif selon la logique métier
                # Ici, on garde le statut actif s'il est déjà actif (pas de changement automatique vers inactif)
                deja_correct += 1
            else:
                deja_correct += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f'  Bailleurs: {mis_a_jour} mis a jour, {deja_correct} deja corrects sur {total}'
            )
        )

    def mettre_a_jour_locataires(self, verbose=False):
        """Met à jour le statut des locataires en fonction de leurs contrats actifs"""
        self.stdout.write(
            self.style.WARNING('Mise a jour des statuts des locataires...')
        )
        
        locataires = Locataire.objects.all()
        total = locataires.count()
        mis_a_jour = 0
        deja_correct = 0
        
        for locataire in locataires:
            # Vérifier si le locataire a des contrats actifs
            a_contrats_actifs = locataire.a_des_contrats_actifs()
            
            # Mettre à jour le statut si nécessaire
            if a_contrats_actifs and locataire.statut != 'actif':
                # Le locataire a des contrats actifs mais n'est pas actif → corriger
                ancien_statut = locataire.statut
                locataire.statut = 'actif'
                locataire.save(update_fields=['statut'])
                mis_a_jour += 1
                if verbose:
                    self.stdout.write(
                        f"  [OK] Locataire {locataire.get_nom_complet()} ({locataire.numero_locataire}): "
                        f"passe de {ancien_statut} a actif (contrats actifs detectes)"
                    )
            elif not a_contrats_actifs and locataire.statut == 'actif':
                # Le locataire n'a pas de contrats actifs mais est marqué actif
                # On peut le laisser actif ou le passer en inactif selon la logique métier
                # Ici, on garde le statut actif s'il est déjà actif (pas de changement automatique vers inactif)
                deja_correct += 1
            else:
                deja_correct += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f'  Locataires: {mis_a_jour} mis a jour, {deja_correct} deja corrects sur {total}'
            )
        )

