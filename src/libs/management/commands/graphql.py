from django.core.management.base import BaseCommand
import os
from django.apps import apps
from models.queries.models import get_fields_and_properties


def remove_history_fields(arr):
    fields = ['history_id', 'history_date',
              'history_change_reason', 'history_type', 'history_user']
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
    property_names = [(name, getattr(getattr(getattr(model, name), "fget", name), 'short_description', name)) for name in dir(
        model) if isinstance(getattr(model, name), property) and name != "pk"]
    return property_names


def createFolder(app, folder):
    try:
        to_directory = f"{app}/graphqls/{folder}/"
        print(to_directory, os.path.isdir(to_directory))
        if not os.path.isdir(to_directory):
            print("mkdir")
            os.mkdir(to_directory)

    except Exception as e:
        print("xx", e)


def createFilters(app, model):
    createFolder(app, 'filters')
    model_name = model.__name__
    properties = get_fields_and_properties(model)
    reverse_fields = {
        f.name: f for f in model._meta.get_fields() if f.auto_created and not f.concrete
    }
    if os.path.exists(f"{app}/graphqls/filters/{model_name}.py"):
        print("file already exist")
        overide = input(
            f"type of  {model_name} already exist, would you like to override (y/n) \n")
        if overide == "n":
            return
    file = open(f"{app}/graphqls/filters/{model_name}.py", '+w')
    file.write('from django_filters import FilterSet\n')
    file.write(f"from {app} import models\n\n\n")
    file.write(f"class {model_name}Filters(FilterSet):\n")
    file.write(f"\tclass Meta:\n")
    file.write("\t\tfields = {\n")
    fields = list(filter(lambda x: x.name != "id", model._meta.fields))
    print(model_name, "xxxxxxxxxxxxxxx")

    file.write("\t\t\t'id':('exact',),\n")

    for f in fields:
        print(model_name, f, "xxxxxxxxxxxxxxx")
        _type = type(f).__name__
        if (_type == "CharField"):
            file.write(f"\t\t\t'{f.name}':('exact','icontains',),\n")
        if (_type == "IntegerField" or _type == "FloatField"):
            file.write(
                f"\t\t\t'{f.name}':('exact','icontains','gte','lte'),\n")
        if (_type == "DateField" or _type == "DateTimeField"):
            file.write(
                f"\t\t\t'{f.name}':('exact','gte','lte'),\n")

        if (_type == "ForeignKey"):
            file.write(
                f"\t\t\t'{f.name}':('exact','in'),\n")
        if (_type == "OneToOneField"):
            file.write(
                f"\t\t\t'{f.name}':('exact','in'),\n")
        if (_type == "ManyToManyField"):
            file.write(
                f"\t\t\t'{f.name}':('exact','in'),\n")
    for name, field in reverse_fields.items():
        file.write(
            f"\t\t\t'{name}':('exact','in'),\n")

    file.write("\t\t }\n")
    file.write(f"\t\tmodel = models.{model_name} \n")
    file.close()

    print(
        f"\x1b[5;30;42m...... file {app}/graphqls/filters/{model_name}.py has been created\x1b[0m ")


