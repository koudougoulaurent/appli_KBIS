"""
Commande Django pour corriger les avances mal configurées
"""
from django.core.management.base import BaseCommand
from paiements.models_avance import AvanceLoyer
from decimal import Decimal


class Command(BaseCommand):
    help = 'Corrige les avances de loyer mal configurées (mois couverts incohérents)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Afficher les corrections sans les appliquer',
        )
        parser.add_argument(
            '--auto-fix',
            action='store_true',
            help='Corriger automatiquement les incohérences',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        auto_fix = options['auto_fix']
        
        self.stdout.write("=" * 80)
        self.stdout.write(self.style.SUCCESS("🔍 DIAGNOSTIC DES AVANCES DE LOYER"))
        self.stdout.write("=" * 80)
        
        # Récupérer toutes les avances actives
        avances = AvanceLoyer.objects.filter(
            statut='active',
            montant_restant__gt=0
        ).select_related('contrat')
        
        self.stdout.write(f"\n📊 Analyse de {avances.count()} avances actives...\n")
        
        problemes_trouves = 0
        corrections_appliquees = 0
        
        for avance in avances:
            # Récupérer le loyer du contrat
            try:
                loyer_contrat = avance.contrat.get_loyer_total()
                if isinstance(loyer_contrat, str):
                    loyer_contrat = Decimal(loyer_contrat.replace(',', '').replace(' ', ''))
                else:
                    loyer_contrat = Decimal(str(loyer_contrat))
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f"⚠️  Avance {avance.id}: Impossible de récupérer le loyer du contrat ({e})")
                )
                continue
            
            # Calculer le nombre de mois selon le loyer du contrat
            mois_calcules_contrat = int(avance.montant_avance // loyer_contrat)
            mois_enregistres = avance.nombre_mois_couverts
            
            # Calculer le nombre de mois selon le loyer de l'avance
            mois_calcules_avance = int(avance.montant_avance // avance.loyer_mensuel) if avance.loyer_mensuel > 0 else 0
            
            # Vérifier s'il y a une incohérence
            difference_loyer = abs(avance.loyer_mensuel - loyer_contrat)
            incoherence_mois = (mois_enregistres != mois_calcules_contrat)
            
            if difference_loyer > 100 or incoherence_mois:
                problemes_trouves += 1
                
                self.stdout.write(f"\n{'='*60}")
                self.stdout.write(self.style.ERROR(f"❌ PROBLÈME DÉTECTÉ - Avance ID {avance.id}"))
                self.stdout.write(f"{'='*60}")
                self.stdout.write(f"   Contrat: {avance.contrat}")
                self.stdout.write(f"   Date avance: {avance.date_avance}")
                self.stdout.write(f"   Montant avance: {avance.montant_avance:,.0f} F CFA")
                self.stdout.write(f"   ")
                self.stdout.write(f"   Loyer mensuel dans avance: {avance.loyer_mensuel:,.0f} F CFA")
                self.stdout.write(f"   Loyer mensuel du contrat: {loyer_contrat:,.0f} F CFA")
                self.stdout.write(f"   Différence: {difference_loyer:,.0f} F CFA")
                self.stdout.write(f"   ")
                self.stdout.write(f"   Mois enregistrés: {mois_enregistres}")
                self.stdout.write(f"   Mois calculés (avec loyer avance): {mois_calcules_avance}")
                self.stdout.write(f"   Mois calculés (avec loyer contrat): {mois_calcules_contrat}")
                self.stdout.write(f"   ")
                self.stdout.write(f"   Couverture actuelle: {avance.mois_debut_couverture} → {avance.mois_fin_couverture}")
                
                # Déterminer la correction
                correction_necessaire = False
                nouveau_nombre_mois = mois_enregistres
                nouveau_loyer = avance.loyer_mensuel
                
                # Cas 1: Le montant correspond exactement au loyer du contrat (avance d'1 mois)
                if abs(avance.montant_avance - loyer_contrat) < 1000 and mois_enregistres > 1:
                    correction_necessaire = True
                    nouveau_nombre_mois = 1
                    nouveau_loyer = loyer_contrat
                    self.stdout.write(self.style.WARNING(f"   💡 CORRECTION SUGGÉRÉE: Avance pour 1 mois"))
                
                # Cas 2: Le loyer de l'avance est incorrect, mais le nombre de mois est cohérent
                elif difference_loyer > 100 and mois_calcules_contrat == mois_enregistres:
                    correction_necessaire = True
                    nouveau_loyer = loyer_contrat
                    self.stdout.write(self.style.WARNING(f"   💡 CORRECTION SUGGÉRÉE: Ajuster le loyer mensuel"))
                
                # Cas 3: Le nombre de mois est incohérent
                elif incoherence_mois:
                    correction_necessaire = True
                    nouveau_nombre_mois = mois_calcules_contrat
                    nouveau_loyer = loyer_contrat
                    self.stdout.write(self.style.WARNING(f"   💡 CORRECTION SUGGÉRÉE: Ajuster le nombre de mois"))
                
                if correction_necessaire:
                    if auto_fix and not dry_run:
                        # Appliquer la correction
                        ancien_nombre_mois = avance.nombre_mois_couverts
                        ancien_loyer = avance.loyer_mensuel
                        ancienne_fin = avance.mois_fin_couverture
                        
                        avance.loyer_mensuel = nouveau_loyer
                        avance.nombre_mois_couverts = nouveau_nombre_mois
                        
                        # Recalculer la fin de couverture
                        from dateutil.relativedelta import relativedelta
                        if nouveau_nombre_mois > 0:
                            avance.mois_fin_couverture = avance.mois_debut_couverture + relativedelta(months=nouveau_nombre_mois - 1)
                        else:
                            avance.mois_fin_couverture = avance.mois_debut_couverture
                        
                        avance.save()
                        corrections_appliquees += 1
                        
                        self.stdout.write(self.style.SUCCESS(f"   ✅ CORRECTION APPLIQUÉE:"))
                        self.stdout.write(f"      Loyer: {ancien_loyer:,.0f} → {nouveau_loyer:,.0f} F CFA")
                        self.stdout.write(f"      Mois: {ancien_nombre_mois} → {nouveau_nombre_mois}")
                        self.stdout.write(f"      Fin couverture: {ancienne_fin} → {avance.mois_fin_couverture}")
                    else:
                        self.stdout.write(self.style.WARNING(f"   ⏸️  Correction non appliquée (utilisez --auto-fix pour corriger)"))
        
        # Résumé
        self.stdout.write(f"\n{'='*80}")
        self.stdout.write(self.style.SUCCESS("📊 RÉSUMÉ"))
        self.stdout.write(f"{'='*80}")
        self.stdout.write(f"   Avances analysées: {avances.count()}")
        self.stdout.write(f"   Problèmes trouvés: {problemes_trouves}")
        
        if auto_fix and not dry_run:
            self.stdout.write(self.style.SUCCESS(f"   Corrections appliquées: {corrections_appliquees}"))
        elif problemes_trouves > 0:
            self.stdout.write(self.style.WARNING(f"\n💡 Pour corriger automatiquement, exécutez:"))
            self.stdout.write(self.style.WARNING(f"   python manage.py corriger_avances --auto-fix"))
        else:
            self.stdout.write(self.style.SUCCESS(f"   ✅ Aucune correction nécessaire !"))
