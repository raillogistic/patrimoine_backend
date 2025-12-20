from django_filters import (
    BooleanFilter,
    CharFilter,
    FilterSet,
    MultipleChoiceFilter,
    NumberFilter,
)


def get_meta_filters(model):
    if (
        model._meta.pk.name == "id"
        or model._meta.pk.name == "pk"
        or "_ptr" in model._meta.pk.name
    ):
        res = {
            "id": (
                "exact",
                "in",
            ),
        }
    else:
        res = {
            model._meta.pk.name: (
                "exact",
                "in",
            ),
        }
    fields = get_all_fields(model)
    reverse_fields = {
        f.name: f for f in model._meta.get_fields() if f.auto_created and not f.concrete
    }
    # if model.__name__ == "ChequeOut":
    #     print(fields)
    # fields.sort(key=lambda f: type(f).__name__, reverse=True)
    for f in fields:
        if f.name == "polymorphic_ctype":
            continue
        _type = type(f).__name__
        if _type == "CharField":
            res = {**res, f.name: ("exact", "icontains", "isnull", "in")}

        if _type == "TimeField":
            res = {**res, f.name: ("exact", "gte", "lte", "isnull")}
        if _type == "IntegerField" or _type == "FloatField":
            res = {
                **res,
                f.name: ("exact", "icontains", "gte", "gt", "lte", "lt", "isnull"),
            }
        if _type == "DecimalField":
            res = {
                **res,
                f.name: (
                    "exact",
                    "icontains",
                    "gte",
                    "lte",
                    "isnull",
                    "lt",
                    "gt",
                ),
            }

        if _type == "DateField" or _type == "DateTimeField":
            res = {
                **res,
                f.name: (
                    "exact",
                    "gte",
                    "gt",
                    "lte",
                    "lt",
                    "isnull",
                    "year",
                    "month",
                    "year__gte",
                    "year__lte",
                ),
            }
        if type(f).__name__ == "OneToOneRel":
            res = {
                **res,
                f.name: ("exact", "isnull"),
            }
        if _type == "ForeignKey":
            res = {
                **res,
                f.name: (
                    "exact",
                    "in",
                    "isnull",
                ),
            }

        if _type == "OneToOneField":
            res = {**res, f.name: ("exact", "isnull")}
        if _type == "ManyToManyField":
            res = {**res, f.name: ("exact", "in", "isnull")}
        if _type == "BooleanField":
            res = {**res, f.name: ("exact", "isnull")}
    # for name, field in reverse_fields.items():
    #     if type(field).__name__ == "OneToOneRel":
    #             res = {
    #                 **res,
    #                 name: ("exact", "isnull"),
    #             }

    #     else:
    #             res = {
    #                 **res,
    #                 name: ("exact", "in", "isnull"),
    #             }

    return res


from django.db.models import Q
from django_filters import CharFilter, FilterSet, MultipleChoiceFilter, NumberFilter

from libs.graphql.filters import PeriodFilters
from libs.models.fields import (
    field_by_numbers,
    get_all_fields,
    get_reversed_m2m_names,
    get_reversed_manytoone_fields,
)
from libs.models.func import count_of_filter, sum_of_filter


def resolve_quick(filters={}):
    def quick(self, queryset, name, value):
        if len(value) == 0:
            return queryset
        queries = []
        for key, _type in filters.items():
            try:
                val = (
                    int(value)
                    if _type == "int"
                    else str(
                        value,
                    )
                )
                queries.append({f"{key}__icontains": val})
            except Exception as E:
                print("Error filters ", E)
        if len(queries) == 0:
            return queryset
        query = Q(**queries.pop())
        for item in queries:
            query |= Q(**item)

        return queryset.filter(query)

    return quick


def sum_of(f, f2, exp=""):
    def resolve_(self, queryset, name, value):
        return sum_of_filter(queryset, f"{f.name}__{f2.name}", value, exp)

    return resolve_


