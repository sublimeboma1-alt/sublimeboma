from django.db import migrations, models
import django.db.models.deletion


TYPE_FRAIS = [
    ('inscription', "Frais d'inscription"),
    ('minerval', 'Minerval'),
    ('uniforme', 'Uniforme'),
    ('examen', "Frais d'examen"),
    ('bibliotheque', 'Bibliotheque'),
    ('activite', 'Activite parascolaire'),
    ('cantine', 'Cantine'),
    ('transport', 'Transport'),
    ('ecusson', 'Ecusson'),
    ('tenasosp', 'Tenasosp'),
    ('dissertation', 'Dissertation'),
    ('exetat', 'Exetat'),
    ('cahier_communication', 'Cahier de communication'),
    ('journal_classe', 'Journal de classe'),
    ('autre', 'Autre'),
]

MODES_PAIEMENT = [
    ('cash', 'Especes'),
    ('mobile_money', 'Mobile Money'),
    ('banque', 'Virement bancaire'),
    ('cheque', 'Cheque'),
    ('carte', 'Carte bancaire'),
]

STATUTS_PAIEMENT = [
    ('valide', 'Valide'),
    ('annule', 'Annule'),
    ('en_attente', 'En attente'),
]

TRIMESTRES = [
    (1, '1er Trimestre'),
    (2, '2eme Trimestre'),
    (3, '3eme Trimestre'),
]


def create_reference_data(apps, schema_editor):
    TypeFrais = apps.get_model('frais_scolaires', 'TypeFrais')
    ModePaiement = apps.get_model('frais_scolaires', 'ModePaiement')
    StatutPaiement = apps.get_model('frais_scolaires', 'StatutPaiement')
    Trimestre = apps.get_model('frais_scolaires', 'Trimestre')

    for code, libelle in TYPE_FRAIS:
        TypeFrais.objects.update_or_create(code=code, defaults={'libelle': libelle, 'est_actif': True})

    for code, libelle in MODES_PAIEMENT:
        ModePaiement.objects.update_or_create(code=code, defaults={'libelle': libelle, 'est_actif': True})

    for code, libelle in STATUTS_PAIEMENT:
        StatutPaiement.objects.update_or_create(code=code, defaults={'libelle': libelle, 'est_actif': True})

    for numero, libelle in TRIMESTRES:
        Trimestre.objects.update_or_create(numero=numero, defaults={'libelle': libelle, 'est_actif': True})


class Migration(migrations.Migration):

    dependencies = [
        ('frais_scolaires', '0003_alter_fraisscolaire_type_frais_and_more'),
        ('eleves', '0009_reference_models_for_choices'),
    ]

    operations = [
        migrations.CreateModel(
            name='ModePaiement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=50, unique=True)),
                ('libelle', models.CharField(max_length=100)),
                ('est_actif', models.BooleanField(default=True)),
            ],
            options={
                'verbose_name': 'Mode de paiement',
                'verbose_name_plural': 'Modes de paiement',
                'ordering': ['libelle'],
            },
        ),
        migrations.CreateModel(
            name='StatutPaiement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=20, unique=True)),
                ('libelle', models.CharField(max_length=100)),
                ('est_actif', models.BooleanField(default=True)),
            ],
            options={
                'verbose_name': 'Statut de paiement',
                'verbose_name_plural': 'Statuts de paiement',
                'ordering': ['libelle'],
            },
        ),
        migrations.CreateModel(
            name='TypeFrais',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=50, unique=True)),
                ('libelle', models.CharField(max_length=100)),
                ('description', models.TextField(blank=True, null=True)),
                ('est_actif', models.BooleanField(default=True)),
            ],
            options={
                'verbose_name': 'Type de frais',
                'verbose_name_plural': 'Types de frais',
                'ordering': ['libelle'],
            },
        ),
        migrations.CreateModel(
            name='Trimestre',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('numero', models.PositiveSmallIntegerField(unique=True)),
                ('libelle', models.CharField(max_length=100)),
                ('est_actif', models.BooleanField(default=True)),
            ],
            options={
                'verbose_name': 'Trimestre',
                'verbose_name_plural': 'Trimestres',
                'ordering': ['numero'],
            },
        ),
        migrations.RunPython(create_reference_data, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='tariffrais',
            name='niveau',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='eleves.niveauclasse', to_field='code', verbose_name='Niveau'),
        ),
        migrations.AlterField(
            model_name='tariffrais',
            name='classe_maternel',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='eleves.classematernelle', to_field='code', verbose_name='Classe maternelle'),
        ),
        migrations.AlterField(
            model_name='tariffrais',
            name='trimestre',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='frais_scolaires.trimestre', to_field='numero', verbose_name='Trimestre'),
        ),
        migrations.AlterField(
            model_name='fraisscolaire',
            name='trimestre',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='frais_scolaires.trimestre', to_field='numero', verbose_name='Trimestre'),
        ),
        migrations.AlterField(
            model_name='paiement',
            name='mode_paiement',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='frais_scolaires.modepaiement', to_field='code', verbose_name='Mode de paiement'),
        ),
        migrations.AlterField(
            model_name='paiement',
            name='statut',
            field=models.ForeignKey(default='valide', on_delete=django.db.models.deletion.PROTECT, to='frais_scolaires.statutpaiement', to_field='code', verbose_name='Statut'),
        ),
        migrations.AlterField(
            model_name='fraisscolaire',
            name='type_frais',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='frais_scolaires.typefrais', to_field='code', verbose_name='Type de frais'),
        ),
        migrations.AlterField(
            model_name='tariffrais',
            name='type_frais',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='frais_scolaires.typefrais', to_field='code', verbose_name='Type de frais'),
        ),
    ]
