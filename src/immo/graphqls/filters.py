from django.db.models import Q
from immo import models
from inventory.models import GroupeComptage
from django_filters import FilterSet, CharFilter, BooleanFilter


#######  Affectation  #########

affectation_quick = {}
affectation_filters = {}


class AffectationCustomFilters(FilterSet):
    pass


#######  Amortization  #########

amortization_quick = {}
amortization_filters = {}


class AmortizationCustomFilters(FilterSet):
    pass


#######  Appliance  #########

appliance_quick = {}
appliance_filters = {}


class ApplianceCustomFilters(FilterSet):
    pass


#######  Article  #########

article_quick = {}
article_filters = {}


class ArticleCustomFilters(FilterSet):
    pass


#######  Articleexitreason  #########

articleexitreason_quick = {}
articleexitreason_filters = {}


class ArticleexitreasonCustomFilters(FilterSet):
    pass


#######  Block  #########

block_quick = {}
block_filters = {}


class BlockCustomFilters(FilterSet):
    pass


#######  Construction  #########

construction_quick = {}
construction_filters = {}


class ConstructionCustomFilters(FilterSet):
    pass


#######  Department  #########

department_quick = {}
department_filters = {}


class DepartmentCustomFilters(FilterSet):
    pass


#######  Departmenthistory  #########

departmenthistory_quick = {}
departmenthistory_filters = {}


class DepartmenthistoryCustomFilters(FilterSet):
    pass


#######  Electronics  #########

electronics_quick = {}
electronics_filters = {}


class ElectronicsCustomFilters(FilterSet):
    pass


#######  Employer  #########

employer_quick = {}
employer_filters = {}


class EmployerCustomFilters(FilterSet):
    pass


#######  Exitreason  #########

exitreason_quick = {}
exitreason_filters = {}


class ExitreasonCustomFilters(FilterSet):
    pass


#######  Family  #########

family_quick = {}
family_filters = {}


class FamilyCustomFilters(FilterSet):
    pass


#######  File  #########

file_quick = {}
file_filters = {}


class FileCustomFilters(FilterSet):
    pass


#######  Financingmethod  #########

financingmethod_quick = {}
financingmethod_filters = {}


class FinancingmethodCustomFilters(FilterSet):
    pass


#######  Fueltype  #########

fueltype_quick = {}
fueltype_filters = {}


class FueltypeCustomFilters(FilterSet):
    pass


#######  Furniture  #########

furniture_quick = {}
furniture_filters = {}


class FurnitureCustomFilters(FilterSet):
    pass


#######  Land  #########

land_quick = {}
land_filters = {}


class LandCustomFilters(FilterSet):
    pass


#######  Location  #########

location_quick = {}
location_filters = {}
from graphql_relay import from_global_id


class LocationCustomFilters(FilterSet):
    for_group = CharFilter(method="resolve_for_group")

    def resolve_for_group(self, queryset, name, value):
        if not value:
            return queryset

        group = GroupeComptage.objects.filter(id=from_global_id(value)[1]).first()
        if not group:
            return queryset.none()

        allowed_ids = group.get_lieux_autorises().values_list("id", flat=True)
        return queryset.filter(id__in=allowed_ids)


#######  Machinery  #########

machinery_quick = {}
machinery_filters = {}


class MachineryCustomFilters(FilterSet):
    pass


#######  Medicalsupply  #########

medicalsupply_quick = {}
medicalsupply_filters = {}


class MedicalsupplyCustomFilters(FilterSet):
    pass


#######  Notification  #########

notification_quick = {}
notification_filters = {}


class NotificationCustomFilters(FilterSet):
    pass


#######  Refreshtoken  #########

refreshtoken_quick = {}
refreshtoken_filters = {}


class RefreshtokenCustomFilters(FilterSet):
    pass


#######  Room  #########

room_quick = {}
room_filters = {}


class RoomCustomFilters(FilterSet):
    pass


#######  Software  #########

software_quick = {}
software_filters = {}


class SoftwareCustomFilters(FilterSet):
    pass


#######  Stationery  #########

stationery_quick = {}
stationery_filters = {}


class StationeryCustomFilters(FilterSet):
    pass


#######  Subfamily  #########

subfamily_quick = {}
subfamily_filters = {}


class SubfamilyCustomFilters(FilterSet):
    pass


#######  Supplier  #########

supplier_quick = {}
supplier_filters = {}


class SupplierCustomFilters(FilterSet):
    pass


#######  Tool  #########

tool_quick = {}
tool_filters = {}


class ToolCustomFilters(FilterSet):
    pass


#######  OldUser  #########

olduser_quick = {}
olduser_filters = {}


class OldUserCustomFilters(FilterSet):
    pass


#######  Vehicle  #########

vehicle_quick = {}
vehicle_filters = {}


class VehicleCustomFilters(FilterSet):
    pass


#######  Vehiclemodel  #########

vehiclemodel_quick = {}
vehiclemodel_filters = {}


class VehiclemodelCustomFilters(FilterSet):
    pass


#######  Vehicletype  #########

vehicletype_quick = {}
vehicletype_filters = {}


class VehicletypeCustomFilters(FilterSet):
    pass