def resolve_count_filters(f):
    def meth(self, queryset, name, value):
        return (
            count_of_filter(queryset, f"{f.name}", value)
            if value or value == 0
            else queryset
        )

    return meth


def resolve_count_filters_gte(f):
    def meth(self, queryset, name, value):
        return (
            count_of_filter(queryset, f"{f.name}", value, "gte")
            if value or value == 0
            else queryset
        )

    return meth


def resolve_count_filters_gt(f):
    def meth(self, queryset, name, value):
        return (
            count_of_filter(queryset, f"{f.name}", value, "gt")
            if value or value == 0
            else queryset
        )

    return meth


def resolve_count_filters_lte(f):
    def meth(self, queryset, name, value):
        return (
            count_of_filter(queryset, f"{f.name}", value, "lte")
            if value or value == 0
            else queryset
        )

    return meth


def resolve_count_filters_lt(f):
    def meth(self, queryset, name, value):
        return (
            count_of_filter(queryset, f"{f.name}", value, "lt")
            if value or value == 0
            else queryset
        )

    return meth


from libs.models.fields import get_simplefields


def get_simplefields_quick(model):
    res = {}
    simples = get_simplefields(model)
    for f in simples:
        if (
            f.__class__.__name__ == "IntegerField"
            or f.__class__.__name__ == "FloatField"
        ):
            res[f.name] = "int"
        if f.__class__.__name__ == "CharField" or f.__class__.__name__ == "TextField":
            res[f.name] = "str"

    return res


def get_field_by_name(module_path, field_name, default=None):
    module = importlib.import_module(module_path)
    class_obj = getattr(module, field_name, {})
    return class_obj


def resolve_include():
    def _resolve_(self, queryset, *args, **kwargs):
        return []

    return _resolve_


def get_title(
    title,
    get,
):
    try:
        return f"{title}".split("/")[get]
    except:
        return title
    return title


def createOtherFilters(model):
    res = {}
    res["include"] = MultipleChoiceFilter(
        method="resolve_include",
    )
    res["resolve_include"] = resolve_include()
    res["quick"] = CharFilter(method="resolve_quick")
    res["resolve_quick"] = resolve_quick(
        {
            **get_simplefields_quick(model),
            **get_field_by_name(
                f"{model._meta.app_label}.graphqls.filters",
                f"{model.__name__.lower()}_quick",
                {},
            ),
        }
    )  # get quik filters for models

    fields = [
        *get_reversed_manytoone_fields(model),
        *get_reversed_m2m_names(model),
    ]

    floats = get_reversed_manytoone_fields(model)
    for f in floats:
        for f2 in field_by_numbers(f.related_model):
            # if model.__name__ == "Entreprise":
            #     print("xxxxxxxxxxx", f2.name)
            res[f"{f.name}__{f2.name}__sum"] = NumberFilter(
                method=f"resolve_{f.name}__{f2.name}__sum",
                # label=f"Somme  ({f.field.verbose_name} - {f2.verbose_name}) égale à ?",
            )
            res[f"{f.name}__{f2.name}__sum__gte"] = NumberFilter(
                method=f"resolve_{f.name}__{f2.name}__sum__gte",
                # label=f"Somme  ({f.field.verbose_name} - {f2.verbose_name}) supérieur à ?",
            )
            res[f"{f.name}__{f2.name}__sum__lte"] = NumberFilter(
                method=f"resolve_{f.name}__{f2.name}__sum__lte",
                # label=f"Somme  ({f.field.verbose_name} - {f2.verbose_name}) inférieur à ?",
            )
            res[f"resolve_{f.name}__{f2.name}__sum"] = sum_of(f, f2)
            res[f"resolve_{f.name}__{f2.name}__sum__gte"] = sum_of(f, f2, "gte")
            res[f"resolve_{f.name}__{f2.name}__sum__lte"] = sum_of(f, f2, "lte")

    for f in fields:
        res[f"{f.name}_count"] = NumberFilter(
            method=f"resolve_{f.name}_count",
            # label=f"Total  ({get_title(f.field.verbose_name,1)}) égale à ?",
        )
        res[f"{f.name}_count_gte"] = NumberFilter(
            method=f"resolve_{f.name}_count_gte",
            # label=f"Total  ({get_title(f.field.verbose_name,1)}) supérieur à ?",
        )
        res[f"{f.name}_count_gt"] = NumberFilter(
            method=f"resolve_{f.name}_count_gt",
            # label=f"Total  ({get_title(f.field.verbose_name,1)}) supérieur à ?",
        )

        res[f"{f.name}_count_lte"] = NumberFilter(
            method=f"resolve_{f.name}_count_lte",
            # label=f"Total  ({get_title(f.field.verbose_name,1)}) inférieur à ?",
        )
        res[f"{f.name}_count_lt"] = NumberFilter(
            method=f"resolve_{f.name}_count_lt",
            # label=f"Total  ({get_title(f.field.verbose_name,1)}) inférieur à ?",
        )

        res[f"resolve_{f.name}_count"] = resolve_count_filters(f)
        res[f"resolve_{f.name}_count_gte"] = resolve_count_filters_gte(f)
        res[f"resolve_{f.name}_count_gt"] = resolve_count_filters_gt(f)
        res[f"resolve_{f.name}_count_lte"] = resolve_count_filters_lte(f)
        res[f"resolve_{f.name}_count_lt"] = resolve_count_filters_lt(f)

    return res


