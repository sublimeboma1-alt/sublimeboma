from django.shortcuts import render
from sub_app.noyau.decorators import superuser_silent_action, superuser_context

# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
from django.core.paginator import Paginator
from .models import Depense, CategorieDepense, BudgetPrevisionnel
from .forms import DepenseForm, FiltreDepenseForm
from sub_app.frais_scolaires.models import AnneeScolaire
import calendar
from datetime import datetime

@login_required
def dashboard_depenses(request):
    """Tableau de bord des dépenses"""
    annee_active = AnneeScolaire.objects.filter(est_active=True).first()
    today = datetime.now().date()
    
    # Dépenses du jour
    depenses_jour = Depense.objects.filter(date_depense=today)
    total_jour = depenses_jour.aggregate(total=Sum('montant'))['total'] or 0
    
    # Dépenses du mois
    depenses_mois = Depense.objects.filter(date_depense__year=today.year, date_depense__month=today.month)
    total_mois = depenses_mois.aggregate(total=Sum('montant'))['total'] or 0
    
    # Dépenses de l'année
    if annee_active:
        depenses_annee = Depense.objects.filter(date_depense__year=annee_active.date_debut.year)
    else:
        depenses_annee = Depense.objects.filter(date_depense__year=today.year)
    total_annee = depenses_annee.aggregate(total=Sum('montant'))['total'] or 0
    
    # Dernières dépenses
    dernieres_depenses = Depense.objects.all().order_by('-date_depense')[:5]
    
    # Dépenses par catégorie (pour graphique)
    depenses_par_categorie = []
    categories = CategorieDepense.objects.all()
    for cat in categories:
        total = Depense.objects.filter(categorie=cat, date_depense__year=today.year).aggregate(total=Sum('montant'))['total'] or 0
        if total > 0:
            depenses_par_categorie.append({'categorie': cat.nom, 'total': total})
    
    context = {
        'total_jour': total_jour,
        'total_mois': total_mois,
        'total_annee': total_annee,
        'dernieres_depenses': dernieres_depenses,
        'depenses_par_categorie': depenses_par_categorie,
        'annee_active': annee_active,
    }
    return render(request, 'depenses/dashboard.html', context)

@login_required
def ajouter_depense(request):
    """Ajouter une dépense"""
    if request.method == 'POST':
        form = DepenseForm(request.POST, request.FILES)
        if form.is_valid():
            depense = form.save(commit=False)
            depense.enregistre_par = request.user
            depense.save()
            messages.success(request, f"Dépense ajoutée avec succès. Code: {depense.code}")
            return redirect('depense:liste_depenses')
    else:
        form = DepenseForm()
    
    context = {'form': form}
    return render(request, 'depenses/ajouter_depense.html', context)

@login_required
def liste_depenses(request):
    """Liste des dépenses avec filtres"""
    depenses = Depense.objects.all().order_by('-date_depense')
    form = FiltreDepenseForm(request.GET)
    
    if form.is_valid():
        if form.cleaned_data.get('categorie'):
            depenses = depenses.filter(categorie=form.cleaned_data['categorie'])
        if form.cleaned_data.get('date_debut'):
            depenses = depenses.filter(date_depense__gte=form.cleaned_data['date_debut'])
        if form.cleaned_data.get('date_fin'):
            depenses = depenses.filter(date_depense__lte=form.cleaned_data['date_fin'])
    
    paginator = Paginator(depenses, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    total_depenses = depenses.aggregate(total=Sum('montant'))['total'] or 0
    
    context = {
        'page_obj': page_obj,
        'form': form,
        'total_depenses': total_depenses,
    }
    return render(request, 'depenses/liste_depenses.html', context)

@login_required
@superuser_silent_action
def modifier_depense(request, pk):
    """Modifier une dépense"""
    depense = get_object_or_404(Depense, pk=pk)
    
    if request.method == 'POST':
        form = DepenseForm(request.POST, request.FILES, instance=depense)
        if form.is_valid():
            form.save()
            messages.success(request, "Dépense modifiée avec succès")
            return redirect('depense:liste_depenses')
    else:
        form = DepenseForm(instance=depense)
    
    context = {'form': form, 'depense': depense}
    return render(request, 'depenses/modifier_depense.html', context)

@login_required
@superuser_silent_action
def supprimer_depense(request, pk):
    """Supprimer une dépense"""
    depense = get_object_or_404(Depense, pk=pk)
    
    if request.method == 'POST':
        code = depense.code
        depense.delete()
        messages.success(request, f"Dépense {code} supprimée avec succès")
        return redirect('depense:liste_depenses')
    
    context = {'depense': depense}
    return render(request, 'depenses/supprimer_depense.html', context)

@login_required
def categories_depenses(request):
    """Gérer les catégories"""
    categories = CategorieDepense.objects.all()
    
    if request.method == 'POST':
        nom = request.POST.get('nom')
        description = request.POST.get('description')
        if nom:
            CategorieDepense.objects.create(nom=nom, description=description)
            messages.success(request, f"Catégorie {nom} ajoutée")
            return redirect('depense:categories')
    
    context = {'categories': categories}
    return render(request, 'depenses/categories.html', context)