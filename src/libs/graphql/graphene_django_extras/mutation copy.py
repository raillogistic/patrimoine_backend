# -*- coding: utf-8 -*-

# -*- coding: utf-8 -*-
from collections import OrderedDict
from typing import Iterable, Union

import graphene
from django import VERSION as DJANGO_VERSION
from django.contrib.auth.models import Permission
from django.db.models import ManyToOneRel
from graphene import ID, Argument, Boolean, Field, Int, List, ObjectType, String
from graphene.types.base import BaseOptions
from graphene.utils.deprecated import warn_deprecation
from graphene.utils.props import props
from graphene_django.types import ErrorType
from graphql import GraphQLError
from libs.graphql.graphene_django_extras.base_types import factory_type
from libs.graphql.graphene_django_extras.registry import get_global_registry
from libs.graphql.graphene_django_extras.types import (
    DjangoInputObjectType,
    DjangoObjectType,
)
from libs.graphql.graphene_django_extras.utils import get_Object_or_None

color = "\033[95m"


class SerializerMutationOptions(BaseOptions):
    fields = None
    input_fields = None
    interfaces = ()
    serializer_class = None
    action = None
    arguments = None
    output = None
    resolver = None
    nested_fields = None


class DjangoSerializerMutation(ObjectType):
    """
    Serializer Mutation Type Definition
    """

    ok = Boolean(description="Boolean field that return mutation result request.")
    errors = List(ErrorType, description="Errors list for the field")

    class Meta:
        abstract = True

    @classmethod
    def __init_subclass_with_meta__(
        cls,
        serializer_class=None,
        only_fields=(),
        include_fields=(),
        exclude_fields=(),
        input_field_name="input",
        output_field_name=None,
        description="",
        nested_fields=(),
        permissions={
            "create": (),
            "change": (),
            "delete": (),
        },
        many=False,
        **options,
    ):
        if not serializer_class:
            raise Exception(
                "serializer_class is required on all DjangoSerializerMutation"
            )

        model = serializer_class.Meta.model
        description = description or "SerializerMutation for {} model".format(
            model.__name__
        )

        input_field_name = input_field_name or "new_{}".format(model._meta.model_name)
        output_field_name = output_field_name or model._meta.model_name

        input_class = getattr(cls, "Arguments", None)
        if not input_class:
            input_class = getattr(cls, "Input", None)
            if input_class:
                warn_deprecation(
                    (
                        "Please use {name}.Arguments instead of {name}.Input."
                        "Input is now only used in ClientMutationID.\nRead more: "
                        "https://github.com/graphql-python/graphene/blob/2.0/UPGRADE-v2.0.md#mutation-input"
                    ).format(name=cls.__name__)
                )
        if input_class:
            arguments = props(input_class)
        else:
            arguments = {}

        registry = get_global_registry()

        factory_kwargs = {
            "model": model,
            "only_fields": only_fields,
            "create_permissions": permissions.get("create", ()),
            "change_permissions": permissions.get("change", ()),
            "delete_permissions": permissions.get("delete", ()),
            "include_fields": include_fields,
            "exclude_fields": exclude_fields,
            "nested_fields": nested_fields,
            "registry": registry,
            "skip_registry": False,
            "many": many,
        }

        output_type = registry.get_type_for_model(model)

        if not output_type:
            output_type = factory_type("output", DjangoObjectType, **factory_kwargs)

        django_fields = OrderedDict({output_field_name: Field(output_type)})

        global_arguments = {}
        for operation in ("create", "delete", "update"):
            global_arguments.update({operation: OrderedDict()})

            if operation != "delete":
                input_type = registry.get_type_for_model(model, for_input=operation)

                if not input_type:
                    # factory_kwargs.update({'skip_registry': True})
                    input_type = factory_type(
                        "input", DjangoInputObjectType, operation, **factory_kwargs
                    )
                    if operation == "create" and many == True:
                        input_type = graphene.List(
                            factory_type(
                                "input",
                                DjangoInputObjectType,
                                operation,
                                **factory_kwargs,
                            )
                        )

                global_arguments[operation].update(
                    {input_field_name: Argument(input_type, required=True)}
                )
            else:
                global_arguments[operation].update(
                    {
                        "id": Argument(
                            graphene.List(ID),
                            required=True,
                            description="Django object unique identification field",
                        )
                    }
                )
            global_arguments[operation].update(arguments)

        _meta = SerializerMutationOptions(cls)
        _meta.output = cls
        _meta.arguments = global_arguments
        _meta.fields = django_fields
        _meta.output_type = output_type
        _meta.model = model
        _meta.many = many
        _meta.create_permissions = permissions.get("create", ())
        _meta.change_permissions = permissions.get("change", ())
        _meta.delete_permissions = permissions.get("delete", ())
        _meta.serializer_class = serializer_class
        _meta.input_field_name = input_field_name
        _meta.output_field_name = output_field_name
        _meta.nested_fields = nested_fields

        super(DjangoSerializerMutation, cls).__init_subclass_with_meta__(
            _meta=_meta, description=description, **options
        )

    @classmethod
    def get_errors(cls, errors):
        for e in errors:
            print("err", e.field)
            print("err", e.messages)

        errors_dict = {cls._meta.output_field_name: None, "ok": False, "errors": errors}

        return cls(**errors_dict)

    @classmethod
    def get_permissions(cls, root, info, operation, *args, **kwargs) -> Iterable[str]:
        if operation == "create":
            return cls._meta.create_permissions
        elif operation == "change":
            return cls._meta.change_permissions
        elif operation == "delete":
            return cls._meta.delete_permissions
        return ()

    @classmethod
    def check_permissions(cls, root, info, operation, *args, **kwargs) -> None:
        get_permissions = getattr(cls, "get_permissions", None)
        if not callable(get_permissions):
            raise TypeError(
                "The `get_permissions` attribute of a mutation must be callable."
            )

        permissions = cls.get_permissions(root, info, operation, *args, **kwargs)

        if permissions and len(permissions) > 0:
            if not info.context.user.has_perms(permissions):
                raise GraphQLError("no_permissions")

    global_id = String()

    @classmethod
    def perform_mutate(cls, obj, info):
        resp = {cls._meta.output_field_name: obj, "ok": True, "errors": None}
        return cls(**resp, global_id=obj.id)

    @classmethod
    def get_serializer_kwargs(cls, root, info, **kwargs):
        return {}

    @classmethod
    def get_reverse_fields(cls):
        return {
            f.name: f
            for f in cls._meta.model._meta.get_fields()
            if f.auto_created and not f.concrete
        }

    @classmethod
    def manage_nested_fields(cls, data, root, info):
        nested_objs = {}
        reverse_nested_objs = {}
        reverse_fields = cls.get_reverse_fields()
        if cls._meta.nested_fields and type(cls._meta.nested_fields) == dict:
            for field in cls._meta.nested_fields:
                if reverse_fields.get(field):
                    reverse_nested_objs.update({field: data.pop(field, None)})

                sub_data = data.pop(field, None)

                if sub_data:
                    serialized_data = cls._meta.nested_fields[field](
                        data=sub_data, many=True if type(sub_data) == list else False
                    )

                    ok, result = cls.save(serialized_data, root, info)

                    if not ok:
                        return cls.get_errors(result)
                    if isinstance(sub_data, list):
                        nested_objs.update({field: result})
                    else:
                        data.update({field: result.id})
        return (nested_objs, reverse_nested_objs)

    @classmethod
    def create(cls, root, info, **kwargs):
        data = kwargs.get(cls._meta.input_field_name)
        request_type = info.context.META.get("CONTENT_TYPE", "")
        if "multipart/form-data" in request_type:
            data.update({name: value for name, value in info.context.FILES.items()})

        nested_objs, reverse_nested_objs = cls.manage_nested_fields(data, root, info)
        serializer = cls._meta.serializer_class(
            data=data, **cls.get_serializer_kwargs(root, info, **kwargs)
        )
        cls.check_permissions(root, info, "create", data)
        ok, obj = cls.save(serializer, root, info)
        for f, v in data.items():
            try:
                getattr(obj, f).save()
            except:
                pass
        if not ok:
            return cls.get_errors(obj)

        elif nested_objs:
            [getattr(obj, field).add(*objs) for field, objs in nested_objs.items()]
        elif reverse_nested_objs:
            for field, objs in reverse_nested_objs.items():
                related_field = cls.get_reverse_fields().get(field)
                related_model = related_field.related_model
                if isinstance(objs, list):
                    for o in objs:
                        if related_model and o and related_field.field.name:
                            serialized_data = cls._meta.nested_fields[field](
                                data={**{**o, related_field.field.name: obj.pk}},
                                many=True if type(o) == list else False,
                            )
                            ok, res = cls.save(serialized_data, root, info)
                            if not ok:
                                return cls.get_errors(res)
                            # nested_obj = related_model.objects.create(
                            #     **{**o, related_field.field.column: obj.pk})
                            getattr(obj, field).add(res)

        return cls.perform_mutate(obj, info)

    @classmethod
    def delete(cls, root, info, **kwargs):
        pk = kwargs.get("id")

        old_obj = get_Object_or_None(cls._meta.model, _type="list", pk__in=pk)
        cls.check_permissions(root, info, "delete", old_obj)

        if old_obj:
            old_obj.delete()
            old_obj.id = pk
            return cls.perform_mutate(old_obj, info)
        else:
            return cls.get_errors(
                [
                    ErrorType(
                        field="id",
                        messages=[
                            "A {} obj with id {} do not exist".format(
                                cls._meta.model.__name__, pk
                            )
                        ],
                    )
                ]
            )

    @classmethod
    def update(cls, root, info, **kwargs):
        data = kwargs.get(cls._meta.input_field_name)
        request_type = info.context.META.get("CONTENT_TYPE", "")
        if "multipart/form-data" in request_type:
            data.update({name: value for name, value in info.context.FILES.items()})
        cls.check_permissions(root, info, "change", data)

        pk = data.pop("id")

        old_obj = get_Object_or_None(cls._meta.model, pk=pk)

        if old_obj:
            nested_objs, reverse_nested_objs = cls.manage_nested_fields(
                data, root, info
            )
            serializer = cls._meta.serializer_class(
                old_obj,
                data=data,
                partial=True,
                **cls.get_serializer_kwargs(root, info, **kwargs),
            )
            ok, obj = cls.save(serializer, root, info)
            if not ok:
                return cls.get_errors(obj)
            elif nested_objs:
                [getattr(obj, field).add(*objs) for field, objs in nested_objs.items()]
            elif reverse_nested_objs:
                for field, objs in reverse_nested_objs.items():
                    related_field = cls.get_reverse_fields().get(field)
                    related_model = related_field.related_model
                    if isinstance(objs, list):
                        # if (len(objs) == 0):
                        # getattr(obj, field).all().delete()
                        # delete old object that has no reference
                        getattr(obj, field).all().delete()

                        for o in objs:
                            if related_model and o and related_field.field.name:
                                serialized_data = cls._meta.nested_fields[field](
                                    data={**{**o, related_field.field.name: obj.pk}},
                                    many=True if type(o) == list else False,
                                )
                                ok, res = cls.save(serialized_data, root, info)
                                if not ok:
                                    return cls.get_errors(res)
                                # getattr(obj, field).add(res)

            return cls.perform_mutate(obj, info)
        else:
            return cls.get_errors(
                [
                    ErrorType(
                        field="id",
                        messages=[
                            "A {} obj with id: {} do not exist".format(
                                cls._meta.model.__name__, pk
                            )
                        ],
                    )
                ]
            )

    @classmethod
    def save(cls, serialized_obj, root, info, **kwargs):
        if serialized_obj.is_valid():
            obj = serialized_obj.save()
            return True, obj

        else:
            errors = [
                ErrorType(field=key, messages=value)
                for key, value in serialized_obj.errors.items()
            ]
            return False, errors

    @classmethod
    def CreateField(cls, *args, **kwargs):
        return Field(
            cls._meta.output,
            args=cls._meta.arguments["create"],
            resolver=cls.create,
            **kwargs,
        )

    @classmethod
    def DeleteField(cls, *args, **kwargs):
        return Field(
            cls._meta.output,
            args=cls._meta.arguments["delete"],
            resolver=cls.delete,
            **kwargs,
        )

    @classmethod
    def UpdateField(cls, *args, **kwargs):
        return Field(
            cls._meta.output,
            args=cls._meta.arguments["update"],
            resolver=cls.update,
            **kwargs,
        )

    @classmethod
    def MutationFields(cls, *args, **kwargs):
        create_field = cls.CreateField(*args, **kwargs)
        delete_field = cls.DeleteField(*args, **kwargs)
        update_field = cls.UpdateField(*args, **kwargs)

        return create_field, delete_field, update_field


