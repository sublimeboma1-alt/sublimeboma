from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import CategorieDepense, Depense, BudgetPrevisionnel

@admin.register(CategorieDepense)
class CategorieDepenseAdmin(admin.ModelAdmin):
    list_display = ['nom', 'description']
    search_fields = ['nom']

@admin.register(Depense)
class DepenseAdmin(admin.ModelAdmin):
    list_display = ['code', 'titre', 'categorie', 'montant', 'date_depense', 'beneficiaire', 'mode_paiement']
    list_filter = ['categorie', 'mode_paiement', 'date_depense']
    search_fields = ['code', 'titre', 'beneficiaire']
    readonly_fields = ['code', 'date_enregistrement']

@admin.register(BudgetPrevisionnel)
class BudgetPrevisionnelAdmin(admin.ModelAdmin):
    list_display = ['categorie', 'annee_scolaire', 'montant_prevu']