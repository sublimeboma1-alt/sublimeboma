from django import forms
from .models import AnneeScolaire, TarifFrais, FraisScolaire, Paiement
from sub_app.eleves.models import Eleve, Classe

class AnneeScolaireForm(forms.ModelForm):
    class Meta:
        model = AnneeScolaire
        fields = ['annee', 'date_debut', 'date_fin', 'est_active']
        widgets = {
            'date_debut': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'date_fin': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'annee': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '2025-2026'}),
            'est_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class TarifFraisForm(forms.ModelForm):
    class Meta:
        model = TarifFrais
        fields = ['niveau', 'classe_maternel', 'classe_primaire', 'classe_humanite', 'option_humanite', 'trimestre', 'type_frais', 'montant']
        widgets = {
            'niveau': forms.Select(attrs={'class': 'form-control'}),
            'classe_maternel': forms.Select(attrs={'class': 'form-control'}),
            'classe_primaire': forms.Select(attrs={'class': 'form-control'}),
            'classe_humanite': forms.Select(attrs={'class': 'form-control'}),
            'option_humanite': forms.Select(attrs={'class': 'form-control'}),
            'trimestre': forms.Select(attrs={'class': 'form-control'}),
            'type_frais': forms.Select(attrs={'class': 'form-control'}),
            'montant': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }


class PaiementForm(forms.ModelForm):
    trimestre = forms.ChoiceField(
        choices=[(1, '1er Trimestre'), (2, '2ème Trimestre'), (3, '3ème Trimestre')],
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=True,
        label="Trimestre"
    )
    type_frais = forms.ChoiceField(
        choices=FraisScolaire.TYPES_FRAIS,
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=True,
        label="Type de frais"
    )
    
    class Meta:
        model = Paiement
        fields = ['montant_paye', 'mode_paiement', 'description']
        widgets = {
            'montant_paye': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'mode_paiement': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

class FiltreEleveFraisForm(forms.Form):
    STATUT_CHOICES = [
        ('', 'Tous'),
        ('non_paye', 'Non payé'),
        ('partiel', 'Partiellement payé'),
        ('paye', 'Payé'),
    ]
    
    TRIMESTRE_CHOICES = [('', 'Tous'), (1, '1er Trimestre'), (2, '2ème Trimestre'), (3, '3ème Trimestre')]
    
    niveau = forms.ChoiceField(choices=[('', 'Tous'), ('primaire', 'Primaire'), ('humanite', 'Humanité')], required=False, label="Niveau")
    classe = forms.ModelChoiceField(queryset=None, required=False, label="Classe")
    option = forms.ChoiceField(choices=[('', 'Toutes')], required=False, label="Option (Humanité)")
    trimestre = forms.ChoiceField(choices=TRIMESTRE_CHOICES, required=False, label="Trimestre")
    statut = forms.ChoiceField(choices=STATUT_CHOICES, required=False, label="Statut")
    recherche = forms.CharField(required=False, label="Recherche", widget=forms.TextInput(attrs={'placeholder': 'Nom, matricule...'}))
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from sub_app.eleves.models import Classe
        self.fields['classe'].queryset = Classe.objects.all()
        self.fields['option'].choices = [('', 'Toutes')] + list(Classe.SECTION_HUMANITE_CHOICES)




class FraisScolaireForm(forms.ModelForm):
    class Meta:
        model = FraisScolaire
        fields = ['eleve', 'trimestre', 'type_frais', 'montant_total', 'description']
        widgets = {
            'eleve': forms.Select(attrs={'class': 'form-control'}),
            'trimestre': forms.Select(attrs={'class': 'form-control'}),
            'type_frais': forms.Select(attrs={'class': 'form-control'}),
            'montant_total': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }