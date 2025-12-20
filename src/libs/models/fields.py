import functools
import importlib
from turtle import mode

from django.db import models


def rgetattr(obj, attr, *args):
    """get nested atributes  by using .
    for example: get(obj,'person.function.grade.salary....')
    """

    def _getattr(obj, attr):
        return getattr(obj, attr, *args)

    return functools.reduce(_getattr, [obj] + attr.split("."))


def get_field_by_name(module_path, class_name, field_name, default=None):
    module = importlib.import_module(module_path)
    class_obj = getattr(module, class_name)
    if rgetattr(class_obj, field_name, None):
        field_value = rgetattr(class_obj, field_name)
        return field_value
    else:
        return default


def not_ptr(res):
    """exclude polymorphic field"""
    return list(
        filter(
            lambda f: f is not None
            and "ptr" not in f.name
            and f.name != "polymorphic_ctype",
            res,
        )
    )


def exclude(fields, exclude_list, exclude_by="name"):
    """Excluded fields from a list by parameter"""
    res = []
    for field in fields:
        if getattr(field, exclude_by) in exclude_list:
            continue
        else:
            res.append(field)
    return res


###########################################################################
from typing import List, get_type_hints


def remove_history_fields(arr):
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


import graphene
from django.db.models import Model


def get_fields_and_properties_with_types(model, types={}):
    field_names = remove_history_fields([f.name for f in model._meta.fields])

    def access_type(model, name):
        return get_type_hints(getattr(getattr(model, name), "fget", {})).get(
            "return", str
        )

    def access_title(model, name):
        return getattr(
            getattr(getattr(model, name), "fget", name), "short_description", name
        )

    def _types(
        name,
        _type,
    ):
        is_model = False
        is_list = False
        if hasattr(_type, "__args__"):
            _type = _type.__args__[0]
            is_list = True
            if issubclass(_type, Model):
                is_model = True
        else:
            if issubclass(_type, Model):
                is_model = True

        if is_model:
            if is_list:
                return graphene.List(types.get(f"{_type.__name__}", graphene.String()))
            else:
                print(
                    _type.__name__,
                    "dsmldsmdlsmdl",
                    types.get(
                        _type.__name__,
                    ),
                    "None",
                )
                return graphene.Field(types.get(f"{_type.__name__}", graphene.String()))
        else:
            _type = _type.__name__

            # print("qqqqqqqqqq", name, _type.__class__.__name__)
        get_types = {
            "_empty": graphene.List(graphene.String)
            if is_list
            else graphene.String(source=f"{name}"),
            "str": graphene.List(graphene.String)
            if is_list
            else graphene.String(source=f"{name}"),
            "int": graphene.List(graphene.Int)
            if is_list
            else graphene.Int(source=f"{name}"),
            "float": graphene.List(graphene.Float)
            if is_list
            else graphene.Float(source=f"{name}"),
            "bool": graphene.List(graphene.Boolean)
            if is_list
            else graphene.Boolean(source=f"{name}"),
            "date": graphene.Date(),
        }
        return get_types[_type]

    fields = [
        name
        for name in dir(model)
        if isinstance(getattr(model, name), property) and name != "pk"
    ]
    res = []

    for name in fields:
        try:
            res.append(
                (
                    name,
                    access_title(model, name),
                    _types(
                        name,
                        access_type(model, name),
                    ),
                )
            )
        except Exception as E:
            print(name, E)
    return res


def get_properties(model):
    """Extract properties from a given django model
    return a list of properties with title
    """

    def access_type(model, name):
        try:
            return get_type_hints(getattr(getattr(model, name), "fget", {})).get(
                "return", str
            )
        except Exception as ex:
            return "str"

    property_names = [
        {
            "name": name,
            "title": getattr(
                getattr(getattr(model, name), "fget", name), "short_description", name
            ),
            "_type": access_type(model, name),
        }
        for name in dir(model)
        if isinstance(getattr(model, name), property) and name != "pk"
    ]

    return list(filter(lambda x: x != "pk" and x != "id", property_names))


###########################################################################


def get_many_to_many_fields(model):
    many_to_many_fields = [
        field
        for field in model._meta.get_fields()
        if isinstance(field, models.ManyToManyField)
    ]
    return not_ptr(many_to_many_fields)


##########################################################################


def get_reversed_m2m_names(model):
    """get reversed manytomany field"""
    reversed_m2m_names = [
        relation
        for relation in model._meta.related_objects
        if isinstance(relation.field, models.ManyToManyField)
    ]
    return not_ptr(reversed_m2m_names)