def createTypes(app, model):
    createFolder(app, 'types')
    model_name = model.__name__
    if os.path.exists(f"{app}/graphqls/types/{model_name}.py"):
        print("file already exist")
        overide = input(
            f"type of  {model_name} already exist, would you like to override (y/n) \n")
        if overide == "n":
            return
    base, = model.__bases__
    if base.__name__ == "Model" or base.__name__ == "PolymorphicModel":
        base = None

    properties = get_fields_and_properties(model)
    reverse_fields = {
        f.name: f for f in model._meta.get_fields() if f.auto_created and not f.concrete
    }

    file = open(f"{app}/graphqls/types/{model_name}.py", '+w')

    # for name, field in reverse_fields.items():
    #     file.writelines(
    #         [f"from {field.related_model._meta.app_label}.graphqls.types.{field.related_model.__name__} import {field.related_model.__name__}Type", '\n'])

    file.writelines(
        ["from libs.graphql.graphene.graphene import CustomDjangoObjectType\n", "import graphene\n",
         "from libs.graphql.graphene.CustomDjangoObjectListType import CustomDjangoListObjectType\n", "from libs.graphql.graphene_django_extras import LimitOffsetGraphqlPagination\n"])

    file.write(f"from {app} import models\n")
    file.write(
        f"from {app}.graphqls.filters import {model_name} as filters \n")
    if base:
        file.write(
            f"from {base._meta.app_label}.graphqls.types.{base.__name__} import {base.__name__}Type, {base.__name__}ListType \n")
    file.writelines(['\n', '\n'])
    if base:

        file.write(f"class {model_name}Type({base.__name__}Type):\n")
    else:
        file.write(f"class {model_name}Type(CustomDjangoObjectType):\n")

    for f in properties:
        name, title = f
        file.writelines([f"\t{name} = graphene.String()", '\n'])

    for name, field in reverse_fields.items():
        if type(field).__name__ == "OneToOneRel":
            file.writelines(
                [f"\t{name} = graphene.Field('{field.related_model._meta.app_label}.graphqls.types.{field.related_model.__name__}.{field.related_model.__name__}Type')", '\n'])
        else:
            file.writelines(
                [f"\t{name} = graphene.List('{field.related_model._meta.app_label}.graphqls.types.{field.related_model.__name__}.{field.related_model.__name__}Type')", '\n'])

    file.writelines(["\tdesignation = graphene.String()", '\n'])

    file.writelines(['\n', ])

    file.write(f"\tclass Meta:\n")
    file.write(f"\t\tname = '{model_name}Type'\n")
    file.write(f"\t\tmodel = models.{model_name} \n")
    file.write(f"\t\t# filter_fields = '__all__'\n")
    file.write(f"\t\tfilterset_class = filters.{model_name}Filters\n")

    file.write("\n\n")
    if base:
        file.write(f"class {model_name}ListType({base.__name__}ListType):\n")
    else:
        file.write(
            f"class {model_name}ListType(CustomDjangoListObjectType):\n")
    file.write(f"\tclass Meta:\n")
    file.write(f"\t\tname = '{model_name}ListType'\n")
    file.write(f"\t\tmodel = models.{model_name} \n")
    file.write(f"\t\t# filter_fields = '__all__'\n")
    file.write(f"\t\tfilterset_class = filters.{model_name}Filters\n")
    file.write("\t\tpagination = LimitOffsetGraphqlPagination()\n")
    file.write("\n\n")
    file.close()
    print(
        f"\x1b[5;30;42m...... file {app}/graphqls/types/{model_name}.py has been created\x1b[0m ")


def createSerializers(app, model):
    createFolder(app, 'serializers')
    model_name = model.__name__

    if os.path.exists(f"{app}/graphqls/serializers/{model_name}.py"):
        print("file already exist")
        overide = input(
            f"type of  {model_name} already exist, would you like to override (y/n) \n")
        if overide == "n":
            return
    file = open(f"{app}/graphqls/serializers/{model_name}.py", '+w')
    # Serializers
    file.writelines(["from rest_framework import serializers\n",
                     f"from {app} import models\n\n\n"])

    file.write(
        f"class {model_name}Serializer(serializers.ModelSerializer):\n")
    file.write(f"\tclass Meta:\n")
    file.write(f"\t\tmodel = models.{model_name}\n")
    file.write(f"\t\tfields = '__all__'\n")
    print(
        f"\x1b[5;30;42m...... file {app}/graphqls/serializers/{model_name}.py has been created\x1b[0m ")


