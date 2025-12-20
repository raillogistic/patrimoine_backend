import datetime
import importlib

import graphene
from django.apps import apps
from django.db.models import (
    Avg,
    Count,
    DecimalField,
    FloatField,
    IntegerField,
    Max,
    Q,
    Sum,
)
from django.db.models.functions import Coalesce, TruncMonth
from graphene_django.filter import DjangoFilterConnectionField


class ReportingDateType(graphene.ObjectType):
    value = graphene.String()
    count = graphene.Int()


class ReportingSumType(graphene.ObjectType):
    value = graphene.String()
    count = graphene.Int()


class NameValue(graphene.ObjectType):
    name = graphene.String()
    value = graphene.Float()
    _type = graphene.String()
    date = graphene.Date()
    compared_to = graphene.List("libs.graphql.schema.custom.reporting.NameValue")
    extra = graphene.List("libs.graphql.schema.custom.reporting.NameValue")
    dates = graphene.List("libs.graphql.schema.custom.reporting.NameValue")


class ReportVariableType(graphene.InputObjectType):
    name = graphene.String()
    value = graphene.String()


def checkExcludeAndEmpty(x):
    if x.name.endswith("__exclude"):
        return False
    if isinstance(x.value, list) and len(x.value) == 0:
        return False
    if x.value == "":
        return False
    return True


import json


def to_bool(value, name):
    if value == "true":
        return True
    elif value == "false":
        return False
    if name.endswith("__in") and len(value) > 0:
        return value.replace("[", "").replace("]", "").split(",")
    return value


def listToObject(filters):
    excludes = list(filter(lambda x: x.name.endswith("__exclude"), filters))
    includes = list(filter(checkExcludeAndEmpty, filters))

    include_filters = dict(
        zip(
            list(map(lambda x: x.name, includes)),
            list(map(lambda x: to_bool(x.value, x.name), includes)),
        )
    )

    exclude_filters = dict(
        zip(
            list(map(lambda x: x.name.replace("__exclude", ""), excludes)),
            list(map(lambda x: to_bool(x.value, x.name), excludes)),
        )
    )
    return include_filters, exclude_filters


def month_details(model, month, year):
    dates = (
        model.objects.annotate(month=TruncMonth("date"))
        .filter(~Q(**{"date": None}) & Q(**{"date__month": month, "date__year": year}))
        .order_by("date")
        .values("date")
        .annotate(count=Count("date"))
    )
    return dates


def convertToNameValue(query, name, value="count"):
    return [
        NameValue(_type=c[name].__class__.__name__, name=c[name], value=c[value])
        for c in query
    ]


def withoutTarget(model, target="date__month"):
    res = (
        model.objects.values(
            target,
        )
        .annotate(count=Count(target))
        .values(
            target,
            "count",
        )
    )
    results = []

    for o in res:
        dates = []
        results.append(
            NameValue(
                name=o[target],
                value=o["count"],
                compared_to=[],
                dates=[NameValue(name=c["date"], value=c["count"]) for c in dates],
            )
        )

    return results


class UnitType(graphene.ObjectType):
    name = graphene.String()
    value = graphene.Int()


class DashUnitType(graphene.ObjectType):
    this_month = graphene.Field(UnitType)
    last_month = graphene.Field(UnitType)
    ALL = graphene.Field(UnitType)


class DashboardReportType(graphene.ObjectType):
    top_nature = graphene.Field(DashUnitType)
    top_wilaya = graphene.Field(DashUnitType)
    top_this_month = graphene.Int()
    top_last_week = graphene.Int()
    natures = graphene.List(UnitType)
    regions = graphene.List(UnitType)


