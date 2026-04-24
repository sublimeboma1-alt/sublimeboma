from django import forms
from .models import Depense, CategorieDepense

class DepenseForm(forms.ModelForm):
    class Meta:
        model = Depense
        fields = ['titre', 'categorie', 'montant', 'date_depense', 'beneficiaire', 'mode_paiement', 'justificatif', 'description']
        widgets = {
            'titre': forms.TextInput(attrs={'class': 'form-control'}),
            'categorie': forms.Select(attrs={'class': 'form-control'}),
            'montant': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'date_depense': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'beneficiaire': forms.TextInput(attrs={'class': 'form-control'}),
            'mode_paiement': forms.Select(attrs={'class': 'form-control'}),
            'justificatif': forms.FileInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class FiltreDepenseForm(forms.Form):
    categorie = forms.ModelChoiceField(queryset=CategorieDepense.objects.all(), required=False, label="Catégorie")
    date_debut = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))
    date_fin = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))