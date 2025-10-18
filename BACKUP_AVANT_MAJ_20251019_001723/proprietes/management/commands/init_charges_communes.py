"""
Commande Django pour initialiser et tester le système de charges communes.

Usage:
    python manage.py init_charges_communes --propriete_id=1
    python manage.py init_charges_communes --all
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from proprietes.models import Propriete, ChargeCommune, Piece
from proprietes.services import GestionChargesCommunesService
from datetime import date


class Command(BaseCommand):
    help = 'Initialise et teste le système de charges communes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--propriete_id',
            type=int,
            help='ID de la propriété pour laquelle créer des charges communes de test'
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Traite toutes les propriétés'
        )
        parser.add_argument(
            '--calculer',
            action='store_true',
            help='Calcule les charges pour le mois courant'
        )
        parser.add_argument(
            '--appliquer',
            action='store_true',
            help='Applique les charges calculées aux contrats'
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🏢 Initialisation du système de charges communes')
        )

        if options['propriete_id']:
            propriete_id = options['propriete_id']
            try:
                propriete = Propriete.objects.get(id=propriete_id)
                self.traiter_propriete(propriete, options)
            except Propriete.DoesNotExist:
                raise CommandError(f'Propriété avec ID {propriete_id} non trouvée')
        
        elif options['all']:
            proprietes = Propriete.objects.filter(is_deleted=False)
            for propriete in proprietes:
                self.traiter_propriete(propriete, options)
        
        else:
            self.stdout.write(
                self.style.WARNING('Veuillez spécifier --propriete_id=X ou --all')
            )

    def traiter_propriete(self, propriete, options):
        self.stdout.write(f'\n📍 Traitement de la propriété: {propriete.titre}')
        
        # Créer des charges communes de test si elles n'existent pas
        self.creer_charges_test(propriete)
        
        if options['calculer']:
            self.calculer_charges(propriete)
        
        if options['appliquer']:
            self.appliquer_charges(propriete)

    def creer_charges_test(self, propriete):
        """Crée des charges communes de test pour une propriété."""
        
        charges_test = [
            {
                'nom': 'Électricité commune',
                'type_charge': 'electricite',
                'montant_mensuel': 150.00,
                'type_repartition': 'equipartition',
                'description': 'Électricité des parties communes (couloirs, entrée, etc.)'
            },
            {
                'nom': 'Internet haut débit',
                'type_charge': 'internet',
                'montant_mensuel': 50.00,
                'type_repartition': 'equipartition',
                'description': 'Connexion internet partagée'
            },
            {
                'nom': 'Entretien ménage',
                'type_charge': 'nettoyage',
                'montant_mensuel': 100.00,
                'type_repartition': 'surface',
                'description': 'Nettoyage des espaces communs'
            },
            {
                'nom': 'Eau commune',
                'type_charge': 'eau',
                'montant_mensuel': 80.00,
                'type_repartition': 'nb_occupants',
                'description': 'Eau des espaces partagés (cuisine, salle de bain commune)'
            }
        ]
        
        charges_creees = 0
        
        for charge_data in charges_test:
            charge, created = ChargeCommune.objects.get_or_create(
                propriete=propriete,
                nom=charge_data['nom'],
                defaults={
                    'type_charge': charge_data['type_charge'],
                    'montant_mensuel': charge_data['montant_mensuel'],
                    'type_repartition': charge_data['type_repartition'],
                    'description': charge_data['description'],
                    'date_debut': date.today(),
                    'active': True
                }
            )
            
            if created:
                charges_creees += 1
                self.stdout.write(
                    f'  ✅ Charge créée: {charge.nom} ({charge.montant_mensuel}€, {charge.get_type_repartition_display()})'
                )
        
        if charges_creees > 0:
            self.stdout.write(
                self.style.SUCCESS(f'📊 {charges_creees} charges communes créées')
            )
        else:
            self.stdout.write('📊 Charges communes déjà existantes')

    def calculer_charges(self, propriete):
        """Calcule les charges communes pour le mois courant."""
        
        mois = timezone.now().month
        annee = timezone.now().year
        
        self.stdout.write(f'🔢 Calcul des charges pour {mois}/{annee}...')
        
        try:
            resultats = GestionChargesCommunesService.calculer_charges_mensuelles(
                propriete.id, mois, annee
            )
            
            if resultats['erreurs']:
                for erreur in resultats['erreurs']:
                    self.stdout.write(self.style.ERROR(f'❌ {erreur}'))
            
            if resultats['charges_calculees']:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ {len(resultats["charges_calculees"])} répartitions calculées'
                    )
                )
                self.stdout.write(
                    f'💰 Total charges: {resultats["total_charges"]:.2f}€'
                )
                self.stdout.write(
                    f'👥 Nombre de locataires: {resultats["nb_locataires"]}'
                )
                
                # Afficher le détail
                for charge_info in resultats['charges_calculees']:
                    statut = "🆕 NOUVEAU" if charge_info['nouveau'] else "🔄 MIS À JOUR"
                    self.stdout.write(
                        f'  {statut} {charge_info["charge"]} - '
                        f'{charge_info["locataire"]} ({charge_info["piece"]}) - '
                        f'{charge_info["montant"]:.2f}€ ({charge_info["base_calcul"]})'
                    )
            else:
                self.stdout.write(
                    self.style.WARNING('⚠️ Aucune charge à calculer (pas de pièces occupées ?)')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Erreur lors du calcul: {str(e)}')
            )

    def appliquer_charges(self, propriete):
        """Applique les charges calculées aux contrats."""
        
        mois = timezone.now().month
        annee = timezone.now().year
        
        self.stdout.write(f'📝 Application des charges pour {mois}/{annee}...')
        
        try:
            resultats = GestionChargesCommunesService.appliquer_charges_aux_contrats(
                propriete.id, mois, annee
            )
            
            if resultats['erreurs']:
                for erreur in resultats['erreurs']:
                    self.stdout.write(self.style.ERROR(f'❌ {erreur}'))
            
            if resultats['applications']:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ Charges appliquées à {len(resultats["applications"])} contrats'
                    )
                )
                self.stdout.write(
                    f'💰 Total appliqué: {resultats["total_applique"]:.2f}€'
                )
                
                # Afficher le détail
                for application in resultats['applications']:
                    self.stdout.write(
                        f'  📋 {application["locataire"]} ({application["piece"]}) - '
                        f'Charges: {application["charges_avant"]:.2f}€ → {application["charges_apres"]:.2f}€ '
                        f'(+{application["charges_ajoutees"]:.2f}€)'
                    )
                    
                    for detail in application['details']:
                        self.stdout.write(
                            f'    • {detail["charge"]}: +{detail["montant"]:.2f}€'
                        )
            else:
                self.stdout.write(
                    self.style.WARNING('⚠️ Aucune charge à appliquer')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Erreur lors de l\'application: {str(e)}')
            )

    def creer_espaces_partages_test(self, propriete):
        """Crée des espaces partagés de test."""
        
        # Vérifier s'il y a des pièces
        pieces = Piece.objects.filter(propriete=propriete, is_deleted=False)
        
        if not pieces.exists():
            self.stdout.write('⚠️ Aucune pièce trouvée pour créer des espaces partagés')
            return
        
        espaces_test = [
            {
                'nom': 'Cuisine commune',
                'type_piece': 'cuisine',
                'surface': 15.0,
                'cout_acces_mensuel': 30.0
            },
            {
                'nom': 'Salon partagé',
                'type_piece': 'salon', 
                'surface': 25.0,
                'cout_acces_mensuel': 20.0
            }
        ]
        
        for espace_data in espaces_test:
            espace, created = Piece.objects.get_or_create(
                propriete=propriete,
                nom=espace_data['nom'],
                defaults={
                    'type_piece': espace_data['type_piece'],
                    'surface': espace_data['surface'],
                    'est_espace_partage': True,
                    'cout_acces_mensuel': espace_data['cout_acces_mensuel'],
                    'statut': 'disponible'
                }
            )
            
            if created:
                self.stdout.write(
                    f'  🏠 Espace partagé créé: {espace.nom} ({espace.cout_acces_mensuel}€/mois)'
                )