def get_related_fields(
    model,
):
    related_fields = [
        f
        for f in model._meta.get_fields()
        if f.auto_created and not f.concrete and not f.related_model == model
    ]
    return not_ptr(exclude(related_fields, []))


def get_reversed_manytoone_fields(
    model,
):
    related_fields = [
        f
        for f in model._meta.get_fields()
        if f.auto_created
        and not f.concrete
        and not f.related_model == model
        and type(f).__name__ == "ManyToOneRel"
    ]
    return not_ptr(exclude(related_fields, []))


def get_reversed_onetoone_fields(
    model,
):
    related_fields = [
        f
        for f in model._meta.get_fields()
        if f.auto_created
        and not f.concrete
        and not f.related_model == model
        and type(f).__name__ == "OneToOneRel"
    ]
    return not_ptr(exclude(related_fields, []))


##########################################################################


def get_simplefields(model):
    return filter(
        lambda x: x.__class__.__name__ != "ForeignKey"
        and x.__class__.__name__ != "OneToOneField",
        not_ptr(
            exclude(
                model._meta.fields,
                [
                    "id",
                    "polymorphic_ctype",
                ],
            )
        ),
    )


def get_foreignkey(model):
    return filter(
        lambda x: x.__class__.__name__ == "ForeignKey"
        or x.__class__.__name__ == "OneToOneField",
        # or x.__class__.__name__ == "OneToOneRel",
        [
            *not_ptr(
                exclude(
                    model._meta.fields,
                    [
                        "id",
                        "polymorphic_ctype",
                    ],
                )
            ),
            *get_related_fields(model),
        ],
    )


# def get_simplefields(model):
#     return not_ptr(exclude(model._meta.fields, ["id", "polymorphic_ctype", "history"]))


##########################################################################


def get_all_fields(model):
    return [
        *get_simplefields(model),
        *get_foreignkey(model),
        *get_related_fields(model),
        *get_many_to_many_fields(model),
        *get_reversed_m2m_names(model),
    ]


def get_all_fields_with_props(model):
    return [
        *get_simplefields(model),
        *get_related_fields(model),
        *get_many_to_many_fields(model),
        *get_reversed_m2m_names(model),
        *get_properties(model),
    ]


def field_by_type(model, _type):
    return list(
        filter(
            lambda x: type(x).__name__ == _type,
            [
                *get_simplefields(model),
                *get_related_fields(model),
                *get_many_to_many_fields(model),
                *get_reversed_m2m_names(model),
                *get_properties(model),
            ],
        )
    )


def field_by_numbers(
    model,
):
    return list(
        filter(
            lambda x: type(x).__name__ == "IntegerField"
            or type(x).__name__ == "FloatField"
            or type(x).__name__ == "DecimalField",
            [
                *get_simplefields(model),
                *get_related_fields(model),
                *get_many_to_many_fields(model),
                *get_reversed_m2m_names(model),
                *get_properties(model),
            ],
        )
    )


def get_decimals(
    model,
):
    return list(
        filter(
            lambda x: type(x).__name__ == "DecimalField",
            [
                *get_simplefields(model),
                *get_related_fields(model),
                *get_many_to_many_fields(model),
                *get_reversed_m2m_names(model),
                *get_properties(model),
            ],
        )
    )


def get_editable_fields(model):
    return list(
        filter(
            lambda x: x.name not in ["created_at"],
            [
                *get_simplefields(model),
                *get_related_fields(model),
                *get_many_to_many_fields(model),
                *get_reversed_m2m_names(model),
            ],
        )
    )


import inspect
from datetime import date, datetime


def convertInputType(_type):
    if issubclass(_type, bool):
        return "graphene.Boolean()"
    if issubclass(_type, str):
        return "graphene.String()"
    if issubclass(_type, int):
        return "graphene.Int()"
    if issubclass(_type, float):
        return "graphene.Float()"
    if issubclass(_type, date):
        return "graphene.Date()"
    if issubclass(_type, datetime):
        return "graphene.DateTime()"
def convertToGraphreneType(_type):
    if issubclass(_type, bool):
        return graphene.Boolean()
    if issubclass(_type, str):
        return graphene.String()
    if issubclass(_type, int):
        return graphene.Int()
    if issubclass(_type, float):
        return graphene.Float()
    if issubclass(_type, date):
        return graphene.Date()
    if issubclass(_type, datetime):
        return graphene.DateTime()

def get_graphene_type(method):
    _type = convertToGraphreneType(returning_type(method))
    if _type is None:
        return graphene.String()
    return _type

def returning_type(method):
    """Get the return type of a method"""
    if hasattr(method, "__annotations__") and "return" in method.__annotations__:
        return method.__annotations__["return"]
    else:
        return str  # Default to string if no return type is specified


