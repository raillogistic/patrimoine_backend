import functools

from django.apps import apps
from django.db import models
from libs.graphql.queries.converters import (
    convert_field,
    convert_manytomany,
    convert_nested,
)
from libs.models.fields import get_properties

from .types import AppType, FieldType, ModelType, RelatedFieldType


def remove_history_fields(arr):
    """return history fields in History lib"""
    fields = [
        "history_id",
        "history_date",
        "history_change_reason",
        "history_type",
        "history_user",
    ]
    res = []
    for a in arr:
        if a in fields:
            continue
        else:
            res.append(a)
    return res


def all_models(app_name):
    models = []
    for m in list(apps.all_models[app_name].values()):
        model = apps.get_model(app_name, m.__name__)
        if getattr(model, "__name__", False):
            models.append(
                {
                    "name": model.__name__,
                }
            )
    return models


def all_apps():
    res = []
    all_apps = apps.app_configs.keys()
    others = [
        "polymorphic",
        "simple_history",
        "field_history",
        "humanize",
        "rest_framework",
        "refresh_token",
        "authentication",
        "admin",
        "corsheaders",
        "auth",
        "contenttypes",
        "sessions",
        "messages",
        "staticfiles",
        "graphene_django",
        "corsheaders" "User",
    ]
    for a in all_apps:
        if a in others:
            continue
        res.append({"name": a, "models": all_models(a)})
    return res


##############################################################


def get_fields(model, nested=[], is_form=False):
    res = []

    related_fields = [
        f
        for f in model._meta.get_fields()
        if f.auto_created and not f.concrete and not f.related_model == model
    ]
    fields = list(
        filter(lambda x: x.name != "id" or x.name == "created_at", model._meta.fields)
    )
    #  "id" and (x.editable or x.name == "created_at"), model._meta.fields))

    many_to_many_fields = [
        field
        for field in model._meta.get_fields()
        if isinstance(field, models.ManyToManyField)
    ]
    reversed_m2m_names = [
        relation
        for relation in model._meta.related_objects
        if isinstance(relation.field, models.ManyToManyField)
    ]
    for f in fields:
        if "ptr" in f.name:
            continue
        if f.__class__.__name__ == "ImageField":
            continue
        elif f.name not in nested:
            res.append(convert_field(f))

        if nested:
            if f.name in nested:
                if (
                    f.__class__.__name__ == "ForeignKey"
                    or f.__class__.__name__ == "OneToOneField"
                ):
                    res.append(convert_nested(f, "nested", get_fields, []))

    for f in many_to_many_fields:
        if "ptr" in f.name:
            continue
        if f.name in nested:
            res.append(convert_nested(f, "array", []))
        else:
            res.append(
                convert_manytomany(
                    f,
                )
            )

    for f in reversed_m2m_names:
        if "ptr" in f.name:
            continue
        if f.name in nested:
            res.append(convert_nested(f, "array", []))
        else:
            res.append(
                convert_manytomany(
                    f,
                )
            )

    for f in related_fields:
        if "ptr" in f.name:
            continue
        if f.name in nested:
            nes = convert_nested(f, "array", [f.field.name])
            res.append(nes)

    if is_form:
        return res

    for p in get_properties(model):
        name, title = p
        res.append({"title": title, "name": name, "is_property": True})

    return res


def access_to_depth_field(model, field):
    # extract nested fields
    fields = field.split("__")
    first = fields[0]
    res = model._meta.get_field(first).related_model

    for f in fields[1:]:
        # check if the field is primitive or foreign relation
        if hasattr(res, "related_model"):
            res = res.related_model._meta.get_field(f)
        else:
            res = res._meta.get_field(f)

    if res:
        return constructReturnField(res)

    else:
        return None


#################################################################


def get_field_type(app, model, ff):
    m = apps.get_model(app, model)
    fields = m._meta.get_fields()
    # related_fields = [f for f in m._meta.get_fields()
    #                   if f.auto_created and not f.concrete and not f.related_model == model]
    # print("related", related_fields)

    fields = list(
        filter(lambda x: x.name != "id", [*m._meta.fields, *m._meta.many_to_many])
    )
    # print(type(fields))
    for field in fields:
        field_name = field.name
        field_type = field.get_internal_type()  # Get the field's internal type
        if "__" in ff:
            res = access_to_depth_field(m, ff)

            if res:
                return {
                    "_type": _types[res.get("_type")],
                    "title": getattr(res.get("field"), "verbose_name", ""),
                    "query": res.get("query", None),
                    "choices": res.get("choices", None),
                }
                # (_types[res.get('_type')], res.get('field').verbose_name, "", res.get('choices'))
            else:
                return None
            # print(type(mar._meta.get_field(_type)))

        if field_name == ff:
            if field.related_model is not None:
                return {
                    "_type": _types[field_type],
                    "title": getattr(field, "verbose_name", ""),
                    "query": f"{field.related_model.__name__.lower()}s",
                    "choices": None,
                }
                # _types[field_type], field.verbose_name, f"{field.related_model.__name__.lower()}s", None
            else:
                choices = None
                if (
                    field_type == "CharField"
                    and getattr(field, "choices", None) is not None
                ):
                    choices = constructChoices(getattr(field, "choices"))

                return {
                    "_type": _types[field_type],
                    "title": getattr(field, "verbose_name", ""),
                    "query": "",
                    "choices": choices,
                }

    return None


