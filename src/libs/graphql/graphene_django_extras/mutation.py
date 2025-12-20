# -*- coding: utf-8 -*-

# -*- coding: utf-8 -*-
from collections import OrderedDict
from typing import Iterable, Union

import graphene
from django import VERSION as DJANGO_VERSION
from django.contrib.auth.models import Permission
from django.core.exceptions import ValidationError
from django.db.models import ManyToOneRel
from django.db.models.deletion import ProtectedError
from django.utils.translation import gettext as _
from graphene import ID, Argument, Boolean, Field, Int, List, ObjectType, String
from graphene.types.base import BaseOptions
from graphene.utils.deprecated import warn_deprecation
from graphene.utils.props import props
from graphene_django.types import ErrorType
from graphql import GraphQLError
from graphql_relay import from_global_id, to_global_id

from libs.graphql.graphene_django_extras.base_types import factory_type
from libs.graphql.graphene_django_extras.registry import get_global_registry
from libs.graphql.graphene_django_extras.types import (
    DjangoInputObjectType,
    DjangoObjectType,
)
from libs.graphql.graphene_django_extras.utils import get_Object_or_None
from libs.models.fields import get_field_by_name

color = "\033[95m"


def get_nested_fields(model):
    return get_field_by_name(
        "libs.graphql.schema.mutations",
        f"{model.__name__}Mutation",
        "_meta.nested_fields",
        {},
    )


