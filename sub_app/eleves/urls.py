from django.urls import path
from . import views

app_name = 'eleves'  # Important : doit correspondre à ce que vous utilisez dans les templates

urlpatterns = [
    path('creer/', views.creer_eleve, name='creer_eleve'),
    path('liste/', views.liste_eleves, name='liste_eleves'),
    path('detail/<int:pk>/', views.detail_eleve, name='detail_eleve'),
    path('modifier/<int:pk>/', views.modifier_eleve, name='modifier_eleve'),
    path('supprimer/<int:pk>/', views.supprimer_eleve, name='supprimer_eleve'),
    path('api/get-or-create-classe/', views.get_or_create_classe, name='get_or_create_classe'),
]