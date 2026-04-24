# decorators.py
from functools import wraps
from django.http import HttpResponse, JsonResponse

def superuser_silent_action(view_func):
    """
    Décorateur pour actions superutilisateur SILENCIEUSES :
    - Superuser : exécute l'action normalement
    - Utilisateur ordinaire : retourne 204 (No Content) - AUCUN message, AUCUNE action
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        
        # Retourner 204 No Content - le navigateur ne fait ABSOLUMENT RIEN
        # Pas de message, pas d'erreur, pas de redirection
        return HttpResponse(status=204)
    
    return wrapper


def superuser_context(request):
    """
    Fonction utilitaire pour ajouter is_superuser au contexte
    """
    return {'is_superuser': request.user.is_superuser}

# from .decorators import superuser_silent_action, superuser_context
#@superuser_silent_action