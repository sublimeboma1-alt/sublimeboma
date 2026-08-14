import json
from collections import defaultdict
from decimal import Decimal
from io import BytesIO
from xml.sax.saxutils import escape

import pandas as pd

from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Prefetch, Q, Sum
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods

from .models import AnneeScolaire, FraisScolaire, ModePaiement, Paiement, TarifFrais, TypeFrais, Trimestre
from sub_app.eleves.models import Classe, Eleve, NiveauClasse, Sexe, StatutEleve
from .serializers import clean_paiement_payload, serialize_dossier, serialize_eleve_detail, serialize_paiement


def export_identity():
    from sub_app.noyau.models import IdentiteEtablissement
    return IdentiteEtablissement.active()


def export_filter_summary(request):
    """Retourne un libelle humain des filtres, imprime dans chaque document."""
    values = []
    year_id = request.GET.get('annee_scolaire', '')
    niveau_code = request.GET.get('niveau', '')
    classe_id = request.GET.get('classe_id', '')
    year = (AnneeScolaire.objects.filter(id=year_id).first() if year_id else None) or AnneeScolaire.objects.filter(est_active=True).first()
    if year:
        values.append(f'Annee scolaire : {year.annee}')
    niveau = NiveauClasse.objects.filter(code=niveau_code).first() if niveau_code else None
    classe = Classe.objects.filter(id=classe_id).first() if classe_id else None
    statut = request.GET.get('statut', '')
    if niveau:
        values.append(f'Niveau : {niveau}')
    if classe:
        values.append(f'Classe : {classe}')
    if request.GET.get('scope', 'inscriptions') == 'frais':
        trimestre_value = request.GET.get('trimestre', '')
        type_frais_code = request.GET.get('type_frais', '')
        trimestre = Trimestre.objects.filter(numero=trimestre_value).first() if trimestre_value else None
        type_frais = TypeFrais.objects.filter(code=type_frais_code).first() if type_frais_code else None
        if trimestre:
            values.append(f'Trimestre : {trimestre}')
        if type_frais:
            values.append(f'Type de frais : {type_frais}')
        if statut:
            values.append(f'Statut paiement : {statut}')
    else:
        sexe_code = request.GET.get('sexe', '')
        sexe = Sexe.objects.filter(code=sexe_code).first() if sexe_code else None
        eleve_statut = StatutEleve.objects.filter(code=statut).first()
        if sexe:
            values.append(f'Sexe : {sexe}')
        if eleve_statut:
            values.append(f'Statut eleve : {eleve_statut}')
    if request.GET.get('date_debut', ''):
        values.append(f'Du : {request.GET["date_debut"]}')
    if request.GET.get('date_fin', ''):
        values.append(f'Au : {request.GET["date_fin"]}')
    if request.GET.get('search', ''):
        values.append(f'Recherche : {request.GET["search"]}')
    return ' | '.join(values) or 'Aucun filtre specifique'


def export_filters(queryset, request, prefix='eleve', year_lookup=None):
    """Applique les filtres communs aux exports sans charger les donnees en memoire."""
    year_id = request.GET.get('annee_scolaire', '').strip()
    classe_id = request.GET.get('classe_id', '').strip()
    niveau = request.GET.get('niveau', '').strip()
    search = request.GET.get('search', '').strip()
    date_start = request.GET.get('date_debut', '').strip()
    date_end = request.GET.get('date_fin', '').strip()
    relation = f'{prefix}__' if prefix else ''
    selected_year = AnneeScolaire.objects.filter(id=year_id).first() if year_id else AnneeScolaire.objects.filter(est_active=True).first()
    if selected_year:
        queryset = queryset.filter(**{year_lookup or f'{relation}annee_scolaire_id': selected_year.id})
    if classe_id:
        queryset = queryset.filter(**{f'{relation}classe_id': classe_id})
    if niveau:
        queryset = queryset.filter(**{f'{relation}classe__niveau_id': niveau})
    if search:
        lookup = Q(**{f'{relation}matricule__icontains': search}) | Q(**{f'{relation}nom__icontains': search}) | Q(**{f'{relation}prenom__icontains': search})
        queryset = queryset.filter(lookup)
    if date_start:
        field = 'date_inscription' if prefix == '' else 'date_paiement'
        queryset = queryset.filter(**{f'{field}__gte': date_start})
    if date_end:
        field = 'date_inscription' if prefix == '' else 'date_paiement'
        queryset = queryset.filter(**{f'{field}__lte': date_end})
    return queryset


