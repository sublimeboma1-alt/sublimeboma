# admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.urls import reverse
from django.utils import timezone
from django.db.models import Sum
from .models import AnneeScolaire, TarifFrais, FraisScolaire, Paiement, TypeFrais, ModePaiement, StatutPaiement, Trimestre
from sub_app.eleves.models import Eleve

@admin.register(AnneeScolaire)
class AnneeScolaireAdmin(admin.ModelAdmin):
    list_display = ['annee', 'date_debut', 'date_fin', 'est_active', 'statut']
    list_filter = ['est_active', 'date_debut']
    search_fields = ['annee']
    list_editable = ['est_active']
    actions = ['activer_annee', 'desactiver_annee']
    
    fieldsets = (
        ('Information générale', {
            'fields': ('annee', 'est_active')
        }),
        ('Période scolaire', {
            'fields': ('date_debut', 'date_fin'),
        }),
    )
    
    def statut(self, obj):
        today = timezone.now().date()
        if obj.est_active:
            if obj.date_debut <= today <= obj.date_fin:
                return mark_safe('<span style="color: green; font-weight: bold;">✓ En cours</span>')
            elif today < obj.date_debut:
                return mark_safe('<span style="color: orange;">⏳ À venir</span>')
            else:
                return mark_safe('<span style="color: red;">✗ Terminée</span>')
        return mark_safe('<span style="color: gray;">● Inactive</span>')
    statut.short_description = "Statut"
    
    def activer_annee(self, request, queryset):
        AnneeScolaire.objects.all().update(est_active=False)
        queryset.update(est_active=True)
        self.message_user(request, f"{queryset.count()} année(s) scolaire(s) activée(s)")
    activer_annee.short_description = "Activer l'année scolaire (désactive les autres)"
    
    def desactiver_annee(self, request, queryset):
        queryset.update(est_active=False)
        self.message_user(request, f"{queryset.count()} année(s) scolaire(s) désactivée(s)")
    desactiver_annee.short_description = "Désactiver l'année scolaire"


@admin.register(TypeFrais)
class TypeFraisAdmin(admin.ModelAdmin):
    list_display = ['code', 'libelle', 'est_actif']
    list_filter = ['est_actif']
    search_fields = ['code', 'libelle']
    list_editable = ['libelle', 'est_actif']


@admin.register(ModePaiement)
class ModePaiementAdmin(admin.ModelAdmin):
    list_display = ['code', 'libelle', 'est_actif']
    list_filter = ['est_actif']
    search_fields = ['code', 'libelle']
    list_editable = ['libelle', 'est_actif']


@admin.register(StatutPaiement)
class StatutPaiementAdmin(admin.ModelAdmin):
    list_display = ['code', 'libelle', 'est_actif']
    list_filter = ['est_actif']
    search_fields = ['code', 'libelle']
    list_editable = ['libelle', 'est_actif']


@admin.register(Trimestre)
class TrimestreAdmin(admin.ModelAdmin):
    list_display = ['numero', 'libelle', 'est_actif']
    list_filter = ['est_actif']
    search_fields = ['libelle']
    list_editable = ['libelle', 'est_actif']


@admin.register(TarifFrais)
class TarifFraisAdmin(admin.ModelAdmin):
    list_display = ['niveau', 'classe_display', 'trimestre', 'type_frais', 'montant_formate', 'annee_scolaire', 'montant']
    list_filter = ['niveau', 'trimestre', 'type_frais', 'annee_scolaire']
    search_fields = ['classe_maternel__libelle', 'classe_primaire', 'classe_humanite', 'option_humanite']
    list_editable = ['montant']
    list_per_page = 20
    
    fieldsets = (
        ('Année scolaire', {
            'fields': ('annee_scolaire',)
        }),
        ('Niveau et classe', {
            'fields': ('niveau', 'classe_maternel', 'classe_primaire', 'classe_humanite', 'option_humanite'),
        }),
        ('Frais', {
            'fields': ('trimestre', 'type_frais', 'montant'),
        }),
    )
    
    def classe_display(self, obj):
        if obj.niveau_id == 'maternel' and obj.classe_maternel:
            return obj.classe_maternel
        elif obj.niveau_id == 'primaire' and obj.classe_primaire:
            return obj.classe_primaire
        elif obj.niveau_id == 'humanite' and obj.classe_humanite:
            if obj.option_humanite:
                return f"{obj.classe_humanite} ({obj.option_humanite})"
            return obj.classe_humanite
        return "-"
    classe_display.short_description = "Classe"
    
    def montant_formate(self, obj):
        return f"{obj.montant:,.0f} FC"
    montant_formate.short_description = "Montant"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('annee_scolaire', 'type_frais', 'niveau', 'classe_maternel', 'trimestre')