def get_by_sum(
    sum_of,
    app,
    model,
    target,
    target_getter=None,
    compared=None,
    filters=[],
    with_date=False,
    top=None,
):
    model = apps.get_model(app, model)
    includes, excludes = listToObject(filters)

    query = (
        model.objects.filter(**includes)
        .exclude(**excludes)
        .values(
            target,
        )
        .annotate(
            count=Sum(sum_of, output_field=IntegerField()),
        )
    )

    results = []
    for o in query:
        if o[target] is None:
            o[target] = "Null"
            # continue
        comparedTo = []
        dates = []
        if o.get("count", 0) >= 0 and compared:
            # ).filter(
            #     Q(**{target: o.get(target)}) & ~Q(**{compared: None})).exclude(**excludes).order_by(compared).values(compared).annotate(count=Count(compared, distinct=False))
            comparedTo = (
                model.objects.filter(**includes)
                .filter(
                    Q(**{target: o.get(target)})
                    & ~Q(**{compared: None})
                    & ~Q(**{target: None})
                )
                .exclude(**excludes)
                .order_by(compared)
                .values(compared)
                .annotate(count=Sum(sum_of, distinct=False))
            )
        if o.get("count", 0) >= 0 and with_date:
            dates = (
                model.objects.filter(**includes)
                .exclude(**excludes)
                .filter(Q(**{target: o.get(target)}) & ~Q(**{"date": None}))
                .order_by("date")
                .values("date")
                .annotate(count=Count("date"))
            )

        results.append(
            NameValue(
                name=o[target],
                value=o["count"],
                compared_to=[
                    NameValue(name=c[compared], value=c["count"]) for c in comparedTo
                ],
                dates=[NameValue(name=c["date"], value=c["count"]) for c in dates],
            )
        )
    results.sort(key=lambda x: x.value, reverse=True)
    print(top)
    if top is not None and top > 0:
        if target == "date__year":
            results = results[:top]
            results.sort(key=lambda x: x.name, reverse=False)
        else:
            return results[:top]
    if target == "date__year":
        results.sort(key=lambda x: x.name, reverse=False)

    return results


def get_by_method(
    field,
    app,
    model,
    target,
    target_getter=None,
    compared=None,
    filters=[],
    with_date=False,
    top=None,
    func="Sum",
    info=None,
):
    Func = Sum
    if func == "Avg":
        Func = Avg
    model = apps.get_model(app, model)
    includes, excludes = listToObject(filters)
    queryset = get_queryset(info, app, model.__name__, includes)
    # model.objects.filter(**includes).exclude(**excludes)
    query = (
        # model.objects.filter(**includes)
        queryset.exclude(**excludes)
        .values(
            target,
        )
        .annotate(
            count=Func(field, output_field=IntegerField()),
        )
        .order_by("-count")
    )
    if top and top > 0:
        query = query[:top]
    results = []
    for o in query:
        if o[target] is None:
            o[target] = "Undéfini"
            # continue
        comparedTo = []
        dates = []
        if o.get("count", 0) >= 0 and compared:
            # ).filter(
            #     Q(**{target: o.get(target)}) & ~Q(**{compared: None})).exclude(**excludes).order_by(compared).values(compared).annotate(count=Count(compared, distinct=False))
            comparedTo = (
                model.objects.filter(**includes)
                .filter(
                    Q(**{target: o.get(target)})
                    & ~Q(**{compared: None})
                    & ~Q(**{target: None})
                )
                .exclude(**excludes)
                .order_by(compared)
                .values(compared)
                .annotate(count=Func(field, distinct=False))
            )
        if o.get("count", 0) >= 0 and with_date:
            dates = (
                model.objects.filter(**includes)
                .exclude(**excludes)
                .filter(Q(**{target: o.get(target)}) & ~Q(**{"date": None}))
                .order_by("date")
                .values(field, "date")
                .annotate(count=Func(field))
            )

        results.append(
            NameValue(
                name=o[target],
                value=o["count"],
                compared_to=[
                    NameValue(name=c[compared], value=c["count"]) for c in comparedTo
                ],
                dates=[NameValue(name=c["date"], value=c["count"]) for c in dates],
            )
        )
    results.sort(key=lambda x: x.value, reverse=True)

    if top is not None and top > 0:
        if target == "date__year":
            results = results[:top]
            results.sort(key=lambda x: x.name, reverse=False)
        return results

    if target == "date__year":
        results.sort(key=lambda x: x.name, reverse=False)
    return results


