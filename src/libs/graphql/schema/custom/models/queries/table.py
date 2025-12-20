import functools
import importlib
import inspect
import sys

import graphene
from django.apps import apps
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django_filters.filterset import FilterSet


class CharfieldChoices(graphene.ObjectType):
    label = graphene.String()
    value = graphene.String()


def get_choices(field):
    choices = field.__dict__["choices"]
    if choices is None:
        return None
    res = []

    for c in choices:
        value, label = c
        res.append(CharfieldChoices(value=value.upper(), label=label))
    return res


class SimpleFieldType(graphene.ObjectType):
    name = graphene.String()
    title = graphene.String()
    _type = graphene.String()
    is_property = graphene.Boolean()
    required = graphene.Boolean()

    query = graphene.String()


class OptionsFieldType(SimpleFieldType):
    choices = graphene.List(CharfieldChoices)


class CharFieldType(SimpleFieldType):
    choices = graphene.List(CharfieldChoices)


class ForeignKeyFieldType(SimpleFieldType):
    query = graphene.String()
    many = graphene.Boolean()


from libs.utils.utils import rgetattr


def get_title(
    title,
    get,
):
    try:
        return f"{title}".split("/")[get]
    except:
        return title
    return title


def convert_nested(field, _type, exclude=[]):
    class_name = field.__class__.__name__

    name = field.name

    required = not field.null
    if class_name == "ManyToOneRel":
        title = get_title(rgetattr(field, "field.verbose_name"), 1)

        _type = "array"
    else:
        title = getattr(field, "verbose_name", getattr(field, "related_name", ""))

    return NestedFieldType(
        name=name,
        title=title,
        required=required,
        is_property=False,
        _type=_type,
        fields=list(
            filter(
                lambda x: x.name != field.name
                and x.name not in exclude
                and "_ptr" not in x.name,
                get_fields(field.related_model),
            )
        ),
    )


def convert_field(field):
    class_name = field.__class__.__name__

    name = field.name
    required = not field.null
    title = getattr(field, "verbose_name", "")

    if class_name == "CharField":
        if field.__dict__["choices"] is not None:
            return OptionsFieldType(
                _type="options",
                title=title,
                choices=get_choices(field),
                name=name,
                required=required,
            )
        else:
            return SimpleFieldType(
                _type=convert_simple_type(class_name),
                title=title,
                name=name,
                required=required,
            )

    if (
        class_name == "IntegerField"
        or class_name == "BigIntegerField"
        or class_name == "FileField"
        or class_name == "ImageField"
        or class_name == "TimeField"
        or class_name == "FloatField"
        or class_name == "DecimalField"
        or class_name == "BooleanField"
        or class_name == "DateField"
        or class_name == "DateTimeField"
        or class_name == "TextField"
    ):
        res = SimpleFieldType(
            _type=convert_simple_type(class_name),
            title=title,
            name=name,
            required=required,
        )
        return res
    if class_name == "ForeignKey" or class_name == "OneToOneField":
        return ForeignKeyFieldType(
            _type=convert_simple_type(class_name),
            title=get_title(title, 0),
            name=name,
            required=required,
            query=f"{field.related_model.__name__.lower()}s",
        )

    return None


def convert_manytomany(field, reversed=False):
    class_name = field.__class__.__name__
    name = field.name
    required = not field.null and not field.blank
    title = getattr(field, "verbose_name", "")

    return ForeignKeyFieldType(
        _type=convert_simple_type(class_name),
        many=True,
        title=get_title(title, 0) if not reversed else get_title(title, 1),
        name=name,
        required=required,
        query=f"{field.related_model.__name__.lower()}s",
    )


def convert_simple_type(_type):
    switcher = {
        "CharField": "text",
        "TextField": "textarea",
        "FloatField": "number",
        "IntegerField": "number",
        "DecimalField": "decimal",
        "PositiveIntegerField": "number",
        "BigIntegerField": "number",
        "DateTimeField": "datetime",
        "DateField": "date",
        "TimeField": "time",
        "BooleanField": "boolean",
        "ForeignKey": "query",
        "OneToOneField": "query",
        "FileField": "file",
        "ImageField": "file",
    }
    return switcher.get(_type, "none")


def get_properties(model):
    property_names = [
        (
            name,
            getattr(
                getattr(getattr(model, name), "fget", name), "short_description", name
            ),
        )
        for name in dir(model)
        if isinstance(getattr(model, name), property) and name != "pk"
    ]

    # property_titles = [getattr(model, name + ".fget.short_description") for name in dir(
    #     model) if isinstance(getattr(model, name, name), property)]
    # print(property_titles)
    return list(filter(lambda x: x != "pk" and x != "id", property_names))


def editables(list):
    return list(filter(lambda x: x.editable == True, list))


