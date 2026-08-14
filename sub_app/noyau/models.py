from django.db import models


class IdentiteEtablissement(models.Model):
    nom = models.CharField(max_length=200, default='Complexe Scolaire Sublime')
    espace = models.CharField(max_length=120, default='Administration')
    sigle = models.CharField(max_length=20, default='CS')
    adresse = models.CharField(max_length=255, blank=True)
    telephone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    est_active = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.nom} - {self.espace}'

    @classmethod
    def active(cls):
        identite = cls.objects.filter(est_active=True).order_by('-date_modification').first()
        if identite:
            return identite

        return cls.objects.order_by('-date_modification').first()

    class Meta:
        verbose_name = "Identite de l'etablissement"
        verbose_name_plural = "Identites de l'etablissement"
        ordering = ['-est_active', '-date_modification']
