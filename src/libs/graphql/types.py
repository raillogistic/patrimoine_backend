import inspect

import graphene
from django.db import models
from graphene.relay.node import Node, NodeField
from graphene.types import Interface
from graphene_django import DjangoObjectType
from graphql_relay import from_global_id, to_global_id

# class CustomInterface(graphene.Interface):
#     pass


class CustomInterface(Interface):
    """An object with an ID"""

    raison_social = graphene.String()

    # @classmethod
    # def Field(cls, *args, **kwargs):  # noqa: N802
    #     return NodeField(cls, *args, **kwargs)

    # @classmethod
    # def node_resolver(cls, only_type, root, info, id):
    #     return cls.get_node_from_global_id(info, id, only_type=only_type)

    # @classmethod
    # def get_node_from_global_id(cls, info, global_id, only_type=None):

    #     _type, _id = cls.resolve_global_id(info, global_id)
    #     graphene_type = info.schema.get_type(_type)
    #     if graphene_type is None:
    #         raise Exception(f'Relay Node "{_type}" not found in schema')

    #     graphene_type = graphene_type.graphene_type

    #     if only_type:
    #         assert (
    #             graphene_type == only_type
    #         ), f"Must receive a {only_type._meta.name} id."

    #     # We make sure the ObjectType implements the "Node" interface
    #     if cls not in graphene_type._meta.interfaces:
    #         raise Exception(
    #             f'ObjectType "{_type}" does not implement the "{cls}" interface.'
    #         )

    #     get_node = getattr(graphene_type, "get_node", None)
    #     if get_node:
    #         return get_node(info, _id)

    # @classmethod
    # def to_global_id(cls, type_, id):
    #     return cls._meta.global_id_type.to_global_id(type_, id)


class CustomNode(
    Node,
):
    @classmethod
    def Field(cls, *args, **kwargs):  # noqa: N802
        if kwargs.get("check", None):
            check = kwargs.pop("check", None)
            (_type,) = args
            setattr(cls, str(_type), check)
            # cls[check.__name__] = check
        return NodeField(cls, *args, **kwargs)

    @classmethod
    def node_resolver(cls, only_type, root, info, id, pk=None):
        pk = cls.to_global_id(only_type, pk) if pk else None
        if pk:
            return cls.get_node_from_global_id(info, pk, only_type=only_type)
        else:
            try:
                return cls.get_node_from_global_id(info, id, only_type=only_type)
            except:
                id = cls.to_global_id(only_type, id)
                return cls.get_node_from_global_id(info, id, only_type=only_type)

    @classmethod
    def get_node_from_global_id(cls, info, global_id, only_type=None):
        _type, _id = cls.resolve_global_id(info, global_id)

        graphene_type = info.schema.get_type(_type)

        if graphene_type is None:
            raise Exception(f'Relay Node "{_type}" not found in schema')

        graphene_type = graphene_type.graphene_type

        if only_type:
            assert (
                graphene_type == only_type
            ), f"Must receive a {only_type._meta.name} id."

        # We make sure the ObjectType implements the "Node" interface
        if cls not in graphene_type._meta.interfaces:
            raise Exception(
                f'ObjectType "{_type}" does not implement the "{cls}" interface.'
            )

        get_node = getattr(graphene_type, "get_node", None)
        if get_node:
            check = getattr(cls, _type, None)
            if check:
                return check(info, get_node(info, _id))
            return get_node(info, _id)

    @classmethod
    def to_global_id(cls, type_, id):
        return cls._meta.global_id_type.to_global_id(type_, id)


class CustomConnection(graphene.Connection):
    class Meta:
        abstract = True

    totalCount = graphene.Int()
    edge_count = graphene.Int()

    def resolve_totalCount(self, info):
        return self.length

    def resolve_edge_count(root, info, **kwargs):
        return len(root.edges)


class CustomDjangoObjectType(DjangoObjectType):
    pk = graphene.ID(source="pk")
    convert_choices_to_enum = False

    class Meta:
        abstract = True

    def is_valid_django_model(model):
        return inspect.isclass(model) and issubclass(model, models.Model)

    @classmethod
    def is_type_of(cls, root, info):
        if isinstance(root, cls):
            return True
        if not cls.is_valid_django_model(root.__class__):
            raise Exception(('Received incompatible instance "{}".').format(root))
        if cls._meta.model.__class__.__name__ == "PolymorphicModelBase":
            return issubclass(root._meta.model, cls._meta.model)

        if cls._meta.model._meta.proxy:
            model = root._meta.model
        else:
            model = root._meta.model._meta.concrete_model

        return model == cls._meta.model


def to_django_id(id):
    try:
        int(id)
        return id
    except:
        return from_global_id(id)[1]