def getID(id):
    pk = id
    try:
        int(pk)
    except Exception as E:
        pk = to_global_id(pk)
    return int(pk)


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

                    # if model.__name__=="Livraison" and operation == "update":
                    #     print(operation,input_type._meta.__dict__['input_fields'])

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
        # print(operation, permissions)
        if permissions and len(permissions) > 0:
            if not info.context.user.has_perms([permissions]):
                raise GraphQLError("no_permissions")

    global_id = String()
    id = String()

    @classmethod
    def perform_mutate(cls, obj, info):
        resp = {cls._meta.output_field_name: obj, "ok": True, "errors": None}
        if "delete" in info.field_name:
            return cls(
                **resp,
            )

        return cls(
            **resp,
            global_id=to_global_id(f"{obj._meta.model.__name__}Type", obj.id),
            id=obj.id,
        )

    @classmethod
    def get_serializer_kwargs(cls, root, info, **kwargs):
        return {}

    # lazem matfouatch cls , mais model li rak hab yjbad manou nested fields

    @classmethod
    def get_reverse_fields(cls, model=None):
        if model is not None:
            return {
                f.name: f
                for f in model._meta.get_fields()
                if f.auto_created and not f.concrete
            }
        else:
            return {
                f.name: f
                for f in cls._meta.model._meta.get_fields()
                if f.auto_created and not f.concrete
            }

    @classmethod
    def manage_nested_fields(cls, data, root, info, model=None):
        nested_objs = {}
        reverse_nested_objs = {}
        reverse_fields = cls.get_reverse_fields(model)
        nested_fields = get_nested_fields(model)
        if nested_fields and type(nested_fields) == dict:
            for field in nested_fields:
                # print("data", data)
                if reverse_fields.get(field):
                    reverse_nested_objs.update({field: data.pop(field, None)})

                if len(data) > 0:
                    sub_data = data.pop(field, None)

                    if sub_data:
                        serialized_data = nested_fields[field](
                            data=sub_data,
                            many=True if type(sub_data) == list else False,
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
        if cls._meta.many == True:
            input = kwargs.get("input")
            if isinstance(input, list):
                if len(input) == 1:
                    return cls.create(root, info, **{"input": input[0]})
                elif len(input) > 1:
                    # create many doesn't handle errors
                    for i in input:
                        # print("iiiii", i)
                        cls.create(root, info, **{"input": i})
                        # return {"ok": True}
                    return {"ok": True}

        # Handle multipart/form-data
        request_type = info.context.META.get("CONTENT_TYPE", "")
        if "multipart/form-data" in request_type and data:
            data.update({name: value for name, value in info.context.FILES.items()})

        # Validate and serialize the parent data (e.g., Facture)
        serializer = cls._meta.serializer_class(
            data=data, **cls.get_serializer_kwargs(root, info, **kwargs)
        )
        cls.check_permissions(root, info, "create", data)
        # Save the parent object (e.g., Facture)
        ok, obj = cls.save(serializer, root, info)
        if not ok:
            return cls.get_errors(obj)

        # Start processing nested fields for the root object
        cls.process_nested_fields(data, obj, root, info, cls._meta.model)

        return cls.perform_mutate(obj, info)

    @classmethod
    def process_nested_fields(cls, data, parent_obj, root, info, current_model):
        """
        Recursively handle nested and reverse nested fields from parent to child.
        """
        nested_objs, reverse_nested_objs = cls.manage_nested_fields(
            data, root, info, current_model
        )
        # Process nested fields (e.g., items)
        if nested_objs:
            for field, objs in nested_objs.items():
                nested_model = current_model._meta.get_field(field).related_model
                if isinstance(objs, list):
                    for o in objs:
                        if isinstance(o, dict):
                            child_obj = cls.create_nested_object(
                                field, o, parent_obj, root, info, nested_model
                            )
                            cls.process_nested_fields(
                                o, child_obj, root, info, nested_model
                            )  # Recursively process fields
                        else:
                            getattr(parent_obj, field).add(o)
                else:
                    if isinstance(objs, dict):
                        child_obj = cls.create_nested_object(
                            field, objs, parent_obj, root, info, nested_model
                        )
                        cls.process_nested_fields(
                            objs, child_obj, root, info, nested_model
                        )  # Recursively process fields
                    else:
                        getattr(parent_obj, field).add(objs)

        # Process reverse nested fields
        if reverse_nested_objs:
            for field, objs in reverse_nested_objs.items():
                related_field = cls.get_reverse_fields(current_model).get(field)
                related_model = related_field.related_model

                if isinstance(objs, list):
                    for o in objs:
                        if o:
                            o[related_field.field.name] = parent_obj.pk

                            child_obj = cls.create_nested_object(
                                field, o, parent_obj, root, info, current_model
                            )

                            cls.process_nested_fields(
                                o, child_obj, root, info, related_model
                            )  # Recursively process fields

                elif objs:
                    objs[related_field.field.name] = parent_obj.pk
                    child_obj = cls.create_nested_object(
                        field, objs, parent_obj, root, info, related_model
                    )
                    cls.process_nested_fields(
                        objs, child_obj, root, info, related_model
                    )  # Recursively process fields

    @classmethod
    def create_nested_object(cls, field, data, parent_obj, root, info, model):
        """
        Create a nested object and link it to its parent.
        """
        nested_serializer = get_nested_fields(model)[field]
        serialized_data = nested_serializer(data=data, many=False)

        ok, child_obj = cls.save(serialized_data, root, info)
        if not ok:
            return cls.get_errors(child_obj)
        # Link child to parent
        getattr(parent_obj, field).add(child_obj)

        return child_obj

    # @classmethod
    # def create(cls, root, info, **kwargs):
    #     if cls._meta.many == True:
    #         input = kwargs.get("input")
    #         if isinstance(input, list):
    #             if len(input) == 1:
    #                 return cls.create(root, info, **{"input": input[0]})
    #             elif len(input) > 1:
    #                 # create many doesn't handle errors
    #                 for i in input:
    #                     # print("iiiii", i)
    #                     cls.create(root, info, **{"input": i})
    #                     # return {"ok": True}
    #                 return {"ok": True}

    #     data = kwargs.get(cls._meta.input_field_name)
    #     request_type = info.context.META.get("CONTENT_TYPE", "")

    #     if "multipart/form-data" in request_type:
    #         if len(data) > 0:
    #             data.update({name: value for name, value in info.context.FILES.items()})

    #     try:
    #         nested_objs, reverse_nested_objs = cls.manage_nested_fields(
    #             data, root, info
    #         )

    #     except Exception as e:
    #         print("xxxxxxxxxxxxxxx", e)
    #         # raise GraphQLError(e)
    #         pass
    #     serializer = cls._meta.serializer_class(
    #         data=data, **cls.get_serializer_kwargs(root, info, **kwargs)
    #     )

    #     cls.check_permissions(root, info, "create", data)
    #     # print(serializer, root, info)
    #     ok, obj = cls.save(serializer, root, info)
    #     # if len(data) > 0:
    #     if len(data) > 0:
    #         # print(data.keys())
    #         for f in data.keys():
    #             # print(getattr(obj, f))
    #             try:
    #                 # print(obj,f)
    #                 getattr(obj, f).save()
    #             except Exception as E:
    #                 pass
    #     if not ok:
    #         return cls.get_errors(obj)
    #     if nested_objs:
    #         [getattr(obj, field).add(*objs) for field, objs in nested_objs.items()]
    #     if reverse_nested_objs:
    #         # for field, objs in reverse_nested_objs.items():
    #         #     if objs and  not isinstance(objs, list):

    #         #         getattr(obj, field).add(*objs)

    #         for field, objs in reverse_nested_objs.items():
    #             related_field = cls.get_reverse_fields().get(field)
    #             related_model = related_field.related_model
    #             # print(objs,reverse_nested_objs)
    #             if isinstance(objs, list):
    #                 for o in objs:
    #                     if related_model and o and related_field.field.name:
    #                         serialized_data = cls._meta.nested_fields[field](
    #                             data={**{**o, related_field.field.name: obj.pk}},
    #                             many=True if type(o) == list else False,
    #                         )
    #                         ok, res = cls.save(serialized_data, root, info)

    #                         if not ok:
    #                             return cls.get_errors(res)
    #                         # nested_obj = related_model.objects.create(
    #                         #     **{**o, related_field.field.column: obj.pk})
    #                         getattr(obj, field).add(res)
    #             else:
    #                 if objs is None:
    #                     continue
    #                 related_field = cls.get_reverse_fields().get(field)
    #                 serialized_data = cls._meta.nested_fields[field](
    #                     data={**{**objs, related_field.field.name: obj.pk}}, many=False
    #                 )
    #                 cls.manage_nested_fields(
    #                     {**{**objs, related_field.field.name: obj.pk}},
    #                     root,
    #                     info,
    #                     cls.get_reverse_fields().get(field).related_model,
    #                 )

    #                 ok, res = cls.save(
    #                     serialized_data,
    #                     None,
    #                     None,
    #                 )

    #                 if not ok:
    #                     return cls.get_errors(res)

    #                 # nested_objs, reverse_nested_objs = cls.manage_nested_fields({**{**objs, related_field.field.name: obj.pk}}, root, info)

    #     return cls.perform_mutate(obj, info)

    @classmethod
    def delete(cls, root, info, **kwargs):
        # print("xxxxxxxxxxxxxxxxxx", pk)
        pk = kwargs.get("id", [])
        pks = []
        for p in pk:
            try:
                int(p)
                pks.append(p)
            except Exception as E:
                pks.append(from_global_id(p)[1])
        old_obj = get_Object_or_None(cls._meta.model, _type="list", pk__in=pks)
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
    def delete_none_nested(cls, kwargs):
        print(cls._meta.__dict__)
        return

    @classmethod
    def update(cls, root, info, **kwargs):
        data = kwargs.get(cls._meta.input_field_name)
        request_type = info.context.META.get("CONTENT_TYPE", "")

        if "multipart/form-data" in request_type and data:
            data.update({name: value for name, value in info.context.FILES.items()})
        pk = data.get("id")

        try:
            int(pk)
        except:
            pk = from_global_id(data.get("id"))[1]

        # Retrieve the parent object
        instance = cls._meta.model.objects.get(pk=pk)
        # Update the parent object
        serializer = cls._meta.serializer_class(
            instance,
            data=data,
            partial=True,
            **cls.get_serializer_kwargs(root, info, **kwargs),
        )

        cls.check_permissions(root, info, "change", data)

        # Save the parent object
        ok, obj = cls.save(serializer, root, info)

        if not ok:
            return cls.get_errors(obj)

        # Process nested fields for updates
        cls.process_nested_fields_update(data, obj, root, info, cls._meta.model)

        return cls.perform_mutate(obj, info)

    @classmethod
    def process_nested_fields_update(cls, data, parent_obj, root, info, current_model):
        nested_objs, reverse_nested_objs = cls.manage_nested_fields(
            data, root, info, current_model
        )

        # Handle nested fields (e.g., items)
        if nested_objs:
            for field, objs in nested_objs.items():
                if objs is None:
                    continue
                nested_model = current_model._meta.get_field(field).related_model
                related_manager = getattr(parent_obj, field)

                # Collect existing IDs from the related manager
                existing_ids = set(related_manager.values_list("id", flat=True))
                input_ids = {
                    obj.get("id")
                    for obj in objs
                    if isinstance(obj, dict) and "id" in obj
                }

                # Delete objects not in input data
                to_delete = existing_ids - input_ids
                if to_delete:
                    related_manager.filter(id__in=to_delete).delete()

                # Create or update objects
                for obj_data in objs:
                    if isinstance(obj_data, dict) and "id" in obj_data:
                        # Update existing object
                        instance = nested_model.objects.get(id=obj_data["id"])
                        serializer = get_nested_fields(nested_model)[field](
                            instance, data=obj_data, partial=True
                        )
                        if serializer.is_valid():
                            serializer.save()
                        else:
                            raise ValidationError(serializer.errors)
                    else:
                        # Create new object
                        child_obj = cls.create_nested_object(
                            field, obj_data, parent_obj, root, info, nested_model
                        )
                        cls.process_nested_fields_update(
                            obj_data, child_obj, root, info, nested_model
                        )  # Recursively process fields

        # Handle reverse nested fields
        if reverse_nested_objs:
            for field, objs in reverse_nested_objs.items():
                if objs is None:
                    continue
                related_field = cls.get_reverse_fields(current_model).get(field)
                related_model = related_field.related_model

                # Collect existing IDs from the related model
                existing_ids = set(
                    related_model.objects.filter(
                        **{related_field.field.name: parent_obj.id}
                    ).values_list("id", flat=True)
                )
                input_ids = {
                    getID(obj.get("id"))
                    for obj in objs
                    if isinstance(obj, dict) and "id" in obj
                }

                # Delete objects not in input data
                to_delete = existing_ids - input_ids
                # print(to_delete, existing_ids, input_ids)
                if to_delete:
                    try:
                        related_model.objects.filter(id__in=to_delete).delete()
                    except ProtectedError as e:
                        raise ProtectedError(
                            _(
                                "Impossible de supprimer certaines instances du modèle 'EntrepriseAccount' car elles sont référencées via des clés étrangères protégées."
                            ),
                            e.protected_objects,  # Passer les objets protégés d'origine
                        )

                # Create or update objects
                for obj_data in objs:
                    if isinstance(obj_data, dict):
                        obj_data[related_field.field.name] = parent_obj.id
                        if "id" in obj_data:
                            # Update existing object
                            instance = related_model.objects.get(id=obj_data["id"])

                            serializer = get_nested_fields(current_model)[field](
                                instance, data=obj_data, partial=True
                            )
                            if serializer.is_valid():
                                updated_obj = serializer.save()
                                cls.process_nested_fields_update(
                                    obj_data, updated_obj, root, info, related_model
                                )
                            else:
                                raise ValidationError(serializer.errors)
                        else:
                            # Create new object
                            child_obj = cls.create_nested_object(
                                field, obj_data, parent_obj, root, info, current_model
                            )

                            cls.process_nested_fields_update(
                                obj_data, child_obj, root, info, related_model
                            )  # Recursively process fields

    # @classmethod
    # def process_nested_fields_update(cls, data, parent_obj, root, info, current_model):
    #     """
    #     Recursively handle nested fields for updates, creating, updating, or deleting child objects as needed.
    #     """

    #     nested_objs, reverse_nested_objs = cls.manage_nested_fields(
    #         data, root, info, current_model
    #     )

    #     # Process nested fields (e.g., items)
    #     if nested_objs:
    #         for field, objs in nested_objs.items():
    #             nested_model = current_model._meta.get_field(field).related_model
    #             manager = getattr(parent_obj, field)

    #             existing_objs = {str(obj.id): obj for obj in manager.all()}

    #             if isinstance(objs, list):
    #                 for o in objs:
    #                     if "id" in o and str(o["id"]) in existing_objs:
    #                         # Update existing object
    #                         child_obj = existing_objs.pop(str(o["id"]))
    #                         serializer = get_nested_fields(current_model)[field](
    #                             instance=child_obj, data=o, partial=True
    #                         )
    #                         ok, updated_obj = cls.save(serializer, root, info)
    #                         if not ok:
    #                             return cls.get_errors(updated_obj)
    #                     else:
    #                         # Create new object
    #                         cls.create_nested_object(
    #                             field, o, parent_obj, root, info, nested_model
    #                         )

    #                 # Delete remaining objects
    #                 for obj in existing_objs.values():
    #                     obj.delete()

    #             elif isinstance(objs, dict):
    #                 if "id" in objs and str(objs["id"]) in existing_objs:
    #                     # Update existing object
    #                     child_obj = existing_objs.pop(str(objs["id"]))
    #                     serializer = get_nested_fields(current_model)[field](
    #                         instance=child_obj, data=objs, partial=True
    #                     )
    #                     ok, updated_obj = cls.save(serializer, root, info)
    #                     if not ok:
    #                         return cls.get_errors(updated_obj)
    #                 else:
    #                     # Create new object
    #                     cls.create_nested_object(
    #                         field, objs, parent_obj, root, info, nested_model
    #                     )

    #     # Process reverse nested fields
    #     if reverse_nested_objs:
    #         for field, objs in reverse_nested_objs.items():
    #             related_field = cls.get_reverse_fields(current_model).get(field)
    #             related_model = related_field.related_model
    #             manager = getattr(parent_obj, field)

    #             existing_objs = {str(obj.id): obj for obj in manager.all()}
    #             if isinstance(objs, list):
    #                 for o in objs:
    #                     if "id" in o and str(o["id"]) in existing_objs:
    #                         # Update existing object
    #                         child_obj = existing_objs.pop(str(o["id"]))
    #                         serializer = get_nested_fields(current_model)[field](
    #                             instance=child_obj, data=o, partial=True
    #                         )
    #                         ok, updated_obj = cls.save(serializer, root, info)
    #                         if not ok:
    #                             return cls.get_errors(updated_obj)
    #                     else:
    #                         # Create new object
    #                         cls.create_nested_object(
    #                             field, o, parent_obj, root, info, related_model
    #                         )

    #                 # Delete remaining objects
    #                 for obj in existing_objs.values():
    #                     obj.delete()

    #             elif isinstance(objs, dict):
    #                 if "id" in objs and str(objs["id"]) in existing_objs:
    #                     # Update existing object
    #                     child_obj = existing_objs.pop(str(objs["id"]))
    #                     serializer = get_nested_fields(current_model)[field](
    #                         instance=child_obj, data=objs, partial=True
    #                     )
    #                     ok, updated_obj = cls.save(serializer, root, info)
    #                     if not ok:
    #                         return cls.get_errors(updated_obj)
    #                 else:
    #                     # Create new object
    #                     cls.create_nested_object(
    #                         field, objs, parent_obj, root, info, related_model
    #                     )

    # @classmethod
    # def update(cls, root, info, **kwargs):
    #     data = kwargs.get(cls._meta.input_field_name)

    #     request_type = info.context.META.get("CONTENT_TYPE", "")
    #     if "multipart/form-data" in request_type:
    #         data.update({name: value for name, value in info.context.FILES.items()})

    #     cls.check_permissions(root, info, "change", data)
    #     pk = data.pop("id")
    #     try:
    #         int(pk)
    #     except:
    #         pk = from_global_id(pk)[1]

    #     old_obj = get_Object_or_None(cls._meta.model, pk=pk)

    #     if old_obj:
    #         nested_objs, reverse_nested_objs = cls.manage_nested_fields(
    #             data, root, info, model=cls._meta.model
    #         )
    #         serializer = cls._meta.serializer_class(
    #             old_obj,
    #             data=data,
    #             partial=True,
    #             **cls.get_serializer_kwargs(root, info, **kwargs),
    #         )

    #         ok, obj = cls.save(serializer, root, info)
    #         # print(ok, obj)
    #         # return

    #         if not ok:
    #             return cls.get_errors(obj)
    #         elif nested_objs:
    #             [getattr(obj, field).add(*objs) for field, objs in nested_objs.items()]
    #         elif reverse_nested_objs:
    #             for field, objs in reverse_nested_objs.items():
    #                 related_field = cls.get_reverse_fields().get(field)
    #                 related_model = related_field.related_model
    #                 if isinstance(objs, list):
    #                     # if (len(objs) == 0):
    #                     # getattr(obj, field).all().delete()
    #                     # delete old object that has no reference
    #                     getattr(obj, field).all().delete()

    #                     for o in objs:
    #                         if related_model and o and related_field.field.name:
    #                             print(
    #                                 "xxx",
    #                                 {**{**o, related_field.field.name: obj.pk}},
    #                                 related_model,
    #                                 get_nested_fields(related_model),
    #                             )

    #                             serialized_data = get_nested_fields(related_model)[
    #                                 field
    #                             ](
    #                                 data={**{**o, related_field.field.name: obj.pk}},
    #                                 many=True if type(o) == list else False,
    #                             )
    #                             ok, res = cls.save(serialized_data, root, info)
    #                             if not ok:
    #                                 return cls.get_errors(res)
    #                             # getattr(obj, field).add(res)

    #         return cls.perform_mutate(obj, info)
    #     else:
    #         return cls.get_errors(
    #             [
    #                 ErrorType(
    #                     field="id",
    #                     messages=[
    #                         "A {} obj with id: {} do not exist".format(
    #                             cls._meta.model.__name__, pk
    #                         )
    #                     ],
    #                 )
    #             ]
    #         )

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
