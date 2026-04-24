# admin.py
import openpyxl # Importation d'openpyxl pour le formatage avancé des rapports Excel    
from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.urls import path, reverse
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from django.utils import timezone
from django.db.models import Count, Q, Sum, Avg, F
from django.contrib import messages
from django.core.paginator import Paginator
from django.conf import settings
import datetime
import json
import pandas as pd
import numpy as np
from io import BytesIO, StringIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Spacer, Paragraph, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.piecharts import Pie
import xlsxwriter
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.chart import BarChart, Reference, PieChart
from openpyxl.utils import get_column_letter
import csv
from .models import Classe, Eleve

class ClasseAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'niveau', 'get_classe_complete', 'section', 'total_eleves']
    list_filter = ['niveau']
    search_fields = ['classe_primaire', 'classe_humanite', 'section']
    list_per_page = 20
    
    fieldsets = (
        ('Informations de la classe', {
            'fields': ('niveau',)
        }),
        ('Niveau Primaire', {
            'fields': ('classe_primaire',),
            'classes': ('collapse',),
        }),
        ('Niveau Humanité', {
            'fields': ('classe_humanite', 'section'),
            'classes': ('collapse',),
        }),
    )
    
    def get_classe_complete(self, obj):
        if obj.niveau == 'primaire' and obj.classe_primaire:
            dict_primaire = dict(obj.CLASSE_PRIMAIRE_CHOICES)
            return dict_primaire.get(obj.classe_primaire, obj.classe_primaire)
        elif obj.niveau == 'humanite' and obj.classe_humanite:
            dict_humanite = dict(obj.CLASSE_HUMANITE_CHOICES)
            return dict_humanite.get(obj.classe_humanite, obj.classe_humanite)
        return "-"
    get_classe_complete.short_description = "Classe"
    
    def total_eleves(self, obj):
        count = Eleve.objects.filter(classe=obj, statut='actif').count()
        return format_html('<span style="color: #4CAF50; font-weight: bold;">{}</span>', count)
    total_eleves.short_description = "Effectif actif"

