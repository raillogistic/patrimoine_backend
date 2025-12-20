

# -*- coding: utf-8 -*-
import re
import string
from collections import OrderedDict
from random import choices

import graphene
from django.conf import settings
from django.contrib.contenttypes.fields import (
    GenericForeignKey,
    GenericRel,
    GenericRelation,
)
from django.db import models
from django.db.models.fields.reverse_related import ManyToOneRel as ReversedManyToOneRel
from django.utils.encoding import force_str
from django_shared_property.decorator import SharedPropertyField
from graphene import (
    ID,
    UUID,
    Boolean,
    Decimal,
    Dynamic,
    Enum,
    Field,
    Float,
    InputObjectType,
    Int,
    List,
    NonNull,
    String,
)
from graphene.types.json import JSONString
from graphene.types.utils import get_field_as, yank_fields_from_attrs
from graphene.utils.str_converters import to_camel_case
from graphene_django.compat import ArrayField, HStoreField, JSONField, RangeField
from graphene_file_upload.scalars import Upload
from graphql import Undefined
from polymorphic.base import PolymorphicModelBase

from .base_types import (
    Binary,
    CustomDate,
    CustomDateTime,
    CustomTime,
    GenericForeignKeyInputType,
    GenericForeignKeyType,
)
from .fields import DjangoFilterListField, DjangoListField
from .utils import get_model_fields, get_related_model, is_required

# from graphene_django.utils import import_single_dispatch


def import_single_dispatch():
    try:
        from functools import singledispatch
    except ImportError:
        singledispatch = None

    if not singledispatch:
        try:
            from singledispatch import singledispatch
        except ImportError:
            pass

    if not singledispatch:
        raise Exception(
            "It seems your python version does not include "
            "functools.singledispatch. Please install the 'singledispatch' "
            "package. More information here: "
            "https://pypi.python.org/pypi/singledispatch"
        )

    return singledispatch


def to_const(string):
    return re.sub(r"[\W|^]+", "_", string).upper()  # noqa


def random_sign():
    return "".join(choices(string.ascii_uppercase + string.digits, k=3))


singledispatch = import_single_dispatch()


NAME_PATTERN = r"^[_a-zA-Z][_a-zA-Z0-9]*$"
COMPILED_NAME_PATTERN = re.compile(NAME_PATTERN)


def assert_valid_name(name):
    """Helper to assert that provided names are valid."""
    assert COMPILED_NAME_PATTERN.match(name), (
        'Names must match /{}/ but "{}" does not.'.format(NAME_PATTERN, name)
    )


def convert_choice_name(name):
    name = to_const(force_str(name))
    try:
        assert_valid_name(name)
    except AssertionError:
        name = "A_%s" % name
    return name


def get_choices(choices):
    converted_names = []
    for value, help_text in choices:
        if isinstance(help_text, (tuple, list)):
            for choice in get_choices(help_text):
                yield choice
        else:
            name = convert_choice_name(value)
            while name in converted_names:
                name += "_" + str(len(converted_names))
            converted_names.append(name)
            description = help_text
            yield name, value, description


def convert_django_field_with_choices(
    field, registry=None, input_flag=None, nested_field=False
):
    choices = getattr(field, "choices", None)
    if choices:
        meta = field.model._meta

        name = "{}_{}_{}".format(meta.object_name, field.name, "Enum")
        if input_flag:
            name = "{}_{}".format(name, input_flag)
        name = to_camel_case(name)

        enum = registry.get_type_for_enum(name)
        if not enum:
            choices = list(get_choices(choices))
            named_choices = [(c[0], c[1]) for c in choices]
            named_choices_descriptions = {c[0]: c[2] for c in choices}

            class EnumWithDescriptionsType(object):
                @property
                def description(self):
                    return named_choices_descriptions[self.name]

            enum = Enum(name, list(named_choices), type=EnumWithDescriptionsType)
            registry.register_enum(name, enum)

        if type(field).__name__ == "MultiSelectField":
            return DjangoListField(
                enum,
                description=field.help_text or field.verbose_name,
                required=is_required(field) and input_flag == "create",
            )
        return enum(
            description=field.help_text or field.verbose_name,
            required=is_required(field) and input_flag == "create",
        )

    return convert_django_field(field, registry, input_flag, nested_field)


