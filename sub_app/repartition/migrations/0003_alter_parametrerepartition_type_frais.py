from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [('repartition', '0002_parametrerepartition_reglerepartition_parametre_and_more')]

    operations = [
        migrations.AlterField(
            model_name='parametrerepartition',
            name='type_frais',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='parametres_repartition', to='frais_scolaires.typefrais', to_field='code', unique=True),
        ),
    ]
