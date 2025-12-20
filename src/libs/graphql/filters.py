from django_filters.filterset import BooleanFilter, FilterSet
from django_filters.utils import get_model_field
from graphene_django.registry import get_global_registry, registry
from graphql_relay import from_global_id, to_global_id
from libs.utils.dates import *


def from_global_filter(filters, kwargs, model):
    for name, value in kwargs.items():
        try:
            if filters[name].__class__.__name__ == "GlobalIDFilter":
                _type, new_value = to_global_id(value)
                kwargs = {**kwargs, name: new_value or value}

            if filters[name].__class__.__name__ == "ListFilter":
                new_values = []
                for v in value:
                    _type, new_vale = from_global_id(v)
                    new_values.append(new_vale or v)
                kwargs = {**kwargs, name: new_values}

        except Exception as E:
            print(E)
        print(kwargs)
    return kwargs


"""

this method expect to return values as relay gloabal id

"""


def from_global_filter_for_relay(filters, kwargs, model):
    for name, value in kwargs.items():
        try:
            # print(field_model)
            if filters[name].__class__.__name__ == "GlobalIDFilter":
                try:
                    int(value)
                    field_model = get_model_field(model, name).related_model.__name__
                    # to throw exception if id is django field
                    v = to_global_id(f"{field_model}Type", value)
                    print(f"{field_model}Type")
                    kwargs = {**kwargs, name: v}
                except:
                    # if relay global id, pass to args directly
                    kwargs = {**kwargs, name: value}

            if filters[name].__class__.__name__ == "ListFilter":
                new_values = []
                for v in value:
                    try:
                        _type, new_vale = from_global_id(v)
                        if new_vale:
                            new_values.append(new_vale)
                        else:
                            new_values.append(v)
                    except:
                        new_values.append(v)

                kwargs = {**kwargs, name: new_values}

        except Exception as E:
            print(E)
    return kwargs


from django.conf import settings
from django.db.models import Q


class PeriodFilters(FilterSet):
    this_week = BooleanFilter(
        method="resolve_this_week",
    )
    # this_week = BooleanFilter(method="resolve_this_week",label="cette semaine")

    def resolve_this_week(self, queryset, name, value):
        a, b = get_current_week()
        if settings.MODEL_DATE.get(self._meta.model.__name__):
            name = settings.MODEL_DATE.get(self._meta.model.__name__)
            return queryset.filter(
                Q(
                    **{
                        f"{name}__gte": a,
                        f"{name}__lte": b,
                    }
                )
            )
        return queryset.filter(date__gte=a, date__lte=b)

    last_week = BooleanFilter(
        method="resolve_last_week",
    )
    # last_week = BooleanFilter(method="resolve_last_week",label="semaine précédente")

    def resolve_last_week(self, queryset, name, value):
        a, b = get_last_week()
        if settings.MODEL_DATE.get(self._meta.model.__name__):
            name = settings.MODEL_DATE.get(self._meta.model.__name__)
            return queryset.filter(
                Q(
                    **{
                        f"{name}__gte": a,
                        f"{name}__lte": b,
                    }
                )
            )
        return queryset.filter(date__gte=a, date__lte=b)

    this_month = BooleanFilter(
        method="resolve_this_month",
    )
    # this_month = BooleanFilter(method="resolve_this_month",label="Cet mois")

    def resolve_this_month(self, queryset, name, value):
        a, b = get_date_range("MOIS_EN_COURS")
        if settings.MODEL_DATE.get(self._meta.model.__name__):
            name = settings.MODEL_DATE.get(self._meta.model.__name__)
            return queryset.filter(
                Q(
                    **{
                        f"{name}__gte": a,
                        f"{name}__lte": b,
                    }
                )
            )
        return queryset.filter(date__gte=a, date__lte=b)

    last_month = BooleanFilter(
        method="resolve_last_month",
    )
    # last_month = BooleanFilter(method="resolve_last_month",label="Mois précédent")

    def resolve_last_month(self, queryset, name, value):
        a, b = get_date_range("MOIS_PRECEDENT")
        if settings.MODEL_DATE.get(self._meta.model.__name__):
            name = settings.MODEL_DATE.get(self._meta.model.__name__)
            return queryset.filter(
                Q(
                    **{
                        f"{name}__gte": a,
                        f"{name}__lte": b,
                    }
                )
            )
        return queryset.filter(date__gte=a, date__lte=b)

    today = BooleanFilter(
        method="resolve_today",
    )
    # today = BooleanFilter(method="resolve_today",label="Aujourd'hui")

    def resolve_today(self, queryset, name, value):
        a, b = get_date_range("CE_JOUR")
        if settings.MODEL_DATE.get(self._meta.model.__name__):
            name = settings.MODEL_DATE.get(self._meta.model.__name__)
            return queryset.filter(
                Q(
                    **{
                        f"{name}": a,
                    }
                )
            )
        return queryset.filter(date=a)

    this_year = BooleanFilter(
        method="resolve_this_year",
    )
    # this_year = BooleanFilter(method="resolve_this_year",label="Cette année")

    def resolve_this_year(self, queryset, name, value):
        a, b = get_date_range("ANNEE_EN_COURS")
        if settings.MODEL_DATE.get(self._meta.model.__name__):
            name = settings.MODEL_DATE.get(self._meta.model.__name__)
            return queryset.filter(
                Q(
                    **{
                        f"{name}__gte": a,
                        f"{name}__lte": b,
                    }
                )
            )
        return queryset.filter(date__gte=a, date__lte=b)

    last_year = BooleanFilter(
        method="resolve_last_year",
    )
    # last_year = BooleanFilter(method="resolve_last_year",label="Année précédente")

    def resolve_last_year(self, queryset, name, value):
        a, b = get_date_range("ANNEE_PRECEDENTE")
        if settings.MODEL_DATE.get(self._meta.model.__name__):
            name = settings.MODEL_DATE.get(self._meta.model.__name__)
            return queryset.filter(
                Q(
                    **{
                        f"{name}__gte": a,
                        f"{name}__lte": b,
                    }
                )
            )
        return queryset.filter(date__gte=a, date__lte=b)