def construct_fields(
    model,
    registry,
    only_fields,
    include_fields,
    exclude_fields,
    input_flag=None,
    nested_fields=(),
):
    _model_fields = get_model_fields(model)

    # if settings.DEBUG:
    #     if input_flag == "create":
    #         _model_fields = sorted(
    #             _model_fields, key=lambda f: (not is_required(f[1]), f[0])
    #         )
    #     elif not input_flag:
    #         _model_fields = sorted(_model_fields, key=lambda f: f[0])

    fields = OrderedDict()
    if input_flag == "delete":
        converted = convert_django_field_with_choices(
            dict(_model_fields)["id"], registry
        )
        fields["id"] = converted
    else:
        for name, field in _model_fields:
            if input_flag == "create" and name == "id":
                continue

            is_included = include_fields and name in include_fields
            nested_field = True if name in nested_fields else False
            is_not_in_only = only_fields and name not in only_fields
            # is_already_created = name in options.fields
            is_excluded = (
                exclude_fields and name in exclude_fields
            )  # or is_already_created

            # https://docs.djangoproject.com/en/1.10/ref/models/fields/#django.db.models.ForeignKey.related_query_name
            is_no_backref = str(name).endswith("+")
            # handle no backref for manytomany with polymorphic added by milia khaled 21-01-2024
            if (
                is_no_backref
                and type(field) == ReversedManyToOneRel
                and "PolymorphicModel" in [clas.__name__ for clas in model.mro()]
            ):
                new_f = field
                try:
                    setattr(new_f, "name", field.name.split("_")[1].replace("+", ""))
                    converted = convert_django_field_with_choices(
                        new_f, registry, input_flag, nested_field
                    )
                    continue
                except:
                    continue

            # if is_not_in_only or is_excluded or is_no_backref:
            if not is_included and (is_not_in_only or is_excluded) or is_no_backref:
                # We skip this field if we specify only_fields and is not
                # in there. Or when we exclude this field in exclude_fields.
                # Or when there is no back reference.
                continue

            if (
                input_flag
                and not field.editable
                and not isinstance(
                    field, (models.fields.related.ForeignObjectRel, GenericForeignKey)
                )
            ):
                continue

            converted = convert_django_field_with_choices(
                field, registry, input_flag, nested_field
            )

            fields[name] = converted

    return fields


@singledispatch
def convert_django_field(
    field, registry=None, input_flag=None, nested_field=False, exclude_fields=[]
):
    raise Exception(
        "Don't know how to convert the Django field {} ({})".format(
            field, field.__class__
        )
    )


@convert_django_field.register(models.BinaryField)
@convert_django_field.register(SharedPropertyField)
@convert_django_field.register(models.BigAutoField)
@convert_django_field.register(models.CharField)
@convert_django_field.register(models.TextField)
@convert_django_field.register(models.EmailField)
@convert_django_field.register(models.SlugField)
@convert_django_field.register(models.URLField)
@convert_django_field.register(models.GenericIPAddressField)
def convert_field_to_string(field, registry=None, input_flag=None, nested_field=False):
    return String(
        description=field.help_text or field.verbose_name,
        required=is_required(field) and input_flag == "create",
    )




@convert_django_field.register(models.AutoField)
@convert_django_field.register(models.BigAutoField)
def convert_field_to_id(field, registry=None, input_flag=None, nested_field=False):
    if input_flag:
        return String(
            description=field.help_text or "Django object unique identification field",
            required=input_flag == "update",
        )
    return String(
        description=field.help_text or "Django object unique identification field",
        required=not field.null,
    )


@convert_django_field.register(models.UUIDField)
def convert_field_to_uuid(field, registry=None, input_flag=None, nested_field=False):
    return UUID(
        description=field.help_text or field.verbose_name,
        required=is_required(field) and input_flag == "create",
    )


@convert_django_field.register(models.PositiveIntegerField)
@convert_django_field.register(models.PositiveSmallIntegerField)
@convert_django_field.register(models.SmallIntegerField)
@convert_django_field.register(models.BigIntegerField)
@convert_django_field.register(models.IntegerField)
def convert_field_to_int(field, registry=None, input_flag=None, nested_field=False):
    return Int(
        description=field.help_text or field.verbose_name,
        required=is_required(field) and input_flag == "create",
    )


@convert_django_field.register(models.BooleanField)
def convert_field_to_boolean(field, registry=None, input_flag=None, nested_field=False):
    required = is_required(field) and input_flag == "create"
    if required:
        return NonNull(Boolean, description=field.help_text)
    return Boolean(description=field.help_text)


@convert_django_field.register(models.NullBooleanField)
def convert_field_to_nullboolean(
    field, registry=None, input_flag=None, nested_field=False
):
    return Boolean(
        description=field.help_text or field.verbose_name,
        required=is_required(field) and input_flag == "create",
    )




@convert_django_field.register(models.DecimalField)
def convert_field_to_float(field, registry=None, input_flag=None, nested_field=False):
    return Decimal(
        description=field.help_text or field.verbose_name,
        required=is_required(field) and input_flag == "create",
    )