# from collections import OrderedDict
# from typing import Iterable, Union
# from graphene import Boolean, List, Field, ID, Argument, ObjectType, Int, String
# from graphene.types.base import BaseOptions
# from graphene.utils.deprecated import warn_deprecation
# from graphene.utils.props import props
# from graphene_django.types import ErrorType
# from graphql import GraphQLError
# from libs.graphql.graphene_django_extras.base_types import factory_type
# from libs.graphql.graphene_django_extras.registry import get_global_registry
# from libs.graphql.graphene_django_extras.types import DjangoObjectType, DjangoInputObjectType
# from libs.graphql.graphene_django_extras.utils import get_Object_or_None
# from django.contrib.auth.models import Permission
# from django import VERSION as DJANGO_VERSION
# from django.db.models import ManyToOneRel
# import graphene


# class SerializerMutationOptions(BaseOptions):
#     fields = None
#     input_fields = None
#     interfaces = ()
#     serializer_class = None
#     action = None
#     arguments = None
#     output = None
#     resolver = None
#     nested_fields = None


# class DjangoSerializerMutation(ObjectType):

#     """
#         Serializer Mutation Type Definition
#     """

#     ok = Boolean(
#         description="Boolean field that return mutation result request.")
#     errors = List(ErrorType, description="Errors list for the field")

