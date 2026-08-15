from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [('repartition', '0004_alter_parametrerepartition_type_frais')]

    operations = [
        migrations.AddField(
            model_name='parametrerepartition',
            name='annee_scolaire',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='parametres_repartition', to='frais_scolaires.anneescolaire'),
        ),
        migrations.AlterField(
            model_name='parametrerepartition',
            name='type_frais',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='parametres_repartition', to='frais_scolaires.typefrais', to_field='code'),
        ),
        migrations.AlterUniqueTogether(name='parametrerepartition', unique_together={('type_frais', 'annee_scolaire')}),
    ]
