from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True
    dependencies = [('frais_scolaires', '0004_reference_models_for_fees')]

    operations = [
        migrations.CreateModel(name='CategorieRepartition', fields=[('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')), ('code', models.CharField(max_length=40, unique=True)), ('libelle', models.CharField(max_length=100)), ('couleur', models.CharField(default='#0C756F', max_length=7)), ('ordre', models.PositiveSmallIntegerField(default=0)), ('est_active', models.BooleanField(default=True))], options={'ordering': ['ordre', 'libelle']}),
        migrations.CreateModel(name='RegleRepartition', fields=[('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')), ('pourcentage', models.DecimalField(decimal_places=2, max_digits=5)), ('est_active', models.BooleanField(default=True)), ('date_modification', models.DateTimeField(auto_now=True)), ('categorie', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='regles', to='repartition.categorierepartition')), ('type_frais', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='regles_repartition', to='frais_scolaires.typefrais', to_field='code'))], options={'ordering': ['categorie__ordre'], 'unique_together': {('type_frais', 'categorie')}}),
        migrations.CreateModel(name='LigneRepartition', fields=[('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')), ('pourcentage', models.DecimalField(decimal_places=2, max_digits=5)), ('montant', models.DecimalField(decimal_places=2, max_digits=12)), ('date_creation', models.DateTimeField(auto_now_add=True)), ('categorie', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='lignes_repartition', to='repartition.categorierepartition')), ('paiement', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='repartitions', to='frais_scolaires.paiement'))], options={'ordering': ['categorie__ordre'], 'unique_together': {('paiement', 'categorie')}}),
    ]