##########################################################################

import inspect
import sys


def class_fields(name, app, model):
    result = []
    name = f"{app}.graphqls.filters.{model}"
    extra_name = f"{app}.graphqls.filters.Custom{model}"
    # Replace 'YourClassName' with the name of the class you want to retrieve
    desired_class = getattr(sys.modules[extra_name], "OtherFilters", None)
    objs = filter(
        lambda x: inspect.isclass(x.obj), inspect.getmembers(sys.modules[name])
    )
    for name, obj in inspect.getmembers(sys.modules[name]):
        if inspect.isclass(obj):
            if name == f"{model}Filters":
                for f in obj._meta.__dict__["fields"]:
                    if f.endswith("_ptr"):
                        continue
                    # pass ID and polymorphic
                    if f == "id" or f == "polymorphic_ctype":
                        continue
                    # append results
                    res = get_field_type(app, model, f)
                    # pass if unkown type
                    if res == None:
                        continue

                    result.append(
                        {
                            "_type": res.get("_type"),
                            "title": res.get("title"),
                            "query": res.get("query"),
                            "choices": res.get("choices"),
                            "name": f,
                            "options": list(
                                map(
                                    lambda x: x if x != "exact" else "",
                                    obj._meta.__dict__["fields"][f],
                                )
                            ),
                        }
                    )


##########################################################################


def get_meta_fields(obj, app, model):
    result = []
    if hasattr(obj, "_meta"):
        if obj._meta.__dict__.get("fields", []):
            for f in obj._meta.__dict__.get("fields", []):
                # print(f)
                try:
                    if f.endswith("_ptr"):
                        continue
                    # pass ID and polymorphic
                    if f == "id" or f == "polymorphic_ctype":
                        continue
                    # append results
                    res = get_field_type(app, model, f)
                    if f == "beneficier":
                        print(res)
                    # pass if unkown type
                    if res == None:
                        continue

                    result.append(
                        {
                            "_type": res.get("_type"),
                            "title": res.get("title"),
                            "query": res.get("query"),
                            "choices": res.get("choices"),
                            "name": f,
                            "options": list(
                                map(
                                    lambda x: x if x != "exact" else "",
                                    obj._meta.__dict__["fields"][f],
                                )
                            ),
                        }
                    )
                except Exception as E:
                    print(E)
    return result


##########################################################################


def get_functions(model):
    child_class_functions = inspect.getmembers(model, inspect.isfunction)
    child_class_name = model.__name__
    child_class_methods = [
        method
        for name, method in child_class_functions
        if child_class_name in getattr(method, "__qualname__", "") and name != "save"
    ]
    return child_class_methods


############################################################################


def get_func(model, name):
    for f in get_functions(model):
        if f.__name__ == name:
            return f
    return None


###############################################################################


def get_params(function):
    signature = inspect.signature(function)
    return [b for a, b in signature.parameters.items() if a != "self"]


###############################################################################


def all_fields(app, model, exclude=None):
    res = []
    _model = apps.get_model(
        app,
        model,
    )
    fields = list(filter(lambda x: x.name != "id", _model._meta.fields))
    reverse_fields = {
        f.name: f
        for f in _model._meta.get_fields()
        if f.auto_created and not f.concrete
    }
    property_names = [
        name for name in dir(_model) if isinstance(getattr(model, name, ""), property)
    ]

    for f in fields:
        if f.name == "history":
            continue
        if f.name == exclude:
            continue
        related = None
        if getattr(f, "related_model", False):
            related = getattr(getattr(f, "related_model", False), "__name__", "")
            if related:
                app_label = getattr(
                    ContentType.objects.get_for_model(f.related_model),
                    "app_label",
                    False,
                )
                nested = apps.get_model(
                    app_label,
                    f.related_model.__name__,
                )
                related = RelatedFieldType(
                    fields=[
                        FieldType(
                            null=n.null,
                            verbose_name=n.verbose_name,
                            _type=type(n).__name__,
                            name=n.name,
                            column=n.column,
                        )
                        for n in list(
                            filter(lambda x: x.name != "id", nested._meta.fields)
                        )
                    ],
                    model=ModelType(name=related, app=app),
                )

        res.append(
            FieldType(
                verbose_name=f.verbose_name,
                name=f.name,
                column=f.column,
                related=related,
                _type=type(f).__name__,
                null=f.null,
            )
        )

    for p in get_properties(
        _model,
    ):
        name, title = p
        res.append(FieldType(verbose_name=title, name=name, column=name))

    for name, field in reverse_fields.items():
        app_label = getattr(
            ContentType.objects.get_for_model(field.related_model), "app_label", False
        )
        nested = all_fields(
            app_label, field.related_model.__name__, exclude=field.field.name
        )

        res.append(
            FieldType(
                verbose_name=field.name,
                null=f.null,
                name=name,
                related=RelatedFieldType(
                    fields=nested,
                    model=ModelType(name=field.related_model.__name__, app=app),
                ),
                _type=type(field).__name__,
            )
        )
    return res
