from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal
import uuid
from sub_app.eleves.models import Eleve, Classe, NiveauClasse, ClasseMaternelle


class TypeFrais(models.Model):
    code = models.CharField(max_length=50, unique=True)
    libelle = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    est_actif = models.BooleanField(default=True)

    def __str__(self):
        return self.libelle

    class Meta:
        verbose_name = "Type de frais"
        verbose_name_plural = "Types de frais"
        ordering = ['libelle']


class ModePaiement(models.Model):
    code = models.CharField(max_length=50, unique=True)
    libelle = models.CharField(max_length=100)
    est_actif = models.BooleanField(default=True)

    def __str__(self):
        return self.libelle

    class Meta:
        verbose_name = "Mode de paiement"
        verbose_name_plural = "Modes de paiement"
        ordering = ['libelle']


class StatutPaiement(models.Model):
    code = models.CharField(max_length=20, unique=True)
    libelle = models.CharField(max_length=100)
    est_actif = models.BooleanField(default=True)

    def __str__(self):
        return self.libelle

    class Meta:
        verbose_name = "Statut de paiement"
        verbose_name_plural = "Statuts de paiement"
        ordering = ['libelle']


class Trimestre(models.Model):
    numero = models.PositiveSmallIntegerField(unique=True)
    libelle = models.CharField(max_length=100)
    est_actif = models.BooleanField(default=True)

    def __str__(self):
        return self.libelle

    class Meta:
        verbose_name = "Trimestre"
        verbose_name_plural = "Trimestres"
        ordering = ['numero']


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
    classe_maternel = models.ForeignKey(ClasseMaternelle, to_field='code', on_delete=models.PROTECT, blank=True, null=True, verbose_name="Classe maternelle")
    
    # Pour primaire
    classe_primaire = models.CharField(max_length=20, blank=True, null=True, verbose_name="Classe primaire")
    
    # Pour humanité
    classe_humanite = models.CharField(max_length=30, blank=True, null=True, verbose_name="Classe humanité")
    option_humanite = models.CharField(max_length=50, blank=True, null=True, verbose_name="Option (section)")
    
    niveau = models.ForeignKey(NiveauClasse, to_field='code', on_delete=models.PROTECT, verbose_name="Niveau")
    trimestre = models.ForeignKey(Trimestre, to_field='numero', on_delete=models.PROTECT, verbose_name="Trimestre")
    type_frais = models.ForeignKey(TypeFrais, to_field='code', on_delete=models.PROTECT, verbose_name="Type de frais")
    montant = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Montant")
    annee_scolaire = models.ForeignKey(AnneeScolaire, on_delete=models.CASCADE, related_name='tarifs', verbose_name="Année scolaire")
    
    class Meta:
        verbose_name = "Tarif"
        verbose_name_plural = "Tarifs"
        unique_together = ['niveau', 'classe_maternel', 'classe_primaire', 'classe_humanite', 'option_humanite', 'trimestre', 'type_frais', 'annee_scolaire']
    
    def __str__(self):
        if self.niveau_id == 'maternel' and self.classe_maternel:
            classe_nom = str(self.classe_maternel)
            return f"{classe_nom} - {self.get_trimestre_display()} - {self.type_frais}: {self.montant} FC"
        elif self.niveau_id == 'primaire' and self.classe_primaire:
            return f"{self.get_niveau_display()} - {self.classe_primaire} - {self.get_trimestre_display()} - {self.type_frais}: {self.montant} FC"
        elif self.niveau_id == 'humanite' and self.classe_humanite:
            return f"{self.get_niveau_display()} - {self.classe_humanite} ({self.option_humanite}) - {self.get_trimestre_display()} - {self.type_frais}: {self.montant} FC"
        return f"{self.get_niveau_display()} - {self.get_trimestre_display()} - {self.type_frais}: {self.montant} FC"

    def get_niveau_display(self):
        return str(self.niveau) if self.niveau else ""

    def get_trimestre_display(self):
        return str(self.trimestre) if self.trimestre else ""



class FraisScolaire(models.Model):
    """Frais assignés à un élève spécifique"""
    TRIMESTRE_CHOICES = [
        (1, '1er Trimestre'),
        (2, '2ème Trimestre'),
        (3, '3ème Trimestre'),
    ]
    
    niveau = models.ForeignKey(NiveauClasse, to_field="code", on_delete=models.SET_NULL, blank=True, null=True, verbose_name="Niveau")
    annee_scolaire = models.ForeignKey(AnneeScolaire, on_delete=models.CASCADE, related_name='frais', verbose_name="Année scolaire")
    trimestre = models.ForeignKey(Trimestre, to_field='numero', on_delete=models.PROTECT, verbose_name="Trimestre")
    type_frais = models.ForeignKey(TypeFrais, to_field='code', on_delete=models.PROTECT, verbose_name="Type de frais")
    montant_total = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Montant total à payer")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    @property
    def total_paye(self):
        """Calculer le total payé pour ce frais"""
        if hasattr(self, '_cached_total_paye'):
            return self._cached_total_paye

        prefetched = getattr(self, '_prefetched_objects_cache', {}).get('paiements')
        if prefetched is not None:
            total = sum(
                (payment.montant_paye for payment in prefetched if payment.statut_id == 'valide'),
                Decimal('0'),
            )
        else:
            total = self.paiements.filter(statut_id='valide').aggregate(total=models.Sum('montant_paye'))['total'] or 0

        self._cached_total_paye = total
        return total
    
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
        return f"{self.get_trimestre_display()} - {self.type_frais} - {self.montant_total} FC"

    def get_trimestre_display(self):
        return str(self.trimestre) if self.trimestre else ""
    
    class Meta:
        verbose_name = "Frais scolaire"
        verbose_name_plural = "Frais scolaires"
        unique_together = ['annee_scolaire', 'trimestre', 'type_frais']


