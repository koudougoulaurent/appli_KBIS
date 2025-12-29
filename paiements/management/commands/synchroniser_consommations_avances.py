"""
Commande Django pour synchroniser toutes les consommations d'avances manquantes
Usage: python manage.py synchroniser_consommations_avances
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from paiements.models_avance import AvanceLoyer, ConsommationAvance
from paiements.models import Paiement
from contrats.models import Contrat
from datetime import date
from dateutil.relativedelta import relativedelta


class Command(BaseCommand):
    help = 'Synchronise les consommations d\'avances manquantes pour tous les contrats'

    def add_arguments(self, parser):
        parser.add_argument(
            '--contrat_id',
            type=int,
            help='ID du contrat spécifique à synchroniser (optionnel)',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forcer la resynchronisation même pour les avances déjà synchronisées',
        )

    def handle(self, *args, **options):
        contrat_id = options.get('contrat_id')
        force = options.get('force', False)

        self.stdout.write(self.style.WARNING('🔄 Début de la synchronisation des consommations d\'avances...'))

        # Récupérer les avances à synchroniser
        if contrat_id:
            avances = AvanceLoyer.objects.filter(contrat_id=contrat_id)
            self.stdout.write(f'📋 Synchronisation pour le contrat ID {contrat_id}')
        else:
            avances = AvanceLoyer.objects.all()
            self.stdout.write(f'📋 Synchronisation pour toutes les avances ({avances.count()} avances)')

        total_avances = avances.count()
        avances_synchronisees = 0
        consommations_creees = 0
        erreurs = 0

        for avance in avances:
            try:
                with transaction.atomic():
                    self.stdout.write(f'\n⚡ Avance ID {avance.id} - Contrat {avance.contrat.numero_contrat}')
                    self.stdout.write(f'   Montant: {avance.montant_avance} F CFA')
                    self.stdout.write(f'   Période: {avance.mois_debut_couverture.strftime("%B %Y") if avance.mois_debut_couverture else "N/A"} - {avance.mois_fin_couverture.strftime("%B %Y") if avance.mois_fin_couverture else "N/A"}')
                    self.stdout.write(f'   Mois couverts: {avance.nombre_mois_couverts}')

                    # Vérifier si l'avance a des dates valides
                    if not avance.mois_debut_couverture or not avance.mois_fin_couverture:
                        self.stdout.write(self.style.WARNING(f'   ⚠️  Dates de couverture manquantes, recalcul...'))
                        avance.calculer_mois_couverts()
                        avance.save()

                    if not avance.mois_debut_couverture:
                        self.stdout.write(self.style.ERROR(f'   ❌ Impossible de calculer les dates de couverture'))
                        erreurs += 1
                        continue

                    # Récupérer les consommations existantes
                    consommations_existantes = ConsommationAvance.objects.filter(avance=avance)
                    mois_consommes_existants = set(c.mois_consomme for c in consommations_existantes)

                    self.stdout.write(f'   📊 Consommations existantes: {len(mois_consommes_existants)} mois')

                    # Récupérer tous les paiements de loyer validés du contrat
                    paiements_loyer = Paiement.objects.filter(
                        contrat=avance.contrat,
                        type_paiement='loyer',
                        statut='valide',
                        is_deleted=False
                    ).order_by('date_paiement')

                    self.stdout.write(f'   💰 Paiements de loyer trouvés: {paiements_loyer.count()}')

                    consommations_ajoutees_cette_avance = 0

                    # Pour chaque paiement de loyer, vérifier s'il doit créer une consommation
                    for paiement in paiements_loyer:
                        mois_paiement = paiement.date_paiement.replace(day=1)

                        # Vérifier si ce mois est dans la période de couverture de l'avance
                        if (avance.mois_debut_couverture <= mois_paiement <= avance.mois_fin_couverture):
                            # Vérifier si ce mois n'est pas déjà consommé
                            if mois_paiement not in mois_consommes_existants:
                                # Créer la consommation
                                ConsommationAvance.objects.create(
                                    avance=avance,
                                    mois_consomme=mois_paiement,
                                    montant_consomme=avance.loyer_mensuel,
                                    montant_restant_apres=max(0, avance.montant_restant - avance.loyer_mensuel),
                                    paiement=paiement
                                )
                                
                                # Mettre à jour le montant restant
                                avance.montant_restant = max(0, avance.montant_restant - avance.loyer_mensuel)
                                
                                consommations_ajoutees_cette_avance += 1
                                consommations_creees += 1
                                
                                self.stdout.write(self.style.SUCCESS(
                                    f'      ✅ Consommation créée pour {mois_paiement.strftime("%B %Y")}'
                                ))

                    # Mettre à jour le statut de l'avance si nécessaire
                    if avance.montant_restant <= 0:
                        avance.statut = 'epuisee'
                    
                    avance.save()

                    if consommations_ajoutees_cette_avance > 0:
                        avances_synchronisees += 1
                        self.stdout.write(self.style.SUCCESS(
                            f'   ✅ {consommations_ajoutees_cette_avance} consommation(s) ajoutée(s)'
                        ))
                    else:
                        self.stdout.write(self.style.SUCCESS(f'   ✅ Déjà synchronisée'))

            except Exception as e:
                erreurs += 1
                self.stdout.write(self.style.ERROR(f'   ❌ Erreur: {str(e)}'))
                continue

        # Résumé
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS('\n📊 RÉSUMÉ DE LA SYNCHRONISATION:'))
        self.stdout.write(f'   • Total avances traitées: {total_avances}')
        self.stdout.write(f'   • Avances synchronisées: {avances_synchronisees}')
        self.stdout.write(f'   • Consommations créées: {consommations_creees}')
        if erreurs > 0:
            self.stdout.write(self.style.ERROR(f'   • Erreurs: {erreurs}'))
        self.stdout.write('\n✅ Synchronisation terminée!')

