from graphene_django import types
from graphene import Int, String
import graphene
from libs.graphql.graphene_django_extras.mutation import DjangoSerializerMutation
from libs.graphql.graphene.CustomSerializerMutationWithType import DjangoSerializerMutation as CustomSerializerMutationWithType
from django.db import models
from graphene_django.rest_framework.mutation import SerializerMutation
from graphene_django_extras.types import DjangoObjectType
from graphene_django.registry import Registry
import inspect


class CustomDjangoObjectType(types.DjangoObjectType):
    class Meta:
        abstract = True

    pk = graphene.ID()
    # _type = String()

    def resolve_pk(self, info):
        return self.pk

    # def resolve__type(self, info):
    #     return self.__class__.__name__

    def is_valid_django_model(model):
        return inspect.isclass(model) and issubclass(model, models.Model)

    @classmethod
    def is_type_of(cls, root, info):
        if isinstance(root, cls):
            return True
        if not cls.is_valid_django_model(root.__class__):
            raise Exception(
                ('Received incompatible instance "{}".').format(root))
        if cls._meta.model.__class__.__name__ == "PolymorphicModelBase":
            return issubclass(root._meta.model, cls._meta.model)

        if cls._meta.model._meta.proxy:
            model = root._meta.model
        else:
            model = root._meta.model._meta.concrete_model

        return model == cls._meta.model


class CustomConnection(graphene.Connection):
    class Meta:
        abstract = True

    total_count = Int()

    def resolve_total_count(self, info):
        return self.length


class CustomDjangoSerializerMutation(DjangoSerializerMutation):

    class Meta:
        abstract = True

    global_id = graphene.String()
    id = graphene.ID()

    @classmethod
    def perform_mutate(cls, obj, info):
        resp = {cls._meta.output_field_name: obj,
                "ok": True, "errors": None, "id": obj.id}

        return cls(**resp, )


class CustomDjangoSerializerMutationWithType(CustomSerializerMutationWithType):
    class Meta:
        abstract = True
