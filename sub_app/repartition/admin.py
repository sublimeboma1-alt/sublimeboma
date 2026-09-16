from django.contrib import admin

from .models import CategorieRepartition, LigneRepartition, ParametreRepartition, RegleRepartition


@admin.register(CategorieRepartition)
class CategorieRepartitionAdmin(admin.ModelAdmin):
    list_display = ('libelle', 'code', 'ordre', 'couleur', 'est_active')
    list_editable = ('ordre', 'couleur', 'est_active')
    search_fields = ('libelle', 'code')


class RegleRepartitionInline(admin.TabularInline):
    model = RegleRepartition
    extra = 0


@admin.register(ParametreRepartition)
class ParametreRepartitionAdmin(admin.ModelAdmin):
    list_display = ('nom', 'type_frais', 'annee_scolaire', 'est_actif', 'date_creation')
    list_filter = ('annee_scolaire', 'type_frais', 'est_actif')
    search_fields = ('nom',)
    inlines = (RegleRepartitionInline,)


@admin.register(LigneRepartition)
class LigneRepartitionAdmin(admin.ModelAdmin):
    list_display = ('paiement', 'categorie', 'pourcentage', 'montant', 'date_creation')
    list_filter = ('categorie',)
    search_fields = ('paiement__reference',)
    readonly_fields = ('date_creation',)
