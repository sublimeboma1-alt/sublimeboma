from django import forms
from .models import Eleve, Classe

class ClasseSelectionForm(forms.Form):
    niveau = forms.ChoiceField(
        choices=[('', 'Sélectionnez le niveau'), ('maternel', 'Maternel'), ('primaire', 'Primaire'), ('humanite', 'Humanité')],
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_niveau'})
    )
    classe_maternel = forms.ChoiceField(
        choices=[('', 'Sélectionnez la classe')] + Classe.CLASSE_MATERNEL_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_classe_maternel'})
    )
    classe_primaire = forms.ChoiceField(
        choices=[('', 'Sélectionnez la classe')] + Classe.CLASSE_PRIMAIRE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_classe_primaire'})
    )
    classe_humanite = forms.ChoiceField(
        choices=[('', 'Sélectionnez la classe')] + Classe.CLASSE_HUMANITE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_classe_humanite'})
    )
    section = forms.ChoiceField(
        choices=[('', 'Sélectionnez la section')] + Classe.SECTION_HUMANITE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_section'})
    )

class EleveForm(forms.ModelForm):
    class Meta:
        model = Eleve
        fields = [
            'nom', 'post_nom', 'prenom', 'date_naissance', 'sexe',
            'adresse', 'telephone', 'email', 'est_masp', 'date_inscription',
            'photo', 'statut'
        ]  # Retiré 'classe' des fields
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'post_nom': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'prenom': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'date_naissance': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'sexe': forms.Select(attrs={'class': 'form-control', 'required': True}),
            'adresse': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'telephone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'est_masp': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'date_inscription': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'photo': forms.FileInput(attrs={'class': 'form-control'}),
            'statut': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'nom': 'Nom *',
            'post_nom': 'Post-nom *',
            'prenom': 'Prénom *',
            'sexe': 'Sexe *',
            'est_masp': 'Membre de la Mutualité MASP',
        }