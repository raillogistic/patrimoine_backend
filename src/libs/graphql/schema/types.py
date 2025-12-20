import graphene
from graphene.utils.module_loading import lazy_import
from libs.graphql.types import CustomConnection, CustomDjangoObjectType, CustomNode
from libs.models.fields import *
from libs.models.fields import (
    field_by_numbers,
    get_decimals,
    get_reversed_manytoone_fields,
)
from libs.models.func import avg_of, sum_of

from .utils import all_mdls, get_fields_and_properties_for_graphql


def properties(
    model,
):
    props = get_fields_and_properties_for_graphql(
        model,
    )
    res = {}
    for p in props:
        name, title, _type = p
        res[name] = _type
    return res


from graphene.types.utils import get_type


def relatedfields(model):
    props = get_foreignkey(model)

    res = {}
    for f in props:
        if f.model.__name__ == model.__name__:
            continue

        if f.related_model._meta.app_label == "auth":
            continue
        if f.name == "polymorphic_ctype":
            continue
        res[f"{f.name}"] = graphene.Field(
            f"{module_name}.{f.related_model.__name__}Type"
        )
    return res


def resolve_all(name):
    def resolve_field(self, info, **kwargs):
        return getattr(self, name).all()

    return resolve_field


def reverse_fields(model):
    def resolve_count(name):
        def resolve_field(self, info, **kwargs):
            return getattr(self, name).count()

        return resolve_field

    reversed = get_related_fields(model)

    res = {}

    for field in reversed:
        if model.__name__ == "Facture" and field.name == "items":
            print(field.related_model)
        if field.related_model._meta.app_label == "auth":
            continue
        name = field.name
        if type(field).__name__ == "OneToOneRel":
            res[name] = graphene.Field(
                f"{module_name}.{field.related_model.__name__}Type"
            )
        else:
            get_name = field.name
            if not field.related_name:
                get_name = f"{field.related_model.__name__.lower()}_set"
            res[get_name] = graphene.List(
                f"{module_name}.{field.related_model.__name__}Type"
            )
            res[f"{get_name}_count"] = graphene.Int()
            res[f"resolve_{get_name}"] = resolve_all(get_name)
            res[f"resolve_{get_name}_count"] = resolve_count(f"{get_name}")
    return res


def manytomany(model):
    def resolve_count(name):
        def resolve_field(self, info, **kwargs):
            return getattr(self, name).count()

        return resolve_field

    manys = get_many_to_many_fields(model)
    res = {}
    for many in manys:
        if many.related_model._meta.app_label == "auth":
            continue
        res[f"{many.name}"] = graphene.List(
            f"{module_name}.{many.related_model.__name__}Type"
        )
        res[f"resolve_{many.name}"] = resolve_all(many.name)
        res[f"{many.name}_count"] = graphene.Int()
        res[f"resolve_{many.name}_count"] = resolve_count(f"{many.name}")
    return res


def get_decimal_fields(model):
    decimals = get_decimals(model)
    res = {}
    for d in decimals:
        res[f"{d.name}"] = graphene.Decimal(required=False)
    return res


def resolve_avg(f1, f2):
    def resolve_avg(self, info, **kwargs):
        return avg_of(self, f1, f2)

    return resolve_avg


def resolve_sum(f1, f2):
    def resolve_sum(self, info, **kwargs):
        return sum_of(self, f1, f2)

    return resolve_sum


def other(model):
    res = {}
    floats = get_reversed_manytoone_fields(model)
    for f in floats:
        for f2 in field_by_numbers(
            f.related_model,
        ):
            res[f"{f.name}__{f2.name}__avg"] = graphene.Float()
            res[f"{f.name}__{f2.name}__sum"] = graphene.Float()
            res[f"resolve_{f.name}__{f2.name}__avg"] = resolve_avg(f.name, f2.name)
            res[f"resolve_{f.name}__{f2.name}__sum"] = resolve_sum(f.name, f2.name)
    return res


from django.db import models