def get_by_count(
    info,
    app=None,
    model=None,
    target=None,
    target_getter=None,
    compared=None,
    filters=[],
    with_date=False,
    top=None,
):
    if model is None or app is None:
        return []
    model = apps.get_model(app, model)
    if not target:
        return withoutTarget(model)
    includes, excludes = listToObject(filters)
    get_queryset(info, app, model.__name__, includes)
    query = (
        get_queryset(info, app, model.__name__, includes)
        # model.objects.filter(**includes)
        .exclude(**excludes)
        .order_by(target)
        .values(target)
        .annotate(
            count=Coalesce(
                Count("*"),
                0,
            )
        )
    )
    if top and top > 0:
        query = query[:top]

    results = []
    for o in query:
        if o[target] is None:
            o[target] = "Null"
            # continue
        comparedTo = []
        dates = []
        if o.get("count") >= 0 and compared:
            # ).filter(
            #     Q(**{target: o.get(target)}) & ~Q(**{compared: None})).exclude(**excludes).order_by(compared).values(compared).annotate(count=Count(compared, distinct=False))
            comparedTo = (
                model.objects.filter(**includes)
                .filter(Q(**{target: o.get(target)}) & ~Q(**{compared: None}))
                .exclude(**excludes)
                .order_by(compared)
                .values(compared)
                .annotate(count=Count(compared, distinct=False))
            )
        if o.get("count") >= 0 and with_date:
            dates = (
                model.objects.filter(**includes)
                .exclude(**excludes)
                .filter(Q(**{target: o.get(target)}) & ~Q(**{"date": None}))
                .order_by("date")
                .values("date")
                .annotate(count=Count("date"))
            )

        results.append(
            NameValue(
                name=o[target],
                value=o["count"],
                compared_to=[
                    NameValue(name=c[compared], value=c["count"]) for c in comparedTo
                ],
                dates=[NameValue(name=c["date"], value=c["count"]) for c in dates],
            )
        )
    results.sort(key=lambda x: x.value, reverse=True)
    if top is not None and top > 0:
        return results[:top]
    return results


from libs.graphql.schema.filters import ProjectFilters
from libs.graphql.schema.types import ProjectTypes


def get_filter_class(app, model):
    model_name = model if type(model) == str else model.__name__
    filterclass = ProjectFilters[f"{model_name}Filters"]
    return filterclass


def get_type_class(app, model):
    model_name = model if type(model) == str else model.__name__
    typeclass = ProjectTypes[
        f"{model_name}Type"
    ]  # importlib.import_module(f"libs.graphql.schema.types.{model}Type")

    return typeclass


from libs.graphql.filters import from_global_filter_for_relay


def create_filterclass(_type, _filter):
    filterclass = DjangoFilterConnectionField(_type, filterset_class=_filter)
    # filter_fields = filterclass.filterset_class().__dict__["filters"]
    # filtering_args = filterclass.filtering_args
    return filterclass


def get_queryset(info, app, model, filters):
    m = apps.get_model(app, model)
    qs = m.objects.all()
    filterclass = DjangoFilterConnectionField(
        ProjectTypes[f"{model}Type"], filterset_class=ProjectFilters[f"{model}Filters"]
    )
    filter_fields = filterclass.filterset_class().__dict__["filters"]
    new_kwargs = from_global_filter_for_relay(filter_fields, filters, m)
    filterset = filterclass.filterset_class(
        data={**filters, **new_kwargs},
        queryset=qs,
        request=info.context,
    )
    qs = filterset.qs
    res = qs

    # filterclass = create_filterclass(
    #     get_type_class(app, model), get_filter_class(app, model)
    # )
    # filterset = filterclass.filterset_class(
    #     data={**filters, "entreprise": 2877},  # **new_kwargs},
    #     queryset=qs,
    #     request=info.context,
    # )
    # qs = filterset.qs

    return res


