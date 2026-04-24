from django.urls import path
from . import views

app_name = 'noyau'

urlpatterns = [
    path('', views.tableau_de_bord, name='tableau_de_bord'),
    path('admin-redirect/', views.go_to_admin, name='go_to_admin'),

]