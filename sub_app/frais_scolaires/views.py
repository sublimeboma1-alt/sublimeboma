from django.shortcuts import render
from django import forms
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Q
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator

from sub_app.noyau.decorators import superuser_silent_action, superuser_context


import io
import xlwt
import datetime
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from django.db.models import Sum, Count, Q





import io
import xlwt
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from django.db import models  # <-- AJOUTEZ CETTE LIGNE
from .models import Eleve, AnneeScolaire, FraisScolaire, Paiement, TarifFrais
from .forms import PaiementForm

from sub_app.frais_scolaires import forms
from .models import AnneeScolaire, TarifFrais, FraisScolaire, Paiement
from .forms import AnneeScolaireForm, FraisScolaireForm, TarifFraisForm, PaiementForm, FiltreEleveFraisForm
from sub_app.eleves.models import Eleve, Classe

@login_required
def dashboard_frais(request):
    """Tableau de bord des frais scolaires"""
    annee_active = AnneeScolaire.objects.filter(est_active=True).first()
    
    if not annee_active:
        messages.warning(request, "Veuillez d'abord configurer une année scolaire active")
        return redirect('frais_scolaire:configurer_annee')
    
    total_attendus = FraisScolaire.objects.filter(annee_scolaire=annee_active).aggregate(total=Sum('montant_total'))['total'] or 0
    total_percus = Paiement.objects.filter(frais__annee_scolaire=annee_active, statut='valide').aggregate(total=Sum('montant_paye'))['total'] or 0
    
    # Statistiques par option (humanité)
    stats_par_option = []
    options = dict(Classe.SECTION_HUMANITE_CHOICES)
    for option_key, option_label in options.items():
        eleves_option = Eleve.objects.filter(classe__niveau='humanite', classe__section=option_key)
        total_attendu_option = FraisScolaire.objects.filter(
            annee_scolaire=annee_active,
            eleve__in=eleves_option
        ).aggregate(total=Sum('montant_total'))['total'] or 0
        total_percu_option = Paiement.objects.filter(
            frais__annee_scolaire=annee_active,
            eleve__in=eleves_option,
            statut='valide'
        ).aggregate(total=Sum('montant_paye'))['total'] or 0
        
        if total_attendu_option > 0:
            stats_par_option.append({
                'option': option_label,
                'total_attendu': total_attendu_option,
                'total_percu': total_percu_option,
                'solde': total_attendu_option - total_percu_option,
                'taux': (total_percu_option / total_attendu_option * 100),
            })
    
    context = {
        'annee_active': annee_active,
        'total_attendus': total_attendus,
        'total_percus': total_percus,
        'solde_total': total_attendus - total_percus,
        'taux_recouvrement': (total_percus / total_attendus * 100) if total_attendus > 0 else 0,
        'stats_par_option': stats_par_option,
    }
    return render(request, 'frais_scolaire/dashboard.html', context)

from .forms import TarifFraisForm  # Ajoutez cette ligne en haut



@login_required
@superuser_silent_action
def configurer_tarifs(request):
    """Configuration des tarifs par niveau, classe et option"""
    annee_active = AnneeScolaire.objects.filter(est_active=True).first()
    
    if not annee_active:
        messages.warning(request, "Veuillez d'abord configurer une année scolaire active")
        return redirect('frais_scolaire:configurer_annee')
    
    tarifs = TarifFrais.objects.filter(annee_scolaire=annee_active)
    
    if request.method == 'POST':
        niveau = request.POST.get('niveau')
        trimestre = request.POST.get('trimestre')
        type_frais = request.POST.get('type_frais')
        montant = request.POST.get('montant')
        
        print(f"Niveau reçu: {niveau}")
        
        if niveau == 'maternel':
            classe_maternel = request.POST.get('classe_maternel')
            if not classe_maternel:
                messages.error(request, "Veuillez sélectionner une classe maternelle")
                return redirect('frais_scolaire:configurer_tarifs')
            
            tarif = TarifFrais(
                niveau=niveau,
                classe_maternel=classe_maternel,
                trimestre=trimestre,
                type_frais=type_frais,
                montant=montant,
                annee_scolaire=annee_active
            )
            tarif.save()
            messages.success(request, f"Tarif Maternel ({classe_maternel}) ajouté avec succès")
            
        elif niveau == 'primaire':
            classe_primaire = request.POST.get('classe_primaire')
            if not classe_primaire:
                messages.error(request, "Veuillez sélectionner une classe primaire")
                return redirect('frais_scolaire:configurer_tarifs')
            
            tarif = TarifFrais(
                niveau=niveau,
                classe_primaire=classe_primaire,
                trimestre=trimestre,
                type_frais=type_frais,
                montant=montant,
                annee_scolaire=annee_active
            )
            tarif.save()
            messages.success(request, f"Tarif Primaire ({classe_primaire}) ajouté avec succès")
            
        elif niveau == 'humanite':
            classe_humanite = request.POST.get('classe_humanite')
            option_humanite = request.POST.get('option_humanite')
            
            if not classe_humanite:
                messages.error(request, "Veuillez sélectionner une classe d'humanité")
                return redirect('frais_scolaire:configurer_tarifs')
            
            if not option_humanite:
                messages.error(request, "Veuillez sélectionner une option/section")
                return redirect('frais_scolaire:configurer_tarifs')
            
            tarif = TarifFrais(
                niveau=niveau,
                classe_humanite=classe_humanite,
                option_humanite=option_humanite,
                trimestre=trimestre,
                type_frais=type_frais,
                montant=montant,
                annee_scolaire=annee_active
            )
            tarif.save()
            messages.success(request, f"Tarif Humanité ({classe_humanite} - {option_humanite}) ajouté avec succès")
        else:
            messages.error(request, "Niveau non reconnu")
            return redirect('frais_scolaire:configurer_tarifs')
        
        return redirect('frais_scolaire:configurer_tarifs')
    
    # Créer un formulaire vide pour l'affichage
    form = TarifFraisForm()
    
    context = {
        'form': form,
        'tarifs': tarifs,
        'annee_active': annee_active,
    }
    return render(request, 'frais_scolaire/configurer_tarifs.html', context)


@login_required
@superuser_silent_action
def supprimer_tarif(request, pk):
    """Supprimer un tarif"""
    tarif = get_object_or_404(TarifFrais, pk=pk)
    tarif.delete()
    messages.success(request, "Tarif supprimé avec succès")
    return redirect('frais_scolaire:configurer_tarifs')



@login_required
def appliquer_tarifs_eleves(request):
    """Appliquer les tarifs aux élèves selon leur classe et option"""
    annee_active = AnneeScolaire.objects.filter(est_active=True).first()
    
    if not annee_active:
        messages.warning(request, "Veuillez d'abord configurer une année scolaire active")
        return redirect('frais_scolaire:configurer_annee')
    
    if request.method == 'POST':
        niveau = request.POST.get('niveau')
        classe_value = request.POST.get('classe')
        option = request.POST.get('option')
        trimestre = request.POST.get('trimestre')
        
        print(f"=== APPLICATION DES TARIFS ===")
        print(f"Niveau: {niveau}")
        print(f"Classe value: {classe_value}")
        print(f"Option: {option}")
        print(f"Trimestre: {trimestre}")
        
        # Récupérer tous les élèves
        eleves = Eleve.objects.all()
        
        # Filtrer selon les critères
        if niveau == 'maternel':
            eleves = eleves.filter(classe__niveau='maternel')
            if classe_value:
                eleves = eleves.filter(classe__classe_maternel=classe_value)
                
        elif niveau == 'primaire':
            eleves = eleves.filter(classe__niveau='primaire')
            if classe_value:
                eleves = eleves.filter(classe__classe_primaire=classe_value)
                
        elif niveau == 'humanite':
            eleves = eleves.filter(classe__niveau='humanite')
            if classe_value:
                eleves = eleves.filter(classe__classe_humanite=classe_value)
            if option:
                eleves = eleves.filter(classe__section=option)
        
        print(f"Nombre d'eleves trouves: {eleves.count()}")
        
        if eleves.count() == 0:
            messages.warning(request, "Aucun eleve trouve avec ces criteres. Verifiez que les eleves ont une classe assignee.")
            return redirect('frais_scolaire:appliquer_tarifs')
        
        compteur_total = 0
        compteur_deja_existants = 0
        
        for eleve in eleves:
            print(f"\n--- Eleve: {eleve.nom} {eleve.prenom} ---")
            
            if not eleve.classe:
                print("  Pas de classe assignee")
                continue
            
            print(f"  Niveau: {eleve.classe.niveau}")
            print(f"  Classe maternel: {eleve.classe.classe_maternel}")
            print(f"  Classe primaire: {eleve.classe.classe_primaire}")
            print(f"  Classe humanite: {eleve.classe.classe_humanite}")
            print(f"  Section: {eleve.classe.section}")
            
            # Chercher les tarifs correspondants à CET élève
            if eleve.classe.niveau == 'maternel':
                # Pour maternel: on cherche les tarifs avec le même classe_maternel
                tarifs = TarifFrais.objects.filter(
                    annee_scolaire=annee_active,
                    niveau='maternel',
                    classe_maternel=eleve.classe.classe_maternel
                )
                print(f"  Recherche tarifs maternel avec classe_maternel={eleve.classe.classe_maternel}")
                
            elif eleve.classe.niveau == 'primaire':
                # Pour primaire: on cherche les tarifs avec le même classe_primaire
                tarifs = TarifFrais.objects.filter(
                    annee_scolaire=annee_active,
                    niveau='primaire',
                    classe_primaire=eleve.classe.classe_primaire
                )
                print(f"  Recherche tarifs primaire avec classe_primaire={eleve.classe.classe_primaire}")
                
            else:
                # Pour humanité: on cherche les tarifs avec la même classe_humanite ET option
                tarifs = TarifFrais.objects.filter(
                    annee_scolaire=annee_active,
                    niveau='humanite',
                    classe_humanite=eleve.classe.classe_humanite,
                    option_humanite=eleve.classe.section
                )
                print(f"  Recherche tarifs humanite avec classe={eleve.classe.classe_humanite}, option={eleve.classe.section}")
            
            # Filtrer par trimestre si spécifié
            if trimestre and trimestre != '':
                tarifs = tarifs.filter(trimestre=int(trimestre))
            
            print(f"  Tarifs trouves: {tarifs.count()}")
            
            # Appliquer chaque tarif avec vérification anti-double
            compteur_eleve = 0
            for tarif in tarifs:
                # Vérifier si le frais existe déjà pour cet élève, ce trimestre et ce type
                frais_existant = FraisScolaire.objects.filter(
                    eleve=eleve,
                    annee_scolaire=annee_active,
                    trimestre=tarif.trimestre,
                    type_frais=tarif.type_frais
                ).exists()
                
                if frais_existant:
                    print(f"    [EXISTANT] {tarif.get_type_frais_display()} - Trimestre {tarif.trimestre}")
                    compteur_deja_existants += 1
                    continue
                
                # Créer le frais s'il n'existe pas
                frais, created = FraisScolaire.objects.get_or_create(
                    eleve=eleve,
                    annee_scolaire=annee_active,
                    trimestre=tarif.trimestre,
                    type_frais=tarif.type_frais,
                    defaults={'montant_total': tarif.montant}
                )
                
                if created:
                    compteur_eleve += 1
                    compteur_total += 1
                    print(f"    [CREE] {tarif.get_type_frais_display()} - {tarif.montant} FC (Trimestre {tarif.trimestre})")
            
            print(f"  Total frais crees pour {eleve.nom}: {compteur_eleve}")
        
        # Message de résultat
        if compteur_total > 0:
            messages.success(
                request, 
                f"{compteur_total} frais ont ete crees pour {eleves.count()} eleve(s). "
                f"{compteur_deja_existants} frais existaient deja."
            )
        else:
            messages.warning(
                request, 
                f"Aucun frais cree. {compteur_deja_existants} frais existaient deja. "
                f"Verifiez que vous avez bien configure des tarifs pour: Niveau={niveau}, Classe={classe_value}, Option={option}"
            )
        
        return redirect('frais_scolaire:dashboard_frais')
    
    # GET: Afficher le formulaire
    classes_maternel = [
        ('1ere_maternelle', '1ère maternelle'),
        ('2eme_maternelle', '2ème maternelle'),
        ('3eme_maternelle', '3ème maternelle'),
    ]
    
    classes_primaire = [
        ('1ere', '1ère année'),
        ('2eme', '2ème année'),
        ('3eme', '3ème année'),
        ('4eme', '4ème année'),
        ('5eme', '5ème année'),
        ('6eme', '6ème année'),
    ]
    
    classes_humanite = [
        ('7eme', '7ème année'),
        ('8eme', '8ème année'),
        ('1ere_humanite', '1ère humanité'),
        ('2eme_humanite', '2ème humanité'),
        ('3eme_humanite', '3ème humanité'),
        ('4eme_humanite', '4ème humanité'),
    ]
    
    options = [
        ('chimie_biologie', 'Chimie Biologie'),
        ('pedagogie', 'Pédagogie'),
        ('electricite', 'Électricité'),
        ('coupe_couture', 'Coupe et Couture'),
        ('latin_philo', 'Latin Philo'),
        ('commerciale', 'Commerciale'),
        ('generale', 'Générale'),
    ]
    
    context = {
        'annee_active': annee_active,
        'classes_maternel': classes_maternel,
        'classes_primaire': classes_primaire,
        'classes_humanite': classes_humanite,
        'options': options,
    }
    return render(request, 'frais_scolaire/appliquer_tarifs.html', context)


   
