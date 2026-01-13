"""
Commande de management pour recalculer tous les récapitulatifs mensuels existants.

Cette commande met à jour tous les récapitulatifs en recalculant:
- Les loyers bruts
- Les charges bailleur
- Le total net à payer
- La commission agence
- Le montant réellement payé

Usage:
    python manage.py recalculer_recaps
    python manage.py recalculer_recaps --bailleur_id=123
    python manage.py recalculer_recaps --mois=2025-12
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from paiements.models import RecapMensuel
from decimal import Decimal
from datetime import datetime


class Command(BaseCommand):
    help = 'Recalcule tous les récapitulatifs mensuels existants avec les charges bailleur'

    def add_arguments(self, parser):
        parser.add_argument(
            '--bailleur_id',
            type=int,
            help='ID du bailleur pour recalculer uniquement ses récapitulatifs',
        )
        parser.add_argument(
            '--mois',
            type=str,
            help='Mois spécifique au format YYYY-MM (ex: 2025-12)',
        )
        parser.add_argument(
            '--statut',
            type=str,
            choices=['brouillon', 'valide', 'envoye', 'paye'],
            help='Recalculer uniquement les récapitulatifs avec ce statut',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Afficher les modifications sans les appliquer',
        )

    def handle(self, *args, **options):
        bailleur_id = options.get('bailleur_id')
        mois = options.get('mois')
        statut = options.get('statut')
        dry_run = options.get('dry_run')

        # Construire la requête de base
        queryset = RecapMensuel.objects.filter(is_deleted=False)

        # Appliquer les filtres
        if bailleur_id:
            queryset = queryset.filter(bailleur_id=bailleur_id)
            self.stdout.write(self.style.SUCCESS(f'Filtre: Bailleur ID {bailleur_id}'))

        if mois:
            try:
                date_obj = datetime.strptime(mois, '%Y-%m')
                queryset = queryset.filter(
                    mois_recap__year=date_obj.year,
                    mois_recap__month=date_obj.month
                )
                self.stdout.write(self.style.SUCCESS(f'Filtre: Mois {mois}'))
            except ValueError:
                raise CommandError(f'Format de mois invalide: {mois}. Utilisez YYYY-MM')

        if statut:
            queryset = queryset.filter(statut=statut)
            self.stdout.write(self.style.SUCCESS(f'Filtre: Statut {statut}'))

        # Compter les récapitulatifs à traiter
        total_recaps = queryset.count()

        if total_recaps == 0:
            self.stdout.write(self.style.WARNING('Aucun récapitulatif trouvé avec ces critères.'))
            return

        self.stdout.write(f'\n{total_recaps} récapitulatif(s) à recalculer...\n')

        if dry_run:
            self.stdout.write(self.style.WARNING('MODE DRY-RUN: Les modifications ne seront pas sauvegardées\n'))

        # Compteurs pour le rapport
        recaps_recalcules = 0
        recaps_erreur = 0
        total_modifications = 0

        # Traiter chaque récapitulatif
        for recap in queryset.select_related('bailleur'):
            try:
                # Afficher les informations du récapitulatif
                bailleur_nom = recap.bailleur.get_nom_complet() if recap.bailleur else "Bailleur inconnu"
                mois_str = recap.mois_recap.strftime('%B %Y')
                
                self.stdout.write(f'\n📋 Traitement: {bailleur_nom} - {mois_str}')
                self.stdout.write(f'   Statut: {recap.get_statut_display()}')

                # Sauvegarder les anciennes valeurs pour comparaison
                ancien_loyers = recap.total_loyers_bruts
                anciennes_charges_deductibles = recap.total_charges_deductibles
                anciennes_charges_bailleur = recap.total_charges_bailleur or Decimal('0')
                ancien_net = recap.total_net_a_payer

                # Recalculer les totaux
                if not dry_run:
                    with transaction.atomic():
                        resultats = recap.calculer_totaux_bailleur()
                else:
                    # En mode dry-run, juste afficher les valeurs actuelles
                    self.stdout.write(f'   Loyers bruts: {ancien_loyers:,.0f} F CFA')
                    self.stdout.write(f'   Charges bailleur: {anciennes_charges_bailleur:,.0f} F CFA')
                    self.stdout.write(f'   Net à payer: {ancien_net:,.0f} F CFA')
                    recaps_recalcules += 1
                    continue

                # Comparer les valeurs
                nouveau_loyers = recap.total_loyers_bruts
                nouvelles_charges_bailleur = recap.total_charges_bailleur or Decimal('0')
                nouveau_net = recap.total_net_a_payer

                modifications = False

                # Afficher les différences
                if ancien_loyers != nouveau_loyers:
                    diff_loyers = nouveau_loyers - ancien_loyers
                    self.stdout.write(
                        f'   ✓ Loyers: {ancien_loyers:,.0f} → {nouveau_loyers:,.0f} '
                        f'({diff_loyers:+,.0f} F CFA)'
                    )
                    modifications = True
                else:
                    self.stdout.write(f'   = Loyers: {nouveau_loyers:,.0f} F CFA (inchangé)')

                if anciennes_charges_bailleur != nouvelles_charges_bailleur:
                    diff_charges = nouvelles_charges_bailleur - anciennes_charges_bailleur
                    self.stdout.write(
                        f'   ✓ Charges bailleur: {anciennes_charges_bailleur:,.0f} → {nouvelles_charges_bailleur:,.0f} '
                        f'({diff_charges:+,.0f} F CFA)'
                    )
                    modifications = True
                else:
                    self.stdout.write(f'   = Charges bailleur: {nouvelles_charges_bailleur:,.0f} F CFA (inchangé)')

                if ancien_net != nouveau_net:
                    diff_net = nouveau_net - ancien_net
                    self.stdout.write(
                        f'   ✓ Net à payer: {ancien_net:,.0f} → {nouveau_net:,.0f} '
                        f'({diff_net:+,.0f} F CFA)'
                    )
                    modifications = True
                else:
                    self.stdout.write(f'   = Net à payer: {nouveau_net:,.0f} F CFA (inchangé)')

                # Afficher la commission et le montant réellement payé
                if hasattr(recap, 'commission_agence'):
                    commission = recap.commission_agence or Decimal('0')
                    self.stdout.write(f'   💰 Commission agence (10%): {commission:,.0f} F CFA')
                
                if hasattr(recap, 'montant_reellement_paye'):
                    montant_reel = recap.montant_reellement_paye or Decimal('0')
                    self.stdout.write(f'   💵 Montant réellement payé: {montant_reel:,.0f} F CFA')

                # Afficher les statistiques
                self.stdout.write(
                    f'   📊 {recap.nombre_proprietes} propriété(s), '
                    f'{recap.nombre_contrats_actifs} contrat(s) actif(s), '
                    f'{recap.nombre_paiements_recus} paiement(s)'
                )

                if modifications:
                    total_modifications += 1
                    self.stdout.write(self.style.SUCCESS('   ✅ Récapitulatif mis à jour'))
                else:
                    self.stdout.write(self.style.WARNING('   ⚠️  Aucune modification détectée'))

                recaps_recalcules += 1

            except Exception as e:
                recaps_erreur += 1
                self.stdout.write(
                    self.style.ERROR(f'   ❌ Erreur lors du recalcul: {str(e)}')
                )

        # Afficher le rapport final
        self.stdout.write('\n' + '='*70)
        self.stdout.write(self.style.SUCCESS('\n📊 RAPPORT FINAL\n'))
        self.stdout.write(f'Total traités: {recaps_recalcules}/{total_recaps}')
        self.stdout.write(f'Modifiés: {total_modifications}')
        self.stdout.write(f'Inchangés: {recaps_recalcules - total_modifications}')
        
        if recaps_erreur > 0:
            self.stdout.write(self.style.ERROR(f'Erreurs: {recaps_erreur}'))
        else:
            self.stdout.write(self.style.SUCCESS('Erreurs: 0'))

        if dry_run:
            self.stdout.write(
                self.style.WARNING('\n⚠️  MODE DRY-RUN: Aucune modification n\'a été sauvegardée')
            )
            self.stdout.write('Relancez sans --dry-run pour appliquer les modifications\n')
        else:
            self.stdout.write(self.style.SUCCESS('\n✅ Recalcul terminé avec succès!\n'))
