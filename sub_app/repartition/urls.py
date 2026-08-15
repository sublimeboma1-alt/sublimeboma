from django.urls import path
from . import views

app_name = 'repartition'

urlpatterns = [
    path('api/dashboard/', views.dashboard, name='dashboard'),
    path('api/parametres/', views.parametres, name='parametres'),
]