class CodeJeton(models.Model):
    """Code d'accès temporaire pour les fonctionnalités financières.
    
    Permet de créer un jeton lié à des données spécifiques (élève, type de frais,
    classe, année scolaire, trimestre) pour limiter l'accès de l'utilisateur
    aux seules données liées au jeton.
    """
    code = models.CharField(max_length=64, unique=True, editable=False, verbose_name="Code du jeton")
    description = models.CharField(max_length=255, blank=True, null=True, verbose_name="Description")
    
    # Périmètre d'accès (tous optionnels — si vide, accès général)
    niveau = models.ForeignKey(NiveauClasse, to_field="code", on_delete=models.SET_NULL, blank=True, null=True, verbose_name="Niveau")
    classe = models.ForeignKey(Classe, on_delete=models.SET_NULL, blank=True, null=True, verbose_name="Classe")
    type_frais = models.ForeignKey(TypeFrais, to_field='code', on_delete=models.SET_NULL, blank=True, null=True, verbose_name="Type de frais")
    annee_scolaire = models.ForeignKey(AnneeScolaire, on_delete=models.SET_NULL, blank=True, null=True, verbose_name="Année scolaire")
    trimestre = models.ForeignKey(Trimestre, to_field='numero', on_delete=models.SET_NULL, blank=True, null=True, verbose_name="Trimestre")
    
    # État du jeton
    est_actif = models.BooleanField(default=True, verbose_name="Actif")
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    date_expiration = models.DateTimeField(blank=True, null=True, verbose_name="Date d'expiration")
    date_utilisation = models.DateTimeField(blank=True, null=True, verbose_name="Date d'utilisation")
    
    # Traçabilité
    cree_par = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='jetons_crees', verbose_name="Créé par")
    utilise_par = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='jetons_utilises', verbose_name="Utilisé par")
    
    def save(self, *args, **kwargs):
        if not self.code:
            self.code = self.generer_code()
        if not self.annee_scolaire_id:
            self.annee_scolaire = AnneeScolaire.objects.filter(est_active=True).first()
        super().save(*args, **kwargs)
    
    def generer_code(self):
        """Génère un code unique de 16 caractères alphanumériques."""
        while True:
            code = uuid.uuid4().hex[:16].upper()
            if not CodeJeton.objects.filter(code=code).exists():
                return code
    
    def est_valide(self):
        """Vérifie si le jeton est encore valide."""
        from django.utils import timezone
        if not self.est_actif:
            return False
        if self.date_expiration and self.date_expiration < timezone.now():
            return False
        return True
    
    def marquer_utilise(self, user=None):
        """Marque le jeton comme utilisé."""
        from django.utils import timezone
        self.date_utilisation = timezone.now()
        if user:
            self.utilise_par = user
        self.save(update_fields=['date_utilisation', 'utilise_par'])
    
    def __str__(self):
        cible = []
        if self.niveau:
            cible.append(str(self.niveau))
        if self.classe:
            cible.append(str(self.classe))
        if self.type_frais:
            cible.append(str(self.type_frais))
        cible_str = " - ".join(cible) if cible else "Accès général"
        return f"Jeton {self.code[:8]}... ({cible_str})"
    
    class Meta:
        verbose_name = "Code jeton"
        verbose_name_plural = "Codes jeton"
        ordering = ['-date_creation']


class Paiement(models.Model):
    frais = models.ForeignKey(FraisScolaire, on_delete=models.CASCADE, related_name='paiements', verbose_name="Frais concerné")
    niveau = models.ForeignKey(NiveauClasse, to_field="code", on_delete=models.SET_NULL, blank=True, null=True, verbose_name="Niveau")
    montant_paye = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Montant payé")
    date_paiement = models.DateField(default=timezone.now, verbose_name="Date de paiement")
    mode_paiement = models.ForeignKey(ModePaiement, to_field='code', on_delete=models.PROTECT, verbose_name="Mode de paiement")
    reference = models.CharField(max_length=100, unique=True, editable=False, verbose_name="Numéro de reçu")
    statut = models.ForeignKey(StatutPaiement, to_field='code', on_delete=models.PROTECT, default='valide', verbose_name="Statut")
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