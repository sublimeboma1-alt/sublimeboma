from django.conf import settings
from django.db import models
from django.utils import timezone
import secrets

class JetonRegularisation(models.Model):
    code = models.CharField(max_length=32, unique=True, editable=False)
    description = models.CharField(max_length=180, blank=True)
    actif = models.BooleanField(default=True)
    cree_le = models.DateTimeField(auto_now_add=True)
    cree_par = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = secrets.token_urlsafe(18).upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.code

    class Meta:
        verbose_name = 'Jeton de regularisation'
        verbose_name_plural = 'Jetons de regularisation'

class Regularisation(models.Model):
    EN_ATTENTE = 'en_attente'
    VALIDE = 'valide'
    REFUSE = 'refuse'
    STATUTS = [(EN_ATTENTE, 'En attente'), (VALIDE, 'Valide'), (REFUSE, 'Refuse')]
    eleve = models.ForeignKey('eleves.Eleve', on_delete=models.PROTECT, related_name='regularisations_scolaires')
    annee_scolaire = models.ForeignKey('frais_scolaires.AnneeScolaire', on_delete=models.PROTECT)
    montant = models.DecimalField(max_digits=10, decimal_places=2)
    date_declaration = models.DateField(default=timezone.localdate)
    reference = models.CharField(max_length=100, blank=True)
    observations = models.TextField(blank=True)
    statut = models.CharField(max_length=16, choices=STATUTS, default=EN_ATTENTE)
    cree_par = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name='regularisations_creees')
    valide_par = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='regularisations_validees')
    date_validation = models.DateTimeField(null=True, blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_creation']
        verbose_name = 'Regularisation scolaire'
        verbose_name_plural = 'Regularisations scolaires'

    def __str__(self):
        return f'{self.eleve} - {self.annee_scolaire} - {self.montant}'
