from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('eleves', '0011_eleve_annee_scolaire'),
        ('frais_scolaires', '0006_alter_fraisscolaire_unique_together_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='fraisscolaire',
            name='eleve',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='frais_inscription', to='eleves.eleve', verbose_name='Élève'),
        ),
        migrations.AddField(
            model_name='paiement',
            name='eleve',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='paiements', to='eleves.eleve', verbose_name='Élève'),
        ),
    ]
