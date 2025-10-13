#!/usr/bin/env python
"""
Commande de management pour le monitoring automatique des avances
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date, datetime

from paiements.services_monitoring_avance import ServiceMonitoringAvance


class Command(BaseCommand):
    help = 'Monitoring automatique des avances de loyer'

    def add_arguments(self, parser):
        parser.add_argument(
            '--sync',
            action='store_true',
            help='Synchroniser les consommations d\'avances',
        )
        parser.add_argument(
            '--alert',
            action='store_true',
            help='Envoyer les alertes d\'expiration',
        )
        parser.add_argument(
            '--report',
            action='store_true',
            help='Générer un rapport de progression',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Exécuter toutes les tâches de monitoring',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🚀 Démarrage du monitoring des avances...')
        )
        
        try:
            # Synchronisation des consommations
            if options['sync'] or options['all']:
                self.stdout.write('📊 Synchronisation des consommations...')
                resultat = ServiceMonitoringAvance.synchroniser_consommations()
                if resultat:
                    self.stdout.write(
                        self.style.SUCCESS('✅ Synchronisation réussie')
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR('❌ Erreur lors de la synchronisation')
                    )
            
            # Envoi des alertes
            if options['alert'] or options['all']:
                self.stdout.write('🚨 Vérification des alertes...')
                message = ServiceMonitoringAvance.envoyer_alertes_expiration()
                if message:
                    self.stdout.write(
                        self.style.WARNING('⚠️ Alertes envoyées:')
                    )
                    self.stdout.write(message)
                else:
                    self.stdout.write(
                        self.style.SUCCESS('✅ Aucune alerte à envoyer')
                    )
            
            # Génération du rapport
            if options['report'] or options['all']:
                self.stdout.write('📈 Génération du rapport de progression...')
                rapport = ServiceMonitoringAvance.generer_rapport_progression()
                if rapport:
                    self.stdout.write(
                        self.style.SUCCESS('✅ Rapport généré avec succès')
                    )
                    self.afficher_rapport(rapport)
                else:
                    self.stdout.write(
                        self.style.ERROR('❌ Erreur lors de la génération du rapport')
                    )
            
            # Si aucune option spécifiée, afficher le statut
            if not any([options['sync'], options['alert'], options['report'], options['all']]):
                self.stdout.write('📊 Analyse de la progression des avances...')
                progressions = ServiceMonitoringAvance.analyser_progression_avances()
                self.afficher_progressions(progressions)
            
            self.stdout.write(
                self.style.SUCCESS('🎉 Monitoring terminé avec succès!')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Erreur lors du monitoring: {str(e)}')
            )

    def afficher_rapport(self, rapport):
        """Affiche le rapport de progression"""
        self.stdout.write('\n' + '='*50)
        self.stdout.write('📊 RAPPORT DE PROGRESSION DES AVANCES')
        self.stdout.write('='*50)
        
        # Statistiques
        stats = rapport['statistiques']
        self.stdout.write(f'📈 Total des avances: {stats["total_avances"]}')
        self.stdout.write(f'🔴 Critiques: {stats["avances_critiques"]}')
        self.stdout.write(f'🟡 Avancées: {stats["avances_avancees"]}')
        self.stdout.write(f'🟢 Normales: {stats["avances_normales"]}')
        self.stdout.write(f'⚫ Épuisées: {stats["avances_epuisees"]}')
        
        # Montants
        montants = rapport['montants']
        self.stdout.write(f'\n💰 MONTANTS:')
        self.stdout.write(f'   Total: {montants["total_avances"]:,.0f} F CFA')
        self.stdout.write(f'   Consommé: {montants["total_consomme"]:,.0f} F CFA')
        self.stdout.write(f'   Restant: {montants["total_restant"]:,.0f} F CFA')
        self.stdout.write(f'   Pourcentage: {montants["pourcentage_consomme"]:.1f}%')
        
        self.stdout.write('='*50)

    def afficher_progressions(self, progressions):
        """Affiche les progressions des avances"""
        if not progressions:
            self.stdout.write('ℹ️ Aucune avance trouvée')
            return
        
        self.stdout.write('\n' + '='*80)
        self.stdout.write('📊 PROGRESSION DES AVANCES')
        self.stdout.write('='*80)
        
        for progression in progressions:
            avance = progression['avance']
            self.stdout.write(f'\n🏠 {avance.contrat.locataire.get_nom_complet()}')
            self.stdout.write(f'   Contrat: {avance.contrat.numero_contrat}')
            self.stdout.write(f'   Montant: {avance.montant_avance:,.0f} F CFA')
            self.stdout.write(f'   Restant: {progression["montant_restant"]:,.0f} F CFA')
            self.stdout.write(f'   Progression: {progression["pourcentage_reel"]:.1f}%')
            self.stdout.write(f'   Statut: {progression["statut_progression"].upper()}')
            self.stdout.write(f'   Mois restants: {progression["mois_restants_estimes"]}')
        
        self.stdout.write('='*80)


























