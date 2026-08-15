from django.db import migrations, models
import django.db.models.deletion


def migrate_rules(apps, schema_editor):
    Parametre = apps.get_model('repartition', 'ParametreRepartition')
    Regle = apps.get_model('repartition', 'RegleRepartition')
    grouped = {}
    for rule in Regle.objects.all():
        grouped.setdefault(rule.type_frais_id, []).append(rule)
    for type_code, rules in grouped.items():
        parameter = Parametre.objects.create(nom=f'Repartition {type_code}', type_frais_id=type_code)
        Regle.objects.filter(id__in=[rule.id for rule in rules]).update(parametre=parameter)


class Migration(migrations.Migration):
    dependencies = [('repartition', '0001_initial')]

    operations = [
        migrations.CreateModel(name='ParametreRepartition', fields=[('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')), ('nom', models.CharField(max_length=120)), ('est_actif', models.BooleanField(default=True)), ('date_creation', models.DateTimeField(auto_now_add=True)), ('type_frais', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='parametres_repartition', to='frais_scolaires.typefrais', to_field='code'))], options={'ordering': ['-est_actif', '-id']}),
        migrations.AddField(model_name='reglerepartition', name='parametre', field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='regles', to='repartition.parametrerepartition')),
        migrations.RunPython(migrate_rules, migrations.RunPython.noop),
        migrations.AlterUniqueTogether(name='reglerepartition', unique_together={('parametre', 'categorie')}),
    ]