#     class Meta:
#         abstract = True

#     @classmethod
#     def __init_subclass_with_meta__(
#         cls,
#         serializer_class=None,
#         only_fields=(),
#         include_fields=(),
#         exclude_fields=(),
#         input_field_name="input",
#         output_field_name=None,
#         description="",
#         nested_fields=(),
#         permissions={
#             "create": (),
#             "change": (),
#             "delete": (),
#         },
#         many=False,
#         **options,
#     ):
#         if not serializer_class:
#             raise Exception(
#                 "serializer_class is required on all DjangoSerializerMutation"
#             )

#         model = serializer_class.Meta.model

#         description = description or "SerializerMutation for {} model".format(
#             model.__name__
#         )
#         input_field_name = input_field_name or "new_{}".format(
#             model._meta.model_name)
#         output_field_name = output_field_name or model._meta.model_name

#         input_class = getattr(cls, "Arguments", None)
#         if not input_class:
#             input_class = getattr(cls, "Input", None)
#             if input_class:
#                 warn_deprecation(
#                     (
#                         "Please use {name}.Arguments instead of {name}.Input."
#                         "Input is now only used in ClientMutationID.\nRead more: "
#                         "https://github.com/graphql-python/graphene/blob/2.0/UPGRADE-v2.0.md#mutation-input"
#                     ).format(name=cls.__name__)
#                 )
#         if input_class:
#             arguments = props(input_class)
#         else:
#             arguments = {}