class DashboardQueries(graphene.ObjectType):
    sum_by = graphene.Field(
        ReportingSumType,
        model=graphene.String(required=True),
        app=graphene.String(required=True),
        field=graphene.String(required=True),
        filters=graphene.List(ReportVariableType),
    )

    def resolve_sum_by(self, info, app, model, field, filters=[]):
        # model = apps.get_model(app, model)
        includes, excludes = listToObject(filters)
        qs = get_queryset(info, app, model, includes)
        sum = qs.exclude(Q(**{field: None})).aggregate(sum=Sum(field))["sum"] or 0
        return ReportingSumType(value=round(sum, 2), count=qs.count())

    by_days = graphene.List(
        NameValue,
        app=graphene.String(),
        model=graphene.String(),
        month=graphene.Int(),
        year=graphene.Int(),
    )

    model_state_sum = graphene.List(
        NameValue,
        app=graphene.String(required=True),
        model=graphene.String(required=True),
        sum_of=graphene.String(),
        with_date=graphene.Boolean(required=False),
        target=graphene.String(required=False),
        compared=graphene.String(required=False),
        filters=graphene.List(ReportVariableType),
        top=graphene.Int(required=False),
    )

    model_state_with_method = graphene.List(
        NameValue,
        app=graphene.String(required=True),
        model=graphene.String(required=True),
        sum_of=graphene.String(),
        with_date=graphene.Boolean(required=False),
        target=graphene.String(required=False),
        compared=graphene.String(required=False),
        filters=graphene.List(ReportVariableType),
        top=graphene.Int(required=False),
    )

    model_state = graphene.List(
        NameValue,
        app=graphene.String(required=True),
        model=graphene.String(required=True),
        with_date=graphene.Boolean(required=False),
        target=graphene.String(required=False),
        compared=graphene.String(required=False),
        filters=graphene.List(ReportVariableType),
        top=graphene.Int(required=False),
    )

    chart_line = graphene.List(
        NameValue,
        app=graphene.String(required=True),
        model=graphene.String(required=True),
        with_date=graphene.Boolean(required=False),
        target=graphene.String(required=False),
        target_getter=graphene.String(required=False),
        compared=graphene.String(required=False),
        filters=graphene.List(ReportVariableType),
    )

    def resolve_chart_line(
        self,
        info,
        app=None,
        model=None,
        target=None,
        compared=None,
        filters=[],
    ):
        return []

    stats_event_natures_by_time = graphene.List(
        NameValue,
    )

    def resolve_by_days(self, info, app, model, month, year):
        model = apps.get_model(app, model)
        return convertToNameValue(month_details(model, month, year), "date")

    """
	return model statistic based on function (Avg,Sum...)
	"""

    model_func_state = graphene.List(
        NameValue,
        app=graphene.String(required=True),
        model=graphene.String(required=True),
        field=graphene.String(required=False),
        with_date=graphene.Boolean(required=False),
        target=graphene.String(required=False),
        compared=graphene.String(required=False),
        filters=graphene.List(ReportVariableType),
        top=graphene.Int(required=False),
        func=graphene.String(required=False),
    )

    def resolve_model_func_state(
        self,
        info,
        field,
        app,
        model,
        target,
        target_getter=None,
        compared=None,
        filters=[],
        with_date=False,
        top=None,
        func="Sum",
    ):
        if func == "Count":
            return get_by_count(
                info,
                app,
                model,
                target,
                target_getter,
                compared,
                filters,
                with_date,
                top,
            )

        return get_by_method(
            field,
            app,
            model,
            target,
            target_getter,
            compared,
            filters,
            with_date,
            top,
            func,
            info,
        )

    def resolve_model_state_sum(
        self,
        info,
        sum_of,
        app,
        model,
        target,
        target_getter=None,
        compared=None,
        filters=[],
        with_date=False,
        top=None,
    ):
        return get_by_sum(
            sum_of, app, model, target, target_getter, compared, filters, with_date, top
        )

    def resolve_model_state(
        self,
        info,
        app=None,
        model=None,
        target=None,
        target_getter=None,
        compared=None,
        filters=[],
        with_date=False,
        top=None,
    ):
        return get_by_count(
            info, app, model, target, target_getter, compared, filters, with_date, top
        )

    def resolve_model_state_with_method(
        self,
        info,
        app=None,
        model=None,
        target=None,
        target_getter=None,
        compared=None,
        filters=[],
        with_date=False,
        top=None,
        sum_of=None,
    ):
        if sum_of:
            return get_by_sum(
                sum_of,
                app,
                model,
                target,
                target_getter,
                compared,
                filters,
                with_date,
                top,
            )

        return get_by_count(
            info, app, model, target, target_getter, compared, filters, with_date, top
        )
