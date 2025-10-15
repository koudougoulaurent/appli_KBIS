"""
Script de migration pour ajouter le champ total_charges_bailleur au modèle RecapMensuel
et pour intégrer le système intelligent des charges bailleur.
"""

from django.db import migrations, models
from django.utils.translation import gettext_lazy as _


class Migration(migrations.Migration):
    """
    Migration pour ajouter le support des charges bailleur dans les récapitulatifs mensuels.
    """
    
    dependencies = [
        ('paiements', '0001_initial'),  # Ajustez selon votre dernière migration
    ]
    
    operations = [
        # Ajouter le champ total_charges_bailleur au modèle RecapMensuel
        migrations.AddField(
            model_name='recapmensuel',
            name='total_charges_bailleur',
            field=models.DecimalField(
                max_digits=12, 
                decimal_places=2, 
                default=0, 
                verbose_name=_("Total des charges bailleur")
            ),
        ),
        
        # Ajouter un index pour optimiser les requêtes
        migrations.AddIndex(
            model_name='recapmensuel',
            index=models.Index(
                fields=['mois_recap', 'total_charges_bailleur'], 
                name='paiements_recap_charges_bailleur_idx'
            ),
        ),
    ]
