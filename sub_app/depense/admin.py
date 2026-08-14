from django.contrib import admin

from .models import CategorieDepense


@admin.register(CategorieDepense)
class CategorieDepenseAdmin(admin.ModelAdmin):
    list_display = ['nom', 'description']
    search_fields = ['nom']
