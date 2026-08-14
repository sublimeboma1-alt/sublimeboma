from django.db import migrations, models


def create_default_identity(apps, schema_editor):
    IdentiteEtablissement = apps.get_model('noyau', 'IdentiteEtablissement')
    IdentiteEtablissement.objects.update_or_create(
        est_active=True,
        defaults={
            'nom': 'Complexe Scolaire Sublime',
            'espace': 'Administration',
            'sigle': 'CS',
        },
    )


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='IdentiteEtablissement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(default='Complexe Scolaire Sublime', max_length=200)),
                ('espace', models.CharField(default='Administration', max_length=120)),
                ('sigle', models.CharField(default='CS', max_length=20)),
                ('adresse', models.CharField(blank=True, max_length=255)),
                ('telephone', models.CharField(blank=True, max_length=50)),
                ('email', models.EmailField(blank=True, max_length=254)),
                ('est_active', models.BooleanField(default=True)),
                ('date_creation', models.DateTimeField(auto_now_add=True)),
                ('date_modification', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': "Identite de l'etablissement",
                'verbose_name_plural': "Identites de l'etablissement",
                'ordering': ['-est_active', '-date_modification'],
            },
        ),
        migrations.RunPython(create_default_identity, migrations.RunPython.noop),
    ]