class PaiementInline(admin.TabularInline):
    model = Paiement
    extra = 0
    fields = ['reference', 'montant_paye', 'date_paiement', 'mode_paiement', 'statut', 'agent']
    readonly_fields = ['reference', 'date_creation', 'date_modification']
    show_change_link = True
    can_delete = True
    classes = ['collapse']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('agent', 'mode_paiement', 'statut')


@admin.register(FraisScolaire)
class FraisScolaireAdmin(admin.ModelAdmin):
    list_display = ['eleve_display', 'classe_eleve', 'annee_scolaire', 'trimestre', 
                    'type_frais', 'montant_total_formate', 'statut_paiement_badge', 
                    'solde_restant_formate', 'pourcentage_paiement']
    list_filter = ['annee_scolaire', 'trimestre', 'type_frais', 'eleve__classe']
    search_fields = ['eleve__nom', 'eleve__prenom', 'eleve__matricule', 'description']
    list_select_related = ['eleve', 'annee_scolaire']
    readonly_fields = ['date_creation', 'date_modification']
    inlines = [PaiementInline]
    actions = ['verifier_paiements']
    list_per_page = 25
    
    fieldsets = (
        ('Informations élève', {
            'fields': ('eleve', 'annee_scolaire')
        }),
        ('Détails du frais', {
            'fields': ('trimestre', 'type_frais', 'montant_total', 'description'),
        }),
        ('Informations système', {
            'fields': ('date_creation', 'date_modification'),
            'classes': ('collapse',)
        }),
    )
    
    def eleve_display(self, obj):
        return f"{obj.eleve.nom} {obj.eleve.prenom}"
    eleve_display.short_description = "Élève"
    eleve_display.admin_order_field = 'eleve__nom'
    
    def classe_eleve(self, obj):
        return obj.eleve.classe
    classe_eleve.short_description = "Classe"
    classe_eleve.admin_order_field = 'eleve__classe'
    
    def montant_total_formate(self, obj):
        return f"{obj.montant_total:,.0f} FC"
    montant_total_formate.short_description = "Montant total"
    
    def total_paye(self, obj):
        total = obj.paiements.filter(statut_id='valide').aggregate(total=Sum('montant_paye'))['total'] or 0
        return total
    
    def solde_restant(self, obj):
        return obj.montant_total - self.total_paye(obj)
    
    def montant_total_formate(self, obj):
        return f"{obj.montant_total:,.0f} FC"
    montant_total_formate.short_description = "Montant total"
    
    def solde_restant_formate(self, obj):
        solde = self.solde_restant(obj)
        if solde <= 0:
            return mark_safe('<span style="color: green;">✓ 0 FC</span>')
        return mark_safe(f'<span style="color: red;">⚠ {solde:,.0f} FC</span>')
    solde_restant_formate.short_description = "Solde restant"
    
    def statut_paiement_badge(self, obj):
        total_paye = self.total_paye(obj)
        if total_paye == 0:
            return mark_safe('<span style="background-color: red; color: white; padding: 3px 8px; border-radius: 3px;">✗ Non payé</span>')
        elif total_paye >= obj.montant_total:
            return mark_safe('<span style="background-color: green; color: white; padding: 3px 8px; border-radius: 3px;">✓ Payé</span>')
        else:
            return mark_safe('<span style="background-color: orange; color: white; padding: 3px 8px; border-radius: 3px;">⚠ Partiel</span>')
    statut_paiement_badge.short_description = "Statut"
    
    def pourcentage_paiement(self, obj):
        if obj.montant_total > 0:
            pourcentage = (self.total_paye(obj) / obj.montant_total) * 100
            color = '#4CAF50' if pourcentage >= 100 else '#FF9800' if pourcentage > 0 else '#F44336'
            return mark_safe(f'''
                <div style="background-color: #f0f0f0; border-radius: 10px; overflow: hidden; width: 100px;">
                    <div style="background-color: {color}; width: {min(pourcentage, 100)}%; height: 20px; text-align: center; color: white; line-height: 20px;">
                        {pourcentage:.0f}%
                    </div>
                </div>
            ''')
        return "0%"
    pourcentage_paiement.short_description = "Progression"
    
    def verifier_paiements(self, request, queryset):
        count = 0
        for frais in queryset:
            if self.solde_restant(frais) <= 0:
                count += 1
        self.message_user(request, f"{count} frais sont entièrement payés")
    verifier_paiements.short_description = "Vérifier les frais payés"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('eleve', 'annee_scolaire', 'type_frais', 'trimestre').prefetch_related('paiements')


