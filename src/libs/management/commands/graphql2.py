import inspect
import os
import shutil
import time
from datetime import date, datetime
from inspect import getattr_static, signature
from typing import List, get_type_hints

from django.apps import apps
from django.core.management.base import BaseCommand
from django.db.models import Model
from models.queries.models import get_fields_and_properties
from polymorphic.models import PolymorphicModel


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
        (
            name,
            getattr(
                getattr(getattr(model, name), "fget", name), "short_description", name
            ),
        )
        for name in dir(model)
        if isinstance(getattr(model, name), property) and name != "pk"
    ]
    return property_names


def get_fields_and_properties_with_types(model):
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
                return f"graphene.List('{_type._meta.app_label}.graphqls.types.{_type.__name__}.{_type.__name__}Type')"
            else:
                return f"graphene.Field('{_type._meta.app_label}.graphqls.types.{_type.__name__}.{_type.__name__}Type')"
        else:
            _type = _type.__name__

            # print("qqqqqqqqqq", name, _type.__class__.__name__)
        get_types = {
            "_empty": f"graphene.List(graphene.String)"
            if is_list
            else f"graphene.String(source='{name}')",
            "str": f"graphene.List(graphene.String)"
            if is_list
            else f"graphene.String(source='{name}')",
            "int": f"graphene.List(graphene.Int)"
            if is_list
            else f"graphene.Int(source='{name}')",
            "float": f"graphene.List(graphene.Float)"
            if is_list
            else f"graphene.Float(source='{name}')",
            "bool": f"graphene.List(graphene.Boolean)"
            if is_list
            else f"graphene.Boolean(source='{name}')",
            "date": f"graphene.Date()",
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


def createFolder(app, folder):
    try:
        to_directory = f"{app}/graphqls/{folder}/"
        if not os.path.isdir(to_directory):
            print("mkdir")
            os.mkdir(to_directory)

    except Exception as e:
        print("xx", e)


def createQuickFilters(app, model):
    createFolder(app, "filters/quick")
    model_name = model.__name__
    if os.path.exists(f"{app}/graphqls/filters/quick/{model_name}.py"):
        # print("xx", res)
        return
    else:
        # models = apps.get_app_config(app).get_models()
        # f = {}
        # for m in models:
        _fields = {}
        for field in model._meta.get_fields():
            _type = field.__class__.__name__
            if _type == "TextField" or _type == "CharField":
                _fields = {**_fields, field.name: "str"}
            elif _type == "IntegerField":
                _fields = {**_fields, field.name: "int"}
        f = _fields

        res = f"""
filters = {f}

        """
        file = open(
            f"{app}/graphqls/filters/quick/{model_name}.py", "+w", encoding="utf-8"
        )
        file.write(res)


def createCustomFilters(app, model):
    createFolder(app, "filters")
    model_name = model.__name__

    #
    if os.path.exists(f"{app}/graphqls/filters/Custom{model_name}.py"):
        # print("xx", res)
        return
    else:
        # models = apps.get_app_config(app).get_models()
        # f = {}
        # for m in models:
        base = model.__base__
        import_base = ""
        if (
            (issubclass(base, Model) or issubclass(base, PolymorphicModel))
            and base.__name__ != "PolymorphicModel"
            and base.__name__ != "Model"
            and base.__name__ != "object"
        ):
            import_base = f"from {base._meta.app_label}.graphqls.filters.Custom{base.__name__} import OtherFilters as OtherFiltersBase"

        res = f"""
from django.db.models import Q
from {app} import models
from django_filters import FilterSet,CharFilter,BooleanFilter
{import_base}
other_filters = {{
    
}}
class OtherFilters({'OtherFiltersBase,' if import_base else '' }FilterSet):

    other_filter = CharFilter(method="resolve_other_filter")

    def resolve_other_filter(self,queryset,name,value):
        return queryset
"""
        file = open(f"{app}/graphqls/filters/Custom{model_name}.py", "+w")
        file.write(res)


from libs.models.fields import field_by_numbers, get_reversed_manytoone_fields


def more_filters(model):
    fields = get_reversed_manytoone_fields(model)
    res = ""
    floats = get_reversed_manytoone_fields(model)
    for f in floats:
        for f2 in field_by_numbers(
            f.related_model,
        ):
            res = (
                res
                + f"""
    {f.name}__{f2.name}__sum = NumberFilter(method="resolve_{f.name}__{f2.name}__sum")
    def resolve_{f.name}__{f2.name}__sum(self,queryset,name,value):
        return queryset
"""
            )
            print(f"{f.name}__{f2.name}")

    for f in fields:
        res = (
            res
            + f"""
    ###################### {f.name} ##############################
    {f.name}_count = NumberFilter(method='resolve_{f.name}_count')
    {f.name}_count_gte = NumberFilter(method='resolve_{f.name}_count_gte')
    {f.name}_count_lte = NumberFilter(method='resolve_{f.name}_count_lte')
    
    def resolve_{f.name}_count(self,queryset,name,value):
        return count_of_filter(queryset,'{f.name}',value) if value or value==0 else queryset
    def resolve_{f.name}_count_gte(self,queryset,name,value):
        return count_of_filter(queryset,'{f.name}',value,"gte") if value or value==0 else queryset
    def resolve_{f.name}_count_lte(self,queryset,name,value):
        return count_of_filter(queryset,'{f.name}',value,"lte") if value or value==0 else queryset
"""
        )

    floats = get_reversed_manytoone_fields(model)
    for f in floats:
        for f2 in field_by_numbers(
            f.related_model,
        ):
            res = (
                res
                + f"""
    {f.name}__{f2.name}_sum = NumberFilter(method='resolve_{f.name}__{f2.name}_sum')
    {f.name}__{f2.name}_sum_gte = NumberFilter(method='resolve_{f.name}__{f2.name}_sum_gte')
    {f.name}__{f2.name}_sum_lte = NumberFilter(method='resolve_{f.name}__{f2.name}_sum_lte')

    def resolve_{f.name}__{f2.name}_sum(self,queryset,name,value):
        return sum_of_filter(queryset,'{f.name}__{f2.name}',value) if value else queryset
    def resolve_{f.name}__{f2.name}_sum_gte(self,queryset,name,value):
        return sum_of_filter(queryset,'{f.name}__{f2.name}',value,"gte") if value else queryset
    def resolve_{f.name}__{f2.name}_sum_lte(self,queryset,name,value):
        return sum_of_filter(queryset,'{f.name}__{f2.name}',value,"lte") if value else queryset
"""
            )
    return res


def createFilters(app, model, erase="n"):
    createFolder(app, "filters")
    model_name = model.__name__
    reverse_fields = {
        f.name: f for f in model._meta.get_fields() if f.auto_created and not f.concrete
    }
    if os.path.exists(f"{app}/graphqls/filters/{model_name}.py"):
        print("file already exist")
        overide = (
            erase
            if erase
            else input(
                f"type of  {model_name} already exist, would you like to override (y/n) \n"
            )
        )
        if overide == "n":
            return

    file = open(f"{app}/graphqls/filters/{model_name}.py", "+w")

    fields = list(filter(lambda x: x.name != "id", model._meta.fields))
    # file.write('from django_filters import FilterSet\n')
    # file.write(f"from {app} import models\n\n\n")
    # file.write(f"class {model_name}Filters(FilterSet):\n")
    # file.write(f"\tclass Meta:\n")
    # file.write("\t\tfields = {\n")
    fields = list(filter(lambda x: x.name != "id", model._meta.fields))
    # print(model_name, "xxxxxxxxxxxxxxx")

    # file.write("\t\t\t'id':('exact',),\n")
    filters = "{"
    for f in fields:
        if f.name == "polymorphic_ctype":
            continue
        # print(model_name, f, "xxxxxxxxxxxxxxx")
        _type = type(f).__name__
        if _type == "CharField":
            filters = filters + f"\t\t\t'{f.name}':('exact','icontains','isnull'),\n"
        if _type == "BooleanField":
            filters = filters + f"\t\t\t'{f.name}':('exact','isnull'),\n"

        if _type == "TimeField":
            filters = filters + f"\t\t\t'{f.name}':('exact','gte','lte','isnull'),\n"

        if _type == "IntegerField" or _type == "FloatField":
            filters = (
                filters
                + f"\t\t\t'{f.name}':('exact','icontains','gte','gt','lte','lt','isnull'),\n"
            )

        if _type == "DateField" or _type == "DateTimeField":
            filters = (
                filters
                + f"\t\t\t'{f.name}':('exact','gte','gt','lte','lt','isnull'),\n"
            )

        if _type == "ForeignKey":
            filters = filters + f"\t\t\t'{f.name}':('exact','in','isnull',),\n"

        if _type == "OneToOneField":
            filters = filters + f"\t\t\t'{f.name}':('exact','isnull'),\n"

        if _type == "ManyToManyField":
            filters = filters + f"\t\t\t'{f.name}':('exact','in','isnull'),\n"

    for name, field in reverse_fields.items():
        if type(field).__name__ == "OneToOneRel":
            filters = filters + f"\t\t\t'{name}':('exact','isnull'),\n"
        else:
            filters = filters + f"\t\t\t'{name}':('exact','in','isnull'),\n"

    filters = filters + "**other_filters}"

    # file.write("\t\t }\n")
    # file.write(f"\t\tmodel = models.{model_name} \n")
    res = f"""
from django_filters import FilterSet,CharFilter,MultipleChoiceFilter,NumberFilter
from {app}.models import {model_name}
from {app}.graphqls.filters.quick.{model_name} import filters

from django.db.models import Q
from .Custom{model_name} import other_filters, OtherFilters
from libs.graphql.filters import PeriodFilters
from libs.models.func import count_of_filter,sum_of_filter


class {model_name}Filters(OtherFilters,PeriodFilters):
    class Meta:
        fields = {filters}
        model = {model_name}
        
    include = MultipleChoiceFilter(method="resolve_include",)
    def resolve_include(self, queryset,*args, **kwargs):
       return queryset
    quick = CharFilter(method="resolve_quick")

    def resolve_quick(self, queryset, name, value):
        if len(value) == 0:
            return queryset
        queries = []
        for key, _type in filters.items():
            try:
                val = int(value) if _type == "int" else str(value, )
                queries.append({{f"{{key}}__icontains": val}})
            except:
                continue
        if len(queries) == 0:
            return queryset
        query = Q(**queries.pop())
        for item in queries:
            query |= Q(**item)

        return queryset.filter(query)

    ################### Count Filters ######################
    {more_filters(model)}
    ########################################################
    """
    file.write(res)
    file.close()

    print(
        f"\x1b[5;30;42m...... file {app}/graphqls/filters/{model_name}.py has been created\x1b[0m "
    )


def createResolvers(app, model):
    createFolder(app, "resolvers")
    model_name = model.__name__
    if os.path.exists(f"{app}/graphqls/resolvers/{model_name}.py"):
        return
    else:
        file = open(f"{app}/graphqls/resolvers/{model_name}.py", "+w")
        res = f"""
from {app} import models
from django.db.models import Q
from libs.graphql.permissions import is_owner
from django.core.exceptions import PermissionDenied


def resolve_{model_name.lower()}_perms(info,qs,**kwargs):
    user = info.context.user
    return qs



def resolve_{model_name.lower()}_object_perms(info, node):
    user = info.context.user
    return node
    # profile = getattr(user, 'profile', None)
    # if user.is_superuser:
    #     return node
    # #same structure
    # # if profile.structure == node.structure:
    # #     return node
    # return node
    # raise PermissionDenied("vous n'avez pas la permission pour consulter ce objet")

# sub_structures(qs, profile)
# same_structures(qs, profile)
# is_owner(qs, profile)
# if user_type == "responsable" :
        #     return sub_structures(qs, profile)
        """
    file.write(res)


def createCustomTypes(app, model):
    createFolder(app, "types")
    model_name = model.__name__

    if os.path.exists(f"{app}/graphqls/types/Custom{model_name}.py"):
        return
    else:
        file = open(f"{app}/graphqls/types/Custom{model_name}.py", "+w")
        base = model.__bases__[0]
        import_base = ""
        if base.__name__ == "Model" or base.__name__ == "PolymorphicModel":
            inherit = "object"
        else:
            base_app = base.__module__.split(".")[0]
            inherit = f"Custom{base.__name__}Type"
            import_base = f"from {base_app}.graphqls.types.Custom{base.__name__} import Custom{base.__name__}Type"
        res = f"""
import graphene
{import_base}
class Custom{model_name}Type({inherit}):
    designation = graphene.String()
        """
        file.write(res)
        file.close()


class ParentClass:
    def parent_method(self):
        pass


class ChildClass(ParentClass):
    def child_method(self):
        pass


def get_functions(model):
    child_class_functions = inspect.getmembers(model, inspect.isfunction)
    child_class_name = model.__name__
    child_class_methods = [
        method
        for name, method in child_class_functions
        if child_class_name in getattr(method, "__qualname__", "") and name != "save"
    ]
    return child_class_methods


def get_params(function):
    signature = inspect.signature(function)
    return [b for a, b in signature.parameters.items() if a != "self"]


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


def createFunctionMutations(app, model, erase="n"):
    createFolder(app, "functions")
    model_name = model.__name__
    if os.path.exists(f"{app}/graphqls/functions/{model_name}.py"):
        print("file already exist")
        overide = (
            erase
            if erase
            else input(
                f"type of  {model_name} already exist, would you like to override (y/n) \n"
            )
        )
        if overide == "n":
            return

    if "Historical" in model.__name__:
        return
    functions = get_functions(model)

    res = f"""
import graphene
from {app}.models import {model_name}
from django.core.exceptions import ObjectDoesNotExist

    """
    for f in functions:
        res = res + createMutationFromFunction(f, app, model_name)
    res = f"""
{res}
class {model_name}CustomFunctionMutations(graphene.ObjectType):
{declare_function_mutations(functions,model_name)}    

"""
    file = open(f"{app}/graphqls/functions/{model_name}.py", "+w", encoding="utf-8")
    file.write(res)
    file.close()


def createTypes(app, model, erase="n"):
    createCustomTypes(app, model)
    createFolder(app, "types")
    model_name = model.__name__

    sums = ""
    floats = get_reversed_manytoone_fields(model)
    for f in floats:
        for f2 in field_by_numbers(
            f.related_model,
        ):
            sums = (
                sums
                + f"""
    {f.name}__{f2.name}__avg = graphene.Float()
    
    def resolve_{f.name}__{f2.name}__avg(self,info,**kwargs):
        return avg_of(self,"{f.name}","{f2.name}")
    {f.name}__{f2.name}__sum = graphene.Float()
    def resolve_{f.name}__{f2.name}__sum(self,info,**kwargs):
        return sum_of(self,"{f.name}","{f2.name}")
"""
            )
    if os.path.exists(f"{app}/graphqls/types/{model_name}.py"):
        print("file already exist")
        overide = (
            erase
            if erase
            else input(
                f"type of  {model_name} already exist, would you like to override (y/n) \n"
            )
        )
        if overide == "n":
            return
    if "Historical" in model.__name__:
        return
    base = model.__bases__[0]

    if base.__name__ == "Model" or base.__name__ == "PolymorphicModel":
        base = None
    properties = get_fields_and_properties_with_types(model)

    import_related = ""

    # properties
    for name, title, _type in properties:
        import_related = import_related + f"    {name} = {_type}\n"

    for many in model._meta.many_to_many:
        if many.related_model._meta.app_label == "auth":
            continue
        import_related = (
            import_related
            + f"    {many.name} = graphene.List(f'{many.related_model._meta.app_label}.graphqls.types.{many.related_model.__name__}.{many.related_model.__name__}Type')\n"
        )
        import_related = (
            import_related
            + f"    def resolve_{many.name}(self,info):\n        return self.{many.name}.all()\n"
        )

    fields = list(
        filter(
            lambda x: x.name != "id"
            and (
                type(x).__name__ == "ForeignKey"
                or (type(x).__name__ == "OneToOneField")
            )
            and not "polymorphic_ctype" in x.name,
            model._meta.fields,
        )
    )

    for f in fields:
        # if type(field).__name__ =="OneToOneField":
        #     import_related = import_related + \
        #         f"{f.name}" =
        if f.related_model._meta.app_label == "auth":
            continue
        import_related = (
            import_related
            + f"    {f.name} = graphene.Field('{f.related_model._meta.app_label}.graphqls.types.{f.related_model.__name__}.{f.related_model.__name__}Type')\n"
        )

    reverse_fields = {
        f.name: f for f in model._meta.get_fields() if f.auto_created and not f.concrete
    }

    file = open(f"{app}/graphqls/types/{model_name}.py", "+w")
    for name, field in reverse_fields.items():
        if field.related_model._meta.app_label == "auth":
            continue

        if type(field).__name__ == "OneToOneRel":
            import_related = (
                import_related
                + f"    {name} = graphene.Field('{field.related_model._meta.app_label}.graphqls.types.{field.related_model.__name__}.{field.related_model.__name__}Type')\n"
            )

        else:
            get_name = field.name
            if not field.related_name:
                get_name = f"{field.related_model.__name__.lower()}_set"
            import_related = (
                import_related
                + f"    {get_name} = graphene.List('{field.related_model._meta.app_label}.graphqls.types.{field.related_model.__name__}.{field.related_model.__name__}Type')\n"
            )
            import_related = import_related + f"    {get_name}_count = graphene.Int()\n"

            import_related = (
                import_related
                + f"    def resolve_{get_name}(self,info):\n        return self.{get_name}.all()\n"
            )

            import_related = (
                import_related
                + f"    def resolve_{get_name}_count(self,info):\n        return self.{get_name}.count()\n"
            )

    if base:
        base_name = base.__name__
        base_app = base.__module__.split(".")[0]
        base_import = (
            ""
            if base is None
            else f"from {base_app}.graphqls.types.{base_name} import {base_name}Type "
        )
        base_name = f"{base_name}Type"
    else:
        base_name = "CustomDjangoObjectType"
        base_import = ""

    res = f"""
{base_import}
import graphene
from graphene import Node
from libs.graphql.types import CustomNode
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from graphene import relay
from libs.graphql.types import CustomDjangoObjectType, CustomConnection
from {app} import models
from {app}.graphqls.filters import {model_name} as filters
from .Custom{model_name} import Custom{model_name}Type 
from libs.models.func import sum_of,avg_of

class {model_name}Type({base_name},Custom{model_name}Type):
    designation = graphene.String()
{import_related}
{sums}
    class Meta:
        connection_class = CustomConnection()
        interfaces = (CustomNode,)
        model = models.{model_name}
        name = "{model_name}Type"
        fields = '__all__'
        # filter_fields = '__all__'
        filterset_class = filters.{model_name}Filters

class {model_name}DesType(CustomDjangoObjectType,Custom{model_name}Type):
    designation = graphene.String()
    class Meta:
        connection_class = CustomConnection()
        interfaces = (CustomNode,)
        model = models.{model_name}
        name = "{model_name}DesType"
        fields = ['id','designation']
        # filter_fields = '__all__'
        filterset_class = filters.{model_name}Filters
    """

    file.write(res)

    # file.writelines(
    #     ["from libs.graphql.graphene.graphene import CustomDjangoObjectType\n", "import graphene\n",
    #      "from libs.graphql.graphene.CustomDjangoObjectListType import CustomDjangoListObjectType\n", "from libs.graphql.graphene_django_extras import LimitOffsetGraphqlPagination\n"])

    # file.write(f"from {app} import models\n")
    # file.write(
    #     f"from {app}.graphqls.filters import {model_name} as filters \n")
    # if base:
    #     file.write(
    #         f"from {base._meta.app_label}.graphqls.types.{base.__name__} import {base.__name__}Type, {base.__name__}ListType \n")
    # file.writelines(['\n', '\n'])
    # if base:

    #     file.write(f"class {model_name}Type({base.__name__}Type):\n")
    # else:
    #     file.write(f"class {model_name}Type(CustomDjangoObjectType):\n")

    # for f in properties:
    #     name, title = f
    #     file.writelines([f"\t{name} = graphene.String()", '\n'])

    # for name, field in reverse_fields.items():
    #     if type(field).__name__ == "OneToOneRel":
    #         file.writelines(
    #             [f"\t{name} = graphene.Field('{field.related_model._meta.app_label}.graphqls.types.{field.related_model.__name__}.{field.related_model.__name__}Type')", '\n'])
    #     else:
    #         file.writelines(
    #             [f"\t{name} = graphene.List('{field.related_model._meta.app_label}.graphqls.types.{field.related_model.__name__}.{field.related_model.__name__}Type')", '\n'])

    # file.writelines(["\tdesignation = graphene.String()", '\n'])

    # file.writelines(['\n', ])

    # file.write(f"\tclass Meta:\n")
    # file.write(f"\t\tname = '{model_name}Type'\n")
    # file.write(f"\t\tmodel = models.{model_name} \n")
    # file.write(f"\t\t# filter_fields = '__all__'\n")
    # file.write(f"\t\tfilterset_class = filters.{model_name}Filters\n")

    # file.write("\n\n")
    # if base:
    #     file.write(f"class {model_name}ListType({base.__name__}ListType):\n")
    # else:
    #     file.write(
    #         f"class {model_name}ListType(CustomDjangoListObjectType):\n")
    # file.write(f"\tclass Meta:\n")
    # file.write(f"\t\tname = '{model_name}ListType'\n")
    # file.write(f"\t\tmodel = models.{model_name} \n")
    # file.write(f"\t\t# filter_fields = '__all__'\n")
    # file.write(f"\t\tfilterset_class = filters.{model_name}Filters\n")
    # file.write("\t\tpagination = LimitOffsetGraphqlPagination()\n")
    # file.write("\n\n")
    file.close()
    print(
        f"\x1b[5;30;42m...... file {app}/graphqls/types/{model_name}.py has been created\x1b[0m "
    )


def createSerializers(app, model, erase="n"):
    createFolder(app, "serializers")
    model_name = model.__name__

    if os.path.exists(f"{app}/graphqls/serializers/{model_name}.py"):
        print("file already exist")
        overide = (
            erase
            if erase
            else input(
                f"type of  {model_name} already exist, would you like to override (y/n) \n"
            )
        )
        if overide == "n":
            return
    file = open(f"{app}/graphqls/serializers/{model_name}.py", "+w")
    # Serializers
    file.writelines(
        [
            "from libs.graphql.serializers import CustomSerializer\n",
            f"from {app} import models\n\n\n",
        ]
    )

    file.write(f"class {model_name}Serializer(CustomSerializer):\n")
    file.write(f"\tclass Meta:\n")
    file.write(f"\t\tmodel = models.{model_name}\n")
    file.write(f"\t\tfields = '__all__'\n")
    print(
        f"\x1b[5;30;42m...... file {app}/graphqls/serializers/{model_name}.py has been created\x1b[0m "
    )


def createMutations(app, model, erase="n"):
    createFolder(app, "mutations")
    model_name = model.__name__
    if os.path.exists(f"{app}/graphqls/mutations/{model_name}.py"):
        # print("file already exist")
        overide = (
            erase
            if erase
            else input(
                f"type of  {model_name} already exist, would you like to override (y/n) \n"
            )
        )
        if overide == "n":
            return

    reverse_fields = {
        f.name: f for f in model._meta.get_fields() if f.auto_created and not f.concrete
    }

    model_lower = model_name.lower()
    file = open(f"{app}/graphqls/mutations/{model_name}.py", "+w")
    file.writelines(
        [
            f"from {app}.graphqls.serializers import {model_name} as serializers\n",
            "from libs.graphql.graphene.graphene import CustomDjangoSerializerMutation\n\n\n",
        ]
    )

    for name, field in reverse_fields.items():
        if name == "owner":
            continue
        if field.related_model.__name__ == "ContentType":
            continue
        file.write(
            f"from {field.related_model._meta.app_label}.graphqls.serializers.{field.related_model.__name__} import {field.related_model.__name__}Serializer\n"
        )
    fields = list(
        filter(lambda x: x.name != "id" and x.name != "owner", model._meta.fields)
    )

    for field in fields:
        if field.name == "owner":
            continue

        if type(field).__name__ == "ForeignKey":
            if field.related_model.__name__ == "ContentType":
                continue

            file.write(
                f"from {field.related_model._meta.app_label}.graphqls.serializers.{field.related_model.__name__} import {field.related_model.__name__}Serializer\n"
            )

    file.write(f"class {model_name}Mutation(CustomDjangoSerializerMutation):\n")
    file.write("\tclass Meta:\n")
    file.write(f"\t\tserializer_class = serializers.{model_name}Serializer \n")
    file.write("\t\tnested_fields = {\n")
    for name, field in reverse_fields.items():
        if name == "owner":
            continue
        if name == "polymorphic_ctype":
            continue
        file.write(f"#\t\t '{name}': {field.related_model.__name__}Serializer,\n")
    for field in fields:
        if field.name == "owner":
            continue

        if type(field).__name__ == "ForeignKey":
            file.write(
                f"#\t\t'{field.name}': {field.related_model.__name__}Serializer,\n"
            )

    file.write("\t\t}\n")

    file.write(
        f"\t\tpermissions = {{'create':'{app}.add_{model_lower}', 'change': '{app}.change_{model_lower}', 'delete': '{app}.delete_{model_lower}',}} \n"
    )

    file.write("\t@classmethod\n")
    file.write("\tdef update(cls, root, info, **kwargs):\n")
    file.write("\t\t\n")
    file.write("\t\treturn super().update(root, info, **kwargs)\n")
    file.write("\t@classmethod\n")
    file.write("\tdef create(cls, root, info, **kwargs):\n")
    file.write("\t\t\n")
    file.write("\t\treturn super().create(root, info, **kwargs)\n")
    print(
        f"\x1b[5;30;42m...... file {app}/graphqls/mutations/{model_name}.py has been created\x1b[0m "
    )


def createSchema(app, model, erase="n"):
    createFolder(app, "schemas")
    model_name = model.__name__

    if os.path.exists(f"{app}/graphqls/schemas/{model_name}.py"):
        print("file already exist")
        overide = (
            erase
            if erase
            else input(
                f"type of  {model_name} already exist, would you like to override (y/n) \n"
            )
        )
        if overide == "n":
            return

    # Schemas
    schema = open(f"{app}/graphqls/schemas/{model_name}.py", "w+")

    res = f"""
import graphene
from graphql_jwt.decorators import login_required
from graphene import relay
from {app} import models
from libs.graphql.settings import *
from graphene_django.filter import DjangoFilterConnectionField
from {app}.graphqls.types.{model_name} import {model_name}Type,{model_name}DesType
from libs.graphql.connection import OrderedDjangoFilterConnectionField
import graphene
from {app}.graphqls.filters.{model_name} import {model_name}Filters
from graphene_django.filter.utils import get_filtering_args_from_filterset
from libs.graphql.types import CustomNode
from libs.graphql.filters import from_global_filter_for_relay
from libs.graphql.permissions import permission_required
from {app}.graphqls.functions.{model_name} import {model_name}CustomFunctionMutations
from {app}.graphqls.resolvers.{model_name} import resolve_{model_name.lower()}_perms
from {app}.graphqls.resolvers.{model_name} import resolve_{model_name.lower()}_object_perms
from {app}.models import {model_name}
 


filterclass = DjangoFilterConnectionField(
    {model_name}Type, filterset_class={model_name}Filters)
filter_fields = filterclass.filterset_class().__dict__['filters']
filtering_args = filterclass.filtering_args


class {model_name}Queries(graphene.ObjectType):
    {model_name.lower()} = CustomNode.Field({model_name}Type,check=resolve_{model_name.lower()}_object_perms)
    all_{model_name.lower()}s = OrderedDjangoFilterConnectionField({model_name}Type,ordering=graphene.List(of_type=graphene.String))
    all_{model_name.lower()}s_des = DjangoFilterConnectionField({model_name}DesType,ordering=graphene.List(of_type=graphene.String))
  
    {model_name.lower()}s = graphene.List({model_name}Type,ordering=graphene.String(), limit=graphene.Int(
    ), **filtering_args)

    
    def resolve_{model_name.lower()}s(self,info,**kwargs):
        ordering = kwargs.get('ordering', '-id')
        qs = models.{model_name}.objects.all()
        

        new_kwargs = from_global_filter_for_relay(filter_fields, kwargs,models.{model_name})
        filterset = filterclass.filterset_class(
            data={{**kwargs, **new_kwargs}}, queryset=qs, request=info.context,
        )
        qs = resolve_{model_name.lower()}_perms(info,filterset.qs,**kwargs)
        res = qs.order_by(ordering)
        limit = kwargs.pop('limit', None)
        add = qs.filter(pk__in=kwargs.get('include',[])) if kwargs.get('include',[]) is not None and len(kwargs.get('include',[]))>0 else []
        
        if limit:
                return [*add,*res[:limit]]

        if( getLen("{model_name}")):
            return [*add,*res[:getLen("{model_name}")]]
        return res

  
    def resolve_all_{model_name.lower()}s(root, info, **kwargs):
        qs = resolve_{model_name.lower()}_perms(info,{model_name}.objects.all(),**kwargs)
        
        return qs


    def resolve_all_{model_name.lower()}s_des(root, info, **kwargs):
        qs = resolve_{model_name.lower()}_perms(info,{model_name}.objects.all(),**kwargs)
        
        return qs

from {app}.graphqls.mutations import {model_name} as mutations

class {model_name}Mutations({model_name}CustomFunctionMutations,graphene.ObjectType):
    
    create_{model_name.lower()} = mutations.{model_name}Mutation.CreateField()
    update_{model_name.lower()} = mutations.{model_name}Mutation.UpdateField()
    delete_{model_name.lower()} = mutations.{model_name}Mutation.DeleteField()
    
    """
    schema.write(res)
    schema.close()
    #     "import graphene\n",
    #     "from graphene_django.filter import DjangoFilterConnectionField\n",
    #     "from graphene.relay.node import Node\n",
    #     f"from {app}.graphqls.types import {model_name} as types\n",
    #     f"from {app}.graphqls.mutations import {model_name} as mutations\n\n\n"])

    # queries

    print(
        f"\x1b[5;30;42m...... file {app}/graphqls/schemas/{model_name}.py has been created\x1b[0m "
    )


def createDefaultFile(
    app,
):
    file = open(f"{app}/graphqls/defaults.py", "w")
    res = f"""import graphene

class {app.upper()}Queries(graphene.ObjectType):
    pass

class {app.upper()}Mutations(graphene.ObjectType):
    pass
    """
    file.write(res)
    file.close()


def createDefault(app, model):
    model_name = model.__name__
    if os.path.exists(f"{app}/graphqls/defaults.py"):
        pass
    else:
        createDefaultFile(app)
    file = open(f"{app}/graphqls/defaults.py", "r")
    line = f"from {app}.graphqls.schemas.{model_name} import {model_name}Queries, {model_name}Mutations"
    content = file.read()
    file.close()
    if f"{model_name}Queries" in content and f"{model_name}Mutations" in content:
        pass
    else:
        content = line + "\n" + content
        add_query = f"{model_name}Queries,"
        add_mutation = f"{model_name}Mutations,"
        index_of_query = content.index("Queries(")
        index_of_mutation = content.index("Mutations(")
        content = (
            content[0 : index_of_query + len("Queries(")]
            + add_query
            + content[index_of_query + len("Queries(") :]
        )

        # uncomment to add mutations
        content = (
            content[0 : index_of_mutation + len(add_query) + len("Mutations(")]
            + add_mutation
            + content[index_of_mutation + len("Mutations(") + len(add_query) :]
        )
        file = open(f"{app}/graphqls/defaults.py", "w")
        # print(content)
        file.write(content)


def createDefaults(app, model):
    model_name = model.__name__
    line = f"from {app}.graphqls.schemas.{model_name} import {model_name}Queries, {model_name}Mutations"
    if os.path.exists(f"{app}/graphqls/defaults.py"):
        file = open(f"{app}/graphqls/defaults.py", "+w")
        content = file.read()
        # print(content)
        file.close()
        if line in content:
            pass
        else:
            f = open(f"{app}/graphqls/defaults.py", "+w")

            # content = f.read()
            print("content", content)
            content = line + "\n" + content
            add_query = f"{model_name}Queries"
            # add_mutation = f"{model_name}Mutations,"
            # try:
            index_of_query = content.index("Queries(", 0)

            # except:
            #     file.write(f'{model_name.upper()}Queries')
            # index_of_mutation = content.index("Mutations(")

            content = (
                content[0 : index_of_query + len("Queries(")]
                + add_query
                + content[index_of_query + len("Queries(") :]
            )

            # content = content[0:index_of_mutation + len(add_query) + len("Mutations(")] + add_mutation + \
            #     content[index_of_mutation +
            #             len("Mutations(") + len(add_query):]

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
        f"\x1b[5;30;42m...... file {app}/graphqls/defaults.py has been created\x1b[0m "
    )


