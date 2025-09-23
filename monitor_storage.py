#!/usr/bin/env python
"""
Script de monitoring du stockage pour le plan Pro (100 GB)
Surveille l'utilisation de l'espace disque et envoie des alertes
"""
import os
import sys
import django
from django.conf import settings

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_immobiliere.settings_pro')
django.setup()

from django.db import connections
from django.core.mail import send_mail
from datetime import datetime, timedelta
import json


def monitor_storage():
    """Surveiller l'utilisation du stockage"""
    print("📊 MONITORING DU STOCKAGE - PLAN PRO (100 GB)")
    print("=" * 60)
    
    try:
        # 1. Vérifier l'utilisation actuelle
        print("🔍 Vérification de l'utilisation...")
        current_usage = get_storage_usage()
        
        # 2. Analyser les tendances
        print("\n📈 Analyse des tendances...")
        analyze_usage_trends()
        
        # 3. Vérifier les alertes
        print("\n🚨 Vérification des alertes...")
        check_storage_alerts(current_usage)
        
        # 4. Générer le rapport
        print("\n📋 Génération du rapport...")
        generate_storage_report(current_usage)
        
        print("\n✅ Monitoring terminé")
        
    except Exception as e:
        print(f"❌ Erreur lors du monitoring: {e}")


def get_storage_usage():
    """Obtenir l'utilisation actuelle du stockage"""
    try:
        connection = connections['default']
        with connection.cursor() as cursor:
            # Taille totale de la base de données
            cursor.execute("SELECT pg_size_pretty(pg_database_size(current_database()));")
            total_size = cursor.fetchone()[0]
            
            # Taille en bytes
            cursor.execute("SELECT pg_database_size(current_database());")
            total_bytes = cursor.fetchone()[0]
            
            # Taille des tables individuelles
            cursor.execute("""
                SELECT 
                    schemaname,
                    tablename,
                    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
                    pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
                FROM pg_tables 
                WHERE schemaname = 'public'
                ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
            """)
            table_sizes = cursor.fetchall()
            
            # Taille des index
            cursor.execute("""
                SELECT 
                    schemaname,
                    tablename,
                    indexname,
                    pg_size_pretty(pg_relation_size(schemaname||'.'||indexname)) as size
                FROM pg_indexes 
                WHERE schemaname = 'public'
                ORDER BY pg_relation_size(schemaname||'.'||indexname) DESC;
            """)
            index_sizes = cursor.fetchall()
            
            usage = {
                'total_size': total_size,
                'total_bytes': total_bytes,
                'total_gb': total_bytes / (1024**3),
                'table_sizes': table_sizes,
                'index_sizes': index_sizes,
                'timestamp': datetime.now().isoformat()
            }
            
            print(f"  📊 Taille totale: {total_size}")
            print(f"  💾 Taille en GB: {usage['total_gb']:.2f} GB")
            print(f"  📋 Tables: {len(table_sizes)}")
            print(f"  🔍 Index: {len(index_sizes)}")
            
            return usage
            
    except Exception as e:
        print(f"  ❌ Erreur lors de la récupération de l'utilisation: {e}")
        return None


def analyze_usage_trends():
    """Analyser les tendances d'utilisation"""
    try:
        # Charger l'historique des utilisations
        history_file = 'storage_history.json'
        if os.path.exists(history_file):
            with open(history_file, 'r') as f:
                history = json.load(f)
        else:
            history = []
        
        # Ajouter l'utilisation actuelle
        current_usage = get_storage_usage()
        if current_usage:
            history.append(current_usage)
            
            # Garder seulement les 30 derniers jours
            cutoff_date = datetime.now() - timedelta(days=30)
            history = [
                h for h in history 
                if datetime.fromisoformat(h['timestamp']) > cutoff_date
            ]
            
            # Sauvegarder l'historique
            with open(history_file, 'w') as f:
                json.dump(history, f, indent=2)
        
        # Analyser les tendances
        if len(history) >= 2:
            old_usage = history[-2]['total_gb']
            new_usage = history[-1]['total_gb']
            growth = new_usage - old_usage
            
            print(f"  📈 Croissance: {growth:.2f} GB")
            
            if growth > 0:
                print(f"  ⚠️ Attention: Croissance de {growth:.2f} GB détectée")
            else:
                print(f"  ✅ Stable: Pas de croissance significative")
        
    except Exception as e:
        print(f"  ❌ Erreur lors de l'analyse des tendances: {e}")


