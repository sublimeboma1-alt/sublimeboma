from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator, EmailValidator
from django.utils import timezone
import datetime

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
        ('generale', 'Générale'),  # Optionnel
    ]
    
    niveau = models.CharField(max_length=20, choices=NIVEAU_CHOICES)
    classe_maternel = models.CharField(max_length=20, choices=CLASSE_MATERNEL_CHOICES, blank=True, null=True)
    classe_primaire = models.CharField(max_length=20, choices=CLASSE_PRIMAIRE_CHOICES, blank=True, null=True)
    classe_humanite = models.CharField(max_length=30, choices=CLASSE_HUMANITE_CHOICES, blank=True, null=True)
    section = models.CharField(max_length=50, choices=SECTION_HUMANITE_CHOICES, blank=True, null=True, verbose_name="Section (Humanité)")
    
    def __str__(self):
        if self.niveau == 'maternel' and self.classe_maternel:
            dict_maternel = dict(self.CLASSE_MATERNEL_CHOICES)
            return dict_maternel.get(self.classe_maternel, self.classe_maternel)
        elif self.niveau == 'primaire' and self.classe_primaire:
            dict_primaire = dict(self.CLASSE_PRIMAIRE_CHOICES)
            return dict_primaire.get(self.classe_primaire, self.classe_primaire)
        elif self.niveau == 'humanite' and self.classe_humanite:
            dict_humanite = dict(self.CLASSE_HUMANITE_CHOICES)
            classe_nom = dict_humanite.get(self.classe_humanite, self.classe_humanite)
            if self.section:
                dict_section = dict(self.SECTION_HUMANITE_CHOICES)
                section_nom = dict_section.get(self.section, self.section)
                return f"{classe_nom} - {section_nom}"
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
    date_naissance = models.DateField(null=True, blank=True, verbose_name="Date de naissance")
    sexe = models.CharField(max_length=1, choices=SEXE_CHOICES, verbose_name="Sexe")
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
    date_inscription = models.DateField(default=timezone.now, verbose_name="Date d'inscription")
    photo = models.ImageField(upload_to='eleves/photos/', blank=True, null=True, verbose_name="Photo")
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='actif', verbose_name="Statut")
    
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
        super().save(*args, **kwargs)
    
    def __str__(self):
        masp_status = " (MASP)" if self.est_masp else ""
        return f"{self.matricule} - {self.nom} {self.post_nom} {self.prenom}{masp_status}"
    
    class Meta:
        verbose_name = "Élève"
        verbose_name_plural = "Élèves"
        ordering = ['nom', 'post_nom', 'prenom']