from django.apps import apps
from django.contrib import admin
from django.db import models
from libs.utils.import_export_admin import SafeImportExportModelAdmin

from .models import Article, Location


class ReadOnlyModelAdmin(SafeImportExportModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


def _field_is_relation(field):
    return isinstance(field, (models.ForeignKey, models.OneToOneField))


def _field_is_filterable(field):
    return isinstance(
        field,
        (
            models.BooleanField,
            models.DateField,
            models.DateTimeField,
            models.ForeignKey,
            models.OneToOneField,
        ),
    )


def _field_is_searchable(field):
    return isinstance(field, (models.CharField, models.TextField))


def _build_list_display(model):
    field_names = [field.name for field in model._meta.fields]
    if "id" in field_names:
        field_names.remove("id")
        field_names.insert(0, "id")
    return tuple(field_names[:8] or ["id"])


def _build_search_fields(model):
    return tuple(
        field.name for field in model._meta.fields if _field_is_searchable(field)
    )


def _build_list_filter(model):
    return tuple(
        field.name for field in model._meta.fields if _field_is_filterable(field)
    )


def _build_raw_id_fields(model):
    return tuple(
        field.name for field in model._meta.fields if _field_is_relation(field)
    )


def _build_list_select_related(model):
    return tuple(
        field.name for field in model._meta.fields if _field_is_relation(field)
    )


def _build_readonly_fields(model):
    field_names = [field.name for field in model._meta.fields]
    field_names.extend(field.name for field in model._meta.many_to_many)
    return tuple(field_names)


def _build_fieldsets(model):
    relation_fields = [
        field.name for field in model._meta.fields if _field_is_relation(field)
    ]
    data_fields = [
        field.name for field in model._meta.fields if field.name not in relation_fields
    ]
    fieldsets = []
    if relation_fields:
        fieldsets.append(("Relations", {"fields": tuple(relation_fields)}))
    if data_fields:
        fieldsets.append(("Donnees", {"fields": tuple(data_fields)}))
    return tuple(fieldsets)


def _build_admin_class(model):
    attrs = {
        "list_display": _build_list_display(model),
        "search_fields": _build_search_fields(model),
        "list_filter": _build_list_filter(model),
        "raw_id_fields": _build_raw_id_fields(model),
        "list_select_related": _build_list_select_related(model),
        "readonly_fields": _build_readonly_fields(model),
        "fieldsets": _build_fieldsets(model),
    }
    return type(f"{model.__name__}Admin", (ReadOnlyModelAdmin,), attrs)


class ArticleAdmin(SafeImportExportModelAdmin):
    list_display = (
        "code",
        "family",
        "supplier",
        "quantity",
        "type",
        "isexited",
        "acquiringdate",
    )
    search_fields = (
        "code",
        "serialnumber",
        "references",
        "invoice",
        "deliverynote",
        "financingmethod",
    )
    list_filter = (
        "type",
        "isexited",
        "acquiringdate",
        "supplier",
        "family",
        "createdat",
    )
    raw_id_fields = ("supplier", "family", "user")
    list_select_related = ("supplier", "family", "user")
    date_hierarchy = "createdat"
    fieldsets = (
        ("Identification", {"fields": ("code", "type", "serialnumber", "references")}),
        (
            "Achat",
            {
                "fields": (
                    "acquiringdate",
                    "deliverynote",
                    "invoice",
                    "financingmethod",
                    "supplier",
                )
            },
        ),
        (
            "Finances",
            {
                "fields": (
                    "beginningfiscalprice",
                    "totalfiscalprice",
                    "amortizationyears",
                )
            },
        ),
        ("Stock", {"fields": ("quantity", "isexited", "exitedat")}),
        ("Classification", {"fields": ("family",)}),
        ("Notes", {"fields": ("observation",)}),
        ("Audit", {"fields": ("user", "createdat", "updatedat")}),
    )


class LocationAdmin(SafeImportExportModelAdmin):
    list_display = (
        "locationname",
        "type",
        "parent",
        "barcode",
        "user",
        "createdat",
    )
    search_fields = (
        "locationname",
        "barcode",
        "type",
    )
    list_filter = (
        "type",
        "parent",
        "createdat",
        "user",
    )
    raw_id_fields = ("parent", "user")
    list_select_related = ("parent", "user")
    date_hierarchy = "createdat"
    fieldsets = (
        ("Identification", {"fields": ("locationname", "type", "barcode")}),
        ("Hierarchie", {"fields": ("parent",)}),
        ("Audit", {"fields": ("user", "createdat", "updatedat")}),
    )


app_models = apps.get_app_config("immo").get_models()

admin.site.register(Article, ArticleAdmin)
admin.site.register(Location, LocationAdmin)

for model in [m for m in app_models]:
    if model in (Article, Location):
        continue
    admin_class = _build_admin_class(model)
    admin.site.register(model, admin_class)
