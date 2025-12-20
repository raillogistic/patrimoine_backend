import graphene
from django.core.paginator import Paginator
from graphene_django.filter import DjangoFilterConnectionField

from libs.graphql.connection import OrderedDjangoFilterConnectionField
from libs.graphql.filters import from_global_filter_for_relay
from libs.graphql.types import CustomNode

from ..settings import getLen
from .types import ProjectTypes
from .utils import sorted_models, userapps


def create_filterclass(_type, _filter):
    filterclass = DjangoFilterConnectionField(_type, filterset_class=_filter)
    # filter_fields = filterclass.filterset_class().__dict__["filters"]
    # filtering_args = filterclass.filtering_args
    return filterclass


def relay_resolver(model, resolve_queryset=None):
    def resolve_models_meth(self, info, **kwargs):
        print("mdlksqmdlksqmdlkqsmlkdsqlmkd")
        if resolve_queryset:
            qs = resolve_queryset(info, model.objects.all(), **kwargs)
        else:
            return model.objects.all()
        return qs

    return resolve_models_meth


import importlib


def get_function(module_path, func_name, default=None):
    module = importlib.import_module(module_path)
    class_obj = getattr(module, func_name, {})
    return class_obj


def list_resolver(model, filterclass, resolve_queryset=None):
    def resolve_models_meth(self, info, **kwargs):
        ordering = kwargs.get(
            "ordering",
        )
        qs = model.objects.all()

        new_kwargs = from_global_filter_for_relay(
            filterclass.filterset_class().__dict__["filters"], kwargs, model
        )

        filterset = filterclass.filterset_class(
            data={**kwargs, **new_kwargs},
            queryset=qs,
            request=info.context,
        )

        fun = get_function(
            f"{model._meta.app_label}.graphqls.resolvers",
            f"resolve_{model.__name__.lower()}_query",
        )

        if fun:
            qs = fun(info, filterset.qs, **kwargs)
        else:
            qs = filterset.qs

        res = qs.order_by(*ordering.split(",")) if ordering else qs
        limit = 0 if kwargs.pop("limit", None) == 0 else kwargs.pop("limit", 100)
        add = (
            model.objects.filter(pk__in=kwargs.get("include", []))
            if kwargs.get("include", []) is not None
            and len(kwargs.get("include", [])) > 0
            else []
        )

        if limit:
            return [*add, *res[:limit]]
        if limit == 0:
            return [*add, *res]
        if getLen(model.__name__):
            return [*add, *res[: getLen(model.__name__)]]
        return [*add, *res]

    return resolve_models_meth


def pages_resolver(model, filterclass, resolve_queryset=None):
    def resolve_models_meth(self, info, **kwargs):
        ordering = kwargs.get(
            "ordering",
        )
        qs = model.objects.all()

        new_kwargs = from_global_filter_for_relay(
            filterclass.filterset_class().__dict__["filters"], kwargs, model
        )
        filterset = filterclass.filterset_class(
            data={**kwargs, **new_kwargs},
            queryset=qs,
            request=info.context,
        )

        fun = get_function(
            f"{model._meta.app_label}.graphqls.resolvers",
            f"resolve_{model.__name__.lower()}_query",
        )

        if fun:
            qs = fun(info, filterset.qs, **kwargs)
        else:
            qs = filterset.qs

        res = qs.order_by(*ordering.split(",")) if ordering else qs
        page_size = kwargs.pop("page_size", 10)
        page = kwargs.pop("page", 1)
        paginator = Paginator(res, page_size)
        page_obj = paginator.get_page(page)
        add = []

        if len(kwargs.get("include", [])) > 0:
            print(qs.filter(pk__in=kwargs.get("include", [])))

        add = (
            model.objects.filter(pk__in=kwargs.get("include", []))
            if kwargs.get("include", []) is not None
            and len(kwargs.get("include", [])) > 0
            else []
        )
        qs = page_obj.object_list
        return {
            "data": [*add, *qs],
            "totalCount": paginator.count,
            "totalPages": paginator.num_pages,
            "currentPage": page,
        }

        # if getLen(model.__name__):
        #     return [*add, *res[: getLen(model.__name__)]]
        return [*add, *res]

    return resolve_models_meth