class Command(BaseCommand):
    help = "Displays current time"

    def add_arguments(self, parser):
        parser.add_argument(
            "--models",
            "--models",
            type=str,
            nargs="+",
            help="Indicates the app.model you want to create graphql for",
        )
        parser.add_argument("-app", "--app", help="Create an admin account")
        parser.add_argument(
            "-all", "--all", action="store_true", help="Create an admin account"
        )
        parser.add_argument(
            "-r", "--register", action="store_true", help="Create an admin account"
        )

    def handle(self, *args, **kwargs):
        models = kwargs["models"]
        app_label = kwargs["app"]
        ALL = kwargs["all"]
        # Will fail if `foo`
        # shutil.copytree(
        #     './../src', f'./../backup/{time.strftime("%Y-%m-%d %H:%M:%S")}')
        if ALL:
            app_models = apps.get_app_config(app_label).get_models()
            for model in app_models:
                if "Historical" in model.__name__:
                    continue
                createTypes(app_label, model, "y")  #
                createCustomFilters(
                    app_label,
                    model,
                )  #
                createFilters(app_label, model, "y")  #
                createQuickFilters(
                    app_label,
                    model,
                )  #
                createSerializers(app_label, model, "y")
                createMutations(app_label, model, "n")
                createFunctionMutations(app_label, model, "y")
                createResolvers(app_label, model)
                createSchema(app_label, model, "y")
                if kwargs["register"]:
                    createDefault(app_label, model)
        else:
            for m in models:
                ####
                model = apps.get_model(app_label, m)
                if "Historical" in model.__name__:
                    continue
                createTypes(app_label, model, "y")
                createCustomFilters(
                    app_label,
                    model,
                )
                createFilters(app_label, model, "y")
                createQuickFilters(
                    app_label,
                    model,
                )
                createSerializers(app_label, model, "y")
                createMutations(app_label, model, "n")
                createFunctionMutations(app_label, model, "y")
                createResolvers(app_label, model)
                createSchema(app_label, model, "y")
                # if kwargs['register']:
                #     # createResolvers(app_label, model)
                #     createDefault(app_label, model)


# ./manage.py graphql  --app billing  --r  --models ProformaItemFihce
# ./manage.py graphql  --app operations  --all --r
# ./manage.py graphql  --app operations   --r --models Charge
# ./manage.py graphql  --app tracking   --r --models FuelCharge