@login_required
def liste_eleves_frais(request):
    """Liste des élèves avec leurs informations de frais"""
    annee_active = AnneeScolaire.objects.filter(est_active=True).first()
    
    if not annee_active:
        return redirect('frais_scolaire:configurer_annee')
    
    eleves = Eleve.objects.all().select_related('classe')
    
    # Filtres
    form = FiltreEleveFraisForm(request.GET)
    niveau = request.GET.get('niveau')
    classe_id = request.GET.get('classe')
    option = request.GET.get('option')
    trimestre = request.GET.get('trimestre')
    statut_filtre = request.GET.get('statut')
    recherche = request.GET.get('recherche')
    
    if niveau:
        eleves = eleves.filter(classe__niveau=niveau)
    
    if classe_id:
        eleves = eleves.filter(classe_id=classe_id)
    
    if option:
        eleves = eleves.filter(classe__section=option)
    
    if recherche:
        eleves = eleves.filter(
            Q(nom__icontains=recherche) |
            Q(post_nom__icontains=recherche) |
            Q(prenom__icontains=recherche) |
            Q(matricule__icontains=recherche)
        )
    
    # Enrichir chaque élève
    eleves_data = []
    for eleve in eleves:
        frais = FraisScolaire.objects.filter(eleve=eleve, annee_scolaire=annee_active)
        if trimestre and trimestre != '':
            frais = frais.filter(trimestre=trimestre)
        
        total_a_payer = frais.aggregate(total=Sum('montant_total'))['total'] or 0
        total_paye = Paiement.objects.filter(eleve=eleve, frais__annee_scolaire=annee_active, statut='valide').aggregate(total=Sum('montant_paye'))['total'] or 0
        solde = total_a_payer - total_paye
        
        if total_a_payer == 0:
            statut_global = 'aucun_frais'
        elif total_paye == 0:
            statut_global = 'non_paye'
        elif total_paye >= total_a_payer:
            statut_global = 'paye'
        else:
            statut_global = 'partiel'
        
        if statut_filtre and statut_filtre != '' and statut_global != statut_filtre:
            continue
        
        eleves_data.append({
            'eleve': eleve,
            'total_a_payer': total_a_payer,
            'total_paye': total_paye,
            'solde': solde,
            'statut': statut_global,
            'option': eleve.classe.get_section_display() if eleve.classe and eleve.classe.section else None,
        })
    
    paginator = Paginator(eleves_data, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'form': form,
        'annee_active': annee_active,
    }
    return render(request, 'frais_scolaire/liste_eleves_frais.html', context)

@login_required
def detail_eleve_frais(request, pk):
    """Détail des frais d'un élève"""
    eleve = get_object_or_404(Eleve, pk=pk)
    annee_active = AnneeScolaire.objects.filter(est_active=True).first()
    
    if not annee_active:
        return redirect('frais_scolaire:configurer_annee')
    
    frais_par_trimestre = []
    for trimestre in [1, 2, 3]:
        frais_liste = FraisScolaire.objects.filter(eleve=eleve, annee_scolaire=annee_active, trimestre=trimestre)
        total_a_payer = frais_liste.aggregate(total=Sum('montant_total'))['total'] or 0
        total_paye = Paiement.objects.filter(eleve=eleve, frais__annee_scolaire=annee_active, frais__trimestre=trimestre, statut='valide').aggregate(total=Sum('montant_paye'))['total'] or 0
        
        frais_par_trimestre.append({
            'trimestre': trimestre,
            'frais_liste': frais_liste,
            'total_a_payer': total_a_payer,
            'total_paye': total_paye,
            'solde': total_a_payer - total_paye,
        })
    
    paiements = Paiement.objects.filter(eleve=eleve, frais__annee_scolaire=annee_active).order_by('-date_paiement')
    
    context = {
        'eleve': eleve,
        'frais_par_trimestre': frais_par_trimestre,
        'paiements': paiements,
        'annee_active': annee_active,
    }
    return render(request, 'frais_scolaire/detail_eleve_frais.html', context)






@login_required
@superuser_silent_action
def enregistrer_paiement(request, eleve_id, frais_id=None):
    """Enregistrer un paiement"""
    eleve = get_object_or_404(Eleve, pk=eleve_id)
    annee_active = AnneeScolaire.objects.filter(est_active=True).first()
    
    if not annee_active:
        messages.warning(request, "Veuillez d'abord configurer une année scolaire active")
        return redirect('frais_scolaire:configurer_annee')
    
    # Récupérer les frais existants pour l'élève
    frais_queryset = FraisScolaire.objects.filter(
        eleve=eleve,
        annee_scolaire=annee_active
    )
    
    # Vérifier si l'élève a des frais appliqués
    if not frais_queryset.exists():
        messages.error(request, f"Impossible d'enregistrer un paiement pour {eleve.nom} {eleve.prenom} car aucun frais n'a été appliqué. Veuillez d'abord appliquer les tarifs à cet élève.")
        return redirect('frais_scolaire:detail_eleve_frais', pk=eleve.id)
    
    # Préparer les frais avec leurs calculs
    frais_existants = []
    total_a_payer = 0
    total_paye_global = 0
    total_restant_global = 0
    
    for frais in frais_queryset:
        # Calculer le total payé pour ce frais
        total_paye_frais = frais.paiements.filter(statut='valide').aggregate(total=models.Sum('montant_paye'))['total'] or 0
        solde_restant = frais.montant_total - total_paye_frais
        
        # Ajouter les propriétés calculées à l'objet frais
        frais.total_paye_calcule = total_paye_frais
        frais.solde_restant_calcule = solde_restant
        
        # Déterminer le statut textuel
        if solde_restant <= 0:
            frais.statut_text = 'paye'
            frais.statut_badge = 'bg-success'
            frais.statut_icone = 'check-circle'
            frais.statut_label = 'Payé'
        elif total_paye_frais > 0:
            frais.statut_text = 'partiel'
            frais.statut_badge = 'bg-warning'
            frais.statut_icone = 'clock'
            frais.statut_label = 'Partiel'
        else:
            frais.statut_text = 'non_paye'
            frais.statut_badge = 'bg-danger'
            frais.statut_icone = 'times-circle'
            frais.statut_label = 'Impayé'
        
        frais_existants.append(frais)
        
        # Calculer les totaux globaux
        total_a_payer += frais.montant_total
        total_paye_global += total_paye_frais
        total_restant_global += solde_restant
    
    if request.method == 'POST':
        trimestre = request.POST.get('trimestre')
        type_frais = request.POST.get('type_frais')
        montant_paye = request.POST.get('montant_paye')
        mode_paiement = request.POST.get('mode_paiement')
        description = request.POST.get('description')
        
        # Validation de base
        if not trimestre or not type_frais or not montant_paye or not mode_paiement:
            messages.error(request, "Tous les champs obligatoires doivent être remplis.")
            return redirect('frais_scolaire:enregistrer_paiement', eleve_id=eleve.id)
        
        # Vérifier si le frais spécifique existe
        frais = FraisScolaire.objects.filter(
            eleve=eleve,
            annee_scolaire=annee_active,
            trimestre=trimestre,
            type_frais=type_frais
        ).first()
        
        if not frais:
            messages.error(request, f"Aucun frais trouvé pour le trimestre {trimestre} et le type {type_frais}.")
            return redirect('frais_scolaire:enregistrer_paiement', eleve_id=eleve.id)
        
        # Calculer le total déjà payé pour ce frais
        total_deja_paye = frais.paiements.filter(statut='valide').aggregate(total=models.Sum('montant_paye'))['total'] or 0
        montant_restant = frais.montant_total - total_deja_paye
        montant_paye = float(montant_paye)
        
        # Vérifier si le montant est valide
        if montant_paye <= 0:
            messages.error(request, "Le montant à payer doit être supérieur à 0.")
            return redirect('frais_scolaire:enregistrer_paiement', eleve_id=eleve.id)
        
        # Vérifier si le montant à payer ne dépasse pas le montant restant
        if montant_paye > montant_restant:
            messages.error(request, f"Le montant saisi ({montant_paye} FC) dépasse le montant restant à payer ({montant_restant} FC) pour {frais.get_type_frais_display()} du trimestre {trimestre}.")
            return redirect('frais_scolaire:enregistrer_paiement', eleve_id=eleve.id)
        
        # Créer le paiement
        paiement = Paiement(
            frais=frais,
            eleve=eleve,
            montant_paye=montant_paye,
            mode_paiement=mode_paiement,
            description=description,
            agent=request.user
        )
        paiement.save()
        
        # Message de succès avec information sur le solde
        nouveau_solde = float(montant_restant - montant_paye)
        if nouveau_solde <= 0:
            messages.success(request, f"Paiement enregistré avec succès. Reçu: {paiement.reference}. Ce frais est maintenant entièrement payé !")
        else:
            messages.success(request, f"Paiement enregistré avec succès. Reçu: {paiement.reference}. Il reste {nouveau_solde} FC à payer.")
        
        return redirect('frais_scolaire:detail_eleve_frais', pk=eleve.id)
    
    context = {
        'eleve': eleve,
        'annee_active': annee_active,
        'frais_existants': frais_existants,
        'total_a_payer': total_a_payer,
        'total_paye_global': total_paye_global,
        'total_restant_global': total_restant_global,
    }
    return render(request, 'frais_scolaire/enregistrer_paiement.html', context)



@login_required
@superuser_silent_action
def configurer_annee(request):
    """Configuration de l'année scolaire"""
    annees = AnneeScolaire.objects.all()
    
    if request.method == 'POST':
        form = AnneeScolaireForm(request.POST)
        if form.is_valid():
            if form.cleaned_data['est_active']:
                AnneeScolaire.objects.filter(est_active=True).update(est_active=False)
            form.save()
            messages.success(request, "Année scolaire configurée avec succès")
            return redirect('frais_scolaire:dashboard_frais')
    else:
        form = AnneeScolaireForm()
    
    context = {
        'form': form,
        'annees': annees,
    }
    return render(request, 'frais_scolaire/configurer_annee.html', context)


@login_required
@superuser_silent_action
def ajouter_frais_manuel(request, eleve_id):
    """Ajouter manuellement des frais pour un élève (sans passer par les tarifs)"""
    eleve = get_object_or_404(Eleve, pk=eleve_id)
    annee_active = AnneeScolaire.objects.filter(est_active=True).first()
    
    if not annee_active:
        messages.warning(request, "Veuillez d'abord configurer une année scolaire active")
        return redirect('frais_scolaire:configurer_annee')
    
    if request.method == 'POST':
        form = FraisScolaireForm(request.POST)
        if form.is_valid():
            frais = form.save(commit=False)
            frais.eleve = eleve
            frais.annee_scolaire = annee_active
            frais.save()
            messages.success(request, f"Frais ajouté avec succès pour {eleve.nom} {eleve.prenom}")
            return redirect('frais_scolaire:detail_eleve_frais', pk=eleve.id)
    else:
        form = FraisScolaireForm(initial={'eleve': eleve})
        form.fields['eleve'].widget = forms.HiddenInput()
    
    context = {
        'eleve': eleve,
        'form': form,
        'annee_active': annee_active,
    }
    return render(request, 'frais_scolaire/ajouter_frais_manuel.html', context)

from django.db.models import Sum, Count, Q
from django.db.models.functions import ExtractYear
import datetime








