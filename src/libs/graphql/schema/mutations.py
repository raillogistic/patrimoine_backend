from libs.graphql.graphene.graphene import CustomDjangoSerializerMutation
from libs.graphql.serializers import CustomSerializer
from libs.models.fields import *
from libs.utils.utils import register_module

from .utils import get_class_by_name, userapps


def createSerializer(model):
    def createMeta():
        attr = {"model": model, "fields": "__all__"}
        meta_class = type("MetaClass", (), attr)
        return meta_class

    model_name = model.__name__
    class_name = f"{model_name}Serializer"
    return type(class_name, (CustomSerializer,), {"Meta": createMeta()})


from libs.models.fields import get_field_by_name


def get_nested_fields(model):
    nested = get_field_by_name(
        f"{model._meta.app_label}.graphqls.mutations",
        f"{model.__name__}CustomMutation",
        "nested",
        {},
    )

    res = {}
    for name, m in nested.items():
        res[name] = ProjectSerializers[m]

    return res


def createModelMutation(
    model,
):
    def createMeta():
        attr = {
            "serializer_class": ProjectSerializers[model.__name__],
            "nested_fields": get_nested_fields(model),
            "many": get_field_by_name(
                f"{model._meta.app_label}.graphqls.mutations",
                f"{model.__name__}CustomMutation",
                "many",
                False,
            ),
            "permissions": {
                "create": f"{model._meta.app_label}.add_{model.__name__.lower()}",
                "change": f"{model._meta.app_label}.change_{model.__name__.lower()}",
                "delete": f"{model._meta.app_label}.delete_{model.__name__.lower()}",
            },
        }
        meta_class = type(
            "MetaClass",
            (),
            attr,
        )
        return meta_class

    return type(
        f"{model.__name__}Mutation",
        (
            get_class_by_name(
                f"{model._meta.app_label}.graphqls.mutations",
                f"{model.__name__}CustomMutation",
            ),
            CustomDjangoSerializerMutation,
        ),
        {"Meta": createMeta()},
    )


from datetime import date, datetime

import graphene
from django.core.exceptions import ObjectDoesNotExist


def convertInputTypeToGraphene(_type):
    if type(_type) == list:
        return graphene.List(convertInputTypeToGraphene(_type[0]).__class__)
    if issubclass(_type, bool):
        return graphene.Boolean()
    if issubclass(_type, str):
        return graphene.String()
    if issubclass(_type, int):
        return graphene.Int()
    if issubclass(_type, float):
        return graphene.Float()
    if issubclass(_type, date):
        return graphene.Date()
    if issubclass(_type, datetime):
        return graphene.DateTime()
    return graphene.String()

def inputClassfields(func):
    res = {"id": graphene.String()}
    params = get_params(func)
    for param in params:
        res = {**res, param.name: convertInputTypeToGraphene(param.annotation)}
    return res
def inputStaticClassfields(func):
    res = {}
    params = get_params(func)
    for param in params:
        res = {**res, param.name: convertInputTypeToGraphene(param.annotation)}
    return res


from graphql import GraphQLError


def function_mutations(
    model,
):
    def resolve(model, func_name):
        def mutate(self, info, input):
            res = ""
            id = input.pop("id", None)

            if not id:
                raise GraphQLError("l'élément n'est pas trouvé")
                # return {"ok": False, "message": "l'élément n'est pas trouvé"}
            try:
                obj = model.objects.get(pk=id)
            except ObjectDoesNotExist:
                raise GraphQLError("l'élément n'est pas trouvé")
                return {"ok": False, "message": "l'élément n'est pas trouvé"}
            try:
                f = getattr(obj, func_name, None)
                if f:
                    res = f(**input)
            except Exception as E:
                print(E)
                raise GraphQLError(str(E))
            return {
                "ok": True,
                "message": "l'opération s'est terminée avec succès",
                "id": f"{res}",
            }

        return mutate

    res = {}
    functions = get_functions(model)
    for func in functions:
        
        inputClassType = type(
            f"Generated{model.__name__.capitalize()}{func.__name__.capitalize()}Input",
            (graphene.InputObjectType,),
            inputClassfields(func),
        )

        inputClass = type("Input", (), {"input": graphene.Argument(inputClassType)})
        mutationClass = type(
            f"Generated{model.__name__.capitalize()}{func.__name__.capitalize()}",
            (graphene.Mutation,),
            {
                "ok": graphene.Boolean(),
                "message": graphene.String(),
                "id": graphene.String(),
                "mutate": resolve(model, func.__name__),
                "Input": inputClass,
            },
        )
        res[f"{model.__name__.lower()}__{func.__name__.lower()}"] = (
            mutationClass.Field()
        )
        # print(createMutationFromFunction(f, model._meta.app_label, model.__name__))
    # input_type = type('',graphene.InputObjectType)
    return res

