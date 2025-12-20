import os
import shutil

import graphene
from django.apps import apps
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.shortcuts import get_current_site
from django.db.models.fields import AutoField
from django.http import HttpResponse
from polymorphic.utils import reset_polymorphic_ctype

from .table import TableCreationQueries, TableFilterQueries, TableQueries
from .types.AppType import AppType
from .types.FieldType import FieldType
from .types.ModelType import ModelType
from .types.RelatedFieldType import RelatedFieldType


def all_models(app_name):
    models = []
    for m in list(apps.all_models[app_name].values()):
        model = apps.get_model(app_name, m.__name__)
        if getattr(model, "__name__", False):
            models.append(
                ModelType(
                    name=model.__name__,
                    app=app_name,
                    # fields=all_fields(
                    #     app_name,
                    #     model.__name__,
                    # ),
                )
            )
    return models


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


def get_fields_and_properties(model):
    field_names = remove_history_fields([f.name for f in model._meta.fields])
    # property_names = [name for name in dir(
    #     model) if isinstance(getattr(model, name, None), property) and name != "pk"]
    # print(field_names)
    property_names = [
        # (
        #     name,
        #     getattr(
        #         getattr(getattr(model, name), "fget", name), "short_description", name
        #     ),
        # )
        # for name in dir(model)
        # if isinstance(getattr(model, name), property) and name != "pk"
    ]
    return property_names


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
    # property_names = [
    #     name for name in dir(_model) if isinstance(getattr(model, name, ""), property)
    # ]

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

    for p in get_fields_and_properties(
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


class ModelQueries(
    TableCreationQueries, TableQueries, TableFilterQueries, graphene.ObjectType
):
    models = graphene.List(ModelType, app_name=graphene.String())
    apps = graphene.List(AppType)
    all_apps = graphene.List(graphene.String)
    fields = graphene.List(FieldType, app=graphene.String(), model=graphene.String())

    def resolve_models(self, info, app_name="", **kwargs):
        if len(app_name) == 0:
            return []
        return all_models(app_name)

    def resolve_all_apps(self, info, **kwargs):
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
            "corsheaders",
            "admin",
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
            res.append(a)
        return res

    def resolve_apps(self, info, **kwargs):
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
            res.append(AppType(name=a, models=all_models(a)))
        return res

    def resolve_fields(self, info, app="", model=""):
        if len(app) == 0 or len(model) == 0:
            return []
        return all_fields(app, model)


class FileInput(graphene.InputObjectType):
    name = graphene.String()
    folder = graphene.String()
    content = graphene.String()
    model = graphene.String()

    # # create graphql folder
    # os.makedirs('authentication/graphqls', exist_ok=True)
    # # create folders related
    # for f in folders:
    #     os.makedirs(f"{app}/graphqls/{f}", exist_ok=True)


class CreateFielsMutation(graphene.Mutation):
    ok = graphene.Boolean()
    url = graphene.String()

    class Input:
        app = graphene.String()
        files = graphene.List(FileInput)

    def mutate(self, info, app, files):
        dir = os.path.join(getattr(settings, "BASE_DIR"), "generated")
        for file in files:
            folder_path = f"{dir}/{file['folder']}"
            os.makedirs(folder_path, exist_ok=True)
            f = open(f"{folder_path}/{file.name}", "w+")
            f.write(file["content"])
            f.close()

        shutil.make_archive(
            os.path.join(getattr(settings, "BASE_DIR"), "zip"), "zip", dir
        )

        return CreateFielsMutation(
            ok=True, url=f"{get_current_site(info.context)}/models/generate"
        )


class BaseModelInput(graphene.InputObjectType):
    model = graphene.String()
    app = graphene.String()


class UpdatePolymorphic(graphene.Mutation):
    class Input:
        base = graphene.Argument(BaseModelInput, required=True)
        models = graphene.List(BaseModelInput, required=True)

    ok = graphene.Boolean()

    def mutate(self, info, base, models=[]):
        for m in models:
            basex = apps.get_model(app_label=base.app, model_name=base.model)
            model = apps.get_model(app_label=m.app, model_name=m.model)
            reset_polymorphic_ctype(basex, model, ignore_existing=True)

        return UpdatePolymorphic(ok=True)


import graphene
from django.apps import apps


class OrderUpdateInput(graphene.InputObjectType):
    order = graphene.Int()
    id = graphene.String()


class OrderUpdateForModel(graphene.InputObjectType):
    items = graphene.List(OrderUpdateInput)
    model = graphene.String()
    app = graphene.String()


class ChangeOrder(graphene.Mutation):
    ok = graphene.Boolean()
    message = graphene.String()

    class Input:
        input = graphene.Argument(OrderUpdateForModel)

    def mutate(self, info, input=[]):
        model_name = input.get("model", None)
        app_name = input.get("app", None)

        if not app_name or not model_name:
            return ChangeOrder(ok=False, message="App or Model undefined")
        model = apps.get_model(app_name, model_name)

        for i in input.get("items", []):
            try:
                m = model.objects.get(
                    id=i["id"],
                )
                m.order = i["order"]
                m.save()
            except Exception as E:
                pass

        return ChangeOrder(ok=True, message="OK")


class ModelsMutations(
    graphene.ObjectType,
):
    create_mutation = CreateFielsMutation.Field()
    update_polymorphism = UpdatePolymorphic.Field()
    change_order = ChangeOrder.Field()
