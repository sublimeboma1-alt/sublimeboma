from django.http import HttpResponseForbidden
from django.shortcuts import redirect, render

# Create your views here.

def tableau_de_bord(request):
    #return render(request, 'noyau/base.html')
    return redirect('/eleves/liste')


def go_to_admin(request):
    if request.user.is_authenticated and request.user.is_superuser:
        return redirect('/admin/')
    return HttpResponseForbidden("Accès refusé")


# views.py
