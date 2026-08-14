from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator, EmailValidator
from django.utils import timezone
import datetime


class ReferenceBase(models.Model):
    code = models.CharField(max_length=50, unique=True)
    libelle = models.CharField(max_length=100)
    est_actif = models.BooleanField(default=True)

    def __str__(self):
        return self.libelle

    class Meta:
        abstract = True
        ordering = ['libelle']


class NiveauClasse(ReferenceBase):
    class Meta(ReferenceBase.Meta):
        verbose_name = "Niveau"
        verbose_name_plural = "Niveaux"


class ClasseMaternelle(ReferenceBase):
    class Meta(ReferenceBase.Meta):
        verbose_name = "Classe maternelle"
        verbose_name_plural = "Classes maternelles"


class ClassePrimaire(ReferenceBase):
    class Meta(ReferenceBase.Meta):
        verbose_name = "Classe primaire"
        verbose_name_plural = "Classes primaires"


class ClasseHumanite(ReferenceBase):
    class Meta(ReferenceBase.Meta):
        verbose_name = "Classe humanite"
        verbose_name_plural = "Classes humanites"


class SectionHumanite(ReferenceBase):
    class Meta(ReferenceBase.Meta):
        verbose_name = "Section humanite"
        verbose_name_plural = "Sections humanites"


class Sexe(ReferenceBase):
    class Meta(ReferenceBase.Meta):
        verbose_name = "Sexe"
        verbose_name_plural = "Sexes"


class StatutEleve(ReferenceBase):
    class Meta(ReferenceBase.Meta):
        verbose_name = "Statut eleve"
        verbose_name_plural = "Statuts eleves"


class Classe(models.Model):
    NIVEAU_CHOICES = [
        ('maternel', 'Maternel'),
        ('primaire', 'Primaire'),
        ('humanite', 'Humanité'),
    ]
    
    CLASSE_MATERNEL_CHOICES = [
        ('1ere_maternelle', '1ère maternelle'),
        ('2eme_maternelle', '2ème maternelle'),
        ('3eme_maternelle', '3ème maternelle'),
    ]
    
    CLASSE_PRIMAIRE_CHOICES = [
        ('1ere', '1ère année'),
        ('2eme', '2ème année'),
        ('3eme', '3ème année'),
        ('4eme', '4ème année'),
        ('5eme', '5ème année'),
        ('6eme', '6ème année'),
    ]

  
    
    CLASSE_HUMANITE_CHOICES = [
        ('7eme', '7ème année'),
        ('8eme', '8ème année'),
        ('1ere_humanite', '1ère humanité'),
        ('2eme_humanite', '2ème humanité'),
        ('3eme_humanite', '3ème humanité'),
        ('4eme_humanite', '4ème humanité'),
    ]
    
    # Options de section pour l'humanité (tous niveaux confondus)
    SECTION_HUMANITE_CHOICES = [
        ('chimie_biologie', 'Chimie Biologie'),
        ('pedagogie', 'Pédagogie'),
        ('electricite', 'Électricité'),
        ('coupe_couture', 'Coupe et Couture'),
        ('latin_philo', 'Latin Philo'),
        ('commerciale', 'Commerciale'),
        ('construction', 'Construction'),
        ('mecanique_auto', 'Mécanique Auto'),
    ]
    
    niveau = models.ForeignKey(NiveauClasse, to_field='code', on_delete=models.PROTECT)
    classe_maternel = models.ForeignKey(ClasseMaternelle, to_field='code', on_delete=models.PROTECT, blank=True, null=True)
    classe_primaire = models.ForeignKey(ClassePrimaire, to_field='code', on_delete=models.PROTECT, blank=True, null=True)
    classe_humanite = models.ForeignKey(ClasseHumanite, to_field='code', on_delete=models.PROTECT, blank=True, null=True)
    section = models.ForeignKey(SectionHumanite, to_field='code', on_delete=models.PROTECT, blank=True, null=True, verbose_name="Section (Humanité)")
    
    def __str__(self):
        niveau_code = getattr(self.niveau, 'code', self.niveau)
        if niveau_code == 'maternel' and self.classe_maternel:
            return str(self.classe_maternel)
        elif niveau_code == 'primaire' and self.classe_primaire:
            return str(self.classe_primaire)
        elif niveau_code == 'humanite' and self.classe_humanite:
            classe_nom = str(self.classe_humanite)
            if self.section:
                return f"{classe_nom} - {self.section}"
            return classe_nom
        return f"{self.niveau}"
    
    class Meta:
        verbose_name = "Classe"
        verbose_name_plural = "Classes"