def input_params(params):
    res = "  id = graphene.String()\n"
    for param in params:
        res = res + f"      {param.name} = {convertInputType(param.annotation)} \n"
    return res


def declare_function_mutations(funcs, model_name):
    if len(funcs) == 0:
        return "\tpass"
    res = ""
    for f in funcs:
        res = (
            res
            + f"\t{model_name.lower()}__{f.__name__} = Generated{f.__name__.capitalize()}.Field()\n"
        )
    return res


def get_functions(model):
    child_class_functions = inspect.getmembers(model, inspect.isfunction)
    child_class_name = model.__name__
    child_class_methods = [
        method
        for name, method in child_class_functions
        if child_class_name in getattr(method, "__qualname__", "") and name != "save"
    ]
    return child_class_methods

import inspect

def get_classmethods(model_class):
    classmethods = []
    module_name = model_class.__module__
    for name, attr in inspect.getmembers(model_class):
        if inspect.ismethod(attr) and attr.__self__ is model_class:
            if name.startswith('__'):
                continue
            method_module = attr.__module__
            if (method_module == module_name or 
                (not method_module.startswith('django.') and 
                 not method_module.startswith('polymorphic.'))):
                classmethods.append(attr)
            
    return classmethods



# def get_classmethods(model):
#     classmethods = []
#     child_class_functions = inspect.getmembers(model, inspect.isfunction)
    
#     child_class_name = model.__name__
#     for name, method in child_class_functions:
#         if child_class_name in getattr(method, "__qualname__", "") and name != "save":
#             if model.__name__=="ControleTechnique":#isinstance(method, classmethod):
#                 print(isinstance(method, staticmethod))
#             classmethods.append(method)

#     return classmethods




# def get_classmethods(model):
#     classmethods = []
#     for name, member in inspect.getmembers(model):
#         if isinstance(member, classmethod):
#             if name != "save":
#                 classmethods.append(member.__func__)
#     return classmethods

    
def get_params(function):
    signature = inspect.signature(function)
    return [b for a, b in signature.parameters.items() if a != "self"]


def createMutationFromFunction(func, app_name, model_name):
    params = get_params(func)
    res = f"""

class Generated{func.__name__.capitalize()}Input(graphene.InputObjectType):
    {input_params(params)}
    
class Generated{func.__name__.capitalize()}(graphene.Mutation):
    class Input:
        input = graphene.Argument(Generated{func.__name__.capitalize()}Input)
    ok = graphene.Boolean()
    message = graphene.String()
    
    def mutate(self,info,input):
        id = input.get('id',None)
        if not id:
            return Generated{func.__name__.capitalize()}(ok=False,message="l'élément n'est pas trouvé")
        try:
            obj = {model_name}.objects.get(pk=id)
        except ObjectDoesNotExist:
            return Generated{func.__name__.capitalize()}(ok=False,message="l'élément n'est pas trouvé")
        try:
            obj.{func.__name__}({','.join([ f"{p.name}=input.get('{p.name}',None)" for p in params])})
        except Exception as E:
            return Generated{func.__name__.capitalize()}(ok=True,message=str(E))

        return Generated{func.__name__.capitalize()}(ok=True,message="l'opération s'est terminée avec succès")
        
    """

    return res


##########################################################################


# def get_fields(model, nested=[], is_form=False):
#     res = []
#     related_fields = get_related_fields(model)
#     fields = get_simplefields(model)
#     many_to_many_fields = get_many_to_many_fields(model)
#     reversed_m2m_names = get_reversed_m2m_names(model)

#     for f in fields:
#         if f.__class__.__name__ == "ImageField":
#             continue
#         elif f.name not in nested:
#             res.append(convert_field(f))

#         if nested:
#             if f.name in nested:
#                 if (
#                     f.__class__.__name__ == "ForeignKey"
#                     or f.__class__.__name__ == "OneToOneField"
#                 ):
#                     res.append(convert_nested(f, "nested", get_fields, []))

#     for f in many_to_many_fields:
#         if f.name in nested:
#             res.append(convert_nested(f, "array", []))
#         else:
#             res.append(
#                 convert_manytomany(
#                     f,
#                 )
#             )

#     for f in reversed_m2m_names:
#         if f.name in nested:
#             res.append(convert_nested(f, "array", []))
#         else:
#             res.append(
#                 convert_manytomany(
#                     f,
#                 )
#             )

#     for f in related_fields:
#         if f.name in nested:
#             nes = convert_nested(f, "array", [f.field.name])
#             res.append(nes)

#     for p in get_properties(model):
#         name, title = p
#         res.append({"title": title, "name": name, "is_property": True})

#     return res