def get_changes(instance, current_record, previous_record):
    """
    Compare two historical records of a model instance to get field changes.
    """
    changes = {}
    for field in instance._meta.fields:
        try:
            field_name = field.name
            old_value = getattr(previous_record, field_name, None)
            new_value = getattr(current_record, field_name, None)

            # Handle ForeignKey fields
            if isinstance(field, models.ForeignKey):
                old_pk = getattr(previous_record, f"{field_name}_id", None)
                new_pk = getattr(current_record, f"{field_name}_id", None)

                if old_pk is not None:
                    old_value = (
                        str(field.related_model.objects.get(pk=old_pk))
                        if field.related_model.objects.filter(pk=old_pk).exists()
                        else None
                    )
                if new_pk is not None:
                    new_value = (
                        str(field.related_model.objects.get(pk=new_pk))
                        if field.related_model.objects.filter(pk=new_pk).exists()
                        else None
                    )
        except:
            pass

        # Track changes
        if old_value != new_value:
            changes[field_name] = (old_value, new_value)

    return changes


from django.contrib.auth.models import User


class HistoryType(graphene.ObjectType):
    date = graphene.Date()

    def resolve_date(self, info):
        return self["history_date"]

    _type = graphene.String()

    def resolve__type(self, info):
        return self["history_type"]

    changes = graphene.List(graphene.String)
    user = graphene.String()
    pk = graphene.String()

    def resolve_user(self, info):
        if self["history_user_id"]:
            try:
                user = User.objects.get(id=self["history_user_id"])
                return user.username
            except:
                return ""
        return

    def resolve_changes(self, info):
        res = []
        for k, v in self.get("changes", {}).items():
            res.append(f"{k} : {v[0]} → {v[1]}")
        return res


def resolve_histories():
    def resolve_history(
        self,
        info,
    ):
        histories = self.history.all()
        res = []
        for i in range(1, len(histories)):
            changes = get_changes(self, histories[i - 1], histories[i])
            res.append({"changes": changes, **histories[i].__dict__, "pk": i})
        return res

    return resolve_history


def construct_fields(
    model,
):
    if "Historical" in model.__name__:
        return
    base = model.__bases__[0]
    if base.__name__ == "Model" or base.__name__ == "PolymorphicModel":
        base = None
    props = properties(
        model,
    )

    many = manytomany(model)
    related = relatedfields(model)
    revs = reverse_fields(model)
    oths = other(model)
    decimals = get_decimal_fields(model)

    res = {
        **props,
        **many,
        **related,
        **revs,
        **oths,
        **decimals,
    }
    if hasattr(model, "history"):
        res["history"] = graphene.List(HistoryType)
        res["resolve_history"] = resolve_histories()

    return res


from .filters import ProjectFilters


def createMeta(
    model,
):
    # filterset_class = filters.EntrepriseFilters
    attr = {
        "model": model,
        "connection_class": CustomConnection(),
        "name": f"{model.__name__}Type",
        "fields": "__all__",
        "interfaces": (CustomNode,),
        "filterset_class": ProjectFilters[f"{model.__name__}Filters"],
        "convert_choices_to_enum": False,
    }
    meta_class = type("MetaClass", (), attr)
    return meta_class


module_name = __name__
ProjectTypes = {}

from .utils import get_class_by_name


def createType(
    model,
):
    class_name = f"{model.__name__}Type"
    if "Historical" in model.__name__:
        return
    base = model.__bases__[0]

    if (
        base.__name__ == "Model"
        or base.__name__ == "PolymorphicModel"
        or base.__name__ == "HistoricalChanges"
        or getattr(base._meta, "abstract", False)
    ):
        base = None
    if base:
        base_name = base.__name__
        base_name = f"{base_name}"
        base_classes = (
            ProjectTypes[f"{base_name}Type"],
            CustomDjangoObjectType,
        )
    else:
        base_classes = (CustomDjangoObjectType,)

    base_classes = (*base_classes,)
    custom_types = get_class_by_name(
        f"{model._meta.app_label}.graphqls.types", f"{model.__name__}CustomType"
    )
    attributes = {
        "Meta": createMeta(
            model,
        ),
        "designation": graphene.String(),
        **construct_fields(
            model,
        ),
        **custom_types.__dict__,
    }

    MyDynamicClass = type(class_name, base_classes, attributes)
    return MyDynamicClass


import sys

from libs.utils.utils import register_module

from .utils import sorted_models

for m in sorted_models():
    if getattr(m._meta, "abstract", False):
        continue

    cls = createType(m)
    name = f"{m.__name__}Type"
    ProjectTypes[name] = cls
    register_module(
        module_name,
        cls,
        f"{m.__name__}Type",
    )

__all__ = ProjectTypes
