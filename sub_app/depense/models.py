from django.db import models


class CategorieDepense(models.Model):
    nom = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.nom

    class Meta:
        verbose_name = "Categorie"
        verbose_name_plural = "Categories"
