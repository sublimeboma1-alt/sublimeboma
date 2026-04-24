from django.db import models

import random
import string
# Create your models here.
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import datetime

class CategorieDepense(models.Model):
    nom = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return self.nom
    
    class Meta:
        verbose_name = "Catégorie"
        verbose_name_plural = "Catégories"


class Depense(models.Model):
    MODE_PAIEMENT = [
        ('cash', 'Espèces'),
        ('mobile_money', 'Mobile Money'),
        ('virement', 'Virement bancaire'),
        ('cheque', 'Chèque'),
    ]
    
    code = models.CharField(max_length=20, unique=True, editable=False, verbose_name="Code dépense")
    titre = models.CharField(max_length=200, verbose_name="Titre de la dépense")
    categorie = models.ForeignKey(CategorieDepense, on_delete=models.CASCADE, verbose_name="Catégorie")
    montant = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Montant (FC)")
    date_depense = models.DateField(default=timezone.now, verbose_name="Date de dépense")
    beneficiaire = models.CharField(max_length=200, verbose_name="Bénéficiaire")
    mode_paiement = models.CharField(max_length=20, choices=MODE_PAIEMENT, verbose_name="Mode de paiement")
    justificatif = models.ImageField(upload_to='depenses/justificatifs/', blank=True, null=True, verbose_name="Justificatif")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    enregistre_par = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Enregistré par")
    date_enregistrement = models.DateTimeField(auto_now_add=True)
    
    def generate_code(self):
        """Générer un code aléatoire unique: 57NH367, 89XC452, etc."""
        while True:
            # 2 chiffres + 2 lettres + 3 chiffres
            part1 = ''.join(random.choices(string.digits, k=2))
            part2 = ''.join(random.choices(string.ascii_uppercase, k=2))
            part3 = ''.join(random.choices(string.digits, k=3))
            code = f"{part1}{part2}{part3}"
            
            # Vérifier que le code n'existe pas déjà
            if not Depense.objects.filter(code=code).exists():
                return code
    
    def save(self, *args, **kwargs):
        if not self.code:
            self.code = self.generate_code()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.code} - {self.titre} - {self.montant} FC"
    
    class Meta:
        verbose_name = "Dépense"
        verbose_name_plural = "Dépenses"
        ordering = ['-date_depense']


class BudgetPrevisionnel(models.Model):
    categorie = models.ForeignKey(CategorieDepense, on_delete=models.CASCADE)
    annee_scolaire = models.CharField(max_length=20, verbose_name="Année scolaire")
    montant_prevu = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Montant prévu (FC)")
    
    class Meta:
        unique_together = ['categorie', 'annee_scolaire']
        verbose_name = "Budget prévisionnel"
        verbose_name_plural = "Budgets prévisionnels"