def createMutaions(app, model):
    createFolder(app, 'mutations')
    model_name = model.__name__
    if os.path.exists(f"{app}/graphqls/mutations/{model_name}.py"):
        # print("file already exist")
        overide = input(
            f"type of  {model_name} already exist, would you like to override (y/n) \n")
        if overide == "n":
            return

    reverse_fields = {
        f.name: f for f in model._meta.get_fields() if f.auto_created and not f.concrete
    }

    model_lower = model_name.lower()
    file = open(f"{app}/graphqls/mutations/{model_name}.py", '+w')
    file.writelines([f"from {app}.graphqls.serializers import {model_name} as serializers\n",
                     "from libs.graphql.graphene.graphene import CustomDjangoSerializerMutation\n\n\n"])

    for name, field in reverse_fields.items():
        if name == "owner":
            continue
        if field.related_model.__name__ == "ContentType":
            continue
        file.write(
            f"from {field.related_model._meta.app_label}.graphqls.serializers.{field.related_model.__name__} import {field.related_model.__name__}Serializer\n")
    fields = list(filter(lambda x: x.name != "id" and x.name !=
                  "owner", model._meta.fields))

    for field in fields:
        if field.name == "owner":
            continue

        if type(field).__name__ == "ForeignKey":
            if field.related_model.__name__ == "ContentType":
                continue

            file.write(
                f"from {field.related_model._meta.app_label}.graphqls.serializers.{field.related_model.__name__} import {field.related_model.__name__}Serializer\n")

    file.write(
        f"class {model_name}Mutation(CustomDjangoSerializerMutation):\n")
    file.write("\tclass Meta:\n")
    file.write(
        f"\t\tserializer_class = serializers.{model_name}Serializer \n")
    file.write("\t\tnested_fields = {\n")
    for name, field in reverse_fields.items():
        if name == "owner":
            continue
        if name == "polymorphic_ctype":
            continue
        file.write(
            f"#\t\t '{name}': {field.related_model.__name__}Serializer,\n")
    for field in fields:

        if field.name == "owner":
            continue

        if type(field).__name__ == "ForeignKey":
            file.write(
                f"#\t\t'{field.name}': {field.related_model.__name__}Serializer,\n")
    file.write("\t\t}\n")

    file.write(
        f"\t\tpermissions = {{'create':'{app}.add_{model_lower}', 'change': '{app}.change_{model_lower}', 'delete': '{app}.delete_{model_lower}',}} \n")

    file.write("\t@classmethod\n")
    file.write("\tdef update(cls, root, info, **kwargs):\n")
    file.write("\t\t\n")
    file.write("\t\treturn super().update(root, info, **kwargs)\n")
    file.write("\t@classmethod\n")
    file.write("\tdef create(cls, root, info, **kwargs):\n")
    file.write("\t\t\n")
    file.write("\t\treturn super().create(root, info, **kwargs)\n")
    print(
        f"\x1b[5;30;42m...... file {app}/graphqls/mutations/{model_name}.py has been created\x1b[0m ")


def createSchema(app, model):
    createFolder(app, 'schemas')
    model_name = model.__name__
    if os.path.exists(f"{app}/graphqls/schemas/{model_name}.py"):
        print("file already exist")
        overide = input(
            f"type of  {model_name} already exist, would you like to override (y/n) \n")
        if overide == "n":
            return

    # Schemas
    schema = open(f"{app}/graphqls/schemas/{model_name}.py", "w+")
    schema.writelines([
        "from libs.graphql.graphene_django_extras import DjangoListObjectField, DjangoObjectField, DjangoFilterPaginateListField,  LimitOffsetGraphqlPagination\n"
        "import graphene\n",
        "from graphene_django.filter import DjangoFilterConnectionField\n",
        "from graphene.relay.node import Node\n",
        f"from {app}.graphqls.types import {model_name} as types\n",
        f"from {app}.graphqls.mutations import {model_name} as mutations\n\n\n"])

    # queries
    schema.write(f"class {model_name}Queries(object):\n")
    schema.write(
        f"\t{model_name.lower()}s= DjangoFilterPaginateListField(types.{model_name}Type,pagination=LimitOffsetGraphqlPagination())\n")
    schema.write(
        f"\tall_{model_name.lower()}s= DjangoListObjectField(types.{model_name}ListType)\n")
    schema.write(
        f"\t{model_name.lower()} = DjangoObjectField(types.{model_name}Type)\n\n\n")

    schema.write(
        f"class {model_name}Mutations(graphene.ObjectType):\n")
    schema.write(
        f'\tcreate_{model_name.lower()} = mutations.{model_name}Mutation.CreateField()\n')
    schema.write(
        f'\tupdate_{model_name.lower()} = mutations.{model_name}Mutation.UpdateField()\n')
    schema.write(
        f'\tdelete_{model_name.lower()} = mutations.{model_name}Mutation.DeleteField()\n')
    print(
        f"\x1b[5;30;42m...... file {app}/graphqls/schemas/{model_name}.py has been created\x1b[0m ")