"""
from django.db.models import Sum, Count, Q
from django.db.models.functions import ExtractYear
import datetime

@login_required
def statistiques_frais(request):
    
    annee_active = AnneeScolaire.objects.filter(est_active=True).first()
    
    if not annee_active:
        messages.warning(request, "Veuillez d'abord configurer une année scolaire active")
        return redirect('frais_scolaire:configurer_annee')
    
    # Récupérer les paramètres de filtres
    niveau_filter = request.GET.get('niveau', '')
    classe_filter = request.GET.get('classe', '')
    trimestre_filter = request.GET.get('trimestre', '')
    annee_filter = request.GET.get('annee', '')
    statut_paiement_filter = request.GET.get('statut_paiement', '')
    type_frais_filter = request.GET.get('type_frais', '')
    
    # Base de requête pour les frais
    frais_base = FraisScolaire.objects.filter(annee_scolaire=annee_active)
    
    # Base pour les paiements
    paiements_base = Paiement.objects.filter(frais__annee_scolaire=annee_active, statut='valide')
    
    # Appliquer les filtres
    if niveau_filter:
        frais_base = frais_base.filter(eleve__classe__niveau=niveau_filter)
        paiements_base = paiements_base.filter(frais__eleve__classe__niveau=niveau_filter)
    
    if classe_filter:
        frais_base = frais_base.filter(
            Q(eleve__classe__classe_maternel=classe_filter) |
            Q(eleve__classe__classe_primaire=classe_filter) |
            Q(eleve__classe__classe_humanite=classe_filter)
        )
        paiements_base = paiements_base.filter(
            Q(frais__eleve__classe__classe_maternel=classe_filter) |
            Q(frais__eleve__classe__classe_primaire=classe_filter) |
            Q(frais__eleve__classe__classe_humanite=classe_filter)
        )
    
    if trimestre_filter and trimestre_filter.isdigit():
        frais_base = frais_base.filter(trimestre=int(trimestre_filter))
        paiements_base = paiements_base.filter(frais__trimestre=int(trimestre_filter))
    
    if type_frais_filter:
        frais_base = frais_base.filter(type_frais=type_frais_filter)
        paiements_base = paiements_base.filter(frais__type_frais=type_frais_filter)
    
    if annee_filter:
        try:
            annee = int(annee_filter)
            paiements_base = paiements_base.filter(date_paiement__year=annee)
        except ValueError:
            pass
    
    # Statistiques générales
    total_attendu_global = frais_base.aggregate(total=Sum('montant_total'))['total'] or 0
    total_percu_global = paiements_base.aggregate(total=Sum('montant_paye'))['total'] or 0
    total_eleves = frais_base.values('eleve').distinct().count()
    total_paiements = paiements_base.count()
    
    # Taux de recouvrement global
    taux_recouvrement_global = (total_percu_global / total_attendu_global * 100) if total_attendu_global > 0 else 0
    
    # Statistiques par trimestre
    stats_trimestres = []
    for trimestre in [1, 2, 3]:
        frais_trimestre = frais_base.filter(trimestre=trimestre)
        total_attendu = frais_trimestre.aggregate(total=Sum('montant_total'))['total'] or 0
        
        paiements_trimestre = paiements_base.filter(frais__trimestre=trimestre)
        total_percu = paiements_trimestre.aggregate(total=Sum('montant_paye'))['total'] or 0
        
        nb_eleves = frais_trimestre.values('eleve').distinct().count()
        nb_paiements = paiements_trimestre.count()
        
        stats_trimestres.append({
            'trimestre': trimestre,
            'libelle': f"{trimestre}er Trimestre" if trimestre == 1 else f"{trimestre}ème Trimestre",
            'total_attendu': total_attendu,
            'total_percu': total_percu,
            'solde': total_attendu - total_percu,
            'taux': (total_percu / total_attendu * 100) if total_attendu > 0 else 0,
            'nb_eleves': nb_eleves,
            'nb_paiements': nb_paiements,
        })
    
    # Statistiques par niveau
    niveaux = ['maternel', 'primaire', 'humanite']
    niveaux_labels = {
        'maternel': 'Maternel',
        'primaire': 'Primaire',
        'humanite': 'Humanité'
    }
    
    stats_niveaux = []
    for niveau in niveaux:
        frais_niveau = frais_base.filter(eleve__classe__niveau=niveau)
        total_attendu = frais_niveau.aggregate(total=Sum('montant_total'))['total'] or 0
        
        paiements_niveau = paiements_base.filter(frais__eleve__classe__niveau=niveau)
        total_percu = paiements_niveau.aggregate(total=Sum('montant_paye'))['total'] or 0
        
        nb_eleves = frais_niveau.values('eleve').distinct().count()
        
        stats_niveaux.append({
            'niveau': niveau,
            'libelle': niveaux_labels.get(niveau, niveau.capitalize()),
            'total_attendu': total_attendu,
            'total_percu': total_percu,
            'solde': total_attendu - total_percu,
            'taux': (total_percu / total_attendu * 100) if total_attendu > 0 else 0,
            'nb_eleves': nb_eleves,
        })
    
    # Top 10 des meilleurs payeurs
    top_payeurs = []
    eleves_avec_paiements = paiements_base.values('eleve').distinct()
    
    for item in eleves_avec_paiements:
        eleve = Eleve.objects.get(pk=item['eleve'])
        total_paye = paiements_base.filter(eleve=eleve).aggregate(total=Sum('montant_paye'))['total'] or 0
        total_a_payer = frais_base.filter(eleve=eleve).aggregate(total=Sum('montant_total'))['total'] or 0
        
        top_payeurs.append({
            'eleve': eleve,
            'total_paye': total_paye,
            'total_a_payer': total_a_payer,
            'taux': (total_paye / total_a_payer * 100) if total_a_payer > 0 else 0,
        })
    
    top_payeurs = sorted(top_payeurs, key=lambda x: x['total_paye'], reverse=True)[:10]
    
    # Liste des mauvais payeurs (solde > 0)
    mauvais_payeurs = []
    tous_les_eleves = Eleve.objects.all()
    
    if niveau_filter:
        tous_les_eleves = tous_les_eleves.filter(classe__niveau=niveau_filter)
    if classe_filter:
        tous_les_eleves = tous_les_eleves.filter(
            Q(classe__classe_maternel=classe_filter) |
            Q(classe__classe_primaire=classe_filter) |
            Q(classe__classe_humanite=classe_filter)
        )
    
    for eleve in tous_les_eleves:
        total_a_payer = frais_base.filter(eleve=eleve).aggregate(total=Sum('montant_total'))['total'] or 0
        total_paye = paiements_base.filter(eleve=eleve).aggregate(total=Sum('montant_paye'))['total'] or 0
        solde = total_a_payer - total_paye
        
        # Appliquer le filtre statut_paiement
        if statut_paiement_filter == 'paye' and solde > 0:
            continue
        elif statut_paiement_filter == 'impaye' and solde <= 0:
            continue
        elif statut_paiement_filter == 'partiel' and (solde <= 0 or total_paye == 0):
            continue
        
        if solde > 0:
            mauvais_payeurs.append({
                'eleve': eleve,
                'total_a_payer': total_a_payer,
                'total_paye': total_paye,
                'solde': solde,
                'taux': (total_paye / total_a_payer * 100) if total_a_payer > 0 else 0,
            })
    
    mauvais_payeurs = sorted(mauvais_payeurs, key=lambda x: x['solde'], reverse=True)[:20]
    
    # Statistiques par type de frais
    types_frais = ['inscription', 'minerval', 'uniforme', 'examen', 'bibliotheque', 'activite', 'cantine', 'transport', 'autre']
    types_frais_labels = dict(FraisScolaire.TYPES_FRAIS)
    
    stats_types = []
    for type_frais in types_frais:
        frais_type = frais_base.filter(type_frais=type_frais)
        total_attendu = frais_type.aggregate(total=Sum('montant_total'))['total'] or 0
        
        paiements_type = paiements_base.filter(frais__type_frais=type_frais)
        total_percu = paiements_type.aggregate(total=Sum('montant_paye'))['total'] or 0
        
        stats_types.append({
            'type': type_frais,
            'libelle': types_frais_labels.get(type_frais, type_frais.capitalize()),
            'total_attendu': total_attendu,
            'total_percu': total_percu,
            'solde': total_attendu - total_percu,
            'taux': (total_percu / total_attendu * 100) if total_attendu > 0 else 0,
        })
    
    # Statistiques par mode de paiement
    modes_paiement = ['cash', 'mobile_money', 'banque', 'cheque', 'carte']
    modes_labels = dict(Paiement.MODE_PAIEMENT)
    
    stats_modes = []
    for mode in modes_paiement:
        total_mode = paiements_base.filter(mode_paiement=mode).aggregate(total=Sum('montant_paye'))['total'] or 0
        nb_paiements_mode = paiements_base.filter(mode_paiement=mode).count()
        
        stats_modes.append({
            'mode': mode,
            'libelle': modes_labels.get(mode, mode.capitalize()),
            'total': total_mode,
            'nb_paiements': nb_paiements_mode,
            'pourcentage': (total_mode / total_percu_global * 100) if total_percu_global > 0 else 0,
        })
    
    # Récupérer les classes disponibles pour les filtres
    classes_maternel = [
        ('1ere_maternelle', '1ère maternelle'),
        ('2eme_maternelle', '2ème maternelle'),
        ('3eme_maternelle', '3ème maternelle'),
    ]
    
    classes_primaire = [
        ('1ere', '1ère année'),
        ('2eme', '2ème année'),
        ('3eme', '3ème année'),
        ('4eme', '4ème année'),
        ('5eme', '5ème année'),
        ('6eme', '6ème année'),
    ]
    
    classes_humanite = [
        ('7eme', '7ème année'),
        ('8eme', '8ème année'),
        ('1ere_humanite', '1ère humanité'),
        ('2eme_humanite', '2ème humanité'),
        ('3eme_humanite', '3ème humanité'),
        ('4eme_humanite', '4ème humanité'),
    ]
    
    # Années disponibles pour les filtres
    annees_paiement = Paiement.objects.filter(
        frais__annee_scolaire=annee_active
    ).dates('date_paiement', 'year', order='DESC')
    
    context = {
        'annee_active': annee_active,
        'stats_trimestres': stats_trimestres,
        'stats_niveaux': stats_niveaux,
        'stats_types': stats_types,
        'stats_modes': stats_modes,
        'top_payeurs': top_payeurs,
        'mauvais_payeurs': mauvais_payeurs,
        'total_attendu_global': total_attendu_global,
        'total_percu_global': total_percu_global,
        'total_eleves': total_eleves,
        'total_paiements': total_paiements,
        'taux_recouvrement_global': taux_recouvrement_global,
        # Filtres
        'niveau_filter': niveau_filter,
        'classe_filter': classe_filter,
        'trimestre_filter': trimestre_filter,
        'annee_filter': annee_filter,
        'statut_paiement_filter': statut_paiement_filter,
        'type_frais_filter': type_frais_filter,
        # Listes déroulantes
        'classes_maternel': classes_maternel,
        'classes_primaire': classes_primaire,
        'classes_humanite': classes_humanite,
        'types_frais': types_frais_labels,
        'annees_paiement': annees_paiement,
        # Statistiques avancées
        'date_generation': datetime.datetime.now(),
    }
    return render(request, 'frais_scolaire/statistiques.html', context)"""



from django.db.models import Sum, Count, Q
from django.db.models.functions import ExtractYear
import datetime




