"""
Commande de Gestion Simple pour les Notifications
Gestion simple et efficace du système de notifications
"""
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from datetime import datetime, timedelta, date
import json

from notifications.services_notifications_simples import ServiceNotificationsSimples
from notifications.signals_simples import (
    verifier_retards_paiement_simple,
    verifier_contrats_expirants_simple,
    nettoyer_notifications_anciennes_simple,
    notifier_erreur_systeme_simple,
    notifier_info_systeme_simple
)
from notifications.models import Notification, NotificationPreference
from utilisateurs.models import Utilisateur


class Command(BaseCommand):
    help = 'Gestion simple et efficace du système de notifications'
    
    def add_arguments(self, parser):
        parser.add_argument(
            'action',
            type=str,
            choices=[
                'status', 'test', 'clean', 'retards', 'contrats', 'maintenance',
                'stats', 'info', 'error'
            ],
            help='Action à effectuer'
        )
        parser.add_argument(
            '--user',
            type=str,
            help='Nom d\'utilisateur pour les actions spécifiques'
        )
        parser.add_argument(
            '--type',
            type=str,
            choices=[
                'payment_received', 'payment_partial', 'payment_overdue',
                'advance_consumed', 'contract_expiring', 'retrait_created',
                'system_alert', 'info'
            ],
            help='Type de notification pour les tests'
        )
        parser.add_argument(
            '--message',
            type=str,
            help='Message personnalisé pour les tests'
        )
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Nombre de jours pour le nettoyage'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forcer l\'action sans confirmation'
        )
    
    def handle(self, *args, **options):
        action = options['action']
        
        try:
            if action == 'status':
                self.show_status()
            elif action == 'test':
                self.test_notification(options)
            elif action == 'clean':
                self.clean_notifications(options)
            elif action == 'retards':
                self.check_retards()
            elif action == 'contrats':
                self.check_contrats()
            elif action == 'maintenance':
                self.maintenance()
            elif action == 'stats':
                self.show_statistics(options)
            elif action == 'info':
                self.test_info_notification(options)
            elif action == 'error':
                self.test_error_notification(options)
            else:
                raise CommandError(f"Action inconnue: {action}")
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Erreur lors de l'exécution: {str(e)}")
            )
            raise CommandError(f"Échec de l'action {action}: {str(e)}")
    
    def show_status(self):
        """Affiche le statut du système de notifications simples"""
        self.stdout.write(self.style.SUCCESS("🔔 STATUT DU SYSTÈME DE NOTIFICATIONS SIMPLES"))
        self.stdout.write("=" * 60)
        
        # Statistiques générales
        total_notifications = Notification.objects.count()
        unread_notifications = Notification.objects.filter(is_read=False).count()
        today_notifications = Notification.objects.filter(
            created_at__date=timezone.now().date()
        ).count()
        
        self.stdout.write(f"📊 Total notifications: {total_notifications}")
        self.stdout.write(f"🔴 Non lues: {unread_notifications}")
        self.stdout.write(f"📅 Aujourd'hui: {today_notifications}")
        
        # Notifications par priorité
        self.stdout.write("\n📈 Par priorité:")
        for priority in ['urgent', 'high', 'medium', 'low']:
            count = Notification.objects.filter(priority=priority, is_read=False).count()
            self.stdout.write(f"  {priority.upper()}: {count}")
        
        # Notifications par type
        self.stdout.write("\n🏷️ Par type:")
        for type_notif in ServiceNotificationsSimples.NOTIFICATION_TYPES.keys():
            count = Notification.objects.filter(type=type_notif, is_read=False).count()
            self.stdout.write(f"  {type_notif}: {count}")
        
        # Utilisateurs avec préférences
        users_with_prefs = NotificationPreference.objects.count()
        total_users = Utilisateur.objects.count()
        self.stdout.write(f"\n👥 Utilisateurs avec préférences: {users_with_prefs}/{total_users}")
    
    def test_notification(self, options):
        """Test d'envoi de notification simple"""
        user = self.get_user(options['user'])
        type_notif = options['type'] or 'info'
        message = options['message'] or f"Test de notification simple {type_notif}"
        
        self.stdout.write(f"🧪 Test d'envoi de notification simple...")
        self.stdout.write(f"Utilisateur: {user.username}")
        self.stdout.write(f"Type: {type_notif}")
        self.stdout.write(f"Message: {message}")
        
        notification = ServiceNotificationsSimples.creer_notification_simple(
            recipient=user,
            type_notification=type_notif,
            message=message,
            force_send=True
        )
        
        if notification:
            self.stdout.write(
                self.style.SUCCESS(f"✅ Notification simple créée avec succès (ID: {notification.id})")
            )
        else:
            self.stdout.write(
                self.style.ERROR("❌ Échec de la création de la notification simple")
            )
    
    def clean_notifications(self, options):
        """Nettoie les notifications anciennes de manière simple"""
        days = options['days']
        force = options['force']
        
        if not force:
            confirm = input(f"Supprimer les notifications de plus de {days} jours? (y/N): ")
            if confirm.lower() != 'y':
                self.stdout.write("❌ Opération annulée")
                return
        
        self.stdout.write(f"🧹 Nettoyage simple des notifications anciennes (> {days} jours)...")
        
        count = ServiceNotificationsSimples.nettoyer_notifications_anciennes_simple(days)
        
        self.stdout.write(
            self.style.SUCCESS(f"✅ {count} notification(s) supprimée(s)")
        )
    
    def check_retards(self):
        """Vérifie les retards de paiement de manière simple"""
        self.stdout.write("🔍 Vérification simple des retards de paiement...")
        
        verifier_retards_paiement_simple()
        
        self.stdout.write(
            self.style.SUCCESS("✅ Vérification simple des retards terminée")
        )
    
    def check_contrats(self):
        """Vérifie les contrats expirants de manière simple"""
        self.stdout.write("🔍 Vérification simple des contrats expirants...")
        
        verifier_contrats_expirants_simple()
        
        self.stdout.write(
            self.style.SUCCESS("✅ Vérification simple des contrats terminée")
        )
    
    def maintenance(self):
        """Maintenance simple du système"""
        self.stdout.write("🔧 Maintenance simple du système de notifications...")
        
        # Nettoyage
        self.stdout.write("  🧹 Nettoyage des notifications anciennes...")
        nettoyer_notifications_anciennes_simple()
        
        # Vérifications
        self.stdout.write("  🔍 Vérification des retards...")
        verifier_retards_paiement_simple()
        
        self.stdout.write("  🔍 Vérification des contrats...")
        verifier_contrats_expirants_simple()
        
        self.stdout.write(
            self.style.SUCCESS("✅ Maintenance simple terminée")
        )
    
    def show_statistics(self, options):
        """Affiche les statistiques simples"""
        user = self.get_user(options['user']) if options['user'] else None
        
        if user:
            self.stdout.write(f"📊 Statistiques simples pour {user.username}")
            stats = ServiceNotificationsSimples.get_statistiques_notifications_simple(user)
        else:
            self.stdout.write("📊 Statistiques globales simples")
            stats = {
                'total': Notification.objects.count(),
                'non_lues': Notification.objects.filter(is_read=False).count(),
                'aujourd_hui': Notification.objects.filter(
                    created_at__date=timezone.now().date()
                ).count(),
                'cette_semaine': Notification.objects.filter(
                    created_at__date__gte=timezone.now().date() - timedelta(days=7)
                ).count(),
                'par_priorite': {}
            }
            
            for priority in ['urgent', 'high', 'medium', 'low']:
                stats['par_priorite'][priority] = Notification.objects.filter(
                    priority=priority, is_read=False
                ).count()
        
        self.stdout.write("=" * 40)
        self.stdout.write(f"Total: {stats['total']}")
        self.stdout.write(f"Non lues: {stats['non_lues']}")
        self.stdout.write(f"Aujourd'hui: {stats['aujourd_hui']}")
        self.stdout.write(f"Cette semaine: {stats['cette_semaine']}")
        
        if 'par_priorite' in stats:
            self.stdout.write("\nPar priorité:")
            for priority, count in stats['par_priorite'].items():
                self.stdout.write(f"  {priority.upper()}: {count}")
    
    def test_info_notification(self, options):
        """Test d'envoi de notification d'information simple"""
        message = options['message'] or "Test d'information système simple"
        
        self.stdout.write("ℹ️ Test de notification d'information simple...")
        
        notifier_info_systeme_simple(message)
        
        self.stdout.write(
            self.style.SUCCESS("✅ Notification d'information simple envoyée")
        )
    
    def test_error_notification(self, options):
        """Test d'envoi de notification d'erreur simple"""
        message = options['message'] or "Test d'erreur système simple"
        
        self.stdout.write("🚨 Test de notification d'erreur simple...")
        
        notifier_erreur_systeme_simple(message)
        
        self.stdout.write(
            self.style.SUCCESS("✅ Notification d'erreur simple envoyée")
        )
    
    def get_user(self, username):
        """Récupère un utilisateur par nom d'utilisateur"""
        if not username:
            # Utiliser le premier utilisateur disponible
            user = Utilisateur.objects.first()
            if not user:
                raise CommandError("Aucun utilisateur trouvé")
            return user
        
        try:
            return Utilisateur.objects.get(username=username)
        except Utilisateur.DoesNotExist:
            raise CommandError(f"Utilisateur '{username}' non trouvé")

