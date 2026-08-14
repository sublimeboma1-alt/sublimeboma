from django.contrib import admin

from .models import IdentiteEtablissement


@admin.register(IdentiteEtablissement)
class IdentiteEtablissementAdmin(admin.ModelAdmin):
    list_display = ['nom', 'espace', 'sigle', 'telephone', 'email', 'est_active']
    list_filter = ['est_active']
    search_fields = ['nom', 'espace', 'sigle', 'telephone', 'email']
    list_editable = ['espace', 'sigle', 'est_active']
