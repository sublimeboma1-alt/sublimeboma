from django.urls import path
from . import views
urlpatterns = [path('api/jeton/ouvrir/', views.ouvrir), path('api/jeton/fermer/', views.fermer), path('api/declarations/', views.declarations), path('api/declarations/<int:item_id>/validation/', views.valider)]