@login_required
def statistiques_frais(request):
    """Statistiques détaillées des frais scolaires avec filtres avancés incluant les dates"""
    annee_active = AnneeScolaire.objects.filter(est_active=True).first()
    
    if not annee_active:
        messages.warning(request, "Veuillez d'abord configurer une année scolaire active")
        return redirect('frais_scolaire:configurer_annee')
    
    # Récupérer les paramètres de filtres
    niveau_filter = request.GET.get('niveau', '')
    classe_filter = request.GET.get('classe', '')
    trimestre_filter = request.GET.get('trimestre', '')
    annee_filter = request.GET.get('annee', '')
    statut_paiement_filter = request.GET.get('statut_paiement', '')
    type_frais_filter = request.GET.get('type_frais', '')
    statut_masp_filter = request.GET.get('statut_masp', '')  # 'masp', 'non_masp', ''
    
    # NOUVEAUX FILTRES DE DATE
    date_debut_filter = request.GET.get('date_debut', '')
    date_fin_filter = request.GET.get('date_fin', '')
    periode_filter = request.GET.get('periode', '')
    periode_glissante = request.GET.get('periode_glissante', '')
    
    # Base de requête pour les frais
    frais_base = FraisScolaire.objects.filter(annee_scolaire=annee_active)
    
    # Base pour les paiements
    paiements_base = Paiement.objects.filter(frais__annee_scolaire=annee_active, statut='valide')
    
    # Appliquer les filtres
    if niveau_filter:
        frais_base = frais_base.filter(eleve__classe__niveau=niveau_filter)
        paiements_base = paiements_base.filter(frais__eleve__classe__niveau=niveau_filter)
    
    if classe_filter:
        frais_base = frais_base.filter(
            Q(eleve__classe__classe_maternel=classe_filter) |
            Q(eleve__classe__classe_primaire=classe_filter) |
            Q(eleve__classe__classe_humanite=classe_filter)
        )
        paiements_base = paiements_base.filter(
            Q(frais__eleve__classe__classe_maternel=classe_filter) |
            Q(frais__eleve__classe__classe_primaire=classe_filter) |
            Q(frais__eleve__classe__classe_humanite=classe_filter)
        )
    
    # Filtrer par MASP
    if statut_masp_filter == 'masp':
        frais_base = frais_base.filter(eleve__est_masp=True)
        paiements_base = paiements_base.filter(eleve__est_masp=True)
    elif statut_masp_filter == 'non_masp':
        frais_base = frais_base.filter(eleve__est_masp=False)
        paiements_base = paiements_base.filter(eleve__est_masp=False)
    
    if trimestre_filter and trimestre_filter.isdigit():
        frais_base = frais_base.filter(trimestre=int(trimestre_filter))
        paiements_base = paiements_base.filter(frais__trimestre=int(trimestre_filter))
    
    if type_frais_filter:
        frais_base = frais_base.filter(type_frais=type_frais_filter)
        paiements_base = paiements_base.filter(frais__type_frais=type_frais_filter)
    
    if annee_filter:
        try:
            annee = int(annee_filter)
            paiements_base = paiements_base.filter(date_paiement__year=annee)
        except ValueError:
            pass
    
    # ============================================================
    # NOUVEAU : APPLICATION DES FILTRES DE DATE SUR LES PAIEMENTS
    # ============================================================
    
    # Fonction pour parser les dates
    def parse_date(date_str):
        if date_str:
            try:
                return datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
            except (ValueError, TypeError):
                return None
        return None
    
    # Appliquer le filtre date_debut (paiements après cette date)
    if date_debut_filter:
        date_debut = parse_date(date_debut_filter)
        if date_debut:
            paiements_base = paiements_base.filter(date_paiement__gte=date_debut)
    
    # Appliquer le filtre date_fin (paiements avant cette date)
    if date_fin_filter:
        date_fin = parse_date(date_fin_filter)
        if date_fin:
            paiements_base = paiements_base.filter(date_paiement__lte=date_fin)
    
    # Appliquer le filtre de période glissante (derniers X jours)
    if periode_glissante:
        try:
            jours = int(periode_glissante)
            date_limite = datetime.date.today() - datetime.timedelta(days=jours)
            paiements_base = paiements_base.filter(date_paiement__gte=date_limite)
        except (ValueError, TypeError):
            pass
    
    # Appliquer le filtre de période prédéfinie
    today = datetime.date.today()
    
    if periode_filter == 'aujourdhui':
        paiements_base = paiements_base.filter(date_paiement=today)
    elif periode_filter == 'hier':
        hier = today - datetime.timedelta(days=1)
        paiements_base = paiements_base.filter(date_paiement=hier)
    elif periode_filter == 'semaine':
        debut_semaine = today - datetime.timedelta(days=today.weekday())
        paiements_base = paiements_base.filter(date_paiement__gte=debut_semaine)
    elif periode_filter == 'semaine_derniere':
        debut_semaine_derniere = today - datetime.timedelta(days=today.weekday() + 7)
        fin_semaine_derniere = debut_semaine_derniere + datetime.timedelta(days=6)
        paiements_base = paiements_base.filter(
            date_paiement__gte=debut_semaine_derniere,
            date_paiement__lte=fin_semaine_derniere
        )
    elif periode_filter == 'mois':
        debut_mois = today.replace(day=1)
        paiements_base = paiements_base.filter(date_paiement__gte=debut_mois)
    elif periode_filter == 'mois_dernier':
        premier_jour_mois_dernier = (today.replace(day=1) - datetime.timedelta(days=1)).replace(day=1)
        dernier_jour_mois_dernier = premier_jour_mois_dernier.replace(
            day=(premier_jour_mois_dernier.replace(month=premier_jour_mois_dernier.month % 12 + 1, day=1) - datetime.timedelta(days=1)).day
        )
        paiements_base = paiements_base.filter(
            date_paiement__gte=premier_jour_mois_dernier,
            date_paiement__lte=dernier_jour_mois_dernier
        )
    elif periode_filter == 'trimestre':
        trimestre_actuel = (today.month - 1) // 3
        debut_trimestre = today.replace(month=trimestre_actuel * 3 + 1, day=1)
        paiements_base = paiements_base.filter(date_paiement__gte=debut_trimestre)
    elif periode_filter == 'annee':
        debut_annee = today.replace(month=1, day=1)
        paiements_base = paiements_base.filter(date_paiement__gte=debut_annee)
    
    # ============================================================
    # FIN DES NOUVEAUX FILTRES DE DATE
    # ============================================================
    
    # Statistiques générales
    total_attendu_global = frais_base.aggregate(total=Sum('montant_total'))['total'] or 0
    total_percu_global = paiements_base.aggregate(total=Sum('montant_paye'))['total'] or 0
    solde_global = total_attendu_global - total_percu_global
    total_eleves = frais_base.values('eleve').distinct().count()
    total_paiements = paiements_base.count()
    
    # Taux de recouvrement global
    taux_recouvrement_global = (total_percu_global / total_attendu_global * 100) if total_attendu_global > 0 else 0
    
    # Statistiques MASP vs Non MASP
    # MASP
    frais_masp = FraisScolaire.objects.filter(annee_scolaire=annee_active, eleve__est_masp=True)
    if niveau_filter:
        frais_masp = frais_masp.filter(eleve__classe__niveau=niveau_filter)
    if classe_filter:
        frais_masp = frais_masp.filter(
            Q(eleve__classe__classe_maternel=classe_filter) |
            Q(eleve__classe__classe_primaire=classe_filter) |
            Q(eleve__classe__classe_humanite=classe_filter)
        )
    if trimestre_filter and trimestre_filter.isdigit():
        frais_masp = frais_masp.filter(trimestre=int(trimestre_filter))
    
    paiements_masp = Paiement.objects.filter(frais__annee_scolaire=annee_active, statut='valide', eleve__est_masp=True)
    if niveau_filter:
        paiements_masp = paiements_masp.filter(frais__eleve__classe__niveau=niveau_filter)
    if classe_filter:
        paiements_masp = paiements_masp.filter(
            Q(frais__eleve__classe__classe_maternel=classe_filter) |
            Q(frais__eleve__classe__classe_primaire=classe_filter) |
            Q(frais__eleve__classe__classe_humanite=classe_filter)
        )
    if trimestre_filter and trimestre_filter.isdigit():
        paiements_masp = paiements_masp.filter(frais__trimestre=int(trimestre_filter))
    
    # Appliquer les filtres de date aux paiements MASP
    if date_debut_filter:
        date_debut = parse_date(date_debut_filter)
        if date_debut:
            paiements_masp = paiements_masp.filter(date_paiement__gte=date_debut)
    if date_fin_filter:
        date_fin = parse_date(date_fin_filter)
        if date_fin:
            paiements_masp = paiements_masp.filter(date_paiement__lte=date_fin)
    if periode_glissante:
        try:
            jours = int(periode_glissante)
            date_limite = datetime.date.today() - datetime.timedelta(days=jours)
            paiements_masp = paiements_masp.filter(date_paiement__gte=date_limite)
        except (ValueError, TypeError):
            pass
    if periode_filter:
        if periode_filter == 'aujourdhui':
            paiements_masp = paiements_masp.filter(date_paiement=today)
        elif periode_filter == 'hier':
            hier = today - datetime.timedelta(days=1)
            paiements_masp = paiements_masp.filter(date_paiement=hier)
        elif periode_filter == 'semaine':
            debut_semaine = today - datetime.timedelta(days=today.weekday())
            paiements_masp = paiements_masp.filter(date_paiement__gte=debut_semaine)
        elif periode_filter == 'mois':
            debut_mois = today.replace(day=1)
            paiements_masp = paiements_masp.filter(date_paiement__gte=debut_mois)
        elif periode_filter == 'annee':
            debut_annee = today.replace(month=1, day=1)
            paiements_masp = paiements_masp.filter(date_paiement__gte=debut_annee)
    
    total_attendu_masp = frais_masp.aggregate(total=Sum('montant_total'))['total'] or 0
    total_percu_masp = paiements_masp.aggregate(total=Sum('montant_paye'))['total'] or 0
    nb_eleves_masp = frais_masp.values('eleve').distinct().count()
    
    # Non MASP
    frais_non_masp = FraisScolaire.objects.filter(annee_scolaire=annee_active, eleve__est_masp=False)
    if niveau_filter:
        frais_non_masp = frais_non_masp.filter(eleve__classe__niveau=niveau_filter)
    if classe_filter:
        frais_non_masp = frais_non_masp.filter(
            Q(eleve__classe__classe_maternel=classe_filter) |
            Q(eleve__classe__classe_primaire=classe_filter) |
            Q(eleve__classe__classe_humanite=classe_filter)
        )
    if trimestre_filter and trimestre_filter.isdigit():
        frais_non_masp = frais_non_masp.filter(trimestre=int(trimestre_filter))
    
    paiements_non_masp = Paiement.objects.filter(frais__annee_scolaire=annee_active, statut='valide', eleve__est_masp=False)
    if niveau_filter:
        paiements_non_masp = paiements_non_masp.filter(frais__eleve__classe__niveau=niveau_filter)
    if classe_filter:
        paiements_non_masp = paiements_non_masp.filter(
            Q(frais__eleve__classe__classe_maternel=classe_filter) |
            Q(frais__eleve__classe__classe_primaire=classe_filter) |
            Q(frais__eleve__classe__classe_humanite=classe_filter)
        )
    if trimestre_filter and trimestre_filter.isdigit():
        paiements_non_masp = paiements_non_masp.filter(frais__trimestre=int(trimestre_filter))
    
    # Appliquer les filtres de date aux paiements Non MASP
    if date_debut_filter:
        date_debut = parse_date(date_debut_filter)
        if date_debut:
            paiements_non_masp = paiements_non_masp.filter(date_paiement__gte=date_debut)
    if date_fin_filter:
        date_fin = parse_date(date_fin_filter)
        if date_fin:
            paiements_non_masp = paiements_non_masp.filter(date_paiement__lte=date_fin)
    if periode_glissante:
        try:
            jours = int(periode_glissante)
            date_limite = datetime.date.today() - datetime.timedelta(days=jours)
            paiements_non_masp = paiements_non_masp.filter(date_paiement__gte=date_limite)
        except (ValueError, TypeError):
            pass
    if periode_filter:
        if periode_filter == 'aujourdhui':
            paiements_non_masp = paiements_non_masp.filter(date_paiement=today)
        elif periode_filter == 'hier':
            hier = today - datetime.timedelta(days=1)
            paiements_non_masp = paiements_non_masp.filter(date_paiement=hier)
        elif periode_filter == 'semaine':
            debut_semaine = today - datetime.timedelta(days=today.weekday())
            paiements_non_masp = paiements_non_masp.filter(date_paiement__gte=debut_semaine)
        elif periode_filter == 'mois':
            debut_mois = today.replace(day=1)
            paiements_non_masp = paiements_non_masp.filter(date_paiement__gte=debut_mois)
        elif periode_filter == 'annee':
            debut_annee = today.replace(month=1, day=1)
            paiements_non_masp = paiements_non_masp.filter(date_paiement__gte=debut_annee)
    
    total_attendu_non_masp = frais_non_masp.aggregate(total=Sum('montant_total'))['total'] or 0
    total_percu_non_masp = paiements_non_masp.aggregate(total=Sum('montant_paye'))['total'] or 0
    nb_eleves_non_masp = frais_non_masp.values('eleve').distinct().count()
    
    # Statistiques par trimestre
    stats_trimestres = []
    for trimestre in [1, 2, 3]:
        frais_trimestre = frais_base.filter(trimestre=trimestre)
        total_attendu = frais_trimestre.aggregate(total=Sum('montant_total'))['total'] or 0
        
        paiements_trimestre = paiements_base.filter(frais__trimestre=trimestre)
        total_percu = paiements_trimestre.aggregate(total=Sum('montant_paye'))['total'] or 0
        
        nb_eleves = frais_trimestre.values('eleve').distinct().count()
        nb_paiements = paiements_trimestre.count()
        
        stats_trimestres.append({
            'trimestre': trimestre,
            'libelle': f"{trimestre}er Trimestre" if trimestre == 1 else f"{trimestre}ème Trimestre",
            'total_attendu': total_attendu,
            'total_percu': total_percu,
            'solde': total_attendu - total_percu,
            'taux': (total_percu / total_attendu * 100) if total_attendu > 0 else 0,
            'nb_eleves': nb_eleves,
            'nb_paiements': nb_paiements,
        })
    
    # Statistiques par niveau
    niveaux = ['maternel', 'primaire', 'humanite']
    niveaux_labels = {
        'maternel': 'Maternel',
        'primaire': 'Primaire',
        'humanite': 'Humanité'
    }
    
    stats_niveaux = []
    for niveau in niveaux:
        frais_niveau = frais_base.filter(eleve__classe__niveau=niveau)
        total_attendu = frais_niveau.aggregate(total=Sum('montant_total'))['total'] or 0
        
        paiements_niveau = paiements_base.filter(frais__eleve__classe__niveau=niveau)
        total_percu = paiements_niveau.aggregate(total=Sum('montant_paye'))['total'] or 0
        
        nb_eleves = frais_niveau.values('eleve').distinct().count()
        
        stats_niveaux.append({
            'niveau': niveau,
            'libelle': niveaux_labels.get(niveau, niveau.capitalize()),
            'total_attendu': total_attendu,
            'total_percu': total_percu,
            'solde': total_attendu - total_percu,
            'taux': (total_percu / total_attendu * 100) if total_attendu > 0 else 0,
            'nb_eleves': nb_eleves,
        })
    
    # Top 10 des meilleurs payeurs
    top_payeurs = []
    eleves_avec_paiements = paiements_base.values('eleve').distinct()
    
    for item in eleves_avec_paiements:
        eleve = Eleve.objects.get(pk=item['eleve'])
        total_paye = paiements_base.filter(eleve=eleve).aggregate(total=Sum('montant_paye'))['total'] or 0
        total_a_payer = frais_base.filter(eleve=eleve).aggregate(total=Sum('montant_total'))['total'] or 0
        solde = total_a_payer - total_paye
        
        # Appliquer le filtre statut_paiement
        if statut_paiement_filter == 'paye' and solde > 0:
            continue
        elif statut_paiement_filter == 'impaye' and solde <= 0:
            continue
        elif statut_paiement_filter == 'partiel' and (solde <= 0 or total_paye == 0):
            continue
        
        top_payeurs.append({
            'eleve': eleve,
            'total_paye': total_paye,
            'total_a_payer': total_a_payer,
            'taux': (total_paye / total_a_payer * 100) if total_a_payer > 0 else 0,
        })
    
    top_payeurs = sorted(top_payeurs, key=lambda x: x['total_paye'], reverse=True)[:10]
    
    # Liste des mauvais payeurs (solde > 0)
    mauvais_payeurs = []
    tous_les_eleves = Eleve.objects.all()
    
    if niveau_filter:
        tous_les_eleves = tous_les_eleves.filter(classe__niveau=niveau_filter)
    if classe_filter:
        tous_les_eleves = tous_les_eleves.filter(
            Q(classe__classe_maternel=classe_filter) |
            Q(classe__classe_primaire=classe_filter) |
            Q(classe__classe_humanite=classe_filter)
        )
    if statut_masp_filter == 'masp':
        tous_les_eleves = tous_les_eleves.filter(est_masp=True)
    elif statut_masp_filter == 'non_masp':
        tous_les_eleves = tous_les_eleves.filter(est_masp=False)
    
    for eleve in tous_les_eleves:
        total_a_payer = frais_base.filter(eleve=eleve).aggregate(total=Sum('montant_total'))['total'] or 0
        total_paye = paiements_base.filter(eleve=eleve).aggregate(total=Sum('montant_paye'))['total'] or 0
        solde = total_a_payer - total_paye
        
        # Appliquer le filtre statut_paiement
        if statut_paiement_filter == 'paye' and solde > 0:
            continue
        elif statut_paiement_filter == 'impaye' and solde <= 0:
            continue
        elif statut_paiement_filter == 'partiel' and (solde <= 0 or total_paye == 0):
            continue
        
        if solde > 0:
            mauvais_payeurs.append({
                'eleve': eleve,
                'total_a_payer': total_a_payer,
                'total_paye': total_paye,
                'solde': solde,
                'taux': (total_paye / total_a_payer * 100) if total_a_payer > 0 else 0,
            })
    
    mauvais_payeurs = sorted(mauvais_payeurs, key=lambda x: x['solde'], reverse=True)[:20]
    
    # Statistiques par type de frais
    types_frais = ['inscription', 'minerval', 'uniforme', 'examen', 'bibliotheque', 'activite', 'cantine', 'transport', 'autre']
    types_frais_labels = dict(FraisScolaire.TYPES_FRAIS)
    
    stats_types = []
    for type_frais in types_frais:
        frais_type = frais_base.filter(type_frais=type_frais)
        total_attendu = frais_type.aggregate(total=Sum('montant_total'))['total'] or 0
        
        paiements_type = paiements_base.filter(frais__type_frais=type_frais)
        total_percu = paiements_type.aggregate(total=Sum('montant_paye'))['total'] or 0
        
        stats_types.append({
            'type': type_frais,
            'libelle': types_frais_labels.get(type_frais, type_frais.capitalize()),
            'total_attendu': total_attendu,
            'total_percu': total_percu,
            'solde': total_attendu - total_percu,
            'taux': (total_percu / total_attendu * 100) if total_attendu > 0 else 0,
        })
    
    # Statistiques par mode de paiement
    modes_paiement = ['cash', 'mobile_money', 'banque', 'cheque', 'carte']
    modes_labels = dict(Paiement.MODE_PAIEMENT)
    
    stats_modes = []
    for mode in modes_paiement:
        total_mode = paiements_base.filter(mode_paiement=mode).aggregate(total=Sum('montant_paye'))['total'] or 0
        nb_paiements_mode = paiements_base.filter(mode_paiement=mode).count()
        
        stats_modes.append({
            'mode': mode,
            'libelle': modes_labels.get(mode, mode.capitalize()),
            'total': total_mode,
            'nb_paiements': nb_paiements_mode,
            'pourcentage': (total_mode / total_percu_global * 100) if total_percu_global > 0 else 0,
        })
    
    # Récupérer les classes disponibles pour les filtres
    classes_maternel = [
        ('1ere_maternelle', '1ère maternelle'),
        ('2eme_maternelle', '2ème maternelle'),
        ('3eme_maternelle', '3ème maternelle'),
    ]
    
    classes_primaire = [
        ('1ere', '1ère année'),
        ('2eme', '2ème année'),
        ('3eme', '3ème année'),
        ('4eme', '4ème année'),
        ('5eme', '5ème année'),
        ('6eme', '6ème année'),
    ]
    
    classes_humanite = [
        ('7eme', '7ème année'),
        ('8eme', '8ème année'),
        ('1ere_humanite', '1ère humanité'),
        ('2eme_humanite', '2ème humanité'),
        ('3eme_humanite', '3ème humanité'),
        ('4eme_humanite', '4ème humanité'),
    ]
    
    # Années disponibles pour les filtres
    annees_paiement = Paiement.objects.filter(
        frais__annee_scolaire=annee_active
    ).dates('date_paiement', 'year', order='DESC')
    
    context = {
        'annee_active': annee_active,
        'stats_trimestres': stats_trimestres,
        'stats_niveaux': stats_niveaux,
        'stats_types': stats_types,
        'stats_modes': stats_modes,
        'top_payeurs': top_payeurs,
        'mauvais_payeurs': mauvais_payeurs,
        'total_attendu_global': total_attendu_global,
        'total_percu_global': total_percu_global,
        'solde_global': solde_global,
        'total_eleves': total_eleves,
        'total_paiements': total_paiements,
        'taux_recouvrement_global': taux_recouvrement_global,
        # Statistiques MASP
        'stats_masp': {
            'total_attendu': total_attendu_masp,
            'total_percu': total_percu_masp,
            'solde': total_attendu_masp - total_percu_masp,
            'taux': (total_percu_masp / total_attendu_masp * 100) if total_attendu_masp > 0 else 0,
            'nb_eleves': nb_eleves_masp,
        },
        'stats_non_masp': {
            'total_attendu': total_attendu_non_masp,
            'total_percu': total_percu_non_masp,
            'solde': total_attendu_non_masp - total_percu_non_masp,
            'taux': (total_percu_non_masp / total_attendu_non_masp * 100) if total_attendu_non_masp > 0 else 0,
            'nb_eleves': nb_eleves_non_masp,
        },
        # Filtres existants
        'niveau_filter': niveau_filter,
        'classe_filter': classe_filter,
        'trimestre_filter': trimestre_filter,
        'annee_filter': annee_filter,
        'statut_paiement_filter': statut_paiement_filter,
        'type_frais_filter': type_frais_filter,
        'statut_masp_filter': statut_masp_filter,
        # NOUVEAUX FILTRES DE DATE
        'date_debut_filter': date_debut_filter,
        'date_fin_filter': date_fin_filter,
        'periode_filter': periode_filter,
        'periode_glissante': periode_glissante,
        # Listes déroulantes
        'classes_maternel': classes_maternel,
        'classes_primaire': classes_primaire,
        'classes_humanite': classes_humanite,
        'types_frais': types_frais_labels,
        'annees_paiement': annees_paiement,
        # Statistiques avancées
        'date_generation': datetime.datetime.now(),
    }
    return render(request, 'frais_scolaire/statistiques.html', context)