def properties(list):
    return list(filter(lambda x: x.is_property == True, list))


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
        # if f.__class__.__name__ == "ImageField":
        #     continue
        elif f.name not in nested:
            res.append(convert_field(f))

        if nested:
            if f.name in nested:
                if (
                    f.__class__.__name__ == "ForeignKey"
                    or f.__class__.__name__ == "OneToOneField"
                ):
                    res.append(convert_nested(f, "nested", []))

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
            res.append(convert_manytomany(f, True))

    for f in related_fields:
        if "ptr" in f.name:
            continue
        if f.name in nested:
            nes = convert_nested(f, "array", [f.field.name])
            res.append(nes)

    for p in get_properties(model):
        name, title = p
        res.append(SimpleFieldType(title=title, name=name, is_property=True))

    return res


class SimpleFieldUnions(graphene.Union):
    class Meta:
        types = (
            SimpleFieldType,
            OptionsFieldType,
            ForeignKeyFieldType,
        )


class NestedFieldType(SimpleFieldType):
    fields = graphene.List(SimpleFieldUnions)


class FieldTypesUnion(graphene.Union):
    class Meta:
        types = (
            SimpleFieldType,
            OptionsFieldType,
            ForeignKeyFieldType,
            NestedFieldType,
        )


class ChoiceType(graphene.ObjectType):
    value = graphene.String()
    label = graphene.String()


class FilterType(graphene.ObjectType):
    name = graphene.String()
    _type = graphene.String()
    options = graphene.List(graphene.String)
    query = graphene.String()
    title = graphene.String()
    choices = graphene.List(ChoiceType)


_types = {
    "ManyToManyField": "ID",
    "ForeignKey": "ID",
    "DateField": "Date",
    "DateTimeField": "DateTime",
    "CharField": "String",
    "TextField": "String",
    "IntegerField": "Int",
    "FloatField": "Float",
    "DecimalField": "Decimal",
    "BooleanField": "Boolean",
    "OneToOneField": "ID",
    "TimeField": "Time",
}


def constructChoices(choices):
    if choices is None:
        return None
    res = []
    for c in choices:
        value, label = c
        res.append({"value": value, "label": label})
    return res


def constructReturnField(res):
    choices = None
    _type = res.get_internal_type()
    query = None

    if _type == "CharField" and getattr(res, "choices", None) is not None:
        choices = getattr(res, "choices")

    if _type == "OneToOneField" or _type == "ForeignKey":
        query = f"{res.related_model.__name__.lower()}s"

    return {
        "field": res,
        "_type": _type,
        "choices": constructChoices(choices),
        "query": query,
    }


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

                # (_types[field_type], field.verbose_name, "", None)
        # print(f"Field name: {field_name}, Field type: {field_type}")
    return None


# def extractFilters(filters):
#     res = []
#     for f in filters:
#         for o in f.options:
#             res.append({FilterType(name=)})

#     return res


def class_fields(name, app, model):
    name = f"{app}.graphqls.filters.{model}"
    extra_name = f"{app}.graphqls.filters.Custom{model}"
    # Replace 'YourClassName' with the name of the class you want to retrieve
    desired_class = getattr(sys.modules[extra_name], "OtherFilters", None)

    objs = filter(
        lambda x: inspect.isclass(x.obj), inspect.getmembers(sys.modules[name])
    )

    result = []
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
                        FilterType(
                            _type=res.get("_type"),
                            title=res.get("title"),
                            query=res.get("query"),
                            choices=res.get("choices"),
                            name=f,
                            options=list(
                                map(
                                    lambda x: x if x != "exact" else "",
                                    obj._meta.__dict__["fields"][f],
                                )
                            ),
                        )
                    )


def rgetattr(obj, attr, *args):
    def _getattr(obj, attr):
        return getattr(obj, attr, *args)

    return functools.reduce(_getattr, [obj] + attr.split("."))


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

                    if res == None:
                        continue
                    if f == "net":
                        print(res.get("_type"))
                    result.append(
                        FilterType(
                            _type=res.get("_type"),
                            title=res.get("title"),
                            query=res.get("query"),
                            choices=res.get("choices"),
                            name=f,
                            options=list(
                                map(
                                    lambda x: x if x != "exact" else "",
                                    obj._meta.__dict__["fields"][f],
                                )
                            ),
                        )
                    )
                except Exception as E:
                    print(E)
    return result


from libs.graphql.schema.filters import ProjectFilters


