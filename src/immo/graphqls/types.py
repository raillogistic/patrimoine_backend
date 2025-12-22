import graphene


#######  Affectation  #########


class AffectationCustomType(object):
    pass


#######  Amortization  #########


class AmortizationCustomType(object):
    pass


#######  Appliance  #########


class ApplianceCustomType(object):
    pass


#######  Article  #########


class ArticleCustomType(object):
    current_location = graphene.Field("libs.graphql.schema.types.LocationType")

    def resolve_current_location(self, info):
        return self.current_location


#######  Articleexitreason  #########


class ArticleexitreasonCustomType(object):
    pass


#######  Block  #########


class BlockCustomType(object):
    pass


#######  Construction  #########


class ConstructionCustomType(object):
    pass


#######  Department  #########


class DepartmentCustomType(object):
    pass


#######  Departmenthistory  #########


class DepartmenthistoryCustomType(object):
    pass


#######  Electronics  #########


class ElectronicsCustomType(object):
    pass


#######  Employer  #########


class EmployerCustomType(object):
    pass


#######  Exitreason  #########


class ExitreasonCustomType(object):
    pass


#######  Family  #########


class FamilyCustomType(object):
    pass


#######  File  #########


class FileCustomType(object):
    pass


#######  Financingmethod  #########


class FinancingmethodCustomType(object):
    pass


#######  Fueltype  #########


class FueltypeCustomType(object):
    pass


#######  Furniture  #########


class FurnitureCustomType(object):
    pass


#######  Land  #########


class LandCustomType(object):
    pass


#######  Location  #########


class LocationCustomType(object):
    children = graphene.List("libs.graphql.schema.types.LocationType")

    def resolve_children(self, info):
        return self.children.all()


#######  Machinery  #########


class MachineryCustomType(object):
    pass


#######  Medicalsupply  #########


class MedicalsupplyCustomType(object):
    pass


#######  Notification  #########


class NotificationCustomType(object):
    pass


#######  Refreshtoken  #########


class RefreshtokenCustomType(object):
    pass


#######  Room  #########


class RoomCustomType(object):
    pass


#######  Software  #########


class SoftwareCustomType(object):
    pass


#######  Stationery  #########


class StationeryCustomType(object):
    pass


#######  Subfamily  #########


class SubfamilyCustomType(object):
    pass


#######  Supplier  #########


class SupplierCustomType(object):
    pass


#######  Tool  #########


class ToolCustomType(object):
    pass


#######  OldUser  #########


class OldUserCustomType(object):
    pass


#######  Vehicle  #########


class VehicleCustomType(object):
    pass


#######  Vehiclemodel  #########


class VehiclemodelCustomType(object):
    pass


#######  Vehicletype  #########


class VehicletypeCustomType(object):
    pass