def createDefaults(app, model):
    model_name = model.__name__
    line = f"from {app}.graphqls.schemas.{model_name} import {model_name}Queries, {model_name}Mutations"
    if os.path.exists(f"{app}/graphqls/defaults.py"):
        file = open(f"{app}/graphqls/defaults.py", "r")
        content = file.read()
        file.close()

        if line in content:
            pass
        else:
            f = open(f"{app}/graphqls/defaults.py", "r")
            content = f.read()
            content = line + "\n" + content
            add_query = f"{model_name}Queries,"
            add_mutation = f"{model_name}Mutations,"
            index_of_query = content.index("Queries(")
            index_of_mutation = content.index("Mutations(")

            content = content[0:index_of_query + len("Queries(")] + add_query + \
                content[index_of_query +
                        len("Queries("):]

            content = content[0:index_of_mutation + len(add_query) + len("Mutations(")] + add_mutation + \
                content[index_of_mutation +
                        len("Mutations(") + len(add_query):]

            # content = content[content.index(
            #     f"{app.upper()}Queries("):content.index(
            #     f"{app.upper()}Queries("):] + "xx"

            f = open(f"{app}/graphqls/defaults.py", "+w")

            f.write(content)

            # if content.count(f"{model_name}Querie") == 0:
            #     print("dmlkqsmdlkqsmdlk")

            #     content = content[0:content.index(
            #         f"{app.upper()}Queries(")] + content[:content.index(
            #             f"{app.upper()}Queries(")]
            #     f.write(content)

            # if content.count(f"{model_name}Mutations"):
            #     content.index(f"{app.upper()}Mutations(")
            f.close()

    print(
        f"\x1b[5;30;42m...... file {app}/graphqls/defaults.py has been created\x1b[0m ")


class Command(BaseCommand):
    help = 'Displays current time'

    def add_arguments(self, parser):
        parser.add_argument('--models', '--models', type=str, nargs='+',
                            help='Indicates the app.model you want to create graphql for')
        parser.add_argument('-app', '--app',
                            help='Create an admin account')
        parser.add_argument('-all', '--all', action='store_true',
                            help='Create an admin account')
        parser.add_argument('-r', '--register', action='store_true',
                            help='Create an admin account')

    def handle(self, *args, **kwargs):
        models = kwargs['models']
        app_label = kwargs['app']
        ALL = kwargs['all']

        if ALL:
            app_models = apps.get_app_config(app_label).get_models()
            for model in app_models:
                createTypes(app_label, model)
                createFilters(app_label, model)
                createSerializers(app_label, model)
                createMutaions(app_label, model)
                createSchema(app_label, model)
                if kwargs['register']:
                    createDefaults(app_label, model)
        else:
            for m in models:
                ####
                model = apps.get_model(app_label, m)
                createTypes(app_label, model)
                createFilters(app_label, model)
                createSerializers(app_label, model)
                createMutaions(app_label, model)
                createSchema(app_label, model)
                registre = kwargs['register']
                if registre:
                    createDefaults(app_label, model)


# ./manage.py graphql  --app billing  --r  --models ProformaItemFihce
# ./manage.py graphql  --app maintenance  --all
# ./manage.py graphql  --app operations   --r --models Charge
# ./manage.py graphql  --app tracking   --r --models FuelCharge
