from collections import defaultdict, deque
from typing import List, get_type_hints

import graphene
from django.apps import apps
from django.conf import settings
from django.db import models
from django.db.models import Model


def get_parent(m):
    base_name = None
    base = m.__bases__[0]
    if base.__name__ == "Model" or base.__name__ == "PolymorphicModel":
        base = None
    if base:
        base_name = base.__name__
        base_app = base.__module__.split(".")[0]

        base_name = base_name
    if base_name == "HistoricalChanges":
        return None
    return base_name


def get_parent_model(m):
    base_name = None
    base = m.__bases__[0]
    if (
        base.__name__ == "Model"
        or base.__name__ == "PolymorphicModel"
        or base.__name__ == "HistoricalChanges"
    ):
        base = None
    return base


def get_model_dependencies(model):
    dependencies = set()
    for field in model._meta.get_fields():
        if isinstance(
            field, (models.ForeignKey, models.OneToOneField, models.ManyToManyField)
        ):
            dependencies.add(field.related_model)

    return dependencies


import importlib


def get_class_by_name(
    module_path,
    class_name,
):
    module = importlib.import_module(module_path)
    class_obj = getattr(module, class_name)
    return class_obj


def userapps():
    base_dir = settings.BASE_DIR
    installed_apps = apps.get_app_configs()
    exclude = ["models", "libs"]
    user_created_apps = [
        app_config
        for app_config in installed_apps
        if app_config.path.startswith(base_dir) and app_config.name not in exclude
    ]
    return user_created_apps


def app_models(app):
    res = []
    res = [*res, *app.get_models()]


import inspect

from django.db.models.base import ModelBase


def abstract_models():
    base_dir = settings.BASE_DIR
    installed_apps = apps.get_app_configs()
    user_created_apps = [
        app_config
        for app_config in installed_apps
        if app_config.path.startswith(base_dir)
    ]
    abstract_models = []

    for app_config in user_created_apps:
        # app_config = apps.get_app_config(app_config.app_label)
        # Import the models.py module explicitly
        try:
            models_module = app_config.module.models  # Access models.py
        except AttributeError:
            return []  # If models.py doesn't exist, return an empty list

        # Inspect all classes in models.py
        for name, obj in inspect.getmembers(models_module):
            # Check if it's a model and abstract
            if inspect.isclass(obj) and issubclass(obj, models.Model):
                if (
                    getattr(obj._meta, "abstract", False)
                    and obj.__name__ != "PolymorphicModel"
                ):
                    abstract_models.append(obj)

    return abstract_models


def all_mdls():
    base_dir = settings.BASE_DIR
    installed_apps = apps.get_app_configs()
    user_created_apps = [
        app_config
        for app_config in installed_apps
        if app_config.path.startswith(base_dir)
    ]
    res = []
    for app_config in user_created_apps:
        res = [*res, *app_config.get_models()]
    # res = [*res, *abstract_models()]
    return res


def topological_sort(models):
    # Step 1: Create a graph of models and their dependencies
    in_degree = {model: 0 for model in models}

    adj_list = defaultdict(list)
    for model, deps in models.items():
        for dep in deps:
            adj_list[dep].append(model)
            in_degree[model] += 1

    # Step 2: Initialize a queue with models that have no dependencies
    queue = deque([model for model in models if in_degree[model] == 0])
    sorted_models = []

    # Step 3: Perform topological sorting
    while queue:
        model = queue.popleft()
        sorted_models.append(model)
        for dependent in adj_list[model]:
            in_degree[dependent] -= 1
            if in_degree[dependent] == 0:
                queue.append(dependent)

    # for s in sorted_models:
    #     if not models.get(s, None):
    #         print(s)
    # Check for cycles
    # if len(sorted_models) != len(models):
    #     raise Exception("A circular dependency was detected.")

    return list(
        filter(
            lambda m: m not in [x.__name__ for x in abstract_models()], sorted_models
        )
    )


def get_deps():
    deps = {}
    for m in [*abstract_models(), *all_mdls()]:
        if "Historical" in m.__name__:
            continue
        p = get_parent(m)
        if p:
            deps[m.__name__] = [get_parent(m)]
        else:
            deps[m.__name__] = []

    return deps


def classes_with_parents():
    models = all_mdls()
    res = []
    for m in models:
        base_name = None
        base = m.__bases__[0]
        if base.__name__ == "Model" or base.__name__ == "PolymorphicModel":
            base = None
        if base:
            base_name = base.__name__
            base_app = base.__module__.split(".")[0]

            base_name = base_name
        res.append({"name": m.__name__, "parent": base_name})
    return res


def get_modelbyname(names):
    res = {}
    for m in all_mdls():
        res[m.__name__] = m
    l = []

    for n in names:
        if res.get(n, None):
            l.append(res[n])
    return l


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


def sorted_models():
    return get_modelbyname(topological_sort(get_deps()))


def get_fields_and_properties_for_graphql(model, types={}):
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
                return graphene.List(f"libs.graphql.schema.types.{_type.__name__}Type")
            else:
                return graphene.Field(f"libs.graphql.schema.types.{_type.__name__}Type")
        else:
            _type = _type.__name__

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