#         registry = get_global_registry()

#         factory_kwargs = {
#             "model": model,
#             "only_fields": only_fields,
#             "create_permissions": permissions.get('create', ()),
#             "change_permissions": permissions.get('change', ()),
#             "delete_permissions": permissions.get('delete', ()),
#             "include_fields": include_fields,
#             "exclude_fields": exclude_fields,
#             "nested_fields": nested_fields,
#             "registry": registry,
#             "skip_registry": False,
#             "many": many,
#         }

#         output_type = registry.get_type_for_model(model)
#         if not output_type:

#             output_type = factory_type(
#                 "output", DjangoObjectType, **factory_kwargs)
#         django_fields = OrderedDict({output_field_name: Field(output_type)})

#         global_arguments = {}
#         for operation in ("create", "delete", "update"):
#             global_arguments.update({operation: OrderedDict()})

#             if operation != "delete":
#                 input_type = registry.get_type_for_model(
#                     model, for_input=operation)
#                 if not input_type:
#                     # factory_kwargs.update({'skip_registry': True})

#                     input_type = factory_type(
#                         "input", DjangoInputObjectType, operation, **factory_kwargs
#                     )
#                     if operation == "create" and many == True:
#                         input_type = graphene.List(factory_type(
#                             "input", DjangoInputObjectType, operation, **factory_kwargs
#                         ))

#                 global_arguments[operation].update(
#                     {input_field_name: Argument(input_type, required=True)}
#                 )
#             else:
#                 global_arguments[operation].update(
#                     {
#                         "id": Argument(
#                             ID,
#                             required=True,
#                             description="Django object unique identification field",
#                         )
#                     }
#                 )
#             global_arguments[operation].update(arguments)

#         _meta = SerializerMutationOptions(cls)
#         _meta.output = cls
#         _meta.arguments = global_arguments
#         _meta.fields = django_fields
#         _meta.output_type = output_type
#         _meta.model = model
#         _meta.create_permissions = permissions.get('create', ())
#         _meta.change_permissions = permissions.get('change', ())
#         _meta.delete_permissions = permissions.get('delete', ())
#         _meta.serializer_class = serializer_class
#         _meta.input_field_name = input_field_name
#         _meta.output_field_name = output_field_name
#         _meta.nested_fields = nested_fields