@convert_django_field.register(models.FloatField)
@convert_django_field.register(models.DurationField)
def convert_field_to_float(field, registry=None, input_flag=None, nested_field=False):
    return Float(
        description=field.help_text or field.verbose_name,
        required=is_required(field) and input_flag == "create",
    )


@convert_django_field.register(models.DateField)
def convert_date_to_string(field, registry=None, input_flag=None, nested_field=False):
    return CustomDate(
        description=field.help_text or field.verbose_name,
        required=is_required(field) and input_flag == "create",
    )


@convert_django_field.register(models.DateTimeField)
def convert_datetime_to_string(
    field, registry=None, input_flag=None, nested_field=False
):
    return CustomDateTime(
        description=field.help_text or field.verbose_name,
        required=is_required(field) and input_flag == "create",
    )


@convert_django_field.register(models.TimeField)
def convert_time_to_string(field, registry=None, input_flag=None, nested_field=False):
    return CustomTime(
        description=field.help_text or field.verbose_name,
        required=is_required(field) and input_flag == "create",
    )


@convert_django_field.register(models.OneToOneRel)
def convert_onetoone_field_to_djangomodel(
    field, registry=None, input_flag=None, nested_field=False
):
    model = field.related_model

    def dynamic_type():
        if input_flag and not nested_field:
            return String(default_value=Undefined)
        _type = registry.get_type_for_model(model, for_input=input_flag)
        if not _type:
            return

        return Field(
            _type,
            required=is_required(field) and input_flag == "create",
            default_value=Undefined,
        )

    return Dynamic(dynamic_type)


@convert_django_field.register(models.ManyToManyField)
def convert_field_to_list_or_connection(
    field, registry=None, input_flag=None, nested_field=False
):
    model = get_related_model(field)

    def dynamic_type():
        if input_flag and not nested_field:
            return DjangoListField(
                graphene.String,
                required=not field.blank,  # and input_flag == "create",
                default_value=Undefined,
            )
        else:
            _type = registry.get_type_for_model(model, for_input=input_flag)
            if not _type:
                return
            elif input_flag and nested_field:
                return DjangoListField(_type)
            elif _type._meta.filter_fields or _type._meta.filterset_class:
                return DjangoFilterListField(
                    _type,
                    required=is_required(field) and input_flag == "create",
                    filterset_class=_type._meta.filterset_class,
                )
            else:
                return DjangoListField(
                    _type, required=is_required(field) and input_flag == "create"
                )

    return Dynamic(dynamic_type)


@convert_django_field.register(GenericRel)
@convert_django_field.register(models.ManyToManyRel)
@convert_django_field.register(models.ManyToOneRel)
def convert_many_rel_to_djangomodel(
    field,
    registry=None,
    input_flag=None,
    nested_field=False,
    only_fields=[],
    include_fields=[],
    exclude_fields=[],
):
    model = field.related_model

    def dynamic_type():
        if input_flag and not nested_field:
            return List(graphene.String, default_value=Undefined, required=False)
        else:
            _type = registry.get_type_for_model(
                model,
                for_input=input_flag,
            )

            if not _type:
                return
            elif input_flag and nested_field:
                # if input_flag == "update":
                #     exclude_fields.append("id") # uncomment this

                exclude_fields.append(field.field.name)

                my_type = yank_fields_from_attrs(
                    construct_fields(
                        model,
                        registry,
                        only_fields,
                        include_fields,
                        exclude_fields=exclude_fields,
                        input_flag=input_flag,
                        nested_fields=registry.get_type_for_model(
                            model,
                            for_input="create",
                        )._meta.nested_fields,
                    )
                )

                if input_flag == "update":
                    my_type["id"] = graphene.String(required=False)
                return graphene.List(
                    type(
                        f"{model.__name__}CreateNestedWith{field.model.__name__}{to_camel_case(input_flag)}{random_sign()}",
                        (InputObjectType,),
                        my_type if input_flag == "create" else my_type,
                    ),
                    required=False,
                    default_value=Undefined,
                )
            elif _type._meta.filter_fields or _type._meta.filterset_class:
                return DjangoFilterListField(
                    _type,
                    required=is_required(field) and input_flag == "create",
                    filterset_class=_type._meta.filterset_class,
                    default_value=Undefined,
                    description="xxxxxxxxxx",
                )
            else:
                return DjangoListField(
                    _type,
                    required=is_required(field) and input_flag == "create",
                    default_value=Undefined,
                )

    return Dynamic(dynamic_type)


