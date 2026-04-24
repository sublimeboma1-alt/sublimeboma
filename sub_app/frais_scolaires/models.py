from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from sub_app.eleves.models import Eleve, Classe

class AnneeScolaire(models.Model):
    annee = models.CharField(max_length=20, unique=True, verbose_name="Année scolaire")
    date_debut = models.DateField()
    date_fin = models.DateField()
    est_active = models.BooleanField(default=False)
    
    def __str__(self):
        return self.annee
    
    class Meta:
        verbose_name = "Année scolaire"
        verbose_name_plural = "Années scolaires"
        ordering = ['-date_debut']


class TarifFrais(models.Model):
    """Modèle pour définir les tarifs par niveau, classe et option"""
    TYPES_FRAIS = [
        ('inscription', 'Frais d\'inscription'),
        ('minerval', 'Minerval'),
        ('uniforme', 'Uniforme'),
        ('examen', 'Frais d\'examen'),
        ('bibliotheque', 'Bibliothèque'),
        ('activite', 'Activité parascolaire'),
        ('cantine', 'Cantine'),
        ('transport', 'Transport'),
        ('autre', 'Autre'),
    ]
    
    NIVEAU_CHOICES = [
        ('maternel', 'Maternel'),
        ('primaire', 'Primaire'),
        ('humanite', 'Humanité'),
    ]
    
    TRIMESTRE_CHOICES = [
        (1, '1er Trimestre'),
        (2, '2ème Trimestre'),
        (3, '3ème Trimestre'),
    ]
    
    CLASSE_MATERNEL_CHOICES = [
        ('1ere_maternelle', '1ère maternelle'),
        ('2eme_maternelle', '2ème maternelle'),
        ('3eme_maternelle', '3ème maternelle'),
    ]
    
    # Pour maternel
    classe_maternel = models.CharField(max_length=20, choices=CLASSE_MATERNEL_CHOICES, blank=True, null=True, verbose_name="Classe maternelle")
    
    # Pour primaire
    classe_primaire = models.CharField(max_length=20, blank=True, null=True, verbose_name="Classe primaire")
    
    # Pour humanité
    classe_humanite = models.CharField(max_length=30, blank=True, null=True, verbose_name="Classe humanité")
    option_humanite = models.CharField(max_length=50, blank=True, null=True, verbose_name="Option (section)")
    
    niveau = models.CharField(max_length=20, choices=NIVEAU_CHOICES, verbose_name="Niveau")
    trimestre = models.IntegerField(choices=TRIMESTRE_CHOICES, verbose_name="Trimestre")
    type_frais = models.CharField(max_length=50, choices=TYPES_FRAIS, verbose_name="Type de frais")
    montant = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Montant")
    annee_scolaire = models.ForeignKey(AnneeScolaire, on_delete=models.CASCADE, related_name='tarifs', verbose_name="Année scolaire")
    
    class Meta:
        verbose_name = "Tarif"
        verbose_name_plural = "Tarifs"
        unique_together = ['niveau', 'classe_maternel', 'classe_primaire', 'classe_humanite', 'option_humanite', 'trimestre', 'type_frais', 'annee_scolaire']
    
    def __str__(self):
        if self.niveau == 'maternel' and self.classe_maternel:
            dict_maternel = dict(self.CLASSE_MATERNEL_CHOICES)
            classe_nom = dict_maternel.get(self.classe_maternel, self.classe_maternel)
            return f"{classe_nom} - {self.get_trimestre_display()} - {self.get_type_frais_display()}: {self.montant} FC"
        elif self.niveau == 'primaire' and self.classe_primaire:
            return f"{self.get_niveau_display()} - {self.classe_primaire} - {self.get_trimestre_display()} - {self.get_type_frais_display()}: {self.montant} FC"
        elif self.niveau == 'humanite' and self.classe_humanite:
            return f"{self.get_niveau_display()} - {self.classe_humanite} ({self.option_humanite}) - {self.get_trimestre_display()} - {self.get_type_frais_display()}: {self.montant} FC"
        return f"{self.get_niveau_display()} - {self.get_trimestre_display()} - {self.get_type_frais_display()}: {self.montant} FC"



