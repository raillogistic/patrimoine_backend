









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
        




#######  ArticleInventaire  #########

articleinventaire_quick = {}
articleinventaire_filters = {}
class ArticleInventaireCustomFilters(FilterSet):
    pass
        






#######  PositionType  #########

positiontype_quick = {}
positiontype_filters = {}
class PositionTypeCustomFilters(FilterSet):
    pass


#######  Position  #########

position_quick = {}
position_filters = {}
class PositionCustomFilters(FilterSet):
    pass


#######  ScannedArticle  #########

scannedarticle_quick = {}
scannedarticle_filters = {}
class ScannedArticleCustomFilters(FilterSet):
    pass
        




#######  RapprochementInventaire  #########

rapprochementinventaire_quick = {}
rapprochementinventaire_filters = {}
class RapprochementInventaireCustomFilters(FilterSet):
    pass
        




#######  RapprochementInventaireDetail  #########

rapprochementinventairedetail_quick = {}
rapprochementinventairedetail_filters = {}
class RapprochementInventaireDetailCustomFilters(FilterSet):
    pass
        
