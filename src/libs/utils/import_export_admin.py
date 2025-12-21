from import_export.admin import ImportExportModelAdmin

from .resources import safe_modelresource_factory


class SafeImportExportModelAdmin(ImportExportModelAdmin):
    def get_resource_classes(self, request):
        return [safe_modelresource_factory(self.model)]
