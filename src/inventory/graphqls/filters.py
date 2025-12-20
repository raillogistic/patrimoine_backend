

from django.db.models import Q
from inventory import models
from django_filters import FilterSet,CharFilter,BooleanFilter







#######  CampagneInventaire  #########

campagneinventaire_quick = {}
campagneinventaire_filters = {}
class CampagneInventaireCustomFilters(FilterSet):
    pass


#######  GroupeComptage  #########

groupecomptage_quick = {}
groupecomptage_filters = {}
class GroupeComptageCustomFilters(FilterSet):
    pass


#######  EnregistrementInventaire  #########

enregistrementinventaire_quick = {}
enregistrementinventaire_filters = {}
class EnregistrementInventaireCustomFilters(FilterSet):
    pass
        
