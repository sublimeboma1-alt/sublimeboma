from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Eleve, Classe
from sub_app.eleves.forms import ClasseSelectionForm, EleveForm
from sub_app.noyau.decorators import superuser_silent_action, superuser_context

@login_required
def creer_eleve(request):
    if request.method == 'POST':
        # Récupérer les données du formulaire de sélection de classe
        niveau = request.POST.get('niveau')
        classe_maternel = request.POST.get('classe_maternel')
        classe_primaire = request.POST.get('classe_primaire')
        classe_humanite = request.POST.get('classe_humanite')
        section = request.POST.get('section')
        
        # Créer ou récupérer la classe
        classe_obj = None
        if niveau:
            # Construire le dictionnaire des filtres
            filters = {'niveau': niveau}
            
            if niveau == 'maternel' and classe_maternel:
                filters['classe_maternel'] = classe_maternel
                filters['classe_primaire'] = None
                filters['classe_humanite'] = None
                filters['section'] = None
            elif niveau == 'primaire' and classe_primaire:
                filters['classe_primaire'] = classe_primaire
                filters['classe_maternel'] = None
                filters['classe_humanite'] = None
                filters['section'] = None
            elif niveau == 'humanite' and classe_humanite:
                filters['classe_humanite'] = classe_humanite
                filters['section'] = section if section else None
                filters['classe_maternel'] = None
                filters['classe_primaire'] = None
            
            # Chercher la classe existante
            classe_obj = Classe.objects.filter(**filters).first()
            
            # Créer si elle n'existe pas
            if not classe_obj and any([classe_maternel, classe_primaire, classe_humanite]):
                classe_obj = Classe.objects.create(**filters)
        
        # Traiter le formulaire Eleve
        form = EleveForm(request.POST, request.FILES)
        
        if form.is_valid():
            eleve = form.save(commit=False)
            eleve.created_by = request.user
            eleve.classe = classe_obj  # Assigner la classe
            eleve.save()
            messages.success(request, f'Élève créé avec succès ! Matricule: {eleve.matricule}')
            return redirect('eleves:detail_eleve', pk=eleve.pk)
        else:
            # Afficher les erreurs du formulaire
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'Erreur dans {field}: {error}')
    else:
        form = EleveForm()
    
    form_classe = ClasseSelectionForm()
    classes = Classe.objects.all()
    
    return render(request, 'eleves/creer_eleve.html', {
        'form': form, 
        'form_classe': form_classe,
        'classes': classes
    })







@login_required
def get_or_create_classe(request):
    """Vue pour créer ou récupérer une classe avec section"""
    if request.method == 'POST':
        niveau = request.POST.get('niveau')
        classe_value = request.POST.get('classe_value')
        section = request.POST.get('section', None)
        
        # Pour la maternelle
        if niveau == 'maternel':
            classe, created = Classe.objects.get_or_create(
                niveau=niveau,
                classe_maternel=classe_value,
                defaults={
                    'classe_primaire': None,
                    'classe_humanite': None,
                    'section': None
                }
            )
        # Pour le primaire
        elif niveau == 'primaire':
            classe, created = Classe.objects.get_or_create(
                niveau=niveau,
                classe_primaire=classe_value,
                defaults={
                    'classe_maternel': None,
                    'classe_humanite': None,
                    'section': None
                }
            )
        # Pour l'humanité
        elif niveau == 'humanite':
            # Pour l'humanité, la section est obligatoire
            if section:
                classe, created = Classe.objects.get_or_create(
                    niveau=niveau,
                    classe_humanite=classe_value,
                    section=section,
                    defaults={
                        'classe_maternel': None,
                        'classe_primaire': None,
                    }
                )
            else:
                return JsonResponse({'error': 'La section est requise pour l\'humanité'}, status=400)
        else:
            return JsonResponse({'error': 'Niveau invalide'}, status=400)
        
        return JsonResponse({'classe_id': classe.id, 'created': created})
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from .models import Eleve, Classe
from .forms import EleveForm
import datetime

@login_required
def liste_eleves(request):
    eleves = Eleve.objects.all()
    classes = Classe.objects.all()
    
    # Récupérer les paramètres de filtre
    search_query = request.GET.get('search', '')
    classe_id = request.GET.get('classe', '')
    statut = request.GET.get('statut', '')
    niveau = request.GET.get('niveau', '')
    annee = request.GET.get('annee', '')
    masp = request.GET.get('masp', '')
    
    # Appliquer les filtres
    if search_query:
        eleves = eleves.filter(
            Q(nom__icontains=search_query) |
            Q(post_nom__icontains=search_query) |
            Q(prenom__icontains=search_query) |
            Q(matricule__icontains=search_query)
        )
    
    if classe_id:
        eleves = eleves.filter(classe_id=classe_id)
    
    if statut:
        eleves = eleves.filter(statut=statut)
    
    if niveau:
        eleves = eleves.filter(classe__niveau=niveau)
    
    if annee:
        try:
            annee_int = int(annee)
            eleves = eleves.filter(date_inscription__year=annee_int)
        except ValueError:
            pass
    
    if masp:
        if masp == 'oui':
            eleves = eleves.filter(est_masp=True)
        elif masp == 'non':
            eleves = eleves.filter(est_masp=False)
    
    # Récupérer les années d'inscription disponibles pour le filtre
    annees_disponibles = Eleve.objects.dates('date_inscription', 'year', order='DESC')
    
    context = {
        'eleves': eleves,
        'classes': classes,
        'search_query': search_query,
        'classe_selected': classe_id,
        'statut_selected': statut,
        'niveau_selected': niveau,
        'annee_selected': annee,
        'masp_selected': masp,
        'annees_disponibles': annees_disponibles,
        'total_eleves': eleves.count(),
    }
    
    return render(request, 'eleves/liste_eleves.html', context)

@login_required
def detail_eleve(request, pk):
    eleve = get_object_or_404(Eleve, pk=pk)
    return render(request, 'eleves/detail_eleve.html', {'eleve': eleve})


@login_required
@superuser_silent_action
def modifier_eleve(request, pk):
    eleve = get_object_or_404(Eleve, pk=pk)

    if request.method == "POST":
        eleve.nom = request.POST.get("nom")
        eleve.post_nom = request.POST.get("post_nom")
        eleve.prenom = request.POST.get("prenom")
        date_naissance = request.POST.get("date_naissance")
        if date_naissance and date_naissance.strip():
            eleve.date_naissance = date_naissance
        else:
            eleve.date_naissance = None
        eleve.sexe = request.POST.get("sexe")
        eleve.adresse = request.POST.get("adresse")
        eleve.telephone = request.POST.get("telephone")
        eleve.email = request.POST.get("email")
        eleve.est_masp = True if request.POST.get("est_masp") == "on" else False
        eleve.statut = request.POST.get("statut")
        eleve.classe_id = request.POST.get("classe")

        if request.FILES.get("photo"):
            eleve.photo = request.FILES.get("photo")

        eleve.save()

        messages.success(request, "Élève modifié avec succès !")
        return redirect("eleves:detail_eleve", pk=eleve.pk)

    classes = Classe.objects.all()

    return render(request, "eleves/modifier_eleve.html", {
        "eleve": eleve,
        "classes": classes
    })

@login_required
@superuser_silent_action
def supprimer_eleve(request, pk):
    eleve = get_object_or_404(Eleve, pk=pk)
    if request.method == 'POST':
        eleve.delete()
        messages.success(request, 'Élève supprimé avec succès !')
        return redirect('eleves:liste_eleves')
    
    return render(request, 'eleves/supprimer_eleve.html', {'eleve': eleve})