from django.http import HttpResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
import io

@login_required
@superuser_silent_action
def imprimer_recu(request, paiement_id):
    """Imprimer un reçu de paiement en PDF"""
    paiement = get_object_or_404(Paiement, pk=paiement_id)
    
    # Créer le buffer PDF
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    story = []
    
    # Style personnalisé pour le titre
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontSize=16,
        alignment=1,  # Centre
        spaceAfter=20,
    )
    
    # En-tête du reçu
    titre = Paragraph("COMPLEXE SCOLAIRE SUBLIME", title_style)
    story.append(titre)
    
    sous_titre = Paragraph("Excellence, Discipline, Réussite", styles['Heading2'])
    sous_titre.alignment = 1
    story.append(sous_titre)
    story.append(Spacer(1, 20))
    
    # Titre du document
    recu_title = Paragraph("REÇU DE PAIEMENT", styles['Heading1'])
    recu_title.alignment = 1
    story.append(recu_title)
    story.append(Spacer(1, 20))
    
    # Informations du reçu
    data = [
        ['N° Reçu:', paiement.reference],
        ['Date:', paiement.date_paiement.strftime('%d/%m/%Y')],
        ['', ''],
        ['Élève:', f"{paiement.eleve.nom} {paiement.eleve.post_nom} {paiement.eleve.prenom}"],
        ['Matricule:', paiement.eleve.matricule],
        ['Classe:', str(paiement.eleve.classe) if paiement.eleve.classe else 'Non définie'],
    ]
    
    # Ajouter l'option si c'est l'humanité
    if paiement.eleve.classe and paiement.eleve.classe.niveau == 'humanite' and paiement.eleve.classe.section:
        data.append(['Option:', paiement.eleve.classe.get_section_display()])
    
    data.extend([
        ['', ''],
        ['Trimestre:', paiement.frais.get_trimestre_display()],
        ['Type de frais:', paiement.frais.get_type_frais_display()],
        ['Montant payé:', f"{paiement.montant_paye:,.0f} FC"],
        ['Mode de paiement:', paiement.get_mode_paiement_display()],
        ['Agent:', paiement.agent.username if paiement.agent else 'N/A'],
    ])
    
    # Créer le tableau
    table = Table(data, colWidths=[4*cm, 10*cm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.black),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    
    story.append(table)
    story.append(Spacer(1, 30))
    
    # Montant en lettres
    montant_lettres = nombre_en_lettres(int(paiement.montant_paye))
    texte_lettres = Paragraph(f"<b>Montant en lettres :</b> {montant_lettres} Francs Congolais", styles['Normal'])
    story.append(texte_lettres)
    story.append(Spacer(1, 30))
    
    # Signatures
    signature_data = [
        ['L\'agent comptable', 'Cachet de l\'établissement'],
        ['', ''],
        ['_________________', '_________________'],
    ]
    
    signature_table = Table(signature_data, colWidths=[7*cm, 7*cm])
    signature_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
    ]))
    story.append(signature_table)
    story.append(Spacer(1, 20))
    
    # Pied de page
    footer = Paragraph("Merci pour votre confiance !", styles['Normal'])
    footer.alignment = 1
    story.append(footer)
    
    # Générer le PDF
    doc.build(story)
    buffer.seek(0)
    
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="recu_{paiement.reference}.pdf"'
    return response