def get_filters(app, model):
    result = []
    result.extend(get_meta_fields(ProjectFilters[f"{model}Filters"], app, model))
    _types = {
        "BooleanFilter": "Boolean",
        "CharFilter": "String",
        "NumberFilter": "Decimal",
        "DateFilter": "Date",
        "ModelChoiceFilter": "ID",
        "MultipleChoiceFilter": "[String]",
    }

    # _custom_filter = getattr(
    #     importlib.import_module(f"{app}.graphqls.filters"),
    #     f"{model}CustomFilters",
    # )

    # for b in getattr(
    #     importlib.import_module(f"{app}.graphqls.filters"),
    #     f"{model}CustomFilters",
    # ).__bases__:
    # for name, _type in _custom_filter.declared_filters.items():
    #     result.append(
    #         FilterType(
    #             name=name,
    #             title=getattr(_type, "label", ""),
    #             _type=_types[_type.__class__.__name__],
    #             options=[""],
    #         )
    #     )

    _custom_filter = ProjectFilters[f"{model}Filters"]

    # for b in getattr(
    #     importlib.import_module(f"{app}.graphqls.filters"),
    #     f"{model}CustomFilters",
    # ).__bases__:

    for name, _type in _custom_filter.declared_filters.items():
        result.append(
            FilterType(
                name=name,
                title=getattr(_type, "label", ""),
                _type=_types[_type.__class__.__name__],
                options=[""],
                query=f"{rgetattr(_type, 'queryset.model.__name__', '').lower()}s" if rgetattr(_type, "queryset.model", None) else None,
            )
        )

    return result


class TableFilterQueries(graphene.ObjectType):
    filters = graphene.List(FilterType, model=graphene.String(), app=graphene.String())

    create_form = graphene.List(
        FilterType,
        model=graphene.String(),
        app=graphene.String(),
        nested=graphene.List(graphene.String, required=False),
    )

    def resolve_create_form(self, info, app, model, nested=[]):
        model = apps.get_model(app, model)
        fields = get_fields(model, nested or [], is_form=True)
        return list(filter(lambda x: x.name not in ["polymorphic_ctype"], fields))

    def resolve_filters(self, info, app, model):
        return get_filters(app, model)


# class ModelFunctionType(graphene.ObjectType):
#     name




from libs.models.fields import get_functions, get_classmethods
def get_func(model, name):
    for f in [*get_functions(model),*get_classmethods(model)]:
        if f.__name__ == name:
            return f
    return None


def get_params(function):
    signature = inspect.signature(function)
    return [b for a, b in signature.parameters.items() if a != "self"]


class ParamsType(graphene.ObjectType):
    name = graphene.String()
    _type = graphene.String()


class FuncType(graphene.ObjectType):
    params = graphene.List(ParamsType)
    _type = graphene.String()


from libs.models.fields import get_classmethods, not_ptr


class TableCreationQueries(graphene.ObjectType):
    create_table = graphene.List(
        FieldTypesUnion,
        app_name=graphene.String(required=True),
        model_name=graphene.String(required=True),
        nested=graphene.List(graphene.String, required=False),
        get_field=graphene.String(required=False),
    )
    permissions = graphene.List(
        graphene.String,
        app_name=graphene.String(required=True),
        model_name=graphene.String(required=True),
    )
    create_function = graphene.Field(
        FuncType,
        model=graphene.String(),
        app=graphene.String(),
        func_name=graphene.String(),
    )

    def resolve_create_function(self, info, app, model, func_name):
        m = apps.get_model(app, model)
        func = get_func(m, func_name)
        params = get_params(func)
        if func is None:
            return
        # if type(_type) == list:
        #     return graphene.List(convertInputTypeToGraphene(_type[0]).__class__)

        return FuncType(
            params=[
                ParamsType(name=p.name, _type=f"[{p.annotation[0].__name__}]" if isinstance(p.annotation, list) else p.annotation.__name__) for p in params
            ],
            _type=f"Generated{model.capitalize()}{func.__name__.capitalize()}Input",
        )

    def resolve_permissions(self, info, app_name, model_name):
        if info.context.user.is_authenticated:
            all_permissions = Permission.objects.filter(
                user=info.context.user,
                content_type=ContentType.objects.get_for_model(
                    apps.get_model(app_name, model_name)
                ),
            )
            # , content_type=ContentType.objects.get(
            # app_label='entity', model='Etablissement')
            return all_permissions.values_list("codename", flat=True)
        else:
            return []
        # Permission.objects.filter(
        # content_type__app_label=app_name, content_type__model=model_name)
        return

    def resolve_create_table(
        self, info, app_name, model_name, nested=[], get_field=None
    ):
        model = apps.get_model(app_name, model_name)
        fields = get_fields(model, nested or [])

        if get_field:
            return list(filter(lambda x: x.name == get_field, fields))
        return not_ptr(fields)


class TableFieldType(graphene.ObjectType):
    name = graphene.String()
    ordering = graphene.String()
    title = graphene.String()


class TableQueries(graphene.ObjectType):
    columns = graphene.List(TableFieldType)