def static_function_mutations(
    model,
):
    def resolve(model, func_name):
        def mutate(self, info, input):
            res = ""
            try:
                f = getattr(model, func_name, None)
                if f:
                    res = f(**input)
            except Exception as E:
                print(E)
                raise GraphQLError(str(E))
            return {
                "ok": True,
                "message": "l'opération s'est terminée avec succès",
                "returning": f"{res}",
            }

        return mutate

    res = {}
    functions = get_classmethods(model)
    
    for func in functions:
        inputClassType = type(
            f"Generated{model.__name__.capitalize()}{func.__name__.capitalize()}Input",
            (graphene.InputObjectType,),
            inputStaticClassfields(func),
        )

        inputClass = type("Input", (), {"input": graphene.Argument(inputClassType)})
        print(get_graphene_type(func))
        mutationClass = type(
            f"Generated{model.__name__.capitalize()}{func.__name__.capitalize()}",
            (graphene.Mutation,),
            {
                "ok": graphene.Boolean(),
                "message": graphene.String(),
                "returning": get_graphene_type(func),
                "mutate": resolve(model, func.__name__),
                "Input": inputClass,
            },
        )
        res[f"{model.__name__.lower()}__{func.__name__.lower()}"] = (
            mutationClass.Field()
        )
        # print(createMutationFromFunction(f, model._meta.app_label, model.__name__))
    # input_type = type('',graphene.InputObjectType)
    return res


from .serializers import ProjectSerializers
from .utils import sorted_models

ModelMutations = {}
for model in sorted_models():
    ModelMutations[model.__name__] = createModelMutation(
        model,
    )
    register_module(
        __name__, ModelMutations[model.__name__], f"{model.__name__}Mutation"
    )


def createModelMutationsSchema(
    model,
):
    model_mutations = ModelMutations[model.__name__]
    functions = type(
        f"{model.__name__}CustomFunctionMutations",
        (graphene.ObjectType,),
        {**function_mutations(model),**static_function_mutations(model)},
    )

    return type(
        f"{model.__name__}Mutation",
        (
            functions,
            graphene.ObjectType,
        ),
        {
            f"create_{model.__name__.lower()}": model_mutations.CreateField(),
            f"update_{model.__name__.lower()}": model_mutations.UpdateField(),
            f"delete_{model.__name__.lower()}": model_mutations.DeleteField(),
        },
    )


from django.conf import settings


def get_custom_mutations():
    res = []
    for app in userapps():
        # try:
        _class = get_class_by_name(
            f"{app.name}.graphqls.custom_schema",
            f"{app.name.capitalize()}CustomMutations",
        )
        res.append(_class)
        # except Exception as E:
        # print("error in get_custom_mutations", E)
    urls = f"{settings.ROOT_URLCONF}".split(".")
    path = None
    if len(urls) > 0:
        path = urls[0]
    if path is None:
        return
    else:
        res.append(
            get_class_by_name(
                f"{path}.global_schema",
                "GlobalMutations",
            )
        )
    return res


from .utils import sorted_models

Mutations = {}

for m in sorted_models():
    Mutations[m.__name__] = createModelMutationsSchema(
        m,
    )
    register_module(__name__, Mutations[m.__name__], f"{m.__name__}Mutations")

__all__ = ["Mutations", "ModelMutations"]