def nombre_en_lettres(nombre):
    """Convertir un nombre en lettres (version simplifiée)"""
    if nombre == 0:
        return "zéro"
    
    unites = ["", "un", "deux", "trois", "quatre", "cinq", "six", "sept", "huit", "neuf",
              "dix", "onze", "douze", "treize", "quatorze", "quinze", "seize", "dix-sept",
              "dix-huit", "dix-neuf"]
    
    dizaines = ["", "dix", "vingt", "trente", "quarante", "cinquante", "soixante", "soixante-dix",
                "quatre-vingt", "quatre-vingt-dix"]
    
    if nombre < 20:
        return unites[nombre]
    elif nombre < 100:
        d = nombre // 10
        u = nombre % 10
        if u == 0:
            return dizaines[d]
        elif d == 7 or d == 9:
            return dizaines[d] + "-" + unites[10 + u]
        else:
            return dizaines[d] + "-" + unites[u]
    elif nombre < 1000:
        c = nombre // 100
        r = nombre % 100
        if c == 1:
            if r == 0:
                return "cent"
            else:
                return "cent " + nombre_en_lettres(r)
        else:
            if r == 0:
                return unites[c] + " cents"
            else:
                return unites[c] + " cent " + nombre_en_lettres(r)
    else:
        return str(nombre)








from django.db.models import Sum, Q
from django.db.models import Sum, Q
import datetime

@login_required
@superuser_silent_action
def comparaison_paiements_masp(request):
    """Comparer les paiements des élèves MASP avec un montant de référence et filtres de date"""
    annee_active = AnneeScolaire.objects.filter(est_active=True).first()
    
    if not annee_active:
        messages.warning(request, "Veuillez d'abord configurer une année scolaire active")
        return redirect('frais_scolaire:configurer_annee')
    
    # Récupérer le montant de référence depuis le formulaire
    montant_reference = request.GET.get('montant_reference', 0)
    try:
        montant_reference = float(montant_reference)
    except ValueError:
        montant_reference = 0
    
    # Récupérer les filtres
    niveau_filter = request.GET.get('niveau', '')
    classe_filter = request.GET.get('classe', '')
    trimestre_filter = request.GET.get('trimestre', '')
    
    # NOUVEAUX FILTRES DE DATE
    date_debut_filter = request.GET.get('date_debut', '')
    date_fin_filter = request.GET.get('date_fin', '')
    periode_filter = request.GET.get('periode', '')
    periode_glissante = request.GET.get('periode_glissante', '')
    
    # Fonction pour parser les dates
    def parse_date(date_str):
        if date_str:
            try:
                return datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
            except (ValueError, TypeError):
                return None
        return None
    
    # Récupérer tous les élèves MASP
    eleves_masp = Eleve.objects.filter(est_masp=True)
    
    # Appliquer les filtres
    if niveau_filter:
        eleves_masp = eleves_masp.filter(classe__niveau=niveau_filter)
    if classe_filter:
        eleves_masp = eleves_masp.filter(
            Q(classe__classe_maternel=classe_filter) |
            Q(classe__classe_primaire=classe_filter) |
            Q(classe__classe_humanite=classe_filter)
        )
    
    # Préparer les données de comparaison
    resultats = []
    total_attendu_global = 0
    total_paye_global = 0
    nb_en_ordre = 0
    nb_non_en_ordre = 0
    
    for eleve in eleves_masp:
        # Base des paiements pour l'élève
        paiements_eleve = Paiement.objects.filter(
            eleve=eleve,
            frais__annee_scolaire=annee_active,
            statut='valide'
        )
        
        # Appliquer les filtres de trimestre
        if trimestre_filter and trimestre_filter.isdigit():
            paiements_eleve = paiements_eleve.filter(frais__trimestre=int(trimestre_filter))
        
        # ============================================================
        # NOUVEAU : APPLICATION DES FILTRES DE DATE SUR LES PAIEMENTS
        # ============================================================
        
        # Appliquer le filtre date_debut (paiements après cette date)
        if date_debut_filter:
            date_debut = parse_date(date_debut_filter)
            if date_debut:
                paiements_eleve = paiements_eleve.filter(date_paiement__gte=date_debut)
        
        # Appliquer le filtre date_fin (paiements avant cette date)
        if date_fin_filter:
            date_fin = parse_date(date_fin_filter)
            if date_fin:
                paiements_eleve = paiements_eleve.filter(date_paiement__lte=date_fin)
        
        # Appliquer le filtre de période glissante (derniers X jours)
        if periode_glissante:
            try:
                jours = int(periode_glissante)
                date_limite = datetime.date.today() - datetime.timedelta(days=jours)
                paiements_eleve = paiements_eleve.filter(date_paiement__gte=date_limite)
            except (ValueError, TypeError):
                pass
        
        # Appliquer le filtre de période prédéfinie
        today = datetime.date.today()
        
        if periode_filter == 'aujourdhui':
            paiements_eleve = paiements_eleve.filter(date_paiement=today)
        elif periode_filter == 'hier':
            hier = today - datetime.timedelta(days=1)
            paiements_eleve = paiements_eleve.filter(date_paiement=hier)
        elif periode_filter == 'semaine':
            debut_semaine = today - datetime.timedelta(days=today.weekday())
            paiements_eleve = paiements_eleve.filter(date_paiement__gte=debut_semaine)
        elif periode_filter == 'semaine_derniere':
            debut_semaine_derniere = today - datetime.timedelta(days=today.weekday() + 7)
            fin_semaine_derniere = debut_semaine_derniere + datetime.timedelta(days=6)
            paiements_eleve = paiements_eleve.filter(
                date_paiement__gte=debut_semaine_derniere,
                date_paiement__lte=fin_semaine_derniere
            )
        elif periode_filter == 'mois':
            debut_mois = today.replace(day=1)
            paiements_eleve = paiements_eleve.filter(date_paiement__gte=debut_mois)
        elif periode_filter == 'mois_dernier':
            premier_jour_mois_dernier = (today.replace(day=1) - datetime.timedelta(days=1)).replace(day=1)
            dernier_jour_mois_dernier = premier_jour_mois_dernier.replace(
                day=(premier_jour_mois_dernier.replace(month=premier_jour_mois_dernier.month % 12 + 1, day=1) - datetime.timedelta(days=1)).day
            )
            paiements_eleve = paiements_eleve.filter(
                date_paiement__gte=premier_jour_mois_dernier,
                date_paiement__lte=dernier_jour_mois_dernier
            )
        elif periode_filter == 'trimestre':
            trimestre_actuel = (today.month - 1) // 3
            debut_trimestre = today.replace(month=trimestre_actuel * 3 + 1, day=1)
            paiements_eleve = paiements_eleve.filter(date_paiement__gte=debut_trimestre)
        elif periode_filter == 'annee':
            debut_annee = today.replace(month=1, day=1)
            paiements_eleve = paiements_eleve.filter(date_paiement__gte=debut_annee)
        
        # ============================================================
        # FIN DES FILTRES DE DATE
        # ============================================================
        
        total_paye = paiements_eleve.aggregate(total=Sum('montant_paye'))['total'] or 0
        
        # Calculer le total attendu pour cet élève
        frais_eleve = FraisScolaire.objects.filter(
            eleve=eleve,
            annee_scolaire=annee_active
        )
        if trimestre_filter and trimestre_filter.isdigit():
            frais_eleve = frais_eleve.filter(trimestre=int(trimestre_filter))
        
        total_attendu = frais_eleve.aggregate(total=Sum('montant_total'))['total'] or 0
        
        # Déterminer si l'élève est en ordre
        if montant_reference > 0:
            est_en_ordre = total_paye >= montant_reference
        else:
            # Si pas de montant de référence, on utilise le total attendu
            est_en_ordre = total_paye >= total_attendu
        
        # Calcul de la différence
        if montant_reference > 0:
            difference = montant_reference - total_paye
        else:
            difference = total_attendu - total_paye
        
        # Calcul du pourcentage
        if montant_reference > 0:
            pourcentage = (total_paye / montant_reference * 100) if montant_reference > 0 else 0
        else:
            pourcentage = (total_paye / total_attendu * 100) if total_attendu > 0 else 0
        
        if est_en_ordre:
            nb_en_ordre += 1
        else:
            nb_non_en_ordre += 1
        
        total_attendu_global += total_attendu
        total_paye_global += total_paye
        
        resultats.append({
            'eleve': eleve,
            'total_attendu': total_attendu,
            'total_paye': total_paye,
            'est_en_ordre': est_en_ordre,
            'difference': difference,
            'pourcentage': pourcentage,
        })
    
    # Trier les résultats (non en ordre d'abord)
    resultats.sort(key=lambda x: x['est_en_ordre'])
    
    # Calcul du solde global
    solde_global = total_attendu_global - total_paye_global
    
    # Taux de recouvrement global
    taux_recouvrement = (total_paye_global / total_attendu_global * 100) if total_attendu_global > 0 else 0
    
    # Préparer les classes pour les filtres
    classes_maternel = [
        ('1ere_maternelle', '1ère maternelle'),
        ('2eme_maternelle', '2ème maternelle'),
        ('3eme_maternelle', '3ème maternelle'),
    ]
    
    classes_primaire = [
        ('1ere', '1ère année'),
        ('2eme', '2ème année'),
        ('3eme', '3ème année'),
        ('4eme', '4ème année'),
        ('5eme', '5ème année'),
        ('6eme', '6ème année'),
    ]
    
    classes_humanite = [
        ('7eme', '7ème année'),
        ('8eme', '8ème année'),
        ('1ere_humanite', '1ère humanité'),
        ('2eme_humanite', '2ème humanité'),
        ('3eme_humanite', '3ème humanité'),
        ('4eme_humanite', '4ème humanité'),
    ]
    
    context = {
        'annee_active': annee_active,
        'resultats': resultats,
        'montant_reference': montant_reference,
        'total_attendu_global': total_attendu_global,
        'total_paye_global': total_paye_global,
        'solde_global': solde_global,
        'total_eleves': len(resultats),
        'nb_en_ordre': nb_en_ordre,
        'nb_non_en_ordre': nb_non_en_ordre,
        'taux_en_ordre': (nb_en_ordre / len(resultats) * 100) if len(resultats) > 0 else 0,
        'taux_recouvrement': taux_recouvrement,
        # Filtres existants
        'niveau_filter': niveau_filter,
        'classe_filter': classe_filter,
        'trimestre_filter': trimestre_filter,
        # NOUVEAUX FILTRES DE DATE
        'date_debut_filter': date_debut_filter,
        'date_fin_filter': date_fin_filter,
        'periode_filter': periode_filter,
        'periode_glissante': periode_glissante,
        # Listes déroulantes
        'classes_maternel': classes_maternel,
        'classes_primaire': classes_primaire,
        'classes_humanite': classes_humanite,
        'date_generation': datetime.datetime.now(),
    }
    
    return render(request, 'frais_scolaire/comparaison_masp.html', context)



#######################################################################
#######################################################################
#######################################################################

