import django.db.models.deletion
from django.db import migrations, models


def attach_eleves_to_school_year(apps, schema_editor):
    Eleve = apps.get_model('eleves', 'Eleve')
    AnneeScolaire = apps.get_model('frais_scolaires', 'AnneeScolaire')
    active_annee = AnneeScolaire.objects.filter(est_active=True).first()

    for eleve in Eleve.objects.all():
        annee = None
        if eleve.date_inscription:
            annee = AnneeScolaire.objects.filter(
                date_debut__lte=eleve.date_inscription,
                date_fin__gte=eleve.date_inscription,
            ).first()

        if not annee:
            annee = active_annee

        if annee:
            eleve.annee_scolaire_id = annee.id
            eleve.save(update_fields=['annee_scolaire'])


class Migration(migrations.Migration):

    dependencies = [
        ('frais_scolaires', '0004_reference_models_for_fees'),
        ('eleves', '0010_alter_classe_section'),
    ]

    operations = [
        migrations.AddField(
            model_name='eleve',
            name='annee_scolaire',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='eleves',
                to='frais_scolaires.anneescolaire',
                verbose_name='Année scolaire',
            ),
        ),
        migrations.RunPython(attach_eleves_to_school_year, migrations.RunPython.noop),
    ]
