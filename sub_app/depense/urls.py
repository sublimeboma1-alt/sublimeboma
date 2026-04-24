from django.urls import path
from . import views

app_name = 'depense'

urlpatterns = [
    path('', views.dashboard_depenses, name='dashboard'),
    path('ajouter/', views.ajouter_depense, name='ajouter_depense'),
    path('liste/', views.liste_depenses, name='liste_depenses'),
    path('modifier/<int:pk>/', views.modifier_depense, name='modifier_depense'),
    path('supprimer/<int:pk>/', views.supprimer_depense, name='supprimer_depense'),
    path('categories/', views.categories_depenses, name='categories'),
]