def createMeta(model):
    attr = {
        "fields": {
            **get_meta_filters(model),
            **get_field_by_name(
                f"{model._meta.app_label}.graphqls.filters",
                f"{model.__name__.lower()}_filters",
                default={},
            ),
        },
        "model": model,
    }
    meta_class = type("MetaClass", (), attr)
    return meta_class


def create_dynamic_method(name):
    def method(self):
        return f"Method {name} called from {self.__class__.__name__}!"

    return method


### need to add methods

import importlib
import inspect
import sys

from django.db.models import Model


def get_parent(m):
    try:
        base_name = None
        base = m.__bases__[0]
        if (
            base.__name__ == "Model"
            or base.__name__ == "PolymorphicModel"
            or base.__name__ == "HistoricalChanges"
        ):
            base = None
        return base
    except Exception as E:
        print("Parent exce", E)


from .utils import get_class_by_name


def get_custom_filters(model):
    custom = ()
    parent = get_parent(model)

    try:
        # module = importlib.import_module(f"{model._meta.app_label}.graphqls.filters")
        _class = get_class_by_name(
            f"{model._meta.app_label}.graphqls.filters",
            f"{model.__name__}CustomFilters",
        )
        # print(_class)

        # filters = getattr(module, "filters")
        custom = (_class,)

        if parent:
            if getattr(parent._meta, "abstract", False):
                return (*custom,)
            else:
                return (*custom, *get_custom_filters(parent))
    except Exception as E:
        print("errrrrrrrrooooor", E)
        if parent:
            return (*custom, *get_custom_filters(parent))
        else:
            pass
    return custom


# def build_custom_filters(model):
#     res = get_custom_filters(model)
#     parent = get_parent(model)
#     if parent:
#         res = (*res,*(get_custom_filters(model)))


from django_filters import FilterSet


def createFilters(model):
    class_name = f"{model.__name__}Filters"
    _meta = createMeta(model)
    attrs = {
        "Meta": _meta,
        # "include": MultipleChoiceFilter(
        #     method="resolve_include",
        # ),
        **createOtherFilters(model),
    }
    filter_class = type(
        class_name,
        (
            *get_custom_filters(model),
            PeriodFilters,
        ),
        attrs,
    )
    return filter_class


from .utils import sorted_models

ProjectFilters = {}

for m in sorted_models():
    if getattr(m._meta, "abstract", False):
        continue
    ProjectFilters[f"{m.__name__}Filters"] = createFilters(m)

__all__ = ["ProjectFilters"]
