import json
from decimal import Decimal, InvalidOperation
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods
from sub_app.eleves.models import Eleve
from sub_app.frais_scolaires.models import AnneeScolaire
from .models import JetonRegularisation, Regularisation

SESSION_KEY = 'regularisations_jeton_id'

def data_json(request):
    try:
        return json.loads(request.body or '{}')
    except (ValueError, TypeError):
        return None

def need_token(request):
    token_id = request.session.get(SESSION_KEY)
    return JetonRegularisation.objects.filter(pk=token_id, actif=True).first() if token_id else None

@login_required
@csrf_protect
@require_http_methods(['POST'])
def ouvrir(request):
    data = data_json(request)
    if data is None:
        return JsonResponse({'detail':'Requete invalide.'}, status=400)
    token = JetonRegularisation.objects.filter(code=(data.get('code') or '').strip().upper(), actif=True).first()
    if not token:
        return JsonResponse({'detail':'Jeton de regularisation invalide ou desactive.'}, status=403)
    request.session[SESSION_KEY] = token.pk
    return JsonResponse({'ok':True, 'description':token.description})

@login_required
@csrf_protect
@require_http_methods(['POST'])
def fermer(request):
    request.session.pop(SESSION_KEY, None)
    return JsonResponse({'ok':True})

@login_required
@require_http_methods(['GET','POST'])
def declarations(request):
    if not need_token(request):
        return JsonResponse({'detail':'Un jeton de regularisation est requis.'}, status=403)
    if request.method == 'GET':
        items = Regularisation.objects.select_related('eleve','annee_scolaire').all()[:300]
        return JsonResponse({'results':[{'id':x.id,'eleve_id':x.eleve_id,'eleve':str(x.eleve),'annee_id':x.annee_scolaire_id,'annee':x.annee_scolaire.annee,'montant':str(x.montant),'date':x.date_declaration.isoformat(),'reference':x.reference,'observations':x.observations,'statut':x.statut} for x in items], 'eleves':[{'id':x.id,'nom':str(x)} for x in Eleve.objects.all().order_by('nom')[:3000]], 'annees':[{'id':x.id,'annee':x.annee,'active':x.est_active} for x in AnneeScolaire.objects.all()]})
    data = data_json(request)
    if data is None:
        return JsonResponse({'detail':'Requete invalide.'}, status=400)
    try:
        amount = Decimal(str(data.get('montant','')))
        if amount <= 0: raise InvalidOperation
        item = Regularisation(eleve_id=int(data['eleve_id']), annee_scolaire_id=int(data['annee_id']), montant=amount, reference=str(data.get('reference',''))[:100], observations=str(data.get('observations',''))[:2000], cree_par=request.user)
        item.full_clean()
        item.save()
    except Exception:
        return JsonResponse({'detail':'Verifiez l eleve, l annee et le montant saisis.'}, status=400)
    return JsonResponse({'id':item.id,'statut':item.statut}, status=201)

@login_required
@csrf_protect
@require_http_methods(['POST'])
def valider(request, item_id):
    if not need_token(request): return JsonResponse({'detail':'Un jeton de regularisation est requis.'}, status=403)
    data = data_json(request)
    if not request.user.is_staff: return JsonResponse({'detail':'Validation reservee aux administrateurs.'}, status=403)
    if data is None: return JsonResponse({'detail':'Requete invalide.'}, status=400)
    item = Regularisation.objects.filter(pk=item_id, statut='en_attente').first()
    if not item: return JsonResponse({'detail':'Declaration introuvable ou deja traitee.'}, status=404)
    decision = data.get('decision')
    if decision not in ('valide','refuse'): return JsonResponse({'detail':'Decision invalide.'}, status=400)
    if decision == 'valide' and item.annee_scolaire.est_active:
        from django.db.models import Sum
        from sub_app.frais_scolaires.models import FraisScolaire, Paiement
        fees = FraisScolaire.objects.filter(eleve=item.eleve, annee_scolaire=item.annee_scolaire)
        expected = fees.aggregate(total=Sum('montant_total'))['total'] or Decimal('0')
        received = Paiement.objects.filter(frais__in=fees, statut_id='valide').aggregate(total=Sum('montant_paye'))['total'] or Decimal('0')
        approved = Regularisation.objects.filter(eleve=item.eleve, annee_scolaire=item.annee_scolaire, statut=Regularisation.VALIDE).aggregate(total=Sum('montant'))['total'] or Decimal('0')
        if item.montant > max(Decimal('0'), expected - received - approved):
            return JsonResponse({'detail':'Le montant depasse le solde restant de l annee active.'}, status=400)
    from django.utils import timezone
    item.statut = decision
    item.valide_par = request.user
    item.date_validation = timezone.now()
    item.save(update_fields=['statut','valide_par','date_validation'])
    return JsonResponse({'ok':True,'statut':item.statut})
