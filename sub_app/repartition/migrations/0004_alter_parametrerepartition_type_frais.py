from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [('repartition', '0003_alter_parametrerepartition_type_frais')]

    operations = [
        migrations.AlterField(
            model_name='parametrerepartition',
            name='type_frais',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='parametre_repartition', to='frais_scolaires.typefrais', to_field='code'),
        ),
    ]