#         super(DjangoSerializerMutation, cls).__init_subclass_with_meta__(
#             _meta=_meta, description=description, **options
#         )

#     @classmethod
#     def get_errors(cls, errors):
#         errors_dict = {cls._meta.output_field_name: None,
#                        "ok": False, "errors": errors}

#         return cls(**errors_dict)

#     @classmethod
#     def get_permissions(cls, root, info, operation, *args, **kwargs) -> Iterable[str]:
#         if operation == "create":
#             return cls._meta.create_permissions
#         elif operation == "change":
#             return cls._meta.change_permissions
#         elif operation == "delete":
#             return cls._meta.delete_permissions
#         return ()

#     @classmethod
#     def check_permissions(cls, root, info, operation, *args, **kwargs) -> None:
#         get_permissions = getattr(cls, "get_permissions", None)
#         if not callable(get_permissions):
#             raise TypeError(
#                 "The `get_permissions` attribute of a mutation must be callable."
#             )

#         permissions = cls.get_permissions(
#             root, info, operation, *args, **kwargs)

#         if permissions and len(permissions) > 0:
#             if not info.context.user.has_perms(permissions):
#                 raise GraphQLError("no_permissions")

#     global_id = String()

#     @classmethod
#     def perform_mutate(cls, obj, info):

#         resp = {cls._meta.output_field_name: obj, "ok": True, "errors": None}
#         return cls(**resp, global_id=obj.id)

#     @classmethod
#     def get_serializer_kwargs(cls, root, info, **kwargs):
#         return {}

#     @classmethod
#     def get_reverse_fields(cls):
#         return {f.name: f for f in cls._meta.model._meta.get_fields(
#         ) if f.auto_created and not f.concrete}

#     @classmethod
#     def manage_nested_fields(cls, data, root, info):
#         nested_objs = {}
#         reverse_nested_objs = {}
#         reverse_fields = cls.get_reverse_fields()
#         if cls._meta.nested_fields and type(cls._meta.nested_fields) == dict:
#             for field in cls._meta.nested_fields:
#                 if(reverse_fields.get(field)):
#                     reverse_nested_objs.update({field: data.pop(field, None)})
#                 sub_data = data.pop(field, None)

#                 if sub_data:
#                     serialized_data = cls._meta.nested_fields[field](
#                         data=sub_data, many=True if type(
#                             sub_data) == list else False
#                     )
#                     ok, result = cls.save(serialized_data, root, info)

#                     if not ok:
#                         return cls.get_errors(result)
#                     if isinstance(sub_data, list):
#                         nested_objs.update({field: result})
#                     else:
#                         data.update({field: result.id})
#         return (nested_objs or {}, reverse_nested_objs or {})

#     @classmethod
#     def create(cls, root, info, **kwargs):

#         data = kwargs.get(cls._meta.input_field_name)
#         request_type = info.context.META.get("CONTENT_TYPE", "")
#         if "multipart/form-data" in request_type:
#             data.update(
#                 {name: value for name, value in info.context.FILES.items()})

#         print("xxxx", cls.manage_nested_fields(
#             data, root, info))

#         nested_objs, reverse_nested_objs = cls.manage_nested_fields(
#             data, root, info)

#         serializer = cls._meta.serializer_class(
#             data=data, **cls.get_serializer_kwargs(root, info, **kwargs)
#         )

#         cls.check_permissions(root, info, 'create', data)
#         ok, obj = cls.save(serializer, root, info)

#         for f, v in data.items():
#             try:
#                 getattr(obj, f).save()
#             except:
#                 pass

#         if not ok:
#             return cls.get_errors(obj)

#         elif nested_objs:
#             [getattr(obj, field).add(*objs)
#              for field, objs in nested_objs.items()]
#         elif reverse_nested_objs:

#             for field, objs in reverse_nested_objs.items():

#                 related_field = cls.get_reverse_fields().get(field)
#                 related_model = related_field.related_model
#                 if isinstance(objs, list):
#                     for o in objs:
#                         if(related_model and o and related_field.field.name):

#                             serialized_data = cls._meta.nested_fields[field](
#                                 data={**{**o, related_field.field.name: obj.pk}}, many=True if type(
#                                     o) == list else False
#                             )
#                             ok, res = cls.save(serialized_data, root, info)
#                             if not ok:
#                                 return cls.get_errors(res)
#                             # nested_obj = related_model.objects.create(
#                             #     **{**o, related_field.field.column: obj.pk})
#                             getattr(obj, field).add(res)