class FraisScolaire(models.Model):
    """Frais assignés à un élève spécifique"""
    TYPES_FRAIS = [
        ('inscription', 'Frais d\'inscription'),
        ('minerval', 'Minerval'),
        ('uniforme', 'Uniforme'),
        ('examen', 'Frais d\'examen'),
        ('bibliotheque', 'Bibliothèque'),
        ('activite', 'Activité parascolaire'),
        ('cantine', 'Cantine'),
        ('transport', 'Transport'),
        ('autre', 'Autre'),
    ]
    
    TRIMESTRE_CHOICES = [
        (1, '1er Trimestre'),
        (2, '2ème Trimestre'),
        (3, '3ème Trimestre'),
    ]
    
    eleve = models.ForeignKey(Eleve, on_delete=models.CASCADE, related_name='frais_inscription', verbose_name="Élève")
    annee_scolaire = models.ForeignKey(AnneeScolaire, on_delete=models.CASCADE, related_name='frais', verbose_name="Année scolaire")
    trimestre = models.IntegerField(choices=TRIMESTRE_CHOICES, verbose_name="Trimestre")
    type_frais = models.CharField(max_length=50, choices=TYPES_FRAIS, verbose_name="Type de frais")
    montant_total = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Montant total à payer")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    @property
    def total_paye(self):
        """Calculer le total payé pour ce frais"""
        return self.paiements.filter(statut='valide').aggregate(total=models.Sum('montant_paye'))['total'] or 0
    
    @property
    def solde_restant(self):
        """Calculer le solde restant"""
        return self.montant_total - self.total_paye
    
    @property
    def statut_paiement(self):
        """Déterminer le statut du paiement"""
        if self.total_paye == 0:
            return 'non_paye'
        elif self.total_paye >= self.montant_total:
            return 'paye'
        else:
            return 'partiel'
    
    def __str__(self):
        return f"{self.eleve.nom} {self.eleve.prenom} - {self.get_trimestre_display()} - {self.get_type_frais_display()}"
    
    class Meta:
        verbose_name = "Frais scolaire"
        verbose_name_plural = "Frais scolaires"
        unique_together = ['eleve', 'annee_scolaire', 'trimestre', 'type_frais']

class Paiement(models.Model):
    MODE_PAIEMENT = [
        ('cash', 'Espèces'),
        ('mobile_money', 'Mobile Money'),
        ('banque', 'Virement bancaire'),
        ('cheque', 'Chèque'),
        ('carte', 'Carte bancaire'),
    ]
    
    STATUT_PAIEMENT = [
        ('valide', 'Validé'),
        ('annule', 'Annulé'),
        ('en_attente', 'En attente'),
    ]
    
    frais = models.ForeignKey(FraisScolaire, on_delete=models.CASCADE, related_name='paiements', verbose_name="Frais concerné")
    eleve = models.ForeignKey(Eleve, on_delete=models.CASCADE, related_name='paiements', verbose_name="Élève")
    montant_paye = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Montant payé")
    date_paiement = models.DateField(default=timezone.now, verbose_name="Date de paiement")
    mode_paiement = models.CharField(max_length=50, choices=MODE_PAIEMENT, verbose_name="Mode de paiement")
    reference = models.CharField(max_length=100, unique=True, editable=False, verbose_name="Numéro de reçu")
    statut = models.CharField(max_length=20, choices=STATUT_PAIEMENT, default='valide', verbose_name="Statut")
    description = models.TextField(blank=True, null=True, verbose_name="Observations")
    agent = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='paiements_enregistres', verbose_name="Agent")
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = self.generer_reference()
        super().save(*args, **kwargs)
    
    def generer_reference(self):
        """Générer un numéro de reçu unique"""
        import datetime
        annee = datetime.datetime.now().strftime('%Y')
        dernier_paiement = Paiement.objects.filter(reference__startswith=f'REC-{annee}').order_by('-reference').first()
        
        if dernier_paiement:
            try:
                dernier_num = int(dernier_paiement.reference.split('-')[-1])
                nouveau_num = dernier_num + 1
            except:
                nouveau_num = 1
        else:
            nouveau_num = 1
        
        return f"REC-{annee}-{nouveau_num:06d}"
    
    def __str__(self):
        return f"{self.reference} - {self.eleve.nom} {self.eleve.prenom} - {self.montant_paye} FC"
    
    class Meta:
        verbose_name = "Paiement"
        verbose_name_plural = "Paiements"
        ordering = ['-date_paiement']