class EleveAdmin(admin.ModelAdmin):
    list_display = ['matricule', 'nom_complet', 'classe', 'sexe', 'age', 'statut', 'date_inscription', 'photo_preview', 'actions_buttons']
    list_filter = ['statut', 'sexe', 'classe__niveau', 'classe', 'date_inscription']
    search_fields = ['matricule', 'nom', 'post_nom', 'prenom', 'telephone', 'email']
    list_per_page = 50
    date_hierarchy = 'date_inscription'
    list_select_related = ['classe', 'created_by']
    
    fieldsets = (
        ('Informations personnelles', {
            'fields': ('nom', 'post_nom', 'prenom', 'date_naissance', 'sexe', 'photo')
        }),
        ('Coordonnées', {
            'fields': ('adresse', 'telephone', 'email')
        }),
        ('Informations académiques', {
            'fields': ('classe', 'date_inscription', 'statut')
        }),
        ('Informations système', {
            'fields': ('matricule', 'created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    readonly_fields = ['matricule', 'created_at', 'updated_at']
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            # Rapports avancés
            path('rapports/', self.rapports_dashboard, name='rapports_dashboard'),
            path('rapport-pdf/', self.rapport_eleves_pdf, name='rapport_eleves_pdf'),
            path('rapport-excel-pandas/', self.rapport_excel_pandas, name='rapport_excel_pandas'),
            path('rapport-excel-xlsxwriter/', self.rapport_excel_xlsxwriter, name='rapport_excel_xlsxwriter'),
            path('rapport-csv/', self.rapport_csv, name='rapport_csv'),
            
            # Rapports analytiques
            path('analyse-statistique/', self.analyse_statistique, name='analyse_statistique'),
            path('dashboard-analytics/', self.dashboard_analytics, name='dashboard_analytics'),
            path('rapport-detaille-pdf/', self.rapport_detaille_pdf, name='rapport_detaille_pdf'),
            
            # Bulletins et documents individuels
            path('bulletin-pdf/<int:eleve_id>/', self.bulletin_pdf_view, name='bulletin_pdf'),
            path('certificat-scolarite/<int:eleve_id>/', self.certificat_scolarite, name='certificat_scolarite'),
            path('carte-etudiant/<int:eleve_id>/', self.carte_etudiant, name='carte_etudiant'),
            
            # Actions batch
            path('impression-masse/', self.impression_masse, name='impression_masse'),
            
            # API pour pandas
            path('api/eleves-data/', self.api_eleves_data, name='api_eleves_data'),
        ]
        return custom_urls + urls
    
    # ==================== MÉTHODES D'AFFICHAGE ====================
    
    def nom_complet(self, obj):
        return f"{obj.nom} {obj.post_nom} {obj.prenom}"
    nom_complet.short_description = "Nom complet"
    nom_complet.admin_order_field = 'nom'
    
    def age(self, obj):
        if obj.date_naissance:
            today = timezone.now().date()
            age = today.year - obj.date_naissance.year
            if today.month < obj.date_naissance.month or (today.month == obj.date_naissance.month and today.day < obj.date_naissance.day):
                age -= 1
            return format_html('<span style="font-weight: bold;">{} ans</span>', age)
        return "-"
    age.short_description = "Âge"
    
    def photo_preview(self, obj):
        if obj.photo:
            return format_html('<img src="{}" width="50" height="50" style="border-radius: 50%; object-fit: cover;"/>', obj.photo.url)
        return format_html('<span style="color: #999;">📷 Aucune</span>')
    photo_preview.short_description = "Photo"
    
    def actions_buttons(self, obj):
        return format_html(
            '<div style="display: flex; gap: 5px;">'
            '<a class="button" href="{}" target="_blank" style="background: #2196F3; padding: 5px 10px; color: white; text-decoration: none; border-radius: 3px;">📄 Bulletin</a>'
            '<a class="button" href="{}" target="_blank" style="background: #4CAF50; padding: 5px 10px; color: white; text-decoration: none; border-radius: 3px;">📜 Certificat</a>'
            '<a class="button" href="{}" target="_blank" style="background: #FF9800; padding: 5px 10px; color: white; text-decoration: none; border-radius: 3px;">🪪 Carte</a>'
            '</div>',
            reverse('admin:bulletin_pdf', args=[obj.id]),
            reverse('admin:certificat_scolarite', args=[obj.id]),
            reverse('admin:carte_etudiant', args=[obj.id])
        )
    actions_buttons.short_description = "Actions rapides"
    actions_buttons.allow_tags = True
    
    # ==================== DASHBOARD PRINCIPAL ====================
    
    def rapports_dashboard(self, request):
        """Dashboard principal des rapports"""
        context = {
            'title': 'Centre de rapports - Complexe Scolaire Sublime',
            'opts': self.model._meta,
            'total_eleves': Eleve.objects.count(),
            'total_actifs': Eleve.objects.filter(statut='actif').count(),
            'total_garcons': Eleve.objects.filter(sexe='M').count(),
            'total_filles': Eleve.objects.filter(sexe='F').count(),
            'classes': Classe.objects.all(),
            'current_date': timezone.now(),
        }
        return render(request, 'admin/rapports_dashboard.html', context)
    
    # ==================== RAPPORT AVEC PANDAS EXCEL ====================
    
    def rapport_excel_pandas(self, request):
        """
        Génération d'un rapport Excel professionnel avec pandas
        Inclut multiples feuilles, graphiques et analyses statistiques
        """
        # Récupérer les filtres
        classe_id = request.GET.get('classe')
        statut = request.GET.get('statut')
        sexe = request.GET.get('sexe')
        date_debut = request.GET.get('date_debut')
        date_fin = request.GET.get('date_fin')
        
        # Filtrer les élèves avec les paramètres
        queryset = Eleve.objects.all()
        if classe_id:
            queryset = queryset.filter(classe_id=classe_id)
        if statut:
            queryset = queryset.filter(statut=statut)
        if sexe:
            queryset = queryset.filter(sexe=sexe)
        if date_debut:
            queryset = queryset.filter(date_inscription__gte=date_debut)
        if date_fin:
            queryset = queryset.filter(date_inscription__lte=date_fin)
        
        # Convertir en DataFrame pandas
        data = []
        for eleve in queryset:
            data.append({
                'Matricule': eleve.matricule,
                'Nom': eleve.nom,
                'Post-nom': eleve.post_nom,
                'Prénom': eleve.prenom,
                'Nom complet': f"{eleve.nom} {eleve.post_nom} {eleve.prenom}",
                'Classe': eleve.classe.__str__() if eleve.classe else 'Non assigné',
                'Niveau': eleve.classe.niveau if eleve.classe else 'Non assigné',
                'Sexe': 'Masculin' if eleve.sexe == 'M' else 'Féminin',
                'Date de naissance': eleve.date_naissance,
                'Âge': self.calculer_age(eleve.date_naissance) if eleve.date_naissance else None,
                'Adresse': eleve.adresse,
                'Téléphone': eleve.telephone,
                'Email': eleve.email,
                'Statut': dict(Eleve.STATUT_CHOICES).get(eleve.statut, eleve.statut),
                "Date d'inscription": eleve.date_inscription,
                "Année inscription": eleve.date_inscription.year,
                "Mois inscription": eleve.date_inscription.strftime('%B'),
            })
        
        df = pd.DataFrame(data)
        
        # Créer le fichier Excel avec pandas
        output = BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Feuille 1: Liste des élèves
            df.to_excel(writer, sheet_name='Liste des élèves', index=False)
            
            # Feuille 2: Statistiques par classe
            stats_classe = df.groupby('Classe').agg({
                'Matricule': 'count',
                'Nom': 'count'
            }).rename(columns={'Matricule': 'Effectif'})
            stats_classe['Pourcentage'] = (stats_classe['Effectif'] / len(df) * 100).round(2)
            stats_classe.to_excel(writer, sheet_name='Stats par classe')
            
            # Feuille 3: Statistiques par sexe
            stats_sexe = df.groupby('Sexe').size().to_frame(name='Effectif')
            stats_sexe['Pourcentage'] = (stats_sexe['Effectif'] / len(df) * 100).round(2)
            stats_sexe.to_excel(writer, sheet_name='Stats par sexe')
            
            # Feuille 4: Statistiques par statut
            stats_statut = df.groupby('Statut').size().to_frame(name='Effectif')
            stats_statut.to_excel(writer, sheet_name='Stats par statut')
            
            # Feuille 5: Distribution des âges
            if 'Âge' in df.columns and not df['Âge'].isnull().all():
                age_stats = pd.DataFrame({
                    'Âge moyen': [df['Âge'].mean()],
                    'Âge min': [df['Âge'].min()],
                    'Âge max': [df['Âge'].max()],
                    'Écart-type': [df['Âge'].std()]
                })
                age_stats.to_excel(writer, sheet_name='Analyse âges', index=False)
                
                # Distribution des âges
                age_dist = df['Âge'].value_counts().sort_index().to_frame(name='Effectif')
                age_dist.to_excel(writer, sheet_name='Distribution âges')
            
            # Feuille 6: Inscriptions par mois
            if 'Mois inscription' in df.columns:
                inscriptions_mois = df['Mois inscription'].value_counts().to_frame(name='Inscriptions')
                inscriptions_mois.to_excel(writer, sheet_name='Inscriptions par mois')
            
            # Feuille 7: Résumé exécutif
            resume = pd.DataFrame({
                'Indicateur': [
                    'Total élèves',
                    'Élèves actifs',
                    'Élèves inactifs',
                    'Garçons',
                    'Filles',
                    'Nombre de classes',
                    'Taux d\'occupation',
                    'Date du rapport'
                ],
                'Valeur': [
                    len(df),
                    len(df[df['Statut'] == 'Actif']),
                    len(df[df['Statut'] != 'Actif']),
                    len(df[df['Sexe'] == 'Masculin']),
                    len(df[df['Sexe'] == 'Féminin']),
                    df['Classe'].nunique(),
                    f"{(len(df) / (df['Classe'].nunique() * 50) * 100):.1f}%" if df['Classe'].nunique() > 0 else "N/A",
                    timezone.now().strftime('%d/%m/%Y %H:%M')
                ]
            })
            resume.to_excel(writer, sheet_name='Résumé exécutif', index=False)
        
        # Appliquer le formatage avec openpyxl
        workbook = openpyxl.load_workbook(output)
        
        # Formater chaque feuille
        for sheetname in workbook.sheetnames:
            worksheet = workbook[sheetname]
            
            # En-têtes en gras et centrés
            for cell in worksheet[1]:
                cell.font = Font(bold=True, color="FFFFFF")
                cell.fill = PatternFill(start_color="4CAF50", end_color="4CAF50", fill_type="solid")
                cell.alignment = Alignment(horizontal='center', vertical='center')
            
            # Ajuster les largeurs de colonnes
            for column in worksheet.columns:
                max_length = 0
                column_letter = get_column_letter(column[0].column)
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_length = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_length
        
        workbook.save(output)
        output.seek(0)
        
        # Générer le nom du fichier
        filename = f"rapport_eleves_{timezone.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        response = HttpResponse(
            output,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        # Message de succès
        messages.success(request, f"Rapport Excel généré avec succès! {len(df)} élèves exportés.")
        
        return response
    
    def rapport_excel_xlsxwriter(self, request):
        """Génération d'un rapport Excel avec xlsxwriter et graphiques intégrés"""
        classe_id = request.GET.get('classe')
        statut = request.GET.get('statut')
        
        queryset = Eleve.objects.all()
        if classe_id:
            queryset = queryset.filter(classe_id=classe_id)
        if statut:
            queryset = queryset.filter(statut=statut)
        
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output, {'options': {'nan_inf_to_errors': True}})
        
        # Formats
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#4CAF50',
            'font_color': 'white',
            'border': 1,
            'align': 'center',
            'valign': 'vcenter'
        })
        
        cell_format = workbook.add_format({'border': 1, 'align': 'left', 'valign': 'vcenter'})
        money_format = workbook.add_format({'border': 1, 'align': 'right', 'num_format': '#,##0.00'})
        percent_format = workbook.add_format({'border': 1, 'align': 'center', 'num_format': '0.00%'})
        
        # Feuille principale
        worksheet = workbook.add_worksheet('Élèves')
        
        # En-têtes
        headers = ['Matricule', 'Nom', 'Post-nom', 'Prénom', 'Classe', 'Sexe', 'Âge', 'Téléphone', 'Email', 'Statut', "Date d'inscription"]
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, header_format)
        
        # Données
        for row, eleve in enumerate(queryset, start=1):
            worksheet.write(row, 0, eleve.matricule, cell_format)
            worksheet.write(row, 1, eleve.nom, cell_format)
            worksheet.write(row, 2, eleve.post_nom, cell_format)
            worksheet.write(row, 3, eleve.prenom, cell_format)
            worksheet.write(row, 4, eleve.classe.__str__() if eleve.classe else "", cell_format)
            worksheet.write(row, 5, dict(Eleve.SEXE_CHOICES).get(eleve.sexe, eleve.sexe), cell_format)
            worksheet.write(row, 6, self.calculer_age(eleve.date_naissance) if eleve.date_naissance else "", cell_format)
            worksheet.write(row, 7, eleve.telephone, cell_format)
            worksheet.write(row, 8, eleve.email, cell_format)
            worksheet.write(row, 9, dict(Eleve.STATUT_CHOICES).get(eleve.statut, eleve.statut), cell_format)
            worksheet.write(row, 10, eleve.date_inscription.strftime('%d/%m/%Y'), cell_format)
        
        # Ajuster les largeurs
        worksheet.set_column(0, 0, 15)  # Matricule
        worksheet.set_column(1, 3, 20)  # Noms
        worksheet.set_column(4, 4, 25)  # Classe
        worksheet.set_column(5, 5, 10)  # Sexe
        worksheet.set_column(6, 6, 8)   # Âge
        worksheet.set_column(7, 7, 15)  # Téléphone
        worksheet.set_column(8, 8, 30)  # Email
        worksheet.set_column(9, 9, 12)  # Statut
        worksheet.set_column(10, 10, 15) # Date inscription
        
        # Feuille de statistiques
        stats_worksheet = workbook.add_worksheet('Statistiques')
        
        # Statistiques par classe
        stats_worksheet.write(0, 0, 'Statistiques par classe', header_format)
        stats_headers = ['Classe', 'Effectif', 'Garçons', 'Filles', 'Taux remplissage']
        for col, header in enumerate(stats_headers):
            stats_worksheet.write(1, col, header, header_format)
        
        classes = Classe.objects.all()
        row = 2
        for classe in classes:
            count = Eleve.objects.filter(classe=classe).count()
            garcons = Eleve.objects.filter(classe=classe, sexe='M').count()
            filles = Eleve.objects.filter(classe=classe, sexe='F').count()
            taux = count / 50 if count <= 50 else 1.0
            
            stats_worksheet.write(row, 0, classe.__str__(), cell_format)
            stats_worksheet.write(row, 1, count, cell_format)
            stats_worksheet.write(row, 2, garcons, cell_format)
            stats_worksheet.write(row, 3, filles, cell_format)
            stats_worksheet.write(row, 4, taux, percent_format)
            row += 1
        
        # Graphique à barres
        chart = workbook.add_chart({'type': 'column'})
        chart.add_series({
            'name': 'Effectif par classe',
            'categories': f'=Statistiques!$A$3:$A${row-1}',
            'values': f'=Statistiques!$B$3:$B${row-1}',
        })
        chart.set_title({'name': 'Répartition des élèves par classe'})
        chart.set_x_axis({'name': 'Classes'})
        chart.set_y_axis({'name': 'Nombre d\'élèves'})
        stats_worksheet.insert_chart('G2', chart, {'x_offset': 25, 'y_offset': 10})
        
        workbook.close()
        output.seek(0)
        
        response = HttpResponse(output, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="rapport_scolaire.xlsx"'
        return response
    
    # ==================== RAPPORT PDF AVANCÉ ====================
    
    def rapport_detaille_pdf(self, request):
        """Rapport PDF détaillé avec graphiques et analyses"""
        classe_id = request.GET.get('classe')
        
        queryset = Eleve.objects.all()
        if classe_id:
            queryset = queryset.filter(classe_id=classe_id)
        
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="rapport_detaille_{timezone.now().strftime("%Y%m%d")}.pdf"'
        
        doc = SimpleDocTemplate(response, pagesize=A4, topMargin=20, bottomMargin=20)
        elements = []
        
        styles = getSampleStyleSheet()
        
        # Styles personnalisés
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=20,
            alignment=TA_CENTER,
            spaceAfter=20,
            textColor=colors.HexColor('#1a472a')
        )
        
        subtitle_style = ParagraphStyle(
            'Subtitle',
            parent=styles['Normal'],
            fontSize=12,
            alignment=TA_CENTER,
            textColor=colors.grey,
            spaceAfter=30
        )
        
        # En-tête du rapport
        elements.append(Paragraph("COMPLEXE SCOLAIRE SUBLIME", title_style))
        elements.append(Paragraph("Rapport Statistique des Élèves", subtitle_style))
        elements.append(Paragraph(f"Date: {timezone.now().strftime('%d/%m/%Y à %H:%M')}", styles['Normal']))
        elements.append(Spacer(1, 20))
        
        # Section Résumé
        elements.append(Paragraph("RÉSUMÉ EXÉCUTIF", styles['Heading2']))
        
        summary_data = [
            ['Indicateur', 'Valeur'],
            ['Total des élèves', str(queryset.count())],
            ['Élèves actifs', str(queryset.filter(statut='actif').count())],
            ['Garçons', str(queryset.filter(sexe='M').count())],
            ['Filles', str(queryset.filter(sexe='F').count())],
            ['Nombre de classes', str(queryset.values('classe').distinct().count())],
        ]
        
        summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a472a')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 20))
        
        # Section par classe
        elements.append(Paragraph("RÉPARTITION PAR CLASSE", styles['Heading2']))
        
        classe_stats = []
        for classe in Classe.objects.all():
            count = queryset.filter(classe=classe).count()
            if count > 0:
                classe_stats.append([classe.__str__(), str(count)])
        
        classe_table = Table([['Classe', 'Effectif']] + classe_stats, colWidths=[4*inch, 2*inch])
        classe_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        elements.append(classe_table)
        
        doc.build(elements)
        return response
    
    def rapport_eleves_pdf(self, request):
        """Rapport PDF simple des élèves"""
        classe_id = request.GET.get('classe')
        statut = request.GET.get('statut')
        
        queryset = Eleve.objects.all()
        if classe_id:
            queryset = queryset.filter(classe_id=classe_id)
        if statut:
            queryset = queryset.filter(statut=statut)
        
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="liste_eleves_{timezone.now().strftime("%Y%m%d")}.pdf"'
        
        doc = SimpleDocTemplate(response, pagesize=landscape(A4))
        elements = []
        
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            alignment=TA_CENTER,
            spaceAfter=20
        )
        
        elements.append(Paragraph("Liste des Élèves - Complexe Scolaire Sublime", title_style))
        elements.append(Spacer(1, 10))
        
        # Données du tableau
        data = [['Matricule', 'Nom complet', 'Classe', 'Sexe', 'Statut']]
        
        for eleve in queryset:
            data.append([
                eleve.matricule,
                f"{eleve.nom} {eleve.post_nom} {eleve.prenom}",
                eleve.classe.__str__() if eleve.classe else "-",
                'M' if eleve.sexe == 'M' else 'F',
                dict(Eleve.STATUT_CHOICES).get(eleve.statut, eleve.statut)
            ])
        
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        
        elements.append(table)
        doc.build(elements)
        return response
    
    # ==================== ANALYSE STATISTIQUE AVEC PANDAS ====================
    
    def analyse_statistique(self, request):
        """Page d'analyse statistique avancée avec pandas"""
        # Récupérer toutes les données
        eleves = Eleve.objects.select_related('classe').all()
        
        # Convertir en DataFrame
        data = []
        for eleve in eleves:
            data.append({
                'id': eleve.id,
                'matricule': eleve.matricule,
                'nom': eleve.nom,
                'classe': eleve.classe.__str__() if eleve.classe else 'Non assigné',
                'niveau': eleve.classe.niveau if eleve.classe else 'Non assigné',
                'sexe': eleve.sexe,
                'statut': eleve.statut,
                'age': self.calculer_age(eleve.date_naissance) if eleve.date_naissance else 0,
                'date_inscription': eleve.date_inscription,
            })
        
        df = pd.DataFrame(data)
        
        # Calculs statistiques
        stats = {
            'total': len(df),
            'actifs': len(df[df['statut'] == 'actif']),
            'garcons': len(df[df['sexe'] == 'M']),
            'filles': len(df[df['sexe'] == 'F']),
            'age_moyen': df['age'].mean() if len(df) > 0 else 0,
            'age_median': df['age'].median() if len(df) > 0 else 0,
            'classe_populeuse': df['classe'].mode()[0] if len(df) > 0 and len(df['classe'].mode()) > 0 else 'N/A',
            'taux_activite': (len(df[df['statut'] == 'actif']) / len(df) * 100) if len(df) > 0 else 0,
        }
        
        # Statistiques par classe
        stats_classe = df.groupby('classe').agg({
            'id': 'count',
            'sexe': lambda x: (x == 'M').sum()
        }).rename(columns={'id': 'effectif', 'sexe': 'garcons'})
        stats_classe['filles'] = stats_classe['effectif'] - stats_classe['garcons']
        stats_classe = stats_classe.to_dict('index')
        
        context = {
            'title': 'Analyse Statistique Avancée',
            'opts': self.model._meta,
            'stats': stats,
            'stats_classe': stats_classe,
            'df_head': df.head(10).to_html(classes='table table-striped', index=False),
            'current_date': timezone.now(),
        }
        
        return render(request, 'admin/analyse_statistique.html', context)
    
    def dashboard_analytics(self, request):
        """Dashboard analytics avec graphiques"""
        eleves = Eleve.objects.select_related('classe').all()
        
        # Préparer les données pour les graphiques
        classes_data = {}
        for eleve in eleves:
            if eleve.classe:
                classe_name = eleve.classe.__str__()
                if classe_name not in classes_data:
                    classes_data[classe_name] = {'total': 0, 'M': 0, 'F': 0}
                classes_data[classe_name]['total'] += 1
                if eleve.sexe == 'M':
                    classes_data[classe_name]['M'] += 1
                else:
                    classes_data[classe_name]['F'] += 1
        
        context = {
            'title': 'Dashboard Analytique',
            'opts': self.model._meta,
            'classes_data': json.dumps(classes_data),
            'total_eleves': eleves.count(),
            'current_date': timezone.now(),
        }
        
        return render(request, 'admin/dashboard_analytics.html', context)
    
    # ==================== DOCUMENTS INDIVIDUELS ====================
    
    def bulletin_pdf_view(self, request, eleve_id):
        """Génère un bulletin scolaire individuel professionnel"""
        try:
            eleve = Eleve.objects.get(id=eleve_id)
        except Eleve.DoesNotExist:
            return HttpResponse("Élève non trouvé", status=404)
        
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="bulletin_{eleve.matricule}.pdf"'
        
        doc = SimpleDocTemplate(response, pagesize=A4, topMargin=40, bottomMargin=40)
        elements = []
        
        styles = getSampleStyleSheet()
        
        # Styles
        header_style = ParagraphStyle(
            'Header',
            parent=styles['Heading1'],
            fontSize=18,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#1a472a'),
            spaceAfter=10
        )
        
        # En-tête
        elements.append(Paragraph("COMPLEXE SCOLAIRE SUBLIME", header_style))
        elements.append(Paragraph("BULLETIN SCOLAIRE", styles['Heading2']))
        elements.append(Paragraph(f"Année académique: {timezone.now().year}", styles['Normal']))
        elements.append(Spacer(1, 30))
        
        # Informations élève
        info_data = [
            ['Matricule:', eleve.matricule],
            ['Nom:', f"{eleve.nom} {eleve.post_nom} {eleve.prenom}"],
            ['Classe:', eleve.classe.__str__() if eleve.classe else "Non assignée"],
            ['Sexe:', dict(Eleve.SEXE_CHOICES).get(eleve.sexe, eleve.sexe)],
            ['Date de naissance:', eleve.date_naissance.strftime('%d/%m/%Y') if eleve.date_naissance else "Non renseignée"],
            ['Statut:', dict(Eleve.STATUT_CHOICES).get(eleve.statut, eleve.statut)],
        ]
        
        info_table = Table(info_data, colWidths=[2*inch, 4*inch])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        elements.append(info_table)
        elements.append(Spacer(1, 30))
        
        # Section des notes (à compléter)
        elements.append(Paragraph("RÉSULTATS ACADÉMIQUES", styles['Heading3']))
        elements.append(Spacer(1, 10))
        elements.append(Paragraph("Les résultats seront disponibles prochainement.", styles['Normal']))
        
        # Signature
        elements.append(Spacer(1, 50))
        signature_data = [
            ['Fait à Kinshasa, le ' + timezone.now().strftime('%d/%m/%Y'), 'Le Secrétaire Général'],
            ['', '__________________'],
        ]
        signature_table = Table(signature_data, colWidths=[3*inch, 3*inch])
        elements.append(signature_table)
        
        doc.build(elements)
        return response
    
    def certificat_scolarite(self, request, eleve_id):
        """Génère un certificat de scolarité"""
        try:
            eleve = Eleve.objects.get(id=eleve_id)
        except Eleve.DoesNotExist:
            return HttpResponse("Élève non trouvé", status=404)
        
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="certificat_scolarite_{eleve.matricule}.pdf"'
        
        doc = SimpleDocTemplate(response, pagesize=A4)
        elements = []
        
        styles = getSampleStyleSheet()
        
        # Contenu du certificat
        content = f"""
        <para alignment="CENTER" fontSize="16" spaceAfter="20"><b>CERTIFICAT DE SCOLARITÉ</b></para>
        <para alignment="CENTER" fontSize="12" spaceAfter="30">Complexe Scolaire Sublime</para>
        
        <para fontSize="11" spaceAfter="10">
        Je soussigné, Directeur du Complexe Scolaire Sublime, certifie que l'élève:
        </para>
        
        <para fontSize="12" spaceAfter="5">
        <b>Nom:</b> {eleve.nom} {eleve.post_nom} {eleve.prenom}<br/>
        <b>Matricule:</b> {eleve.matricule}<br/>
        <b>Date de naissance:</b> {eleve.date_naissance.strftime('%d/%m/%Y') if eleve.date_naissance else "Non renseignée"}<br/>
        <b>Classe:</b> {eleve.classe.__str__() if eleve.classe else "Non assignée"}<br/>
        <b>Statut:</b> {dict(Eleve.STATUT_CHOICES).get(eleve.statut, eleve.statut)}<br/>
        </para>
        
        <para fontSize="11" spaceAfter="20">
        Est régulièrement inscrit(e) au Complexe Scolaire Sublime pour l'année académique {timezone.now().year}.
        </para>
        
        <para fontSize="11">
        Le présent certificat est délivré pour servir et valoir ce que de droit.
        </para>
        """
        
        elements.append(Paragraph(content, styles['Normal']))
        elements.append(Spacer(1, 60))
        
        # Signature
        elements.append(Paragraph(f"Fait à Kinshasa, le {timezone.now().strftime('%d/%m/%Y')}", styles['Normal']))
        elements.append(Spacer(1, 20))
        elements.append(Paragraph("Le Directeur", styles['Normal']))
        elements.append(Spacer(1, 30))
        elements.append(Paragraph("__________________", styles['Normal']))
        
        doc.build(elements)
        return response
    
    def carte_etudiant(self, request, eleve_id):
        """Génère une carte d'étudiant"""
        try:
            eleve = Eleve.objects.get(id=eleve_id)
        except Eleve.DoesNotExist:
            return HttpResponse("Élève non trouvé", status=404)
        
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="carte_etudiant_{eleve.matricule}.pdf"'
        
        doc = SimpleDocTemplate(response, pagesize=(2.5*inch, 4*inch), topMargin=10, bottomMargin=10)
        elements = []
        
        styles = getSampleStyleSheet()
        
        # Design de la carte
        content = f"""
        <para alignment="CENTER" fontSize="10" spaceAfter="5"><b>COMPLEXE SCOLAIRE SUBLIME</b></para>
        <para alignment="CENTER" fontSize="8" spaceAfter="10">CARTE D'ÉTUDIANT</para>
        
        <para fontSize="8" spaceAfter="3">
        <b>Nom:</b> {eleve.nom}<br/>
        <b>Post-nom:</b> {eleve.post_nom}<br/>
        <b>Prénom:</b> {eleve.prenom}<br/>
        <b>Matricule:</b> {eleve.matricule}<br/>
        <b>Classe:</b> {eleve.classe.__str__() if eleve.classe else "N/A"}<br/>
        <b>Année:</b> {timezone.now().year}
        </para>
        """
        
        elements.append(Paragraph(content, styles['Normal']))
        
        doc.build(elements)
        return response
    
    # ==================== AUTRES MÉTHODES ====================
    
    def rapport_csv(self, request):
        """Export CSV simple"""
        classe_id = request.GET.get('classe')
        statut = request.GET.get('statut')
        
        queryset = Eleve.objects.all()
        if classe_id:
            queryset = queryset.filter(classe_id=classe_id)
        if statut:
            queryset = queryset.filter(statut=statut)
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="eleves_{timezone.now().strftime("%Y%m%d")}.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Matricule', 'Nom', 'Post-nom', 'Prénom', 'Classe', 'Sexe', 'Statut', "Date d'inscription"])
        
        for eleve in queryset:
            writer.writerow([
                eleve.matricule, eleve.nom, eleve.post_nom, eleve.prenom,
                eleve.classe.__str__() if eleve.classe else "",
                'M' if eleve.sexe == 'M' else 'F',
                dict(Eleve.STATUT_CHOICES).get(eleve.statut, eleve.statut),
                eleve.date_inscription.strftime('%d/%m/%Y')
            ])
        
        return response
    
    def impression_masse(self, request):
        """Page pour l'impression en masse"""
        if request.method == 'POST':
            eleve_ids = request.POST.getlist('eleves')
            type_doc = request.POST.get('type_doc')
            
            if type_doc == 'bulletin':
                # Générer des bulletins en masse
                return redirect('admin:rapports_dashboard')
            elif type_doc == 'certificat':
                return redirect('admin:rapports_dashboard')
        
        context = {
            'title': 'Impression en masse',
            'opts': self.model._meta,
            'eleves': Eleve.objects.filter(statut='actif'),
        }
        return render(request, 'admin/impression_masse.html', context)
    
    def api_eleves_data(self, request):
        """API pour récupérer les données des élèves (pour pandas)"""
        eleves = Eleve.objects.select_related('classe').all().values(
            'matricule', 'nom', 'post_nom', 'prenom', 'sexe', 'statut',
            'classe__niveau', 'date_inscription'
        )
        return JsonResponse(list(eleves), safe=False)
    
    # ==================== MÉTHODES UTILITAIRES ====================
    
    def calculer_age(self, date_naissance):
        """Calcule l'âge à partir de la date de naissance"""
        if not date_naissance:
            return None
        today = timezone.now().date()
        age = today.year - date_naissance.year
        if today.month < date_naissance.month or (today.month == date_naissance.month and today.day < date_naissance.day):
            age -= 1
        return age
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    # Actions admin
    actions = ['exporter_csv_selection', 'exporter_excel_selection', 'generer_bulletins_masse']
    
    def exporter_csv_selection(self, request, queryset):
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['Matricule', 'Nom', 'Post-nom', 'Prénom', 'Classe', 'Sexe', 'Statut'])
        
        for eleve in queryset:
            writer.writerow([
                eleve.matricule, eleve.nom, eleve.post_nom, eleve.prenom,
                eleve.classe.__str__() if eleve.classe else "",
                eleve.sexe, eleve.statut
            ])
        
        response = HttpResponse(output.getvalue(), content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="eleves_selection.csv"'
        return response
    exporter_csv_selection.short_description = "Exporter la sélection en CSV"
    
    def exporter_excel_selection(self, request, queryset):
        # Convertir en DataFrame
        data = [{
            'Matricule': e.matricule,
            'Nom': e.nom,
            'Post-nom': e.post_nom,
            'Prénom': e.prenom,
            'Classe': e.classe.__str__() if e.classe else "",
            'Sexe': e.sexe,
            'Statut': e.statut,
        } for e in queryset]
        
        df = pd.DataFrame(data)
        output = BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Élèves sélectionnés', index=False)
        
        output.seek(0)
        response = HttpResponse(output, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="eleves_selection.xlsx"'
        return response
    exporter_excel_selection.short_description = "Exporter la sélection en Excel (pandas)"
    
    def generer_bulletins_masse(self, request, queryset):
        messages.info(request, f"Génération des bulletins pour {queryset.count()} élèves...")
        return redirect('admin:rapports_dashboard')
    generer_bulletins_masse.short_description = "Générer les bulletins pour la sélection"

# Enregistrement des modèles
admin.site.register(Classe, ClasseAdmin)
admin.site.register(Eleve, EleveAdmin)

# Personnalisation de l'interface admin
admin.site.site_header = "Complexe Scolaire Sublime - Administration Professionnelle"
admin.site.site_title = "Complexe Scolaire Sublime"
admin.site.index_title = "Tableau de bord - Complexe Scolaire Sublime"