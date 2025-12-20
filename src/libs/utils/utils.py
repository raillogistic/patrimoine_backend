import functools
import sys

import graphene
from libs.graphql.graphene_django_extras.registry import get_global_registry, registry


def register_module(module_name, cls, name):
    setattr(sys.modules[module_name], name, cls)


def CreateArgument(model, required=False):
    return graphene.Argument(
        registry.get_type_for_model(model, for_input="create"), required=required
    )


def CreateArgumentList(model, required=False):
    return graphene.List(
        registry.get_type_for_model(model, for_input="create"), required=required
    )


def getTypeFromModel(model, required=False):
    return registry.get_type_for_model(model, for_input="create")


def rgetattr(obj, attr, *args):
    """get nested atributes  by using .
    for example: get(obj,'person.function.grade.salary....')
    """

    def _getattr(obj, attr):
        return getattr(obj, attr, *args)

    return functools.reduce(_getattr, [obj] + attr.split("."))


def rgetattrdict(obj, attr, default):
    """get nested atributes  by using .
    for example: get(obj,'person.function.grade.salary....')
    """

    def _getattr(obj, attr):
        return obj.get(attr, {})

    res = functools.reduce(_getattr, [obj] + attr.split("."))
    print(res)
    if res == {}:
        return default
    else:
        return res


from typing import Any, Dict, List, Union


def dgetattr(data: Dict, path: Union[str, List[str]], default: Any = None) -> Any:
    if isinstance(path, str):
        path = path.split(".")

    current = data
    try:
        for key in path:
            current = current[key]
    except (KeyError, TypeError):
        return default

    return current


# # Example Usage:
# nested_dict = {
#     "user": {
#         "profile": {
#             "name": "Milia",
#             "address": {
#                 "city": "Algiers",
#                 "zip": "16000"
#             }
#         }
#     }
# }