@login_required
def export_statistiques_excel(request):
    """Export des statistiques en Excel"""
    annee_active = AnneeScolaire.objects.filter(est_active=True).first()
    
    if not annee_active:
        messages.warning(request, "Veuillez d'abord configurer une année scolaire active")
        return redirect('frais_scolaire:configurer_annee')
    
    # Récupérer les mêmes données que la vue statistiques
    niveau_filter = request.GET.get('niveau', '')
    classe_filter = request.GET.get('classe', '')
    trimestre_filter = request.GET.get('trimestre', '')
    statut_masp_filter = request.GET.get('statut_masp', '')
    
    frais_base = FraisScolaire.objects.filter(annee_scolaire=annee_active)
    paiements_base = Paiement.objects.filter(frais__annee_scolaire=annee_active, statut='valide')
    
    if niveau_filter:
        frais_base = frais_base.filter(eleve__classe__niveau=niveau_filter)
        paiements_base = paiements_base.filter(frais__eleve__classe__niveau=niveau_filter)
    if classe_filter:
        frais_base = frais_base.filter(
            Q(eleve__classe__classe_maternel=classe_filter) |
            Q(eleve__classe__classe_primaire=classe_filter) |
            Q(eleve__classe__classe_humanite=classe_filter)
        )
    if trimestre_filter and trimestre_filter.isdigit():
        frais_base = frais_base.filter(trimestre=int(trimestre_filter))
        paiements_base = paiements_base.filter(frais__trimestre=int(trimestre_filter))
    if statut_masp_filter == 'masp':
        frais_base = frais_base.filter(eleve__est_masp=True)
        paiements_base = paiements_base.filter(eleve__est_masp=True)
    elif statut_masp_filter == 'non_masp':
        frais_base = frais_base.filter(eleve__est_masp=False)
        paiements_base = paiements_base.filter(eleve__est_masp=False)
    
    total_attendu = frais_base.aggregate(total=Sum('montant_total'))['total'] or 0
    total_percu = paiements_base.aggregate(total=Sum('montant_paye'))['total'] or 0
    
    # Créer le classeur Excel
    wb = Workbook()
    
    # Style pour les en-têtes
    header_font = Font(bold=True, color="FFFFFF", size=11)
    header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    header_alignment = Alignment(horizontal="center", vertical="center")
    
    # Style pour les cellules
    border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    
    # Feuille 1: Résumé général
    ws_resume = wb.active
    ws_resume.title = "Résumé Général"
    
    # Titre
    ws_resume['A1'] = f"STATISTIQUES FRAIS SCOLAIRES - {annee_active.annee}"
    ws_resume['A1'].font = Font(bold=True, size=14)
    ws_resume.merge_cells('A1:D1')
    
    ws_resume['A3'] = "Indicateur"
    ws_resume['B3'] = "Valeur"
    ws_resume['A3'].font = header_font
    ws_resume['B3'].font = header_font
    ws_resume['A3'].fill = header_fill
    ws_resume['B3'].fill = header_fill
    ws_resume['A3'].alignment = header_alignment
    ws_resume['B3'].alignment = header_alignment
    
    resume_data = [
        ("Année scolaire", annee_active.annee),
        ("Total attendu", f"{total_attendu:,.0f} FC"),
        ("Total perçu", f"{total_percu:,.0f} FC"),
        ("Solde restant", f"{total_attendu - total_percu:,.0f} FC"),
        ("Taux recouvrement", f"{(total_percu / total_attendu * 100) if total_attendu > 0 else 0:.1f}%"),
        ("Date génération", datetime.datetime.now().strftime("%d/%m/%Y %H:%M"))
    ]
    
    for i, (label, value) in enumerate(resume_data, start=4):
        ws_resume[f'A{i}'] = label
        ws_resume[f'B{i}'] = value
        ws_resume[f'A{i}'].border = border
        ws_resume[f'B{i}'].border = border
        ws_resume[f'A{i}'].font = Font(bold=True)
    
    for col in ['A', 'B']:
        ws_resume.column_dimensions[col].width = 25
    
    # Feuille 2: Paiements par élève
    ws_eleves = wb.create_sheet("Paiements par élève")
    
    # En-têtes
    headers = ["Matricule", "Nom", "Post-nom", "Prénom", "Classe", "Statut MASP", "Total à payer", "Total payé", "Solde", "Statut"]
    for col, header in enumerate(headers, start=1):
        cell = ws_eleves.cell(row=1, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_alignment
        cell.border = border
    
    # Données des élèves
    eleves = Eleve.objects.all()
    if niveau_filter:
        eleves = eleves.filter(classe__niveau=niveau_filter)
    if classe_filter:
        eleves = eleves.filter(
            Q(classe__classe_maternel=classe_filter) |
            Q(classe__classe_primaire=classe_filter) |
            Q(classe__classe_humanite=classe_filter)
        )
    if statut_masp_filter == 'masp':
        eleves = eleves.filter(est_masp=True)
    elif statut_masp_filter == 'non_masp':
        eleves = eleves.filter(est_masp=False)
    
    row = 2
    for eleve in eleves:
        total_a_payer = frais_base.filter(eleve=eleve).aggregate(total=Sum('montant_total'))['total'] or 0
        total_paye = paiements_base.filter(eleve=eleve).aggregate(total=Sum('montant_paye'))['total'] or 0
        solde = total_a_payer - total_paye
        
        ws_eleves.cell(row=row, column=1, value=eleve.matricule).border = border
        ws_eleves.cell(row=row, column=2, value=eleve.nom).border = border
        ws_eleves.cell(row=row, column=3, value=eleve.post_nom).border = border
        ws_eleves.cell(row=row, column=4, value=eleve.prenom).border = border
        ws_eleves.cell(row=row, column=5, value=str(eleve.classe or "-")).border = border
        ws_eleves.cell(row=row, column=6, value="MASP" if eleve.est_masp else "Ordinaire").border = border
        ws_eleves.cell(row=row, column=7, value=f"{total_a_payer:,.0f}").border = border
        ws_eleves.cell(row=row, column=8, value=f"{total_paye:,.0f}").border = border
        ws_eleves.cell(row=row, column=9, value=f"{solde:,.0f}").border = border
        statut = "En ordre" if solde <= 0 else "Non en ordre"
        ws_eleves.cell(row=row, column=10, value=statut).border = border
        row += 1
    
    # Ajuster les largeurs
    for col in range(1, len(headers) + 1):
        ws_eleves.column_dimensions[get_column_letter(col)].width = 18
    
    # Feuille 3: Paiements par trimestre
    ws_trimestres = wb.create_sheet("Paiements par trimestre")
    
    trimestre_headers = ["Trimestre", "Total attendu", "Total perçu", "Solde", "Taux recouvrement"]
    for col, header in enumerate(trimestre_headers, start=1):
        cell = ws_trimestres.cell(row=1, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_alignment
        cell.border = border
    
    for trimestre in [1, 2, 3]:
        frais_trim = frais_base.filter(trimestre=trimestre)
        att = frais_trim.aggregate(total=Sum('montant_total'))['total'] or 0
        paiements_trim = paiements_base.filter(frais__trimestre=trimestre)
        perc = paiements_trim.aggregate(total=Sum('montant_paye'))['total'] or 0
        solde = att - perc
        taux = (perc / att * 100) if att > 0 else 0
        
        row = trimestre + 1
        ws_trimestres.cell(row=row, column=1, value=f"{trimestre}er Trimestre" if trimestre == 1 else f"{trimestre}ème Trimestre").border = border
        ws_trimestres.cell(row=row, column=2, value=f"{att:,.0f}").border = border
        ws_trimestres.cell(row=row, column=3, value=f"{perc:,.0f}").border = border
        ws_trimestres.cell(row=row, column=4, value=f"{solde:,.0f}").border = border
        ws_trimestres.cell(row=row, column=5, value=f"{taux:.1f}%").border = border
    
    for col in range(1, len(trimestre_headers) + 1):
        ws_trimestres.column_dimensions[get_column_letter(col)].width = 20
    
    # Créer la réponse HTTP
    response = HttpResponse(content_type='application/vnd.ms-excel')
    response['Content-Disposition'] = f'attachment; filename="statistiques_frais_{annee_active.annee}_{datetime.datetime.now().strftime("%Y%m%d_%H%M")}.xlsx"'
    
    wb.save(response)
    return response


@login_required
def export_statistiques_pdf(request):
    """Export des statistiques en PDF"""
    annee_active = AnneeScolaire.objects.filter(est_active=True).first()
    
    if not annee_active:
        messages.warning(request, "Veuillez d'abord configurer une année scolaire active")
        return redirect('frais_scolaire:configurer_annee')
    
    # Récupérer les mêmes données
    niveau_filter = request.GET.get('niveau', '')
    classe_filter = request.GET.get('classe', '')
    trimestre_filter = request.GET.get('trimestre', '')
    statut_masp_filter = request.GET.get('statut_masp', '')
    
    frais_base = FraisScolaire.objects.filter(annee_scolaire=annee_active)
    paiements_base = Paiement.objects.filter(frais__annee_scolaire=annee_active, statut='valide')
    
    if niveau_filter:
        frais_base = frais_base.filter(eleve__classe__niveau=niveau_filter)
    if classe_filter:
        frais_base = frais_base.filter(
            Q(eleve__classe__classe_maternel=classe_filter) |
            Q(eleve__classe__classe_primaire=classe_filter) |
            Q(eleve__classe__classe_humanite=classe_filter)
        )
    if trimestre_filter and trimestre_filter.isdigit():
        frais_base = frais_base.filter(trimestre=int(trimestre_filter))
    
    total_attendu = frais_base.aggregate(total=Sum('montant_total'))['total'] or 0
    total_percu = paiements_base.aggregate(total=Sum('montant_paye'))['total'] or 0
    
    # Statistiques par trimestre
    stats_trimestres = []
    for trimestre in [1, 2, 3]:
        frais_trim = frais_base.filter(trimestre=trimestre)
        att = frais_trim.aggregate(total=Sum('montant_total'))['total'] or 0
        perc = paiements_base.filter(frais__trimestre=trimestre).aggregate(total=Sum('montant_paye'))['total'] or 0
        stats_trimestres.append({
            'trimestre': trimestre,
            'libelle': f"{trimestre}er Trimestre" if trimestre == 1 else f"{trimestre}ème Trimestre",
            'total_attendu': att,
            'total_percu': perc,
            'solde': att - perc,
            'taux': (perc / att * 100) if att > 0 else 0,
        })
    
    # Données des élèves
    eleves_data = []
    eleves = Eleve.objects.all()
    if niveau_filter:
        eleves = eleves.filter(classe__niveau=niveau_filter)
    if classe_filter:
        eleves = eleves.filter(
            Q(classe__classe_maternel=classe_filter) |
            Q(classe__classe_primaire=classe_filter) |
            Q(classe__classe_humanite=classe_filter)
        )
    if statut_masp_filter == 'masp':
        eleves = eleves.filter(est_masp=True)
    elif statut_masp_filter == 'non_masp':
        eleves = eleves.filter(est_masp=False)
    
    for eleve in eleves[:50]:  # Limiter à 50 élèves pour le PDF
        total_a_payer = frais_base.filter(eleve=eleve).aggregate(total=Sum('montant_total'))['total'] or 0
        total_paye = paiements_base.filter(eleve=eleve).aggregate(total=Sum('montant_paye'))['total'] or 0
        eleves_data.append({
            'eleve': eleve,
            'total_a_payer': total_a_payer,
            'total_paye': total_paye,
            'solde': total_a_payer - total_paye,
        })
    
    context = {
        'annee_active': annee_active,
        'total_attendu': total_attendu,
        'total_percu': total_percu,
        'taux_recouvrement': (total_percu / total_attendu * 100) if total_attendu > 0 else 0,
        'stats_trimestres': stats_trimestres,
        'eleves_data': eleves_data,
        'date_generation': datetime.datetime.now(),
        'niveau_filter': niveau_filter,
        'classe_filter': classe_filter,
        'trimestre_filter': trimestre_filter,
        'statut_masp_filter': statut_masp_filter,
    }
    
    template = get_template('frais_scolaire/export_statistiques_pdf.html')
    html = template.render(context)
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="statistiques_frais_{annee_active.annee}_{datetime.datetime.now().strftime("%Y%m%d_%H%M")}.pdf"'
    
    pisa_status = pisa.CreatePDF(html, dest=response)
    
    if pisa_status.err:
        return HttpResponse('Erreur lors de la génération du PDF', status=500)
    
    return response







@login_required
def export_comparaison_masp_excel(request):
    """Export de la comparaison MASP en Excel"""
    annee_active = AnneeScolaire.objects.filter(est_active=True).first()
    
    if not annee_active:
        messages.warning(request, "Veuillez d'abord configurer une année scolaire active")
        return redirect('frais_scolaire:configurer_annee')
    
    # Récupérer les paramètres
    montant_reference = request.GET.get('montant_reference', 0)
    try:
        montant_reference = float(montant_reference)
    except ValueError:
        montant_reference = 0
    
    niveau_filter = request.GET.get('niveau', '')
    classe_filter = request.GET.get('classe', '')
    trimestre_filter = request.GET.get('trimestre', '')
    
    # Récupérer les élèves MASP
    eleves_masp = Eleve.objects.filter(est_masp=True)
    
    if niveau_filter:
        eleves_masp = eleves_masp.filter(classe__niveau=niveau_filter)
    if classe_filter:
        eleves_masp = eleves_masp.filter(
            Q(classe__classe_maternel=classe_filter) |
            Q(classe__classe_primaire=classe_filter) |
            Q(classe__classe_humanite=classe_filter)
        )
    
    # Préparer les données
    resultats = []
    total_attendu_global = 0
    total_paye_global = 0
    nb_en_ordre = 0
    nb_non_en_ordre = 0
    
    for eleve in eleves_masp:
        paiements_eleve = Paiement.objects.filter(
            eleve=eleve,
            frais__annee_scolaire=annee_active,
            statut='valide'
        )
        if trimestre_filter and trimestre_filter.isdigit():
            paiements_eleve = paiements_eleve.filter(frais__trimestre=int(trimestre_filter))
        total_paye = paiements_eleve.aggregate(total=Sum('montant_paye'))['total'] or 0
        
        frais_eleve = FraisScolaire.objects.filter(
            eleve=eleve,
            annee_scolaire=annee_active
        )
        if trimestre_filter and trimestre_filter.isdigit():
            frais_eleve = frais_eleve.filter(trimestre=int(trimestre_filter))
        total_attendu = frais_eleve.aggregate(total=Sum('montant_total'))['total'] or 0
        
        if montant_reference > 0:
            est_en_ordre = total_paye >= montant_reference
            difference = montant_reference - total_paye
        else:
            est_en_ordre = total_paye >= total_attendu
            difference = total_attendu - total_paye
        
        if est_en_ordre:
            nb_en_ordre += 1
        else:
            nb_non_en_ordre += 1
        
        total_attendu_global += total_attendu
        total_paye_global += total_paye
        
        resultats.append({
            'eleve': eleve,
            'total_attendu': total_attendu,
            'total_paye': total_paye,
            'est_en_ordre': est_en_ordre,
            'difference': difference,
            'pourcentage': (total_paye / montant_reference * 100) if montant_reference > 0 else (total_paye / total_attendu * 100) if total_attendu > 0 else 0,
        })
    
    resultats.sort(key=lambda x: x['est_en_ordre'])
    
    # Créer le classeur Excel
    wb = Workbook()
    
    # Styles
    header_font = Font(bold=True, color="FFFFFF", size=11)
    header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    header_alignment = Alignment(horizontal="center", vertical="center")
    success_fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
    danger_fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
    border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    
    # Feuille 1: Résumé
    ws_resume = wb.active
    ws_resume.title = "Résumé MASP"
    
    ws_resume['A1'] = f"CONTRÔLE MASP - {annee_active.annee}"
    ws_resume['A1'].font = Font(bold=True, size=14)
    ws_resume.merge_cells('A1:F1')
    
    ws_resume['A3'] = "Paramètres"
    ws_resume['A3'].font = Font(bold=True, size=12)
    ws_resume['A4'] = "Montant de référence:"
    ws_resume['B4'] = f"{montant_reference:,.0f} FC" if montant_reference > 0 else "Non défini"
    ws_resume['A5'] = "Année scolaire:"
    ws_resume['B5'] = annee_active.annee
    ws_resume['A6'] = "Date génération:"
    ws_resume['B6'] = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
    if niveau_filter:
        ws_resume['A7'] = "Niveau:"
        ws_resume['B7'] = dict(Classe.NIVEAU_CHOICES).get(niveau_filter, niveau_filter)
    if classe_filter:
        ws_resume['A8'] = "Classe:"
        ws_resume['B8'] = classe_filter
    if trimestre_filter:
        ws_resume['A9'] = "Trimestre:"
        ws_resume['B9'] = f"{trimestre_filter}er" if trimestre_filter == '1' else f"{trimestre_filter}ème"
    
    ws_resume['A11'] = "RÉSULTATS GLOBAUX"
    ws_resume['A11'].font = Font(bold=True, size=12)
    
    resume_data = [
        ("Total élèves MASP", f"{len(resultats)}"),
        ("En ordre", f"{nb_en_ordre}"),
        ("Non en ordre", f"{nb_non_en_ordre}"),
        ("Taux de conformité", f"{(nb_en_ordre / len(resultats) * 100) if len(resultats) > 0 else 0:.1f}%"),
        ("Total attendu", f"{total_attendu_global:,.0f} FC"),
        ("Total payé", f"{total_paye_global:,.0f} FC"),
        ("Solde global", f"{(total_attendu_global - total_paye_global):,.0f} FC"),
    ]
    
    for i, (label, value) in enumerate(resume_data, start=12):
        ws_resume[f'A{i}'] = label
        ws_resume[f'B{i}'] = value
        ws_resume[f'A{i}'].font = Font(bold=True)
    
    for col in ['A', 'B']:
        ws_resume.column_dimensions[col].width = 25
    
    # Feuille 2: Liste détaillée
    ws_details = wb.create_sheet("Liste détaillée")
    
    headers = ["#", "Matricule", "Nom", "Post-nom", "Prénom", "Classe", "Téléphone", "Total attendu", "Total payé", "Statut", "Différence", "Taux"]
    for col, header in enumerate(headers, start=1):
        cell = ws_details.cell(row=1, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_alignment
        cell.border = border
    
    for idx, item in enumerate(resultats, start=2):
        # Appliquer la couleur selon le statut
        row_color = success_fill if item['est_en_ordre'] else danger_fill
        
        ws_details.cell(row=idx, column=1, value=idx-1).border = border
        ws_details.cell(row=idx, column=1).fill = row_color
        ws_details.cell(row=idx, column=2, value=item['eleve'].matricule).border = border
        ws_details.cell(row=idx, column=2).fill = row_color
        ws_details.cell(row=idx, column=3, value=item['eleve'].nom).border = border
        ws_details.cell(row=idx, column=3).fill = row_color
        ws_details.cell(row=idx, column=4, value=item['eleve'].post_nom).border = border
        ws_details.cell(row=idx, column=4).fill = row_color
        ws_details.cell(row=idx, column=5, value=item['eleve'].prenom).border = border
        ws_details.cell(row=idx, column=5).fill = row_color
        ws_details.cell(row=idx, column=6, value=str(item['eleve'].classe or "-")).border = border
        ws_details.cell(row=idx, column=6).fill = row_color
        ws_details.cell(row=idx, column=7, value=item['eleve'].telephone or "-").border = border
        ws_details.cell(row=idx, column=7).fill = row_color
        ws_details.cell(row=idx, column=8, value=f"{item['total_attendu']:,.0f}").border = border
        ws_details.cell(row=idx, column=8).fill = row_color
        ws_details.cell(row=idx, column=9, value=f"{item['total_paye']:,.0f}").border = border
        ws_details.cell(row=idx, column=9).fill = row_color
        ws_details.cell(row=idx, column=10, value="EN ORDRE" if item['est_en_ordre'] else "NON EN ORDRE").border = border
        ws_details.cell(row=idx, column=10).fill = row_color
        ws_details.cell(row=idx, column=11, value=f"{item['difference']:,.0f}").border = border
        ws_details.cell(row=idx, column=11).fill = row_color
        ws_details.cell(row=idx, column=12, value=f"{item['pourcentage']:.1f}%").border = border
        ws_details.cell(row=idx, column=12).fill = row_color
    
    # Ajuster les largeurs
    for col in range(1, len(headers) + 1):
        ws_details.column_dimensions[get_column_letter(col)].width = 18
    
    # Créer la réponse
    response = HttpResponse(content_type='application/vnd.ms-excel')
    response['Content-Disposition'] = f'attachment; filename="comparaison_masp_{annee_active.annee}_{datetime.datetime.now().strftime("%Y%m%d_%H%M")}.xlsx"'
    
    wb.save(response)
    return response

##################################################################
##################################################################
##################################################################
##################################################################
##################################################################
##################################################################
##################################################################
##################################################################
##################################################################
##################################################################
@login_required
def export_comparaison_masp_pdf(request):
    """Export de la comparaison MASP en PDF"""
    annee_active = AnneeScolaire.objects.filter(est_active=True).first()
    
    if not annee_active:
        messages.warning(request, "Veuillez d'abord configurer une année scolaire active")
        return redirect('frais_scolaire:configurer_annee')
    
    # Récupérer les paramètres
    montant_reference = request.GET.get('montant_reference', 0)
    try:
        montant_reference = float(montant_reference)
    except ValueError:
        montant_reference = 0
    
    niveau_filter = request.GET.get('niveau', '')
    classe_filter = request.GET.get('classe', '')
    trimestre_filter = request.GET.get('trimestre', '')
    
    # Récupérer les élèves MASP
    eleves_masp = Eleve.objects.filter(est_masp=True)
    
    if niveau_filter:
        eleves_masp = eleves_masp.filter(classe__niveau=niveau_filter)
    if classe_filter:
        eleves_masp = eleves_masp.filter(
            Q(classe__classe_maternel=classe_filter) |
            Q(classe__classe_primaire=classe_filter) |
            Q(classe__classe_humanite=classe_filter)
        )
    
    # Préparer les données
    resultats = []
    total_attendu_global = 0
    total_paye_global = 0
    nb_en_ordre = 0
    nb_non_en_ordre = 0
    
    for eleve in eleves_masp:
        paiements_eleve = Paiement.objects.filter(
            eleve=eleve,
            frais__annee_scolaire=annee_active,
            statut='valide'
        )
        if trimestre_filter and trimestre_filter.isdigit():
            paiements_eleve = paiements_eleve.filter(frais__trimestre=int(trimestre_filter))
        total_paye = paiements_eleve.aggregate(total=Sum('montant_paye'))['total'] or 0
        
        frais_eleve = FraisScolaire.objects.filter(
            eleve=eleve,
            annee_scolaire=annee_active
        )
        if trimestre_filter and trimestre_filter.isdigit():
            frais_eleve = frais_eleve.filter(trimestre=int(trimestre_filter))
        total_attendu = frais_eleve.aggregate(total=Sum('montant_total'))['total'] or 0
        
        if montant_reference > 0:
            est_en_ordre = total_paye >= montant_reference
            difference = montant_reference - total_paye
        else:
            est_en_ordre = total_paye >= total_attendu
            difference = total_attendu - total_paye
        
        if est_en_ordre:
            nb_en_ordre += 1
        else:
            nb_non_en_ordre += 1
        
        total_attendu_global += total_attendu
        total_paye_global += total_paye
        
        resultats.append({
            'eleve': eleve,
            'total_attendu': total_attendu,
            'total_paye': total_paye,
            'est_en_ordre': est_en_ordre,
            'difference': difference,
            'pourcentage': (total_paye / montant_reference * 100) if montant_reference > 0 else (total_paye / total_attendu * 100) if total_attendu > 0 else 0,
        })
    
    resultats.sort(key=lambda x: x['est_en_ordre'])
    
    context = {
        'annee_active': annee_active,
        'montant_reference': montant_reference,
        'resultats': resultats,
        'total_attendu_global': total_attendu_global,
        'total_paye_global': total_paye_global,
        'total_eleves': len(resultats),
        'nb_en_ordre': nb_en_ordre,
        'nb_non_en_ordre': nb_non_en_ordre,
        'taux_en_ordre': (nb_en_ordre / len(resultats) * 100) if len(resultats) > 0 else 0,
        'niveau_filter': niveau_filter,
        'classe_filter': classe_filter,
        'trimestre_filter': trimestre_filter,
        'date_generation': datetime.datetime.now(),
    }
    
    template = get_template('frais_scolaire/export_comparaison_masp_pdf.html')
    html = template.render(context)
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="comparaison_masp_{annee_active.annee}_{datetime.datetime.now().strftime("%Y%m%d_%H%M")}.pdf"'
    
    pisa_status = pisa.CreatePDF(html, dest=response)
    
    if pisa_status.err:
        return HttpResponse('Erreur lors de la génération du PDF', status=500)
    
    return response