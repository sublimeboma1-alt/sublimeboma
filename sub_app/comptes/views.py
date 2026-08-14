import json

from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST


def user_payload(user):
    return {
        'id': user.id,
        'username': user.username,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'email': user.email,
        'is_staff': user.is_staff,
        'is_superuser': user.is_superuser,
    }


@require_GET
@ensure_csrf_cookie
def session_view(request):
    csrf_token = get_token(request)
    if request.user.is_authenticated:
        return JsonResponse({
            'is_authenticated': True,
            'user': user_payload(request.user),
            'csrf_token': csrf_token,
        })

    return JsonResponse({'is_authenticated': False, 'user': None, 'csrf_token': csrf_token})


@require_POST
@csrf_protect
def login_view(request):
    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'detail': 'Donnees invalides.'}, status=400)

    username = payload.get('username', '').strip()
    password = payload.get('password', '')

    if not username or not password:
        return JsonResponse({'detail': 'Nom utilisateur et mot de passe requis.'}, status=400)

    user = authenticate(request, username=username, password=password)
    if user is None:
        return JsonResponse({'detail': 'Identifiants incorrects.'}, status=400)

    login(request, user)
    return JsonResponse({'is_authenticated': True, 'user': user_payload(user)})


@require_POST
@csrf_protect
def logout_view(request):
    logout(request)
    return JsonResponse({'is_authenticated': False, 'user': None})