def export_dataframe(request):
    scope = request.GET.get('scope', 'inscriptions')
    if scope == 'frais':
        rows = export_filters(
            Paiement.objects.select_related('eleve__classe__niveau', 'frais__annee_scolaire', 'frais__trimestre', 'frais__type_frais', 'mode_paiement', 'statut'), request, year_lookup='frais__annee_scolaire_id'
        )
        status = request.GET.get('statut', '').strip()
        trimestre = request.GET.get('trimestre', '').strip()
        type_frais = request.GET.get('type_frais', '').strip()
        if status:
            rows = rows.filter(statut_id=status)
        if trimestre:
            rows = rows.filter(frais__trimestre_id=trimestre)
        if type_frais:
            rows = rows.filter(frais__type_frais_id=type_frais)
        data = [{
            'Recu': row.reference, 'Date paiement': row.date_paiement, 'Matricule': row.eleve.matricule,
            'Eleve': f'{row.eleve.nom} {row.eleve.post_nom} {row.eleve.prenom}'.strip(),
            'Classe': str(row.eleve.classe or ''), 'Niveau': str(row.eleve.classe.niveau) if row.eleve.classe else '',
            'Annee scolaire': str(row.frais.annee_scolaire), 'Trimestre': str(row.frais.trimestre),
            'Type de frais': str(row.frais.type_frais), 'Montant paye': float(row.montant_paye),
            'Mode de paiement': str(row.mode_paiement), 'Statut': str(row.statut), 'Observation': row.description or '',
        } for row in rows]
        return pd.DataFrame(data), 'rapport_frais', 'Rapport des paiements et frais'

    rows = export_filters(
        Eleve.objects.select_related('annee_scolaire', 'classe__niveau', 'sexe', 'statut'), request, prefix=''
    )
    statut = request.GET.get('statut', '').strip()
    sexe = request.GET.get('sexe', '').strip()
    if statut:
        rows = rows.filter(statut_id=statut)
    if sexe:
        rows = rows.filter(sexe_id=sexe)
    data = [{
        'Matricule': row.matricule, 'Nom': row.nom, 'Post-nom': row.post_nom, 'Prenom': row.prenom,
        'Sexe': str(row.sexe), 'Date naissance': row.date_naissance, 'Classe': str(row.classe or ''),
        'Niveau': str(row.classe.niveau) if row.classe else '', 'Annee scolaire': str(row.annee_scolaire or ''),
        'Statut': str(row.statut), 'MASP': 'Oui' if row.est_masp else 'Non', 'Telephone': row.telephone,
        'Email': row.email, "Date d'inscription": row.date_inscription,
    } for row in rows]
    return pd.DataFrame(data), 'inscriptions', 'Registre des inscriptions'


