# Generated manually for commission agence feature in RecapMensuel

from django.db import migrations, models
from decimal import Decimal


def calculer_commission_recaps_existants(apps, schema_editor):
    """Calcule la commission agence et le montant réellement payé pour les récapitulatifs existants."""
    RecapMensuel = apps.get_model('paiements', 'RecapMensuel')
    
    recaps = RecapMensuel.objects.all().select_related('bailleur')
    updated_count = 0
    
    for recap in recaps:
        try:
            # Utiliser la méthode calculer_totaux_bailleur qui recalcule tout avec la nouvelle logique
            # Cette méthode calcule automatiquement la commission et le montant réellement payé
            totaux = recap.calculer_totaux_bailleur()
            
            # Vérifier que la commission a été calculée
            if 'commission_agence' in totaux:
                recap.commission_agence = totaux['commission_agence']
                recap.montant_reellement_paye = totaux['montant_reellement_paye']
            else:
                # Fallback : calculer manuellement si la méthode n'a pas retourné la commission
                commission_agence = recap.total_net_a_payer * Decimal('0.10')
                montant_reellement_paye = max(recap.total_net_a_payer - commission_agence, Decimal('0'))
                recap.commission_agence = commission_agence
                recap.montant_reellement_paye = montant_reellement_paye
            
            # Sauvegarder tous les champs mis à jour
            recap.save()
            updated_count += 1
            
        except Exception as e:
            # En cas d'erreur, calculer au moins la commission basique
            try:
                commission_agence = recap.total_net_a_payer * Decimal('0.10')
                montant_reellement_paye = max(recap.total_net_a_payer - commission_agence, Decimal('0'))
                recap.commission_agence = commission_agence
                recap.montant_reellement_paye = montant_reellement_paye
                recap.save(update_fields=['commission_agence', 'montant_reellement_paye'])
                updated_count += 1
                print(f"⚠️  Récapitulatif {recap.id}: calcul basique effectué (erreur lors du recalcul complet: {str(e)})")
            except Exception as e2:
                print(f"❌ Erreur pour le récapitulatif {recap.id}: {str(e2)}")
    
    print(f"\n✅ {updated_count} récapitulatif(s) mensuel(s) mis à jour avec commission agence et montant réellement payé.")


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

