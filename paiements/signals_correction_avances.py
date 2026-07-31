"""
Signal pour corriger automatiquement les avances mal configurées au démarrage
"""
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.conf import settings
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


@receiver(post_migrate)
def corriger_avances_automatiquement(sender, **kwargs):
    """
    Corrige automatiquement les avances mal configurées après les migrations.

    *** DÉSACTIVÉ PAR DÉFAUT DEPUIS LA V11 ***

    Ce signal réécrivait `nombre_mois_couverts` et `mois_fin_couverture` à chaque
    `migrate`, avec une règle de calcul DIFFÉRENTE de ServiceLogiqueAvanceUnique
    (troncature simple, sans le seuil de 50 % du loyer). Comme il ne s'activait
    qu'avec DEBUG=False, il se déclenchait à chaque déploiement en production et
    jamais en local : les périodes de couverture des avances « glissaient » d'un
    mois sans trace, et le prochain mois à payer avec.

    La réparation des avances passe désormais par une commande explicite,
    exécutable en simulation avant écriture :

        python manage.py reparer_avances_v11              # simulation + rapport
        python manage.py reparer_avances_v11 --appliquer  # écriture

    Pour réactiver malgré tout ce signal, poser FORCE_CORRECTION_AVANCES = True
    dans les settings.
    """
    # Ne s'exécute que pour l'app paiements
    if sender.name != 'paiements':
        return

    # Désactivé sauf activation explicite (dans TOUS les environnements)
    if not getattr(settings, 'FORCE_CORRECTION_AVANCES', False):
        logger.info(
            "⏭️  Correction automatique des avances désactivée "
            "(utilisez `manage.py reparer_avances_v11`)"
        )
        return

    try:
        from paiements.models_avance import AvanceLoyer
        from dateutil.relativedelta import relativedelta
        
        logger.info("=" * 80)
        logger.info("🔧 CORRECTION AUTOMATIQUE DES AVANCES AU DÉMARRAGE")
        logger.info("=" * 80)
        
        # Récupérer toutes les avances actives avec montant restant
        avances = AvanceLoyer.objects.filter(
            statut='active',
            montant_restant__gt=0
        ).select_related('contrat')
        
        if not avances.exists():
            logger.info("✅ Aucune avance active à corriger")
            return
        
        logger.info(f"📊 Analyse de {avances.count()} avances actives...")
        
        corrections_appliquees = 0
        
        for avance in avances:
            try:
                # Récupérer le loyer du contrat
                loyer_contrat = avance.contrat.get_loyer_total()
                if isinstance(loyer_contrat, str):
                    loyer_contrat = Decimal(loyer_contrat.replace(',', '').replace(' ', ''))
                else:
                    loyer_contrat = Decimal(str(loyer_contrat))
                
                # Calculer le nombre de mois selon le loyer du contrat
                mois_calcules_contrat = int(avance.montant_avance // loyer_contrat)
                mois_enregistres = avance.nombre_mois_couverts
                
                # Vérifier s'il y a une incohérence
                difference_loyer = abs(avance.loyer_mensuel - loyer_contrat)
                
                # Déterminer si une correction est nécessaire
                correction_necessaire = False
                nouveau_nombre_mois = mois_enregistres
                nouveau_loyer = avance.loyer_mensuel
                
                # Cas 1: Le montant correspond exactement au loyer du contrat (avance d'1 mois)
                if abs(avance.montant_avance - loyer_contrat) < 1000 and mois_enregistres > 1:
                    correction_necessaire = True
                    nouveau_nombre_mois = 1
                    nouveau_loyer = loyer_contrat
                    logger.warning(f"⚠️  Avance {avance.id}: Correction nécessaire (avance 1 mois détectée)")
                
                # Cas 2: Le loyer de l'avance est incorrect
                elif difference_loyer > 100 and mois_calcules_contrat != mois_enregistres:
                    correction_necessaire = True
                    nouveau_nombre_mois = mois_calcules_contrat
                    nouveau_loyer = loyer_contrat
                    logger.warning(f"⚠️  Avance {avance.id}: Correction nécessaire (incohérence loyer/mois)")
                
                if correction_necessaire:
                    # Appliquer la correction
                    ancien_nombre_mois = avance.nombre_mois_couverts
                    ancien_loyer = avance.loyer_mensuel
                    ancienne_fin = avance.mois_fin_couverture
                    
                    avance.loyer_mensuel = nouveau_loyer
                    avance.nombre_mois_couverts = nouveau_nombre_mois
                    
                    # Recalculer la fin de couverture
                    if nouveau_nombre_mois > 0:
                        avance.mois_fin_couverture = avance.mois_debut_couverture + relativedelta(months=nouveau_nombre_mois - 1)
                    else:
                        avance.mois_fin_couverture = avance.mois_debut_couverture
                    
                    avance.save()
                    corrections_appliquees += 1
                    
                    logger.info(f"✅ Avance {avance.id} corrigée:")
                    logger.info(f"   Loyer: {ancien_loyer:,.0f} → {nouveau_loyer:,.0f} F CFA")
                    logger.info(f"   Mois: {ancien_nombre_mois} → {nouveau_nombre_mois}")
                    logger.info(f"   Fin: {ancienne_fin} → {avance.mois_fin_couverture}")
            
            except Exception as e:
                logger.error(f"❌ Erreur lors de la correction de l'avance {avance.id}: {e}")
                continue
        
        if corrections_appliquees > 0:
            logger.info("=" * 80)
            logger.info(f"✅ {corrections_appliquees} avance(s) corrigée(s) automatiquement")
            logger.info("=" * 80)
        else:
            logger.info("✅ Aucune correction nécessaire")
    
    except Exception as e:
        logger.error(f"❌ Erreur lors de la correction automatique des avances: {e}")
        import traceback
        logger.error(traceback.format_exc())