class Eleve(models.Model):
    SEXE_CHOICES = [
        ('M', 'Masculin'),
        ('F', 'Féminin'),
    ]
    
    STATUT_CHOICES = [
        ('actif', 'Actif'),
        ('inactif', 'Inactif'),
        ('suspendu', 'Suspendu'),
        ('diplome', 'Diplômé'),
    ]
    
    # Informations personnelles
    nom = models.CharField(max_length=100, verbose_name="Nom")
    post_nom = models.CharField(max_length=100, verbose_name="Post-nom")
    prenom = models.CharField(max_length=100, verbose_name="Prénom")
    lieu_de_naissance = models.CharField(max_length=200, blank=True, null=True, verbose_name="Lieu de naissance")
    date_naissance = models.DateField(null=True, blank=True, verbose_name="Date de naissance")
    sexe = models.ForeignKey(Sexe, to_field='code', on_delete=models.PROTECT, verbose_name="Sexe")
    adresse = models.TextField(blank=True, verbose_name="Adresse")
    telephone = models.CharField(
        max_length=20, 
        blank=True,
        validators=[RegexValidator(r'^\+?1?\d{9,15}$', 'Numéro de téléphone invalide')],
        verbose_name="Téléphone"
    )
    email = models.EmailField(
        blank=True,
        validators=[EmailValidator(message='Email invalide')],
        verbose_name="Email"
    )
    
    # Mutualité MASP
    est_masp = models.BooleanField(default=False, verbose_name="Est membre de la Mutualité MASP")
    
    # Informations académiques
    matricule = models.CharField(max_length=20, unique=True, editable=False, verbose_name="Matricule")
    classe = models.ForeignKey(Classe, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Classe")
    annee_scolaire = models.ForeignKey(
        'frais_scolaires.AnneeScolaire',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='eleves',
        verbose_name="Année scolaire",
    )
    date_inscription = models.DateField(default=timezone.now, verbose_name="Date d'inscription")
    photo = models.ImageField(upload_to='eleves/photos/', blank=True, null=True, verbose_name="Photo")
    statut = models.ForeignKey(StatutEleve, to_field='code', on_delete=models.PROTECT, default='actif', verbose_name="Statut")
    
    # Créateur
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='eleves_crees', verbose_name="Créé par")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def generate_matricule(self):
        """Génère le matricule automatiquement: ANNÉE + E + NUMÉRO (ex: 2026E000001)"""
        current_year = datetime.datetime.now().year
        last_eleve = Eleve.objects.filter(matricule__startswith=f"{current_year}E").order_by('-matricule').first()
        
        if last_eleve and last_eleve.matricule:
            try:
                last_number = int(last_eleve.matricule[-6:])
                new_number = last_number + 1
            except:
                new_number = 1
        else:
            new_number = 1
        
        return f"{current_year}E{new_number:06d}"
    
    def save(self, *args, **kwargs):
        if not self.matricule:
            self.matricule = self.generate_matricule()
        if not self.annee_scolaire_id:
            from sub_app.frais_scolaires.models import AnneeScolaire
            self.annee_scolaire = AnneeScolaire.objects.filter(est_active=True).first()
        super().save(*args, **kwargs)

    # Dans sub_app/eleves/models.py, ajoutez cette méthode à la classe Eleve


    # AJOUT: Méthode pour obtenir l'année scolaire de l'élève
    def get_annee_scolaire(self):
        """Retourne l'année scolaire officielle de l'élève."""
        if self.annee_scolaire_id:
            return self.annee_scolaire

        from sub_app.frais_scolaires.models import AnneeScolaire
        return AnneeScolaire.objects.filter(
            date_debut__lte=self.date_inscription,
            date_fin__gte=self.date_inscription
        ).first()
    
    def est_dans_annee_active(self):
        """Vérifie si l'élève est dans l'année scolaire active"""
        from sub_app.frais_scolaires.models import AnneeScolaire
        annee_active = AnneeScolaire.objects.filter(est_active=True).first()
        return bool(annee_active and self.annee_scolaire_id == annee_active.id)

    def get_sexe_display(self):
        return str(self.sexe) if self.sexe else ""

    def get_statut_display(self):
        return str(self.statut) if self.statut else ""
    
    def __str__(self):
        masp_status = " (MASP)" if self.est_masp else ""
        return f"{self.matricule} - {self.nom} {self.post_nom} {self.prenom}{masp_status}"
    
    class Meta:
        verbose_name = "Élève"
        verbose_name_plural = "Élèves"
        ordering = ['nom', 'post_nom', 'prenom']
