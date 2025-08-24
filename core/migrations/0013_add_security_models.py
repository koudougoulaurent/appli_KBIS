# Generated manually to add missing security models

from django.db import migrations, models
import django.db.models.deletion
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0012_merge_0009_fix_devise_model_0011_auto_20250823_1502'),
        ('auth', '0012_alter_user_first_name_max_length'),
        ('utilisateurs', '0004_alter_utilisateur_managers'),
    ]

    operations = [
        migrations.CreateModel(
            name='NiveauAcces',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(max_length=50, unique=True, verbose_name='Nom du niveau')),
                ('niveau', models.CharField(max_length=20, choices=[
                    ('public', 'Public - Données générales'),
                    ('interne', 'Interne - Données de l\'équipe'),
                    ('confidentiel', 'Confidentiel - Données sensibles'),
                    ('secret', 'Secret - Données critiques direction'),
                    ('top_secret', 'Top Secret - Données stratégiques')
                ], unique=True, verbose_name='Niveau d\'accès')),
                ('description', models.TextField(verbose_name='Description')),
                ('priorite', models.PositiveIntegerField(validators=[
                    django.core.validators.MinValueValidator(1),
                    django.core.validators.MaxValueValidator(10)
                ], verbose_name='Priorité')),
                ('date_creation', models.DateTimeField(auto_now_add=True)),
                ('date_modification', models.DateTimeField(auto_now=True)),
                ('actif', models.BooleanField(default=True, verbose_name='Actif')),
                ('groupes_autorises', models.ManyToManyField(
                    to='auth.group',
                    related_name='niveaux_acces',
                    verbose_name='Groupes autorisés'
                )),
            ],
            options={
                'verbose_name': 'Niveau d\'accès',
                'verbose_name_plural': 'Niveaux d\'accès',
                'ordering': ['-priorite', 'nom'],
            },
        ),
        migrations.CreateModel(
            name='PermissionTableauBord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(max_length=100, unique=True, verbose_name='Nom de la permission')),
                ('type_donnees', models.CharField(max_length=20, choices=[
                    ('financier', 'Données financières'),
                    ('locataire', 'Données locataires'),
                    ('bailleur', 'Données bailleurs'),
                    ('propriete', 'Données propriétés'),
                    ('contrat', 'Données contrats'),
                    ('paiement', 'Données paiements'),
                    ('charge', 'Données charges'),
                    ('statistique', 'Statistiques globales'),
                    ('rapport', 'Rapports détaillés')
                ], verbose_name='Type de données')),
                ('peut_voir_montants', models.BooleanField(default=False, verbose_name='Peut voir les montants exacts')),
                ('peut_voir_details_personnels', models.BooleanField(default=False, verbose_name='Peut voir les détails personnels')),
                ('peut_voir_historique', models.BooleanField(default=False, verbose_name='Peut voir l\'historique complet')),
                ('peut_exporter', models.BooleanField(default=False, verbose_name='Peut exporter les données')),
                ('peut_imprimer', models.BooleanField(default=False, verbose_name='Peut imprimer les rapports')),
                ('limite_periode_jours', models.PositiveIntegerField(blank=True, null=True, verbose_name='Limitation période (jours)')),
                ('limite_nombre_resultats', models.PositiveIntegerField(blank=True, null=True, verbose_name='Limite nombre de résultats')),
                ('date_creation', models.DateTimeField(auto_now_add=True)),
                ('date_modification', models.DateTimeField(auto_now=True)),
                ('actif', models.BooleanField(default=True, verbose_name='Actif')),
                ('niveau_acces_requis', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    to='core.niveauacces',
                    verbose_name='Niveau d\'accès requis'
                )),
            ],
            options={
                'verbose_name': 'Permission tableau de bord',
                'verbose_name_plural': 'Permissions tableaux de bord',
                'ordering': ['type_donnees', 'nom'],
            },
        ),
        migrations.CreateModel(
            name='LogAccesDonnees',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type_action', models.CharField(max_length=20, choices=[
                    ('consultation', 'Consultation'),
                    ('export', 'Export'),
                    ('impression', 'Impression'),
                    ('modification', 'Modification'),
                    ('suppression', 'Suppression')
                ], verbose_name='Type d\'action')),
                ('type_donnees', models.CharField(max_length=50, verbose_name='Type de données accédées')),
                ('identifiant_objet', models.CharField(blank=True, max_length=100, null=True, verbose_name='Identifiant de l\'objet')),
                ('adresse_ip', models.GenericIPAddressField(blank=True, null=True, verbose_name='Adresse IP')),
                ('user_agent', models.TextField(blank=True, null=True, verbose_name='User Agent')),
                ('timestamp', models.DateTimeField(auto_now_add=True, verbose_name='Horodatage')),
                ('succes', models.BooleanField(default=True, verbose_name='Succès')),
                ('message_erreur', models.TextField(blank=True, null=True, verbose_name='Message d\'erreur')),
                ('niveau_acces_utilise', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    to='core.niveauacces',
                    verbose_name='Niveau d\'accès utilisé'
                )),
                ('utilisateur', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    to='utilisateurs.utilisateur',
                    verbose_name='Utilisateur'
                )),
            ],
            options={
                'verbose_name': 'Log d\'accès aux données',
                'verbose_name_plural': 'Logs d\'accès aux données',
                'ordering': ['-timestamp'],
            },
        ),
        migrations.CreateModel(
            name='ConfigurationTableauBord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom_tableau', models.CharField(max_length=100, verbose_name='Nom du tableau')),
                ('par_defaut', models.BooleanField(default=False, verbose_name='Configuration par défaut')),
                ('widgets_actifs', models.JSONField(default=list, verbose_name='Widgets actifs')),
                ('masquer_montants_sensibles', models.BooleanField(default=True, verbose_name='Masquer les montants sensibles')),
                ('date_creation', models.DateTimeField(auto_now_add=True)),
                ('date_modification', models.DateTimeField(auto_now=True)),
                ('utilisateur', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    to='utilisateurs.utilisateur',
                    verbose_name='Utilisateur'
                )),
            ],
            options={
                'verbose_name': 'Configuration tableau de bord',
                'verbose_name_plural': 'Configurations tableaux de bord',
                'ordering': ['-date_modification'],
            },
        ),
    ]