@login_required
@require_http_methods(['GET'])
def export_data(request):
    """Genere un XLSX ou PDF a partir des filtres recus depuis l'interface."""
    dataframe, filename, title = export_dataframe(request)
    identity = export_identity()
    filter_summary = export_filter_summary(request)
    export_format = request.GET.get('format', 'xlsx').lower()
    stamp = timezone.localtime().strftime('%Y%m%d_%H%M%S')
    if export_format == 'xlsx':
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            # Les six premieres lignes constituent l'en-tete officiel du document.
            dataframe.to_excel(writer, sheet_name='Donnees', index=False, startrow=6)
            sheet = writer.sheets['Donnees']
            last_column = max(len(dataframe.columns) - 1, 0)
            title_format = writer.book.add_format({'bold': True, 'font_size': 16, 'font_color': '#14213D', 'align': 'center', 'valign': 'vcenter'})
            subtitle_format = writer.book.add_format({'bold': True, 'font_size': 11, 'font_color': '#0C5A5B', 'align': 'center', 'valign': 'vcenter'})
            details_format = writer.book.add_format({'font_size': 9, 'font_color': '#536271', 'align': 'center', 'valign': 'vcenter'})
            report_format = writer.book.add_format({'bold': True, 'font_size': 13, 'font_color': '#14213D', 'align': 'center', 'valign': 'vcenter'})
            contact = ' | '.join(value for value in [getattr(identity, 'adresse', ''), getattr(identity, 'telephone', ''), getattr(identity, 'email', '')] if value)
            sheet.merge_range(0, 0, 0, last_column, getattr(identity, 'nom', '') or 'Etablissement', title_format)
            sheet.merge_range(1, 0, 1, last_column, getattr(identity, 'espace', '') or getattr(identity, 'sigle', ''), subtitle_format)
            sheet.merge_range(2, 0, 2, last_column, contact, details_format)
            sheet.merge_range(3, 0, 3, last_column, title, report_format)
            sheet.merge_range(4, 0, 4, last_column, f'Genere le {timezone.localtime().strftime("%d/%m/%Y a %H:%M")}', details_format)
            sheet.merge_range(5, 0, 5, last_column, f'Filtres : {filter_summary}', details_format)
            header_format = writer.book.add_format({'bold': True, 'bg_color': '#0C5A5B', 'font_color': '#FFFFFF', 'border': 0})
            for index, column in enumerate(dataframe.columns):
                width = max(len(str(column)), *(dataframe[column].fillna('').astype(str).map(len).tolist() or [0])) + 2
                sheet.set_column(index, index, min(width, 32))
                sheet.write(6, index, column, header_format)
            sheet.freeze_panes(7, 0)
        response = HttpResponse(output.getvalue(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename="{filename}_{stamp}.xlsx"'
        return response
    if export_format != 'pdf':
        return JsonResponse({'detail': 'Format non pris en charge.'}, status=400)

    from reportlab.lib import colors
    from reportlab.lib.pagesizes import landscape, A4
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    output = BytesIO()
    document = SimpleDocTemplate(output, pagesize=landscape(A4), leftMargin=22, rightMargin=22, topMargin=24, bottomMargin=24)
    styles = getSampleStyleSheet()
    centered_title = ParagraphStyle('export-title', parent=styles['Title'], alignment=TA_CENTER, textColor=colors.HexColor('#14213D'), spaceAfter=5)
    centered_subtitle = ParagraphStyle('export-subtitle', parent=styles['Normal'], alignment=TA_CENTER, textColor=colors.HexColor('#0C5A5B'), fontName='Helvetica-Bold', spaceAfter=3)
    centered_details = ParagraphStyle('export-details', parent=styles['Normal'], alignment=TA_CENTER, textColor=colors.HexColor('#536271'), fontSize=8, spaceAfter=3)
    table_data = [list(dataframe.columns)] + dataframe.fillna('').astype(str).values.tolist()
    if len(table_data) == 1:
        table_data.append(['Aucune donnee pour ces filtres.'] + [''] * max(0, len(dataframe.columns) - 1))
    table = Table(table_data, repeatRows=1)
    table.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0C5A5B')), ('TEXTCOLOR', (0, 0), (-1, 0), colors.white), ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'), ('FONTSIZE', (0, 0), (-1, -1), 7), ('GRID', (0, 0), (-1, -1), .25, colors.HexColor('#D9E3E7')), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F5F9F9')])]))
    contact = ' | '.join(value for value in [getattr(identity, 'adresse', ''), getattr(identity, 'telephone', ''), getattr(identity, 'email', '')] if value)
    document.build([
        Paragraph(escape(getattr(identity, 'nom', '') or 'Etablissement'), centered_title),
        Paragraph(escape(getattr(identity, 'espace', '') or getattr(identity, 'sigle', '')), centered_subtitle),
        Paragraph(escape(contact), centered_details),
        Paragraph(escape(title), centered_subtitle),
        Paragraph(f'Genere le {timezone.localtime().strftime("%d/%m/%Y a %H:%M")}', centered_details),
        Paragraph(f'Filtres : {escape(filter_summary)}', centered_details),
        Spacer(1, 12), table,
    ])
    response = HttpResponse(output.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}_{stamp}.pdf"'
    return response


def payload(request):
    try:
        return json.loads(request.body.decode('utf-8') or '{}')
    except json.JSONDecodeError:
        raise ValidationError({'detail': 'Donnees JSON invalides.'})


def selected_year(request):
    value = request.GET.get('annee_scolaire', '')
    if value:
        return AnneeScolaire.objects.filter(id=value).first()
    return AnneeScolaire.objects.filter(est_active=True).first()


def dossiers_queryset(request):
    year = selected_year(request)
    frais = FraisScolaire.objects.select_related('eleve__classe').prefetch_related('paiements')
    if year:
        frais = frais.filter(annee_scolaire=year)
    return frais, year


def grouped_dossiers(request):
    frais, year = dossiers_queryset(request)
    groups = defaultdict(list)
    for item in frais:
        groups[item.eleve].append(item)
    return [serialize_dossier(eleve, items) for eleve, items in groups.items()], year


def financial_filters(queryset, request, relation='eleve__', year_key=None):
    """Filtres partages par la vue statistiques et ses paiements detailles."""
    year = selected_year(request)
    if year:
        queryset = queryset.filter(**{year_key or ('annee_scolaire' if relation == '' else f'{relation}annee_scolaire'): year})
    niveau = request.GET.get('niveau', '')
    classe_id = request.GET.get('classe_id', '')
    if niveau:
        queryset = queryset.filter(**{f'{relation}classe__niveau_id': niveau})
    if classe_id:
        queryset = queryset.filter(**{f'{relation}classe_id': classe_id})
    return queryset


@login_required
@require_http_methods(['GET'])
def statistiques(request):
    """Tableau de bord financier filtre, sans action d'enregistrement de paiement."""
    fees = financial_filters(FraisScolaire.objects.select_related('eleve__classe', 'trimestre', 'type_frais'), request, year_key='annee_scolaire')
    trimestre = request.GET.get('trimestre', '')
    type_frais = request.GET.get('type_frais', '')
    if trimestre:
        fees = fees.filter(trimestre_id=trimestre)
    if type_frais:
        fees = fees.filter(type_frais_id=type_frais)
    expected = fees.aggregate(total=Sum('montant_total'))['total'] or Decimal('0')
    payments = Paiement.objects.select_related('eleve', 'frais__type_frais', 'frais__trimestre', 'mode_paiement').filter(statut_id='valide', frais__in=fees).order_by('-date_paiement', '-id')
    date_debut = request.GET.get('date_debut', '')
    date_fin = request.GET.get('date_fin', '')
    if date_debut:
        payments = payments.filter(date_paiement__gte=date_debut)
    if date_fin:
        payments = payments.filter(date_paiement__lte=date_fin)
    collected = payments.aggregate(total=Sum('montant_paye'))['total'] or Decimal('0')
    today = timezone.localdate()
    today_payments = payments.filter(date_paiement=today)
    by_type = []
    for item in TypeFrais.objects.filter(est_actif=True):
        amount = payments.filter(frais__type_frais_id=item.code).aggregate(total=Sum('montant_paye'))['total'] or Decimal('0')
        if amount:
            by_type.append({'label': str(item), 'amount': float(amount), 'percent': round(float(amount / collected * 100), 1) if collected else 0})
    by_trimester = []
    for item in Trimestre.objects.filter(est_actif=True):
        amount = payments.filter(frais__trimestre_id=item.numero).aggregate(total=Sum('montant_paye'))['total'] or Decimal('0')
        if amount:
            by_trimester.append({'label': str(item), 'amount': float(amount), 'percent': round(float(amount / collected * 100), 1) if collected else 0})
    return JsonResponse({
        'annee_scolaire': {'id': selected_year(request).id, 'annee': selected_year(request).annee} if selected_year(request) else None,
        'expected': float(expected), 'collected': float(collected), 'balance': float(expected - collected),
        'recovery_rate': round(float(collected / expected * 100), 1) if expected else 0,
        'payment_count': payments.count(), 'today_count': today_payments.count(), 'today_amount': float(today_payments.aggregate(total=Sum('montant_paye'))['total'] or Decimal('0')),
        'by_type': by_type, 'by_trimester': by_trimester,
        'payments': [serialize_paiement(item) for item in payments[:100]],
    })


@login_required
@require_http_methods(['GET'])
def references(request):
    active = AnneeScolaire.objects.filter(est_active=True).first()
    classes = []
    for item in Classe.objects.select_related('niveau', 'classe_maternel', 'classe_primaire', 'classe_humanite', 'section').all():
        classes.append({
            'id': item.id,
            'libelle': str(item),
            'niveau': item.niveau_id,
            'classe': str(item.classe_maternel or item.classe_primaire or item.classe_humanite or ''),
            'section': str(item.section) if item.section else '',
        })
    return JsonResponse({'annees_scolaires': [{'id': item.id, 'annee': item.annee, 'est_active': item.est_active} for item in AnneeScolaire.objects.all()], 'annee_active_id': active.id if active else None, 'modes_paiement': [{'code': item.code, 'libelle': item.libelle} for item in ModePaiement.objects.filter(est_actif=True)], 'niveaux': [{'code': item.code, 'libelle': item.libelle} for item in NiveauClasse.objects.filter(est_actif=True)], 'types_frais': [{'code': item.code, 'libelle': item.libelle} for item in TypeFrais.objects.filter(est_actif=True)], 'trimestres': [{'code': item.numero, 'libelle': item.libelle} for item in Trimestre.objects.filter(est_actif=True)], 'classes': classes})


@login_required
@require_http_methods(['GET'])
def dashboard(request):
    dossiers, year = grouped_dossiers(request)
    expected = sum((Decimal(str(item['total'])) for item in dossiers), Decimal('0'))
    paid = sum((Decimal(str(item['paid'])) for item in dossiers), Decimal('0'))
    return JsonResponse({'annee_scolaire': {'id': year.id, 'annee': year.annee} if year else None, 'expected': float(expected), 'paid': float(paid), 'dossiers_paid': sum(item['balance'] <= 0 for item in dossiers), 'dossiers_partial': sum(item['paid'] > 0 and item['balance'] > 0 for item in dossiers), 'dossiers_unpaid': sum(item['paid'] == 0 for item in dossiers), 'masp': sum(item['masp'] for item in dossiers), 'results': dossiers})


@login_required
@require_http_methods(['GET'])
def dossiers(request):
    results, year = grouped_dossiers(request)
    search = request.GET.get('search', '').lower().strip()
    status = request.GET.get('status', '')
    if search:
        results = [item for item in results if search in f"{item['name']} {item['matricule']} {item['classe']}".lower()]
    if status:
        results = [item for item in results if ('paid' if item['balance'] <= 0 else 'late' if item['paid'] == 0 else 'partial') == status]
    return JsonResponse({'annee_scolaire': {'id': year.id, 'annee': year.annee} if year else None, 'results': results})


@login_required
@require_http_methods(['GET'])
def eleve_detail(request, eleve_id):
    eleve = Eleve.objects.select_related('classe', 'classe__niveau', 'classe__section', 'annee_scolaire').filter(id=eleve_id).first()
    if not eleve:
        return JsonResponse({'detail': 'Eleve introuvable.'}, status=404)
    frais = FraisScolaire.objects.select_related('trimestre', 'type_frais').prefetch_related('paiements__mode_paiement', 'paiements__agent').filter(eleve=eleve)
    return JsonResponse(serialize_eleve_detail(eleve, list(frais)))


@login_required
@csrf_protect
@require_http_methods(['GET', 'POST'])
def paiements(request):
    if request.method == 'POST':
        try:
            with transaction.atomic():
                paiement = clean_paiement_payload(payload(request), request.user)
                paiement.full_clean()
                paiement.save()
        except ValidationError as error:
            return JsonResponse({'errors': error.message_dict}, status=400)
        return JsonResponse(serialize_paiement(paiement), status=201)
    queryset = Paiement.objects.select_related('eleve', 'frais', 'mode_paiement').order_by('-date_paiement', '-id')
    year = selected_year(request)
    if year:
        queryset = queryset.filter(frais__annee_scolaire=year)
    return JsonResponse({'results': [serialize_paiement(item) for item in queryset]})


@login_required
@csrf_protect
@require_http_methods(['GET', 'POST'])
def annees(request):
    if request.method == 'POST':
        try:
            data = payload(request)
            with transaction.atomic():
                if data.get('est_active'):
                    AnneeScolaire.objects.update(est_active=False)
                item = AnneeScolaire.objects.create(annee=data['annee'], date_debut=data['date_debut'], date_fin=data['date_fin'], est_active=bool(data.get('est_active')))
        except (KeyError, ValidationError) as error:
            return JsonResponse({'detail': str(error)}, status=400)
        return JsonResponse({'id': item.id, 'annee': item.annee, 'est_active': item.est_active}, status=201)
    return JsonResponse({'results': [{'id': item.id, 'annee': item.annee, 'date_debut': item.date_debut.isoformat(), 'date_fin': item.date_fin.isoformat(), 'est_active': item.est_active} for item in AnneeScolaire.objects.all()]})


@login_required
@csrf_protect
@require_http_methods(['GET', 'POST'])
def tarifs(request):
    if request.method == 'POST':
        try:
            data = payload(request)
            classe_id = data.get('classe_id')
            if classe_id:
                classe = Classe.objects.select_related('section', 'classe_maternel', 'classe_primaire', 'classe_humanite').filter(id=classe_id).first()
                if not classe:
                    return JsonResponse({'detail': 'Classe introuvable.'}, status=400)
                item = TarifFrais.objects.create(
                    annee_scolaire_id=data['annee_scolaire_id'],
                    niveau_id=classe.niveau_id,
                    trimestre_id=data['trimestre'],
                    type_frais_id=data['type_frais'],
                    montant=data['montant'],
                    classe_maternel_id=classe.classe_maternel_id,
                    classe_primaire=classe.classe_primaire.code if classe.classe_primaire else None,
                    classe_humanite=classe.classe_humanite.code if classe.classe_humanite else None,
                    option_humanite=classe.section.code if classe.section else None,
                )
            else:
                item = TarifFrais.objects.create(
                    annee_scolaire_id=data['annee_scolaire_id'],
                    niveau_id=data['niveau'],
                    trimestre_id=data['trimestre'],
                    type_frais_id=data['type_frais'],
                    montant=data['montant'],
                    classe_maternel_id=data.get('classe_maternel') or None,
                    classe_primaire=data.get('classe_primaire') or None,
                    classe_humanite=data.get('classe_humanite') or None,
                    option_humanite=data.get('option_humanite') or None,
                )
        except Exception as error:
            return JsonResponse({'detail': str(error)}, status=400)
        return JsonResponse({'id': item.id}, status=201)
    year = selected_year(request)
    rows = TarifFrais.objects.select_related('niveau', 'trimestre', 'type_frais').filter(annee_scolaire=year) if year else TarifFrais.objects.none()
    return JsonResponse({'results': [{'id': item.id, 'niveau': str(item.niveau), 'classe': str(item.classe_maternel or item.classe_primaire or item.classe_humanite or ''), 'option': item.option_humanite or '', 'trimestre': str(item.trimestre), 'type_frais': str(item.type_frais), 'montant': float(item.montant)} for item in rows]})


@login_required
@csrf_protect
@require_http_methods(['POST'])
def appliquer_tarif(request):
    data = payload(request)
    tariff = TarifFrais.objects.select_related('annee_scolaire').get(id=data.get('tarif_id'))
    eleves = Eleve.objects.filter(annee_scolaire=tariff.annee_scolaire, classe__niveau_id=tariff.niveau_id)
    if tariff.classe_maternel_id: eleves = eleves.filter(classe__classe_maternel_id=tariff.classe_maternel_id)
    if tariff.classe_primaire: eleves = eleves.filter(classe__classe_primaire__code=tariff.classe_primaire)
    if tariff.classe_humanite: eleves = eleves.filter(classe__classe_humanite__code=tariff.classe_humanite)
    if tariff.option_humanite: eleves = eleves.filter(classe__section__code=tariff.option_humanite)
    created = 0
    with transaction.atomic():
        for eleve in eleves:
            _, was_created = FraisScolaire.objects.get_or_create(eleve=eleve, annee_scolaire=tariff.annee_scolaire, trimestre=tariff.trimestre, type_frais=tariff.type_frais, defaults={'montant_total': tariff.montant})
            created += was_created
    return JsonResponse({'created': created, 'eligible': eleves.count()})
