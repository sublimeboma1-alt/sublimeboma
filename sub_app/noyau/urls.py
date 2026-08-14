from django.urls import path

from . import views


app_name = 'noyau'

urlpatterns = [
    path('', views.home, name='home'),
    path('api/identite-etablissement/', views.identite_etablissement, name='identite_etablissement'),
]
