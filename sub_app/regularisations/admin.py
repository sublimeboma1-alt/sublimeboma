from django.contrib import admin
from .models import JetonRegularisation, Regularisation

@admin.register(JetonRegularisation)
class JetonRegularisationAdmin(admin.ModelAdmin):
    list_display = ('code', 'description', 'actif', 'cree_le')
    list_filter = ('actif',)
    readonly_fields = ('code', 'cree_le')

@admin.register(Regularisation)
class RegularisationAdmin(admin.ModelAdmin):
    list_display = ('eleve', 'annee_scolaire', 'montant', 'date_declaration', 'statut', 'cree_par', 'valide_par')
    list_filter = ('statut', 'annee_scolaire')
    search_fields = ('eleve__nom', 'eleve__prenom', 'eleve__matricule', 'reference')
    readonly_fields = ('cree_par', 'valide_par', 'date_validation', 'date_creation')
    actions = ('valider_reglements', 'refuser_reglements')

    @admin.action(description='Valider les declarations selectionnees')
    def valider_reglements(self, request, queryset):
        queryset.filter(statut='en_attente').update(statut='valide', valide_par=request.user, date_validation=__import__('django.utils.timezone', fromlist=['now']).now())

    @admin.action(description='Refuser les declarations selectionnees')
    def refuser_reglements(self, request, queryset):
        queryset.filter(statut='en_attente').update(statut='refuse', valide_par=request.user, date_validation=__import__('django.utils.timezone', fromlist=['now']).now())
