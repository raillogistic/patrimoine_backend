from django.db.models import Q, Max
from django_filters import BooleanFilter, CharFilter, FilterSet
from inventory import models

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

enregistrementinventaire_quick = {
    "article__desc": "str",
    "article__code": "str",
}
enregistrementinventaire_filters = {}


class EnregistrementInventaireCustomFilters(FilterSet):
    unique_article = BooleanFilter(method="filter_unique_article")

    def filter_unique_article(self, queryset, name, value):
        if value:
            ids = (
                queryset.filter(article__isnull=False)
                .values("article")
                .annotate(max_id=Max("id"))
                .values_list("max_id", flat=True)
            )
            return queryset.filter(id__in=ids)
        return queryset


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
