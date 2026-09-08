"""
URL configuration for sublime project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path

from sublime import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('comptes/', include('sub_app.comptes.urls')),
    path('', include('sub_app.noyau.urls')),
    path('eleves/', include('sub_app.eleves.urls')),
    path('frais_scolaires/', include('sub_app.frais_scolaires.urls')),
    path('depense/', include('sub_app.depense.urls')),  
    path('repartition/', include('sub_app.repartition.urls')),
]
# Servir les fichiers téléversés depuis le dossier local media/.
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


# Personnalisation de l'admin site
admin.site.site_header = "Complexe Scolaire Sublime - Administration"
admin.site.site_title = "Complexe Scolaire Sublime"
admin.site.index_title = "Bienvenue dans l'administration du Complexe Scolaire Sublime"
