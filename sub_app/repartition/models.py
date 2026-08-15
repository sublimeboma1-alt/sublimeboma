from django.db import models


class CategorieRepartition(models.Model):
    code = models.CharField(max_length=40, unique=True)
    libelle = models.CharField(max_length=100)
    couleur = models.CharField(max_length=7, default='#0C756F')
    ordre = models.PositiveSmallIntegerField(default=0)
    est_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['ordre', 'libelle']

    def __str__(self):
        return self.libelle


class ParametreRepartition(models.Model):
    nom = models.CharField(max_length=120)
    type_frais = models.ForeignKey('frais_scolaires.TypeFrais', to_field='code', on_delete=models.CASCADE, related_name='parametres_repartition')
    annee_scolaire = models.ForeignKey('frais_scolaires.AnneeScolaire', on_delete=models.PROTECT, related_name='parametres_repartition', null=True, blank=True)
    est_actif = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-est_actif', '-id']
        unique_together = ['type_frais', 'annee_scolaire']

    def __str__(self):
        return self.nom


class RegleRepartition(models.Model):
    type_frais = models.ForeignKey('frais_scolaires.TypeFrais', to_field='code', on_delete=models.CASCADE, related_name='regles_repartition')
    categorie = models.ForeignKey(CategorieRepartition, on_delete=models.PROTECT, related_name='regles')
    parametre = models.ForeignKey(ParametreRepartition, on_delete=models.CASCADE, related_name='regles', null=True, blank=True)
    pourcentage = models.DecimalField(max_digits=5, decimal_places=2)
    est_active = models.BooleanField(default=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['parametre', 'categorie']
        ordering = ['categorie__ordre']


class LigneRepartition(models.Model):
    paiement = models.ForeignKey('frais_scolaires.Paiement', on_delete=models.CASCADE, related_name='repartitions')
    categorie = models.ForeignKey(CategorieRepartition, on_delete=models.PROTECT, related_name='lignes_repartition')
    pourcentage = models.DecimalField(max_digits=5, decimal_places=2)
    montant = models.DecimalField(max_digits=12, decimal_places=2)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['paiement', 'categorie']
        ordering = ['categorie__ordre']
