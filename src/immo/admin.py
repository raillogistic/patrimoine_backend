from django.apps import apps
from django.contrib import admin


class ReadOnlyModelAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


app_models = apps.get_app_config("immo").get_models()

# Register managed=False models as read-only to prevent writes from admin.
for model in [m for m in app_models]:
    if not model._meta.managed:
        admin.site.register(model, ReadOnlyModelAdmin)
    else:
        admin.site.register(model)