@admin.register(Paiement)
class PaiementAdmin(admin.ModelAdmin):
    list_display = ['reference', 'eleve_display', 'frais_info', 'montant_paye_formate', 
                   'date_paiement', 'mode_paiement', 'statut_badge', 'agent', 'date_creation']
    list_filter = ['statut', 'mode_paiement', 'date_paiement', 'agent']
    search_fields = ['reference', 'eleve__nom', 'eleve__prenom', 'eleve__matricule', 'description']
    readonly_fields = ['reference', 'date_creation', 'date_modification']
    list_select_related = ['eleve', 'frais', 'agent']
    list_per_page = 30
    date_hierarchy = 'date_paiement'
    
    fieldsets = (
        ('Information du reçu', {
            'fields': ('reference', 'statut')
        }),
        ('Élève et frais', {
            'fields': ('eleve', 'frais')
        }),
        ('Détails du paiement', {
            'fields': ('montant_paye', 'date_paiement', 'mode_paiement', 'description'),
        }),
        ('Agent et système', {
            'fields': ('agent', 'date_creation', 'date_modification'),
            'classes': ('collapse',)
        }),
    )
    
    def eleve_display(self, obj):
        return f"{obj.eleve.nom} {obj.eleve.prenom}"
    eleve_display.short_description = "Élève"
    eleve_display.admin_order_field = 'eleve__nom'
    
    def frais_info(self, obj):
        if obj.frais:
            trimestre = obj.frais.get_trimestre_display()
            type_frais = obj.frais.type_frais
            montant_total = obj.frais.montant_total
            return f"{trimestre} - {type_frais} (Total: {montant_total:,.0f} FC)"
        return "-"
    frais_info.short_description = "Frais concerné"
    
    def montant_paye_formate(self, obj):
        return f"{obj.montant_paye:,.0f} FC"
    montant_paye_formate.short_description = "Montant payé"
    
    def statut_badge(self, obj):
        if obj.statut_id == 'valide':
            return mark_safe('<span style="background-color: green; color: white; padding: 3px 8px; border-radius: 3px;">✓ Validé</span>')
        elif obj.statut_id == 'annule':
            return mark_safe('<span style="background-color: red; color: white; padding: 3px 8px; border-radius: 3px;">✗ Annulé</span>')
        elif obj.statut_id == 'en_attente':
            return mark_safe('<span style="background-color: orange; color: white; padding: 3px 8px; border-radius: 3px;">⏳ En attente</span>')
        return obj.statut
    statut_badge.short_description = "Statut"
    
    actions = ['valider_paiements', 'annuler_paiements']
    
    def valider_paiements(self, request, queryset):
        updated = queryset.update(statut_id='valide')
        self.message_user(request, f"{updated} paiement(s) validé(s)")
    valider_paiements.short_description = "Valider les paiements sélectionnés"
    
    def annuler_paiements(self, request, queryset):
        updated = queryset.update(statut_id='annule')
        self.message_user(request, f"{updated} paiement(s) annulé(s)")
    annuler_paiements.short_description = "Annuler les paiements sélectionnés"
    
    def save_model(self, request, obj, form, change):
        if not obj.agent:
            obj.agent = request.user
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('eleve', 'frais', 'agent', 'mode_paiement', 'statut')
