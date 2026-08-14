from django.db import migrations, models
import django.db.models.deletion


NIVEAUX = [
    ('maternel', 'Maternel'),
    ('primaire', 'Primaire'),
    ('humanite', 'Humanite'),
]

CLASSES_MATERNELLES = [
    ('1ere_maternelle', '1ere maternelle'),
    ('2eme_maternelle', '2eme maternelle'),
    ('3eme_maternelle', '3eme maternelle'),
]

CLASSES_PRIMAIRES = [
    ('1ere', '1ere annee'),
    ('2eme', '2eme annee'),
    ('3eme', '3eme annee'),
    ('4eme', '4eme annee'),
    ('5eme', '5eme annee'),
    ('6eme', '6eme annee'),
    ('1ère', '1ere annee'),
    ('2ème', '2eme annee'),
    ('3ème', '3eme annee'),
    ('4ème', '4eme annee'),
    ('5ème', '5eme annee'),
    ('6ème', '6eme annee'),
    ('1ère', '1ere annee'),
    ('2ème', '2eme annee'),
    ('3ème', '3eme annee'),
    ('4ème', '4eme annee'),
    ('5ème', '5eme annee'),
    ('6ème', '6eme annee'),
]

CLASSES_HUMANITES = [
    ('7eme', '7eme annee'),
    ('8eme', '8eme annee'),
    ('1ere_humanite', '1ere humanite'),
    ('2eme_humanite', '2eme humanite'),
    ('3eme_humanite', '3eme humanite'),
    ('4eme_humanite', '4eme humanite'),
    ('1ère humanité', '1ere humanite'),
    ('2ème humanité', '2eme humanite'),
    ('3ème humanité', '3eme humanite'),
    ('4ème humanité', '4eme humanite'),
    ('1ere_maternelle', '1ere maternelle'),
    ('2eme_maternelle', '2eme maternelle'),
    ('3eme_maternelle', '3eme maternelle'),
    ('7ème', '7eme annee'),
    ('8ème', '8eme annee'),
    ('1ère humanité', '1ere humanite'),
    ('2ème humanité', '2eme humanite'),
    ('3ème humanité', '3eme humanite'),
    ('4ème humanité', '4eme humanite'),
]

SECTIONS = [
    ('chimie_biologie', 'Chimie Biologie'),
    ('pedagogie', 'Pedagogie'),
    ('electricite', 'Electricite'),
    ('coupe_couture', 'Coupe et Couture'),
    ('latin_philo', 'Latin Philo'),
    ('commerciale', 'Commerciale'),
    ('construction', 'Construction'),
    ('mecanique_auto', 'Mecanique Auto'),
    ('generale', 'Generale'),
]

SEXES = [
    ('M', 'Masculin'),
    ('F', 'Feminin'),
]

STATUTS = [
    ('actif', 'Actif'),
    ('inactif', 'Inactif'),
    ('suspendu', 'Suspendu'),
    ('diplome', 'Diplome'),
    ('diplômé', 'Diplome'),
    ('diplômé', 'Diplome'),
]


def seed_model(model, values):
    for code, libelle in values:
        model.objects.update_or_create(code=code, defaults={'libelle': libelle, 'est_actif': True})


def create_reference_data(apps, schema_editor):
    seed_model(apps.get_model('eleves', 'NiveauClasse'), NIVEAUX)
    seed_model(apps.get_model('eleves', 'ClasseMaternelle'), CLASSES_MATERNELLES)
    seed_model(apps.get_model('eleves', 'ClassePrimaire'), CLASSES_PRIMAIRES)
    seed_model(apps.get_model('eleves', 'ClasseHumanite'), CLASSES_HUMANITES)
    seed_model(apps.get_model('eleves', 'SectionHumanite'), SECTIONS)
    seed_model(apps.get_model('eleves', 'Sexe'), SEXES)
    seed_model(apps.get_model('eleves', 'StatutEleve'), STATUTS)


def reference_model(name, verbose_name, verbose_name_plural):
    return migrations.CreateModel(
        name=name,
        fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('code', models.CharField(max_length=50, unique=True)),
            ('libelle', models.CharField(max_length=100)),
            ('est_actif', models.BooleanField(default=True)),
        ],
        options={
            'verbose_name': verbose_name,
            'verbose_name_plural': verbose_name_plural,
            'ordering': ['libelle'],
        },
    )


class Migration(migrations.Migration):

    dependencies = [
        ('eleves', '0008_alter_eleve_lieu_de_naissance'),
    ]

    operations = [
        reference_model('NiveauClasse', 'Niveau', 'Niveaux'),
        reference_model('ClasseMaternelle', 'Classe maternelle', 'Classes maternelles'),
        reference_model('ClassePrimaire', 'Classe primaire', 'Classes primaires'),
        reference_model('ClasseHumanite', 'Classe humanite', 'Classes humanites'),
        reference_model('SectionHumanite', 'Section humanite', 'Sections humanites'),
        reference_model('Sexe', 'Sexe', 'Sexes'),
        reference_model('StatutEleve', 'Statut eleve', 'Statuts eleves'),
        migrations.RunPython(create_reference_data, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='classe',
            name='niveau',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='eleves.niveauclasse', to_field='code'),
        ),
        migrations.AlterField(
            model_name='classe',
            name='classe_maternel',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='eleves.classematernelle', to_field='code'),
        ),
        migrations.AlterField(
            model_name='classe',
            name='classe_primaire',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='eleves.classeprimaire', to_field='code'),
        ),
        migrations.AlterField(
            model_name='classe',
            name='classe_humanite',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='eleves.classehumanite', to_field='code'),
        ),
        migrations.AlterField(
            model_name='classe',
            name='section',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='eleves.sectionhumanite', to_field='code', verbose_name='Section (Humanite)'),
        ),
        migrations.AlterField(
            model_name='eleve',
            name='sexe',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='eleves.sexe', to_field='code', verbose_name='Sexe'),
        ),
        migrations.AlterField(
            model_name='eleve',
            name='statut',
            field=models.ForeignKey(default='actif', on_delete=django.db.models.deletion.PROTECT, to='eleves.statuteleve', to_field='code', verbose_name='Statut'),
        ),
    ]
