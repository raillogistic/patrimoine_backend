




































class AffectationCustomMutation:
    nested = {
        #'notification' : 'Notification',
#'department' : 'Department',
#'employer' : 'Employer',
#'article' : 'Article',
#'location' : 'Location',
#'user' : 'OldUser',

    }



class AmortizationCustomMutation:
    nested = {
        #'article' : 'Article',

    }



class ApplianceCustomMutation:
    nested = {
        #'article' : 'Article',
#'user' : 'OldUser',

    }



class ArticleCustomMutation:
    nested = {
        #'affectation' : 'Affectation',
#'amortization' : 'Amortization',
#'appliance' : 'Appliance',
#'articleexitreason' : 'Articleexitreason',
#'construction' : 'Construction',
#'electronics' : 'Electronics',
#'furniture' : 'Furniture',
#'land' : 'Land',
#'machinery' : 'Machinery',
#'medicalsupply' : 'Medicalsupply',
#'notification' : 'Notification',
#'software' : 'Software',
#'stationery' : 'Stationery',
#'tool' : 'Tool',
#'vehicle' : 'Vehicle',
#'enregistrements_inventaire' : 'EnregistrementInventaire',
#'supplier' : 'Supplier',
#'family' : 'Family',
#'user' : 'OldUser',

    }



class ArticleexitreasonCustomMutation:
    nested = {
        #'article' : 'Article',
#'exitreason' : 'Exitreason',

    }



class BlockCustomMutation:
    nested = {
        #'room' : 'Room',
#'user' : 'OldUser',

    }



class ConstructionCustomMutation:
    nested = {
        #'article' : 'Article',
#'user' : 'OldUser',

    }



class DepartmentCustomMutation:
    nested = {
        #'affectation' : 'Affectation',
#'departmenthistory' : 'Departmenthistory',
#'employer' : 'Employer',
#'enregistrements_inventaire' : 'EnregistrementInventaire',
#'user' : 'OldUser',

    }



class DepartmenthistoryCustomMutation:
    nested = {
        #'department' : 'Department',
#'changedby' : 'OldUser',

    }



class ElectronicsCustomMutation:
    nested = {
        #'article' : 'Article',
#'user' : 'OldUser',

    }



class EmployerCustomMutation:
    nested = {
        #'affectation' : 'Affectation',
#'department' : 'Department',
#'user' : 'OldUser',

    }



class ExitreasonCustomMutation:
    nested = {
        #'articleexitreason' : 'Articleexitreason',
#'user' : 'OldUser',

    }



class FamilyCustomMutation:
    nested = {
        #'article' : 'Article',
#'subfamily' : 'Subfamily',
#'user' : 'OldUser',

    }



class FileCustomMutation:
    nested = {
        
    }



class FinancingmethodCustomMutation:
    nested = {
        #'user' : 'OldUser',

    }



class FueltypeCustomMutation:
    nested = {
        #'user' : 'OldUser',

    }



class FurnitureCustomMutation:
    nested = {
        #'article' : 'Article',
#'user' : 'OldUser',

    }



class LandCustomMutation:
    nested = {
        #'article' : 'Article',
#'user' : 'OldUser',

    }



class LocationCustomMutation:
    nested = {
        #'affectation' : 'Affectation',
#'location' : 'Location',
#'enregistrements_inventaire' : 'EnregistrementInventaire',
#'user' : 'OldUser',
#'parent' : 'Location',

    }



class MachineryCustomMutation:
    nested = {
        #'article' : 'Article',
#'user' : 'OldUser',

    }



class MedicalsupplyCustomMutation:
    nested = {
        #'article' : 'Article',
#'user' : 'OldUser',

    }



class NotificationCustomMutation:
    nested = {
        #'user' : 'OldUser',
#'article' : 'Article',
#'affectation' : 'Affectation',

    }



class RefreshtokenCustomMutation:
    nested = {
        #'user' : 'OldUser',

    }



class RoomCustomMutation:
    nested = {
        #'block' : 'Block',
#'user' : 'OldUser',

    }



class SoftwareCustomMutation:
    nested = {
        #'article' : 'Article',
#'user' : 'OldUser',

    }



class StationeryCustomMutation:
    nested = {
        #'article' : 'Article',
#'user' : 'OldUser',

    }



class SubfamilyCustomMutation:
    nested = {
        #'family' : 'Family',
#'user' : 'OldUser',

    }



class SupplierCustomMutation:
    nested = {
        #'article' : 'Article',
#'user' : 'OldUser',

    }



class ToolCustomMutation:
    nested = {
        #'article' : 'Article',
#'user' : 'OldUser',

    }



class OldUserCustomMutation:
    nested = {
        #'affectation' : 'Affectation',
#'appliance' : 'Appliance',
#'article' : 'Article',
#'block' : 'Block',
#'construction' : 'Construction',
#'department' : 'Department',
#'departmenthistory' : 'Departmenthistory',
#'electronics' : 'Electronics',
#'employer' : 'Employer',
#'exitreason' : 'Exitreason',
#'family' : 'Family',
#'financingmethod' : 'Financingmethod',
#'fueltype' : 'Fueltype',
#'furniture' : 'Furniture',
#'land' : 'Land',
#'location' : 'Location',
#'machinery' : 'Machinery',
#'medicalsupply' : 'Medicalsupply',
#'notification' : 'Notification',
#'refreshtoken' : 'Refreshtoken',
#'room' : 'Room',
#'software' : 'Software',
#'stationery' : 'Stationery',
#'subfamily' : 'Subfamily',
#'supplier' : 'Supplier',
#'tool' : 'Tool',
#'vehicle' : 'Vehicle',
#'vehiclemodel' : 'Vehiclemodel',
#'vehicletype' : 'Vehicletype',

    }



class VehicleCustomMutation:
    nested = {
        #'article' : 'Article',
#'vehiclemodel' : 'Vehiclemodel',
#'vehicletype' : 'Vehicletype',
#'user' : 'OldUser',

    }



class VehiclemodelCustomMutation:
    nested = {
        #'vehicle' : 'Vehicle',
#'vehicletype' : 'Vehicletype',
#'user' : 'OldUser',

    }



class VehicletypeCustomMutation:
    nested = {
        #'vehicle' : 'Vehicle',
#'vehiclemodel' : 'Vehiclemodel',
#'user' : 'OldUser',

    }