@convert_django_field.register(models.OneToOneField)
@convert_django_field.register(models.ForeignKey)
def convert_field_to_djangomodel(
    field,
    registry=None,
    input_flag=None,
    nested_field=False,
    only_fields=[],
    include_fields=[],
    exclude_fields=[],
):
    model = get_related_model(field)

    def dynamic_type():
        # Avoid create field for auto generate OneToOneField product of an inheritance
        if isinstance(field, models.OneToOneField) and issubclass(
            field.model, field.related_model
        ):
            return

        if input_flag and not nested_field:
            return graphene.types.InputField(
                graphene.String,
                description=field.help_text or field.verbose_name,
                default_value=Undefined if is_required(field) else Undefined,
                required=is_required(field) and input_flag == "create",
            )

        _type = registry.get_type_for_model(model, for_input=input_flag)

        if not _type:
            return

        if input_flag == "update" and nested_field:
            my_type = yank_fields_from_attrs(
                construct_fields(
                    model,
                    registry,
                    only_fields,
                    include_fields,
                    exclude_fields=["id"],
                    input_flag="update",
                    nested_fields=(),
                )
            )

            return graphene.Field(
                type(
                    f"{model.__name__}UpdateNestedWith{field.remote_field.related_model.__name__.upper()}{random_sign()}",
                    (InputObjectType,),
                    my_type,
                ),
                default_value=Undefined,
                required=is_required(field) and input_flag == "create",
            )
        return graphene.Field(
            _type,
            default_value=Undefined,
            description=field.help_text or field.verbose_name or field.verbose_name,
            required=is_required(field) and input_flag == "create",
        )

    return Dynamic(dynamic_type)


@convert_django_field.register(GenericForeignKey)
def convert_generic_foreign_key_to_object(
    field, registry=None, input_flag=None, nested_field=False
):
    def dynamic_type():
        key = "{}_{}".format(field.name, field.model.__name__.lower())
        if input_flag is not None:
            key = "{}_{}".format(key, input_flag)

        key = to_camel_case(key)
        model = field.model
        ct_field = None
        fk_field = None
        required = False
        for f in get_model_fields(model):
            if f[0] == field.ct_field:
                ct_field = f[1]
            elif f[0] == field.fk_field:
                fk_field = f[1]
            if fk_field is not None and ct_field is not None:
                break

        if ct_field is not None and fk_field is not None:
            required = (is_required(ct_field) and is_required(fk_field)) or required

        if input_flag:
            return GenericForeignKeyInputType(
                description="Input Type for a GenericForeignKey field",
                required=required and input_flag == "create",
            )

        _type = registry.get_type_for_enum(key)
        if not _type:
            _type = GenericForeignKeyType

        # return Field(_type, description=field.help_text or field.verbose_name, required=field.null)
        return Field(
            _type,
            description="Type for a GenericForeignKey field",
            required=required and input_flag == "create",
        )

    return Dynamic(dynamic_type)


@convert_django_field.register(GenericRelation)
def convert_generic_relation_to_object_list(
    field, registry=None, input_flag=None, nested_field=False
):
    model = field.related_model

    def dynamic_type():
        if input_flag:
            return

        _type = registry.get_type_for_model(model)
        if not _type:
            return
        return DjangoListField(_type)

    return Dynamic(dynamic_type)


@convert_django_field.register(ArrayField)
def convert_postgres_array_to_list(
    field, registry=None, input_flag=None, nested_field=False
):
    base_type = convert_django_field(field.base_field)
    if not isinstance(base_type, (List, NonNull)):
        base_type = type(base_type)
    return List(
        base_type,
        description=field.help_text or field.verbose_name,
        required=is_required(field) and input_flag == "create",
    )


@convert_django_field.register(HStoreField)
@convert_django_field.register(JSONField)
def convert_postgres_field_to_string(
    field, registry=None, input_flag=None, nested_field=False
):
    return JSONString(
        description=field.help_text or field.verbose_name,
        required=is_required(field) and input_flag == "create",
    )


@convert_django_field.register(RangeField)
def convert_postgres_range_to_string(
    field, registry=None, input_flag=None, nested_field=False
):
    inner_type = convert_django_field(field.base_field)
    if not isinstance(inner_type, (List, NonNull)):
        inner_type = type(inner_type)
    return List(
        inner_type,
        description=field.help_text or field.verbose_name,
        required=is_required(field) and input_flag == "create",
    )


from libs.graphql.graphene.types import Binary

@convert_django_field.register(models.BinaryField)
def convert_binary_field_to_graphql(field, registry=None):
    return Binary(description=field.help_text, required=not field.null)

@convert_django_field.register(models.FileField)
@convert_django_field.register(models.BinaryField)
def convert_field_to_file(field, registry=None, input_flag=None, nested_field=False):
    return Upload(
        description=field.help_text or field.verbose_name,
        required=False,
    )
