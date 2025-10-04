# Migration pour créer les modèles RetraitBailleur et RetraitQuittance

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('proprietes', '0001_initial'),
        ('utilisateurs', '0001_initial'),
        ('paiements', '0031_add_total_charges_bailleur_column'),
    ]

    operations = [
        migrations.CreateModel(
            name='RetraitBailleur',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('mois_retrait', models.DateField(help_text='Mois pour lequel le retrait est effectué', verbose_name='Mois de retrait')),
                ('montant_loyers_bruts', models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name='Montant des loyers bruts')),
                ('montant_charges_deductibles', models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name='Montant des charges déductibles')),
                ('montant_charges_bailleur', models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name='Montant des charges bailleur')),
                ('montant_net_a_payer', models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name='Montant net à payer')),
                ('statut', models.CharField(choices=[('en_attente', 'En attente'), ('valide', 'Validé'), ('paye', 'Payé'), ('annule', 'Annulé')], default='en_attente', max_length=20, verbose_name='Statut')),
                ('type_retrait', models.CharField(choices=[('mensuel', 'Retrait mensuel'), ('trimestriel', 'Retrait trimestriel'), ('annuel', 'Retrait annuel'), ('exceptionnel', 'Retrait exceptionnel')], default='mensuel', max_length=20, verbose_name='Type de retrait')),
                ('mode_retrait', models.CharField(choices=[('virement', 'Virement bancaire'), ('cheque', 'Chèque'), ('especes', 'Espèces')], default='virement', max_length=20, verbose_name='Mode de retrait')),
                ('date_demande', models.DateField(auto_now_add=True, verbose_name='Date de demande')),
                ('date_validation', models.DateField(blank=True, null=True, verbose_name='Date de validation')),
                ('date_paiement', models.DateField(blank=True, null=True, verbose_name='Date de paiement')),
                ('notes', models.TextField(blank=True, verbose_name='Notes')),
                ('is_deleted', models.BooleanField(default=False, verbose_name='Supprimé')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Date de création')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Date de modification')),
                ('bailleur', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='retraits', to='proprietes.bailleur', verbose_name='Bailleur')),
                ('cree_par', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='retraits_crees', to=settings.AUTH_USER_MODEL, verbose_name='Créé par')),
                ('valide_par', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='retraits_valides', to=settings.AUTH_USER_MODEL, verbose_name='Validé par')),
            ],
            options={
                'verbose_name': 'Retrait bailleur',
                'verbose_name_plural': 'Retraits bailleur',
                'ordering': ['-mois_retrait', '-created_at'],
            },
        ),
        migrations.CreateModel(
            name='RetraitQuittance',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('numero_quittance', models.CharField(max_length=50, unique=True, verbose_name='Numéro de quittance')),
                ('date_emission', models.DateField(auto_now_add=True, verbose_name="Date d'émission")),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Date de création')),
                ('cree_par', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='Créé par')),
                ('retrait', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='quittance', to='paiements.retraitbailleur', verbose_name='Retrait')),
            ],
            options={
                'verbose_name': 'Quittance de retrait',
                'verbose_name_plural': 'Quittances de retrait',
                'ordering': ['-date_emission'],
            },
        ),
        migrations.AddIndex(
            model_name='retraitbailleur',
            index=models.Index(fields=['bailleur', 'mois_retrait'], name='paiements_r_bailleu_123456_idx'),
        ),
        migrations.AddIndex(
            model_name='retraitbailleur',
            index=models.Index(fields=['statut'], name='paiements_r_statut_123456_idx'),
        ),
        migrations.AddIndex(
            model_name='retraitbailleur',
            index=models.Index(fields=['date_demande'], name='paiements_r_date_de_123456_idx'),
        ),
        migrations.AddConstraint(
            model_name='retraitbailleur',
            constraint=models.UniqueConstraint(condition=models.Q(('is_deleted', False)), fields=('bailleur', 'mois_retrait'), name='unique_retrait_actif_per_bailleur_month'),
        ),
    ]
