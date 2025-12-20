import graphene


class CharfieldChoices(graphene.ObjectType):
    label = graphene.String()
    value = graphene.String()


class AppType(graphene.ObjectType):
    name = graphene.String()
    models = graphene.List(
        "libs.graphql.schema.custom.models.queries.types.ModelType.ModelType"
    )


class FieldType(graphene.ObjectType):
    name = graphene.String()
    _type = graphene.String()
    column = graphene.String()
    related = graphene.Field(
        "libs.graphql.schema.custom.models.queries.types.RelatedFieldType.RelatedFieldType"
    )
    null = graphene.Boolean()
    verbose_name = graphene.String()
    model = graphene.String()


class ModelType(graphene.ObjectType):
    app = graphene.String()
    name = graphene.String()
    fields = graphene.List(
        "libs.graphql.schema.custom.models.queries.types.FieldType.FieldType"
    )


class RelatedFieldType(graphene.ObjectType):
    model = graphene.Field(
        "libs.graphql.schema.custom.models.queries.types.ModelType.ModelType"
    )
    fields = graphene.List(
        "libs.graphql.schema.custom.models.queries.types.FieldType.FieldType"
    )