def count_resolver(model, filterclass, resolve_queryset=None):
    def resolve_models_meth(self, info, **kwargs):
        ordering = kwargs.get("ordering", "-id")
        qs = model.objects.all()

        new_kwargs = from_global_filter_for_relay(
            filterclass.filterset_class().__dict__["filters"], kwargs, model
        )

        filterset = filterclass.filterset_class(
            data={**kwargs, **new_kwargs},
            queryset=qs,
            request=info.context,
        )

        fun = get_function(
            f"{model._meta.app_label}.graphqls.resolvers",
            f"resolve_{model.__name__.lower()}_query",
        )

        if fun:
            qs = fun(info, filterset.qs, **kwargs)
        else:
            qs = filterset.qs

        return qs.count()

    return resolve_models_meth


def resolve_one(_type, resolve_one=None):
    if resolve_one:
        return CustomNode.Field(
            _type,
            check=resolve_one,
        )
    return CustomNode.Field(
        _type,
    )


from .filters import ProjectFilters


def createModelQuerySchema(
    model,
):
    model_name = model.__name__.lower()
    _type = ProjectTypes[f"{model.__name__}Type"]
    _filters = ProjectFilters[f"{model.__name__}Filters"]
    class_name = f"{model.__name__}Queries"
    #################
    filterclass = create_filterclass(_type, _filters)

    attrs = {
        f"{model.__name__.lower()}": resolve_one(_type, None),
        f"all_{model.__name__.lower()}s": OrderedDjangoFilterConnectionField(
            _type, ordering=graphene.List(of_type=graphene.String)
        ),
        f"{model.__name__.lower()}s": graphene.List(
            _type,
            ordering=graphene.String(),
            limit=graphene.Int(),
            **filterclass.filtering_args,
        ),
        f"{model.__name__.lower()}_pages": graphene.Field(
            type(
                f"{model.__name__.lower()}PaginationType",
                (graphene.ObjectType,),
                {
                    "data": graphene.List(of_type=_type),
                    "totalCount": graphene.Int(),
                    "totalPages": graphene.Int(),
                    "currentPage": graphene.Int(),
                },
            ),
            ordering=graphene.String(),
            page_size=graphene.Int(required=False, default_value=10),
            page=graphene.Int(required=False, default_value=1),
            **filterclass.filtering_args,
        ),
        f"{model.__name__.lower()}_count": graphene.Int(
            ordering=graphene.String(),
            limit=graphene.Int(),
            **filterclass.filtering_args,
        ),
        f"resolve_{model_name.lower()}s": list_resolver(
            model,
            filterclass,
        ),
        f"resolve_{model.__name__.lower()}_pages": pages_resolver(
            model,
            filterclass,
        ),
        f"resolve_{model_name.lower()}_count": count_resolver(
            model,
            filterclass,
        ),
        f"all_{model.__name__.lower()}": relay_resolver(
            model,
        ),
    }
    return type(class_name, (graphene.ObjectType,), attrs)


from django.conf import settings

from .utils import get_class_by_name


def get_custom_queries():
    res = []
    for app in userapps():
        try:
            _class = get_class_by_name(
                f"{app.name}.graphqls.custom_schema",
                f"{app.name.capitalize()}CustomQueries",
            )
            res.append(_class)
        except Exception as E:
            print("error in get_custom_queries", E)
    urls = f"{settings.ROOT_URLCONF}".split(".")
    path = None
    if len(urls) > 0:
        path = urls[0]
    if path is None:
        return
    else:
        res.append(
            get_class_by_name(
                f"{path}.global_schema",
                "GlobalQueries",
            )
        )

    return res


Queries = {}

for m in sorted_models():
    if getattr(m._meta, "abstract", False):
        continue
    Queries[m.__name__] = createModelQuerySchema(
        m,
    )

__all__ = ["Queries"]
