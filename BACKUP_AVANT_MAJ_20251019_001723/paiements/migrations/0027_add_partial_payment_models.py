# Generated manually for partial payment models

from django.db import migrations, models
import django.db.models.deletion
import django.core.validators
import django.utils.timezone
import uuid
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('contrats', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('paiements', '0026_detailretraitunite'),
    ]

    operations = [
        migrations.CreateModel(
            name='PlanPaiementPartiel',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('numero_plan', models.CharField(max_length=50, unique=True, verbose_name='Numéro du plan')),
                ('nom_plan', models.CharField(help_text='Ex: Plan de paiement échelonné - Janvier 2025', max_length=100, verbose_name='Nom du plan')),
                ('description', models.TextField(blank=True, verbose_name='Description du plan')),
                ('montant_total', models.DecimalField(decimal_places=2, max_digits=10, validators=[django.core.validators.MinValueValidator(0.01)], verbose_name='Montant total à payer')),
                ('montant_deja_paye', models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='Montant déjà payé')),
                ('montant_restant', models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='Montant restant')),
                ('date_debut', models.DateField(verbose_name='Date de début du plan')),
                ('date_fin_prevue', models.DateField(verbose_name='Date de fin prévue')),
                ('date_fin_reelle', models.DateField(blank=True, null=True, verbose_name='Date de fin réelle')),
                ('statut', models.CharField(choices=[('actif', 'Actif'), ('suspendu', 'Suspendu'), ('termine', 'Terminé'), ('annule', 'Annulé')], default='actif', max_length=20, verbose_name='Statut du plan')),
                ('date_creation', models.DateTimeField(auto_now_add=True, verbose_name='Date de création')),
                ('date_modification', models.DateTimeField(auto_now=True, verbose_name='Date de modification')),
                ('is_deleted', models.BooleanField(default=False, verbose_name='Supprimé')),
                ('deleted_at', models.DateTimeField(blank=True, null=True, verbose_name='Date de suppression')),
                ('contrat', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='plans_paiement_partiel', to='contrats.contrat', verbose_name='Contrat')),
                ('cree_par', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='plans_paiement_crees', to=settings.AUTH_USER_MODEL, verbose_name='Créé par')),
                ('deleted_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='plans_paiement_supprimes', to=settings.AUTH_USER_MODEL, verbose_name='Supprimé par')),
                ('modifie_par', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='plans_paiement_modifies', to=settings.AUTH_USER_MODEL, verbose_name='Modifié par')),
            ],
            options={
                'verbose_name': 'Plan de paiement partiel',
                'verbose_name_plural': 'Plans de paiement partiel',
                'ordering': ['-date_creation'],
            },
        ),
        migrations.CreateModel(
            name='EchelonPaiement',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('numero_echelon', models.PositiveIntegerField(verbose_name="Numéro d'échelon")),
                ('montant', models.DecimalField(decimal_places=2, max_digits=10, validators=[django.core.validators.MinValueValidator(0.01)], verbose_name="Montant de l'échelon")),
                ('date_echeance', models.DateField(verbose_name="Date d'échéance")),
                ('statut', models.CharField(choices=[('en_attente', 'En attente'), ('paye', 'Payé'), ('en_retard', 'En retard'), ('annule', 'Annulé')], default='en_attente', max_length=20, verbose_name='Statut de l\'échelon')),
                ('date_paiement', models.DateTimeField(blank=True, null=True, verbose_name='Date de paiement')),
                ('date_creation', models.DateTimeField(auto_now_add=True, verbose_name='Date de création')),
                ('cree_par', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='echelons_crees', to=settings.AUTH_USER_MODEL, verbose_name='Créé par')),
                ('paiement', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='echelon_paiement', to='paiements.paiement', verbose_name='Paiement associé')),
                ('plan', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='echelons', to='paiements.planpaiementpartiel', verbose_name='Plan de paiement')),
            ],
            options={
                'verbose_name': 'Échelon de paiement',
                'verbose_name_plural': 'Échelons de paiement',
                'ordering': ['plan', 'numero_echelon'],
            },
        ),
        migrations.CreateModel(
            name='PaiementPartiel',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('numero_paiement_partiel', models.CharField(max_length=50, unique=True, verbose_name='Numéro de paiement partiel')),
                ('montant', models.DecimalField(decimal_places=2, max_digits=10, validators=[django.core.validators.MinValueValidator(0.01)], verbose_name='Montant du paiement partiel')),
                ('montant_restant_apres', models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='Montant restant après ce paiement')),
                ('motif', models.CharField(max_length=200, verbose_name='Motif du paiement partiel')),
                ('description', models.TextField(blank=True, verbose_name='Description détaillée')),
                ('statut', models.CharField(choices=[('en_attente', 'En attente'), ('valide', 'Validé'), ('refuse', 'Refusé'), ('annule', 'Annulé')], default='en_attente', max_length=20, verbose_name='Statut')),
                ('date_paiement', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Date de paiement')),
                ('date_validation', models.DateTimeField(blank=True, null=True, verbose_name='Date de validation')),
                ('is_deleted', models.BooleanField(default=False, verbose_name='Supprimé')),
                ('deleted_at', models.DateTimeField(blank=True, null=True, verbose_name='Date de suppression')),
                ('cree_par', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='paiements_partiels_crees', to=settings.AUTH_USER_MODEL, verbose_name='Créé par')),
                ('deleted_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='paiements_partiels_supprimes', to=settings.AUTH_USER_MODEL, verbose_name='Supprimé par')),
                ('echelon', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='paiements', to='paiements.echelonpaiement', verbose_name='Échelon associé')),
                ('paiement_principal', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='paiements_partiels', to='paiements.paiement', verbose_name='Paiement principal')),
                ('plan', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='paiements_partiels', to='paiements.planpaiementpartiel', verbose_name='Plan de paiement')),
                ('valide_par', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='paiements_partiels_valides', to=settings.AUTH_USER_MODEL, verbose_name='Validé par')),
            ],
            options={
                'verbose_name': 'Paiement partiel',
                'verbose_name_plural': 'Paiements partiels',
                'ordering': ['-date_paiement'],
            },
        ),
        migrations.CreateModel(
            name='AlertePaiementPartiel',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('type_alerte', models.CharField(choices=[('echeance_proche', 'Échéance proche'), ('echeance_depassee', 'Échéance dépassée'), ('montant_insuffisant', 'Montant insuffisant'), ('plan_suspendu', 'Plan suspendu'), ('plan_termine', 'Plan terminé')], max_length=30, verbose_name="Type d'alerte")),
                ('message', models.TextField(verbose_name='Message d\'alerte')),
                ('niveau_urgence', models.CharField(choices=[('faible', 'Faible'), ('moyen', 'Moyen'), ('eleve', 'Élevé'), ('critique', 'Critique')], default='moyen', max_length=20, verbose_name='Niveau d\'urgence')),
                ('statut', models.CharField(choices=[('active', 'Active'), ('traitee', 'Traitée'), ('ignoree', 'Ignorée')], default='active', max_length=20, verbose_name='Statut de l\'alerte')),
                ('date_creation', models.DateTimeField(auto_now_add=True, verbose_name='Date de création')),
                ('date_traitement', models.DateTimeField(blank=True, null=True, verbose_name='Date de traitement')),
                ('cree_par', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='alertes_paiement_crees', to=settings.AUTH_USER_MODEL, verbose_name='Créé par')),
                ('echelon', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='alertes', to='paiements.echelonpaiement', verbose_name='Échelon concerné')),
                ('plan', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='alertes', to='paiements.planpaiementpartiel', verbose_name='Plan de paiement')),
                ('traite_par', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='alertes_paiement_traitees', to=settings.AUTH_USER_MODEL, verbose_name='Traité par')),
            ],
            options={
                'verbose_name': 'Alerte de paiement partiel',
                'verbose_name_plural': 'Alertes de paiement partiel',
                'ordering': ['-date_creation'],
            },
        ),
        migrations.AddConstraint(
            model_name='echelonpaiement',
            constraint=models.UniqueConstraint(fields=('plan', 'numero_echelon'), name='unique_plan_echelon'),
        ),
    ]
