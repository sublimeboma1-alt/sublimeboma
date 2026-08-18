from django.urls import path

from . import views
from .jeton_views import valider_jeton


app_name = 'frais_scolaires'


urlpatterns = [
    path('api/jetons/valider/', valider_jeton, name='valider_jeton'),
    path('api/references/', views.references, name='references'),
    path('api/exports/', views.export_data, name='export_data'),
    path('api/dashboard/', views.dashboard, name='dashboard'),
    path('api/statistiques/', views.statistiques, name='statistiques'),
    path('api/dossiers/', views.dossiers, name='dossiers'),
    path('api/eleves/<int:eleve_id>/detail/', views.eleve_detail, name='eleve_detail'),
    path('api/paiements/', views.paiements, name='paiements'),
    path('api/annees/', views.annees, name='annees'),
    path('api/tarifs/', views.tarifs, name='tarifs'),
    path('api/appliquer-tarif/', views.appliquer_tarif, name='appliquer_tarif'),
]