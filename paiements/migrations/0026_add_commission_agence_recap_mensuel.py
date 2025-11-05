# Generated manually for commission agence feature in RecapMensuel

from django.db import migrations, models
from decimal import Decimal


def calculer_commission_recaps_existants(apps, schema_editor):
    """Calcule la commission agence et le montant réellement payé pour les récapitulatifs existants."""
    RecapMensuel = apps.get_model('paiements', 'RecapMensuel')
    
    # Filtrer seulement les récapitulatifs avec un bailleur (après la migration 0025, tous doivent en avoir un)
    recaps = RecapMensuel.objects.filter(bailleur__isnull=False)
    updated_count = 0
    
    for recap in recaps:
        try:
            # Vérifier que le bailleur existe toujours
            if not recap.bailleur:
                print(f"[WARN] Recapitulatif {recap.id}: bailleur manquant, ignore")
                continue
            
            # Calculer directement la commission et le montant réellement payé
            # On ne peut pas utiliser les méthodes du modèle dans les migrations
            if recap.total_net_a_payer:
                commission_agence = recap.total_net_a_payer * Decimal('0.10')
                montant_reellement_paye = max(recap.total_net_a_payer - commission_agence, Decimal('0'))
            else:
                commission_agence = Decimal('0')
                montant_reellement_paye = Decimal('0')
            
            recap.commission_agence = commission_agence
            recap.montant_reellement_paye = montant_reellement_paye
            recap.save(update_fields=['commission_agence', 'montant_reellement_paye'])
            updated_count += 1
            
        except Exception as e:
            # En cas d'erreur, essayer au moins de calculer la commission basique
            try:
                if recap.total_net_a_payer:
                    commission_agence = recap.total_net_a_payer * Decimal('0.10')
                    montant_reellement_paye = max(recap.total_net_a_payer - commission_agence, Decimal('0'))
                else:
                    commission_agence = Decimal('0')
                    montant_reellement_paye = Decimal('0')
                
                recap.commission_agence = commission_agence
                recap.montant_reellement_paye = montant_reellement_paye
                recap.save(update_fields=['commission_agence', 'montant_reellement_paye'])
                updated_count += 1
                print(f"[WARN] Recapitulatif {recap.id}: calcul basique effectue (erreur: {str(e)})")
            except Exception as e2:
                print(f"[ERROR] Erreur pour le recapitulatif {recap.id}: {str(e2)}")
    
    print(f"\n[OK] {updated_count} recapitulatif(s) mensuel(s) mis a jour avec commission agence et montant reellement paye.")


def reverse_calculer_commission_recaps_existants(apps, schema_editor):
    """Fonction de rollback - remet les valeurs à 0."""
    RecapMensuel = apps.get_model('paiements', 'RecapMensuel')
    RecapMensuel.objects.all().update(
        commission_agence=Decimal('0'),
        montant_reellement_paye=Decimal('0')
    )


class Migration(migrations.Migration):

    dependencies = [
        ('paiements', '0025_rendre_bailleur_obligatoire_recap'),
    ]

    operations = [
        migrations.AddField(
            model_name='recapmensuel',
            name='commission_agence',
            field=models.DecimalField(
                decimal_places=2,
                default=0,
                max_digits=12,
                verbose_name='Commission agence (10%)',
                help_text='Commission de l\'agence de gestion immobilière (10% du montant net)'
            ),
        ),
        migrations.AddField(
            model_name='recapmensuel',
            name='montant_reellement_paye',
            field=models.DecimalField(
                decimal_places=2,
                default=0,
                max_digits=12,
                verbose_name='Montant réellement payé',
                help_text='Montant net - Commission agence'
            ),
        ),
        migrations.RunPython(
            calculer_commission_recaps_existants,
            reverse_calculer_commission_recaps_existants
        ),
    ]

