from django.contrib import admin
from libs.utils.import_export_admin import SafeImportExportModelAdmin

from .models import CampagneInventaire, EnregistrementInventaire, GroupeComptage


class TimestampedAdmin(SafeImportExportModelAdmin):
    readonly_fields = ("cree_le", "modifie_le")


@admin.register(CampagneInventaire)
class CampagneInventaireAdmin(TimestampedAdmin):
    list_display = (
        "code_campagne",
        "nom",
        "date_debut",
        "date_fin",
        "cree_le",
        "modifie_le",
    )
    list_filter = ("date_debut", "date_fin")
    search_fields = ("code_campagne", "nom")
    ordering = ("-cree_le", "nom")
    date_hierarchy = "cree_le"
    fieldsets = (
        (
            "Identite",
            {
                "fields": ("code_campagne", "nom"),
            },
        ),
        (
            "Calendrier",
            {
                "fields": ("date_debut", "date_fin"),
            },
        ),
        (
            "Suivi",
            {
                "fields": ("cree_le", "modifie_le"),
            },
        ),
    )


@admin.register(GroupeComptage)
class GroupeComptageAdmin(TimestampedAdmin):
    list_display = (
        "nom",
        "campagne",
        "utilisateur",
        "appareil_identifiant",
        "role",
        "pin_code",
        "cree_le",
        "modifie_le",
    )
    list_filter = ("campagne", "role", "cree_le")
    search_fields = (
        "nom",
        "appareil_identifiant",
        "utilisateur__username",
        "utilisateur__email",
        "utilisateur__first_name",
        "utilisateur__last_name",
        "campagne__code_campagne",
        "campagne__nom",
    )
    raw_id_fields = ("campagne", "utilisateur")
    filter_horizontal = ("lieux_autorises",)
    ordering = ("nom",)
    list_select_related = ("campagne", "utilisateur")
    fieldsets = (
        (
            "Comptage",
            {
                "fields": (
                "campagne",
                "nom",
                "utilisateur",
                "role",
                "appareil_identifiant",
                "pin_code",
                "lieux_autorises",
                "commentaire",
            ),
        },
        ),
        (
            "Suivi",
            {
                "fields": ("cree_le", "modifie_le"),
            },
        ),
    )


@admin.register(EnregistrementInventaire)
class EnregistrementInventaireAdmin(TimestampedAdmin):
    list_display = (
        "code_article",
        "campagne",
        "groupe",
        "lieu",
        "departement",
        "article",
        "etat",
        "capture_le",
        "source_scan",
    )
    list_filter = ("groupe__nom", "lieu")
    search_fields = (
        "code_article",
        "article__code",
        "lieu__locationname",
        "departement__departmentname",
        "groupe__nom",
        "campagne__code_campagne",
        "campagne__nom",
    )
    raw_id_fields = ("campagne", "groupe", "lieu", "departement", "article")
    ordering = ("-capture_le",)
    date_hierarchy = "capture_le"
    list_select_related = ("campagne", "groupe", "lieu", "departement", "article")
    fieldsets = (
        (
            "Reference",
            {
                "fields": (
                    "campagne",
                    "groupe",
                    "lieu",
                    "departement",
                    "article",
                    "code_article",
                ),
            },
        ),
        (
            "Capture",
            {
                "fields": ("capture_le", "source_scan", "etat", "donnees_capture"),
            },
        ),
        (
            "Notes",
            {
                "fields": ("commentaire",),
            },
        ),
        (
            "Suivi",
            {
                "fields": ("cree_le", "modifie_le"),
            },
        ),
    )
