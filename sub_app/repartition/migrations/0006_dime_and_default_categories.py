from django.db import migrations, models


DEFAULT_CATEGORIES = [
    ('proprietaire', 'Proprietaire', '#315069', 10),
    ('enseignants', 'Enseignants', '#0C756F', 20),
    ('fonctionnement_general', 'Fonctionnement general', '#D28127', 30),
    ('fonctionnement_interne', 'Fonctionnement interne', '#7D5CB8', 40),
]


def create_default_categories(apps, schema_editor):
    Category = apps.get_model('repartition', 'CategorieRepartition')
    for code, label, color, order in DEFAULT_CATEGORIES:
        Category.objects.get_or_create(
            code=code,
            defaults={'libelle': label, 'couleur': color, 'ordre': order, 'est_active': True},
        )


class Migration(migrations.Migration):
    dependencies = [('repartition', '0005_parametrerepartition_annee_scolaire_and_more')]

    operations = [
        migrations.AddField(
            model_name='parametrerepartition',
            name='accepte_dime',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='parametrerepartition',
            name='pourcentage_dime',
            field=models.DecimalField(decimal_places=2, default=10, max_digits=5),
        ),
        migrations.RunPython(create_default_categories, migrations.RunPython.noop),
    ]