def check_storage_alerts(usage):
    """Vérifier les alertes de stockage"""
    if not usage:
        return
    
    total_gb = usage['total_gb']
    
    # Seuils d'alerte
    alerts = []
    
    if total_gb > 80:  # 80% de 100 GB
        alerts.append({
            'level': 'CRITICAL',
            'message': f'Utilisation critique: {total_gb:.2f} GB (80%+)',
            'action': 'Considérer l\'upgrade vers le plan Pro Max'
        })
    elif total_gb > 60:  # 60% de 100 GB
        alerts.append({
            'level': 'WARNING',
            'message': f'Utilisation élevée: {total_gb:.2f} GB (60%+)',
            'action': 'Surveiller de près l\'utilisation'
        })
    elif total_gb > 40:  # 40% de 100 GB
        alerts.append({
            'level': 'INFO',
            'message': f'Utilisation modérée: {total_gb:.2f} GB (40%+)',
            'action': 'Utilisation normale'
        })
    
    # Afficher les alertes
    for alert in alerts:
        if alert['level'] == 'CRITICAL':
            print(f"  🚨 {alert['level']}: {alert['message']}")
        elif alert['level'] == 'WARNING':
            print(f"  ⚠️ {alert['level']}: {alert['message']}")
        else:
            print(f"  ℹ️ {alert['level']}: {alert['message']}")
        
        print(f"    💡 Action: {alert['action']}")
    
    # Envoyer des alertes par email si nécessaire
    if alerts and any(a['level'] in ['CRITICAL', 'WARNING'] for a in alerts):
        send_storage_alert(alerts)


def send_storage_alert(alerts):
    """Envoyer une alerte par email"""
    try:
        subject = f"🚨 Alerte Stockage KBIS - {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        
        message = "Alerte de stockage détectée:\n\n"
        for alert in alerts:
            message += f"{alert['level']}: {alert['message']}\n"
            message += f"Action: {alert['action']}\n\n"
        
        message += f"Timestamp: {datetime.now().isoformat()}\n"
        message += "Application: KBIS IMMOBILIER\n"
        
        # Envoyer l'email (si configuré)
        if hasattr(settings, 'EMAIL_HOST_USER') and settings.EMAIL_HOST_USER:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [settings.EMAIL_HOST_USER],
                fail_silently=True
            )
            print("  📧 Alerte envoyée par email")
        else:
            print("  ⚠️ Email non configuré, alerte non envoyée")
            
    except Exception as e:
        print(f"  ❌ Erreur lors de l'envoi de l'alerte: {e}")


def generate_storage_report(usage):
    """Générer un rapport de stockage"""
    if not usage:
        return
    
    report = {
        'timestamp': datetime.now().isoformat(),
        'total_size': usage['total_size'],
        'total_gb': usage['total_gb'],
        'usage_percentage': (usage['total_gb'] / 100) * 100,
        'top_tables': usage['table_sizes'][:10],  # Top 10 des tables
        'top_indexes': usage['index_sizes'][:10],  # Top 10 des index
    }
    
    # Sauvegarder le rapport
    report_file = f"storage_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"  📋 Rapport sauvegardé: {report_file}")
    print(f"  📊 Utilisation: {report['usage_percentage']:.1f}%")
    print(f"  📋 Top tables: {len(report['top_tables'])}")
    print(f"  🔍 Top index: {len(report['top_indexes'])}")


if __name__ == "__main__":
    monitor_storage()