#         return cls.perform_mutate(obj, info)

#     @classmethod
#     def delete(cls, root, info, **kwargs):
#         pk = kwargs.get("id")

#         old_obj = get_Object_or_None(cls._meta.model, pk=pk)
#         cls.check_permissions(root, info, 'delete', old_obj)

#         if old_obj:
#             old_obj.delete()
#             old_obj.id = pk
#             return cls.perform_mutate(old_obj, info)
#         else:
#             return cls.get_errors(
#                 [
#                     ErrorType(
#                         field="id",
#                         messages=[
#                             "A {} obj with id {} do not exist".format(
#                                 cls._meta.model.__name__, pk
#                             )
#                         ],
#                     )
#                 ]
#             )

#     @classmethod
#     def update(cls, root, info, **kwargs):

#         data = kwargs.get(cls._meta.input_field_name)
#         request_type = info.context.META.get("CONTENT_TYPE", "")
#         if "multipart/form-data" in request_type:
#             data.update(
#                 {name: value for name, value in info.context.FILES.items()})
#         cls.check_permissions(root, info, 'change', data)

#         pk = data.pop("id")

#         old_obj = get_Object_or_None(cls._meta.model, pk=pk)

#         if old_obj:

#             nested_objs, reverse_nested_objs = cls.manage_nested_fields(
#                 data, root, info)
#             serializer = cls._meta.serializer_class(
#                 old_obj,
#                 data=data,
#                 partial=True,
#                 **cls.get_serializer_kwargs(root, info, **kwargs),
#             )
#             ok, obj = cls.save(serializer, root, info)
#             if not ok:
#                 return cls.get_errors(obj)
#             elif nested_objs:
#                 [getattr(obj, field).add(*objs)
#                  for field, objs in nested_objs.items()]
#             elif reverse_nested_objs:
#                 for field, objs in reverse_nested_objs.items():
#                     related_field = cls.get_reverse_fields().get(field)
#                     related_model = related_field.related_model
#                     if isinstance(objs, list):
#                         # if (len(objs) == 0):
#                         # getattr(obj, field).all().delete()
#                         # delete old object that has no reference
#                         getattr(obj, field).all().delete()

#                         for o in objs:
#                             if(related_model and o and related_field.field.name):
#                                 serialized_data = cls._meta.nested_fields[field](
#                                     data={**{**o, related_field.field.name: obj.pk}}, many=True if type(
#                                         o) == list else False
#                                 )
#                                 ok, res = cls.save(serialized_data, root, info)
#                                 if not ok:
#                                     return cls.get_errors(res)
#                                 # getattr(obj, field).add(res)

#             return cls.perform_mutate(obj, info)
#         else:
#             return cls.get_errors(
#                 [
#                     ErrorType(
#                         field="id",
#                         messages=[
#                             "A {} obj with id: {} do not exist".format(
#                                 cls._meta.model.__name__, pk
#                             )
#                         ],
#                     )
#                 ]
#             )

#     @classmethod
#     def save(cls, serialized_obj, root, info, **kwargs):
#         if serialized_obj.is_valid():
#             obj = serialized_obj.save()
#             return True, obj

#         else:
#             errors = [
#                 ErrorType(field=key, messages=value)
#                 for key, value in serialized_obj.errors.items()
#             ]
#             return False, errors

#     @classmethod
#     def CreateField(cls, *args, **kwargs):

#         return Field(
#             cls._meta.output,
#             args=cls._meta.arguments["create"],
#             resolver=cls.create,
#             **kwargs,
#         )

#     @classmethod
#     def DeleteField(cls, *args, **kwargs):
#         return Field(
#             cls._meta.output,
#             args=cls._meta.arguments["delete"],
#             resolver=cls.delete,
#             **kwargs,
#         )

#     @classmethod
#     def UpdateField(cls, *args, **kwargs):
#         return Field(
#             cls._meta.output,
#             args=cls._meta.arguments["update"],
#             resolver=cls.update,
#             **kwargs,
#         )

#     @classmethod
#     def MutationFields(cls, *args, **kwargs):
#         create_field = cls.CreateField(*args, **kwargs)
#         delete_field = cls.DeleteField(*args, **kwargs)
#         update_field = cls.UpdateField(*args, **kwargs)

#         return create_field, delete_field, update_field
